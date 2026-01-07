"""
Vendly POS - Cache Configuration and Service
=============================================
TTL-based caching for different data types with Redis backend

Cache TTL Configuration:
- Product catalog: 10-30 min (relatively static data)
- Price: 10-60 sec (needs quick refresh for dynamic pricing)
- Inventory: 5-15 sec (near real-time accuracy needed)
- User session: 15-30 min (session-based caching)
- Reports: 1-5 min (can be slightly stale)
"""

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union

from app.core.config import settings
from app.core.redis_client import get_token_store

logger = logging.getLogger(__name__)

# Type variable for generic cache functions
T = TypeVar("T")


class CachePrefix(str, Enum):
    """Cache key prefixes for different data types"""

    PRODUCT_CATALOG = "product:catalog"
    PRODUCT_DETAIL = "product:detail"
    PRODUCT_LIST = "product:list"
    PRODUCT_CATEGORY = "product:category"

    PRICE = "price"
    PRICE_PRODUCT = "price:product"
    PRICE_CATEGORY = "price:category"

    INVENTORY = "inventory"
    INVENTORY_PRODUCT = "inventory:product"
    INVENTORY_LOW_STOCK = "inventory:low_stock"
    INVENTORY_OUT_OF_STOCK = "inventory:out_of_stock"

    SESSION = "session"
    SESSION_USER = "session:user"
    SESSION_TOKEN = "session:token"

    REPORT = "report"
    REPORT_SALES = "report:sales"
    REPORT_INVENTORY = "report:inventory"
    REPORT_EOD = "report:eod"
    REPORT_ANALYTICS = "report:analytics"


@dataclass
class CacheTTL:
    """
    TTL configuration for different data types (in seconds)

    Each data type has a default and max TTL to allow flexibility
    while ensuring reasonable bounds.
    """

    # Product Catalog: 10-30 minutes (relatively static)
    PRODUCT_CATALOG_DEFAULT: int = 600  # 10 minutes
    PRODUCT_CATALOG_MAX: int = 1800  # 30 minutes
    PRODUCT_CATALOG_MIN: int = 300  # 5 minutes

    # Product Detail: 15 minutes (individual product info)
    PRODUCT_DETAIL_DEFAULT: int = 900  # 15 minutes

    # Price: 10-60 seconds (needs quick refresh)
    PRICE_DEFAULT: int = 30  # 30 seconds
    PRICE_MAX: int = 60  # 60 seconds
    PRICE_MIN: int = 10  # 10 seconds

    # Inventory: 5-15 seconds (near real-time)
    INVENTORY_DEFAULT: int = 10  # 10 seconds
    INVENTORY_MAX: int = 15  # 15 seconds
    INVENTORY_MIN: int = 5  # 5 seconds

    # User Session: 15-30 minutes
    SESSION_DEFAULT: int = 900  # 15 minutes (aligned with settings)
    SESSION_MAX: int = 1800  # 30 minutes
    SESSION_MIN: int = 600  # 10 minutes

    # Reports: 1-5 minutes
    REPORT_DEFAULT: int = 120  # 2 minutes
    REPORT_MAX: int = 300  # 5 minutes
    REPORT_MIN: int = 60  # 1 minute

    # Analytics/Dashboard: 3 minutes
    ANALYTICS_DEFAULT: int = 180  # 3 minutes


# Singleton TTL config instance
TTL = CacheTTL()


class CacheService:
    """
    Centralized caching service with data-type specific methods

    Provides type-safe caching with automatic TTL management
    and cache key generation.
    """

    def __init__(self):
        self._store = get_token_store()

    def _generate_key(self, prefix: CachePrefix, *args: Any) -> str:
        """Generate a cache key with prefix and arguments"""
        key_parts = [prefix.value]
        for arg in args:
            if isinstance(arg, (dict, list)):
                # Hash complex objects
                key_parts.append(
                    hashlib.md5(
                        json.dumps(arg, sort_keys=True, default=str).encode()
                    ).hexdigest()[:12]
                )
            else:
                key_parts.append(str(arg))
        return ":".join(key_parts)

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            return self._store.get(key)
        except Exception as e:
            logger.error(f"Cache GET error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in cache with TTL"""
        try:
            return self._store.set(key, value, ttl)
        except Exception as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            return self._store.delete(key)
        except Exception as e:
            logger.error(f"Cache DELETE error for key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return self._store.exists(key)
        except Exception as e:
            logger.error(f"Cache EXISTS error for key {key}: {e}")
            return False

    def invalidate_pattern(self, pattern: CachePrefix) -> int:
        """
        Invalidate all keys matching a pattern prefix

        Note: This is a basic implementation. For production,
        consider using Redis SCAN for large datasets.
        """
        # This would need Redis SCAN implementation
        # For now, log the intent
        logger.info(f"Cache invalidation requested for pattern: {pattern.value}")
        return 0

    # ========================
    # Product Catalog Caching
    # ========================

    def get_product_catalog(
        self,
        page: int = 1,
        limit: int = 50,
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Optional[Dict]:
        """Get cached product catalog"""
        key = self._generate_key(
            CachePrefix.PRODUCT_CATALOG, page, limit, category or "", search or ""
        )
        return self.get(key)

    def set_product_catalog(
        self,
        data: Any,
        page: int = 1,
        limit: int = 50,
        category: Optional[str] = None,
        search: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache product catalog"""
        key = self._generate_key(
            CachePrefix.PRODUCT_CATALOG, page, limit, category or "", search or ""
        )
        return self.set(key, data, ttl or TTL.PRODUCT_CATALOG_DEFAULT)

    def get_product(self, product_id: int) -> Optional[Dict]:
        """Get cached product detail"""
        key = self._generate_key(CachePrefix.PRODUCT_DETAIL, product_id)
        return self.get(key)

    def set_product(
        self,
        product_id: int,
        data: Dict,
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache product detail"""
        key = self._generate_key(CachePrefix.PRODUCT_DETAIL, product_id)
        return self.set(key, data, ttl or TTL.PRODUCT_DETAIL_DEFAULT)

    def invalidate_product(self, product_id: int) -> bool:
        """Invalidate product cache"""
        key = self._generate_key(CachePrefix.PRODUCT_DETAIL, product_id)
        return self.delete(key)

    def get_products_by_category(self, category_id: int) -> Optional[List[Dict]]:
        """Get cached products by category"""
        key = self._generate_key(CachePrefix.PRODUCT_CATEGORY, category_id)
        return self.get(key)

    def set_products_by_category(
        self,
        category_id: int,
        data: List[Dict],
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache products by category"""
        key = self._generate_key(CachePrefix.PRODUCT_CATEGORY, category_id)
        return self.set(key, data, ttl or TTL.PRODUCT_CATALOG_DEFAULT)

    # ========================
    # Price Caching
    # ========================

    def get_price(self, product_id: int) -> Optional[Dict]:
        """Get cached product price"""
        key = self._generate_key(CachePrefix.PRICE_PRODUCT, product_id)
        return self.get(key)

    def set_price(
        self,
        product_id: int,
        data: Dict,
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache product price with short TTL"""
        key = self._generate_key(CachePrefix.PRICE_PRODUCT, product_id)
        return self.set(key, data, ttl or TTL.PRICE_DEFAULT)

    def invalidate_price(self, product_id: int) -> bool:
        """Invalidate price cache"""
        key = self._generate_key(CachePrefix.PRICE_PRODUCT, product_id)
        return self.delete(key)

    def get_category_prices(self, category_id: int) -> Optional[List[Dict]]:
        """Get cached category prices"""
        key = self._generate_key(CachePrefix.PRICE_CATEGORY, category_id)
        return self.get(key)

    def set_category_prices(
        self,
        category_id: int,
        data: List[Dict],
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache category prices"""
        key = self._generate_key(CachePrefix.PRICE_CATEGORY, category_id)
        return self.set(key, data, ttl or TTL.PRICE_DEFAULT)

    # ========================
    # Inventory Caching
    # ========================

    def get_inventory(self, product_id: int) -> Optional[Dict]:
        """Get cached inventory for a product"""
        key = self._generate_key(CachePrefix.INVENTORY_PRODUCT, product_id)
        return self.get(key)

    def set_inventory(
        self,
        product_id: int,
        data: Dict,
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache inventory with very short TTL"""
        key = self._generate_key(CachePrefix.INVENTORY_PRODUCT, product_id)
        return self.set(key, data, ttl or TTL.INVENTORY_DEFAULT)

    def invalidate_inventory(self, product_id: int) -> bool:
        """Invalidate inventory cache (call on inventory changes)"""
        key = self._generate_key(CachePrefix.INVENTORY_PRODUCT, product_id)
        return self.delete(key)

    def get_low_stock_products(self) -> Optional[List[Dict]]:
        """Get cached low stock products"""
        key = self._generate_key(CachePrefix.INVENTORY_LOW_STOCK, "all")
        return self.get(key)

    def set_low_stock_products(
        self,
        data: List[Dict],
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache low stock products"""
        key = self._generate_key(CachePrefix.INVENTORY_LOW_STOCK, "all")
        return self.set(key, data, ttl or TTL.INVENTORY_DEFAULT)

    def get_out_of_stock_products(self) -> Optional[List[Dict]]:
        """Get cached out of stock products"""
        key = self._generate_key(CachePrefix.INVENTORY_OUT_OF_STOCK, "all")
        return self.get(key)

    def set_out_of_stock_products(
        self,
        data: List[Dict],
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache out of stock products"""
        key = self._generate_key(CachePrefix.INVENTORY_OUT_OF_STOCK, "all")
        return self.set(key, data, ttl or TTL.INVENTORY_DEFAULT)

    # ========================
    # Session Caching
    # ========================

    def get_user_session(self, user_id: int) -> Optional[Dict]:
        """Get cached user session data"""
        key = self._generate_key(CachePrefix.SESSION_USER, user_id)
        return self.get(key)

    def set_user_session(
        self,
        user_id: int,
        data: Dict,
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache user session data"""
        key = self._generate_key(CachePrefix.SESSION_USER, user_id)
        # Use configured session timeout if available
        session_ttl = ttl or (settings.SESSION_TIMEOUT_MINUTES * 60)
        return self.set(key, data, session_ttl)

    def invalidate_user_session(self, user_id: int) -> bool:
        """Invalidate user session cache (call on logout)"""
        key = self._generate_key(CachePrefix.SESSION_USER, user_id)
        return self.delete(key)

    def get_token_data(self, token_hash: str) -> Optional[Dict]:
        """Get cached token validation data"""
        key = self._generate_key(CachePrefix.SESSION_TOKEN, token_hash)
        return self.get(key)

    def set_token_data(
        self,
        token_hash: str,
        data: Dict,
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache token validation data"""
        key = self._generate_key(CachePrefix.SESSION_TOKEN, token_hash)
        return self.set(key, data, ttl or TTL.SESSION_DEFAULT)

    def invalidate_token(self, token_hash: str) -> bool:
        """Invalidate token cache"""
        key = self._generate_key(CachePrefix.SESSION_TOKEN, token_hash)
        return self.delete(key)

    # ========================
    # Reports Caching
    # ========================

    def get_sales_report(
        self,
        start_date: str,
        end_date: str,
        report_type: str = "daily",
    ) -> Optional[Dict]:
        """Get cached sales report"""
        key = self._generate_key(
            CachePrefix.REPORT_SALES, start_date, end_date, report_type
        )
        return self.get(key)

    def set_sales_report(
        self,
        data: Dict,
        start_date: str,
        end_date: str,
        report_type: str = "daily",
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache sales report"""
        key = self._generate_key(
            CachePrefix.REPORT_SALES, start_date, end_date, report_type
        )
        return self.set(key, data, ttl or TTL.REPORT_DEFAULT)

    def get_inventory_report(self, report_type: str = "current") -> Optional[Dict]:
        """Get cached inventory report"""
        key = self._generate_key(CachePrefix.REPORT_INVENTORY, report_type)
        return self.get(key)

    def set_inventory_report(
        self,
        data: Dict,
        report_type: str = "current",
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache inventory report"""
        key = self._generate_key(CachePrefix.REPORT_INVENTORY, report_type)
        return self.set(key, data, ttl or TTL.REPORT_DEFAULT)

    def get_eod_report(self, date: str) -> Optional[Dict]:
        """Get cached end-of-day report"""
        key = self._generate_key(CachePrefix.REPORT_EOD, date)
        return self.get(key)

    def set_eod_report(
        self,
        data: Dict,
        date: str,
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache end-of-day report"""
        key = self._generate_key(CachePrefix.REPORT_EOD, date)
        return self.set(key, data, ttl or TTL.REPORT_DEFAULT)

    def get_analytics(
        self,
        analytics_type: str,
        params: Optional[Dict] = None,
    ) -> Optional[Dict]:
        """Get cached analytics data"""
        key = self._generate_key(
            CachePrefix.REPORT_ANALYTICS, analytics_type, params or {}
        )
        return self.get(key)

    def set_analytics(
        self,
        analytics_type: str,
        data: Dict,
        params: Optional[Dict] = None,
        ttl: Optional[int] = None,
    ) -> bool:
        """Cache analytics data"""
        key = self._generate_key(
            CachePrefix.REPORT_ANALYTICS, analytics_type, params or {}
        )
        return self.set(key, data, ttl or TTL.ANALYTICS_DEFAULT)


# Decorator for automatic caching
def cached(
    prefix: CachePrefix,
    ttl: Optional[int] = None,
    key_builder: Optional[Callable[..., str]] = None,
):
    """
    Decorator for automatic function result caching

    Usage:
        @cached(CachePrefix.PRODUCT_CATALOG, ttl=TTL.PRODUCT_CATALOG_DEFAULT)
        async def get_products(page: int, limit: int):
            ...
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            cache = get_cache()

            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Default key building from function args
                key_parts = [prefix.value, func.__name__]
                key_parts.extend(
                    str(arg) for arg in args if not hasattr(arg, "__dict__")
                )
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT for {cache_key}")
                return cached_value

            # Execute function and cache result
            logger.debug(f"Cache MISS for {cache_key}")
            result = await func(*args, **kwargs)  # type: ignore[misc]

            if result is not None:
                # Determine TTL based on prefix if not specified
                cache_ttl = ttl
                if cache_ttl is None:
                    cache_ttl = _get_default_ttl(prefix)

                cache.set(cache_key, result, cache_ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            cache = get_cache()

            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                key_parts = [prefix.value, func.__name__]
                key_parts.extend(
                    str(arg) for arg in args if not hasattr(arg, "__dict__")
                )
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT for {cache_key}")
                return cached_value

            # Execute function and cache result
            logger.debug(f"Cache MISS for {cache_key}")
            result = func(*args, **kwargs)

            if result is not None:
                cache_ttl = ttl
                if cache_ttl is None:
                    cache_ttl = _get_default_ttl(prefix)

                cache.set(cache_key, result, cache_ttl)

            return result

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator  # type: ignore[return-value]


def _get_default_ttl(prefix: CachePrefix) -> int:
    """Get default TTL based on cache prefix"""
    prefix_value = prefix.value

    if prefix_value.startswith("product"):
        return TTL.PRODUCT_CATALOG_DEFAULT
    elif prefix_value.startswith("price"):
        return TTL.PRICE_DEFAULT
    elif prefix_value.startswith("inventory"):
        return TTL.INVENTORY_DEFAULT
    elif prefix_value.startswith("session"):
        return TTL.SESSION_DEFAULT
    elif prefix_value.startswith("report"):
        return TTL.REPORT_DEFAULT

    return 300  # Default 5 minutes


# Singleton cache service instance
_cache_instance: Optional[CacheService] = None


def get_cache() -> CacheService:
    """Get the cache service singleton"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CacheService()
    return _cache_instance


# Export convenience function
def invalidate_all_product_cache():
    """Invalidate all product-related caches"""
    cache = get_cache()
    cache.invalidate_pattern(CachePrefix.PRODUCT_CATALOG)
    cache.invalidate_pattern(CachePrefix.PRODUCT_DETAIL)
    cache.invalidate_pattern(CachePrefix.PRODUCT_CATEGORY)


def invalidate_all_inventory_cache():
    """Invalidate all inventory-related caches"""
    cache = get_cache()
    cache.invalidate_pattern(CachePrefix.INVENTORY)
    cache.invalidate_pattern(CachePrefix.INVENTORY_PRODUCT)
    cache.invalidate_pattern(CachePrefix.INVENTORY_LOW_STOCK)
    cache.invalidate_pattern(CachePrefix.INVENTORY_OUT_OF_STOCK)


def invalidate_all_report_cache():
    """Invalidate all report-related caches"""
    cache = get_cache()
    cache.invalidate_pattern(CachePrefix.REPORT)
    cache.invalidate_pattern(CachePrefix.REPORT_SALES)
    cache.invalidate_pattern(CachePrefix.REPORT_INVENTORY)
    cache.invalidate_pattern(CachePrefix.REPORT_EOD)
    cache.invalidate_pattern(CachePrefix.REPORT_ANALYTICS)
