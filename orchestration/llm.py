"""Provider-agnostic LLM client.

MVP supports three providers: Anthropic Claude, OpenAI, and a deterministic
mock used for tests and offline demos. The supervisor stays decoupled from any
single vendor — switching providers is an env change, not a refactor.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod

from orchestration.config import Settings, get_settings


class LLMClient(ABC):
    @abstractmethod
    async def complete_json(self, system: str, user: str) -> dict:
        """Return a parsed JSON object from the LLM response."""


class AnthropicClient(LLMClient):
    def __init__(self, *, model: str, api_key: str) -> None:
        from anthropic import AsyncAnthropic

        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def complete_json(self, system: str, user: str) -> dict:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=512,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
        )
        text = "".join(block.text for block in response.content if block.type == "text")
        return _parse_json_lenient(text)


class OpenAIClient(LLMClient):
    def __init__(self, *, model: str, api_key: str) -> None:
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def complete_json(self, system: str, user: str) -> dict:
        response = await self._client.chat.completions.create(
            model=self._model,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        text = response.choices[0].message.content or "{}"
        return _parse_json_lenient(text)


class MockLLMClient(LLMClient):
    """Deterministic rule-based fallback.

    Mirrors the supervisor prompt's ESI logic well enough to run offline demos,
    unit tests, and CI without burning API credits. Used as the production
    fallback when the LLM API is unreachable, per the technical report.
    """

    async def complete_json(self, system: str, user: str) -> dict:
        payload = _extract_payload(user)
        observations = payload.get("agent_observations", [])
        missing = payload.get("missing_agents", [])

        by_agent: dict[str, dict] = {o["agent"]: o for o in observations}
        weights = {
            name: (by_agent[name]["confidence"] if name in by_agent else 0.0)
            for name in ("gait", "thermal", "expression")
        }

        red_flags = 0
        yellow_flags = 0
        rationale_parts: list[str] = []

        # Gait: ESKI (sway:bool/sway_score/symmetry) VEYA YENI (sway_detected/
        # symmetry_status). 3 ajanlı setup'ta severity:"high" tek başına kırmızı
        # eşiğe yaklaşır (belirgin sallantılı + asimetrik yürüyüş düşme/şok
        # riskinin güçlü göstergesi).
        gait = by_agent.get("gait")
        if gait and gait["confidence"] >= 0.5:
            signals = gait.get("signals", {})
            sway_score = float(signals.get("sway_score", 0))
            severity = signals.get("severity")
            sway_new = signals.get("sway_detected") is True
            asym_new = signals.get("symmetry_status") == "anormal"
            has_sway = (
                signals.get("sway") is True
                or sway_score >= 0.6
                or sway_new
                or asym_new
            )
            if severity == "high":
                red_flags += 1
                rationale_parts.append(
                    f"yürüyüş ajanı %{int(gait['confidence']*100)} "
                    "güvenle belirgin sallantılı/asimetrik yürüyüş tespit etti"
                )
            elif has_sway or severity == "mild":
                yellow_flags += 1
                rationale_parts.append(
                    f"yürüyüş ajanı %{int(gait['confidence']*100)} "
                    "güvenle sallantılı yürüyüş tespit etti"
                )

        # Yüz ifadesi ajanı: geometrik proxy modunda destekleyici sinyal.
        # Ağrı/bilinç/asimetri tek başına kırmızıya çekmez; başka anormallikle
        # birleşince kırmızıya katkı verir.
        expression = by_agent.get("expression")
        if expression and expression["confidence"] >= 0.4:
            signals = expression.get("signals", {})
            state = signals.get("expression_state", "")
            pain = float(signals.get("pain_score", 0.0))
            asym = float(signals.get("face_asymmetry", 0.0))
            consciousness = signals.get("consciousness_hint", "")

            asymmetry_high = asym >= 0.6
            consciousness_low = consciousness == "belirsiz"
            pain_high = state == "ağrı" or pain >= 0.6

            if asymmetry_high and (red_flags >= 1 or yellow_flags >= 1):
                red_flags += 1
                rationale_parts.append(
                    "yüz ifadesi ajanı belirgin yüz asimetrisi bildirdi (felç şüphesi)"
                )
            elif consciousness_low and (red_flags >= 1 or yellow_flags >= 1):
                red_flags += 1
                rationale_parts.append(
                    "yüz ifadesi ajanı bilinç kaybı şüphesi bildirdi"
                )
            elif pain_high:
                # Ağrı tek başına sarı; başka anormallikle birleşirse kırmızı.
                if red_flags >= 1 or yellow_flags >= 1:
                    red_flags += 1
                    rationale_parts.append(
                        "yüz ifadesi ajanı belirgin ağrı bulguları bildirdi"
                    )
                else:
                    yellow_flags += 1
                    rationale_parts.append(
                        "yüz ifadesi ajanı ağrı şüphesi bildirdi"
                    )
            elif state == "distres" or pain >= 0.3:
                yellow_flags += 1
                rationale_parts.append(
                    "yüz ifadesi ajanı distres/rahatsızlık bildirdi"
                )

        # Termal ajan: proxy modunda destekleyici sinyal, tek başına kırmızıya çekmez.
        thermal = by_agent.get("thermal")
        if thermal and thermal["confidence"] >= 0.4:
            signals = thermal.get("signals", {})
            temp_c = float(signals.get("temp_estimate_c", 36.5))
            is_proxy = signals.get("sensor_type") == "rgb_proxy"
            if signals.get("hypothermia_flag") is True:
                # Hipotermi + başka anormallik birleşince kırmızı; tek başına sarı.
                if red_flags >= 1 or yellow_flags >= 1:
                    red_flags += 1
                else:
                    yellow_flags += 1
                rationale_parts.append(
                    f"termal ajan düşük sıcaklık şüphesi bildirdi (~{temp_c}°C)"
                )
            elif signals.get("fever_flag") is True:
                # Proxy modunda ateş tek başına sarı kabul edilir.
                yellow_flags += 1
                proxy_note = " [RGB proxy]" if is_proxy else ""
                rationale_parts.append(
                    f"termal ajan ateş şüphesi bildirdi (~{temp_c}°C){proxy_note}"
                )

        for name in missing:
            rationale_parts.append(f"{name} ajanı için veri yetersiz")

        if red_flags >= 2:
            category = "red"
        elif red_flags == 1 or yellow_flags >= 2:
            category = "yellow"
        elif yellow_flags == 1:
            category = "yellow"
        elif len(observations) == 0 or all(w < 0.5 for w in weights.values()):
            category = "insufficient"
        else:
            category = "green"

        if not rationale_parts:
            rationale_parts.append("Tüm ajanlar normal aralıkta sinyal raporladı")

        category_tr = {
            "red": "Kırmızı",
            "yellow": "Sarı",
            "green": "Yeşil",
            "insufficient": "Veri yetersiz",
        }[category]

        rationale = (
            ", ".join(rationale_parts).capitalize()
            + f". Önerilen triaj: {category_tr}."
        )

        valid_confidences = [w for w in weights.values() if w > 0]
        overall_confidence = (
            sum(valid_confidences) / len(valid_confidences) if valid_confidences else 0.0
        )

        return {
            "category": category,
            "rationale_tr": rationale,
            "confidence": round(overall_confidence, 2),
            "per_agent_weights": {k: round(v, 2) for k, v in weights.items()},
        }


def build_llm_client(settings: Settings | None = None) -> LLMClient:
    s = settings or get_settings()
    if s.llm_provider == "anthropic" and s.anthropic_api_key:
        return AnthropicClient(model=s.llm_model, api_key=s.anthropic_api_key)
    if s.llm_provider == "openai" and s.openai_api_key:
        return OpenAIClient(model=s.llm_model, api_key=s.openai_api_key)
    return MockLLMClient()


def _parse_json_lenient(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`").lstrip("json").strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start : end + 1])
        raise


def _extract_payload(user_message: str) -> dict:
    start = user_message.find("{")
    end = user_message.rfind("}")
    if start == -1 or end == -1:
        return {}
    return json.loads(user_message[start : end + 1])
