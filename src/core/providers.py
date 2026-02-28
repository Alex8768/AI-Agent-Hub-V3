from __future__ import annotations

"""Providers facade (stable public API).

Keep this module stable for imports across the codebase:
    from src.core.providers import get_vector_store, get_authorizer, ...

Concrete implementations live in src.core.providers_parts/*.
"""

from src.core.providers_parts.contracts import (
    Authorizer,
    MemoryStore,
    GraphStoreAPI,
    NoopAuthorizer,
    NoopMemoryStore,
)

from src.core.providers_parts.db_wrappers import (
    DBBackedGraphStore,
    DBBackedMemoryStore,
)

from src.core.providers_parts.facade import (
    get_vector_store,
    get_authorizer,
    get_memory_store,
    get_graph_store,
    get_reasoning_engine,
)
