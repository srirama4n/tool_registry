/** MCP Streamable HTTP client - tools/list and tools/call */

const MCP_BASE = '/mcp'

interface JsonRpcRequest {
  jsonrpc: '2.0'
  id: number
  method: string
  params?: Record<string, unknown>
}

interface JsonRpcResponse<T = unknown> {
  jsonrpc: '2.0'
  id: number
  result?: T
  error?: { code: number; message: string }
}

export interface McpTool {
  name: string
  title?: string
  description?: string
  inputSchema?: {
    type?: string
    properties?: Record<string, { type?: string; description?: string; default?: unknown }>
    required?: string[]
  }
  outputSchema?: Record<string, unknown>
}

interface ListToolsResult {
  tools: McpTool[]
  nextCursor?: string
}

interface ContentPart {
  type: 'text'
  text: string
}

interface CallToolResult {
  content: ContentPart[]
  isError: boolean
}

let requestId = 0

async function mcpRequest<T>(method: string, params?: Record<string, unknown>): Promise<T> {
  const req: JsonRpcRequest = {
    jsonrpc: '2.0',
    id: ++requestId,
    method,
    ...(params && { params }),
  }
  const res = await fetch(`${MCP_BASE}/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json, text/event-stream',
    },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error(`MCP request failed: ${res.status} ${res.statusText}`)
  const json = (await res.json()) as JsonRpcResponse<T>
  if (json.error) throw new Error(json.error.message || 'MCP error')
  if (!json.result) throw new Error('No result in MCP response')
  return json.result
}

export async function mcpListTools(): Promise<McpTool[]> {
  const result = await mcpRequest<ListToolsResult>('tools/list')
  return result.tools || []
}

export async function mcpCallTool(name: string, arguments_: Record<string, unknown>): Promise<CallToolResult> {
  return mcpRequest<CallToolResult>('tools/call', {
    name,
    arguments: arguments_,
  })
}
