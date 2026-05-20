"""Synthetic-frame unit tests for the three visual agents.

No real camera, no real video, no network. Frames are constructed with numpy
so the tests run on any machine, on CI included.
"""

from __future__ import annotations

import numpy as np
import pytest

from gateway_agents.agents.base import AnalysisWindow
from orchestration.schemas import AgentObservation

# Lazily imported per-agent so a missing optional dep skips just one bucket.
cv2 = pytest.importorskip("cv2")


# ----------------------------------------------------------------- fixtures


def _black_frames(n: int, h: int = 240, w: int = 320) -> list[np.ndarray]:
    return [np.zeros((h, w, 3), dtype=np.uint8) for _ in range(n)]


def _solid_color_frames(
    n: int, color: tuple[int, int, int] = (128, 128, 128), h: int = 240, w: int = 320
) -> list[np.ndarray]:
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    frame[:, :] = color
    return [frame.copy() for _ in range(n)]


@pytest.fixture
def empty_window() -> AnalysisWindow:
    return AnalysisWindow(frames=[], fps=15.0)


@pytest.fixture
def black_window() -> AnalysisWindow:
    return AnalysisWindow(frames=_black_frames(30), fps=15.0)


@pytest.fixture
def static_gray_window() -> AnalysisWindow:
    return AnalysisWindow(frames=_solid_color_frames(45, color=(128, 128, 128)), fps=15.0)


# =============================================================== GaitAgent


class TestGaitAgent:
    def _agent(self):
        pytest.importorskip("mediapipe")
        from gateway_agents.agents.gait import GaitAgent

        return GaitAgent()

    def test_empty_window_returns_zero_confidence(self, empty_window: AnalysisWindow) -> None:
        agent = self._agent()
        try:
            obs = agent.analyze(empty_window)
        finally:
            agent.close()
        assert obs.agent == "gait"
        assert obs.confidence == 0.0

    def test_black_frames_yield_low_confidence(self, black_window: AnalysisWindow) -> None:
        agent = self._agent()
        try:
            obs = agent.analyze(black_window)
        finally:
            agent.close()
        assert obs.agent == "gait"
        assert obs.confidence < 0.5

    def test_random_frames_do_not_crash(self) -> None:
        agent = self._agent()
        rng = np.random.default_rng(seed=0)
        frames = [rng.integers(0, 256, (240, 320, 3), dtype=np.uint8) for _ in range(30)]
        try:
            obs = agent.analyze(AnalysisWindow(frames=frames, fps=15.0))
        finally:
            agent.close()
        assert obs.agent == "gait"
        assert 0.0 <= obs.confidence <= 1.0


# =========================================================== ExpressionAgent


class TestExpressionAgent:
    def _agent(self):
        pytest.importorskip("mediapipe")
        from gateway_agents.agents.expression import ExpressionAgent

        return ExpressionAgent()

    def test_empty_window_returns_zero_confidence(self, empty_window: AnalysisWindow) -> None:
        agent = self._agent()
        try:
            obs = agent.analyze(empty_window)
        finally:
            agent.close()
        assert obs.agent == "expression"
        assert obs.confidence == 0.0
        # Insufficient path: belirsiz sınıf + sıfır pain.
        assert obs.signals["expression_state"] == "belirsiz"
        assert obs.signals["pain_score"] == 0.0

    def test_black_frames_yield_low_confidence(self, black_window: AnalysisWindow) -> None:
        agent = self._agent()
        try:
            obs = agent.analyze(black_window)
        finally:
            agent.close()
        assert obs.agent == "expression"
        # Siyah karelerde yüz mesh tespit edilemez → düşük güven.
        assert obs.confidence < 0.5

    def test_random_frames_do_not_crash(self) -> None:
        agent = self._agent()
        rng = np.random.default_rng(seed=0)
        frames = [rng.integers(0, 256, (240, 320, 3), dtype=np.uint8) for _ in range(30)]
        try:
            obs = agent.analyze(AnalysisWindow(frames=frames, fps=15.0))
        finally:
            agent.close()
        assert obs.agent == "expression"
        assert 0.0 <= obs.confidence <= 0.55  # proxy modu üst sınırı
        # Schema'da olması gereken anahtarlar her yolda mevcut olmalı.
        expected = {
            "expression_state",
            "pain_score",
            "eye_openness",
            "face_asymmetry",
            "consciousness_hint",
            "face_detected_ratio",
            "sensor_type",
        }
        assert expected.issubset(obs.signals.keys())


# ===================================================== Schema conformance


def _gait_obs() -> AgentObservation:
    pytest.importorskip("mediapipe")
    from gateway_agents.agents.gait import GaitAgent

    agent = GaitAgent()
    try:
        return agent.analyze(AnalysisWindow(frames=_black_frames(15), fps=15.0))
    finally:
        agent.close()


def _expression_obs() -> AgentObservation:
    pytest.importorskip("mediapipe")
    from gateway_agents.agents.expression import ExpressionAgent

    agent = ExpressionAgent()
    try:
        return agent.analyze(AnalysisWindow(frames=_black_frames(15), fps=15.0))
    finally:
        agent.close()


@pytest.mark.parametrize(
    "factory,expected_name",
    [
        (_gait_obs, "gait"),
        (_expression_obs, "expression"),
    ],
)
def test_observation_schema_conformance(factory, expected_name: str) -> None:
    obs = factory()
    assert obs.agent == expected_name
    assert 0.0 <= obs.confidence <= 1.0
    assert obs.summary_tr and obs.summary_tr.strip()
    assert isinstance(obs.signals, dict)
