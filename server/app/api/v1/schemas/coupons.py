"""
Vendly POS - Coupon Schemas
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CouponType(str, Enum):
    percentage = "percentage"
    fixed = "fixed"


class CouponBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    type: CouponType
    value: float = Field(..., gt=0)
    max_off: Optional[float] = Field(None, ge=0)
    min_order: Optional[float] = Field(None, ge=0)
    active: bool = True
    expires_at: Optional[datetime] = None
    stackable: bool = True

    @field_validator("type", mode="before")
    @classmethod
    def normalize_coupon_type(cls, v: str) -> str:
        """Accept 'percent'/'amount' as aliases for 'percentage'/'fixed'"""
        if isinstance(v, str):
            mapping = {"percent": "percentage", "amount": "fixed"}
            return mapping.get(v.lower(), v)
        return v


class CouponCreate(CouponBase):
    pass


class CouponUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    type: Optional[CouponType] = None
    value: Optional[float] = Field(None, gt=0)
    max_off: Optional[float] = Field(None, ge=0)
    min_order: Optional[float] = Field(None, ge=0)
    active: Optional[bool] = None
    expires_at: Optional[datetime] = None
    stackable: Optional[bool] = None


class CouponOut(CouponBase):
    id: int
    usage_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class CouponValidateRequest(BaseModel):
    code: str
    order_total: float = Field(..., ge=0)


class CouponValidateResponse(BaseModel):
    valid: bool
    coupon: Optional[CouponOut] = None
    discount_amount: float = 0
    message: str
