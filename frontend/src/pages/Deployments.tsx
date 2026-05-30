import { useEffect, useState } from 'react'

import { SectionCard } from '@/components/SectionCard'
import { api } from '@/lib/api'
import { useAppStore } from '@/store/useAppStore'

const targets = [
  'windows-exe',
  'linux-binary',
  'macos-app',
  'docker',
  'render',
  'railway',
  'flyio',
  'vps',
  'vercel',
  'cloudflare-workers',
  'netlify',
]

export default function DeploymentsPage() {
  const endpoints = useAppStore((state) => state.endpoints)
  const settings = useAppStore((state) => state.settings)
  const [target, setTarget] = useState('docker')
  const [showBuildModal, setShowBuildModal] = useState(false)
  const [flowPath, setFlowPath] = useState('/api/translate')
  const [endpointStyle, setEndpointStyle] = useState<'openai' | 'anthropic' | 'gemini' | 'lm-studio'>('openai')
  const [dashboardAuthEnabled, setDashboardAuthEnabled] = useState(false)
  const [password, setPassword] = useState('')
  const [notes, setNotes] = useState('')
  const [autoBuild, setAutoBuild] = useState(false)
  const [outputDir, setOutputDir] = useState('')
  const [result, setResult] = useState('')

  useEffect(() => {
    if (settings?.endpointStyle) {
      setEndpointStyle(settings.endpointStyle)
    }
    if (settings?.dashboardAuthEnabled) {
      setDashboardAuthEnabled(settings.dashboardAuthEnabled)
    }
    if (endpoints[0]?.path) {
      setFlowPath(endpoints[0].path)
    }
  }, [endpoints, settings])

  const build = async () => {
    let nextOutputDir = outputDir
    if (target === 'windows-exe' && autoBuild && !nextOutputDir.trim()) {
      const prompted = window.prompt('Where should the Windows EXE be saved?', 'C:\\Users\\Public\\Desktop\\AI-Translator.exe')
      if (!prompted) {
        return
      }
      nextOutputDir = prompted.trim()
      setOutputDir(nextOutputDir)
    }

    const response = await api.buildDeployment({
      target,
      flowPath,
      endpointStyle,
      dashboardAuthEnabled,
      password: password || undefined,
      notes: notes || undefined,
      autoBuild,
      outputDir: nextOutputDir || undefined,
    })
    const buildSummary = response.manifest.build
      ? response.manifest.build.built
        ? ` Built artifact: ${response.manifest.build.artifactPath}`
        : ` Bundle created. Binary not built here: ${response.manifest.build.reason}`
      : ' Bundle includes setup commands and starter files.'
    setResult(`Generated ${response.manifest.target} bundle at ${response.manifest.path}.${buildSummary}`)
    setShowBuildModal(false)
  }

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_1.1fr]">
      <SectionCard title="Deployment Wizard" eyebrow="Export" description="Generate artifacts for binaries, Docker, serverless hosts, and traditional servers.">
        <div className="grid gap-3 sm:grid-cols-2">
          {targets.map((item) => (
            <button
              key={item}
              onClick={() => setTarget(item)}
              className={`rounded-2xl border px-4 py-4 text-left transition ${target === item ? 'border-cyan-400/40 bg-cyan-300/10 text-white' : 'border-white/10 bg-black/20 text-zinc-400 hover:bg-white/[0.04]'}`}
            >
              <p className="font-medium capitalize">{item.replace('-', ' ')}</p>
              <p className="mt-2 text-xs uppercase tracking-[0.2em]">Generated export</p>
            </button>
          ))}
        </div>
        <button onClick={() => setShowBuildModal(true)} className="mt-5 w-full rounded-2xl bg-gradient-to-r from-cyan-400 to-violet-500 px-4 py-3 font-medium text-zinc-950 transition hover:opacity-90">
          Build App
        </button>
      </SectionCard>

      <SectionCard title="Target Overview" eyebrow="Release" description="Beginner-friendly packaging flows for local binaries and cloud deployment handoff.">
        <div className="space-y-4 text-sm text-zinc-300">
          <p>Executable exports prepare the project for PyInstaller-driven Windows, Linux, and macOS packaging.</p>
          <p>Server targets generate starter deployment files for Render, Railway, Fly.io, VPS, and Docker-based hosting.</p>
          <p>Serverless targets create minimal output folders for Vercel, Cloudflare Workers, and Netlify deployment workflows.</p>
          <div className="rounded-2xl border border-white/10 bg-zinc-950 p-4 text-cyan-100">{result || 'Choose a target and build a bundle to generate export files inside `exports/`.'}</div>
        </div>
      </SectionCard>

      {showBuildModal ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/70 p-4 backdrop-blur">
          <div className="w-full max-w-2xl rounded-[32px] border border-white/10 bg-[#0b0b11] p-6 shadow-[0_30px_100px_rgba(0,0,0,0.55)]">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="text-xs uppercase tracking-[0.28em] text-cyan-300/80">Build App</p>
                <h2 className="mt-2 text-2xl font-semibold text-white">Build Settings</h2>
              </div>
              <button type="button" onClick={() => setShowBuildModal(false)} className="rounded-2xl border border-white/10 px-4 py-2 text-sm text-zinc-300">
                Close
              </button>
            </div>
            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <label className="block text-sm text-zinc-300">
                Flow To Use
                <select value={flowPath} onChange={(event) => setFlowPath(event.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-white outline-none">
                  {endpoints.length === 0 ? <option value="/api/translate">/api/translate</option> : null}
                  {endpoints.map((endpoint) => (
                    <option key={endpoint.id} value={endpoint.path}>
                      {endpoint.name} ({endpoint.path})
                    </option>
                  ))}
                </select>
              </label>
              <label className="block text-sm text-zinc-300">
                Endpoint Style
                <select value={endpointStyle} onChange={(event) => setEndpointStyle(event.target.value as typeof endpointStyle)} className="mt-2 w-full rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-white outline-none">
                  <option value="openai">OpenAI style</option>
                  <option value="anthropic">Anthropic style</option>
                  <option value="gemini">Gemini style</option>
                  <option value="lm-studio">LM Studio style</option>
                </select>
              </label>
              <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-4 py-4 md:col-span-2">
                <span>Protect dashboard with password</span>
                <input type="checkbox" checked={dashboardAuthEnabled} onChange={(event) => setDashboardAuthEnabled(event.target.checked)} />
              </label>
              {dashboardAuthEnabled ? (
                <label className="block text-sm text-zinc-300 md:col-span-2">
                  Password
                  <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-white outline-none" />
                </label>
              ) : null}
              <label className="block text-sm text-zinc-300 md:col-span-2">
                Notes
                <textarea value={notes} onChange={(event) => setNotes(event.target.value)} className="mt-2 h-24 w-full rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-white outline-none" placeholder="Optional build notes" />
              </label>
              {['windows-exe', 'linux-binary', 'macos-app'].includes(target) ? (
                <>
                  <label className="flex items-center justify-between rounded-2xl border border-white/10 bg-black/20 px-4 py-4 md:col-span-2">
                    <span>Build artifact now</span>
                    <input type="checkbox" checked={autoBuild} onChange={(event) => setAutoBuild(event.target.checked)} />
                  </label>
                  {target === 'windows-exe' ? (
                    <label className="block text-sm text-zinc-300 md:col-span-2">
                      Windows Output Path
                      <input
                        value={outputDir}
                        onChange={(event) => setOutputDir(event.target.value)}
                        className="mt-2 w-full rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-white outline-none"
                        placeholder="Folder or full .exe path. Leave blank to get prompted when you click Build App"
                      />
                    </label>
                  ) : null}
                </>
              ) : null}
            </div>
            <button onClick={() => void build()} className="mt-6 w-full rounded-2xl bg-gradient-to-r from-cyan-400 to-violet-500 px-4 py-3 font-medium text-zinc-950 transition hover:opacity-90">
              Build App
            </button>
          </div>
        </div>
      ) : null}
    </div>
  )
}
