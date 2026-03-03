"""Pydantic models matching the Tools Schema / Domain Model diagram."""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict


# ---- PropertyDefinition (InputSchema.properties value) ----
class ValidationRules(BaseModel):
    minLength: int | None = None
    maxLength: int | None = None
    minimum: int | float | None = None
    maximum: int | float | None = None
    pattern: str | None = None


class PropertyDefinition(BaseModel):
    type: str  # "string" | "integer" | "boolean" | "array" | "object"
    format: str | None = None  # "date-time" | "email" | "uri" | "uuid"
    enum: list[Any] | None = None
    description: str | None = None
    default: Any = None
    validation: ValidationRules | None = None


# ---- InputSchema ----
class InputSchema(BaseModel):
    type: str = "object"
    properties: dict[str, PropertyDefinition] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)
    additionalProperties: bool | None = None


# ---- OutputSchema ----
class ResponseSchema(BaseModel):
    type: str = "object"
    properties: dict[str, Any] = Field(default_factory=dict)


class ErrorSchema(BaseModel):
    type: str = "object"
    properties: dict[str, Any] = Field(default_factory=dict)


class OutputSchema(BaseModel):
    contentType: str = "application/json"
    schema_: ResponseSchema | None = Field(None, alias="schema")
    errorSchema: ErrorSchema | None = None

    model_config = ConfigDict(populate_by_name=True)


# ---- OpenAIMetadata ----
class OpenAIMetadata(BaseModel):
    outputTemplate: str | None = None
    toolInvocationInvoking: str | None = None
    toolInvocationInvoked: bool = False
    requiresConfirmation: bool = False
    iconUrl: str | None = None


# ---- CustomMetadata ----
class CustomMetadata(BaseModel):
    model_config = ConfigDict(extra="allow")


# ---- ToolMetadata ----
class ToolMetadata(BaseModel):
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    appId: str | None = None
    created: datetime | None = None
    updated: datetime | None = None
    openAI: OpenAIMetadata | None = None
    custom: CustomMetadata | dict[str, Any] | None = None


# ---- LifecycleEvents ----
class LifecycleEvents(BaseModel):
    onRegister: str | None = None
    onDeregister: str | None = None
    onUpdate: str | None = None
    healthCheck: str | None = None


# ---- RateLimitConfig ----
class RateLimitConfig(BaseModel):
    maxRequestsPerMinute: int | None = None
    maxRequestsPerHour: int | None = None
    quotaType: str | None = None  # "fixed" | "sliding_window"


# ---- SecurityConfig ----
class SecurityConfig(BaseModel):
    authType: str | None = None  # "API_KEY" | "OAuth2" | "None"
    requiredScopes: list[str] = Field(default_factory=list)
    allowedOrigins: list[str] = Field(default_factory=list)
    rateLimit: RateLimitConfig | None = None


# ---- ServiceEndpoints ----
class ServiceEndpoints(BaseModel):
    serviceId: str | None = None
    baseUrl: str
    healthEndpoint: str | None = None
    metricsEndpoint: str | None = None
    customEndpoints: dict[str, str] = Field(default_factory=dict)


# ---- Tool (root) ----
class Tool(BaseModel):
    toolId: str | None = None
    name: str
    version: str = "1.0.0"
    title: str | None = None
    description: str = ""
    metadata: ToolMetadata | None = None
    inputSchema: InputSchema
    outputSchema: OutputSchema | None = None
    endpoints: ServiceEndpoints
    security: SecurityConfig | None = None
    lifecycle: LifecycleEvents | None = None

    model_config = ConfigDict(populate_by_name=True)


def tool_to_mcp_input_schema(t: Tool) -> dict[str, Any]:
    """Convert Tool.inputSchema to MCP/JSON Schema dict for tools/list."""
    raw = t.inputSchema.model_dump(by_alias=False)
    # Ensure properties is a plain dict of schema objects (PropertyDefinition -> dict)
    if "properties" in raw and raw["properties"]:
        raw["properties"] = {
            k: v.model_dump() if hasattr(v, "model_dump") else v
            for k, v in raw["properties"].items()
        }
    return raw
