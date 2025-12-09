from typing import Optional

from pydantic import BaseModel


class StripePaymentIntentRequest(BaseModel):
    amount: int  # in cents
    currency: Optional[str] = "usd"
    description: Optional[str] = None


class StripePaymentIntentResponse(BaseModel):
    client_secret: str


class UPIPaymentRequest(BaseModel):
    amount: int
    vpa: str
    name: Optional[str] = None
    note: Optional[str] = None


class UPIPaymentResponse(BaseModel):
    upi_url: str
    qr_code_base64: str
