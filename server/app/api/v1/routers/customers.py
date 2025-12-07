"""
Vendly POS - Customers Router
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db import models as m

router = APIRouter()


# ---------- Schemas ----------
class CustomerIn(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    loyalty_points: Optional[int] = 0
    is_active: bool = True


class CustomerOut(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    loyalty_points: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LoyaltyAdjustment(BaseModel):
    points: int
    reason: Optional[str] = None


# ---------- Endpoints ----------
@router.get("", response_model=List[CustomerOut])
def list_customers(
    q: Optional[str] = Query(None),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """List all customers with optional filtering"""
    stmt = db.query(m.Customer)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.filter(
            m.Customer.name.ilike(like)
            | m.Customer.email.ilike(like)
            | m.Customer.phone.ilike(like)
        )
    if active_only:
        stmt = stmt.filter(m.Customer.is_active == True)
    return stmt.order_by(m.Customer.name).offset(skip).limit(limit).all()


@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(
    payload: CustomerIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Create a new customer"""
    # Check for duplicate email
    if payload.email:
        existing = (
            db.query(m.Customer).filter(m.Customer.email == payload.email).first()
        )
        if existing:
            raise HTTPException(400, detail="Customer with this email already exists")

    customer = m.Customer(
        name=payload.name,
        email=payload.email,
        phone=payload.phone,
        address=payload.address,
        notes=payload.notes,
        is_active=payload.is_active,
        loyalty_points=payload.loyalty_points or 0,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get a single customer by ID"""
    customer = db.get(m.Customer, customer_id)
    if not customer:
        raise HTTPException(404, detail="Customer not found")
    return customer


@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int,
    payload: CustomerIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Update an existing customer"""
    customer = db.get(m.Customer, customer_id)
    if not customer:
        raise HTTPException(404, detail="Customer not found")

    # Check for duplicate email if changing
    if payload.email and payload.email != customer.email:
        existing = (
            db.query(m.Customer).filter(m.Customer.email == payload.email).first()
        )
        if existing:
            raise HTTPException(400, detail="Customer with this email already exists")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(customer, field, value)

    db.commit()
    db.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=204)
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Delete a customer"""
    customer = db.get(m.Customer, customer_id)
    if not customer:
        return
    db.delete(customer)
    db.commit()


@router.post("/{customer_id}/adjust-loyalty", response_model=CustomerOut)
def adjust_loyalty_points(
    customer_id: int,
    payload: LoyaltyAdjustment,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Add or subtract loyalty points for a customer"""
    customer = db.get(m.Customer, customer_id)
    if not customer:
        raise HTTPException(404, detail="Customer not found")

    customer.loyalty_points = max(0, customer.loyalty_points + payload.points)
    db.commit()
    db.refresh(customer)
    return customer
