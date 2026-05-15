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

    agent: Literal["gait", "skin", "respiration", "thermal", "expression"]
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
    expression: AgentObservation | None = None
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def observations(self) -> list[AgentObservation]:
        candidates = (
            self.gait,
            self.skin,
            self.respiration,
            self.thermal,
            self.expression,
        )
        return [obs for obs in candidates if obs is not None]


class HistoricalFeedback(BaseModel):
    """Geçmişten getirilen hemşire kararı — supervisor pipeline'da RAG yanında.

    Yeni vaka geldiğinde, sinyaller benzer eski vakalara hemşirenin nasıl yanıt
    verdiğini bağlam olarak ekler. Karar mercii hâlâ LLM + ESI; bu sadece
    "geçmişte bu görünüm aldığında hemşire şöyle demişti" bilgisidir.
    """

    nurse_name: str
    hospital: str
    original_category: TriageCategory
    nurse_verdict: str
    verdict_kind: Literal["approve", "reject", "override"]
    rationale_tr: str = ""
    feedback_at: datetime
    similarity_score: float = 0.0


class TriageDecision(BaseModel):
    """Supervisor output rendered on the nurse dashboard."""

    patient_id: str
    category: TriageCategory
    label_tr: str
    rationale_tr: str = Field(description="ESI protokolüne dayalı kısa Türkçe gerekçe")
    confidence: float = Field(ge=0.0, le=1.0)
    per_agent_weights: dict[str, float] = Field(default_factory=dict)
    rag_references: list[str] = Field(default_factory=list)
    historical_feedback: list[HistoricalFeedback] = Field(default_factory=list)
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
        historical_feedback: list[HistoricalFeedback] | None = None,
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
            historical_feedback=historical_feedback or [],
            latency_ms=latency_ms,
        )


class DecisionRecord(BaseModel):
    """Bir kararın verdict-bağımsız kalıcı kaydı.

    Hemşire henüz ✓/✗/✎ yapmamış olsa bile karar `decisions_store`'a yazılır.
    Frontend yenilendiğinde bu kayıtlar + feedback kayıtları birleştirilip
    history reconstruct edilir.
    """

    decision_id: str
    patient_id: str
    decision: TriageDecision
    observations_snapshot: dict[str, AgentObservation] = Field(default_factory=dict)


class NurseFeedback(BaseModel):
    """Hemşire bir karara verdik verdiğinde oluşan kalıcı kayıt.

    `decision_id` frontend'in `entryKey(patient_id, decided_at)` ile ürettiği
    deterministic anahtar — aynı kararda birden fazla feedback verilirse
    sonuncusu üstüne yazılabilir (UI tarafında bu kararla tek verdict
    tutuluyor).
    """

    decision_id: str
    patient_id: str
    original_category: TriageCategory
    nurse_verdict: TriageCategory
    verdict_kind: Literal["approve", "reject", "override"]
    rationale_tr: str = ""
    nurse_first_name: str
    nurse_last_name: str
    hospital: str
    signals_summary: str = Field(
        default="",
        description="Token-overlap RAG için ajan gözlemlerinin tek-string özeti.",
    )
    observations_snapshot: dict[str, AgentObservation] = Field(default_factory=dict)
    decided_at: datetime
    feedback_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_historical(self, *, similarity_score: float = 0.0) -> HistoricalFeedback:
        return HistoricalFeedback(
            nurse_name=f"{self.nurse_first_name} {self.nurse_last_name}".strip(),
            hospital=self.hospital,
            original_category=self.original_category,
            nurse_verdict=self.nurse_verdict.value,
            verdict_kind=self.verdict_kind,
            rationale_tr=self.rationale_tr,
            feedback_at=self.feedback_at,
            similarity_score=similarity_score,
        )


class TriageEvent(BaseModel):
    """Wire envelope pushed over SSE to the dashboard."""

    type: Literal["agent_observation", "decision", "error", "heartbeat"]
    patient_id: str | None = None
    observation: AgentObservation | None = None
    decision: TriageDecision | None = None
    message: str | None = None
    emitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
