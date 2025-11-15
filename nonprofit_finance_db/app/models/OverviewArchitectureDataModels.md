# Receipt Engine Architecture (Gemini‑first, OpenAI‑swappable, with Checks & Balances)

This document focuses on **how we architect the Python side** so that:

1. **Gemini Flash** is the primary engine for receipt parsing right now.  
2. We can **swap in OpenAI (GPT‑4o / mini) later** with minimal disruption.  
3. We have a clear **“trust but verify” pipeline**: the output is *validated* before being considered “good” and forwarded to the next process (e.g., creating an `Expense`).

---

## 1. High‑Level Architecture

### 1.1 Core Concepts

We’ll introduce four main backend pieces:

1. **`ReceiptEngine` interface (Protocol)**  
   - Abstract interface the rest of your code talks to.  
   - Concrete implementations:  
     - `GeminiReceiptEngine` (primary)  
     - `OpenAIReceiptEngine` (swappable later)  
2. **`ReceiptExtractionResult` (Pydantic model)**  
   - Canonical structured representation of what the AI engine returns:  
     - merchant, date, items, totals, payment method, currency, etc.  
3. **`ReceiptValidator`**  
   - Performs **checks and balances** on the AI output:  
     - numeric consistency of totals, required fields, non‑negative amounts, etc.  
     - returns a **validation report** with `is_valid` + list of issues.  
4. **`ReceiptParserService`**  
   - Orchestrator used by the FastAPI route:  
     - receives uploaded file  
     - prepares image bytes  
     - calls `ReceiptEngine.extract_receipt(...)`  
     - runs `ReceiptValidator.validate(...)`  
     - returns both `extraction_result` and `validation_report` to the API layer  

The API route (`/api/parse‑receipt`) will **not** be tightly coupled to Gemini or OpenAI. It only depends on:

- `ReceiptParserService`  
- which in turn depends on a `ReceiptEngine` instance.

---

## 2. Shared Data Models (Pydantic)

Create a new module:

`nonprofit_finance_db/app/models/receipt_models.py`

```python
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
