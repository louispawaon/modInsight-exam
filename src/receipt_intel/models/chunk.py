from __future__ import annotations

from pydantic import BaseModel, Field


class ReceiptChunk(BaseModel):
    chunk_id: str
    receipt_id: str
    content: str
    chunk_type: str
    metadata: dict[str, str | int | float | None] = Field(default_factory=dict)

