"""Synthetic-frame unit tests for the three visual agents.

No real camera, no real video, no network. Frames are constructed with numpy
so the tests run on any machine, on CI included.
"""

from __future__ import annotations

from typing import Any

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


# ============================================================ ThermalAgent
#
# ThermalAgent iki kod yolunda çalışır:
#   1. ESP /thermal AMG8833 (esp_host verildiğinde) — ham sayı, etiket yok
#   2. RGB proxy (esp_host=None veya ESP erişilemez) — LAB renk uzayı tahmini
#
# Schema sözleşmesi her iki yolda da aynı olmalı: confidence ∈ [0,1],
# summary_tr dolu, signals zorunlu anahtarları içermeli.


class TestThermalAgent:
    _REQUIRED_SIGNALS = {
        "temp_estimate_c",
        "fever_flag",
        "hypothermia_flag",
        "sensor_type",
        "data_source",
    }

    def _agent(self, esp_host: str | None = None):
        from gateway_agents.agents.thermal import ThermalAgent

        return ThermalAgent(esp_host=esp_host)

    # --- RGB proxy yolu (esp_host=None) ---

    def test_proxy_mode_empty_window(self, empty_window: AnalysisWindow) -> None:
        agent = self._agent()
        try:
            obs = agent.analyze(empty_window)
        finally:
            agent.close()
        assert obs.agent == "thermal"
        assert obs.confidence == 0.0
        assert self._REQUIRED_SIGNALS.issubset(obs.signals.keys())
        assert obs.signals["sensor_type"] == "rgb_proxy"

    def test_proxy_mode_random_frames(self) -> None:
        agent = self._agent()
        rng = np.random.default_rng(seed=0)
        frames = [rng.integers(0, 256, (240, 320, 3), dtype=np.uint8) for _ in range(30)]
        try:
            obs = agent.analyze(AnalysisWindow(frames=frames, fps=15.0))
        finally:
            agent.close()
        assert obs.agent == "thermal"
        assert 0.0 <= obs.confidence <= 0.60  # RGB proxy üst sınırı
        assert obs.signals["sensor_type"] == "rgb_proxy"

    # --- AMG8833 yolu: politika "DAİMA last_confirmed yolla" ---

    @staticmethod
    def _mock_esp(monkeypatch: pytest.MonkeyPatch, payload: dict[str, Any]) -> None:
        import httpx

        def fake_get(self: httpx.Client, url: str, **kwargs: Any) -> Any:
            class _R:
                status_code = 200

                def raise_for_status(self) -> None:
                    return None

                def json(self) -> dict[str, Any]:
                    return payload

            return _R()

        monkeypatch.setattr(httpx.Client, "get", fake_get)

    def test_esp_fresh_confirmed_used_directly(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Anlık HIGH + taze last_confirmed → o değer yollanır, sensor_type=amg8833."""

        self._mock_esp(
            monkeypatch,
            {
                "ok": True,
                "person_present": True,
                "ambient": 24.5,
                # Anlık ölçüm de geliyor ama gateway artık BAKMIYOR — kaynak last_confirmed
                "skin_temp": 36.9,
                "confidence": {"level": 3, "label": "yuksek"},
                "distance": {"estimate_cm": 17.0},
                "quality": {"score": 0.84},
                "last_confirmed": {
                    "set": True,
                    "skin_temp": 36.8,
                    "distance_cm": 17.0,
                    "quality": 0.84,
                    "conf": 3,
                    "age_ms": 200,  # tazecik
                },
                "gate": {"reason": "open"},
            },
        )

        agent = self._agent(esp_host="192.168.1.42")
        try:
            obs = agent.analyze(AnalysisWindow(frames=[], fps=15.0))
        finally:
            agent.close()

        assert obs.agent == "thermal"
        assert obs.confidence == 0.95  # HIGH + age<5s → tam
        # Gateway anlık 36.9'a değil last_confirmed 36.8'e bakmalı
        assert obs.signals["temp_estimate_c"] == 36.8
        assert obs.signals["sensor_type"] == "amg8833"
        assert obs.signals["data_source"] == "last_confirmed"
        assert obs.signals["measurement_age_s"] == 0.2
        assert obs.signals["fever_flag"] is False
        assert obs.signals["hypothermia_flag"] is False

    def test_esp_low_confidence_still_returns_last_confirmed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Anlık LOW (alın gitti) olsa bile en son emin değer yollanmaya devam eder."""

        self._mock_esp(
            monkeypatch,
            {
                "ok": True,
                "person_present": False,
                "ambient": 23.0,
                "skin_temp": 0.0,
                "confidence": {"level": 1, "label": "dusuk"},
                "distance": {"estimate_cm": 0.0},
                "quality": {"score": 0.0},
                "last_confirmed": {
                    "set": True,
                    "skin_temp": 38.4,  # ateş eşiği üstü
                    "distance_cm": 18.0,
                    "quality": 0.78,
                    "conf": 3,
                    "age_ms": 1500,
                },
                "gate": {"reason": "stabilite_bekleniyor"},
            },
        )

        agent = self._agent(esp_host="192.168.1.42")
        try:
            obs = agent.analyze(AnalysisWindow(frames=[], fps=15.0))
        finally:
            agent.close()

        assert obs.signals["sensor_type"] == "amg8833"
        assert obs.signals["data_source"] == "last_confirmed"
        assert obs.signals["temp_estimate_c"] == 38.4
        assert obs.signals["fever_flag"] is True
        assert obs.confidence == 0.95  # age 1.5s < 5s → ceza yok

    def test_esp_no_confirmed_yet_returns_waiting(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Henüz hiç emin ölçüm gelmemişse boş gözlem dönmeli (flicker yok)."""

        self._mock_esp(
            monkeypatch,
            {
                "ok": True,
                "person_present": False,
                "ambient": 23.0,
                "skin_temp": 0.0,
                "confidence": {"level": 0, "label": "yok"},
                "distance": {"estimate_cm": 0.0},
                "quality": {"score": 0.0},
                "last_confirmed": {"set": False},
                "gate": {"reason": "ortam_soguk"},
            },
        )

        agent = self._agent(esp_host="192.168.1.42")
        try:
            obs = agent.analyze(AnalysisWindow(frames=[], fps=15.0))
        finally:
            agent.close()

        assert obs.confidence == 0.0
        assert obs.signals["temp_estimate_c"] == 0.0
        assert obs.signals["data_source"] == "waiting"
        assert obs.signals["fever_flag"] is False

    def test_esp_stale_confirmed_gets_penalty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Çok eski last_confirmed (30s+) → değer yine yollanır ama confidence düşer."""

        self._mock_esp(
            monkeypatch,
            {
                "ok": True,
                "person_present": False,
                "ambient": 24.0,
                "confidence": {"level": 0, "label": "yok"},
                "last_confirmed": {
                    "set": True,
                    "skin_temp": 36.6,
                    "distance_cm": 16.0,
                    "quality": 0.80,
                    "conf": 3,
                    "age_ms": 45_000,  # 45 saniye eski
                },
                "gate": {"reason": "kimse_yok"},
            },
        )

        agent = self._agent(esp_host="192.168.1.42")
        try:
            obs = agent.analyze(AnalysisWindow(frames=[], fps=15.0))
        finally:
            agent.close()

        assert obs.signals["temp_estimate_c"] == 36.6
        assert obs.signals["data_source"] == "last_confirmed"
        # 0.95 * 0.70 = 0.665 → stale cezası
        assert obs.confidence < 0.80
        assert obs.confidence >= 0.30

    def test_esp_unreachable_falls_back_to_proxy(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """ESP'ye ulaşılamazsa RGB proxy'ye sessizce düşülür."""

        import httpx

        def raising_get(*args: Any, **kwargs: Any):
            raise httpx.ConnectError("esp offline")

        monkeypatch.setattr(httpx.Client, "get", raising_get)

        agent = self._agent(esp_host="192.168.1.42")
        rng = np.random.default_rng(seed=0)
        frames = [rng.integers(0, 256, (240, 320, 3), dtype=np.uint8) for _ in range(15)]
        try:
            obs = agent.analyze(AnalysisWindow(frames=frames, fps=15.0))
        finally:
            agent.close()

        # ESP düştü → RGB proxy üst sınırına uymalı
        assert obs.signals["sensor_type"] == "rgb_proxy"
        assert obs.confidence <= 0.60


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
