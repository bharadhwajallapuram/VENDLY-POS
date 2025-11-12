from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(p: str) -> str:
    return pwd_context.hash(p)

def verify_password(p: str, h: str) -> bool:
    return pwd_context.verify(p, h)

def create_access_token(sub: str, expires_min: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_min or settings.ACCESS_TTL_MIN)
    return jwt.encode({"sub": sub, "exp": expire}, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def create_refresh_token(sub: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TTL_DAYS)
    return jwt.encode({"sub": sub, "exp": expire, "type": "refresh"}, settings.JWT_SECRET, algorithm=settings.JWT_ALG)