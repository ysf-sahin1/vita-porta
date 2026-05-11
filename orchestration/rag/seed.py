"""One-shot script to seed the ChromaDB collection with ESI case patterns."""

from __future__ import annotations

from orchestration.config import get_settings
from orchestration.rag.esi_cases import ESI_SEED_CASES


def seed() -> int:
    import chromadb
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

    settings = get_settings()
    client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    embedder = SentenceTransformerEmbeddingFunction(model_name=settings.embedding_model)
    collection = client.get_or_create_collection(name="esi_cases", embedding_function=embedder)

    collection.upsert(
        ids=[case["id"] for case in ESI_SEED_CASES],
        documents=[f"[{case['category']}] {case['pattern']}" for case in ESI_SEED_CASES],
        metadatas=[{"category": case["category"]} for case in ESI_SEED_CASES],
    )
    return collection.count()


if __name__ == "__main__":
    count = seed()
    print(f"esi_cases koleksiyonu güncellendi. Toplam belge: {count}")
