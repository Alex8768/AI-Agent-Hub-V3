import { useEffect, useMemo, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './ChatPanel.css';
import { sendMessage } from '../lib/apiClient';
import { useAppContext } from '../context/AppContext';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  thoughts?: string;
  runtimeInfo?: RuntimeInfo;
  error?: boolean;
}

interface RuntimeInfo {
  requestedMode: string;
  selectedMode: string;
  actStatus: string;
  diagnosticsMode: string;
  reasonCodes: string[];
  toolName: string;
  confirmationToken: string;
  canConfirmWrite: boolean;
}

interface GraphNodeLike {
  id?: string;
  name?: string;
  type?: string;
}

interface GraphEdgeLike {
  id?: string;
  src_id?: string;
  dst_id?: string;
  source?: string;
  target?: string;
  rel_type?: string;
}

interface GraphDataLike {
  nodes: GraphNodeLike[];
  edges: GraphEdgeLike[];
}

interface ChatPanelProps {
  workspaceId: string;
  sessionId: string;
  onSessionUsed: (ws: string, sid: string) => void;
  locale?: 'en' | 'ru';
}

function makeMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export default function ChatPanel({ workspaceId, sessionId, onSessionUsed, locale = 'en' }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [diagnosticsView, setDiagnosticsView] = useState<'compact' | 'full'>(() => {
    if (typeof window === 'undefined') return 'compact';
    return localStorage.getItem('chat.diagnosticsView') === 'full' ? 'full' : 'compact';
  });
  const [isLoading, setIsLoading] = useState(false);
  const [requestError, setRequestError] = useState<string>('');
  const { setLastAnswer, setLastGraph } = useAppContext();

  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const readThoughts = (value: unknown): string | undefined => {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return undefined;
    const thoughts = (value as Record<string, unknown>).thoughts;
    return typeof thoughts === 'string' && thoughts.trim().length > 0 ? thoughts : undefined;
  };

  const readGraph = (value: unknown): GraphDataLike | null => {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
    const row = value as Record<string, unknown>;

    const nodes = Array.isArray(row.nodes)
      ? row.nodes.map((node) => {
          const item =
            node && typeof node === 'object' && !Array.isArray(node)
              ? (node as Record<string, unknown>)
              : {};
          return {
            id: item.id !== undefined ? String(item.id) : undefined,
            name: item.name !== undefined ? String(item.name) : undefined,
            type: item.type !== undefined ? String(item.type) : undefined,
          };
        })
      : [];

    const edges = Array.isArray(row.edges)
      ? row.edges.map((edge) => {
          const item =
            edge && typeof edge === 'object' && !Array.isArray(edge)
              ? (edge as Record<string, unknown>)
              : {};
          return {
            id: item.id !== undefined ? String(item.id) : undefined,
            src_id: item.src_id !== undefined ? String(item.src_id) : undefined,
            dst_id: item.dst_id !== undefined ? String(item.dst_id) : undefined,
            source: item.source !== undefined ? String(item.source) : undefined,
            target: item.target !== undefined ? String(item.target) : undefined,
            rel_type: item.rel_type !== undefined ? String(item.rel_type) : undefined,
          };
        })
      : [];

    if (nodes.length === 0 && edges.length === 0) return null;
    return { nodes, edges };
  };

  const readReasonCodes = (value: unknown): string[] => {
    if (!Array.isArray(value)) return [];
    return value.map((item) => String(item)).filter((item) => item.trim().length > 0);
  };

  const readRuntimeInfo = (diagnostics: unknown): RuntimeInfo | undefined => {
    if (!diagnostics || typeof diagnostics !== 'object' || Array.isArray(diagnostics)) return undefined;
    const row = diagnostics as Record<string, unknown>;
    const runtimeMode =
      row.runtime_mode && typeof row.runtime_mode === 'object' && !Array.isArray(row.runtime_mode)
        ? (row.runtime_mode as Record<string, unknown>)
        : {};
    const actRuntime =
      row.act_runtime && typeof row.act_runtime === 'object' && !Array.isArray(row.act_runtime)
        ? (row.act_runtime as Record<string, unknown>)
        : {};
    const confirmation =
      actRuntime.confirmation && typeof actRuntime.confirmation === 'object' && !Array.isArray(actRuntime.confirmation)
        ? (actRuntime.confirmation as Record<string, unknown>)
        : {};
    const presentation =
      row.presentation && typeof row.presentation === 'object' && !Array.isArray(row.presentation)
        ? (row.presentation as Record<string, unknown>)
        : {};
    const reasonCodes = Array.from(
      new Set([
        ...readReasonCodes(runtimeMode.reason_codes),
        ...readReasonCodes(actRuntime.reason_codes),
        ...readReasonCodes(presentation.reason_codes),
        ...readReasonCodes(row.warnings),
      ]),
    );
    const requestedMode = String(runtimeMode.requested_mode ?? 'answer');
    const selectedMode = String(runtimeMode.selected_mode ?? requestedMode);
    const actStatus = String(actRuntime.status ?? 'n/a');
    const diagnosticsMode = String(presentation.mode ?? 'full');
    const toolName = String(actRuntime.tool_name ?? '');
    const confirmationToken = String(confirmation.token ?? '');
    const canConfirmWrite = actStatus === 'pending_confirmation' && toolName.length > 0 && confirmationToken.length > 0;
    const hasSignals =
      reasonCodes.length > 0 ||
      requestedMode !== 'answer' ||
      selectedMode !== 'answer' ||
      actStatus !== 'n/a' ||
      diagnosticsMode !== 'full';
    if (!hasSignals) return undefined;
    return { requestedMode, selectedMode, actStatus, diagnosticsMode, reasonCodes, toolName, confirmationToken, canConfirmWrite };
  };

  useEffect(() => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('chat.diagnosticsView', diagnosticsView);
    }
  }, [diagnosticsView]);

  useEffect(() => {
    if (!scrollRef.current) return;
    scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, isLoading]);

  useEffect(() => {
    if (!textareaRef.current) return;
    textareaRef.current.style.height = '0px';
    textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 220)}px`;
  }, [input]);

  const canSend = useMemo(() => input.trim().length > 0 && !isLoading, [input, isLoading]);
  const ui = useMemo(
    () =>
      locale === 'ru'
        ? {
            emptyTitle: 'Готов к следующему запросу',
            emptyText:
              'Спрашивайте по документам, запускайте задачи с инструментами, анализируйте граф и работайте в контексте выбранной области и сессии.',
            hintWorkspace: 'Контекст области',
            hintGraph: 'Готов к графу',
            hintTools: 'Инструменты включены',
            you: 'Вы',
            agent: 'Агент',
            error: 'Ошибка',
            reasoning: 'Ход рассуждений',
            mode: 'Режим',
            requested: 'Запрошено',
            action: 'Действие',
            diag: 'Диаг',
            approveWrite: 'Подтвердить запись',
            cancel: 'Отмена',
            requestFailed: 'Запрос завершился ошибкой.',
            approvalFailed: 'Подтверждение завершилось ошибкой.',
            requestFailedHint: 'Последний запрос завершился ошибкой. Проверьте backend/API и попробуйте снова.',
            diagnostics: 'Диагностика',
            compact: 'компактный',
            expanded: 'расширенный',
            placeholder: 'Напишите агенту…',
            send: 'Отправить',
            working: 'Выполняю…',
            enterToSend: 'Enter - отправить',
            shiftEnter: 'Shift + Enter - новая строка',
          }
        : {
            emptyTitle: 'Ready for the next query',
            emptyText:
              'Ask about documents, run tool-assisted tasks, inspect graph context, or work inside a specific workspace and session.',
            hintWorkspace: 'Workspace-aware',
            hintGraph: 'Graph-ready',
            hintTools: 'Tool-capable',
            you: 'You',
            agent: 'Agent',
            error: 'Error',
            reasoning: 'Reasoning notes',
            mode: 'Mode',
            requested: 'Requested',
            action: 'Act',
            diag: 'Diag',
            approveWrite: 'Approve Write',
            cancel: 'Cancel',
            requestFailed: 'Request failed.',
            approvalFailed: 'Approval request failed.',
            requestFailedHint: 'Last request failed. Check backend/API availability and try again.',
            diagnostics: 'Diagnostics',
            compact: 'compact',
            expanded: 'expanded',
            placeholder: 'Message the agent…',
            send: 'Send',
            working: 'Working…',
            enterToSend: 'Enter to send',
            shiftEnter: 'Shift + Enter for newline',
          },
    [locale],
  );

  const handleSend = async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    const userMsg: Message = {
      id: makeMessageId(),
      role: 'user',
      content: trimmed,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsLoading(true);
    setRequestError('');
    onSessionUsed(workspaceId, sessionId);

    try {
      const response = await sendMessage(workspaceId, sessionId, trimmed, diagnosticsView);

      const assistantMsg: Message = {
        id: makeMessageId(),
        role: 'assistant',
        content: response.answer,
        thoughts: readThoughts(response.diagnostics),
        runtimeInfo: readRuntimeInfo(response.diagnostics),
      };

      setMessages((prev) => [...prev, assistantMsg]);
      setLastAnswer(response);

      const graph = readGraph(
        response.diagnostics && typeof response.diagnostics === 'object'
          ? (response.diagnostics as Record<string, unknown>).graph
          : null,
      );

      if (graph) {
        setLastGraph(graph);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setRequestError(message);
      setMessages((prev) => [
        ...prev,
        {
          id: makeMessageId(),
          role: 'assistant',
          content: `${ui.requestFailed}\n\n${message}`,
          error: true,
        },
      ]);
      console.error('Failed to send message:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleWriteApproval = async (msg: Message, decision: 'approve' | 'cancel') => {
    if (isLoading || !msg.runtimeInfo?.canConfirmWrite) return;
    setIsLoading(true);
    setRequestError('');
    try {
      const response = await sendMessage(
        workspaceId,
        sessionId,
        decision === 'approve' ? 'Approve write action' : 'Cancel write action',
        diagnosticsView,
        {
          runtime_mode: 'act',
          act_tool_name: msg.runtimeInfo.toolName,
          act_confirm_decision: decision,
          act_confirmation_token: msg.runtimeInfo.confirmationToken,
          act_idempotency_key: decision === 'approve' ? `ui-approve:${msg.id}` : '',
        },
      );
      const assistantMsg: Message = {
        id: makeMessageId(),
        role: 'assistant',
        content: response.answer,
        thoughts: readThoughts(response.diagnostics),
        runtimeInfo: readRuntimeInfo(response.diagnostics),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setLastAnswer(response);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      setRequestError(message);
      setMessages((prev) => [
        ...prev,
        {
          id: makeMessageId(),
          role: 'assistant',
          content: `${ui.approvalFailed}\n\n${message}`,
          error: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="messages-list" ref={scrollRef}>
        {messages.length === 0 && !isLoading && (
          <div className="chat-empty-state">
            <div className="chat-empty-badge">Agent Console</div>
            <h2>{ui.emptyTitle}</h2>
            <p>
              {ui.emptyText}
            </p>
            <div className="chat-empty-hints">
              <span>{ui.hintWorkspace}</span>
              <span>{ui.hintGraph}</span>
              <span>{ui.hintTools}</span>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`message-row ${msg.role} ${msg.error ? 'is-error' : ''}`}
          >
            <div className="message-avatar">
              {msg.role === 'user' ? ui.you : 'AI'}
            </div>

            <div className="message-card">
              <div className="message-header">
                <span className="message-role">{msg.role === 'user' ? ui.you : ui.agent}</span>
                {msg.error && <span className="message-state">{ui.error}</span>}
              </div>

              {msg.thoughts && (
                <details className="agent-thoughts">
                  <summary>{ui.reasoning}</summary>
                  <div className="agent-thoughts-body">{msg.thoughts}</div>
                </details>
              )}

              {msg.runtimeInfo && (
                <div className="runtime-info-card">
                  <div className="runtime-info-row">
                    <span className="runtime-info-pill">
                      {ui.mode}: {msg.runtimeInfo.selectedMode}
                    </span>
                    {msg.runtimeInfo.requestedMode !== msg.runtimeInfo.selectedMode && (
                      <span className="runtime-info-pill is-warn">
                        {ui.requested}: {msg.runtimeInfo.requestedMode}
                      </span>
                    )}
                    {msg.runtimeInfo.actStatus !== 'n/a' && (
                      <span className="runtime-info-pill">
                        {ui.action}: {msg.runtimeInfo.actStatus}
                      </span>
                    )}
                    <span className="runtime-info-pill">
                      {ui.diag}: {msg.runtimeInfo.diagnosticsMode}
                    </span>
                  </div>
                  {msg.runtimeInfo.reasonCodes.length > 0 && (
                    <div className="runtime-reasons">
                      {msg.runtimeInfo.reasonCodes.map((code) => (
                        <code key={`${msg.id}-${code}`}>{code}</code>
                      ))}
                    </div>
                  )}
                  {msg.runtimeInfo.canConfirmWrite && (
                    <div className="runtime-approval-actions">
                      <button
                        className="runtime-approval-btn is-approve"
                        type="button"
                        onClick={() => void handleWriteApproval(msg, 'approve')}
                        disabled={isLoading}
                      >
                        {ui.approveWrite}
                      </button>
                      <button
                        className="runtime-approval-btn is-cancel"
                        type="button"
                        onClick={() => void handleWriteApproval(msg, 'cancel')}
                        disabled={isLoading}
                      >
                        {ui.cancel}
                      </button>
                    </div>
                  )}
                </div>
              )}

              <div className="message-content">
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message-row assistant">
            <div className="message-avatar">AI</div>
            <div className="message-card is-loading">
              <div className="message-header">
                <span className="message-role">{ui.agent}</span>
              </div>
              <div className="message-loading">
                <span className="loading-dot" />
                <span className="loading-dot" />
                <span className="loading-dot" />
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="chat-input-area">
        {requestError && (
          <div className="chat-request-error">
            {ui.requestFailedHint}
          </div>
        )}

        <div className="input-shell">
          <div className="input-context-row">
            <span className="input-context-pill">Workspace: {workspaceId || 'default'}</span>
            <span className="input-context-pill">Session: {sessionId || 'default'}</span>
            <label className="input-context-select">
              {ui.diagnostics}:
              <select
                value={diagnosticsView}
                onChange={(e) => setDiagnosticsView(e.target.value === 'full' ? 'full' : 'compact')}
              >
                <option value="compact">{ui.compact}</option>
                <option value="full">{ui.expanded}</option>
              </select>
            </label>
          </div>

          <div className="input-wrapper">
            <textarea
              ref={textareaRef}
              className="chat-input"
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  void handleSend();
                }
              }}
              placeholder={ui.placeholder}
            />
            <button
              className="send-btn"
              onClick={() => void handleSend()}
              disabled={!canSend}
              type="button"
            >
              {isLoading ? ui.working : ui.send}
            </button>
          </div>

          <div className="input-footer">
            <span>{ui.enterToSend}</span>
            <span>{ui.shiftEnter}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
