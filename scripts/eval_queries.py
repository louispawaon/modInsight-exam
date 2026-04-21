import json
from pathlib import Path

from receipt_intel.config import get_settings
from receipt_intel.embeddings import OllamaEmbedder
from receipt_intel.evaluation import run_eval_scenarios
from receipt_intel.query import QueryEngine
from receipt_intel.vectorstore import QdrantStore


def main() -> None:
    settings = get_settings()
    embedder = OllamaEmbedder(settings.ollama_embedding_model, settings.ollama_base_url)
    probe_vector = embedder.embed_query("receipt probe")
    store = QdrantStore(
        path=str(settings.qdrant_path),
        collection_name=settings.qdrant_collection,
        vector_size=len(probe_vector),
    )
    engine = QueryEngine(store=store, embedder=embedder, retrieval_k=settings.retrieval_k)

    output_path = Path("data/eval_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    report = run_eval_scenarios(engine)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        f"Wrote evaluation report to {output_path} | "
        f"passed={report['summary']['passed']}/{report['summary']['total']}"
    )
if __name__ == "__main__":
    main()

