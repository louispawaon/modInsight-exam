from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from dateutil import parser as date_parser

from receipt_intel.config import get_settings
from receipt_intel.time import parse_query_date

DATASET_MIN = date(2023, 11, 1)
DATASET_MAX = date(2024, 1, 31)
DEFAULT_PARSED_RECEIPTS_PATH = Path("data/parsed_receipts.jsonl")

MONTH_RANGES = {
    "november": ("2023-11-01", "2023-11-30"),
    "december": ("2023-12-01", "2023-12-31"),
    "january": ("2024-01-01", "2024-01-31"),
}


@dataclass
class TemporalResolution:
    start_date: str | None = None
    end_date: str | None = None
    resolution_source: str = "none"
    confidence: float = 0.0
    is_ambiguous: bool = False
    parse_policy_used: str = ""
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "resolution_source": self.resolution_source,
            "confidence": self.confidence,
            "is_ambiguous": self.is_ambiguous,
            "parse_policy_used": self.parse_policy_used,
            "notes": self.notes,
        }


def normalize_temporal_range(raw_query: str, date_text: str | None = None) -> tuple[str | None, str | None]:
    resolution = normalize_temporal_resolution(raw_query, date_text)
    return resolution.start_date, resolution.end_date


def normalize_temporal_resolution(raw_query: str, date_text: str | None = None) -> TemporalResolution:
    text = f"{raw_query} {date_text or ''}".lower()
    bounds_min, bounds_max = infer_dataset_bounds()
    settings = get_settings()

    ranged = _parse_between_dates(
        text,
        date_parse_order=settings.date_parse_order,
        ambiguity_strategy=settings.date_ambiguity_strategy,
    )
    if ranged:
        start, end, clipped = _clamp_range(ranged[0], ranged[1], bounds_min, bounds_max)
        notes = list(ranged[2])
        if clipped:
            notes.append("clipped_to_dataset_bounds")
        return TemporalResolution(
            start_date=start,
            end_date=end,
            resolution_source="range",
            confidence=0.95,
            parse_policy_used=f"{settings.date_parse_order}:{settings.date_ambiguity_strategy}",
            notes=notes,
        )

    if "week before christmas" in text:
        start, end, clipped = _clamp_range("2023-12-18", "2023-12-24", bounds_min, bounds_max)
        return TemporalResolution(
            start,
            end,
            "event",
            0.95,
            parse_policy_used=f"{settings.date_parse_order}:{settings.date_ambiguity_strategy}",
            notes=["clipped_to_dataset_bounds"] if clipped else [],
        )
    if "christmas week" in text:
        start, end, clipped = _clamp_range("2023-12-18", "2023-12-25", bounds_min, bounds_max)
        return TemporalResolution(
            start,
            end,
            "event",
            0.95,
            parse_policy_used=f"{settings.date_parse_order}:{settings.date_ambiguity_strategy}",
            notes=["clipped_to_dataset_bounds"] if clipped else [],
        )
    if "before christmas" in text:
        start, end, clipped = _clamp_range("2023-11-01", "2023-12-24", bounds_min, bounds_max)
        return TemporalResolution(
            start,
            end,
            "event",
            0.9,
            parse_policy_used=f"{settings.date_parse_order}:{settings.date_ambiguity_strategy}",
            notes=["clipped_to_dataset_bounds"] if clipped else [],
        )
    if "thanksgiving week" in text:
        start, end, clipped = _clamp_range("2023-11-20", "2023-11-26", bounds_min, bounds_max)
        return TemporalResolution(
            start,
            end,
            "event",
            0.9,
            parse_policy_used=f"{settings.date_parse_order}:{settings.date_ambiguity_strategy}",
            notes=["clipped_to_dataset_bounds"] if clipped else [],
        )

    if "first week of january" in text:
        start, end, clipped = _clamp_range("2024-01-01", "2024-01-07", bounds_min, bounds_max)
        return TemporalResolution(
            start,
            end,
            "relative",
            0.9,
            parse_policy_used=f"{settings.date_parse_order}:{settings.date_ambiguity_strategy}",
            notes=["clipped_to_dataset_bounds"] if clipped else [],
        )
    if "last week" in text:
        start, end = _last_week_in_dataset(bounds_max)
        return TemporalResolution(
            start,
            end,
            "relative",
            0.85,
            parse_policy_used=f"{settings.date_parse_order}:{settings.date_ambiguity_strategy}",
        )
    if "this week" in text:
        end_date = bounds_max
        start_date = end_date - timedelta(days=end_date.weekday())
        start, end, clipped = _clamp_range(start_date.isoformat(), end_date.isoformat(), bounds_min, bounds_max)
        return TemporalResolution(
            start,
            end,
            "relative",
            0.8,
            parse_policy_used=f"{settings.date_parse_order}:{settings.date_ambiguity_strategy}",
            notes=["clipped_to_dataset_bounds"] if clipped else [],
        )

    quarter = _parse_quarter(text)
    if quarter:
        start, end, clipped = _clamp_range(quarter[0], quarter[1], bounds_min, bounds_max)
        return TemporalResolution(
            start,
            end,
            "quarter",
            0.8,
            parse_policy_used=f"{settings.date_parse_order}:{settings.date_ambiguity_strategy}",
            notes=["clipped_to_dataset_bounds"] if clipped else [],
        )

    explicit, explicit_ambiguous, explicit_notes = _explicit_date(
        text,
        bounds_min,
        bounds_max,
        date_parse_order=settings.date_parse_order,
        ambiguity_strategy=settings.date_ambiguity_strategy,
    )
    if explicit:
        day = explicit.isoformat()
        notes = explicit_notes + (["ambiguous_slash_date"] if explicit_ambiguous else [])
        return TemporalResolution(
            day,
            day,
            "explicit",
            0.9,
            is_ambiguous=explicit_ambiguous,
            parse_policy_used=f"{settings.date_parse_order}:{settings.date_ambiguity_strategy}",
            notes=notes,
        )

    for month, (start, end) in MONTH_RANGES.items():
        if re.search(rf"\b{month}\b", text):
            start, end, clipped = _clamp_range(start, end, bounds_min, bounds_max)
            return TemporalResolution(
                start,
                end,
                "month",
                0.75,
                parse_policy_used=f"{settings.date_parse_order}:{settings.date_ambiguity_strategy}",
                notes=["clipped_to_dataset_bounds"] if clipped else [],
            )

    return TemporalResolution()


def _explicit_date(
    text: str,
    bounds_min: date,
    bounds_max: date,
    *,
    date_parse_order: str,
    ambiguity_strategy: str,
) -> tuple[date | None, bool, list[str]]:
    parsed = parse_query_date(
        text,
        date_parse_order=date_parse_order,
        ambiguity_strategy=ambiguity_strategy,
    )
    if not parsed.iso_date:
        if parsed.error == "ambiguous_date_rejected":
            return None, True, ["ambiguous_date_rejected"]
        return None, False, []
    dt = date_parser.parse(parsed.iso_date).date()
    ambiguous = parsed.is_ambiguous
    if dt < bounds_min or dt > bounds_max:
        return None, ambiguous, ["outside_dataset_bounds"]
    notes: list[str] = []
    if parsed.warning:
        notes.append(parsed.warning)
    return dt, ambiguous, notes


def _last_week_in_dataset(bounds_max: date) -> tuple[str, str]:
    end_date = bounds_max
    start_date = end_date - timedelta(days=6)
    return start_date.isoformat(), end_date.isoformat()


def resolve_dates(
    raw_query: str,
    date_text: str | None,
    start_date: str | None,
    end_date: str | None,
) -> tuple[str | None, str | None]:
    resolution = resolve_temporal(raw_query, date_text, start_date, end_date)
    return resolution.start_date, resolution.end_date


def resolve_temporal(
    raw_query: str,
    date_text: str | None,
    start_date: str | None,
    end_date: str | None,
) -> TemporalResolution:
    resolution = normalize_temporal_resolution(raw_query, date_text)
    bounds_min, bounds_max = infer_dataset_bounds()
    start = start_date or resolution.start_date
    end = end_date or resolution.end_date

    notes = list(resolution.notes)
    if start and end:
        try:
            clamped_start, clamped_end, clipped = _clamp_range(start, end, bounds_min, bounds_max)
            if clipped:
                notes.append("clipped_to_dataset_bounds")
            if clamped_start > clamped_end:
                clamped_start, clamped_end = clamped_end, clamped_start
                notes.append("swapped_inverted_range")
            start, end = clamped_start, clamped_end
        except Exception:
            start, end = resolution.start_date, resolution.end_date
            notes.append("invalid_llm_date_replaced")

    return TemporalResolution(
        start_date=start,
        end_date=end,
        resolution_source=resolution.resolution_source if resolution.resolution_source != "none" else "llm_or_none",
        confidence=resolution.confidence,
        is_ambiguous=resolution.is_ambiguous,
        parse_policy_used=resolution.parse_policy_used,
        notes=sorted(set(notes)),
    )


def _parse_between_dates(
    text: str,
    *,
    date_parse_order: str,
    ambiguity_strategy: str,
) -> tuple[str, str, list[str]] | None:
    # Handles: from 2023-12-01 to 2023-12-20, between 11/01/2023 and 11/30/2023
    range_match = re.search(
        r"(?:from|between)\s+(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\s+(?:to|and)\s+(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})",
        text,
    )
    if not range_match:
        return None
    left = parse_query_date(
        range_match.group(1),
        date_parse_order=date_parse_order,
        ambiguity_strategy=ambiguity_strategy,
    )
    right = parse_query_date(
        range_match.group(2),
        date_parse_order=date_parse_order,
        ambiguity_strategy=ambiguity_strategy,
    )
    if not left.iso_date or not right.iso_date:
        return None
    notes: list[str] = []
    if left.warning:
        notes.append(left.warning)
    if right.warning:
        notes.append(right.warning)
    if left.error == "ambiguous_date_rejected" or right.error == "ambiguous_date_rejected":
        notes.append("ambiguous_date_rejected")
    return left.iso_date, right.iso_date, notes


def _parse_quarter(text: str) -> tuple[str, str] | None:
    if "q4 2023" in text:
        return "2023-10-01", "2023-12-31"
    if "q1 2024" in text:
        return "2024-01-01", "2024-03-31"
    return None


def _clamp_range(start: str, end: str, bounds_min: date, bounds_max: date) -> tuple[str, str, bool]:
    clipped = False
    start_dt = date_parser.parse(start).date()
    end_dt = date_parser.parse(end).date()
    if start_dt < bounds_min:
        start_dt = bounds_min
        clipped = True
    if end_dt > bounds_max:
        end_dt = bounds_max
        clipped = True
    return start_dt.isoformat(), end_dt.isoformat(), clipped


def infer_dataset_bounds() -> tuple[date, date]:
    if not DEFAULT_PARSED_RECEIPTS_PATH.exists():
        return DATASET_MIN, DATASET_MAX
    min_date: date | None = None
    max_date: date | None = None
    try:
        with DEFAULT_PARSED_RECEIPTS_PATH.open("r", encoding="utf-8") as handle:
            for line in handle:
                payload = json.loads(line)
                value = payload.get("date")
                if not value:
                    continue
                try:
                    d = date_parser.parse(str(value)).date()
                except (ValueError, TypeError):
                    continue
                min_date = d if min_date is None or d < min_date else min_date
                max_date = d if max_date is None or d > max_date else max_date
    except Exception:
        return DATASET_MIN, DATASET_MAX
    resolved_min = min_date or DATASET_MIN
    resolved_max = max_date or DATASET_MAX

    # Never shrink known challenge envelope due to partial/failed parsing.
    if resolved_min > DATASET_MIN:
        resolved_min = DATASET_MIN
    if resolved_max < DATASET_MAX:
        resolved_max = DATASET_MAX
    return resolved_min, resolved_max

