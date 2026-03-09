/** Types matching Tool Registry API schema */

export interface PropertyDefinition {
  type: string
  format?: string
  enum?: unknown[]
  description?: string
  default?: unknown
  validation?: {
    minLength?: number
    maxLength?: number
    minimum?: number | null
    maximum?: number | null
    pattern?: string
  }
}

export interface InputSchema {
  type?: string
  properties?: Record<string, PropertyDefinition>
  required?: string[]
  additionalProperties?: boolean
}

export interface ResponseSchema {
  type?: string
  properties?: Record<string, unknown>
}

export interface OutputSchema {
  contentType?: string
  schema?: ResponseSchema
  /** API returns schema_ when by_alias=False */
  schema_?: ResponseSchema
  errorSchema?: { type?: string; properties?: Record<string, unknown> }
}

export interface ToolMetadata {
  category?: string
  tags?: string[]
  appId?: string
  created?: string
  updated?: string
  openAI?: Record<string, unknown>
  custom?: Record<string, unknown>
}

export interface ServiceEndpoints {
  serviceId?: string
  baseUrl: string
  healthEndpoint?: string
  metricsEndpoint?: string
  customEndpoints?: Record<string, string>
}

export interface RateLimitConfig {
  maxRequestsPerMinute?: number
  maxRequestsPerHour?: number
  quotaType?: string
}

export interface SSLConfig {
  verifyCert?: boolean
  certPath?: string
  keyPath?: string
  caPath?: string
  tlsVersion?: string
}

export interface OAuthConfig {
  tokenUrl?: string
  authorizationUrl?: string
  clientId?: string
  grantType?: string
  scopes?: string[]
}

export interface JWTConfig {
  issuer?: string
  audience?: string
  jwksUrl?: string
  algorithm?: string
  headerName?: string
}

export interface SecurityConfig {
  authType?: string
  requiredScopes?: string[]
  allowedOrigins?: string[]
  rateLimit?: RateLimitConfig
  ssl?: SSLConfig
  oauth?: OAuthConfig
  jwt?: JWTConfig
}

export interface LifecycleEvents {
  onRegister?: string
  onDeregister?: string
  onUpdate?: string
  healthCheck?: string
}

export interface Tool {
  toolId?: string
  name: string
  version?: string
  title?: string
  description?: string
  metadata?: ToolMetadata
  inputSchema: InputSchema
  outputSchema?: OutputSchema
  endpoints: ServiceEndpoints
  security?: SecurityConfig
  lifecycle?: LifecycleEvents
}
