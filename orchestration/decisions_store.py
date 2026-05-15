"""Karar kayıtlarının kalıcı saklanması — verdict'ten bağımsız.

Hemşire henüz onay/red/değiştir yapmamış bir karar bile burada saklanır;
frontend sayfası yenilendiğinde, oturum değişse bile geçmiş kararlar
listede kalır. ``FeedbackStore`` ile birlikte iki tablo gibi düşün:
*decisions* = sistemin önerdiği kararlar, *feedback* = hemşire kararları.

JSON append-only; aynı ``decision_id`` tekrar yazılırsa ``list_all`` son
kayda öncelik verir (override mantığı).
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Protocol

from orchestration.config import REPO_ROOT
from orchestration.schemas import DecisionRecord

logger = logging.getLogger(__name__)

_DEFAULT_PATH = REPO_ROOT / ".decisions" / "decisions.jsonl"


class DecisionStore(Protocol):
    def save(self, record: DecisionRecord) -> None: ...
    def list_all(self) -> list[DecisionRecord]: ...
    def clear(self) -> None: ...


class JsonDecisionStore:
    def __init__(self, path: Path | str | None = None) -> None:
        self._path = Path(path) if path is not None else _DEFAULT_PATH
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, record: DecisionRecord) -> None:
        line = record.model_dump_json()
        with self._lock:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")

    def list_all(self) -> list[DecisionRecord]:
        if not self._path.exists():
            return []

        latest: dict[str, DecisionRecord] = {}
        with self._lock:
            with self._path.open("r", encoding="utf-8") as fh:
                for raw_line in fh:
                    raw_line = raw_line.strip()
                    if not raw_line:
                        continue
                    try:
                        record = DecisionRecord.model_validate_json(raw_line)
                    except Exception as exc:  # noqa: BLE001 — defensive on hand-edits
                        logger.warning(
                            "DecisionStore: satır atlandı (%s): %s", exc, raw_line[:80]
                        )
                        continue
                    prev = latest.get(record.decision_id)
                    if prev is None or record.decision.decided_at >= prev.decision.decided_at:
                        latest[record.decision_id] = record

        return sorted(
            latest.values(),
            key=lambda r: r.decision.decided_at,
            reverse=True,
        )

    def clear(self) -> None:
        with self._lock:
            if self._path.exists():
                self._path.unlink()


def build_default_decision_store() -> DecisionStore:
    return JsonDecisionStore()
