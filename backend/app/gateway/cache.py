"""
Redis caching layer for LLM gateway.

Implements prompt-based caching to avoid repeated LLM calls.
Cache key: SHA256(provider + model + prompt_content)
TTL: Configurable (default 24 hours)
"""

import hashlib
import json
import logging
import os
from typing import Optional, Dict, Any

import redis
from redis.exceptions import RedisError, ConnectionError

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages Redis cache for LLM responses."""

    def __init__(
        self,
        redis_host: str = None,
        redis_port: int = None,
        redis_db: int = 0,
        redis_password: str = None,
        default_ttl: int = 86400,  # 24 hours in seconds
        enabled: bool = True,
    ):
        """
        Initialize cache manager.

        Args:
            redis_host: Redis server host (default: localhost)
            redis_port: Redis server port (default: 6379)
            redis_db: Redis database number (default: 0)
            redis_password: Redis password (optional)
            default_ttl: Default cache TTL in seconds (default: 24 hours)
            enabled: Whether caching is enabled (default: True)
        """
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self.redis_port = redis_port or int(os.getenv("REDIS_PORT", 6379))
        self.redis_db = redis_db
        self.redis_password = redis_password or os.getenv("REDIS_PASSWORD")
        self.default_ttl = default_ttl
        self.enabled = enabled

        self.client: Optional[redis.Redis] = None
        self.connected = False
        self.stats = {"hits": 0, "misses": 0, "errors": 0}

        if self.enabled:
            self._connect()

    def _connect(self) -> None:
        """Connect to Redis."""
        try:
            self.client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            # Test connection
            self.client.ping()
            self.connected = True
            logger.info(
                f"Connected to Redis at {self.redis_host}:{self.redis_port}"
            )
        except ConnectionError as e:
            self.connected = False
            logger.warning(
                f"Redis connection failed: {e}. Caching disabled."
            )
        except Exception as e:
            self.connected = False
            logger.error(f"Redis error: {e}")

    @staticmethod
    def _generate_cache_key(
        provider: str, model: str, messages: list
    ) -> str:
        """
        Generate cache key from provider, model, and messages.

        Uses SHA256 hash of the combined string for consistent, compact keys.

        Args:
            provider: LLM provider (openai, anthropic, gemini)
            model: Model name (gpt-4, claude-3-opus, etc.)
            messages: List of message dicts with role and content

        Returns:
            Cache key (format: cache:provider:model:hash)
        """
        # Normalize messages to JSON string for consistent hashing
        messages_str = json.dumps(messages, sort_keys=True, separators=(",", ":"))

        # Create combined content string
        content = f"{provider}:{model}:{messages_str}"

        # Generate SHA256 hash
        hash_digest = hashlib.sha256(content.encode()).hexdigest()

        return f"cache:{provider}:{model}:{hash_digest}"

    def get(self, provider: str, model: str, messages: list) -> Optional[Dict]:
        """
        Get cached response from Redis.

        Args:
            provider: LLM provider
            model: Model name
            messages: List of message dicts

        Returns:
            Cached response dict, or None if not found/error
        """
        if not self.enabled or not self.connected:
            return None

        try:
            key = self._generate_cache_key(provider, model, messages)
            value = self.client.get(key)

            if value:
                self.stats["hits"] += 1
                logger.debug(f"✓ Cache HIT: {key}")
                return json.loads(value)
            else:
                self.stats["misses"] += 1
                logger.debug(f"✗ Cache MISS: {key}")
                return None

        except RedisError as e:
            self.stats["errors"] += 1
            logger.warning(f"⚠ Cache get error: {e}")
            return None
        except json.JSONDecodeError as e:
            self.stats["errors"] += 1
            logger.warning(f"⚠ Cache value decode error: {e}")
            return None

    def set(
        self,
        provider: str,
        model: str,
        messages: list,
        response: Dict,
        ttl: Optional[int] = None,
    ) -> bool:
        """
        Store response in Redis cache.

        Args:
            provider: LLM provider
            model: Model name
            messages: List of message dicts
            response: Response dict to cache
            ttl: Cache TTL in seconds (default: self.default_ttl)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.connected:
            return False

        try:
            key = self._generate_cache_key(provider, model, messages)
            ttl = ttl or self.default_ttl
            value = json.dumps(response)

            self.client.setex(key, ttl, value)
            logger.debug(f"✓ Cache SET: {key} (TTL: {ttl}s)")
            return True

        except RedisError as e:
            self.stats["errors"] += 1
            logger.warning(f"⚠ Cache set error: {e}")
            return False
        except (TypeError, ValueError) as e:
            self.stats["errors"] += 1
            logger.warning(f"⚠ Cache value encode error: {e}")
            return False

    def clear(self) -> bool:
        """Clear all cache entries."""
        if not self.enabled or not self.connected:
            return False

        try:
            # Delete all cache:* keys
            cursor = 0
            deleted = 0
            while True:
                cursor, keys = self.client.scan(
                    cursor, match="cache:*", count=100
                )
                if keys:
                    deleted += self.client.delete(*keys)
                if cursor == 0:
                    break
            logger.info(f"✓ Cleared {deleted} cache entries")
            return True
        except RedisError as e:
            logger.warning(f"⚠ Cache clear error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dict with hits, misses, errors, and hit rate
        """
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            (self.stats["hits"] / total * 100) if total > 0 else 0
        )

        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "errors": self.stats["errors"],
            "total": total,
            "hit_rate_percent": round(hit_rate, 2),
            "connected": self.connected,
            "enabled": self.enabled,
        }

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self.stats = {"hits": 0, "misses": 0, "errors": 0}
        logger.debug("✓ Cache stats reset")

    def close(self) -> None:
        """Close Redis connection."""
        if self.client:
            try:
                self.client.close()
                self.connected = False
                logger.info("✓ Redis connection closed")
            except Exception as e:
                logger.warning(f"⚠ Error closing Redis: {e}")


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(
    enabled: bool = True,
    redis_host: str = None,
    redis_port: int = None,
    redis_db: int = 0,
    redis_password: str = None,
    default_ttl: int = 86400,
) -> CacheManager:
    """
    Get or create global cache manager instance.

    Args:
        enabled: Whether caching is enabled
        redis_host: Redis host
        redis_port: Redis port
        redis_db: Redis database number
        redis_password: Redis password
        default_ttl: Default cache TTL

    Returns:
        CacheManager instance
    """
    global _cache_manager

    if _cache_manager is None:
        _cache_manager = CacheManager(
            redis_host=redis_host,
            redis_port=redis_port,
            redis_db=redis_db,
            redis_password=redis_password,
            default_ttl=default_ttl,
            enabled=enabled,
        )

    return _cache_manager
