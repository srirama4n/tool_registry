import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Wrench, Search, PlusCircle, Pencil, Trash2, Tag, AlertCircle } from 'lucide-react'
import { listTools, deregisterTool } from '../api'
import type { Tool } from '../types'

export function ToolList() {
  const [tools, setTools] = useState<Tool[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [category, setCategory] = useState('')
  const [tags, setTags] = useState('')
  const [deleting, setDeleting] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    listTools({ category: category || undefined, tags: tags || undefined })
      .then((data) => {
        if (!cancelled) setTools(data)
      })
      .catch((e) => {
        if (!cancelled) setError(e.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [category, tags])

  async function handleDelete(name: string) {
    if (!confirm(`Delete tool "${name}"?`)) return
    setDeleting(name)
    try {
      await deregisterTool(name)
      setTools((prev) => prev.filter((t) => t.name !== name))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Delete failed')
    } finally {
      setDeleting(null)
    }
  }

  return (
    <div className="tool-list-page">
      <div className="page-header">
        <h1>
          <Wrench size={28} className="page-title-icon" />
          <span>Tools</span>
        </h1>
        <Link to="/tools/new" className="btn btn-primary">
          <PlusCircle size={18} />
          <span>Register Tool</span>
        </Link>
      </div>

      <div className="filters">
        <div className="filter-input-wrap">
          <Search size={18} className="filter-icon" />
          <input
            type="text"
            placeholder="Filter by category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="input"
          />
        </div>
        <div className="filter-input-wrap">
          <Tag size={18} className="filter-icon" />
          <input
            type="text"
            placeholder="Filter by tags (comma-separated)"
            value={tags}
            onChange={(e) => setTags(e.target.value)}
            className="input"
          />
        </div>
      </div>

      {error && (
        <div className="alert alert-error">
          <AlertCircle size={20} className="alert-icon" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="loading-state">
          <div className="loading-spinner" />
          <p>Loading tools...</p>
        </div>
      ) : tools.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">
            <Wrench size={48} strokeWidth={1.5} />
          </div>
          <p>No tools registered yet</p>
          <p className="empty-sub">Register your first tool to get started</p>
          <Link to="/tools/new" className="btn btn-primary">
            <PlusCircle size={18} />
            <span>Register Tool</span>
          </Link>
        </div>
      ) : (
        <div className="tool-grid">
          {tools.map((tool) => (
            <div key={tool.name} className="tool-card">
              <div className="tool-card-header">
                <h3>
                  <span className="tool-card-icon">
                    <Wrench size={20} strokeWidth={1.5} />
                  </span>
                  <Link to={`/tools/${encodeURIComponent(tool.name)}`}>
                    {tool.title || tool.name}
                  </Link>
                </h3>
                <span className="badge">{tool.name}</span>
              </div>
              {tool.metadata?.category && (
                <span className="meta">
                  <Tag size={12} />
                  {tool.metadata.category}
                </span>
              )}
              <p className="tool-desc">
                {tool.description || 'No description'}
              </p>
              <div className="tool-card-actions">
                <Link to={`/tools/${encodeURIComponent(tool.name)}/edit`} className="btn btn-sm">
                  <Pencil size={14} />
                  <span>Edit</span>
                </Link>
                <button
                  onClick={() => handleDelete(tool.name)}
                  disabled={deleting === tool.name}
                  className="btn btn-sm btn-danger"
                >
                  <Trash2 size={14} />
                  <span>{deleting === tool.name ? 'Deleting...' : 'Delete'}</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
