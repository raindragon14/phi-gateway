FROM python:3.12-slim

WORKDIR /app

# Copy project files and install
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir . && rm -rf /root/.cache

# Copy runtime files
COPY srv/ /app/srv/
COPY alembic.ini /app/
COPY alembic/ /app/alembic/
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
