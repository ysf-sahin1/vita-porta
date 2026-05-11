"""Shared agent contract.

An agent consumes a short window of frames, returns an AgentObservation. The
window length is dictated by the gateway (default ~3 seconds, matching the
"3 saniye içinde değerlendirme" promise from the pitch).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import numpy as np

from orchestration.schemas import AgentObservation


@dataclass
class AnalysisWindow:
    """A short sequence of BGR frames captured by the gateway."""

    frames: list[np.ndarray] = field(default_factory=list)
    fps: float = 15.0

    @property
    def duration_s(self) -> float:
        if not self.frames or self.fps <= 0:
            return 0.0
        return len(self.frames) / self.fps


class Agent(ABC):
    name: str

    @abstractmethod
    def analyze(self, window: AnalysisWindow) -> AgentObservation:
        """Produce a single observation summarising the window."""
