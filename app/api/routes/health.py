"""Health check endpoints for liveness and readiness."""
import logging

from fastapi import APIRouter, Request, Response

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", status_code=200)
async def health_live():
    """Liveness: always 200 if the process is running."""
    return {"status": "ok"}


@router.get("/health/ready", status_code=200)
async def health_ready(request: Request) -> Response:
    """
    Readiness: 200 if MongoDB (and optionally Redis) are reachable, else 503.
    Use for load balancers and orchestrators.
    """
    try:
        registry = request.app.state.registry
        checks = await registry.ping()
        mongodb_ok = checks["mongodb"]
        redis_ok = checks["redis"]
        if not mongodb_ok:
            logger.warning("Readiness: MongoDB unreachable")
            return Response(
                content='{"status":"degraded","mongodb":false,"redis":' + str(redis_ok).lower() + "}",
                status_code=503,
                media_type="application/json",
            )
        return {
            "status": "ok",
            "mongodb": mongodb_ok,
            "redis": redis_ok,
        }
    except Exception as e:
        logger.exception("Readiness check failed: %s", e)
        return Response(
            content='{"status":"error","detail":"' + str(e).replace('"', '\\"') + '"}',
            status_code=503,
            media_type="application/json",
        )
