#!/bin/sh
# Run database migrations then start the server.
# Used as the container entrypoint in production (Railway, Render, etc.)
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting server on port ${PORT:-8000}..."
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
