from __future__ import annotations


def evaluate_assertions(result: dict, assertions: dict) -> dict[str, bool]:
    checks: dict[str, bool] = {}
    min_receipts = assertions.get("min_receipts")
    if min_receipts is not None:
        checks["min_receipts"] = len(result.get("matched_receipts", [])) >= int(min_receipts)

    min_sum = assertions.get("min_sum")
    if min_sum is not None:
        total_sum = float(result.get("totals", {}).get("sum", 0.0))
        checks["min_sum"] = total_sum >= float(min_sum)

    contains_any = assertions.get("answer_contains_any")
    if contains_any:
        answer = str(result.get("answer", "")).lower()
        checks["answer_contains_any"] = any(str(token).lower() in answer for token in contains_any)

    expected_mode = assertions.get("retrieval_mode")
    if expected_mode is not None:
        mode = str(result.get("retrieval", {}).get("mode", ""))
        checks["retrieval_mode"] = mode == str(expected_mode)

    required_intent_field = assertions.get("intent_field_nonempty")
    if required_intent_field:
        value = result.get("intent", {}).get(str(required_intent_field))
        checks["intent_field_nonempty"] = bool(value)
    return checks

