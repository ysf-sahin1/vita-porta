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


def _periodic_motion_frames(
    n: int,
    period: int,
    h: int = 240,
    w: int = 320,
    bright: int = 220,
    dim: int = 30,
) -> list[np.ndarray]:
    """Frames with a small rectangle in the chest-ROI alternating brightness.

    ``period`` is the number of frames per full bright/dim cycle.
    A period of 2 means flipping every frame (~fps/2 Hz at fps frame rate).
    """

    frames: list[np.ndarray] = []
    half = max(1, period // 2)
    # Chest ROI used by RespirationAgent is roughly the center rectangle:
    # x in [0.30w, 0.70w], y in [0.30h, 0.60h]. Put the patch in the middle.
    cx0, cx1 = int(w * 0.45), int(w * 0.55)
    cy0, cy1 = int(h * 0.40), int(h * 0.50)
    for i in range(n):
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        value = bright if (i // half) % 2 == 0 else dim
        frame[cy0:cy1, cx0:cx1] = value
        frames.append(frame)
    return frames


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


# =============================================================== SkinAgent


class TestSkinAgent:
    def _agent(self):
        from gateway_agents.agents.skin import SkinAgent

        return SkinAgent()

    def test_empty_window_returns_low_confidence(self, empty_window: AnalysisWindow) -> None:
        agent = self._agent()
        obs = agent.analyze(empty_window)
        assert obs.agent == "skin"
        assert obs.confidence < 0.5

    def test_solid_color_no_face_low_confidence(self, static_gray_window: AnalysisWindow) -> None:
        agent = self._agent()
        obs = agent.analyze(static_gray_window)
        assert obs.agent == "skin"
        # Without a face the agent should report near-zero confidence.
        assert obs.confidence < 0.1
        # And surface "belirsiz" since it could not measure skin tone.
        assert obs.signals.get("skin_tone", "belirsiz") == "belirsiz"

    def test_signal_keys_present_with_face_detection_path(self) -> None:
        """If a face *were* detected, expected signal keys are present.

        We exercise the agent and verify either the insufficient-data path
        (empty signals) or the populated path advertises the right keys.
        """

        agent = self._agent()
        obs = agent.analyze(AnalysisWindow(frames=_solid_color_frames(30), fps=15.0))
        if obs.signals:
            expected = {"skin_tone", "color_variance", "mean_saturation", "face_detected_ratio"}
            assert expected.issubset(obs.signals.keys())


# ============================================================ RespirationAgent


class TestRespirationAgent:
    def _agent(self):
        from gateway_agents.agents.respiration import RespirationAgent

        return RespirationAgent()

    def test_empty_window_returns_zero_confidence(self, empty_window: AnalysisWindow) -> None:
        agent = self._agent()
        obs = agent.analyze(empty_window)
        assert obs.agent == "respiration"
        assert obs.confidence == 0.0

    def test_static_frames_have_no_motion(self, static_gray_window: AnalysisWindow) -> None:
        agent = self._agent()
        obs = agent.analyze(static_gray_window)
        assert obs.agent == "respiration"
        if obs.signals:
            # Static frames → essentially no inter-frame motion.
            intensity = float(obs.signals.get("movement_intensity", 0.0))
            assert intensity == pytest.approx(0.0, abs=1e-3)
            bpm = float(obs.signals.get("breaths_per_minute", 0.0))
            assert bpm == pytest.approx(0.0, abs=1e-3)

    def test_periodic_motion_yields_nonzero_bpm(self) -> None:
        agent = self._agent()

        # High-frequency flipping (every frame) registers as continuous motion
        # but does not produce distinct peaks — verify motion is detected.
        fast = _periodic_motion_frames(n=45, period=2)
        obs_fast = agent.analyze(AnalysisWindow(frames=fast, fps=15.0))
        assert obs_fast.agent == "respiration"
        assert obs_fast.signals, "Hareketli pencere için signals dolu olmalı"
        assert float(obs_fast.signals.get("movement_intensity", 0.0)) > 0.0

        # Slower flipping (every 2 frames at 15 fps) produces distinct,
        # well-separated motion peaks → nonzero BPM.
        slow = _periodic_motion_frames(n=45, period=4)
        obs_slow = agent.analyze(AnalysisWindow(frames=slow, fps=15.0))
        assert obs_slow.agent == "respiration"
        assert obs_slow.signals
        slow_bpm = float(obs_slow.signals.get("breaths_per_minute", 0.0))
        assert float(obs_slow.signals.get("movement_intensity", 0.0)) > 0.0
        assert slow_bpm > 0.0


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


def _skin_obs() -> AgentObservation:
    from gateway_agents.agents.skin import SkinAgent

    return SkinAgent().analyze(AnalysisWindow(frames=_solid_color_frames(15), fps=15.0))


def _respiration_obs() -> AgentObservation:
    from gateway_agents.agents.respiration import RespirationAgent

    frames = _periodic_motion_frames(n=30, period=4)
    return RespirationAgent().analyze(AnalysisWindow(frames=frames, fps=15.0))


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
        (_skin_obs, "skin"),
        (_respiration_obs, "respiration"),
        (_expression_obs, "expression"),
    ],
)
def test_observation_schema_conformance(factory, expected_name: str) -> None:
    obs = factory()
    assert obs.agent == expected_name
    assert 0.0 <= obs.confidence <= 1.0
    assert obs.summary_tr and obs.summary_tr.strip()
    assert isinstance(obs.signals, dict)
