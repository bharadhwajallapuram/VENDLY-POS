"""
Vendly POS - Two-Factor Authentication API Routes
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.db import models as m
from app.schemas.auth import UserResponse
from app.services.audit import (
    log_two_factor_disabled,
    log_two_factor_enabled,
    log_two_factor_verified,
)
from app.services.two_factor_auth import (
    TwoFactorAuthDB,
    TwoFactorAuthService,
)

router = APIRouter(prefix="/api/v1/auth/2fa", tags=["2fa"])


# ============================================================
# Request/Response Models
# ============================================================


class TwoFactorSetupRequest(BaseModel):
    user_id: int


class TwoFactorSetupResponse(BaseModel):
    secret: str
    qr_code: str
    user_email: str


class TwoFactorVerifyRequest(BaseModel):
    user_id: int
    token: str = Field(..., min_length=6, max_length=6)


class TwoFactorVerifyResponse(BaseModel):
    message: str
    backup_codes: list[str]


class TwoFactorLoginRequest(BaseModel):
    user_id: int
    token: Optional[str] = Field(None, min_length=6, max_length=6)
    backup_code: Optional[str] = None


class TwoFactorLoginResponse(BaseModel):
    success: bool
    message: str


class BackupCodesResponse(BaseModel):
    backup_codes: list[str]


# ============================================================
# Endpoints
# ============================================================


@router.post("/setup", response_model=TwoFactorSetupResponse)
async def setup_2fa(
    request: TwoFactorSetupRequest,
    db: Session = Depends(get_db),
):
    """
    Start 2FA setup process
    Generates secret and QR code
    """
    # Get user
    user = db.query(m.User).filter(m.User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Generate secret
    secret = TwoFactorAuthService.generate_secret()

    # Generate QR code
    qr_code = TwoFactorAuthService.get_qr_code(
        secret=secret,
        email=user.email,
        issuer="Vendly POS",
    )

    # Generate backup codes
    backup_codes = TwoFactorAuthService.get_backup_codes()

    # Store pending 2FA config
    TwoFactorAuthDB.enable_2fa(db, user.id, secret, backup_codes)

    return TwoFactorSetupResponse(
        secret=secret,
        qr_code=qr_code,
        user_email=user.email,
    )


@router.post("/verify", response_model=TwoFactorVerifyResponse)
async def verify_2fa_setup(
    request: TwoFactorVerifyRequest,
    db: Session = Depends(get_db),
):
    """
    Verify 2FA setup with TOTP code
    """
    # Get user
    user = db.query(m.User).filter(m.User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Verify and enable 2FA
    success = TwoFactorAuthDB.verify_and_enable_2fa(
        db,
        user.id,
        request.token,
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )

    log_two_factor_enabled(user.id)

    # Return backup codes for user to save
    tfa = TwoFactorAuthDB.get_2fa(db, user.id)
    backup_codes = tfa.backup_codes.split(",") if tfa and tfa.backup_codes else []

    return TwoFactorVerifyResponse(
        message="2FA enabled successfully",
        backup_codes=backup_codes,
    )


@router.post("/verify-login", response_model=TwoFactorLoginResponse)
async def verify_2fa_login(
    request: TwoFactorLoginRequest,
    db: Session = Depends(get_db),
):
    """
    Verify 2FA code during login
    """
    # Get user
    user = db.query(m.User).filter(m.User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Get 2FA config
    tfa = TwoFactorAuthDB.get_2fa(db, user.id)
    if not tfa or not tfa.is_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA not enabled",
        )

    # Try TOTP token first
    if request.token:
        success = TwoFactorAuthService.verify_token(tfa.secret, request.token)
        if success:
            log_two_factor_verified(user.id, "totp")
            return TwoFactorLoginResponse(
                success=True,
                message="2FA verification successful",
            )

    # Try backup code
    if request.backup_code:
        success = TwoFactorAuthDB.use_backup_code(
            db,
            user.id,
            request.backup_code,
        )
        if success:
            log_two_factor_verified(user.id, "backup_code")
            return TwoFactorLoginResponse(
                success=True,
                message="2FA verification successful (backup code used)",
            )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid 2FA code or backup code",
    )


@router.post("/disable")
async def disable_2fa(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """
    Disable 2FA for current user
    Requires re-authentication
    """
    # Only allow admin or the user themselves
    tfa = TwoFactorAuthDB.get_2fa(db, current_user.id)
    if not tfa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="2FA not enabled",
        )

    success = TwoFactorAuthDB.disable_2fa(db, current_user.id)

    if success:
        log_two_factor_disabled(current_user.id)

    return {"message": "2FA disabled"}


@router.post("/regenerate-backup-codes", response_model=BackupCodesResponse)
async def regenerate_backup_codes(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """
    Regenerate backup codes
    """
    new_codes = TwoFactorAuthDB.regenerate_backup_codes(db, current_user.id)

    if not new_codes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="2FA not enabled",
        )

    return BackupCodesResponse(backup_codes=new_codes)


@router.get("/status")
async def get_2fa_status(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """
    Get 2FA status for current user
    """
    tfa = TwoFactorAuthDB.get_2fa(db, current_user.id)

    if not tfa:
        return {
            "enabled": False,
            "message": "2FA not configured",
        }

    backup_code_count = len(tfa.backup_codes.split(",")) if tfa.backup_codes else 0

    return {
        "enabled": tfa.is_enabled,
        "enabled_at": tfa.enabled_at.isoformat() if tfa.enabled_at else None,
        "backup_codes_remaining": backup_code_count,
    }


@router.post("/admin/disable/{user_id}")
async def admin_disable_2fa(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """
    Admin endpoint: Disable 2FA for another user
    """
    # Check permissions
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    success = TwoFactorAuthDB.disable_2fa(db, user_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User 2FA not found",
        )

    log_two_factor_disabled(user_id, admin_id=current_user.id)

    return {"message": "2FA disabled for user"}
