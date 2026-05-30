import type {
  DashboardSummary,
  DeploymentManifest,
  DocsSection,
  EndpointRecord,
  KeyRecord,
  LogRecord,
  ProviderCatalogItem,
  ProviderRecord,
  SettingsRecord,
} from '@/types/api'

const API_ROOT = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const csrf = document.cookie
    .split('; ')
    .find((item) => item.startsWith('api_translate_csrf='))
    ?.split('=')[1]

  const response = await fetch(`${API_ROOT}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(csrf ? { 'X-CSRF-Token': csrf } : {}),
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(text || `Request failed: ${response.status}`)
  }
  return response.json() as Promise<T>
}

export const api = {
  authStatus: () => request<{ protected: boolean; authenticated: boolean }>('/auth/status'),
  login: (password: string) => request<{ status: string }>('/auth/login', { method: 'POST', body: JSON.stringify({ password }) }),
  logout: () => request<{ status: string }>('/auth/logout', { method: 'POST' }),

  dashboard: () => request<DashboardSummary>('/dashboard/summary'),

  providerCatalog: () => request<{ items: ProviderCatalogItem[] }>('/providers/catalog'),
  providers: () => request<{ items: ProviderRecord[] }>('/providers/list'),
  addProvider: (payload: Record<string, unknown>) => request<{ item: ProviderRecord }>('/providers/add', { method: 'POST', body: JSON.stringify(payload) }),
  updateProvider: (payload: Record<string, unknown>) => request<{ item: ProviderRecord }>('/providers/update', { method: 'POST', body: JSON.stringify(payload) }),
  removeProvider: (slug: string) => request<{ status: string }>('/providers/remove', { method: 'DELETE', body: JSON.stringify({ slug }) }),

  keys: () => request<{ items: KeyRecord[] }>('/keys/list'),
  saveKey: (payload: Record<string, unknown>) => request<{ maskedKey: string }>('/keys/save', { method: 'POST', body: JSON.stringify(payload) }),

  endpoints: () => request<{ items: EndpointRecord[] }>('/endpoints/list'),
  generateEndpoint: (payload: Record<string, unknown>) => request<{ item: EndpointRecord }>('/endpoints/generate', { method: 'POST', body: JSON.stringify(payload) }),
  cloneEndpoint: (payload: Record<string, unknown>) => request<{ item: EndpointRecord }>('/endpoints/clone', { method: 'POST', body: JSON.stringify(payload) }),
  removeEndpoint: (id: number) => request<{ status: string }>('/endpoints/remove', { method: 'DELETE', body: JSON.stringify({ id }) }),
  testGateway: (payload: Record<string, unknown>) => request<Record<string, unknown>>('/gateway/test', { method: 'POST', body: JSON.stringify(payload) }),

  logs: () => request<{ items: LogRecord[] }>('/logs'),
  exportLogs: () => request<{ items: LogRecord[] }>('/logs/export'),

  settings: () => request<SettingsRecord>('/settings'),
  saveSettings: (payload: Record<string, unknown>) => request<{ item: { dashboardAuthEnabled: boolean } }>('/settings', { method: 'POST', body: JSON.stringify(payload) }),

  docs: () => request<{ sections: DocsSection[] }>('/docs/generated'),
  buildDeployment: (payload: Record<string, unknown>) => request<{ manifest: DeploymentManifest }>('/deployments/build', { method: 'POST', body: JSON.stringify(payload) }),
}
