from __future__ import annotations

import pytest
from fastapi import HTTPException

from src.core.config import settings


@pytest.mark.asyncio
async def test_acl_denies_foreign_workspace(monkeypatch):
    # Enable ACL feature
    monkeypatch.setattr(settings, "feature_acl", True, raising=False)

    # Make guard say "ok" so ACL is the one to decide
    from src.security.workspace_guard.guard import WorkspaceGuard

    async def _allow_all(self, workspace_id: str, user_id: str) -> bool:
        return True

    monkeypatch.setattr(WorkspaceGuard, "validate_workspace_access", _allow_all, raising=True)

    from src.api.dependencies_impl import get_workspace

    user = {"id": "u1", "roles": [], "claims": {}}

    # Not default and not ws_u1 -> should be denied by ACLAuthorizer
    with pytest.raises(HTTPException) as e:
        await get_workspace(workspace_id="ws_someone_else", user=user)

    assert e.value.status_code == 403

    monkeypatch.setattr(settings, "feature_acl", False, raising=False)


@pytest.mark.asyncio
async def test_acl_allows_default_and_personal_workspace(monkeypatch):
    monkeypatch.setattr(settings, "feature_acl", True, raising=False)

    from src.security.workspace_guard.guard import WorkspaceGuard

    async def _allow_all(self, workspace_id: str, user_id: str) -> bool:
        return True

    monkeypatch.setattr(WorkspaceGuard, "validate_workspace_access", _allow_all, raising=True)

    from src.api.dependencies_impl import get_workspace

    user = {"id": "u1", "roles": [], "claims": {}}

    assert await get_workspace(workspace_id="default", user=user) == "default"
    assert await get_workspace(workspace_id="ws_u1", user=user) == "ws_u1"

    monkeypatch.setattr(settings, "feature_acl", False, raising=False)
