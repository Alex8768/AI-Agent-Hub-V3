"""
Dependencies package facade.

Implementations live in: src/api/dependencies_impl.py
This package re-exports them for stable imports:
    from src.api.dependencies import get_current_user, get_workspace
"""

from src.api.dependencies_impl import get_current_user, get_workspace

__all__ = ["get_current_user", "get_workspace"]
