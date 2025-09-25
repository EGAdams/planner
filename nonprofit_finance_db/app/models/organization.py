from dataclasses import dataclass
from typing import Optional
from .base import ID

@dataclass
class Organization:
    id: Optional[ID]
    name: str
    type: str  # 'NONPROFIT' | 'PERSONAL'