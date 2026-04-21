from receipt_intel.eval_harness import evaluate_assertions


def test_evaluate_assertions_reports_expected_checks() -> None:
    result = {
        "matched_receipts": ["receipt_001", "receipt_002"],
        "totals": {"sum": 62.42},
    }
    assertions = {"min_receipts": 2, "min_sum": 50}
    checks = evaluate_assertions(result, assertions)
    assert checks["min_receipts"] is True
    assert checks["min_sum"] is True


def test_evaluate_assertions_intent_field_equals_and_temporal_range() -> None:
    result = {
        "intent": {
            "city": "san francisco",
            "min_tip_pct": 20.0,
            "temporal": {"start_date": "2023-12-18", "end_date": "2023-12-24"},
        }
    }
    assertions = {
        "intent_field_equals": {"city": "san francisco", "min_tip_pct": 20.0},
        "temporal_range_eq": {"start": "2023-12-18", "end": "2023-12-24"},
    }
    checks = evaluate_assertions(result, assertions)
    assert checks["intent_field_equals"] is True
    assert checks["temporal_range_eq"] is True


def test_evaluate_assertions_facts_path_and_evidence_flag() -> None:
    result = {
        "facts": {"per_period": {"avg_per_bucket": 12.5}},
        "evidence_rows": [{"has_warranty": True}, {"has_warranty": False}],
    }
    assertions = {
        "facts_path_nonempty": ["per_period", "avg_per_bucket"],
        "evidence_any_flag": "has_warranty",
    }
    checks = evaluate_assertions(result, assertions)
    assert checks["facts_path_nonempty"] is True
    assert checks["evidence_any_flag"] is True


def test_evaluate_assertions_allow_empty_or_contains() -> None:
    result_empty = {"matched_receipts": [], "answer": ""}
    result_with_token = {"matched_receipts": ["r1"], "answer": "Loyalty discounts found"}
    assertions = {"allow_empty_or_contains": ["loyalty", "no matching"]}
    assert evaluate_assertions(result_empty, assertions)["allow_empty_or_contains"] is True
    assert evaluate_assertions(result_with_token, assertions)["allow_empty_or_contains"] is True

