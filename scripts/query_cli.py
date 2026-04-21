from receipt_intel.config import get_settings
from receipt_intel.embeddings import OllamaEmbedder
from receipt_intel.query import QueryEngine
from receipt_intel.vectorstore import QdrantStore


def build_engine() -> QueryEngine:
    settings = get_settings()
    embedder = OllamaEmbedder(settings.ollama_embedding_model, settings.ollama_base_url)
    probe_vector = embedder.embed_query("receipt probe")
    store = QdrantStore(
        path=str(settings.qdrant_path),
        collection_name=settings.qdrant_collection,
        vector_size=len(probe_vector),
    )
    return QueryEngine(store=store, embedder=embedder, retrieval_k=settings.retrieval_k)


def main() -> None:
    engine = build_engine()
    print("Receipt query CLI. Type 'exit' to quit.")
    while True:
        raw = input("> ").strip()
        if raw.lower() in {"exit", "quit"}:
            break
        result = engine.query(raw)
        print(result.answer)
        if result.matched_receipts:
            print("Receipts:", ", ".join(result.matched_receipts[:10]))
        if result.totals.get("count"):
            print("Totals:", result.totals)


if __name__ == "__main__":
    main()

