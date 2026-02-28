"""
Core contracts (abstract interfaces) for AI Agent Hub V3.
Defines the architectural boundaries between components.
ARCHITECTURE_V3: Core Layer - Contracts and Interfaces
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator
from dataclasses import dataclass

from src.core.types.types import Message

# NOTE: Compatibility barrel. Definitions live in _parts/*.
# Keep external imports stable: from src.core.contracts import X

from ._parts.common import *  # noqa: F401,F403
from ._parts.embeddings import *  # noqa: F401,F403
from ._parts.llm import *  # noqa: F401,F403
from ._parts.vector_store import *  # noqa: F401,F403
from ._parts.mcp import *  # noqa: F401,F403
from ._parts.agent import *  # noqa: F401,F403
from ._parts.workspace import *  # noqa: F401,F403
from ._parts.misc import *  # noqa: F401,F403
