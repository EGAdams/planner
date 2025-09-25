from dataclasses import dataclass
from typing import Optional
from .base import ID

@dataclass
class Category:
    id: Optional[ID]
    name: str
    kind: str  # 'EXPENSE' | 'INCOME'
    is_active: bool = True