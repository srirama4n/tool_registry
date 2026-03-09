"""REST API: register, list, get, update, deregister tools."""
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.api.deps import get_registry
from app.core.config import settings
from app.core.rate_limit import get_rate_limit_string, limiter
from app.models import Tool
from app.services.registry import ToolRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tools", tags=["tools"])
_rate_limit = get_rate_limit_string()


@router.post("", response_model=dict, status_code=201)
@limiter.limit(_rate_limit)
async def register_tool(
    request: Request,
    tool: Tool,
    registry: ToolRegistry = Depends(get_registry),
):
    """Register a new tool (or replace existing one with same name)."""
    try:
        created = await asyncio.wait_for(registry.register(tool), timeout=settings.api_request_timeout_seconds)
        return created.model_dump(mode="json", by_alias=False)
    except asyncio.TimeoutError:
        logger.warning("register_tool timed out after %ss", settings.api_request_timeout_seconds)
        raise HTTPException(status_code=504, detail="Request timed out; MongoDB may be unreachable. Try again.") from None
    except Exception as e:
        logger.exception("register_tool failed name=%s: %s", tool.name, e)
        raise HTTPException(status_code=500, detail=f"Registration failed: {e!s}")


@router.get("", response_model=list)
@limiter.limit(_rate_limit)
async def list_tools(
    request: Request,
    registry: ToolRegistry = Depends(get_registry),
    category: str | None = Query(None, description="Filter by category"),
    tags: str | None = Query(None, description="Comma-separated tags"),
    skip: int = Query(0, ge=0, description="Number of tools to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max tools to return"),
):
    """List registered tools. Optional filters: category, tags (comma-separated)."""
    try:
        tag_list = [t.strip() for t in tags.split(",")] if tags else None
        tools = await asyncio.wait_for(
            registry.list_all(category=category, tags=tag_list, skip=skip, limit=limit),
            timeout=settings.api_request_timeout_seconds,
        )
        return [t.model_dump(mode="json", by_alias=False) for t in tools]
    except asyncio.TimeoutError:
        logger.warning("list_tools timed out after %ss (MongoDB/Atlas may be slow or unreachable)", settings.api_request_timeout_seconds)
        raise HTTPException(status_code=504, detail="Request timed out; MongoDB may be unreachable or Atlas cluster may be resuming. Try again in a moment.") from None
    except Exception as e:
        logger.exception("list_tools failed: %s", e)
        raise HTTPException(status_code=500, detail=f"List tools failed: {e!s}")


@router.get("/{name}", response_model=dict)
@limiter.limit(_rate_limit)
async def get_tool(
    request: Request,
    name: str,
    registry: ToolRegistry = Depends(get_registry),
):
    """Get a tool by name."""
    try:
        tool = await asyncio.wait_for(registry.get_by_name(name), timeout=settings.api_request_timeout_seconds)
        if not tool:
            logger.debug("get_tool not found: name=%s", name)
            raise HTTPException(status_code=404, detail="Tool not found")
        return tool.model_dump(mode="json", by_alias=False)
    except HTTPException:
        raise
    except asyncio.TimeoutError:
        logger.warning("get_tool timed out for name=%s", name)
        raise HTTPException(status_code=504, detail="Request timed out; MongoDB may be unreachable. Try again.") from None
    except Exception as e:
        logger.exception("get_tool failed name=%s: %s", name, e)
        raise HTTPException(status_code=500, detail=f"Get tool failed: {e!s}")


@router.put("/{name}", response_model=dict)
@limiter.limit(_rate_limit)
async def update_tool(
    request: Request,
    name: str,
    tool: Tool,
    registry: ToolRegistry = Depends(get_registry),
):
    """Update an existing tool by name."""
    try:
        updated = await asyncio.wait_for(registry.update(name, tool), timeout=settings.api_request_timeout_seconds)
        if not updated:
            logger.debug("update_tool not found: name=%s", name)
            raise HTTPException(status_code=404, detail="Tool not found")
        return updated.model_dump(mode="json", by_alias=False)
    except HTTPException:
        raise
    except asyncio.TimeoutError:
        logger.warning("update_tool timed out for name=%s", name)
        raise HTTPException(status_code=504, detail="Request timed out; MongoDB may be unreachable. Try again.") from None
    except Exception as e:
        logger.exception("update_tool failed name=%s: %s", name, e)
        raise HTTPException(status_code=500, detail=f"Update failed: {e!s}")


@router.delete("/{name}", status_code=204)
@limiter.limit(_rate_limit)
async def deregister_tool(
    request: Request,
    name: str,
    registry: ToolRegistry = Depends(get_registry),
):
    """Deregister a tool by name."""
    try:
        deleted = await asyncio.wait_for(registry.deregister(name), timeout=settings.api_request_timeout_seconds)
        if not deleted:
            logger.debug("deregister_tool not found: name=%s", name)
            raise HTTPException(status_code=404, detail="Tool not found")
    except HTTPException:
        raise
    except asyncio.TimeoutError:
        logger.warning("deregister_tool timed out for name=%s", name)
        raise HTTPException(status_code=504, detail="Request timed out; MongoDB may be unreachable. Try again.") from None
    except Exception as e:
        logger.exception("deregister_tool failed name=%s: %s", name, e)
        raise HTTPException(status_code=500, detail=f"Deregister failed: {e!s}")
