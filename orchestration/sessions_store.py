"""Hemşire mesai oturumlarının kalıcı kaydı.

Append-only JSONL — `decisions_store` / `feedback_store` ile aynı pattern.
Aynı `session_id` birden fazla satıra yazılabilir (start → end overrider);
``list_all`` her oturum için son satırı tutar.
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from orchestration.config import REPO_ROOT
from orchestration.schemas import NurseSession

logger = logging.getLogger(__name__)

_DEFAULT_PATH = REPO_ROOT / ".sessions" / "sessions.jsonl"


class SessionStore(Protocol):
    def start(self, *, first_name: str, last_name: str, hospital: str) -> NurseSession: ...
    def end(self, session_id: str) -> NurseSession | None: ...
    def list_all(self) -> list[NurseSession]: ...
    def clear(self) -> None: ...


class JsonSessionStore:
    def __init__(self, path: Path | str | None = None) -> None:
        self._path = Path(path) if path is not None else _DEFAULT_PATH
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def start(self, *, first_name: str, last_name: str, hospital: str) -> NurseSession:
        record = NurseSession(
            session_id=uuid4().hex,
            nurse_first_name=first_name.strip(),
            nurse_last_name=last_name.strip(),
            hospital=hospital.strip(),
        )
        self._append(record)
        return record

    def end(self, session_id: str) -> NurseSession | None:
        """``session_id``'ye karşılık gelen son oturuma çıkış damgası yazar.

        Oturum bulunamazsa ``None`` döner; UI tarafı buna sessizce göz yumar
        (eski/temizlenmiş session_id beacon'ları için).
        """

        latest = {s.session_id: s for s in self.list_all()}
        existing = latest.get(session_id)
        if existing is None:
            return None
        if existing.logout_at is not None:
            return existing  # idempotent — zaten kapalı
        closed = existing.model_copy(update={"logout_at": datetime.now(timezone.utc)})
        self._append(closed)
        return closed

    def list_all(self) -> list[NurseSession]:
        if not self._path.exists():
            return []

        latest: dict[str, NurseSession] = {}
        with self._lock:
            with self._path.open("r", encoding="utf-8") as fh:
                for raw_line in fh:
                    raw_line = raw_line.strip()
                    if not raw_line:
                        continue
                    try:
                        record = NurseSession.model_validate_json(raw_line)
                    except Exception as exc:  # noqa: BLE001 — defensive on hand-edits
                        logger.warning(
                            "SessionStore: satır atlandı (%s): %s", exc, raw_line[:80]
                        )
                        continue
                    prev = latest.get(record.session_id)
                    # Aynı session_id için: logout_at != None olan satır openi geçersiz kılar;
                    # iki kapalı satır arasında en son login_at/logout_at geçerli.
                    if prev is None:
                        latest[record.session_id] = record
                    elif record.logout_at is not None:
                        latest[record.session_id] = record

        return sorted(latest.values(), key=lambda r: r.login_at, reverse=True)

    def clear(self) -> None:
        with self._lock:
            if self._path.exists():
                self._path.unlink()

    def _append(self, record: NurseSession) -> None:
        line = record.model_dump_json()
        with self._lock:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")


def build_default_session_store() -> SessionStore:
    return JsonSessionStore()
