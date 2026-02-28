from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from .base import HubError

# ============ WORKSPACE ERRORS ============

class WorkspaceError(HubError):
    """Errors related to workspace operations."""
    
    def __init__(
        self,
        message: str,
        workspace_id: Optional[str] = None,
        path: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if workspace_id:
            details["workspace_id"] = workspace_id
        if path:
            details["path"] = path
        
        super().__init__(
            message=message,
            error_code="WORKSPACE_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )



class SecurityError(WorkspaceError):
    """Security-related workspace errors."""
    
    def __init__(
        self,
        message: str,
        violation_type: Optional[str] = None,
        attempted_action: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get("details", {})
        if violation_type:
            details["violation_type"] = violation_type
        if attempted_action:
            details["attempted_action"] = attempted_action
        
        super().__init__(
            message=message,
            error_code="SECURITY_ERROR",
            details=details,
            **{k: v for k, v in kwargs.items() if k != "details"}
        )
