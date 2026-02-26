"""
Dependencies for AI Agent Hub V3 API.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi import Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.config import settings
from src.security.auth.jwt import verify_token, JWTError


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get current user from Bearer JWT.

    - In production: requires valid JWT (HS256) with at least `sub`
    - In debug mode: allows anonymous access (debug_user) if no token provided
    """
    if not settings.debug:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        secret = getattr(settings, "jwt_secret", None) or getattr(settings, "secret_key", None) or ""
        if not secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="JWT secret is not configured",
            )

        token = credentials.credentials
        try:
            claims = verify_token(
                token,
                secret,
                issuer=getattr(settings, "jwt_issuer", None),
                audience=getattr(settings, "jwt_audience", None),
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {e}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        user_id = claims.get("sub") or claims.get("user_id") or claims.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing sub",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {
            "id": str(user_id),
            "username": claims.get("username") or claims.get("preferred_username") or str(user_id),
            "roles": claims.get("roles") or [],
            "claims": claims,
        }

    # Debug mode: allow anonymous access, but if token provided — still validate (best effort)
    if credentials:
        secret = getattr(settings, "jwt_secret", None) or getattr(settings, "secret_key", None) or ""
        if secret:
            try:
                claims = verify_token(
                    credentials.credentials,
                    secret,
                    issuer=getattr(settings, "jwt_issuer", None),
                    audience=getattr(settings, "jwt_audience", None),
                )
                user_id = claims.get("sub") or claims.get("user_id") or claims.get("id") or "debug_user"
                return {
                    "id": str(user_id),
                    "username": claims.get("username") or claims.get("preferred_username") or str(user_id),
                    "roles": claims.get("roles") or [],
                    "claims": claims,
                }
            except Exception:
                pass

    return {"id": "debug_user", "username": "debug", "roles": [], "claims": {}}


async def get_workspace(
    workspace_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
    x_workspace_id: Optional[str] = Header(default=None, alias="X-Workspace-Id"),
):
    """Get or validate workspace."""
    # Local imports keep this dependency robust during refactors
    from fastapi import HTTPException, status
    from src.security.workspace_guard import WorkspaceGuard
    from src.core.providers import get_authorizer

    # Header fallback (clients/PS scripts may prefer header to avoid query plumbing)
    if not workspace_id and x_workspace_id:
        workspace_id = x_workspace_id
    
    guard = WorkspaceGuard()
    
    if workspace_id:
        # Validate workspace access (filesystem-level)
        if not await guard.validate_workspace_access(workspace_id, user["id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to workspace denied",
            )

        # Pro ACL enforcement (feature-flagged via providers)
        try:
            authorizer = get_authorizer()
            # authorize_workspace is async in ACLAuthorizer
            if hasattr(authorizer, "authorize_workspace"):
                await authorizer.authorize_workspace(user, workspace_id)  # type: ignore[attr-defined]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e) or "Access denied by ACL",
            )

        return workspace_id
    else:
        # Get default workspace (deterministic for Base/Smoke)
        return "default"

async def get_llm_provider(
    provider_type: Optional[str] = None
):
    """Get LLM provider based on configuration.

    IMPORTANT: Do not instantiate abstract factories here.
    Delegate to src.layers.base.llm.providers.get_llm_provider (concrete wiring).
    """
    # Normalize provider name (Enum -> str) for base provider router
    provider_name = provider_type or settings.llm_provider
    try:
        provider_name = provider_name.value  # type: ignore[attr-defined]
    except Exception:
        provider_name = str(provider_name)

    from src.layers.base.llm.providers import get_llm_provider as _get

    return await _get(provider_type=provider_name)
