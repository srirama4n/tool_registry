"""REST API: register, list, get, update, deregister tools."""
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_registry
from app.models import Tool
from app.services.registry import ToolRegistry

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.post("", response_model=dict, status_code=201)
async def register_tool(tool: Tool, registry: ToolRegistry = Depends(get_registry)):
    """Register a new tool (or replace existing one with same name)."""
    try:
        created = await registry.register(tool)
        return created.model_dump(mode="json", by_alias=False)
    except Exception as e:
        logger.exception("register_tool failed name=%s: %s", tool.name, e)
        raise HTTPException(status_code=500, detail=f"Registration failed: {e!s}")


@router.get("", response_model=list)
async def list_tools(
    category: str | None = None,
    tags: str | None = None,
    skip: int = 0,
    limit: int = 100,
    registry: ToolRegistry = Depends(get_registry),
):
    """List registered tools. Optional filters: category, tags (comma-separated)."""
    try:
        tag_list = [t.strip() for t in tags.split(",")] if tags else None
        tools = await registry.list_all(category=category, tags=tag_list, skip=skip, limit=limit)
        return [t.model_dump(mode="json", by_alias=False) for t in tools]
    except Exception as e:
        logger.exception("list_tools failed: %s", e)
        raise HTTPException(status_code=500, detail=f"List tools failed: {e!s}")


@router.get("/{name}", response_model=dict)
async def get_tool(name: str, registry: ToolRegistry = Depends(get_registry)):
    """Get a tool by name."""
    try:
        tool = await registry.get_by_name(name)
        if not tool:
            logger.debug("get_tool not found: name=%s", name)
            raise HTTPException(status_code=404, detail="Tool not found")
        return tool.model_dump(mode="json", by_alias=False)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_tool failed name=%s: %s", name, e)
        raise HTTPException(status_code=500, detail=f"Get tool failed: {e!s}")


@router.put("/{name}", response_model=dict)
async def update_tool(name: str, tool: Tool, registry: ToolRegistry = Depends(get_registry)):
    """Update an existing tool by name."""
    try:
        updated = await registry.update(name, tool)
        if not updated:
            logger.debug("update_tool not found: name=%s", name)
            raise HTTPException(status_code=404, detail="Tool not found")
        return updated.model_dump(mode="json", by_alias=False)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("update_tool failed name=%s: %s", name, e)
        raise HTTPException(status_code=500, detail=f"Update failed: {e!s}")


@router.delete("/{name}", status_code=204)
async def deregister_tool(name: str, registry: ToolRegistry = Depends(get_registry)):
    """Deregister a tool by name."""
    try:
        deleted = await registry.deregister(name)
        if not deleted:
            logger.debug("deregister_tool not found: name=%s", name)
            raise HTTPException(status_code=404, detail="Tool not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("deregister_tool failed name=%s: %s", name, e)
        raise HTTPException(status_code=500, detail=f"Deregister failed: {e!s}")
