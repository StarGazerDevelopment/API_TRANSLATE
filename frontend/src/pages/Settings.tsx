import { useEffect, useState } from 'react'

import { SectionCard } from '@/components/SectionCard'
import { api } from '@/lib/api'
import { useAppStore } from '@/store/useAppStore'

export default function SettingsPage() {
  const settings = useAppStore((state) => state.settings)
  const bootstrap = useAppStore((state) => state.bootstrap)
  const [form, setForm] = useState({
    dashboardAuthEnabled: false,
    password: '',
    corsOrigins: '*',
    defaultTimeoutSeconds: 60,
    defaultRateLimitPerMinute: 120,
    endpointStyle: 'openai' as 'openai' | 'anthropic' | 'gemini' | 'lm-studio',
    csrfEnabled: true,
    secureHeadersEnabled: true,
  })
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!settings) {
      return
    }
    setForm({
      dashboardAuthEnabled: settings.dashboardAuthEnabled,
      password: '',
      corsOrigins: settings.corsOrigins.join(','),
      defaultTimeoutSeconds: settings.defaultTimeoutSeconds,
      defaultRateLimitPerMinute: settings.defaultRateLimitPerMinute,
      endpointStyle: settings.endpointStyle,
      csrfEnabled: settings.csrfEnabled,
      secureHeadersEnabled: settings.secureHeadersEnabled,
    })
  }, [settings])

  const save = async () => {
    await api.saveSettings({
      dashboardAuthEnabled: form.dashboardAuthEnabled,
      password: form.password || undefined,
      corsOrigins: form.corsOrigins.split(',').map((item) => item.trim()).filter(Boolean),
      defaultTimeoutSeconds: form.defaultTimeoutSeconds,
      defaultRateLimitPerMinute: form.defaultRateLimitPerMinute,
      endpointStyle: form.endpointStyle,
      csrfEnabled: form.csrfEnabled,
      secureHeadersEnabled: form.secureHeadersEnabled,
    })
    await bootstrap()
    setMessage('Settings saved.')
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
      <SectionCard title="Endpoint Style" eyebrow="Compatibility" description="Choose the main endpoint format this app should present across builds and the local gateway UI.">
        <div className="space-y-4">
          {[
            ['openai', 'OpenAI style'],
            ['anthropic', 'Anthropic style'],
            ['gemini', 'Gemini style'],
            ['lm-studio', 'LM Studio style'],
          ].map(([value, label]) => (
            <button
              key={value}
              type="button"
              onClick={() => setForm((current) => ({ ...current, endpointStyle: value as typeof current.endpointStyle }))}
              className={`w-full rounded-2xl border px-4 py-4 text-left transition ${form.endpointStyle === value ? 'border-cyan-400/35 bg-cyan-300/10 text-white' : 'border-white/10 bg-black/20 text-zinc-400 hover:bg-white/[0.05]'}`}
            >
              {label}
            </button>
          ))}
        </div>
      </SectionCard>

      <SectionCard title="App Settings" eyebrow="Runtime" description="Keep the app setup simple. Save gateway defaults and optional dashboard protection here.">
        <div className="space-y-4">
          <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-4 py-4">
            <span>Protect dashboard with password</span>
            <input type="checkbox" checked={form.dashboardAuthEnabled} onChange={(event) => setForm((current) => ({ ...current, dashboardAuthEnabled: event.target.checked }))} />
          </label>
          <label className="block text-sm text-zinc-300">
            Password
            <input type="password" value={form.password} onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))} className="mt-2 w-full rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-white outline-none" placeholder="Leave blank to keep current password" />
          </label>
          <label className="block text-sm text-zinc-300">
            CORS Origins
            <input value={form.corsOrigins} onChange={(event) => setForm((current) => ({ ...current, corsOrigins: event.target.value }))} className="mt-2 w-full rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-white outline-none" />
          </label>
          <label className="block text-sm text-zinc-300">
            Default Timeout Seconds
            <input type="number" value={form.defaultTimeoutSeconds} onChange={(event) => setForm((current) => ({ ...current, defaultTimeoutSeconds: Number(event.target.value) }))} className="mt-2 w-full rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-white outline-none" />
          </label>
          <label className="block text-sm text-zinc-300">
            Default Rate Limit Per Minute
            <input type="number" value={form.defaultRateLimitPerMinute} onChange={(event) => setForm((current) => ({ ...current, defaultRateLimitPerMinute: Number(event.target.value) }))} className="mt-2 w-full rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-white outline-none" />
          </label>
          <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-4 py-4">
            <span>Enable CSRF protection</span>
            <input type="checkbox" checked={form.csrfEnabled} onChange={(event) => setForm((current) => ({ ...current, csrfEnabled: event.target.checked }))} />
          </label>
          <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-4 py-4">
            <span>Enable secure headers</span>
            <input type="checkbox" checked={form.secureHeadersEnabled} onChange={(event) => setForm((current) => ({ ...current, secureHeadersEnabled: event.target.checked }))} />
          </label>
          <button onClick={() => void save()} className="w-full rounded-2xl bg-gradient-to-r from-cyan-400 to-violet-500 px-4 py-3 font-medium text-zinc-950 transition hover:opacity-90">
            Save Settings
          </button>
          {message ? <p className="text-sm text-emerald-300">{message}</p> : null}
        </div>
      </SectionCard>
    </div>
  )
}
