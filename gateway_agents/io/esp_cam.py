"""ESP32-CAM MJPEG stream'inden frame okuyan kaynak.

ESP32-CAM Arduino sketch'i http://<IP>:81/stream adresinde MJPEG yayını yapar.
OpenCV bu URL'yi doğrudan VideoCapture ile okuyabilir.

Kullanım:
    python -m gateway_agents.runner --esp 192.168.1.42
"""

from __future__ import annotations

import logging
from collections.abc import Iterator

import cv2
import numpy as np

from gateway_agents.io.base import FrameSource

logger = logging.getLogger(__name__)

_DEFAULT_PORT = 81
_DEFAULT_PATH = "/stream"


class EspCamSource(FrameSource):
    """ESP32-CAM MJPEG HTTP stream'i tüketen FrameSource.

    Args:
        host: ESP32-CAM'in IP adresi (ör. "192.168.1.42")
        port: Stream portu — Arduino sketch'te 81 olarak tanımlı.
        target_fps: İstenen FPS; ESP32-CAM ~10 FPS üretir, bu değer
                    pencere hesaplaması için kullanılır (gerçek FPS'i değiştirmez).
        fallback_webcam: Kameraya ulaşılamazsa True ise webcam 0'a geçer,
                         False ise hata fırlatır.
    """

    def __init__(
        self,
        host: str,
        port: int = _DEFAULT_PORT,
        target_fps: float = 10.0,
        fallback_webcam: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.fps = target_fps
        self._fallback_webcam = fallback_webcam
        self._using_fallback = False

        stream_url = f"http://{host}:{port}{_DEFAULT_PATH}"
        logger.info("ESP32-CAM bağlanılıyor: %s", stream_url)

        cap = cv2.VideoCapture(stream_url)
        ok = False
        if cap.isOpened():
            ok, _ = cap.read()

        if not ok:
            if cap is not None:
                cap.release()
            if fallback_webcam:
                logger.warning(
                    "ESP32-CAM'e ulaşılamadı (%s). Webcam 0'a geçiliyor.", stream_url
                )
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    raise RuntimeError(
                        f"ESP32-CAM ({stream_url}) ve webcam 0 açılamadı. "
                        "IP adresini ve WiFi bağlantısını kontrol edin."
                    )
                self._using_fallback = True
                self.fps = 15.0
            else:
                raise RuntimeError(
                    f"ESP32-CAM stream açılamadı: {stream_url}\n"
                    "Kontrol listesi:\n"
                    "  1. ESP32-CAM aynı WiFi ağında mı?\n"
                    "  2. Arduino sketch yüklü ve çalışıyor mu?\n"
                    "  3. IP adresi doğru mu? (Serial Monitor'dan kontrol edin)\n"
                    "  4. http://<IP>:81/stream tarayıcıda açılıyor mu?"
                )

        self._cap: cv2.VideoCapture | None = cap

        if self._using_fallback:
            logger.info("Fallback: webcam 0 açıldı.")
        else:
            logger.info("ESP32-CAM bağlandı: %s  fps=%.1f", stream_url, target_fps)

    def frames(self) -> Iterator[np.ndarray]:
        cap = self._cap
        if cap is None:
            return

        label = "Webcam (fallback)" if self._using_fallback else f"ESP32-CAM {self.host}"

        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                logger.warning("%s frame okunamadı, stream kopmuş olabilir.", label)
                return

            try:
                cv2.imshow(f"Vita Porta — {label}", frame)
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
