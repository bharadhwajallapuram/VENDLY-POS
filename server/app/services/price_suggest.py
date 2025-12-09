import random
from typing import List, Optional


def suggest_price(
    product_id: int, recent_prices: Optional[List[float]] = None
) -> float:
    """
    Suggest a price for a product based on recent prices (mean + random noise for demo).
    """
    if not recent_prices:
        # Fallback: use a default price range
        base_price = 100.0 + product_id % 10 * 5
    else:
        base_price = sum(recent_prices) / len(recent_prices)
    # Add small randomization for demo
    return round(base_price * (1 + random.uniform(-0.05, 0.05)), 2)
