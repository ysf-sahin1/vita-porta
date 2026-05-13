"""Frame source contract — BGR frame'leri tek tek yield eden ABC."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from types import TracebackType

import numpy as np


class FrameSource(ABC):
    fps: float

    @abstractmethod
    def frames(self) -> Iterator[np.ndarray]:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    def __enter__(self) -> "FrameSource":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
