from __future__ import annotations

from typing import List

from src.adapters.embedding import get_embedding_factory


class QueryEmbedder:
    """
    Produces embedding vector for a query text using existing embedding factory.
    """

    def __init__(self, provider_type: str = "sentence_transformer"):
        self.provider_type = provider_type
        self._model = None

    async def _get_model(self):
        if self._model is None:
            factory = get_embedding_factory()
            self._model = await factory.create_embedding_model(provider_type=self.provider_type)
        return self._model

    async def embed_query(self, query: str) -> List[float]:
        model = await self._get_model()

        if hasattr(model, "embed_query"):
            return await model.embed_query(query)  # type: ignore[attr-defined]

        vectors = await model.embed_documents([query])
        return vectors[0]
