import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Pencil, Box, Zap, Database, Shield, FileJson, Lock, KeyRound, ShieldCheck } from 'lucide-react'
import { getTool } from '../api'
import type { Tool } from '../types'

export function ToolDetail() {
  const { name } = useParams<{ name: string }>()
  const [tool, setTool] = useState<Tool | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!name) return
    let cancelled = false
    setLoading(true)
    setError(null)
    getTool(name)
      .then((data) => {
        if (!cancelled) setTool(data)
      })
      .catch((e) => {
        if (!cancelled) setError(e.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [name])

  if (!name) return <p>Invalid tool</p>
  if (loading) return <p className="muted">Loading...</p>
  if (error) return <div className="alert alert-error">{error}</div>
  if (!tool) return null

  const tagsDisplay = (tool.metadata && tool.metadata.tags ? tool.metadata.tags : []).join(', ')

  return (
    <div className="tool-detail">
      <div className="page-header">
        <h1>{tool.title || tool.name}</h1>
        <div className="actions">
          <Link to={`/tools/${encodeURIComponent(tool.name)}/edit`} className="btn btn-primary">
            <Pencil size={16} />
            <span>Edit</span>
          </Link>
          <Link to="/" className="btn">
            <ArrowLeft size={16} />
            <span>Back</span>
          </Link>
        </div>
      </div>

      <div className="detail-section">
        <h2><Box size={18} /> Basic</h2>
        <dl className="detail-dl">
          <dt>Name</dt>
          <dd><code>{tool.name}</code></dd>
          <dt>Version</dt>
          <dd>{tool.version || '1.0.0'}</dd>
          <dt>Description</dt>
          <dd>{tool.description || '—'}</dd>
          {tool.metadata && tool.metadata.category && (
            <>
              <dt>Category</dt>
              <dd>{tool.metadata.category}</dd>
            </>
          )}
          {tagsDisplay && (
            <>
              <dt>Tags</dt>
              <dd>{tagsDisplay}</dd>
            </>
          )}
        </dl>
      </div>

      <div className="detail-section">
        <h2><Zap size={18} /> Endpoints</h2>
        <dl className="detail-dl">
          <dt>Base URL</dt>
          <dd><code>{tool.endpoints && tool.endpoints.baseUrl ? tool.endpoints.baseUrl : '—'}</code></dd>
          {tool.endpoints && tool.endpoints.healthEndpoint && (
            <>
              <dt>Health</dt>
              <dd><code>{tool.endpoints.healthEndpoint}</code></dd>
            </>
          )}
          {tool.endpoints && tool.endpoints.customEndpoints && Object.keys(tool.endpoints.customEndpoints).length > 0 && (
            <>
              <dt>Custom</dt>
              <dd>
                <pre>{JSON.stringify(tool.endpoints.customEndpoints, null, 2)}</pre>
              </dd>
            </>
          )}
        </dl>
      </div>

      <div className="detail-section">
        <h2><FileJson size={18} /> Input Schema</h2>
        <pre className="code-block">{JSON.stringify(tool.inputSchema, null, 2)}</pre>
      </div>

      <div className="detail-section">
        <h2><Database size={18} /> Output Schema</h2>
        {tool.outputSchema ? (
          <pre className="code-block">{JSON.stringify(tool.outputSchema, null, 2)}</pre>
        ) : (
          <p className="muted">Not defined</p>
        )}
      </div>

      <div className="detail-section">
        <h2><Shield size={18} /> Security</h2>
        {tool.security && (tool.security.authType || tool.security.ssl || tool.security.oauth || tool.security.jwt || (tool.security.allowedOrigins?.length ?? 0) > 0) ? (
          <div className="security-detail">
            <div className="security-badges">
              {tool.security.authType ? (
                <span className="security-badge">{tool.security.authType}</span>
              ) : (
                <span className="security-badge muted">None</span>
              )}
            </div>
            {tool.security.authType && (
              <dl className="detail-dl">
                <dt>Auth Type</dt>
                <dd>{tool.security.authType}</dd>
              </dl>
            )}
            {tool.security.ssl && (
              <div className="security-subsection">
                <h3><Lock size={14} /> SSL / TLS</h3>
                <dl className="detail-dl">
                  <dt>Verify Cert</dt>
                  <dd>{String(tool.security.ssl.verifyCert ?? true)}</dd>
                  {tool.security.ssl.certPath && (
                    <>
                      <dt>Cert Path</dt>
                      <dd><code>{tool.security.ssl.certPath}</code></dd>
                    </>
                  )}
                  {tool.security.ssl.keyPath && (
                    <>
                      <dt>Key Path</dt>
                      <dd><code>{tool.security.ssl.keyPath}</code></dd>
                    </>
                  )}
                  {tool.security.ssl.caPath && (
                    <>
                      <dt>CA Path</dt>
                      <dd><code>{tool.security.ssl.caPath}</code></dd>
                    </>
                  )}
                  {tool.security.ssl.tlsVersion && (
                    <>
                      <dt>TLS Version</dt>
                      <dd>{tool.security.ssl.tlsVersion}</dd>
                    </>
                  )}
                </dl>
              </div>
            )}
            {tool.security.oauth && (
              <div className="security-subsection">
                <h3><KeyRound size={14} /> OAuth</h3>
                <dl className="detail-dl">
                  {tool.security.oauth.tokenUrl && (
                    <>
                      <dt>Token URL</dt>
                      <dd><code>{tool.security.oauth.tokenUrl}</code></dd>
                    </>
                  )}
                  {tool.security.oauth.authorizationUrl && (
                    <>
                      <dt>Authorization URL</dt>
                      <dd><code>{tool.security.oauth.authorizationUrl}</code></dd>
                    </>
                  )}
                  {tool.security.oauth.clientId && (
                    <>
                      <dt>Client ID</dt>
                      <dd><code>{tool.security.oauth.clientId}</code></dd>
                    </>
                  )}
                  {tool.security.oauth.grantType && (
                    <>
                      <dt>Grant Type</dt>
                      <dd>{tool.security.oauth.grantType}</dd>
                    </>
                  )}
                  {tool.security.oauth.scopes && tool.security.oauth.scopes.length > 0 && (
                    <>
                      <dt>Scopes</dt>
                      <dd>{tool.security.oauth.scopes.join(', ')}</dd>
                    </>
                  )}
                </dl>
              </div>
            )}
            {tool.security.jwt && (
              <div className="security-subsection">
                <h3><ShieldCheck size={14} /> JWT</h3>
                <dl className="detail-dl">
                  {tool.security.jwt.issuer && (
                    <>
                      <dt>Issuer</dt>
                      <dd><code>{tool.security.jwt.issuer}</code></dd>
                    </>
                  )}
                  {tool.security.jwt.audience && (
                    <>
                      <dt>Audience</dt>
                      <dd><code>{tool.security.jwt.audience}</code></dd>
                    </>
                  )}
                  {tool.security.jwt.jwksUrl && (
                    <>
                      <dt>JWKS URL</dt>
                      <dd><code>{tool.security.jwt.jwksUrl}</code></dd>
                    </>
                  )}
                  {tool.security.jwt.algorithm && (
                    <>
                      <dt>Algorithm</dt>
                      <dd>{tool.security.jwt.algorithm}</dd>
                    </>
                  )}
                  {tool.security.jwt.headerName && (
                    <>
                      <dt>Header Name</dt>
                      <dd><code>{tool.security.jwt.headerName}</code></dd>
                    </>
                  )}
                </dl>
              </div>
            )}
            {tool.security.allowedOrigins && tool.security.allowedOrigins.length > 0 && (
              <dl className="detail-dl">
                <dt>Allowed Origins</dt>
                <dd>{tool.security.allowedOrigins.join(', ')}</dd>
              </dl>
            )}
          </div>
        ) : (
          <p className="muted">No security configured</p>
        )}
      </div>
    </div>
  )
}
