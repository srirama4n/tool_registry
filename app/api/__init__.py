"""API: dependencies and route modules."""
from app.api.deps import get_registry, get_settings
from app.api.routes import health_router, tools_router

__all__ = ["get_registry", "get_settings", "health_router", "tools_router"]
