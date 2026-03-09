"""
Ingest Service для AI Agent Hub V3.
ARCHITECTURE_V3: Services Layer - Document Ingestion
Оптимизирован для работы на MacBook M4 с MPS.
"""

import asyncio
import re
import uuid
import time
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from src.core.contracts import VectorStore, VectorDocument, EmbeddingModel
from src.core.config import settings
from src.core.accelerator import accelerator
from src.adapters.embedding import get_embedding_factory
from src.adapters.logging_adapter import get_logger
from src.core.exceptions import (
    ValidationError,
    EmbeddingError,
    VectorStoreError,
    wrap_exception
)
from src.services.document.ocr import (
    NoopOCRProvider,
    OCRProvider,
    build_ocr_quality_summary,
    run_ocr_provider,
)


class ChunkingStrategy(str, Enum):
    """Стратегии разбиения текста на чанки."""
    RECURSIVE_CHARACTER = "recursive_character"
    FIXED_SIZE = "fixed_size"


class DocumentFormat(str, Enum):
    """Поддерживаемые форматы документов."""
    TXT = "txt"
    MD = "md"
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    UNKNOWN = "unknown"


@dataclass
class Chunk:
    """Структура чанка документа."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None


@dataclass
class IngestResult:
    """Результат обработки документа (полная версия для отладки)."""
    document_id: str
    filename: str
    format: DocumentFormat
    total_chunks: int
    success: bool
    errors: List[str]
    chunk_ids: List[str]
    processing_time_ms: int
    vector_store_stats: Dict[str, Any]
    metadata: Dict[str, Any]


class RecursiveCharacterChunker:
    """
    Улучшенный рекурсивный чанкер для русского языка.
    Гарантирует соблюдение размера чанка.
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Разделители для русского языка в порядке приоритета
        self.separators = [
            "\n\n",        # Двойной перевод строки
            "\n",          # Перевод строки
            ". ",          # Конец предложения (точка с пробелом)
            "! ",          # Восклицательный знак
            "? ",          # Вопросительный знак
            "; ",          # Точка с запятой
            ", ",          # Запятая
            " ",           # Пробел
            ""             # Любой символ (последний вариант)
        ]
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Chunk]:
        """Разбивает текст на чанки с сохранением семантических границ."""
        if not text or len(text.strip()) == 0:
            return []
        
        # Очистка текста
        text = self._clean_text(text)
        
        # Рекурсивное разбиение
        chunks_content = self._split_recursively(text)
        
        # Создание объектов Chunk
        chunks = []
        for i, content in enumerate(chunks_content):
            if not content.strip():
                continue
                
            chunk_metadata = metadata.copy()
            chunk_metadata.update({
                "chunk_id": str(uuid.uuid4()),
                "chunk_index": i,
                "total_chunks": len(chunks_content),
                "char_count": len(content),
                "word_count": len(content.split()),
            })
            
            chunks.append(Chunk(
                id=chunk_metadata["chunk_id"],
                content=content,
                metadata=chunk_metadata
            ))
        
        return chunks
    
    def _split_recursively(self, text: str) -> List[str]:
        """Рекурсивное разбиение текста."""
        # Базовый случай: текст достаточно короткий
        if len(text) <= self.chunk_size:
            return [text] if text.strip() else []
        
        # Пробуем найти лучший разделитель
        for separator in self.separators:
            if separator:
                # Ищем разделитель в пределах чанка
                split_pos = text.rfind(separator, 0, self.chunk_size)
                if split_pos != -1 and split_pos > 0:
                    # Нашли разделитель - разбиваем
                    left_part = text[:split_pos + len(separator)].rstrip()
                    right_part = text[split_pos + len(separator):].lstrip()
                    
                    # Рекурсивно разбиваем правую часть
                    result = [left_part]
                    if right_part:
                        result.extend(self._split_recursively(right_part))
                    return result
        
        # Если не нашли разделитель, принудительно разбиваем по размеру
        # но пытаемся найти пробел
        split_pos = text.rfind(' ', 0, self.chunk_size)
        if split_pos != -1 and split_pos > 0:
            left_part = text[:split_pos].rstrip()
            right_part = text[split_pos:].lstrip()
        else:
            # Принудительное разбиение
            left_part = text[:self.chunk_size].rstrip()
            right_part = text[self.chunk_size:].lstrip()
        
        result = [left_part]
        if right_part:
            result.extend(self._split_recursively(right_part))
        return result
    
    def _clean_text(self, text: str) -> str:
        """Очистка текста от лишних пробелов и непечатаемых символов."""
        # Заменяем множественные пробелы на один
        text = re.sub(r'\s+', ' ', text)
        # Удаляем непечатаемые символы, кроме стандартных
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
        return text.strip()


class IngestService:
    """
    Сервис для загрузки документов.
    Интегрирует чанкинг, эмбеддинги и векторное хранилище.
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        embedding_model: Optional[EmbeddingModel] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        ocr_provider: Optional[OCRProvider] = None,
        ocr_min_confidence: float = 0.6,
        ocr_min_coverage: float = 0.7,
    ):
        """
        Инициализация с инъекцией зависимостей.
        
        Args:
            vector_store: Векторное хранилище (FAISS)
            embedding_model: Модель эмбеддингов (если не передана, создаётся через фабрику)
            chunk_size: Размер чанка в символах
            chunk_overlap: Перекрытие чанков
        """
        self._vector_store = vector_store
        self.vector_store = vector_store
        self._embedding_model = embedding_model
        self.chunker = RecursiveCharacterChunker(chunk_size, chunk_overlap)
        self._logger = get_logger()
        self._ocr_provider = ocr_provider or NoopOCRProvider()
        self._ocr_min_confidence = float(ocr_min_confidence)
        self._ocr_min_coverage = float(ocr_min_coverage)
        
        self._logger.info(
            "IngestService инициализирован",
            context={
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "vector_store": vector_store.name if hasattr(vector_store, 'name') else "FAISS",
                "embedding_model_provided": embedding_model is not None,
                "ocr_provider": getattr(self._ocr_provider, "name", "noop"),
            }
        )
    
    async def _get_embedding_model(self) -> EmbeddingModel:
        """Возвращает модель эмбеддингов (свою или создаёт через фабрику)."""
        if self._embedding_model is not None:
            return self._embedding_model
        
        # Fallback для обратной совместимости
        factory = get_embedding_factory()
        return await factory.create_embedding_model("sentence_transformer")
    
    async def ingest_text(
        self,
        text: str,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None,
        source_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = None,
    ) -> IngestResult:
        """
        Основной метод обработки текста.
        
        Args:
            text: Текст для обработки
            filename: Имя файла
            metadata: Дополнительные метаданные
            document_id: ID документа (если None, генерируется)
            
        Returns:
            Результат обработки
        """
        start_time = time.time()
        document_id = document_id or str(uuid.uuid4())
        errors = []
        chunk_ids = []
        chunks = []  # инициализируем заранее
        
        try:
            # 1-2. Определение формата + подготовка метаданных
            format, final_metadata = self._prepare_ingest_metadata_boundary(
                metadata=metadata or {},
                filename=filename,
                text_length=len(text),
                document_id=document_id,
            )
            # 3. OCR ветка для image/pdf, если есть бинарный контент
            runtime_text, ocr_diag = await self._maybe_apply_ocr_boundary(
                text=text,
                filename=filename,
                format=format,
                document_id=document_id,
                source_bytes=source_bytes,
                mime_type=mime_type,
            )
            if ocr_diag:
                diagnostics = dict(final_metadata.get("diagnostics", {}) or {})
                diagnostics["ocr"] = dict(ocr_diag)
                final_metadata["diagnostics"] = diagnostics
                final_metadata["ocr_used"] = bool(ocr_diag.get("ocr_used", False))
            # 4. Валидация текста после OCR ветки
            await self._validate_text(runtime_text)
            
            # 5. Чанкинг
            chunks = self._chunk_text_boundary(
                text=runtime_text,
                filename=filename,
                final_metadata=final_metadata,
            )
            
            # 6. Генерация эмбеддингов (оптимизация для M4)
            self._logger.info(f"Генерация эмбеддингов для {len(chunks)} чанков")
            chunks = await self._generate_embeddings_batch(chunks)
            
            # 7. Подготовка VectorDocument
            vector_docs = self._prepare_vector_documents(chunks, document_id)

            # 8. Сохранение в векторное хранилище
            saved_ids = await self._persist_vectors_boundary(
                vector_docs=vector_docs,
            )
            chunk_ids.extend(saved_ids)
            
            # 9. Статистика
            store_stats = await self.vector_store.get_stats()
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            result = IngestResult(
                document_id=document_id,
                filename=filename,
                format=format,
                total_chunks=len(chunks),
                success=True,
                errors=errors,
                chunk_ids=chunk_ids,
                processing_time_ms=processing_time_ms,
                vector_store_stats=store_stats,
                metadata=final_metadata
            )
            
            self._logger.info(
                f"Документ обработан: {filename}",
                context={
                    "document_id": document_id,
                    "chunks": len(chunks),
                    "time_ms": processing_time_ms
                }
            )
            
            return result
        except ValidationError as e:
            # Base: validation errors should bubble up (bad input)
            error_msg = f"Ошибка валидации {filename}: {str(e)}"
            self._logger.error(error_msg)
            raise

        except Exception as e:
            error_msg = f"Ошибка обработки {filename}: {str(e)}"
            self._logger.error(error_msg)
            # Best-effort rollback to avoid partial vector writes
            # Prefer known ids from prepared vector_docs if store failed before returning saved_ids
            rollback_ids = chunk_ids
            if (not rollback_ids) and ('vector_docs' in locals()) and vector_docs:
                try:
                    rollback_ids = [d.id for d in vector_docs]
                except Exception:
                    rollback_ids = chunk_ids
            await self._rollback_vectors(rollback_ids, document_id=document_id)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Пытаемся сохранить максимум информации
            chunks_count = len(chunks) if chunks else 0
            meta = final_metadata if 'final_metadata' in locals() and final_metadata else (metadata or {})
            
            return IngestResult(
                document_id=document_id,
                filename=filename,
                format=self._detect_format(filename),
                total_chunks=chunks_count,
                success=False,
                errors=[error_msg],
                chunk_ids=[],
                processing_time_ms=processing_time_ms,
                vector_store_stats={},
                metadata=meta
            )
            
    async def _maybe_apply_ocr_boundary(
        self,
        *,
        text: str,
        filename: str,
        format: DocumentFormat,
        document_id: str,
        source_bytes: bytes | None,
        mime_type: str | None,
    ) -> tuple[str, Dict[str, Any]]:
        """Run OCR branch for image/pdf inputs and return updated text + diagnostics."""
        detected_mime = str(mime_type or self._detect_mime_type(filename) or "")
        should_use_ocr = bool(source_bytes) and (
            detected_mime.startswith("image/")
            or detected_mime == "application/pdf"
            or format == DocumentFormat.PDF
        )
        if not should_use_ocr:
            return text, {}

        outcome = await run_ocr_provider(
            provider=self._ocr_provider,
            document_id=document_id,
            content_bytes=bytes(source_bytes or b""),
            mime_type=detected_mime,
        )
        quality = build_ocr_quality_summary(
            extraction_result=dict(outcome.get("result", {}) or {}),
            min_confidence=self._ocr_min_confidence,
            min_coverage=self._ocr_min_coverage,
        )
        extracted_text = str(dict(outcome.get("result", {}) or {}).get("combined_text", "") or "")
        merged_text = extracted_text if extracted_text else text
        diagnostics: Dict[str, Any] = {
            "ocr_used": True,
            "provider": str(outcome.get("provider", "") or ""),
            "ok": bool(outcome.get("ok", False)),
            "mime_type": detected_mime,
            "result_pages": int(dict(outcome.get("result", {}) or {}).get("total_pages", 0) or 0),
            "quality": dict(quality),
            "error": dict(outcome.get("error", {}) or {}) if outcome.get("error") else None,
        }
        return merged_text, diagnostics

    def _prepare_ingest_metadata_boundary(
        self,
        *,
        metadata: Dict[str, Any],
        filename: str,
        text_length: int,
        document_id: str,
    ) -> tuple[DocumentFormat, Dict[str, Any]]:
        """Build ingest format + metadata in one boundary."""
        format = self._detect_format(filename)
        final_metadata = self._prepare_metadata(
            metadata,
            filename,
            format,
            text_length,
            document_id,
        )
        return format, final_metadata

    def _chunk_text_boundary(
        self,
        *,
        text: str,
        filename: str,
        final_metadata: Dict[str, Any],
    ) -> List[Chunk]:
        """Run chunking with validation in one boundary."""
        self._logger.info(f"Чанкинг документа: {filename}")
        chunks = self.chunker.chunk_text(text, final_metadata)

        if not chunks:
            raise ValidationError(
                message="Текст не содержит значимого контента",
                field="text",
                value=text[:100] + "..." if len(text) > 100 else text
            )
        return chunks


    async def _rollback_vectors(self, chunk_ids: list[str], *, document_id: str | None = None) -> None:
        """Best-effort rollback for partially ingested vectors.

        Base policy: avoid leaving partial vectors after a failed ingest.
        Uses duck-typing to support different VectorStore implementations.
        """
        if (not chunk_ids) and (not document_id):
            return

        store = getattr(self, "_vector_store", None)
        if store is None:
            store = getattr(self, "vector_store", None)
        if store is None:
            return

        try:
            # Prefer document-level delete if available
            if document_id and hasattr(store, "delete_by_document_id"):
                await store.delete_by_document_id(document_id)
                return

            # Otherwise delete by ids if supported
            if chunk_ids:
                if hasattr(store, "delete_documents"):
                    await store.delete_documents(chunk_ids)
                    return
                if hasattr(store, "delete"):
                    await store.delete(chunk_ids)
                    return

            self._logger.warning(
                "Vector rollback skipped: store has no delete API",
                context={
                    "document_id": document_id,
                    "count": len(chunk_ids),
                    "sample": chunk_ids[:5],
                    "store_type": type(store).__name__,
                    "has_delete_by_document_id": bool(hasattr(store, "delete_by_document_id")),
                    "has_delete_documents": bool(hasattr(store, "delete_documents")),
                    "has_delete": bool(hasattr(store, "delete")),
                },
            )
        except Exception as e:
            # Rollback must never mask original error.
            self._logger.warning(
                f"Vector rollback failed: {e}",
                context={"document_id": document_id, "count": len(chunk_ids), "sample": chunk_ids[:5]},
            )

    async def _validate_text(self, text: str) -> None:
        """Валидация текста."""
        if not text or not text.strip():
            raise ValidationError(
                message="Текст не может быть пустым",
                field="text"
            )
        
        if len(text) > 10_000_000:  # 10MB
            raise ValidationError(
                message="Текст слишком большой (>10MB)",
                field="text",
                value=f"{len(text)} bytes"
            )
    
    def _detect_format(self, filename: str) -> DocumentFormat:
        """Определение формата по расширению."""
        ext = Path(filename).suffix.lower()
        
        format_map = {
            '.txt': DocumentFormat.TXT,
            '.md': DocumentFormat.MD,
            '.pdf': DocumentFormat.PDF,
            '.docx': DocumentFormat.DOCX,
            '.doc': DocumentFormat.DOCX,
            '.html': DocumentFormat.HTML,
            '.htm': DocumentFormat.HTML,
        }
        
        return format_map.get(ext, DocumentFormat.UNKNOWN)

    def _detect_mime_type(self, filename: str) -> str:
        ext = Path(filename).suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".tiff": "image/tiff",
            ".pdf": "application/pdf",
        }
        return mime_map.get(ext, "")
    
    def _prepare_metadata(
        self,
        metadata: Dict[str, Any],
        filename: str,
        format: DocumentFormat,
        text_length: int,
        document_id: str
    ) -> Dict[str, Any]:
        """Подготовка полных метаданных."""
        final_metadata = metadata.copy()
        final_metadata.update({
            "filename": filename,
            "format": format.value,
            "text_length": text_length,
            "document_id": document_id,
            "timestamp": time.time(),
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "platform": "MacBook M4"
        })
        # Base: workspace_id must always exist
        final_metadata.setdefault("workspace_id", "default")
        return final_metadata
    
    async def _generate_embeddings_batch(self, chunks: List[Chunk], batch_size: int | None = None) -> List[Chunk]:
        """Генерация эмбеддингов для чанков батчами (защита от OOM на больших документах).

        Returns:
            List[Chunk]: чанки с эмбеддингами

        Raises:
            EmbeddingError: если не удалось сгенерировать эмбеддинги
        """
        try:
            model = await self._get_embedding_model()

            total = len(chunks)
            # Resolve batch size (auto by default, overridable via settings.EMBEDDING_BATCH_SIZE)
            if batch_size is None:
                base = int(getattr(settings, 'embedding_batch_size', None) or 32)
                batch_size = accelerator.recommended_batch_size(base=base)

            if total == 0:
                return []

            result_chunks: List[Chunk] = []

            for start in range(0, total, batch_size):
                batch = chunks[start : start + batch_size]
                texts = [c.content for c in batch]

                self._logger.info(
                    "Embedding batch",
                    context={
                        "start": start,
                        "end": min(start + batch_size, total),
                        "total": total,
                        "batch_size": len(batch),
                    },
                )

                embeddings = await model.embed_documents(texts)
                try:
                    if len(embeddings) != len(batch):
                        raise EmbeddingError(
                            message=f"Embedding count mismatch: expected {len(batch)}, got {len(embeddings)}"
                        )

                    for i, chunk in enumerate(batch):
                        # Keep content as-is for downstream logic; embedding is attached.
                        result_chunks.append(
                            Chunk(
                                id=chunk.id,
                                content=chunk.content,
                                metadata=chunk.metadata.copy(),
                                embedding=embeddings[i],
                            )
                        )
                finally:
                    # Release batch embeddings ASAP (important for MPS/unified memory)
                    try:
                        del embeddings
                    except Exception:
                        pass
                    # Unified cache cleanup (cuda/mps/no-op)
                    accelerator.empty_cache()
            self._logger.info(
            "Эмбеддинги сгенерированы",
            context={
            "chunks": len(result_chunks),
            "dimensions": len(result_chunks[0].embedding) if result_chunks and result_chunks[0].embedding else 0,
            "batch_size": batch_size,
            },
            )
            return result_chunks

        except Exception as e:
            wrapped = wrap_exception(
                e,
                EmbeddingError,
                message="Embedding failed",
                details={
                    "chunks_count": len(chunks),
                    "batch_size": batch_size,
                    "error_type": type(e).__name__,
                },
            )
            raise wrapped from e
    def _prepare_vector_documents(
        self,
        chunks: List[Chunk],
        document_id: str
    ) -> List[VectorDocument]:
        """Подготовка объектов для векторного хранилища."""
        vector_docs = []
        
        for chunk in chunks:
            chunk_metadata = chunk.metadata.copy()
            chunk_metadata["document_id"] = document_id
            # workspace_id берется из metadata (если есть) или "default"
            if "workspace_id" not in chunk_metadata:
                chunk_metadata["workspace_id"] = "default"
            
            vector_doc = VectorDocument(
                id=chunk.id,
                content=chunk.content,
                embedding=chunk.embedding,
                metadata=chunk_metadata
            )
            
            vector_docs.append(vector_doc)
        
        return vector_docs

    async def _persist_vectors_boundary(
        self,
        *,
        vector_docs: List[VectorDocument],
    ) -> List[str]:
        """Persist prepared vector docs as one boundary."""
        self._logger.info("Сохранение в векторное хранилище")
        saved_ids = await self._save_to_vector_store(vector_docs)
        return saved_ids
    
    async def _save_to_vector_store(
        self,
        vector_docs: List[VectorDocument]
    ) -> List[str]:
        """Сохранение в векторное хранилище."""
        try:
            missing_embeddings = [doc.id for doc in vector_docs if doc.embedding is None]
            if missing_embeddings:
                self._logger.error(
                    "Эмбеддинги не сгенерированы для части чанков; ingest остановлен",
                    context={
                        "missing_count": len(missing_embeddings),
                        "total_chunks": len(vector_docs),
                        "missing_ids_sample": missing_embeddings[:5],
                    }
                )
                raise EmbeddingError(
                    message=f"Embeddings missing for {len(missing_embeddings)} chunks"
                )

            embeddings = [doc.embedding for doc in vector_docs]
            
            saved_ids = await self._vector_store.add_documents(
                documents=vector_docs,
                embeddings=embeddings
            )
            
            return saved_ids
            
        except Exception as e:
            wrapped = wrap_exception(
                e,
                VectorStoreError,
                message="Ошибка сохранения в векторное хранилище",
                details={
                    "documents_count": len(vector_docs),
                    "error": str(e)
                }
            )
            raise wrapped from e
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья сервиса."""
        try:
            store_health = await self._vector_store.health_check()
            
            return {
                "status": "healthy" if store_health.get("status") == "healthy" else "degraded",
                "ingest_service": "operational",
                "vector_store": store_health,
                "chunker": {
                    "strategy": "recursive_character",
                    "operational": True
                },
                "platform": "MacBook M4"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "service": "ingest_service"
            }
