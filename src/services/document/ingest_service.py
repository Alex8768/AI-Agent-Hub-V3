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

from src.core.contracts import VectorStore, VectorDocument
from src.adapters.embedding import get_embedding_factory
from src.adapters.logging_adapter import get_logger
from src.core.exceptions import (
    ValidationError,
    EmbeddingError,
    VectorStoreError,
    wrap_exception
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
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Инициализация с инъекцией зависимостей.
        
        Args:
            vector_store: Векторное хранилище (FAISS)
            chunk_size: Размер чанка в символах
            chunk_overlap: Перекрытие чанков
        """
        self.vector_store = vector_store
        self.chunker = RecursiveCharacterChunker(chunk_size, chunk_overlap)
        self._logger = get_logger()
        
        self._logger.info(
            "IngestService инициализирован",
            context={
                "chunk_size": chunk_size,
                "chunk_overlap": chunk_overlap,
                "vector_store": vector_store.name if hasattr(vector_store, 'name') else "FAISS"
            }
        )
    
    async def ingest_text(
        self,
        text: str,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None,
        document_id: Optional[str] = None,
    ) -> IngestResult:
        """
        Основной метод обработки текста.
        
        Args:
            text: Текст для обработки
            filename: Имя файла
            metadata: Дополнительные метаданные
            
        Returns:
            Результат обработки
        """
        start_time = time.time()
        document_id = document_id or str(uuid.uuid4())
        errors = []
        chunk_ids = []
        
        try:
            # 1. Валидация
            await self._validate_text(text)
            
            # 2. Определение формата
            format = self._detect_format(filename)
            
            # 3. Подготовка метаданных
            final_metadata = self._prepare_metadata(
                metadata or {}, 
                filename, 
                format, 
                len(text),
                document_id
            )
            
            # 4. Чанкинг
            self._logger.info(f"Чанкинг документа: {filename}")
            chunks = self.chunker.chunk_text(text, final_metadata)
            
            if not chunks:
                raise ValidationError(
                    message="Текст не содержит значимого контента",
                    field="text",
                    value=text[:100] + "..." if len(text) > 100 else text
                )
            
            # 5. Генерация эмбеддингов (оптимизация для M4)
            self._logger.info(f"Генерация эмбеддингов для {len(chunks)} чанков")
            await self._generate_embeddings_batch(chunks)
            
            # 6. Подготовка VectorDocument
            vector_docs = self._prepare_vector_documents(chunks, document_id)
            
            # 7. Сохранение в векторное хранилище
            self._logger.info(f"Сохранение в векторное хранилище")
            saved_ids = await self._save_to_vector_store(vector_docs)
            chunk_ids.extend(saved_ids)
            
            # 8. Статистика
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
            
        except Exception as e:
            error_msg = f"Ошибка обработки {filename}: {str(e)}"
            self._logger.error(error_msg)
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            return IngestResult(
                document_id=document_id,
                filename=filename,
                format=self._detect_format(filename),
                total_chunks=0,
                success=False,
                errors=[str(e)],
                chunk_ids=[],
                processing_time_ms=processing_time_ms,
                vector_store_stats={},
                metadata={}
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
        return final_metadata
    
    async def _generate_embeddings_batch(self, chunks: List[Chunk]) -> None:
        """Генерация эмбеддингов для всех чанков (оптимизация для M4)."""
        try:
            # Получаем модель (будет использовать MPS на M4)
            embedding_factory = get_embedding_factory()
            model = await embedding_factory.create_embedding_model(
                provider_type="sentence_transformer"
            )
            
            # Собираем тексты для батча
            texts = [chunk.content for chunk in chunks]
            
            # Генерируем эмбеддинги одним батчем (быстрее на GPU)
            embeddings = await model.embed_documents(texts)
            
            # Присваиваем чанкам
            for i, chunk in enumerate(chunks):
                if i < len(embeddings):
                    chunk.embedding = embeddings[i]
            
            self._logger.info(
                f"Эмбеддинги сгенерированы",
                context={
                    "chunks": len(chunks),
                    "dimensions": len(embeddings[0]) if embeddings else 0
                }
            )
            
        except Exception as e:
            self._logger.warning(f"Не удалось сгенерировать эмбеддинги: {e}")
            # Оставляем None - система сможет работать без них
    
    def _prepare_vector_documents(
        self,
        chunks: List[Chunk],
        document_id: str
    ) -> List[VectorDocument]:
        """Подготовка объектов для векторного хранилища."""
        vector_docs = []
        
        for chunk in chunks:
            # Копируем метаданные, добавляем ID документа
            chunk_metadata = chunk.metadata.copy()
            chunk_metadata["document_id"] = document_id
            chunk_metadata["workspace_id"] = chunk_metadata.get("workspace_id", "default")
            chunk_metadata["workspace_id"] = "default"
            
            vector_doc = VectorDocument(
                id=chunk.id,
                content=chunk.content,
                embedding=chunk.embedding,
                metadata=chunk_metadata
            )
            
            vector_docs.append(vector_doc)
        
        return vector_docs
    
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

            # Извлекаем эмбеддинги
            embeddings = [doc.embedding for doc in vector_docs]
            
            # Сохраняем
            saved_ids = await self.vector_store.add_documents(
                documents=vector_docs,
                embeddings=embeddings
            )
            
            return saved_ids
            
        except Exception as e:
            wrapped = wrap_exception(
                e,
                VectorStoreError,
                message="Ошибка сохранения в векторное хранилище",
                operation="add_documents",
                details={"documents_count": len(vector_docs)}
            )
            raise wrapped
    
    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья сервиса."""
        try:
            store_health = await self.vector_store.health_check()
            
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
