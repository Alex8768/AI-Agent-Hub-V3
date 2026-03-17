import React from 'react'
import type { ToolItemDto, ToolSchemaDto } from '../../contracts/api'
import { Copy, Loader2, Sparkles } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'

interface ToolInvokeModalProps {
  selectedTool: ToolItemDto
  selectedToolSchema: ToolSchemaDto | null
  schemaLoading: boolean
  invokeArgsText: string
  invokeResult: string
  invokeError: string
  invokeLoading: boolean
  resultCopied: boolean
  onClose: () => void
  onArgsChange: (value: string) => void
  onApplySchemaTemplate: () => void
  onInvoke: (event: React.FormEvent) => void
  onCopyResult: () => void
}

const ToolInvokeModal: React.FC<ToolInvokeModalProps> = ({
  selectedTool,
  selectedToolSchema,
  schemaLoading,
  invokeArgsText,
  invokeResult,
  invokeError,
  invokeLoading,
  resultCopied,
  onClose,
  onArgsChange,
  onApplySchemaTemplate,
  onInvoke,
  onCopyResult,
}) => {
  const inputSchema = selectedToolSchema?.input_schema as Record<string, unknown> | undefined

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[90vh] max-w-3xl overflow-hidden p-0">
        <DialogHeader className="border-b p-4">
          <DialogTitle className="flex items-center gap-2 text-base">
            <span>Invoke Tool:</span>
            <Badge variant="secondary" className="font-mono">
              {selectedTool.tool_name}
            </Badge>
          </DialogTitle>
        </DialogHeader>

        <div className="grid gap-4 p-4">
          {schemaLoading && (
            <div className="flex items-center gap-2 rounded-md border bg-muted/50 p-3 text-sm">
              <Loader2 className="h-4 w-4 animate-spin" />
              Loading schema...
            </div>
          )}

          {inputSchema && (
            <div className="rounded-md border">
              <div className="border-b bg-muted/30 px-3 py-2 text-xs font-semibold">
                Input Schema
              </div>
              <ScrollArea className="h-40">
                <pre className="p-3 font-mono text-xs">
                  {JSON.stringify(inputSchema, null, 2)}
                </pre>
              </ScrollArea>
            </div>
          )}

          <form onSubmit={onInvoke} className="space-y-3">
            <div className="space-y-2">
              <label className="text-xs font-semibold">Arguments (JSON)</label>
              <Textarea
                value={invokeArgsText}
                onChange={(e) => onArgsChange(e.target.value)}
                rows={8}
                className="font-mono text-xs"
                placeholder="{}"
              />
            </div>

            {invokeError && (
              <div className="rounded-md border border-destructive/30 bg-destructive/10 p-2 text-xs text-destructive">
                Error: {invokeError}
              </div>
            )}

            <div className="flex items-center justify-between gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={onApplySchemaTemplate}
                disabled={schemaLoading || invokeLoading}
              >
                <Sparkles className="mr-2 h-3 w-3" />
                Use Template
              </Button>

              <div className="flex items-center gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={onClose}
                  disabled={invokeLoading}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={invokeLoading}
                >
                  {invokeLoading ? (
                    <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                  ) : null}
                  Run
                </Button>
              </div>
            </div>
          </form>

          {invokeResult && (
            <div className="rounded-md border">
              <div className="flex items-center justify-between border-b bg-muted/30 px-3 py-2">
                <h4 className="text-xs font-semibold">Result</h4>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-6 gap-1 px-2 text-xs"
                  onClick={onCopyResult}
                >
                  <Copy className="h-3 w-3" />
                  {resultCopied ? 'Copied!' : 'Copy'}
                </Button>
              </div>
              <ScrollArea className="h-60">
                <pre className="p-3 font-mono text-xs">
                  {invokeResult}
                </pre>
              </ScrollArea>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default ToolInvokeModal
