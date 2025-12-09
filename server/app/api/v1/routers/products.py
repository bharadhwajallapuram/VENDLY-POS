"""
Vendly POS - Products Router
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.schemas.products import (
    CategoryIn,
    CategoryOut,
    ProductIn,
    ProductOut,
)
from app.core.deps import get_current_user, get_db
from app.db import models as m

router = APIRouter()


# ---------- Products ----------
@router.get("", response_model=List[ProductOut])
def list_products(
    q: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """List all products with optional filtering"""
    stmt = db.query(m.Product)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.filter(
            m.Product.name.ilike(like)
            | m.Product.sku.ilike(like)
            | m.Product.barcode.ilike(like)
        )
    if category_id:
        stmt = stmt.filter(m.Product.category_id == category_id)
    if active_only:
        stmt = stmt.filter(m.Product.is_active == True)
    return stmt.order_by(m.Product.name).offset(skip).limit(limit).all()


@router.post("", response_model=ProductOut, status_code=201)
def create_product(
    payload: ProductIn, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    """Create a new product"""
    prod = m.Product(
        name=payload.name,
        sku=payload.sku,
        barcode=payload.barcode,
        description=payload.description,
        price=payload.price,
        cost=payload.cost,
        quantity=payload.quantity,
        min_quantity=payload.min_quantity,
        category_id=payload.category_id,
        tax_rate=payload.tax_rate,
        image_url=payload.image_url,
        is_active=payload.is_active,
    )
    db.add(prod)
    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        error_str = str(e).lower()
        if "sku" in error_str:
            raise HTTPException(409, detail="A product with this SKU already exists")
        elif "barcode" in error_str:
            raise HTTPException(
                409, detail="A product with this barcode already exists"
            )
        else:
            raise HTTPException(
                409, detail="Product with duplicate unique field already exists"
            )
    db.refresh(prod)
    return prod


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    """Get a single product by ID"""
    prod = db.get(m.Product, product_id)
    if not prod:
        raise HTTPException(404, detail="Product not found")
    return prod


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Update an existing product"""
    prod = db.get(m.Product, product_id)
    if not prod:
        raise HTTPException(404, detail="Product not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prod, field, value)

    try:
        db.commit()
    except IntegrityError as e:
        db.rollback()
        error_str = str(e).lower()
        if "sku" in error_str:
            raise HTTPException(409, detail="A product with this SKU already exists")
        elif "barcode" in error_str:
            raise HTTPException(
                409, detail="A product with this barcode already exists"
            )
        else:
            raise HTTPException(
                409, detail="Product with duplicate unique field already exists"
            )
    db.refresh(prod)
    return prod


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)
):
    """Delete a product"""
    prod = db.get(m.Product, product_id)
    if not prod:
        return
    db.delete(prod)
    db.commit()
