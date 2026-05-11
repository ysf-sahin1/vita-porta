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
            max_tokens=1024,
            system=system,
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
            for name in ("gait", "skin", "respiration")
        }

        red_flags = 0
        yellow_flags = 0
        rationale_parts: list[str] = []

        skin = by_agent.get("skin")
        if skin and skin["confidence"] >= 0.5:
            signals = skin.get("signals", {})
            if signals.get("pallor") is True or signals.get("severity") == "high":
                red_flags += 1
                rationale_parts.append(
                    f"Ten rengi ajanı %{int(skin['confidence']*100)} güvenle solgunluk tespit etti"
                )
            elif signals.get("severity") == "mild":
                yellow_flags += 1
                rationale_parts.append("Ten rengi ajanı hafif solgunluk tespit etti")

        resp = by_agent.get("respiration")
        if resp and resp["confidence"] >= 0.5:
            signals = resp.get("signals", {})
            rate = float(signals.get("rate_bpm", 0))
            if rate >= 24 or signals.get("severity") == "high":
                red_flags += 1
                rationale_parts.append(
                    f"solunum ajanı %{int(resp['confidence']*100)} güvenle hızlı solunum bildirdi"
                )
            elif rate >= 20 or signals.get("severity") == "mild":
                yellow_flags += 1
                rationale_parts.append("solunum ajanı hafif hızlanma bildirdi")

        gait = by_agent.get("gait")
        if gait and gait["confidence"] >= 0.5:
            signals = gait.get("signals", {})
            if signals.get("sway") is True or signals.get("severity") == "high":
                yellow_flags += 1
                rationale_parts.append(
                    f"yürüyüş ajanı %{int(gait['confidence']*100)} güvenle sallantılı yürüyüş tespit etti"
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
