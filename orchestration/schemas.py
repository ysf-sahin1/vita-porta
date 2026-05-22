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

    agent: Literal["gait", "thermal", "expression"]
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
    """The set of observations the supervisor evaluates together.

    All three modalities (gait, thermal, expression) are required — analiz
    politikası: 3 ajan bir arada gelmezse triaj yapılmaz. Eksik veri
    ``confidence=0`` ile gelen bir AgentObservation olarak temsil edilir,
    None ile değil.
    """

    patient_id: str = Field(default_factory=lambda: uuid4().hex[:8])
    gait: AgentObservation
    thermal: AgentObservation
    expression: AgentObservation
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def observations(self) -> list[AgentObservation]:
        return [self.gait, self.thermal, self.expression]


# Üç ajanın da analize girebilmesi için minimum güven eşikleri.
# - gait: MediaPipe pose visibility — yarı görünürlük (0.40) yeterli sayılır.
# - thermal: AMG LOW-confirmed (0.55) ile RGB proxy mid-range arası taban.
#            0.50 LOW okumayı kabul ederken çok zayıf proxy'yi (face_ratio<0.45) eler.
# - expression: face_mesh tavanı 0.55 proxy modunda; 0.35 = face_ratio ~0.27 = "yüz var".
#
# Eşik altında kalan ajan "gözlem üretti ama veri zayıf" demektir; bundle analiz
# için INSUFFICIENT işaretlenir. Hem runner (POST-öncesi) hem supervisor
# (LLM-öncesi) hem de backend (curl bypass için) bu sözlüğe bakar — single source.
AGENT_PRESENCE_THRESHOLDS: dict[str, float] = {
    "gait": 0.40,
    "thermal": 0.50,
    "expression": 0.35,
}


def bundle_completeness_issues(bundle: "AgentBundle") -> list[tuple[str, str]]:
    """3 ajanın da kendi eşiğinin üstünde olup olmadığını döndürür.

    Returns:
        Eşiği geçmeyen ajanlar için (agent_name, reason) tuple listesi.
        Boş liste → 3'ü de eşik üstünde, analize girebilir.
    """
    issues: list[tuple[str, str]] = []
    obs_by_agent = {o.agent: o for o in bundle.observations()}
    for agent, threshold in AGENT_PRESENCE_THRESHOLDS.items():
        obs = obs_by_agent.get(agent)
        if obs is None:
            issues.append((agent, "gözlem yok"))
            continue
        if obs.confidence < threshold:
            issues.append(
                (agent, f"güven {obs.confidence:.2f} < {threshold:.2f}")
            )
    return issues


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


class NurseSession(BaseModel):
    """Hemşire mesai oturumu — giriş ve (varsa) çıkış zamanı.

    Frontend `LoginScreen` submit'ettiğinde `start` endpoint çağrılır,
    backend `session_id` üretir ve `logout_at=None` ile satırı yazar.
    Hemşire "Çıkış" butonuna bastığında `end` endpoint çağrılır, aynı
    `session_id` ile `logout_at=now` olan yeni satır append edilir.
    ``JsonSessionStore.list_all`` aynı session_id için son satırı döndürür
    (override mantığı), böylece kapalı oturumlar logout zamanıyla, açık
    oturumlar None ile listede görünür.
    """

    session_id: str
    nurse_first_name: str
    nurse_last_name: str
    hospital: str
    login_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    logout_at: datetime | None = None


class TriageEvent(BaseModel):
    """Wire envelope pushed over SSE to the dashboard."""

    type: Literal["agent_observation", "decision", "error", "heartbeat"]
    patient_id: str | None = None
    observation: AgentObservation | None = None
    decision: TriageDecision | None = None
    message: str | None = None
    emitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
