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
    {
        "id": "esi-red-chest-pain",
        "category": "red",
        "pattern": (
            "Göğüs ağrısı + terleme + solukluk kombinasyonu kardiyak acil işaretidir. "
            "ESI Seviye 1-2 kapsamında acil müdahale gerekir."
        ),
    },
    {
        "id": "esi-red-stroke",
        "category": "red",
        "pattern": (
            "Yüz sarkması + kol güçsüzlüğü + konuşma bozukluğu inme belirtisidir. "
            "ESI Seviye 1 kapsamında acil nörolojik değerlendirme gerekir."
        ),
    },
    {
        "id": "esi-red-anaphylaxis",
        "category": "red",
        "pattern": (
            "Ani gelişen yüz/boyun ödemi + nefes darlığı + döküntü anafilaksi "
            "işaretidir. ESI Seviye 1, epinefrin uygulanmalı."
        ),
    },
    {
        "id": "esi-red-trauma",
        "category": "red",
        "pattern": (
            "Yüksek enerjili travma + bilinç değişikliği + anormal vital bulgular "
            "hayati tehlike işaretidir. ESI Seviye 1-2 acil müdahale."
        ),
    },
    {
        "id": "esi-red-sepsis",
        "category": "red",
        "pattern": (
            "Yüksek ateş + hızlı solunum + konfüzyon + hipotansiyon sepsis triadıdır. "
            "ESI Seviye 2 kapsamında acil kan kültürü ve antibiyotik."
        ),
    },
    {
        "id": "esi-yellow-abdominal",
        "category": "yellow",
        "pattern": (
            "Karın ağrısı + bulantı + hafif ateş gözlem gerektiren durumdur. "
            "ESI Seviye 3, apandisit ekarte edilmeli."
        ),
    },
    {
        "id": "esi-yellow-headache",
        "category": "yellow",
        "pattern": (
            "Şiddetli baş ağrısı + ışık hassasiyeti + bulantı menenjit veya migren "
            "ayırıcı tanısı gerektirir. ESI Seviye 2-3."
        ),
    },
    {
        "id": "esi-yellow-fracture",
        "category": "yellow",
        "pattern": (
            "Ekstremitede şişlik + hareket kısıtlılığı + ağrı kırık şüphesi "
            "işaretidir. ESI Seviye 3, radyoloji değerlendirmesi gerekir."
        ),
    },
    {
        "id": "esi-yellow-hypertension",
        "category": "yellow",
        "pattern": (
            "Kan basıncı 180/110 üzeri + baş ağrısı + görme bozukluğu hipertansif "
            "acil sınırındadır. ESI Seviye 2-3 yakın izlem."
        ),
    },
    {
        "id": "esi-yellow-dysrhythmia",
        "category": "yellow",
        "pattern": (
            "Çarpıntı + baş dönmesi + hafif göğüs rahatsızlığı kardiyak aritmi "
            "şüphesi doğurur. ESI Seviye 3, EKG öncelikli."
        ),
    },
    {
        "id": "esi-yellow-dehydration",
        "category": "yellow",
        "pattern": (
            "Uzun süreli kusma/ishal + turgor kaybı + taşikardi dehidrasyon "
            "işaretidir. ESI Seviye 3, IV sıvı değerlendirmesi."
        ),
    },
    {
        "id": "esi-green-minor-laceration",
        "category": "green",
        "pattern": (
            "Küçük yüzeysel kesi + aktif kanama yok + vital bulgular normal. "
            "ESI Seviye 4-5, yara bakımı ve pansuman yeterli."
        ),
    },
    {
        "id": "esi-green-mild-fever",
        "category": "green",
        "pattern": (
            "38.5 altı ateş + genel durum iyi + solunum normal üst solunum yolu "
            "enfeksiyonu olabilir. ESI Seviye 4-5 rutin değerlendirme."
        ),
    },
    {
        "id": "esi-green-sprain",
        "category": "green",
        "pattern": (
            "Ayak bileği burkması + hafif şişlik + yük verebiliyor + vital normal. "
            "ESI Seviye 4-5, Ottawa kuralları negatif."
        ),
    },
    {
        "id": "esi-green-skin-rash",
        "category": "green",
        "pattern": (
            "Lokalize döküntü + kaşıntı + sistemik belirti yok alerjik kontakt "
            "dermatit düşündürür. ESI Seviye 5, topikal tedavi."
        ),
    },
]


