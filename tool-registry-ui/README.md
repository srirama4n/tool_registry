# Tool Registry UI

React frontend for managing tools in the Tool Registry API.

## Prerequisites

- Node.js 18+
- Tool Registry backend running at `http://localhost:8000`

## Development

```bash
# From tool_registry root
cd tool-registry-ui
npm run dev
```

The app runs at http://localhost:5173 and proxies API requests to the backend.

## Build

```bash
npm run build
npm run preview  # preview production build
```

## Features

- **List tools** – Browse all registered tools with filters (category, tags)
- **View tool** – See full tool details including schemas
- **Register tool** – Add new tools via form
- **Edit tool** – Update existing tools
- **Delete tool** – Deregister tools
