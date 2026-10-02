# ==============================================================================
# VerifAI — Production Dockerfile
# Multi-stage / secure non-root unprivileged container
# ==============================================================================

FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend

# Create unprivileged system user for container security
RUN groupadd -g 10001 verifai && \
    useradd -u 10001 -g verifai -s /bin/sh -d /app verifai

# Install system dependencies if required
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir --retries 5 --timeout 60 -r requirements.txt

# Copy backend application source
COPY backend /app/backend
COPY pyproject.toml /app/

# Set ownership
RUN chown -R verifai:verifai /app

# Switch to non-root user
USER verifai

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/api/v1/health || exit 1

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
