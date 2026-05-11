"""Önceden çekilmiş test videolarını oynatan kaynak — jüri için fallback.

Webcam müsait değilse veya tekrarlanabilir demo gerekiyorsa kullanılır.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

import cv2

from gateway_agents.agents.base import AnalysisWindow
from gateway_agents.io.base import FrameSource

logger = logging.getLogger(__name__)


class VideoFileSource(FrameSource):
    def __init__(
        self,
        path: str | Path,
        window_seconds: float = 3.0,
        loop: bool = False,
    ) -> None:
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"Video bulunamadı: {self.path}")
        self.window_seconds = window_seconds
        self.loop = loop

    def windows(self) -> Iterator[AnalysisWindow]:
        while True:
            cap = cv2.VideoCapture(str(self.path))
            if not cap.isOpened():
                raise RuntimeError(f"Video açılamadı: {self.path}")
            fps = cap.get(cv2.CAP_PROP_FPS) or 15.0
            frames_per_window = max(2, int(fps * self.window_seconds))
            try:
                buffer: list = []
                while True:
                    ok, frame = cap.read()
                    if not ok or frame is None:
                        if buffer:
                            yield AnalysisWindow(frames=buffer, fps=fps)
                        break
                    buffer.append(frame)
                    if len(buffer) >= frames_per_window:
                        yield AnalysisWindow(frames=buffer, fps=fps)
                        buffer = []
            finally:
                cap.release()
            if not self.loop:
                return
            logger.info("Video sonuna ulaşıldı, döngü baştan başlıyor: %s", self.path)
