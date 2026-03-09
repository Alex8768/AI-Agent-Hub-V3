# AI Agent Hub V3 Frontend

Frontend foundation for `A2.28 Interface Foundation (MVP)`.

## Current scope

- App shell with backend health status.
- Typed API contracts for core backend flows.
- Lightweight API client foundation.

## Local development

```bash
cd frontend
npm install
npm run dev
```

By default, the app reads backend URL from `VITE_API_BASE_URL` and falls back to:

`http://localhost:8000`

## Next planned increments

- Documents flow UI (ingest/list/delete).
- Search + hybrid search UI.
- Answer + diagnostics UI panels.
