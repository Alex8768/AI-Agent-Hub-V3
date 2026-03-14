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
    <Group orientation="horizontal" style={{ height: '100vh', width: '100%' }}>
      {leftVisible && (
        <>
          <Panel defaultSize={20} minSize={15} maxSize={30}>
            <div style={{ height: '100%', overflow: 'auto', borderRight: '1px solid #ccc' }}>
              {leftPanel}
            </div>
          </Panel>
          <Separator style={{ width: '4px', background: '#888', cursor: 'col-resize' }} />
        </>
      )}
      <Panel minSize={30}>
        <div style={{ height: '100%', overflow: 'auto' }}>{centerPanel}</div>
      </Panel>
      {rightVisible && (
        <>
          <Separator style={{ width: '4px', background: '#888', cursor: 'col-resize' }} />
          <Panel defaultSize={25} minSize={15} maxSize={35}>
            <div style={{ height: '100%', overflow: 'auto', borderLeft: '1px solid #ccc' }}>
              {rightPanel}
            </div>
          </Panel>
        </>
      )}
    </Group>
  );
};

export default AppLayout;
