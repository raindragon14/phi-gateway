FROM python:3.12-slim

WORKDIR /app

# Build dependencies (gcc needed for bcrypt compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files and install
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir . && rm -rf /root/.cache

# Copy runtime files
COPY alembic.ini alembic/ /app/
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create data directory and non-root user
RUN mkdir -p /app/data && \
    groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /sbin/nologin appuser && \
    chown -R appuser:appuser /app

USER appuser
EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
