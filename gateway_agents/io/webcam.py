"""Yerel webcam üzerinden frame yakalayan kaynak.

ESP32-CAM hazır olmadan jüri demosunda kullanılır.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Iterator

import cv2

from gateway_agents.agents.base import AnalysisWindow
from gateway_agents.io.base import FrameSource

logger = logging.getLogger(__name__)


class WebcamSource(FrameSource):
    def __init__(
        self,
        camera_index: int = 0,
        window_seconds: float = 3.0,
        target_fps: float = 15.0,
        width: int = 640,
        height: int = 480,
    ) -> None:
        self.camera_index = camera_index
        self.window_seconds = window_seconds
        self.target_fps = target_fps
        self.width = width
        self.height = height
        self._cap: cv2.VideoCapture | None = None

    def _open(self) -> cv2.VideoCapture:
        if self._cap is not None and self._cap.isOpened():
            return self._cap
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError(f"Webcam açılamadı (index={self.camera_index}).")
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.target_fps)
        self._cap = cap
        logger.info("Webcam açıldı: index=%s %dx%d", self.camera_index, self.width, self.height)
        return cap

    def windows(self) -> Iterator[AnalysisWindow]:
        cap = self._open()
        frames_per_window = max(2, int(self.target_fps * self.window_seconds))
        frame_interval = 1.0 / self.target_fps
        while True:
            frames = []
            t_start = time.perf_counter()
            for _ in range(frames_per_window):
                ok, frame = cap.read()
                if not ok or frame is None:
                    logger.warning("Webcam frame okunamadı, kaynak kapanmış olabilir.")
                    return
                frames.append(frame)
                # Basit hız sınırlandırma
                elapsed = time.perf_counter() - t_start - len(frames) * frame_interval
                if elapsed < 0:
                    time.sleep(min(0.05, -elapsed))
            t_end = time.perf_counter()
            actual_fps = len(frames) / max(0.001, t_end - t_start)
            yield AnalysisWindow(frames=frames, fps=actual_fps)

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
