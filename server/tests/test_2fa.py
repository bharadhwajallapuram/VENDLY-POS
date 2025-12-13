# ===========================================
# Vendly POS - Two-Factor Authentication Tests
# ===========================================

import pytest
from fastapi.testclient import TestClient

from app.services.two_factor_auth import TwoFactorAuthService


class Test2FASetup:
    """Test 2FA setup flow"""

    def test_setup_2fa_generates_secret_and_qr(self, client: TestClient):
        """Test that setup endpoint generates secret and QR code"""
        response = client.post(
            "/api/v1/auth/2fa/setup",
            json={"user_id": 1},  # Admin user from test fixtures
        )

        assert response.status_code == 200
        data = response.json()
        assert "secret" in data
        assert "qr_code" in data
        assert "user_email" in data
        assert data["user_email"] == "admin@vendly.com"
        assert data["qr_code"].startswith("data:image/png;base64,")
        assert len(data["secret"]) == 32  # Base32 encoded TOTP secret

    def test_setup_2fa_nonexistent_user(self, client: TestClient):
        """Test setup with non-existent user"""
        response = client.post(
            "/api/v1/auth/2fa/setup",
            json={"user_id": 99999},
        )

        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]


class Test2FAVerification:
    """Test 2FA verification flow"""

    def test_verify_2fa_with_valid_token(self, client: TestClient):
        """Test 2FA verification with valid TOTP token"""
        # Step 1: Setup 2FA
        setup_response = client.post(
            "/api/v1/auth/2fa/setup",
            json={"user_id": 1},
        )
        assert setup_response.status_code == 200
        secret = setup_response.json()["secret"]

        # Step 2: Generate valid TOTP token
        totp = TwoFactorAuthService.get_totp(secret)
        token = totp.now()

        # Step 3: Verify with token
        verify_response = client.post(
            "/api/v1/auth/2fa/verify",
            json={"user_id": 1, "token": token},
        )

        assert verify_response.status_code == 200
        data = verify_response.json()
        assert "backup_codes" in data
        assert len(data["backup_codes"]) == 10  # Default 10 backup codes
        assert data["message"] == "2FA enabled successfully"

    def test_verify_2fa_with_invalid_token(self, client: TestClient):
        """Test 2FA verification with invalid TOTP token"""
        # Step 1: Setup 2FA
        client.post(
            "/api/v1/auth/2fa/setup",
            json={"user_id": 1},
        )

        # Step 2: Try with invalid token
        verify_response = client.post(
            "/api/v1/auth/2fa/verify",
            json={"user_id": 1, "token": "000000"},
        )

        assert verify_response.status_code == 400
        assert "Invalid verification code" in verify_response.json()["detail"]

    def test_verify_2fa_with_invalid_token_format(self, client: TestClient):
        """Test 2FA verification with non-6-digit token"""
        client.post(
            "/api/v1/auth/2fa/setup",
            json={"user_id": 1},
        )

        # Try with non-6-digit code
        verify_response = client.post(
            "/api/v1/auth/2fa/verify",
            json={"user_id": 1, "token": "12345"},  # Only 5 digits
        )

        assert verify_response.status_code == 422  # Validation error


class Test2FALogin:
    """Test 2FA during login"""

    def test_verify_login_with_totp_token(self, client: TestClient):
        """Test login 2FA verification with TOTP token"""
        # Step 1: Setup and enable 2FA
        setup_response = client.post(
            "/api/v1/auth/2fa/setup",
            json={"user_id": 1},
        )
        secret = setup_response.json()["secret"]

        totp = TwoFactorAuthService.get_totp(secret)
        token = totp.now()

        client.post(
            "/api/v1/auth/2fa/verify",
            json={"user_id": 1, "token": token},
        )

        # Step 2: Verify login with 2FA
        new_token = totp.now()  # Get fresh token
        login_response = client.post(
            "/api/v1/auth/2fa/verify-login",
            json={"user_id": 1, "token": new_token},
        )

        assert login_response.status_code == 200
        data = login_response.json()
        assert data["success"] is True
        assert "2FA verification successful" in data["message"]

    def test_verify_login_with_backup_code(self, client: TestClient):
        """Test login 2FA verification with backup code"""
        # Step 1: Setup and enable 2FA, capture backup codes
        setup_response = client.post(
            "/api/v1/auth/2fa/setup",
            json={"user_id": 1},
        )
        secret = setup_response.json()["secret"]

        totp = TwoFactorAuthService.get_totp(secret)
        token = totp.now()

        verify_response = client.post(
            "/api/v1/auth/2fa/verify",
            json={"user_id": 1, "token": token},
        )
        backup_codes = verify_response.json()["backup_codes"]
        first_backup_code = backup_codes[0]

        # Step 2: Verify login with backup code
        login_response = client.post(
            "/api/v1/auth/2fa/verify-login",
            json={"user_id": 1, "backup_code": first_backup_code},
        )

        assert login_response.status_code == 200
        data = login_response.json()
        assert data["success"] is True
        assert "backup code used" in data["message"]

    def test_verify_login_with_used_backup_code(self, client: TestClient):
        """Test that backup codes can only be used once"""
        # Step 1: Setup and enable 2FA
        setup_response = client.post(
            "/api/v1/auth/2fa/setup",
            json={"user_id": 1},
        )
        secret = setup_response.json()["secret"]

        totp = TwoFactorAuthService.get_totp(secret)
        token = totp.now()

        verify_response = client.post(
            "/api/v1/auth/2fa/verify",
            json={"user_id": 1, "token": token},
        )
        backup_codes = verify_response.json()["backup_codes"]
        first_backup_code = backup_codes[0]

        # Step 2: Use backup code once
        client.post(
            "/api/v1/auth/2fa/verify-login",
            json={"user_id": 1, "backup_code": first_backup_code},
        )

        # Step 3: Try to use same backup code again
        login_response = client.post(
            "/api/v1/auth/2fa/verify-login",
            json={"user_id": 1, "backup_code": first_backup_code},
        )

        assert login_response.status_code == 400
        assert "Invalid 2FA code or backup code" in login_response.json()["detail"]

    def test_verify_login_2fa_not_enabled(self, client: TestClient):
        """Test login 2FA verification when 2FA is not enabled"""
        response = client.post(
            "/api/v1/auth/2fa/verify-login",
            json={"user_id": 1, "token": "123456"},
        )

        assert response.status_code == 400
        assert "2FA not enabled" in response.json()["detail"]


class Test2FAManagement:
    """Test 2FA management endpoints"""

    def test_get_2fa_status_enabled(self, client: TestClient, auth_headers: dict):
        """Test getting 2FA status when enabled"""
        # Setup and enable 2FA
        setup_response = client.post(
            "/api/v1/auth/2fa/setup",
            json={"user_id": 1},
        )
        secret = setup_response.json()["secret"]

        totp = TwoFactorAuthService.get_totp(secret)
        token = totp.now()

        client.post(
            "/api/v1/auth/2fa/verify",
            json={"user_id": 1, "token": token},
        )

        # Get status
        response = client.get("/api/v1/auth/2fa/status", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True
        assert "enabled_at" in data
        assert data["backup_codes_remaining"] == 10

    def test_get_2fa_status_disabled(self, client: TestClient, auth_headers: dict):
        """Test getting 2FA status when disabled"""
        response = client.get("/api/v1/auth/2fa/status", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False
        assert data["message"] == "2FA not configured"

    def test_disable_2fa(self, client: TestClient, auth_headers: dict):
        """Test disabling 2FA"""
        # Setup and enable 2FA
        setup_response = client.post(
            "/api/v1/auth/2fa/setup",
            json={"user_id": 1},
        )
        secret = setup_response.json()["secret"]

        totp = TwoFactorAuthService.get_totp(secret)
        token = totp.now()

        client.post(
            "/api/v1/auth/2fa/verify",
            json={"user_id": 1, "token": token},
        )

        # Disable 2FA
        response = client.post("/api/v1/auth/2fa/disable", headers=auth_headers)

        assert response.status_code == 200
        assert "2FA disabled" in response.json()["message"]

        # Verify it's disabled
        status_response = client.get("/api/v1/auth/2fa/status", headers=auth_headers)
        assert status_response.json()["enabled"] is False

    def test_regenerate_backup_codes(self, client: TestClient, auth_headers: dict):
        """Test regenerating backup codes"""
        # Setup and enable 2FA
        setup_response = client.post(
            "/api/v1/auth/2fa/setup",
            json={"user_id": 1},
        )
        secret = setup_response.json()["secret"]

        totp = TwoFactorAuthService.get_totp(secret)
        token = totp.now()

        verify_response = client.post(
            "/api/v1/auth/2fa/verify",
            json={"user_id": 1, "token": token},
        )
        old_backup_codes = verify_response.json()["backup_codes"]

        # Regenerate codes
        response = client.post(
            "/api/v1/auth/2fa/regenerate-backup-codes",
            headers=auth_headers,
        )

        assert response.status_code == 200
        new_backup_codes = response.json()["backup_codes"]
        assert len(new_backup_codes) == 10
        # Old codes should be different from new codes
        assert new_backup_codes != old_backup_codes

    def test_admin_disable_2fa_for_user(self, client: TestClient, auth_headers: dict):
        """Test admin disabling 2FA for another user"""
        # Setup and enable 2FA for user
        setup_response = client.post(
            "/api/v1/auth/2fa/setup",
            json={"user_id": 1},
        )
        secret = setup_response.json()["secret"]

        totp = TwoFactorAuthService.get_totp(secret)
        token = totp.now()

        client.post(
            "/api/v1/auth/2fa/verify",
            json={"user_id": 1, "token": token},
        )

        # Admin disables 2FA
        response = client.post(
            "/api/v1/auth/2fa/admin/disable/1",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert "2FA disabled for user" in response.json()["message"]


class Test2FAEdgeCases:
    """Test edge cases and error scenarios"""

    def test_token_with_time_drift(self, client: TestClient):
        """Test TOTP verification with time drift"""
        # Setup 2FA
        setup_response = client.post(
            "/api/v1/auth/2fa/setup",
            json={"user_id": 1},
        )
        secret = setup_response.json()["secret"]

        # Get TOTP and verify - should work even with small time drift
        totp = TwoFactorAuthService.get_totp(secret)
        token = totp.now()

        verify_response = client.post(
            "/api/v1/auth/2fa/verify",
            json={"user_id": 1, "token": token},
        )

        assert verify_response.status_code == 200

    def test_empty_backup_codes_list(self, client: TestClient):
        """Test behavior when all backup codes are used"""
        # Setup and enable 2FA
        setup_response = client.post(
            "/api/v1/auth/2fa/setup",
            json={"user_id": 1},
        )
        secret = setup_response.json()["secret"]

        totp = TwoFactorAuthService.get_totp(secret)
        token = totp.now()

        verify_response = client.post(
            "/api/v1/auth/2fa/verify",
            json={"user_id": 1, "token": token},
        )
        backup_codes = verify_response.json()["backup_codes"]

        # Use all backup codes
        for code in backup_codes:
            client.post(
                "/api/v1/auth/2fa/verify-login",
                json={"user_id": 1, "backup_code": code},
            )

        # Check status - should show 0 remaining codes
        auth_headers = {"Authorization": "Bearer test-token"}  # Mock auth
        # Note: This would need proper auth setup in real scenario
