"""
Vendly POS - Sales Schemas
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class SaleItemIn(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    discount: float = 0


class SaleItemOut(BaseModel):
    id: int
    sale_id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: int
    unit_price: float
    discount: float
    total: float

    class Config:
        from_attributes = True


class SaleIn(BaseModel):
    customer_id: Optional[int] = None
    items: List[SaleItemIn]
    discount: float = 0
    payment_method: str = "cash"
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


class SaleOut(BaseModel):
    id: int
    user_id: int
    customer_id: Optional[int] = None
    subtotal: float
    tax: float
    discount: float
    total: float
    payment_method: str
    payment_reference: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    items: List[SaleItemOut] = []

    class Config:
        from_attributes = True


class SaleListOut(BaseModel):
    items: List[SaleOut]
    total: int
