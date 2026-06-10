"""
Resilience layer for LLM gateway.

Implements:
1. Redis-backed Circuit Breaker to track provider health across processes.
2. Async retry logic with exponential backoff.
"""

import asyncio
import logging
import os
import time
from enum import Enum
from typing import Callable, Any, Awaitable, Optional

import httpx
import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class CircuitState(str, Enum):
    CLOSED = "CLOSED"      # Normal operation, accepting requests
    OPEN = "OPEN"          # Failing, fast-rejecting requests
    HALF_OPEN = "HALF_OPEN" # Testing if provider recovered


class RedisCircuitBreaker:
    """
    Redis-backed circuit breaker to track provider health.
    If Redis is unavailable, it gracefully degrades to a no-op (always CLOSED)
    so it doesn't block the system.
    """

    def __init__(
        self,
        redis_host: str = None,
        redis_port: int = None,
        redis_db: int = 0,
        redis_password: str = None,
        failure_threshold: int = 3,
        reset_timeout: int = 60,
    ):
        self.redis_host = redis_host or os.getenv("REDIS_HOST", "localhost")
        self.redis_port = redis_port or int(os.getenv("REDIS_PORT", 6379))
        self.redis_db = redis_db
        self.redis_password = redis_password or os.getenv("REDIS_PASSWORD")
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.client: Optional[redis.Redis] = None

        self._connect()

    def _connect(self) -> None:
        try:
            self.client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=True,
                socket_connect_timeout=2,
            )
            self.client.ping()
        except Exception as e:
            logger.warning(f"Circuit Breaker Redis connection failed: {e}. Degrading to No-Op.")
            self.client = None

    def _get_key(self, provider: str, suffix: str) -> str:
        return f"circuit_breaker:{provider}:{suffix}"

    def get_state(self, provider: str) -> CircuitState:
        if not self.client:
            return CircuitState.CLOSED
        
        try:
            state = self.client.get(self._get_key(provider, "state"))
            if state == CircuitState.OPEN.value:
                return CircuitState.OPEN
            if state == CircuitState.HALF_OPEN.value:
                return CircuitState.HALF_OPEN
            return CircuitState.CLOSED
        except RedisError as e:
            logger.warning(f"Redis error getting state for {provider}: {e}")
            return CircuitState.CLOSED

    def record_failure(self, provider: str) -> None:
        if not self.client:
            return
        
        try:
            failures_key = self._get_key(provider, "failures")
            state_key = self._get_key(provider, "state")
            
            # Increment failure count
            failures = self.client.incr(failures_key)
            
            # Set expiry if this is the first failure
            if failures == 1:
                self.client.expire(failures_key, self.reset_timeout * 2)
            
            if failures >= self.failure_threshold:
                current_state = self.get_state(provider)
                if current_state != CircuitState.OPEN:
                    logger.error(f"🚨 Circuit Breaker OPEN for {provider} after {failures} failures.")
                    # Set state to OPEN with an expiry (reset_timeout)
                    # After expiry, the key disappears, effectively becoming CLOSED, but
                    # we want to transition to HALF_OPEN. We handle this in get_state or before call.
                    # A better way: Set OPEN with timeout, let it expire. 
                    self.client.setex(state_key, self.reset_timeout, CircuitState.OPEN.value)
        except RedisError as e:
            logger.warning(f"Redis error recording failure for {provider}: {e}")

    def record_success(self, provider: str) -> None:
        if not self.client:
            return
            
        try:
            failures_key = self._get_key(provider, "failures")
            state_key = self._get_key(provider, "state")
            
            current_state = self.get_state(provider)
            if current_state in (CircuitState.HALF_OPEN, CircuitState.OPEN):
                logger.info(f"✅ Circuit Breaker CLOSED for {provider} after successful test.")
            
            # Reset counters and state
            self.client.delete(failures_key, state_key)
        except RedisError as e:
            logger.warning(f"Redis error recording success for {provider}: {e}")

    def allow_request(self, provider: str) -> bool:
        """Check if request should be allowed to proceed."""
        state = self.get_state(provider)
        if state == CircuitState.CLOSED:
            return True
            
        # If it's OPEN, but the timeout has expired, Redis will return None (which maps to CLOSED)
        # So we only reach here if it's explicitly OPEN. 
        if state == CircuitState.OPEN:
            # Check if TTL is gone. Actually `setex` handles the timeout automatically.
            return False
            
        return True


# Singleton instance
_circuit_breaker: Optional[RedisCircuitBreaker] = None

def get_circuit_breaker() -> RedisCircuitBreaker:
    global _circuit_breaker
    if _circuit_breaker is None:
        _circuit_breaker = RedisCircuitBreaker()
    return _circuit_breaker


async def with_retries(
    func: Callable[..., Awaitable[Any]],
    *args,
    max_retries: int = 3,
    initial_backoff: float = 1.0,
    **kwargs
) -> Any:
    """
    Execute an async function with exponential backoff retries.
    Catches httpx.HTTPError.
    """
    retries = 0
    backoff = initial_backoff
    
    while True:
        try:
            return await func(*args, **kwargs)
        except httpx.HTTPError as e:
            retries += 1
            if retries >= max_retries:
                logger.error(f"❌ Max retries ({max_retries}) reached. Last error: {e}")
                raise e
            
            logger.warning(f"⚠️ Request failed: {e}. Retrying {retries}/{max_retries} in {backoff}s...")
            await asyncio.sleep(backoff)
            backoff *= 2  # Exponential backoff
