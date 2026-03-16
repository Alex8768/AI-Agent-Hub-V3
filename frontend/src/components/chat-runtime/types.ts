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

export interface RuntimeEvent {
  id: string
  type: RuntimeEventType
  title: string
  detail?: string
  timestamp: number
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

export interface ApprovalItem {
  id: string
  kind: 'approval'
  title: string
  detail: string
  prompt: string
  status: 'pending' | 'approved' | 'denied' | 'review'
}

export interface ResultItem {
  id: string
  kind: 'result'
  content: string
  error?: boolean
}

export type ChatTimelineItem =
  | UserMessageItem
  | AssistantMessageItem
  | ReasoningSummaryItem
  | PlanItem
  | ExecutionEventItem
  | ApprovalItem
  | ResultItem
