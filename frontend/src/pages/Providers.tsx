import { useMemo, useState } from 'react'

import { ProviderLogo } from '@/components/ProviderLogo'
import { SectionCard } from '@/components/SectionCard'
import { StatusBadge } from '@/components/StatusBadge'
import { api } from '@/lib/api'
import { useAppStore } from '@/store/useAppStore'

export default function Providers() {
  const catalog = useAppStore((state) => state.catalog)
  const providers = useAppStore((state) => state.providers)
  const refreshProviders = useAppStore((state) => state.refreshProviders)
  const refreshKeys = useAppStore((state) => state.refreshKeys)

  const [selected, setSelected] = useState(catalog[0]?.slug ?? 'openai')
  const [displayName, setDisplayName] = useState('OpenAI')
  const [baseUrl, setBaseUrl] = useState('https://api.openai.com/v1')
  const [apiKey, setApiKey] = useState('')
  const [message, setMessage] = useState('')

  const configuredSlugs = useMemo(() => new Set(providers.map((item) => item.slug)), [providers])

  const handleAddOrUpdate = async () => {
    const exists = configuredSlugs.has(selected)
    const payload = {
      provider: selected,
      displayName,
      baseUrl,
      apiKey: apiKey || undefined,
      defaultModel: undefined,
      timeoutSeconds: 60,
      maxRetries: 2,
      enabled: true,
      priority: exists ? 50 : providers.length + 1,
      metadata: {},
    }

    await (exists ? api.updateProvider(payload) : api.addProvider(payload))
    await Promise.all([refreshProviders(), refreshKeys()])
    setMessage(`${exists ? 'Updated' : 'Added'} ${displayName}.`)
    setApiKey('')
  }

  const handleRemove = async (slug: string) => {
    await api.removeProvider(slug)
    await Promise.all([refreshProviders(), refreshKeys()])
    setMessage(`Removed ${slug}.`)
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1.2fr_1fr]">
      <SectionCard title="Configured Providers" eyebrow="Registry" description="Manage enabled providers, priorities, and failover-ready health states.">
        <div className="space-y-3">
          {providers.map((provider) => (
            <div key={provider.slug} className="group flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-white/10 bg-black/20 px-4 py-4 transition duration-300 hover:border-cyan-400/20 hover:bg-white/[0.03]">
              <div className="flex items-center gap-4">
                <ProviderLogo name={provider.displayName} initials={provider.logoText} color={provider.logoColor} />
                <div>
                  <p className="font-medium text-white">{provider.displayName}</p>
                  <p className="text-sm text-zinc-400">
                    {provider.slug} · {provider.transport} · {provider.baseUrl || 'Default base URL'}
                  </p>
                  <p className="mt-1 text-xs uppercase tracking-[0.24em] text-zinc-500">
                    Retry {provider.maxRetries} · Timeout {provider.timeoutSeconds}s
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <StatusBadge status={provider.healthStatus} />
                <button
                  onClick={() => handleRemove(provider.slug)}
                  className="rounded-full border border-rose-400/25 bg-rose-400/10 px-4 py-2 text-sm text-rose-200 transition hover:bg-rose-400/20"
                >
                  Remove
                </button>
              </div>
            </div>
          ))}
          {providers.length === 0 ? <p className="text-sm text-zinc-400">No providers configured yet. Add one from the catalog to enable the gateway.</p> : null}
        </div>
      </SectionCard>

      <SectionCard title="Add Or Update" eyebrow="Editor" description="Attach credentials, set defaults, and prepare providers for failover routing.">
        <div className="space-y-4">
          <label className="block text-sm text-zinc-300">
            Provider
            <div className="mt-2 grid grid-cols-1 gap-2">
              {catalog.slice(0, 12).map((item) => (
                <button
                  key={item.slug}
                  type="button"
                  onClick={() => {
                    setSelected(item.slug)
                    setDisplayName(item.name)
                    setBaseUrl(item.base_url ?? '')
                  }}
                  className={`flex items-center gap-3 rounded-2xl border px-4 py-3 text-left transition ${selected === item.slug ? 'border-cyan-400/35 bg-cyan-300/10 text-white' : 'border-white/10 bg-zinc-950 text-zinc-300 hover:bg-white/[0.04]'}`}
                >
                  <ProviderLogo name={item.name} initials={item.logo_text} color={item.logo_color} className="h-9 w-9" />
                  <span>{item.name}</span>
                </button>
              ))}
            </div>
          </label>
          <label className="block text-sm text-zinc-300">
            Display Name
            <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-white outline-none" />
          </label>
          <label className="block text-sm text-zinc-300">
            Base URL
            <input value={baseUrl} onChange={(event) => setBaseUrl(event.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-white outline-none" />
          </label>
          <label className="block text-sm text-zinc-300">
            API Key
            <input value={apiKey} onChange={(event) => setApiKey(event.target.value)} placeholder="Stored only on the backend and masked in the UI" className="mt-2 w-full rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-white outline-none" />
          </label>
          <button
            onClick={() => void handleAddOrUpdate()}
            className="w-full rounded-2xl bg-gradient-to-r from-cyan-400 to-violet-500 px-4 py-3 font-medium text-zinc-950 transition hover:opacity-90"
          >
            Save Provider
          </button>
          {message ? <p className="text-sm text-emerald-300">{message}</p> : null}
        </div>
      </SectionCard>
    </div>
  )
}
