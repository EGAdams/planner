from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, validator
from datetime import date


PaymentMethod = Literal["CASH", "CARD", "BANK", "OTHER"]


class ReceiptItem(BaseModel):
    description: str = Field(..., min_length=1)
    quantity: float = Field(1.0, ge=0)
    unit_price: float = Field(..., ge=0)
    line_total: float = Field(..., ge=0)

    @validator("line_total", always=True)
    def compute_line_total(cls, v, values):
        qty = values.get("quantity", 1.0)
        price = values.get("unit_price", 0.0)
        if v is None:
            return round(qty * price, 2)
        return v


class ReceiptTotals(BaseModel):
    subtotal: float = Field(..., ge=0)
    tax_amount: Optional[float] = Field(0.0, ge=0)
    tip_amount: Optional[float] = Field(0.0, ge=0)
    discount_amount: Optional[float] = Field(0.0, ge=0)
    total_amount: float = Field(..., ge=0)


class ReceiptPartyInfo(BaseModel):
    merchant_name: str = Field(..., min_length=1)
    merchant_phone: Optional[str]
    merchant_address: Optional[str]
    store_location: Optional[str]


class ReceiptMeta(BaseModel):
    currency: str = Field("USD", min_length=3, max_length=3)
    receipt_number: Optional[str]
    model_name: Optional[str]
    model_provider: Optional[str]
    engine_version: Optional[str]
    raw_text: Optional[str]


class ReceiptExtractionResult(BaseModel):
    transaction_date: date
    payment_method: PaymentMethod
    party: ReceiptPartyInfo
    items: List[ReceiptItem]
    totals: ReceiptTotals
    meta: ReceiptMeta
