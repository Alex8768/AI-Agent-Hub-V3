from __future__ import annotations

import pytest

from src.core.providers import get_authorizer, get_memory_store, NoopAuthorizer, NoopMemoryStore


def test_providers_defaults_are_noop():
    assert isinstance(get_authorizer(), NoopAuthorizer)
    assert isinstance(get_memory_store(), NoopMemoryStore)


@pytest.mark.asyncio
async def test_vector_store_provider_default_works():
    # This should not raise; it should route to Base FAISS singleton.
    from src.core.providers import get_vector_store
    store = await get_vector_store()
    assert store is not None
