"""
Vendly POS - Users Router (Admin Only)
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_role
from app.db import models as m
from app.services.audit import (
    AuditAction,
    log_audit,
    log_user_created,
    log_user_deleted,
)
from app.services.auth import hash_password

router = APIRouter()


# ---------- Schemas ----------
class UserIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    full_name: Optional[str] = None
    role: str = "clerk"  # clerk, manager, admin


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


# ---------- Admin dependency ----------
require_admin = require_role(["admin"])


# ---------- Endpoints ----------
@router.get("", response_model=List[UserOut])
def list_users(
    q: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    """List all users (admin only)"""
    query = db.query(m.User)

    if q:
        search = f"%{q}%"
        query = query.filter(
            (m.User.email.ilike(search)) | (m.User.full_name.ilike(search))
        )

    return query.order_by(m.User.email).offset(skip).limit(limit).all()


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    payload: UserIn,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """Create a new user (admin only)"""
    # Check for duplicate email
    existing = db.query(m.User).filter(m.User.email == payload.email).first()
    if existing:
        raise HTTPException(400, detail="User with this email already exists")

    # Validate role
    valid_roles = ["clerk", "manager", "admin"]
    if payload.role not in valid_roles:
        raise HTTPException(
            400, detail=f"Role must be one of: {', '.join(valid_roles)}"
        )

    new_user = m.User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Audit log
    log_user_created(admin.id, new_user.id, new_user.email, new_user.role)

    return new_user


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    """Get a single user by ID (admin only)"""
    db_user = db.get(m.User, user_id)
    if not db_user:
        raise HTTPException(404, detail="User not found")
    return db_user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Update a user (admin only)"""
    db_user = db.get(m.User, user_id)
    if not db_user:
        raise HTTPException(404, detail="User not found")

    # Check for duplicate email if changing
    if payload.email and payload.email != db_user.email:
        existing = db.query(m.User).filter(m.User.email == payload.email).first()
        if existing:
            raise HTTPException(400, detail="User with this email already exists")

    # Validate role if changing
    if payload.role:
        valid_roles = ["clerk", "manager", "admin"]
        if payload.role not in valid_roles:
            raise HTTPException(
                400, detail=f"Role must be one of: {', '.join(valid_roles)}"
            )

    # Apply updates
    if payload.email is not None:
        db_user.email = payload.email
    if payload.full_name is not None:
        db_user.full_name = payload.full_name
    if payload.role is not None:
        db_user.role = payload.role
    if payload.is_active is not None:
        db_user.is_active = payload.is_active
    if payload.password is not None:
        db_user.password_hash = hash_password(payload.password)

    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete("/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """Delete a user (admin only)"""
    db_user = db.get(m.User, user_id)
    if not db_user:
        return

    # Prevent deleting yourself
    if db_user.id == current_user.id:
        raise HTTPException(400, detail="Cannot delete your own account")

    # Audit log before deletion
    log_user_deleted(current_user.id, db_user.id, db_user.email)

    db.delete(db_user)
    db.commit()
