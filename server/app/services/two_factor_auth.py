"""
Vendly POS - Two-Factor Authentication Service
Implements TOTP-based 2FA for admin and sensitive roles
"""

import base64
import io
import logging
from datetime import UTC, datetime, timedelta
from typing import Optional

import pyotp
import qrcode
from sqlalchemy.orm import Session

from app.db import models as m

logger = logging.getLogger(__name__)


class TwoFactorAuthService:
    """Service for managing 2FA (TOTP) authentication"""

    @staticmethod
    def generate_secret() -> str:
        """Generate a new TOTP secret"""
        return pyotp.random_base32()

    @staticmethod
    def get_totp(secret: str) -> pyotp.TOTP:
        """Get TOTP object from secret"""
        return pyotp.TOTP(secret)

    @staticmethod
    def verify_token(secret: str, token: str) -> bool:
        """
        Verify a TOTP token

        Args:
            secret: The TOTP secret
            token: The 6-digit token from authenticator app

        Returns:
            True if token is valid, False otherwise
        """
        from app.core.config import settings

        try:
            # Allow for time drift (configurable window, default ±30 seconds)
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=settings.TWO_FACTOR_TOTP_WINDOW)
        except Exception as e:
            logger.error(f"2FA verification failed: {e}")
            return False

    @staticmethod
    def get_qr_code(secret: str, email: str, issuer: str = "Vendly POS") -> str:
        """
        Generate QR code for TOTP setup

        Args:
            secret: The TOTP secret
            email: User's email
            issuer: Application name (appears in authenticator app)

        Returns:
            Base64-encoded PNG image of QR code
        """
        try:
            totp = pyotp.TOTP(secret)
            provisioning_uri = totp.provisioning_uri(name=email, issuer_name=issuer)

            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(provisioning_uri)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()

            return f"data:image/png;base64,{img_str}"
        except Exception as e:
            logger.error(f"QR code generation failed: {e}")
            raise

    @staticmethod
    def get_backup_codes(count: int | None = None) -> list[str]:
        """
        Generate backup codes for account recovery

        Args:
            count: Number of backup codes to generate (uses config default if None)

        Returns:
            List of backup codes
        """
        import secrets

        from app.core.config import settings

        if count is None:
            count = settings.TWO_FACTOR_BACKUP_CODES

        codes = []
        for _ in range(count):
            # Format: XXXX-XXXX-XXXX (12 chars total)
            code = "-".join(secrets.token_hex(2).upper() for _ in range(3))
            codes.append(code)
        return codes


class TwoFactorAuthDB:
    """Database operations for 2FA"""

    @staticmethod
    def enable_2fa(
        db: Session, user_id: int, secret: str, backup_codes: list[str]
    ) -> m.TwoFactorAuth:
        """Enable 2FA for a user"""
        # Check if 2FA already exists
        existing = (
            db.query(m.TwoFactorAuth).filter(m.TwoFactorAuth.user_id == user_id).first()
        )

        if existing:
            existing.secret = secret
            existing.backup_codes = ",".join(backup_codes)
            existing.is_enabled = False  # Not enabled until verified
            existing.enabled_at = None
        else:
            existing = m.TwoFactorAuth(
                user_id=user_id,
                secret=secret,
                backup_codes=",".join(backup_codes),
                is_enabled=False,  # Not enabled until verified
            )
            db.add(existing)

        db.commit()
        return existing

    @staticmethod
    def verify_and_enable_2fa(db: Session, user_id: int, token: str) -> bool:
        """
        Verify 2FA setup with a token and enable it

        Returns:
            True if successfully enabled, False if verification failed
        """
        tfa = (
            db.query(m.TwoFactorAuth).filter(m.TwoFactorAuth.user_id == user_id).first()
        )

        if not tfa:
            return False

        # Verify the token
        if not TwoFactorAuthService.verify_token(tfa.secret, token):
            return False

        # Enable 2FA
        tfa.is_enabled = True
        tfa.enabled_at = datetime.now(UTC)
        db.commit()

        logger.info(f"2FA enabled for user {user_id}")
        return True

    @staticmethod
    def disable_2fa(db: Session, user_id: int) -> bool:
        """Disable 2FA for a user"""
        tfa = (
            db.query(m.TwoFactorAuth).filter(m.TwoFactorAuth.user_id == user_id).first()
        )

        if not tfa:
            return False

        tfa.is_enabled = False
        tfa.disabled_at = datetime.now(UTC)
        db.commit()

        logger.info(f"2FA disabled for user {user_id}")
        return True

    @staticmethod
    def get_2fa(db: Session, user_id: int) -> Optional[m.TwoFactorAuth]:
        """Get 2FA config for a user"""
        return (
            db.query(m.TwoFactorAuth).filter(m.TwoFactorAuth.user_id == user_id).first()
        )

    @staticmethod
    def use_backup_code(db: Session, user_id: int, code: str) -> bool:
        """
        Use a backup code for login (one-time use)

        Returns:
            True if code was valid and unused, False otherwise
        """
        tfa = (
            db.query(m.TwoFactorAuth)
            .filter(
                m.TwoFactorAuth.user_id == user_id, m.TwoFactorAuth.is_enabled == True
            )
            .first()
        )

        if not tfa:
            return False

        codes = [c.strip() for c in tfa.backup_codes.split(",")]

        if code not in codes:
            return False

        # Remove used code
        codes.remove(code)
        tfa.backup_codes = ",".join(codes)
        db.commit()

        logger.info(f"Backup code used for user {user_id}")
        return True

    @staticmethod
    def regenerate_backup_codes(db: Session, user_id: int) -> list[str]:
        """Generate new backup codes for a user"""
        tfa = (
            db.query(m.TwoFactorAuth).filter(m.TwoFactorAuth.user_id == user_id).first()
        )

        if not tfa:
            return []

        new_codes = TwoFactorAuthService.get_backup_codes()
        tfa.backup_codes = ",".join(new_codes)
        db.commit()

        return new_codes
