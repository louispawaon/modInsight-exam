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
    city: Optional[str] = None
    state: Optional[str] = None
    subtotal: Optional[float] = None
    tax: Optional[float] = None
    tax_rate: Optional[float] = None
    total: float
    payment_method: Optional[str] = None
    discount: Optional[float] = None
    tip_amount: Optional[float] = None
    tip_pct: Optional[float] = None
    has_prescription: bool = False
    has_warranty: bool = False
    loyalty_flag: bool = False
    metadata: dict[str, str | float | int | bool | None] = Field(default_factory=dict)
    items: list[ReceiptItem] = Field(default_factory=list)

