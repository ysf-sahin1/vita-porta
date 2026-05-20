"""Runner orchestrator tests.

The runner is exercised with a synthetic in-memory frame source and a
monkeypatched ``httpx.Client.post`` — no real backend, no real camera.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import numpy as np
import pytest

from gateway_agents.agents.base import AnalysisWindow
from gateway_agents.io.base import FrameSource
from gateway_agents.runner import Runner
from orchestration.schemas import AgentBundle, AgentObservation


class _StubAgent:
    """Deterministic stub — Runner pipeline'ı test ederken gerçek ajan
    çıkarımına bağlanmadan istediğimiz güveni dönerek bundle akışını izole
    eder. Random frame'lerde gerçek mediapipe pose/face tutarsız güvenle
    döner; bu da meaningful-bundle gate testlerini kırılgan yapar."""

    def __init__(self, name: str, confidence: float = 0.7) -> None:
        self.name = name
        self._conf = confidence

    def analyze(self, window: AnalysisWindow) -> AgentObservation:
        return AgentObservation(
            agent=self.name,  # type: ignore[arg-type]
            confidence=self._conf,
            summary_tr=f"{self.name} stub gözlemi",
            signals={},
        )

    def close(self) -> None:
        return None


def _patch_agents(runner: Runner, confidence: float = 0.7) -> None:
    """Replace the runner's real agents with deterministic stubs."""
    runner._gait = _StubAgent("gait", confidence)         # type: ignore[assignment]
    runner._thermal = _StubAgent("thermal", confidence)   # type: ignore[assignment]
    runner._expression = _StubAgent("expression", confidence)  # type: ignore[assignment]


class FakeFrameSource(FrameSource):
    """Yields ``count`` synthetic BGR frames at the configured ``fps``."""

    def __init__(
        self,
        count: int,
        fps: float = 15.0,
        h: int = 240,
        w: int = 320,
        seed: int = 0,
    ) -> None:
        self.fps = float(fps)
        self._count = count
        self._h = h
        self._w = w
        self._seed = seed
        self.closed = False

    def frames(self) -> Iterator[np.ndarray]:
        rng = np.random.default_rng(self._seed)
        for _ in range(self._count):
            yield rng.integers(0, 256, (self._h, self._w, 3), dtype=np.uint8)

    def close(self) -> None:
        self.closed = True


class _CapturingResponse:
    def __init__(self, json_body: dict[str, Any]) -> None:
        self._json = json_body
        self.text = ""
        self.status_code = 200

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, Any]:
        return self._json


@pytest.fixture
def capture_post(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, Any]]:
    """Replace ``httpx.Client.post`` with a recorder, return the captured calls."""

    import httpx

    captured: list[dict[str, Any]] = []

    def fake_post(
        self: httpx.Client,
        url: str,
        *,
        json: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> _CapturingResponse:
        captured.append({"url": url, "json": json, "kwargs": kwargs})
        return _CapturingResponse(
            {
                "patient_id": (json or {}).get("patient_id", "test"),
                "category": "green",
                "label_tr": "Yeşil — Düşük öncelik",
                "rationale_tr": "Sentetik test",
                "confidence": 0.42,
            }
        )

    monkeypatch.setattr(httpx.Client, "post", fake_post)
    return captured


def test_run_once_returns_bundle_with_three_observations(
    capture_post: list[dict[str, Any]],
) -> None:
    source = FakeFrameSource(count=60, fps=15.0)
    with Runner(source=source, window_duration_s=3.0) as runner:
        _patch_agents(runner)
        bundle = runner.run_once()

    assert isinstance(bundle, AgentBundle)
    assert bundle.gait is not None
    assert bundle.thermal is not None
    assert bundle.expression is not None
    assert len(bundle.observations()) == 3

    assert len(capture_post) == 1
    call = capture_post[0]
    assert call["url"].endswith("/api/triage/run")
    payload = call["json"]
    assert isinstance(payload, dict)
    for name in ("gait", "thermal", "expression"):
        assert name in payload
        assert payload[name]["agent"] == name


def test_run_once_returns_none_when_source_empty(
    capture_post: list[dict[str, Any]],
) -> None:
    source = FakeFrameSource(count=0, fps=15.0)
    with Runner(source=source) as runner:
        _patch_agents(runner)
        result = runner.run_once()
    assert result is None
    assert capture_post == []


def test_partial_window_still_produces_bundle(
    capture_post: list[dict[str, Any]],
) -> None:
    # Window target is fps * 3 = 45 frames; we provide 10 — runner should
    # take what is available and still produce a bundle (≥1 frame).
    source = FakeFrameSource(count=10, fps=15.0)
    with Runner(source=source, window_duration_s=3.0) as runner:
        _patch_agents(runner)
        bundle = runner.run_once()

    assert isinstance(bundle, AgentBundle)
    assert len(bundle.observations()) == 3
    assert len(capture_post) == 1


def test_backend_unreachable_does_not_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    def raising_post(*args: Any, **kwargs: Any):
        raise httpx.ConnectError("backend down")

    monkeypatch.setattr(httpx.Client, "post", raising_post)

    source = FakeFrameSource(count=45, fps=15.0)
    with Runner(source=source) as runner:
        # Must not raise even though POST fails — runner logs a warning.
        _patch_agents(runner)
        bundle = runner.run_once()

    assert isinstance(bundle, AgentBundle)


def test_close_releases_source() -> None:
    source = FakeFrameSource(count=0, fps=15.0)
    runner = Runner(source=source)
    runner.close()
    assert source.closed is True


def test_context_manager_closes(monkeypatch: pytest.MonkeyPatch) -> None:
    import httpx

    def fake_post(self: httpx.Client, url: str, **kwargs: Any) -> _CapturingResponse:
        return _CapturingResponse({"category": "green", "rationale_tr": "", "confidence": 0.1})

    monkeypatch.setattr(httpx.Client, "post", fake_post)

    source = FakeFrameSource(count=45, fps=15.0)
    with Runner(source=source) as runner:
        assert isinstance(runner, Runner)
    assert source.closed is True


def test_esp_host_triggers_verdict_callback(
    monkeypatch: pytest.MonkeyPatch,
    capture_post: list[dict[str, Any]],
) -> None:
    """esp_host verildiğinde supervisor verdict'i ESP'ye GET ile bildirilir."""

    import httpx

    captured_gets: list[dict[str, Any]] = []

    def fake_get(
        self: httpx.Client,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> _CapturingResponse:
        captured_gets.append({"url": url, "params": params})
        return _CapturingResponse({"ok": True})

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    source = FakeFrameSource(count=45, fps=15.0)
    with Runner(source=source, esp_host="192.168.1.42") as runner:
        _patch_agents(runner)
        runner.run_once()

    # Backend POST hâlâ yapılmalı
    assert len(capture_post) == 1
    # ESP /verdict GET çağrısı yapılmış olmalı
    verdict_calls = [g for g in captured_gets if "/verdict" in g["url"]]
    assert len(verdict_calls) == 1
    call = verdict_calls[0]
    assert call["url"] == "http://192.168.1.42:80/verdict"
    assert call["params"] == {"level": "green", "src": "supervisor"}


def test_esp_verdict_failure_does_not_crash(
    monkeypatch: pytest.MonkeyPatch,
    capture_post: list[dict[str, Any]],
) -> None:
    """ESP /verdict çağrısı çökse bile runner devam etmeli (best-effort)."""

    import httpx

    def raising_get(*args: Any, **kwargs: Any) -> _CapturingResponse:
        raise httpx.ConnectError("esp offline")

    monkeypatch.setattr(httpx.Client, "get", raising_get)

    source = FakeFrameSource(count=45, fps=15.0)
    with Runner(source=source, esp_host="192.168.1.42") as runner:
        _patch_agents(runner)
        bundle = runner.run_once()

    assert bundle is not None
    assert len(capture_post) == 1  # backend POST yine yapıldı


def test_no_esp_host_skips_verdict_callback(
    monkeypatch: pytest.MonkeyPatch,
    capture_post: list[dict[str, Any]],
) -> None:
    """esp_host=None iken /verdict çağrısı **hiç** yapılmamalı."""

    import httpx

    captured_gets: list[dict[str, Any]] = []

    def fake_get(self: httpx.Client, url: str, **kwargs: Any) -> _CapturingResponse:
        captured_gets.append({"url": url})
        return _CapturingResponse({"ok": True})

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    source = FakeFrameSource(count=45, fps=15.0)
    with Runner(source=source) as runner:
        _patch_agents(runner)
        runner.run_once()

    assert captured_gets == []
    assert len(capture_post) == 1


# ----------------------------------------------- meaningful-bundle gate testleri


def test_low_confidence_bundle_is_not_posted(
    capture_post: list[dict[str, Any]],
) -> None:
    """Tüm ajan güveni 0.3 eşiğinin altındaysa backend'e POST atılmamalı."""

    source = FakeFrameSource(count=45, fps=15.0)
    with Runner(source=source) as runner:
        _patch_agents(runner, confidence=0.1)  # eşik altı
        bundle = runner.run_once()

    assert bundle is not None  # bundle yine üretildi (debug erişimi için)
    assert capture_post == []  # ama backend'e gitmedi


def test_meaningful_bundle_is_posted(
    capture_post: list[dict[str, Any]],
) -> None:
    """En az bir ajan eşiği geçtiğinde bundle gönderilmeli."""

    source = FakeFrameSource(count=45, fps=15.0)
    with Runner(source=source) as runner:
        _patch_agents(runner, confidence=0.4)
        bundle = runner.run_once()

    assert bundle is not None
    assert len(capture_post) == 1


def test_low_confidence_bundle_skips_verdict_callback(
    monkeypatch: pytest.MonkeyPatch,
    capture_post: list[dict[str, Any]],
) -> None:
    """Bundle atlanırsa ESP /verdict de tetiklenmemeli (POST yapılmadığı için)."""

    import httpx

    captured_gets: list[dict[str, Any]] = []

    def fake_get(self: httpx.Client, url: str, **kwargs: Any) -> _CapturingResponse:
        captured_gets.append({"url": url})
        return _CapturingResponse({"ok": True})

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    source = FakeFrameSource(count=45, fps=15.0)
    with Runner(source=source, esp_host="192.168.1.42") as runner:
        _patch_agents(runner, confidence=0.1)
        runner.run_once()

    assert capture_post == []
    verdict_calls = [g for g in captured_gets if "/verdict" in g["url"]]
    assert verdict_calls == []
