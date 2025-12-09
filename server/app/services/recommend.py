import random
from typing import List


def recommend_products(customer_id: int, n: int = 3) -> List[int]:
    """
    Recommend n product IDs for a customer.
    For demo: returns random product IDs from 1 to 20.
    """
    product_pool = list(range(1, 21))
    return random.sample(product_pool, min(n, len(product_pool)))
