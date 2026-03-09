"""Bootstrap: MongoDB, Redis, and ToolRegistry clients for app lifespan and scripts."""
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import certifi
import redis.asyncio as redis
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.services.registry import ToolRegistry

logger = logging.getLogger(__name__)


@asynccontextmanager
async def create_clients():
    """
    Async context manager yielding (mongo_client, redis_client, registry).
    Used by seed_tools and by the app factory lifespan.
    """
    mongo_client = AsyncIOMotorClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout_ms,
        connectTimeoutMS=settings.mongodb_connect_timeout_ms,
        tlsCAFile=certifi.where(),
    )
    db = mongo_client[settings.mongodb_db_name]

    redis_client = None
    for attempt in range(1, settings.redis_connect_retry_attempts + 1):
        try:
            redis_client = redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=settings.redis_connect_timeout_seconds,
                socket_timeout=10,
            )
            await asyncio.wait_for(redis_client.ping(), settings.redis_connect_timeout_seconds)
            logger.debug("Redis connected")
            break
        except Exception as e:
            logger.warning("Redis connect attempt %d/%d failed: %s", attempt, settings.redis_connect_retry_attempts, e)
            if attempt < settings.redis_connect_retry_attempts:
                await asyncio.sleep(1)
            else:
                redis_client = None  # Run without cache

    registry = ToolRegistry(
        db=db,
        redis_client=redis_client,
        tools_list_ttl_seconds=settings.redis_tools_list_ttl_seconds,
    )

    # Warm up MongoDB connection (Motor connects lazily; Atlas can take 30-60s to resume)
    try:
        await db.client.admin.command("ping")
        logger.info("MongoDB connected")
    except Exception as e:
        logger.warning("MongoDB warmup failed (first request may be slow): %s", e)

    try:
        yield mongo_client, redis_client, registry
    finally:
        if redis_client:
            await redis_client.aclose()
        mongo_client.close()
