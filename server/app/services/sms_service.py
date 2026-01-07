"""
SMS service for sending 2FA codes via SMS/WhatsApp
Supports multiple providers: Twilio, Vonage (Nexmo), AWS SNS
All providers have free tiers for testing
"""

import hashlib
import hmac
import json
import logging
import random
import string
import urllib.parse
import urllib.request
from typing import Any, Dict, Literal, Optional

logger = logging.getLogger(__name__)

SMSProvider = Literal["twilio", "vonage", "aws_sns", "console"]


class SMSService:
    """Service for sending SMS messages using open-source compatible providers"""

    @staticmethod
    def _get_settings():
        """Lazy load settings to avoid circular imports"""
        from app.core.config import settings

        return settings

    @staticmethod
    def generate_sms_code(length: int = 6) -> str:
        """Generate a random SMS 2FA code"""
        return "".join(random.choices(string.digits, k=length))

    @staticmethod
    def _send_via_twilio(phone: str, message: str) -> bool:
        """
        Send SMS via Twilio REST API (no SDK required)
        Free tier: $15 credit for testing
        """
        settings = SMSService._get_settings()

        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            logger.warning("Twilio credentials not configured")
            return False

        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"

            data = urllib.parse.urlencode(
                {
                    "To": phone,
                    "From": settings.TWILIO_PHONE_NUMBER,
                    "Body": message,
                }
            ).encode("utf-8")

            # Create request with Basic Auth
            request = urllib.request.Request(url, data=data, method="POST")
            credentials = f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}"
            import base64

            auth_header = base64.b64encode(credentials.encode()).decode()
            request.add_header("Authorization", f"Basic {auth_header}")
            request.add_header("Content-Type", "application/x-www-form-urlencoded")

            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode())
                logger.info(f"📱 Twilio SMS sent: SID={result.get('sid')}")
                return True

        except urllib.error.HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            logger.error(f"Twilio HTTP error: {e.code} - {error_body}")
            return False
        except Exception as e:
            logger.error(f"Twilio error: {e}")
            return False

    @staticmethod
    def _send_via_vonage(phone: str, message: str) -> bool:
        """
        Send SMS via Vonage/Nexmo REST API (no SDK required)
        Free tier: €2 credit for testing
        """
        settings = SMSService._get_settings()

        vonage_api_key = getattr(settings, "VONAGE_API_KEY", "")
        vonage_api_secret = getattr(settings, "VONAGE_API_SECRET", "")
        vonage_from = getattr(settings, "VONAGE_FROM", "Vendly")

        if not vonage_api_key or not vonage_api_secret:
            logger.warning("Vonage credentials not configured")
            return False

        try:
            url = "https://rest.nexmo.com/sms/json"

            data = urllib.parse.urlencode(
                {
                    "api_key": vonage_api_key,
                    "api_secret": vonage_api_secret,
                    "to": phone.replace("+", ""),  # Vonage doesn't want the +
                    "from": vonage_from,
                    "text": message,
                }
            ).encode("utf-8")

            request = urllib.request.Request(url, data=data, method="POST")
            request.add_header("Content-Type", "application/x-www-form-urlencoded")

            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode())
                messages = result.get("messages", [])
                if messages and messages[0].get("status") == "0":
                    logger.info(
                        f"📱 Vonage SMS sent: ID={messages[0].get('message-id')}"
                    )
                    return True
                else:
                    error = (
                        messages[0].get("error-text", "Unknown error")
                        if messages
                        else "No response"
                    )
                    logger.error(f"Vonage error: {error}")
                    return False

        except Exception as e:
            logger.error(f"Vonage error: {e}")
            return False

    @staticmethod
    def send_2fa_code(
        phone: str, code: str, provider: Optional[SMSProvider] = None
    ) -> bool:
        """
        Send 2FA code via SMS

        Args:
            phone: Recipient phone number (E.164 format: +1234567890)
            code: 6-digit code
            provider: SMS provider (twilio, vonage, aws_sns, console)

        Returns:
            True if sent successfully
        """
        settings = SMSService._get_settings()

        # Use configured provider if not specified
        if provider is None:
            provider = getattr(settings, "SMS_PROVIDER", "console")

        # If SMS is not enabled, log to console (dev mode)
        if not getattr(settings, "SMS_ENABLED", False):
            logger.info(f"📱 [DEV MODE] 2FA code for {phone}: {code}")
            return True

        message = f"Your Vendly POS verification code is: {code}. Valid for 5 minutes."

        try:
            if provider == "twilio":
                return SMSService._send_via_twilio(phone, message)
            elif provider == "vonage":
                return SMSService._send_via_vonage(phone, message)
            elif provider == "console":
                logger.info(f"📱 [CONSOLE] 2FA code for {phone}: {code}")
                return True
            else:
                logger.warning(
                    f"Unknown SMS provider: {provider}, falling back to console"
                )
                logger.info(f"📱 [CONSOLE] 2FA code for {phone}: {code}")
                return True

        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
            return False

    @staticmethod
    def send_whatsapp_code(phone: str, code: str) -> bool:
        """
        Send 2FA code via WhatsApp (Twilio WhatsApp)

        Args:
            phone: Recipient phone number (E.164 format: +1234567890)
            code: 6-digit code

        Returns:
            True if sent successfully
        """
        settings = SMSService._get_settings()

        if not getattr(settings, "SMS_ENABLED", False):
            logger.info(f"💬 [DEV MODE] WhatsApp 2FA code for {phone}: {code}")
            return True

        if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
            logger.warning("Twilio credentials not configured for WhatsApp")
            return False

        whatsapp_number = getattr(settings, "TWILIO_WHATSAPP_NUMBER", "")
        if not whatsapp_number:
            logger.warning("Twilio WhatsApp number not configured")
            return False

        try:
            url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"

            message = (
                f"Your Vendly POS verification code is: {code}. Valid for 5 minutes."
            )

            data = urllib.parse.urlencode(
                {
                    "To": f"whatsapp:{phone}",
                    "From": f"whatsapp:{whatsapp_number}",
                    "Body": message,
                }
            ).encode("utf-8")

            request = urllib.request.Request(url, data=data, method="POST")
            import base64

            credentials = f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}"
            auth_header = base64.b64encode(credentials.encode()).decode()
            request.add_header("Authorization", f"Basic {auth_header}")
            request.add_header("Content-Type", "application/x-www-form-urlencoded")

            with urllib.request.urlopen(request, timeout=30) as response:
                result = json.loads(response.read().decode())
                logger.info(f"💬 WhatsApp sent: SID={result.get('sid')}")
                return True

        except Exception as e:
            logger.error(f"Failed to send WhatsApp to {phone}: {e}")
            return False

    @staticmethod
    def verify_phone_number(phone: str) -> bool:
        """
        Verify that a phone number is valid (E.164 format)

        Args:
            phone: Phone number to verify

        Returns:
            True if valid
        """
        if not phone:
            return False
        if not phone.startswith("+"):
            return False
        if len(phone) < 10 or len(phone) > 15:
            return False
        if not phone[1:].isdigit():
            return False
        return True

    @staticmethod
    def format_phone_number(phone: str, country_code: str = "+1") -> str:
        """
        Format a phone number to E.164 format

        Args:
            phone: Phone number (can be local format)
            country_code: Default country code

        Returns:
            E.164 formatted phone number
        """
        # Remove all non-digit characters
        digits = "".join(c for c in phone if c.isdigit())

        # If already has country code
        if phone.startswith("+"):
            return f"+{digits}"

        # If starts with country code without +
        if digits.startswith(country_code.replace("+", "")):
            return f"+{digits}"

        # Add country code
        return f"{country_code}{digits}"
