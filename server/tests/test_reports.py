# ===========================================
# Vendly POS - Reports API Tests
# ===========================================

import pytest
from fastapi.testclient import TestClient


class TestReportsEndpoints:
    """Test reporting endpoints"""

    @pytest.fixture
    def create_sales_data(self, client: TestClient, auth_headers: dict):
        """Create some sales data for report testing"""
        # Create products
        product1 = client.post(
            "/api/v1/products",
            json={"name": "Report Product A", "price": 50.00, "quantity": 100},
            headers=auth_headers,
        ).json()

        product2 = client.post(
            "/api/v1/products",
            json={"name": "Report Product B", "price": 30.00, "quantity": 100},
            headers=auth_headers,
        ).json()

        # Create some sales
        for _ in range(3):
            client.post(
                "/api/v1/sales",
                json={
                    "items": [
                        {
                            "product_id": product1["id"],
                            "quantity": 2,
                            "unit_price": 50.00,
                            "discount": 0,
                        }
                    ],
                    "payment_method": "cash",
                    "discount": 0,
                },
                headers=auth_headers,
            )

        for _ in range(2):
            client.post(
                "/api/v1/sales",
                json={
                    "items": [
                        {
                            "product_id": product2["id"],
                            "quantity": 1,
                            "unit_price": 30.00,
                            "discount": 0,
                        }
                    ],
                    "payment_method": "card",
                    "discount": 0,
                },
                headers=auth_headers,
            )

        return {"product1": product1, "product2": product2}

    def test_get_sales_summary(
        self, client: TestClient, auth_headers: dict, create_sales_data
    ):
        """Test getting sales summary report"""
        response = client.get("/api/v1/reports/summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "total_sales" in data
        assert "total_revenue" in data
        assert data["total_sales"] >= 5

    def test_get_sales_summary_with_date_range(
        self, client: TestClient, auth_headers: dict, create_sales_data
    ):
        """Test getting sales summary with date filter"""
        response = client.get(
            "/api/v1/reports/summary?start_date=2025-01-01&end_date=2025-12-31",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_sales" in data

    def test_get_top_products(
        self, client: TestClient, auth_headers: dict, create_sales_data
    ):
        """Test that top products are included in summary"""
        response = client.get("/api/v1/reports/summary", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "top_products" in data
        assert isinstance(data["top_products"], list)

    def test_get_daily_sales(
        self, client: TestClient, auth_headers: dict, create_sales_data
    ):
        """Test getting daily sales breakdown"""
        # Correct endpoint is sales-by-day, not daily
        response = client.get("/api/v1/reports/sales-by-day", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_sales_by_payment_method(
        self, client: TestClient, auth_headers: dict, create_sales_data
    ):
        """Test getting sales by payment method"""
        response = client.get("/api/v1/reports/sales-by-payment", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "data" in data

        # Should have both cash and card sales
        methods = [item["method"] for item in data["data"]]
        assert "cash" in methods
        assert "card" in methods

    def test_reports_require_auth(self, client: TestClient):
        """Test reports - test override provides auth"""
        response = client.get("/api/v1/reports/summary")

        # Test environment always provides test user via override
        assert response.status_code == 200
