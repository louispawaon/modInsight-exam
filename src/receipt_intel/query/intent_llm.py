from __future__ import annotations

import json
from typing import Any

import httpx

from receipt_intel.models import QueryIntent

INTENT_PROMPT = """You are a query intent parser for a receipt intelligence system.
Return ONLY valid JSON (no markdown) with this schema:
{
  "query_type": "search|aggregation",
  "aggregation": "sum|avg|count|max|min|group|null",
  "merchant": "string|null",
  "category": "string|null",
  "merchants": ["string"],
  "categories": ["string"],
  "item_terms": ["string"],
  "min_total": number|null,
  "max_total": number|null,
  "start_date": "YYYY-MM-DD|null",
  "end_date": "YYYY-MM-DD|null",
  "date_text": "string|null",
  "group_by": "merchant|category|week|null",
  "sort_by": "amount_desc|amount_asc|date_desc|date_asc|null",
  "limit": number|null,
  "needs_semantic": true,
  "confidence": 0.0
}
Unknown fields must be null or empty list.
"""


def extract_intent_with_ollama(
    raw_query: str,
    *,
    base_url: str,
    model: str,
    timeout_s: int,
) -> QueryIntent | None:
    try:
        payload = {
            "model": model,
            "format": "json",
            "stream": False,
            "messages": [
                {"role": "system", "content": INTENT_PROMPT},
                {"role": "user", "content": raw_query},
            ],
        }
        response = httpx.post(
            f"{base_url.rstrip('/')}/api/chat",
            json=payload,
            timeout=timeout_s,
        )
        response.raise_for_status()
        data = response.json()
        content = _extract_content(data)
        if not content:
            return None
        parsed = _safe_load_json(content)
        if parsed is None:
            return None
        intent = QueryIntent(
            raw_query=raw_query,
            **_sanitize_intent_payload(parsed),
            parse_source="llm",
        )
        return intent
    except Exception:
        return None


def _extract_content(data: dict[str, Any]) -> str:
    msg = data.get("message", {})
    content = msg.get("content")
    return content.strip() if isinstance(content, str) else ""


def _safe_load_json(content: str) -> dict[str, Any] | None:
    try:
        loaded = json.loads(content)
        return loaded if isinstance(loaded, dict) else None
    except json.JSONDecodeError:
        return None


def _sanitize_intent_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    allowed = {
        "query_type",
        "aggregation",
        "merchant",
        "category",
        "merchants",
        "categories",
        "item_terms",
        "min_total",
        "max_total",
        "start_date",
        "end_date",
        "date_text",
        "group_by",
        "sort_by",
        "limit",
        "needs_semantic",
        "confidence",
    }
    for key in allowed:
        if key not in payload:
            continue
        value = payload[key]
        if key in {"merchants", "categories", "item_terms"}:
            if isinstance(value, list):
                cleaned[key] = [str(v).strip() for v in value if str(v).strip()]
            else:
                cleaned[key] = []
        elif key in {"min_total", "max_total", "confidence"}:
            try:
                cleaned[key] = float(value) if value is not None else None
            except (TypeError, ValueError):
                cleaned[key] = None
        elif key == "limit":
            try:
                cleaned[key] = max(1, int(value)) if value is not None else None
            except (TypeError, ValueError):
                cleaned[key] = None
        elif key == "needs_semantic":
            cleaned[key] = bool(value)
        else:
            cleaned[key] = str(value).strip() if value is not None else None
    return cleaned

