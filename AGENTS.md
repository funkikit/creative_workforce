# Repository Guidelines

## Project Structure & Module Organization
- Backend service lives in `backend/` (FastAPI + LangGraph). Core modules are under `backend/app/` with subdirectories for `api/`, `agents/`, `core/`, `models/`, `services/`, and `workers/`. Tests reside in `backend/tests/`.
- Frontend web client is in `frontend/` (Next.js, pnpm). UI components live in `frontend/components/`, shared logic in `frontend/hooks/` and `frontend/lib/`, and route files in `frontend/app/`.
- DevOps assets sit in `infrastructure/` (`docker-compose.yaml`, Dockerfiles, Terraform plans, GitHub Actions). Configuration templates are grouped in `config/env/`, while prompt templates live in `config/prompts/`.
- Human-facing docs (企画書, 提案書, PoC仕様書, etc.) remain in `documents/`. Sample assets or fixtures should go in `data/` when needed.

## Build, Test, and Development Commands
- **Backend**: `uv sync` (install dependencies), `uv run fastapi dev` (start dev server), `uv run pytest` (run unit/integration tests).
- **Frontend**: `pnpm install` (dependencies), `pnpm dev` (local dev server), `pnpm lint` / `pnpm test` (quality gates).
- **Infrastructure**: `docker-compose up -d postgres minio redis` to provision local backing services; `docker-compose up backend frontend` to run both stacks together.

## Coding Style & Naming Conventions
- Python code follows `ruff` + `black` defaults: 4-space indentation, snake_case for modules/functions, PascalCase for Pydantic models. Type hints are mandatory on public functions.
- TypeScript/React uses eslint + prettier defaults: 2-space indentation, camelCase for variables, PascalCase for components, file names in kebab-case (e.g., `agent-sidebar.tsx`).
- Keep service implementations under `services/` and agent behaviors under `agents/` to preserve separation of concerns. Shared constants reside in `core/constants.py` or `frontend/lib/constants.ts`.

## Testing Guidelines
- Python tests use `pytest`; place new suites under `backend/tests/` mirroring the runtime package structure (e.g., `tests/api/test_artifacts.py`).
- Frontend tests use `vitest` (or Jest if enabled later); co-locate component specs using `*.test.tsx`.
- チーム方針としてテスト駆動開発（TDD）を採用します。新機能は失敗するテストを書いてから実装し、グリーン後にリファクタリングを行ってください。
- Aim for meaningful coverage over critical flows (agent orchestration, artifact persistence, Gemini prompt generation). Add regression tests when fixing bugs.

## Commit & Pull Request Guidelines
- Write commits in imperative mood (`Add artifact dependency resolver`). Keep scope focused; split large changes into logical chunks.
- Work in small increments and commit frequently so that each change is reviewable and easily reversible. Avoid large uncommitted streaks.
- Before opening a PR, run backend/frontend tests and linting. PR descriptions should cover intent, major changes, and validation steps. Link related GitHub issues and attach UI screenshots or sample outputs when relevant.
- Require at least one reviewer. Resolve discussions before merge. Use squash merge unless the branch already reflects a reviewed history.
