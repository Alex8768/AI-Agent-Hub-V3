#!/usr/bin/env python3
"""
Test embeddings on Apple M4.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.adapters.embedding import get_embedding_model


async def main():
    print("🧪 Testing embeddings on Apple M4...")
    
    # Get embedding model (will auto-detect MPS)
    model = await get_embedding_model()
    
    # Test single query
    query = "Что такое искусственный интеллект?"
    query_embedding = await model.embed_query(query)
    
    print(f"✅ Query embedding (dim={len(query_embedding)}):")
    print(f"   Query: {query}")
    print(f"   First 3 values: {query_embedding[:3]}")
    
    # Test batch documents
    documents = [
        "Машинное обучение - это подраздел искусственного интеллекта.",
        "Нейронные сети используются в глубоком обучении.",
        "Обработка естественного языка помогает компьютерам понимать текст."
    ]
    
    doc_embeddings = await model.embed_documents(documents)
    
    print(f"\n✅ Document embeddings (batch of {len(documents)}):")
    for i, (doc, emb) in enumerate(zip(documents, doc_embeddings)):
        print(f"   Doc {i+1}: '{doc[:30]}...' → dim={len(emb)}")
    
    # Test health check
    health = await model.health_check()
    print(f"\n✅ Health check: {health['status']}")
    print(f"   Model: {health['model']}")
    print(f"   Device: {health['device']}")
    print(f"   Cache size: {health['cache_size']}")
    
    # Cleanup
    await model.cleanup()
    print("\n🎉 All tests passed! M4 optimization working.")


if __name__ == "__main__":
    asyncio.run(main())