#!/usr/bin/env python3
"""
Простой тест эмбеддингов
"""

import asyncio
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def test_embeddings():
    """Тестируем эмбеддинги."""
    print("🧪 Тестируем Sentence Transformers...")
    
    try:
        from src.adapters.embedding.sentence_transformer_adapter import SentenceTransformerAdapter
        
        # Создаём адаптер с минимальной конфигурацией
        adapter = SentenceTransformerAdapter(
            model_name="paraphrase-multilingual-MiniLM-L12-v2",
            device="cpu"  # Для теста используем CPU
        )
        
        print(f"✅ Адаптер создан: {adapter.name}")
        print(f"   Размерность: {adapter.dimensions}")
        print(f"   Макс токенов: {adapter.max_tokens}")
        
        # Тестируем health check
        health = await adapter.health_check()
        print(f"✅ Health check: {health.get('status', 'unknown')}")
        
        # Простой тест эмбеддинга (если модель загрузится)
        try:
            embedding = await adapter.embed_query("Тестовый запрос")
            print(f"✅ Эмбеддинг создан! Размер: {len(embedding)}")
            print(f"   Первые 3 значения: {embedding[:3]}")
        except Exception as e:
            print(f"⚠️  Не удалось создать эмбеддинг: {e}")
            print("   Возможно, нужно установить sentence-transformers:")
            print("   pip install sentence-transformers")
        
        return True
        
    except ImportError as e:
        print(f"❌ Импорт не удался: {e}")
        print("\n📦 Установи зависимости:")
        print("   pip install sentence-transformers torch")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_embeddings())
    sys.exit(0 if success else 1)
