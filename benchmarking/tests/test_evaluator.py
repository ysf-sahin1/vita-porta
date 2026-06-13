from __future__ import annotations

from benchmarking.datasets import synthetic_baseline_dataset
from benchmarking.evaluator import (
    build_benchmark_supervisor,
    calculate_metrics,
    evaluate_dataset,
)
from benchmarking.models import BenchmarkCaseResult
from orchestration.schemas import TriageCategory


def _result(
    case_id: str,
    expected: TriageCategory,
    predicted: TriageCategory,
) -> BenchmarkCaseResult:
    urgency = {
        TriageCategory.GREEN: 1,
        TriageCategory.YELLOW: 2,
        TriageCategory.RED: 3,
    }
    under = (
        expected is not TriageCategory.INSUFFICIENT
        and (
            predicted is TriageCategory.INSUFFICIENT
            or urgency[predicted] < urgency[expected]
        )
    )
    over = (
        expected is not TriageCategory.INSUFFICIENT
        and predicted is not TriageCategory.INSUFFICIENT
        and urgency[predicted] > urgency[expected]
    )
    return BenchmarkCaseResult(
        case_id=case_id,
        expected_category=expected,
        predicted_category=predicted,
        correct=expected is predicted,
        critical_miss=expected is TriageCategory.RED and predicted is not TriageCategory.RED,
        under_triage=under,
        over_triage=over,
        input_type="bundle",
        confidence=0.7,
        latency_ms=10,
    )


def test_metrics_count_red_to_green_as_critical_miss() -> None:
    metrics = calculate_metrics(
        [
            _result("red-hit", TriageCategory.RED, TriageCategory.RED),
            _result("red-miss", TriageCategory.RED, TriageCategory.GREEN),
            _result("green-over", TriageCategory.GREEN, TriageCategory.YELLOW),
        ]
    )

    assert metrics.red_sensitivity == 0.5
    assert metrics.critical_miss_rate == 0.5
    assert metrics.under_triage_rate == 0.3333
    assert metrics.over_triage_rate == 0.3333
    assert metrics.confusion_matrix["red"]["green"] == 1


async def test_synthetic_baseline_is_repeatable() -> None:
    dataset = synthetic_baseline_dataset()
    supervisor = build_benchmark_supervisor("mock")

    report = await evaluate_dataset(dataset, supervisor, engine="mock")

    assert report.synthetic is True
    assert report.metrics.total_cases == 11
    assert report.metrics.red_sensitivity == 1.0
    assert report.metrics.critical_miss_rate == 0.0
    assert report.metrics.accuracy == 1.0
