"""
Vendly POS - Categories Router
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.schemas.products import CategoryIn, CategoryOut
from app.core.deps import get_current_user, get_db
from app.db import models as m

router = APIRouter()


@router.get("", response_model=List[CategoryOut])
def list_categories(
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """List all categories"""
    stmt = db.query(m.Category)
    if active_only:
        stmt = stmt.filter(m.Category.is_active == True)
    return stmt.order_by(m.Category.name).offset(skip).limit(limit).all()


@router.get("/{category_id}", response_model=CategoryOut)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get a specific category"""
    category = db.query(m.Category).filter(m.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("", response_model=CategoryOut, status_code=201)
def create_category(
    payload: CategoryIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create a new category"""
    category = m.Category(
        name=payload.name,
        description=payload.description,
        parent_id=payload.parent_id,
        is_active=payload.is_active if payload.is_active is not None else True,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    payload: CategoryIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Update a category"""
    category = db.query(m.Category).filter(m.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category.name = payload.name
    category.description = payload.description
    category.parent_id = payload.parent_id
    if payload.is_active is not None:
        category.is_active = payload.is_active

    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=204)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Delete a category"""
    category = db.query(m.Category).filter(m.Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check if any products are using this category
    product_count = (
        db.query(m.Product).filter(m.Product.category_id == category_id).count()
    )
    if product_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete category with {product_count} products. Reassign products first.",
        )

    db.delete(category)
    db.commit()
    return None
