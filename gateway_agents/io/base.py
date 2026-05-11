"""Frame source contract — bir AnalysisWindow toplayıp yield eden iterator."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from gateway_agents.agents.base import AnalysisWindow


class FrameSource(ABC):
    """Bir source, sürekli olarak `AnalysisWindow` üretir.

    Her window, ajanların analiz edebileceği kısa bir frame penceresidir
    (örn. 3 saniye / ~45 frame @ 15 fps).
    """

    @abstractmethod
    def windows(self) -> Iterator[AnalysisWindow]:
        """Sonsuz veya sonlu bir window iteratoru döner."""

    def close(self) -> None:  # pragma: no cover — opsiyonel kaynak temizliği
        pass
