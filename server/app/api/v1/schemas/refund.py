from pydantic import BaseModel
from typing import List, Optional

class RefundItem(BaseModel):
    sale_item_id: int
    quantity: int

class RefundRequest(BaseModel):
    items: List[RefundItem]
    employee_id: str  # Required employee ID for validation
    reason: Optional[str] = None

class RefundResponse(BaseModel):
    sale_id: int
    refunded_items: List[RefundItem]
    status: str
    refund_amount: float
    processed_by: Optional[str] = None  # Employee ID who processed the refund
    message: Optional[str] = None
