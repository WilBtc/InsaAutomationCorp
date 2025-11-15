# Multi-stage Docker build for Insa-iot Platform
# Production-ready Python application

# Stage 1: Builder
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY iot-platform/requirements.txt requirements.txt
COPY iot-platform/requirements-new-features.txt requirements-new.txt

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt && \
    pip install --no-cache-dir --user -r requirements-new.txt && \
    pip install --no-cache-dir --user gunicorn==21.2.0

# Stage 2: Runtime
FROM python:3.11-slim

# Set metadata
LABEL maintainer="Insa-iot Team"
LABEL description="Industrial IoT Platform with AI Security"
LABEL version="2.0"

# Create non-root user
RUN useradd --create-home --shell /bin/bash iiot && \
    mkdir -p /app && \
    chown -R iiot:iiot /app

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /home/iiot/.local

# Copy application code
COPY --chown=iiot:iiot iot-platform/ /app/

# Set environment variables
ENV PATH=/home/iiot/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=5000 \
    ENVIRONMENT=production

# Switch to non-root user
USER iiot

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Default command
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
