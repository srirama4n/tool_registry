import { useState } from 'react'
import { Zap, RefreshCw, Play, ChevronDown, ChevronRight, AlertCircle, CheckCircle } from 'lucide-react'
import { mcpListTools, mcpCallTool, type McpTool } from '../mcpApi'

export function McpTest() {
  const [tools, setTools] = useState<McpTool[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [argsByTool, setArgsByTool] = useState<Record<string, string>>({})
  const [resultsByTool, setResultsByTool] = useState<Record<string, { ok: boolean; text: string }>>({})

  async function handleListTools() {
    setLoading(true)
    setError(null)
    try {
      const list = await mcpListTools()
      setTools(list)
      setExpanded(null)
      setArgsByTool({})
      setResultsByTool({})
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to list tools')
      setTools([])
    } finally {
      setLoading(false)
    }
  }

  async function handleCallTool(tool: McpTool) {
    let args: Record<string, unknown> = {}
    const raw = argsByTool[tool.name]?.trim()
    if (raw) {
      try {
        args = JSON.parse(raw) as Record<string, unknown>
      } catch {
        setResultsByTool((prev) => ({
          ...prev,
          [tool.name]: { ok: false, text: 'Invalid JSON in arguments' },
        }))
        return
      }
    }
    setLoading(true)
    setError(null)
    try {
      const result = await mcpCallTool(tool.name, args)
      const text = result.content?.map((c) => c.text).join('\n') ?? ''
      setResultsByTool((prev) => ({
        ...prev,
        [tool.name]: { ok: !result.isError, text },
      }))
      setExpanded(tool.name)
    } catch (e) {
      setResultsByTool((prev) => ({
        ...prev,
        [tool.name]: { ok: false, text: e instanceof Error ? e.message : 'Call failed' },
      }))
      setExpanded(tool.name)
    } finally {
      setLoading(false)
    }
  }

  function setArgs(toolName: string, value: string) {
    setArgsByTool((prev) => ({ ...prev, [toolName]: value }))
  }

  const defaultArgs = (tool: McpTool): string => {
    const props = tool.inputSchema?.properties ?? {}
    const def: Record<string, unknown> = {}
    for (const [k, v] of Object.entries(props)) {
      if (v?.default !== undefined) def[k] = v.default
      else if (v?.type === 'string') def[k] = ''
      else if (v?.type === 'boolean') def[k] = false
      else if (v?.type === 'number' || v?.type === 'integer') def[k] = 0
    }
    return JSON.stringify(def, null, 2)
  }

  return (
    <div className="mcp-test-page">
      <div className="page-header">
        <h1>
          <Zap size={28} className="page-title-icon" />
          <span>MCP Test</span>
        </h1>
        <button
          onClick={handleListTools}
          disabled={loading}
          className="btn btn-primary"
        >
          <RefreshCw size={18} className={loading ? 'spin' : ''} />
          <span>{loading && !tools.length ? 'Connecting...' : 'List Tools'}</span>
        </button>
      </div>

      <div className="mcp-endpoint">
        <span className="mcp-endpoint-label">Endpoint:</span>
        <code className="mcp-endpoint-url">{window.location.origin}/mcp</code>
      </div>

      {error && (
        <div className="alert alert-error">
          <AlertCircle size={20} className="alert-icon" />
          <span>{error}</span>
        </div>
      )}

      {tools.length === 0 && !loading && (
        <div className="mcp-empty">
          <Zap size={48} strokeWidth={1.5} className="mcp-empty-icon" />
          <p>Click &quot;List Tools&quot; to fetch tools from the MCP endpoint</p>
        </div>
      )}

      {tools.length > 0 && (
        <div className="mcp-tool-list">
          {tools.map((tool) => {
            const isExpanded = expanded === tool.name
            const result = resultsByTool[tool.name]
            const argsValue = argsByTool[tool.name] ?? defaultArgs(tool)
            return (
              <div key={tool.name} className="mcp-tool-card">
                <div
                  className="mcp-tool-card-header"
                  onClick={() => setExpanded(isExpanded ? null : tool.name)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault()
                      setExpanded(isExpanded ? null : tool.name)
                    }
                  }}
                >
                  {isExpanded ? (
                    <ChevronDown size={20} />
                  ) : (
                    <ChevronRight size={20} />
                  )}
                  <span className="mcp-tool-name">{tool.name}</span>
                  <span className="mcp-tool-title">{tool.title || tool.name}</span>
                  {result && (
                    <span className={`mcp-tool-result-badge ${result.ok ? 'ok' : 'err'}`}>
                      {result.ok ? <CheckCircle size={14} /> : <AlertCircle size={14} />}
                      {result.ok ? 'Success' : 'Error'}
                    </span>
                  )}
                </div>
                {isExpanded && (
                  <div className="mcp-tool-card-body">
                    {tool.description && (
                      <p className="mcp-tool-desc">{tool.description}</p>
                    )}
                    {tool.inputSchema?.properties && Object.keys(tool.inputSchema.properties).length > 0 && (
                      <div className="mcp-tool-args">
                        <label>Arguments (JSON)</label>
                        <textarea
                          value={argsValue}
                          onChange={(e) => setArgs(tool.name, e.target.value)}
                          rows={6}
                          className="input mcp-args-textarea"
                          spellCheck={false}
                        />
                      </div>
                    )}
                    <button
                      onClick={() => handleCallTool(tool)}
                      disabled={loading}
                      className="btn btn-primary mcp-run-btn"
                    >
                      <Play size={16} />
                      <span>Run</span>
                    </button>
                    {result && (
                      <div className={`mcp-result ${result.ok ? 'success' : 'error'}`}>
                        <pre>{result.text}</pre>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
