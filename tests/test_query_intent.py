from __future__ import annotations

from receipt_intel.query.intent import parse_query_intent
from receipt_intel.query.intent_llm import extract_intent_with_ollama
from receipt_intel.query.temporal import normalize_temporal_range, resolve_temporal


class _MockResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


def test_extract_intent_with_ollama_parses_valid_json(monkeypatch) -> None:
    payload = {
        "message": {
            "content": (
                '{"query_type":"aggregation","aggregation":"sum","merchants":["Whole Foods"],'
                '"categories":["grocery"],"start_date":"2023-12-01","end_date":"2023-12-31",'
                '"needs_semantic":true,"confidence":0.92}'
            )
        }
    }

    def _mock_post(*args, **kwargs):
        return _MockResponse(payload)

    monkeypatch.setattr("receipt_intel.query.intent_llm.httpx.post", _mock_post)
    intent = extract_intent_with_ollama(
        "How much groceries in December?",
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        timeout_s=5,
    )
    assert intent is not None
    assert intent.parse_source == "llm"
    assert intent.query_type == "aggregation"
    assert intent.categories == ["grocery"]


def test_parse_query_intent_falls_back_when_llm_missing(monkeypatch) -> None:
    monkeypatch.setattr("receipt_intel.query.intent.extract_intent_with_ollama", lambda *args, **kwargs: None)
    intent = parse_query_intent("find grocery receipts over $50 in December")
    assert intent.parse_source == "rule"
    assert intent.category == "grocery"
    assert intent.min_total == 50
    assert intent.start_date == "2023-12-01"
    assert intent.end_date == "2023-12-31"


def test_temporal_normalization_special_phrases() -> None:
    start, end = normalize_temporal_range("show me receipts before Christmas")
    assert start == "2023-11-01"
    assert end == "2023-12-24"

    start, end = normalize_temporal_range("what did I buy first week of January")
    assert start == "2024-01-01"
    assert end == "2024-01-07"


def test_temporal_normalization_between_and_quarter() -> None:
    start, end = normalize_temporal_range("from 2023-10-20 to 2023-12-10")
    assert start == "2023-11-01"
    assert end == "2023-12-10"

    start, end = normalize_temporal_range("show q4 2023 purchases")
    assert start == "2023-11-01"
    assert end == "2023-12-31"


def test_parse_query_intent_repairs_partial_llm_dates(monkeypatch) -> None:
    monkeypatch.setattr("receipt_intel.query.intent.extract_intent_with_ollama", lambda *a, **k: None)
    intent = parse_query_intent("show me receipts from 2023-12-05 to 2023-12-20")
    assert intent.start_date == "2023-12-05"
    assert intent.end_date == "2023-12-20"


def test_temporal_resolution_ambiguous_slash_date_has_flag() -> None:
    resolved = resolve_temporal(
        raw_query="show me receipts on 12/01/2023",
        date_text=None,
        start_date=None,
        end_date=None,
    )
    assert resolved.start_date == "2023-12-01"
    assert resolved.end_date == "2023-12-01"
    assert resolved.is_ambiguous is True
    assert "ambiguous_slash_date" in resolved.notes
    assert resolved.parse_policy_used


def test_temporal_resolution_clips_out_of_range() -> None:
    resolved = resolve_temporal(
        raw_query="from 2023-01-01 to 2025-12-31",
        date_text=None,
        start_date=None,
        end_date=None,
    )
    assert resolved.start_date == "2023-11-01"
    assert resolved.end_date == "2024-01-31"
    assert "clipped_to_dataset_bounds" in resolved.notes


def test_parse_query_intent_includes_temporal_diagnostics(monkeypatch) -> None:
    monkeypatch.setattr("receipt_intel.query.intent.extract_intent_with_ollama", lambda *a, **k: None)
    intent = parse_query_intent("what did I buy before Christmas")
    assert intent.temporal.get("resolution_source") in {"event", "llm_or_none"}
    assert intent.temporal.get("start_date") == "2023-11-01"
    assert intent.temporal.get("end_date") == "2023-12-24"
    assert intent.temporal.get("parse_policy_used")


def test_parse_query_intent_normalizes_plural_category(monkeypatch) -> None:
    monkeypatch.setattr("receipt_intel.query.intent.extract_intent_with_ollama", lambda *a, **k: None)
    intent = parse_query_intent("List all groceries over $5")
    assert intent.category == "grocery"
    assert intent.min_total == 5.0


def test_parse_query_intent_detects_concept_terms(monkeypatch) -> None:
    monkeypatch.setattr("receipt_intel.query.intent.extract_intent_with_ollama", lambda *a, **k: None)
    intent = parse_query_intent("Find health-related purchases")
    assert "pharmacy" in intent.item_terms

