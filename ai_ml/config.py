# ===========================================
# Vendly POS - AI/ML Configuration
# ===========================================

import os
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class MLConfig:
    """Machine Learning configuration settings"""
    
    # Model storage paths
    model_path: Path = field(
        default_factory=lambda: Path(os.getenv("ML_MODEL_PATH", "./ai_ml/models"))
    )
    
    # Feature flags
    enable_predictions: bool = field(
        default_factory=lambda: os.getenv("ENABLE_PREDICTIONS", "true").lower() == "true"
    )
    enable_recommendations: bool = field(
        default_factory=lambda: os.getenv("ENABLE_RECOMMENDATIONS", "true").lower() == "true"
    )
    enable_anomaly_detection: bool = field(
        default_factory=lambda: os.getenv("ENABLE_ANOMALY_DETECTION", "true").lower() == "true"
    )
    
    # Prediction thresholds
    prediction_threshold: float = field(
        default_factory=lambda: float(os.getenv("PREDICTION_THRESHOLD", "0.8"))
    )
    anomaly_threshold: float = field(
        default_factory=lambda: float(os.getenv("ANOMALY_THRESHOLD", "2.5"))
    )
    
    # Model training settings
    min_training_samples: int = 100
    retrain_interval_days: int = 7
    validation_split: float = 0.2
    
    # Sales forecasting settings
    forecast_horizon_days: int = 30
    seasonality_mode: str = "multiplicative"
    include_holidays: bool = True
    
    # Inventory optimization settings
    safety_stock_days: int = 3
    lead_time_days: int = 5
    service_level: float = 0.95
    
    # Database connection
    database_url: Optional[str] = field(
        default_factory=lambda: os.getenv("DATABASE_URL")
    )
    
    def ensure_model_dir(self):
        """Ensure model directory exists"""
        self.model_path.mkdir(parents=True, exist_ok=True)
        return self.model_path


# Default configuration instance
ml_config = MLConfig()
