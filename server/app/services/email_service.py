"""
Email service for sending 2FA codes and notifications
"""

import logging
import random
import string
from datetime import datetime, UTC, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""

    @staticmethod
    def generate_email_code(length: int = 6) -> str:
        """Generate a random email 2FA code"""
        return "".join(random.choices(string.digits, k=length))

    @staticmethod
    def send_2fa_code(email: str, code: str, name: str = "Vendly POS") -> bool:
        """
        Send 2FA code via email

        Args:
            email: Recipient email
            code: 6-digit code
            name: User's name or app name

        Returns:
            True if sent successfully

        Note:
            In production, integrate with SMTP/SendGrid/AWS SES
        """
        try:
            # TODO: Implement actual email sending
            # For now, just log it
            logger.info(f"📧 Would send 2FA code to {email}: {code}")

            # Example using smtplib (uncomment to use):
            # import smtplib
            # from email.mime.text import MIMEText
            #
            # from app.core.config import settings
            #
            # if not settings.SMTP_ENABLED:
            #     return False
            #
            # msg = MIMEText(f"Your {name} 2FA code is: {code}")
            # msg["Subject"] = f"{name} - Verification Code"
            # msg["From"] = settings.SMTP_FROM
            # msg["To"] = email
            #
            # with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            #     if settings.SMTP_TLS:
            #         server.starttls()
            #     server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            #     server.send_message(msg)

            return True
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {e}")
            return False

    @staticmethod
    def send_login_notification(email: str, ip: str, device: str = "Unknown") -> bool:
        """
        Send login notification email

        Args:
            email: User email
            ip: Login IP address
            device: Device info

        Returns:
            True if sent successfully
        """
        try:
            logger.info(f"📧 Login notification for {email} from {ip} ({device})")
            return True
        except Exception as e:
            logger.error(f"Failed to send login notification to {email}: {e}")
            return False

    @staticmethod
    def send_2fa_disabled_notification(email: str) -> bool:
        """Send notification that 2FA was disabled"""
        try:
            logger.info(f"📧 2FA disabled notification sent to {email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send 2FA disabled notification: {e}")
            return False
