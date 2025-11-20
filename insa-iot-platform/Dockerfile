# ============================================================================
# Alkhorayef ESP IoT Platform - Production Docker Image
# ============================================================================
# Multi-stage build for minimal production image
# ============================================================================

# ----------------------------------------------------------------------------
# Stage 1: Builder - Compile dependencies and prepare application
# ----------------------------------------------------------------------------
FROM python:3.11-slim as builder

# Set build arguments
ARG DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    make \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip, setuptools, wheel
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy requirements first (leverage Docker cache)
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies in virtual environment
# Separate heavy ML dependencies for better layer caching
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ----------------------------------------------------------------------------
# Stage 2: Runtime - Minimal production image
# ----------------------------------------------------------------------------
FROM python:3.11-slim

# Metadata
LABEL maintainer="Alkhorayef Petroleum Company <support@alkhorayef.com>"
LABEL description="Intelligent ESP pump diagnostics with AI-powered RAG system"
LABEL version="1.0.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=UTC \
    PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client for health checks and backups
    postgresql-client \
    # Networking tools
    curl \
    wget \
    netcat-openbsd \
    # SSL/TLS support
    ca-certificates \
    openssl \
    # Process management
    tini \
    # Timezone data
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /var/cache/apt/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for security
RUN groupadd -r alkhorayef --gid=1000 && \
    useradd -r -g alkhorayef --uid=1000 --home-dir=/app --shell=/bin/bash alkhorayef

# Set working directory
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p \
    /app/logs \
    /app/data \
    /app/static \
    /app/ml-models \
    /app/.cache \
    /app/tmp \
    && chown -R alkhorayef:alkhorayef /app

# Copy application files
COPY --chown=alkhorayef:alkhorayef . /app/

# Create health check script
RUN echo '#!/bin/bash\n\
curl -f http://localhost:${API_PORT:-8000}/health || exit 1' > /app/healthcheck.sh \
    && chmod +x /app/healthcheck.sh \
    && chown alkhorayef:alkhorayef /app/healthcheck.sh

# Switch to non-root user
USER alkhorayef

# Expose ports
# 8000: Main API
# 8001: ML Service (optional)
# 9090: Prometheus metrics (optional)
EXPOSE 8000 8001 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD ["/app/healthcheck.sh"]

# Volume mounts for persistent data
VOLUME ["/app/logs", "/app/data", "/app/ml-models"]

# Use tini as init system (proper signal handling)
ENTRYPOINT ["/usr/bin/tini", "--"]

# Default command: Run with Gunicorn for production
CMD ["gunicorn", \
     "app:app", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--timeout", "120", \
     "--keepalive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "--graceful-timeout", "30", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100"]

# Alternative commands (override in docker-compose.yml or kubernetes):
# Development with auto-reload:
#   CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
#
# Direct Python execution:
#   CMD ["python", "app.py"]
#
# Custom worker count:
#   CMD ["gunicorn", "app:app", "--workers", "${GUNICORN_WORKERS:-4}", ...]
