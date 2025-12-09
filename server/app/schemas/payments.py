from pydantic import BaseModel


class StripePaymentIntentRequest(BaseModel):
    amount: int
    currency: str = "inr"
    description: str = None


class StripePaymentIntentResponse(BaseModel):
    client_secret: str


class UPIPaymentRequest(BaseModel):
    amount: int  # in paise (e.g., 10000 = ₹100)
    vpa: str  # UPI ID (e.g., user@upi)
    name: str = None
    note: str = None


class UPIPaymentResponse(BaseModel):
    upi_url: str
    qr_code_base64: str  # PNG QR code as base64
