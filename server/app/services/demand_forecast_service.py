# ===========================================
# Vendly POS - Demand Forecast Service
# Business logic for demand forecasting
# ===========================================

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.db import models as m

# Add parent directory to path to import ai_ml module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from ai_ml.demand_forecast import DemandForecaster

logger = logging.getLogger(__name__)


class DemandForecastService:
    """Service for managing demand forecasting operations"""

    def __init__(self):
        self.forecaster = DemandForecaster()

    def get_product_sales_history(
        self, db: Session, product_id: int, days_back: int = 180
    ) -> pd.DataFrame:
        """
        Retrieve historical sales data for a product.

        Args:
            db: Database session
            product_id: Product ID
            days_back: Number of days of history to retrieve

        Returns:
            DataFrame with sales history
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)

        # Query from existing demand history or calculate from sales
        history = (
            db.query(m.DemandHistory)
            .filter(
                m.DemandHistory.product_id == product_id,
                m.DemandHistory.date >= cutoff_date,
            )
            .all()
        )

        if history:
            # Convert to DataFrame
            data = [
                {
                    "date": h.date,
                    "quantity": h.quantity_sold,
                    "revenue": h.revenue,
                }
                for h in history
            ]
            df = pd.DataFrame(data)
        else:
            # Calculate from sales
            sales_data = (
                db.query(
                    m.Sale.created_at,
                    m.SaleItem.quantity,
                    m.SaleItem.unit_price * m.SaleItem.quantity,
                )
                .join(m.SaleItem, m.Sale.id == m.SaleItem.sale_id)
                .filter(
                    m.SaleItem.product_id == product_id,
                    m.Sale.created_at >= cutoff_date,
                )
                .all()
            )

            if not sales_data:
                return pd.DataFrame()

            # Aggregate by day
            df_list = []
            for date_val, quantity, revenue in sales_data:
                df_list.append(
                    {
                        "date": date_val.date(),
                        "quantity": quantity,
                        "revenue": float(revenue) if revenue else 0,
                    }
                )

            df = pd.DataFrame(df_list)
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                df = (
                    df.groupby("date")
                    .agg({"quantity": "sum", "revenue": "sum"})
                    .reset_index()
                )

        return df

    def train_forecast_model(
        self,
        db: Session,
        product_id: int,
        model_type: str = "ensemble",
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Train a demand forecast model for a product.

        Args:
            db: Database session
            product_id: Product ID
            model_type: Type of model ('prophet', 'arima', 'ensemble')
            user_id: User ID for audit trail

        Returns:
            Training results dictionary
        """
        try:
            # Get product
            product = db.query(m.Product).filter(m.Product.id == product_id).first()
            if not product:
                return {"error": "Product not found"}

            # Get sales history
            df = self.get_product_sales_history(db, product_id)
            if df.empty:
                return {"error": "Insufficient sales history for this product"}

            # Prepare data with standard column name
            df = df.rename(columns={"quantity": "quantity"})

            # Train model
            logger.info(f"Training {model_type} model for product {product_id}")
            metrics = self.forecaster.train_ensemble(df)

            return {
                "product_id": product_id,
                "product_name": product.name,
                "model_type": model_type,
                "metrics": metrics,
                "trained_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {"error": str(e)}

    def generate_forecast(
        self,
        db: Session,
        product_id: int,
        days_ahead: int = 30,
        model_type: str = "ensemble",
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate demand forecast for a product.

        Args:
            db: Database session
            product_id: Product ID
            days_ahead: Number of days to forecast
            model_type: Type of model to use
            user_id: User ID for audit trail

        Returns:
            Forecast results dictionary
        """
        try:
            # Get product
            product = db.query(m.Product).filter(m.Product.id == product_id).first()
            if not product:
                return {"error": "Product not found"}

            # Get sales history
            df = self.get_product_sales_history(db, product_id)
            if df.empty:
                return {"error": "Insufficient sales history"}

            # Prepare data
            df = df.rename(columns={"quantity": "quantity"})

            # Generate forecast
            forecast_result = self.forecaster.forecast(df, days_ahead, model_type)

            if "error" in forecast_result:
                return forecast_result

            # Save forecast to database
            forecast_record = m.DemandForecast(
                product_id=product_id,
                forecast_date=datetime.utcnow(),
                forecast_horizon_days=days_ahead,
                model_type=model_type,
                average_demand=forecast_result.get("average_demand", 0),
                confidence_level=forecast_result.get("confidence_level", 0.9),
                created_by_user_id=user_id,
            )
            db.add(forecast_record)
            db.flush()  # Get the ID

            # Save forecast details
            for forecast_item in forecast_result.get("forecast", []):
                detail = m.ForecastDetail(
                    demand_forecast_id=forecast_record.id,
                    forecast_for_date=forecast_item["date"],
                    forecasted_quantity=forecast_item["forecast"],
                    lower_bound=forecast_item.get("lower_bound"),
                    upper_bound=forecast_item.get("upper_bound"),
                )
                db.add(detail)

            db.commit()

            return {
                "forecast_id": forecast_record.id,
                "product_id": product_id,
                "product_name": product.name,
                "model_type": model_type,
                "forecast_horizon": days_ahead,
                "average_demand": forecast_result.get("average_demand"),
                "forecast": forecast_result.get("forecast"),
                "created_at": forecast_record.created_at.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            db.rollback()
            return {"error": str(e)}

    def evaluate_forecast(
        self,
        db: Session,
        forecast_id: int,
    ) -> Dict[str, Any]:
        """
        Evaluate forecast accuracy against actual data.

        Args:
            db: Database session
            forecast_id: Forecast ID

        Returns:
            Evaluation metrics
        """
        try:
            # Get forecast
            forecast = (
                db.query(m.DemandForecast)
                .filter(m.DemandForecast.id == forecast_id)
                .first()
            )
            if not forecast:
                return {"error": "Forecast not found"}

            # Get forecast details
            details = (
                db.query(m.ForecastDetail)
                .filter(m.ForecastDetail.demand_forecast_id == forecast_id)
                .all()
            )

            if not details:
                return {"error": "No forecast details found"}

            # Get actual sales data
            actual_data = self.get_product_sales_history(
                db, forecast.product_id, days_back=forecast.forecast_horizon_days
            )

            if actual_data.empty:
                return {"error": "No actual sales data available"}

            # Build forecast dataframe from details
            forecast_data = pd.DataFrame(
                [
                    {
                        "date": d.forecast_for_date,
                        "forecast": d.forecasted_quantity,
                    }
                    for d in details
                ]
            )

            # Calculate metrics
            metrics = self.forecaster.get_forecast_metrics(actual_data, forecast_data)

            if "error" in metrics:
                return metrics

            # Update forecast record with metrics
            forecast.mae = metrics.get("mae")
            forecast.rmse = metrics.get("rmse")
            forecast.r2_score = metrics.get("r2")
            forecast.updated_at = datetime.utcnow()

            # Save metrics record
            metric = m.ForecastMetric(
                product_id=forecast.product_id,
                metric_date=datetime.utcnow(),
                model_type=forecast.model_type,
                mae=metrics.get("mae", 0),
                mape=metrics.get("mape"),
                rmse=metrics.get("rmse", 0),
                r2=metrics.get("r2", 0),
                samples_evaluated=metrics.get("samples", 0),
            )
            db.add(metric)
            db.commit()

            return {
                "forecast_id": forecast_id,
                "metrics": metrics,
                "updated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error evaluating forecast: {e}")
            db.rollback()
            return {"error": str(e)}

    def get_forecast_summary(self, db: Session, product_id: int) -> Dict[str, Any]:
        """
        Get summary of latest forecasts for a product.

        Args:
            db: Database session
            product_id: Product ID

        Returns:
            Forecast summary
        """
        try:
            # Get latest forecast
            latest = (
                db.query(m.DemandForecast)
                .filter(m.DemandForecast.product_id == product_id)
                .order_by(m.DemandForecast.created_at.desc())
                .first()
            )

            if not latest:
                return {"error": "No forecasts found for this product"}

            # Get product
            product = db.query(m.Product).filter(m.Product.id == product_id).first()

            # Get forecast details for next 7 days
            next_7_days = datetime.utcnow() + timedelta(days=7)
            details = (
                db.query(m.ForecastDetail)
                .filter(
                    m.ForecastDetail.demand_forecast_id == latest.id,
                    m.ForecastDetail.forecast_for_date <= next_7_days,
                )
                .all()
            )

            return {
                "product_id": product_id,
                "product_name": product.name if product else "Unknown",
                "current_stock": product.quantity if product else 0,
                "latest_forecast_id": latest.id,
                "model_type": latest.model_type,
                "forecast_date": latest.created_at.isoformat(),
                "average_demand": latest.average_demand,
                "mae": latest.mae,
                "rmse": latest.rmse,
                "r2_score": latest.r2_score,
                "next_7_days": [
                    {
                        "date": d.forecast_for_date.date().isoformat(),
                        "forecast": d.forecasted_quantity,
                        "lower_bound": d.lower_bound,
                        "upper_bound": d.upper_bound,
                    }
                    for d in details
                ],
            }

        except Exception as e:
            logger.error(f"Error getting forecast summary: {e}")
            return {"error": str(e)}

    def get_low_stock_alerts(
        self, db: Session, threshold_days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get products that will have low stock based on forecasts.

        Args:
            db: Database session
            threshold_days: Days of stock to consider as low

        Returns:
            List of low stock alerts
        """
        try:
            alerts = []

            # Get all products with forecasts
            products = (
                db.query(m.Product)
                .join(m.DemandForecast, m.Product.id == m.DemandForecast.product_id)
                .filter(m.DemandForecast.is_active == True)
                .distinct()
                .all()
            )

            for product in products:
                # Get latest forecast
                forecast = (
                    db.query(m.DemandForecast)
                    .filter(
                        m.DemandForecast.product_id == product.id,
                        m.DemandForecast.is_active == True,
                    )
                    .order_by(m.DemandForecast.created_at.desc())
                    .first()
                )

                if not forecast:
                    continue

                # Sum forecast for next N days
                threshold_date = datetime.utcnow() + timedelta(days=threshold_days)
                forecasted_demand = (
                    db.query(m.ForecastDetail)
                    .filter(
                        m.ForecastDetail.demand_forecast_id == forecast.id,
                        m.ForecastDetail.forecast_for_date <= threshold_date,
                    )
                    .all()
                )

                total_forecasted = sum(d.forecasted_quantity for d in forecasted_demand)

                # Check if stock will be insufficient
                if product.quantity < total_forecasted:
                    shortage = total_forecasted - product.quantity
                    alerts.append(
                        {
                            "product_id": product.id,
                            "product_name": product.name,
                            "current_stock": product.quantity,
                            "forecasted_demand": total_forecasted,
                            "shortage": shortage,
                            "reorder_recommended": True,
                            "reorder_quantity": int(
                                shortage * 1.5
                            ),  # Reorder 1.5x shortage
                        }
                    )

            return sorted(alerts, key=lambda x: x["shortage"], reverse=True)

        except Exception as e:
            logger.error(f"Error getting low stock alerts: {e}")
            return []

    def update_demand_history(
        self,
        db: Session,
        product_id: int,
        date: datetime,
        quantity: int,
        revenue: float = 0,
    ) -> Dict[str, Any]:
        """
        Update or create demand history record.

        Args:
            db: Database session
            product_id: Product ID
            date: Date of the demand
            quantity: Quantity sold
            revenue: Revenue from the sale

        Returns:
            Result dictionary
        """
        try:
            # Check if record exists
            existing = (
                db.query(m.DemandHistory)
                .filter(
                    m.DemandHistory.product_id == product_id,
                    m.DemandHistory.date == date,
                )
                .first()
            )

            date_obj = pd.to_datetime(date)

            if existing:
                existing.quantity_sold += quantity
                existing.revenue += revenue
                existing.updated_at = datetime.utcnow()
            else:
                history = m.DemandHistory(
                    product_id=product_id,
                    date=date,
                    quantity_sold=quantity,
                    revenue=revenue,
                    day_of_week=date_obj.weekday(),
                    is_weekend=date_obj.weekday() >= 5,
                )
                db.add(history)

            db.commit()
            return {"success": True, "product_id": product_id, "date": str(date)}

        except Exception as e:
            logger.error(f"Error updating demand history: {e}")
            db.rollback()
            return {"error": str(e)}

    def get_product_forecast_comparison(
        self, db: Session, product_id: int, days: int = 30
    ) -> Dict[str, Any]:
        """
        Compare forecast vs actual for a product.

        Args:
            db: Database session
            product_id: Product ID
            days: Number of days to compare

        Returns:
            Comparison data
        """
        try:
            # Get latest forecast
            forecast = (
                db.query(m.DemandForecast)
                .filter(m.DemandForecast.product_id == product_id)
                .order_by(m.DemandForecast.created_at.desc())
                .first()
            )

            if not forecast:
                return {"error": "No forecast found"}

            # Get forecast details
            cutoff_date = datetime.utcnow() + timedelta(days=days)
            details = (
                db.query(m.ForecastDetail)
                .filter(
                    m.ForecastDetail.demand_forecast_id == forecast.id,
                    m.ForecastDetail.forecast_for_date <= cutoff_date,
                )
                .all()
            )

            # Get actual sales
            actual_data = self.get_product_sales_history(db, product_id, days)

            # Build comparison
            comparison: list[dict[str, Any]] = []
            for detail in details:
                actual = 0
                if not actual_data.empty:
                    match = actual_data[
                        actual_data["date"].dt.date == detail.forecast_for_date.date()
                    ]
                    if not match.empty:
                        actual = match["quantity"].iloc[0]

                forecasted_qty = float(detail.forecasted_quantity)
                error = float(actual) - forecasted_qty
                accuracy = 100 - (abs(error) / (forecasted_qty + 0.001)) * 100

                comparison.append(
                    {
                        "date": detail.forecast_for_date.date().isoformat(),
                        "forecasted": forecasted_qty,
                        "actual": actual,
                        "error": error,
                        "accuracy_percent": max(0.0, float(accuracy)),
                    }
                )

            # Calculate average accuracy
            avg_acc = 0.0
            if comparison:
                avg_acc = sum(c["accuracy_percent"] for c in comparison) / len(
                    comparison
                )

            return {
                "product_id": product_id,
                "forecast_id": forecast.id,
                "model_type": forecast.model_type,
                "comparison": comparison,
                "avg_accuracy": avg_acc,
            }

        except Exception as e:
            logger.error(f"Error comparing forecast: {e}")
            return {"error": str(e)}


# Service instance
demand_forecast_service = DemandForecastService()
