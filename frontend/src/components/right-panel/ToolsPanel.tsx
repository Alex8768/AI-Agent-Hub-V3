import React from 'react'
import type { ToolItemDto } from '../../contracts/api'
import { Hammer, Play, Wrench } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ScrollArea } from '@/components/ui/scroll-area'

interface ToolsPanelProps {
  tools: ToolItemDto[]
  toolsLoading: boolean
  onInvokeTool: (tool: ToolItemDto) => void
}

const ToolsPanel: React.FC<ToolsPanelProps> = ({
  tools,
  toolsLoading,
  onInvokeTool,
}) => {
  if (toolsLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Hammer className="mx-auto h-8 w-8 animate-pulse text-muted-foreground" />
          <p className="mt-2 text-sm text-muted-foreground">Loading tools...</p>
        </div>
      </div>
    )
  }

  if (tools.length === 0) {
    return (
      <div className="flex h-full items-center justify-center p-6">
        <Card className="w-full">
          <CardContent className="pt-6 text-center">
            <Wrench className="mx-auto h-8 w-8 text-muted-foreground" />
            <p className="mt-2 text-sm text-muted-foreground">No tools available</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="flex h-full flex-col p-3">
      <Card className="flex-1">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Hammer className="h-4 w-4" />
            Available Tools
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[calc(100vh-300px)] px-3 pb-3">
            <div className="space-y-2">
              {tools.map((tool) => (
                <Card key={tool.tool_name} className="overflow-hidden">
                  <CardContent className="p-3">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <p className="truncate text-sm font-medium">
                            {tool.tool_name}
                          </p>
                          {tool.server_name && (
                            <Badge variant="secondary" className="px-1 text-[10px]">
                              {tool.server_name}
                            </Badge>
                          )}
                        </div>
                        <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
                          {tool.description || 'No description'}
                        </p>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        className="shrink-0"
                        onClick={() => onInvokeTool(tool)}
                      >
                        <Play className="mr-1 h-3 w-3" />
                        Run
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}

export default ToolsPanel
