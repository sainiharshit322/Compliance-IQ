import asyncio
from datetime import datetime, timezone
import functools
import inspect
import logging
import random
import time
from typing import Any, Callable, Dict, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("collector_agent.resiliency")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RateLimitException(Exception):
    """Raised when HTTP 429 Too Many Requests or HTTP 503 Service Unavailable occurs."""
    def __init__(self, message: str, retry_after_seconds: Optional[int] = None, error_code: str = "AZURE_ARM_RATE_LIMIT_EXCEEDED"):
        super().__init__(message)
        self.message = message
        self.retry_after_seconds = retry_after_seconds
        self.error_code = error_code


class PartialThrottledPayload(BaseModel):
    timestamp: str = Field(default_factory=utc_now_iso)
    status: str = Field(default="PARTIAL_THROTTLED")
    error_code: str = Field(default="AZURE_ARM_RATE_LIMIT_EXCEEDED")
    error_message: str
    retry_after_seconds: int = Field(default=300)
    partial_data: Optional[Dict[str, Any]] = None
    requires_hitl_fallback: bool = Field(default=True)


def generate_partial_throttled_payload(
    error_message: str = "HTTP 429: Rate limit quota exhausted on Student Tier.",
    error_code: str = "AZURE_ARM_RATE_LIMIT_EXCEEDED",
    retry_after_seconds: int = 300,
    partial_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generates standardized degraded fallback payload matching Section 3.2 of 05_agent_tools.md."""
    payload = PartialThrottledPayload(
        error_message=error_message,
        error_code=error_code,
        retry_after_seconds=retry_after_seconds,
        partial_data=partial_data,
    )
    return payload.model_dump()


def execute_with_exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 2.0,
    max_delay: float = 30.0,
):
    """
    Decorator / wrapper function to retry operations on RateLimitException with exponential backoff.
    If retries are exhausted, catches the exception and returns a PARTIAL_THROTTLED payload.
    """
    def decorator(func: Callable):
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                for attempt in range(1, max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except RateLimitException as rle:
                        logger.warning(
                            f"Rate limit hit on attempt {attempt}/{max_retries} for {func.__name__}: {rle.message}"
                        )
                        if attempt == max_retries:
                            logger.error(
                                f"Retries exhausted ({max_retries} attempts) for {func.__name__}. Generating PARTIAL_THROTTLED fallback."
                            )
                            return generate_partial_throttled_payload(
                                error_message=rle.message,
                                error_code=rle.error_code,
                                retry_after_seconds=rle.retry_after_seconds or 300,
                            )
                        
                        raw_delay = rle.retry_after_seconds if rle.retry_after_seconds else (base_delay ** attempt) + random.uniform(-0.5, 0.5)
                        delay = min(max_delay, raw_delay)
                        logger.info(f"Sleeping {delay:.2f}s before retry attempt {attempt + 1}...")
                        await asyncio.sleep(max(0.01, delay))
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                for attempt in range(1, max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except RateLimitException as rle:
                        logger.warning(
                            f"Rate limit hit on attempt {attempt}/{max_retries} for {func.__name__}: {rle.message}"
                        )
                        if attempt == max_retries:
                            logger.error(
                                f"Retries exhausted ({max_retries} attempts) for {func.__name__}. Generating PARTIAL_THROTTLED fallback."
                            )
                            return generate_partial_throttled_payload(
                                error_message=rle.message,
                                error_code=rle.error_code,
                                retry_after_seconds=rle.retry_after_seconds or 300,
                            )

                        raw_delay = rle.retry_after_seconds if rle.retry_after_seconds else (base_delay ** attempt) + random.uniform(-0.5, 0.5)
                        delay = min(max_delay, raw_delay)
                        logger.info(f"Sleeping {delay:.2f}s before retry attempt {attempt + 1}...")
                        time.sleep(max(0.01, delay))
            return sync_wrapper
    return decorator
