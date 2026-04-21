from __future__ import annotations

from datetime import datetime


def dedupe_receipt_rows(points: list[dict]) -> list[dict]:
    by_receipt: dict[str, dict] = {}
    for payload in points:
        receipt_id = payload.get("receipt_id")
        if not receipt_id:
            continue
        total = payload.get("total_amount")
        if not isinstance(total, (int, float)):
            continue
        existing = by_receipt.get(str(receipt_id))
        if existing is None:
            by_receipt[str(receipt_id)] = payload
            continue
        existing_score = 1 if existing.get("chunk_type") == "receipt" else 0
        candidate_score = 1 if payload.get("chunk_type") == "receipt" else 0
        if candidate_score > existing_score:
            by_receipt[str(receipt_id)] = payload
    return list(by_receipt.values())


def aggregate_totals(points: list[dict]) -> dict[str, float]:
    totals: dict[str, float] = {"sum": 0.0, "count": 0.0, "avg": 0.0}
    values: list[float] = []
    for payload in points:
        total = payload.get("total_amount")
        if isinstance(total, (int, float)):
            values.append(float(total))
    if not values:
        return totals
    totals["sum"] = round(sum(values), 2)
    totals["count"] = float(len(values))
    totals["avg"] = round(totals["sum"] / totals["count"], 2)
    return totals


def group_totals_by_field(points: list[dict], field_name: str) -> dict[str, float]:
    grouped: dict[str, float] = {}
    for payload in points:
        key = payload.get(field_name)
        total = payload.get("total_amount")
        if not key or not isinstance(total, (int, float)):
            continue
        grouped[str(key)] = grouped.get(str(key), 0.0) + float(total)
    return {k: round(v, 2) for k, v in grouped.items()}


def group_totals_by_week(points: list[dict]) -> dict[str, float]:
    grouped: dict[str, float] = {}
    for payload in points:
        total = payload.get("total_amount")
        date_value = payload.get("date")
        if not isinstance(total, (int, float)) or not isinstance(date_value, str) or not date_value:
            continue
        try:
            dt = datetime.fromisoformat(date_value)
        except ValueError:
            continue
        week_key = f"{dt.isocalendar().year}-W{dt.isocalendar().week:02d}"
        grouped[week_key] = grouped.get(week_key, 0.0) + float(total)
    return {k: round(v, 2) for k, v in grouped.items()}


def compute_period_rate(points: list[dict], period: str) -> dict[str, float | int | str]:
    if period not in {"week", "month"}:
        return {"period": period, "buckets": 0, "total": 0.0, "avg_per_bucket": 0.0}
    grouped = group_totals_by_week(points) if period == "week" else _group_totals_by_month(points)
    buckets = len(grouped)
    total = round(sum(grouped.values()), 2) if grouped else 0.0
    avg = round(total / buckets, 2) if buckets else 0.0
    return {
        "period": period,
        "buckets": buckets,
        "total": total,
        "avg_per_bucket": avg,
    }


def _group_totals_by_month(points: list[dict]) -> dict[str, float]:
    grouped: dict[str, float] = {}
    for payload in points:
        total = payload.get("total_amount")
        date_value = payload.get("date")
        if not isinstance(total, (int, float)) or not isinstance(date_value, str) or not date_value:
            continue
        try:
            dt = datetime.fromisoformat(date_value)
        except ValueError:
            continue
        month_key = f"{dt.year:04d}-{dt.month:02d}"
        grouped[month_key] = grouped.get(month_key, 0.0) + float(total)
    return {k: round(v, 2) for k, v in grouped.items()}

