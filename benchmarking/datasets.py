"""Built-in labelled datasets.

The bundled dataset is deliberately marked synthetic. It validates benchmark
plumbing and regression behaviour; it is not evidence of clinical performance.
"""

from __future__ import annotations

from benchmarking.models import BenchmarkCase, BenchmarkDataset
from orchestration.demo import ambiguous_case, critical_case, stable_case
from orchestration.schemas import AgentBundle, AgentObservation, TriageCategory


def _obs(
    agent: str,
    confidence: float,
    summary: str,
    signals: dict[str, float | str | bool],
) -> AgentObservation:
    return AgentObservation(
        agent=agent,  # type: ignore[arg-type]
        confidence=confidence,
        summary_tr=summary,
        signals=signals,
    )


def _bundle(
    case_id: str,
    *,
    gait: AgentObservation,
    thermal: AgentObservation,
    expression: AgentObservation,
) -> AgentBundle:
    return AgentBundle(
        patient_id=case_id,
        gait=gait,
        thermal=thermal,
        expression=expression,
    )


def _normal_gait(confidence: float = 0.82) -> AgentObservation:
    return _obs(
        "gait",
        confidence,
        "Dik ve simetrik yürüyüş",
        {"sway": False, "severity": "none", "symmetry": 0.92},
    )


def _normal_thermal(confidence: float = 0.82) -> AgentObservation:
    return _obs(
        "thermal",
        confidence,
        "Termal ölçüm normal aralıkta",
        {
            "temp_estimate_c": 36.6,
            "fever_flag": False,
            "hypothermia_flag": False,
            "sensor_type": "amg8833",
        },
    )


def _normal_expression(confidence: float = 0.72) -> AgentObservation:
    return _obs(
        "expression",
        confidence,
        "Yüz ifadesi sakin",
        {
            "expression_state": "sakin",
            "pain_score": 0.08,
            "face_asymmetry": 0.1,
            "consciousness_hint": "uyanık",
            "sensor_type": "geometric_proxy",
        },
    )


def synthetic_baseline_dataset() -> BenchmarkDataset:
    """Return a deterministic regression dataset covering all four outputs."""

    red_gait_face = _bundle(
        "syn-red-gait-face",
        gait=_obs(
            "gait",
            0.88,
            "Belirgin sallantılı ve asimetrik yürüyüş",
            {"sway": True, "severity": "high", "symmetry": 0.25},
        ),
        thermal=_normal_thermal(),
        expression=_obs(
            "expression",
            0.72,
            "Belirgin yüz asimetrisi",
            {
                "expression_state": "distres",
                "pain_score": 0.35,
                "face_asymmetry": 0.74,
                "consciousness_hint": "uyanık",
                "sensor_type": "geometric_proxy",
            },
        ),
    )
    red_gait_hypothermia = _bundle(
        "syn-red-gait-hypothermia",
        gait=_obs(
            "gait",
            0.84,
            "Belirgin sallantılı yürüyüş",
            {"sway": True, "severity": "high", "symmetry": 0.3},
        ),
        thermal=_obs(
            "thermal",
            0.91,
            "Düşük sıcaklık ölçümü",
            {
                "temp_estimate_c": 34.7,
                "fever_flag": False,
                "hypothermia_flag": True,
                "sensor_type": "amg8833",
            },
        ),
        expression=_normal_expression(),
    )
    yellow_gait = _bundle(
        "syn-yellow-gait",
        gait=_obs(
            "gait",
            0.76,
            "Hafif sallantılı yürüyüş",
            {"sway": True, "severity": "mild", "symmetry": 0.61},
        ),
        thermal=_normal_thermal(),
        expression=_normal_expression(),
    )
    yellow_fever = _bundle(
        "syn-yellow-fever",
        gait=_normal_gait(),
        thermal=_obs(
            "thermal",
            0.92,
            "Yüksek sıcaklık ölçümü",
            {
                "temp_estimate_c": 38.4,
                "fever_flag": True,
                "hypothermia_flag": False,
                "sensor_type": "amg8833",
            },
        ),
        expression=_normal_expression(),
    )
    yellow_pain = _bundle(
        "syn-yellow-pain",
        gait=_normal_gait(),
        thermal=_normal_thermal(),
        expression=_obs(
            "expression",
            0.7,
            "Belirgin ağrı ifadesi",
            {
                "expression_state": "ağrı",
                "pain_score": 0.72,
                "face_asymmetry": 0.12,
                "consciousness_hint": "uyanık",
                "sensor_type": "geometric_proxy",
            },
        ),
    )
    green_high_confidence = _bundle(
        "syn-green-high-confidence",
        gait=_normal_gait(0.94),
        thermal=_normal_thermal(0.95),
        expression=_normal_expression(0.88),
    )
    all_low = _bundle(
        "syn-insufficient-all-low",
        gait=_obs("gait", 0.1, "Postür verisi yetersiz", {}),
        thermal=_obs("thermal", 0.1, "Termal veri yetersiz", {}),
        expression=_obs("expression", 0.1, "Yüz verisi yetersiz", {}),
    )
    thermal_low = _bundle(
        "syn-insufficient-thermal-low",
        gait=_normal_gait(),
        thermal=_obs("thermal", 0.2, "Termal veri yetersiz", {}),
        expression=_normal_expression(),
    )

    cases = [
        BenchmarkCase(
            case_id="syn-red-multimodal",
            expected_category=TriageCategory.RED,
            bundle=critical_case().model_copy(update={"patient_id": "syn-red-multimodal"}),
            tags=["red", "multimodal"],
        ),
        BenchmarkCase(
            case_id=red_gait_face.patient_id,
            expected_category=TriageCategory.RED,
            bundle=red_gait_face,
            tags=["red", "gait", "expression"],
        ),
        BenchmarkCase(
            case_id=red_gait_hypothermia.patient_id,
            expected_category=TriageCategory.RED,
            bundle=red_gait_hypothermia,
            tags=["red", "gait", "thermal"],
        ),
        BenchmarkCase(
            case_id="syn-yellow-multimodal",
            expected_category=TriageCategory.YELLOW,
            bundle=ambiguous_case().model_copy(update={"patient_id": "syn-yellow-multimodal"}),
            tags=["yellow", "multimodal"],
        ),
        BenchmarkCase(
            case_id=yellow_gait.patient_id,
            expected_category=TriageCategory.YELLOW,
            bundle=yellow_gait,
            tags=["yellow", "gait"],
        ),
        BenchmarkCase(
            case_id=yellow_fever.patient_id,
            expected_category=TriageCategory.YELLOW,
            bundle=yellow_fever,
            tags=["yellow", "thermal"],
        ),
        BenchmarkCase(
            case_id=yellow_pain.patient_id,
            expected_category=TriageCategory.YELLOW,
            bundle=yellow_pain,
            tags=["yellow", "expression"],
        ),
        BenchmarkCase(
            case_id="syn-green-standard",
            expected_category=TriageCategory.GREEN,
            bundle=stable_case().model_copy(update={"patient_id": "syn-green-standard"}),
            tags=["green", "standard"],
        ),
        BenchmarkCase(
            case_id=green_high_confidence.patient_id,
            expected_category=TriageCategory.GREEN,
            bundle=green_high_confidence,
            tags=["green", "high-confidence"],
        ),
        BenchmarkCase(
            case_id=all_low.patient_id,
            expected_category=TriageCategory.INSUFFICIENT,
            bundle=all_low,
            tags=["insufficient", "all-low-confidence"],
        ),
        BenchmarkCase(
            case_id=thermal_low.patient_id,
            expected_category=TriageCategory.INSUFFICIENT,
            bundle=thermal_low,
            tags=["insufficient", "thermal-low-confidence"],
        ),
    ]

    return BenchmarkDataset(
        name="Vita Porta Sentetik Baseline",
        version="1.0.0",
        description=(
            "Benchmark motorunu ve karar regresyonlarını doğrulayan sentetik vaka seti. "
            "Klinik performans kanıtı değildir."
        ),
        synthetic=True,
        cases=cases,
    )
