from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReceiptItem(BaseModel):
    item_id: str
    name: str
    price: float
    quantity: int = 1


class Receipt(BaseModel):
    receipt_id: str
    source_file: str
    merchant: str
    category: str
    date: datetime
    location: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    total: float
    payment_method: Optional[str] = None
    discount: Optional[float] = None
    metadata: dict[str, str | float | int | None] = Field(default_factory=dict)
    items: list[ReceiptItem] = Field(default_factory=list)

