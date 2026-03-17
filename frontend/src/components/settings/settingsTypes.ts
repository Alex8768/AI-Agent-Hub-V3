export type ApiProvider = 'openai' | 'ollama' | 'anthropic'
export type ReasoningMode = 'standard' | 'deep'
export type LayoutDensity = 'comfortable' | 'compact'
export type ApprovalStrictness = 'balanced' | 'strict'
export type ExecutionDetailLevel = 'summary' | 'detailed'
export type FileSafetyPolicy = 'confirm-writes' | 'readonly-preferred'

export interface LegacyAgentSettings {
  apiProvider: string
  selectedModel: string
  reasoningMode: ReasoningMode
  forceSearch: boolean
  showReasoning: boolean
  apiBaseUrl: string
}

export interface ConnectionModelSettings {
  provider: ApiProvider
  model: string
  endpoint: string
}

export interface AgentBehaviorSettings {
  reasoningMode: ReasoningMode
  searchBehavior: 'normal' | 'force'
  approvalStrictness: ApprovalStrictness
  executionDetailLevel: ExecutionDetailLevel
  autoOpenTrace: boolean
  autoOpenCanvas: boolean
}

export interface WorkspaceSettingsState {
  workspaceRoot: string
  fileSafetyPolicy: FileSafetyPolicy
  defaultsProfile: 'default' | 'safe'
  sessionPreference: 'project-scoped' | 'global'
}

export interface AppSettingsState {
  connection: ConnectionModelSettings
  behavior: AgentBehaviorSettings
  workspace: WorkspaceSettingsState
}

export const DEFAULT_APP_SETTINGS: AppSettingsState = {
  connection: {
    provider: 'openai',
    model: '',
    endpoint: '',
  },
  behavior: {
    reasoningMode: 'standard',
    searchBehavior: 'normal',
    approvalStrictness: 'balanced',
    executionDetailLevel: 'summary',
    autoOpenTrace: false,
    autoOpenCanvas: false,
  },
  workspace: {
    workspaceRoot: '',
    fileSafetyPolicy: 'confirm-writes',
    defaultsProfile: 'default',
    sessionPreference: 'project-scoped',
  },
}

export function toLegacyAgentSettings(settings: AppSettingsState): LegacyAgentSettings {
  return {
    apiProvider: settings.connection.provider,
    selectedModel: settings.connection.model,
    reasoningMode: settings.behavior.reasoningMode,
    forceSearch: settings.behavior.searchBehavior === 'force',
    showReasoning: settings.behavior.executionDetailLevel !== 'summary' || settings.behavior.reasoningMode === 'deep',
    apiBaseUrl: settings.connection.endpoint,
  }
}
