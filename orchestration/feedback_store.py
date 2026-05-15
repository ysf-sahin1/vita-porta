"""Hemşire verdict'lerinin kalıcı kaydı + benzerlik sorgusu.

Pilot fazda ChromaDB'ye taşınacak; hackathon için JSON append-only dosya +
in-memory token-overlap scoring yeterli. Mevcut RAG retriever de aynı
mantığı kullanıyor — tutarlı, deterministik, kurulum gerektirmez.

Veri akışı:
    Hemşire ✓/✗/✎ verir → frontend POST /api/triage/feedback
        → FeedbackStore.save() → satır olarak .feedback/feedbacks.jsonl
    Yeni vaka geldiğinde → Supervisor retrieve_feedback node →
        FeedbackStore.query_similar(signals_text) → HistoricalFeedback[]
        → prompt'a "Geçmiş Hemşire Kararları" snippet'i + TriageDecision'a iliştirilir.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Protocol

from orchestration.config import REPO_ROOT
from orchestration.schemas import HistoricalFeedback, NurseFeedback

logger = logging.getLogger(__name__)

_DEFAULT_PATH = REPO_ROOT / ".feedback" / "feedbacks.jsonl"


class FeedbackStore(Protocol):
    def save(self, feedback: NurseFeedback) -> None: ...
    def list_all(self) -> list[NurseFeedback]: ...
    def query_similar(self, signals_text: str, *, k: int = 3) -> list[HistoricalFeedback]: ...
    def clear(self) -> None: ...


class JsonFeedbackStore:
    """Append-only JSONL dosyası. Thread-safe (basit lock); süreçler arası
    senkronizasyon yok — tek backend süreci varsayımı geçerli."""

    def __init__(self, path: Path | str | None = None) -> None:
        self._path = Path(path) if path is not None else _DEFAULT_PATH
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------- public

    def save(self, feedback: NurseFeedback) -> None:
        """Aynı `decision_id` daha önce varsa eski satırlar mantıksal olarak
        eskiyor; basit tutmak için sadece append. ``list_all`` decision_id
        bazında son kaydı döndürmek için filtreleme yapar."""

        line = feedback.model_dump_json()
        with self._lock:
            with self._path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")

    def list_all(self) -> list[NurseFeedback]:
        if not self._path.exists():
            return []

        latest: dict[str, NurseFeedback] = {}
        with self._lock:
            with self._path.open("r", encoding="utf-8") as fh:
                for raw_line in fh:
                    raw_line = raw_line.strip()
                    if not raw_line:
                        continue
                    try:
                        record = NurseFeedback.model_validate_json(raw_line)
                    except Exception as exc:  # noqa: BLE001 — defensive on hand-edits
                        logger.warning("FeedbackStore: satır atlandı (%s): %s", exc, raw_line[:80])
                        continue
                    # decision_id başına son kaydı tut (override mantığı)
                    prev = latest.get(record.decision_id)
                    if prev is None or record.feedback_at >= prev.feedback_at:
                        latest[record.decision_id] = record

        return sorted(latest.values(), key=lambda r: r.feedback_at, reverse=True)

    def clear(self) -> None:
        """Tüm hemşire feedback'lerini siler. Geri alınamaz."""

        with self._lock:
            if self._path.exists():
                self._path.unlink()

    def query_similar(self, signals_text: str, *, k: int = 3) -> list[HistoricalFeedback]:
        """Token-overlap scoring — RAG retriever'la aynı yaklaşım."""

        tokens = _tokenize(signals_text)
        if not tokens:
            return []

        scored: list[tuple[float, NurseFeedback]] = []
        for record in self.list_all():
            ref_tokens = _tokenize(record.signals_summary)
            if not ref_tokens:
                continue
            overlap = len(tokens & ref_tokens)
            if overlap == 0:
                continue
            similarity = overlap / max(1, len(tokens | ref_tokens))  # Jaccard
            scored.append((similarity, record))

        scored.sort(key=lambda item: item[0], reverse=True)
        return [record.to_historical(similarity_score=round(score, 3)) for score, record in scored[:k]]


def _tokenize(text: str) -> set[str]:
    """Türkçe-uyumlu basit tokenize: lowercase + 3+ karakter."""

    return {tok.lower() for tok in text.replace("\n", " ").split() if len(tok) > 2}


def build_default_store() -> FeedbackStore:
    """Hackathon default: JSON dosyası. Pilot için ChromaDB swap'ı kolay."""

    return JsonFeedbackStore()
