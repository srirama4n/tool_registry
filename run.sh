#!/usr/bin/env bash
# Run the Tool Registry app (FastAPI + MCP at /mcp)
cd "$(dirname "$0")"
exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
