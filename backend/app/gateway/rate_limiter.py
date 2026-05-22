"""Token bucket rate limiter with Redis backend."""

import logging
import os
import time
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request

from app.gateway.cache import get_cache_manager

logger = logging.getLogger("gateway.rate_limiter")


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter.
    
    Tracks requests per API key or IP address using Redis as the backend store.
    """

    def __init__(
        self,
        requests_per_minute: Optional[int] = None,
        burst_size: Optional[int] = None,
        enabled: Optional[bool] = None,
    ):
        """
        Initialize rate limiter with configurations.
        
        Args:
            requests_per_minute: Maximum requests allowed per minute.
            burst_size: Maximum bucket capacity (allows short bursts).
            enabled: Toggle rate limiting.
        """
        self.enabled = (
            enabled if enabled is not None 
            else os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        )
        self.requests_per_minute = (
            requests_per_minute if requests_per_minute is not None 
            else int(os.getenv("RATE_LIMIT_RPM", "60"))
        )
        self.burst_size = (
            burst_size if burst_size is not None 
            else int(os.getenv("RATE_LIMIT_BURST", "10"))
        )
        
        # Calculate how many tokens are added to the bucket per second
        self.refill_rate = self.requests_per_minute / 60.0

        # Redis Lua Script to ensure atomic check-and-update behavior
        self.lua_script = """
        local key = KEYS[1]
        local max_tokens = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local requested = tonumber(ARGV[3])
        local now = tonumber(ARGV[4])

        -- Get current bucket state
        local rate_limit_info = redis.call('HMGET', key, 'tokens', 'last_updated')
        local tokens = tonumber(rate_limit_info[1])
        local last_updated = tonumber(rate_limit_info[2])

        if not tokens then
            -- Bucket doesn't exist yet, initialize to max capacity
            tokens = max_tokens
            last_updated = now
        else
            -- Refill tokens based on time elapsed
            local elapsed = math.max(0, now - last_updated)
            local refill = elapsed * refill_rate
            tokens = math.min(max_tokens, tokens + refill)
            last_updated = now
        end

        local allowed = false
        if tokens >= requested then
            tokens = tokens - requested
            allowed = true
        end

        -- Update bucket state in Redis
        redis.call('HMSET', key, 'tokens', tokens, 'last_updated', last_updated)
        -- Set TTL to 1 hour (3600 seconds) so inactive keys clean up automatically
        redis.call('EXPIRE', key, 3600)

        return allowed and 1 or 0
        """

    @property
    def redis_client(self):
        """Lazy load and return redis client from global CacheManager."""
        cache_manager = get_cache_manager()
        if cache_manager and cache_manager.enabled and cache_manager.connected:
            return cache_manager.client
        return None

    def check_rate_limit(self, identifier: str, requested: int = 1) -> bool:
        """
        Check if a request is allowed under the rate limit.
        
        Args:
            identifier: The unique client ID (API key or IP).
            requested: Tokens to consume per check.
            
        Returns:
            bool: True if allowed (tokens consumed), False if denied (rate limited).
        """
        if not self.enabled:
            return True

        client = self.redis_client
        if not client:
            # Gracefully allow traffic if Redis is down/disabled
            logger.warning("Redis client is not available. Rate limiting is bypassed.")
            return True

        key = f"rate_limit:{identifier}"
        now = time.time()

        try:
            # Execute the Lua script atomically
            allowed_flag = client.eval(
                self.lua_script,
                1,
                key,
                self.burst_size,
                self.refill_rate,
                requested,
                now
            )
            return bool(allowed_flag)
        except Exception as e:
            logger.error(f"Error checking rate limit in Redis: {e}")
            # Fallback to allowing request in case of Redis exceptions
            return True


# Global rate limiter instance (singleton)
_rate_limiter: Optional[TokenBucketRateLimiter] = None


def get_rate_limiter() -> TokenBucketRateLimiter:
    """Retrieve or create the global TokenBucketRateLimiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = TokenBucketRateLimiter()
    return _rate_limiter

 
async def verify_rate_limit(
    request: Request,
    x_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    rate_limiter: TokenBucketRateLimiter = Depends(get_rate_limiter),
):
    """
    FastAPI dependency to verify client rate limits.
    
    Checks X-API-Key and Authorization headers, falling back to request IP.
    """
    if x_api_key:
        identifier = f"apikey:{x_api_key}"
    elif authorization:
        # Sanitize authorization value to avoid exposing credentials in logs/keys
        identifier = f"auth:{authorization[:50]}"
    else:
        # Fallback to Client IP Address
        client_host = request.client.host if request.client else "unknown"
        identifier = f"ip:{client_host}"

    if not rate_limiter.check_rate_limit(identifier):
        logger.warning(f"Rate limit exceeded for identifier: {identifier}")
        raise HTTPException(
            status_code=429,
            detail="Too Many Requests: Rate limit exceeded"
        )
