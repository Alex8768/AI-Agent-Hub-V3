"""
Dependencies for AI Agent Hub V3 API.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.core.config import settings


security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """Get current user from token."""
    if not settings.debug:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # TODO: Implement actual token validation
        # For now, return a mock user
        return {"id": "user_123", "username": "demo_user"}
    
    # In debug mode, allow anonymous access
    return {"id": "debug_user", "username": "debug"}


async def get_workspace(
    workspace_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """Get or validate workspace."""
    from src.security.workspace_guard import WorkspaceGuard
    
    guard = WorkspaceGuard()
    
    if workspace_id:
        # Validate workspace access
        if not await guard.validate_workspace_access(workspace_id, user["id"]):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access to workspace denied",
            )
        return workspace_id
    else:
        # Get default workspace
        return await guard.get_default_workspace(user["id"])


async def get_llm_provider(
    provider_type: Optional[str] = None
):
    """Get LLM provider based on configuration."""
    from src.layers.base.llm.providers import LLMProviderFactory
    
    provider_name = provider_type or settings.llm_provider
    factory = LLMProviderFactory()
    
    return await factory.get_provider(provider_name)
