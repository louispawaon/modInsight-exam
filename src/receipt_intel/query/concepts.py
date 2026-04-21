from __future__ import annotations

import re

CONCEPT_TERMS: dict[str, list[str]] = {
    "health_related": ["pharmacy", "medicine", "medication", "vitamin", "supplement", "cvs"],
    "treats": ["candy", "ice cream", "dessert", "baked goods", "pastry", "snack"],
    "warranty": ["warranty", "protection plan", "extended coverage", "coverage"],
    "prescription": ["rx", "prescription", "copay", "pharmacy pickup"],
    "loyalty": ["loyalty", "rewards", "redcard", "member"],
    "prepared_food": [
        "burrito",
        "sandwich",
        "pizza",
        "burger",
        "salad",
        "entree",
        "meal",
        "deli",
        "prepared",
    ],
}

CONCEPT_TRIGGERS: dict[str, list[str]] = {
    "health_related": ["health related", "health-related", "health", "wellness"],
    "treats": ["treat", "treats", "dessert", "snacks", "sweet"],
    "warranty": [
        "warranty",
        "warranties",
        "protection plan",
        "extended warranty",
        "extended warranties",
        "extended coverage",
    ],
    "prescription": [
        "prescription",
        "prescriptions",
        "rx",
        "picked up",
        "pick up rx",
        "copay",
    ],
    "loyalty": ["loyalty", "rewards", "redcard", "member savings", "loyalty discount", "loyalty discounts"],
    "prepared_food": [
        "prepared food",
        "prepared meal",
        "prepared meals",
        "ready to eat",
        "ready-to-eat",
        "takeout",
    ],
}


def detect_concepts(text: str) -> list[str]:
    lowered = text.lower()
    matches: list[str] = []
    for concept, triggers in CONCEPT_TRIGGERS.items():
        if any(re.search(rf"\b{re.escape(trigger)}\b", lowered) for trigger in triggers):
            matches.append(concept)
    return matches


def expand_terms_for_concepts(concepts: list[str]) -> list[str]:
    terms: list[str] = []
    for concept in concepts:
        terms.extend(CONCEPT_TERMS.get(concept, []))
    # Preserve order, remove duplicates.
    deduped: list[str] = []
    seen: set[str] = set()
    for term in terms:
        if term in seen:
            continue
        seen.add(term)
        deduped.append(term)
    return deduped
