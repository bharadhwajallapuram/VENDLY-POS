"""
SMS service for sending 2FA codes via SMS/WhatsApp
"""

import logging
import random
import string
from typing import Literal

logger = logging.getLogger(__name__)

SMSProvider = Literal["twilio", "aws_sns", "nexmo"]


class SMSService:
    """Service for sending SMS messages"""

    @staticmethod
    def generate_sms_code(length: int = 6) -> str:
        """Generate a random SMS 2FA code"""
        return "".join(random.choices(string.digits, k=length))

    @staticmethod
    def send_2fa_code(
        phone: str, code: str, provider: SMSProvider = "twilio"
    ) -> bool:
        """
        Send 2FA code via SMS

        Args:
            phone: Recipient phone number (E.164 format: +1234567890)
            code: 6-digit code
            provider: SMS provider (twilio, aws_sns, nexmo)

        Returns:
            True if sent successfully

        Note:
            In production, integrate with Twilio/AWS SNS/Nexmo
        """
        try:
            # TODO: Implement actual SMS sending
            # For now, just log it
            logger.info(f"📱 Would send 2FA code via {provider} to {phone}: {code}")

            # Example using Twilio (uncomment to use):
            # from twilio.rest import Client
            # from app.core.config import settings
            #
            # if not settings.TWILIO_ENABLED:
            #     return False
            #
            # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            # message = client.messages.create(
            #     body=f"Your Vendly 2FA code is: {code}",
            #     from_=settings.TWILIO_PHONE_NUMBER,
            #     to=phone,
            # )
            # logger.info(f"SMS sent: {message.sid}")
            # return True

            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
            return False

    @staticmethod
    def send_whatsapp_code(phone: str, code: str) -> bool:
        """
        Send 2FA code via WhatsApp

        Args:
            phone: Recipient phone number (E.164 format: +1234567890)
            code: 6-digit code

        Returns:
            True if sent successfully
        """
        try:
            logger.info(f"💬 Would send 2FA code via WhatsApp to {phone}: {code}")

            # Example using Twilio WhatsApp (uncomment to use):
            # from twilio.rest import Client
            # from app.core.config import settings
            #
            # if not settings.TWILIO_ENABLED:
            #     return False
            #
            # client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            # message = client.messages.create(
            #     body=f"Your Vendly 2FA code is: {code}",
            #     from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
            #     to=f"whatsapp:{phone}",
            # )
            # logger.info(f"WhatsApp message sent: {message.sid}")
            # return True

            return True
        except Exception as e:
            logger.error(f"Failed to send WhatsApp to {phone}: {e}")
            return False

    @staticmethod
    def verify_phone_number(phone: str) -> bool:
        """
        Verify that a phone number is valid

        Args:
            phone: Phone number to verify

        Returns:
            True if valid

        Note:
            In production, use libphonenumber or similar
        """
        # Basic validation
        if not phone.startswith("+"):
            return False
        if len(phone) < 10 or len(phone) > 15:
            return False
        if not phone[1:].isdigit():
            return False
        return True
