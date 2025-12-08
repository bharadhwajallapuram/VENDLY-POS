
from fastapi import APIRouter, HTTPException, Request
from ....services.payments import create_stripe_payment_intent, create_upi_payment_request
from ....schemas.payments import StripePaymentIntentRequest, StripePaymentIntentResponse, UPIPaymentRequest, UPIPaymentResponse

router = APIRouter()
@router.post("/stripe-webhook")
async def stripe_webhook(request: Request):
    # TODO: Validate and process Stripe webhook events
    payload = await request.body()
    # signature = request.headers.get("stripe-signature")
    # Process event here (e.g., payment_intent.succeeded)
    return {"status": "received"}

@router.post("/upi-webhook")
async def upi_webhook(request: Request):
    # TODO: Validate and process UPI provider webhook events
    payload = await request.body()
    # Process event here (e.g., payment success notification)
    return {"status": "received"}

@router.post("/stripe-intent", response_model=StripePaymentIntentResponse)
def stripe_payment_intent(req: StripePaymentIntentRequest):
    try:
        client_secret = create_stripe_payment_intent(req.amount, req.currency, req.description)
        return StripePaymentIntentResponse(client_secret=client_secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upi-request", response_model=UPIPaymentResponse)
def upi_payment_request(req: UPIPaymentRequest):
    try:
        upi_url, qr_code_base64 = create_upi_payment_request(req.amount, req.vpa, req.name, req.note)
        return UPIPaymentResponse(upi_url=upi_url, qr_code_base64=qr_code_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
