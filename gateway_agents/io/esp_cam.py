"""ESP32-CAM MJPEG stream'inden frame okuyan kaynak.

ESP32-CAM Arduino sketch'i ``http://<IP>:81/stream`` adresinde
``multipart/x-mixed-replace`` MJPEG yayını yapar. Windows üzerinde
cv2.VideoCapture bu stream'i bazen açamadığı (FFmpeg backend
``isOpened()=False`` döndü) için manuel JPEG ayrıştırıcı kullanıyoruz:

- ``requests.get(stream=True)`` ile baytları akış olarak çek
- JPEG SOI/EOI markörlerini (0xFFD8 / 0xFFD9) bul
- Her bir JPEG bloğunu ``cv2.imdecode`` ile numpy karesine çevir

Bu hem cross-platform hem de cv2'nin MJPEG backend bağımlılığını ortadan
kaldırıyor.

Önizleme penceresi: ``VITA_PREVIEW=1`` env değişkeni set edilirse her frame
``cv2.imshow`` ile gösterilir. Default kapalı — headless ortamlarda GUI
thread olmadan sıkışmayı önler.

Kullanım:
    python -m gateway_agents.runner --esp 192.168.1.42
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator

import cv2
import numpy as np
import requests

from gateway_agents.io.base import FrameSource

logger = logging.getLogger(__name__)

_DEFAULT_PORT = 81
_DEFAULT_PATH = "/stream"
_CONNECT_TIMEOUT_S = 5.0
_READ_TIMEOUT_S = 10.0
_CHUNK_SIZE = 4096
_MAX_BUFFER_BYTES = 4 * 1024 * 1024  # 4MB — bozuk stream'de buffer şişmesin

_JPEG_SOI = b"\xff\xd8"  # Start of Image
_JPEG_EOI = b"\xff\xd9"  # End of Image

_PREVIEW_ENABLED = os.environ.get("VITA_PREVIEW", "0") not in ("0", "", "false", "False")


class EspCamSource(FrameSource):
    """ESP32-CAM MJPEG HTTP stream'i tüketen FrameSource.

    Args:
        host: ESP32-CAM'in IP adresi (ör. ``"192.168.1.42"``)
        port: Stream portu — Arduino sketch'inde 81.
        target_fps: Pencere hesaplamasında kullanılan tahmini FPS (akışın
                    gerçek hızını değiştirmez).
        fallback_webcam: ESP'ye ulaşılamazsa True ise webcam 0'a düş.
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
        self._response: requests.Response | None = None
        self._webcam_cap: cv2.VideoCapture | None = None

        stream_url = f"http://{host}:{port}{_DEFAULT_PATH}"
        logger.info("ESP32-CAM bağlanılıyor: %s", stream_url)

        try:
            resp = requests.get(
                stream_url,
                stream=True,
                timeout=(_CONNECT_TIMEOUT_S, _READ_TIMEOUT_S),
            )
            resp.raise_for_status()
            self._response = resp
            logger.info("ESP32-CAM bağlandı: %s fps=%.1f", stream_url, target_fps)
        except (requests.RequestException, OSError) as exc:
            logger.warning("ESP32-CAM'e ulaşılamadı (%s): %s", stream_url, exc)
            if fallback_webcam:
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    raise RuntimeError(
                        f"ESP32-CAM ({stream_url}) ve webcam 0 da açılamadı."
                    ) from exc
                self._webcam_cap = cap
                self._using_fallback = True
                self.fps = 15.0
                logger.info("Fallback: webcam 0 açıldı.")
            else:
                raise RuntimeError(
                    f"ESP32-CAM stream açılamadı: {stream_url}\n"
                    "Kontrol listesi:\n"
                    "  1. ESP32-CAM aynı WiFi ağında mı?\n"
                    "  2. Arduino sketch yüklü ve çalışıyor mu?\n"
                    "  3. http://<IP>:81/stream tarayıcıda açılıyor mu?"
                ) from exc

    def frames(self) -> Iterator[np.ndarray]:
        if self._using_fallback:
            yield from self._webcam_frames()
            return
        yield from self._mjpeg_frames()

    def _mjpeg_frames(self) -> Iterator[np.ndarray]:
        """Streaming HTTP yanıtından JPEG bloklarını ayrıştırıp numpy verir."""

        resp = self._response
        if resp is None:
            return

        label = f"ESP32-CAM {self.host}"
        buffer = bytearray()

        try:
            for chunk in resp.iter_content(chunk_size=_CHUNK_SIZE):
                if not chunk:
                    continue
                buffer.extend(chunk)

                # Buffer'da kalan tüm JPEG'leri çıkar
                while True:
                    start = buffer.find(_JPEG_SOI)
                    if start < 0:
                        # SOI yok, baştan biriken çöpü at
                        buffer.clear()
                        break
                    end = buffer.find(_JPEG_EOI, start + 2)
                    if end < 0:
                        # Henüz tam JPEG yok — daha veri bekle
                        if start > 0:
                            # SOI'den önceki bytes işe yaramaz
                            del buffer[:start]
                        break

                    jpeg_bytes = bytes(buffer[start : end + 2])
                    del buffer[: end + 2]

                    arr = np.frombuffer(jpeg_bytes, dtype=np.uint8)
                    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                    if frame is None:
                        logger.debug("JPEG decode başarısız, atlandı (%d byte)", len(jpeg_bytes))
                        continue

                    if _PREVIEW_ENABLED:
                        try:
                            cv2.imshow(f"Vita Porta — {label}", frame)
                            cv2.waitKey(1)
                        except Exception:
                            pass

                    yield frame

                # Buffer aşırı şişerse koru
                if len(buffer) > _MAX_BUFFER_BYTES:
                    logger.warning("MJPEG buffer aşıldı, temizleniyor")
                    buffer.clear()
        except (requests.RequestException, OSError) as exc:
            logger.warning("%s stream koptu: %s", label, exc)
            return

    def _webcam_frames(self) -> Iterator[np.ndarray]:
        cap = self._webcam_cap
        if cap is None:
            return
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                logger.warning("Webcam frame okunamadı.")
                return
            if _PREVIEW_ENABLED:
                try:
                    cv2.imshow("Vita Porta — Webcam (fallback)", frame)
                    cv2.waitKey(1)
                except Exception:
                    pass
            yield frame

    def close(self) -> None:
        if self._response is not None:
            try:
                self._response.close()
            except Exception:  # noqa: BLE001
                pass
            self._response = None
        if self._webcam_cap is not None:
            self._webcam_cap.release()
            self._webcam_cap = None
        if _PREVIEW_ENABLED:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass
