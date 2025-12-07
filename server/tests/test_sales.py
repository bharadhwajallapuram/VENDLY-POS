# ===========================================
# Vendly POS - Sales API Tests
# ===========================================

import pytest
from fastapi.testclient import TestClient


class TestSalesEndpoints:
    """Test sales endpoints - the core of POS"""

    @pytest.fixture
    def sample_product(self, client: TestClient, auth_headers: dict):
        """Create a sample product for sale tests"""
        response = client.post(
            "/api/v1/products",
            json={
                "name": "Sale Test Product",
                "sku": "SALE-001",
                "price": 29.99,
                "quantity": 100,
                "tax_rate": 0.08,
            },
            headers=auth_headers,
        )
        return response.json()

    def test_create_sale(
        self, client: TestClient, auth_headers: dict, sample_product: dict
    ):
        """Test creating a new sale"""
        sale_data = {
            "items": [
                {
                    "product_id": sample_product["id"],
                    "quantity": 2,
                    "unit_price": 29.99,
                    "discount": 0,
                }
            ],
            "payment_method": "cash",
            "discount": 0,
        }

        response = client.post("/api/v1/sales", json=sale_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "completed"
        assert len(data["items"]) == 1
        assert data["items"][0]["quantity"] == 2

    def test_create_sale_updates_inventory(
        self, client: TestClient, auth_headers: dict, sample_product: dict
    ):
        """Test that creating a sale reduces product inventory"""
        initial_quantity = sample_product["quantity"]

        # Create sale for 5 items
        sale_data = {
            "items": [
                {
                    "product_id": sample_product["id"],
                    "quantity": 5,
                    "unit_price": 29.99,
                    "discount": 0,
                }
            ],
            "payment_method": "cash",
            "discount": 0,
        }

        client.post("/api/v1/sales", json=sale_data, headers=auth_headers)

        # Check inventory was reduced
        product_response = client.get(
            f"/api/v1/products/{sample_product['id']}", headers=auth_headers
        )

        assert product_response.json()["quantity"] == initial_quantity - 5

    def test_create_sale_without_auth(self, client: TestClient):
        """Test creating sale without authentication fails"""
        sale_data = {
            "items": [
                {"product_id": 1, "quantity": 1, "unit_price": 10, "discount": 0}
            ],
            "payment_method": "cash",
            "discount": 0,
        }

        response = client.post("/api/v1/sales", json=sale_data)

        assert response.status_code == 401

    def test_create_sale_with_invalid_product(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating sale with non-existent product fails"""
        sale_data = {
            "items": [
                {"product_id": 99999, "quantity": 1, "unit_price": 10.00, "discount": 0}
            ],
            "payment_method": "cash",
            "discount": 0,
        }

        response = client.post("/api/v1/sales", json=sale_data, headers=auth_headers)

        # API returns 400 Bad Request for invalid product
        assert response.status_code == 400

    def test_get_sale_by_id(
        self, client: TestClient, auth_headers: dict, sample_product: dict
    ):
        """Test retrieving a specific sale"""
        # Create a sale
        sale_data = {
            "items": [
                {
                    "product_id": sample_product["id"],
                    "quantity": 1,
                    "unit_price": 29.99,
                    "discount": 0,
                }
            ],
            "payment_method": "card",
            "discount": 0,
        }

        create_response = client.post(
            "/api/v1/sales", json=sale_data, headers=auth_headers
        )
        sale_id = create_response.json()["id"]

        # Get the sale
        response = client.get(f"/api/v1/sales/{sale_id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["id"] == sale_id
        assert response.json()["payment_method"] == "card"

    def test_list_sales(
        self, client: TestClient, auth_headers: dict, sample_product: dict
    ):
        """Test listing all sales"""
        # Create a few sales
        for _ in range(3):
            sale_data = {
                "items": [
                    {
                        "product_id": sample_product["id"],
                        "quantity": 1,
                        "unit_price": 29.99,
                        "discount": 0,
                    }
                ],
                "payment_method": "cash",
                "discount": 0,
            }
            client.post("/api/v1/sales", json=sale_data, headers=auth_headers)

        response = client.get("/api/v1/sales", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    def test_sale_total_calculation(
        self, client: TestClient, auth_headers: dict, sample_product: dict
    ):
        """Test that sale totals are calculated correctly"""
        sale_data = {
            "items": [
                {
                    "product_id": sample_product["id"],
                    "quantity": 3,
                    "unit_price": 10.00,
                    "discount": 5.00,  # $5 discount on this line
                }
            ],
            "payment_method": "cash",
            "discount": 0,
        }

        response = client.post("/api/v1/sales", json=sale_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        # 3 * $10 = $30, minus $5 discount = $25 subtotal
        # Total should include tax calculation
        assert data["subtotal"] == 25.0

    def test_create_sale_with_multiple_items(
        self, client: TestClient, auth_headers: dict
    ):
        """Test creating a sale with multiple different products"""
        # Create two products
        product1 = client.post(
            "/api/v1/products",
            json={"name": "Product A", "price": 10.00, "quantity": 50},
            headers=auth_headers,
        ).json()

        product2 = client.post(
            "/api/v1/products",
            json={"name": "Product B", "price": 20.00, "quantity": 30},
            headers=auth_headers,
        ).json()

        # Create sale with both
        sale_data = {
            "items": [
                {
                    "product_id": product1["id"],
                    "quantity": 2,
                    "unit_price": 10.00,
                    "discount": 0,
                },
                {
                    "product_id": product2["id"],
                    "quantity": 1,
                    "unit_price": 20.00,
                    "discount": 0,
                },
            ],
            "payment_method": "cash",
            "discount": 0,
        }

        response = client.post("/api/v1/sales", json=sale_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert len(data["items"]) == 2
        # $20 + $20 = $40 subtotal
        assert data["subtotal"] == 40.0

    def test_get_sale_receipt(
        self, client: TestClient, auth_headers: dict, sample_product: dict
    ):
        """Test getting a receipt for a sale"""
        # Create a sale
        sale_data = {
            "items": [
                {
                    "product_id": sample_product["id"],
                    "quantity": 1,
                    "unit_price": 29.99,
                    "discount": 0,
                }
            ],
            "payment_method": "cash",
            "discount": 0,
        }

        create_response = client.post(
            "/api/v1/sales", json=sale_data, headers=auth_headers
        )
        sale_id = create_response.json()["id"]

        # Get receipt
        response = client.get(
            f"/api/v1/sales/{sale_id}/receipt?format=text", headers=auth_headers
        )

        assert response.status_code == 200
        assert (
            "Sale Test Product" in response.text or "RECEIPT" in response.text.upper()
        )
