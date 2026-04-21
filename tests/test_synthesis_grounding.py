from __future__ import annotations

from types import SimpleNamespace

from receipt_intel.models import QueryIntent
from receipt_intel.query.synthesis import synthesize_answer


def _point(receipt_id: str, merchant: str, total: float, date: str, chunk_id: str = "chunk-1"):
    return SimpleNamespace(
        payload={
            "receipt_id": receipt_id,
            "merchant": merchant,
            "total_amount": total,
            "date": date,
            "chunk_id": chunk_id,
            "category": "grocery",
            "item_name": "item",
        }
    )


def test_aggregation_synthesis_contains_evidence_references() -> None:
    intent = QueryIntent(raw_query="How much?", query_type="aggregation", aggregation="sum")
    points = [
        _point("receipt_001", "Whole Foods", 40.32, "2023-12-01", "c1"),
        _point("receipt_002", "Whole Foods", 22.10, "2023-12-03", "c2"),
    ]
    answer, totals, facts = synthesize_answer(intent, points)
    assert "You spent $" in answer
    assert "receipt_001" in answer
    assert totals["sum"] == 62.42
    assert facts["receipt_count"] == 2


def test_listing_synthesis_mentions_top_matches() -> None:
    intent = QueryIntent(raw_query="show receipts", query_type="search")
    points = [_point("receipt_010", "Target", 70.0, "2023-11-22", "c10")]
    answer, _, facts = synthesize_answer(intent, points)
    assert "Top matches" in answer
    assert "receipt_010" in answer
    assert facts["receipt_count"] == 1


def test_aggregation_dedupes_duplicate_receipt_chunks() -> None:
    intent = QueryIntent(raw_query="How much?", query_type="aggregation", aggregation="sum")
    points = [
        _point("receipt_001", "Whole Foods", 40.32, "2023-12-01", "c1"),
        _point("receipt_001", "Whole Foods", 40.32, "2023-12-01", "c1_item"),
        _point("receipt_002", "Whole Foods", 22.10, "2023-12-03", "c2"),
    ]
    _, totals, facts = synthesize_answer(intent, points)
    assert totals["sum"] == 62.42
    assert totals["count"] == 2.0
    assert facts["receipt_count"] == 2


def test_group_by_week_supported() -> None:
    intent = QueryIntent(
        raw_query="How much per week?",
        query_type="aggregation",
        aggregation="group",
        group_by="week",
    )
    points = [
        _point("receipt_001", "Whole Foods", 40.32, "2023-12-01", "c1"),
        _point("receipt_002", "Whole Foods", 22.10, "2023-12-03", "c2"),
    ]
    answer, _, _ = synthesize_answer(intent, points)
    assert "Top by week:" in answer


def test_no_evidence_message_includes_filters() -> None:
    intent = QueryIntent(raw_query="find grocery receipts", query_type="search", category="grocery")
    answer, _, _ = synthesize_answer(intent, [])
    assert "filters:" in answer


def test_listing_includes_applied_filters() -> None:
    intent = QueryIntent(raw_query="show receipts", query_type="search", item_terms=["vitamin"])
    points = [_point("receipt_010", "Target", 70.0, "2023-11-22", "c10")]
    answer, _, _ = synthesize_answer(intent, points)
    assert "Not enough direct item evidence" in answer

