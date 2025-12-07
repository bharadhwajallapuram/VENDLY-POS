# ===========================================
# Vendly POS - Customers API Tests
# ===========================================

import pytest
from fastapi.testclient import TestClient


class TestCustomersEndpoints:
    """Test customer management endpoints"""

    def test_create_customer(self, client: TestClient, auth_headers: dict):
        """Test creating a new customer"""
        customer_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
            "address": "123 Main St",
            "notes": "VIP customer"
        }
        
        response = client.post(
            "/api/v1/customers",
            json=customer_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"
        assert data["loyalty_points"] == 0

    def test_create_customer_without_auth(self, client: TestClient):
        """Test creating customer without authentication fails"""
        response = client.post(
            "/api/v1/customers",
            json={"name": "Test Customer"}
        )
        
        assert response.status_code == 401

    def test_list_customers(self, client: TestClient, auth_headers: dict):
        """Test listing all customers"""
        # Create a customer
        client.post(
            "/api/v1/customers",
            json={"name": "List Test Customer"},
            headers=auth_headers
        )
        
        response = client.get("/api/v1/customers", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_customer_by_id(self, client: TestClient, auth_headers: dict):
        """Test getting a specific customer"""
        create_response = client.post(
            "/api/v1/customers",
            json={"name": "Get Test Customer", "email": "get@test.com"},
            headers=auth_headers
        )
        customer_id = create_response.json()["id"]
        
        response = client.get(f"/api/v1/customers/{customer_id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["name"] == "Get Test Customer"

    def test_update_customer(self, client: TestClient, auth_headers: dict):
        """Test updating a customer"""
        create_response = client.post(
            "/api/v1/customers",
            json={"name": "Update Test", "phone": "111-1111"},
            headers=auth_headers
        )
        customer_id = create_response.json()["id"]
        
        # Use PATCH (not PUT) as per API design
        response = client.patch(
            f"/api/v1/customers/{customer_id}",
            json={"name": "Updated Name", "phone": "222-2222"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["phone"] == "222-2222"

    def test_delete_customer(self, client: TestClient, auth_headers: dict):
        """Test deleting a customer"""
        create_response = client.post(
            "/api/v1/customers",
            json={"name": "Delete Test"},
            headers=auth_headers
        )
        customer_id = create_response.json()["id"]
        
        response = client.delete(f"/api/v1/customers/{customer_id}", headers=auth_headers)
        
        assert response.status_code == 204

    def test_adjust_loyalty_points(self, client: TestClient, auth_headers: dict):
        """Test adjusting customer loyalty points"""
        create_response = client.post(
            "/api/v1/customers",
            json={"name": "Loyalty Test"},
            headers=auth_headers
        )
        customer_id = create_response.json()["id"]
        
        # Add points
        response = client.post(
            f"/api/v1/customers/{customer_id}/adjust-loyalty",
            json={"points": 100, "reason": "Welcome bonus"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        assert response.json()["loyalty_points"] == 100

    def test_search_customers(self, client: TestClient, auth_headers: dict):
        """Test searching customers"""
        client.post(
            "/api/v1/customers",
            json={"name": "Alice Smith", "email": "alice@example.com"},
            headers=auth_headers
        )
        client.post(
            "/api/v1/customers",
            json={"name": "Bob Jones", "email": "bob@example.com"},
            headers=auth_headers
        )
        
        response = client.get("/api/v1/customers?q=Alice", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert any("Alice" in c["name"] for c in data)
