import React, { useEffect, useState } from 'react'
import {
  deleteDocument,
  getToolSchema,
  invokeTool,
  listDocuments,
  listTools,
  uploadDocument,
} from '../lib/apiClient'
import type { DocumentItem, ToolItemDto, ToolSchemaDto } from '../contracts/api'
import type { RightSidebarTab } from './shell/layoutState'
import ToolInvokeModal from './right-panel/ToolInvokeModal'
import ApprovalsTab from './right-sidebar/ApprovalsTab'
import ContextTab from './right-sidebar/ContextTab'
import FilesTab from './right-sidebar/FilesTab'
import ToolsTab from './right-sidebar/ToolsTab'
import TraceTab from './right-sidebar/TraceTab'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useAppContext } from '../context/useAppContext'

interface RightPanelProps {
  workspaceId: string
  activeTab: RightSidebarTab
  onTabChange: (tab: RightSidebarTab) => void
}

const RightPanel: React.FC<RightPanelProps> = ({ workspaceId, activeTab, onTabChange }) => {
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [documentsLoading, setDocumentsLoading] = useState(false)
  const [tools, setTools] = useState<ToolItemDto[]>([])
  const [toolsLoading, setToolsLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedTool, setSelectedTool] = useState<ToolItemDto | null>(null)
  const [selectedToolSchema, setSelectedToolSchema] = useState<ToolSchemaDto | null>(null)
  const [schemaLoading, setSchemaLoading] = useState(false)
  const [invokeArgsText, setInvokeArgsText] = useState('{}')
  const [invokeResult, setInvokeResult] = useState('')
  const [invokeError, setInvokeError] = useState('')
  const [invokeLoading, setInvokeLoading] = useState(false)
  const [resultCopied, setResultCopied] = useState(false)
  const { lastAnswer } = useAppContext()

  useEffect(() => {
    let mounted = true

    const fetchData = async () => {
      setDocumentsLoading(true)
      setToolsLoading(true)

      try {
        const [docs, toolsData] = await Promise.all([
          listDocuments({ workspaceId }),
          listTools({ workspaceId })
        ])

        if (mounted) {
          setDocuments(docs)
          setTools(toolsData.tools || [])
        }
      } catch (err) {
        if (mounted) setError(String(err))
      } finally {
        if (mounted) {
          setDocumentsLoading(false)
          setToolsLoading(false)
        }
      }
    }

    fetchData()

    return () => { mounted = false }
  }, [workspaceId])

  const handleUpload = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!selectedFile) return

    setDocumentsLoading(true)
    setError('')

    try {
      await uploadDocument(selectedFile, { workspaceId })
      setSelectedFile(null)
      const items = await listDocuments({ workspaceId })
      setDocuments(items)
    } catch (err) {
      setError(String(err))
    } finally {
      setDocumentsLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    setDocumentsLoading(true)
    setError('')

    try {
      await deleteDocument(id, { workspaceId })
      setDocuments(prev => prev.filter(item => item.id !== id))
    } catch (err) {
      setError(String(err))
    } finally {
      setDocumentsLoading(false)
    }
  }

  const openInvokeModal = async (tool: ToolItemDto) => {
    setSelectedTool(tool)
    setSelectedToolSchema(null)
    setInvokeArgsText('{}')
    setInvokeResult('')
    setInvokeError('')
    setSchemaLoading(true)

    try {
      const schema = await getToolSchema(tool.tool_name, { workspaceId })
      setSelectedToolSchema(schema)

      const inputSchema = schema.input_schema as { properties?: Record<string, unknown> } | undefined
      const template = inputSchema?.properties
        ? Object.keys(inputSchema.properties).reduce((acc, key) => {
            acc[key] = ''
            return acc
          }, {} as Record<string, unknown>)
        : {}

      setInvokeArgsText(JSON.stringify(template, null, 2))
    } catch (err) {
      setInvokeError(`Failed to load schema: ${String(err)}`)
    } finally {
      setSchemaLoading(false)
    }
  }

  const handleInvoke = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!selectedTool?.tool_name) return

    setInvokeLoading(true)
    setInvokeError('')
    setInvokeResult('')

    try {
      const parsed = JSON.parse(invokeArgsText)
      const result = await invokeTool(selectedTool.tool_name, parsed, { workspaceId })
      setInvokeResult(JSON.stringify(result, null, 2))
    } catch (err) {
      setInvokeError(String(err))
    } finally {
      setInvokeLoading(false)
    }
  }

  const copyResult = async () => {
    if (!invokeResult) return
    await navigator.clipboard.writeText(invokeResult)
    setResultCopied(true)
    setTimeout(() => setResultCopied(false), 1200)
  }

  return (
    <>
      <Tabs value={activeTab} onValueChange={(value) => onTabChange(value as RightSidebarTab)} className="h-full">
        <div className="border-b px-3 py-2">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="files" className="text-xs">Files</TabsTrigger>
            <TabsTrigger value="tools" className="text-xs">Tools</TabsTrigger>
            <TabsTrigger value="context" className="text-xs">Context</TabsTrigger>
            <TabsTrigger value="trace" className="text-xs">Trace</TabsTrigger>
            <TabsTrigger value="approvals" className="text-xs">Approvals</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="files" className="h-[calc(100%-48px)] overflow-auto">
          <FilesTab
            documents={documents}
            documentsLoading={documentsLoading}
            error={error}
            selectedFile={selectedFile}
            onFileSelected={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
            onUpload={handleUpload}
            onDelete={handleDelete}
          />
        </TabsContent>

        <TabsContent value="tools" className="h-[calc(100%-48px)] overflow-auto">
          <ToolsTab
            tools={tools}
            toolsLoading={toolsLoading}
            onInvokeTool={openInvokeModal}
          />
        </TabsContent>

        <TabsContent value="context" className="h-[calc(100%-48px)] overflow-auto">
          <ContextTab lastAnswer={lastAnswer} />
        </TabsContent>

        <TabsContent value="trace" className="h-[calc(100%-48px)] overflow-auto">
          <TraceTab lastAnswer={lastAnswer} />
        </TabsContent>

        <TabsContent value="approvals" className="h-[calc(100%-48px)] overflow-auto">
          <ApprovalsTab />
        </TabsContent>
      </Tabs>

      {selectedTool && (
        <ToolInvokeModal
          selectedTool={selectedTool}
          selectedToolSchema={selectedToolSchema}
          schemaLoading={schemaLoading}
          invokeArgsText={invokeArgsText}
          invokeResult={invokeResult}
          invokeError={invokeError}
          invokeLoading={invokeLoading}
          resultCopied={resultCopied}
          onClose={() => setSelectedTool(null)}
          onArgsChange={setInvokeArgsText}
          onApplySchemaTemplate={() => {
            if (!selectedToolSchema) return
            const inputSchema = selectedToolSchema.input_schema as { properties?: Record<string, unknown> } | undefined
            const template = inputSchema?.properties
              ? Object.keys(inputSchema.properties).reduce((acc, key) => {
                  acc[key] = ''
                  return acc
                }, {} as Record<string, unknown>)
              : {}
            setInvokeArgsText(JSON.stringify(template, null, 2))
          }}
          onInvoke={handleInvoke}
          onCopyResult={copyResult}
        />
      )}
    </>
  )
}

export default RightPanel
