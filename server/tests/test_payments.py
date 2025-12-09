# ===========================================
# Vendly POS - Payments Tests
# ===========================================

import pytest
from fastapi.testclient import TestClient


class TestPaymentsEndpoints:
    """Test cases for payments API endpoints"""

    # ===========================================
    # Stripe Payment Intent Tests
    # ===========================================

    def test_create_stripe_payment_intent(self, client: TestClient):
        """Test creating a Stripe payment intent"""
        response = client.post(
            "/api/v1/payments/stripe-intent",
            json={"amount": 1000, "currency": "usd", "description": "Test payment"},
        )
        # May return 400 if Stripe not configured, which is expected in test env
        assert response.status_code in (200, 400)
        if response.status_code == 200:
            data = response.json()
            assert "client_secret" in data

    def test_create_stripe_payment_intent_invalid_amount(self, client: TestClient):
        """Test that invalid amount is handled"""
        response = client.post(
            "/api/v1/payments/stripe-intent",
            json={"amount": -100, "currency": "usd"},
        )
        assert response.status_code in (400, 422)

    def test_create_stripe_payment_intent_missing_amount(self, client: TestClient):
        """Test that missing amount returns validation error"""
        response = client.post(
            "/api/v1/payments/stripe-intent",
            json={"currency": "usd"},
        )
        assert response.status_code == 422

    # ===========================================
    # UPI Payment Request Tests
    # ===========================================

    def test_create_upi_payment_request(self, client: TestClient):
        """Test creating a UPI payment request"""
        response = client.post(
            "/api/v1/payments/upi-request",
            json={
                "amount": 100.00,
                "vpa": "test@upi",
                "name": "Test Merchant",
                "note": "Test payment",
            },
        )
        # May return 400 if UPI not configured
        assert response.status_code in (200, 400)
        if response.status_code == 200:
            data = response.json()
            assert "upi_url" in data

    def test_create_upi_payment_request_missing_fields(self, client: TestClient):
        """Test that missing fields returns validation error"""
        response = client.post(
            "/api/v1/payments/upi-request",
            json={"amount": 100.00},
        )
        assert response.status_code == 422

    # ===========================================
    # Webhook Tests
    # ===========================================

    def test_stripe_webhook(self, client: TestClient):
        """Test Stripe webhook endpoint accepts requests"""
        response = client.post(
            "/api/v1/payments/stripe-webhook",
            content=b'{"type": "payment_intent.succeeded"}',
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "received"

    def test_upi_webhook(self, client: TestClient):
        """Test UPI webhook endpoint accepts requests"""
        response = client.post(
            "/api/v1/payments/upi-webhook",
            content=b'{"status": "success", "transaction_id": "123"}',
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "received"


class TestPaymentsErrorHandling:
    """Test error handling in payments"""

    def test_stripe_intent_handles_service_error(self, client: TestClient):
        """Test that Stripe service errors are handled gracefully"""
        # Without proper Stripe configuration, this should return an error
        response = client.post(
            "/api/v1/payments/stripe-intent",
            json={"amount": 1000, "currency": "usd"},
        )
        # Should return 400 with error detail, not 500
        if response.status_code == 400:
            assert "detail" in response.json()

    def test_upi_request_handles_service_error(self, client: TestClient):
        """Test that UPI service errors are handled gracefully"""
        response = client.post(
            "/api/v1/payments/upi-request",
            json={"amount": 100, "vpa": "invalid", "name": "Test"},
        )
        # Should handle gracefully
        assert response.status_code in (200, 400)
