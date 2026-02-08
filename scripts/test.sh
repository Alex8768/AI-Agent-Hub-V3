#!/bin/bash

# Test script for AI Agent Hub V3

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🧪 Running AI Agent Hub V3 tests..."

# Run unit tests
echo ""
echo "📋 Running unit tests..."
pytest tests/unit/ -v --cov=src --cov-report=term-missing

# Run integration tests if any
if [ -d "tests/integration" ] && [ "$(ls -A tests/integration)" ]; then
    echo ""
    echo "🔗 Running integration tests..."
    pytest tests/integration/ -v
fi

# Run E2E tests if any
if [ -d "tests/e2e" ] && [ "$(ls -A tests/e2e)" ]; then
    echo ""
    echo "🚀 Running E2E tests..."
    pytest tests/e2e/ -v
fi

echo ""
echo "✅ All tests completed!"
