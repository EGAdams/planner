from dataclasses import dataclass
from typing import Optional
from .base import ID

@dataclass
class Contact:
    id: Optional[ID]
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    contact_type: str = "PERSON"  # 'PERSON' | 'ORG'