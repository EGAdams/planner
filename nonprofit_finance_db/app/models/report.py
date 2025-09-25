from dataclasses import dataclass
from typing import Optional
from .base import ID

@dataclass
class Report:
    id: Optional[ID]
    title: str
    date_created: str  # YYYY-MM-DD
    start_date: str    # YYYY-MM-DD
    end_date: str      # YYYY-MM-DD
    notes: Optional[str] = None
    file_url: Optional[str] = None