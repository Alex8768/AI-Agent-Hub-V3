from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from src.core.config import get_settings
from src.mcp_protocol import MCPToolRegistry
from src.security.workspace_guard import WorkspaceGuard

_MAX_READ_BYTES = 256 * 1024


def _coerce_bool(value: object, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return default


def _coerce_path(value: object, *, default: str = ".") -> str:
    raw = str(value or "").strip()
    return raw or default


def _safe_abs_path(*, guard: WorkspaceGuard, workspace_root: Path, user_path: object) -> Path:
    return guard.safe_path_root(workspace_root, _coerce_path(user_path))


def _list_workspace_files(*, guard: WorkspaceGuard, workspace_root: Path, arguments: dict[str, object]) -> dict[str, object]:
    target = _safe_abs_path(guard=guard, workspace_root=workspace_root, user_path=arguments.get("path", "."))
    recursive = _coerce_bool(arguments.get("recursive"), default=False)
    if not target.exists():
        raise FileNotFoundError(f"Path does not exist: {target}")
    if not target.is_dir():
        raise NotADirectoryError(f"Not a directory: {target}")
    rows: list[dict[str, object]] = []
    iterator = target.rglob("*") if recursive else target.iterdir()
    for item in iterator:
        rel = item.relative_to(workspace_root)
        rows.append(
            {
                "name": item.name,
                "path": str(rel),
                "type": "directory" if item.is_dir() else "file",
                "size_bytes": item.stat().st_size if item.is_file() else 0,
            }
        )
        if len(rows) >= 500:
            break
    rows.sort(key=lambda x: (str(x.get("type", "")), str(x.get("path", ""))))
    return {
        "root": str(workspace_root),
        "path": str(target.relative_to(workspace_root)),
        "recursive": recursive,
        "count": len(rows),
        "items": rows,
    }


def _read_workspace_file(*, guard: WorkspaceGuard, workspace_root: Path, arguments: dict[str, object]) -> dict[str, object]:
    target = _safe_abs_path(guard=guard, workspace_root=workspace_root, user_path=arguments.get("path"))
    if not target.exists():
        raise FileNotFoundError(f"File does not exist: {target}")
    if not target.is_file():
        raise IsADirectoryError(f"Not a file: {target}")
    size = int(target.stat().st_size)
    if size > _MAX_READ_BYTES:
        raise ValueError(f"File is too large ({size} bytes). Limit: {_MAX_READ_BYTES} bytes")
    encoding = str(arguments.get("encoding", "utf-8") or "utf-8")
    content = target.read_text(encoding=encoding)
    return {
        "path": str(target.relative_to(workspace_root)),
        "size_bytes": size,
        "content": content,
    }


def _save_workspace_file(*, guard: WorkspaceGuard, workspace_root: Path, arguments: dict[str, object]) -> dict[str, object]:
    target = _safe_abs_path(guard=guard, workspace_root=workspace_root, user_path=arguments.get("path"))
    overwrite = _coerce_bool(arguments.get("overwrite"), default=False)
    content = str(arguments.get("content", ""))
    if target.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {target}. Pass overwrite=true to replace.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding=str(arguments.get("encoding", "utf-8") or "utf-8"))
    return {
        "path": str(target.relative_to(workspace_root)),
        "size_bytes": len(content.encode("utf-8")),
        "saved": True,
    }


def wire_workspace_mcp_runtime(app: FastAPI) -> None:
    state = getattr(app, "state", None)
    if state is None:
        return
    registry = getattr(state, "mcp_registry", None)
    if not isinstance(registry, MCPToolRegistry):
        registry = MCPToolRegistry()
        state.mcp_registry = registry

    server_name = "workspace_local"
    existing = registry.get_server(server_name)
    if not existing:
        registry.register_server(
            {
                "server_name": server_name,
                "transport": "http",
                "endpoint": "local://workspace",
                "enabled": True,
                "tool_names": [],
            }
        )

    registry.register_tool(
        {
            "tool_name": "list_files",
            "server_name": server_name,
            "description": "List files and folders in workspace path",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path in workspace", "default": "."},
                    "recursive": {"type": "boolean", "description": "Recursively list children", "default": False},
                },
                "required": [],
            },
            "tags": ["filesystem", "workspace", "read"],
            "enabled": True,
        }
    )
    registry.register_tool(
        {
            "tool_name": "read_file",
            "server_name": server_name,
            "description": "Read UTF-8 text file from workspace",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path"},
                    "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"},
                },
                "required": ["path"],
            },
            "tags": ["filesystem", "workspace", "read"],
            "enabled": True,
        }
    )
    registry.register_tool(
        {
            "tool_name": "save_file",
            "server_name": server_name,
            "description": "Save text content to a workspace file",
            "input_schema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative file path"},
                    "content": {"type": "string", "description": "Text content to save"},
                    "overwrite": {"type": "boolean", "description": "Overwrite existing file", "default": False},
                    "encoding": {"type": "string", "description": "File encoding", "default": "utf-8"},
                },
                "required": ["path", "content"],
            },
            "tags": ["filesystem", "workspace", "save"],
            "enabled": True,
        }
    )

    settings = get_settings()
    guard = WorkspaceGuard()
    workspace_root = settings.workspace_root_path
    if bool(getattr(settings, "workspace_tools_use_repo_root_in_dev", False)) and bool(getattr(settings, "debug", False)):
        # Dev convenience mode: point workspace tools to repository root.
        workspace_root = Path(__file__).resolve().parents[2]
    workspace_root.mkdir(parents=True, exist_ok=True)

    async def _invoker(*, tool_name: str, arguments: dict[str, object]) -> dict[str, object]:
        if tool_name == "list_files":
            return _list_workspace_files(guard=guard, workspace_root=workspace_root, arguments=arguments)
        if tool_name == "read_file":
            return _read_workspace_file(guard=guard, workspace_root=workspace_root, arguments=arguments)
        if tool_name == "save_file":
            return _save_workspace_file(guard=guard, workspace_root=workspace_root, arguments=arguments)
        raise ValueError(f"Unsupported tool: {tool_name}")

    state.mcp_tool_invoker = _invoker
