import { useEffect, useRef } from 'react'
import * as Blockly from 'blockly'

type BlocklyCanvasProps = {
  providers?: Array<{ slug: string; displayName: string; models?: string[] }>
  defaultProvider?: string
  defaultModel?: string
  defaultPath?: string
  defaultMethod?: 'POST' | 'GET'
  workspaceData?: Record<string, unknown>
  workspaceKey?: string
  onChange: (data: Record<string, unknown>) => void
}

const toolbox = {
  kind: 'categoryToolbox',
  contents: [
    {
      kind: 'category',
      name: 'Gateway',
      colour: '#22d3ee',
      contents: [
        { kind: 'block', type: 'on_api_call' },
        { kind: 'block', type: 'call_api' },
        { kind: 'block', type: 'provider' },
        { kind: 'block', type: 'api_key' },
        { kind: 'block', type: 'model' },
        { kind: 'block', type: 'prompt' },
        { kind: 'block', type: 'input' },
        { kind: 'block', type: 'output' },
      ],
    },
    {
      kind: 'category',
      name: 'Control',
      colour: '#8b5cf6',
      contents: [
        { kind: 'block', type: 'cache' },
        { kind: 'block', type: 'condition' },
        { kind: 'block', type: 'transform' },
        { kind: 'block', type: 'logging' },
        { kind: 'block', type: 'authentication' },
        { kind: 'block', type: 'failover' },
        { kind: 'block', type: 'retry' },
        { kind: 'block', type: 'rate_limit' },
        { kind: 'block', type: 'repeat_times' },
        { kind: 'block', type: 'repeat_until_true' },
        { kind: 'block', type: 'webhook' },
        { kind: 'block', type: 'json_formatter' },
        { kind: 'block', type: 'response_formatter' },
        { kind: 'block', type: 'custom_code' },
      ],
    },
  ],
}

let initialized = false
let currentProviderOptions: Array<[string, string]> = [['OpenAI', 'openai']]
let providerModelOptions: Record<string, Array<[string, string]>> = {
  openai: [['gpt-4o-mini', 'gpt-4o-mini']],
}
let currentDefaults = {
  provider: 'openai',
  model: 'gpt-4o-mini',
  path: '/api/custom',
  method: 'POST',
}

const blockTypes = [
  ['provider', 'Provider', '#22d3ee'],
  ['api_key', 'API Key', '#22d3ee'],
  ['model', 'Model', '#22d3ee'],
  ['prompt', 'Prompt', '#22d3ee'],
  ['input', 'Input', '#22d3ee'],
  ['output', 'Output', '#22d3ee'],
  ['cache', 'Cache', '#8b5cf6'],
  ['condition', 'Condition', '#8b5cf6'],
  ['transform', 'Transform', '#8b5cf6'],
  ['logging', 'Logging', '#8b5cf6'],
  ['authentication', 'Authentication', '#8b5cf6'],
  ['failover', 'Failover', '#8b5cf6'],
  ['retry', 'Retry', '#8b5cf6'],
  ['rate_limit', 'Rate Limit', '#8b5cf6'],
  ['webhook', 'Webhook', '#8b5cf6'],
  ['json_formatter', 'JSON Formatter', '#8b5cf6'],
  ['response_formatter', 'Response Formatter', '#8b5cf6'],
] as const

function ensureBlocks() {
  if (initialized) {
    return
  }
  initialized = true

  Blockly.Blocks.on_api_call = {
    init() {
      this.appendDummyInput()
        .appendField('Start')
        .appendField('method')
        .appendField(new Blockly.FieldDropdown([
          ['POST', 'POST'],
          ['GET', 'GET'],
        ]), 'METHOD')
        .appendField('path')
        .appendField(new Blockly.FieldTextInput(currentDefaults.path), 'PATH')
      this.setNextStatement(true)
      this.setColour('#22d3ee')
      this.setMovable(false)
      this.setDeletable(false)
    },
  }

  Blockly.Blocks.call_api = {
    init() {
      const getModelOptions = function (this: Blockly.FieldDropdown) {
        const sourceBlock = this.getSourceBlock()
        const providerSlug = sourceBlock?.getFieldValue('PROVIDER') ?? currentDefaults.provider
        return providerModelOptions[providerSlug] ?? [[currentDefaults.model, currentDefaults.model]]
      }

      this.appendDummyInput()
        .appendField('Call API')
        .appendField('provider')
        .appendField(new Blockly.FieldDropdown(() => currentProviderOptions), 'PROVIDER')
        .appendField('model')
        .appendField(new Blockly.FieldDropdown(getModelOptions), 'MODEL')
      this.setPreviousStatement(true)
      this.setNextStatement(true)
      this.setColour('#22d3ee')
    },
  }

  Blockly.Blocks.repeat_times = {
    init() {
      this.appendDummyInput()
        .appendField('Repeat Cmds')
        .appendField(new Blockly.FieldNumber(3, 1, 100, 1), 'COUNT')
      this.setPreviousStatement(true)
      this.setNextStatement(true)
      this.setColour('#8b5cf6')
    },
  }

  Blockly.Blocks.repeat_until_true = {
    init() {
      this.appendDummyInput()
        .appendField('Repeat Until True')
        .appendField(new Blockly.FieldTextInput('response.ok'), 'CONDITION')
      this.setPreviousStatement(true)
      this.setNextStatement(true)
      this.setColour('#8b5cf6')
    },
  }

  Blockly.Blocks.custom_code = {
    init() {
      this.appendDummyInput()
        .appendField('Custom Code')
        .appendField(new Blockly.FieldTextInput('return payload'), 'CODE')
      this.setPreviousStatement(true)
      this.setNextStatement(true)
      this.setColour('#8b5cf6')
    },
  }

  blockTypes.forEach(([type, label, color]) => {
    Blockly.Blocks[type] = {
      init() {
        this.appendDummyInput().appendField(label)
        this.setPreviousStatement(true)
        this.setNextStatement(true)
        this.setColour(color)
      },
    }
  })
}

function createDefaultWorkspace() {
  return {
  blocks: {
    languageVersion: 0,
    blocks: [
      {
        type: 'on_api_call',
        id: 'default-on-api-call',
        x: 36,
        y: 34,
        fields: {
          METHOD: currentDefaults.method,
          PATH: currentDefaults.path,
        },
        next: {
          block: {
            type: 'call_api',
            id: 'default-call-api',
            fields: {
              PROVIDER: currentDefaults.provider,
              MODEL: currentDefaults.model,
            },
          },
        },
      },
    ],
  },
}
}

function hasWorkspaceBlocks(workspaceData?: Record<string, unknown>) {
  const blocks = workspaceData?.blocks
  return Boolean(blocks && typeof blocks === 'object' && Array.isArray((blocks as { blocks?: unknown[] }).blocks) && (blocks as { blocks?: unknown[] }).blocks?.length)
}

export function BlocklyCanvas({
  providers = [],
  defaultProvider = 'openai',
  defaultModel = 'gpt-4o-mini',
  defaultPath = '/api/custom',
  defaultMethod = 'POST',
  workspaceData,
  workspaceKey,
  onChange,
}: BlocklyCanvasProps) {
  const hostRef = useRef<HTMLDivElement | null>(null)
  const workspaceRef = useRef<Blockly.WorkspaceSvg | null>(null)
  const loadingRef = useRef(false)

  currentProviderOptions = providers.length
    ? providers.map((provider) => [provider.displayName, provider.slug] as [string, string])
    : [['OpenAI', 'openai']]

  providerModelOptions = Object.fromEntries(
    providers.map((provider) => [
      provider.slug,
      (provider.models?.length ? provider.models : [defaultModel]).map((model) => [model, model] as [string, string]),
    ]),
  )
  if (!providerModelOptions[defaultProvider]) {
    providerModelOptions[defaultProvider] = [[defaultModel, defaultModel]]
  }
  currentDefaults = {
    provider: defaultProvider,
    model: defaultModel,
    path: defaultPath,
    method: defaultMethod,
  }

  useEffect(() => {
    ensureBlocks()
    if (!hostRef.current || workspaceRef.current) {
      return
    }
    const workspace = Blockly.inject(hostRef.current, {
      toolbox,
      grid: { spacing: 20, length: 3, colour: '#27272a', snap: true },
      zoom: { controls: true, wheel: true, startScale: 0.9 },
      theme: Blockly.Theme.defineTheme('api-translate', {
        name: 'api-translate',
        componentStyles: {
          workspaceBackgroundColour: '#09090b',
          toolboxBackgroundColour: '#111116',
          toolboxForegroundColour: '#f4f4f5',
          flyoutBackgroundColour: '#0f172a',
          flyoutForegroundColour: '#f4f4f5',
          flyoutOpacity: 0.92,
          scrollbarColour: '#3f3f46',
          insertionMarkerColour: '#22d3ee',
          insertionMarkerOpacity: 0.3,
        },
      }),
    })

    workspace.addChangeListener(() => {
      if (loadingRef.current) {
        return
      }

      const apiBlocks = workspace.getAllBlocks(false).filter((block) => block.type === 'call_api')
      for (const block of apiBlocks) {
        const providerSlug = block.getFieldValue('PROVIDER') || currentDefaults.provider
        const supportedModels = (providerModelOptions[providerSlug] ?? [[currentDefaults.model, currentDefaults.model]]).map(
          ([label]) => label,
        )
        const currentModel = block.getFieldValue('MODEL')
        if (!currentModel || !supportedModels.includes(currentModel)) {
          block.setFieldValue(supportedModels[0], 'MODEL')
        }
      }

      onChange(Blockly.serialization.workspaces.save(workspace) as Record<string, unknown>)
    })

    loadingRef.current = true
    Blockly.serialization.workspaces.load(((hasWorkspaceBlocks(workspaceData) ? workspaceData : createDefaultWorkspace()) as never), workspace)
    loadingRef.current = false
    workspaceRef.current = workspace
    return () => {
      workspace.dispose()
      workspaceRef.current = null
    }
  }, [onChange])

  useEffect(() => {
    if (!workspaceRef.current) {
      return
    }
    loadingRef.current = true
    workspaceRef.current.clear()
    Blockly.serialization.workspaces.load(((hasWorkspaceBlocks(workspaceData) ? workspaceData : createDefaultWorkspace()) as never), workspaceRef.current)
    loadingRef.current = false
  }, [workspaceKey])

  return <div ref={hostRef} className="h-[520px] w-full overflow-hidden rounded-3xl border border-white/10" />
}
