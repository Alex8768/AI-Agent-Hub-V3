#!/bin/bash

echo "🍎 AI Agent Hub V3 - Mac M4"
echo "============================="

# Kill any process on port 8000
echo "🔧 Очищаем порт 8000..."
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 1

# Проверяем Ollama
echo "🤖 Проверяем Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama запущен"
    curl -s http://localhost:11434/api/tags | python -c "import json,sys; data=json.load(sys.stdin); print(f'   Модели: {', '.join([m[\"name\"] for m in data[\"models\"]])}')"
else
    echo "⚠️ Ollama не запущен. Запустите в отдельном окне:"
    echo "   ollama serve"
    echo "   ollama pull llama3.2"
fi

# Создаем директории
echo "📁 Создаем структуру..."
mkdir -p data logs exports workspace data/vector_store

# Запускаем сервер ПРАВИЛЬНО
echo ""
echo "🚀 Запускаем AI Agent Hub V3..."
echo "🌐 API: http://localhost:8000"
echo "📚 Docs: http://localhost:8000/docs"
echo "📈 Health: http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop"
echo ""

cd "/Users/aleksandrladygin/Documents/LLM Engineering/ai-agent-hub-v3"
PYTHONPATH="$PWD" \
WORKSPACE_TOOLS_USE_REPO_ROOT_IN_DEV=true \
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
