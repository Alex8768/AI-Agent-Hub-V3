import { useEffect, useMemo, useState } from 'react';
import './App.css';
import AppLayout from './components/AppLayout';
import ChatTabs from './components/ChatTabs';
import RightPanel from './components/RightPanel';
import ChatPanel from './components/ChatPanel';
import GraphCanvas from './components/GraphCanvas';
import MetaPanel from './components/MetaPanel';
import { AppProvider, useAppContext } from './context/AppContext';
import { getHealth } from './lib/apiClient';
import {
  readLocalePreference,
  readThemeModePreference,
  resolveLocale,
  resolveThemeMode,
  writeLocalePreference,
  writeThemeModePreference,
  type UiLocale,
  type UiThemeMode,
} from './lib/uiPreferences';

type HealthState = 'checking' | 'healthy' | 'unreachable';

function AppContent() {
  const [healthStatus, setHealthStatus] = useState<HealthState>('checking');
  const [leftVisible, setLeftVisible] = useState(false);
  const [rightVisible, setRightVisible] = useState(false);
  const [workspaceId, setWorkspaceId] = useState('default');
  const [sessionId, setSessionId] = useState('default');
  const [lastUsedSession, setLastUsedSession] = useState('default:default');
  const [themeMode, setThemeMode] = useState<UiThemeMode>(() => readThemeModePreference());
  const [localeMode, setLocaleMode] = useState<UiLocale | 'auto'>(() => readLocalePreference());

  const { lastGraph, lastAnswer } = useAppContext();
  const locale = useMemo(() => resolveLocale(localeMode), [localeMode]);
  const resolvedTheme = useMemo(() => resolveThemeMode(themeMode), [themeMode]);

  const copy = useMemo(() => {
    if (locale === 'ru') {
      return {
        healthy: 'Доступен',
        unreachable: 'Недоступен',
        checking: 'Проверка',
        workspace: 'Рабочая область',
        session: 'Сессия',
        agentWorkspace: 'Контекст агента',
        sessionContext: 'Контекст сессии',
        sidebarText: 'Ограничьте чат, граф и инструменты выбранной рабочей областью и сессией.',
        currentScope: 'Текущий контекст',
        lastChannel: 'Последний активный канал',
        noRequestsYet: 'Запросов пока не было',
        diagnosticsTab: 'Метаданные',
        scopePrefix: 'Контекст',
        appearance: 'Тема',
        language: 'Язык',
        themeSystem: 'Системная',
        themeLight: 'Светлая',
        themeDark: 'Тёмная',
        localeAuto: 'Авто',
        localeRu: 'Русский',
        localeEn: 'English',
      };
    }
    return {
      healthy: 'Healthy',
      unreachable: 'Unreachable',
      checking: 'Checking',
      workspace: 'Workspace',
      session: 'Session',
      agentWorkspace: 'Agent Workspace',
      sessionContext: 'Session Context',
      sidebarText: 'Scope the chat, graph and tool activity to a specific workspace/session pair.',
      currentScope: 'Current Scope',
      lastChannel: 'Last Active Channel',
      noRequestsYet: 'No requests yet',
      diagnosticsTab: 'Meta',
      scopePrefix: 'Scope',
      appearance: 'Theme',
      language: 'Language',
      themeSystem: 'System',
      themeLight: 'Light',
      themeDark: 'Dark',
      localeAuto: 'Auto',
      localeRu: 'Русский',
      localeEn: 'English',
    };
  }, [locale]);

  useEffect(() => {
    getHealth()
      .then(() => setHealthStatus('healthy'))
      .catch(() => setHealthStatus('unreachable'));
  }, []);

  useEffect(() => {
    if (typeof document === 'undefined') return;
    const root = document.documentElement;
    root.setAttribute('data-theme', resolvedTheme);
    root.setAttribute('data-locale', locale);
  }, [resolvedTheme, locale]);

  useEffect(() => {
    writeThemeModePreference(themeMode);
  }, [themeMode]);

  useEffect(() => {
    writeLocalePreference(localeMode);
  }, [localeMode]);

  const onSessionUsed = (ws: string, sid: string) => {
    const normalizedWorkspace = ws.trim() || 'default';
    const normalizedSession = sid.trim() || 'default';
    setLastUsedSession(`${normalizedWorkspace}:${normalizedSession}`);
  };

  const healthLabel = useMemo(() => {
    if (healthStatus === 'healthy') return copy.healthy;
    if (healthStatus === 'unreachable') return copy.unreachable;
    return copy.checking;
  }, [copy.checking, copy.healthy, copy.unreachable, healthStatus]);

  const leftPanel = (
    <div className="panel-body shell-sidebar">
      <div className="sidebar-section">
        <div className="sidebar-eyebrow">{copy.agentWorkspace}</div>
        <h2 className="sidebar-title">{copy.sessionContext}</h2>
        <p className="sidebar-copy">
          {copy.sidebarText}
        </p>
      </div>

      <div className="sidebar-section">
        <label className="field-label" htmlFor="workspace-input">
          {copy.workspace}
        </label>
        <input
          id="workspace-input"
          className="field-input"
          value={workspaceId}
          onChange={(e) => setWorkspaceId(e.target.value)}
          placeholder="default"
        />

        <label className="field-label" htmlFor="session-input">
          {copy.session}
        </label>
        <input
          id="session-input"
          className="field-input"
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          placeholder="default"
        />
      </div>

      <div className="sidebar-section sidebar-info-card">
        <div className="section-title">{copy.currentScope}</div>
        <div className="scope-grid">
          <div className="scope-item">
            <span className="scope-key">{copy.workspace}</span>
            <strong>{workspaceId.trim() || 'default'}</strong>
          </div>
          <div className="scope-item">
            <span className="scope-key">{copy.session}</span>
            <strong>{sessionId.trim() || 'default'}</strong>
          </div>
        </div>
      </div>

      <div className="sidebar-section sidebar-info-card">
        <div className="section-title">{copy.lastChannel}</div>
        <div className="sidebar-copy sidebar-copy-tight">{lastUsedSession || copy.noRequestsYet}</div>
      </div>
    </div>
  );

  return (
    <div className="app-root">
      <main className="app-content">
        <AppLayout
          leftVisible={leftVisible}
          rightVisible={rightVisible}
          onToggleLeft={() => setLeftVisible((v) => !v)}
          onToggleRight={() => setRightVisible((v) => !v)}
          leftPanel={leftPanel}
          centerPanel={
            <ChatTabs
              chatContent={
                <ChatPanel
                  workspaceId={workspaceId}
                  sessionId={sessionId}
                  onSessionUsed={onSessionUsed}
                  locale={locale}
                />
              }
              canvasContent={<GraphCanvas nodes={lastGraph?.nodes} edges={lastGraph?.edges} />}
              metaContent={<MetaPanel diagnostics={lastAnswer?.diagnostics || null} />}
            />
          }
          rightPanel={<RightPanel workspaceId={workspaceId} />}
        />
      </main>

      <footer className="status-bar">
        <div className="status-section">
          <div className="status-indicator">
            {copy.scopePrefix}: {(workspaceId.trim() || 'default')} / {(sessionId.trim() || 'default')}
          </div>
        </div>

        <div className="status-section">
          <label className="status-select">
            {copy.appearance}
            <select
              value={themeMode}
              onChange={(e) => setThemeMode((e.target.value as UiThemeMode) || 'system')}
            >
              <option value="system">{copy.themeSystem}</option>
              <option value="light">{copy.themeLight}</option>
              <option value="dark">{copy.themeDark}</option>
            </select>
          </label>
          <label className="status-select">
            {copy.language}
            <select
              value={localeMode}
              onChange={(e) => setLocaleMode((e.target.value as UiLocale | 'auto') || 'auto')}
            >
              <option value="auto">{copy.localeAuto}</option>
              <option value="ru">{copy.localeRu}</option>
              <option value="en">{copy.localeEn}</option>
            </select>
          </label>
          <div className={`status-indicator ${healthStatus}`}>
            ● {healthLabel}
          </div>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}
