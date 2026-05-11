"""Yürüyüş ajanı — MediaPipe Pose ile postür, simetri ve sallanma analizi.

Çıktı sinyalleri:
    sway_score       0..1   — gövde yatay salınımı (yüksek = dengesiz)
    symmetry_score   0..1   — omuz/kalça yükseklik simetrisi (1 = mükemmel)
    posture_score    0..1   — dik duruş (1 = dik, 0 = yere yığılmış)
    detection_ratio  0..1   — kaç frame'de pose tespit edildi
"""

from __future__ import annotations

import logging

import numpy as np

from gateway_agents.agents.base import Agent, AnalysisWindow
from orchestration.schemas import AgentObservation

logger = logging.getLogger(__name__)

try:
    import mediapipe as mp

    _POSE_AVAILABLE = True
except ImportError:
    mp = None  # type: ignore[assignment]
    _POSE_AVAILABLE = False


_LM = None
if _POSE_AVAILABLE:
    _LM = mp.solutions.pose.PoseLandmark


class GaitAgent(Agent):
    name = "gait"

    def __init__(self, min_detection_confidence: float = 0.5) -> None:
        if not _POSE_AVAILABLE:
            raise RuntimeError(
                "mediapipe yüklü değil. `pip install mediapipe` ile kur."
            )
        self._pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=0.5,
        )

    def analyze(self, window: AnalysisWindow) -> AgentObservation:
        if not window.frames:
            return _insufficient("Görüntü alınamadı.")

        # Per-frame landmark dizileri
        nose_xs: list[float] = []
        shoulder_dys: list[float] = []  # |left.y - right.y|
        hip_dys: list[float] = []
        shoulder_hip_ys: list[float] = []  # avg shoulder - avg hip (yükseklik farkı)
        detections = 0

        for frame in window.frames:
            # MediaPipe RGB bekler, OpenCV BGR verir
            rgb = frame[:, :, ::-1] if frame.ndim == 3 else frame
            result = self._pose.process(rgb)
            if not result.pose_landmarks:
                continue
            detections += 1
            lm = result.pose_landmarks.landmark
            nose_xs.append(lm[_LM.NOSE.value].x)
            ls = lm[_LM.LEFT_SHOULDER.value]
            rs = lm[_LM.RIGHT_SHOULDER.value]
            lh = lm[_LM.LEFT_HIP.value]
            rh = lm[_LM.RIGHT_HIP.value]
            shoulder_dys.append(abs(ls.y - rs.y))
            hip_dys.append(abs(lh.y - rh.y))
            shoulder_hip_ys.append(((ls.y + rs.y) / 2.0) - ((lh.y + rh.y) / 2.0))

        if detections == 0:
            return _insufficient("Pose tespit edilemedi.")

        detection_ratio = detections / len(window.frames)

        # Sway: nose x'in std'i (normalize coord, 0..1) — 0.04 üstü belirgin
        sway_raw = float(np.std(nose_xs)) if len(nose_xs) > 1 else 0.0
        sway_score = float(min(1.0, sway_raw / 0.05))

        # Symmetry: omuz/kalça ortalaması düşükse simetri yüksek
        asym = (np.mean(shoulder_dys) + np.mean(hip_dys)) / 2.0
        symmetry_score = float(max(0.0, 1.0 - asym / 0.08))

        # Posture: ortalama (omuz_y - kalça_y) negatif olmalı (omuz üstte).
        # Negatif değer ne kadar büyük (mutlak) → o kadar dik. Eşik: -0.15 → 1.0
        sh_diff = float(np.mean(shoulder_hip_ys))
        if sh_diff >= 0:
            posture_score = 0.0
        else:
            posture_score = float(min(1.0, abs(sh_diff) / 0.15))

        confidence = float(min(1.0, detection_ratio * 1.1))

        summary_tr = _build_summary(sway_score, symmetry_score, posture_score)

        return AgentObservation(
            agent="gait",
            confidence=confidence,
            summary_tr=summary_tr,
            signals={
                "sway_score": round(sway_score, 3),
                "symmetry_score": round(symmetry_score, 3),
                "posture_score": round(posture_score, 3),
                "detection_ratio": round(detection_ratio, 3),
            },
        )

    def close(self) -> None:
        self._pose.close()


def _build_summary(sway: float, symmetry: float, posture: float) -> str:
    parts: list[str] = []
    if sway > 0.6:
        parts.append("belirgin sallanma")
    elif sway > 0.35:
        parts.append("hafif sallanma")
    else:
        parts.append("denge stabil")

    if symmetry < 0.4:
        parts.append("postür asimetrik")
    elif symmetry < 0.7:
        parts.append("hafif asimetri")
    else:
        parts.append("postür simetrik")

    if posture < 0.3:
        parts.append("çökmüş duruş")
    elif posture < 0.6:
        parts.append("kısmen dik")
    else:
        parts.append("dik duruş")

    return "Yürüyüş: " + ", ".join(parts) + "."


def _insufficient(reason: str) -> AgentObservation:
    return AgentObservation(
        agent="gait",
        confidence=0.0,
        summary_tr=f"Yürüyüş verisi yetersiz: {reason}",
        signals={"detection_ratio": 0.0},
    )
