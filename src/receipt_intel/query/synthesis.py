from __future__ import annotations

from typing import Any

from qdrant_client.http import models as rest

from receipt_intel.analytics import (
    aggregate_totals,
    dedupe_receipt_rows,
    group_totals_by_field,
    group_totals_by_week,
)
from receipt_intel.models import QueryIntent


def synthesize_answer(
    intent: QueryIntent, points: list[rest.ScoredPoint]
) -> tuple[str, dict[str, float], dict[str, Any]]:
    payloads = [_payload(point) for point in points]
    deduped_payloads = dedupe_receipt_rows(payloads)
    totals = aggregate_totals(deduped_payloads)
    evidence = _evidence_rows(deduped_payloads)
    facts = _build_facts(intent, totals, evidence)
    filters = _describe_filters(intent)

    if not evidence:
        return f"No matching receipts found for filters: {filters}.", totals, facts

    if intent.query_type == "aggregation":
        return _synthesize_aggregation(intent, evidence, totals, filters), totals, facts
    if intent.item_terms:
        lexical_hits = [row for row in evidence if any(term in row["item_name"].lower() for term in intent.item_terms)]
        if not lexical_hits:
            return f"Not enough direct item evidence for concept filters: {filters}.", totals, facts
    return _synthesize_listing(evidence, filters), totals, facts


def _synthesize_aggregation(
    intent: QueryIntent, evidence: list[dict[str, Any]], totals: dict[str, float], filters: str
) -> str:
    unique_receipts = {row["receipt_id"] for row in evidence if row["receipt_id"]}
    agg = intent.aggregation or "sum"
    lines = []
    if agg == "sum":
        lines.append(f"You spent ${totals['sum']:.2f} across {len(unique_receipts)} receipts.")
    elif agg == "avg":
        lines.append(f"Your average receipt total is ${totals['avg']:.2f} across {len(unique_receipts)} receipts.")
    elif agg == "count":
        lines.append(f"There are {int(totals['count'])} matching receipts.")
    elif agg == "max":
        max_total = max((row["total_amount"] for row in evidence), default=0.0)
        lines.append(f"The highest matching receipt total is ${max_total:.2f}.")
    elif agg == "min":
        min_total = min((row["total_amount"] for row in evidence), default=0.0)
        lines.append(f"The lowest matching receipt total is ${min_total:.2f}.")
    else:
        lines.append(
            f"Matched {len(unique_receipts)} receipts with total ${totals['sum']:.2f} "
            f"and average ${totals['avg']:.2f}."
        )

    grouped: dict[str, float] = {}
    if intent.group_by in {"merchant", "category"}:
        grouped = group_totals_by_field(evidence, intent.group_by)
    elif intent.group_by == "week":
        grouped = group_totals_by_week(evidence)

    if grouped:
        top = sorted(grouped.items(), key=lambda x: x[1], reverse=True)[:5]
        parts = [f"{name}: ${amount:.2f}" for name, amount in top]
        lines.append(f"Top by {intent.group_by}: " + "; ".join(parts) + ".")
    lines.append(f"Filters used: {filters}.")
    lines.append(_format_evidence_suffix(evidence))
    return " ".join(lines)


def _synthesize_listing(evidence: list[dict[str, Any]], filters: str) -> str:
    top_rows = evidence[:5]
    parts = []
    for row in top_rows:
        parts.append(
            f"{row['receipt_id']} ({row['date']}) {row['merchant']} ${row['total_amount']:.2f}"
        )
    return f"Found {len(evidence)} evidence rows for filters ({filters}). Top matches: " + " | ".join(parts)


def _format_evidence_suffix(evidence: list[dict[str, Any]]) -> str:
    top_rows = evidence[:3]
    refs = [f"{row['receipt_id']} @ {row['date']} = ${row['total_amount']:.2f}" for row in top_rows]
    return "Example receipts: " + ", ".join(refs) + "."


def _evidence_rows(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for payload in payloads:
        rows.append(
            {
                "receipt_id": str(payload.get("receipt_id", "")),
                "chunk_id": str(payload.get("chunk_id", "")),
                "date": str(payload.get("date", "")),
                "merchant": str(payload.get("merchant", "")),
                "category": str(payload.get("category", "")),
                "item_name": str(payload.get("item_name", "")),
                "total_amount": float(payload.get("total_amount", 0.0) or 0.0),
            }
        )
    return rows


def _payload(point: rest.ScoredPoint) -> dict[str, Any]:
    payload = getattr(point, "payload", None)
    return payload if isinstance(payload, dict) else {}


def _build_facts(intent: QueryIntent, totals: dict[str, float], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    unique_receipts = sorted({row["receipt_id"] for row in evidence if row["receipt_id"]})
    evidence_preview = [
        {
            "receipt_id": row["receipt_id"],
            "date": row["date"],
            "merchant": row["merchant"],
            "total_amount": row["total_amount"],
        }
        for row in evidence[:5]
    ]
    return {
        "query_type": intent.query_type,
        "aggregation": intent.aggregation,
        "group_by": intent.group_by,
        "item_terms": intent.item_terms,
        "receipt_count": len(unique_receipts),
        "receipt_ids": unique_receipts[:10],
        "totals": totals,
        "evidence_preview": evidence_preview,
    }


def _describe_filters(intent: QueryIntent) -> str:
    parts: list[str] = []
    if intent.categories:
        parts.append(f"categories={intent.categories}")
    elif intent.category:
        parts.append(f"category={intent.category}")
    if intent.merchants:
        parts.append(f"merchants={intent.merchants}")
    elif intent.merchant:
        parts.append(f"merchant={intent.merchant}")
    if intent.start_date or intent.end_date:
        parts.append(f"date={intent.start_date or '*'}..{intent.end_date or '*'}")
    if intent.min_total is not None:
        parts.append(f"min_total={intent.min_total}")
    if intent.max_total is not None:
        parts.append(f"max_total={intent.max_total}")
    if intent.item_terms:
        parts.append(f"item_terms={intent.item_terms}")
    return ", ".join(parts) if parts else "none"

