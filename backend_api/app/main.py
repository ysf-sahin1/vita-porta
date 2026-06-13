"""Vita Porta backend API.

Endpoints:
  GET  /healthz                 — liveness
  POST /api/triage/run          — submit an agent bundle, get a decision
  GET  /api/triage/stream       — SSE stream of agent observations + decisions
  POST /api/triage/demo         — fire the three canonical demo bundles
  POST /api/sessions/start      — hemşire mesai başlangıcı (login)
  POST /api/sessions/end        — hemşire mesai sonu (logout)
  GET  /api/sessions            — hemşire mesai geçmişi (header popover)
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from backend_api.app.event_bus import EventBus
from benchmarking.datasets import synthetic_baseline_dataset
from benchmarking.evaluator import build_benchmark_supervisor, evaluate_dataset
from benchmarking.store import BenchmarkReportStore
from orchestration.config import get_settings
from orchestration.decisions_store import build_default_decision_store
from orchestration.demo import ambiguous_case, critical_case, stable_case
from orchestration.feedback_store import build_default_store
from orchestration.schemas import (
    AgentBundle,
    DecisionRecord,
    NurseFeedback,
    TriageCategory,
    TriageDecision,
    TriageEvent,
    bundle_completeness_issues,
)
from orchestration.sessions_store import build_default_session_store
from orchestration.supervisor import Supervisor

logger = logging.getLogger("vita_porta")
logging.basicConfig(level=logging.INFO)

# 3 ajan da kendi eşiğinin üstünde değilse bundle "eksik" sayılır:
# supervisor çağrılmaz, doğrudan INSUFFICIENT döner. Eşikler tek kaynaktan
# (orchestration.schemas.AGENT_PRESENCE_THRESHOLDS) okunur; gateway runner ve
# supervisor da aynı sözlüğü kullanır. Bu fonksiyon gateway by-pass edildiğinde
# (curl, demo, 3. taraf client) ikinci kapıdır.


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.event_bus = EventBus()
    app.state.feedback_store = build_default_store()
    app.state.decisions_store = build_default_decision_store()
    app.state.sessions_store = build_default_session_store()
    app.state.benchmark_store = BenchmarkReportStore()
    app.state.benchmark_lock = asyncio.Lock()
    app.state.supervisor = Supervisor(feedback_store=app.state.feedback_store)
    app.state.pir_motion: bool | None = None

    # Sentence-transformers modelini startup'ta ısıt: ilk kullanıcı isteği
    # soğuk başlangıç (~12s) yerine sıcak (~17ms) RAG retrieval görür.
    asyncio.create_task(_warmup_retriever(app.state.supervisor))

    logger.info("Vita Porta backend hazır.")
    yield


async def _warmup_retriever(supervisor: Supervisor) -> None:
    try:
        await supervisor.retriever.retrieve("triaj değerlendirmesi ısınma", k=1)
        logger.info("RAG retriever ısındı.")
    except Exception as exc:
        logger.warning("RAG ısınma başarısız (devam ediliyor): %s", exc)


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

    # Eksik bundle (3 ajan bir arada değil / biri eşik altında) → LLM çağırma,
    # SSE bus'ı kirletme, decisions_store'a "boş hasta" yazma. Doğrudan
    # INSUFFICIENT dön. Gateway zaten gate uyguluyor; bu burada da olunca
    # curl / demo / 3. taraf client'lardan da korunmuş olur.
    completeness_issues = bundle_completeness_issues(bundle)
    if completeness_issues:
        missing = ", ".join(f"{agent} ({reason})" for agent, reason in completeness_issues)
        return TriageDecision.from_category(
            patient_id=bundle.patient_id,
            category=TriageCategory.INSUFFICIENT,
            rationale_tr=f"Veri yetersiz — eksik ajan(lar): {missing}. Analiz yapılamadı.",
            confidence=0.0,
        ).model_dump(mode="json")

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


class _SessionStartBody(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    hospital: str = Field(min_length=1)


class _SessionEndBody(BaseModel):
    session_id: str = Field(min_length=1)


@app.post("/api/sessions/start")
async def start_session(body: _SessionStartBody) -> dict:
    record = app.state.sessions_store.start(
        first_name=body.first_name,
        last_name=body.last_name,
        hospital=body.hospital,
    )
    logger.info(
        "Mesai başladı: %s %s @ %s (id=%s)",
        record.nurse_first_name,
        record.nurse_last_name,
        record.hospital,
        record.session_id,
    )
    return record.model_dump(mode="json")


@app.post("/api/sessions/end")
async def end_session(body: _SessionEndBody) -> dict:
    record = app.state.sessions_store.end(body.session_id)
    if record is None:
        # Bilinmeyen session_id — sessizce 200 dön, idempotent davranış.
        return {"closed": False, "session_id": body.session_id}
    logger.info(
        "Mesai bitti: %s %s (id=%s)",
        record.nurse_first_name,
        record.nurse_last_name,
        record.session_id,
    )
    return {"closed": True, "session": record.model_dump(mode="json")}


class _PirReportBody(BaseModel):
    motion: bool


@app.post("/api/pir/report")
async def report_pir(body: _PirReportBody) -> dict:
    """Gateway runner'dan PIR hareket durumu güncelleme.

    Runner hareket başladığında motion=True, biterken motion=False gönderir.
    Durum SSE üzerinden dashboard'a yayınlanır.
    """
    app.state.pir_motion = body.motion
    bus: EventBus = app.state.event_bus
    await bus.publish(
        TriageEvent(type="pir_status", pir_motion=body.motion)
    )
    return {"pir_motion": body.motion}


@app.get("/api/pir/status")
async def get_pir_status() -> dict:
    """Son bilinen PIR durumunu döner — frontend ilk yüklemede çağırabilir."""
    return {"pir_motion": app.state.pir_motion}


@app.get("/api/sessions")
async def list_sessions(limit: int = 20) -> dict[str, list[dict]]:
    """Header popover için son N mesai oturumu (en yeni önce)."""

    records = app.state.sessions_store.list_all()
    limited = records[: max(1, min(limit, 200))]
    return {"sessions": [r.model_dump(mode="json") for r in limited]}


@app.get("/api/benchmark/latest")
async def latest_benchmark() -> dict:
    """Return the latest persisted benchmark report, if one exists."""

    report = app.state.benchmark_store.load()
    return {"report": report.model_dump(mode="json") if report else None}


@app.post("/api/benchmark/run")
async def run_benchmark(engine: Literal["mock", "configured"] = "mock") -> dict:
    """Run the labelled synthetic baseline without touching live triage history."""

    async with app.state.benchmark_lock:
        dataset = synthetic_baseline_dataset()
        supervisor = build_benchmark_supervisor(engine)
        report = await evaluate_dataset(dataset, supervisor, engine=engine)
        app.state.benchmark_store.save(report)
    return report.model_dump(mode="json")


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
