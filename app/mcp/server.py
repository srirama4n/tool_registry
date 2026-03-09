"""MCP server that lists and executes all tools from the registry (Streamable HTTP)."""
import logging
from typing import Any

from mcp.server.lowlevel.server import Server as MCPServer
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from mcp.types import CallToolResult, ListToolsResult, TextContent, Tool
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.types import Receive, Scope, Send

from app.models.tool_schema import tool_to_mcp_input_schema
from app.services import ToolRegistry, execute_tool, tool_result_to_mcp_content

logger = logging.getLogger(__name__)

# Max tools to expose in MCP tools/list (all registered tools up to this limit)
MCP_LIST_TOOLS_LIMIT = 10_000


def _tool_to_mcp(t: Any) -> Tool:
    """Convert our Tool model to MCP Tool type."""
    input_schema = tool_to_mcp_input_schema(t)
    output_schema = None
    if t.outputSchema and t.outputSchema.schema_:
        output_schema = t.outputSchema.schema_.model_dump()
    return Tool(
        name=t.name,
        title=t.title or t.name,
        description=t.description or "",
        inputSchema=input_schema,
        outputSchema=output_schema,
    )


def create_mcp_app(
    registry: ToolRegistry,
    mcp_path: str = "/mcp",
) -> tuple[Starlette, StreamableHTTPSessionManager]:
    """
    Build a Starlette app and session manager for MCP over Streamable HTTP.

    Returns (asgi_app, session_manager). The caller must run session_manager.run()
    in their lifespan before mounting the app, because mounted sub-apps do not
    receive lifespan events—only the parent app does.
    """
    server = MCPServer("Tool Registry Hub")

    @server.list_tools()
    async def list_tools() -> ListToolsResult:
        try:
            tools = await registry.list_all(skip=0, limit=MCP_LIST_TOOLS_LIMIT)
            mcp_tools = [_tool_to_mcp(t) for t in tools]
            logger.debug("MCP list_tools returning %d tools", len(mcp_tools))
            return ListToolsResult(tools=mcp_tools)
        except Exception as e:
            logger.exception("MCP list_tools failed: %s", e)
            return ListToolsResult(tools=[])

    @server.call_tool(validate_input=False)
    async def call_tool(name: str, arguments: dict[str, Any] | None) -> CallToolResult:
        try:
            tool = await registry.get_by_name(name)
            if not tool:
                logger.warning("MCP call_tool tool not found: name=%s", name)
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Tool not found: {name}")],
                    isError=True,
                )
            arguments = arguments or {}
            result = await execute_tool(tool, arguments)
            return CallToolResult(
                content=tool_result_to_mcp_content(
                    result,
                    tool.outputSchema.contentType if tool.outputSchema else "application/json",
                ),
                isError=False,
            )
        except Exception as e:
            logger.exception("MCP call_tool failed name=%s: %s", name, e)
            return CallToolResult(
                content=[TextContent(type="text", text=f"Tool execution error: {e!s}")],
                isError=True,
            )

    session_manager = StreamableHTTPSessionManager(
        app=server,
        event_store=None,
        json_response=True,
        stateless=True,
        security_settings=None,
    )

    class StreamableHTTPASGIApp:
        def __init__(self, sm: StreamableHTTPSessionManager):
            self.session_manager = sm

        async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
            await self.session_manager.handle_request(scope, receive, send)

    asgi_app = StreamableHTTPASGIApp(session_manager)

    mcp_starlette = Starlette(
        debug=False,
        routes=[Route("/", endpoint=asgi_app, methods=["GET", "POST", "OPTIONS"])],
    )
    return mcp_starlette, session_manager
