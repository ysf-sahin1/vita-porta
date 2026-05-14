"""Runnable supervisor demo.

Three canonical scenarios — critical, ambiguous, and stable — driven by hand-
crafted agent observations. Use this to verify the prompt, the RAG hook, and
the LLM fallback path before plugging in real cameras.

    python -m orchestration.demo
"""

from __future__ import annotations

import asyncio
import json

from orchestration.schemas import AgentBundle, AgentObservation
from orchestration.supervisor import Supervisor


def critical_case() -> AgentBundle:
    return AgentBundle(
        patient_id="demo-red",
        skin=AgentObservation(
            agent="skin",
            confidence=0.88,
            summary_tr="Yüzde belirgin solgunluk ve dudak renginde kayıp gözlemlendi",
            signals={"pallor": True, "severity": "high", "hsv_v": 0.42},
        ),
        respiration=AgentObservation(
            agent="respiration",
            confidence=0.92,
            summary_tr="Solunum hızı 28/dk, sığ ve hızlı solunum örüntüsü",
            signals={"rate_bpm": 28, "severity": "high", "regularity": 0.41},
        ),
        gait=AgentObservation(
            agent="gait",
            confidence=0.76,
            summary_tr="Sağa doğru sallantılı yürüyüş, asimetrik adım örüntüsü",
            signals={"sway": True, "severity": "high", "symmetry": 0.31},
        ),
        thermal=AgentObservation(
            agent="thermal",
            confidence=0.58,
            summary_tr="Ateş şüphesi: tahmini cilt sıcaklığı 38.8°C (RGB proxy)",
            signals={
                "temp_estimate_c": 38.8,
                "fever_flag": True,
                "hypothermia_flag": False,
                "warmth_score": 0.92,
                "sensor_type": "rgb_proxy",
            },
        ),
    )


def ambiguous_case() -> AgentBundle:
    return AgentBundle(
        patient_id="demo-yellow",
        skin=AgentObservation(
            agent="skin",
            confidence=0.63,
            summary_tr="Hafif solgunluk eğilimi, kritik eşik altında",
            signals={"pallor": False, "severity": "mild"},
        ),
        gait=AgentObservation(
            agent="gait",
            confidence=0.71,
            summary_tr="Hafif sallantı, tek başına stabilite riski",
            signals={"sway": True, "severity": "mild", "symmetry": 0.62},
        ),
        thermal=AgentObservation(
            agent="thermal",
            confidence=0.52,
            summary_tr="Hafif ısı artışı: tahmini 37.7°C, ateş eşiğinde (RGB proxy)",
            signals={
                "temp_estimate_c": 37.7,
                "fever_flag": True,
                "hypothermia_flag": False,
                "warmth_score": 0.68,
                "sensor_type": "rgb_proxy",
            },
        ),
    )


def stable_case() -> AgentBundle:
    return AgentBundle(
        patient_id="demo-green",
        skin=AgentObservation(
            agent="skin",
            confidence=0.84,
            summary_tr="Normal ten rengi, ek bulgu yok",
            signals={"pallor": False, "severity": "none"},
        ),
        respiration=AgentObservation(
            agent="respiration",
            confidence=0.81,
            summary_tr="Solunum hızı 15/dk, düzenli",
            signals={"rate_bpm": 15, "severity": "none", "regularity": 0.94},
        ),
        gait=AgentObservation(
            agent="gait",
            confidence=0.80,
            summary_tr="Dik ve simetrik yürüyüş",
            signals={"sway": False, "severity": "none", "symmetry": 0.91},
        ),
        thermal=AgentObservation(
            agent="thermal",
            confidence=0.55,
            summary_tr="Normal cilt sıcaklığı: tahmini 36.6°C (RGB proxy)",
            signals={
                "temp_estimate_c": 36.6,
                "fever_flag": False,
                "hypothermia_flag": False,
                "warmth_score": 0.48,
                "sensor_type": "rgb_proxy",
            },
        ),
    )


async def main() -> None:
    supervisor = Supervisor()
    cases = [
        ("Kritik vaka", critical_case()),
        ("Belirsiz vaka", ambiguous_case()),
        ("Stabil vaka", stable_case()),
    ]
    for label, bundle in cases:
        decision = await supervisor.decide(bundle)
        print(f"\n=== {label} ({bundle.patient_id}) ===")
        print(json.dumps(decision.model_dump(mode="json"), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
