import React from 'react'
import type { DocumentItem } from '../../contracts/api'
import { File as FileIcon, Loader2, Trash2, Upload } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'

interface DocumentsPanelProps {
  documents: DocumentItem[]
  documentsLoading: boolean
  error: string
  selectedFile: File | null
  onFileSelected: (event: React.ChangeEvent<HTMLInputElement>) => void
  onUpload: (event: React.FormEvent) => void
  onDelete: (id: string) => void
}

const DocumentsPanel: React.FC<DocumentsPanelProps> = ({
  documents,
  documentsLoading,
  error,
  selectedFile,
  onFileSelected,
  onUpload,
  onDelete,
}) => {
  return (
    <div className="flex h-full flex-col gap-3 p-3">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Upload className="h-4 w-4" />
            Upload Document
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <form onSubmit={onUpload} className="space-y-2">
            <Input
              type="file"
              onChange={onFileSelected}
              className="file:mr-2 file:rounded file:border-0 file:bg-primary/10 file:px-2 file:py-1 file:text-xs file:font-medium hover:file:bg-primary/20"
            />
            <Button
              type="submit"
              disabled={!selectedFile || documentsLoading}
              className="w-full"
              size="sm"
            >
              {documentsLoading ? (
                <Loader2 className="mr-2 h-3 w-3 animate-spin" />
              ) : (
                <Upload className="mr-2 h-3 w-3" />
              )}
              Upload
            </Button>
          </form>
          {error && (
            <div className="rounded-md border border-destructive/30 bg-destructive/10 p-2 text-xs text-destructive">
              Error: {error}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="flex-1">
        <CardHeader className="pb-2">
          <CardTitle className="flex items-center gap-2 text-sm">
            <FileIcon className="h-4 w-4" />
            Workspace Files
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <ScrollArea className="h-[calc(100vh-300px)] px-3 pb-3">
            {documentsLoading && (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            )}

            {!documentsLoading && documents.length === 0 && (
              <div className="py-8 text-center text-sm text-muted-foreground">
                No documents yet
              </div>
            )}

            <div className="space-y-2">
              {documents.map((doc) => (
                <div key={doc.id} className="group rounded-lg border p-2 transition-colors hover:bg-muted/50">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium" title={doc.filename}>
                        {doc.filename}
                      </p>
                      <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                        <Badge variant="outline" className="px-1 py-0 text-[10px]">
                          {doc.status}
                        </Badge>
                        <span>{(doc.size_bytes / 1024).toFixed(1)} KB</span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 opacity-0 transition-opacity group-hover:opacity-100"
                      onClick={() => onDelete(doc.id)}
                      disabled={documentsLoading}
                    >
                      <Trash2 className="h-3 w-3 text-destructive" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}

export default DocumentsPanel
