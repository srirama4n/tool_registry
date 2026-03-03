"""Bootstrap: create DB, Redis, and registry for app lifespan."""
import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis

from app.core.config import settings
from app.services.registry import ToolRegistry

logger = logging.getLogger(__name__)


@asynccontextmanager
async def create_clients() -> AsyncIterator[tuple[AsyncIOMotorClient, Redis | None, ToolRegistry]]:
    """Create MongoDB client, optional Redis client, and ToolRegistry. Caller must close clients."""
    mongo_host = settings.mongodb_uri.split("@")[-1] if "@" in settings.mongodb_uri else settings.mongodb_uri
    logger.info(
        "Connecting to MongoDB at %s (serverSelectionTimeoutMS=%s, connectTimeoutMS=%s)",
        mongo_host,
        settings.mongodb_server_selection_timeout_ms,
        settings.mongodb_connect_timeout_ms,
    )
    try:
        client = AsyncIOMotorClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms,
            connectTimeoutMS=settings.mongodb_connect_timeout_ms,
        )
        db = client[settings.mongodb_db_name]
    except Exception as e:
        logger.exception(
            "MongoDB connection failed. Check: (1) Atlas IP allow list includes your IP, "
            "(2) Network/VPN allows outbound 27017, (3) Cluster is running. Error: %s",
            e,
        )
        raise

    redis_client: Redis | None = None
    try:
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        await redis_client.ping()
        logger.info("Redis cache connected at %s", settings.redis_url)
    except Exception as e:
        logger.warning("Redis unavailable, list cache disabled: %s", e)
        redis_client = None

    registry = ToolRegistry(
        db,
        redis_client=redis_client,
        tools_list_ttl_seconds=settings.redis_tools_list_ttl_seconds,
    )
    try:
        await registry.ensure_index()
        logger.debug("Registry indexes ensured")
    except Exception as e:
        if settings.mongodb_defer_index_creation:
            logger.warning(
                "MongoDB index creation failed (defer enabled). App will start; indexes created on first use. Error: %s",
                e,
            )
        else:
            logger.exception(
                "Registry setup failed. Set MONGODB_DEFER_INDEX_CREATION=true to start anyway. Error: %s",
                e,
            )
            if redis_client is not None:
                await redis_client.aclose()
            client.close()
            raise

    try:
        yield client, redis_client, registry
    finally:
        if redis_client is not None:
            try:
                await redis_client.aclose()
                logger.debug("Redis connection closed")
            except Exception as e:
                logger.warning("Error closing Redis: %s", e)
        try:
            client.close()
            logger.debug("MongoDB connection closed")
        except Exception as e:
            logger.warning("Error closing MongoDB client: %s", e)
