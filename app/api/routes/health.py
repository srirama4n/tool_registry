"""Health check endpoints for liveness and readiness."""
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.deps import get_registry
from app.services.registry import ToolRegistry

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_live():
    """Liveness: always 200 if the process is running."""
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready(registry: ToolRegistry = Depends(get_registry)):
    """
    Readiness: 200 if MongoDB (and optionally Redis) are reachable, else 503.
    Use for load balancers and orchestrators.
    """
    try:
        checks = await registry.ping()
        mongodb_ok = checks["mongodb"]
        redis_ok = checks["redis"]
        if not mongodb_ok:
            logger.warning("Readiness: MongoDB unreachable")
            return JSONResponse(
                status_code=503,
                content={"status": "degraded", "mongodb": False, "redis": redis_ok},
            )
        return {"status": "ok", "mongodb": mongodb_ok, "redis": redis_ok}
    except Exception as e:
        logger.exception("Readiness check failed: %s", e)
        return JSONResponse(
            status_code=503,
            content={"status": "error", "detail": str(e)},
        )
