import React from 'react';
import * as Tabs from '@radix-ui/react-tabs';

interface ChatTabsProps {
  chatContent: React.ReactNode;
  canvasContent: React.ReactNode;
  metaContent?: React.ReactNode;
}

const ChatTabs: React.FC<ChatTabsProps> = ({ chatContent, canvasContent, metaContent }) => {
  return (
    <Tabs.Root defaultValue="chat" className="tabs-root">
      <Tabs.List className="tabs-list">
        <Tabs.Trigger value="chat" className="tabs-trigger">Chat</Tabs.Trigger>
        <Tabs.Trigger value="canvas" className="tabs-trigger">Canvas</Tabs.Trigger>
        {metaContent && <Tabs.Trigger value="meta" className="tabs-trigger">Meta</Tabs.Trigger>}
      </Tabs.List>
      <Tabs.Content value="chat" className="tabs-content">
        {chatContent}
      </Tabs.Content>
      <Tabs.Content value="canvas" className="tabs-content">
        {canvasContent}
      </Tabs.Content>
      {metaContent && (
        <Tabs.Content value="meta" className="tabs-content">
          {metaContent}
        </Tabs.Content>
      )}
    </Tabs.Root>
  );
};

export default ChatTabs;
