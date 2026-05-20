"""Runner orchestrator tests.

The runner is exercised with a synthetic in-memory frame source and a
monkeypatched ``httpx.Client.post`` — no real backend, no real camera.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import numpy as np
import pytest

from gateway_agents.io.base import FrameSource
from gateway_agents.runner import Runner
from orchestration.schemas import AgentBundle


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
