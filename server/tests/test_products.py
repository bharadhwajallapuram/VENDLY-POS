# ===========================================
# Vendly POS - Products API Tests
# ===========================================

import pytest
from fastapi.testclient import TestClient


class TestProductsEndpoints:
    """Test products CRUD endpoints"""

    def test_create_product(self, client: TestClient, auth_headers: dict):
        """Test creating a new product"""
        product_data = {
            "name": "Test Product",
            "sku": "TEST-001",
            "price": 19.99,
            "quantity": 100,
            "min_quantity": 10,
            "tax_rate": 0.08,
            "is_active": True,
        }

        response = client.post(
            "/api/v1/products", json=product_data, headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Product"
        assert data["sku"] == "TEST-001"
        assert data["price"] == 19.99
        assert data["quantity"] == 100

    def test_create_product_without_auth(self, client: TestClient):
        """Test creating product without authentication fails"""
        product_data = {"name": "Test", "price": 10.00, "quantity": 5}

        response = client.post("/api/v1/products", json=product_data)

        assert response.status_code == 401

    def test_list_products(self, client: TestClient, auth_headers: dict):
        """Test listing all products"""
        # Create a product first
        client.post(
            "/api/v1/products",
            json={"name": "List Test", "price": 5.00, "quantity": 10},
            headers=auth_headers,
        )

        response = client.get("/api/v1/products", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_product_by_id(self, client: TestClient, auth_headers: dict):
        """Test getting a specific product"""
        # Create product
        create_response = client.post(
            "/api/v1/products",
            json={"name": "Get Test", "price": 15.00, "quantity": 20},
            headers=auth_headers,
        )
        product_id = create_response.json()["id"]

        response = client.get(f"/api/v1/products/{product_id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["name"] == "Get Test"

    def test_get_nonexistent_product(self, client: TestClient, auth_headers: dict):
        """Test getting a product that doesn't exist"""
        response = client.get("/api/v1/products/99999", headers=auth_headers)

        assert response.status_code == 404

    def test_update_product(self, client: TestClient, auth_headers: dict):
        """Test updating a product"""
        # Create product
        create_response = client.post(
            "/api/v1/products",
            json={"name": "Update Test", "price": 10.00, "quantity": 50},
            headers=auth_headers,
        )
        product_id = create_response.json()["id"]

        # Update it
        response = client.patch(
            f"/api/v1/products/{product_id}",
            json={"name": "Updated Name", "price": 25.00},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["price"] == 25.00
        assert data["quantity"] == 50  # Unchanged

    def test_delete_product(self, client: TestClient, auth_headers: dict):
        """Test deleting a product"""
        # Create product
        create_response = client.post(
            "/api/v1/products",
            json={"name": "Delete Test", "price": 5.00, "quantity": 10},
            headers=auth_headers,
        )
        product_id = create_response.json()["id"]

        # Delete it
        response = client.delete(f"/api/v1/products/{product_id}", headers=auth_headers)

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(
            f"/api/v1/products/{product_id}", headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_search_products(self, client: TestClient, auth_headers: dict):
        """Test searching products by name"""
        # Create products
        client.post(
            "/api/v1/products",
            json={"name": "Apple iPhone", "price": 999.00, "quantity": 10},
            headers=auth_headers,
        )
        client.post(
            "/api/v1/products",
            json={"name": "Samsung Galaxy", "price": 899.00, "quantity": 15},
            headers=auth_headers,
        )

        response = client.get("/api/v1/products?q=iPhone", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any("iPhone" in p["name"] for p in data)
