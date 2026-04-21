from __future__ import annotations

from datetime import date

from receipt_intel.query.engine import (
    _answer_unique_values,
    _answer_year_coverage,
    _is_year_coverage_query,
    _try_metadata_shortcuts,
)


def test_is_year_coverage_query_detects_range_request() -> None:
    assert _is_year_coverage_query("give me the year ranges that is present in the receipts")
    assert _is_year_coverage_query("what years are available in this dataset?")
    assert not _is_year_coverage_query("how much did i spend in december")


def test_answer_year_coverage_uses_dataset_bounds(monkeypatch) -> None:
    monkeypatch.setattr(
        "receipt_intel.query.engine.infer_dataset_bounds",
        lambda: (date(2023, 11, 1), date(2024, 1, 31)),
    )
    result = _answer_year_coverage("give me year ranges")
    assert "2023, 2024" in result.answer
    assert result.retrieval.get("mode") == "metadata_shortcut"
    assert result.facts.get("years") == [2023, 2024]


def test_try_metadata_shortcuts_for_earliest_date(monkeypatch) -> None:
    monkeypatch.setattr(
        "receipt_intel.query.engine.infer_dataset_bounds",
        lambda: (date(2023, 11, 1), date(2024, 1, 31)),
    )
    result = _try_metadata_shortcuts("what is the earliest date in the receipts")
    assert result is not None
    assert "2023-11-01" in result.answer


def test_answer_unique_values_count(monkeypatch) -> None:
    monkeypatch.setattr("receipt_intel.query.engine._load_unique_values", lambda field: ["A", "B", "C"])
    result = _answer_unique_values("how many merchants are there", field="merchant")
    assert "3 unique merchants" in result.answer
