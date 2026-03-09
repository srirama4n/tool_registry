# Tool Registry – MCP API Hub

A single MCP server that exposes **dynamically registered tools**. Tools are stored in MongoDB and managed via REST APIs. The same tools are listed and executable over the Model Context Protocol (MCP) at `/mcp`.

## Features

- **REST API**: Register, list, get, update, and deregister tools
- **MCP server**: One Streamable HTTP MCP endpoint; `tools/list` and `tools/call` use the registry
- **MongoDB**: Tool definitions persisted using the [Tools Schema](assets/db_diagram-79e71cdd-9e4c-44d7-918c-037d3eedb358.png) (Tool, ToolMetadata, InputSchema, ServiceEndpoints, SecurityConfig, LifecycleEvents, etc.)
- **Redis**: Cache for listing tools (read-intensive); list results are served from Redis when available and invalidated on register/update/deregister
- **Execution**: Registered tools are invoked by HTTP POST to each tool’s `endpoints.baseUrl`

## Prerequisites

- Python 3.10+
- MongoDB (local or remote)
- Redis (optional; if unavailable, list tools reads from MongoDB only)

## Setup

```bash
cd tool_registry
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Configuration

Environment variables (optional; defaults shown):

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URI` | `mongodb://localhost:27017` | MongoDB connection string |
| `MONGODB_DB_NAME` | `tool_registry` | Database name |
| `MONGODB_SERVER_SELECTION_TIMEOUT_MS` | `60000` | MongoDB server selection timeout (ms); increase for Atlas/slow networks |
| `MONGODB_CONNECT_TIMEOUT_MS` | `60000` | MongoDB connect timeout (ms) |
| `MONGODB_DEFER_INDEX_CREATION` | `false` | If `true`, app starts even when MongoDB is unreachable; indexes created on first use |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis URL for list-tools cache |
| `REDIS_TOOLS_LIST_TTL_SECONDS` | `60` | TTL in seconds for cached tool list |
| `RETRY_MAX_ATTEMPTS` | `3` | Max retries for transient failures (DB, tool HTTP) |
| `RETRY_MIN_WAIT_SECONDS` | `0.5` | Min backoff between retries |
| `RETRY_MAX_WAIT_SECONDS` | `8` | Max backoff between retries |
| `CIRCUIT_BREAKER_FAILURE_THRESHOLD` | `5` | Failures before opening circuit per tool |
| `CIRCUIT_BREAKER_RECOVERY_SECONDS` | `60` | Seconds before half-open (retry one call) |
| `TOOL_EXECUTION_TIMEOUT_SECONDS` | `30` | HTTP timeout for tool endpoint calls |
| `RATE_LIMIT_PER_MINUTE` | `60` | API requests per minute per IP (returns 429 when exceeded) |
| `BULKHEAD_MAX_CONCURRENT_PER_TOOL` | `10` | Max concurrent executions per tool |
| `REDIS_CONNECT_TIMEOUT_SECONDS` | `5` | Redis connect timeout |
| `REDIS_CONNECT_RETRY_ATTEMPTS` | `3` | Retries for Redis connect on startup |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `HOST` | `0.0.0.0` | Bind host |
| `PORT` | `8000` | Bind port |
| `MCP_PATH` | `/mcp` | Path where MCP is mounted |

Create a `.env` file or export these as needed.

## Run

From the project root:

```bash
./run.sh
```

Or with uvicorn directly (ensure you're in the project directory first):

```bash
cd /path/to/tool_registry
.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
```

- **UI**: http://localhost:8000/ (tool management interface)  
- **API docs**: http://localhost:8000/docs  
- **MCP**: http://localhost:8000/mcp (Streamable HTTP)  
- **Health (liveness)**: http://localhost:8000/health  
- **Health (readiness)**: http://localhost:8000/health/ready  

The UI is built and served from the same server. On first run, `run.sh` builds the UI automatically if `tool-registry-ui/dist` doesn't exist. To run the UI in dev mode with hot reload:

```bash
cd tool-registry-ui
npm install && npm run dev
```

The dev UI runs at http://localhost:5173 and proxies API requests to the backend. See `tool-registry-ui/README.md` for details.  

## Resilience

- **Retry with exponential backoff**: Transient failures (connection/timeout, MongoDB/Redis/tool HTTP) are retried (configurable attempts and backoff).
- **Circuit breaker**: Per-tool execution; after N consecutive failures the circuit opens and calls fail fast until recovery_seconds, then one probe is allowed.
- **Rate limiting**: API requests are throttled per IP (configurable requests/minute); returns 429 when exceeded.
- **Bulkhead**: Max concurrent executions per tool (configurable); prevents one tool from exhausting resources.
- **Redis connect retry**: Retries Redis connection on startup with timeout and configurable attempts.
- **Health checks**: `/health` (liveness, always 200); `/health/ready` (readiness, 503 if MongoDB unreachable).

## REST API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/tools` | Register a tool (body: full Tool JSON) |
| `GET` | `/api/tools` | List tools (query: `category`, `tags`, `skip`, `limit`) |
| `GET` | `/api/tools/{name}` | Get one tool by name |
| `PUT` | `/api/tools/{name}` | Update a tool |
| `DELETE` | `/api/tools/{name}` | Deregister a tool |

### Example: Register a tool

```bash
curl -X POST http://localhost:8000/api/tools \
  -H "Content-Type: application/json" \
  -d '{
    "name": "weather",
    "description": "Get weather for a city",
    "inputSchema": {
      "type": "object",
      "properties": {
        "city": { "type": "string", "description": "City name" }
      },
      "required": ["city"]
    },
    "endpoints": {
      "baseUrl": "https://your-service.com",
      "customEndpoints": { "invoke": "/run/weather" }
    }
  }'
```

If `customEndpoints.invoke` (or `execute`) is set, tool execution POSTs to `baseUrl + that path` with body `{"arguments": {...}}`. Otherwise it POSTs to `baseUrl/`.

## MCP

- **Endpoint**: `http://localhost:8000/mcp` (Streamable HTTP)
- **tools/list**: Returns all tools currently in the registry
- **tools/call**: Looks up the tool by name, then calls its `endpoints.baseUrl` (and optional invoke path) with the given arguments

Use any MCP client (e.g. MCP Inspector, Claude Code) and connect to `http://localhost:8000/mcp`.

## Project layout

```
tool_registry/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan, router include
│   ├── bootstrap.py         # Create DB, Redis, registry (lifespan wiring)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py        # Settings from env
│   │   └── logging_config.py # Logging setup (LOG_LEVEL)
│   ├── models/
│   │   ├── __init__.py
│   │   └── tool_schema.py   # Tool, ToolMetadata, InputSchema, etc.
│   ├── services/
│   │   ├── __init__.py
│   │   ├── registry.py      # MongoDB CRUD + Redis cache for tools
│   │   └── execution.py     # Invoke tool via HTTP (baseUrl)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py          # get_registry, get_settings
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── tools.py     # REST routes for tools
│   └── mcp/
│       ├── __init__.py
│       └── server.py        # MCP Streamable HTTP (list_tools / call_tool)
├── requirements.txt
└── README.md
```

## License

MIT
