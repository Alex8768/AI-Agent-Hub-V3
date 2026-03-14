import React from 'react';
import * as Tabs from '@radix-ui/react-tabs';

interface ChatTabsProps {
  chatContent: React.ReactNode;
  canvasContent: React.ReactNode;
  metaContent?: React.ReactNode;
}

const ChatTabs: React.FC<ChatTabsProps> = ({ chatContent, canvasContent, metaContent }) => {
  return (
    <Tabs.Root defaultValue="chat" style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Tabs.List style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid #ccc', padding: '0 1rem' }}>
        <Tabs.Trigger value="chat" style={{ padding: '0.5rem 0', border: 'none', background: 'none', cursor: 'pointer' }}>Chat</Tabs.Trigger>
        <Tabs.Trigger value="canvas" style={{ padding: '0.5rem 0', border: 'none', background: 'none', cursor: 'pointer' }}>Canvas</Tabs.Trigger>
        {metaContent && <Tabs.Trigger value="meta" style={{ padding: '0.5rem 0', border: 'none', background: 'none', cursor: 'pointer' }}>Meta</Tabs.Trigger>}
      </Tabs.List>
      <Tabs.Content value="chat" style={{ flex: 1, overflow: 'auto', padding: '1rem' }}>
        {chatContent}
      </Tabs.Content>
      <Tabs.Content value="canvas" style={{ flex: 1, overflow: 'auto', padding: '1rem' }}>
        {canvasContent}
      </Tabs.Content>
      {metaContent && (
        <Tabs.Content value="meta" style={{ flex: 1, overflow: 'auto', padding: '1rem' }}>
          {metaContent}
        </Tabs.Content>
      )}
    </Tabs.Root>
  );
};

export default ChatTabs;
