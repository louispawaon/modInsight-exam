from __future__ import annotations

import logging
from pathlib import Path

import json

from receipt_intel.config import get_settings
from receipt_intel.embeddings import OllamaEmbedder
from receipt_intel.models import QueryResult
from receipt_intel.query.humanize import humanize_answer_with_ollama
from receipt_intel.query.intent import parse_query_intent
from receipt_intel.query.retrieval import RetrievalConfig, retrieve_hybrid_with_meta
from receipt_intel.query.synthesis import synthesize_answer
from receipt_intel.query.temporal import infer_dataset_bounds
from receipt_intel.vectorstore import QdrantStore


logger = logging.getLogger(__name__)


class QueryEngine:
    def __init__(self, store: QdrantStore, embedder: OllamaEmbedder, retrieval_k: int = 10) -> None:
        self.store = store
        self.embedder = embedder
        self.retrieval_k = retrieval_k
        settings = get_settings()
        self.answer_style = settings.answer_style.lower().strip()
        self.ollama_base_url = settings.ollama_base_url
        self.ollama_chat_model = settings.ollama_chat_model
        self.ollama_answer_timeout_s = settings.ollama_answer_timeout_s
        self.retrieval_config = RetrievalConfig(
            limit=retrieval_k,
            sparse_threshold=settings.retrieval_sparse_threshold,
        )

    def query(self, raw_query: str) -> QueryResult:
        metadata_response = _try_metadata_shortcuts(raw_query)
        if metadata_response is not None:
            return metadata_response

        intent = parse_query_intent(raw_query)
        logger.debug("Parsed intent via %s: %s", intent.parse_source, intent.model_dump())
        query_vector = self.embedder.embed_query(raw_query)
        points, retrieval_meta = retrieve_hybrid_with_meta(
            self.store, query_vector, intent, self.retrieval_config
        )
        retrieval_meta["intent_family"] = _intent_family(intent.parse_source)
        answer, totals, facts = synthesize_answer(intent, points)
        evidence_rows = self._build_evidence_rows(points)
        answer_mode = "deterministic"

        if self.answer_style == "hybrid":
            rewritten = humanize_answer_with_ollama(
                deterministic_answer=answer,
                facts=facts,
                base_url=self.ollama_base_url,
                model=self.ollama_chat_model,
                timeout_s=self.ollama_answer_timeout_s,
            )
            if rewritten:
                answer = rewritten
                answer_mode = "humanized"

        matched_receipts = sorted(
            {str(p.payload.get("receipt_id")) for p in points if p.payload.get("receipt_id")}
        )
        matched_chunks = [str(p.id) for p in points]

        return QueryResult(
            answer=answer,
            matched_receipts=matched_receipts,
            matched_chunks=matched_chunks,
            totals=totals,
            answer_mode=answer_mode,
            facts=facts,
            intent=intent.model_dump(),
            retrieval=retrieval_meta,
            evidence_rows=evidence_rows,
        )

    def _build_evidence_rows(self, points: list) -> list[dict]:
        rows: list[dict] = []
        for point in points:
            payload = point.payload if isinstance(point.payload, dict) else {}
            rows.append(
                {
                    "receipt_id": str(payload.get("receipt_id", "")),
                    "chunk_id": str(payload.get("chunk_id", point.id)),
                    "merchant": str(payload.get("merchant", "")),
                    "category": str(payload.get("category", "")),
                    "date": str(payload.get("date", "")),
                    "total_amount": float(payload.get("total_amount", 0.0) or 0.0),
                    "item_name": str(payload.get("item_name", "")),
                    "chunk_type": str(payload.get("chunk_type", "")),
                }
            )
        return rows


def _is_year_coverage_query(raw_query: str) -> bool:
    text = raw_query.lower()
    has_year = "year" in text or "years" in text
    has_range = "range" in text or "ranges" in text or "present" in text or "available" in text
    return has_year and has_range


def _try_metadata_shortcuts(raw_query: str) -> QueryResult | None:
    text = raw_query.lower()
    if _is_year_coverage_query(raw_query):
        return _answer_year_coverage(raw_query)
    if "earliest" in text and "date" in text:
        return _answer_date_bound(raw_query, which="earliest")
    if ("latest" in text or "most recent" in text) and "date" in text:
        return _answer_date_bound(raw_query, which="latest")
    if "unique merchant" in text or ("merchant" in text and ("how many" in text or "list" in text)):
        return _answer_unique_values(raw_query, field="merchant")
    if "unique categor" in text or ("categor" in text and ("how many" in text or "list" in text)):
        return _answer_unique_values(raw_query, field="category")
    return None


def _answer_year_coverage(raw_query: str) -> QueryResult:
    min_date, max_date = infer_dataset_bounds()
    start_year = min_date.year
    end_year = max_date.year
    years = list(range(start_year, end_year + 1))
    years_text = ", ".join(str(year) for year in years)
    answer = f"Years present in the receipts: {years_text} (date range {min_date.isoformat()} to {max_date.isoformat()})."
    facts = {
        "query_type": "metadata",
        "metric": "year_coverage",
        "start_date": min_date.isoformat(),
        "end_date": max_date.isoformat(),
        "years": years,
    }
    return QueryResult(
        answer=answer,
        answer_mode="deterministic",
        matched_receipts=[],
        matched_chunks=[],
        totals={},
        facts=facts,
        intent={"raw_query": raw_query, "query_type": "metadata", "parse_source": "rule"},
        retrieval={
            "mode": "metadata_shortcut",
            "reason": "year_coverage_query",
            "intent_family": "core_rule",
            "evidence_quality": "metadata",
        },
        evidence_rows=[],
    )


def _answer_date_bound(raw_query: str, *, which: str) -> QueryResult:
    min_date, max_date = infer_dataset_bounds()
    chosen = min_date if which == "earliest" else max_date
    answer = f"The {which} receipt date is {chosen.isoformat()}."
    facts = {"query_type": "metadata", "metric": f"{which}_date", "value": chosen.isoformat()}
    return QueryResult(
        answer=answer,
        answer_mode="deterministic",
        facts=facts,
        intent={"raw_query": raw_query, "query_type": "metadata", "parse_source": "rule"},
        retrieval={
            "mode": "metadata_shortcut",
            "reason": f"{which}_date_query",
            "intent_family": "core_rule",
            "evidence_quality": "metadata",
        },
    )


def _answer_unique_values(raw_query: str, *, field: str) -> QueryResult:
    values = _load_unique_values(field)
    if "how many" in raw_query.lower() or "count" in raw_query.lower():
        answer = f"There are {len(values)} unique {field}s in the receipts."
    else:
        answer = f"Unique {field}s: {', '.join(values[:25])}."
    facts = {"query_type": "metadata", "metric": f"unique_{field}", "count": len(values), "values": values[:50]}
    return QueryResult(
        answer=answer,
        answer_mode="deterministic",
        facts=facts,
        intent={"raw_query": raw_query, "query_type": "metadata", "parse_source": "rule"},
        retrieval={
            "mode": "metadata_shortcut",
            "reason": f"unique_{field}_query",
            "intent_family": "core_rule",
            "evidence_quality": "metadata",
        },
    )


def _load_unique_values(field: str) -> list[str]:
    settings = get_settings()
    parsed_path: Path = settings.parsed_output_path
    values: set[str] = set()
    if not parsed_path.exists():
        return []
    with parsed_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            payload = json.loads(line)
            raw = str(payload.get(field, "")).strip()
            if raw:
                values.add(raw)
    return sorted(values)


def _intent_family(parse_source: str) -> str:
    if "concept" in parse_source:
        return "semantic_concept"
    if parse_source.startswith("rule"):
        return "core_rule"
    return "llm_or_hybrid"

