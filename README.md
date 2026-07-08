# SupportLedger AI - Support & Billing Operations Hub

A portfolio-grade SaaS operations platform that helps support teams resolve customer and billing issues faster. Built with **FastAPI + React/TypeScript + PostgreSQL**, following the project PRD.

> **Status:** Phase 0 (Foundation) and Phase 1 (Core Support MVP) are complete. Later phases (Knowledge Base, AI Assist, Stripe Billing, AI Copilot, RAG + Guardrails, Production Polish) are scaffolded for but not yet implemented.

## What's implemented

- **Backend (FastAPI):** modular routers, dependency injection, services, repositories, SQLAlchemy 2.0 models, Alembic migrations, Pydantic v2 schemas, consistent error handling, and PyTest coverage.
- **Frontend (React + TypeScript, strict):** Vite, React Router, TanStack Query, a typed API client, and a clean Tailwind UI with loading / empty / error states throughout.
- **Domains:** Customers CRUD, Tickets CRUD with a status-transition state machine, ticket timeline (internal notes + customer replies), and a dashboard summary.
- **DevOps:** Docker Compose (Postgres + backend + frontend), seed data, and GitHub Actions CI (backend lint + tests, frontend lint + typecheck + build).

## Architecture

```mermaid
flowchart LR
  subgraph frontend [Frontend - React + TypeScript + Vite]
    UI[Pages & feature modules]
    RQ[TanStack Query]
    API[Typed API client]
    UI --> RQ --> API
  end

  subgraph backend [Backend - FastAPI]
    Routers[APIRouters: customers, tickets, dashboard, health]
    Deps[Dependencies: db session, current_user, pagination]
    Services[Services: Customer, Ticket, Dashboard]
    Repos[Repositories: SQLAlchemy data access]
    Routers --> Deps
    Routers --> Services --> Repos
  end

  DB[(PostgreSQL)]

  API -->|"REST /api"| Routers
  Repos --> DB
```

### Repository layout

```
backend/          FastAPI app (app/), Alembic migrations, tests, Dockerfile
frontend/         React + TypeScript app (src/), Vite config, Dockerfile
docker-compose.yml
.github/workflows/ci.yml
.env.example
```

Backend internals follow the PRD structure: `app/api/v1/` (routers), `app/core/` (config, logging, errors), `app/db/` (session, base), `app/models/`, `app/schemas/`, `app/services/`, `app/repositories/`, `app/commands/seed.py`.

## Running with Docker (recommended)

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- API docs (Swagger): http://localhost:8000/docs
- Health: http://localhost:8000/api/health

The backend container automatically runs migrations, seeds demo data, and starts the API.

## Running locally (without Docker)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Point at a running Postgres, or use SQLite for a quick spin-up:
export DATABASE_URL="sqlite:///./dev.db"

python -m app.commands.seed          # create + seed tables
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
VITE_API_BASE_URL="http://localhost:8000" npm run dev
```

## Commands

| Area     | Command                        | Purpose                          |
| -------- | ------------------------------ | -------------------------------- |
| Backend  | `uvicorn app.main:app --reload`| Run the API                      |
| Backend  | `pytest`                       | Run tests                        |
| Backend  | `ruff check .`                 | Lint                             |
| Backend  | `alembic upgrade head`         | Apply migrations                 |
| Backend  | `python -m app.commands.seed`  | Seed demo data                   |
| Frontend | `npm run dev`                  | Dev server                       |
| Frontend | `npm run typecheck`            | TypeScript check                 |
| Frontend | `npm run lint`                 | ESLint                           |
| Frontend | `npm run build`                | Production build                 |

## Environment variables

See [.env.example](.env.example). Stripe and LLM keys are declared but unused in Phase 0-1; they exist so later phases plug in without config churn.

## Security notes (what's real vs mocked)

- **Auth is mocked** in Phase 0-1: a `get_current_user` dependency returns the seeded agent. This is the single seam to replace with real JWT/session auth later (PRD 6.1).
- **No card data is ever stored** - Stripe (Phase 4) will handle payment details.
- Secrets are read from environment variables and never committed.
- ORM parameterized queries guard against SQL injection.
- For a production deployment you would add real authentication, RBAC enforcement, rate limiting, and audit logging (planned in later phases).

## Testing

- Backend: `pytest` (16 tests) covers customer CRUD, ticket creation, status transitions, resolve, message timeline, dashboard counts, validation (422), and not-found (404). Tests run against in-memory SQLite with dependency overrides - no external services required.
- Frontend: type safety is enforced via `npm run typecheck` and `npm run build`; component/e2e tests are planned for later phases per the PRD.

## Roadmap

| Phase | Name               | Status        |
| ----- | ------------------ | ------------- |
| 0     | Foundation         | Done          |
| 1     | Core Support MVP   | Done          |
| 2     | Knowledge Base     | Planned       |
| 3     | AI Assist v1       | Planned       |
| 4     | Stripe Billing     | Planned       |
| 5     | AI Billing Copilot | Planned       |
| 6     | RAG + Guardrails   | Planned       |
| 7     | Production Polish  | Planned       |
```
