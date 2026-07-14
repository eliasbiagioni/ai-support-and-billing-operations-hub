# SupportLedger AI - Support & Billing Operations Hub

A portfolio-grade SaaS operations platform that helps support teams resolve customer and billing issues faster. Built with **FastAPI + React/TypeScript + PostgreSQL**, following the project PRD.

> **Status:** Phases 0-7 are complete — Foundation, Core Support MVP, Knowledge Base, AI Assist v1, Stripe Billing, AI Billing Copilot (tool-calling), RAG + Guardrails (pgvector), and Production Polish (real JWT auth + RBAC, rate limiting, security headers).

## What's implemented

- **Backend (FastAPI):** modular routers, dependency injection, services, repositories, SQLAlchemy 2.0 models, Alembic migrations, Pydantic v2 schemas, consistent error handling, and PyTest coverage.
- **Frontend (React + TypeScript, strict):** Vite, React Router, TanStack Query, a typed API client, and a clean Tailwind UI with loading / empty / error states throughout.
- **Domains:** Customers CRUD, Tickets CRUD with a status-transition state machine, ticket timeline (internal notes + customer replies), a dashboard summary, a Knowledge Base (articles + chunking + keyword search), AI Assist (classify / summarize / suggest-reply with an audit log), and Stripe Billing (invoices, payments, checkout sessions, idempotent webhooks).
- **UUID identifiers:** every entity uses UUID primary keys (cross-dialect `sa.Uuid()`), generated application-side.
- **Real integrations:** AI (OpenAI) and Billing (Stripe) are real-only — they require live API keys at runtime and return a clear error when keys are absent. All other features run without keys. Tests mock both providers so CI stays green.
- **DevOps:** Docker Compose (Postgres + backend + frontend), seed data, and GitHub Actions CI (backend lint + tests, frontend lint + typecheck + build).

## API surface

- **Customers:** `GET/POST /api/customers`, `GET/PATCH /api/customers/{id}`
- **Tickets:** `GET/POST /api/tickets`, `GET/PATCH /api/tickets/{id}`, `POST /api/tickets/{id}/messages`, `POST /api/tickets/{id}/resolve`
- **Dashboard:** `GET /api/dashboard/summary`
- **Knowledge base:** `GET/POST /api/knowledge/articles`, `GET/PATCH /api/knowledge/articles/{id}`, `POST /api/knowledge/articles/{id}/chunk`, `GET /api/knowledge/search?q=`
- **AI Assist:** `POST /api/ai/tickets/{id}/classify|summarize|suggest-reply`, `GET /api/ai/audit-logs`
- **AI Copilot (RAG + tools):** `POST /api/ai/copilot`
- **Billing:** `GET /api/customers/{id}/billing`, `POST /api/customers/{id}/checkout-session`, `GET /api/invoices`, `GET /api/payments`
- **Webhooks:** `POST /api/webhooks/stripe`, `GET /api/webhooks/events`
- **Auth:** `POST /api/auth/login`, `GET /api/auth/me`, `POST /api/auth/change-password`
- **Users (admin only):** `GET/POST /api/users`, `PATCH /api/users/{id}`, `POST /api/users/{id}/reset-password`

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
    Routers[APIRouters: customers, tickets, dashboard, knowledge, ai, billing, webhooks, health]
    Deps[Dependencies: db session, current_user, pagination, llm_client, stripe_client]
    Services[Services: Customer, Ticket, Dashboard, Knowledge, AI, Billing, Webhook]
    Repos[Repositories: SQLAlchemy data access]
    Routers --> Deps
    Routers --> Services --> Repos
  end

  DB[(PostgreSQL)]
  OpenAI[[OpenAI API]]
  Stripe[[Stripe API]]

  API -->|"REST /api"| Routers
  Repos --> DB
  Services --> OpenAI
  Services --> Stripe
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

The backend container automatically runs migrations, seeds demo data, and starts the API. Source is mounted as a volume, so backend and frontend edits hot-reload without rebuilding the containers.

### Demo login

Seeded accounts share the password `password123`:

| Email                            | Role          |
| -------------------------------- | ------------- |
| `ava.admin@supportledger.io`     | admin         |
| `sam.support@supportledger.io`   | support agent |
| `bianca.billing@supportledger.io`| billing agent |

Only the **admin** can access the Users management screen and create/manage accounts — there is no public sign-up.

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
| Backend  | `python -m app.commands.backfill_embeddings` | Compute missing RAG embeddings |
| Frontend | `npm run dev`                  | Dev server                       |
| Frontend | `npm run typecheck`            | TypeScript check                 |
| Frontend | `npm run lint`                 | ESLint                           |
| Frontend | `npm run build`                | Production build                 |

## Environment variables

See [.env.example](.env.example). AI Assist requires `OPENAI_API_KEY` (and optionally `AI_MODEL`); Billing requires `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and `STRIPE_PRICE_ID_PRO`. These integrations are real-only: without the keys, the AI and billing endpoints return a clear `503` error while every other feature keeps working.

## Security notes

- **Real JWT auth + RBAC**: `POST /api/auth/login` issues a signed JWT; `get_current_user` verifies the `Authorization: Bearer` token, and `require_roles(...)` enforces role-based access (admin-only user management and destructive/billing-write actions). Passwords are hashed with bcrypt. There is **no public sign-up** — admins provision accounts.
- **AI guardrails**: user-supplied text is PII-redacted (emails, phone, card-like numbers) and screened for prompt-injection before reaching the LLM; risky/write copilot actions are returned as **proposed actions** requiring human approval.
- **No card data is ever stored** - Stripe handles all payment details; the app only mirrors invoices/payments and verifies webhook signatures.
- **AI actions are audited**: every classify/summarize/suggest-reply/copilot call writes an `ai_audit_logs` row (with tools used + risk flags), and suggested replies are labeled AI drafts requiring human review before sending.
- **Webhooks are idempotent**: events are deduped by `(provider, event_id)` so Stripe retries are safe.
- **Hardening**: per-IP rate limiting on auth + AI endpoints (enforced in production), security response headers, and per-request IDs with structured request logging.
- Secrets are read from environment variables and never committed; ORM parameterized queries guard against SQL injection.

## Testing

- Backend: `pytest` (48 tests) covers customer CRUD, ticket workflows (status transitions, resolve, message timeline), dashboard counts, knowledge base (CRUD, chunking, search), AI Assist (structured classification, invalid-JSON safe failure, audit logging), the tool-calling copilot (scripted tool loop, citations, proposed actions), RAG (fake embeddings + SQLite cosine fallback), guardrails (PII redaction + injection flagging), Stripe billing (checkout session, idempotent webhooks, billing summary), and auth/RBAC (login, JWT-protected routes, admin-only user management). Everything runs against in-memory SQLite with dependency overrides - no external services required.
- Frontend: type safety is enforced via `npm run typecheck`, `npm run lint`, and `npm run build`; component/e2e tests are planned for later phases per the PRD.

## Roadmap

| Phase | Name               | Status        |
| ----- | ------------------ | ------------- |
| 0     | Foundation         | Done          |
| 1     | Core Support MVP   | Done          |
| 2     | Knowledge Base     | Done          |
| 3     | AI Assist v1       | Done          |
| 4     | Stripe Billing     | Done          |
| 5     | AI Billing Copilot | Done          |
| 6     | RAG + Guardrails   | Done          |
| 7     | Production Polish  | Done          |
```
