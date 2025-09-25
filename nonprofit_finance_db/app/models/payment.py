from dataclasses import dataclass
from typing import Optional
from .base import ID

@dataclass
class Payment:
    id: Optional[ID]
    org_id: int
    payment_date: str  # YYYY-MM-DD
    amount: float
    source_contact_id: Optional[int]
    type: str  # 'DONATION' | 'GRANT' | 'REIMBURSEMENT' | 'OTHER'
    notes: Optional[str] = None