import React from 'react';
import { Group, Panel, Separator } from 'react-resizable-panels';

interface AppLayoutProps {
  leftPanel: React.ReactNode;
  centerPanel: React.ReactNode;
  rightPanel: React.ReactNode;
  leftVisible?: boolean;
  rightVisible?: boolean;
}

const AppLayout: React.FC<AppLayoutProps> = ({
  leftPanel,
  centerPanel,
  rightPanel,
  leftVisible = true,
  rightVisible = true,
}) => {
  return (
    <Group orientation="horizontal" style={{ height: '100%', width: '100%' }}>
      {leftVisible && (
        <>
          <Panel defaultSize={20} minSize={15} maxSize={30}>
            <div className="layout-panel layout-panel-left">
              {leftPanel}
            </div>
          </Panel>
          <Separator className="layout-separator" />
        </>
      )}

      <Panel minSize={30}>
        <div className="layout-panel layout-panel-center">
          {centerPanel}
        </div>
      </Panel>

      {rightVisible && (
        <>
          <Separator className="layout-separator" />
          <Panel defaultSize={25} minSize={15} maxSize={35}>
            <div className="layout-panel layout-panel-right">
              {rightPanel}
            </div>
          </Panel>
        </>
      )}
    </Group>
  );
};

export default AppLayout;
