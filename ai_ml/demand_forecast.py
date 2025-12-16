# ===========================================
# Vendly POS - AI/ML Demand Forecasting
# Advanced forecasting models for retail
# ===========================================

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

try:
    from prophet import Prophet
except ImportError:
    Prophet = None

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.seasonal import seasonal_decompose
except ImportError:
    ARIMA = None
    seasonal_decompose = None

from .config import ml_config

logger = logging.getLogger(__name__)


class DemandForecaster:
    """
    Advanced demand forecasting using multiple models.
    Combines Prophet, ARIMA, and ensemble methods for accurate predictions.
    """

    MODEL_TYPES = ["prophet", "arima", "ensemble"]

    def __init__(self, config=None):
        self.config = config or ml_config
        self.models = {}
        self.scaler = StandardScaler()
        self.ensemble_feature_columns = []  # Store feature columns for ensemble
        self.model_path = self.config.model_path / "demand_forecaster"
        self.config.ensure_model_dir()
        self.model_path.mkdir(parents=True, exist_ok=True)

    def prepare_data(
        self, sales_data: pd.DataFrame, column_name: str = "quantity"
    ) -> pd.DataFrame:
        """
        Prepare sales data for forecasting.

        Args:
            sales_data: DataFrame with 'date' and quantity columns
            column_name: Name of the column to forecast

        Returns:
            Cleaned and preprocessed DataFrame
        """
        df = sales_data.copy()

        # Ensure date column is datetime
        if "date" not in df.columns:
            raise ValueError("DataFrame must have a 'date' column")

        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

        # Handle missing dates (fill with 0 or interpolate)
        # Select only the columns we need
        df_subset = df[["date", column_name]].copy()
        df_subset = df_subset.set_index("date")
        
        # Reindex to fill missing dates
        date_range = pd.date_range(df_subset.index.min(), df_subset.index.max(), freq="D")
        df_reindexed = df_subset.reindex(date_range)
        df_reindexed[column_name] = df_reindexed[column_name].fillna(0)
        
        # Reset index to get date back as a column
        df_reindexed = df_reindexed.reset_index()
        df_reindexed.columns = ["date", column_name]

        # Remove outliers using IQR
        Q1 = df_reindexed[column_name].quantile(0.25)
        Q3 = df_reindexed[column_name].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outlier_mask = (df_reindexed[column_name] < lower_bound) | (
            df_reindexed[column_name] > upper_bound
        )
        # Replace outliers with median, preserving dtype
        median_val = df_reindexed[column_name].median()
        df_reindexed = df_reindexed.astype({column_name: 'float64'})
        df_reindexed.loc[outlier_mask, column_name] = median_val

        return df_reindexed

    def train_prophet(
        self, sales_data: pd.DataFrame, column_name: str = "quantity"
    ) -> Dict[str, float]:
        """
        Train Facebook Prophet model for time series forecasting.

        Args:
            sales_data: DataFrame with 'date' and quantity columns
            column_name: Name of the column to forecast

        Returns:
            Training metrics
        """
        if Prophet is None:
            logger.warning("Prophet not installed. Skipping Prophet model.")
            return {"error": "Prophet not installed"}

        try:
            df = self.prepare_data(sales_data, column_name)

            # Format for Prophet
            prophet_df = df[["date", column_name]].copy()
            prophet_df.columns = ["ds", "y"]

            # Train Prophet
            model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                interval_width=0.95,
                changepoint_prior_scale=0.05,
                seasonality_prior_scale=10,
            )
            model.fit(prophet_df)

            # Evaluate on validation set
            future = model.make_future_dataframe(periods=len(df) // 4)
            forecast = model.predict(future)

            # Calculate metrics
            validation_start = int(len(df) * 0.75)
            y_true = df[column_name].iloc[validation_start:].values
            y_pred = forecast["yhat"].iloc[validation_start : validation_start + len(y_true)].values

            mae = mean_absolute_error(y_true, y_pred)
            rmse = np.sqrt(mean_squared_error(y_true, y_pred))
            r2 = r2_score(y_true, y_pred)

            # Save model
            self.models["prophet"] = model
            self._save_model("prophet", model)

            metrics = {
                "model_type": "prophet",
                "mae": float(mae),
                "rmse": float(rmse),
                "r2": float(r2),
                "samples_trained": len(df),
                "trained_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"Prophet model trained. Metrics: {metrics}")
            return metrics

        except Exception as e:
            logger.error(f"Error training Prophet model: {e}")
            return {"error": str(e)}

    def train_arima(
        self, sales_data: pd.DataFrame, column_name: str = "quantity", order: Tuple[int, int, int] = (1, 1, 1)
    ) -> Dict[str, float]:
        """
        Train ARIMA model for time series forecasting.

        Args:
            sales_data: DataFrame with 'date' and quantity columns
            column_name: Name of the column to forecast
            order: ARIMA order (p, d, q)

        Returns:
            Training metrics
        """
        if ARIMA is None:
            logger.warning("statsmodels not installed. Skipping ARIMA model.")
            return {"error": "statsmodels not installed"}

        try:
            df = self.prepare_data(sales_data, column_name)

            # Ensure no NaN values
            df = df.dropna()

            if len(df) < 50:
                return {"error": "Insufficient data for ARIMA (need at least 50 samples)"}

            # Split data
            train_size = int(len(df) * 0.8)
            train_data = df[column_name].iloc[:train_size]
            test_data = df[column_name].iloc[train_size:]

            # Train ARIMA
            model = ARIMA(train_data, order=order)
            results = model.fit()

            # Forecast on test set
            forecast = results.get_forecast(steps=len(test_data))
            y_pred = forecast.predicted_mean.values
            y_true = test_data.values

            # Calculate metrics
            mae = mean_absolute_error(y_true, y_pred)
            rmse = np.sqrt(mean_squared_error(y_true, y_pred))
            r2 = r2_score(y_true, y_pred)

            # Save model
            self.models["arima"] = results
            self._save_model("arima", results)

            metrics = {
                "model_type": "arima",
                "order": order,
                "mae": float(mae),
                "rmse": float(rmse),
                "r2": float(r2),
                "samples_trained": len(train_data),
                "samples_tested": len(test_data),
                "trained_at": datetime.utcnow().isoformat(),
            }

            logger.info(f"ARIMA model trained. Metrics: {metrics}")
            return metrics

        except Exception as e:
            logger.error(f"Error training ARIMA model: {e}")
            return {"error": str(e)}

    def train_ensemble(
        self, sales_data: pd.DataFrame, column_name: str = "quantity"
    ) -> Dict[str, float]:
        """
        Train ensemble model combining multiple approaches.

        Args:
            sales_data: DataFrame with 'date' and quantity columns
            column_name: Name of the column to forecast

        Returns:
            Training metrics
        """
        df = self.prepare_data(sales_data, column_name)

        # Extract features
        df["day_of_week"] = df["date"].dt.dayofweek
        df["month"] = df["date"].dt.month
        df["day_of_month"] = df["date"].dt.day
        df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)

        # Lag features
        for lag in [1, 7, 14, 30]:
            df[f"lag_{lag}"] = df[column_name].shift(lag)

        # Rolling statistics
        for window in [7, 14]:
            df[f"rolling_mean_{window}"] = df[column_name].rolling(window).mean()
            df[f"rolling_std_{window}"] = df[column_name].rolling(window).std()

        # Drop NaN
        df = df.dropna()

        if len(df) < 50:
            return {"error": "Insufficient data for ensemble model"}

        # Prepare features
        feature_cols = [col for col in df.columns if col not in ["date", column_name]]
        self.ensemble_feature_columns = feature_cols  # Store for later use
        X = df[feature_cols].values
        y = df[column_name].values

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Train multiple models and average
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
        from sklearn.linear_model import Ridge

        models_ensemble = {
            "rf": RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
            "gb": GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42),
            "ridge": Ridge(alpha=1.0),
        }

        train_size = int(len(X_scaled) * 0.8)
        X_train, X_test = X_scaled[:train_size], X_scaled[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]

        predictions = {}
        scores = {}

        for name, model in models_ensemble.items():
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            predictions[name] = y_pred
            scores[name] = {"mae": mae, "rmse": rmse, "r2": r2}

        # Save ensemble
        ensemble_data = {
            "models": models_ensemble,
            "scaler": self.scaler,
            "feature_columns": feature_cols,
            "trained_at": datetime.utcnow().isoformat(),
        }
        self.models["ensemble"] = ensemble_data
        self._save_model("ensemble", ensemble_data)

        # Average R2 score
        avg_r2 = np.mean([s["r2"] for s in scores.values()])
        avg_mae = np.mean([s["mae"] for s in scores.values()])
        avg_rmse = np.mean([s["rmse"] for s in scores.values()])

        metrics = {
            "model_type": "ensemble",
            "mae": float(avg_mae),
            "rmse": float(avg_rmse),
            "r2": float(avg_r2),
            "samples_trained": len(X_train),
            "samples_tested": len(X_test),
            "component_scores": scores,
            "trained_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Ensemble model trained. Metrics: {metrics}")
        return metrics

    def forecast(
        self, 
        sales_data: pd.DataFrame, 
        days_ahead: int = 30, 
        model_type: str = "ensemble",
        column_name: str = "quantity"
    ) -> Dict[str, Any]:
        """
        Generate demand forecast for future days.

        Args:
            sales_data: Historical sales data
            days_ahead: Number of days to forecast
            model_type: Type of model to use ('prophet', 'arima', 'ensemble')
            column_name: Column to forecast

        Returns:
            Dictionary with forecast results
        """
        if model_type not in self.MODEL_TYPES:
            return {"error": f"Model type must be one of {self.MODEL_TYPES}"}

        try:
            if model_type == "prophet":
                return self._forecast_prophet(sales_data, days_ahead, column_name)
            elif model_type == "arima":
                return self._forecast_arima(sales_data, days_ahead, column_name)
            else:  # ensemble
                return self._forecast_ensemble(sales_data, days_ahead, column_name)
        except Exception as e:
            logger.error(f"Forecasting error: {e}")
            return {"error": str(e)}

    def _forecast_prophet(
        self, sales_data: pd.DataFrame, days_ahead: int, column_name: str
    ) -> Dict[str, Any]:
        """Forecast using Prophet model."""
        if Prophet is None:
            return {"error": "Prophet not installed"}

        df = self.prepare_data(sales_data, column_name)
        prophet_df = df[["date", column_name]].copy()
        prophet_df.columns = ["ds", "y"]

        model = Prophet(yearly_seasonality=True, weekly_seasonality=True)
        model.fit(prophet_df)

        future = model.make_future_dataframe(periods=days_ahead)
        forecast = model.predict(future)

        # Extract forecast for future days only
        future_forecast = forecast.tail(days_ahead)[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
        future_forecast.columns = ["date", "forecast", "lower_bound", "upper_bound"]
        future_forecast["forecast"] = future_forecast["forecast"].clip(lower=0)
        future_forecast["lower_bound"] = future_forecast["lower_bound"].clip(lower=0)

        return {
            "model_type": "prophet",
            "forecast_horizon": days_ahead,
            "forecast": future_forecast.to_dict(orient="records"),
            "average_demand": float(future_forecast["forecast"].mean()),
            "confidence_level": 0.95,
        }

    def _forecast_arima(
        self, sales_data: pd.DataFrame, days_ahead: int, column_name: str
    ) -> Dict[str, Any]:
        """Forecast using ARIMA model."""
        if ARIMA is None:
            return {"error": "statsmodels not installed"}

        df = self.prepare_data(sales_data, column_name)

        if len(df) < 50:
            return {"error": "Insufficient data for ARIMA forecasting"}

        # Train on all data
        model = ARIMA(df[column_name], order=(1, 1, 1))
        results = model.fit()

        # Forecast
        forecast = results.get_forecast(steps=days_ahead)
        forecast_df = forecast.summary_frame()

        # Prepare results
        future_dates = pd.date_range(
            start=df["date"].max() + timedelta(days=1), periods=days_ahead, freq="D"
        )

        results_list = []
        for i, date in enumerate(future_dates):
            results_list.append({
                "date": date,
                "forecast": max(0, forecast_df["mean"].iloc[i]),
                "lower_bound": max(0, forecast_df["mean_ci_lower"].iloc[i]),
                "upper_bound": forecast_df["mean_ci_upper"].iloc[i],
            })

        return {
            "model_type": "arima",
            "forecast_horizon": days_ahead,
            "forecast": results_list,
            "average_demand": float(np.mean([r["forecast"] for r in results_list])),
            "confidence_level": 0.95,
        }

    def _forecast_ensemble(
        self, sales_data: pd.DataFrame, days_ahead: int, column_name: str
    ) -> Dict[str, Any]:
        """Forecast using ensemble model."""
        df = self.prepare_data(sales_data, column_name)

        # For ensemble, use simple moving average + trend
        ma_7 = df[column_name].rolling(window=7).mean().iloc[-1]
        ma_30 = df[column_name].rolling(window=30).mean().iloc[-1]
        
        trend = (ma_7 - ma_30) / ma_30 if ma_30 > 0 else 0

        forecast_values = []
        base_forecast = ma_7

        future_dates = pd.date_range(
            start=df["date"].max() + timedelta(days=1), periods=days_ahead, freq="D"
        )

        for i, date in enumerate(future_dates):
            # Simple trend-adjusted forecast
            trend_adjustment = 1 + (trend * (i / days_ahead))
            forecast_val = max(0, base_forecast * trend_adjustment)
            
            # Confidence bounds (±20%)
            lower = forecast_val * 0.8
            upper = forecast_val * 1.2

            forecast_values.append({
                "date": date,
                "forecast": float(forecast_val),
                "lower_bound": float(lower),
                "upper_bound": float(upper),
            })

        return {
            "model_type": "ensemble",
            "forecast_horizon": days_ahead,
            "forecast": forecast_values,
            "average_demand": float(np.mean([v["forecast"] for v in forecast_values])),
            "confidence_level": 0.90,
        }

    def get_forecast_metrics(
        self, actual_data: pd.DataFrame, forecast_data: pd.DataFrame, column_name: str = "quantity"
    ) -> Dict[str, float]:
        """
        Calculate metrics comparing forecast to actual data.

        Args:
            actual_data: Actual sales data
            forecast_data: Forecasted data
            column_name: Column name to compare

        Returns:
            Dictionary with performance metrics
        """
        # Align data by date
        actual_data = actual_data.copy()
        actual_data["date"] = pd.to_datetime(actual_data["date"])
        forecast_data = forecast_data.copy()
        forecast_data["date"] = pd.to_datetime(forecast_data["date"])

        merged = pd.merge(
            actual_data[["date", column_name]],
            forecast_data[["date", "forecast"]],
            on="date",
            how="inner",
        )

        if len(merged) == 0:
            return {"error": "No overlapping dates between actual and forecast"}

        y_true = merged[column_name].values
        y_pred = merged["forecast"].values

        mae = mean_absolute_error(y_true, y_pred)
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100 if np.all(y_true > 0) else None
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)

        return {
            "mae": float(mae),
            "mape": float(mape) if mape else None,
            "rmse": float(rmse),
            "r2": float(r2),
            "samples": len(merged),
        }

    def _save_model(self, model_type: str, model: Any):
        """Save model to disk."""
        model_file = self.model_path / f"{model_type}_model.joblib"
        joblib.dump(model, model_file)
        logger.info(f"Model {model_type} saved to {model_file}")

    def _load_model(self, model_type: str) -> Optional[Any]:
        """Load model from disk."""
        model_file = self.model_path / f"{model_type}_model.joblib"
        if model_file.exists():
            return joblib.load(model_file)
        return None

    def load_all_models(self):
        """Load all available models from disk."""
        for model_type in self.MODEL_TYPES:
            model = self._load_model(model_type)
            if model:
                self.models[model_type] = model
                logger.info(f"Loaded {model_type} model from disk")
