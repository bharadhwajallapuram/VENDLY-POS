"""
Vendly POS - Products Schemas
"""
from typing import List, Optional

from pydantic import BaseModel


class CategoryIn(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool = True


class CategoryOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool = True

    class Config:
        from_attributes = True


class ProductIn(BaseModel):
    name: str
    sku: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    price: float
    cost: Optional[float] = None
    quantity: int = 0
    min_quantity: int = 0
    category_id: Optional[int] = None
    tax_rate: float = 0
    image_url: Optional[str] = None
    is_active: bool = True


class ProductOut(BaseModel):
    id: int
    name: str
    sku: Optional[str] = None
    barcode: Optional[str] = None
    description: Optional[str] = None
    price: float
    cost: Optional[float] = None
    quantity: int
    min_quantity: int
    category_id: Optional[int] = None
    tax_rate: float
    image_url: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class ProductListOut(BaseModel):
    items: List[ProductOut]
    total: int
