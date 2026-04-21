from __future__ import annotations

import json
import re
from pathlib import Path

from receipt_intel.config import get_settings
from receipt_intel.models import QueryIntent
from receipt_intel.query.concepts import detect_concepts, expand_terms_for_concepts
from receipt_intel.query.intent_llm import extract_intent_with_ollama
from receipt_intel.query.temporal import resolve_temporal

KNOWN_CATEGORIES = {
    "grocery",
    "restaurant",
    "coffee",
    "fast_food",
    "electronics",
    "pharmacy",
    "retail",
    "hardware",
    "gas",
}
CATEGORY_SYNONYMS = {
    "groceries": "grocery",
    "grocery": "grocery",
    "restaurants": "restaurant",
    "restaurant": "restaurant",
    "coffee shop": "coffee",
    "coffee shops": "coffee",
    "electronics": "electronics",
    "pharmacy": "pharmacy",
    "hardware": "hardware",
    "gas": "gas",
}

PAYMENT_METHOD_ALIASES = {
    "visa": "VISA",
    "mastercard": "MASTERCARD",
    "master card": "MASTERCARD",
    "amex": "AMEX",
    "american express": "AMEX",
    "discover": "DISCOVER",
    "debit": "DEBIT",
    "cash": "CASH",
    "apple pay": "APPLE PAY",
}

_CITY_CACHE: list[str] | None = None
_DEFAULT_CITIES = [
    "san francisco",
    "oakland",
    "berkeley",
    "daly city",
    "san mateo",
    "palo alto",
    "san jose",
    "redwood city",
    "south san francisco",
    "mountain view",
    "sunnyvale",
    "fremont",
    "hayward",
]


def _known_cities() -> list[str]:
    global _CITY_CACHE
    if _CITY_CACHE is not None:
        return _CITY_CACHE
    values: set[str] = set()
    try:
        parsed_path: Path = get_settings().parsed_output_path
        if parsed_path.exists():
            with parsed_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    payload = json.loads(line)
                    city = payload.get("city")
                    if isinstance(city, str) and city.strip():
                        values.add(city.strip().lower())
    except Exception:
        values = set()
    for fallback in _DEFAULT_CITIES:
        values.add(fallback)
    _CITY_CACHE = sorted(values, key=len, reverse=True)
    return _CITY_CACHE


def parse_query_intent(raw_query: str) -> QueryIntent:
    settings = get_settings()
    llm_intent = extract_intent_with_ollama(
        raw_query,
        base_url=settings.ollama_base_url,
        model=settings.ollama_chat_model,
        timeout_s=settings.ollama_intent_timeout_s,
    )
    rule_intent = _parse_query_intent_rules(raw_query)

    if llm_intent is None:
        return _apply_temporal(rule_intent)

    merged = _merge_intents(primary=llm_intent, fallback=rule_intent)
    return _apply_temporal(merged)


def _parse_query_intent_rules(raw_query: str) -> QueryIntent:
    text = raw_query.lower().strip()
    intent = QueryIntent(raw_query=raw_query, parse_source="rule")

    if (
        "how much" in text
        or "total" in text
        or "average" in text
        or "spent at" in text
        or "spending at" in text
    ):
        intent.query_type = "aggregation"
        intent.aggregation = "sum" if "average" not in text else "avg"
    if "count" in text:
        intent.query_type = "aggregation"
        intent.aggregation = "count"
    if "highest" in text or "most expensive" in text or "max" in text:
        intent.query_type = "aggregation"
        intent.aggregation = "max"
    if "lowest" in text or "min" in text or "cheapest" in text:
        intent.query_type = "aggregation"
        intent.aggregation = "min"

    for phrase, normalized in CATEGORY_SYNONYMS.items():
        if phrase in text:
            intent.category = normalized
            intent.categories = [normalized]
            break
    if not intent.category:
        for category in KNOWN_CATEGORIES:
            if category.replace("_", " ") in text or category in text:
                intent.category = category
                intent.categories = [category]
                break

    money_matches = re.findall(r"\$?\s*(\d+(?:\.\d+)?)", text)
    if "over" in text and money_matches:
        intent.min_total = float(money_matches[0])
    elif ("under" in text or "below" in text) and money_matches:
        intent.max_total = float(money_matches[0])

    merchant_patterns = ["whole foods", "starbucks", "walmart", "target", "costco", "best buy"]
    for merchant in merchant_patterns:
        if merchant in text:
            intent.merchant = merchant
            intent.merchants = [merchant]
            break

    if "by merchant" in text or "per merchant" in text:
        intent.group_by = "merchant"
    elif "by category" in text or "per category" in text:
        intent.group_by = "category"
    elif "per week" in text or "by week" in text or "weekly" in text:
        intent.group_by = "week"

    if re.search(r"\b(per|each|every)\s+week\b", text) or "weekly average" in text or "average per week" in text:
        intent.per_period = "week"
    elif re.search(r"\b(per|each|every)\s+month\b", text) or "monthly average" in text or "average per month" in text:
        intent.per_period = "month"
    if intent.per_period and intent.query_type != "aggregation":
        intent.query_type = "aggregation"
        if not intent.aggregation:
            intent.aggregation = "avg"

    for city in _known_cities():
        if re.search(rf"\b{re.escape(city)}\b", text):
            intent.city = city
            intent.cities = [city]
            break

    for alias, normalized in PAYMENT_METHOD_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", text):
            intent.payment_method = normalized
            intent.payment_methods = [normalized]
            break

    tip_match = re.search(r"tip(?:ped|ping)?\s*(?:of\s*)?(?:over|more than|above|greater than|>=?)\s*(\d+)%?", text)
    if tip_match:
        intent.min_tip_pct = float(tip_match.group(1))
        if not intent.category:
            intent.category = "restaurant"
            intent.categories = ["restaurant"]
    else:
        tip_under = re.search(r"tip(?:ped|ping)?\s*(?:under|below|less than|<=?)\s*(\d+)%?", text)
        if tip_under:
            intent.max_tip_pct = float(tip_under.group(1))
            if not intent.category:
                intent.category = "restaurant"
                intent.categories = ["restaurant"]

    concepts = detect_concepts(text)
    if concepts:
        concept_terms = expand_terms_for_concepts(concepts)
        intent.item_terms = _unique_list(intent.item_terms + concept_terms)
        if "prescription" in concepts:
            intent.require_prescription = True
            if not intent.category:
                intent.category = "pharmacy"
                intent.categories = ["pharmacy"]
        if "warranty" in concepts:
            intent.require_warranty = True
        if "loyalty" in concepts:
            intent.require_loyalty = True
        if intent.parse_source == "rule":
            intent.parse_source = "rule_concept"

    return intent


def _merge_intents(primary: QueryIntent, fallback: QueryIntent) -> QueryIntent:
    merged = primary.model_copy(deep=True)

    if not merged.merchant and fallback.merchant:
        merged.merchant = fallback.merchant
    if not merged.category and fallback.category:
        merged.category = fallback.category
    if merged.min_total is None and fallback.min_total is not None:
        merged.min_total = fallback.min_total
    if merged.max_total is None and fallback.max_total is not None:
        merged.max_total = fallback.max_total
    if not merged.aggregation and fallback.aggregation:
        merged.aggregation = fallback.aggregation
    if not merged.query_type and fallback.query_type:
        merged.query_type = fallback.query_type
    if not merged.merchants and fallback.merchants:
        merged.merchants = fallback.merchants
    if not merged.categories and fallback.categories:
        merged.categories = fallback.categories
    if not merged.item_terms and fallback.item_terms:
        merged.item_terms = fallback.item_terms

    if not merged.start_date and fallback.start_date:
        merged.start_date = fallback.start_date
    if not merged.end_date and fallback.end_date:
        merged.end_date = fallback.end_date

    if not merged.city and fallback.city:
        merged.city = fallback.city
    if not merged.cities and fallback.cities:
        merged.cities = fallback.cities
    if not merged.payment_method and fallback.payment_method:
        merged.payment_method = fallback.payment_method
    if not merged.payment_methods and fallback.payment_methods:
        merged.payment_methods = fallback.payment_methods
    if merged.min_tip_pct is None and fallback.min_tip_pct is not None:
        merged.min_tip_pct = fallback.min_tip_pct
    if merged.max_tip_pct is None and fallback.max_tip_pct is not None:
        merged.max_tip_pct = fallback.max_tip_pct
    if not merged.per_period and fallback.per_period:
        merged.per_period = fallback.per_period
    if fallback.require_prescription:
        merged.require_prescription = True
    if fallback.require_warranty:
        merged.require_warranty = True
    if fallback.require_loyalty:
        merged.require_loyalty = True

    if merged.merchants and not merged.merchant:
        merged.merchant = merged.merchants[0]
    if merged.categories and not merged.category:
        merged.category = merged.categories[0]
    if merged.parse_source == "llm" and fallback.parse_source.startswith("rule_concept"):
        merged.parse_source = "hybrid_concept"
    return merged


def _apply_temporal(intent: QueryIntent) -> QueryIntent:
    temporal = resolve_temporal(
        raw_query=intent.raw_query,
        date_text=intent.date_text,
        start_date=intent.start_date,
        end_date=intent.end_date,
    )
    intent.start_date = temporal.start_date
    intent.end_date = temporal.end_date
    intent.temporal = temporal.as_dict()
    return intent


def _unique_list(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = value.strip().lower()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        deduped.append(cleaned)
    return deduped

