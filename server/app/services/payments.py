import os
import stripe

def create_stripe_payment_intent(amount: int, currency: str = "usd", description: str = None) -> str:
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...replace_me...")
    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency=currency,
        description=description,
        payment_method_types=["card"],
    )
    return intent.client_secret


# --- UPI Payment (Demo/Placeholder) ---
import qrcode
import base64
from io import BytesIO

def create_upi_payment_request(amount: int, vpa: str, name: str = None, note: str = None):
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
