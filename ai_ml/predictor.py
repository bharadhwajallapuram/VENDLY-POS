# ===========================================
# Vendly POS - AI/ML Prediction Models
# Sales Forecasting & Inventory Optimization
# ===========================================

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler

from .config import ml_config

logger = logging.getLogger(__name__)


class SalesPredictor:
    """
    Sales forecasting model using time series analysis and ML.
    Predicts future sales based on historical data and patterns.
    """
    
    def __init__(self, config=None):
        self.config = config or ml_config
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = []
        self.model_path = self.config.model_path / "sales_predictor.joblib"
        
    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for the model"""
        df = df.copy()
        
        # Time-based features
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_of_month'] = df['date'].dt.day
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['is_month_start'] = df['date'].dt.is_month_start.astype(int)
        df['is_month_end'] = df['date'].dt.is_month_end.astype(int)
        
        # Lag features
        for lag in [1, 7, 14, 30]:
            if 'sales_amount' in df.columns:
                df[f'sales_lag_{lag}'] = df['sales_amount'].shift(lag)
        
        # Rolling features
        for window in [7, 14, 30]:
            if 'sales_amount' in df.columns:
                df[f'sales_rolling_mean_{window}'] = df['sales_amount'].rolling(window).mean()
                df[f'sales_rolling_std_{window}'] = df['sales_amount'].rolling(window).std()
        
        return df.dropna()
    
    def train(self, sales_data: pd.DataFrame) -> Dict[str, float]:
        """
        Train the sales prediction model.
        
        Args:
            sales_data: DataFrame with 'date' and 'sales_amount' columns
            
        Returns:
            Training metrics dictionary
        """
        if len(sales_data) < self.config.min_training_samples:
            raise ValueError(
                f"Insufficient data: {len(sales_data)} samples. "
                f"Minimum required: {self.config.min_training_samples}"
            )
        
        # Prepare features
        df = self._prepare_features(sales_data)
        
        self.feature_columns = [
            col for col in df.columns 
            if col not in ['date', 'sales_amount', 'sale_id']
        ]
        
        X = df[self.feature_columns]
        y = df['sales_amount']
        
        # Split data
        split_idx = int(len(X) * (1 - self.config.validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Train model
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train_scaled, y_train)
        val_score = self.model.score(X_val_scaled, y_val)
        
        # Save model
        self._save_model()
        
        return {
            'train_r2': train_score,
            'validation_r2': val_score,
            'samples_trained': len(X_train),
            'samples_validated': len(X_val),
            'feature_count': len(self.feature_columns)
        }
    
    def predict(
        self,
        historical_data: pd.DataFrame,
        horizon_days: int = None
    ) -> pd.DataFrame:
        """
        Predict future sales.
        
        Args:
            historical_data: Recent historical sales data
            horizon_days: Number of days to forecast
            
        Returns:
            DataFrame with date and predicted sales
        """
        if self.model is None:
            self._load_model()
        
        horizon = horizon_days or self.config.forecast_horizon_days
        
        # Generate future dates
        last_date = historical_data['date'].max()
        future_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=horizon,
            freq='D'
        )
        
        predictions = []
        current_data = historical_data.copy()
        
        for future_date in future_dates:
            # Create a row for the future date
            future_row = pd.DataFrame({'date': [future_date]})
            
            # Use last known sales as placeholder
            future_row['sales_amount'] = current_data['sales_amount'].iloc[-1]
            
            # Append to current data
            temp_data = pd.concat([current_data, future_row], ignore_index=True)
            temp_data = self._prepare_features(temp_data)
            
            if len(temp_data) > 0:
                X = temp_data[self.feature_columns].iloc[-1:]
                X_scaled = self.scaler.transform(X)
                pred = self.model.predict(X_scaled)[0]
                
                predictions.append({
                    'date': future_date,
                    'predicted_sales': max(0, pred),
                    'confidence': self.config.prediction_threshold
                })
                
                # Update current data with prediction
                future_row['sales_amount'] = pred
                current_data = pd.concat([current_data, future_row], ignore_index=True)
        
        return pd.DataFrame(predictions)
    
    def _save_model(self):
        """Save model to disk"""
        self.config.ensure_model_dir()
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'trained_at': datetime.utcnow().isoformat()
        }
        joblib.dump(model_data, self.model_path)
        logger.info(f"Model saved to {self.model_path}")
    
    def _load_model(self):
        """Load model from disk"""
        if self.model_path.exists():
            model_data = joblib.load(self.model_path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            logger.info(f"Model loaded from {self.model_path}")
        else:
            raise FileNotFoundError(f"No trained model found at {self.model_path}")


class InventoryOptimizer:
    """
    Inventory optimization model.
    Calculates optimal reorder points and quantities.
    """
    
    def __init__(self, config=None):
        self.config = config or ml_config
        self.anomaly_detector = None
    
    def calculate_reorder_point(
        self,
        daily_demand_avg: float,
        daily_demand_std: float,
        lead_time_days: int = None
    ) -> int:
        """
        Calculate reorder point using safety stock methodology.
        
        Args:
            daily_demand_avg: Average daily demand
            daily_demand_std: Standard deviation of daily demand
            lead_time_days: Lead time in days
            
        Returns:
            Reorder point (quantity)
        """
        lead_time = lead_time_days or self.config.lead_time_days
        safety_days = self.config.safety_stock_days
        
        # Calculate safety stock using normal distribution
        # Z-score for 95% service level is approximately 1.645
        from scipy import stats
        z_score = stats.norm.ppf(self.config.service_level)
        
        safety_stock = z_score * daily_demand_std * np.sqrt(lead_time)
        reorder_point = (daily_demand_avg * lead_time) + safety_stock
        
        return int(np.ceil(reorder_point))
    
    def calculate_eoq(
        self,
        annual_demand: float,
        ordering_cost: float,
        holding_cost_per_unit: float
    ) -> int:
        """
        Calculate Economic Order Quantity (EOQ).
        
        Args:
            annual_demand: Annual demand quantity
            ordering_cost: Cost per order
            holding_cost_per_unit: Annual holding cost per unit
            
        Returns:
            Economic order quantity
        """
        eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost_per_unit)
        return int(np.ceil(eoq))
    
    def analyze_product(
        self,
        sales_history: pd.DataFrame,
        current_stock: int,
        unit_cost: float = 10.0,
        ordering_cost: float = 50.0
    ) -> Dict[str, Any]:
        """
        Analyze a product's inventory status and provide recommendations.
        
        Args:
            sales_history: DataFrame with daily sales data
            current_stock: Current stock level
            unit_cost: Cost per unit
            ordering_cost: Cost per order
            
        Returns:
            Analysis results with recommendations
        """
        if len(sales_history) < 7:
            return {"error": "Insufficient sales history"}
        
        # Calculate demand statistics
        daily_demand = sales_history['quantity'].values
        demand_avg = np.mean(daily_demand)
        demand_std = np.std(daily_demand)
        
        # Calculate reorder point
        reorder_point = self.calculate_reorder_point(demand_avg, demand_std)
        
        # Calculate EOQ
        annual_demand = demand_avg * 365
        holding_cost = unit_cost * 0.2  # 20% holding cost
        eoq = self.calculate_eoq(annual_demand, ordering_cost, holding_cost)
        
        # Days until stockout
        days_of_stock = int(current_stock / demand_avg) if demand_avg > 0 else float('inf')
        
        # Recommendation
        needs_reorder = current_stock <= reorder_point
        
        return {
            'current_stock': current_stock,
            'reorder_point': reorder_point,
            'economic_order_quantity': eoq,
            'days_of_stock': days_of_stock,
            'daily_demand_avg': round(demand_avg, 2),
            'daily_demand_std': round(demand_std, 2),
            'needs_reorder': needs_reorder,
            'recommendation': (
                f"REORDER: Order {eoq} units immediately" 
                if needs_reorder 
                else f"OK: {days_of_stock} days of stock remaining"
            )
        }
    
    def detect_anomalies(
        self,
        sales_data: pd.DataFrame,
        contamination: float = 0.1
    ) -> pd.DataFrame:
        """
        Detect anomalies in sales data using Isolation Forest.
        
        Args:
            sales_data: DataFrame with sales data
            contamination: Expected proportion of outliers
            
        Returns:
            DataFrame with anomaly labels
        """
        if self.anomaly_detector is None:
            self.anomaly_detector = IsolationForest(
                contamination=contamination,
                random_state=42
            )
        
        features = sales_data[['quantity', 'amount']].values
        labels = self.anomaly_detector.fit_predict(features)
        
        result = sales_data.copy()
        result['is_anomaly'] = labels == -1
        result['anomaly_score'] = self.anomaly_detector.decision_function(features)
        
        return result
