# Creative Workforce Platform

This repository hosts the creative workforce tooling platform, combining a FastAPI + LangGraph backend and a Next.js frontend to coordinate artifact-focused AI agents.

## Getting Started

1. Install dependencies:
   - Backend: `cd backend && uv sync`
   - Frontend: `cd frontend && pnpm install`
2. Provision local services: `docker-compose -f infrastructure/docker-compose.yaml up -d postgres minio redis`
3. Run the stacks:
   - Backend: `uv run uvicorn backend.app.main:app --reload`
   - Frontend: `pnpm dev`

Refer to `AGENTS.md` for contributor guidelines and `documents/PoC仕様書.md` for functional specifications.
