import { useEffect, useMemo, useState } from 'react'
import { Copy, MoreHorizontal, Play, Plus, Save, Sparkles, Trash2 } from 'lucide-react'

import { BlocklyCanvas } from '@/components/BlocklyCanvas'
import { ProviderLogo } from '@/components/ProviderLogo'
import { SectionCard } from '@/components/SectionCard'
import { api } from '@/lib/api'
import { useAppStore } from '@/store/useAppStore'

const BUILDER_TABS = ['flows', 'builder', 'guide'] as const

type EndpointType = 'chat' | 'completion' | 'embedding' | 'image' | 'audio'
type FlowDefaults = {
  providerSlug: string
  model: string
  path: string
  method: 'POST' | 'GET'
}

type ProviderInfo = {
  slug: string
  displayName: string
  models?: string[]
  logoText: string
  logoColor: string
}

function pickRandomModel(models: string[]) {
  if (!models.length) {
    return 'gpt-4o-mini'
  }
  return models[Math.floor(Math.random() * models.length)]
}

function styleToCompatibilities(style: 'openai' | 'anthropic' | 'gemini' | 'lm-studio') {
  if (style === 'anthropic') return ['anthropic']
  if (style === 'gemini') return ['gemini']
  if (style === 'lm-studio') return ['lm-studio']
  return ['openai']
}

function inferEndpointType(path: string): EndpointType {
  const normalized = path.toLowerCase()
  if (normalized.includes('/embeddings')) return 'embedding'
  if (normalized.includes('/images')) return 'image'
  if (normalized.includes('/audio')) return 'audio'
  if (normalized.endsWith('/completions') && !normalized.includes('/chat/')) return 'completion'
  return 'chat'
}

function collectBlocks(value: unknown): Array<Record<string, unknown>> {
  const results: Array<Record<string, unknown>> = []
  const visit = (node: unknown) => {
    if (!node || typeof node !== 'object') {
      return
    }
    const record = node as Record<string, unknown>
    if (typeof record.type === 'string') {
      results.push(record)
    }
    for (const child of Object.values(record)) {
      if (Array.isArray(child)) {
        child.forEach(visit)
      } else if (child && typeof child === 'object') {
        visit(child)
      }
    }
  }
  visit(value)
  return results
}

function getFieldValue(blocks: Record<string, unknown>, type: string, field: string) {
  const block = collectBlocks(blocks).find((item) => item.type === type)
  const fields = block?.fields
  if (!fields || typeof fields !== 'object') {
    return undefined
  }
  return (fields as Record<string, unknown>)[field]
}

function deriveFlowMeta(
  blocks: Record<string, unknown>,
  providers: ProviderInfo[],
  endpointStyle: 'openai' | 'anthropic' | 'gemini' | 'lm-studio',
  defaults: FlowDefaults,
) {
  const defaultProvider = providers[0]
  const providerSlug = String(getFieldValue(blocks, 'call_api', 'PROVIDER') ?? defaults.providerSlug ?? defaultProvider?.slug ?? 'openai')
  const provider = providers.find((item) => item.slug === providerSlug) ?? defaultProvider
  const providerModels = provider?.models ?? []
  const model = String(getFieldValue(blocks, 'call_api', 'MODEL') ?? defaults.model ?? providerModels[0] ?? 'gpt-4o-mini')
  const path = String(getFieldValue(blocks, 'on_api_call', 'PATH') ?? defaults.path ?? '/api/custom')
  const method = String(getFieldValue(blocks, 'on_api_call', 'METHOD') ?? defaults.method ?? 'POST')
  return {
    providerSlug,
    provider,
    model,
    path,
    method,
    endpointType: inferEndpointType(path),
    compatibilities: styleToCompatibilities(endpointStyle),
  }
}

export default function BuilderPage() {
  const providers = useAppStore((state) => state.providers)
  const endpoints = useAppStore((state) => state.endpoints)
  const settings = useAppStore((state) => state.settings)
  const refreshEndpoints = useAppStore((state) => state.refreshEndpoints)
  const refreshLogs = useAppStore((state) => state.refreshLogs)

  const [activeTab, setActiveTab] = useState<(typeof BUILDER_TABS)[number]>('flows')
  const [menuOpenId, setMenuOpenId] = useState<number | null>(null)
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [name, setName] = useState('New Flow')
  const [summary, setSummary] = useState('A simple API flow.')
  const [blocks, setBlocks] = useState<Record<string, unknown>>({})
  const [workspaceKey, setWorkspaceKey] = useState('new-flow')
  const [result, setResult] = useState('')
  const [isRunning, setIsRunning] = useState(false)
  const [flowDefaults, setFlowDefaults] = useState<FlowDefaults>({
    providerSlug: 'openai',
    model: 'gpt-4o-mini',
    path: '/api/custom',
    method: 'POST',
  })

  const endpointStyle = settings?.endpointStyle ?? 'openai'
  const flowMeta = useMemo(
    () => deriveFlowMeta(blocks, providers, endpointStyle, flowDefaults),
    [blocks, endpointStyle, flowDefaults, providers],
  )

  const createNewWorkflow = () => {
    const firstProvider = providers[0]
    const starterModel = pickRandomModel(firstProvider?.models ?? [])
    setFlowDefaults({
      providerSlug: firstProvider?.slug ?? 'openai',
      model: starterModel,
      path: '/api/custom',
      method: 'POST',
    })
    setSelectedId(null)
    setName('New Flow')
    setSummary('A simple API flow.')
    setBlocks({})
    setWorkspaceKey(`new-${firstProvider?.slug ?? 'provider'}-${starterModel}-${Date.now()}`)
    setResult('')
    setActiveTab('builder')
  }

  useEffect(() => {
    if (providers.length && !selectedId && workspaceKey === 'new-flow') {
      createNewWorkflow()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [providers.length])

  const loadWorkflow = (endpointId: number) => {
    const endpoint = endpoints.find((item) => item.id === endpointId)
    if (!endpoint) {
      return
    }
    setSelectedId(endpoint.id)
    setName(endpoint.name)
    setSummary(endpoint.summary)
    setFlowDefaults({
      providerSlug: endpoint.providerOrder[0] ?? 'openai',
      model: endpoint.modelName ?? 'gpt-4o-mini',
      path: endpoint.path,
      method: endpoint.method,
    })
    setBlocks(endpoint.blocks)
    setWorkspaceKey(`workflow-${endpoint.id}-${endpoint.updatedAt ?? Date.now()}`)
    setResult(endpoint.generatedCode || '')
    setActiveTab('builder')
    setMenuOpenId(null)
  }

  const saveEndpoint = async () => {
    const response = await api.generateEndpoint({
      name,
      path: flowMeta.path,
      method: flowMeta.method,
      category: 'custom',
      summary,
      endpointType: flowMeta.endpointType,
      compatibilities: flowMeta.compatibilities,
      modelName: flowMeta.model,
      blocks,
      providerOrder: [flowMeta.providerSlug],
      authMode: 'public',
      cacheEnabled: true,
      cacheMode: 'sqlite',
      cacheTtlSeconds: 600,
      rateLimitPerMinute: 90,
    })
    await refreshEndpoints()
    setSelectedId(response.item.id)
    setResult(response.item.generatedCode)
  }

  const runFlow = async () => {
    if (isRunning) {
      return
    }
    setIsRunning(true)
    try {
      const saved = await api.generateEndpoint({
        name,
        path: flowMeta.path,
        method: flowMeta.method,
        category: 'custom',
        summary,
        endpointType: flowMeta.endpointType,
        compatibilities: flowMeta.compatibilities,
        modelName: flowMeta.model,
        blocks,
        providerOrder: [flowMeta.providerSlug],
        authMode: 'public',
        cacheEnabled: true,
        cacheMode: 'sqlite',
        cacheTtlSeconds: 600,
        rateLimitPerMinute: 90,
      })
      await refreshEndpoints()
      setSelectedId(saved.item.id)

      const payload =
        flowMeta.endpointType === 'completion'
          ? { model: flowMeta.model, prompt: 'Say hello from AI-Translator.' }
          : flowMeta.endpointType === 'embedding'
            ? { model: flowMeta.model, input: 'Hello from AI-Translator.' }
            : flowMeta.endpointType === 'image'
              ? { model: flowMeta.model, prompt: 'A clean glowing AI terminal' }
              : flowMeta.endpointType === 'audio'
                ? { model: flowMeta.model, file: 'demo.wav' }
                : { model: flowMeta.model, messages: [{ role: 'user', content: 'Say hello from AI-Translator.' }] }

      const response = await fetch(flowMeta.path, {
        method: flowMeta.method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        credentials: 'include',
      })
      const data = await response.json()
      await refreshLogs()
      setResult(JSON.stringify(data, null, 2))
    } finally {
      setIsRunning(false)
    }
  }

  const renameEndpoint = async (id: number) => {
    const endpoint = endpoints.find((item) => item.id === id)
    if (!endpoint) {
      return
    }
    const nextName = window.prompt('Rename flow', endpoint.name)
    if (!nextName) {
      return
    }
    await api.generateEndpoint({ ...endpoint, name: nextName })
    await refreshEndpoints()
    setMenuOpenId(null)
  }

  const cloneEndpoint = async (id: number) => {
    const endpoint = endpoints.find((item) => item.id === id)
    if (!endpoint) {
      return
    }
    const nextPath = window.prompt('Clone path', `${endpoint.path}-copy`)
    if (!nextPath) {
      return
    }
    await api.cloneEndpoint({ id, path: nextPath, name: `${endpoint.name} Copy` })
    await refreshEndpoints()
    setMenuOpenId(null)
  }

  const deleteEndpoint = async (id: number) => {
    if (!window.confirm('Delete this flow?')) {
      return
    }
    await api.removeEndpoint(id)
    await refreshEndpoints()
    if (selectedId === id) {
      createNewWorkflow()
    }
    setMenuOpenId(null)
  }

  return (
    <div className="space-y-6">
      <SectionCard title="API Builder" eyebrow="Flow Editor" description="The flow is the endpoint. Start and Call API blocks decide the route, provider, and model.">
        <div className="flex flex-wrap items-center gap-2">
          {BUILDER_TABS.map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setActiveTab(tab)}
              className={`rounded-2xl border px-4 py-2 text-sm font-medium capitalize transition ${activeTab === tab ? 'border-cyan-400/35 bg-cyan-300/10 text-white' : 'border-white/10 bg-white/[0.03] text-zinc-400 hover:bg-white/[0.05]'}`}
            >
              {tab}
            </button>
          ))}
          <button type="button" onClick={createNewWorkflow} className="ml-auto inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-400 to-violet-500 px-4 py-2 text-sm font-medium text-zinc-950">
            <Plus className="h-4 w-4" />
            New Flow
          </button>
        </div>
      </SectionCard>

      {activeTab === 'flows' ? (
        <SectionCard title="Saved Flows" eyebrow="Open Flow" description="Open one flow at a time and edit the real endpoint inside the builder.">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {endpoints.map((endpoint) => (
              <div key={endpoint.id} className="relative rounded-3xl border border-white/10 bg-white/[0.03] p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-lg font-semibold text-white">{endpoint.name}</p>
                    <p className="mt-1 text-sm text-zinc-400">{endpoint.path}</p>
                  </div>
                  <button type="button" onClick={() => setMenuOpenId((current) => (current === endpoint.id ? null : endpoint.id))} className="rounded-full border border-white/10 p-2 text-zinc-300">
                    <MoreHorizontal className="h-4 w-4" />
                  </button>
                </div>
                <p className="mt-4 text-sm text-zinc-400">{endpoint.summary || 'Saved API flow'}</p>
                <button type="button" onClick={() => loadWorkflow(endpoint.id)} className="mt-5 inline-flex items-center gap-2 rounded-2xl border border-cyan-400/25 bg-cyan-300/10 px-4 py-2 text-sm text-white">
                  <Sparkles className="h-4 w-4" />
                  Open
                </button>

                {menuOpenId === endpoint.id ? (
                  <div className="absolute right-4 top-14 z-20 w-40 rounded-2xl border border-white/10 bg-[#0b0b11] p-2 shadow-2xl">
                    <button type="button" onClick={() => void renameEndpoint(endpoint.id)} className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm text-zinc-200 hover:bg-white/[0.05]">
                      <Save className="h-4 w-4" />
                      Rename
                    </button>
                    <button type="button" onClick={() => void cloneEndpoint(endpoint.id)} className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm text-zinc-200 hover:bg-white/[0.05]">
                      <Copy className="h-4 w-4" />
                      Clone
                    </button>
                    <button type="button" onClick={() => void deleteEndpoint(endpoint.id)} className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-left text-sm text-rose-200 hover:bg-rose-500/10">
                      <Trash2 className="h-4 w-4" />
                      Delete
                    </button>
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        </SectionCard>
      ) : null}

      {activeTab === 'builder' ? (
        <div className="grid gap-6 xl:grid-cols-[1.45fr_0.95fr]">
          <SectionCard title="Builder" eyebrow="Blocks" description="Provider and model are defined in the blocks only, not outside the code area.">
            <BlocklyCanvas
              providers={providers}
              defaultProvider={flowMeta.providerSlug}
              defaultModel={flowMeta.model}
              defaultPath={flowMeta.path}
              defaultMethod={flowMeta.method as 'POST' | 'GET'}
              workspaceData={blocks}
              workspaceKey={workspaceKey}
              onChange={setBlocks}
            />
          </SectionCard>

          <SectionCard title="Flow Details" eyebrow="Simple Setup" description="Name the flow, then save or run the exact endpoint defined by the Start block.">
            <div className="space-y-4">
              <label className="block text-sm text-zinc-300">
                Flow Name
                <input value={name} onChange={(event) => setName(event.target.value)} className="mt-2 w-full rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-white outline-none" />
              </label>
              <label className="block text-sm text-zinc-300">
                Summary
                <textarea value={summary} onChange={(event) => setSummary(event.target.value)} className="mt-2 h-20 w-full rounded-2xl border border-white/10 bg-zinc-950 px-4 py-3 text-white outline-none" />
              </label>
              <div className="grid gap-3">
                <div className="rounded-2xl border border-white/10 bg-zinc-950 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Endpoint</p>
                  <p className="mt-2 font-medium text-white">{flowMeta.method} {flowMeta.path}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-zinc-950 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Provider And Model</p>
                  <div className="mt-3 flex items-center gap-3">
                    {flowMeta.provider ? (
                      <ProviderLogo
                        name={flowMeta.provider.displayName}
                        initials={flowMeta.provider.logoText}
                        color={flowMeta.provider.logoColor}
                        className="h-10 w-10"
                      />
                    ) : null}
                    <div>
                      <p className="text-sm font-medium text-white">{flowMeta.provider?.displayName ?? 'No provider selected'}</p>
                      <p className="text-sm text-zinc-400">{flowMeta.model}</p>
                    </div>
                  </div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-zinc-950 p-4">
                  <p className="text-xs uppercase tracking-[0.2em] text-zinc-500">Endpoint Style</p>
                  <p className="mt-2 font-medium capitalize text-white">{endpointStyle}</p>
                  <p className="mt-1 text-sm text-zinc-400">This comes from Settings and controls compatibility automatically.</p>
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <button onClick={() => void saveEndpoint()} className="inline-flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-400 to-violet-500 px-4 py-3 font-medium text-zinc-950">
                  <Save className="h-4 w-4" />
                  Save Flow
                </button>
                <button
                  onClick={() => void runFlow()}
                  disabled={isRunning}
                  className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 font-medium text-white disabled:cursor-not-allowed disabled:opacity-60"
                >
                  <Play className="h-4 w-4" />
                  {isRunning ? 'Running...' : 'Run Flow'}
                </button>
              </div>
              <pre className="max-h-56 overflow-y-auto overflow-x-auto whitespace-pre rounded-2xl border border-white/10 bg-zinc-950 p-4 text-xs text-cyan-100">
                {result || 'Save or run the flow to see generated code or endpoint output.'}
              </pre>
            </div>
          </SectionCard>
        </div>
      ) : null}

      {activeTab === 'guide' ? (
        <SectionCard title="How To Use" eyebrow="Guide" description="A simple guide for building a working endpoint flow.">
          <div className="space-y-4 text-sm text-zinc-300">
            <p>1. Add an API key in `Providers`. You do not set the model there anymore.</p>
            <p>2. Open `API Builder` and create a new flow.</p>
            <p>3. In the `Start` block, set the endpoint path you want this flow to become.</p>
            <p>4. In the `Call API` block, pick the provider and model to use for that endpoint.</p>
            <p>5. Add `Repeat Cmds`, `Repeat Until True`, or `Custom Code` blocks if your flow needs them.</p>
            <p>6. Click `Save Flow` to create or update that same endpoint.</p>
            <p>7. Click `Run Flow` to call the exact endpoint path from the flow, not a separate test endpoint.</p>
            <p>8. Change endpoint style in `Settings` if you want OpenAI, Anthropic, Gemini, or LM Studio compatibility.</p>
          </div>
        </SectionCard>
      ) : null}
    </div>
  )
}
