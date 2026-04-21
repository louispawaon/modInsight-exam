from __future__ import annotations

from types import SimpleNamespace

from receipt_intel.models import QueryIntent
from receipt_intel.query.retrieval import RetrievalConfig, retrieve_hybrid


class _FakeStore:
    def __init__(self, strict_points, fallback_points):
        self.strict_points = strict_points
        self.fallback_points = fallback_points

    def search(self, query_vector, limit, filters=None):
        return self.strict_points[:limit]

    def search_relaxed(self, query_vector, limit):
        return self.fallback_points[:limit]


def _point(chunk_id: str, receipt_id: str, score: float, chunk_type: str = "item"):
    return SimpleNamespace(
        id=f"id-{chunk_id}",
        score=score,
        payload={"chunk_id": chunk_id, "receipt_id": receipt_id, "chunk_type": chunk_type, "total_amount": 10.0},
    )


def test_hybrid_retrieval_uses_fallback_and_balances_chunks() -> None:
    strict = [_point("a1", "r1", 0.9, "receipt")]
    fallback = [
        _point("b1", "r1", 0.8, "item"),
        _point("b2", "r2", 0.75, "receipt"),
        _point("b3", "r2", 0.7, "item"),
    ]
    store = _FakeStore(strict, fallback)
    intent = QueryIntent(raw_query="test")
    points = retrieve_hybrid(store, [0.1, 0.2], intent, RetrievalConfig(limit=4, sparse_threshold=2))

    assert len(points) >= 2
    types = [p.payload["chunk_type"] for p in points]
    assert "receipt" in types
    assert "item" in types

