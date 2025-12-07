# ===========================================
# Vendly POS - Users API Tests (Admin Only)
# ===========================================

import pytest
from fastapi.testclient import TestClient


class TestUsersEndpoints:
    """Test user management endpoints - admin only"""

    def test_create_user_as_admin(self, client: TestClient, auth_headers: dict):
        """Test admin can create new users"""
        user_data = {
            "email": "newuser@vendly.com",
            "password": "securepass123",
            "full_name": "New User",
            "role": "clerk"
        }
        
        response = client.post(
            "/api/v1/users",
            json=user_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@vendly.com"
        assert data["role"] == "clerk"
        assert "password" not in data  # Password should never be returned

    def test_create_user_without_auth(self, client: TestClient):
        """Test creating user without auth fails"""
        response = client.post(
            "/api/v1/users",
            json={"email": "test@test.com", "password": "test123"}
        )
        
        assert response.status_code == 401

    def test_list_users_as_admin(self, client: TestClient, auth_headers: dict):
        """Test admin can list all users"""
        response = client.get("/api/v1/users", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # At least admin user exists
        assert len(data) >= 1

    def test_get_user_by_id(self, client: TestClient, auth_headers: dict):
        """Test getting a specific user"""
        import uuid
        unique_email = f"gettest_{uuid.uuid4().hex[:8]}@vendly.com"
        
        # Create a user first (valid roles: clerk, manager, admin)
        create_response = client.post(
            "/api/v1/users",
            json={"email": unique_email, "password": "test123", "role": "clerk"},
            headers=auth_headers
        )
        assert create_response.status_code in (200, 201), f"Failed to create user: {create_response.json()}"
        user_id = create_response.json()["id"]
        
        response = client.get(f"/api/v1/users/{user_id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["email"] == unique_email

    def test_update_user(self, client: TestClient, auth_headers: dict):
        """Test updating a user"""
        # Create user
        create_response = client.post(
            "/api/v1/users",
            json={"email": "update@vendly.com", "password": "test123", "role": "clerk"},
            headers=auth_headers
        )
        user_id = create_response.json()["id"]
        
        # Update
        response = client.patch(
            f"/api/v1/users/{user_id}",
            json={"full_name": "Updated Name", "role": "manager"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == "Updated Name"
        assert data["role"] == "manager"

    def test_deactivate_user(self, client: TestClient, auth_headers: dict):
        """Test deactivating a user"""
        # Create user
        create_response = client.post(
            "/api/v1/users",
            json={"email": "deactivate@vendly.com", "password": "test123"},
            headers=auth_headers
        )
        user_id = create_response.json()["id"]
        
        # Deactivate
        response = client.patch(
            f"/api/v1/users/{user_id}",
            json={"is_active": False},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["is_active"] == False

    def test_delete_user(self, client: TestClient, auth_headers: dict):
        """Test deleting a user"""
        # Create user
        create_response = client.post(
            "/api/v1/users",
            json={"email": "delete@vendly.com", "password": "test123"},
            headers=auth_headers
        )
        user_id = create_response.json()["id"]
        
        response = client.delete(f"/api/v1/users/{user_id}", headers=auth_headers)
        
        assert response.status_code == 204

    def test_cannot_delete_self(self, client: TestClient, auth_headers: dict):
        """Test admin cannot delete their own account"""
        # Get admin user ID
        me_response = client.get("/api/v1/auth/me", headers=auth_headers)
        # This test assumes we have a way to get the admin's ID
        # If not implemented, this test can be skipped
        pass  # Skip for now - would need /me to return ID

    def test_duplicate_email_rejected(self, client: TestClient, auth_headers: dict):
        """Test that duplicate emails are rejected"""
        user_data = {"email": "duplicate@vendly.com", "password": "test123"}
        
        # Create first user
        client.post("/api/v1/users", json=user_data, headers=auth_headers)
        
        # Try to create another with same email
        response = client.post("/api/v1/users", json=user_data, headers=auth_headers)
        
        assert response.status_code in [400, 409]  # Bad request or Conflict
