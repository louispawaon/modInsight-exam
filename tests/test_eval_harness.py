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

