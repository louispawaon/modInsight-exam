from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from dateutil import parser as date_parser

DATE_TOKEN_RE = re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b")


@dataclass
class ParsedDateResult:
    iso_date: str | None = None
    is_ambiguous: bool = False
    parse_policy_used: str = ""
    raw_value: str = ""
    warning: str | None = None
    error: str | None = None

    def as_dict(self) -> dict:
        return {
            "iso_date": self.iso_date,
            "is_ambiguous": self.is_ambiguous,
            "parse_policy_used": self.parse_policy_used,
            "raw_value": self.raw_value,
            "warning": self.warning,
            "error": self.error,
        }


def parse_receipt_date(
    text: str,
    *,
    date_parse_order: str = "mdy",
    ambiguity_strategy: str = "flag",
) -> ParsedDateResult:
    return _parse_date_value(
        text=text,
        date_parse_order=date_parse_order,
        ambiguity_strategy=ambiguity_strategy,
    )


def parse_query_date(
    text: str,
    *,
    date_parse_order: str = "mdy",
    ambiguity_strategy: str = "flag",
) -> ParsedDateResult:
    return _parse_date_value(
        text=text,
        date_parse_order=date_parse_order,
        ambiguity_strategy=ambiguity_strategy,
    )


def _parse_date_value(
    text: str,
    *,
    date_parse_order: str,
    ambiguity_strategy: str,
) -> ParsedDateResult:
    match = DATE_TOKEN_RE.search(text)
    if not match:
        return ParsedDateResult(error="no_date_token_found")
    raw = match.group(1)

    if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
        try:
            parsed = date_parser.parse(raw).date().isoformat()
            return ParsedDateResult(
                iso_date=parsed,
                raw_value=raw,
                parse_policy_used="iso",
            )
        except (ValueError, TypeError):
            return ParsedDateResult(raw_value=raw, parse_policy_used="iso", error="invalid_iso_date")

    ambiguous = _is_ambiguous_slash_date(raw)
    policy = f"{date_parse_order}:{ambiguity_strategy}"
    effective_order = date_parse_order

    if ambiguous:
        if ambiguity_strategy == "reject":
            return ParsedDateResult(
                raw_value=raw,
                parse_policy_used=policy,
                is_ambiguous=True,
                error="ambiguous_date_rejected",
            )
        if ambiguity_strategy == "prefer_dmy":
            effective_order = "dmy"
        elif ambiguity_strategy == "prefer_mdy":
            effective_order = "mdy"

    dayfirst = effective_order == "dmy"
    try:
        parsed_date = date_parser.parse(raw, dayfirst=dayfirst).date().isoformat()
    except (ValueError, TypeError):
        return ParsedDateResult(
            raw_value=raw,
            parse_policy_used=policy,
            is_ambiguous=ambiguous,
            error="invalid_slash_date",
        )

    warning = "ambiguous_date_interpreted" if ambiguous else None
    return ParsedDateResult(
        iso_date=parsed_date,
        is_ambiguous=ambiguous,
        parse_policy_used=policy,
        raw_value=raw,
        warning=warning,
    )


def _is_ambiguous_slash_date(raw_value: str) -> bool:
    parts = raw_value.split("/")
    if len(parts) != 3:
        return False
    left = int(parts[0])
    right = int(parts[1])
    return left <= 12 and right <= 12

