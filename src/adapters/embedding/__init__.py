# 📄 ФАЙЛ: src/adapters/embedding/__init__.py
"""
Embedding adapters for AI Agent Hub V3.
ARCHITECTURE_V3: Adapters Layer - Embedding Providers
"""

from src.adapters.embedding.sentence_transformer_adapter import (
    SentenceTransformerAdapter,
)
from src.adapters.embedding.embedding_factory import (
    EmbeddingFactoryImpl,
    get_embedding_factory,
    get_embedding_model,
)

__all__ = [
    # Adapters
    "SentenceTransformerAdapter",
    
    # Factory
    "EmbeddingFactoryImpl",
    "get_embedding_factory",
    "get_embedding_model",
]