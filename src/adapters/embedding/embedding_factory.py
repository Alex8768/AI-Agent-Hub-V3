"""
Embedding Factory for AI Agent Hub V3.
ARCHITECTURE_V3: Adapters Layer - Embedding Factory
"""

from __future__ import annotations

from typing import Dict, Type, Optional, List, Any
import hashlib
import json

from src.core.contracts import EmbeddingModel, EmbeddingFactory
from src.core.exceptions import ConfigurationError
from src.core.config import settings
from src.adapters.logging_adapter import get_logger


def _is_mps_available() -> bool:
    try:
        import torch
        return bool(getattr(torch.backends, "mps", None) and torch.backends.mps.is_available())
    except Exception:
        return False


class EmbeddingFactoryImpl(EmbeddingFactory):
    _instance: Optional["EmbeddingFactoryImpl"] = None
    _instances: Dict[str, EmbeddingModel] = {}
    _providers: Dict[str, Type[EmbeddingModel]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._logger = get_logger()
            self._initialize_providers()
            self._initialized = True

    def _initialize_providers(self) -> None:
        try:
            from .sentence_transformer_adapter import SentenceTransformerAdapter
            self._providers["sentence_transformer"] = SentenceTransformerAdapter
            self._providers["local"] = SentenceTransformerAdapter
            self._logger.info("Registered Sentence Transformer provider")
        except ImportError:
            self._logger.warning("Sentence Transformer provider not available")

    def _get_default_config(self, provider_type: str) -> Dict[str, Any]:
        if provider_type in ["sentence_transformer", "local"]:
            device = getattr(settings, "embedding_device", None) or ("mps" if _is_mps_available() else "cpu")
            return {
                "model_name": getattr(settings, "embedding_model", "paraphrase-multilingual-MiniLM-L12-v2"),
                "device": device,
            }
        return {}

    async def create_embedding_model(
        self,
        provider_type: str,
        config: Optional[Dict[str, Any]] = None
    ) -> EmbeddingModel:
        provider_type = provider_type.lower()
        if provider_type not in self._providers:
            raise ConfigurationError(message=f"Unsupported provider: {provider_type}")

        merged_config = self._get_default_config(provider_type)
        if config:
            merged_config.update(config)

        # cache key (stable)
        config_hash = hashlib.md5(
            json.dumps(merged_config, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()[:8]
        cache_key = f"{provider_type}:{config_hash}"

        if cache_key in self._instances:
            return self._instances[cache_key]

        provider_class = self._providers[provider_type]
        instance = provider_class(**merged_config)
        self._instances[cache_key] = instance
        return instance

    async def get_available_providers(self) -> List[str]:
        return list(self._providers.keys())
    def get_cached_models_legacy(self) -> Dict[str, str]:
        """Backward-compatible cached model map (cache_key -> class name)."""
        return {k: type(v).__name__ for k, v in self._instances.items()}

    def get_cached_models(self) -> List[Dict[str, Any]]:
        """Structured cache introspection for health/observability."""
        out: List[Dict[str, Any]] = []
        for cache_key, inst in self._instances.items():
            # cache_key format: provider_type:hash
            provider_type = cache_key.split(":", 1)[0] if ":" in cache_key else cache_key
            info: Dict[str, Any] = {
                "cache_key": cache_key,
                "provider_type": provider_type,
                "class_name": type(inst).__name__,
            }

            # Best-effort introspection (adapter-dependent)
            for attr, key in [
                ("model_name", "model_name"),
                ("device", "device"),
                ("dimensions", "dimensions"),
                ("name", "name"),
            ]:
                try:
                    val = getattr(inst, attr)
                    # properties may raise / be non-serializable
                    if callable(val):
                        val = val()
                    info[key] = val
                except Exception:
                    pass

            out.append(info)
        return out

    async def cleanup_all(self) -> None:
        for model in list(self._instances.values()):
            await model.cleanup()
        self._instances.clear()


def get_embedding_factory() -> EmbeddingFactoryImpl:
    """Global access to embedding factory (Singleton)."""
    return EmbeddingFactoryImpl()


async def get_embedding_model(
    provider_type: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> EmbeddingModel:
    """Convenience function to get model directly."""
    if provider_type is None:
        provider_type = "sentence_transformer"
    factory = get_embedding_factory()
    return await factory.create_embedding_model(provider_type, config)
