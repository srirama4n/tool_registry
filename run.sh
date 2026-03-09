#!/usr/bin/env bash
# Run the Tool Registry app (FastAPI + MCP at /mcp + UI at /)
# Use: ./run.sh  OR  bash run.sh  (NOT python run.sh)
cd "$(dirname "$0")"
# Kill any existing instance on port 8000 to avoid "address already in use"
if lsof -i :8000 -sTCP:LISTEN -t 2>/dev/null | grep -q .; then
  echo "Stopping existing process on port 8000..."
  lsof -i :8000 -sTCP:LISTEN -t 2>/dev/null | xargs kill -9 2>/dev/null || true
  sleep 2
fi
# Build UI if dist doesn't exist
if [ ! -d "tool-registry-ui/dist" ] && [ -d "tool-registry-ui" ]; then
  echo "Building UI..."
  (cd tool-registry-ui && npm run build) || echo "UI build skipped (npm run build failed)"
fi
exec .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
