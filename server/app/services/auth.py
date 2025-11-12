from typing import Optional
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def authenticate(db: Session, email: str, password: str) -> Optional[dict]:
    """
    Authenticate user with email and password
    For now, return a dummy token for demo purposes
    """
    # Demo users for testing
    demo_users = {
        "demo@vendly.com": {"password": "demo123", "role": "cashier", "name": "Demo Cashier"},
        "admin@vendly.com": {"password": "admin123", "role": "admin", "name": "Admin User"},
        "manager@vendly.com": {"password": "manager123", "role": "manager", "name": "Manager User"}
    }
    
    if email in demo_users and demo_users[email]["password"] == password:
        user_data = demo_users[email]
        access_token = create_access_token(data={
            "sub": email,
            "role": user_data["role"],
            "name": user_data["name"]
        })
        return {
            "access_token": access_token,
            "refresh_token": access_token,  # Same for demo
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TTL_MIN * 60
        }
    return None

async def register_user(db: Session, email: str, password: str, full_name: str, role: str = "cashier"):
    """
    Register a new user
    For now, return a dummy user for demo purposes
    """
    # Check if user already exists in demo users
    demo_users = ["demo@vendly.com", "admin@vendly.com", "manager@vendly.com"]
    if email in demo_users:
        return None  # User already exists
    
    # TODO: Implement actual user creation in database
    return type('User', (), {
        'email': email,
        'full_name': full_name,
        'role': role,
        'id': len(demo_users) + 1
    })()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TTL_MIN)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
    return encoded_jwt
