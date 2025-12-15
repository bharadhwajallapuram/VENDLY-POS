from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PurchaseOrderCreate(BaseModel):
    product_id: int
    quantity: int
    supplier_notes: Optional[str] = None
    status: Optional[str] = "pending"


class PurchaseOrderResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    supplier_notes: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
