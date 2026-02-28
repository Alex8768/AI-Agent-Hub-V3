from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from .base import HubError

# ============ UTILITY FUNCTIONS ============
def wrap_exception(
    exception: Exception,
    wrapper_class: type[HubError],
    message: Optional[str] = None,
    **kwargs
) -> HubError:
    """
    Wrap any exception into a HubError hierarchy exception.
    
    Args:
        exception: Original exception
        wrapper_class: HubError subclass to wrap with
        message: Custom message (defaults to original exception message)
        **kwargs: Additional parameters for wrapper class
        
    Returns:
        Wrapped exception
    """
    if isinstance(exception, HubError):
        return exception
    
    msg = message or str(exception)
    return wrapper_class(
        message=msg,
        original_exception=exception,
        **kwargs
    )


def create_error_context(**context: Any) -> Dict[str, Any]:
    """
    Create a standardized error context dictionary.
    
    Args:
        **context: Key-value pairs for context
        
    Returns:
        Standardized context dictionary
    """
    import time
    import traceback
    
    return {
        "timestamp": time.time(),
        "traceback": traceback.format_exc(),
        **context
    }
