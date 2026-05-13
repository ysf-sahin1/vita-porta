"""Solunum ajanı — sabit göğüs ROI üzerinde frame-fark tabanlı BPM tahmini."""

from __future__ import annotations

import cv2
import numpy as np

from gateway_agents.agents.base import Agent, AnalysisWindow
from orchestration.schemas import AgentObservation


_DIFF_THRESHOLD = 25
_BPM_SLOW_MAX = 10.0
_BPM_FAST_MIN = 22.0
# Walking/large-body motion penceresinde CV (std/mean) > 1.0 olur; nefes daha
# stabildir. Bu üstü erratik kabul edilip güven düşürülür.
_ERRATIC_CV_THRESHOLD = 1.0
# Tepe için medyan çarpanı; çok düşük bırakılırsa gürültü tepesi sayılır.
_PEAK_MEDIAN_FACTOR = 1.2


class RespirationAgent(Agent):
    name = "respiration"

    def analyze(self, window: AnalysisWindow) -> AgentObservation:
        frames = window.frames
        if not frames or window.fps <= 0:
            return _insufficient()

        min_required = max(2, int(window.fps * 1.0))
        if len(frames) < min_required:
            return _insufficient()

        motion_series: list[float] = []
        prev_gray = None
        for frame in frames:
            if frame is None or frame.ndim != 3:
                continue
            roi = _chest_roi(frame)
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            if prev_gray is not None and gray.shape == prev_gray.shape:
                diff = cv2.absdiff(gray, prev_gray)
                _, mask = cv2.threshold(diff, _DIFF_THRESHOLD, 255, cv2.THRESH_BINARY)
                motion_series.append(float(np.sum(mask) / 255.0))
            prev_gray = gray

        if len(motion_series) < 3:
            return _insufficient()

        signal = _smooth(np.asarray(motion_series, dtype=np.float32))
        median = float(np.median(signal))
        peak_indices = _find_peaks(signal, median * _PEAK_MEDIAN_FACTOR)

        duration_s = window.duration_s
        if duration_s <= 0.5:
            return _insufficient()

        bpm = (len(peak_indices) / duration_s) * 60.0
        movement_intensity = float(np.mean(signal))
        mean_for_cv = max(movement_intensity, 1e-6)
        cv_ratio = float(np.std(signal) / mean_for_cv)

        pattern = _classify(bpm, peak_indices, cv_ratio)

        confidence = 0.7
        if cv_ratio > _ERRATIC_CV_THRESHOLD:
            confidence = 0.2

        return AgentObservation(
            agent="respiration",
            confidence=confidence,
            summary_tr=_summary(pattern, bpm),
            signals={
                "breathing_pattern": pattern,
                "breaths_per_minute": round(bpm, 1),
                "movement_intensity": round(movement_intensity, 2),
            },
        )


def _chest_roi(frame: np.ndarray) -> np.ndarray:
    h, w = frame.shape[:2]
    x0 = int(w * 0.30)
    x1 = int(w * 0.70)
    y0 = int(h * 0.30)
    y1 = int(h * 0.60)
    return frame[y0:y1, x0:x1]


def _smooth(signal: np.ndarray, k: int = 3) -> np.ndarray:
    if signal.size < k:
        return signal
    kernel = np.ones(k, dtype=np.float32) / k
    return np.convolve(signal, kernel, mode="same")


def _find_peaks(signal: np.ndarray, min_height: float) -> list[int]:
    peaks: list[int] = []
    for i in range(1, len(signal) - 1):
        if signal[i] > signal[i - 1] and signal[i] > signal[i + 1] and signal[i] > min_height:
            peaks.append(i)
    return peaks


def _classify(bpm: float, peak_indices: list[int], cv_ratio: float) -> str:
    if len(peak_indices) >= 3:
        intervals = np.diff(peak_indices)
        if intervals.size > 1 and np.std(intervals) / max(np.mean(intervals), 1e-6) > 0.5:
            return "düzensiz"
    if bpm < _BPM_SLOW_MAX:
        return "yavaş"
    if bpm > _BPM_FAST_MIN:
        return "hızlı"
    return "normal"


def _summary(pattern: str, bpm: float) -> str:
    bpm_txt = f"{bpm:.0f} nefes/dk"
    if pattern == "yavaş":
        return f"Solunum yavaşlamış ({bpm_txt}), bilinç ve oksijen kontrolü önerilir."
    if pattern == "hızlı":
        return f"Solunum hızlanmış ({bpm_txt}), takipne açısından değerlendirilmeli."
    if pattern == "düzensiz":
        return f"Solunum örüntüsü düzensiz ({bpm_txt}), dikkatli izlem gerekli."
    return f"Solunum normal aralıkta ({bpm_txt})."


def _insufficient() -> AgentObservation:
    return AgentObservation(
        agent="respiration",
        confidence=0.0,
        summary_tr="Görsel veri yetersiz",
        signals={},
    )
