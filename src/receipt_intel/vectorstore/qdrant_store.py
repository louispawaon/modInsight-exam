from __future__ import annotations

import hashlib

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

from receipt_intel.models import ReceiptChunk


class QdrantStore:
    def __init__(self, path: str, collection_name: str, vector_size: int) -> None:
        self.collection_name = collection_name
        self.client = QdrantClient(path=path)
        self._ensure_collection(vector_size)

    def _ensure_collection(self, vector_size: int) -> None:
        collections = {c.name for c in self.client.get_collections().collections}
        if self.collection_name in collections:
            return
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=rest.VectorParams(size=vector_size, distance=rest.Distance.COSINE),
        )

    def upsert_chunks(self, chunks: list[ReceiptChunk], vectors: list[list[float]]) -> None:
        points = []
        for i, chunk in enumerate(chunks):
            point_id = self._stable_int_id(chunk.chunk_id)
            points.append(
                rest.PointStruct(
                    id=point_id,
                    vector=vectors[i],
                    payload={
                        "content": chunk.content,
                        "chunk_type": chunk.chunk_type,
                        "chunk_id": chunk.chunk_id,
                        **chunk.metadata,
                    },
                )
            )
        self.client.upsert(collection_name=self.collection_name, points=points)

    def search(
        self,
        query_vector: list[float],
        limit: int,
        filters: rest.Filter | None = None,
    ) -> list[rest.ScoredPoint]:
        # qdrant-client APIs differ across versions (`search` vs `query_points`).
        if hasattr(self.client, "search"):
            return self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=filters,
                limit=limit,
            )

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=filters,
            limit=limit,
        )
        return list(response.points)

    def search_relaxed(self, query_vector: list[float], limit: int) -> list[rest.ScoredPoint]:
        return self.search(query_vector=query_vector, limit=limit, filters=None)

    def count(self, filters: rest.Filter | None = None) -> int:
        if hasattr(self.client, "count"):
            response = self.client.count(
                collection_name=self.collection_name,
                count_filter=filters,
                exact=False,
            )
            return int(response.count)
        return 0

    def reset(self, vector_size: int) -> None:
        collections = {c.name for c in self.client.get_collections().collections}
        if self.collection_name in collections:
            self.client.delete_collection(collection_name=self.collection_name)
        self._ensure_collection(vector_size)

    def delete_by_receipt_ids(self, receipt_ids: list[str]) -> None:
        if not receipt_ids:
            return
        delete_filter = rest.Filter(
            should=[
                rest.FieldCondition(key="receipt_id", match=rest.MatchValue(value=receipt_id))
                for receipt_id in receipt_ids
            ]
        )
        selector = rest.FilterSelector(filter=delete_filter)
        self.client.delete(collection_name=self.collection_name, points_selector=selector)

    def _stable_int_id(self, text_id: str) -> int:
        # Local Qdrant accepts numeric/UUID ids; hash text ids to deterministic int ids.
        digest = hashlib.sha1(text_id.encode("utf-8")).hexdigest()[:16]
        return int(digest, 16)

