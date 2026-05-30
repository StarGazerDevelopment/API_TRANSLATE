export type ProviderCatalogItem = {
  slug: string
  name: string
  env_var: string
  transport: string
  base_url: string
  category: string
  logo_text: string
  logo_color: string
  models: string[]
}

export type ProviderRecord = {
  id: number
  slug: string
  displayName: string
  envVar: string
  baseUrl?: string
  transport: string
  defaultModel?: string
  enabled: boolean
  priority: number
  timeoutSeconds: number
  maxRetries: number
  healthStatus: string
  maskedKey?: string | null
  metadata?: Record<string, unknown>
  logoText: string
  logoColor: string
  models: string[]
  updatedAt?: string
}

export type EndpointRecord = {
  id: number
  name: string
  path: string
  method: 'POST' | 'GET'
  category: string
  summary: string
  endpointType: 'chat' | 'completion' | 'embedding' | 'image' | 'audio'
  compatibilities: string[]
  modelName?: string | null
  blocks: Record<string, unknown>
  generatedCode: string
  providerOrder: string[]
  authMode: 'public' | 'dashboard_password'
  cacheEnabled: boolean
  cacheMode: 'memory' | 'sqlite'
  cacheTtlSeconds: number
  rateLimitPerMinute: number
  enabled: boolean
  updatedAt?: string
}

export type KeyRecord = {
  provider: string
  displayName: string
  envVar: string
  maskedKey?: string | null
}

export type LogRecord = {
  id: number
  endpointPath: string
  providerSlug?: string | null
  statusCode: number
  latencyMs: number
  cacheHit: boolean
  failoverUsed: boolean
  errorType?: string | null
  createdAt: string
  requestExcerpt: string
  responseExcerpt: string
}

export type DashboardSummary = {
  activeProviders: number
  requestsToday: number
  requestsThisMonth: number
  averageResponseTime: number
  failedRequests: number
  runningEndpoints: number
  cacheHitRate: number
  failoverEvents: number
  requestSeries: Array<{ label: string; requests: number }>
  latencySeries: Array<{ label: string; latency: number }>
  providerHealth: Array<{ name: string; status: string }>
  recentActivity: Array<{
    endpoint: string
    provider?: string | null
    statusCode: number
    latencyMs: number
    cacheHit: boolean
    createdAt: string
  }>
}

export type DocsSection = {
  title: string
  content: string[]
}

export type DeploymentManifest = {
  target: string
  path: string
  config: Record<string, unknown>
  build?: {
    built: boolean
    targetPlatform: string
    currentPlatform: string
    artifactPath?: string | null
    reason?: string
  } | null
  commands?: Record<string, string>
}

export type SettingsRecord = {
  dashboardAuthEnabled: boolean
  corsOrigins: string[]
  defaultTimeoutSeconds: number
  defaultRateLimitPerMinute: number
  endpointStyle: 'openai' | 'anthropic' | 'gemini' | 'lm-studio'
  csrfEnabled: boolean
  secureHeadersEnabled: boolean
}
