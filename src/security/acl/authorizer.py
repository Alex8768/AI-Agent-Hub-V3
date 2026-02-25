from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List


class AuthorizationError(Exception):
    pass


class Authorizer:
    async def authorize_workspace(self, user: Dict[str, Any], workspace_id: str) -> None:
        raise NotImplementedError


@dataclass
class ACLAuthorizer(Authorizer):
    """
    Minimal ACL MVP.

    Rules (MVP):
    - Allow access to:
        - workspace "default"
        - workspace "ws_<user_id>"
        - any workspace if user has role "admin"
    - Otherwise -> AuthorizationError
    """

    async def authorize_workspace(self, user: Dict[str, Any], workspace_id: str) -> None:
        user_id = str(user.get("id"))
        roles: List[str] = user.get("roles") or []

        if "admin" in roles:
            return

        if workspace_id == "default":
            return

        if workspace_id == f"ws_{user_id}":
            return

        raise AuthorizationError(f"Access denied to workspace '{workspace_id}' for user '{user_id}'")
