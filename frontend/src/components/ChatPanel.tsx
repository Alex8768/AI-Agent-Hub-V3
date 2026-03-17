import { useEffect, useMemo, useRef, useState } from 'react'
import { CheckCircle2, Loader2, SendHorizontal, ShieldAlert } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import ResultActionBar from './chat-runtime/ResultActionBar'
import type { ApprovalItem, ChatTimelineItem, RuntimeEventType } from './chat-runtime/types'
import type { CanvasViewType } from './canvas/canvasState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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

function makeMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function isApprovalRequired(prompt: string): boolean {
  const sensitiveTerms = ['delete', 'overwrite', 'remove', 'rm ', 'drop ', 'truncate', 'write file', 'dangerous']
  const lower = prompt.toLowerCase()
  return sensitiveTerms.some((term) => lower.includes(term))
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
      emptyText: locale === 'ru'
        ? 'Спросите о документах, задачах или просто начните диалог.'
        : 'Ask about documents, tasks, or start a conversation.',
      you: locale === 'ru' ? 'Вы' : 'You',
      agent: locale === 'ru' ? 'Ассистент' : 'Assistant',
      error: locale === 'ru' ? 'Ошибка' : 'Error',
      requestFailedHint: locale === 'ru'
        ? 'Не удалось получить ответ. Проверьте подключение и попробуйте снова.'
        : 'Failed to get response. Check connection and try again.',
      placeholder: locale === 'ru' ? 'Напишите сообщение...' : 'Type a message...',
      send: locale === 'ru' ? 'Отправить' : 'Send',
      working: locale === 'ru' ? 'Выполняю шаги...' : 'Running steps...',
      runReady: locale === 'ru' ? 'Runtime stream active' : 'Runtime stream active',
      enterToSend: locale === 'ru' ? 'Enter - отправить' : 'Enter to send',
      shiftEnter: locale === 'ru' ? 'Shift+Enter - новая строка' : 'Shift+Enter for new line',
      approve: locale === 'ru' ? 'Approve' : 'Approve',
      deny: locale === 'ru' ? 'Deny' : 'Deny',
      review: locale === 'ru' ? 'Review' : 'Review',
    }),
    [locale]
  )

  const appendEvent = (type: RuntimeEventType, title: string, detail?: string) => {
    setTimeline((prev) => [
      ...prev,
      {
        id: makeMessageId(),
        kind: 'execution_event',
        event: {
          id: makeMessageId(),
          type,
          title,
          detail,
          timestamp: Date.now(),
        },
      },
    ])
  }

  const updateApproval = (id: string, status: ApprovalItem['status']) => {
    setTimeline((prev) =>
      prev.map((item) => {
        if (item.kind !== 'approval' || item.id !== id) return item
        return { ...item, status }
      }),
    )
  }

  const executePrompt = async (prompt: string) => {
    if (!prompt.trim()) return

    setIsLoading(true)
    setRequestError('')
    setLastPrompt(prompt)
    onSessionUsed(workspaceId, sessionId)

    appendEvent('run_started', 'Run started', 'Execution runtime initialized.')
    setTimeline((prev) => [
      ...prev,
      {
        id: makeMessageId(),
        kind: 'plan',
        steps: [
          'Analyze user request and constraints',
          'Execute relevant backend call',
          'Assemble final response and diagnostics',
        ],
      },
    ])
    appendEvent('plan_created', 'Plan created')
    appendEvent('step_started', 'Step 1/1: Execute answer pipeline')

    if (settings.showReasoning) {
      setTimeline((prev) => [
        ...prev,
        {
          id: makeMessageId(),
          kind: 'reasoning_summary',
          summary:
            locale === 'ru'
              ? 'Построена краткая стратегия ответа: проверка запроса, вызов backend, финальная сводка.'
              : 'Prepared a concise response strategy: validate request, call backend, produce final summary.',
        },
      ])
      appendEvent('reasoning_summary', 'Reasoning summary available')
    }

    try {
      const response = await sendMessage(workspaceId, sessionId, prompt, {
        api_provider: settings.apiProvider,
        model: settings.selectedModel,
        reasoning_mode: settings.reasoningMode,
        force_search: settings.forceSearch,
      })

      appendEvent('step_completed', 'Step completed', 'Answer pipeline returned successfully.')
      appendEvent('final_response', 'Final response produced')
      setTimeline((prev) => [
        ...prev,
        {
          id: makeMessageId(),
          kind: 'result',
          content: response.answer || '(no response)',
        },
      ])
      appendEvent('run_completed', 'Run completed')
      setLastAnswer(response)
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      setRequestError(message)
      appendEvent('warning', 'Execution warning', message)
      appendEvent('run_failed', 'Run failed')
      setTimeline((prev) => [
        ...prev,
        {
          id: makeMessageId(),
          kind: 'result',
          content: `**${ui.error}:**\n\n${message}`,
          error: true,
        },
      ])
      console.error('Failed to execute runtime prompt:', err)
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

    if (isApprovalRequired(prompt)) {
      const approvalId = makeMessageId()
      setTimeline((prev) => [
        ...prev,
        {
          id: approvalId,
          kind: 'approval',
          title: locale === 'ru' ? 'Требуется подтверждение' : 'Approval required',
          detail:
            locale === 'ru'
              ? 'Запрос может менять данные или файлы. Подтвердите действие.'
              : 'This request may modify data or files. Confirm before execution.',
          prompt,
          status: 'pending',
        },
      ])
      appendEvent('approval_required', 'Approval required', 'Pending user decision in chat stream.')
      return
    }

    await executePrompt(prompt)
  }

  const copyResult = async (content: string) => {
    if (!content.trim()) return
    await navigator.clipboard.writeText(content)
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <ScrollArea className="min-h-0 flex-1" ref={scrollRef}>
        <div className="mx-auto flex w-full max-w-4xl flex-col gap-4 px-4 py-4">
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

            if (item.kind === 'plan') {
              return (
                <Card key={item.id} className="border-primary/20 bg-primary/5">
                  <CardContent className="p-4 text-sm">
                    <div className="mb-2 font-medium">Execution plan</div>
                    <ol className="list-decimal space-y-1 pl-4">
                      {item.steps.map((step) => (
                        <li key={step}>{step}</li>
                      ))}
                    </ol>
                  </CardContent>
                </Card>
              )
            }

            if (item.kind === 'reasoning_summary') {
              return (
                <Card key={item.id} className="border-amber-300/50 bg-amber-50/40 dark:bg-amber-900/10">
                  <CardContent className="p-4 text-sm">
                    <div className="mb-1 font-medium">Reasoning summary</div>
                    <p className="text-muted-foreground">{item.summary}</p>
                  </CardContent>
                </Card>
              )
            }

            if (item.kind === 'execution_event') {
              if (settings.showExecutionEvents === false) return null
              return (
                <Card key={item.id}>
                  <CardContent className="flex items-start justify-between gap-3 p-3">
                    <div>
                      <div className="text-sm font-medium">{item.event.title}</div>
                      {item.event.detail && <p className="text-xs text-muted-foreground">{item.event.detail}</p>}
                    </div>
                    <Badge variant="outline" className="text-[10px]">
                      {item.event.type}
                    </Badge>
                  </CardContent>
                </Card>
              )
            }

            if (item.kind === 'approval') {
              return (
                <Card key={item.id} className="border-orange-300/60">
                  <CardContent className="space-y-3 p-4">
                    <div>
                      <div className="flex items-center gap-2 text-sm font-medium">
                        <ShieldAlert className="h-4 w-4 text-orange-600" />
                        {item.title}
                      </div>
                      <p className="mt-1 text-xs text-muted-foreground">{item.detail}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline">{item.status}</Badge>
                      {item.status === 'pending' && (
                        <Button
                          size="sm"
                          onClick={async () => {
                            updateApproval(item.id, 'approved')
                            appendEvent('approval_resolved', 'Approval resolved', 'User approved execution.')
                            await executePrompt(item.prompt)
                          }}
                        >
                          {ui.approve}
                        </Button>
                      )}
                      {item.status === 'pending' && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            updateApproval(item.id, 'review')
                            appendEvent(
                              'approval_resolved',
                              'Approval moved to review',
                              'User selected review before execution.',
                            )
                          }}
                        >
                          {ui.review}
                        </Button>
                      )}
                      {item.status === 'pending' && (
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => {
                            updateApproval(item.id, 'denied')
                            appendEvent('approval_resolved', 'Approval denied', 'Execution was denied by user.')
                          }}
                        >
                          {ui.deny}
                        </Button>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )
            }

            if (item.kind === 'assistant_message' || item.kind === 'result') {
              return (
                <Card key={item.id} className={item.kind === 'result' && item.error ? 'border-destructive' : ''}>
                  <CardContent className="p-4">
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                      <ReactMarkdown>{item.content}</ReactMarkdown>
                    </div>
                    {item.kind === 'result' && (
                      <ResultActionBar
                        onCopy={() => copyResult(item.content)}
                        onRetry={() => {
                          if (lastPrompt) {
                            void executePrompt(lastPrompt)
                          }
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
                            title: 'Trace Preview',
                            payload: { text: JSON.stringify(lastAnswer?.diagnostics ?? {}, null, 2) },
                            mode: 'split',
                          })
                        }
                        showTraceAction={settings.showTraceShortcut !== false}
                        onShowContext={() =>
                          onOpenCanvasView?.({
                            view: 'document',
                            title: 'Context Preview',
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
                      />
                    )}
                  </CardContent>
                </Card>
              )
            }

            return null
          })}

          {isLoading && (
            <Card>
              <CardContent className="flex items-center gap-2 p-4 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>{ui.working}</span>
              </CardContent>
            </Card>
          )}
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
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSend()
                }
              }}
              placeholder={ui.placeholder}
            />

            <Button
              onClick={handleSend}
              disabled={!canSend}
              className="h-10 shrink-0 px-4"
            >
              <SendHorizontal className="mr-2 h-4 w-4" />
              {isLoading ? ui.working : ui.send}
            </Button>
          </div>

          <div className="mt-2 flex items-center justify-between text-[10px] text-muted-foreground">
            <span>{ui.enterToSend}</span>
            <div className="flex items-center gap-2">
              <span>{ui.shiftEnter}</span>
              <span>{ui.runReady}</span>
              {isLoading ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <CheckCircle2 className="h-3 w-3 text-emerald-600" />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
