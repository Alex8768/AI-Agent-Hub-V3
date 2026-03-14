import React from 'react';
import { Group, Panel, Separator } from 'react-resizable-panels';

interface AppLayoutProps {
  leftPanel: React.ReactNode;
  centerPanel: React.ReactNode;
  rightPanel: React.ReactNode;
  leftVisible?: boolean;
  rightVisible?: boolean;
  onToggleLeft?: () => void;
  onToggleRight?: () => void;
}

interface SidebarShellProps {
  side: 'left' | 'right';
  title: string;
  onCollapse?: () => void;
  children: React.ReactNode;
}

const SidebarShell: React.FC<SidebarShellProps> = ({
  side,
  title,
  onCollapse,
  children,
}) => {
  return (
    <div className={`sidebar-shell sidebar-shell-${side}`}>
      <div className="sidebar-header">
        <span className="sidebar-header-title">{title}</span>
        <button
          className="sidebar-toggle-btn"
          type="button"
          onClick={onCollapse}
          aria-label={`Collapse ${title}`}
        >
          {side === 'left' ? '‹' : '›'}
        </button>
      </div>
      <div className="sidebar-content">{children}</div>
    </div>
  );
};

interface RailProps {
  side: 'left' | 'right';
  label: string;
  onExpand?: () => void;
}

const Rail: React.FC<RailProps> = ({ side, label, onExpand }) => (
  <div className={`layout-rail layout-rail-${side}`}>
    <button
      className="layout-rail-button"
      type="button"
      onClick={onExpand}
      aria-label={`Expand ${label}`}
    >
      {side === 'left' ? '›' : '‹'}
    </button>
    <span className="layout-rail-label">{label}</span>
  </div>
);

const AppLayout: React.FC<AppLayoutProps> = ({
  leftPanel,
  centerPanel,
  rightPanel,
  leftVisible = true,
  rightVisible = true,
  onToggleLeft,
  onToggleRight,
}) => {
  return (
    <Group orientation="horizontal" style={{ height: '100%', width: '100%' }}>
      {leftVisible ? (
        <>
          <Panel defaultSize={18} minSize={18} maxSize={26}>
            <div className="layout-panel layout-panel-left">
              <SidebarShell side="left" title="Workspace" onCollapse={onToggleLeft}>
                {leftPanel}
              </SidebarShell>
            </div>
          </Panel>
          <Separator className="layout-separator" />
        </>
      ) : (
        <>
          <Panel defaultSize={2.8} minSize={2.8} maxSize={2.8}>
            <Rail side="left" label="NAV" onExpand={onToggleLeft} />
          </Panel>
          <Separator className="layout-separator is-collapsed" />
        </>
      )}

      <Panel minSize={40}>
        <div className="layout-panel layout-panel-center">{centerPanel}</div>
      </Panel>

      {rightVisible ? (
        <>
          <Separator className="layout-separator" />
          <Panel defaultSize={22} minSize={20} maxSize={30}>
            <div className="layout-panel layout-panel-right">
              <SidebarShell side="right" title="Inspector" onCollapse={onToggleRight}>
                {rightPanel}
              </SidebarShell>
            </div>
          </Panel>
        </>
      ) : (
        <>
          <Separator className="layout-separator is-collapsed" />
          <Panel defaultSize={3.2} minSize={3.2} maxSize={3.2}>
            <Rail side="right" label="INSPECT" onExpand={onToggleRight} />
          </Panel>
        </>
      )}
    </Group>
  );
};

export default AppLayout;
