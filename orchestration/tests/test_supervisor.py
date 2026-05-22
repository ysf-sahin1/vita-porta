"""Smoke tests for the supervisor against the deterministic mock LLM."""

from __future__ import annotations

import pytest

from orchestration.demo import ambiguous_case, critical_case, stable_case
from orchestration.llm import MockLLMClient
from orchestration.rag import InMemoryRetriever
from orchestration.schemas import AgentBundle, AgentObservation, TriageCategory
from orchestration.supervisor import Supervisor


@pytest.fixture
def supervisor() -> Supervisor:
    return Supervisor(llm=MockLLMClient(), retriever=InMemoryRetriever())


async def test_critical_case_returns_red(supervisor: Supervisor) -> None:
    decision = await supervisor.decide(critical_case())
    assert decision.category is TriageCategory.RED
    assert "Kırmızı" in decision.label_tr
    assert decision.rationale_tr


async def test_stable_case_returns_green(supervisor: Supervisor) -> None:
    decision = await supervisor.decide(stable_case())
    assert decision.category is TriageCategory.GREEN


async def test_ambiguous_case_is_yellow(supervisor: Supervisor) -> None:
    decision = await supervisor.decide(ambiguous_case())
    assert decision.category is TriageCategory.YELLOW


def _zero_obs(agent: str, summary: str = "veri yok") -> AgentObservation:
    """AgentBundle artık 3 alanı zorunlu kıldığı için 'eksik veri' durumu
    sıfır-güven gözlemle temsil edilir (None ile değil)."""
    return AgentObservation(
        agent=agent,  # type: ignore[arg-type]
        confidence=0.0,
        summary_tr=summary,
        signals={},
    )


async def test_all_zero_bundle_is_insufficient(supervisor: Supervisor) -> None:
    """3 ajan da gözlem üretmiş ama hiçbiri eşik üstünde değil → INSUFFICIENT."""
    bundle = AgentBundle(
        patient_id="demo-none",
        gait=_zero_obs("gait"),
        thermal=_zero_obs("thermal"),
        expression=_zero_obs("expression"),
    )
    decision = await supervisor.decide(bundle)
    assert decision.category is TriageCategory.INSUFFICIENT
    # Tüm ajanların eksik olduğu rationale'da görünmeli
    assert "gait" in decision.rationale_tr
    assert "thermal" in decision.rationale_tr
    assert "expression" in decision.rationale_tr


async def test_low_confidence_is_demoted(supervisor: Supervisor) -> None:
    """Tek ajan zayıf (gait güven 0.2) → INSUFFICIENT, LLM çağrılmamalı."""
    bundle = AgentBundle(
        patient_id="demo-noisy",
        gait=AgentObservation(
            agent="gait",
            confidence=0.2,
            summary_tr="Belirsiz sallantı sinyali",
            signals={"sway": True, "severity": "high"},
        ),
        thermal=AgentObservation(
            agent="thermal",
            confidence=0.7,
            summary_tr="Normal cilt sıcaklığı 36.5°C",
            signals={"temp_estimate_c": 36.5, "fever_flag": False},
        ),
        expression=AgentObservation(
            agent="expression",
            confidence=0.5,
            summary_tr="Sakin yüz ifadesi",
            signals={"expression_state": "sakin", "pain_score": 0.1},
        ),
    )
    decision = await supervisor.decide(bundle)
    assert decision.category is TriageCategory.INSUFFICIENT
    assert "gait" in decision.rationale_tr
