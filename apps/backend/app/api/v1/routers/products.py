from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.deps import get_db, get_current_user
from app.db import models as m
from app.api.v1.schemas.products import ProductIn, ProductOut

router = APIRouter()

@router.get("", response_model=List[ProductOut])
def list_products(q: Optional[str] = Query(None), db: Session = Depends(get_db), user=Depends(get_current_user)):
    stmt = db.query(m.Product)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.filter(m.Product.name.ilike(like))
    return stmt.order_by(m.Product.name).all()

@router.post("", response_model=ProductOut, status_code=201)
def create_product(payload: ProductIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    prod = m.Product(
        name=payload.name, sku=payload.sku, description=payload.description,
        category_id=payload.category_id, default_tax_id=payload.default_tax_id,
        is_active=payload.is_active,
    )
    for v in payload.variants:
        prod.variants.append(m.ProductVariant(sku=v.sku, price_cents=v.price_cents, cost_cents=v.cost_cents, attributes=v.attributes))
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod

@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    prod = db.get(m.Product, product_id)
    if not prod:
        raise HTTPException(404, detail="Product not found")
    return prod

@router.patch("/{product_id}", response_model=ProductOut)
def update_product(product_id: UUID, payload: ProductIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    prod = db.get(m.Product, product_id)
    if not prod:
        raise HTTPException(404, detail="Product not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        if field == "variants":
            continue
        setattr(prod, field, value)
    sku_to_variant = {v.sku: v for v in prod.variants}
    for v in payload.variants:
        if v.sku in sku_to_variant:
            var = sku_to_variant[v.sku]
            var.price_cents = v.price_cents
            var.cost_cents = v.cost_cents
            var.attributes = v.attributes
        else:
            prod.variants.append(m.ProductVariant(sku=v.sku, price_cents=v.price_cents, cost_cents=v.cost_cents, attributes=v.attributes))
    db.commit()
    db.refresh(prod)
    return prod

@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    prod = db.get(m.Product, product_id)
    if not prod:
        return
    db.delete(prod)
    db.commit()