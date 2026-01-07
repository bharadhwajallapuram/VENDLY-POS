"""
Payment webhooks and endpoints for Stripe and UPI
"""

import hashlib
import hmac
import json
import logging
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Request

from ....schemas.payments import (
    StripePaymentIntentRequest,
    StripePaymentIntentResponse,
    UPIPaymentRequest,
    UPIPaymentResponse,
)
from ....services.payments import (
    create_stripe_payment_intent,
    create_upi_payment_request,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_settings():
    """Lazy load settings to avoid circular imports"""
    from app.core.config import settings

    return settings


def verify_stripe_signature(
    payload: bytes,
    signature: str,
    webhook_secret: str,
    tolerance: int = 300,
) -> Dict[str, Any]:
    """
    Verify Stripe webhook signature (open-source implementation)

    Args:
        payload: Raw request body
        signature: Stripe-Signature header
        webhook_secret: Webhook endpoint secret (whsec_...)
        tolerance: Max age of event in seconds (default 5 min)

    Returns:
        Parsed event data

    Raises:
        ValueError: If signature is invalid
    """
    if not signature:
        raise ValueError("No signature provided")

    # Parse signature header
    # Format: t=timestamp,v1=signature,v0=signature
    sig_parts = {}
    for part in signature.split(","):
        if "=" in part:
            key, value = part.split("=", 1)
            sig_parts[key] = value

    timestamp = sig_parts.get("t")
    expected_sig = sig_parts.get("v1")

    if not timestamp or not expected_sig:
        raise ValueError("Invalid signature format")

    # Check timestamp tolerance
    try:
        event_time = int(timestamp)
    except ValueError:
        raise ValueError("Invalid timestamp in signature")

    if abs(time.time() - event_time) > tolerance:
        raise ValueError("Signature timestamp outside tolerance")

    # Compute expected signature
    # Stripe uses: HMAC-SHA256(timestamp + "." + payload)
    signed_payload = f"{timestamp}.{payload.decode('utf-8')}"
    computed_sig = hmac.new(
        webhook_secret.encode("utf-8"),
        signed_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    # Constant-time comparison
    if not hmac.compare_digest(computed_sig, expected_sig):
        raise ValueError("Signature verification failed")

    # Parse and return event
    return json.loads(payload)


def verify_upi_signature(
    payload: bytes,
    signature: str,
    secret_key: str,
) -> Dict[str, Any]:
    """
    Verify UPI provider webhook signature

    This is a generic implementation - actual format depends on UPI provider
    (Razorpay, PayTM, PhonePe, etc.)

    Args:
        payload: Raw request body
        signature: Signature header
        secret_key: Webhook secret key

    Returns:
        Parsed event data
    """
    if not signature:
        raise ValueError("No signature provided")

    # Compute HMAC-SHA256 signature
    computed_sig = hmac.new(
        secret_key.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(computed_sig, signature):
        raise ValueError("Signature verification failed")

    return json.loads(payload)


@router.post("/stripe-webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
):
    """
    Handle Stripe webhook events with signature verification

    Supported events:
    - payment_intent.succeeded
    - payment_intent.payment_failed
    - charge.refunded
    - customer.subscription.created
    """
    settings = _get_settings()
    stripe_webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")

    payload = await request.body()

    # If webhook secret is configured, verify signature
    if stripe_webhook_secret:
        try:
            event = verify_stripe_signature(
                payload,
                stripe_signature or "",
                stripe_webhook_secret,
            )
        except ValueError as e:
            logger.warning(f"Stripe webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    else:
        # Dev mode - parse without verification
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        logger.warning(
            "⚠️ Stripe webhook processed without signature verification (dev mode)"
        )

    # Process event
    event_type = event.get("type", "unknown")
    event_data = event.get("data", {}).get("object", {})

    logger.info(f"📥 Stripe webhook received: {event_type}")

    try:
        if event_type == "payment_intent.succeeded":
            payment_intent_id = event_data.get("id")
            amount = event_data.get("amount", 0) / 100  # Convert cents to dollars
            currency = event_data.get("currency", "usd")
            logger.info(
                f"✅ Payment succeeded: {payment_intent_id} - {currency.upper()} {amount}"
            )
            # TODO: Update sale status in database

        elif event_type == "payment_intent.payment_failed":
            payment_intent_id = event_data.get("id")
            error = event_data.get("last_payment_error", {}).get(
                "message", "Unknown error"
            )
            logger.warning(f"❌ Payment failed: {payment_intent_id} - {error}")
            # TODO: Handle failed payment

        elif event_type == "charge.refunded":
            charge_id = event_data.get("id")
            refund_amount = event_data.get("amount_refunded", 0) / 100
            logger.info(f"💸 Refund processed: {charge_id} - ${refund_amount}")
            # TODO: Update refund status

        elif event_type == "customer.subscription.created":
            subscription_id = event_data.get("id")
            customer_id = event_data.get("customer")
            logger.info(f"📋 Subscription created: {subscription_id} for {customer_id}")

        else:
            logger.debug(f"Unhandled Stripe event type: {event_type}")

    except Exception as e:
        logger.error(f"Error processing Stripe webhook: {e}")
        # Still return success to acknowledge receipt

    return {"status": "received", "event_type": event_type}


@router.post("/upi-webhook")
async def upi_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
    x_paytm_signature: Optional[str] = Header(None, alias="X-PayTM-Signature"),
):
    """
    Handle UPI provider webhook events

    Supports multiple providers:
    - Razorpay
    - PayTM
    - Generic UPI callbacks
    """
    settings = _get_settings()
    upi_webhook_secret = getattr(settings, "UPI_WEBHOOK_SECRET", "")

    payload = await request.body()

    # Determine which provider signature to use
    signature = x_razorpay_signature or x_paytm_signature

    # If webhook secret is configured, verify signature
    if upi_webhook_secret and signature:
        try:
            event = verify_upi_signature(payload, signature, upi_webhook_secret)
        except ValueError as e:
            logger.warning(f"UPI webhook signature verification failed: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    else:
        # Dev mode - parse without verification
        try:
            event = json.loads(payload) if payload else {}
        except json.JSONDecodeError:
            event = {}
        if not upi_webhook_secret:
            logger.warning(
                "⚠️ UPI webhook processed without signature verification (dev mode)"
            )

    # Process event
    event_type = event.get("event", event.get("type", "unknown"))
    payment_data = event.get("payload", {}).get("payment", {}).get("entity", event)

    logger.info(f"📥 UPI webhook received: {event_type}")

    try:
        if event_type in ["payment.captured", "payment_success"]:
            payment_id = payment_data.get("id", payment_data.get("payment_id"))
            amount = payment_data.get("amount", 0)
            if isinstance(amount, int) and amount > 100:
                amount = amount / 100  # Razorpay sends paise
            vpa = payment_data.get("vpa", payment_data.get("upi_id"))
            logger.info(f"✅ UPI Payment captured: {payment_id} - ₹{amount} from {vpa}")
            # TODO: Update sale status in database

        elif event_type in ["payment.failed", "payment_failure"]:
            payment_id = payment_data.get("id", payment_data.get("payment_id"))
            error = payment_data.get("error_description", "Unknown error")
            logger.warning(f"❌ UPI Payment failed: {payment_id} - {error}")
            # TODO: Handle failed payment

        elif event_type in ["refund.processed", "refund_success"]:
            refund_id = payment_data.get("id", payment_data.get("refund_id"))
            amount = payment_data.get("amount", 0)
            if isinstance(amount, int) and amount > 100:
                amount = amount / 100
            logger.info(f"💸 UPI Refund processed: {refund_id} - ₹{amount}")

        else:
            logger.debug(f"Unhandled UPI event type: {event_type}")

    except Exception as e:
        logger.error(f"Error processing UPI webhook: {e}")

    return {"status": "received", "event_type": event_type}


@router.post("/stripe-intent", response_model=StripePaymentIntentResponse)
def stripe_payment_intent(req: StripePaymentIntentRequest):
    """Create a Stripe Payment Intent"""
    try:
        client_secret = create_stripe_payment_intent(
            req.amount, req.currency, req.description
        )
        return StripePaymentIntentResponse(client_secret=client_secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/upi-request", response_model=UPIPaymentResponse)
def upi_payment_request(req: UPIPaymentRequest):
    """Create a UPI payment request with QR code"""
    try:
        upi_url, qr_code_base64 = create_upi_payment_request(
            req.amount, req.vpa, req.name, req.note
        )
        return UPIPaymentResponse(upi_url=upi_url, qr_code_base64=qr_code_base64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
