"""FastAPI dependency injection: registry, config."""
from fastapi import Request

from app.core.config import settings
from app.services.registry import ToolRegistry


def get_registry(request: Request) -> ToolRegistry:
    """Return the tool registry from app state."""
    return request.app.state.registry


def get_settings():
    """Return app settings (for routes that need config)."""
    return settings
