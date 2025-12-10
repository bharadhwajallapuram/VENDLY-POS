"""
Vendly POS - Sales Schemas
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class SaleItemIn(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    discount: float = 0


class OfflinePayment(BaseModel):
    method: str
    amount: float


class OfflineSaleIn(BaseModel):
    """Schema for offline sale data that needs to be synced"""
    id: str  # Offline UUID for tracking
    items: List[SaleItemIn]
    payments: List[OfflinePayment]
    discount: float = 0
    coupon_code: Optional[str] = None
    notes: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    created_at: str  # ISO date string from client


class BatchSyncRequest(BaseModel):
    """Request body for batch sync of offline sales"""
    sales: List[OfflineSaleIn]


class SyncResultItem(BaseModel):
    """Result for a single synced sale"""
    success: bool
    offlineId: str
    serverId: Optional[int] = None
    error: Optional[str] = None


class BatchSyncResponse(BaseModel):
    """Response for batch sync operation"""
    synced: int
    failed: int
    results: List[SyncResultItem]


class SaleItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_id: int
    product_id: int
    product_name: Optional[str] = None
    quantity: int
    unit_price: float
    discount: float
    total: float


class SaleIn(BaseModel):
    customer_id: Optional[int] = None
    items: List[SaleItemIn]
    discount: float = 0  # manual order-level discount
    coupon_code: Optional[str] = None  # promo/coupon code applied to this sale
    payment_method: str = "cash"
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


class SaleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    customer_id: Optional[int] = None
    subtotal: float
    tax: float
    discount: float  # total discount (order + coupon)
    order_discount: Optional[float] = None  # manual discount
    coupon_discount: Optional[float] = None  # discount derived from coupon
    coupon_code: Optional[str] = None
    total: float
    payment_method: str
    payment_reference: Optional[str] = None
    status: str
    notes: Optional[str] = None
    created_at: datetime
    items: List[SaleItemOut] = []


class SaleListOut(BaseModel):
    items: List[SaleOut]
    total: int
