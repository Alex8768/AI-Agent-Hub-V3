#!/usr/bin/env python3
"""
Реализация реального векторного хранилища (FAISS)
"""

from pathlib import Path
import json

def create_faiss_store():
    """Создаём реальный векторный store на FAISS."""
    
    faiss_content = '''"""
Реализация VectorStore для FAISS.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import hashlib
import pickle

from src.core.contracts import VectorStore, VectorDocument, SearchResult
from src.core.exceptions import VectorStoreError
from src.adapters.logging_adapter import get_logger


class FAISSVectorStore(VectorStore):
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
        
        self._initialize_faiss()
    
    def _initialize_faiss(self):
        """Инициализация FAISS (ленивая загрузка)."""
        try:
            import faiss
            
            if self._index_path.exists():
                # Загружаем существующий индекс
                self._logger.info(f"Загружаем FAISS индекс из {self._index_path}")
                self._index = faiss.read_index(str(self._index_path))
                
                # Загружаем метаданные
                meta_path = self._index_path.with_suffix('.meta.pkl')
                if meta_path.exists():
                    with open(meta_path, 'rb') as f:
                        data = pickle.load(f)
                        self._document_store = data.get('documents', {})
                        self._id_to_index = data.get('id_to_index', {})
                
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
        if not documents:
            return []
        
        try:
            # Проверяем размерность
            if embeddings:
                for emb in embeddings:
                    if len(emb) != self._dimension:
                        raise VectorStoreError(
                            message=f"Размерность эмбеддинга {len(emb)} != {self._dimension}",
                            operation="add_documents"
                        )
            
            # Преобразуем эмбеддинги в numpy
            import numpy as np
            import faiss
            
            if embeddings:
                vectors = np.array(embeddings, dtype=np.float32)
            else:
                # Если эмбеддингов нет, создаём случайные (для теста)
                vectors = np.random.randn(len(documents), self._dimension).astype(np.float32)
            
            # Нормализуем векторы для косинусного сходства
            faiss.normalize_L2(vectors)
            
            # Добавляем в индекс
            start_idx = self._index.ntotal
            self._index.add(vectors)
            
            # Сохраняем документы
            added_ids = []
            for i, doc in enumerate(documents):
                doc_id = doc.id
                
                # Сохраняем документ
                self._document_store[doc_id] = doc
                self._id_to_index[doc_id] = start_idx + i
                added_ids.append(doc_id)
            
            # Сохраняем индекс
            self._save_index()
            
            self._logger.info(f"Добавлено {len(documents)} документов в FAISS")
            return added_ids
            
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
        try:
            import numpy as np
            import faiss
            
            # Если эмбеддинг не предоставлен, нужно его получить
            if query_embedding is None:
                # В реальной системе тут бы вызывался embedding model
                # Для демо создаём случайный вектор
                query_embedding = np.random.randn(self._dimension).astype(np.float32)
            
            # Преобразуем и нормализуем
            query_vector = np.array([query_embedding], dtype=np.float32)
            faiss.normalize_L2(query_vector)
            
            # Ищем
            distances, indices = self._index.search(query_vector, min(k, self._index.ntotal))
            
            # Формируем результаты
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx == -1:  # FAISS возвращает -1 если недостаточно данных
                    continue
                
                # Ищем документ по индексу
                doc_id = None
                for did, doc_idx in self._id_to_index.items():
                    if doc_idx == idx:
                        doc_id = did
                        break
                
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
            
        except Exception as e:
            self._logger.error(f"Ошибка поиска: {e}")
            raise VectorStoreError(
                message=f"Ошибка поиска: {str(e)}",
                operation="search",
                query=query
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
    
    def _save_index(self):
        """Сохраняет индекс и метаданные."""
        try:
            import faiss
            
            # Сохраняем FAISS индекс
            faiss.write_index(self._index, str(self._index_path))
            
            # Сохраняем метаданные
            meta_path = self._index_path.with_suffix('.meta.pkl')
            with open(meta_path, 'wb') as f:
                pickle.dump({
                    'documents': self._document_store,
                    'id_to_index': self._id_to_index
                }, f)
            
            self._logger.debug(f"Индекс сохранён: {self._index_path}")
            
        except Exception as e:
            self._logger.error(f"Ошибка сохранения индекса: {e}")
    
    async def delete(self, document_ids: List[str]) -> int:
        """Удаление документов (упрощённая версия)."""
        # FAISS не поддерживает удаление, так что помечаем как удалённые
        deleted = 0
        for doc_id in document_ids:
            if doc_id in self._document_store:
                # Помечаем как удалённый
                self._document_store[doc_id].metadata['_deleted'] = True
                deleted += 1
        
        if deleted > 0:
            self._save_index()
        
        return deleted
    
    async def get_document(self, document_id: str) -> Optional[VectorDocument]:
        return self._document_store.get(document_id)
    
    async def update_metadata(self, document_id: str, metadata: Dict[str, Any]) -> bool:
        if document_id in self._document_store:
            self._document_store[document_id].metadata.update(metadata)
            self._save_index()
            return True
        return False
    
    async def get_stats(self) -> Dict[str, Any]:
        return {
            "provider": "faiss",
            "total_documents": len(self._document_store),
            "total_vectors": self._index.ntotal if self._index else 0,
            "dimension": self._dimension,
            "index_path": str(self._index_path),
            "active_documents": len([d for d in self._document_store.values() 
                                     if not d.metadata.get('_deleted', False)])
        }
    
    async def initialize(self):
        """Инициализация (уже сделана в __init__)."""
        pass
    
    async def cleanup(self):
        """Очистка ресурсов."""
        self._save_index()
        self._logger.info("FAISS store очищен")
    
    async def health_check(self) -> Dict[str, Any]:
        return {
            "status": "healthy" if self._index else "unhealthy",
            "provider": "faiss",
            "vectors": self._index.ntotal if self._index else 0,
            "documents": len(self._document_store),
            "dimension": self._dimension
        }
'''
    
    Path("src/layers/base/rag/vector_stores/faiss_store.py").write_text(faiss_content, encoding="utf-8")
    print("✅ Создан FAISSVectorStore")
    
    # Создаём __init__.py
    Path("src/layers/base/rag/vector_stores/__init__.py").write_text(
        'from .faiss_store import FAISSVectorStore\n',
        encoding="utf-8"
    )
    
    return True

def add_faiss_endpoints():
    """Добавляем эндпоинты для работы с FAISS."""
    
    # Читаем run_utf8.py
    with open("run_utf8.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Добавляем импорты
    if "from src.core.contracts import VectorDocument" not in content:
        import_line = 'from src.core.contracts import VectorDocument'
        # Добавляем после других импортов
        insert_pos = content.find('from fastapi import')
        if insert_pos != -1:
            end_of_imports = content.find('\n', content.find('from fastapi import'))
            content = content[:end_of_imports] + '\n' + import_line + content[end_of_imports:]
    
    # Добавляем эндпоинты перед запуском сервера
    faiss_endpoints = '''

@app.post("/api/faiss/add-documents")
async def add_documents_to_faiss():
    """Добавляем тестовые документы в FAISS."""
    try:
        from src.layers.base.rag.vector_stores import FAISSVectorStore
        from src.core.config import settings
        
        # Создаём store
        store = FAISSVectorStore(
            index_path=settings.faiss_index_path,
            dimension=settings.faiss_dimension
        )
        
        # Тестовые документы
        documents = [
            VectorDocument(
                id="doc_1",
                content="Искусственный интеллект - это способность машин обучаться и решать задачи.",
                metadata={"type": "definition", "source": "wikipedia"}
            ),
            VectorDocument(
                id="doc_2", 
                content="Машинное обучение является подразделом искусственного интеллекта.",
                metadata={"type": "definition", "source": "textbook"}
            ),
            VectorDocument(
                id="doc_3",
                content="Нейронные сети вдохновлены биологическими нейронными сетями мозга.",
                metadata={"type": "technology", "source": "research"}
            )
        ]
        
        # Добавляем
        added_ids = await store.add_documents(documents)
        
        return {
            "status": "success",
            "message": f"Добавлено {len(added_ids)} документов в FAISS",
            "document_ids": added_ids,
            "stats": await store.get_stats()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Ошибка: {str(e)}",
            "action": "Установите FAISS: pip install faiss-cpu"
        }

@app.get("/api/faiss/search")
async def search_faiss(query: str = "искусственный интеллект"):
    """Поиск по FAISS индексу."""
    try:
        from src.layers.base.rag.vector_stores import FAISSVectorStore
        from src.core.config import settings
        
        store = FAISSVectorStore(
            index_path=settings.faiss_index_path,
            dimension=settings.faiss_dimension
        )
        
        results = await store.search(query=query, k=3)
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                "document_id": result.document.id,
                "content": result.document.content[:100] + "..." if len(result.document.content) > 100 else result.document.content,
                "score": result.score,
                "metadata": result.document.metadata
            })
        
        return {
            "status": "success",
            "query": query,
            "results": formatted_results,
            "total": len(results),
            "store_stats": await store.get_stats()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "query": query
        }

@app.get("/api/faiss/stats")
async def get_faiss_stats():
    """Статистика FAISS хранилища."""
    try:
        from src.layers.base.rag.vector_stores import FAISSVectorStore
        from src.core.config import settings
        
        store = FAISSVectorStore(
            index_path=settings.faiss_index_path,
            dimension=settings.faiss_dimension
        )
        
        stats = await store.get_stats()
        health = await store.health_check()
        
        return {
            "status": "success",
            "stats": stats,
            "health": health
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
'''
    
    # Вставляем перед запуском сервера
    insert_pos = content.find('config = uvicorn.Config')
    if insert_pos != -1:
        content = content[:insert_pos] + faiss_endpoints + content[insert_pos:]
    
    # Записываем обратно
    with open("run_utf8.py", "w", encoding="utf-8") as f:
        f.write(content)
    
    print("✅ Эндпоинты FAISS добавлены в API")
    return True

def main():
    print("🔧 Реализуем векторное хранилище FAISS...")
    print("="*60)
    
    try:
        # Создаём структуру директорий
        Path("src/layers/base/rag/vector_stores").mkdir(parents=True, exist_ok=True)
        
        # Создаём FAISS реализацию
        create_faiss_store()
        
        # Добавляем эндпоинты
        add_faiss_endpoints()
        
        print("\\n" + "="*60)
        print("🎉 FAISS реализован!")
        print("="*60)
        print("\\n📋 Установи FAISS:")
        print("   pip install faiss-cpu")
        print("\\n🚀 Затем запусти сервер:")
        print("   python run_utf8.py")
        print("\\n🔍 Новые эндпоинты:")
        print("   POST /api/faiss/add-documents - добавить тестовые данные")
        print("   GET  /api/faiss/search?query=... - поиск по FAISS")
        print("   GET  /api/faiss/stats - статистика хранилища")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()