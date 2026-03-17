import { useEffect, useMemo, useState } from 'react'
import AppLayout from './components/AppLayout'
import RightPanel from './components/RightPanel'
import ChatPanel from './components/ChatPanel'
import { AppProvider } from './context/AppContext'
import { useAppContext } from './context/useAppContext'
import { getHealth } from './lib/apiClient'
import { ThemeProvider } from '@/components/theme-provider'
import { readLocalePreference, resolveLocale, type UiLocale } from './lib/uiPreferences'
import GlobalModalHost from './components/shell/GlobalModalHost'
import LeftSidebar from './components/shell/LeftSidebar'
import MainWorkspace from './components/shell/MainWorkspace'
import RightSidebar from './components/shell/RightSidebar'
import TopBar from './components/shell/TopBar'
import ChatsSection from './components/left-sidebar/ChatsSection'
import ProjectsSection from './components/left-sidebar/ProjectsSection'
import SavedSection from './components/left-sidebar/SavedSection'
import ViewsSection from './components/left-sidebar/ViewsSection'
import CanvasHost from './components/canvas/CanvasHost'
import type { CanvasViewType } from './components/canvas/canvasState'
import { DEFAULT_APP_SETTINGS, toLegacyAgentSettings, type AppSettingsState } from './components/settings/settingsTypes'
import {
  readLayoutState,
  writeLayoutState,
  type AppMode,
  type LeftSidebarSection,
  type RightSidebarTab,
  type ShellLayoutState,
} from './components/shell/layoutState'

type HealthState = 'checking' | 'healthy' | 'unreachable'

function AppContent() {
  const [healthStatus, setHealthStatus] = useState<HealthState>('checking')
  const [layoutState, setLayoutState] = useState<ShellLayoutState>(() => readLayoutState())
  const [workspaceId] = useState('default')
  const [sessionId] = useState('default')
  const [lastUsedSession, setLastUsedSession] = useState('default:default')
  const [localeMode] = useState<UiLocale | 'auto'>(() => readLocalePreference())
  const [settings, setSettings] = useState<AppSettingsState>(DEFAULT_APP_SETTINGS)

  const { lastGraph } = useAppContext()
  const legacySettings = useMemo(() => toLegacyAgentSettings(settings), [settings])
  const locale = useMemo(() => resolveLocale(localeMode), [localeMode])

  useEffect(() => {
    getHealth()
      .then(() => setHealthStatus('healthy'))
      .catch(() => setHealthStatus('unreachable'))
  }, [])

  useEffect(() => {
    document.documentElement.lang = locale
  }, [locale])

  useEffect(() => {
    writeLayoutState(layoutState)
  }, [layoutState])

  const onSessionUsed = (ws: string, sid: string) => {
    setLastUsedSession(`${ws.trim() || 'default'}:${sid.trim() || 'default'}`)
  }

  const updateLayout = (next: Partial<ShellLayoutState>) => {
    setLayoutState((prev) => ({
      ...prev,
      ...next,
    }))
  }

  const setAppMode = (appMode: AppMode) => {
    const nextCanvas =
      appMode === 'canvas' && layoutState.canvas.activeView === 'empty'
        ? {
            activeView: 'graph' as CanvasViewType,
            title: 'Graph View',
            payload: { nodes: lastGraph?.nodes ?? [], edges: lastGraph?.edges ?? [] },
          }
        : layoutState.canvas

    updateLayout({
      appMode,
      canvasVisible: appMode === 'split' || appMode === 'canvas',
      canvas: nextCanvas,
    })
  }

  const setLeftSidebarSection = (leftSidebarSection: LeftSidebarSection) => {
    updateLayout({ leftSidebarSection })
  }

  const setRightSidebarTab = (rightSidebarTab: RightSidebarTab) => {
    updateLayout({ rightSidebarTab })
  }

  const openCanvasView = (request: {
    view: CanvasViewType
    title?: string
    payload?: unknown
    mode?: 'canvas' | 'split'
  }) => {
    const nextMode: AppMode = request.mode === 'split' ? 'split' : 'canvas'
    updateLayout({
      appMode: nextMode,
      canvasVisible: true,
      canvas: {
        activeView: request.view,
        title: request.title,
        payload: request.payload,
      },
    })
  }

  return (
    <div className="flex h-screen flex-col bg-background">
      <TopBar
        title="AI Agent Hub"
        workspaceId={workspaceId}
        sessionId={sessionId}
        settings={settings}
        onConnectionSettingsChange={(next) => setSettings((prev) => ({ ...prev, connection: next }))}
        onBehaviorSettingsChange={(next) => setSettings((prev) => ({ ...prev, behavior: next }))}
        onWorkspaceSettingsChange={(next) => setSettings((prev) => ({ ...prev, workspace: next }))}
        density={layoutState.density}
        onDensityChange={(next) => updateLayout({ density: next })}
        showReasoningSummaries={layoutState.showReasoningSummaries}
        onShowReasoningSummariesChange={(next) => updateLayout({ showReasoningSummaries: next })}
        showExecutionEvents={layoutState.showExecutionEvents}
        onShowExecutionEventsChange={(next) => updateLayout({ showExecutionEvents: next })}
        traceShortcutVisible={layoutState.showTraceShortcut}
        onTraceShortcutVisibleChange={(next) => updateLayout({ showTraceShortcut: next })}
        healthStatus={healthStatus}
        appMode={layoutState.appMode}
        onAppModeChange={setAppMode}
        leftPanelOpen={layoutState.leftSidebarOpen}
        rightPanelOpen={layoutState.rightSidebarOpen}
        onToggleLeftPanel={() => updateLayout({ leftSidebarOpen: !layoutState.leftSidebarOpen })}
        onToggleRightPanel={() => updateLayout({ rightSidebarOpen: !layoutState.rightSidebarOpen })}
      />

      <main className="min-h-0 flex-1">
        <AppLayout
          leftVisible={layoutState.leftSidebarOpen}
          rightVisible={layoutState.rightSidebarOpen}
          onToggleLeft={() => updateLayout({ leftSidebarOpen: !layoutState.leftSidebarOpen })}
          onToggleRight={() => updateLayout({ rightSidebarOpen: !layoutState.rightSidebarOpen })}
          leftPanel={
            <LeftSidebar
              section={layoutState.leftSidebarSection}
              onSectionChange={setLeftSidebarSection}
              sections={{
                chats: (
                  <ChatsSection
                    workspaceId={workspaceId}
                    sessionId={sessionId}
                    lastUsedSession={lastUsedSession}
                  />
                ),
                projects: <ProjectsSection workspaceId={workspaceId} />,
                views: <ViewsSection appMode={layoutState.appMode} onAppModeChange={setAppMode} />,
                saved: <SavedSection />,
              }}
            />
          }
          centerPanel={
            <MainWorkspace
              appMode={layoutState.appMode}
              chatContent={
                <ChatPanel
                  workspaceId={workspaceId}
                  sessionId={sessionId}
                  onSessionUsed={onSessionUsed}
                  locale={locale}
                  settings={{
                    ...legacySettings,
                    showReasoning: layoutState.showReasoningSummaries,
                    showExecutionEvents: layoutState.showExecutionEvents,
                    showTraceShortcut: layoutState.showTraceShortcut,
                  }}
                  onOpenCanvasView={(request) => {
                    if (request.title?.toLowerCase().includes('trace')) {
                      updateLayout({ rightSidebarOpen: true })
                      setRightSidebarTab('trace')
                    }
                    if (request.title?.toLowerCase().includes('context')) {
                      updateLayout({ rightSidebarOpen: true })
                      setRightSidebarTab('context')
                    }
                    openCanvasView(request)
                  }}
                />
              }
              canvasContent={
                <CanvasHost
                  canvasState={
                    layoutState.canvas.activeView === 'empty' && lastGraph
                      ? {
                          activeView: 'graph',
                          title: 'Graph View',
                          payload: { nodes: lastGraph.nodes, edges: lastGraph.edges },
                        }
                      : layoutState.canvas
                  }
                />
              }
            />
          }
          rightPanel={
            <RightSidebar>
              <RightPanel
                workspaceId={workspaceId}
                activeTab={layoutState.rightSidebarTab}
                onTabChange={setRightSidebarTab}
              />
            </RightSidebar>
          }
        />
      </main>
      <GlobalModalHost />
    </div>
  )
}

export default function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <AppProvider>
        <AppContent />
      </AppProvider>
    </ThemeProvider>
  )
}
