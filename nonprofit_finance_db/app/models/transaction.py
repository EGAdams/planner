from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from .base import ID

@dataclass
class Transaction:
    id: Optional[ID]
    org_id: int
    transaction_date: str  # YYYY-MM-DD
    amount: float
    description: str
    transaction_type: str  # 'DEBIT' | 'CREDIT' | 'TRANSFER'
    account_number: Optional[str] = None
    bank_reference: Optional[str] = None
    balance_after: Optional[float] = None
    category_id: Optional[int] = None
    import_batch_id: Optional[int] = None
    raw_data: Optional[str] = None  # Original bank statement line as JSON
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class ImportBatch:
    id: Optional[ID]
    org_id: int
    filename: str
    file_format: str  # 'CSV' | 'PDF' | 'OFX'
    import_date: datetime
    total_transactions: int
    successful_imports: int
    failed_imports: int
    duplicate_count: int
    status: str  # 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
    error_log: Optional[str] = None
    created_at: Optional[datetime] = None

@dataclass
class DuplicateFlag:
    id: Optional[ID]
    transaction_id: int
    duplicate_transaction_id: int
    confidence_score: float  # 0.0 to 1.0
    match_criteria: str  # JSON string describing what matched
    status: str  # 'PENDING' | 'CONFIRMED' | 'REJECTED'
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None