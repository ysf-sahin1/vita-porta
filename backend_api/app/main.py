"""Vita Porta backend API.

Endpoints:
  GET  /healthz                 — liveness
  POST /api/triage/run          — submit an agent bundle, get a decision
  GET  /api/triage/stream       — SSE stream of agent observations + decisions
  POST /api/triage/demo         — fire the three canonical demo bundles
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from backend_api.app.event_bus import EventBus
from orchestration.decisions_store import build_default_decision_store
from orchestration.demo import ambiguous_case, critical_case, stable_case
from orchestration.feedback_store import build_default_store
from orchestration.schemas import (
    AgentBundle,
    DecisionRecord,
    NurseFeedback,
    TriageDecision,
    TriageEvent,
)
from orchestration.supervisor import Supervisor

logger = logging.getLogger("vita_porta")
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.event_bus = EventBus()
    app.state.feedback_store = build_default_store()
    app.state.decisions_store = build_default_decision_store()
    app.state.supervisor = Supervisor(feedback_store=app.state.feedback_store)
    logger.info("Vita Porta backend hazır.")
    yield


def _persist_decision(app: FastAPI, bundle: AgentBundle, decision: TriageDecision) -> None:
    """Hemşire ✓/✗/✎ vermeden de karar kalıcı kaydedilsin — refresh'te kaybolmasın."""

    observations = {obs.agent: obs for obs in bundle.observations()}
    record = DecisionRecord(
        decision_id=f"{decision.patient_id}__{decision.decided_at.isoformat().replace('+00:00', 'Z')}",
        patient_id=decision.patient_id,
        decision=decision,
        observations_snapshot=observations,
    )
    try:
        app.state.decisions_store.save(record)
    except Exception:  # noqa: BLE001 — persistance is advisory; main path must continue
        logger.warning("Karar kaydı yazılamadı (devam ediliyor).", exc_info=True)


app = FastAPI(title="Vita Porta API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/triage/run")
async def run_triage(bundle: AgentBundle) -> dict:
    supervisor: Supervisor = app.state.supervisor
    bus: EventBus = app.state.event_bus

    for obs in bundle.observations():
        await bus.publish(
            TriageEvent(type="agent_observation", patient_id=bundle.patient_id, observation=obs)
        )

    decision = await supervisor.decide(bundle)
    await bus.publish(
        TriageEvent(type="decision", patient_id=decision.patient_id, decision=decision)
    )
    _persist_decision(app, bundle, decision)
    return decision.model_dump(mode="json")


@app.get("/api/triage/stream")
async def stream_triage():
    bus: EventBus = app.state.event_bus

    async def event_source() -> AsyncIterator[dict[str, str]]:
        yield {
            "event": "heartbeat",
            "data": json.dumps({"msg": "connected"}, ensure_ascii=False),
        }
        async for event in bus.subscribe():
            yield {
                "event": event.type,
                "data": event.model_dump_json(),
            }

    return EventSourceResponse(event_source())


@app.post("/api/triage/feedback")
async def submit_feedback(feedback: NurseFeedback) -> dict:
    """Hemşire ✓/✗/✎ verdiğinde çağrılır — JSON store'a kalıcı kayıt."""

    store = app.state.feedback_store
    store.save(feedback)
    logger.info(
        "Feedback kaydedildi: decision=%s hemşire=%s %s verdict=%s (%s)",
        feedback.decision_id,
        feedback.nurse_first_name,
        feedback.nurse_last_name,
        feedback.nurse_verdict.value,
        feedback.verdict_kind,
    )
    return {"saved": True, "decision_id": feedback.decision_id}


@app.get("/api/triage/history")
async def list_history() -> dict[str, list[dict]]:
    """Frontend ilk yüklemede çağırır.

    Döndürdüğü iki liste birlikte history reconstruct'ı yapar:
    - decisions: tüm karar kayıtları (verdict'ten bağımsız, her hasta görünür)
    - feedback:  hemşire ✓/✗/✎ verdiği kayıtlar (decision_id ile bağlanır)
    """

    decisions = app.state.decisions_store.list_all()
    feedback = app.state.feedback_store.list_all()
    return {
        "decisions": [r.model_dump(mode="json") for r in decisions],
        "feedback": [r.model_dump(mode="json") for r in feedback],
    }


@app.delete("/api/triage/history", status_code=204)
async def reset_history() -> None:
    """Tüm karar ve hemşire feedback kayıtlarını siler. Geri alınamaz.

    Frontend'deki "Sıfırla" butonu çağırır; kullanıcı confirmation modal'ı
    onayladıktan sonra.
    """

    app.state.decisions_store.clear()
    app.state.feedback_store.clear()
    logger.info("Karar ve feedback geçmişi sıfırlandı.")


@app.post("/api/triage/demo")
async def demo_triage(scenario: str = "all") -> dict:
    supervisor: Supervisor = app.state.supervisor
    bus: EventBus = app.state.event_bus

    bundles_by_name: dict[str, AgentBundle] = {
        "red": critical_case(),
        "yellow": ambiguous_case(),
        "green": stable_case(),
    }
    if scenario == "all":
        bundles = list(bundles_by_name.values())
    elif scenario in bundles_by_name:
        bundles = [bundles_by_name[scenario]]
    else:
        raise HTTPException(404, f"unknown scenario: {scenario}")

    decisions = []
    for bundle in bundles:
        for obs in bundle.observations():
            await bus.publish(
                TriageEvent(
                    type="agent_observation", patient_id=bundle.patient_id, observation=obs
                )
            )
            await asyncio.sleep(0.4)
        decision = await supervisor.decide(bundle)
        await bus.publish(
            TriageEvent(type="decision", patient_id=decision.patient_id, decision=decision)
        )
        _persist_decision(app, bundle, decision)
        decisions.append(decision.model_dump(mode="json"))
        await asyncio.sleep(0.6)

    return {"scenarios_played": [b.patient_id for b in bundles], "decisions": decisions}
