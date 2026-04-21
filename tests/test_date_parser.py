from receipt_intel.time import parse_query_date


def test_parse_query_date_unambiguous_mdy() -> None:
    parsed = parse_query_date("11/24/2023", date_parse_order="mdy", ambiguity_strategy="flag")
    assert parsed.iso_date == "2023-11-24"
    assert parsed.is_ambiguous is False


def test_parse_query_date_unambiguous_dmy() -> None:
    parsed = parse_query_date("24/11/2023", date_parse_order="mdy", ambiguity_strategy="flag")
    assert parsed.iso_date == "2023-11-24"
    assert parsed.is_ambiguous is False


def test_parse_query_date_ambiguous_prefers_dmy() -> None:
    parsed = parse_query_date("03/04/2024", date_parse_order="mdy", ambiguity_strategy="prefer_dmy")
    assert parsed.iso_date == "2024-04-03"
    assert parsed.is_ambiguous is True


def test_parse_query_date_ambiguous_reject_mode() -> None:
    parsed = parse_query_date("03/04/2024", date_parse_order="mdy", ambiguity_strategy="reject")
    assert parsed.iso_date is None
    assert parsed.error == "ambiguous_date_rejected"
    assert parsed.is_ambiguous is True


def test_parse_query_date_iso_passthrough() -> None:
    parsed = parse_query_date("2023-12-01", date_parse_order="dmy", ambiguity_strategy="reject")
    assert parsed.iso_date == "2023-12-01"
    assert parsed.parse_policy_used == "iso"

