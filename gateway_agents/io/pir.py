"""PIR (Pasif Kızılötesi) hareket sensörü tetikleyici.

Raspberry Pi GPIO'suna bağlı HC-SR501 veya benzeri PIR sensörler için.
gpiozero kütüphanesi üzerinden GPIO erişimi sağlar.

Pi dışında (geliştirme ortamı, Windows vb.) gpiozero yoksa
MockPirTrigger devreye girer ve her zaman hareket sinyali döner.

Kullanım:
    python -m gateway_agents.runner --esp 192.168.4.2 --pir-pin 17
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger(__name__)


@runtime_checkable
class PirProtocol(Protocol):
    """PIR sensörü için asgari arayüz."""

    @property
    def motion_detected(self) -> bool: ...

    def wait_for_motion(self, timeout: float | None = None) -> bool: ...

    def close(self) -> None: ...


class PirTrigger:
    """gpiozero MotionSensor wrapper'ı.

    Args:
        pin:       Raspberry Pi GPIO numarası (BCM, ör. 17)
        queue_len: MotionSensor iç kuyruk uzunluğu — kararlılık filtresi.
                   1 = anlık (en hızlı), daha yüksek = gürültüyü azaltır.
    """

    def __init__(self, pin: int, queue_len: int = 1) -> None:
        try:
            from gpiozero import MotionSensor
        except ImportError as exc:
            raise RuntimeError(
                "gpiozero yüklü değil. Raspberry Pi'de: pip install gpiozero\n"
                "PC/geliştirme ortamında MockPirTrigger kullanın ya da "
                "--mock-pir flag'ini ekleyin."
            ) from exc

        self._pin = pin
        self._pir = MotionSensor(pin, queue_len=queue_len)
        logger.info("PIR sensörü başlatıldı: GPIO%d", pin)

    @property
    def pin(self) -> int:
        return self._pin

    @property
    def motion_detected(self) -> bool:
        return bool(self._pir.motion_detected)

    def wait_for_motion(self, timeout: float | None = None) -> bool:
        """Hareket algılanana kadar bloklayarak bekler.

        Args:
            timeout: Saniye cinsinden bekleme süresi. None → sonsuz bekle.

        Returns:
            True  — hareket algılandı.
            False — timeout doldu, hareket yok.
        """
        self._pir.wait_for_motion(timeout=timeout)
        return self.motion_detected

    def close(self) -> None:
        try:
            self._pir.close()
            logger.debug("PIR sensörü GPIO%d kapatıldı.", self._pin)
        except Exception:  # noqa: BLE001 — defensive shutdown
            logger.debug("PIR kapatılırken hata yutuldu.", exc_info=True)


class MockPirTrigger:
    """Geliştirme / test ortamı için sahte PIR tetikleyici.

    gpiozero veya gerçek donanım olmadığında kullanılır.
    her zaman motion_detected=True döner; wait_for_motion() anında geri döner.
    """

    def __init__(self) -> None:
        logger.warning(
            "MockPirTrigger aktif — gerçek GPIO yok. "
            "Tüm analizler sürekli çalışır (PIR filtresi devre dışı)."
        )

    @property
    def motion_detected(self) -> bool:
        return True

    def wait_for_motion(self, timeout: float | None = None) -> bool:  # noqa: ARG002
        return True

    def close(self) -> None:
        pass


def build_pir_trigger(pin: int, mock_fallback: bool = False) -> PirProtocol:
    """PIR tetikleyici oluşturur.

    Args:
        pin:           GPIO pin numarası (BCM).
        mock_fallback: True ise gpiozero yoksa MockPirTrigger döner.
                       False ise gpiozero yoksa RuntimeError fırlatır.

    Returns:
        PirProtocol uyumlu nesne.
    """
    try:
        return PirTrigger(pin=pin)
    except RuntimeError:
        if mock_fallback:
            logger.warning("gpiozero bulunamadı — MockPirTrigger kullanılıyor.")
            return MockPirTrigger()
        raise
