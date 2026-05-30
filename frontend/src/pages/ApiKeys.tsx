import { useState } from 'react'

import { SectionCard } from '@/components/SectionCard'
import { api } from '@/lib/api'
import { useAppStore } from '@/store/useAppStore'

export default function ApiKeysPage() {
  const keys = useAppStore((state) => state.keys)
  const providers = useAppStore((state) => state.providers)
  const refreshKeys = useAppStore((state) => state.refreshKeys)

  const [provider, setProvider] = useState(providers[0]?.slug ?? 'openai')
  const [apiKey, setApiKey] = useState('')
  const [message, setMessage] = useState('')

  const save = async () => {
    const selected = providers.find((item) => item.slug === provider)
    await api.saveKey({ provider, apiKey, envVar: selected?.envVar })
    await refreshKeys()
    setApiKey('')
    setMessage(`Saved key for ${selected?.displayName ?? provider}.`)
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1.15fr_1fr]">
      <SectionCard title="Key Vault" eyebrow="Secrets" description="Keys are written to the backend `.env`, masked in the UI, and never returned in raw form.">
        <div className="space-y-3">
          {keys.map((item) => (
            <div key={item.envVar} className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-4 py-4">
              <div>
                <p className="font-medium text-white">{item.displayName}</p>
                <p className="text-sm text-zinc-400">{item.envVar}</p>
              </div>
              <code className="rounded-full border border-white/10 bg-zinc-950 px-4 py-2 text-xs text-cyan-200">{item.maskedKey ?? 'Not set'}</code>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="Save Secret" eyebrow="Vault" description="Use provider-linked environment variables and backend-only key persistence.">
        <div className="space-y-4">
          <label className="block text-sm text-zinc-300">
            Provider
            <select value={provider} onChange={(event) => setProvider(event.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-white outline-none">
              {providers.map((item) => (
                <option key={item.slug} value={item.slug}>
                  {item.displayName}
                </option>
              ))}
            </select>
          </label>
          <label className="block text-sm text-zinc-300">
            API Key
            <input value={apiKey} onChange={(event) => setApiKey(event.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-white outline-none" placeholder="sk-..." />
          </label>
          <button onClick={() => void save()} className="w-full rounded-2xl bg-gradient-to-r from-cyan-400 to-violet-500 px-4 py-3 font-medium text-zinc-950 transition hover:opacity-90">
            Save Key
          </button>
          {message ? <p className="text-sm text-emerald-300">{message}</p> : null}
        </div>
      </SectionCard>
    </div>
  )
}
