#!/usr/bin/env bash
# Container entrypoint: apply migrations, seed demo data, then serve the API.
set -euo pipefail

echo "Running database migrations…"
alembic upgrade head

echo "Seeding demo data (idempotent)…"
python -m app.commands.seed

echo "Starting API server…"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
