# ===========================================
# Vendly POS - End-of-Day Reports Tests
# ===========================================

import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta


class TestEndOfDayReports:
    """Test end-of-day reporting endpoints"""

    @pytest.fixture
    def create_daily_sales_data(self, client: TestClient, auth_headers: dict):
        """Create sales data for a specific day"""
        # Use UTC for consistency with database timestamps
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Create products
        product1_resp = client.post(
            "/api/v1/products",
            json={"name": "EOD Product A", "price": 50.00, "quantity": 100},
            headers=auth_headers,
        )
        assert (
            product1_resp.status_code == 201
        ), f"Failed to create product1: {product1_resp.text}"
        product1 = product1_resp.json()

        product2_resp = client.post(
            "/api/v1/products",
            json={"name": "EOD Product B", "price": 30.00, "quantity": 100},
            headers=auth_headers,
        )
        assert (
            product2_resp.status_code == 201
        ), f"Failed to create product2: {product2_resp.text}"
        product2 = product2_resp.json()

        # Create cash sales
        for _ in range(3):
            sale_resp = client.post(
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
            assert (
                sale_resp.status_code == 201
            ), f"Failed to create cash sale: {sale_resp.text}"

        # Create card sales
        for _ in range(2):
            sale_resp = client.post(
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
                    "discount": 5,
                },
                headers=auth_headers,
            )
            assert (
                sale_resp.status_code == 201
            ), f"Failed to create card sale: {sale_resp.text}"

        return {
            "product1": product1,
            "product2": product2,
            "today": today,
        }

    def test_get_z_report(
        self, client: TestClient, auth_headers: dict, create_daily_sales_data
    ):
        """Test getting Z-Report for a day"""
        today = create_daily_sales_data["today"]
        response = client.get(
            f"/api/v1/reports/z-report?report_date={today}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check Z-Report structure
        assert "report_date" in data
        assert "report_time" in data
        assert "total_sales" in data
        assert "total_revenue" in data
        assert "total_tax" in data
        assert "items_sold" in data
        assert "payment_methods" in data
        assert "top_products" in data

        # Verify sales data
        assert data["total_sales"] == 5
        assert data["total_revenue"] > 0
        assert len(data["payment_methods"]) == 2

    def test_z_report_payment_breakdown(
        self, client: TestClient, auth_headers: dict, create_daily_sales_data
    ):
        """Test that Z-Report includes payment method breakdown"""
        today = create_daily_sales_data["today"]
        response = client.get(
            f"/api/v1/reports/z-report?report_date={today}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check payment methods
        methods = {m["method"]: m for m in data["payment_methods"]}
        assert "cash" in methods
        assert "card" in methods
        assert methods["cash"]["count"] == 3
        assert methods["card"]["count"] == 2

    def test_z_report_top_products(
        self, client: TestClient, auth_headers: dict, create_daily_sales_data
    ):
        """Test that Z-Report includes top products"""
        today = create_daily_sales_data["today"]
        response = client.get(
            f"/api/v1/reports/z-report?report_date={today}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check top products
        assert len(data["top_products"]) > 0
        assert "name" in data["top_products"][0]
        assert "quantity" in data["top_products"][0]
        assert "revenue" in data["top_products"][0]

    def test_reconcile_cash_drawer(
        self, client: TestClient, auth_headers: dict, create_daily_sales_data
    ):
        """Test cash drawer reconciliation"""
        today = create_daily_sales_data["today"]

        # Get Z-Report first to see expected cash
        response = client.get(
            f"/api/v1/reports/z-report?report_date={today}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        z_report = response.json()

        # Calculate expected cash from payment methods
        cash_method = next(
            (m for m in z_report["payment_methods"] if m["method"] == "cash"), None
        )
        expected_cash = cash_method["revenue"] if cash_method else 0.0

        # Reconcile with matching cash
        reconcile_response = client.post(
            f"/api/v1/reports/z-report/reconcile?report_date={today}",
            json={
                "actual_cash": expected_cash,
                "notes": "Exact match",
            },
            headers=auth_headers,
        )

        assert reconcile_response.status_code == 200
        result = reconcile_response.json()

        # Check reconciliation result
        assert "reconciliation" in result
        assert "status" in result
        assert result["reconciliation"]["variance"] == 0.0

    def test_reconcile_cash_with_variance(
        self, client: TestClient, auth_headers: dict, create_daily_sales_data
    ):
        """Test cash reconciliation with variance"""
        today = create_daily_sales_data["today"]

        # Reconcile with different cash amount
        reconcile_response = client.post(
            f"/api/v1/reports/z-report/reconcile?report_date={today}",
            json={
                "actual_cash": 500.00,
                "notes": "Variance detected",
            },
            headers=auth_headers,
        )

        assert reconcile_response.status_code == 200
        result = reconcile_response.json()

        # Check variance is detected
        assert "reconciliation" in result
        assert result["reconciliation"]["actual_cash"] == 500.00
        assert result["reconciliation"]["variance"] != 0.0

    def test_sales_summary(
        self, client: TestClient, auth_headers: dict, create_daily_sales_data
    ):
        """Test daily sales summary endpoint"""
        today = create_daily_sales_data["today"]
        response = client.get(
            f"/api/v1/reports/sales-summary?report_date={today}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check summary structure
        assert "date" in data
        assert "total_sales" in data
        assert "total_revenue" in data
        assert "total_tax" in data
        assert "items_sold" in data
        assert "average_transaction" in data

        # Verify values
        assert data["total_sales"] == 5
        assert data["items_sold"] > 0
        assert data["average_transaction"] > 0

    def test_eod_reports_require_auth(self, client: TestClient):
        """Test that EOD reports require authentication"""
        response = client.get("/api/v1/reports/z-report")
        assert response.status_code == 401

        response = client.post(
            "/api/v1/reports/z-report/reconcile",
            json={"actual_cash": 100.00},
        )
        assert response.status_code == 401

    def test_z_report_default_to_today(
        self, client: TestClient, auth_headers: dict, create_daily_sales_data
    ):
        """Test that Z-Report defaults to today when no date provided"""
        response = client.get(
            "/api/v1/reports/z-report",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        assert data["report_date"] == today

    def test_z_report_past_date(self, client: TestClient, auth_headers: dict):
        """Test Z-Report for a past date with no sales"""
        past_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime(
            "%Y-%m-%d"
        )
        response = client.get(
            f"/api/v1/reports/z-report?report_date={past_date}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["report_date"] == past_date
        assert data["total_sales"] == 0
        assert data["total_revenue"] == 0.0

    def test_refunds_and_returns_in_z_report(
        self, client: TestClient, auth_headers: dict, create_daily_sales_data
    ):
        """Test that Z-Report includes refund and return statistics"""
        today = create_daily_sales_data["today"]

        # Get a sale to refund
        sales_response = client.get("/api/v1/sales", headers=auth_headers)
        assert sales_response.status_code == 200
        sales = sales_response.json()

        if sales:
            sale_id = sales[0]["id"]
            # Create a refund
            client.post(
                f"/api/v1/sales/{sale_id}/refund",
                json={"employee_id": "emp1", "reason": "Customer request"},
                headers=auth_headers,
            )

        # Get Z-Report
        response = client.get(
            f"/api/v1/reports/z-report?report_date={today}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Check refund statistics
        assert "total_refunds" in data
        assert "refund_amount" in data
        assert "total_returns" in data
