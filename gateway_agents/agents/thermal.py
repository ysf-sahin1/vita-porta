"""Termal ajan — RGB proxy ile vücut sıcaklığı tahmini.

Gerçek termal kamera (MLX90640 / FLIR Lepton) bağlandığında `sensor_type`
"thermal" olur ve temp_estimate_c güvenilir ölçüm değeri taşır. Yokken
webcam karesi üzerinden LAB renk uzayındaki kırmızılık/sıcaklık tonu
kullanılarak kaba bir tahmin üretilir (sensor_type="rgb_proxy").

RGB proxy yaklaşımı:
    - Yüz ROI → LAB renk uzayı
    - LAB.a kanalı: pozitif yönde sapma → ten kızarıklığı / ateş belirtisi
    - LAB.b kanalı: pozitif yönde sapma → sarımtırak/sıcak ton
    - Warmth indeksi → kalibre edilmemiş sıcaklık tahminine dönüşüm
    - Confidence maks. 0.60 (proxy; gerçek sensör → 0.95)

Çıktı sinyalleri:
    temp_estimate_c   float  — tahmini vücut sıcaklığı (°C)
    fever_flag        bool   — > 37.5 °C
    hypothermia_flag  bool   — < 35.5 °C
    warmth_score      0..1   — normalize sıcaklık indeksi (0.5 = normal)
    sensor_type       str    — "rgb_proxy" | "thermal"
"""

from __future__ import annotations

import logging

import numpy as np

from gateway_agents.agents.base import Agent, AnalysisWindow
from orchestration.schemas import AgentObservation

logger = logging.getLogger(__name__)

try:
    import cv2

    _CV_AVAILABLE = True
except ImportError:
    cv2 = None  # type: ignore[assignment]
    _CV_AVAILABLE = False

try:
    import mediapipe as mp

    _MP_AVAILABLE = True
except ImportError:
    mp = None  # type: ignore[assignment]
    _MP_AVAILABLE = False

# Sağlıklı ten referans noktaları (LAB, 0-255 ölçeği)
_LAB_A_NEUTRAL = 138.0   # nötr ten kırmızılığı
_LAB_B_NEUTRAL = 122.0   # nötr ten sarılığı
_A_RANGE = 25.0          # ±25 birim ≈ ±2.5°C sapma
_B_RANGE = 18.0

# Sıcaklık eşikleri
_FEVER_THRESHOLD = 37.5
_HYPOTHERMIA_THRESHOLD = 35.5
_BASE_TEMP = 36.5        # proxy kalibrasyonu: nötr ten → 36.5°C


class ThermalAgent(Agent):
    """RGB görüntüsünden termal proxy veya gerçek termal matrisin analizi."""

    name = "thermal"

    def __init__(self) -> None:
        if not _CV_AVAILABLE:
            raise RuntimeError("opencv-python yüklü değil.")
        self._face = None
        if _MP_AVAILABLE:
            self._face = mp.solutions.face_detection.FaceDetection(
                model_selection=0, min_detection_confidence=0.5
            )

    def analyze(self, window: AnalysisWindow) -> AgentObservation:
        if not window.frames:
            return _insufficient("Görüntü alınamadı.")

        a_vals: list[float] = []
        b_vals: list[float] = []
        face_hits = 0

        for frame in window.frames:
            roi, has_face = self._extract_face_roi(frame)
            if has_face:
                face_hits += 1
            if roi is None or roi.size == 0:
                continue
            lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
            a_vals.append(float(np.mean(lab[:, :, 1])))
            b_vals.append(float(np.mean(lab[:, :, 2])))

        if not a_vals:
            return _insufficient("Yüz ROI çıkarılamadı.")

        a_mean = float(np.mean(a_vals))
        b_mean = float(np.mean(b_vals))

        # Warmth: nötr ten etrafındaki LAB sapması → −1..1
        a_delta = (a_mean - _LAB_A_NEUTRAL) / _A_RANGE
        b_delta = (b_mean - _LAB_B_NEUTRAL) / _B_RANGE
        warmth = float(np.clip(0.6 * a_delta + 0.4 * b_delta, -1.0, 1.0))

        # Sıcaklık tahmini: warmth=0 → 36.5°C, ±1 → ±2.5°C
        temp_c = round(_BASE_TEMP + 2.5 * warmth, 1)
        fever = temp_c > _FEVER_THRESHOLD
        hypothermia = temp_c < _HYPOTHERMIA_THRESHOLD

        # Warmth 0..1 normalizasyonu (0.5 = normal)
        warmth_score = round(float(np.clip(0.5 + warmth * 0.5, 0.0, 1.0)), 3)

        face_ratio = face_hits / len(window.frames)
        # RGB proxy: güven max 0.60; yüz tespit oranı ile doğrusal
        confidence = float(min(0.60, 0.25 + 0.55 * face_ratio))

        summary_tr = _build_summary(temp_c, fever, hypothermia, face_ratio > 0)

        return AgentObservation(
            agent="thermal",
            confidence=confidence,
            summary_tr=summary_tr,
            signals={
                "temp_estimate_c": temp_c,
                "fever_flag": fever,
                "hypothermia_flag": hypothermia,
                "warmth_score": warmth_score,
                "sensor_type": "rgb_proxy",
            },
        )

    def _extract_face_roi(self, frame: np.ndarray) -> tuple[np.ndarray | None, bool]:
        h, w = frame.shape[:2]
        if self._face is not None:
            rgb = frame[:, :, ::-1]
            result = self._face.process(rgb)
            if result.detections:
                box = result.detections[0].location_data.relative_bounding_box
                x = max(0, int(box.xmin * w))
                y = max(0, int(box.ymin * h))
                bw = max(1, int(box.width * w))
                bh = max(1, int(box.height * h))
                return frame[y : y + bh, x : x + bw], True
        # Fallback: yüz bölgesi olası orta-üst dikdörtgen
        cy0 = int(h * 0.10)
        cy1 = int(h * 0.55)
        cx0 = int(w * 0.30)
        cx1 = int(w * 0.70)
        return frame[cy0:cy1, cx0:cx1], False

    def close(self) -> None:
        if self._face is not None:
            self._face.close()


def _build_summary(temp_c: float, fever: bool, hypothermia: bool, face_seen: bool) -> str:
    sensor_note = "" if face_seen else " (yüz tespit edilemedi, ROI fallback)"
    if fever:
        return f"Termal: ateş şüphesi — tahmini {temp_c}°C{sensor_note}. [RGB proxy]"
    if hypothermia:
        return f"Termal: düşük sıcaklık — tahmini {temp_c}°C{sensor_note}. [RGB proxy]"
    return f"Termal: normal aralık — tahmini {temp_c}°C{sensor_note}. [RGB proxy]"


def _insufficient(reason: str) -> AgentObservation:
    return AgentObservation(
        agent="thermal",
        confidence=0.0,
        summary_tr=f"Termal veri yetersiz: {reason}",
        signals={
            "temp_estimate_c": 0.0,
            "fever_flag": False,
            "hypothermia_flag": False,
            "warmth_score": 0.5,
            "sensor_type": "rgb_proxy",
        },
    )
