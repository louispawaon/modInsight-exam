from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class QueryIntent(BaseModel):
    raw_query: str
    query_type: str = "search"
    merchant: str | None = None
    category: str | None = None
    min_total: float | None = None
    max_total: float | None = None
    start_date: str | None = None
    end_date: str | None = None
    aggregation: str | None = None
    needs_semantic: bool = True
    merchants: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    item_terms: list[str] = Field(default_factory=list)
    date_text: str | None = None
    group_by: str | None = None
    sort_by: str | None = None
    limit: int | None = None
    confidence: float | None = None
    parse_source: str = "rule"
    temporal: dict = Field(default_factory=dict)

    @field_validator("query_type")
    @classmethod
    def validate_query_type(cls, value: str) -> str:
        allowed = {"search", "aggregation"}
        return value if value in allowed else "search"

    @field_validator("aggregation")
    @classmethod
    def validate_aggregation(cls, value: str | None) -> str | None:
        if value is None:
            return None
        allowed = {"sum", "avg", "count", "max", "min", "group"}
        return value if value in allowed else None

    @field_validator("group_by")
    @classmethod
    def validate_group_by(cls, value: str | None) -> str | None:
        if value is None:
            return None
        allowed = {"merchant", "category", "week"}
        return value if value in allowed else None


class QueryResult(BaseModel):
    answer: str
    answer_mode: str = "deterministic"
    matched_receipts: list[str] = Field(default_factory=list)
    matched_chunks: list[str] = Field(default_factory=list)
    totals: dict[str, float] = Field(default_factory=dict)
    facts: dict = Field(default_factory=dict)
    intent: dict = Field(default_factory=dict)
    retrieval: dict = Field(default_factory=dict)
    evidence_rows: list[dict] = Field(default_factory=list)

