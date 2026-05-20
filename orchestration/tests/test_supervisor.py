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


async def test_empty_bundle_is_insufficient(supervisor: Supervisor) -> None:
    decision = await supervisor.decide(AgentBundle(patient_id="demo-none"))
    assert decision.category is TriageCategory.INSUFFICIENT


async def test_low_confidence_is_demoted(supervisor: Supervisor) -> None:
    bundle = AgentBundle(
        patient_id="demo-noisy",
        gait=AgentObservation(
            agent="gait",
            confidence=0.2,
            summary_tr="Belirsiz sallantı sinyali",
            signals={"sway": True, "severity": "high"},
        ),
    )
    decision = await supervisor.decide(bundle)
    assert decision.category is TriageCategory.INSUFFICIENT
