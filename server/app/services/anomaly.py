import pandas as pd
from typing import List, Dict, Any

def detect_anomalies(sales_data: List[Dict[str, Any]], method: str = "zscore", threshold: float = 2.0) -> List[Dict[str, Any]]:
    """
    Detect anomalies in sales data using z-score method.
    sales_data: List of dicts with at least 'date' and 'sales' keys.
    Returns list of anomalies (dicts with date, sales, zscore).
    """
    if not sales_data:
        return []
    df = pd.DataFrame(sales_data)
    if 'sales' not in df.columns:
        return []
    df['zscore'] = (df['sales'] - df['sales'].mean()) / df['sales'].std(ddof=0)
    anomalies = df[df['zscore'].abs() > threshold]
    return anomalies.to_dict(orient='records')
