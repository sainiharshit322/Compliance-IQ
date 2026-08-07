"""
ComplianceIQ - Evidence Collector Agent Resiliency Pytest Unit Tests (Day 10)
Tests exponential backoff retries, RateLimitException handling, and PARTIAL_THROTTLED payload generation.
"""

from unittest.mock import MagicMock
import pytest

from services.collector_agent.resiliency import (
    RateLimitException,
    execute_with_exponential_backoff,
    generate_partial_throttled_payload,
)


def test_generate_partial_throttled_payload_schema():
    payload = generate_partial_throttled_payload(
        error_message="HTTP 429: Azure ARM API read quota exhausted on Student Tier.",
        error_code="AZURE_ARM_RATE_LIMIT_EXCEEDED",
        retry_after_seconds=300,
    )

    assert payload["status"] == "PARTIAL_THROTTLED"
    assert payload["error_code"] == "AZURE_ARM_RATE_LIMIT_EXCEEDED"
    assert payload["requires_hitl_fallback"] is True
    assert payload["retry_after_seconds"] == 300
    assert "timestamp" in payload


def test_exponential_backoff_success_on_retry():
    call_counter = MagicMock()

    @execute_with_exponential_backoff(max_retries=3, base_delay=0.01, max_delay=0.05)
    def flaky_tool():
        call_counter()
        if call_counter.call_count < 2:
            raise RateLimitException("HTTP 429: Too Many Requests")
        return {"status": "SUCCESS"}

    result = flaky_tool()
    assert result == {"status": "SUCCESS"}
    assert call_counter.call_count == 2


def test_exponential_backoff_exhaustion_returns_partial_throttled():
    call_counter = MagicMock()

    @execute_with_exponential_backoff(max_retries=3, base_delay=0.01, max_delay=0.05)
    def always_throttled_tool():
        call_counter()
        raise RateLimitException("HTTP 429: Rate limit quota exhausted", retry_after_seconds=120)

    result = always_throttled_tool()
    assert call_counter.call_count == 3
    assert result["status"] == "PARTIAL_THROTTLED"
    assert result["requires_hitl_fallback"] is True
    assert result["retry_after_seconds"] == 120
    assert "Rate limit quota exhausted" in result["error_message"]


@pytest.mark.asyncio
async def test_async_exponential_backoff_exhaustion():
    call_counter = MagicMock()

    @execute_with_exponential_backoff(max_retries=3, base_delay=0.01, max_delay=0.05)
    async def async_throttled_tool():
        call_counter()
        raise RateLimitException("HTTP 503: Service Unavailable", error_code="AZURE_SERVICE_UNAVAILABLE")

    result = await async_throttled_tool()
    assert call_counter.call_count == 3
    assert result["status"] == "PARTIAL_THROTTLED"
    assert result["error_code"] == "AZURE_SERVICE_UNAVAILABLE"
