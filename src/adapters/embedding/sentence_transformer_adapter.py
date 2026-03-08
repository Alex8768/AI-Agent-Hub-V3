"""
Sentence Transformer Embedding Adapter for AI Agent Hub V3.
Supports Apple M4 (MPS), CUDA, and CPU with automatic device detection.
"""
import asyncio
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from src.core.accelerator import accelerator

from src.core.config import settings

from src.core.contracts import EmbeddingModel
from src.core.exceptions import EmbeddingError, ConfigurationError
from src.adapters.logging_adapter import get_logger


class SentenceTransformerAdapter(EmbeddingModel):
    """
    Local embedding model using Sentence Transformers.
    Optimized for Apple Silicon with MPS acceleration.
    """

    def __init__(
        self,
        model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
        device: Optional[str] = None,
        cache_folder: Optional[str] = None,
        max_workers: int = 4
    ):
        self._model_name = model_name
        self._cache_folder = cache_folder
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._logger = get_logger()

        # Auto device selection (single source of truth) with override via settings.DEVICE
        if device:
            self._device = device
        else:
            pref = getattr(settings, "device", "auto") or "auto"
            self._device = pref if pref != "auto" else accelerator.device

        self._model = None
        self._dimensions = None  # будет определено при загрузке модели
        self._logger.info(f"SentenceTransformerAdapter initialized on {self._device}")

    def _get_model(self):
        """Lazy model load with strict offline enforcement (no HF network)."""
        if self._model is None:
            # sentence-transformers imports torch internally; keep adapter lazy, but fail clearly if used.
            if not accelerator.torch_available:
                raise ConfigurationError(
                    message=(
                        "SentenceTransformer embedding requires torch + sentence-transformers. "
                        "Install torch (and sentence-transformers) or use a non-torch embedder."
                    )
                )
            import os

            # Resolve HF cache dir
            hf_home = getattr(settings, "hf_home", None)
            if hf_home:
                hf_home_abs = str(Path(hf_home).resolve())
                hub_cache = str(Path(hf_home_abs, "hub"))
                transformers_cache = str(Path(hf_home_abs, "transformers"))

                os.environ["HF_HOME"] = hf_home_abs
                os.environ["HF_HUB_CACHE"] = hub_cache
                os.environ["TRANSFORMERS_CACHE"] = transformers_cache

                # SentenceTransformers uses cache_folder as cache root
                self._cache_folder = hub_cache

            os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1" if getattr(settings, "hf_hub_disable_telemetry", False) else "0"
            os.environ["HF_HUB_OFFLINE"] = "1" if getattr(settings, "hf_hub_offline", False) else "0"
            os.environ["TRANSFORMERS_OFFLINE"] = "1" if getattr(settings, "transformers_offline", False) else "0"

            offline = bool(getattr(settings, "hf_hub_offline", False) or getattr(settings, "transformers_offline", False))

            # Import AFTER env is applied (prevents HF Hub network lookups)
            try:
                from sentence_transformers import SentenceTransformer
            except Exception as e:
                raise ConfigurationError(
                    message=(
                        "sentence-transformers is not available (or torch backend is missing). "
                        "Install required dependencies for local embeddings."
                    )
                ) from e

            self._model = SentenceTransformer(
                self._model_name,
                device=self._device,
                cache_folder=self._cache_folder,
                local_files_only=offline,
            )
            # Определяем реальную размерность модели
            self._dimensions = self._model.get_sentence_embedding_dimension()
        return self._model

    @property
    def name(self) -> str:
        return f"sentence_transformer_{self._model_name}"

    @property
    def dimensions(self) -> int:
        if self._dimensions is None:
            # Загружаем модель, чтобы узнать размерность
            self._get_model()
        return self._dimensions

    @property
    def max_tokens(self) -> int:
        return 512

    async def embed_query(self, text: str) -> List[float]:
        loop = asyncio.get_running_loop()
        model = self._get_model()
        embedding = await loop.run_in_executor(
            self._executor,
            lambda: model.encode(text, convert_to_numpy=True).tolist()
        )
        return embedding

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        loop = asyncio.get_running_loop()
        model = self._get_model()
        embeddings = await loop.run_in_executor(
            self._executor,
            lambda: model.encode(texts, convert_to_numpy=True).tolist()
        )
        return embeddings

    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy",
            "device": self._device,
            "model": self._model_name,
            "dimensions": self.dimensions,
        }

    def configure(self, config: Dict[str, Any]) -> None:
        pass

    def clear_cache(self) -> None:
        if self._model:
            accelerator.empty_cache()

    async def cleanup(self) -> None:
        self._executor.shutdown(wait=True)
