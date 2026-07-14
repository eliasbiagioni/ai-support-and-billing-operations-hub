#!/usr/bin/env bash
# Container entrypoint: apply migrations, seed demo data, then serve the API.
set -euo pipefail

echo "Running database migrations…"
alembic upgrade head

echo "Seeding demo data (idempotent)…"
python -m app.commands.seed

echo "Starting API server…"
# Enable auto-reload outside production so mounted source edits take effect
# without rebuilding the container.
RELOAD_FLAG=""
if [ "${ENVIRONMENT:-development}" != "production" ]; then
  RELOAD_FLAG="--reload"
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 ${RELOAD_FLAG}
