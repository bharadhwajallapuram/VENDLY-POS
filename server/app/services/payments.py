from typing import Optional

import stripe

from app.core.config import settings


def create_stripe_payment_intent(
    amount: int, currency: str = "inr", description: Optional[str] = None
) -> str:
    stripe.api_key = settings.STRIPE_SECRET_KEY
    if not stripe.api_key:
        raise ValueError("Stripe secret key is not configured")

    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency=currency,
        description=description or "",
        payment_method_types=["card"],
    )
    client_secret = intent.client_secret
    if client_secret is None:
        raise ValueError("Failed to create payment intent - no client secret returned")
    return client_secret


import base64
from io import BytesIO

# --- UPI Payment (Demo/Placeholder) ---
import qrcode


def create_upi_payment_request(
    amount: int, vpa: str, name: Optional[str] = None, note: Optional[str] = None
) -> tuple[str, str]:
    # UPI deep link format
    upi_url = f"upi://pay?pa={vpa}&pn={name or 'Vendly'}&am={amount/100:.2f}&cu=INR&tn={note or 'Vendly POS'}"
    # Generate QR code as base64
    qr = qrcode.QRCode(box_size=10, border=2)
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    qr_code_base64 = base64.b64encode(buffered.getvalue()).decode()
    return upi_url, qr_code_base64
