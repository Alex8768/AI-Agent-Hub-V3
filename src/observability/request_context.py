from __future__ import annotations

from fastapi import Request


def get_request_id(http: Request) -> str | None:
    """Get request correlation id from request state or headers."""
    return (
        getattr(getattr(http, "state", None), "request_id", None)
        or http.headers.get("x-request-id")
        or http.headers.get("X-Request-ID")
        or http.headers.get("X-Request-Id")
    )


def get_workspace_id(http: Request) -> str:
    """Get workspace id from request state or header fallback."""
    ws = (
        getattr(getattr(http, "state", None), "workspace_id", None)
        or http.headers.get("x-workspace-id")
        or http.headers.get("X-Workspace-Id")
        or http.headers.get("X-Workspace-ID")
        or "default"
    )
    return str(ws or "default")


def set_workspace_id(http: Request, workspace_id: str) -> None:
    """Store workspace context in request.state for middleware/services."""
    try:
        http.state.workspace_id = str(workspace_id or "default")
    except Exception:
        pass
