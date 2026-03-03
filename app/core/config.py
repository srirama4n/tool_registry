"""Application configuration from environment."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "tool_registry"
    # Timeouts in ms (increase if Atlas/slow network; default 60s)
    mongodb_server_selection_timeout_ms: int = 60_000
    mongodb_connect_timeout_ms: int = 60_000
    # If True, app starts even when ensure_index fails (e.g. MongoDB unreachable); indexes created on first use
    mongodb_defer_index_creation: bool = False

    # Redis (cache for list tools - read-intensive)
    redis_url: str = "redis://localhost:6379/0"
    redis_tools_list_ttl_seconds: int = 60

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # MCP mount path
    mcp_path: str = "/mcp"

    # Logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    log_level: str = "INFO"

    # Resilience: retry
    retry_max_attempts: int = 3
    retry_min_wait_seconds: float = 0.5
    retry_max_wait_seconds: float = 8.0

    # Resilience: circuit breaker (per-tool execution)
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_seconds: float = 60.0

    # Resilience: tool execution timeout
    tool_execution_timeout_seconds: float = 30.0


settings = Settings()
