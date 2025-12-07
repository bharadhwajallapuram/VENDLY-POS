# ===========================================
# Vendly POS - Authentication Tests
# ===========================================

import pytest
from fastapi.testclient import TestClient


class TestAuthEndpoints:
    """Test authentication endpoints"""

    def test_login_with_valid_credentials(self, client: TestClient):
        """Test login with valid admin credentials"""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@vendly.com", "password": "admin123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_with_invalid_password(self, client: TestClient):
        """Test login with wrong password"""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "admin@vendly.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401

    def test_login_with_nonexistent_user(self, client: TestClient):
        """Test login with non-existent email"""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@vendly.com", "password": "password123"},
        )

        assert response.status_code == 401

    def test_me_endpoint_with_valid_token(self, client: TestClient, auth_headers: dict):
        """Test /me endpoint with valid token"""
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@vendly.com"
        assert data["role"] == "admin"

    def test_me_endpoint_without_token(self, client: TestClient):
        """Test /me endpoint without authentication"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401

    def test_me_endpoint_with_invalid_token(self, client: TestClient):
        """Test /me endpoint with invalid token"""
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )

        assert response.status_code == 401
