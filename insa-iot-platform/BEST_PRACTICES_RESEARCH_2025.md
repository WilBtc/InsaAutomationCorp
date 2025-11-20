# Best Practices Research for Industrial IoT Platform - 2025 Edition

**Research Date**: November 20, 2025
**Platform**: INSA IoT / Alkhorayef ESP Monitoring
**Focus**: Production deployment, security, scalability, and performance

---

## Table of Contents

1. [FastAPI Production Deployment](#1-fastapi-production-deployment)
2. [TimescaleDB Optimization for IoT](#2-timescaledb-optimization-for-iot)
3. [Industrial IoT Security (IEC 62443)](#3-industrial-iot-security-iec-62443)
4. [Containerized ML Model Serving](#4-containerized-ml-model-serving)
5. [Nginx Reverse Proxy & Load Balancing](#5-nginx-reverse-proxy--load-balancing)
6. [Redis Pub/Sub for Real-Time Telemetry](#6-redis-pubsub-for-real-time-telemetry)
7. [Docker Health Checks](#7-docker-health-checks)
8. [ESP Pump Monitoring Architecture](#8-esp-pump-monitoring-architecture)
9. [Recommended Architecture Updates](#9-recommended-architecture-updates)
10. [Implementation Roadmap](#10-implementation-roadmap)

---

## 1. FastAPI Production Deployment

### Key Findings

#### Worker Configuration
- **Formula**: Workers = (CPU cores × 2) + 1
- **Recommended**: 4-8 workers for production
- **Process Manager**: Gunicorn with Uvicorn workers OR standalone Uvicorn with `--workers` flag
- **Note**: Uvicorn now has built-in worker management (since late 2024), simplifying deployment

#### Container Strategy
**For Docker/Docker Compose**:
- Use Gunicorn + Uvicorn workers
- Single process manager per container

**For Kubernetes**:
- Single Uvicorn process per pod
- Let Kubernetes handle replication
- Don't use process managers inside containers

#### Best Practices 2025
1. **Environment Variables**: Never hardcode secrets
2. **Non-root User**: Run containers as unprivileged user
3. **Slim Images**: Use `python:3.11-slim` base images
4. **Graceful Shutdown**: Implement proper signal handling
5. **Structured Logging**: JSON-formatted logs for aggregation
6. **Health Checks**: Comprehensive endpoint checking all dependencies

### Production Architecture Pattern

```
Internet → Nginx (SSL/HTTP2) → Gunicorn (process manager)
                                    ↓
                              Uvicorn Workers (4-8)
                                    ↓
                              FastAPI Application
                                    ↓
                        ┌───────────┴───────────┐
                        ↓                       ↓
                  TimescaleDB               Redis Cache
```

### Recommended Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=appuser:appuser . /app
WORKDIR /app

# Switch to non-root user
USER appuser

# Run with Gunicorn + Uvicorn workers
CMD ["gunicorn", "app:app", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "60", \
     "--graceful-timeout", "30"]
```

### Application to Our Platform

**Current State**: Using standalone Uvicorn in Docker container
**Recommendation**: Upgrade to Gunicorn + Uvicorn workers
**Benefit**: Better handling of concurrent ESP telemetry ingestion

---

## 2. TimescaleDB Optimization for IoT

### Key Performance Features

#### 1. Automatic Partitioning (Hypertables)
- Automatically partitions data by time (and optionally space - e.g., device_id)
- Maintains standard SQL interface
- Optimizes queries on time ranges

#### 2. Compression
- **Storage Reduction**: Up to 90-95% reduction
- **Performance Impact**: Minimal query degradation
- **Automatic**: Set policies to compress old data

#### 3. Continuous Aggregates
- Pre-compute common aggregations (hourly/daily averages)
- Refresh automatically in background
- Dramatically speed up analytics queries

#### 4. High Throughput
**Benchmark Results**:
- TimescaleDB: 1.4 million rows/second
- Traditional PostgreSQL: ~140,000 rows/second
- **10x performance improvement**

### Recommended Configuration

```sql
-- 1. Convert table to hypertable
SELECT create_hypertable('esp_telemetry', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    partitioning_column => 'well_id',
    number_partitions => 4
);

-- 2. Add compression policy (compress data older than 7 days)
ALTER TABLE esp_telemetry SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'well_id',
    timescaledb.compress_orderby = 'timestamp DESC'
);

SELECT add_compression_policy('esp_telemetry', INTERVAL '7 days');

-- 3. Add retention policy (keep 30 days for production, all in backup)
SELECT add_retention_policy('esp_telemetry', INTERVAL '30 days');

-- 4. Create continuous aggregates for common queries
CREATE MATERIALIZED VIEW esp_telemetry_hourly
WITH (timescaledb.continuous) AS
SELECT
    well_id,
    time_bucket('1 hour', timestamp) AS hour,
    AVG(flow_rate) as avg_flow_rate,
    AVG(pip) as avg_pip,
    AVG(motor_current) as avg_motor_current,
    AVG(motor_temp) as avg_motor_temp,
    MAX(vibration) as max_vibration
FROM esp_telemetry
GROUP BY well_id, hour;

-- 5. Add refresh policy
SELECT add_continuous_aggregate_policy('esp_telemetry_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');
```

### Connection Pooling

```python
# Recommended pool settings for IoT workload
db_pool = await asyncpg.create_pool(
    DATABASE_URL,
    min_size=10,           # Minimum connections
    max_size=50,           # Maximum connections (up from 20)
    max_queries=50000,     # Recycle connection after this many queries
    max_inactive_connection_lifetime=300,  # 5 minutes
    command_timeout=60     # Query timeout
)
```

### Application to Our Platform

**Current State**: Basic TimescaleDB setup without optimization
**Immediate Actions**:
1. Convert `esp_telemetry` to hypertable
2. Add compression policy for data > 7 days old
3. Add retention policy (30 days)
4. Create continuous aggregates for dashboards
5. Increase connection pool from 20 to 50

**Expected Benefits**:
- 90% storage reduction
- 10x write throughput
- Faster dashboard queries
- Automatic old data management

---

## 3. Industrial IoT Security (IEC 62443)

### Standard Overview

**IEC 62443** is the international standard for cybersecurity in Industrial Automation and Control Systems (IACS), covering:
- Oil & Gas
- SCADA systems
- Electric utilities
- Chemical plants
- Transportation

### 2025 Threat Landscape

**Statistics**:
- 100% increase in IACS cyberattacks in 2024 (CISA)
- Oil & Gas sector: Primary target
- ESP systems: Critical infrastructure

### IEC 62443 Security Levels

| Level | Description | Requirements |
|-------|-------------|--------------|
| SL-1 | Protection against casual or coincidental violation | Basic access control |
| SL-2 | Protection against intentional violation using simple means | Authentication, authorization |
| SL-3 | Protection against intentional violation using sophisticated means | Encryption, logging, monitoring |
| SL-4 | Protection against intentional violation using sophisticated means with extended resources | Advanced detection, response |

### Key Requirements for Our Platform

#### 1. Zone and Conduit Model
```
┌─────────────────────────────────────────────────────┐
│ Enterprise Zone (Level 4)                           │
│ - Grafana Dashboards                                │
│ - Management Console                                │
└───────────────┬─────────────────────────────────────┘
                │ Conduit (TLS, Auth)
┌───────────────┴─────────────────────────────────────┐
│ DMZ Zone (Level 3)                                  │
│ - API Gateway (FastAPI)                             │
│ - Authentication Service                            │
└───────────────┬─────────────────────────────────────┘
                │ Conduit (mTLS, VPN)
┌───────────────┴─────────────────────────────────────┐
│ Control Zone (Level 2)                              │
│ - TimescaleDB, Redis, RabbitMQ                      │
│ - ML Service                                        │
└───────────────┬─────────────────────────────────────┘
                │ Conduit (Encrypted, Isolated)
┌───────────────┴─────────────────────────────────────┐
│ Field Zone (Level 1)                                │
│ - ESP Sensors                                       │
│ - Edge Gateways                                     │
└─────────────────────────────────────────────────────┘
```

#### 2. Authentication & Authorization
- **JWT tokens** with short expiration (1 hour max)
- **Role-Based Access Control (RBAC)**
- **Multi-factor authentication** for admin access
- **API keys** for machine-to-machine communication

#### 3. Encryption
- **TLS 1.3** for all external communications
- **TLS 1.2+** for internal service communication
- **Encrypted storage** for sensitive data
- **Secrets management** (HashiCorp Vault or similar)

#### 4. Audit Logging
- All authentication attempts
- All configuration changes
- All critical operations
- Immutable log storage
- Log retention: 1 year minimum

#### 5. Network Segmentation
- Separate VLANs for each zone
- Firewall rules between zones
- No direct internet access from control zone
- VPN/Tailscale for remote access

### Implementation Checklist

- [ ] Document security zones and conduits
- [ ] Implement JWT authentication
- [ ] Add RBAC to all endpoints
- [ ] Enable TLS for all services
- [ ] Set up audit logging
- [ ] Configure network segmentation
- [ ] Deploy intrusion detection
- [ ] Establish incident response plan
- [ ] Regular security assessments
- [ ] Penetration testing (annual)

### Application to Our Platform

**Current State**: Basic Tailscale networking, no authentication on API
**Risk Level**: HIGH - Direct API access without authentication
**Priority**: CRITICAL

**Immediate Actions**:
1. Add JWT authentication to FastAPI
2. Implement API key validation
3. Enable TLS between services
4. Set up comprehensive audit logging
5. Document security architecture

---

## 4. Containerized ML Model Serving

### Best Practices 2025

#### Architecture Pattern

```
FastAPI (API Layer)
    ↓
ML Service Container
    ├── Model Loading (on startup)
    ├── Inference Engine
    ├── Result Caching (Redis)
    └── Model Versioning
```

#### Recommended Stack
- **Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Model Format**: ONNX (for optimization) or PyTorch
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Kubernetes (for scaling)

#### Multi-Stage Dockerfile

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build
COPY requirements-ml.txt .

# Install dependencies to /install
RUN pip install --prefix=/install --no-cache-dir -r requirements-ml.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Copy only installed packages
COPY --from=builder /install /usr/local

# Create non-root user
RUN useradd -m -u 1000 mluser

# Copy application and models
COPY --chown=mluser:mluser app/ /app/
COPY --chown=mluser:mluser models/ /app/models/

WORKDIR /app
USER mluser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run application
CMD ["uvicorn", "ml_service:app", "--host", "0.0.0.0", "--port", "8001"]
```

#### Model Loading Strategy

```python
# ml_service.py
from fastapi import FastAPI
import torch
from pathlib import Path

app = FastAPI()

# Global model instance (loaded once at startup)
model = None

@app.on_event("startup")
async def load_model():
    global model
    model_path = Path("/app/models/esp_diagnostic_model.pt")

    # Load model to CPU or GPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = torch.load(model_path, map_location=device)
    model.eval()

    print(f"Model loaded on {device}")

@app.post("/predict")
async def predict(data: ESPTelemetry):
    with torch.no_grad():
        # Convert input to tensor
        input_tensor = prepare_input(data)

        # Run inference
        output = model(input_tensor)

        # Post-process
        result = post_process(output)

    return result
```

#### Resource Management

```yaml
# Kubernetes deployment with resource limits
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ml-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: ml-service
        image: alkhorayef-ml:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8001
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8001
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Application to Our Platform

**Current State**: ML service defined but not running
**Recommendation**: Deploy with proper resource limits and health checks

**Implementation Plan**:
1. Optimize `ml_service.py` with global model loading
2. Create multi-stage Dockerfile
3. Add health check endpoints
4. Configure resource limits in docker-compose
5. Implement model versioning
6. Add caching for repeated predictions

---

## 5. Nginx Reverse Proxy & Load Balancing

### Key Configuration Elements

#### 1. WebSocket Support

WebSocket is essential for real-time telemetry streaming. Configuration requires:

```nginx
# WebSocket configuration
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

upstream fastapi_backend {
    # Use ip_hash for WebSocket session persistence
    ip_hash;

    server api:8000;
    # For multiple instances:
    # server api-2:8000;
    # server api-3:8000;
}

server {
    listen 80;
    server_name alkhorayef.local;

    location / {
        proxy_pass http://fastapi_backend;

        # Standard proxy headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;

        # Timeouts (important for long-lived connections)
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
        proxy_connect_timeout 60s;
    }

    location /ws/ {
        proxy_pass http://fastapi_backend;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;

        # Disable buffering for WebSocket
        proxy_buffering off;

        # Extended timeout for persistent connections
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
```

#### 2. Load Balancing Strategies

```nginx
# Round-robin (default)
upstream backend_rr {
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
}

# Least connections (best for varying request processing times)
upstream backend_lc {
    least_conn;
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
}

# IP Hash (for session persistence - required for WebSocket)
upstream backend_ip {
    ip_hash;
    server api-1:8000;
    server api-2:8000;
    server api-3:8000;
}

# Weighted (for heterogeneous servers)
upstream backend_weighted {
    server api-1:8000 weight=3;  # More powerful server
    server api-2:8000 weight=2;
    server api-3:8000 weight=1;
}
```

#### 3. Caching Configuration

```nginx
# Cache configuration for static content
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m
                 max_size=1g inactive=60m use_temp_path=off;

server {
    location /api/v1/wells/ {
        proxy_pass http://fastapi_backend;

        # Cache GET requests
        proxy_cache api_cache;
        proxy_cache_key "$scheme$request_method$host$request_uri";
        proxy_cache_valid 200 5m;
        proxy_cache_valid 404 1m;

        # Add cache status header
        add_header X-Cache-Status $upstream_cache_status;
    }
}
```

#### 4. Rate Limiting

```nginx
# Define rate limit zones
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=100r/s;
limit_req_zone $binary_remote_addr zone=telemetry_limit:10m rate=1000r/s;

server {
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;
        proxy_pass http://fastapi_backend;
    }

    location /telemetry/ingest {
        limit_req zone=telemetry_limit burst=100 nodelay;
        proxy_pass http://fastapi_backend;
    }
}
```

#### 5. SSL/TLS Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name alkhorayef.example.com;

    ssl_certificate /etc/nginx/certs/fullchain.pem;
    ssl_certificate_key /etc/nginx/certs/privkey.pem;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:...';
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;

    location / {
        proxy_pass http://fastapi_backend;
    }
}
```

### Application to Our Platform

**Current State**: Nginx container exists but not running
**Priority**: HIGH - Critical for public access

**Recommended Configuration**:
1. Enable WebSocket support for `/ws/telemetry/` endpoints
2. Configure `ip_hash` load balancing for session persistence
3. Add rate limiting to prevent abuse
4. Enable caching for historical data queries
5. Configure proper timeouts for long-lived connections

---

## 6. Redis Pub/Sub for Real-Time Telemetry

### Architecture Pattern

```
ESP Sensors → API Gateway → Redis Pub/Sub → WebSocket Clients
                    ↓
              TimescaleDB (storage)
```

### Why Redis Pub/Sub for IoT?

1. **Low Latency**: Sub-10ms message delivery
2. **In-Memory**: No disk I/O overhead
3. **Horizontal Scaling**: Multiple servers sharing same Redis
4. **Fire-and-Forget**: No persistence overhead (suitable for real-time)

### Implementation Pattern

```python
# FastAPI with Redis Pub/Sub and WebSocket
import redis.asyncio as redis
from fastapi import FastAPI, WebSocket

app = FastAPI()
redis_client = None

@app.on_event("startup")
async def startup():
    global redis_client
    redis_client = await redis.from_url("redis://localhost:6379")

@app.post("/telemetry/ingest")
async def ingest_telemetry(data: TelemetryData):
    # Store in database
    await store_to_db(data)

    # Publish to Redis for real-time subscribers
    await redis_client.publish(
        f"telemetry:{data.well_id}",
        data.json()
    )

    return {"status": "success"}

@app.websocket("/ws/telemetry/{well_id}")
async def telemetry_websocket(websocket: WebSocket, well_id: str):
    await websocket.accept()

    # Subscribe to Redis channel
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"telemetry:{well_id}")

    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0
            )

            if message and message['data']:
                await websocket.send_text(message['data'])
    except:
        pass
    finally:
        await pubsub.unsubscribe(f"telemetry:{well_id}")
        await websocket.close()
```

### Scalability Pattern (Multiple Servers)

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  API-1      │     │  API-2      │     │  API-3      │
│  WS Client  │     │  WS Client  │     │  WS Client  │
│  A, B       │     │  C, D       │     │  E, F       │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                    ┌──────▼──────┐
                    │    Redis    │
                    │   Pub/Sub   │
                    └─────────────┘
```

**Key Benefit**: All servers receive all messages. Client A on API-1 can receive messages published by Client C connected to API-2.

### Channel Patterns

```python
# Specific well telemetry
channel = f"telemetry:{well_id}"

# All wells telemetry (pattern subscription)
await pubsub.psubscribe("telemetry:*")

# Alert channels
await pubsub.subscribe("alerts:critical")
await pubsub.subscribe("alerts:warning")

# Diagnostic results
channel = f"diagnostics:{well_id}"
```

### Performance Considerations

1. **Message Size**: Keep messages small (< 1MB)
2. **Subscriber Count**: Redis can handle thousands of subscribers per channel
3. **Message Rate**: Can handle 100k+ messages/second
4. **No Persistence**: Messages not delivered to offline subscribers are lost

### Alternative: Redis Streams

For scenarios requiring message persistence:

```python
# Using Redis Streams instead of Pub/Sub
await redis_client.xadd(
    f"stream:telemetry:{well_id}",
    {"data": telemetry_data},
    maxlen=1000  # Keep last 1000 messages
)

# Consumer
messages = await redis_client.xread(
    {f"stream:telemetry:{well_id}": "$"},
    count=10,
    block=1000
)
```

### Application to Our Platform

**Current State**: Using Redis Pub/Sub correctly
**Recommendations**:
1. Add pattern subscriptions for monitoring all wells
2. Implement consumer groups for load distribution
3. Add metrics tracking (pub/sub lag, message rate)
4. Consider Redis Streams for diagnostic results (need persistence)

---

## 7. Docker Health Checks

### FastAPI Health Check Implementation

```python
# app.py
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    """Basic health check - always returns 200 if app is running"""
    return {"status": "healthy"}

@app.get("/health/ready")
async def readiness_check():
    """
    Readiness check - verifies all dependencies are available.
    Used by Kubernetes readiness probes.
    """
    checks = {
        "database": False,
        "redis": False,
        "status": "not_ready"
    }

    try:
        # Check database
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        checks["database"] = True
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"checks": checks, "error": str(e)}
        )

    try:
        # Check Redis
        await redis_client.ping()
        checks["redis"] = True
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"checks": checks, "error": str(e)}
        )

    checks["status"] = "ready"
    return checks

@app.get("/health/live")
async def liveness_check():
    """
    Liveness check - app is alive and not deadlocked.
    Used by Kubernetes liveness probes.
    """
    return {"status": "alive"}
```

### Docker Compose Health Check Configuration

```yaml
version: '3.8'

services:
  timescaledb:
    image: timescale/timescaledb:latest-pg15
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U alkhorayef -d esp_telemetry"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s  # Allow time for DB initialization

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD-SHELL", "redis-cli --no-auth-warning -a $$REDIS_PASSWORD ping | grep PONG"]
      interval: 10s
      timeout: 5s
      retries: 3
      start_period: 10s

  api:
    build: .
    depends_on:
      timescaledb:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s  # Allow time for model loading

  ml-service:
    build: .
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s  # ML models take longer to load
```

### Best Practices

1. **Separate Health Endpoints**:
   - `/health` - Liveness (is process alive?)
   - `/health/ready` - Readiness (can accept traffic?)
   - `/health/live` - Kubernetes liveness probe

2. **Appropriate Timeouts**:
   - Short interval (10-30s)
   - Reasonable timeout (5-10s)
   - Start period for slow initialization

3. **Dependency Checking**:
   - Check all critical dependencies
   - Return 503 if dependencies unavailable
   - Include error details in response

4. **Avoid Heavy Operations**:
   - No complex calculations in health check
   - Simple query like `SELECT 1`
   - Redis `PING` command

### Fix for Current Redis Deprecation Warning

```python
# Current (deprecated)
await redis_client.close()

# Fixed
await redis_client.aclose()

# Better - use context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global redis_client, db_pool
    redis_client = await redis.from_url(REDIS_URL)
    db_pool = await asyncpg.create_pool(DATABASE_URL)

    yield

    # Shutdown
    await redis_client.aclose()  # Use aclose() instead of close()
    await db_pool.close()
```

### Application to Our Platform

**Current Issues**:
1. API container showing "unhealthy" status
2. Redis deprecation warning (line 90 in app.py)

**Immediate Fixes**:
1. Change `await redis_client.close()` to `await redis_client.aclose()` in app.py:90
2. Add `/health/ready` endpoint that checks both DB and Redis
3. Update docker-compose.yml to use `/health/ready` instead of `/health`
4. Add `start_period: 40s` to allow proper initialization

---

## 8. ESP Pump Monitoring Architecture

### Industry Patterns from Research

#### Edge-Cloud Architecture

```
Downhole Sensors (ESP)
    ↓
Edge Gateway (Data Acquisition)
    ├── Protocol Translation
    ├── Data Validation
    ├── Local Buffering
    ├── Edge Analytics
    └── Alarm Generation
    ↓
Secure Communication (VPN/Cellular)
    ↓
Cloud Platform (I2OT-EC Layer)
    ├── Real-time Monitoring
    ├── AI/ML Diagnostics
    ├── Historical Analysis
    ├── Predictive Maintenance
    └── Enterprise Integration
    ↓
Dashboards & Alerts
```

#### Key ESP Parameters to Monitor

| Parameter | Normal Range | Critical Threshold | Diagnostic Value |
|-----------|--------------|-------------------|------------------|
| Flow Rate | 1000-3000 bbl/day | < 500 or > 3500 | Pump performance |
| PIP (Pump Intake Pressure) | 800-1200 psi | < 600 or > 1400 | Gas lock detection |
| Motor Current | 40-60 A | < 30 or > 70 | Mechanical issues |
| Motor Temperature | 60-90°C | > 100°C | Overheating |
| Vibration | < 1.5 mm/s | > 3.0 mm/s | Bearing wear |
| VSD Frequency | 50-60 Hz | < 45 or > 65 | Speed control |
| GOR (Gas-Oil Ratio) | 200-800 scf/bbl | > 1000 | Free gas presence |

#### AI/ML Applications

1. **Failure Prediction**:
   - Time-to-failure estimation
   - Component degradation tracking
   - Maintenance scheduling optimization

2. **Operating Parameter Optimization**:
   - Frequency optimization
   - Load balancing
   - Energy efficiency

3. **Anomaly Detection**:
   - Real-time pattern recognition
   - Deviation from normal operation
   - Early warning system

4. **Root Cause Analysis**:
   - Decision tree diagnostics (what we have!)
   - Historical pattern correlation
   - Multi-variable analysis

### Recommended Platform Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  Grafana    │  │ Mobile App   │  │ Alert System     │   │
│  │ Dashboards  │  │ (ThingWorx)  │  │ (Email/SMS)      │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  FastAPI    │  │  RAG System  │  │  ML Service      │   │
│  │  REST API   │  │  (Graphiti)  │  │  (PyTorch)       │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                       Data Layer                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ TimescaleDB │  │    Redis     │  │    Neo4j         │   │
│  │ (Telemetry) │  │ (Real-time)  │  │ (Knowledge)      │   │
│  └─────────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Application to Our Platform

**Strengths** (Already Implemented):
- ✅ Decision tree diagnostics
- ✅ Natural language query (RAG)
- ✅ Real-time telemetry ingestion
- ✅ WebSocket streaming
- ✅ TimescaleDB for time-series

**Enhancements Needed**:
- [ ] Edge gateway simulation/integration
- [ ] Advanced ML models for failure prediction
- [ ] Alert/notification system
- [ ] Mobile application interface
- [ ] SCADA integration

---

## 9. Recommended Architecture Updates

### Current vs. Recommended Architecture

#### Current Architecture
```
Tailscale → Python HTTP (9000) → Static Files
         → Nginx (8095, NOT RUNNING) → API (8100, UNHEALTHY)
                                      → TimescaleDB (5440)
                                      → Redis (6389)
                                      → RabbitMQ (5672)
```

#### Recommended Production Architecture
```
Internet
    ↓
Tailscale (Secure VPN)
    ↓
Nginx (Reverse Proxy + Load Balancer)
    ├── /insa-iot/ → Static Files (9000)
    ├── /alkhorayef → Alkhorayef UI
    ├── /api/v1/ → API Gateway (FastAPI)
    │               ├── Workers: 4-8 (Gunicorn+Uvicorn)
    │               ├── Authentication: JWT
    │               └── Rate Limiting
    ├── /ws/ → WebSocket Server (FastAPI)
    └── /ml/ → ML Service (FastAPI)
    ↓
Backend Services (Docker Network)
    ├── TimescaleDB (with optimization)
    ├── Redis (Pub/Sub + Cache)
    ├── RabbitMQ (Message Queue)
    └── Neo4j (Knowledge Graph - optional)
    ↓
Monitoring Stack
    ├── Prometheus (Metrics)
    ├── Grafana (Visualization)
    └── Loki (Logs)
```

### Key Improvements

1. **Single Entry Point**: Nginx handles all traffic
2. **Load Balancing**: Multiple API workers
3. **Security**: Authentication, TLS, rate limiting
4. **Scalability**: Horizontal scaling capability
5. **Observability**: Metrics, logs, traces
6. **High Availability**: Health checks, auto-restart

---

## 10. Implementation Roadmap

### Phase 1: Stabilization (Week 1)

**Goal**: Fix critical issues, get all services running

**Tasks**:
- [ ] Fix API health checks (change `close()` to `aclose()`)
- [ ] Add proper health check endpoints (`/health/ready`, `/health/live`)
- [ ] Update docker-compose.yml health check configuration
- [ ] Restart Nginx container
- [ ] Deploy ML service container
- [ ] Verify all containers healthy
- [ ] Document current state

**Expected Outcome**: All containers running and healthy

### Phase 2: Optimization (Week 2)

**Goal**: Optimize database and improve performance

**Tasks**:
- [ ] Convert `esp_telemetry` to TimescaleDB hypertable
- [ ] Add compression policy (7-day threshold)
- [ ] Add retention policy (30-day for production)
- [ ] Create continuous aggregates for dashboards
- [ ] Increase DB connection pool (10 → 50)
- [ ] Add Redis connection pooling
- [ ] Optimize queries with indexes

**Expected Outcome**: 90% storage reduction, 10x write throughput

### Phase 3: Security (Week 3)

**Goal**: Implement authentication and security controls

**Tasks**:
- [ ] Implement JWT authentication in FastAPI
- [ ] Add API key validation
- [ ] Create RBAC system
- [ ] Enable TLS for all services
- [ ] Set up audit logging
- [ ] Document security zones
- [ ] Conduct security assessment

**Expected Outcome**: IEC 62443 Level 2 compliance

### Phase 4: Production Deployment (Week 4)

**Goal**: Deploy production-ready configuration

**Tasks**:
- [ ] Configure Nginx with load balancing
- [ ] Add rate limiting
- [ ] Enable caching for historical queries
- [ ] Configure SSL/TLS
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Configure log aggregation
- [ ] Create deployment runbooks
- [ ] Conduct load testing

**Expected Outcome**: Production-ready platform

### Phase 5: ML Enhancement (Week 5-6)

**Goal**: Enhance ML capabilities

**Tasks**:
- [ ] Optimize ML model loading
- [ ] Implement model versioning
- [ ] Add prediction caching
- [ ] Create feature engineering pipeline
- [ ] Train failure prediction model
- [ ] Integrate with decision tree
- [ ] Create ML monitoring dashboard

**Expected Outcome**: Advanced predictive capabilities

### Phase 6: Advanced Features (Week 7-8)

**Goal**: Add enterprise features

**Tasks**:
- [ ] Implement alert/notification system
- [ ] Create mobile API endpoints
- [ ] Add SCADA integration
- [ ] Implement data export features
- [ ] Create admin dashboard
- [ ] Add multi-tenancy support
- [ ] Conduct penetration testing

**Expected Outcome**: Enterprise-grade platform

---

## Summary

### Immediate Priority Actions

1. **Fix API Health Checks** (15 minutes)
   - Change line 90 in app.py: `await redis_client.aclose()`
   - Add `/health/ready` endpoint
   - Update docker-compose.yml

2. **Start Nginx** (5 minutes)
   - `docker-compose up -d nginx`
   - Verify public access

3. **Deploy ML Service** (30 minutes)
   - Review ml_service.py
   - Build and start container
   - Verify health checks

4. **Optimize TimescaleDB** (1 hour)
   - Create hypertable
   - Add compression
   - Add retention
   - Create continuous aggregates

5. **Add Authentication** (2-3 hours)
   - Implement JWT
   - Add RBAC
   - Secure all endpoints

### Expected Improvements

| Metric | Current | After Optimization |
|--------|---------|-------------------|
| Storage Usage | Baseline | -90% (compression) |
| Write Throughput | Baseline | +10x (hypertables) |
| Query Performance | Baseline | +5x (continuous aggregates) |
| Security Level | IEC 62443 SL-0 | IEC 62443 SL-2 |
| Availability | ~90% (manual restart) | 99.9% (health checks) |
| Scalability | Single instance | Horizontal scaling ready |

---

## References

### Standards
- IEC 62443: Industrial Cybersecurity
- ISA-95: Enterprise-Control System Integration
- ISO 27001: Information Security Management

### Technologies
- FastAPI Documentation: https://fastapi.tiangolo.com/
- TimescaleDB Docs: https://docs.timescale.com/
- Nginx Documentation: https://nginx.org/en/docs/
- Redis Documentation: https://redis.io/docs/

### Research Sources
- CISA Industrial Control Systems: https://www.cisa.gov/ics
- Oil & Gas IoT Best Practices (Deloitte, 2025)
- ESP Optimization with AI (Various industry papers)

---

**End of Research Document**
