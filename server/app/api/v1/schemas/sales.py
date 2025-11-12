from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class SaleOpenIn(BaseModel):
    store_id: UUID
    register_id: UUID


class SaleOut(BaseModel):
    id: UUID
    status: str
    subtotal_cents: int
    discount_cents: int
    tax_cents: int
    total_cents: int


class SaleLineIn(BaseModel):
    variant_id: UUID
    qty: int
    unit_price_cents: int


class PaymentIn(BaseModel):
    method_code: str
    amount_cents: int


class CompleteOut(BaseModel):
    id: UUID
    total_cents: int
    status: str
