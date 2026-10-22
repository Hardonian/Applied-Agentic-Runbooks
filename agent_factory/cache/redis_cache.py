"""Redis caching implementation."""

import json
import os
from functools import wraps
from typing import Any

import redis

from agent_factory.monitoring.metrics import MetricsCollector


class RedisCache:
    """Redis cache implementation."""

    def __init__(self, host: str | None = None, port: int = 6379, db: int = 0):
        """
        Initialize Redis cache.

        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
        """
        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port or int(os.getenv("REDIS_PORT", "6379"))
        self.db = db

        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True,
                socket_connect_timeout=5,
            )
            # Test connection
            self.client.ping()
        except Exception:
            self.client = None

    def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.client:
            return None

        try:
            value = self.client.get(key)
            if value:
                MetricsCollector.record_cache_hit("redis")
                return json.loads(value)
            else:
                MetricsCollector.record_cache_miss("redis")
                return None
        except Exception:
            MetricsCollector.record_cache_miss("redis")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
        """
        if not self.client:
            return

        try:
            self.client.setex(key, ttl, json.dumps(value))
        except Exception:
            pass

    def delete(self, key: str):
        """
        Delete key from cache.

        Args:
            key: Cache key
        """
        if not self.client:
            return

        try:
            self.client.delete(key)
        except Exception:
            pass

    def clear(self, pattern: str = "*"):
        """
        Clear cache by pattern.

        Args:
            pattern: Key pattern
        """
        if not self.client:
            return

        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
        except Exception:
            pass


# Global cache instance
_cache: RedisCache | None = None


def get_cache() -> RedisCache:
    """Get global cache instance."""
    global _cache
    if _cache is None:
        _cache = RedisCache()
    return _cache


def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorator to cache function results.

    Args:
        ttl: Time to live in seconds
        key_prefix: Key prefix
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()

            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper

    return decorator
