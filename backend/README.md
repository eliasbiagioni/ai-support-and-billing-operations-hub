# SupportLedger AI - Backend

FastAPI backend for the AI Support & Billing Operations Hub (Phase 0-1).

See the [root README](../README.md) for full project documentation, architecture, and run instructions.

## Quick reference

```bash
# Install (editable, with dev tools)
pip install -e ".[dev]"

# Run the API
uvicorn app.main:app --reload --port 8000

# Run migrations / seed
alembic upgrade head
python -m app.commands.seed

# Tests and lint
pytest
ruff check .
```
