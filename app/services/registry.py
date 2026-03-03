"""Tool registry: MongoDB-backed CRUD with Redis cache for list (read-intensive)."""
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import settings
from app.core.resilience import make_db_retry
from app.models import Tool

logger = logging.getLogger(__name__)

_db_retry = make_db_retry(
    max_attempts=settings.retry_max_attempts,
    min_wait=settings.retry_min_wait_seconds,
    max_wait=settings.retry_max_wait_seconds,
)

TOOLS_LIST_CACHE_KEY = "tools:list"


class ToolRegistry:
    """CRUD for tools in MongoDB; list_all uses Redis cache when available."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        redis_client: Any = None,
        tools_list_ttl_seconds: int = 60,
    ):
        self._coll = db.tools
        self._redis = redis_client
        self._tools_list_ttl = tools_list_ttl_seconds
        self._indexes_ensured = False

    async def ping(self) -> dict[str, bool]:
        """Check connectivity to MongoDB and Redis. For health checks."""
        mongodb_ok = False
        redis_ok = False
        try:
            await self._coll.database.client.admin.command("ping")
            mongodb_ok = True
        except Exception:
            pass
        if self._redis is not None:
            try:
                await self._redis.ping()
                redis_ok = True
            except Exception:
                pass
        return {"mongodb": mongodb_ok, "redis": redis_ok}

    async def _invalidate_list_cache(self) -> None:
        if self._redis is None:
            return
        try:
            await self._redis.delete(TOOLS_LIST_CACHE_KEY)
            logger.debug("List cache invalidated")
        except Exception as e:
            logger.warning("Cache invalidation failed: %s", e)

    @_db_retry
    async def _list_all_from_db(
        self,
        category: str | None = None,
        tags: list[str] | None = None,
    ) -> list[Tool]:
        try:
            q: dict[str, Any] = {}
            if category:
                q["metadata.category"] = category
            if tags:
                q["metadata.tags"] = {"$in": tags}
            cursor = self._coll.find(q)
            docs = await cursor.to_list(length=None)
            tools = [_doc_to_tool(d) for d in docs]
            logger.debug("Loaded %d tools from DB (category=%s, tags=%s)", len(tools), category, tags)
            return tools
        except Exception as e:
            logger.exception("_list_all_from_db failed: %s", e)
            raise

    @_db_retry
    async def ensure_index(self) -> None:
        try:
            await self._coll.create_index("name", unique=True)
            await self._coll.create_index("toolId", unique=True, sparse=True)
            self._indexes_ensured = True
            logger.debug("Registry indexes created/ensured")
        except Exception as e:
            logger.exception("ensure_index failed: %s", e)
            raise

    async def _ensure_index_once(self) -> None:
        """Create indexes once; safe to call on every request (no-op after first success)."""
        if self._indexes_ensured:
            return
        try:
            await self.ensure_index()
        except Exception:
            pass  # Logged in ensure_index; allow request to proceed and fail on DB op if needed

    async def register(self, tool: Tool) -> Tool:
        await self._ensure_index_once()
        try:
            now = datetime.now(timezone.utc)
            doc = tool.model_dump(mode="json", by_alias=False)
            if not doc.get("toolId"):
                doc["toolId"] = str(uuid.uuid4())
            if tool.metadata is None:
                doc["metadata"] = {"created": now, "updated": now}
            else:
                doc["metadata"] = doc.get("metadata") or {}
                doc["metadata"]["created"] = doc["metadata"].get("created") or now
                doc["metadata"]["updated"] = now
            doc["metadata"]["updated"] = now
            await self._coll.update_one(
                {"name": tool.name},
                {"$set": doc},
                upsert=True,
            )
            await self._invalidate_list_cache()
            result = await self.get_by_name(tool.name) or tool
            logger.info("Registered tool: name=%s", tool.name)
            return result
        except Exception as e:
            logger.exception("register failed for name=%s: %s", tool.name, e)
            raise

    async def get_by_name(self, name: str) -> Tool | None:
        await self._ensure_index_once()
        try:
            doc = await self._coll.find_one({"name": name})
            return _doc_to_tool(doc) if doc else None
        except Exception as e:
            logger.exception("get_by_name failed for name=%s: %s", name, e)
            raise

    async def get_by_tool_id(self, tool_id: str) -> Tool | None:
        await self._ensure_index_once()
        try:
            doc = await self._coll.find_one({"toolId": tool_id})
            return _doc_to_tool(doc) if doc else None
        except Exception as e:
            logger.exception("get_by_tool_id failed for tool_id=%s: %s", tool_id, e)
            raise

    async def list_all(
        self,
        category: str | None = None,
        tags: list[str] | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Tool]:
        await self._ensure_index_once()
        try:
            tools: list[Tool] = []
            if self._redis is not None:
                try:
                    raw = await self._redis.get(TOOLS_LIST_CACHE_KEY)
                    if raw is not None:
                        data = json.loads(raw)
                        tools = [Tool.model_validate(d) for d in data]
                        logger.debug("List cache hit: %d tools", len(tools))
                except Exception as e:
                    logger.warning("Redis list cache read failed: %s", e)
            if not tools:
                tools = await self._list_all_from_db(category=None, tags=None)
                if self._redis is not None:
                    try:
                        payload = json.dumps([t.model_dump(mode="json", by_alias=False) for t in tools])
                        await self._redis.set(TOOLS_LIST_CACHE_KEY, payload, ex=self._tools_list_ttl)
                        logger.debug("List cache populated: %d tools, ttl=%ds", len(tools), self._tools_list_ttl)
                    except Exception as e:
                        logger.warning("Redis list cache write failed: %s", e)
            if category:
                tools = [t for t in tools if t.metadata and t.metadata.category == category]
            if tags:
                tools = [t for t in tools if t.metadata and t.metadata.tags and set(tags) & set(t.metadata.tags)]
            result = tools[skip : skip + limit]
            logger.debug("list_all returning %d tools (skip=%s, limit=%s)", len(result), skip, limit)
            return result
        except Exception as e:
            logger.exception("list_all failed: %s", e)
            raise

    async def update(self, name: str, tool: Tool) -> Tool | None:
        await self._ensure_index_once()
        try:
            existing = await self._coll.find_one({"name": name})
            if not existing:
                logger.debug("update: tool not found name=%s", name)
                return None
            now = datetime.now(timezone.utc)
            doc = tool.model_dump(mode="json", by_alias=False)
            doc["metadata"] = doc.get("metadata") or {}
            doc["metadata"]["updated"] = now
            if existing.get("metadata"):
                doc["metadata"]["created"] = existing["metadata"].get("created") or now
            await self._coll.update_one({"name": name}, {"$set": doc})
            await self._invalidate_list_cache()
            result = await self.get_by_name(name)
            logger.info("Updated tool: name=%s", name)
            return result
        except Exception as e:
            logger.exception("update failed for name=%s: %s", name, e)
            raise

    async def deregister(self, name: str) -> bool:
        await self._ensure_index_once()
        try:
            result = await self._coll.delete_one({"name": name})
            if result.deleted_count > 0:
                await self._invalidate_list_cache()
                logger.info("Deregistered tool: name=%s", name)
            else:
                logger.debug("deregister: tool not found name=%s", name)
            return result.deleted_count > 0
        except Exception as e:
            logger.exception("deregister failed for name=%s: %s", name, e)
            raise


def _doc_to_tool(doc: dict[str, Any]) -> Tool:
    try:
        if not doc:
            raise ValueError("empty doc")
        doc = {k: v for k, v in doc.items() if k != "_id"}
        if doc.get("metadata") and isinstance(doc["metadata"], dict):
            for t in ("created", "updated"):
                v = doc["metadata"].get(t)
                if hasattr(v, "isoformat"):
                    doc["metadata"][t] = v.isoformat()
        return Tool.model_validate(doc)
    except Exception as e:
        logger.exception("_doc_to_tool failed: %s", e)
        raise
