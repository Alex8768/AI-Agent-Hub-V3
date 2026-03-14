import React from 'react';
import type { ToolItemDto } from '../../contracts/api';

interface ToolsPanelProps {
  tools: ToolItemDto[];
  toolsLoading: boolean;
  onInvokeTool: (tool: ToolItemDto) => void | Promise<void>;
}

const ToolsPanel: React.FC<ToolsPanelProps> = ({
  tools,
  toolsLoading,
  onInvokeTool,
}) => {
  return (
    <div className="panel-body">
      <h3 className="panel-title">MCP Tools</h3>

      {toolsLoading && <p className="empty-note">Loading tools...</p>}
      {!toolsLoading && tools.length === 0 && (
        <p className="empty-note">No tools available.</p>
      )}

      <ul className="item-list">
        {tools.map((tool) => (
          <li key={tool.tool_name} className="item-row tool-row">
            <div className="item-main">
              <strong>{tool.tool_name}</strong>
              <span className="item-subtle">
                ({tool.server_name || 'unknown'})
              </span>
              <p className="item-subtle">
                {tool.description || 'No description'}
              </p>
            </div>

            <button
              className="btn btn-secondary"
              type="button"
              onClick={() => void onInvokeTool(tool)}
            >
              Invoke
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default ToolsPanel;
