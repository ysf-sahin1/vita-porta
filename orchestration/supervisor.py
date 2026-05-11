"""LangGraph-based supervisor.

The supervisor takes a bundle of agent observations, retrieves a handful of
ESI case patterns from the RAG store, asks the configured LLM for a structured
decision, and validates the response against the TriageDecision schema.

State graph (single linear flow for MVP):
    retrieve_rag → ask_llm → validate
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TypedDict

from langgraph.graph import END, StateGraph

from orchestration.llm import LLMClient, build_llm_client
from orchestration.prompts import SUPERVISOR_SYSTEM_PROMPT, build_supervisor_user_prompt
from orchestration.rag import RagRetriever, build_default_retriever
from orchestration.schemas import (
    AgentBundle,
    TriageCategory,
    TriageDecision,
)

logger = logging.getLogger(__name__)


class _SupervisorState(TypedDict, total=False):
    bundle: AgentBundle
    rag_snippets: list[str]
    raw_decision: dict
    decision: TriageDecision
    started_ms: float


@dataclass
class Supervisor:
    """Async-friendly façade over the LangGraph workflow."""

    llm: LLMClient = field(default_factory=build_llm_client)
    retriever: RagRetriever = field(default_factory=build_default_retriever)

    def __post_init__(self) -> None:
        self._graph = self._build_graph()

    def _build_graph(self):
        graph: StateGraph = StateGraph(_SupervisorState)
        graph.add_node("retrieve_rag", self._retrieve_rag)
        graph.add_node("ask_llm", self._ask_llm)
        graph.add_node("validate", self._validate)
        graph.set_entry_point("retrieve_rag")
        graph.add_edge("retrieve_rag", "ask_llm")
        graph.add_edge("ask_llm", "validate")
        graph.add_edge("validate", END)
        return graph.compile()

    async def decide(self, bundle: AgentBundle) -> TriageDecision:
        initial: _SupervisorState = {"bundle": bundle, "started_ms": time.perf_counter() * 1000}
        final = await self._graph.ainvoke(initial)
        return final["decision"]

    async def _retrieve_rag(self, state: _SupervisorState) -> _SupervisorState:
        bundle = state["bundle"]
        query = " ".join(obs.summary_tr for obs in bundle.observations())
        snippets = await self.retriever.retrieve(query or "triaj değerlendirmesi", k=3)
        return {"rag_snippets": snippets}

    async def _ask_llm(self, state: _SupervisorState) -> _SupervisorState:
        bundle = state["bundle"]
        user_prompt = build_supervisor_user_prompt(bundle, state.get("rag_snippets", []))
        try:
            raw = await self.llm.complete_json(SUPERVISOR_SYSTEM_PROMPT, user_prompt)
        except Exception as exc:  # noqa: BLE001 — production fallback per tech report
            logger.exception("LLM çağrısı başarısız, kural tabanlı yedeğe geçiliyor: %s", exc)
            from orchestration.llm import MockLLMClient

            raw = await MockLLMClient().complete_json(SUPERVISOR_SYSTEM_PROMPT, user_prompt)
        return {"raw_decision": raw}

    async def _validate(self, state: _SupervisorState) -> _SupervisorState:
        raw = state["raw_decision"]
        bundle = state["bundle"]
        started_ms = state.get("started_ms")
        latency_ms = int(time.perf_counter() * 1000 - started_ms) if started_ms else None

        category_raw = raw.get("category", "insufficient")
        try:
            category = TriageCategory(category_raw)
        except ValueError:
            category = TriageCategory.INSUFFICIENT

        decision = TriageDecision.from_category(
            patient_id=bundle.patient_id,
            category=category,
            rationale_tr=str(raw.get("rationale_tr", "Veri yetersiz.")).strip(),
            confidence=float(raw.get("confidence", 0.0)),
            per_agent_weights={
                k: float(v) for k, v in (raw.get("per_agent_weights") or {}).items()
            },
            rag_references=state.get("rag_snippets", []),
            latency_ms=latency_ms,
        )
        return {"decision": decision}
