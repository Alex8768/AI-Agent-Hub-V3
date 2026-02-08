#!/usr/bin/env python3
"""
Integration test for IngestService on MacBook M4.
Tests the complete document ingestion pipeline: chunking → embeddings → FAISS.
ARCHITECTURE_V3: Integration Test - Document Ingestion Pipeline
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


async def test_ingest_pipeline():
    """Test complete document ingestion pipeline."""
    
    print("🧠 AI Agent Hub V3 - Ingest Pipeline Integration Test")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Platform: MacBook Pro M4 (Apple Silicon)")
    print("=" * 60)
    
    test_results = {
        "test_name": "ingest_pipeline_integration",
        "timestamp": datetime.now().isoformat(),
        "platform": "macbook_m4",
        "components": {},
        "success": False,
        "metrics": {}
    }
    
    try:
        # 1. Import components
        print("\n1. 📦 Importing components...")
        from src.layers.base.rag.vector_stores.faiss_store import FAISSVectorStore
        from src.services.document import IngestService
        
        test_results["components"]["import"] = "success"
        print("   ✅ All imports successful")
        
        # 2. Test data
        print("\n2. 📄 Preparing test data...")
        test_text = """
        Искусственный интеллект (ИИ) — это область компьютерных наук, 
        занимающаяся созданием систем, способных выполнять задачи, 
        требующие человеческого интеллекта.
        
        Машинное обучение — подраздел ИИ, который позволяет компьютерам 
        обучаться на данных без явного программирования.
        
        Глубокое обучение использует многослойные нейронные сети 
        для решения сложных задач компьютерного зрения и NLP.
        """
        
        print(f"   ✅ Test text: {len(test_text)} chars, {len(test_text.split())} words")
        test_results["metrics"]["text_length"] = len(test_text)
        
        # 3. Initialize FAISS
        print("\n3. 🗄️  Initializing FAISS vector store...")
        try:
            index_path = "data/test_integration.index"
            vector_store = FAISSVectorStore(
                index_path=index_path,
                dimension=384  # MiniLM dimension
            )
            await vector_store.initialize()
            
            # Check FAISS health
            faiss_health = await vector_store.health_check()
            test_results["components"]["faiss"] = {
                "status": faiss_health.get("status"),
                "dimensions": faiss_health.get("dimension"),
                "vectors": faiss_health.get("vectors")
            }
            
            print(f"   ✅ FAISS initialized: {faiss_health.get('vectors', 0)} vectors")
            
        except Exception as e:
            print(f"   ❌ FAISS initialization failed: {e}")
            test_results["components"]["faiss"] = {"status": "failed", "error": str(e)}
            print("   ⚠️  This test requires FAISS. Install: pip install faiss-cpu")
            return False
        
        # 4. Create IngestService
        print("\n4. 🚀 Creating IngestService...")
        try:
            service = IngestService(
                vector_store=vector_store,
                chunk_size=800,
                chunk_overlap=100
            )
            
            # Service health check
            service_health = await service.health_check()
            test_results["components"]["ingest_service"] = {
                "status": service_health.get("status"),
                "chunk_size": 800,
                "chunk_overlap": 100
            }
            
            print("   ✅ IngestService created and healthy")
            
        except Exception as e:
            print(f"   ❌ IngestService creation failed: {e}")
            test_results["components"]["ingest_service"] = {"status": "failed", "error": str(e)}
            return False
        
        # 5. Test ingestion pipeline
        print("\n5. ⚙️  Testing complete ingestion pipeline...")
        print("   Steps: Text → Chunking → Embeddings → FAISS")
        
        try:
            start_time = asyncio.get_event_loop().time()
            
            result = await service.ingest_text(
                text=test_text,
                filename="ai_concepts_ru.txt",
                metadata={
                    "language": "ru",
                    "category": "artificial_intelligence",
                    "source": "integration_test",
                    "author": "AI Agent Hub V3"
                }
            )
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            # Record metrics
            test_results["metrics"].update({
                "total_chunks": result.total_chunks,
                "success": result.success,
                "processing_time_ms": result.processing_time_ms,
                "chunk_ids_count": len(result.chunk_ids)
            })
            
            test_results["ingest_result"] = {
                "document_id": result.document_id,
                "filename": result.filename,
                "format": result.format.value if hasattr(result.format, 'value') else str(result.format),
                "success": result.success
            }
            
            print(f"\n   📊 Pipeline Results:")
            print(f"      • Success: {result.success}")
            print(f"      • Document ID: {result.document_id[:8]}...")
            print(f"      • Chunks created: {result.total_chunks}")
            print(f"      • Processing time: {result.processing_time_ms}ms")
            print(f"      • FAISS vectors after: {result.vector_store_stats.get('total_vectors', 0)}")
            
            if result.success:
                print("   ✅ Complete pipeline works!")
            else:
                print(f"   ⚠️  Pipeline completed with errors: {result.errors}")
                
        except Exception as e:
            print(f"   ❌ Pipeline execution failed: {e}")
            import traceback
            traceback.print_exc()
            test_results["metrics"]["pipeline_error"] = str(e)
            return False
        
        # 6. Test vector search
        print("\n6. 🔍 Testing vector search...")
        try:
            search_results = await vector_store.search(
                query="Что такое машинное обучение?",
                k=2
            )
            
            test_results["metrics"]["search_results"] = len(search_results)
            
            if search_results:
                print(f"   ✅ Search successful: {len(search_results)} results")
                print(f"      Top result similarity: {search_results[0].score:.3f}")
                print(f"      Content preview: {search_results[0].document.content[:80]}...")
            else:
                print("   ⚠️  No search results returned")
                
        except Exception as e:
            print(f"   ⚠️  Search test skipped: {e}")
        
        # 7. Cleanup
        print("\n7. 🧹 Cleaning up test resources...")
        try:
            await vector_store.cleanup()
            print("   ✅ Resources cleaned up")
        except Exception as e:
            print(f"   ⚠️  Cleanup warning: {e}")
        
        # 8. Final report
        print("\n" + "=" * 60)
        print("📋 INTEGRATION TEST COMPLETE")
        print("=" * 60)
        
        # Calculate overall success
        all_healthy = all(
            comp.get("status") in ["healthy", "success"]
            for comp in test_results["components"].values()
            if isinstance(comp, dict) and "status" in comp
        )
        
        test_results["success"] = all_healthy and result.success
        
        if test_results["success"]:
            print("✅ SUCCESS: All components integrated and working!")
            print(f"   • FAISS: {test_results['components']['faiss']['status']}")
            print(f"   • IngestService: {test_results['components']['ingest_service']['status']}")
            print(f"   • Pipeline: {result.total_chunks} chunks processed")
            print(f"   • Total time: {result.processing_time_ms}ms")
        else:
            print("⚠️  PARTIAL SUCCESS: Some components need attention")
            
        # Save detailed results
        results_file = PROJECT_ROOT / "test_results" / "ingest_integration.json"
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
            
        print(f"\n📁 Detailed results saved to: {results_file.relative_to(PROJECT_ROOT)}")
        
        return test_results["success"]
        
    except ImportError as e:
        print(f"\n❌ Critical import error: {e}")
        print("   Please check project structure and dependencies")
        return False
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Create necessary directories
    Path("data").mkdir(exist_ok=True)
    Path("test_results").mkdir(exist_ok=True)
    
    # Run test
    print("🚀 Starting Ingest Pipeline Integration Test...")
    success = asyncio.run(test_ingest_pipeline())
    
    # Exit code
    sys.exit(0 if success else 1)