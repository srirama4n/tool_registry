"""Resilience patterns: retry with backoff, circuit breaker."""
import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx
from pymongo.errors import NetworkTimeout, ServerSelectionTimeoutError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Transient errors worth retrying: connection, timeout
RETRY_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,
    httpx.ConnectError,
    httpx.ReadTimeout,
    httpx.WriteTimeout,
    httpx.ConnectTimeout,
)

# MongoDB transient errors
DB_RETRY_EXCEPTIONS = (ServerSelectionTimeoutError, NetworkTimeout, TimeoutError, ConnectionError, OSError)


def make_async_retry(
    max_attempts: int = 3,
    min_wait: float = 0.5,
    max_wait: float = 8.0,
    retry_exceptions: tuple[type[Exception], ...] = RETRY_EXCEPTIONS,
):
    """Return a retry decorator for async functions with exponential backoff."""
    def _decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(retry_exceptions),
            reraise=True,
        )
        async def _wrapper(*args, **kwargs) -> T:
            return await func(*args, **kwargs)
        return _wrapper
    return _decorator


def make_db_retry(
    max_attempts: int = 3,
    min_wait: float = 0.5,
    max_wait: float = 8.0,
):
    """Retry decorator for DB operations (MongoDB timeouts, connection errors)."""
    return make_async_retry(
        max_attempts=max_attempts,
        min_wait=min_wait,
        max_wait=max_wait,
        retry_exceptions=DB_RETRY_EXCEPTIONS,
    )


class CircuitBreakerOpenError(Exception):
    """Raised when the circuit breaker is open and the call is rejected."""
    pass


class CircuitBreaker:
    """
    In-memory circuit breaker: opens after N consecutive failures,
    allows one probe after recovery_seconds (half-open), then closes on success.
    """
    def __init__(self, failure_threshold: int = 5, recovery_seconds: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self._failures: dict[str, int] = {}
        self._last_failure_time: dict[str, float] = {}
        self._lock = asyncio.Lock()

    def _key(self, name: str) -> str:
        return name

    async def call(self, key: str, func: Callable[[], Awaitable[T]]) -> T:
        async with self._lock:
            failures = self._failures.get(key, 0)
            last_fail = self._last_failure_time.get(key, 0.0)
            now = time.monotonic()
            if failures >= self.failure_threshold:
                if now - last_fail < self.recovery_seconds:
                    raise CircuitBreakerOpenError(
                        f"Circuit open for {key} (failures={failures}, try again after {self.recovery_seconds}s)"
                    )
                # half-open: allow one attempt
                pass
        try:
            result = await func()
            async with self._lock:
                self._failures[key] = 0
            return result
        except Exception as e:
            async with self._lock:
                self._failures[key] = self._failures.get(key, 0) + 1
                self._last_failure_time[key] = time.monotonic()
                logger.warning(
                    "Circuit breaker recorded failure for key=%s failures=%s: %s",
                    key, self._failures[key], e,
                )
            raise
