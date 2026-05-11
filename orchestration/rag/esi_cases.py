"""Seed ESI case patterns for the RAG layer.

For the MVP the medical content stays minimal and synthetic — five canonical
ESI patterns covering the categories the supervisor must produce. The pilot
phase replaces this with anonymised hospital triage records, per the data
strategy in the technical report.
"""

from __future__ import annotations

ESI_SEED_CASES: list[dict[str, str]] = [
    {
        "id": "esi-red-pallor-tachypnea",
        "category": "red",
        "pattern": (
            "Belirgin solgunluk + hızlı sığ solunum + sallantılı veya destekli yürüyüş "
            "kombinasyonu hayati tehlike işaretidir. ESI Seviye 1-2 kapsamında acil "
            "müdahale gerekir."
        ),
    },
    {
        "id": "esi-red-cyanosis",
        "category": "red",
        "pattern": (
            "Siyanoz (mavimsi solukluk) + düşük solunum hızı veya düzensiz solunum "
            "vital riskidir. Hemşire derhal değerlendirmeli."
        ),
    },
    {
        "id": "esi-yellow-gait-sway",
        "category": "yellow",
        "pattern": (
            "Stabilite kaybı (sallantılı yürüyüş, asimetri) tek başına ESI Seviye 3 "
            "değerlendirmesi gerektirir; düşme riski ve nörolojik bulgular için yakın izlem."
        ),
    },
    {
        "id": "esi-yellow-mild-pallor",
        "category": "yellow",
        "pattern": (
            "Hafif solgunluk veya orta düzeyde solunum hızı artışı (solunum 20-24/dk) "
            "stabil ama izlenmesi gereken sinyaldir."
        ),
    },
    {
        "id": "esi-green-stable",
        "category": "green",
        "pattern": (
            "Dik ve simetrik yürüyüş, düzenli solunum (12-18/dk) ve normal ten rengi "
            "ESI Seviye 4-5 kapsamındadır; rutin akışta değerlendirilir."
        ),
    },
]
