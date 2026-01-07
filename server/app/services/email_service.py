"""
Email service for sending 2FA codes and notifications
Uses Python's built-in smtplib (open-source)
"""

import logging
import random
import smtplib
import ssl
import string
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails using SMTP (open-source)"""

    @staticmethod
    def _get_settings():
        """Lazy load settings to avoid circular imports"""
        from app.core.config import settings

        return settings

    @staticmethod
    def generate_email_code(length: int = 6) -> str:
        """Generate a random email 2FA code"""
        return "".join(random.choices(string.digits, k=length))

    @staticmethod
    def _create_2fa_email_html(code: str, name: str) -> str:
        """Create HTML email template for 2FA code"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .logo {{ text-align: center; margin-bottom: 20px; }}
                .logo h1 {{ color: #4F46E5; margin: 0; }}
                .code {{ background: #4F46E5; color: white; font-size: 32px; font-weight: bold; text-align: center; padding: 20px; border-radius: 8px; letter-spacing: 8px; margin: 20px 0; }}
                .message {{ color: #666; font-size: 16px; line-height: 1.6; }}
                .footer {{ text-align: center; color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>🛒 {name}</h1>
                </div>
                <p class="message">Your verification code is:</p>
                <div class="code">{code}</div>
                <p class="message">
                    This code will expire in 5 minutes.<br>
                    If you didn't request this code, please ignore this email.
                </p>
                <div class="footer">
                    <p>© 2025 {name}. All rights reserved.</p>
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """

    @staticmethod
    def send_2fa_code(email: str, code: str, name: str = "Vendly POS") -> bool:
        """
        Send 2FA code via email using SMTP

        Args:
            email: Recipient email
            code: 6-digit code
            name: User's name or app name

        Returns:
            True if sent successfully
        """
        settings = EmailService._get_settings()

        # If SMTP is not enabled, log and return success (for dev mode)
        if not settings.SMTP_ENABLED:
            logger.info(f"📧 [DEV MODE] 2FA code for {email}: {code}")
            return True

        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"{name} - Your Verification Code"
            msg["From"] = settings.SMTP_FROM
            msg["To"] = email

            # Plain text version
            text_content = f"""
            Your {name} verification code is: {code}
            
            This code will expire in 5 minutes.
            If you didn't request this code, please ignore this email.
            """

            # HTML version
            html_content = EmailService._create_2fa_email_html(code, name)

            # Attach both versions
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            # Send email
            if settings.SMTP_TLS:
                # Use STARTTLS
                context = ssl.create_default_context()
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    server.starttls(context=context)
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
            else:
                # Use SSL directly (port 465)
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    settings.SMTP_HOST, settings.SMTP_PORT, context=context
                ) as server:
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)

            logger.info(f"📧 2FA code sent successfully to {email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed for {email}: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending to {email}: {e}")
            return False
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
        settings = EmailService._get_settings()

        if not settings.SMTP_ENABLED:
            logger.info(
                f"📧 [DEV MODE] Login notification for {email} from {ip} ({device})"
            )
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Vendly POS - New Login Detected"
            msg["From"] = settings.SMTP_FROM
            msg["To"] = email

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; }}
                    .alert {{ background: #FEF3C7; border-left: 4px solid #F59E0B; padding: 15px; margin: 20px 0; }}
                    .details {{ background: #F3F4F6; padding: 15px; border-radius: 4px; margin: 15px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>🔐 New Login to Your Account</h2>
                    <div class="alert">
                        <strong>A new login was detected on your account.</strong>
                    </div>
                    <div class="details">
                        <p><strong>IP Address:</strong> {ip}</p>
                        <p><strong>Device:</strong> {device}</p>
                        <p><strong>Time:</strong> Just now</p>
                    </div>
                    <p>If this wasn't you, please change your password immediately.</p>
                </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(html_content, "html"))

            if settings.SMTP_TLS:
                context = ssl.create_default_context()
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    server.starttls(context=context)
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
            else:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    settings.SMTP_HOST, settings.SMTP_PORT, context=context
                ) as server:
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)

            logger.info(f"📧 Login notification sent to {email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send login notification to {email}: {e}")
            return False

    @staticmethod
    def send_2fa_disabled_notification(email: str) -> bool:
        """Send notification that 2FA was disabled"""
        settings = EmailService._get_settings()

        if not settings.SMTP_ENABLED:
            logger.info(f"📧 [DEV MODE] 2FA disabled notification for {email}")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Vendly POS - Two-Factor Authentication Disabled"
            msg["From"] = settings.SMTP_FROM
            msg["To"] = email

            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }
                    .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 30px; }
                    .warning { background: #FEE2E2; border-left: 4px solid #EF4444; padding: 15px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h2>⚠️ Two-Factor Authentication Disabled</h2>
                    <div class="warning">
                        <strong>2FA has been disabled on your Vendly POS account.</strong>
                    </div>
                    <p>If you didn't make this change, please contact your administrator immediately.</p>
                    <p>We recommend keeping 2FA enabled for enhanced security.</p>
                </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(html_content, "html"))

            if settings.SMTP_TLS:
                context = ssl.create_default_context()
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    server.starttls(context=context)
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
            else:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    settings.SMTP_HOST, settings.SMTP_PORT, context=context
                ) as server:
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)

            logger.info(f"📧 2FA disabled notification sent to {email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send 2FA disabled notification: {e}")
            return False

    @staticmethod
    def send_custom_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send a custom email

        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body (optional)

        Returns:
            True if sent successfully
        """
        settings = EmailService._get_settings()

        if not settings.SMTP_ENABLED:
            logger.info(f"📧 [DEV MODE] Custom email to {to_email}: {subject}")
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM
            msg["To"] = to_email

            if text_content:
                msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            if settings.SMTP_TLS:
                context = ssl.create_default_context()
                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                    server.starttls(context=context)
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)
            else:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(
                    settings.SMTP_HOST, settings.SMTP_PORT, context=context
                ) as server:
                    if settings.SMTP_USER and settings.SMTP_PASSWORD:
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.send_message(msg)

            logger.info(f"📧 Custom email sent to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send custom email to {to_email}: {e}")
            return False
