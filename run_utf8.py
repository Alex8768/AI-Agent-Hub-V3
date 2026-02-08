#!/usr/bin/env python3
"""
AI Agent Hub V3 - Production Runner
"""
import asyncio
import sys
import json
import typing
from pathlib import Path

# Добавляем корень проекта
sys.path.insert(0, str(Path(__file__).parent))

try:
    import uvicorn
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware

    # === ГЛАВНЫЙ ФИКС КОДИРОВКИ ===
    class UTF8JSONResponse(JSONResponse):
        # Явно указываем браузеру, что это UTF-8
        media_type = "application/json; charset=utf-8"

        def render(self, content: typing.Any) -> bytes:
            return json.dumps(
                content,
                ensure_ascii=False, # Не экранировать кириллицу
                allow_nan=False,
                indent=None,
                separators=(",", ":"),
            ).encode("utf-8")

    app = FastAPI(
        title="AI Agent Hub V3",
        version="3.0.0",
        default_response_class=UTF8JSONResponse
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return {"message": "AI Agent Hub V3 работает! 🚀", "status": "ok"}

    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "AI Agent Hub V3"}

    @app.get("/api/test-embedding")
    async def test_embedding():
        try:
            from src.adapters.embedding import get_embedding_model
            model = await get_embedding_model()
            vec = await model.embed_query("Тест")
            return {
                "status": "success", 
                "provider": "sentence-transformers", 
                "dimension": len(vec),
                "device": getattr(model, "_device", "unknown")
            }
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    if __name__ == "__main__":
        print("\n🚀 Запуск сервера с поддержкой UTF-8...")
        print("📍 http://localhost:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Выполните: pip install fastapi uvicorn")
