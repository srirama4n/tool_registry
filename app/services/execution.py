"""Execute a registered tool by calling its service endpoint (baseUrl + arguments)."""
import asyncio
import logging
from typing import Any

import httpx

from app.core.config import settings
from app.core.resilience import CircuitBreaker, CircuitBreakerOpenError, make_async_retry
from app.models import Tool

logger = logging.getLogger(__name__)

# Per-tool circuit breaker: opens after N failures, recovers after recovery_seconds
_circuit_breaker = CircuitBreaker(
    failure_threshold=settings.circuit_breaker_failure_threshold,
    recovery_seconds=settings.circuit_breaker_recovery_seconds,
)

# Bulkhead: per-tool semaphores to limit concurrent executions
_bulkhead_limit = max(1, settings.bulkhead_max_concurrent_per_tool)
_semaphores: dict[str, asyncio.Semaphore] = {}
_semaphores_lock = asyncio.Lock()


async def _get_semaphore(tool_name: str) -> asyncio.Semaphore:
    """Get or create semaphore for tool (async-safe)."""
    async with _semaphores_lock:
        if tool_name not in _semaphores:
            _semaphores[tool_name] = asyncio.Semaphore(_bulkhead_limit)
        return _semaphores[tool_name]


@make_async_retry(
    max_attempts=settings.retry_max_attempts,
    min_wait=settings.retry_min_wait_seconds,
    max_wait=settings.retry_max_wait_seconds,
)
async def _execute_tool_request(url: str, tool_name: str, arguments: dict[str, Any]) -> str:
    """Single attempt at tool HTTP call; retry decorator handles transient failures."""
    async with httpx.AsyncClient(timeout=settings.tool_execution_timeout_seconds) as client:
        resp = await client.post(
            url,
            json={"arguments": arguments} if arguments else {},
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        return resp.text


async def execute_tool(tool: Tool, arguments: dict[str, Any]) -> str:
    """
    Invoke the tool's endpoint (baseUrl) with the given arguments.
    Uses retry (exponential backoff), circuit breaker, and bulkhead (concurrency limit) per tool.
    Returns the response body as string; caller can wrap in MCP content.
    """
    base_url = tool.endpoints.baseUrl.rstrip("/")
    custom = tool.endpoints.customEndpoints or {}
    invoke_path = custom.get("invoke") or custom.get("execute") or "/"
    url = f"{base_url}{invoke_path}" if invoke_path.startswith("/") else f"{base_url}/{invoke_path}"
    logger.debug("Executing tool name=%s url=%s", tool.name, url)
    sem = await _get_semaphore(tool.name)
    try:
        async with sem:
            result = await _circuit_breaker.call(
                tool.name, lambda: _execute_tool_request(url, tool.name, arguments)
            )
        logger.info("Tool executed successfully: name=%s", tool.name)
        return result
    except CircuitBreakerOpenError as e:
        logger.warning("Circuit open for tool name=%s: %s", tool.name, e)
        raise
    except httpx.HTTPStatusError as e:
        logger.error(
            "Tool endpoint HTTP error name=%s status=%s response=%s",
            tool.name, e.response.status_code, (e.response.text or "")[:500],
        )
        raise
    except httpx.RequestError as e:
        logger.exception("Tool endpoint request error name=%s: %s", tool.name, e)
        raise
    except Exception as e:
        logger.exception("execute_tool failed name=%s: %s", tool.name, e)
        raise


def tool_result_to_mcp_content(result: str, content_type: str = "application/json") -> list[dict[str, Any]]:
    """Format execution result as MCP CallToolResult content."""
    return [{"type": "text", "text": result}]
