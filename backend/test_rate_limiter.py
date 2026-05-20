"""
Test script for the Redis-backed Token Bucket Rate Limiter.

Run after starting Redis (either via Docker or local Redis server):
  docker-compose up -d redis
  # OR
  redis-server (if installed locally)

Then run:
  python backend/test_rate_limiter.py
"""

import logging
import os
import time
from fastapi.testclient import TestClient

# Ensure environment variables are set for testing
os.environ["RATE_LIMIT_ENABLED"] = "true"

from main import app
from app.gateway.rate_limiter import TokenBucketRateLimiter, get_rate_limiter

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_rate_limiter_class_basic():
    print("\n" + "="*60)
    print("[TEST 1] Basic Rate Limiter Class Operations")
    print("="*60)
    
    # Initialize limiter with low burst for testing
    limiter = TokenBucketRateLimiter(requests_per_minute=60, burst_size=3, enabled=True)
    
    # Check if Redis client is available
    if not limiter.redis_client:
        print("[WARN] Redis not connected - rate limiter disabled/degraded (this is OK for testing)")
        # Test default fallback behavior: always returns True
        assert limiter.check_rate_limit("test_client") is True
        print("[OK] Test passed with graceful degradation (offline fallback)")
        return

    # Clear any existing rate limit keys for the test client
    limiter.redis_client.delete("rate_limit:test_client")

    # First request - should be allowed
    assert limiter.check_rate_limit("test_client") is True
    print("[OK] Request 1 allowed")

    # Second request - should be allowed
    assert limiter.check_rate_limit("test_client") is True
    print("[OK] Request 2 allowed")

    # Third request - should be allowed
    assert limiter.check_rate_limit("test_client") is True
    print("[OK] Request 3 allowed")

    # Fourth request - should be denied (burst limit is 3)
    assert limiter.check_rate_limit("test_client") is False
    print("[OK] Request 4 denied (limit exceeded as expected)")


def test_rate_limiter_refill():
    print("\n" + "="*60)
    print("[TEST 2] Token Bucket Refill Mechanism")
    print("="*60)

    # Initialize limiter with high fill rate for quick testing
    # 360 RPM = 6 tokens per second
    limiter = TokenBucketRateLimiter(requests_per_minute=360, burst_size=3, enabled=True)

    if not limiter.redis_client:
        print("[WARN] Redis not connected - skipping refill test")
        return

    limiter.redis_client.delete("rate_limit:test_refill")

    # Exhaust the bucket
    assert limiter.check_rate_limit("test_refill") is True
    assert limiter.check_rate_limit("test_refill") is True
    assert limiter.check_rate_limit("test_refill") is True
    assert limiter.check_rate_limit("test_refill") is False
    print("[OK] Bucket successfully exhausted")

    # Wait 0.5 seconds -> refill rate is 6 tokens/sec, so we should get ~3 tokens back
    time.sleep(0.5)

    # Should be allowed again
    assert limiter.check_rate_limit("test_refill") is True
    print("[OK] Request after wait allowed (refill works)")


def test_fastapi_dependency():
    print("\n" + "="*60)
    print("[TEST 3] FastAPI Dependency and Route Integration")
    print("="*60)

    # Configure the global rate limiter instance to have low burst for testing
    limiter = get_rate_limiter()
    limiter.enabled = True
    limiter.burst_size = 2
    limiter.requests_per_minute = 10  # low fill rate so it stays exhausted during test

    client = TestClient(app)

    # Mock/simulate request headers
    headers = {"X-API-Key": "test_api_key_123"}
    
    if limiter.redis_client:
        limiter.redis_client.delete("rate_limit:apikey:test_api_key_123")

    # Simple mock payload for gateway/chat
    payload = {
        "provider": "gemini",
        "model": "gemini-2.5-flash",
        "messages": [{"role": "user", "content": "Ping"}],
        "temperature": 0.7,
        "max_tokens": 10
    }

    # Request 1
    response1 = client.post("/gateway/chat", json=payload, headers=headers)
    print(f"Request 1 status: {response1.status_code}")
    
    # Request 2
    response2 = client.post("/gateway/chat", json=payload, headers=headers)
    print(f"Request 2 status: {response2.status_code}")

    # Request 3 - should get 429 if Redis is active
    response3 = client.post("/gateway/chat", json=payload, headers=headers)
    print(f"Request 3 status: {response3.status_code}")

    if limiter.redis_client:
        assert response3.status_code == 429
        assert "Rate limit exceeded" in response3.json()["detail"]
        print("[OK] Route returned HTTP 429 on third request as expected")
    else:
        print("[WARN] Redis is not running. Checking that requests degrade gracefully without 429.")
        assert response1.status_code != 429
        assert response2.status_code != 429
        assert response3.status_code != 429
        print("[OK] Graceful offline route degradation verified")


if __name__ == "__main__":
    test_rate_limiter_class_basic()
    test_rate_limiter_refill()
    test_fastapi_dependency()
    print("\n" + "="*60)
    print("[SUCCESS] All rate limiter tests completed successfully!")
    print("="*60)
