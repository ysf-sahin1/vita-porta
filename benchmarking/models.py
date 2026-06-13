"""Data contracts for repeatable benchmark runs."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field, model_validator

from orchestration.schemas import AgentBundle, TriageCategory


class BenchmarkCase(BaseModel):
    """One expert-labelled or synthetic evaluation case."""

    case_id: str = Field(min_length=1)
    expected_category: TriageCategory
    bundle: AgentBundle | None = None
    video_path: str | None = None
    window_duration_s: float = Field(default=3.0, gt=0.0, le=30.0)
    notes: str = ""
    tags: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def exactly_one_input(self) -> BenchmarkCase:
        if (self.bundle is None) == (self.video_path is None):
            raise ValueError(
                "Benchmark vakası bundle veya video_path alanlarından tam birini içermeli"
            )
        return self


class BenchmarkDataset(BaseModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = ""
    synthetic: bool = False
    cases: list[BenchmarkCase] = Field(min_length=1)


class BenchmarkCaseResult(BaseModel):
    case_id: str
    expected_category: TriageCategory
    predicted_category: TriageCategory
    correct: bool
    critical_miss: bool
    under_triage: bool
    over_triage: bool
    input_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    latency_ms: int = Field(ge=0)
    agent_confidences: dict[str, float] = Field(default_factory=dict)
    notes: str = ""
    tags: list[str] = Field(default_factory=list)
    error: str | None = None


class BenchmarkMetrics(BaseModel):
    total_cases: int = Field(ge=0)
    correct_cases: int = Field(ge=0)
    accuracy: float = Field(ge=0.0, le=1.0)
    red_sensitivity: float | None = Field(default=None, ge=0.0, le=1.0)
    critical_miss_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    under_triage_rate: float = Field(ge=0.0, le=1.0)
    over_triage_rate: float = Field(ge=0.0, le=1.0)
    insufficient_rate: float = Field(ge=0.0, le=1.0)
    mean_latency_ms: float = Field(ge=0.0)
    p95_latency_ms: float = Field(ge=0.0)
    category_recall: dict[str, float | None] = Field(default_factory=dict)
    confusion_matrix: dict[str, dict[str, int]] = Field(default_factory=dict)


class BenchmarkReport(BaseModel):
    dataset_name: str
    dataset_version: str
    dataset_description: str = ""
    synthetic: bool
    engine: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metrics: BenchmarkMetrics
    results: list[BenchmarkCaseResult]
