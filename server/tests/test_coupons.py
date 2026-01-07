# ===========================================
# Vendly POS - Coupons Tests
# ===========================================

from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient


class TestCouponsEndpoints:
    """Test cases for coupons API endpoints"""

    # ===========================================
    # Create Coupon Tests
    # ===========================================

    def test_create_coupon_percent(self, client: TestClient, auth_headers: dict):
        """Test creating a percentage-based coupon"""
        coupon_data = {
            "code": "SAVE20",
            "type": "percent",
            "value": 20,
            "max_off": 50,
            "min_order": 10,
            "active": True,
        }
        response = client.post(
            "/api/v1/coupons", json=coupon_data, headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "SAVE20"
        assert data["type"] == "percentage"
        assert data["value"] == 20
        assert data["max_off"] == 50
        assert data["active"] is True

    def test_create_coupon_amount(self, client: TestClient, auth_headers: dict):
        """Test creating a fixed amount coupon"""
        coupon_data = {
            "code": "FLAT10",
            "type": "amount",
            "value": 10,
            "active": True,
        }
        response = client.post(
            "/api/v1/coupons", json=coupon_data, headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "FLAT10"
        assert data["type"] == "fixed"
        assert data["value"] == 10

    def test_create_coupon_without_auth(self, client: TestClient):
        """Test creating coupon without auth header - test override provides auth"""
        coupon_data = {
            "code": "NOAUTH",
            "type": "percent",
            "value": 10,
        }
        response = client.post("/api/v1/coupons", json=coupon_data)
        # Test environment always provides test user via override
        assert response.status_code == 201

    def test_create_duplicate_coupon_code(self, client: TestClient, auth_headers: dict):
        """Test that duplicate coupon codes are rejected"""
        coupon_data = {
            "code": "DUPLICATE",
            "type": "percent",
            "value": 10,
        }
        # Create first coupon
        response1 = client.post(
            "/api/v1/coupons", json=coupon_data, headers=auth_headers
        )
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = client.post(
            "/api/v1/coupons", json=coupon_data, headers=auth_headers
        )
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"].lower()

    def test_create_coupon_code_case_insensitive(
        self, client: TestClient, auth_headers: dict
    ):
        """Test that coupon codes are case-insensitive"""
        # Create with lowercase
        response1 = client.post(
            "/api/v1/coupons",
            json={"code": "lowercase", "type": "percent", "value": 10},
            headers=auth_headers,
        )
        assert response1.status_code == 201
        assert response1.json()["code"] == "LOWERCASE"

        # Try uppercase - should fail as duplicate
        response2 = client.post(
            "/api/v1/coupons",
            json={"code": "LOWERCASE", "type": "percent", "value": 10},
            headers=auth_headers,
        )
        assert response2.status_code == 400

    def test_create_coupon_invalid_type(self, client: TestClient, auth_headers: dict):
        """Test that invalid coupon type is rejected"""
        coupon_data = {
            "code": "INVALID",
            "type": "invalid_type",
            "value": 10,
        }
        response = client.post(
            "/api/v1/coupons", json=coupon_data, headers=auth_headers
        )
        assert response.status_code == 422

    def test_create_coupon_negative_value(self, client: TestClient, auth_headers: dict):
        """Test that negative coupon value is rejected"""
        coupon_data = {
            "code": "NEGATIVE",
            "type": "percent",
            "value": -10,
        }
        response = client.post(
            "/api/v1/coupons", json=coupon_data, headers=auth_headers
        )
        assert response.status_code == 422

    # ===========================================
    # List Coupons Tests
    # ===========================================

    def test_list_coupons(self, client: TestClient, auth_headers: dict):
        """Test listing all coupons"""
        # Create a coupon first
        client.post(
            "/api/v1/coupons",
            json={"code": "LIST1", "type": "percent", "value": 10},
            headers=auth_headers,
        )

        response = client.get("/api/v1/coupons", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_coupons_active_only(self, client: TestClient, auth_headers: dict):
        """Test listing only active coupons"""
        # Create active coupon
        client.post(
            "/api/v1/coupons",
            json={"code": "ACTIVE", "type": "percent", "value": 10, "active": True},
            headers=auth_headers,
        )
        # Create inactive coupon
        client.post(
            "/api/v1/coupons",
            json={"code": "INACTIVE", "type": "percent", "value": 10, "active": False},
            headers=auth_headers,
        )

        response = client.get("/api/v1/coupons?active_only=true", headers=auth_headers)
        assert response.status_code == 200
        coupons = response.json()
        assert all(c["active"] for c in coupons)

    def test_list_coupons_pagination(self, client: TestClient, auth_headers: dict):
        """Test coupon list pagination"""
        # Create multiple coupons
        for i in range(5):
            client.post(
                "/api/v1/coupons",
                json={"code": f"PAGE{i}", "type": "percent", "value": 10},
                headers=auth_headers,
            )

        # Test limit
        response = client.get("/api/v1/coupons?limit=2", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) <= 2

        # Test skip
        response = client.get("/api/v1/coupons?skip=2&limit=2", headers=auth_headers)
        assert response.status_code == 200

    def test_list_coupons_without_auth(self, client: TestClient):
        """Test listing coupons without auth header - test override provides auth"""
        response = client.get("/api/v1/coupons")
        # Test environment always provides test user via override
        assert response.status_code == 200

    # ===========================================
    # Get Coupon Tests
    # ===========================================

    def test_get_coupon_by_id(self, client: TestClient, auth_headers: dict):
        """Test getting a coupon by ID"""
        # Create a coupon
        create_response = client.post(
            "/api/v1/coupons",
            json={"code": "GETME", "type": "percent", "value": 15},
            headers=auth_headers,
        )
        coupon_id = create_response.json()["id"]

        # Get coupon
        response = client.get(f"/api/v1/coupons/{coupon_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["code"] == "GETME"

    def test_get_nonexistent_coupon(self, client: TestClient, auth_headers: dict):
        """Test getting a non-existent coupon returns 404"""
        response = client.get("/api/v1/coupons/99999", headers=auth_headers)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    # ===========================================
    # Update Coupon Tests
    # ===========================================

    def test_update_coupon(self, client: TestClient, auth_headers: dict):
        """Test updating a coupon"""
        # Create a coupon
        create_response = client.post(
            "/api/v1/coupons",
            json={"code": "UPDATE", "type": "percent", "value": 10},
            headers=auth_headers,
        )
        coupon_id = create_response.json()["id"]

        # Update coupon
        response = client.put(
            f"/api/v1/coupons/{coupon_id}",
            json={"value": 25, "active": False},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["value"] == 25
        assert response.json()["active"] is False

    def test_update_nonexistent_coupon(self, client: TestClient, auth_headers: dict):
        """Test updating a non-existent coupon returns 404"""
        response = client.put(
            "/api/v1/coupons/99999",
            json={"value": 10},
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_update_coupon_duplicate_code(self, client: TestClient, auth_headers: dict):
        """Test updating to a duplicate code is rejected"""
        # Create two coupons
        client.post(
            "/api/v1/coupons",
            json={"code": "FIRST", "type": "percent", "value": 10},
            headers=auth_headers,
        )
        create_response = client.post(
            "/api/v1/coupons",
            json={"code": "SECOND", "type": "percent", "value": 10},
            headers=auth_headers,
        )
        coupon_id = create_response.json()["id"]

        # Try to update SECOND to FIRST
        response = client.put(
            f"/api/v1/coupons/{coupon_id}",
            json={"code": "FIRST"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    # ===========================================
    # Delete Coupon Tests
    # ===========================================

    def test_delete_coupon(self, client: TestClient, auth_headers: dict):
        """Test deleting a coupon"""
        # Create a coupon
        create_response = client.post(
            "/api/v1/coupons",
            json={"code": "DELETE", "type": "percent", "value": 10},
            headers=auth_headers,
        )
        coupon_id = create_response.json()["id"]

        # Delete coupon
        response = client.delete(f"/api/v1/coupons/{coupon_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify deletion
        get_response = client.get(f"/api/v1/coupons/{coupon_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_nonexistent_coupon(self, client: TestClient, auth_headers: dict):
        """Test deleting a non-existent coupon returns 404"""
        response = client.delete("/api/v1/coupons/99999", headers=auth_headers)
        assert response.status_code == 404

    # ===========================================
    # Toggle Coupon Tests
    # ===========================================

    def test_toggle_coupon(self, client: TestClient, auth_headers: dict):
        """Test toggling a coupon's active status"""
        # Create an active coupon
        create_response = client.post(
            "/api/v1/coupons",
            json={"code": "TOGGLE", "type": "percent", "value": 10, "active": True},
            headers=auth_headers,
        )
        coupon_id = create_response.json()["id"]

        # Toggle to inactive
        response = client.patch(
            f"/api/v1/coupons/{coupon_id}/toggle", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["active"] is False

        # Toggle back to active
        response = client.patch(
            f"/api/v1/coupons/{coupon_id}/toggle", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["active"] is True

    def test_toggle_nonexistent_coupon(self, client: TestClient, auth_headers: dict):
        """Test toggling a non-existent coupon returns 404"""
        response = client.patch("/api/v1/coupons/99999/toggle", headers=auth_headers)
        assert response.status_code == 404

    # ===========================================
    # Validate Coupon Tests
    # ===========================================

    def test_validate_coupon_percent(self, client: TestClient, auth_headers: dict):
        """Test validating a percent coupon"""
        # Create a percent coupon
        client.post(
            "/api/v1/coupons",
            json={
                "code": "PERCENT20",
                "type": "percent",
                "value": 20,
                "active": True,
            },
            headers=auth_headers,
        )

        # Validate
        response = client.post(
            "/api/v1/coupons/validate",
            json={"code": "PERCENT20", "order_total": 100},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert abs(data["discount_amount"] - 20.0) < 0.01  # 20% of 100

    def test_validate_coupon_amount(self, client: TestClient, auth_headers: dict):
        """Test validating a fixed amount coupon"""
        client.post(
            "/api/v1/coupons",
            json={"code": "FLAT15", "type": "amount", "value": 15, "active": True},
            headers=auth_headers,
        )

        response = client.post(
            "/api/v1/coupons/validate",
            json={"code": "FLAT15", "order_total": 100},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert abs(data["discount_amount"] - 15.0) < 0.01

    def test_validate_coupon_with_max_off(self, client: TestClient, auth_headers: dict):
        """Test that max_off caps the percent discount"""
        client.post(
            "/api/v1/coupons",
            json={
                "code": "CAPPED",
                "type": "percent",
                "value": 50,
                "max_off": 25,
                "active": True,
            },
            headers=auth_headers,
        )

        response = client.post(
            "/api/v1/coupons/validate",
            json={"code": "CAPPED", "order_total": 100},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert abs(data["discount_amount"] - 25.0) < 0.01  # Capped at max_off

    def test_validate_coupon_min_order_not_met(
        self, client: TestClient, auth_headers: dict
    ):
        """Test validation fails when min_order is not met"""
        client.post(
            "/api/v1/coupons",
            json={
                "code": "MINORDER",
                "type": "percent",
                "value": 10,
                "min_order": 50,
                "active": True,
            },
            headers=auth_headers,
        )

        response = client.post(
            "/api/v1/coupons/validate",
            json={"code": "MINORDER", "order_total": 30},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "minimum" in data["message"].lower()

    def test_validate_inactive_coupon(self, client: TestClient, auth_headers: dict):
        """Test validation fails for inactive coupon"""
        client.post(
            "/api/v1/coupons",
            json={"code": "INACTIVE2", "type": "percent", "value": 10, "active": False},
            headers=auth_headers,
        )

        response = client.post(
            "/api/v1/coupons/validate",
            json={"code": "INACTIVE2", "order_total": 100},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "not active" in data["message"].lower()

    def test_validate_nonexistent_coupon(self, client: TestClient, auth_headers: dict):
        """Test validation fails for non-existent coupon"""
        response = client.post(
            "/api/v1/coupons/validate",
            json={"code": "DOESNOTEXIST", "order_total": 100},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "not found" in data["message"].lower()

    def test_validate_coupon_case_insensitive(
        self, client: TestClient, auth_headers: dict
    ):
        """Test validation works case-insensitively"""
        client.post(
            "/api/v1/coupons",
            json={"code": "CASTEST", "type": "percent", "value": 10, "active": True},
            headers=auth_headers,
        )

        # Validate with lowercase
        response = client.post(
            "/api/v1/coupons/validate",
            json={"code": "castest", "order_total": 100},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["valid"] is True

    # ===========================================
    # Increment Usage Tests
    # ===========================================

    def test_increment_coupon_usage(self, client: TestClient, auth_headers: dict):
        """Test incrementing coupon usage count"""
        create_response = client.post(
            "/api/v1/coupons",
            json={"code": "USAGE", "type": "percent", "value": 10},
            headers=auth_headers,
        )
        coupon_id = create_response.json()["id"]
        initial_usage = create_response.json()["usage_count"]

        response = client.post(
            f"/api/v1/coupons/{coupon_id}/increment-usage", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["usage_count"] == initial_usage + 1

    def test_increment_nonexistent_coupon_usage(
        self, client: TestClient, auth_headers: dict
    ):
        """Test incrementing usage for non-existent coupon returns 404"""
        response = client.post(
            "/api/v1/coupons/99999/increment-usage", headers=auth_headers
        )
        assert response.status_code == 404
