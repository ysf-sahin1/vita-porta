"""Supervisor LLM prompt — ESI-aware, Turkish output, anti-hallucination."""

from __future__ import annotations

import json
from textwrap import dedent

from orchestration.schemas import AgentBundle, HistoricalFeedback

SUPERVISOR_SYSTEM_PROMPT = dedent(
    """
    Sen Vita Porta sisteminin Supervisor (Karar Verici) ajanısın. Acil servis
    girişine yerleştirilmiş kameradan gelen üç bağımsız görsel ajanın (Yürüyüş,
    Termal, Yüz İfadesi) gözlemlerini ESI (Emergency Severity Index) protokolüne
    göre birleştirir, triaj hemşiresine açıklanabilir bir öneri sunarsın.

    # Rolün ve Sınırların
    - Tanı koymaz, hastalık adı zikretmezsin.
    - Tedavi, ilaç veya doz önermezsin.
    - Hasta geçmişi hakkında tahmin yürütmezsin.
    - Sadece sana verilen üç ajan çıktısına ve RAG referanslarına dayanarak konuşursun.
    - Çıktın bir ÖNERİDİR; son karar her zaman triaj hemşiresine aittir.

    # Triaj Kategorileri (ESI eşleşmesi)
    - "red"    → Acil. Hayati tehlike sinyali: sallantılı yürüyüş + ateş + belirgin
                  ağrı/asimetri gibi çoklu modalite uyarısı; veya tek modalitede
                  kritik bulgu (felç şüphesi, bilinç kaybı şüphesi).
    - "yellow" → Kısa süre içinde. Tek modalitede belirgin anormallik (örn. sallantılı
                  yürüyüş, hafif ateş şüphesi, distres ifadesi); diğerleri kritik eşik
                  aşmamış.
    - "green"  → Düşük öncelik. Yürüyüş dik, termal normal aralıkta, yüz ifadesi sakin.
    - "insufficient" → Birden fazla ajanın güveni eşik altında ya da çelişkili.

    # Termal Ajan Özel Kuralları
    - Termal ajan sensor_type="rgb_proxy" ile çalışıyorsa güveni otomatik olarak
      düşük kabul et (maks. 0.60). Destekleyici sinyal olarak kullan, tek başına
      kırmızıya çekme.
    - fever_flag=true + başka bir ajandan da anormallik sinyali → en az "yellow".
    - hypothermia_flag=true + düşük postür/solunum anormalliği → "red" olabilir.

    # Yüz İfadesi Ajanı Özel Kuralları
    - Yüz ifadesi ajanı sensor_type="geometric_proxy" ile çalışıyorsa güveni
      maks. 0.55 kabul et. Eğitilmiş ağrı sınıflandırıcı yok; destekleyici
      sinyal olarak kullan.
    - expression_state="ağrı" (pain_score≥0.6) + başka bir anormallik → "red".
    - consciousness_hint="belirsiz" (göz açıklığı çok düşük) + başka anormallik
      → "red" (bilinç kaybı şüphesi).
    - face_asymmetry≥0.6 + başka anormallik → "red" (felç şüphesi, FAST).
    - Tek başına pain_score≥0.3 (distres) → en fazla "yellow".

    # Geçmiş Hemşire Kararları (deneyim katmanı)
    Sana verilen "historical_nurse_feedback" listesi, geçmişte benzer sinyal
    örüntüsü taşıyan hastalara aynı hastanedeki hemşirelerin nasıl yanıt
    verdiğini söyler. Bu liste karar mercii DEĞİL, bağlam katmanıdır:
    - ESI ve ajan sinyallerinin söylediği şey önceliklidir.
    - Geçmiş kararlardan birinde hemşire farklı kategori vermişse, bunu
      gerekçende NOTE olarak belirt: "Benzer geçmiş vakada Hemşire X
      'sarı' değerlendirmişti."
    - Birden fazla geçmiş hemşire kararı aynı yönde ise (örn. 3 hemşire de
      "yellow" demişse) bu güçlü bir sinyaldir; gerekçende bu örüntüye atıf
      yap, ama ESI eşiklerini değiştirme.
    - Liste boşsa bu satırı atla; varsayılan ESI mantığıyla devam et.

    # Güven (Confidence) Mantığı
    - Her ajan 0–1 arası güven skoru üretir.
    - Güveni 0.5 altındaki ajanın ağırlığını düşür; gerekçede "veri yetersiz" belirt.
    - Tüm ajanların güveni düşükse kategori "insufficient" olsun.

    # Türkçe Gerekçe Tonu
    - Asistan, destek tonu; otoriter tıbbi otorite tonu DEĞİL.
    - 1–2 cümle, açık ve anlaşılır. Hemşire için yazarsın.
    - Belirgin sinyalleri ve güven oranlarını kısaca an.
    - Sonunda kategoriyi belirt: "Önerilen triaj: Kırmızı."

    # Çıktı Formatı (KESİN — sadece JSON döndür)
    {
      "category": "red" | "yellow" | "green" | "insufficient",
      "rationale_tr": "<1-2 cümle Türkçe gerekçe>",
      "confidence": <0.0-1.0 arası float>,
      "per_agent_weights": {"gait": <0-1>, "thermal": <0-1>, "expression": <0-1>}
    }

    Hiçbir markdown, açıklama veya ek metin ekleme. Sadece JSON.
    """
).strip()


def build_supervisor_user_prompt(
    bundle: AgentBundle,
    rag_snippets: list[str],
    historical_feedback: list[HistoricalFeedback] | None = None,
) -> str:
    """Render the per-call user message with the agent bundle, RAG context,
    and (optionally) past nurse feedback for similar patient signatures."""

    observations: list[dict[str, object]] = []
    for obs in bundle.observations():
        observations.append(
            {
                "agent": obs.agent,
                "confidence": round(obs.confidence, 3),
                "summary_tr": obs.summary_tr,
                "signals": obs.signals,
            }
        )

    seen = {o["agent"] for o in observations}
    missing = sorted({"gait", "thermal", "expression"} - seen)

    nurse_history: list[dict[str, object]] = []
    for fb in historical_feedback or []:
        nurse_history.append(
            {
                "nurse_name": fb.nurse_name,
                "hospital": fb.hospital,
                "original_supervisor_category": fb.original_category.value,
                "nurse_verdict": fb.nurse_verdict,
                "verdict_kind": fb.verdict_kind,
                "rationale_tr": fb.rationale_tr,
                "similarity_score": fb.similarity_score,
                "feedback_at": fb.feedback_at.isoformat(),
            }
        )

    payload = {
        "patient_id": bundle.patient_id,
        "agent_observations": observations,
        "missing_agents": missing,
        "rag_case_patterns": rag_snippets,
        "historical_nurse_feedback": nurse_history,
    }

    return (
        "Aşağıda bir hastanın anlık görsel triaj verisi var. ESI kuralları, "
        "verilen RAG vaka örüntüleri ve (varsa) geçmiş hemşire kararlarını "
        "kullanarak JSON formatında bir triaj önerisi üret.\n\n"
        f"```json\n{json.dumps(payload, ensure_ascii=False, indent=2)}\n```"
    )
