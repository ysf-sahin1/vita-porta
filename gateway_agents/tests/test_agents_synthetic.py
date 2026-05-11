"""Sentetik frame'lerle ajan testleri.

Bu testler gerçek kamera olmadan ajan logic'inin import edilebildiğini ve
boş/yetersiz girdilere zarif şekilde tepki verdiğini doğrular. Gerçek
modaliteye özgü davranış testi (örn. sallanan figür → yüksek sway_score)
fixture videolarıyla ayrıca yapılır.
"""

from __future__ import annotations

import numpy as np
import pytest

from gateway_agents.agents.base import AnalysisWindow


def _blank_window(frames: int = 30, h: int = 240, w: int = 320) -> AnalysisWindow:
    frames_list = [np.zeros((h, w, 3), dtype=np.uint8) for _ in range(frames)]
    return AnalysisWindow(frames=frames_list, fps=15.0)


def _noisy_window(frames: int = 30, h: int = 240, w: int = 320) -> AnalysisWindow:
    rng = np.random.default_rng(seed=42)
    frames_list = [rng.integers(0, 256, (h, w, 3), dtype=np.uint8) for _ in range(frames)]
    return AnalysisWindow(frames=frames_list, fps=15.0)


@pytest.fixture
def blank_window() -> AnalysisWindow:
    return _blank_window()


@pytest.fixture
def noisy_window() -> AnalysisWindow:
    return _noisy_window()


def test_skin_agent_blank_frame_returns_observation(blank_window: AnalysisWindow) -> None:
    cv2 = pytest.importorskip("cv2")
    from gateway_agents.agents.skin import SkinAgent

    agent = SkinAgent()
    obs = agent.analyze(blank_window)
    assert obs.agent == "skin"
    assert 0.0 <= obs.confidence <= 1.0
    # Tamamen siyah frame → çok yüksek pallor beklenir (saturation 0)
    assert obs.signals["pallor_score"] >= 0.5


def test_respiration_agent_blank_frame_classifies_as_apnea(
    blank_window: AnalysisWindow,
) -> None:
    pytest.importorskip("cv2")
    from gateway_agents.agents.respiration import RespirationAgent

    agent = RespirationAgent()
    obs = agent.analyze(blank_window)
    assert obs.agent == "respiration"
    assert obs.signals["pattern"] == "apne_riski"
    assert obs.signals["motion_score"] < 0.05


def test_respiration_agent_noisy_frame_detects_motion(noisy_window: AnalysisWindow) -> None:
    pytest.importorskip("cv2")
    from gateway_agents.agents.respiration import RespirationAgent

    agent = RespirationAgent()
    obs = agent.analyze(noisy_window)
    assert obs.signals["motion_score"] > 0.5  # rastgele gürültü = belirgin hareket


def test_gait_agent_blank_frame_returns_insufficient(blank_window: AnalysisWindow) -> None:
    pytest.importorskip("mediapipe")
    from gateway_agents.agents.gait import GaitAgent

    agent = GaitAgent()
    obs = agent.analyze(blank_window)
    assert obs.agent == "gait"
    # Siyah frame'de pose tespit edilmez → 0 confidence
    assert obs.confidence == 0.0
    assert obs.signals.get("detection_ratio") == 0.0


def test_empty_window_skin() -> None:
    pytest.importorskip("cv2")
    from gateway_agents.agents.skin import SkinAgent

    agent = SkinAgent()
    obs = agent.analyze(AnalysisWindow(frames=[], fps=15.0))
    assert obs.confidence == 0.0
    assert "yetersiz" in obs.summary_tr.lower()


def test_empty_window_respiration() -> None:
    pytest.importorskip("cv2")
    from gateway_agents.agents.respiration import RespirationAgent

    agent = RespirationAgent()
    obs = agent.analyze(AnalysisWindow(frames=[], fps=15.0))
    assert obs.confidence == 0.0
    assert "yetersiz" in obs.summary_tr.lower()
