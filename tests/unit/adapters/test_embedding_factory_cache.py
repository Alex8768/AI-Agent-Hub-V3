import pytest

from src.adapters.embedding import get_embedding_factory


@pytest.mark.asyncio
async def test_embedding_factory_caches_same_config():
    factory = get_embedding_factory()

    m1 = await factory.create_embedding_model("sentence_transformer")
    m2 = await factory.create_embedding_model("sentence_transformer")

    # must be same instance (cache hit)
    assert m1 is m2

    cached = factory.get_cached_models()
    assert isinstance(cached, list)
    assert len(cached) >= 1
