import { create } from 'zustand'

import { api } from '@/lib/api'
import type {
  DashboardSummary,
  DocsSection,
  EndpointRecord,
  KeyRecord,
  LogRecord,
  ProviderCatalogItem,
  ProviderRecord,
  SettingsRecord,
} from '@/types/api'

type AppState = {
  loading: boolean
  authenticated: boolean
  protectedMode: boolean
  dashboard?: DashboardSummary
  catalog: ProviderCatalogItem[]
  providers: ProviderRecord[]
  keys: KeyRecord[]
  endpoints: EndpointRecord[]
  logs: LogRecord[]
  docs: DocsSection[]
  settings?: SettingsRecord
  error?: string
  bootstrap: () => Promise<void>
  refreshProviders: () => Promise<void>
  refreshKeys: () => Promise<void>
  refreshEndpoints: () => Promise<void>
  refreshLogs: () => Promise<void>
}

export const useAppStore = create<AppState>((set, get) => ({
  loading: false,
  authenticated: false,
  protectedMode: false,
  catalog: [],
  providers: [],
  keys: [],
  endpoints: [],
  logs: [],
  docs: [],
  error: undefined,

  bootstrap: async () => {
    set({ loading: true, error: undefined })
    try {
      const [auth, dashboard, catalog, providers, keys, endpoints, logs, docs, settings] = await Promise.all([
        api.authStatus(),
        api.dashboard().catch(() => undefined),
        api.providerCatalog(),
        api.providers().catch(() => ({ items: [] })),
        api.keys().catch(() => ({ items: [] })),
        api.endpoints().catch(() => ({ items: [] })),
        api.logs().catch(() => ({ items: [] })),
        api.docs().catch(() => ({ sections: [] })),
        api.settings().catch(() => undefined),
      ])

      set({
        authenticated: auth.authenticated,
        protectedMode: auth.protected,
        dashboard,
        catalog: catalog.items,
        providers: providers.items,
        keys: keys.items,
        endpoints: endpoints.items,
        logs: logs.items,
        docs: docs.sections,
        settings,
        loading: false,
      })
    } catch (error) {
      set({ loading: false, error: error instanceof Error ? error.message : 'Failed to load application.' })
    }
  },

  refreshProviders: async () => {
    const providers = await api.providers()
    set({ providers: providers.items })
  },

  refreshKeys: async () => {
    const keys = await api.keys()
    set({ keys: keys.items })
  },

  refreshEndpoints: async () => {
    const endpoints = await api.endpoints()
    const dashboard = await api.dashboard().catch(() => get().dashboard)
    set({ endpoints: endpoints.items, dashboard })
  },

  refreshLogs: async () => {
    const logs = await api.logs()
    const dashboard = await api.dashboard().catch(() => get().dashboard)
    set({ logs: logs.items, dashboard })
  },
}))
