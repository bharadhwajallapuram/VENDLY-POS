from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from uuid import UUID

class CategoryOut(BaseModel):
    id: UUID
    name: str
    parent_id: Optional[UUID] = None

class TaxRateOut(BaseModel):
    id: UUID
    name: str
    rate: float

class VariantIn(BaseModel):
    sku: str
    price_cents: int
    cost_cents: Optional[int] = None
    attributes: Optional[Dict] = None

class VariantOut(VariantIn):
    id: UUID
    product_id: UUID

class ProductIn(BaseModel):
    name: str
    sku: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[UUID] = None
    default_tax_id: Optional[UUID] = None
    is_active: bool = True
    variants: List[VariantIn] = Field(default_factory=list)

class ProductOut(ProductIn):
    id: UUID
    variants: List[VariantOut] = []