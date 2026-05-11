"""Ten rengi ajanı — OpenCV ile HSV/LAB renk uzayında solgunluk analizi.

Strateji:
    1. MediaPipe Face Detection ile yüz bölgesini bul (yoksa frame ortası ROI).
    2. ROI'yi HSV ve LAB'a çevir.
    3. Solgunluk = düşük saturation (HSV.S) + düşük redness (LAB.a).
    4. Birden fazla frame'in ortalamasını al → gürültüye dayanıklı.

Çıktı sinyalleri:
    pallor_score      0..1   — 1 = belirgin solgun, 0 = normal
    saturation_mean   0..255 — ortalama doygunluk
    redness_mean      0..255 — LAB.a kanalı ortalaması (128 = nötr)
    face_detected     bool   — yüz tespit edildi mi
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


# Solgunluk eşikleri: standart aydınlatmada kalibre edilmiş kaba değerler.
# Pilot aşamasında kapı altı ışıklandırmasıyla yeniden kalibre edilmeli.
_SAT_NORMAL = 80.0  # HSV.S — bunun altı solgun yönünde
_RED_NORMAL = 138.0  # LAB.a — 128 nötr, sağlıklı ten ~140+


class SkinAgent(Agent):
    name = "skin"

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

        sat_means: list[float] = []
        red_means: list[float] = []
        face_hits = 0

        for frame in window.frames:
            roi, has_face = self._extract_face_roi(frame)
            if has_face:
                face_hits += 1
            if roi is None or roi.size == 0:
                continue
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
            sat_means.append(float(np.mean(hsv[:, :, 1])))
            red_means.append(float(np.mean(lab[:, :, 1])))

        if not sat_means:
            return _insufficient("ROI çıkarılamadı.")

        sat_mean = float(np.mean(sat_means))
        red_mean = float(np.mean(red_means))

        # Pallor: düşük saturation + düşük redness → yüksek skor
        sat_pallor = max(0.0, (_SAT_NORMAL - sat_mean) / _SAT_NORMAL)
        red_pallor = max(0.0, (_RED_NORMAL - red_mean) / 10.0)
        pallor_score = float(min(1.0, 0.6 * sat_pallor + 0.4 * red_pallor))

        face_ratio = face_hits / len(window.frames)
        confidence = float(min(1.0, 0.4 + 0.6 * face_ratio))

        summary_tr = _build_summary(pallor_score, face_ratio > 0)

        return AgentObservation(
            agent="skin",
            confidence=confidence,
            summary_tr=summary_tr,
            signals={
                "pallor_score": round(pallor_score, 3),
                "saturation_mean": round(sat_mean, 1),
                "redness_mean": round(red_mean, 1),
                "face_detected": face_ratio > 0,
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
                roi = frame[y : y + bh, x : x + bw]
                return roi, True
        # Fallback: orta-üst dikdörtgen ROI (yüz olası bölgesi)
        cy0 = int(h * 0.15)
        cy1 = int(h * 0.55)
        cx0 = int(w * 0.30)
        cx1 = int(w * 0.70)
        return frame[cy0:cy1, cx0:cx1], False

    def close(self) -> None:
        if self._face is not None:
            self._face.close()


def _build_summary(pallor: float, face_seen: bool) -> str:
    if pallor > 0.6:
        head = "Ten rengi belirgin solgun"
    elif pallor > 0.3:
        head = "Hafif solgunluk"
    else:
        head = "Ten rengi normal"
    tail = " (yüz tespit edildi)" if face_seen else " (yüz tespit edilemedi, ROI fallback)"
    return head + tail + "."


def _insufficient(reason: str) -> AgentObservation:
    return AgentObservation(
        agent="skin",
        confidence=0.0,
        summary_tr=f"Ten rengi verisi yetersiz: {reason}",
        signals={"pallor_score": 0.0, "face_detected": False},
    )
