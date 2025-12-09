from typing import Optional

from pydantic import BaseModel


class StripePaymentIntentRequest(BaseModel):
    amount: int
    currency: str = "inr"
    description: Optional[str] = None


class StripePaymentIntentResponse(BaseModel):
    client_secret: str


class UPIPaymentRequest(BaseModel):
    amount: int  # in paise (e.g., 10000 = ₹100)
    vpa: str  # UPI ID (e.g., user@upi)
    name: Optional[str] = None
    note: Optional[str] = None


class UPIPaymentResponse(BaseModel):
    upi_url: str
    qr_code_base64: str  # PNG QR code as base64
