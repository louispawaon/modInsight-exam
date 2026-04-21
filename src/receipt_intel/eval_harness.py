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

    intent_equals = assertions.get("intent_field_equals")
    if isinstance(intent_equals, dict):
        intent = result.get("intent", {})
        all_match = True
        for field_name, expected_value in intent_equals.items():
            if intent.get(field_name) != expected_value:
                all_match = False
                break
        checks["intent_field_equals"] = all_match

    temporal_range = assertions.get("temporal_range_eq")
    if isinstance(temporal_range, dict):
        temporal = result.get("intent", {}).get("temporal", {}) or {}
        start_ok = temporal.get("start_date") == temporal_range.get("start")
        end_ok = temporal.get("end_date") == temporal_range.get("end")
        checks["temporal_range_eq"] = bool(start_ok and end_ok)

    facts_path = assertions.get("facts_path_nonempty")
    if isinstance(facts_path, list) and facts_path:
        node = result.get("facts", {})
        ok = True
        for key in facts_path:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                ok = False
                break
        checks["facts_path_nonempty"] = bool(ok and node not in (None, "", 0, [], {}))

    evidence_any_flag = assertions.get("evidence_any_flag")
    if evidence_any_flag:
        rows = result.get("evidence_rows", []) or []
        checks["evidence_any_flag"] = any(bool(row.get(evidence_any_flag)) for row in rows)

    allow_empty = assertions.get("allow_empty_or_contains")
    if isinstance(allow_empty, list) and allow_empty:
        answer = str(result.get("answer", "")).lower()
        no_receipts = len(result.get("matched_receipts", [])) == 0
        token_match = any(str(token).lower() in answer for token in allow_empty)
        checks["allow_empty_or_contains"] = no_receipts or token_match

    return checks

