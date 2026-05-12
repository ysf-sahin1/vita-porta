"""Önceden çekilmiş test videolarını oynatan kaynak — jüri için fallback.

Webcam müsait değilse veya tekrarlanabilir demo gerekiyorsa kullanılır.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

import cv2
import numpy as np

from gateway_agents.io.base import FrameSource

logger = logging.getLogger(__name__)


class VideoFileSource(FrameSource):
    def __init__(
        self,
        path: str | Path,
        loop: bool = False,
    ) -> None:
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"Video bulunamadı: {self.path}")
        self.loop = loop

        cap = cv2.VideoCapture(str(self.path))
        if not cap.isOpened():
            raise RuntimeError(f"Video açılamadı: {self.path}")

        native_fps = cap.get(cv2.CAP_PROP_FPS)
        self.fps: float = float(native_fps) if native_fps and native_fps > 0 else 15.0
        self._cap: cv2.VideoCapture | None = cap
        logger.info("Video açıldı: %s fps=%.2f loop=%s", self.path, self.fps, loop)

    def frames(self) -> Iterator[np.ndarray]:
        cap = self._cap
        if cap is None:
            return
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                if self.loop:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    logger.info("Video sonuna ulaşıldı, baştan başlıyor: %s", self.path)
                    continue
                return
            yield frame

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
