from __future__ import annotations

from dataclasses import dataclass

from qdrant_client.http import models as rest

from receipt_intel.models import QueryIntent
from receipt_intel.query.filters import build_qdrant_filter
from receipt_intel.vectorstore import QdrantStore


@dataclass
class RetrievalConfig:
    limit: int = 12
    sparse_threshold: int = 4


def retrieve_hybrid(
    store: QdrantStore,
    query_vector: list[float],
    intent: QueryIntent,
    config: RetrievalConfig,
) -> list[rest.ScoredPoint]:
    points, _ = retrieve_hybrid_with_meta(store, query_vector, intent, config)
    return points


def retrieve_hybrid_with_meta(
    store: QdrantStore,
    query_vector: list[float],
    intent: QueryIntent,
    config: RetrievalConfig,
) -> tuple[list[rest.ScoredPoint], dict[str, int]]:
    strict_filter = build_qdrant_filter(intent)
    strict = store.search(query_vector=query_vector, limit=config.limit, filters=strict_filter)

    fallback: list[rest.ScoredPoint] = []
    should_fallback = len(strict) < config.sparse_threshold
    if intent.item_terms and strict:
        # For concept/term queries, avoid broad fallback when strict already has evidence.
        should_fallback = False
    if should_fallback:
        fallback = store.search_relaxed(query_vector=query_vector, limit=config.limit)

    final = _fuse_dedupe_balance(strict, fallback, config.limit)
    meta = {
        "strict_count": len(strict),
        "fallback_count": len(fallback),
        "final_count": len(final),
        "sparse_threshold": config.sparse_threshold,
        "used_fallback": 1 if bool(fallback) else 0,
        "item_terms_count": len(intent.item_terms),
        "evidence_quality": _evidence_quality(len(strict), len(fallback)),
    }
    return final, meta


def _fuse_dedupe_balance(
    strict: list[rest.ScoredPoint],
    fallback: list[rest.ScoredPoint],
    limit: int,
) -> list[rest.ScoredPoint]:
    by_chunk: dict[str, tuple[float, rest.ScoredPoint]] = {}

    for point in strict:
        payload = _payload(point)
        chunk_id = str(payload.get("chunk_id", point.id))
        score = float(getattr(point, "score", 0.0)) + 0.25
        if payload.get("chunk_type") == "receipt":
            score += 0.05
        by_chunk[chunk_id] = (score, point)

    for point in fallback:
        payload = _payload(point)
        chunk_id = str(payload.get("chunk_id", point.id))
        score = float(getattr(point, "score", 0.0))
        existing = by_chunk.get(chunk_id)
        if not existing or score > existing[0]:
            by_chunk[chunk_id] = (score, point)

    ordered = [item[1] for item in sorted(by_chunk.values(), key=lambda x: x[0], reverse=True)]

    # Receipt-level dedupe and chunk-type balancing.
    receipt_selected: set[str] = set()
    receipt_chunks: list[rest.ScoredPoint] = []
    item_chunks: list[rest.ScoredPoint] = []
    for point in ordered:
        payload = _payload(point)
        receipt_id = str(payload.get("receipt_id", ""))
        if receipt_id in receipt_selected and payload.get("chunk_type") == "receipt":
            continue
        if payload.get("chunk_type") == "receipt":
            receipt_chunks.append(point)
            receipt_selected.add(receipt_id)
        else:
            item_chunks.append(point)

    final: list[rest.ScoredPoint] = []
    while (receipt_chunks or item_chunks) and len(final) < limit:
        if receipt_chunks:
            final.append(receipt_chunks.pop(0))
        if item_chunks and len(final) < limit:
            final.append(item_chunks.pop(0))
    return final[:limit]


def _payload(point: rest.ScoredPoint) -> dict:
    payload = getattr(point, "payload", None)
    return payload if isinstance(payload, dict) else {}


def _evidence_quality(strict_count: int, fallback_count: int) -> str:
    if strict_count > 0 and fallback_count == 0:
        return "strict_only"
    if strict_count > 0 and fallback_count > 0:
        return "mixed"
    if strict_count == 0 and fallback_count > 0:
        return "fallback_only"
    return "none"

