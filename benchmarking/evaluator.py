"""Benchmark execution and safety-oriented metric calculation."""

from __future__ import annotations

import asyncio
import math
import time
from pathlib import Path

from benchmarking.models import (
    BenchmarkCase,
    BenchmarkCaseResult,
    BenchmarkDataset,
    BenchmarkMetrics,
    BenchmarkReport,
)
from gateway_agents.io.video_file import VideoFileSource
from gateway_agents.runner import Runner
from orchestration.feedback_store import FeedbackStore
from orchestration.llm import MockLLMClient
from orchestration.rag import InMemoryRetriever
from orchestration.schemas import AgentBundle, TriageCategory
from orchestration.supervisor import Supervisor

_CATEGORIES = list(TriageCategory)
_URGENCY = {
    TriageCategory.GREEN: 1,
    TriageCategory.YELLOW: 2,
    TriageCategory.RED: 3,
}


class EmptyFeedbackStore(FeedbackStore):
    """Isolates benchmark runs from live nurse feedback."""

    def save(self, feedback) -> None:
        return None

    def list_all(self) -> list:
        return []

    def query_similar(self, signals_text: str, *, k: int = 3) -> list:
        return []

    def clear(self) -> None:
        return None


def build_benchmark_supervisor(engine: str = "mock") -> Supervisor:
    """Build an isolated supervisor for reproducible or configured runs."""

    feedback = EmptyFeedbackStore()
    if engine == "mock":
        return Supervisor(
            llm=MockLLMClient(),
            retriever=InMemoryRetriever(),
            feedback_store=feedback,
        )
    if engine == "configured":
        return Supervisor(feedback_store=feedback)
    raise ValueError(f"Bilinmeyen benchmark motoru: {engine}")


async def evaluate_dataset(
    dataset: BenchmarkDataset,
    supervisor: Supervisor,
    *,
    engine: str = "mock",
) -> BenchmarkReport:
    results: list[BenchmarkCaseResult] = []
    for case in dataset.cases:
        results.append(await _evaluate_case(case, supervisor))

    return BenchmarkReport(
        dataset_name=dataset.name,
        dataset_version=dataset.version,
        dataset_description=dataset.description,
        synthetic=dataset.synthetic,
        engine=engine,
        metrics=calculate_metrics(results),
        results=results,
    )


async def _evaluate_case(case: BenchmarkCase, supervisor: Supervisor) -> BenchmarkCaseResult:
    started = time.perf_counter()
    error: str | None = None
    bundle = case.bundle

    try:
        if bundle is None and case.video_path is not None:
            bundle = await asyncio.to_thread(
                _analyse_video,
                case.video_path,
                case.window_duration_s,
            )
        if bundle is None:
            raise ValueError("Vaka girdisinden AgentBundle üretilemedi")
        decision = await supervisor.decide(bundle)
        predicted = decision.category
        confidence = decision.confidence
    except Exception as exc:  # noqa: BLE001 - a failed case must remain visible in the report
        error = str(exc)
        predicted = TriageCategory.INSUFFICIENT
        confidence = 0.0

    latency_ms = max(0, int((time.perf_counter() - started) * 1000))
    expected = case.expected_category
    return BenchmarkCaseResult(
        case_id=case.case_id,
        expected_category=expected,
        predicted_category=predicted,
        correct=predicted is expected,
        critical_miss=expected is TriageCategory.RED and predicted is not TriageCategory.RED,
        under_triage=_is_under_triage(expected, predicted),
        over_triage=_is_over_triage(expected, predicted),
        input_type="video" if case.video_path else "bundle",
        confidence=confidence,
        latency_ms=latency_ms,
        agent_confidences={
            obs.agent: obs.confidence for obs in bundle.observations()
        }
        if bundle is not None
        else {},
        notes=case.notes,
        tags=case.tags,
        error=error,
    )


def _analyse_video(video_path: str, window_duration_s: float) -> AgentBundle | None:
    source = VideoFileSource(Path(video_path), loop=False)
    with Runner(source=source, window_duration_s=window_duration_s) as runner:
        return runner.analyze_once()


def _is_under_triage(expected: TriageCategory, predicted: TriageCategory) -> bool:
    if expected is TriageCategory.INSUFFICIENT:
        return False
    if predicted is TriageCategory.INSUFFICIENT:
        return True
    return _URGENCY[predicted] < _URGENCY[expected]


def _is_over_triage(expected: TriageCategory, predicted: TriageCategory) -> bool:
    if expected is TriageCategory.INSUFFICIENT or predicted is TriageCategory.INSUFFICIENT:
        return False
    return _URGENCY[predicted] > _URGENCY[expected]


def calculate_metrics(results: list[BenchmarkCaseResult]) -> BenchmarkMetrics:
    total = len(results)
    matrix = {
        expected.value: {predicted.value: 0 for predicted in _CATEGORIES}
        for expected in _CATEGORIES
    }
    for result in results:
        matrix[result.expected_category.value][result.predicted_category.value] += 1

    correct = sum(result.correct for result in results)
    red_results = [r for r in results if r.expected_category is TriageCategory.RED]
    red_correct = sum(r.predicted_category is TriageCategory.RED for r in red_results)
    latencies = sorted(result.latency_ms for result in results)

    category_recall: dict[str, float | None] = {}
    for category in _CATEGORIES:
        expected = [r for r in results if r.expected_category is category]
        category_recall[category.value] = (
            round(sum(r.predicted_category is category for r in expected) / len(expected), 4)
            if expected
            else None
        )

    return BenchmarkMetrics(
        total_cases=total,
        correct_cases=correct,
        accuracy=_ratio(correct, total),
        red_sensitivity=_ratio(red_correct, len(red_results)) if red_results else None,
        critical_miss_rate=(
            _ratio(sum(r.critical_miss for r in red_results), len(red_results))
            if red_results
            else None
        ),
        under_triage_rate=_ratio(sum(r.under_triage for r in results), total),
        over_triage_rate=_ratio(sum(r.over_triage for r in results), total),
        insufficient_rate=_ratio(
            sum(r.predicted_category is TriageCategory.INSUFFICIENT for r in results),
            total,
        ),
        mean_latency_ms=round(sum(latencies) / total, 2) if total else 0.0,
        p95_latency_ms=float(_percentile_nearest_rank(latencies, 0.95)),
        category_recall=category_recall,
        confusion_matrix=matrix,
    )


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _percentile_nearest_rank(values: list[int], percentile: float) -> int:
    if not values:
        return 0
    rank = max(1, math.ceil(percentile * len(values)))
    return values[rank - 1]
