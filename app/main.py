"""Tool Registry: FastAPI app with REST API and MCP server mounted."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import health_router, tools_router
from app.bootstrap import create_clients
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.mcp import create_mcp_app

logger = logging.getLogger(__name__)

# Configure logging at module load (before any handlers run)
configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with create_clients() as (_, __, registry):
            app.state.registry = registry
            mcp_starlette = create_mcp_app(registry, mcp_path=settings.mcp_path)
            app.mount(settings.mcp_path, mcp_starlette)
            logger.info("Tool Registry started: MCP mounted at %s", settings.mcp_path)
            yield
    except Exception as e:
        logger.exception("Lifespan error: %s", e)
        raise
    finally:
        logger.info("Tool Registry shutting down")


app = FastAPI(
    title="Tool Registry",
    description="MCP API Hub: register tools and expose them via one MCP server",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(tools_router)


@app.get("/")
async def root():
    try:
        return {
            "service": "Tool Registry",
            "docs": "/docs",
            "mcp": settings.mcp_path,
            "api": "/api/tools",
            "health": "/health",
            "health_ready": "/health/ready",
        }
    except Exception as e:
        logger.exception("Root handler error: %s", e)
        raise
