import type { ToolItemDto } from '../../contracts/api'
import ToolsPanel from '../right-panel/ToolsPanel'

interface ToolsTabProps {
  tools: ToolItemDto[]
  toolsLoading: boolean
  onInvokeTool: (tool: ToolItemDto) => void
}

export default function ToolsTab({ tools, toolsLoading, onInvokeTool }: ToolsTabProps) {
  return <ToolsPanel tools={tools} toolsLoading={toolsLoading} onInvokeTool={onInvokeTool} />
}
