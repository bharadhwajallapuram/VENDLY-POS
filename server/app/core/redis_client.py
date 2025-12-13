"""
Redis client for temporary token storage and caching
"""

import json
import logging
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    import redis

try:
    import redis as redis_module
except ImportError:
    redis_module = None  # type: ignore

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper for token storage"""

    _instance: Optional["RedisClient"] = None
    _client: Optional[Any] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._connect()

    def _connect(self):
        """Connect to Redis"""
        if not redis_module:
            logger.warning("Redis not installed. Using in-memory fallback.")
            return

        try:
            self._client = redis_module.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
            )
            # Test connection
            self._client.ping()
            logger.info("✓ Connected to Redis")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}. Using in-memory fallback.")
            self._client = None

    def set(self, key: str, value: Any, ttl: int) -> bool:
        """
        Store value with TTL (seconds)

        Args:
            key: Redis key
            value: Value to store (will be JSON encoded)
            ttl: Time to live in seconds

        Returns:
            True if successful, False otherwise
        """
        if not self._client:
            return False

        try:
            json_value = json.dumps(value) if not isinstance(value, str) else value
            self._client.setex(key, ttl, json_value)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from Redis

        Args:
            key: Redis key

        Returns:
            Decoded value or None if not found
        """
        if not self._client:
            return None

        try:
            value = self._client.get(key)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    def delete(self, key: str) -> bool:
        """
        Delete key from Redis

        Args:
            key: Redis key

        Returns:
            True if successful
        """
        if not self._client:
            return False

        try:
            self._client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self._client:
            return False

        try:
            return bool(self._client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error: {e}")
            return False


# In-memory fallback for when Redis is not available
class InMemoryStore:
    """Fallback in-memory storage"""

    def __init__(self):
        self._store = {}

    def set(self, key: str, value: Any, ttl: int) -> bool:
        """Store value in memory"""
        self._store[key] = value
        return True

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from memory"""
        return self._store.get(key)

    def delete(self, key: str) -> bool:
        """Delete value from memory"""
        if key in self._store:
            del self._store[key]
        return True

    def exists(self, key: str) -> bool:
        """Check if key exists"""
        return key in self._store


# Global instance
_redis = RedisClient()
_fallback = InMemoryStore()


def get_token_store():
    """Get the appropriate token store (Redis or in-memory)"""
    if _redis._client:
        return _redis
    return _fallback
