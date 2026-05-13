"""Shared contracts between agents and the supervisor.

Every agent emits a structured observation; the supervisor consumes the bundle
and emits a triage decision. These models are the single source of truth.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


class TriageCategory(str, Enum):
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"
    INSUFFICIENT = "insufficient"


TRIAGE_LABEL_TR: dict[TriageCategory, str] = {
    TriageCategory.RED: "Kırmızı — Acil",
    TriageCategory.YELLOW: "Sarı — Kısa süre içinde",
    TriageCategory.GREEN: "Yeşil — Düşük öncelik",
    TriageCategory.INSUFFICIENT: "Veri yetersiz",
}


class AgentObservation(BaseModel):
    """One agent's view of the patient.

    The summary field is what the dashboard renders verbatim under each agent's
    card; signals carry the machine-readable details the supervisor reasons over.
    """

    agent: Literal["gait", "skin", "respiration", "thermal"]
    confidence: float = Field(ge=0.0, le=1.0)
    summary_tr: str = Field(description="Hemşireye gösterilecek tek cümlelik Türkçe gözlem")
    signals: dict[str, float | str | bool] = Field(default_factory=dict)
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("summary_tr")
    @classmethod
    def summary_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("summary_tr boş olamaz")
        return v.strip()


class AgentBundle(BaseModel):
    """The set of observations the supervisor evaluates together."""

    patient_id: str = Field(default_factory=lambda: uuid4().hex[:8])
    gait: AgentObservation | None = None
    skin: AgentObservation | None = None
    respiration: AgentObservation | None = None
    thermal: AgentObservation | None = None
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def observations(self) -> list[AgentObservation]:
        candidates = (self.gait, self.skin, self.respiration, self.thermal)
        return [obs for obs in candidates if obs is not None]


class TriageDecision(BaseModel):
    """Supervisor output rendered on the nurse dashboard."""

    patient_id: str
    category: TriageCategory
    label_tr: str
    rationale_tr: str = Field(description="ESI protokolüne dayalı kısa Türkçe gerekçe")
    confidence: float = Field(ge=0.0, le=1.0)
    per_agent_weights: dict[str, float] = Field(default_factory=dict)
    rag_references: list[str] = Field(default_factory=list)
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: int | None = None

    @classmethod
    def from_category(
        cls,
        *,
        patient_id: str,
        category: TriageCategory,
        rationale_tr: str,
        confidence: float,
        per_agent_weights: dict[str, float] | None = None,
        rag_references: list[str] | None = None,
        latency_ms: int | None = None,
    ) -> "TriageDecision":
        return cls(
            patient_id=patient_id,
            category=category,
            label_tr=TRIAGE_LABEL_TR[category],
            rationale_tr=rationale_tr,
            confidence=confidence,
            per_agent_weights=per_agent_weights or {},
            rag_references=rag_references or [],
            latency_ms=latency_ms,
        )


class TriageEvent(BaseModel):
    """Wire envelope pushed over SSE to the dashboard."""

    type: Literal["agent_observation", "decision", "error", "heartbeat"]
    patient_id: str | None = None
    observation: AgentObservation | None = None
    decision: TriageDecision | None = None
    message: str | None = None
    emitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
