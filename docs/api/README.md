# API Documentation

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
```bash
# For protected endpoints
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/...
```

## Endpoints

### Health
```
GET /health
GET /api/v1/health
```

### LLM
```
POST /api/v1/llm/generate
POST /api/v1/llm/generate-stream
```

### Documents
```
POST /api/v1/documents/upload
GET  /api/v1/documents
GET  /api/v1/documents/{id}
```

### Search
```
POST /api/v1/search
```

### Export
```
POST /api/v1/export
```

### Streaming
```
GET /api/v1/stream/{session_id}
```

## OpenAPI
Access interactive documentation at:
- http://localhost:8000/api/v1/docs (Swagger UI)
- http://localhost:8000/api/v1/redoc (ReDoc)

## Rate Limiting
- 100 requests per minute per IP
- Headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
