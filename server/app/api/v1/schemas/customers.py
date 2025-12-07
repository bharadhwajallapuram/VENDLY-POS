# ===========================================
# Vendly POS - Customer Schemas
# ===========================================

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class CustomerBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class CustomerIn(CustomerBase):
    loyalty_points: Optional[int] = 0
    is_active: Optional[bool] = True


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    loyalty_points: Optional[int] = None
    is_active: Optional[bool] = None


class CustomerOut(CustomerBase):
    id: int
    loyalty_points: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoyaltyAdjustment(BaseModel):
    points: int
    reason: Optional[str] = None
