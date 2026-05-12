"""MQTT topic'ten JPEG payload yakalayan kaynak.

ESP32-CAM veya başka bir edge cihaz `vitaporta/frames` topic'ine JPEG payload
yayınladığında bu kaynak frame'leri decode edip tüketicilere iletir.
"""

from __future__ import annotations

import logging
import queue
import threading
from collections.abc import Iterator
from typing import Any

import cv2
import numpy as np

from gateway_agents.io.base import FrameSource

logger = logging.getLogger(__name__)

_QUEUE_MAXSIZE = 64
_GET_TIMEOUT_S = 1.0


class MqttSource(FrameSource):
    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        topic: str = "vitaporta/frames",
        target_fps: float = 10.0,
    ) -> None:
        try:
            import paho.mqtt.client as mqtt
        except ImportError as exc:
            raise RuntimeError(
                "paho-mqtt yüklü değil. `pip install paho-mqtt` ile kurun."
            ) from exc

        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self.fps = target_fps

        self._queue: queue.Queue[np.ndarray] = queue.Queue(maxsize=_QUEUE_MAXSIZE)
        self._lock = threading.Lock()
        self._closed = False

        client = mqtt.Client()
        client.on_connect = self._on_connect
        client.on_message = self._on_message
        client.on_disconnect = self._on_disconnect

        client.connect(broker_host, broker_port, keepalive=60)
        client.loop_start()
        self._client = client
        logger.info(
            "MQTT kaynağı bağlandı: %s:%d topic=%s", broker_host, broker_port, topic
        )

    def _on_connect(self, client: Any, userdata: Any, flags: Any, rc: int) -> None:
        if rc == 0:
            client.subscribe(self.topic)
            logger.info("MQTT subscribe: %s", self.topic)
        else:
            logger.error("MQTT bağlantı hatası rc=%s", rc)

    def _on_disconnect(self, client: Any, userdata: Any, rc: int) -> None:
        if rc != 0:
            logger.warning("MQTT beklenmedik kopuş rc=%s", rc)

    def _on_message(self, client: Any, userdata: Any, msg: Any) -> None:
        payload = msg.payload
        if not payload:
            return
        buffer = np.frombuffer(payload, dtype=np.uint8)
        frame = cv2.imdecode(buffer, cv2.IMREAD_COLOR)
        if frame is None:
            logger.warning("JPEG decode başarısız (boyut=%d)", len(payload))
            return
        self._enqueue(frame)

    def _enqueue(self, frame: np.ndarray) -> None:
        try:
            self._queue.put_nowait(frame)
        except queue.Full:
            with self._lock:
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    pass
                try:
                    self._queue.put_nowait(frame)
                except queue.Full:
                    logger.warning("MQTT frame kuyruğu hâlâ dolu, drop edildi.")

    def frames(self) -> Iterator[np.ndarray]:
        while not self._closed:
            try:
                frame = self._queue.get(timeout=_GET_TIMEOUT_S)
            except queue.Empty:
                continue
            yield frame

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            self._client.loop_stop()
            self._client.disconnect()
        except Exception as exc:
            logger.warning("MQTT close sırasında hata: %s", exc)
        logger.info("MQTT kaynağı kapatıldı.")
