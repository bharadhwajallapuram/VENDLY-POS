# ===========================================
# Vendly POS - AI/ML Endpoints Tests
# ===========================================

import pytest
from fastapi.testclient import TestClient


class TestAIEndpoints:
    """Test cases for AI/ML API endpoints"""

    # ===========================================
    # Sales Forecasting Tests
    # ===========================================

    def test_forecast_sales(self, client: TestClient):
        """Test sales forecasting endpoint"""
        response = client.post(
            "/api/v1/ai/forecast",
            json={"product_id": 1, "days": 7},
        )
        assert response.status_code == 200
        data = response.json()
        assert "dates" in data
        assert "sales" in data
        assert len(data["dates"]) == 7
        assert len(data["sales"]) == 7

    def test_forecast_sales_default_days(self, client: TestClient):
        """Test forecasting with default number of days"""
        response = client.post(
            "/api/v1/ai/forecast",
            json={"product_id": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["dates"]) == 7  # default is 7

    def test_forecast_sales_custom_days(self, client: TestClient):
        """Test forecasting with custom number of days"""
        response = client.post(
            "/api/v1/ai/forecast",
            json={"days": 14},
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["dates"]) == 14

    def test_forecast_sales_empty_body(self, client: TestClient):
        """Test forecasting with empty body uses defaults"""
        response = client.post(
            "/api/v1/ai/forecast",
            json={},
        )
        assert response.status_code == 200

    # ===========================================
    # Anomaly Detection Tests
    # ===========================================

    def test_detect_anomalies(self, client: TestClient):
        """Test anomaly detection endpoint"""
        sales_data = [
            {"date": "2025-01-01", "sales": 100.0},
            {"date": "2025-01-02", "sales": 105.0},
            {"date": "2025-01-03", "sales": 98.0},
            {"date": "2025-01-04", "sales": 500.0},  # Anomaly
            {"date": "2025-01-05", "sales": 102.0},
        ]
        response = client.post(
            "/api/v1/ai/anomaly",
            json={"sales_data": sales_data, "threshold": 2.0},
        )
        assert response.status_code == 200
        data = response.json()
        assert "anomalies" in data
        assert isinstance(data["anomalies"], list)

    def test_detect_anomalies_empty_data(self, client: TestClient):
        """Test anomaly detection with empty data"""
        response = client.post(
            "/api/v1/ai/anomaly",
            json={"sales_data": []},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["anomalies"] == []

    def test_detect_anomalies_default_threshold(self, client: TestClient):
        """Test anomaly detection with default threshold"""
        sales_data = [
            {"date": "2025-01-01", "sales": 100.0},
            {"date": "2025-01-02", "sales": 105.0},
        ]
        response = client.post(
            "/api/v1/ai/anomaly",
            json={"sales_data": sales_data},
        )
        assert response.status_code == 200

    def test_detect_anomalies_invalid_data(self, client: TestClient):
        """Test anomaly detection with invalid data format"""
        response = client.post(
            "/api/v1/ai/anomaly",
            json={"sales_data": [{"invalid": "data"}]},
        )
        assert response.status_code == 422

    # ===========================================
    # Recommendations Tests
    # ===========================================

    def test_recommend_products(self, client: TestClient):
        """Test product recommendations endpoint"""
        response = client.post(
            "/api/v1/ai/recommend",
            json={"customer_id": 1, "n": 3},
        )
        assert response.status_code == 200
        data = response.json()
        assert "product_ids" in data
        assert isinstance(data["product_ids"], list)
        assert len(data["product_ids"]) <= 3

    def test_recommend_products_default_n(self, client: TestClient):
        """Test recommendations with default number"""
        response = client.post(
            "/api/v1/ai/recommend",
            json={"customer_id": 1},
        )
        assert response.status_code == 200

    def test_recommend_products_missing_customer(self, client: TestClient):
        """Test recommendations with missing customer_id"""
        response = client.post(
            "/api/v1/ai/recommend",
            json={"n": 3},
        )
        assert response.status_code == 422

    # ===========================================
    # Price Suggestion Tests
    # ===========================================

    def test_suggest_price(self, client: TestClient):
        """Test price suggestion endpoint"""
        response = client.post(
            "/api/v1/ai/price-suggest",
            json={"product_id": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert "suggested_price" in data
        assert isinstance(data["suggested_price"], (int, float))
        assert data["suggested_price"] > 0

    def test_suggest_price_missing_product(self, client: TestClient):
        """Test price suggestion with missing product_id"""
        response = client.post(
            "/api/v1/ai/price-suggest",
            json={},
        )
        assert response.status_code == 422

    # ===========================================
    # Ask Analytics Tests
    # ===========================================

    def test_ask_analytics(self, client: TestClient):
        """Test natural language analytics endpoint"""
        response = client.post(
            "/api/v1/ai/ask",
            json={"question": "What were total sales today?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert isinstance(data["answer"], str)

    def test_ask_analytics_empty_question(self, client: TestClient):
        """Test ask with empty question"""
        response = client.post(
            "/api/v1/ai/ask",
            json={"question": ""},
        )
        assert response.status_code == 200

    def test_ask_analytics_missing_question(self, client: TestClient):
        """Test ask with missing question field"""
        response = client.post(
            "/api/v1/ai/ask",
            json={},
        )
        assert response.status_code == 422

    # ===========================================
    # Voice Command Tests
    # ===========================================

    def test_voice_command(self, client: TestClient):
        """Test voice command endpoint"""
        response = client.post(
            "/api/v1/ai/voice",
            json={"command": "add item to cart"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert isinstance(data["result"], str)

    def test_voice_command_empty(self, client: TestClient):
        """Test voice command with empty command"""
        response = client.post(
            "/api/v1/ai/voice",
            json={"command": ""},
        )
        assert response.status_code == 200

    def test_voice_command_missing(self, client: TestClient):
        """Test voice command with missing command field"""
        response = client.post(
            "/api/v1/ai/voice",
            json={},
        )
        assert response.status_code == 422


class TestAIErrorHandling:
    """Test error handling in AI endpoints"""

    def test_forecast_handles_invalid_product(self, client: TestClient):
        """Test forecast handles non-existent product gracefully"""
        response = client.post(
            "/api/v1/ai/forecast",
            json={"product_id": 999999, "days": 7},
        )
        # Should return 200 with some default/empty forecast
        assert response.status_code == 200

    def test_recommend_handles_invalid_customer(self, client: TestClient):
        """Test recommendations handle non-existent customer gracefully"""
        response = client.post(
            "/api/v1/ai/recommend",
            json={"customer_id": 999999, "n": 3},
        )
        # Should return 200 with some default recommendations
        assert response.status_code == 200

    def test_price_suggest_handles_invalid_product(self, client: TestClient):
        """Test price suggestion handles non-existent product"""
        response = client.post(
            "/api/v1/ai/price-suggest",
            json={"product_id": 999999},
        )
        # Should return 200 with some default price
        assert response.status_code == 200
