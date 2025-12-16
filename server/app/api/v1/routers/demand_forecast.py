# ===========================================
# Vendly POS - Demand Forecasting API
# REST endpoints for demand forecasting
# ===========================================

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.db import models as m
from app.services.demand_forecast_service import demand_forecast_service

router = APIRouter(prefix="/demand-forecast", tags=["Demand Forecasting"])


# ==================== Schemas ====================


class ForecastDetailOut(BaseModel):
    date: str = Field(..., description="Forecast date")
    forecast: float = Field(..., description="Forecasted quantity")
    lower_bound: Optional[float] = Field(
        None, description="Lower bound (confidence interval)"
    )
    upper_bound: Optional[float] = Field(
        None, description="Upper bound (confidence interval)"
    )


class GenerateForecastRequest(BaseModel):
    product_id: int = Field(..., description="Product ID to forecast")
    days_ahead: int = Field(
        default=30, ge=1, le=365, description="Number of days to forecast"
    )
    model_type: str = Field(
        default="ensemble", description="Model type: prophet, arima, ensemble"
    )


class GenerateForecastResponse(BaseModel):
    forecast_id: int
    product_id: int
    product_name: str
    model_type: str
    forecast_horizon: int
    average_demand: float
    forecast: List[ForecastDetailOut]
    created_at: str


class TrainModelRequest(BaseModel):
    product_id: int = Field(..., description="Product ID to train on")
    model_type: str = Field(default="ensemble", description="Model type to train")


class TrainModelResponse(BaseModel):
    product_id: int
    product_name: str
    model_type: str
    metrics: dict
    trained_at: str


class ForecastMetricsOut(BaseModel):
    mae: float = Field(..., description="Mean Absolute Error")
    mape: Optional[float] = Field(None, description="Mean Absolute Percentage Error")
    rmse: float = Field(..., description="Root Mean Squared Error")
    r2: float = Field(..., description="R² Score")
    samples: int = Field(..., description="Number of samples evaluated")


class ForecastSummaryOut(BaseModel):
    product_id: int
    product_name: str
    current_stock: int
    latest_forecast_id: int
    model_type: str
    forecast_date: str
    average_demand: float
    mae: Optional[float]
    rmse: Optional[float]
    r2_score: Optional[float]
    next_7_days: List[ForecastDetailOut]


class LowStockAlert(BaseModel):
    product_id: int
    product_name: str
    current_stock: int
    forecasted_demand: float
    shortage: float
    reorder_recommended: bool
    reorder_quantity: int


class ForecastComparisonOut(BaseModel):
    date: str
    forecasted: float
    actual: float
    error: float
    accuracy_percent: float


class ProductForecastComparison(BaseModel):
    product_id: int
    forecast_id: int
    model_type: str
    comparison: List[ForecastComparisonOut]
    avg_accuracy: float


class EvaluateForecastResponse(BaseModel):
    forecast_id: int
    metrics: ForecastMetricsOut
    updated_at: str


# ==================== Endpoints ====================


@router.post("/train-model", response_model=TrainModelResponse)
def train_model(
    request: TrainModelRequest,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """
    Train a demand forecast model for a product.

    - **product_id**: Product to train model on
    - **model_type**: Type of model (prophet, arima, ensemble)
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can train models")

    result = demand_forecast_service.train_forecast_model(
        db, request.product_id, request.model_type, current_user.id
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/generate", response_model=GenerateForecastResponse)
def generate_forecast(
    request: GenerateForecastRequest,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """
    Generate demand forecast for a product.

    - **product_id**: Product to forecast
    - **days_ahead**: Number of days to forecast (default: 30)
    - **model_type**: Forecasting model to use (default: ensemble)
    """
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    result = demand_forecast_service.generate_forecast(
        db, request.product_id, request.days_ahead, request.model_type, current_user.id
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/summary/{product_id}", response_model=ForecastSummaryOut)
def get_forecast_summary(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """
    Get summary of latest forecast for a product.

    - **product_id**: Product ID to get forecast summary
    """
    result = demand_forecast_service.get_forecast_summary(db, product_id)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/low-stock-alerts", response_model=List[LowStockAlert])
def get_low_stock_alerts(
    threshold_days: int = Query(
        default=7, ge=1, le=90, description="Days of stock to consider low"
    ),
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """
    Get products that will have low stock based on forecasts.

    - **threshold_days**: Number of days to look ahead for low stock warnings
    """
    alerts = demand_forecast_service.get_low_stock_alerts(db, threshold_days)
    return alerts


@router.post("/evaluate/{forecast_id}", response_model=EvaluateForecastResponse)
def evaluate_forecast(
    forecast_id: int,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """
    Evaluate forecast accuracy against actual sales data.

    - **forecast_id**: Forecast ID to evaluate
    """
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    result = demand_forecast_service.evaluate_forecast(db, forecast_id)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.get("/comparison/{product_id}", response_model=ProductForecastComparison)
def get_forecast_comparison(
    product_id: int,
    days: int = Query(
        default=30, ge=1, le=365, description="Number of days to compare"
    ),
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """
    Get forecast vs actual comparison for a product.

    - **product_id**: Product ID to compare
    - **days**: Number of days to include in comparison
    """
    result = demand_forecast_service.get_product_forecast_comparison(
        db, product_id, days
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result


@router.get("/list-by-product/{product_id}")
def list_forecasts_by_product(
    product_id: int,
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """
    List all forecasts for a product.

    - **product_id**: Product ID
    - **limit**: Maximum number of forecasts to return
    """
    forecasts = (
        db.query(m.DemandForecast)
        .filter(m.DemandForecast.product_id == product_id)
        .order_by(m.DemandForecast.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": f.id,
            "product_id": f.product_id,
            "forecast_date": f.forecast_date.isoformat(),
            "model_type": f.model_type,
            "average_demand": f.average_demand,
            "mae": f.mae,
            "rmse": f.rmse,
            "r2_score": f.r2_score,
            "created_at": f.created_at.isoformat(),
            "is_active": f.is_active,
        }
        for f in forecasts
    ]


@router.get("/forecast-details/{forecast_id}")
def get_forecast_details(
    forecast_id: int,
    limit: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """
    Get detailed forecast for specific days.

    - **forecast_id**: Forecast ID
    - **limit**: Maximum days to return
    """
    forecast = (
        db.query(m.DemandForecast).filter(m.DemandForecast.id == forecast_id).first()
    )

    if not forecast:
        raise HTTPException(status_code=404, detail="Forecast not found")

    details = (
        db.query(m.ForecastDetail)
        .filter(m.ForecastDetail.demand_forecast_id == forecast_id)
        .order_by(m.ForecastDetail.forecast_for_date)
        .limit(limit)
        .all()
    )

    return {
        "forecast_id": forecast_id,
        "product_id": forecast.product_id,
        "model_type": forecast.model_type,
        "created_at": forecast.created_at.isoformat(),
        "details": [
            {
                "date": d.forecast_for_date.date().isoformat(),
                "forecasted_quantity": d.forecasted_quantity,
                "lower_bound": d.lower_bound,
                "upper_bound": d.upper_bound,
                "actual_quantity": d.actual_quantity,
                "error": d.error,
            }
            for d in details
        ],
    }


@router.get("/metrics/{product_id}")
def get_forecast_metrics(
    product_id: int,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    """
    Get forecast performance metrics for a product.

    - **product_id**: Product ID
    - **days**: Time period for metrics
    """
    metrics = (
        db.query(m.ForecastMetric)
        .filter(m.ForecastMetric.product_id == product_id)
        .order_by(m.ForecastMetric.metric_date.desc())
        .limit(days)
        .all()
    )

    return {
        "product_id": product_id,
        "metrics": [
            {
                "date": m.metric_date.date().isoformat(),
                "model_type": m.model_type,
                "mae": float(m.mae),
                "mape": float(m.mape) if m.mape else None,
                "rmse": float(m.rmse),
                "r2": float(m.r2),
                "samples_evaluated": m.samples_evaluated,
            }
            for m in metrics
        ],
    }
