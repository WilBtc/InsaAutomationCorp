# Alkhorayef ESP IoT Platform - Configuration Guide

## Table of Contents

1. [Overview](#overview)
2. [Environment Setup](#environment-setup)
3. [Database Configuration](#database-configuration)
4. [Security Configuration](#security-configuration)
5. [Performance Tuning](#performance-tuning)
6. [Data Retention Policies](#data-retention-policies)
7. [Monitoring & Alerting](#monitoring--alerting)
8. [Production Deployment](#production-deployment)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Alkhorayef ESP IoT Platform uses environment variables for configuration management. This approach provides:

- **Security**: Sensitive credentials never committed to version control
- **Flexibility**: Different configurations for dev/staging/production
- **Simplicity**: Single source of truth for all settings
- **Portability**: Easy deployment across different environments

### Configuration Files

| File | Purpose | Version Control |
|------|---------|----------------|
| `.env` | Actual configuration values | **NEVER commit** |
| `.env.example` | Template with all variables | Committed |
| `pyproject.toml` | Tool configurations | Committed |
| `.gitignore` | Exclude sensitive files | Committed |

---

## Environment Setup

### Quick Start

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Generate secure secrets:**
   ```bash
   # JWT Secret Key
   python -c "import secrets; print(f'JWT_SECRET_KEY={secrets.token_urlsafe(32)}')"

   # Database Password
   python -c "import secrets; print(f'POSTGRES_PASSWORD={secrets.token_urlsafe(24)}')"

   # Redis Password
   python -c "import secrets; print(f'REDIS_PASSWORD={secrets.token_urlsafe(24)}')"
   ```

3. **Update critical values in `.env`:**
   - Replace all `CHANGE_ME_*` placeholders
   - Update database connection details
   - Configure external service credentials

4. **Validate configuration:**
   ```bash
   python -c "from dotenv import load_dotenv; load_dotenv(); import os; print('✓ Configuration loaded')"
   ```

### Environment-Specific Configurations

#### Development
```bash
# .env.development
ENVIRONMENT=development
DEBUG_MODE=true
LOG_LEVEL=DEBUG
AUTO_RELOAD=true
SQL_ECHO=true
ENABLE_API_DOCS=true
```

#### Staging
```bash
# .env.staging
ENVIRONMENT=staging
DEBUG_MODE=false
LOG_LEVEL=INFO
AUTO_RELOAD=false
ENABLE_API_DOCS=true
```

#### Production
```bash
# .env.production
ENVIRONMENT=production
DEBUG_MODE=false
LOG_LEVEL=WARNING
AUTO_RELOAD=false
SHOW_ERROR_DETAILS=false
ENABLE_API_DOCS=false  # Disable in production for security
```

---

## Database Configuration

### PostgreSQL + TimescaleDB

The platform uses PostgreSQL with TimescaleDB extension for time-series data.

#### Basic Connection
```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=esp_telemetry
POSTGRES_USER=alkhorayef
POSTGRES_PASSWORD=<your-secure-password>
```

#### Connection Pool Settings

Optimize for your workload:

```bash
# Minimum connections kept alive
DB_POOL_MIN_SIZE=10

# Maximum concurrent connections
# Formula: (CPU cores × 2) + effective_spindle_count
DB_POOL_MAX_SIZE=20

# Connection timeout in seconds
DB_POOL_TIMEOUT=30

# Maximum connection lifetime (prevent stale connections)
DB_MAX_CONNECTION_AGE=3600

# Query timeout (prevent runaway queries)
DB_QUERY_TIMEOUT=30
```

**Sizing Guidelines:**

| Environment | Min Size | Max Size | Workers |
|-------------|----------|----------|---------|
| Development | 2 | 5 | 1 |
| Staging | 5 | 10 | 2 |
| Production | 10 | 20 | 4-8 |

#### Database URLs

Two formats supported:

```bash
# Synchronous (psycopg2)
DATABASE_URL=postgresql://user:pass@host:port/dbname

# Asynchronous (asyncpg - recommended)
DATABASE_URL_ASYNC=postgresql+asyncpg://user:pass@host:port/dbname
```

---

## Security Configuration

### JWT Authentication

```bash
# Generate strong random key (32+ bytes)
JWT_SECRET_KEY=<output-from-secrets.token_urlsafe(32)>

# Algorithm (HS256 for symmetric, RS256 for asymmetric)
JWT_ALGORITHM=HS256

# Token expiration
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### CORS Configuration

```bash
# Comma-separated allowed origins
CORS_ORIGINS=https://app.alkhorayef.com,https://dashboard.alkhorayef.com

# Production: Disable wildcard
# CORS_ORIGINS=*  # ⚠️ NEVER use in production

CORS_ALLOW_CREDENTIALS=true
```

### API Rate Limiting

```bash
# Requests per minute per IP
RATE_LIMIT_PER_MINUTE=60

# For public endpoints, consider lower limits:
# - /health: 120/min
# - /telemetry/ingest: 1000/min (high throughput)
# - /api/v1/diagnostics: 30/min (computationally expensive)
```

### Password Hashing

Default: `bcrypt` with automatic salt

Configure in code if needed:
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

---

## Performance Tuning

### Gunicorn Workers

```bash
# Formula: (2 × CPU_cores) + 1
GUNICORN_WORKERS=9  # For 4-core server

# Worker class (ASGI for async)
GUNICORN_WORKER_CLASS=uvicorn.workers.UvicornWorker

# Request timeout
GUNICORN_TIMEOUT=120

# Keep-alive
GUNICORN_KEEPALIVE=5
```

### Redis Caching

```bash
# Connection pool
REDIS_MAX_CONNECTIONS=50

# Default cache TTL (5 minutes)
REDIS_DEFAULT_TTL=300

# For specific data:
# - Telemetry latest: 300s (5 min)
# - Diagnostics: 3600s (1 hour)
# - Well metadata: 86400s (24 hours)
```

### Application Performance

```bash
# Maximum request body size (10 MB)
MAX_REQUEST_SIZE=10485760

# Request timeout
REQUEST_TIMEOUT=60

# Background task processing
TASK_QUEUE_SIZE=1000
MAX_CONCURRENT_TASKS=10
```

### WebSocket Configuration

```bash
ENABLE_WEBSOCKET=true
WEBSOCKET_PING_INTERVAL=30
WEBSOCKET_PING_TIMEOUT=10
```

---

## Data Retention Policies

### Important Note on Data Retention

Per project requirements:
- **Azure backup**: Retains only **last 30 days** of IoT telemetry
- **Backup system**: Must have **ALL historical data**

Configure accordingly:

```bash
# IoT telemetry retention in primary database (30 days as per requirement)
TELEMETRY_RETENTION_DAYS=30

# Diagnostic results (keep longer for analysis)
DIAGNOSTICS_RETENTION_DAYS=90

# System logs
LOGS_RETENTION_DAYS=30

# Prometheus metrics
METRICS_RETENTION_DAYS=90
```

### Automated Cleanup

Enable automated cleanup jobs:

```bash
ENABLE_AUTOMATED_BACKUP=true

# Daily at 2 AM UTC
BACKUP_SCHEDULE=0 2 * * *

# Backup retention (must be longer than telemetry retention)
BACKUP_RETENTION_DAYS=90

# Azure Storage for backups
AZURE_STORAGE_ACCOUNT=alkhorayefbackup
AZURE_STORAGE_CONTAINER=esp-backups
AZURE_STORAGE_KEY=<your-key>
```

### Data Cleanup Script

Add to crontab or systemd timer:

```bash
# Cleanup old telemetry (keeps 30 days)
0 3 * * * /app/scripts/cleanup_old_telemetry.sh

# Archive to backup system before deletion
0 1 * * * /app/scripts/archive_to_backup.sh
```

---

## Monitoring & Alerting

### Prometheus Metrics

```bash
ENABLE_METRICS=true

# Metrics available at http://<host>:8000/metrics
# - Request duration histogram
# - Active connections gauge
# - Database pool statistics
# - Cache hit/miss ratio
```

### OpenTelemetry Tracing

```bash
ENABLE_TRACING=false  # Enable in production for debugging

# If enabled, configure exporter
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
```

### Email Alerts

```bash
ALERT_EMAIL_RECIPIENTS=ops@alkhorayef.com,admin@alkhorayef.com

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=alerts@alkhorayef.com
SMTP_PASSWORD=<app-specific-password>
SMTP_FROM=noreply@alkhorayef.com
```

### Slack Integration

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] All `CHANGE_ME_*` values replaced
- [ ] Strong random secrets generated
- [ ] Database passwords rotated from defaults
- [ ] CORS origins restricted (no wildcards)
- [ ] Debug mode disabled (`DEBUG_MODE=false`)
- [ ] API docs disabled or protected (`ENABLE_API_DOCS=false`)
- [ ] SSL/TLS certificates configured
- [ ] Backup system tested
- [ ] Monitoring dashboards configured
- [ ] Alert recipients verified

### Docker Deployment

```bash
# Build production image
docker build -t alkhorayef-esp:1.0.0 .

# Run with environment file
docker run -d \
  --name alkhorayef-esp \
  --env-file .env \
  -p 8000:8000 \
  -v /data/esp-logs:/app/logs \
  -v /data/esp-models:/app/ml-models \
  alkhorayef-esp:1.0.0
```

### Docker Compose

```yaml
version: '3.8'
services:
  api:
    build: .
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./ml-models:/app/ml-models
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "/app/healthcheck.sh"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Kubernetes ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: alkhorayef-esp-config
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  API_PORT: "8000"
  # Non-sensitive values only
```

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: alkhorayef-esp-secrets
type: Opaque
stringData:
  POSTGRES_PASSWORD: <base64-encoded>
  REDIS_PASSWORD: <base64-encoded>
  JWT_SECRET_KEY: <base64-encoded>
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failures

**Symptoms:**
```
asyncpg.exceptions.InvalidPasswordError
```

**Solutions:**
- Verify `POSTGRES_PASSWORD` matches PostgreSQL configuration
- Check `POSTGRES_HOST` is reachable: `ping <host>`
- Ensure PostgreSQL is listening: `netstat -an | grep 5432`
- Check firewall rules: `sudo ufw status`

#### 2. Redis Connection Errors

**Symptoms:**
```
redis.exceptions.ConnectionError
```

**Solutions:**
- Test Redis connectivity: `redis-cli -h <host> -p 6379 -a <password> ping`
- Verify `REDIS_PASSWORD` is correct
- Check Redis is running: `systemctl status redis`

#### 3. High Memory Usage

**Symptoms:**
- OOM kills
- Slow response times

**Solutions:**
```bash
# Reduce connection pool sizes
DB_POOL_MAX_SIZE=10
REDIS_MAX_CONNECTIONS=25

# Reduce worker count
GUNICORN_WORKERS=2

# Enable memory limits in Docker
docker run --memory=2g --memory-swap=2g ...
```

#### 4. Slow Query Performance

**Solutions:**
- Enable query logging: `SQL_ECHO=true`
- Check database indexes
- Optimize connection pool: `DB_POOL_MIN_SIZE=5`
- Increase query timeout: `DB_QUERY_TIMEOUT=60`

### Health Check Endpoint

Test system health:

```bash
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-11-20T12:00:00Z"
}
```

### Logging

```bash
# View application logs
docker logs -f alkhorayef-esp

# JSON structured logging
tail -f /app/logs/app.log | jq .

# Filter by level
grep "ERROR" /app/logs/app.log
```

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Tuning](https://wiki.postgresql.org/wiki/Tuning_Your_PostgreSQL_Server)
- [Redis Best Practices](https://redis.io/docs/manual/patterns/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/stable/configure.html)
- [TimescaleDB Documentation](https://docs.timescale.com/)

---

**Last Updated:** 2025-11-20
**Version:** 1.0.0
**Maintainer:** Alkhorayef Petroleum Company
