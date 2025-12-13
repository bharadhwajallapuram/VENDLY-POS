import json
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.v1.schemas.auth import (
    LoginIn,
    TokenOut,
    TwoFactorRequiredResponse,
    TwoFactorVerifyLoginIn,
    UserOut,
)
from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.redis_client import get_token_store
from app.db import models as m
from app.services.audit import log_login_failed, log_login_success
from app.services.auth import authenticate, create_access_token
from app.services.rate_limit import get_client_ip, rate_limit
from app.services.two_factor_auth import TwoFactorAuthDB, TwoFactorAuthService

router = APIRouter()

# Get token store (Redis or in-memory fallback)
token_store = get_token_store()


@router.post("/login")
async def login(
    request: Request,
    payload: LoginIn,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit("5/minute")),  # 5 attempts per minute per IP
):
    """Login endpoint - returns token or 2FA requirement"""
    ip = get_client_ip(request)
    result = await authenticate(db, payload.email, payload.password)

    if not result:
        log_login_failed(payload.email, ip=ip)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user_id = result["user_id"]

    # Check if user has 2FA enabled
    tfa = TwoFactorAuthDB.get_2fa(db, user_id)

    if tfa and tfa.is_enabled:
        # Generate temporary token for 2FA verification (5 minute expiry)
        temp_token = secrets.token_urlsafe(32)
        token_store.set(
            f"2fa_temp:{temp_token}",
            {"user_id": user_id},
            ttl=300,  # 5 minutes
        )

        # Get user email for response
        user = db.query(m.User).filter(m.User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return TwoFactorRequiredResponse(
            requires_2fa=True,
            user_id=user_id,
            email=user.email,
            temp_token=temp_token,
        )

    # No 2FA required, return access token
    log_login_success(user_id, payload.email, ip=ip)
    return result


@router.post("/verify-2fa", response_model=TokenOut)
async def verify_2fa_login(
    request: Request,
    payload: TwoFactorVerifyLoginIn,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit("5/minute")),  # Rate limit 2FA attempts
):
    """Verify 2FA code during login and return access token"""
    ip = get_client_ip(request)

    # Validate temporary token from Redis
    temp_data = token_store.get(f"2fa_temp:{payload.temp_token}")
    if not temp_data:
        raise HTTPException(status_code=401, detail="Invalid or expired 2FA session")

    user_id = temp_data["user_id"]
    user = db.query(m.User).filter(m.User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get 2FA config
    tfa = TwoFactorAuthDB.get_2fa(db, user_id)
    if not tfa or not tfa.is_enabled:
        raise HTTPException(status_code=400, detail="2FA not enabled for this user")

    # Try TOTP code first
    if payload.token and len(payload.token) == 6:
        if TwoFactorAuthService.verify_token(tfa.secret, payload.token):
            # Valid TOTP code
            token_store.delete(f"2fa_temp:{payload.temp_token}")
            log_login_success(user_id, user.email, ip=ip)

            # Generate access token
            access_token = create_access_token(data={"sub": str(user_id)})
            return TokenOut(
                access_token=access_token,
                refresh_token="",
                token_type="bearer",
                expires_in=int(settings.ACCESS_TTL_MIN * 60),
            )

    # Try backup code
    if payload.backup_code:
        success = TwoFactorAuthDB.use_backup_code(db, user_id, payload.backup_code)
        if success:
            token_store.delete(f"2fa_temp:{payload.temp_token}")
            log_login_success(user_id, user.email, ip=ip)

            access_token = create_access_token(data={"sub": str(user_id)})
            return TokenOut(
                access_token=access_token,
                refresh_token="",
                token_type="bearer",
                expires_in=int(settings.ACCESS_TTL_MIN * 60),
            )

    log_login_failed(user.email, ip=ip)
    raise HTTPException(status_code=401, detail="Invalid 2FA code or backup code")


# Public registration disabled - users are created by admin only via /api/v1/users


@router.get("/me", response_model=UserOut)
async def me(user=Depends(get_current_user)):
    return UserOut(
        id=user.id, email=user.email, full_name=user.full_name, role=user.role
    )
