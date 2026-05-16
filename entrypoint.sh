#!/bin/sh
set -e

echo "PhiGateway — starting up"

# Run database migrations
echo "Running Alembic migrations..."
cd /app
alembic upgrade head || echo "Migration warning: continuing with create_all fallback"

# Start the API server
echo "Starting API server on 0.0.0.0:8000"
exec uvicorn phi_gateway.main:app --host 0.0.0.0 --port 8000
