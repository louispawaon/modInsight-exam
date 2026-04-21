from __future__ import annotations

from qdrant_client.http import models as rest

from receipt_intel.models import QueryIntent


def build_qdrant_filter(intent: QueryIntent) -> rest.Filter | None:
    conditions: list[object] = []

    category_values = intent.categories or ([intent.category] if intent.category else [])
    merchant_values = intent.merchants or ([intent.merchant] if intent.merchant else [])

    if category_values:
        conditions.append(
            rest.Filter(
                should=[
                    rest.FieldCondition(key="category", match=rest.MatchValue(value=category))
                    for category in category_values
                ]
            )
        )
    if merchant_values:
        conditions.append(
            rest.Filter(
                should=[
                    rest.FieldCondition(key="merchant", match=rest.MatchText(text=merchant))
                    for merchant in merchant_values
                ]
            )
        )
    if intent.min_total is not None:
        conditions.append(rest.FieldCondition(key="total_amount", range=rest.Range(gte=float(intent.min_total))))
    if intent.max_total is not None:
        conditions.append(rest.FieldCondition(key="total_amount", range=rest.Range(lte=float(intent.max_total))))
    if intent.start_date or intent.end_date:
        conditions.append(
            rest.FieldCondition(
                key="date",
                range=rest.DatetimeRange(gte=intent.start_date, lte=intent.end_date),
            )
        )
    if intent.item_terms:
        term_conditions: list[object] = []
        for term in intent.item_terms:
            term_conditions.append(rest.FieldCondition(key="item_name", match=rest.MatchText(text=term)))
        # Also allow receipts where semantic content may include item words.
        for term in intent.item_terms:
            term_conditions.append(rest.FieldCondition(key="content", match=rest.MatchText(text=term)))
        conditions.append(rest.Filter(should=term_conditions))

    if not conditions:
        return None
    return rest.Filter(must=conditions)

