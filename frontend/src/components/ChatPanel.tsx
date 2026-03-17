import { useEffect, useMemo, useRef, useState } from 'react'
import { CheckCircle2, ChevronDown, Circle, Loader2, SendHorizontal, ShieldAlert, XCircle } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import ResultActionBar, { type ResultActionVisibility } from './chat-runtime/ResultActionBar'
import RuntimeCard from './chat-runtime/RuntimeCard'
import type {
  ChatTimelineItem,
  RuntimePhase,
  RuntimePhaseState,
  RuntimeRunItem,
  RuntimeStatus,
} from './chat-runtime/types'
import type { CanvasViewType } from './canvas/canvasState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Textarea } from '@/components/ui/textarea'
import { sendMessage } from '../lib/apiClient'
import { useAppContext } from '../context/useAppContext'

interface ChatPanelProps {
  workspaceId: string
  sessionId: string
  onSessionUsed: (ws: string, sid: string) => void
  locale?: 'en' | 'ru' | 'de' | 'fr'
  onOpenCanvasView?: (request: {
    view: CanvasViewType
    title?: string
    payload?: unknown
    mode?: 'canvas' | 'split'
  }) => void
  settings: {
    apiProvider: string
    selectedModel: string
    reasoningMode: 'standard' | 'deep'
    forceSearch: boolean
    showReasoning: boolean
    showExecutionEvents?: boolean
    showTraceShortcut?: boolean
    apiBaseUrl: string
  }
}

const PHASE_ORDER: RuntimePhase[] = ['analyze', 'discover', 'plan', 'execute', 'finalize']

function makeMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function isApprovalRequired(prompt: string): boolean {
  const sensitiveTerms = ['delete', 'overwrite', 'remove', 'rm ', 'drop ', 'truncate', 'write file', 'dangerous']
  const lower = prompt.toLowerCase()
  return sensitiveTerms.some((term) => lower.includes(term))
}

function makeInitialPhases(): RuntimePhaseState[] {
  return [
    { phase: 'analyze', status: 'active', summary: 'Analyzing request', details: [] },
    { phase: 'discover', status: 'waiting', summary: 'Waiting for discovery', details: [] },
    { phase: 'plan', status: 'waiting', summary: 'Waiting for plan', details: [] },
    { phase: 'execute', status: 'waiting', summary: 'Waiting for execution', details: [] },
    { phase: 'finalize', status: 'waiting', summary: 'Waiting for finalization', details: [] },
  ]
}

function phaseLabel(phase: RuntimePhase): string {
  if (phase === 'analyze') return 'Analyze'
  if (phase === 'discover') return 'Discover'
  if (phase === 'plan') return 'Plan'
  if (phase === 'execute') return 'Execute'
  return 'Finalize'
}

function statusLabel(status: RuntimeStatus): string {
  if (status === 'active') return 'active'
  if (status === 'completed') return 'done'
  if (status === 'waiting') return 'waiting'
  if (status === 'warning') return 'warning'
  return 'failed'
}

function tick(ms = 120): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export default function ChatPanel({
  workspaceId,
  sessionId,
  onSessionUsed,
  locale = 'en',
  settings,
  onOpenCanvasView,
}: ChatPanelProps) {
  const [timeline, setTimeline] = useState<ChatTimelineItem[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [requestError, setRequestError] = useState<string>('')
  const [lastPrompt, setLastPrompt] = useState('')
  const { lastAnswer, setLastAnswer } = useAppContext()

  const scrollRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (!scrollRef.current) return
    const viewport = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]') as HTMLDivElement | null
    if (!viewport) return
    viewport.scrollTop = viewport.scrollHeight
  }, [timeline, isLoading])

  useEffect(() => {
    if (!textareaRef.current) return
    textareaRef.current.style.height = '0px'
    textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 220)}px`
  }, [input])

  const canSend = useMemo(() => input.trim().length > 0 && !isLoading, [input, isLoading])

  const ui = useMemo(
    () => ({
      emptyTitle: locale === 'ru' ? 'Чем я могу помочь?' : 'How can I help?',
      emptyText:
        locale === 'ru'
          ? 'Спросите о документах, задачах или просто начните диалог.'
          : 'Ask about documents, tasks, or start a conversation.',
      you: locale === 'ru' ? 'Вы' : 'You',
      error: locale === 'ru' ? 'Ошибка' : 'Error',
      requestFailedHint:
        locale === 'ru'
          ? 'Не удалось получить ответ. Проверьте подключение и попробуйте снова.'
          : 'Failed to get response. Check connection and try again.',
      placeholder: locale === 'ru' ? 'Напишите сообщение...' : 'Type a message...',
      send: locale === 'ru' ? 'Отправить' : 'Send',
      working: locale === 'ru' ? 'Выполняю run...' : 'Running...',
      runReady: locale === 'ru' ? 'Runtime stream active' : 'Runtime stream active',
      enterToSend: locale === 'ru' ? 'Enter - отправить' : 'Enter to send',
      shiftEnter: locale === 'ru' ? 'Shift+Enter - новая строка' : 'Shift+Enter for new line',
      approve: locale === 'ru' ? 'Approve' : 'Approve',
      deny: locale === 'ru' ? 'Deny' : 'Deny',
      review: locale === 'ru' ? 'Review' : 'Review',
    }),
    [locale],
  )

  const createRun = (prompt: string): string => {
    const runId = makeMessageId()
    const runItem: RuntimeRunItem = {
      id: runId,
      kind: 'runtime_run',
      prompt,
      status: 'running',
      startedAt: Date.now(),
      phases: makeInitialPhases(),
      activePhase: 'analyze',
    }
    setTimeline((prev) => [...prev, runItem])
    return runId
  }

  const updateRun = (runId: string, updater: (run: RuntimeRunItem) => RuntimeRunItem) => {
    setTimeline((prev) => prev.map((item) => (item.kind === 'runtime_run' && item.id === runId ? updater(item) : item)))
  }

  const setPhase = (runId: string, phase: RuntimePhase, status: RuntimeStatus, summary?: string) => {
    updateRun(runId, (run) => ({
      ...run,
      activePhase: status === 'active' ? phase : run.activePhase,
      phases: run.phases.map((entry) =>
        entry.phase === phase
          ? {
              ...entry,
              status,
              summary: summary ?? entry.summary,
            }
          : entry,
      ),
    }))
  }

  const pushPhaseDetail = (
    runId: string,
    phase: RuntimePhase,
    detail: {
      kind: 'event' | 'file' | 'tool' | 'warning'
      summary: string
      detail?: string
      status?: RuntimeStatus
      tag?: string
    },
  ) => {
    updateRun(runId, (run) => ({
      ...run,
      phases: run.phases.map((entry) =>
        entry.phase === phase
          ? {
              ...entry,
              details: [
                ...entry.details,
                {
                  id: makeMessageId(),
                  ...detail,
                },
              ],
            }
          : entry,
      ),
    }))
  }

  const appendResult = (result: {
    content: string
    summary?: string
    error?: boolean
    traceSummary?: string
    contextSummary?: string
  }) => {
    setTimeline((prev) => [
      ...prev,
      {
        id: makeMessageId(),
        kind: 'result',
        content: result.content,
        summary: result.summary,
        error: result.error,
        traceSummary: result.traceSummary,
        contextSummary: result.contextSummary,
      },
    ])
  }

  const executeRun = async (runId: string, prompt: string) => {
    setIsLoading(true)
    setRequestError('')
    setLastPrompt(prompt)
    onSessionUsed(workspaceId, sessionId)

    setPhase(runId, 'analyze', 'active', 'Analyzing request and constraints')
    pushPhaseDetail(runId, 'analyze', {
      kind: 'event',
      summary: 'Run started',
      detail: 'Runtime block initialized for this user request.',
      status: 'active',
      tag: 'run',
    })
    if (settings.showReasoning) {
      pushPhaseDetail(runId, 'analyze', {
        kind: 'event',
        summary: 'Reasoning summary prepared',
        detail:
          locale === 'ru'
            ? 'Краткая стратегия: проверка запроса, backend вызов, финальная сводка.'
            : 'Summary strategy: validate request, call backend, assemble final response.',
        status: 'completed',
        tag: 'reasoning',
      })
    }
    await tick()
    setPhase(runId, 'analyze', 'completed', 'Request understanding completed')

    setPhase(runId, 'discover', 'active', 'Collecting workspace and context signals')
    pushPhaseDetail(runId, 'discover', {
      kind: 'file',
      summary: 'Workspace context checked',
      detail: 'Resolved active workspace/session for this run.',
      status: 'completed',
      tag: 'read',
    })
    await tick()
    setPhase(runId, 'discover', 'completed', 'Discovery completed')

    setPhase(runId, 'plan', 'active', 'Preparing execution plan')
    pushPhaseDetail(runId, 'plan', {
      kind: 'event',
      summary: 'Plan prepared',
      detail: 'Analyze -> discover -> execute -> finalize.',
      status: 'completed',
      tag: 'plan',
    })
    await tick()
    setPhase(runId, 'plan', 'completed', 'Plan ready')

    setPhase(runId, 'execute', 'active', 'Executing backend answer pipeline')
    pushPhaseDetail(runId, 'execute', {
      kind: 'tool',
      summary: 'sendMessage started',
      detail: `${settings.apiProvider} / ${settings.selectedModel || 'default model'}`,
      status: 'active',
      tag: 'tool',
    })

    try {
      const response = await sendMessage(workspaceId, sessionId, prompt, {
        api_provider: settings.apiProvider,
        model: settings.selectedModel,
        reasoning_mode: settings.reasoningMode,
        force_search: settings.forceSearch,
      })

      pushPhaseDetail(runId, 'execute', {
        kind: 'tool',
        summary: 'sendMessage completed',
        status: 'completed',
        tag: 'tool',
      })
      setPhase(runId, 'execute', 'completed', 'Execution completed')

      setPhase(runId, 'finalize', 'active', 'Finalizing outcome')
      if (response.context_preview) {
        pushPhaseDetail(runId, 'finalize', {
          kind: 'file',
          summary: 'Context sources available',
          detail: 'You can inspect them via Show Context.',
          status: 'completed',
          tag: 'context',
        })
      }
      await tick()
      setPhase(runId, 'finalize', 'completed', 'Run completed successfully')

      updateRun(runId, (run) => ({ ...run, status: 'completed' }))
      appendResult({
        content: response.answer || '(no response)',
        summary: 'Final answer produced from completed run.',
        traceSummary: response.diagnostics ? 'Trace diagnostics available.' : undefined,
        contextSummary: response.context_preview ? 'Context sources available.' : undefined,
      })
      setLastAnswer(response)
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error)
      setRequestError(message)

      pushPhaseDetail(runId, 'execute', {
        kind: 'tool',
        summary: 'sendMessage failed',
        detail: message,
        status: 'failed',
        tag: 'tool',
      })
      setPhase(runId, 'execute', 'failed', 'Execution failed')
      setPhase(runId, 'finalize', 'failed', 'Run ended with failure')
      pushPhaseDetail(runId, 'finalize', {
        kind: 'warning',
        summary: 'Runtime failure recorded',
        detail: message,
        status: 'failed',
        tag: 'warning',
      })
      updateRun(runId, (run) => ({ ...run, status: 'failed' }))

      appendResult({
        content: `**${ui.error}:**\n\n${message}`,
        summary: 'Run failed before successful completion.',
        error: true,
      })
      console.error('Failed to execute runtime prompt:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSend = async () => {
    const prompt = input.trim()
    if (!prompt || isLoading) return
    setInput('')

    setTimeline((prev) => [
      ...prev,
      {
        id: makeMessageId(),
        kind: 'user_message',
        content: prompt,
      },
    ])

    const runId = createRun(prompt)

    if (isApprovalRequired(prompt)) {
      setPhase(runId, 'analyze', 'completed', 'Request analyzed')
      setPhase(runId, 'discover', 'completed', 'Discovery completed')
      setPhase(runId, 'plan', 'waiting', 'Waiting for approval gate')
      updateRun(runId, (run) => ({
        ...run,
        status: 'waiting_approval',
        activePhase: 'plan',
        approvalGate: {
          title: locale === 'ru' ? 'Требуется подтверждение' : 'Approval required',
          detail:
            locale === 'ru'
              ? 'Запрос может менять файлы или данные. Подтвердите запуск.'
              : 'This request may modify files or data. Confirm before execution.',
          targetSummary: prompt.slice(0, 140),
          risk: 'high',
          status: 'pending',
        },
      }))
      pushPhaseDetail(runId, 'plan', {
        kind: 'file',
        summary: 'Write operation proposed',
        detail: 'Execution paused until user approval.',
        status: 'waiting',
        tag: 'approval',
      })
      return
    }

    await executeRun(runId, prompt)
  }

  const copyResult = async (content: string) => {
    if (!content.trim()) return
    await navigator.clipboard.writeText(content)
  }

  const rerunLastPrompt = async () => {
    if (!lastPrompt || isLoading) return
    const runId = createRun(lastPrompt)
    await executeRun(runId, lastPrompt)
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <ScrollArea className="min-h-0 flex-1" ref={scrollRef}>
        <div className="mx-auto flex w-full max-w-4xl flex-col gap-3 px-4 py-4">
          {timeline.length === 0 && !isLoading && (
            <Card className="mx-auto mt-8 w-full max-w-2xl">
              <CardHeader>
                <CardTitle className="text-2xl">{ui.emptyTitle}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">{ui.emptyText}</p>
              </CardContent>
            </Card>
          )}

          {timeline.map((item) => {
            if (item.kind === 'user_message') {
              return (
                <div key={item.id} className="flex justify-end">
                  <div className="flex w-full max-w-3xl flex-row-reverse gap-3">
                    <div className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border bg-muted text-xs font-semibold">
                      {ui.you.charAt(0)}
                    </div>
                    <Card className="w-full">
                      <CardContent className="p-4">
                        <div className="prose prose-sm max-w-none dark:prose-invert">
                          <ReactMarkdown>{item.content}</ReactMarkdown>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )
            }

            if (item.kind === 'runtime_run') {
              const progressIndex = PHASE_ORDER.indexOf(item.activePhase)
              const progressPct = Math.max(15, Math.round(((progressIndex + 1) / PHASE_ORDER.length) * 100))

              return (
                <RuntimeCard
                  key={item.id}
                  variant="execution"
                  title="Runtime run"
                  subtitle={item.status === 'running' ? 'In progress' : item.status === 'waiting_approval' ? 'Waiting for approval' : item.status === 'completed' ? 'Completed' : 'Failed'}
                  badge={item.status}
                >
                  <div className="space-y-3">
                    <div className="h-1.5 w-full rounded-full bg-muted/60">
                      <div
                        className={`h-1.5 rounded-full transition-all ${
                          item.status === 'failed'
                            ? 'bg-destructive'
                            : item.status === 'completed'
                              ? 'bg-emerald-500'
                              : item.status === 'waiting_approval'
                                ? 'bg-amber-500'
                                : 'bg-primary'
                        }`}
                        style={{ width: `${progressPct}%` }}
                      />
                    </div>

                    <div className="space-y-2">
                      {item.phases.map((phase) => (
                        <div key={phase.phase} className="rounded-md border bg-background/60 p-2.5">
                          <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2 text-sm">
                              {phase.status === 'completed' ? (
                                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                              ) : phase.status === 'failed' ? (
                                <XCircle className="h-4 w-4 text-destructive" />
                              ) : phase.status === 'active' ? (
                                <Loader2 className="h-4 w-4 animate-spin text-primary" />
                              ) : (
                                <Circle className="h-4 w-4 text-muted-foreground" />
                              )}
                              <span className="font-medium">{phaseLabel(phase.phase)}</span>
                            </div>
                            <Badge variant="outline" className="text-[10px]">
                              {statusLabel(phase.status)}
                            </Badge>
                          </div>
                          <p className="mt-1 text-xs text-muted-foreground">{phase.summary}</p>
                          {phase.details.length > 0 && (
                            <Collapsible>
                              <CollapsibleTrigger asChild>
                                <Button size="sm" variant="ghost" className="mt-1 h-7 px-2 text-xs text-muted-foreground">
                                  Details
                                  <ChevronDown className="ml-1 h-3.5 w-3.5" />
                                </Button>
                              </CollapsibleTrigger>
                              <CollapsibleContent className="space-y-1.5 pt-1">
                                {phase.details.map((detail) => (
                                  <div key={detail.id} className="rounded border bg-muted/20 p-2 text-xs">
                                    <div className="mb-1 flex items-center gap-1.5">
                                      {detail.tag && (
                                        <Badge variant="outline" className="text-[10px]">
                                          {detail.tag}
                                        </Badge>
                                      )}
                                      {detail.status && (
                                        <span className="text-[10px] uppercase tracking-wide text-muted-foreground">
                                          {statusLabel(detail.status)}
                                        </span>
                                      )}
                                    </div>
                                    <div className="font-medium">{detail.summary}</div>
                                    {detail.detail && <p className="mt-0.5 text-muted-foreground">{detail.detail}</p>}
                                  </div>
                                ))}
                              </CollapsibleContent>
                            </Collapsible>
                          )}
                        </div>
                      ))}
                    </div>

                    {item.approvalGate && (
                      <div className="rounded-md border border-orange-300/70 bg-orange-50/30 p-3 dark:bg-orange-900/15">
                        <div className="mb-1.5 flex items-center justify-between gap-2">
                          <div className="flex items-center gap-2 text-sm font-medium">
                            <ShieldAlert className="h-4 w-4 text-orange-600" />
                            {item.approvalGate.title}
                          </div>
                          <Badge variant="outline">risk:{item.approvalGate.risk}</Badge>
                        </div>
                        <p className="text-xs text-muted-foreground">{item.approvalGate.detail}</p>
                        <div className="mt-2 rounded border bg-background/70 p-2 text-xs text-muted-foreground">
                          {item.approvalGate.targetSummary || item.prompt}
                        </div>
                        <div className="mt-2 flex flex-wrap items-center gap-2">
                          <Badge variant="outline">{item.approvalGate.status}</Badge>
                          {item.approvalGate.status === 'pending' && (
                            <Button
                              size="sm"
                              className="h-8 px-3"
                              onClick={async () => {
                                updateRun(item.id, (run) => ({
                                  ...run,
                                  status: 'running',
                                  approvalGate: run.approvalGate ? { ...run.approvalGate, status: 'approved' } : run.approvalGate,
                                }))
                                setPhase(item.id, 'plan', 'completed', 'Approval granted')
                                await executeRun(item.id, item.prompt)
                              }}
                            >
                              {ui.approve}
                            </Button>
                          )}
                          {item.approvalGate.status === 'pending' && (
                            <Button
                              size="sm"
                              variant="outline"
                              className="h-8 px-3"
                              onClick={() => {
                                updateRun(item.id, (run) => ({
                                  ...run,
                                  status: 'waiting_approval',
                                  approvalGate: run.approvalGate ? { ...run.approvalGate, status: 'review' } : run.approvalGate,
                                }))
                              }}
                            >
                              {ui.review}
                            </Button>
                          )}
                          {item.approvalGate.status === 'pending' && (
                            <Button
                              size="sm"
                              variant="destructive"
                              className="h-8 px-3"
                              onClick={() => {
                                updateRun(item.id, (run) => ({
                                  ...run,
                                  status: 'failed',
                                  approvalGate: run.approvalGate ? { ...run.approvalGate, status: 'denied' } : run.approvalGate,
                                }))
                                setPhase(item.id, 'plan', 'failed', 'Approval denied')
                                setPhase(item.id, 'execute', 'failed', 'Execution blocked by user decision')
                                setPhase(item.id, 'finalize', 'failed', 'Run terminated by denied approval')
                                appendResult({
                                  content: locale === 'ru' ? 'Запуск остановлен: подтверждение отклонено.' : 'Run stopped: approval was denied.',
                                  summary: 'Terminal outcome: run stopped before execution.',
                                  error: true,
                                })
                              }}
                            >
                              {ui.deny}
                            </Button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </RuntimeCard>
              )
            }

            if (item.kind === 'result') {
              const visibleActions: ResultActionVisibility = {
                copy: item.content.trim().length > 0,
                retry: Boolean(lastPrompt),
                continue: !item.error,
                openCanvas: !item.error,
                openDiff: !item.error && item.content.includes('\n'),
                openArtifact: !item.error && item.content.length > 80,
                showTrace: settings.showTraceShortcut !== false && Boolean(lastAnswer?.diagnostics),
                showContext: Boolean(lastAnswer?.context_preview),
                export: item.content.trim().length > 0,
              }

              return (
                <RuntimeCard
                  key={item.id}
                  variant={item.error ? 'warning' : 'result'}
                  title={item.error ? 'Final outcome: failed' : 'Final outcome: answer ready'}
                  subtitle={item.summary}
                  badge={item.error ? 'failed' : 'completed'}
                  footer={
                    <ResultActionBar
                      onCopy={() => copyResult(item.content)}
                      onRetry={() => {
                        void rerunLastPrompt()
                      }}
                      onContinue={() => {
                        setInput((prev) => (prev.trim() ? `${prev}\nContinue with next step.` : 'Continue with next step.'))
                      }}
                      onOpenCanvas={() =>
                        onOpenCanvasView?.({
                          view: 'plan',
                          title: 'Result Plan',
                          payload: {
                            steps: item.content
                              .split('\n')
                              .map((line) => line.trim())
                              .filter((line) => line.length > 0)
                              .slice(0, 6),
                          },
                          mode: 'canvas',
                        })
                      }
                      onOpenDiff={() =>
                        onOpenCanvasView?.({
                          view: 'diff',
                          title: 'Result Diff Preview',
                          payload: { before: '', after: item.content },
                          mode: 'split',
                        })
                      }
                      onOpenArtifact={() =>
                        onOpenCanvasView?.({
                          view: 'artifact',
                          title: 'Result Artifact',
                          payload: {
                            source: 'assistant_result',
                            content: item.content,
                          },
                          mode: 'split',
                        })
                      }
                      onShowTrace={() =>
                        onOpenCanvasView?.({
                          view: 'document',
                          title: 'Trace Companion',
                          payload: { text: JSON.stringify(lastAnswer?.diagnostics ?? {}, null, 2) },
                          mode: 'split',
                        })
                      }
                      onShowContext={() =>
                        onOpenCanvasView?.({
                          view: 'document',
                          title: 'Context Companion',
                          payload: { text: lastAnswer?.context_preview ?? '' },
                          mode: 'split',
                        })
                      }
                      onExport={() => {
                        const blob = new Blob([item.content], { type: 'text/plain;charset=utf-8' })
                        const href = URL.createObjectURL(blob)
                        const link = document.createElement('a')
                        link.href = href
                        link.download = 'agent-result.txt'
                        link.click()
                        URL.revokeObjectURL(href)
                      }}
                      visibleActions={visibleActions}
                    />
                  }
                >
                  <div className="prose prose-sm max-w-none dark:prose-invert">
                    <ReactMarkdown>{item.content}</ReactMarkdown>
                  </div>
                  {(item.traceSummary || item.contextSummary) && (
                    <div className="flex flex-wrap items-center gap-2 pt-2">
                      {item.traceSummary && <Badge variant="outline">{item.traceSummary}</Badge>}
                      {item.contextSummary && <Badge variant="outline">{item.contextSummary}</Badge>}
                    </div>
                  )}
                </RuntimeCard>
              )
            }

            return null
          })}
        </div>
      </ScrollArea>

      <div className="border-t bg-background/95 p-4 backdrop-blur">
        <div className="mx-auto max-w-4xl">
          {requestError && (
            <div className="mb-2 rounded-md border border-destructive/50 bg-destructive/10 p-2 text-xs text-destructive">
              {ui.requestFailedHint}
            </div>
          )}

          <div className="flex items-end gap-2">
            <Textarea
              ref={textareaRef}
              className="min-h-[40px] max-h-[200px] resize-none"
              rows={1}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault()
                  void handleSend()
                }
              }}
              placeholder={ui.placeholder}
            />

            <Button onClick={() => void handleSend()} disabled={!canSend} className="h-10 shrink-0 px-4">
              <SendHorizontal className="mr-2 h-4 w-4" />
              {isLoading ? ui.working : ui.send}
            </Button>
          </div>

          <div className="mt-2 flex items-center justify-between text-[10px] text-muted-foreground">
            <span>{ui.enterToSend}</span>
            <div className="flex items-center gap-2">
              <span>{ui.shiftEnter}</span>
              <span>{ui.runReady}</span>
              {isLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <CheckCircle2 className="h-3 w-3 text-emerald-600" />}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
