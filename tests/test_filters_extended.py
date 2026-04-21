from __future__ import annotations

from receipt_intel.models import QueryIntent
from receipt_intel.query.filters import build_qdrant_filter


def _serialize(filt) -> str:
    return repr(filt)


def test_build_qdrant_filter_includes_city_and_payment() -> None:
    intent = QueryIntent(raw_query="t", city="san francisco", payment_method="VISA")
    filt = build_qdrant_filter(intent)
    rendered = _serialize(filt)
    assert "city" in rendered
    assert "san francisco" in rendered
    assert "payment_method" in rendered
    assert "VISA" in rendered


def test_build_qdrant_filter_includes_tip_range() -> None:
    intent = QueryIntent(raw_query="t", min_tip_pct=20.0)
    filt = build_qdrant_filter(intent)
    rendered = _serialize(filt)
    assert "tip_pct" in rendered
    assert "20" in rendered


def test_build_qdrant_filter_includes_boolean_flags() -> None:
    intent = QueryIntent(
        raw_query="t",
        require_prescription=True,
        require_warranty=True,
        require_loyalty=True,
    )
    filt = build_qdrant_filter(intent)
    rendered = _serialize(filt)
    assert "has_prescription" in rendered
    assert "has_warranty" in rendered
    assert "loyalty_flag" in rendered


def test_build_qdrant_filter_returns_none_when_empty() -> None:
    intent = QueryIntent(raw_query="t")
    assert build_qdrant_filter(intent) is None
