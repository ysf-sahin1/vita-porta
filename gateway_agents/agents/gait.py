"""Yürüyüş ajanı — MediaPipe Pose ile sallanma ve duruş analizi."""

from __future__ import annotations

import numpy as np

from gateway_agents.agents.base import Agent, AnalysisWindow
from orchestration.schemas import AgentObservation


# Normalize koordinatlar (0..1) üzerinden eşikler; el-titremesi olmayan dik
# duruşta gövde-merkezi x std'i 0.02 altında kalır, sallantılı yürüyüşte 0.04+.
_SWAY_STD_THRESHOLD = 0.025
_SHOULDER_ASYM_THRESHOLD = 0.04


class GaitAgent(Agent):
    name = "gait"

    def __init__(self, min_detection_confidence: float = 0.5) -> None:
        try:
            import mediapipe as mp
        except ImportError as exc:
            raise RuntimeError(
                "mediapipe yüklü değil. `pip install mediapipe` ile kur."
            ) from exc

        self._mp = mp
        self._landmark_enum = mp.solutions.pose.PoseLandmark
        self._pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=0,
            enable_segmentation=False,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=0.5,
        )

    def analyze(self, window: AnalysisWindow) -> AgentObservation:
        if not window.frames:
            return _insufficient()

        lm_enum = self._landmark_enum
        shoulder_cx: list[float] = []
        hip_cx: list[float] = []
        shoulder_dy: list[float] = []
        visibilities: list[float] = []

        for frame in window.frames:
            if frame is None or frame.ndim != 3:
                continue
            rgb = frame[:, :, ::-1]
            result = self._pose.process(rgb)
            if not result.pose_landmarks:
                continue
            lm = result.pose_landmarks.landmark
            ls = lm[lm_enum.LEFT_SHOULDER.value]
            rs = lm[lm_enum.RIGHT_SHOULDER.value]
            lh = lm[lm_enum.LEFT_HIP.value]
            rh = lm[lm_enum.RIGHT_HIP.value]
            shoulder_cx.append((ls.x + rs.x) / 2.0)
            hip_cx.append((lh.x + rh.x) / 2.0)
            shoulder_dy.append(ls.y - rs.y)
            visibilities.extend([ls.visibility, rs.visibility, lh.visibility, rh.visibility])

        if len(shoulder_cx) < 2:
            return _insufficient()

        shoulder_std = float(np.std(shoulder_cx))
        hip_std = float(np.std(hip_cx))
        sway_metric = max(shoulder_std, hip_std)
        sway_detected = sway_metric > _SWAY_STD_THRESHOLD

        shoulder_asym = float(np.mean(np.abs(shoulder_dy)))
        symmetry_anormal = shoulder_asym > _SHOULDER_ASYM_THRESHOLD

        avg_visibility = float(np.mean(visibilities)) if visibilities else 0.0
        confidence = float(np.clip(avg_visibility, 0.0, 1.0))

        posture = "eğik" if symmetry_anormal else "dik"
        symmetry_status = "anormal" if symmetry_anormal else "normal"

        return AgentObservation(
            agent="gait",
            confidence=confidence,
            summary_tr=_summary(sway_detected, symmetry_anormal),
            signals={
                "posture": posture,
                "sway_detected": sway_detected,
                "symmetry_status": symmetry_status,
                "avg_visibility": round(avg_visibility, 3),
            },
        )

    def close(self) -> None:
        self._pose.close()


def _summary(sway: bool, asym: bool) -> str:
    if sway and asym:
        return "Yürüyüş sallantılı, omuzlarda asimetri saptandı."
    if sway:
        return "Yürüyüş sallantılı, duruş genel olarak simetrik."
    if asym:
        return "Yürüyüş stabil ancak omuzlarda duruş bozukluğu görülüyor."
    return "Yürüyüş stabil ve duruş simetrik."


def _insufficient() -> AgentObservation:
    return AgentObservation(
        agent="gait",
        confidence=0.0,
        summary_tr="Görsel veri yetersiz",
        signals={},
    )
