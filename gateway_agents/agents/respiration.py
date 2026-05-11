"""Solunum ajanı — basitleştirilmiş frame-fark analizi.

NotebookLM hackathon önerisi: tam optik akış yerine frame-fark eşiklemesi ile
göğüs hareket örüntüsünü çıkarmak yeterli. Tam optik akış sonraki sprint.

Strateji:
    1. Göğüs ROI'sini frame'in alt-orta bölgesinden al (kapı çerçevesi kamerası
       hastayı dik konumda görür; pose tabanlı ROI Faz-6'da gelir).
    2. Ardışık frame'ler arasında grayscale fark (mutlak değer ortalaması).
    3. Fark sinyalinden tepe sayısı → solunum frekansı (BPM tahmini).
    4. Sinyal varyansı çok düşükse "apne benzeri", çok yüksekse "hızlı/düzensiz".

Çıktı sinyalleri:
    breath_per_minute  float  — kaba BPM tahmini
    motion_score       0..1   — toplam hareket yoğunluğu
    pattern            str    — "normal" | "hızlı" | "yavaş" | "düzensiz" | "apne_riski"
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


# Erişkin normal: 12–20 nefes/dk. Sınırlar:
_BPM_NORMAL_LOW = 12.0
_BPM_NORMAL_HIGH = 20.0
_BPM_FAST_HIGH = 30.0


class RespirationAgent(Agent):
    name = "respiration"

    def __init__(self) -> None:
        if not _CV_AVAILABLE:
            raise RuntimeError("opencv-python yüklü değil.")

    def analyze(self, window: AnalysisWindow) -> AgentObservation:
        frames = window.frames
        if len(frames) < 4:
            return _insufficient("Solunum analizi için yeterli frame yok (en az 4).")
        if window.fps <= 0:
            return _insufficient("Geçersiz fps.")

        diffs: list[float] = []
        prev_gray = None
        for frame in frames:
            roi = _chest_roi(frame)
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            if prev_gray is not None and gray.shape == prev_gray.shape:
                diff = float(np.mean(cv2.absdiff(gray, prev_gray)))
                diffs.append(diff)
            prev_gray = gray

        if not diffs:
            return _insufficient("Frame farkı hesaplanamadı.")

        signal = np.array(diffs, dtype=np.float32)

        # Tepe sayısı: sinyal ortalamasının üstünden geçen yükselen kenarlar
        mean = float(signal.mean())
        std = float(signal.std())
        threshold = mean + 0.3 * std
        peaks = 0
        above = False
        for v in signal:
            if v > threshold and not above:
                peaks += 1
                above = True
            elif v <= threshold:
                above = False

        # Pencere süresi (saniye)
        duration_s = len(frames) / window.fps
        if duration_s <= 0.1:
            return _insufficient("Çok kısa analiz penceresi.")
        bpm = peaks * (60.0 / duration_s)

        motion_score = float(min(1.0, mean / 8.0))  # 8 BGR gri-fark birimi = belirgin
        pattern = _classify(bpm, std, motion_score)

        # Güven: hareket çok düşükse veya frame sayısı azsa düşer
        confidence = float(min(1.0, 0.3 + 0.7 * motion_score))
        if pattern == "apne_riski":
            confidence *= 0.7  # düşük hareketle BPM güvenilmez

        summary_tr = _build_summary(bpm, pattern)

        return AgentObservation(
            agent="respiration",
            confidence=confidence,
            summary_tr=summary_tr,
            signals={
                "breath_per_minute": round(bpm, 1),
                "motion_score": round(motion_score, 3),
                "pattern": pattern,
            },
        )


def _chest_roi(frame: np.ndarray) -> np.ndarray:
    """Frame'in alt-orta dikdörtgenini göğüs ROI olarak al."""
    h, w = frame.shape[:2]
    y0 = int(h * 0.45)
    y1 = int(h * 0.85)
    x0 = int(w * 0.25)
    x1 = int(w * 0.75)
    return frame[y0:y1, x0:x1]


def _classify(bpm: float, std: float, motion: float) -> str:
    if motion < 0.05:
        return "apne_riski"
    if std / max(0.01, motion * 8.0) > 1.5:
        return "düzensiz"
    if bpm > _BPM_FAST_HIGH:
        return "hızlı"
    if bpm < _BPM_NORMAL_LOW:
        return "yavaş"
    if bpm <= _BPM_NORMAL_HIGH:
        return "normal"
    return "hızlı"


def _build_summary(bpm: float, pattern: str) -> str:
    bpm_txt = f"{bpm:.0f} nefes/dk"
    if pattern == "apne_riski":
        # Hareket yokken BPM gürültüye dayalı; göstermek yanıltıcı olur.
        return "Solunum: belirgin göğüs hareketi yok, apne riski."
    if pattern == "düzensiz":
        return f"Solunum: düzensiz örüntü ({bpm_txt})."
    if pattern == "hızlı":
        return f"Solunum: hızlanmış ({bpm_txt})."
    if pattern == "yavaş":
        return f"Solunum: yavaşlamış ({bpm_txt})."
    return f"Solunum: normal hızda ({bpm_txt})."


def _insufficient(reason: str) -> AgentObservation:
    return AgentObservation(
        agent="respiration",
        confidence=0.0,
        summary_tr=f"Solunum verisi yetersiz: {reason}",
        signals={"breath_per_minute": 0.0, "motion_score": 0.0, "pattern": "yetersiz"},
    )
