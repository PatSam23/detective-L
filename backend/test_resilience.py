"""Tests for the LLM Gateway resilience layer."""

import asyncio
import os
import pytest
import httpx
from unittest.mock import AsyncMock, patch

from app.gateway.resilience import (
    RedisCircuitBreaker,
    CircuitState,
    with_retries,
    get_circuit_breaker
)
from app.gateway.schemas import GatewayChatRequest, GatewayMessage, GatewayChatResponse
from app.gateway.providers import call_provider_with_failover


@pytest.fixture
def mock_circuit_breaker():
    # Use a dummy Redis config so it degrades to no-op
    # Or mock the redis client to test circuit breaker logic
    cb = RedisCircuitBreaker(redis_host="invalid_host", redis_port=9999)
    # Mock the client directly with an in-memory dict
    mock_db = {}
    
    class MockRedisClient:
        def ping(self): pass
        def get(self, key): return mock_db.get(key)
        def setex(self, key, ttl, value): mock_db[key] = value
        def incr(self, key):
            mock_db[key] = mock_db.get(key, 0) + 1
            return mock_db[key]
        def expire(self, key, ttl): pass
        def delete(self, *keys):
            for k in keys:
                mock_db.pop(k, None)

    cb.client = MockRedisClient()
    return cb


@pytest.mark.asyncio
async def test_with_retries_success():
    """Test successful execution on first try."""
    mock_func = AsyncMock(return_value="success")
    result = await with_retries(mock_func, max_retries=3, initial_backoff=0.01)
    assert result == "success"
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_with_retries_recovers():
    """Test successful execution after some failures."""
    call_count = 0
    
    async def failing_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise httpx.HTTPError("Simulated error")
        return "success"
        
    result = await with_retries(failing_func, max_retries=5, initial_backoff=0.01)
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_with_retries_exhausted():
    """Test exception raised after max retries."""
    async def always_fails():
        raise httpx.HTTPError("Always fails")
        
    with pytest.raises(httpx.HTTPError):
        await with_retries(always_fails, max_retries=2, initial_backoff=0.01)


def test_circuit_breaker_state_transitions(mock_circuit_breaker):
    """Test CLOSED -> OPEN -> CLOSED transitions."""
    provider = "test_provider"
    
    # Initially CLOSED
    assert mock_circuit_breaker.get_state(provider) == CircuitState.CLOSED
    assert mock_circuit_breaker.allow_request(provider) == True
    
    # Fail below threshold
    mock_circuit_breaker.record_failure(provider)
    mock_circuit_breaker.record_failure(provider)
    assert mock_circuit_breaker.get_state(provider) == CircuitState.CLOSED
    
    # Fail at threshold (3)
    mock_circuit_breaker.record_failure(provider)
    assert mock_circuit_breaker.get_state(provider) == CircuitState.OPEN
    assert mock_circuit_breaker.allow_request(provider) == False
    
    # After success, should be CLOSED
    mock_circuit_breaker.record_success(provider)
    assert mock_circuit_breaker.get_state(provider) == CircuitState.CLOSED
    assert mock_circuit_breaker.allow_request(provider) == True


@pytest.mark.asyncio
@patch("app.gateway.providers._call_provider_single", new_callable=AsyncMock)
@patch("app.gateway.providers.get_circuit_breaker")
async def test_call_provider_with_failover(mock_get_cb, mock_call_single, monkeypatch):
    """Test failover chain execution."""
    # Set up mock circuit breaker
    cb = RedisCircuitBreaker(redis_host="invalid")
    cb.client = None # degrade to no-op
    mock_get_cb.return_value = cb
    
    # Configure failover chain
    monkeypatch.setenv("LLM_FAILOVER_CHAIN", "gemini,openai,anthropic")
    
    request = GatewayChatRequest(
        provider="gemini",
        model="gemini-2.5-flash",
        messages=[GatewayMessage(role="user", content="Hello")]
    )
    
    # Scenario: gemini fails, openai succeeds
    # Simulate gemini failure
    def side_effect(req, *args, **kwargs):
        if req.provider == "gemini":
            raise httpx.HTTPError("Gemini is down")
        if req.provider == "openai":
            return GatewayChatResponse(
                provider="openai",
                model="gpt-4o-mini",
                content="Hello from OpenAI"
            )
    
    mock_call_single.side_effect = side_effect
    
    # Override sleep to speed up test
    with patch("asyncio.sleep", new_callable=AsyncMock):
        response = await call_provider_with_failover(request)
        
    assert response.provider == "openai"
    assert response.model == "gpt-4o-mini"
    assert response.content == "Hello from OpenAI"
