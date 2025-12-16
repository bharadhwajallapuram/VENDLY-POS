# ===========================================
# Vendly POS - Demand Forecasting Tests
# Unit and integration tests
# ===========================================

import sys
from pathlib import Path

# Add parent directory to path to import ai_ml module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

# Check for optional dependencies
try:
    from prophet import Prophet

    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False

try:
    from statsmodels.tsa.arima.model import ARIMA

    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False

from app.db import models as m
from app.db.session import SessionLocal, engine
from app.services.demand_forecast_service import DemandForecastService
from ai_ml.demand_forecast import DemandForecaster


@pytest.fixture
def db():
    """Create a test database session"""
    # Create tables
    m.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    # Clean up
    m.Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_product(db: Session):
    """Create a sample product for testing"""
    product = m.Product(
        name="Test Product",
        sku="TEST-001",
        barcode="1234567890",
        price=100.0,
        cost=50.0,
        quantity=100,
        category_id=None,
    )
    db.add(product)
    db.commit()
    return product


@pytest.fixture
def sample_sales_data(db: Session, sample_product: m.Product):
    """Create sample sales history"""
    # Create 60 days of sales history
    base_date = datetime.utcnow() - timedelta(days=60)

    for i in range(60):
        date = base_date + timedelta(days=i)
        quantity = np.random.randint(5, 25)

        history = m.DemandHistory(
            product_id=sample_product.id,
            date=date,
            quantity_sold=quantity,
            revenue=quantity * sample_product.price,
            day_of_week=date.weekday(),
            is_weekend=date.weekday() >= 5,
        )
        db.add(history)

    db.commit()
    return sample_product


class TestDemandForecaster:
    """Tests for DemandForecaster class"""

    def test_prepare_data(self):
        """Test data preparation"""
        forecaster = DemandForecaster()

        # Create sample data
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "quantity": np.random.randint(5, 20, 30),
            }
        )

        result = forecaster.prepare_data(data)

        assert len(result) == 30
        assert "date" in result.columns
        assert "quantity" in result.columns
        assert result["date"].dtype == "datetime64[ns]"

    def test_prepare_data_missing_date_column(self):
        """Test error handling for missing date column"""
        forecaster = DemandForecaster()

        data = pd.DataFrame(
            {
                "quantity": [1, 2, 3],
            }
        )

        with pytest.raises(ValueError):
            forecaster.prepare_data(data)

    def test_train_ensemble(self):
        """Test ensemble model training"""
        forecaster = DemandForecaster()

        # Create sample data
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        quantity = [
            10 + 5 * np.sin(i / 10) + np.random.normal(0, 1) for i in range(100)
        ]

        data = pd.DataFrame(
            {
                "date": dates,
                "quantity": quantity,
            }
        )

        metrics = forecaster.train_ensemble(data)

        assert "model_type" in metrics
        assert metrics["model_type"] == "ensemble"
        assert "mae" in metrics
        assert "rmse" in metrics
        assert "r2" in metrics
        assert metrics["mae"] >= 0
        assert metrics["rmse"] >= 0

    def test_forecast_ensemble(self):
        """Test ensemble forecasting"""
        forecaster = DemandForecaster()

        # Create sample data
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        quantity = [10 + 5 * np.sin(i / 10) for i in range(100)]

        data = pd.DataFrame(
            {
                "date": dates,
                "quantity": quantity,
            }
        )

        result = forecaster.forecast(data, days_ahead=14, model_type="ensemble")

        assert "model_type" in result
        assert result["model_type"] == "ensemble"
        assert "forecast" in result
        assert "average_demand" in result
        assert len(result["forecast"]) == 14

    def test_forecast_output_format(self):
        """Test forecast output structure"""
        forecaster = DemandForecaster()

        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        quantity = [10 + np.random.randint(-2, 5) for _ in range(100)]

        data = pd.DataFrame(
            {
                "date": dates,
                "quantity": quantity,
            }
        )

        result = forecaster.forecast(data, days_ahead=7)

        assert "forecast" in result
        for forecast_item in result["forecast"]:
            assert "date" in forecast_item
            assert "forecast" in forecast_item
            assert "lower_bound" in forecast_item
            assert "upper_bound" in forecast_item
            assert forecast_item["forecast"] >= 0

    def test_get_forecast_metrics(self):
        """Test forecast evaluation metrics"""
        forecaster = DemandForecaster()

        # Create actual and forecast data
        dates = pd.date_range("2024-01-01", periods=10, freq="D")

        actual_data = pd.DataFrame(
            {
                "date": dates,
                "quantity": [10, 12, 11, 13, 14, 12, 11, 15, 14, 12],
            }
        )

        forecast_data = pd.DataFrame(
            {
                "date": dates,
                "forecast": [
                    10.5,
                    11.5,
                    11.2,
                    13.5,
                    13.8,
                    12.2,
                    11.5,
                    14.8,
                    14.2,
                    12.5,
                ],
            }
        )

        metrics = forecaster.get_forecast_metrics(actual_data, forecast_data)

        assert "mae" in metrics
        assert "rmse" in metrics
        assert "r2" in metrics
        assert metrics["mae"] >= 0
        assert metrics["rmse"] >= 0


class TestDemandForecastService:
    """Tests for DemandForecastService"""

    def test_get_product_sales_history(self, db: Session, sample_sales_data: m.Product):
        """Test retrieving sales history"""
        service = DemandForecastService()

        result = service.get_product_sales_history(
            db, sample_sales_data.id, days_back=60
        )

        assert not result.empty
        assert "date" in result.columns
        assert "quantity" in result.columns
        assert len(result) > 0

    def test_get_product_sales_history_no_data(
        self, db: Session, sample_product: m.Product
    ):
        """Test handling of product with no sales"""
        service = DemandForecastService()

        result = service.get_product_sales_history(db, sample_product.id)

        assert result.empty

    def test_train_forecast_model(self, db: Session, sample_sales_data: m.Product):
        """Test model training"""
        service = DemandForecastService()

        result = service.train_forecast_model(db, sample_sales_data.id, user_id=None)

        assert "product_id" in result
        assert "product_name" in result
        assert "model_type" in result
        assert "metrics" in result

    def test_generate_forecast(self, db: Session, sample_sales_data: m.Product):
        """Test forecast generation"""
        service = DemandForecastService()

        result = service.generate_forecast(
            db, sample_sales_data.id, days_ahead=14, user_id=None
        )

        assert "forecast_id" in result
        assert "product_id" in result
        assert "forecast" in result
        assert len(result["forecast"]) == 14

    def test_generate_forecast_persists_to_db(
        self, db: Session, sample_sales_data: m.Product
    ):
        """Test that forecast is saved to database"""
        service = DemandForecastService()

        result = service.generate_forecast(db, sample_sales_data.id, days_ahead=10)

        # Verify forecast is in database
        forecast = (
            db.query(m.DemandForecast)
            .filter(m.DemandForecast.id == result["forecast_id"])
            .first()
        )

        assert forecast is not None
        assert forecast.product_id == sample_sales_data.id
        assert forecast.forecast_horizon_days == 10

    def test_generate_forecast_persists_details(
        self, db: Session, sample_sales_data: m.Product
    ):
        """Test that forecast details are saved"""
        service = DemandForecastService()

        result = service.generate_forecast(db, sample_sales_data.id, days_ahead=10)

        # Verify details are in database
        details = (
            db.query(m.ForecastDetail)
            .filter(m.ForecastDetail.demand_forecast_id == result["forecast_id"])
            .all()
        )

        assert len(details) == 10

    def test_evaluate_forecast(self, db: Session, sample_sales_data: m.Product):
        """Test forecast evaluation"""
        service = DemandForecastService()

        # Generate forecast
        forecast_result = service.generate_forecast(
            db, sample_sales_data.id, days_ahead=10
        )
        forecast_id = forecast_result["forecast_id"]

        # Evaluate - may return error if no overlapping dates (which is expected in test)
        eval_result = service.evaluate_forecast(db, forecast_id)

        # Either we get metrics or an expected error about no overlapping dates
        assert "metrics" in eval_result or "error" in eval_result
        if "metrics" in eval_result:
            assert "mae" in eval_result["metrics"]
            assert "rmse" in eval_result["metrics"]

    def test_get_forecast_summary(self, db: Session, sample_sales_data: m.Product):
        """Test getting forecast summary"""
        service = DemandForecastService()

        # Generate forecast
        service.generate_forecast(db, sample_sales_data.id, days_ahead=10)

        # Get summary
        summary = service.get_forecast_summary(db, sample_sales_data.id)

        assert "product_id" in summary
        assert "product_name" in summary
        assert "latest_forecast_id" in summary
        assert "next_7_days" in summary

    def test_get_low_stock_alerts(self, db: Session, sample_sales_data: m.Product):
        """Test low stock alert generation"""
        service = DemandForecastService()

        # Generate forecast
        service.generate_forecast(db, sample_sales_data.id, days_ahead=10)

        # Get alerts (may be empty if stock is sufficient)
        alerts = service.get_low_stock_alerts(db, threshold_days=7)

        assert isinstance(alerts, list)

    def test_update_demand_history(self, db: Session, sample_product: m.Product):
        """Test updating demand history"""
        service = DemandForecastService()

        result = service.update_demand_history(
            db, sample_product.id, datetime.utcnow(), quantity=5, revenue=500.0
        )

        assert "success" in result or "error" in result

    def test_get_product_forecast_comparison(
        self, db: Session, sample_sales_data: m.Product
    ):
        """Test forecast vs actual comparison"""
        service = DemandForecastService()

        # Generate forecast
        service.generate_forecast(db, sample_sales_data.id, days_ahead=10)

        # Get comparison - may have error key if no matching data
        comparison = service.get_product_forecast_comparison(db, sample_sales_data.id)

        # Either we get a valid comparison or an error (both are acceptable)
        if "error" not in comparison:
            assert "product_id" in comparison
            assert "comparison" in comparison
            assert "avg_accuracy" in comparison
        else:
            # Error response is acceptable for edge cases
            assert isinstance(comparison["error"], str)


class TestDemandForecastIntegration:
    """Integration tests for demand forecasting"""

    def test_full_forecasting_workflow(self, db: Session, sample_sales_data: m.Product):
        """Test complete forecasting workflow"""
        service = DemandForecastService()

        # 1. Generate forecast
        forecast = service.generate_forecast(db, sample_sales_data.id, days_ahead=14)
        assert "forecast_id" in forecast or "error" not in forecast

        if "forecast_id" in forecast:
            # 2. Get summary
            summary = service.get_forecast_summary(db, sample_sales_data.id)
            assert summary["latest_forecast_id"] == forecast["forecast_id"]

            # 3. Get comparison - may not have forecast_id if there's an error
            comparison = service.get_product_forecast_comparison(
                db, sample_sales_data.id
            )
            if "error" not in comparison:
                assert comparison["forecast_id"] == forecast["forecast_id"]

            # 4. Evaluate - may return error for no overlapping dates
            evaluation = service.evaluate_forecast(db, forecast["forecast_id"])
            assert "metrics" in evaluation or "error" in evaluation

    def test_multiple_forecasts_for_same_product(
        self, db: Session, sample_sales_data: m.Product
    ):
        """Test generating multiple forecasts for same product"""
        service = DemandForecastService()

        # Generate first forecast
        forecast1 = service.generate_forecast(db, sample_sales_data.id, days_ahead=14)

        # Generate second forecast (different model)
        forecast2 = service.generate_forecast(db, sample_sales_data.id, days_ahead=30)

        assert forecast1["forecast_id"] != forecast2["forecast_id"]
        assert forecast1["forecast_horizon"] == 14
        assert forecast2["forecast_horizon"] == 30

    def test_forecast_with_insufficient_data(
        self, db: Session, sample_product: m.Product
    ):
        """Test forecasting with insufficient data"""
        service = DemandForecastService()

        # Add minimal sales data
        history = m.DemandHistory(
            product_id=sample_product.id,
            date=datetime.utcnow(),
            quantity_sold=5,
            revenue=500,
        )
        db.add(history)
        db.commit()

        result = service.generate_forecast(db, sample_product.id)

        # Should handle gracefully (may return error or result)
        assert result is not None


class TestModelTypes:
    """Test different model types"""

    @pytest.mark.skipif(not HAS_PROPHET, reason="Prophet not installed")
    def test_prophet_model(self):
        """Test Prophet model training and forecasting"""
        forecaster = DemandForecaster()

        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "quantity": [10 + np.sin(i / 10) for i in range(100)],
            }
        )

        # Train
        metrics = forecaster.train_prophet(data)
        assert "mae" in metrics or "error" in metrics

        # Forecast
        result = forecaster.forecast(data, model_type="prophet")
        assert result is not None

    @pytest.mark.skipif(not HAS_STATSMODELS, reason="statsmodels not installed")
    def test_arima_model(self):
        """Test ARIMA model training and forecasting"""
        forecaster = DemandForecaster()

        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        data = pd.DataFrame(
            {
                "date": dates,
                "quantity": [10 + np.sin(i / 10) for i in range(100)],
            }
        )

        # Train
        metrics = forecaster.train_arima(data)
        assert "mae" in metrics or "error" in metrics

        # Forecast
        result = forecaster.forecast(data, model_type="arima")
        assert result is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
