from pydantic import BaseModel, Field, ValidationError
from typing import List

class ReceiptItem(BaseModel):
    description: str = Field(..., min_length=1)
    quantity: float = Field(1.0)
    unit_price: float = Field(...)
    line_total: float = Field(...)

try:
    item = ReceiptItem(description="Test", quantity=1, unit_price=-1.39, line_total=-1.39)
    print("Success:", item)
except ValidationError as e:
    print("Validation Error:", e)
