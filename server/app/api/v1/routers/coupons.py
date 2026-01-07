"""
Vendly POS - Coupons Router
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.v1.schemas.coupons import (
    CouponCreate,
    CouponOut,
    CouponUpdate,
    CouponValidateRequest,
    CouponValidateResponse,
)
from app.core.deps import get_current_user, get_db
from app.db import models as m

router = APIRouter()


@router.get("", response_model=List[CouponOut])
def list_coupons(
    active_only: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """List all coupons with optional filtering"""
    stmt = db.query(m.Coupon)
    if active_only:
        stmt = stmt.filter(m.Coupon.active == True)
    return stmt.order_by(m.Coupon.created_at.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=CouponOut, status_code=201)
def create_coupon(
    data: CouponCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create a new coupon"""
    # Check if code already exists
    existing = db.query(m.Coupon).filter(m.Coupon.code == data.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Coupon code already exists")

    coupon = m.Coupon(
        code=data.code.upper(),
        type=data.type.value,
        value=data.value,
        max_off=data.max_off,
        min_order=data.min_order,
        active=data.active,
        expires_at=data.expires_at,
        stackable=data.stackable,
        usage_count=0,
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon


@router.get("/{coupon_id}", response_model=CouponOut)
def get_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get a coupon by ID"""
    coupon = db.query(m.Coupon).filter(m.Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return coupon


@router.put("/{coupon_id}", response_model=CouponOut)
def update_coupon(
    coupon_id: int,
    data: CouponUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Update an existing coupon"""
    coupon = db.query(m.Coupon).filter(m.Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    update_data = data.model_dump(exclude_unset=True)

    # Check if new code conflicts with existing
    if "code" in update_data and update_data["code"]:
        update_data["code"] = update_data["code"].upper()
        existing = (
            db.query(m.Coupon)
            .filter(m.Coupon.code == update_data["code"], m.Coupon.id != coupon_id)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Coupon code already exists")

    # Convert type enum to string if present
    if "type" in update_data and update_data["type"]:
        update_data["type"] = update_data["type"].value

    for field, value in update_data.items():
        setattr(coupon, field, value)

    db.commit()
    db.refresh(coupon)
    return coupon


@router.delete("/{coupon_id}", status_code=204)
def delete_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Delete a coupon"""
    coupon = db.query(m.Coupon).filter(m.Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    db.delete(coupon)
    db.commit()


@router.patch("/{coupon_id}/toggle", response_model=CouponOut)
def toggle_coupon(
    coupon_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Toggle a coupon's active status"""
    coupon = db.query(m.Coupon).filter(m.Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    coupon.active = not coupon.active
    db.commit()
    db.refresh(coupon)
    return coupon


@router.post("/validate", response_model=CouponValidateResponse)
def validate_coupon(
    data: CouponValidateRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Validate a coupon code and calculate discount"""
    coupon = db.query(m.Coupon).filter(m.Coupon.code == data.code.upper()).first()

    if not coupon:
        return CouponValidateResponse(valid=False, message="Coupon not found")

    if not coupon.active:
        return CouponValidateResponse(valid=False, message="Coupon is not active")

    if coupon.expires_at and coupon.expires_at < datetime.now():
        return CouponValidateResponse(valid=False, message="Coupon has expired")

    if coupon.min_order and data.order_total < coupon.min_order:
        return CouponValidateResponse(
            valid=False, message=f"Minimum order amount is ${coupon.min_order:.2f}"
        )

    # Calculate discount
    if coupon.type in ("percent", "percentage"):
        discount_amount = float(data.order_total) * (float(coupon.value) / 100)
        if coupon.max_off and discount_amount > float(coupon.max_off):
            discount_amount = float(coupon.max_off)
    else:
        discount_amount = min(float(coupon.value), float(data.order_total))

    return CouponValidateResponse(
        valid=True,
        coupon=CouponOut.model_validate(coupon),
        discount_amount=discount_amount,
        message="Coupon applied successfully",
    )


@router.post("/{coupon_id}/increment-usage", response_model=CouponOut)
def increment_coupon_usage(
    coupon_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Increment the usage count of a coupon"""
    coupon = db.query(m.Coupon).filter(m.Coupon.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    coupon.usage_count += 1
    db.commit()
    db.refresh(coupon)
    return coupon
