"""Yerel webcam üzerinden frame yakalayan kaynak.

ESP32-CAM hazır olmadan jüri demosunda kullanılır.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

import cv2
import numpy as np

from gateway_agents.io.base import FrameSource

logger = logging.getLogger(__name__)


class WebcamSource(FrameSource):
    def __init__(
        self,
        device_index: int = 0,
        target_fps: float = 15.0,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        self.device_index = device_index
        self.fps = target_fps
        self.width = width
        self.height = height

        # Önce varsayılan (MSMF) backend'i deneyelim; sanal kameralar (Iriun, OBS)
        # MSMF ile daha kararlı çalışır ve kare akışı anında başlar.
        cap = cv2.VideoCapture(device_index)
        ok = False
        if cap.isOpened():
            ok, _ = cap.read()

        if not ok:
            if cap is not None:
                cap.release()
            logger.info("Varsayılan backend akış vermedi, DirectShow (CAP_DSHOW) deneniyor...")
            cap = cv2.VideoCapture(device_index, cv2.CAP_DSHOW)
            if cap.isOpened():
                ok, _ = cap.read()

        if not cap.isOpened() or not ok:
            if cap is not None:
                cap.release()
            raise RuntimeError(f"Webcam açılamadı veya akış alınamadı (index={device_index}). Iriun/telefon bağlantısını kontrol edin.")

        if target_fps:
            cap.set(cv2.CAP_PROP_FPS, target_fps)
        if width is not None:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        if height is not None:
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        self._cap: cv2.VideoCapture | None = cap
        logger.info(
            "Webcam açıldı: index=%s fps=%.1f size=%sx%s",
            device_index,
            target_fps,
            width,
            height,
        )

    def frames(self) -> Iterator[np.ndarray]:
        cap = self._cap
        if cap is None:
            return
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                logger.warning("Webcam frame okunamadı, kaynak kapanmış olabilir.")
                return
            
            # Kullanıcının kameranın ne gördüğünü (açı, ışık, yön) anında izleyebilmesi
            # için canlı önizleme penceresi gösteriyoruz.
            try:
                cv2.imshow(f"Vita Porta Kamera Akisi (Kamera Indeks: {self.device_index})", frame)
                cv2.waitKey(1)
            except Exception:
                pass

            yield frame

    def close(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass

