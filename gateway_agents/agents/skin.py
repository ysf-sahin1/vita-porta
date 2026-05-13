"""Ten rengi ajanı — Haar Cascade yüz tespiti + HSV ortalaması ile solgunluk."""

from __future__ import annotations

import os

import cv2
import numpy as np

from gateway_agents.agents.base import Agent, AnalysisWindow
from orchestration.schemas import AgentObservation


# Standart ofis aydınlatmasında kalibre: doygunluk düşük + parlaklık yüksek →
# kan dolaşımı azalmış soluk yüz örüntüsü. Hackathon kalibrasyonu; klinik değil.
_SAT_PALE_MAX = 80.0
_VAL_PALE_MIN = 120.0
_DIM_BRIGHTNESS = 60.0
_SAMPLE_COUNT = 5


class SkinAgent(Agent):
    name = "skin"

    def __init__(self) -> None:
        cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
        if not os.path.exists(cascade_path):
            raise RuntimeError(f"Haar cascade dosyası bulunamadı: {cascade_path}")
        self._face_cascade = cv2.CascadeClassifier(cascade_path)
        if self._face_cascade.empty():
            raise RuntimeError("Haar cascade yüklenemedi.")

    def analyze(self, window: AnalysisWindow) -> AgentObservation:
        frames = window.frames
        if not frames:
            return _insufficient()

        samples = _sample_frames(frames, _SAMPLE_COUNT)
        sat_means: list[float] = []
        val_means: list[float] = []
        sat_stds: list[float] = []
        face_hits = 0

        for frame in samples:
            if frame is None or frame.ndim != 3:
                continue
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self._face_cascade.detectMultiScale(
                gray, scaleFactor=1.2, minNeighbors=5, minSize=(60, 60)
            )
            if len(faces) == 0:
                continue
            face_hits += 1
            x, y, w, h = max(faces, key=lambda r: r[2] * r[3])
            roi = frame[y : y + h, x : x + w]
            if roi.size == 0:
                continue
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            sat_means.append(float(np.mean(hsv[:, :, 1])))
            val_means.append(float(np.mean(hsv[:, :, 2])))
            sat_stds.append(float(np.std(hsv[:, :, 1])))

        sampled = len(samples)
        face_ratio = face_hits / sampled if sampled else 0.0

        if not sat_means:
            return AgentObservation(
                agent="skin",
                confidence=0.0,
                summary_tr="Görsel veri yetersiz",
                signals={},
            )

        mean_sat = float(np.mean(sat_means))
        mean_val = float(np.mean(val_means))
        color_variance = float(np.mean(sat_stds))

        if mean_sat < _SAT_PALE_MAX and mean_val > _VAL_PALE_MIN:
            skin_tone = "solgun"
        elif mean_val < _DIM_BRIGHTNESS:
            skin_tone = "belirsiz"
        else:
            skin_tone = "normal"

        confidence = float(np.clip(face_ratio, 0.0, 1.0))
        # Loş ortamda renk ölçümü güvenilmez; üst sınırı düşür.
        if mean_val < _DIM_BRIGHTNESS:
            confidence = min(confidence, 0.5)

        return AgentObservation(
            agent="skin",
            confidence=confidence,
            summary_tr=_summary(skin_tone),
            signals={
                "skin_tone": skin_tone,
                "color_variance": round(color_variance, 3),
                "mean_saturation": round(mean_sat, 2),
                "face_detected_ratio": round(face_ratio, 3),
            },
        )


def _sample_frames(frames: list[np.ndarray], count: int) -> list[np.ndarray]:
    n = len(frames)
    if n <= count:
        return list(frames)
    step = n / float(count)
    return [frames[int(i * step)] for i in range(count)]


def _summary(skin_tone: str) -> str:
    if skin_tone == "solgun":
        return "Cilt tonu solgun, dolaşım/oksijenizasyon değerlendirmesi önerilir."
    if skin_tone == "belirsiz":
        return "Ortam ışığı düşük, cilt tonu güvenilir değerlendirilemedi."
    return "Cilt tonu normal sınırlarda."


def _insufficient() -> AgentObservation:
    return AgentObservation(
        agent="skin",
        confidence=0.0,
        summary_tr="Görsel veri yetersiz",
        signals={},
    )
