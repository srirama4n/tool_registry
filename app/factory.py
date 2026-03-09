"""Application factory: creates FastAPI app with lifespan, routers, MCP, and UI."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.staticfiles import StaticFiles

from app.api.routes import health_router, tools_router
from app.bootstrap import create_clients
from app.core.config import settings
from app.core.rate_limit import limiter
from app.mcp.server import create_mcp_app

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
UI_DIST = ROOT / "tool-registry-ui" / "dist"


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Connect MongoDB, Redis, create registry, start MCP session manager."""
    async with create_clients() as (_mongo_client, _redis_client, registry):
        app.state.registry = registry

        mcp_app, session_manager = create_mcp_app(
            registry=registry,
            mcp_path=settings.mcp_path,
        )
        # Mount MCP first (before StaticFiles) so /mcp gets POST/OPTIONS
        app.mount(settings.mcp_path, mcp_app)

        async with session_manager.run():
            logger.info("MCP session manager started")
            # Mount StaticFiles after MCP so /mcp is checked first
            if UI_DIST.exists():
                app.mount("/", StaticFiles(directory=str(UI_DIST), html=True))
            yield

    logger.info("Shutting down")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Tool Registry",
        description="MCP API Hub - Register, list, and invoke tools",
        lifespan=_lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(tools_router)

    # MCP and StaticFiles mounted in lifespan (MCP first so /mcp handles POST before StaticFiles)
    if not UI_DIST.exists():
        logger.warning("UI dist not found at %s; run ./run.sh or build UI first", UI_DIST)

    return app
