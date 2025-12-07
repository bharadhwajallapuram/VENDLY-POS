from datetime import datetime, timedelta, timezone

from jose import jwt
import bcrypt

from app.core.config import settings


def hash_password(p: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(p.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(p: str, h: str) -> bool:
    """Verify a password against a hash"""
    return bcrypt.checkpw(p.encode("utf-8"), h.encode("utf-8"))


def create_access_token(sub: str, expires_min: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_min or settings.ACCESS_TTL_MIN
    )
    return jwt.encode(
        {"sub": sub, "exp": expire}, settings.JWT_SECRET, algorithm=settings.JWT_ALG
    )


def create_refresh_token(sub: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TTL_DAYS)
    return jwt.encode(
        {"sub": sub, "exp": expire, "type": "refresh"},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALG,
    )
