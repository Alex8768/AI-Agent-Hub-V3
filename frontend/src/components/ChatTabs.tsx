import React from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

interface ChatTabsProps {
  chatContent: React.ReactNode;
  canvasContent: React.ReactNode;
  metaContent?: React.ReactNode;
  locale?: 'en' | 'ru';
  labels?: {
    split?: string;
    meta?: string;
  };
}

const ChatTabs: React.FC<ChatTabsProps> = ({ chatContent, canvasContent, metaContent, locale = 'en', labels }) => {
  const splitLabel = labels?.split || (locale === 'ru' ? 'Сплит' : 'Split');
  const metaLabel = labels?.meta || 'Meta';
  return (
    <Tabs defaultValue="chat" className="flex h-full min-h-0 flex-col">
      <div className="border-b px-3 py-2">
        <TabsList className="h-8 bg-muted/60">
          <TabsTrigger value="chat" className="text-xs">Chat</TabsTrigger>
          <TabsTrigger value="canvas" className="text-xs">Canvas</TabsTrigger>
          <TabsTrigger value="split" className="text-xs">{splitLabel}</TabsTrigger>
          {metaContent && <TabsTrigger value="meta" className="text-xs">{metaLabel}</TabsTrigger>}
        </TabsList>
      </div>
      <TabsContent value="chat" className="mt-0 min-h-0 flex-1 overflow-hidden">
        {chatContent}
      </TabsContent>
      <TabsContent value="canvas" className="mt-0 min-h-0 flex-1 overflow-hidden">
        {canvasContent}
      </TabsContent>
      <TabsContent value="split" className="mt-0 min-h-0 flex-1 overflow-hidden">
        <div className="grid h-full min-h-0 grid-cols-[1.2fr_1fr] gap-2 p-2">
          <section className="min-h-0 overflow-hidden rounded-md border">
            {chatContent}
          </section>
          <section className="min-h-0 overflow-hidden rounded-md border">
            {canvasContent}
          </section>
        </div>
      </TabsContent>
      {metaContent && (
        <TabsContent value="meta" className="mt-0 min-h-0 flex-1 overflow-hidden">
          {metaContent}
        </TabsContent>
      )}
    </Tabs>
  );
};

export default ChatTabs;
