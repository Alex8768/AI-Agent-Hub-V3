"""WorkspaceGuard: filesystem safety for workspaces.

Goals:
- Prevent path traversal (.., absolute paths)
- Prevent symlink escape
- Cross-platform (Win/Linux/macOS)
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class WorkspaceAccessError(Exception):
    pass


@dataclass(frozen=True)
class WorkspaceInfo:
    workspace_id: str
    root: Path


class WorkspaceGuard:
    """Minimal workspace guard used by API dependencies and filesystem operations."""

    def __init__(self, base_dir: Optional[str | Path] = None) -> None:
        # Keep default simple; can be wired to settings.data_dir later (P0.5/P2)
        if base_dir is None:
            base_dir = Path("./data/workspaces")
        self._base_dir = Path(base_dir)

    def workspace_root(self, workspace_id: str) -> Path:
        if not workspace_id or workspace_id.strip() == "":
            raise WorkspaceAccessError("workspace_id is required")
        # basic normalization: allow alnum, dash, underscore only
        safe = "".join(ch for ch in workspace_id if ch.isalnum() or ch in ("-", "_"))
        if safe != workspace_id:
            raise WorkspaceAccessError("Invalid workspace_id")
        root = (self._base_dir / safe).resolve()
        return root

    def safe_path(self, workspace_id: str, user_path: str | Path) -> Path:
        """Return a safe absolute path inside workspace root.

        - Reject absolute paths
        - Resolve '..' without escaping root
        - Disallow symlink escape (realpath must stay within root)
        """
        root = self.workspace_root(workspace_id)

        up = Path(user_path)
        if up.is_absolute():
            raise WorkspaceAccessError("Absolute paths are not allowed")

        # Join and resolve
        candidate = (root / up).resolve()

        # Ensure within root
        try:
            candidate.relative_to(root)
        except Exception:
            raise WorkspaceAccessError("Path traversal detected")

        # Symlink escape protection: realpath must remain inside root
        real_root = Path(os.path.realpath(root))
        real_candidate = Path(os.path.realpath(candidate))
        try:
            real_candidate.relative_to(real_root)
        except Exception:
            raise WorkspaceAccessError("Symlink escape detected")

        return candidate

    async def validate_workspace_access(self, workspace_id: str, user_id: str) -> bool:
        """Placeholder access policy.

        For Base: allow access if workspace exists or can be created as default for user.
        Later (P0.3+DB): enforce membership from DB.
        """
        # minimal policy: allow user's default workspace; otherwise require directory exists
        if workspace_id == "default":
            return True
        root = self.workspace_root(workspace_id)
        return root.exists()

    async def get_default_workspace(self, user_id: str) -> str:
        """Return a deterministic default workspace for a user."""
        # deterministic mapping to avoid collisions; keep it simple for Base
        wid = f"ws_{user_id}"
        root = self.workspace_root(wid)
        root.mkdir(parents=True, exist_ok=True)
        return wid
