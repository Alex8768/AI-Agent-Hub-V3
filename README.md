# 🏗️ AI Agent Hub Enterprise V3

**Enterprise-grade AI Agent Platform** based on ARCHITECTURE_V3 design with hybrid LLM support (Local + Cloud).

## 🌟 Features

### 🎯 ARCHITECTURE_V3 Core
- **Modular Layer Architecture** (Base + Pro levels)
- **Contract-Oriented Development** with clear interfaces
- **Inversion of Control** for easy component replacement
- **Test-Driven Development** from day one

### 🤖 AI Capabilities
- **Hybrid LLM Support**: Local (Ollama) + Cloud (OpenAI, Anthropic, Google)
- **Smart Document Ingestion**: PDF, DOCX, TXT, MD, HTML parsing
- **Vector RAG**: FAISS/Qdrant with semantic search
- **Graph RAG**: Knowledge graph integration (Pro level)

### 🚀 Production Ready
- **Docker Compose** with full infrastructure
- **Monitoring**: Prometheus + Grafana + Jaeger
- **Security**: Workspace guard, rate limiting, audit logs
- **Scalability**: Async-first, connection pooling, caching

## 🏗️ Architecture Overview
```
src/
├── core/           # Ядро системы (контракты, типы, граф)
├── layers/         # Уровни: Base (Level 1) и Pro (Level 2)
├── api/            # FastAPI REST API
├── adapters/       # Адаптеры внешних систем
└── services/       # Бизнес-сервисы
```

## 🚀 Quick Start


## ⚡ Operational Quick Start (Verified)

These commands match the current repo wiring (Base + Pro feature flags).

### Base install
python -m pip install -e ".[base,test]"

### Full base
python -m pip install -e ".[base,security,embeddings,faiss,ingest,test]"

### Pro (Qdrant tests)
python -m pip install -e ".[test,qdrant,embeddings,faiss]"

### Run API
uvicorn src.api.main:app --reload

### Golden Path (Base)
python scripts/demo_golden_path.py

### Golden Path (Pro)
DEMO_ENABLE_REASONING=1 python scripts/demo_golden_path.py



### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- UV (modern Python package manager)

### Installation
```bash
# 1. Clone and initialize
./init-ai-agent-v3.sh

# 2. Start services
docker-compose up -d ollama qdrant redis db

# 3. Install dependencies
uv sync

# 4. Initialize database
python scripts/database/init_db.py

# 5. Run the application
uvicorn src.api.main:app --reload
```

### Configuration
Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

## 📦 Components

### Base Layer (Level 1)
- **Smart Ingest**: Intelligent document parsing
- **Vector RAG**: Semantic search with FAISS/Qdrant
- **Process Streaming**: Real-time agent thought streaming
- **Export Layer**: DOCX, PDF, HTML, Markdown export

### Pro Layer (Level 2) - Enterprise
- **Graph RAG**: Knowledge graphs with Neo4j
- **Split View Canvas**: Interactive workspace
- **Semantic Memory**: User preference learning
- **Multi-Agent**: Coordinated agent systems

## 🔧 Development

### Running Tests
```bash
./scripts/test.sh
```

### Code Quality
```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/
```

## 📊 Monitoring
- **Metrics**: Prometheus on port 9090
- **Dashboards**: Grafana on port 3000 (admin/admin)
- **Tracing**: Jaeger on port 16686

## 🐳 Docker Deployment
```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.prod.yml up -d
```

## 📚 Documentation
- [Architecture](./docs/architecture/ARCHITECTURE_V3.md)
- [API Reference](./docs/api/README.md)
- [Deployment Guide](./docs/deployment/README.md)
- [Development Guide](./docs/development/README.md)

## 🛡️ Security
- Workspace isolation with guard system
- Rate limiting and API key authentication
- Audit logging for all operations
- Safe path validation

## 🔄 Roadmap
- [x] Base Layer implementation
- [ ] Pro Layer components
- [ ] Advanced MCP tool integration
- [ ] Multi-tenant support
- [ ] Plugin system

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License
MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments
- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Vector search with [FAISS](https://github.com/facebookresearch/faiss) and [Qdrant](https://qdrant.tech/)
- Local LLMs with [Ollama](https://ollama.ai/)
- Architecture inspired by Clean Architecture and Hexagonal patterns

## 📞 Support
- Issues: [GitHub Issues](https://github.com/ai-agent-hub/v3/issues)
- Discussions: [GitHub Discussions](https://github.com/ai-agent-hub/v3/discussions)
- Email: team@ai-agent-hub.com
