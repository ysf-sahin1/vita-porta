"""RAG retriever for ESI case patterns.

ChromaDB is the production target; for hackathon-pace iteration we expose a
lightweight in-memory retriever that ranks seed cases by simple lexical
overlap. The supervisor only depends on the RagRetriever protocol — swapping
to Chroma is a constructor change.
"""

from __future__ import annotations

from typing import Protocol

from orchestration.rag.esi_cases import ESI_SEED_CASES


class RagRetriever(Protocol):
    async def retrieve(self, query: str, *, k: int = 3) -> list[str]: ...


class InMemoryRetriever:
    """Deterministic retriever — no embeddings, no disk, no network."""

    def __init__(self, cases: list[dict[str, str]] | None = None) -> None:
        self._cases = cases or ESI_SEED_CASES

    async def retrieve(self, query: str, *, k: int = 3) -> list[str]:
        tokens = {t.lower() for t in query.split() if len(t) > 2}
        scored: list[tuple[int, str]] = []
        for case in self._cases:
            pattern = case["pattern"]
            overlap = sum(1 for t in tokens if t in pattern.lower())
            scored.append((overlap, f"[{case['category']}] {pattern}"))

        scored.sort(key=lambda item: item[0], reverse=True)
        top = [snippet for score, snippet in scored[:k] if score > 0]
        if not top:
            top = [f"[{c['category']}] {c['pattern']}" for c in self._cases[:k]]
        return top


class ChromaRetriever:
    """ChromaDB-backed retriever using sentence-transformers embeddings.

    Lazy imports keep the gateway and tests lightweight when Chroma isn't
    installed or warmed up.
    """

    def __init__(self, persist_dir: str, embedding_model: str) -> None:
        self._persist_dir = persist_dir
        self._embedding_model = embedding_model
        self._collection = None

    def _ensure_collection(self):
        if self._collection is not None:
            return self._collection
        import chromadb
        from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

        client = chromadb.PersistentClient(path=self._persist_dir)
        embedder = SentenceTransformerEmbeddingFunction(model_name=self._embedding_model)
        self._collection = client.get_or_create_collection(
            name="esi_cases", embedding_function=embedder
        )
        return self._collection

    async def retrieve(self, query: str, *, k: int = 3) -> list[str]:
        collection = self._ensure_collection()
        result = collection.query(query_texts=[query], n_results=k)
        documents = result.get("documents") or [[]]
        return list(documents[0])


def build_default_retriever() -> RagRetriever:
    """Hackathon default: in-memory. Pilot phase swaps in ChromaRetriever."""
    import os
    return ChromaRetriever(
    persist_dir=os.getenv("CHROMA_PERSIST_DIR", "./.chroma"),
    embedding_model=os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
)
