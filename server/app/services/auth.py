"""
Vendly POS - Authentication Services
"""

from datetime import UTC, datetime, timedelta
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import models as m


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


async def authenticate(db: Session, email: str, password: str) -> Optional[dict]:
    """
    Authenticate user with email and password
    """
    # Look up user in database
    user = db.query(m.User).filter(m.User.email == email).first()

    if not user:
        return None

    if not verify_password(password, user.password_hash):
        return None

    if not user.is_active:
        return None

    # Create access token
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role,
            "name": user.full_name or user.email,
        }
    )

    return {
        "access_token": access_token,
        "refresh_token": access_token,  # Same for now
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TTL_MIN * 60,
        "user_id": user.id,  # For audit logging
    }


async def register_user(
    db: Session, email: str, password: str, full_name: str, role: str = "clerk"
) -> Optional[m.User]:
    """
    Register a new user
    """
    # Check if user already exists
    existing = db.query(m.User).filter(m.User.email == email).first()
    if existing:
        return None

    # Create user
    user = m.User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TTL_MIN)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
    return encoded_jwt
