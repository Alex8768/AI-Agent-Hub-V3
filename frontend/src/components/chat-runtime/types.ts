export type RuntimeEventType =
  | 'run_started'
  | 'plan_created'
  | 'step_started'
  | 'step_completed'
  | 'reasoning_summary'
  | 'tool_call_started'
  | 'tool_call_completed'
  | 'file_read'
  | 'file_write_proposed'
  | 'approval_required'
  | 'approval_resolved'
  | 'warning'
  | 'final_response'
  | 'run_completed'
  | 'run_failed'
  | 'companion_opened'

export type RuntimePhase = 'analyze' | 'discover' | 'plan' | 'execute' | 'finalize'
export type RuntimeStatus = 'active' | 'completed' | 'waiting' | 'warning' | 'failed'
export type RunStatus = 'running' | 'waiting_approval' | 'completed' | 'failed'

export interface RuntimeEvent {
  id: string
  type: RuntimeEventType
  title: string
  detail?: string
  phase?: RuntimePhase
  status?: RuntimeStatus
  timestamp: number
}

export interface PhaseDetailItem {
  id: string
  kind: 'event' | 'file' | 'tool' | 'warning'
  summary: string
  detail?: string
  status?: RuntimeStatus
  tag?: string
}

export interface RuntimePhaseState {
  phase: RuntimePhase
  status: RuntimeStatus
  summary: string
  details: PhaseDetailItem[]
}

export interface RuntimeRunItem {
  id: string
  kind: 'runtime_run'
  prompt: string
  status: RunStatus
  startedAt: number
  phases: RuntimePhaseState[]
  activePhase: RuntimePhase
  approvalGate?: {
    title: string
    detail: string
    targetSummary?: string
    risk: 'low' | 'medium' | 'high'
    status: 'pending' | 'approved' | 'denied' | 'review'
  }
}

export interface UserMessageItem {
  id: string
  kind: 'user_message'
  content: string
}

export interface AssistantMessageItem {
  id: string
  kind: 'assistant_message'
  content: string
}

export interface ReasoningSummaryItem {
  id: string
  kind: 'reasoning_summary'
  summary: string
}

export interface PlanItem {
  id: string
  kind: 'plan'
  steps: string[]
}

export interface ExecutionEventItem {
  id: string
  kind: 'execution_event'
  event: RuntimeEvent
}

export interface FileActivityItem {
  id: string
  kind: 'file_activity'
  action: 'read' | 'write_proposed' | 'write_completed' | 'compared'
  target: string
  summary: string
  detail?: string
  phase?: RuntimePhase
}

export interface ToolActivityItem {
  id: string
  kind: 'tool_activity'
  state: 'started' | 'completed' | 'failed'
  toolName: string
  summary: string
  detail?: string
  phase?: RuntimePhase
}

export interface ApprovalItem {
  id: string
  kind: 'approval'
  title: string
  detail: string
  prompt: string
  targetSummary?: string
  risk: 'low' | 'medium' | 'high'
  status: 'pending' | 'approved' | 'denied' | 'review'
}

export interface WarningItem {
  id: string
  kind: 'warning'
  title: string
  detail: string
}

export interface ResultItem {
  id: string
  kind: 'result'
  content: string
  summary?: string
  traceSummary?: string
  contextSummary?: string
  error?: boolean
}

export type ChatTimelineItem =
  | UserMessageItem
  | RuntimeRunItem
  | AssistantMessageItem
  | ReasoningSummaryItem
  | PlanItem
  | ExecutionEventItem
  | FileActivityItem
  | ToolActivityItem
  | ApprovalItem
  | WarningItem
  | ResultItem
