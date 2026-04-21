from __future__ import annotations

from receipt_intel.models import Receipt, ReceiptChunk


def build_chunks(receipt: Receipt, strategy: str = "hybrid") -> list[ReceiptChunk]:
    if strategy == "receipt_level":
        return _receipt_level(receipt)
    if strategy == "item_level":
        return _item_level(receipt)
    return _hybrid(receipt)


def _receipt_level(receipt: Receipt) -> list[ReceiptChunk]:
    lines = [f"Merchant: {receipt.merchant}", f"Date: {receipt.date.date()}", f"Total: {receipt.total:.2f}"]
    lines.extend(f"{item.name} - ${item.price:.2f}" for item in receipt.items)
    return [
        ReceiptChunk(
            chunk_id=f"{receipt.receipt_id}_receipt",
            receipt_id=receipt.receipt_id,
            chunk_type="receipt",
            content="\n".join(lines),
            metadata=_base_metadata(receipt),
        )
    ]


def _item_level(receipt: Receipt) -> list[ReceiptChunk]:
    chunks: list[ReceiptChunk] = []
    for item in receipt.items:
        chunks.append(
            ReceiptChunk(
                chunk_id=f"{receipt.receipt_id}_{item.item_id}",
                receipt_id=receipt.receipt_id,
                chunk_type="item",
                content=f"{item.name} (${item.price:.2f}) from {receipt.merchant} on {receipt.date.date()}",
                metadata={**_base_metadata(receipt), "item_id": item.item_id, "item_name": item.name, "item_price": item.price},
            )
        )
    return chunks


def _hybrid(receipt: Receipt) -> list[ReceiptChunk]:
    return _receipt_level(receipt) + _item_level(receipt)


def _base_metadata(receipt: Receipt) -> dict[str, str | float | int | None]:
    return {
        "receipt_id": receipt.receipt_id,
        "merchant": receipt.merchant,
        "category": receipt.category,
        "date": receipt.date.date().isoformat(),
        "total_amount": receipt.total,
        "tax": receipt.tax,
        "location": receipt.location,
        "payment_method": receipt.payment_method,
        "items_count": len(receipt.items),
    }

