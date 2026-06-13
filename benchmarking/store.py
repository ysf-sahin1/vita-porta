"""Persistent latest-report store used by the API and CLI."""

from __future__ import annotations

import threading
from pathlib import Path

from benchmarking.models import BenchmarkReport
from orchestration.config import REPO_ROOT

_DEFAULT_PATH = REPO_ROOT / ".benchmark" / "latest.json"


class BenchmarkReportStore:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path is not None else _DEFAULT_PATH
        self._lock = threading.Lock()

    def save(self, report: BenchmarkReport) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self.path.write_text(report.model_dump_json(indent=2), encoding="utf-8")

    def load(self) -> BenchmarkReport | None:
        if not self.path.exists():
            return None
        with self._lock:
            return BenchmarkReport.model_validate_json(self.path.read_text(encoding="utf-8"))
