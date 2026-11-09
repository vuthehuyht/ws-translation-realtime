# Backend Service (`apps/backend`)

FastAPI + `asyncio` unified service for REST API (`/api/v1/*`), WebSocket Audio Ingest (`/ws/v1/*`), and background workers.

## Quick Commands

```bash
uv sync
uv run ruff check .
uv run mypy app
uv run pytest -v
uv run uvicorn app.main:app --reload --port 8000
```
