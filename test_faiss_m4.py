import asyncio
import numpy as np
from src.adapters.embedding import get_embedding_model
from src.layers.base.rag.vector_stores.faiss_store import FAISSVectorStore
from src.core.contracts import VectorDocument

async def main():
    print("🧠 Тестируем связку: M4 (MPS) + FAISS")
    
    # 1. Получаем модель эмбеддингов (наша MPS-версия)
    model = await get_embedding_model()
    
    # 2. Инициализируем хранилище
    store = FAISSVectorStore(index_path="data/test_faiss.index", dimension=384)
    
    # 3. Данные для "памяти"
    texts = [
        "Александр работает на MacBook Pro M4",
        "Проект называется AI Agent Hub V3",
        "Векторная база данных использует FAISS"
    ]
    
    print("📝 Генерируем эмбеддинги для документов...")
    embeddings = await model.embed_documents(texts)
    
    docs = [VectorDocument(id=f"doc_{i}", content=txt, metadata={"source": "test"}) 
            for i, txt in enumerate(texts)]
    
    # 4. Сохраняем в базу
    await store.add_documents(docs, embeddings=embeddings)
    print("✅ Документы сохранены в FAISS")
    
    # 5. Тестируем поиск
    query = "На каком ноутбуке работает Александр?"
    print(f"\n🔍 Поиск по запросу: '{query}'")
    
    query_emb = await model.embed_query(query)
    results = await store.search(query=query, query_embedding=query_emb, k=1)
    
    if results:
        res = results[0]
        print(f"🎯 Найден ответ: {res.document.content}")
        print(f"📊 Сходство (score): {res.score:.4f}")

if __name__ == "__main__":
    asyncio.run(main())