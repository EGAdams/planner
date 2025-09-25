from dataclasses import dataclass
from typing import Optional
from .base import ID

@dataclass
class Expense:
    id: Optional[ID]
    org_id: int
    expense_date: str  # YYYY-MM-DD
    amount: float
    category_id: int
    description: Optional[str] = None
    paid_by_contact_id: Optional[int] = None
    method: str = "OTHER"  # 'CASH' | 'CARD' | 'BANK' | 'OTHER'
    receipt_url: Optional[str] = None