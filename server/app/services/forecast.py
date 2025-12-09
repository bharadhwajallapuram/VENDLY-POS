"""
Sales Forecasting Service (Moving Average Example)
"""

from datetime import datetime, timedelta
from typing import List

import pandas as pd

# Dummy function to simulate sales history retrieval from DB
# Replace with real DB query in production


def get_sales_history(product_id: int, days: int = 60):
    today = datetime.today()
    dates = [today - timedelta(days=i) for i in range(days)]
    sales = [100 + (i % 7) * 5 for i in range(days)]  # Simulate weekly seasonality
    df = pd.DataFrame({"date": dates, "sales": sales})
    df = df.sort_values("date")
    return df


def moving_average_forecast(product_id: int, forecast_days: int = 7, window: int = 7):
    df = get_sales_history(product_id, days=60)
    # Use rolling mean as forecast
    avg = df["sales"].rolling(window=window).mean().iloc[-1]
    today = df["date"].iloc[-1]
    forecast_dates = [today + timedelta(days=i) for i in range(1, forecast_days + 1)]
    forecast_sales = [float(avg)] * forecast_days
    return [d.strftime("%Y-%m-%d") for d in forecast_dates], forecast_sales
