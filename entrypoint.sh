#!/bin/sh
set -e

echo "PhiGateway — starting up"

# Run database migrations
echo "Running Alembic migrations..."
cd /app
alembic upgrade head || echo "Migration warning: continuing with create_all fallback"

# Start the API server
echo "Starting API server on 127.0.0.1:8000"
exec uvicorn phi_gateway.main:app --host 127.0.0.1 --port 8000
