# 📄 ФАЙЛ: src/layers/base/rag/vector_stores/faiss_store.py (исправленный)
"""
Реализация VectorStore для FAISS.
"""

import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import hashlib
import pickle
import os
import time
import tempfile
from concurrent.futures import ThreadPoolExecutor

from src.core.contracts import VectorStore, VectorDocument, SearchResult
from src.core.exceptions import VectorStoreError
from src.adapters.logging_adapter import get_logger
from src.core.accelerator import accelerator


class FAISSVectorStore(VectorStore):
    PREVIEW_MAX_CHARS: int = 512  # Store only a short preview, never full content
    """
    Локальное векторное хранилище на FAISS.
    Оптимизировано для Apple Silicon (MPS).
    """
    
    def __init__(self, index_path: str, dimension: int = 384):
        """
        Инициализация FAISS хранилища.
        
        Args:
            index_path: Путь к файлу индекса
            dimension: Размерность векторов
        """
        self._index_path = Path(index_path)
        self._dimension = dimension
        self._logger = get_logger()
        
        # Создаём директорию если нужно
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Загружаем или создаём индекс
        self._index = None
        self._document_store = {}  # id -> VectorDocument
        self._id_to_index = {}     # document_id -> faiss_index
        
        self._index_to_id = {}     # faiss_index -> document_id (reverse map)
        # Инициализация будет ленивой
        self._initialized = False
        # Write-lock for concurrent add/save operations (important on Win/Linux)
        self._write_lock = asyncio.Lock()
        # Single-thread executor for blocking FAISS IO (Win/Linux safe)
        self._executor = ThreadPoolExecutor(max_workers=1)
    
    # ============ РЕАЛИЗАЦИЯ КОНТРАКТНЫХ МЕТОДОВ ============
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Конфигурация хранилища."""
        if "index_path" in config:
            self._index_path = Path(config["index_path"])
        if "dimension" in config:
            self._dimension = config["dimension"]
        self._logger.info("FAISS store reconfigured", context=config)
    
    async def initialize(self) -> None:
        """Инициализация хранилища (ленивая)."""
        if not self._initialized:
            await self._initialize_faiss()
            self._initialized = True
    
    async def cleanup(self) -> None:
        """Очистка ресурсов."""
        if self._initialized:
            await self._save_index()
            # Best-effort cache cleanup (torch optional, centralized)
            accelerator.empty_cache()
            try:
                self._executor.shutdown(wait=True)
            except Exception as e:
                self._logger.warning(f"Executor shutdown failed: {e}")
            self._logger.info("FAISS store очищен")
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья хранилища."""
        status = "healthy" if self._index and self._initialized else "unhealthy"
        return {
            "status": status,
            "provider": "faiss",
            "vectors": self._index.ntotal if self._index else 0,
            "documents": len(self._document_store),
            "dimension": self._dimension,
            "initialized": self._initialized
        }
    
    def _make_preview(self, content: str | None) -> str:
        if not content:
            return ""
        if len(content) <= self.PREVIEW_MAX_CHARS:
            return content
        return content[: self.PREVIEW_MAX_CHARS]

    def _lighten_document(self, doc: VectorDocument) -> VectorDocument:
        """Return a lightweight copy: keep id/embedding/metadata + preview only."""
        return VectorDocument(
            id=doc.id,
            content=self._make_preview(getattr(doc, 'content', None)),
            metadata=dict(getattr(doc, 'metadata', {}) or {}),
            embedding=getattr(doc, 'embedding', None),
        )

    # ============ ОСНОВНЫЕ МЕТОДЫ ============
    
    async def _initialize_faiss(self):
        """Инициализация FAISS (ленивая загрузка)."""
        try:
            import faiss

            loop = asyncio.get_running_loop()

            if self._index_path.exists():
                # Загружаем существующий индекс
                self._logger.info(f"Загружаем FAISS индекс из {self._index_path}")
                meta_path = self._index_path.with_suffix('.meta.pkl')

                def _load_blocking():
                    idx = faiss.read_index(str(self._index_path))
                    docs = {}
                    id_to = {}
                    if meta_path.exists():
                        with open(meta_path, 'rb') as f:
                            data = pickle.load(f)
                            docs = data.get('documents', {})
                            id_to = data.get('id_to_index', {})
                    return idx, docs, id_to

                self._index, self._document_store, self._id_to_index = await loop.run_in_executor(self._executor, _load_blocking)
                
                # Sanitize loaded documents: ensure only preview is kept
                try:
                    sanitized = {}
                    for _did, _doc in (self._document_store or {}).items():
                        try:
                            sanitized[_did] = self._lighten_document(_doc)
                        except Exception:
                            # If something is weird/unpickleable, skip it
                            continue
                    self._document_store = sanitized
                except Exception:
                    pass

                # Build reverse map for O(1) lookup during search
                self._index_to_id = {int(v): k for k, v in (self._id_to_index or {}).items()}
                self._logger.info(f"Индекс загружен: {self._index.ntotal} векторов")
            else:
                # Создаём новый индекс
                self._logger.info(f"Создаём новый FAISS индекс (dim={self._dimension})")
                
                # Используем IndexFlatIP для косинусного сходства
                # (после нормализации векторов)
                self._index = faiss.IndexFlatIP(self._dimension)
                
                self._logger.info("Новый FAISS индекс создан")
                
        except ImportError as e:
            self._logger.error(f"FAISS не установлен: {e}")
            raise VectorStoreError(
                message="FAISS не установлен. Установите: pip install faiss-cpu",
                operation="initialize",
                details={"dimension": self._dimension}
            )
        except Exception as e:
            self._logger.error(f"Ошибка инициализации FAISS: {e}")
            raise
    
    @property
    def name(self) -> str:
        return "faiss"
    
    @property
    def dimensions(self) -> int:
        return self._dimension

    def _raise_dimension_mismatch(self, embedder_dimension: int, operation: str) -> None:
        raise VectorStoreError(
            message=f"FAISS dimension mismatch: index={self._dimension} embedder={embedder_dimension}",
            operation=operation,
            details={
                "index_dimension": self._dimension,
                "embedder_dimension": embedder_dimension,
            }
        )
    
    async def add_documents(
        self,
        documents: List[VectorDocument],
        embeddings: Optional[List[List[float]]] = None
    ) -> List[str]:
        """
        Добавляем документы в векторное хранилище.
        
        Args:
            documents: Список документов
            embeddings: Опциональные эмбеддинги
            
        Returns:
            Список ID добавленных документов
        """
        # Убедимся что инициализированы
        if not self._initialized:
            await self.initialize()
        
        if not documents:
            return []
        
        try:
            # Проверяем размерность
            if embeddings:
                for emb in embeddings:
                    if len(emb) != self._dimension:
                        self._raise_dimension_mismatch(len(emb), "add_documents")
            
            # Преобразуем эмбеддинги в numpy
            import faiss
            import numpy as np
            
            if embeddings:
                vectors = np.array(embeddings, dtype=np.float32)
            else:
                raise VectorStoreError(
                    message="Embeddings are required for add_documents()",
                    operation="add_documents",
                    details={"documents_count": len(documents)},
                )
            
            # Нормализуем векторы для косинусного сходства
            faiss.normalize_L2(vectors)
            
            # Добавляем в индекс + обновляем маппинги атомарно относительно других writer-операций
            async with self._write_lock:
                start_idx = self._index.ntotal
                self._index.add(vectors)
                
                # Сохраняем документы
                added_ids = []
                for i, doc in enumerate(documents):
                    doc_id = doc.id
                    
                    # Сохраняем документ
                    light = self._lighten_document(doc)
                    self._document_store[doc_id] = light
                    self._id_to_index[doc_id] = start_idx + i
                    self._index_to_id[start_idx + i] = doc_id
                    added_ids.append(doc_id)
                
                # Сохраняем индекс
                await self._save_index()
            
            self._logger.info(f"Добавлено {len(documents)} документов в FAISS")
            return added_ids
            
        except VectorStoreError:
            raise
        except Exception as e:
            self._logger.error(f"Ошибка добавления документов: {e}")
            raise VectorStoreError(
                message=f"Ошибка добавления документов: {str(e)}",
                operation="add_documents",
                details={"documents_count": len(documents)}
            )
    
    async def search(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True
    ) -> List[SearchResult]:
        """
        Поиск похожих документов.
        
        Args:
            query: Текстовый запрос
            query_embedding: Опциональный эмбеддинг запроса
            k: Количество результатов
            filter: Фильтр по метаданным
            include_metadata: Включать метаданные
            
        Returns:
            Список результатов поиска
        """
        # Убедимся что инициализированы
        if not self._initialized:
            await self.initialize()
        
        try:
            import faiss
            import numpy as np
            
            # Если эмбеддинг не предоставлен, нужно его получить
            if query_embedding is None:
                raise VectorStoreError(
                    message="query_embedding is required for search()",
                    operation="search",
                    details={"query_preview": (query[:80] if query else "")},
                )
            elif len(query_embedding) != self._dimension:
                self._raise_dimension_mismatch(len(query_embedding), "search")
            
            # Преобразуем и нормализуем
            query_vector = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_vector)
            
            # Если индекс пуст — возвращаем пустой результат (нормальное поведение)
            if not self._index or self._index.ntotal == 0 or k <= 0:
                self._logger.info("FAISS index is empty → 0 results")
                return []

            # Ищем
            # Ищем (в executor + timeout, чтобы не подвешивать event loop)
            loop = asyncio.get_running_loop()
            k_eff = min(k, self._index.ntotal)
            try:
                distances, indices = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: self._index.search(query_vector, k_eff)),
                    timeout=10.0,
                )
            except asyncio.TimeoutError:
                raise VectorStoreError(
                    message="Search timeout after 10 seconds",
                    operation="search",
                    details={"k": int(k_eff), "index_total": int(self._index.ntotal)},
                )

            
            # Формируем результаты
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx == -1:  # FAISS возвращает -1 если недостаточно данных
                    continue
                
                # Fast lookup by FAISS index
                doc_id = self._index_to_id.get(int(idx))
                
                if doc_id and doc_id in self._document_store:
                    doc = self._document_store[doc_id]
                    
                    # Применяем фильтр если есть
                    if filter and not self._matches_filter(doc, filter):
                        continue
                    
                    results.append(SearchResult(
                        document=doc,
                        score=float(distance),
                        distance=float(1.0 - distance)  # Преобразуем в расстояние
                    ))
            
            self._logger.info(f"Поиск '{query[:30]}...' → {len(results)} результатов")
            return results
            
        except VectorStoreError:
            raise
        except Exception as e:
            self._logger.error(f"Ошибка поиска: {e}")
            raise VectorStoreError(
                message=f"Ошибка поиска: {str(e)}",
                operation="search",
                details={"query": query[:200]},
            )
    
    def _matches_filter(self, doc: VectorDocument, filter: Dict[str, Any]) -> bool:
        """Проверяет документ по фильтру."""
        for key, value in filter.items():
            if key in doc.metadata:
                if doc.metadata[key] != value:
                    return False
            else:
                return False
        return True


    async def delete(self, document_ids: List[str]) -> int:
        """Удаление документов из хранилища (writer-safe)."""
        if not self._initialized:
            await self.initialize()

        if not document_ids:
            return 0

        async with self._write_lock:
            deleted = 0
            for doc_id in document_ids:
                if doc_id in self._document_store:
                    del self._document_store[doc_id]
                    index_id = self._id_to_index.pop(doc_id, None)
                    if index_id is not None:
                        self._index_to_id.pop(int(index_id), None)
                    deleted += 1

            if deleted > 0:
                await self._rebuild_index()
            return deleted

    async def _rebuild_index(self):
        """Перестраивает индекс после удаления документов (non-blocking)."""
        if not self._initialized:
            await self.initialize()

        # Snapshot for executor
        docs_snapshot = list((self._document_store or {}).items())
        loop = asyncio.get_running_loop()

        def _rebuild_blocking():
            import faiss
            import numpy as np

            vectors = []
            new_id_to_index = {}

            for doc_id, doc in docs_snapshot:
                emb = getattr(doc, "embedding", None)
                if emb:
                    vectors.append(emb)
                    new_id_to_index[doc_id] = len(vectors) - 1

            idx = faiss.IndexFlatIP(self._dimension)
            if vectors:
                vectors_array = np.array(vectors, dtype=np.float32)
                faiss.normalize_L2(vectors_array)
                idx.add(vectors_array)

            new_index_to_id = {int(v): k for k, v in new_id_to_index.items()}
            return idx, new_id_to_index, new_index_to_id

        self._index, self._id_to_index, self._index_to_id = await loop.run_in_executor(self._executor, _rebuild_blocking)
        await self._save_index()
    async def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """Получение документа по ID."""
        return (self._document_store or {}).get(document_id)
    async def update_metadata(self, document_id: str, metadata: Dict[str, Any]) -> bool:
        """Обновление метаданных документа (writer-safe)."""
        if not self._initialized:
            await self.initialize()

        async with self._write_lock:
            if document_id in (self._document_store or {}):
                self._document_store[document_id].metadata.update(metadata)
                await self._save_index()
                return True
        return False
    async def get_stats(self) -> Dict[str, Any]:
        """Получение статистики хранилища."""
        total_vectors = int(self._index.ntotal) if self._index else 0
        active_documents = len([
            d for d in (self._document_store or {}).values()
            if not (getattr(d, "metadata", {}) or {}).get("_deleted", False)
        ])
        return {
            "provider": "faiss",
            "total_documents": len(self._document_store),
            "total_vectors": total_vectors,
            "dimension": self._dimension,
            "index_path": str(self._index_path),
            "active_documents": active_documents,
            "initialized": self._initialized,
        }
    async def _save_index(self):
        """Сохраняет индекс и метаданные (atomic, non-blocking)."""
        if not self._index:
            return
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(self._executor, self._save_index_blocking)

    def _save_index_blocking(self):
        import faiss

        # Ensure dir exists
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path = self._index_path.with_suffix(".meta.pkl")

        def _atomic_replace(src: Path, dst: Path):
            os.replace(str(src), str(dst))

        def _write_temp_path(dst: Path) -> Path:
            ts = int(time.time() * 1000)
            return dst.with_name(dst.name + f".tmp.{os.getpid()}.{ts}")

        def _retry(op, attempts: int = 3):
            delay = 0.05
            last = None
            for _ in range(attempts):
                try:
                    return op()
                except PermissionError as e:
                    last = e
                    time.sleep(delay)
                    delay *= 2
            if last:
                raise last

        # 1) Write index atomically
        tmp_index = _write_temp_path(self._index_path)

        def _write_index():
            faiss.write_index(self._index, str(tmp_index))
            _atomic_replace(tmp_index, self._index_path)

        _retry(_write_index)

        # 2) Write meta atomically
        tmp_meta = _write_temp_path(meta_path)

        def _write_meta():
            with open(tmp_meta, "wb") as f:
                pickle.dump({"documents": self._document_store, "id_to_index": self._id_to_index}, f)
            _atomic_replace(tmp_meta, meta_path)

        _retry(_write_meta)

        self._logger.debug(f"Индекс сохранён: {self._index_path}")
