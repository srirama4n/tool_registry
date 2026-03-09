import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { Box, Zap, FileJson, Shield, Save, X, Lock, KeyRound, ShieldCheck } from 'lucide-react'
import { getTool, registerTool, updateTool } from '../api'
import type { Tool } from '../types'

const defaultInputSchema: Tool['inputSchema'] = {
  type: 'object',
  properties: {},
  required: [],
}

export function ToolForm() {
  const { name } = useParams<{ name?: string }>()
  const navigate = useNavigate()
  const isEdit = !!name

  const [tool, setTool] = useState<Partial<Tool>>({
    name: '',
    version: '1.0.0',
    title: '',
    description: '',
    metadata: { category: '', tags: [] },
    inputSchema: defaultInputSchema,
    endpoints: { baseUrl: '' },
  })
  const [inputSchemaJson, setInputSchemaJson] = useState('')
  const [outputSchemaJson, setOutputSchemaJson] = useState('')
  const [loading, setLoading] = useState(isEdit)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!isEdit) return
    if (!name) return
    let cancelled = false
    setLoading(true)
    getTool(name)
      .then((data) => {
        if (!cancelled) {
          setTool(data)
          setInputSchemaJson(JSON.stringify(data.inputSchema, null, 2))
          setOutputSchemaJson(
            data.outputSchema ? JSON.stringify(data.outputSchema, null, 2) : ''
          )
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [isEdit, name])

  useEffect(() => {
    if (!isEdit && !inputSchemaJson) {
      setInputSchemaJson(JSON.stringify(defaultInputSchema, null, 2))
    }
  }, [isEdit])

  function parseInputSchema(): Tool['inputSchema'] | null {
    try {
      return JSON.parse(inputSchemaJson) as Tool['inputSchema']
    } catch {
      return null
    }
  }

  function buildSecurityPayload(
    sec: Tool['security']
  ): Tool['security'] | undefined {
    if (!sec) return undefined
    const ssl =
      sec.ssl?.verifyCert !== undefined ||
      sec.ssl?.certPath ||
      sec.ssl?.keyPath ||
      sec.ssl?.caPath ||
      sec.ssl?.tlsVersion
        ? { verifyCert: sec.ssl.verifyCert ?? true, ...sec.ssl }
        : undefined
    const oauth =
      sec.authType === 'OAuth2' &&
      (sec.oauth?.tokenUrl ||
        sec.oauth?.authorizationUrl ||
        sec.oauth?.clientId ||
        sec.oauth?.grantType ||
        (sec.oauth?.scopes?.length ?? 0) > 0)
        ? sec.oauth
        : undefined
    const jwt =
      sec.authType === 'JWT' &&
      (sec.jwt?.issuer ||
        sec.jwt?.audience ||
        sec.jwt?.jwksUrl ||
        sec.jwt?.algorithm ||
        sec.jwt?.headerName)
        ? sec.jwt
        : undefined
    const hasAny =
      sec.authType ||
      (sec.allowedOrigins?.length ?? 0) > 0 ||
      ssl ||
      oauth ||
      jwt
    if (!hasAny) return undefined
    return { ...sec, ssl, oauth, jwt }
  }

  function parseOutputSchema(): Tool['outputSchema'] | undefined {
    const trimmed = outputSchemaJson.trim()
    if (!trimmed) return undefined
    try {
      return JSON.parse(outputSchemaJson) as Tool['outputSchema']
    } catch {
      return undefined
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    const schema = parseInputSchema()
    if (!schema) {
      setError('Invalid JSON in Input Schema')
      return
    }
    const outputSchema = parseOutputSchema()
    if (outputSchemaJson.trim() && !outputSchema) {
      setError('Invalid JSON in Output Schema')
      return
    }
    const payload: Tool = {
      name: tool.name!.trim(),
      version: tool.version || '1.0.0',
      title: tool.title?.trim() || undefined,
      description: tool.description?.trim() || '',
      metadata:
        tool.metadata?.category || (tool.metadata?.tags && (tool.metadata.tags as string[]).length)
          ? {
              category: tool.metadata?.category?.trim() || undefined,
              tags: Array.isArray(tool.metadata?.tags)
                ? tool.metadata.tags
                : String(tool.metadata?.tags || '')
                    .split(',')
                    .map((s) => s.trim())
                    .filter(Boolean),
            }
          : undefined,
      inputSchema: schema,
      outputSchema: outputSchema,
      endpoints: {
        serviceId: tool.endpoints?.serviceId,
        baseUrl: tool.endpoints!.baseUrl!.trim(),
        healthEndpoint: tool.endpoints?.healthEndpoint?.trim() || undefined,
        metricsEndpoint: tool.endpoints?.metricsEndpoint?.trim() || undefined,
        customEndpoints: tool.endpoints?.customEndpoints,
      },
      security: buildSecurityPayload(tool.security),
      lifecycle: tool.lifecycle,
    }
    if (!payload.endpoints.baseUrl) {
      setError('Base URL is required')
      return
    }
    setSaving(true)
    try {
      if (isEdit) {
        await updateTool(name!, payload)
        navigate(`/tools/${encodeURIComponent(payload.name)}`)
      } else {
        await registerTool(payload)
        navigate('/')
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Save failed')
    } finally {
      setSaving(false)
    }
  }

  if (loading)
    return (
      <div className="loading-state">
        <div className="loading-spinner" />
        <p>Loading...</p>
      </div>
    )

  const tagsStr = Array.isArray(tool.metadata?.tags)
    ? tool.metadata.tags.join(', ')
    : String(tool.metadata?.tags || '')

  return (
    <div className="tool-form-page">
      <div className="page-header">
        <h1>{isEdit ? `Edit: ${name}` : 'Register Tool'}</h1>
        <Link to={isEdit ? `/tools/${encodeURIComponent(name!)}` : '/'} className="btn">
          <X size={18} />
          <span>Cancel</span>
        </Link>
      </div>

      <form onSubmit={handleSubmit} className="tool-form">
        {error && <div className="alert alert-error">{error}</div>}

        <section>
          <h2><Box size={18} /> Basic</h2>
          <div className="form-row">
            <label>
              Name <span className="required">*</span>
              <input
                type="text"
                value={tool.name ?? ''}
                onChange={(e) => setTool((t) => ({ ...t, name: e.target.value }))}
                required
                disabled={isEdit}
                placeholder="unique-tool-name"
                className="input"
              />
            </label>
            {isEdit && <span className="hint">Name cannot be changed</span>}
          </div>
          <div className="form-row">
            <label>
              Version
              <input
                type="text"
                value={tool.version ?? ''}
                onChange={(e) => setTool((t) => ({ ...t, version: e.target.value }))}
                placeholder="1.0.0"
                className="input"
                readOnly={isEdit}
                disabled={isEdit}
              />
            </label>
            {isEdit && <span className="hint">Auto-incremented on save (patch version bumped)</span>}
          </div>
          <div className="form-row">
            <label>
              Title
              <input
                type="text"
                value={tool.title ?? ''}
                onChange={(e) => setTool((t) => ({ ...t, title: e.target.value }))}
                placeholder="Human-readable title"
                className="input"
              />
            </label>
          </div>
          <div className="form-row">
            <label>
              Description
              <textarea
                value={tool.description ?? ''}
                onChange={(e) => setTool((t) => ({ ...t, description: e.target.value }))}
                placeholder="What does this tool do?"
                className="input"
                rows={2}
              />
            </label>
          </div>
          <div className="form-row">
            <label>
              Category
              <input
                type="text"
                value={tool.metadata?.category ?? ''}
                onChange={(e) =>
                  setTool((t) => ({
                    ...t,
                    metadata: { ...t.metadata, category: e.target.value },
                  }))
                }
                placeholder="e.g. search"
                className="input"
              />
            </label>
          </div>
          <div className="form-row">
            <label>
              Tags (comma-separated)
              <input
                type="text"
                value={tagsStr}
                onChange={(e) =>
                  setTool((t) => ({
                    ...t,
                    metadata: {
                      ...t.metadata,
                      tags: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                    },
                  }))
                }
                placeholder="api, web, search"
                className="input"
              />
            </label>
          </div>
        </section>

        <section>
          <h2><Zap size={18} /> Endpoints</h2>
          <div className="form-row">
            <label>
              Base URL <span className="required">*</span>
              <input
                type="url"
                value={tool.endpoints?.baseUrl ?? ''}
                onChange={(e) =>
                  setTool((t) => ({
                    ...t,
                    endpoints: { ...t.endpoints!, baseUrl: e.target.value },
                  }))
                }
                required
                placeholder="https://api.example.com"
                className="input"
              />
            </label>
          </div>
          <div className="form-row">
            <label>
              Health endpoint
              <input
                type="text"
                value={tool.endpoints?.healthEndpoint ?? ''}
                onChange={(e) =>
                  setTool((t) => ({
                    ...t,
                    endpoints: { ...t.endpoints!, healthEndpoint: e.target.value },
                  }))
                }
                placeholder="/health"
                className="input"
              />
            </label>
          </div>
        </section>

        <section>
          <h2><FileJson size={18} /> Input Schema (JSON)</h2>
          <textarea
            value={inputSchemaJson}
            onChange={(e) => setInputSchemaJson(e.target.value)}
            className="input code-input"
            rows={12}
            placeholder='{"type":"object","properties":{},"required":[]}'
            spellCheck={false}
          />
          <p className="hint">JSON schema for tool inputs. Must include type, properties, and required.</p>
        </section>

        <section>
          <h2><FileJson size={18} /> Output Schema (JSON, optional)</h2>
          <textarea
            value={outputSchemaJson}
            onChange={(e) => setOutputSchemaJson(e.target.value)}
            className="input code-input"
            rows={8}
            placeholder='{"type":"object","properties":{},"contentType":"application/json"}'
            spellCheck={false}
          />
          <p className="hint">Optional JSON schema for tool response. Leave empty if not defined.</p>
        </section>

        <section>
          <h2><Shield size={18} /> Security</h2>
          <p className="security-hint">Configure what authentication the API allows.</p>
          <div className="form-row">
            <label>
              Allowed Auth
              <select
                value={tool.security?.authType ?? ''}
                onChange={(e) =>
                  setTool((t) => ({
                    ...t,
                    security: { ...t.security, authType: e.target.value || undefined },
                  }))
                }
                className="input"
              >
                <option value="">None</option>
                <option value="API_KEY">API Key</option>
                <option value="OAuth2">OAuth 2.0</option>
                <option value="JWT">JWT</option>
              </select>
            </label>
          </div>

          {tool.security?.authType === 'OAuth2' && (
            <div className="security-subsection">
              <h3><KeyRound size={16} /> OAuth 2.0</h3>
              <div className="form-row">
                <label>Token URL</label>
                <input
                  type="url"
                  value={tool.security?.oauth?.tokenUrl ?? ''}
                  onChange={(e) =>
                    setTool((t) => ({
                      ...t,
                      security: {
                        ...t.security,
                        oauth: { ...t.security?.oauth, tokenUrl: e.target.value || undefined },
                      },
                    }))
                  }
                  placeholder="https://auth.example.com/oauth/token"
                  className="input"
                />
              </div>
              <div className="form-row">
                <label>Authorization URL</label>
                <input
                  type="url"
                  value={tool.security?.oauth?.authorizationUrl ?? ''}
                  onChange={(e) =>
                    setTool((t) => ({
                      ...t,
                      security: {
                        ...t.security,
                        oauth: { ...t.security?.oauth, authorizationUrl: e.target.value || undefined },
                      },
                    }))
                  }
                  placeholder="https://auth.example.com/oauth/authorize"
                  className="input"
                />
              </div>
              <div className="form-row">
                <label>Client ID</label>
                <input
                  type="text"
                  value={tool.security?.oauth?.clientId ?? ''}
                  onChange={(e) =>
                    setTool((t) => ({
                      ...t,
                      security: {
                        ...t.security,
                        oauth: { ...t.security?.oauth, clientId: e.target.value || undefined },
                      },
                    }))
                  }
                  placeholder="your-client-id"
                  className="input"
                />
              </div>
              <div className="form-row">
                <label>Grant type</label>
                <select
                  value={tool.security?.oauth?.grantType ?? ''}
                  onChange={(e) =>
                    setTool((t) => ({
                      ...t,
                      security: {
                        ...t.security,
                        oauth: { ...t.security?.oauth, grantType: e.target.value || undefined },
                      },
                    }))
                  }
                  className="input"
                >
                  <option value="">—</option>
                  <option value="client_credentials">Client credentials</option>
                  <option value="authorization_code">Authorization code</option>
                </select>
              </div>
              <div className="form-row">
                <label>Scopes (comma-separated)</label>
                <input
                  type="text"
                  value={(tool.security?.oauth?.scopes ?? []).join(', ')}
                  onChange={(e) =>
                    setTool((t) => ({
                      ...t,
                      security: {
                        ...t.security,
                        oauth: {
                          ...t.security?.oauth,
                          scopes: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                        },
                      },
                    }))
                  }
                  placeholder="read, write"
                  className="input"
                />
              </div>
            </div>
          )}

          {tool.security?.authType === 'JWT' && (
            <div className="security-subsection">
              <h3><ShieldCheck size={16} /> JWT</h3>
              <div className="form-row">
                <label>Issuer</label>
                <input
                  type="text"
                  value={tool.security?.jwt?.issuer ?? ''}
                  onChange={(e) =>
                    setTool((t) => ({
                      ...t,
                      security: {
                        ...t.security,
                        jwt: { ...t.security?.jwt, issuer: e.target.value || undefined },
                      },
                    }))
                  }
                  placeholder="https://auth.example.com"
                  className="input"
                />
              </div>
              <div className="form-row">
                <label>Audience</label>
                <input
                  type="text"
                  value={tool.security?.jwt?.audience ?? ''}
                  onChange={(e) =>
                    setTool((t) => ({
                      ...t,
                      security: {
                        ...t.security,
                        jwt: { ...t.security?.jwt, audience: e.target.value || undefined },
                      },
                    }))
                  }
                  placeholder="api.example.com"
                  className="input"
                />
              </div>
              <div className="form-row">
                <label>JWKS URL</label>
                <input
                  type="url"
                  value={tool.security?.jwt?.jwksUrl ?? ''}
                  onChange={(e) =>
                    setTool((t) => ({
                      ...t,
                      security: {
                        ...t.security,
                        jwt: { ...t.security?.jwt, jwksUrl: e.target.value || undefined },
                      },
                    }))
                  }
                  placeholder="https://auth.example.com/.well-known/jwks.json"
                  className="input"
                />
              </div>
              <div className="form-row">
                <label>Algorithm</label>
                <select
                  value={tool.security?.jwt?.algorithm ?? ''}
                  onChange={(e) =>
                    setTool((t) => ({
                      ...t,
                      security: {
                        ...t.security,
                        jwt: { ...t.security?.jwt, algorithm: e.target.value || undefined },
                      },
                    }))
                  }
                  className="input"
                >
                  <option value="">—</option>
                  <option value="RS256">RS256</option>
                  <option value="RS384">RS384</option>
                  <option value="RS512">RS512</option>
                  <option value="HS256">HS256</option>
                  <option value="HS384">HS384</option>
                  <option value="HS512">HS512</option>
                </select>
              </div>
              <div className="form-row">
                <label>Header name</label>
                <input
                  type="text"
                  value={tool.security?.jwt?.headerName ?? ''}
                  onChange={(e) =>
                    setTool((t) => ({
                      ...t,
                      security: {
                        ...t.security,
                        jwt: { ...t.security?.jwt, headerName: e.target.value || undefined },
                      },
                    }))
                  }
                  placeholder="Authorization"
                  className="input"
                />
              </div>
            </div>
          )}

          {(tool.security?.authType === 'OAuth2' || tool.security?.authType === 'JWT' || tool.security?.authType === 'API_KEY') && (
            <div className="security-subsection">
              <h3><Lock size={16} /> SSL / TLS</h3>
              <div className="form-row">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={tool.security?.ssl?.verifyCert ?? true}
                    onChange={(e) =>
                      setTool((t) => ({
                        ...t,
                        security: {
                          ...t.security,
                          ssl: { ...t.security?.ssl, verifyCert: e.target.checked },
                        },
                      }))
                    }
                  />
                  Verify certificate
                </label>
              </div>
              <div className="form-row">
                <label>Cert path</label>
                <input
                  type="text"
                  value={tool.security?.ssl?.certPath ?? ''}
                  onChange={(e) =>
                    setTool((t) => ({
                      ...t,
                      security: {
                        ...t.security,
                        ssl: { ...t.security?.ssl, certPath: e.target.value || undefined },
                      },
                    }))
                  }
                  placeholder="/path/to/cert.pem"
                  className="input"
                />
              </div>
              <div className="form-row">
                <label>Key path</label>
                <input
                  type="text"
                  value={tool.security?.ssl?.keyPath ?? ''}
                  onChange={(e) =>
                    setTool((t) => ({
                      ...t,
                      security: {
                        ...t.security,
                        ssl: { ...t.security?.ssl, keyPath: e.target.value || undefined },
                      },
                    }))
                  }
                  placeholder="/path/to/key.pem"
                  className="input"
                />
              </div>
              <div className="form-row">
                <label>CA path</label>
                <input
                  type="text"
                  value={tool.security?.ssl?.caPath ?? ''}
                  onChange={(e) =>
                    setTool((t) => ({
                      ...t,
                      security: {
                        ...t.security,
                        ssl: { ...t.security?.ssl, caPath: e.target.value || undefined },
                      },
                    }))
                  }
                  placeholder="/path/to/ca.pem"
                  className="input"
                />
              </div>
              <div className="form-row">
                <label>TLS version</label>
                <select
                  value={tool.security?.ssl?.tlsVersion ?? ''}
                  onChange={(e) =>
                    setTool((t) => ({
                      ...t,
                      security: {
                        ...t.security,
                        ssl: { ...t.security?.ssl, tlsVersion: e.target.value || undefined },
                      },
                    }))
                  }
                  className="input"
                >
                  <option value="">Default</option>
                  <option value="TLSv1.2">TLS 1.2</option>
                  <option value="TLSv1.3">TLS 1.3</option>
                </select>
              </div>
            </div>
          )}

          <div className="form-row">
            <label>Allowed origins (comma-separated)</label>
            <input
              type="text"
              value={(tool.security?.allowedOrigins ?? []).join(', ')}
              onChange={(e) =>
                setTool((t) => ({
                  ...t,
                  security: {
                    ...t.security,
                    allowedOrigins: e.target.value
                      .split(',')
                      .map((s) => s.trim())
                      .filter(Boolean),
                  },
                }))
              }
              placeholder="https://app.example.com"
              className="input"
            />
          </div>
        </section>

        <div className="form-actions">
          <button type="submit" disabled={saving} className="btn btn-primary">
            <Save size={18} />
            <span>{saving ? 'Saving...' : isEdit ? 'Update Tool' : 'Register Tool'}</span>
          </button>
          <Link to={isEdit ? `/tools/${encodeURIComponent(name!)}` : '/'} className="btn">
            <X size={18} />
            <span>Cancel</span>
          </Link>
        </div>
      </form>
    </div>
  )
}
