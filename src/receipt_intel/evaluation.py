from __future__ import annotations

from receipt_intel.eval_harness import evaluate_assertions
from receipt_intel.query import QueryEngine

SCENARIOS = [
    {
        "name": "december_spend",
        "tag": "temporal",
        "query": "How much did I spend in December 2023?",
        "assertions": {"min_receipts": 5},
    },
    {
        "name": "whole_foods",
        "tag": "merchant",
        "query": "Find all Whole Foods receipts",
        "assertions": {"min_receipts": 1},
    },
    {
        "name": "electronics",
        "tag": "category",
        "query": "Show me all electronics purchases",
        "assertions": {"min_receipts": 1},
    },
    {
        "name": "grocery_over_50_dec",
        "tag": "multi-filter",
        "query": "Find all grocery receipts over $50 in December",
        "assertions": {"min_receipts": 1},
    },
    {
        "name": "avg_grocery_bill",
        "tag": "aggregation",
        "query": "What's my average grocery bill?",
        "assertions": {"min_sum": 1.0},
    },
    {
        "name": "last_week_list",
        "tag": "temporal",
        "query": "What did I buy last week?",
        "assertions": {"min_receipts": 1},
    },
    {
        "name": "december_receipts",
        "tag": "temporal",
        "query": "Show me all receipts from December",
        "assertions": {"min_receipts": 1},
    },
    {
        "name": "coffee_spend",
        "tag": "category",
        "query": "How much have I spent at coffee shops?",
        "assertions": {"min_sum": 1.0},
    },
    {
        "name": "restaurant_spend",
        "tag": "category",
        "query": "What's my total spending at restaurants?",
        "assertions": {"min_sum": 1.0},
    },
    {
        "name": "warranty_information",
        "tag": "concept",
        "query": "Find receipts with warranty information",
        "assertions": {"intent_field_nonempty": "item_terms"},
    },
    {
        "name": "pharmacy_items",
        "tag": "category",
        "query": "What pharmacy items did I buy?",
        "assertions": {"min_receipts": 1},
    },
    {
        "name": "groceries_over_5",
        "tag": "multi-filter",
        "query": "List all groceries over $5",
        "assertions": {"min_receipts": 1},
    },
    {
        "name": "health_related_purchases",
        "tag": "semantic",
        "query": "Find health-related purchases",
        "assertions": {"intent_field_nonempty": "item_terms"},
    },
    {
        "name": "treats_bought",
        "tag": "semantic",
        "query": "Show me treats I bought",
        "assertions": {"intent_field_nonempty": "item_terms"},
    },
    {
        "name": "year_ranges_present",
        "tag": "metadata",
        "query": "give me the year ranges that is present in the receipts",
        "assertions": {"retrieval_mode": "metadata_shortcut", "answer_contains_any": ["2023", "2024"]},
    },
    {
        "name": "sf_receipts",
        "tag": "location",
        "query": "Find all San Francisco receipts",
        "assertions": {
            "min_receipts": 1,
            "intent_field_equals": {"city": "san francisco"},
        },
    },
    {
        "name": "restaurants_tip_over_20",
        "tag": "tip",
        "query": "What restaurants did I tip over 20% at?",
        "assertions": {
            "intent_field_equals": {"min_tip_pct": 20.0, "category": "restaurant"},
        },
    },
    {
        "name": "coffee_per_week",
        "tag": "rate",
        "query": "How much do I spend on coffee per week?",
        "assertions": {
            "intent_field_equals": {"per_period": "week"},
            "facts_path_nonempty": ["per_period", "avg_per_bucket"],
        },
    },
    {
        "name": "week_before_christmas",
        "tag": "temporal",
        "query": "Find receipts from the week before Christmas",
        "assertions": {
            "temporal_range_eq": {"start": "2023-12-18", "end": "2023-12-24"},
        },
    },
    {
        "name": "prescription_pickup",
        "tag": "concept",
        "query": "Show me all prescriptions I picked up",
        "assertions": {
            "intent_field_equals": {"require_prescription": True},
            "evidence_any_flag": "has_prescription",
        },
    },
    {
        "name": "electronics_with_warranty",
        "tag": "concept",
        "query": "Show me electronics with warranties",
        "assertions": {
            "intent_field_equals": {"require_warranty": True},
            "evidence_any_flag": "has_warranty",
        },
    },
    {
        "name": "loyalty_discounts",
        "tag": "concept",
        "query": "Find all loyalty discounts",
        "assertions": {
            "intent_field_equals": {"require_loyalty": True},
            "allow_empty_or_contains": ["loyalty", "no matching", "0 receipts"],
        },
    },
    {
        "name": "visa_payments",
        "tag": "payment",
        "query": "Show me receipts paid with Visa",
        "assertions": {
            "min_receipts": 1,
            "intent_field_equals": {"payment_method": "VISA"},
        },
    },
]


def run_eval_scenarios(engine: QueryEngine) -> dict:
    records = []
    passed = 0
    for scenario in SCENARIOS:
        result = engine.query(scenario["query"])
        result_dump = result.model_dump()
        checks = evaluate_assertions(result_dump, scenario["assertions"])
        scenario_passed = all(checks.values()) if checks else True
        if scenario_passed:
            passed += 1
        records.append(
            {
                "name": scenario["name"],
                "tag": scenario["tag"],
                "query": scenario["query"],
                "result": result_dump,
                "checks": checks,
                "passed": scenario_passed,
            }
        )
    summary = {"total": len(SCENARIOS), "passed": passed, "failed": len(SCENARIOS) - passed}
    return {"summary": summary, "scenarios": records}

