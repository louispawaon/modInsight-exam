from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from receipt_intel.config import get_settings
from receipt_intel.models import Receipt, ReceiptItem
from receipt_intel.time import parse_receipt_date

PRICE_RE = re.compile(r"\$\s*([0-9]+(?:\.[0-9]{2})?)")
DATE_RE = re.compile(r"(\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})")
ITEM_RE = re.compile(
    r"^(?:(?P<qty>\d+)\s*[xX]\s+)?(?P<name>.+?)\s+\$\s*(?P<price>[0-9]+(?:\.[0-9]{2})?)\s*$"
)
CITY_STATE_RE = re.compile(r"^([A-Za-z][A-Za-z .'-]+),\s*([A-Z]{2})\b")
TIP_PCT_RE = re.compile(r"^\s*TIP\s*\((\d+)%\)\s+\$\s*([0-9]+(?:\.[0-9]{2})?)", re.IGNORECASE)
TIP_PLAIN_RE = re.compile(r"^\s*TIP\b[^$]*\$\s*([0-9]+(?:\.[0-9]{2})?)", re.IGNORECASE)
TAX_RATE_RE = re.compile(r"TAX\s*\(([0-9]+(?:\.[0-9]+)?)%\)", re.IGNORECASE)
LOYALTY_MARKERS = ("REDCARD", "LOYALTY", "MEMBER SAVINGS", "REWARDS", "REWARD EARNED", "REWARDS EARNED")
WARRANTY_MARKERS = ("EXTENDED WARRANTY", "PROTECTION PLAN", "EXTENDED COVERAGE")
PRESCRIPTION_MARKERS = ("PHARMACY PICKUP", "RX#", "RX #", "INSURANCE COPAY", "PRESCRIPTION")
TOTAL_LABELS = ("SUBTOTAL", "TOTAL", "GRAND TOTAL", "AMOUNT DUE")
SUMMARY_SKIP_WORDS = (
    "PHONE:",
    "DATE:",
    "TIME:",
    "CASHIER:",
    "ORDER #",
    "ITEMS SOLD",
    "THANK YOU",
    "THANKS",
)


class ReceiptParser:
    def parse_file(self, path: Path) -> Receipt:
        text = self._read_text(path)
        lines = [line.rstrip() for line in text.splitlines() if line.strip()]
        if not lines:
            raise ValueError(f"Empty receipt file: {path.name}")

        stem_meta = self._parse_stem(path.stem)
        merchant = self._extract_merchant(lines)
        location, city, state = self._extract_location(lines)
        dt, date_source, date_diag = self._extract_date(text, lines)
        subtotal = self._extract_named_amount(text, "SUBTOTAL")
        tax, tax_rate = self._extract_tax(text)
        total = self._extract_named_amount(text, "TOTAL")
        payment_method = self._extract_payment_method(lines)
        tip_amount, tip_pct = self._extract_tip(lines)
        has_warranty = self._detect_any(lines, WARRANTY_MARKERS)
        has_prescription = self._detect_any(lines, PRESCRIPTION_MARKERS)
        loyalty_flag, loyalty_discount = self._extract_loyalty(lines, merchant)
        items, item_diag = self._extract_items(lines, stem_meta["numeric_id"])
        if has_prescription:
            items.extend(self._extract_prescription_items(lines, stem_meta["numeric_id"], start_idx=len(items) + 1))
        category = stem_meta["category"]
        receipt_id = stem_meta["receipt_id"]
        metadata: dict[str, str | float | int | bool | None] = {
            "raw_filename": path.name,
            "lines_count": len(lines),
            "date_source": date_source,
            "date_raw": date_diag.get("raw_value", ""),
            "date_policy": date_diag.get("parse_policy_used", ""),
            "date_ambiguous": bool(date_diag.get("is_ambiguous", False)),
            "date_warning": date_diag.get("warning"),
            "item_parse_mode": item_diag,
            "missing_fields": ",".join(
                [
                    name
                    for name, value in (
                        ("location", location),
                        ("subtotal", subtotal),
                        ("tax", tax),
                        ("payment_method", payment_method),
                    )
                    if value is None
                ]
            ),
        }

        if total is None:
            raise ValueError(f"Missing TOTAL for {path.name}")

        return Receipt(
            receipt_id=receipt_id,
            source_file=str(path),
            merchant=merchant,
            category=category,
            date=dt,
            location=location,
            city=city,
            state=state,
            subtotal=subtotal,
            tax=tax,
            tax_rate=tax_rate,
            total=total,
            payment_method=payment_method,
            discount=loyalty_discount,
            tip_amount=tip_amount,
            tip_pct=tip_pct,
            has_prescription=has_prescription,
            has_warranty=has_warranty,
            loyalty_flag=loyalty_flag,
            metadata=metadata,
            items=items,
        )

    def _read_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return path.read_text(encoding="latin-1")

    def _parse_stem(self, stem: str) -> dict[str, str]:
        parts = stem.split("_")
        receipt_id = "_".join(parts[:2]) if len(parts) >= 2 else stem
        numeric_id = parts[1] if len(parts) >= 2 and parts[1].isdigit() else "000"
        category = parts[2] if len(parts) >= 3 else "unknown"
        return {"receipt_id": receipt_id, "numeric_id": numeric_id, "category": category}

    def _extract_merchant(self, lines: list[str]) -> str:
        for line in lines[:4]:
            if not PRICE_RE.search(line):
                return line.strip()
        return lines[0].strip()

    def _extract_location(self, lines: list[str]) -> tuple[str | None, str | None, str | None]:
        raw: str | None = None
        city: str | None = None
        state: str | None = None
        for line in lines[:10]:
            stripped = line.strip()
            if PRICE_RE.search(stripped):
                continue
            match = CITY_STATE_RE.match(stripped)
            if match:
                city = match.group(1).strip().lower()
                state = match.group(2).upper()
                raw = stripped
                return raw, city, state
            if raw is None and "," in stripped and len(stripped) > 4:
                raw = stripped
        return raw, city, state

    def _extract_date(self, text: str, lines: list[str]) -> tuple[datetime, str, dict]:
        settings = get_settings()
        for line in lines[:10]:
            if "DATE" in line.upper():
                parsed = parse_receipt_date(
                    line,
                    date_parse_order=settings.date_parse_order,
                    ambiguity_strategy=settings.date_ambiguity_strategy,
                )
                if parsed.iso_date:
                    return datetime.fromisoformat(parsed.iso_date), "date_line", parsed.as_dict()
        match = DATE_RE.search(text)
        if not match:
            raise ValueError("Missing date")
        parsed = parse_receipt_date(
            match.group(1),
            date_parse_order=settings.date_parse_order,
            ambiguity_strategy=settings.date_ambiguity_strategy,
        )
        if not parsed.iso_date:
            raise ValueError(f"Invalid date: {parsed.raw_value or 'unknown'}")
        return datetime.fromisoformat(parsed.iso_date), "regex_scan", parsed.as_dict()

    def _extract_named_amount(self, text: str, label: str) -> float | None:
        for line in text.splitlines():
            upper = line.upper()
            is_target = label == "TOTAL" and any(key in upper for key in ("TOTAL", "GRAND TOTAL", "AMOUNT DUE"))
            if label in upper or is_target:
                m = PRICE_RE.search(line)
                if m:
                    return float(m.group(1))
        return None

    def _extract_tax(self, text: str) -> tuple[float | None, float | None]:
        tax_amount: float | None = None
        tax_rate: float | None = None
        for line in text.splitlines():
            if "TAX" not in line.upper():
                continue
            if tax_amount is None:
                m = PRICE_RE.search(line)
                if m:
                    tax_amount = float(m.group(1))
            if tax_rate is None:
                rate_match = TAX_RATE_RE.search(line)
                if rate_match:
                    tax_rate = float(rate_match.group(1))
            if tax_amount is not None and tax_rate is not None:
                break
        return tax_amount, tax_rate

    def _extract_payment_method(self, lines: list[str]) -> str | None:
        candidates = ("VISA", "MASTERCARD", "AMEX", "DISCOVER", "DEBIT", "CASH", "APPLE PAY")
        for line in lines[-6:]:
            upper = line.upper()
            for c in candidates:
                if c in upper:
                    return c
        return None

    def _extract_tip(self, lines: list[str]) -> tuple[float | None, float | None]:
        for line in lines:
            pct_match = TIP_PCT_RE.match(line)
            if pct_match:
                return float(pct_match.group(2)), float(pct_match.group(1))
        for line in lines:
            if line.strip().upper().startswith("TIP"):
                plain_match = TIP_PLAIN_RE.match(line)
                if plain_match:
                    return float(plain_match.group(1)), None
        return None, None

    def _detect_any(self, lines: list[str], markers: tuple[str, ...]) -> bool:
        for line in lines:
            upper = line.upper()
            if any(marker in upper for marker in markers):
                return True
        return False

    def _extract_loyalty(self, lines: list[str], merchant: str) -> tuple[bool, float | None]:
        loyalty = False
        discount: float | None = None
        merchant_lower = (merchant or "").lower()
        for line in lines:
            upper = line.upper()
            if any(marker in upper for marker in LOYALTY_MARKERS):
                loyalty = True
                neg_match = re.search(r"-\$?\s*([0-9]+(?:\.[0-9]{2})?)", line)
                if neg_match and discount is None:
                    discount = float(neg_match.group(1))
            if discount is None:
                neg_match = re.search(r"^\s*[A-Z].*-\s*\$\s*([0-9]+(?:\.[0-9]{2})?)\s*$", line)
                if neg_match and any(
                    token in upper for token in ("SAVINGS", "DISCOUNT", "REDCARD", "REWARD", "LOYALTY", "MEMBER")
                ):
                    loyalty = True
                    discount = float(neg_match.group(1))
        if not loyalty and merchant_lower in {"target"} and self._detect_any(lines, ("REDCARD",)):
            loyalty = True
        return loyalty, discount

    def _extract_prescription_items(
        self, lines: list[str], numeric_id: str, *, start_idx: int
    ) -> list[ReceiptItem]:
        items: list[ReceiptItem] = []
        in_pickup = False
        idx = start_idx
        for line in lines:
            upper = line.upper()
            if "PHARMACY PICKUP" in upper:
                in_pickup = True
                continue
            if not in_pickup:
                continue
            if any(label in upper for label in ("SUBTOTAL", "TAX", "TOTAL")):
                break
            price_match = PRICE_RE.search(line)
            if not price_match:
                continue
            name = line[: price_match.start()].strip()
            if not name or name.startswith("RX#") or name.startswith("RX #"):
                name = f"Rx: {name}" if name else "Rx prescription"
            else:
                name = f"Rx: {name}"
            items.append(
                ReceiptItem(
                    item_id=f"receipt_{numeric_id}_rx_{idx}",
                    name=name,
                    price=float(price_match.group(1)),
                    quantity=1,
                )
            )
            idx += 1
        return items

    def _extract_items(self, lines: list[str], numeric_id: str) -> tuple[list[ReceiptItem], str]:
        items: list[ReceiptItem] = []
        idx = 1
        parsed_with_qty = False
        in_pickup = False
        for line in lines:
            upper = line.upper()
            if "PHARMACY PICKUP" in upper:
                in_pickup = True
                continue
            if in_pickup:
                if any(label in upper for label in ("SUBTOTAL", "TAX", "TOTAL")):
                    in_pickup = False
                else:
                    continue
            if any(word in upper for word in (*TOTAL_LABELS, "TAX", *SUMMARY_SKIP_WORDS)):
                continue
            if upper.strip().startswith("TIP"):
                continue
            if any(marker in upper for marker in WARRANTY_MARKERS):
                continue
            if any(marker in upper for marker in LOYALTY_MARKERS):
                continue
            match = ITEM_RE.match(line)
            if not match:
                continue
            item_name = match.group("name").strip()
            item_price = float(match.group("price"))
            qty_raw = match.group("qty")
            quantity = int(qty_raw) if qty_raw else 1
            parsed_with_qty = parsed_with_qty or qty_raw is not None
            items.append(
                ReceiptItem(
                    item_id=f"receipt_{numeric_id}_item_{idx}",
                    name=item_name,
                    price=item_price,
                    quantity=quantity,
                )
            )
            idx += 1
        parse_mode = "qty_pattern" if parsed_with_qty else "basic_pattern"
        return items, parse_mode

