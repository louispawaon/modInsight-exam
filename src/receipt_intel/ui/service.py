from __future__ import annotations

import time
from pathlib import Path

import httpx

from receipt_intel.config import Settings, get_settings
from receipt_intel.embeddings import OllamaEmbedder
from receipt_intel.evaluation import run_eval_scenarios
from receipt_intel.pipeline import ingest_and_index
from receipt_intel.query import QueryEngine
from receipt_intel.vectorstore import QdrantStore


def build_engine_from_settings() -> QueryEngine:
    settings = get_settings()
    embedder = OllamaEmbedder(settings.ollama_embedding_model, settings.ollama_base_url)
    probe_vector = embedder.embed_query("receipt probe")
    store = QdrantStore(
        path=str(settings.qdrant_path),
        collection_name=settings.qdrant_collection,
        vector_size=len(probe_vector),
    )
    return QueryEngine(store=store, embedder=embedder, retrieval_k=settings.retrieval_k)


def run_query(raw_query: str) -> dict:
    engine = build_engine_from_settings()
    result = engine.query(raw_query)
    return result.model_dump()


def run_ingest() -> dict:
    settings = get_settings()
    started = time.perf_counter()
    ingest_and_index(settings)
    elapsed = time.perf_counter() - started
    return {"ok": True, "elapsed_s": round(elapsed, 2), "manifest_path": str(settings.index_manifest_path)}


def run_evaluation() -> dict:
    engine = build_engine_from_settings()
    return run_eval_scenarios(engine)


def health_check() -> dict:
    settings = get_settings()
    ollama_ok = _check_ollama(settings.ollama_base_url)
    manifest_exists = settings.index_manifest_path.exists()
    qdrant_exists = settings.qdrant_path.exists()
    return {
        "ollama_ok": ollama_ok,
        "manifest_exists": manifest_exists,
        "qdrant_exists": qdrant_exists,
        "qdrant_path": str(settings.qdrant_path),
        "manifest_path": str(settings.index_manifest_path),
    }


def get_config_snapshot() -> dict:
    settings = get_settings()
    return {
        "embedding_model": settings.ollama_embedding_model,
        "chat_model": settings.ollama_chat_model,
        "collection": settings.qdrant_collection,
        "chunking_strategy": settings.chunking_strategy,
        "retrieval_k": settings.retrieval_k,
        "sparse_threshold": settings.retrieval_sparse_threshold,
        "answer_style": settings.answer_style,
    }


def _check_ollama(base_url: str) -> bool:
    try:
        response = httpx.get(f"{base_url.rstrip('/')}/api/tags", timeout=3)
        return response.status_code == 200
    except Exception:
        return False

