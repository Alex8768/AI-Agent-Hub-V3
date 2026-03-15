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
  reasonCodes: string[];
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
}

function makeMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export default function ChatPanel({ workspaceId, sessionId, onSessionUsed }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
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
    const reasonCodes = Array.from(
      new Set([
        ...readReasonCodes(runtimeMode.reason_codes),
        ...readReasonCodes(actRuntime.reason_codes),
        ...readReasonCodes(row.warnings),
      ]),
    );
    const requestedMode = String(runtimeMode.requested_mode ?? 'answer');
    const selectedMode = String(runtimeMode.selected_mode ?? requestedMode);
    const actStatus = String(actRuntime.status ?? 'n/a');
    const hasSignals =
      reasonCodes.length > 0 ||
      requestedMode !== 'answer' ||
      selectedMode !== 'answer' ||
      actStatus !== 'n/a';
    if (!hasSignals) return undefined;
    return { requestedMode, selectedMode, actStatus, reasonCodes };
  };

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
      const response = await sendMessage(workspaceId, sessionId, trimmed);

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
          content: `Request failed.\n\n${message}`,
          error: true,
        },
      ]);
      console.error('Failed to send message:', err);
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
            <h2>Ready for the next query</h2>
            <p>
              Ask about documents, run tool-assisted tasks, inspect graph context, or work inside a
              specific workspace and session.
            </p>
            <div className="chat-empty-hints">
              <span>Workspace-aware</span>
              <span>Graph-ready</span>
              <span>Tool-capable</span>
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`message-row ${msg.role} ${msg.error ? 'is-error' : ''}`}
          >
            <div className="message-avatar">
              {msg.role === 'user' ? 'You' : 'AI'}
            </div>

            <div className="message-card">
              <div className="message-header">
                <span className="message-role">{msg.role === 'user' ? 'You' : 'Agent'}</span>
                {msg.error && <span className="message-state">Error</span>}
              </div>

              {msg.thoughts && (
                <details className="agent-thoughts">
                  <summary>Reasoning notes</summary>
                  <div className="agent-thoughts-body">{msg.thoughts}</div>
                </details>
              )}

              {msg.runtimeInfo && (
                <div className="runtime-info-card">
                  <div className="runtime-info-row">
                    <span className="runtime-info-pill">
                      Mode: {msg.runtimeInfo.selectedMode}
                    </span>
                    {msg.runtimeInfo.requestedMode !== msg.runtimeInfo.selectedMode && (
                      <span className="runtime-info-pill is-warn">
                        Requested: {msg.runtimeInfo.requestedMode}
                      </span>
                    )}
                    {msg.runtimeInfo.actStatus !== 'n/a' && (
                      <span className="runtime-info-pill">
                        Act: {msg.runtimeInfo.actStatus}
                      </span>
                    )}
                  </div>
                  {msg.runtimeInfo.reasonCodes.length > 0 && (
                    <div className="runtime-reasons">
                      {msg.runtimeInfo.reasonCodes.map((code) => (
                        <code key={`${msg.id}-${code}`}>{code}</code>
                      ))}
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
                <span className="message-role">Agent</span>
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
            Last request failed. Check backend/API availability and try again.
          </div>
        )}

        <div className="input-shell">
          <div className="input-context-row">
            <span className="input-context-pill">Workspace: {workspaceId || 'default'}</span>
            <span className="input-context-pill">Session: {sessionId || 'default'}</span>
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
              placeholder="Message the agent…"
            />
            <button
              className="send-btn"
              onClick={() => void handleSend()}
              disabled={!canSend}
              type="button"
            >
              {isLoading ? 'Working…' : 'Send'}
            </button>
          </div>

          <div className="input-footer">
            <span>Enter to send</span>
            <span>Shift + Enter for newline</span>
          </div>
        </div>
      </div>
    </div>
  );
}
