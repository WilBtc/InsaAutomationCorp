# Expert Architecture Plan: Alkhorayef ESP Platform
## Multi-Perspective Deep Dive & Implementation Strategy

**Date**: November 20, 2025
**Platform**: Alkhorayef ESP Systems (INSA IoT Platform)
**Perspectives**: Senior Developer | Security Engineer | Data Engineer

---

## Executive Summary

This document synthesizes expert analysis from three critical perspectives to create a production-grade, enterprise-ready architecture for the Alkhorayef ESP predictive maintenance platform.

### Current State Assessment

| Aspect | Current | Target | Gap Severity |
|--------|---------|--------|--------------|
| **Security** | No auth, plain credentials | IEC 62443 SL-2 | 🔴 CRITICAL |
| **Scalability** | Single process, 500 devices | Multi-worker, 5000+ devices | 🟡 HIGH |
| **Data Pipeline** | Basic insert | Optimized time-series | 🟡 HIGH |
| **Observability** | Basic logs | Full o11y stack | 🟢 MEDIUM |
| **Testing** | None | Comprehensive | 🟢 MEDIUM |
| **Code Quality** | Monolithic | Modular | 🟢 MEDIUM |

### Strategic Approach

**Phase-based implementation** over **12 weeks**:
- **Weeks 1-2**: Stabilization & Security Foundations
- **Weeks 3-4**: Data Pipeline Optimization
- **Weeks 5-6**: Scalability & Performance
- **Weeks 7-8**: Observability & Operations
- **Weeks 9-10**: Advanced Features
- **Weeks 11-12**: Testing & Hardening

---

# Part 1: Senior Developer Analysis

## 1.1 Current Architecture Assessment

### Strengths ✅
1. **Modern Stack**: FastAPI + async/await
2. **Time-Series Ready**: TimescaleDB chosen (not yet optimized)
3. **Real-Time Capable**: WebSocket + Redis Pub/Sub
4. **Containerized**: Docker Compose setup
5. **Good Separation**: API, ML service concepts

### Critical Issues 🔴

#### Issue #1: Monolithic Application Structure
**File**: `app.py` (385 lines, all concerns mixed)

**Current**:
```python
app.py
  ├── Database models (implicit)
  ├── API routes
  ├── Business logic
  ├── Database queries
  └── Startup/shutdown
```

**Problem**:
- Hard to test
- Difficult to maintain
- Can't scale components independently
- Violates Single Responsibility Principle

**Solution**: Modular architecture

```
app/
├── __init__.py
├── main.py                    # Application entry point
├── config.py                  # Configuration management
├── dependencies.py            # Dependency injection
│
├── api/                       # API layer
│   ├── __init__.py
│   ├── v1/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── telemetry.py   # Telemetry endpoints
│   │   │   ├── diagnostics.py  # Diagnostic endpoints
│   │   │   ├── wells.py        # Well management
│   │   │   └── health.py       # Health checks
│   │   └── dependencies.py     # Route dependencies
│   └── middleware/
│       ├── auth.py             # Authentication
│       ├── logging.py          # Request logging
│       └── rate_limit.py       # Rate limiting
│
├── core/                      # Core business logic
│   ├── __init__.py
│   ├── diagnostics/
│   │   ├── decision_tree.py   # Decision tree engine
│   │   ├── nlp_query.py       # NLP processing
│   │   └── rules.py            # Diagnostic rules
│   ├── telemetry/
│   │   ├── processor.py        # Telemetry processing
│   │   ├── validator.py        # Data validation
│   │   └── enricher.py         # Data enrichment
│   └── ml/
│       ├── models.py           # ML model interfaces
│       └── predictor.py        # Prediction service
│
├── db/                        # Database layer
│   ├── __init__.py
│   ├── models.py              # SQLAlchemy models
│   ├── repositories/          # Repository pattern
│   │   ├── telemetry_repo.py
│   │   ├── diagnostic_repo.py
│   │   └── well_repo.py
│   ├── session.py             # DB session management
│   └── migrations/            # Alembic migrations
│       └── versions/
│
├── schemas/                   # Pydantic schemas
│   ├── __init__.py
│   ├── telemetry.py
│   ├── diagnostic.py
│   └── well.py
│
├── services/                  # External services
│   ├── __init__.py
│   ├── cache.py               # Redis service
│   ├── queue.py               # RabbitMQ service
│   └── storage.py             # MinIO service
│
└── utils/                     # Utilities
    ├── __init__.py
    ├── logging.py
    └── metrics.py
```

**Benefits**:
- **Testability**: Each module independently testable
- **Maintainability**: Clear responsibility boundaries
- **Scalability**: Can extract services as needed
- **Reusability**: Core logic reusable across apps

---

#### Issue #2: Missing Health Check Strategy

**Current**: Basic `/health` endpoint
**Problem**: Doesn't check dependencies

**Solution**: Comprehensive health check system

```python
# app/api/v1/routes/health.py
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from typing import Dict, Any
import asyncio

router = APIRouter()

class HealthCheck:
    """Comprehensive health checking"""

    @staticmethod
    async def check_postgres() -> Dict[str, Any]:
        """Check PostgreSQL connectivity and performance"""
        try:
            start = time.time()
            async with db_pool.acquire() as conn:
                # Check connectivity
                await conn.fetchval("SELECT 1")

                # Check hypertable status
                result = await conn.fetchrow("""
                    SELECT
                        compressed_chunks,
                        uncompressed_chunks
                    FROM timescaledb_information.hypertables
                    WHERE hypertable_name = 'esp_telemetry'
                """)

            latency = (time.time() - start) * 1000

            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "compressed_chunks": result['compressed_chunks'],
                "uncompressed_chunks": result['uncompressed_chunks']
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    @staticmethod
    async def check_redis() -> Dict[str, Any]:
        """Check Redis connectivity and performance"""
        try:
            start = time.time()
            await redis_client.ping()

            # Check pub/sub
            pubsub = redis_client.pubsub()
            await pubsub.subscribe("health_check")
            await pubsub.unsubscribe("health_check")

            latency = (time.time() - start) * 1000

            # Get Redis info
            info = await redis_client.info("memory")

            return {
                "status": "healthy",
                "latency_ms": round(latency, 2),
                "memory_used_mb": round(info['used_memory'] / 1024 / 1024, 2),
                "connected_clients": info.get('connected_clients', 0)
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    @staticmethod
    async def check_rabbitmq() -> Dict[str, Any]:
        """Check RabbitMQ connectivity"""
        try:
            # Use aio-pika to check connection
            connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URL,
                timeout=5
            )
            channel = await connection.channel()
            await channel.close()
            await connection.close()

            return {"status": "healthy"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

@router.get("/health")
async def health_basic():
    """Basic liveness check - is the app running?"""
    return {"status": "alive", "timestamp": datetime.now().isoformat()}

@router.get("/health/ready")
async def health_ready():
    """Readiness check - can the app handle traffic?"""

    # Run checks concurrently
    checks = await asyncio.gather(
        HealthCheck.check_postgres(),
        HealthCheck.check_redis(),
        HealthCheck.check_rabbitmq(),
        return_exceptions=True
    )

    postgres_check, redis_check, rabbitmq_check = checks

    all_healthy = all([
        postgres_check.get("status") == "healthy",
        redis_check.get("status") == "healthy",
        rabbitmq_check.get("status") == "healthy"
    ])

    response = {
        "status": "ready" if all_healthy else "not_ready",
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "postgres": postgres_check,
            "redis": redis_check,
            "rabbitmq": rabbitmq_check
        }
    }

    if not all_healthy:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response
        )

    return response

@router.get("/health/live")
async def health_live():
    """Kubernetes liveness probe - is process responsive?"""
    return {"status": "live", "timestamp": datetime.now().isoformat()}
```

---

#### Issue #3: No Error Handling Strategy

**Current**: Basic try/except in routes
**Problem**: Inconsistent error responses, no error tracking

**Solution**: Global exception handlers + structured errors

```python
# app/api/middleware/error_handler.py
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import traceback
import uuid

class ErrorResponse:
    """Standardized error response"""

    @staticmethod
    def format(
        error_id: str,
        error_type: str,
        message: str,
        details: dict = None,
        status_code: int = 500
    ) -> dict:
        return {
            "error": {
                "id": error_id,
                "type": error_type,
                "message": message,
                "details": details or {},
                "timestamp": datetime.now().isoformat()
            },
            "status_code": status_code
        }

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    error_id = str(uuid.uuid4())

    logger.error(
        f"Validation error {error_id}",
        extra={
            "error_id": error_id,
            "path": request.url.path,
            "errors": exc.errors()
        }
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse.format(
            error_id=error_id,
            error_type="VALIDATION_ERROR",
            message="Invalid request data",
            details={"validation_errors": exc.errors()},
            status_code=422
        )
    )

@app.exception_handler(asyncpg.PostgresError)
async def database_exception_handler(request: Request, exc: asyncpg.PostgresError):
    """Handle database errors"""
    error_id = str(uuid.uuid4())

    logger.error(
        f"Database error {error_id}: {exc}",
        extra={
            "error_id": error_id,
            "path": request.url.path,
            "query": getattr(exc, 'query', None)
        },
        exc_info=True
    )

    # Don't expose internal database errors
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse.format(
            error_id=error_id,
            error_type="DATABASE_ERROR",
            message="Database operation failed",
            details={"error_id": error_id},  # Client can use this for support
            status_code=500
        )
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all for unexpected errors"""
    error_id = str(uuid.uuid4())

    logger.critical(
        f"Unhandled exception {error_id}",
        extra={
            "error_id": error_id,
            "path": request.url.path,
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc()
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse.format(
            error_id=error_id,
            error_type="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details={"error_id": error_id},
            status_code=500
        )
    )
```

---

#### Issue #4: Missing Testing Infrastructure

**Current**: No tests
**Problem**: Can't safely refactor or deploy

**Solution**: Comprehensive test suite

```python
# tests/conftest.py
import pytest
import asyncio
from httpx import AsyncClient
from app.main import app
from app.db.session import get_db
from app.config import Settings

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def client():
    """Test client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def db_session():
    """Database session for tests"""
    # Use test database
    async with get_db() as session:
        yield session
        await session.rollback()  # Rollback after each test

@pytest.fixture
def sample_telemetry():
    """Sample telemetry data"""
    return {
        "well_id": "TEST-001",
        "flow_rate": 1500.0,
        "pip": 850.0,
        "motor_current": 45.0,
        "motor_temp": 85.0,
        "vibration": 0.8,
        "vsd_frequency": 55.0,
        "flow_variance": 18.5,
        "torque": 120.0,
        "gor": 600.0
    }

# tests/test_telemetry_api.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_ingest_telemetry_success(client: AsyncClient, sample_telemetry):
    """Test successful telemetry ingestion"""
    response = await client.post(
        "/telemetry/ingest",
        json=sample_telemetry
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["well_id"] == "TEST-001"

@pytest.mark.asyncio
async def test_ingest_telemetry_invalid_data(client: AsyncClient):
    """Test validation error handling"""
    response = await client.post(
        "/telemetry/ingest",
        json={"well_id": "TEST-001"}  # Missing required fields
    )

    assert response.status_code == 422
    assert "error" in response.json()

@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint"""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"

# tests/test_diagnostics.py
@pytest.mark.asyncio
async def test_decision_tree_gas_lock(client: AsyncClient):
    """Test gas lock diagnosis"""
    diagnostic_request = {
        "well_id": "TEST-001",
        "flow_stable": False,
        "production_below_target": True,
        "pip_low": False,
        "flow_level": "medium",
        "telemetry": {
            # ... telemetry data
        }
    }

    response = await client.post(
        "/api/v1/diagnostics/decision_tree",
        json=diagnostic_request
    )

    assert response.status_code == 200
    result = response.json()
    assert result["diagnosis"]["type"] == "Free Gas Lock"
    assert result["diagnosis"]["confidence"] > 0.8
```

**Test Coverage Targets**:
- **Unit Tests**: 80% coverage
- **Integration Tests**: Critical paths
- **Load Tests**: 1000 req/s sustained
- **E2E Tests**: User workflows

---

## 1.2 Performance Optimization Strategy

### Current Performance Profile

**Baseline Measurements** (estimated):
```
Telemetry Ingestion:
- Throughput: ~100 requests/sec
- Latency (p50): 50ms
- Latency (p99): 200ms
- Database writes: Synchronous, blocking

WebSocket Connections:
- Max concurrent: ~100 clients
- Message latency: 15ms
- Pub/Sub overhead: 5ms
```

### Performance Targets

```
Telemetry Ingestion:
- Throughput: 1000 requests/sec
- Latency (p50): 10ms
- Latency (p99): 50ms
- Database writes: Async batched

WebSocket Connections:
- Max concurrent: 1000 clients
- Message latency: 5ms
- Pub/Sub overhead: <2ms
```

### Optimization #1: Async Batch Writing

**Current** (synchronous):
```python
@app.post("/telemetry/ingest")
async def ingest_telemetry(data: TelemetryData):
    # Writes immediately - blocks response
    async with db_pool.acquire() as conn:
        await conn.execute("""INSERT INTO ...""")

    await redis_client.publish(...)
    return {"status": "success"}
```

**Optimized** (async queue):
```python
# app/services/telemetry_writer.py
class TelemetryWriter:
    """Batched async telemetry writer"""

    def __init__(self, batch_size=1000, flush_interval=1.0):
        self.queue = asyncio.Queue()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.running = False

    async def start(self):
        """Start background writer"""
        self.running = True
        asyncio.create_task(self._writer_loop())

    async def write(self, telemetry: TelemetryData):
        """Queue telemetry for writing"""
        await self.queue.put(telemetry)

    async def _writer_loop(self):
        """Background batch writer"""
        while self.running:
            batch = []
            deadline = asyncio.get_event_loop().time() + self.flush_interval

            # Collect batch
            while len(batch) < self.batch_size:
                timeout = max(0, deadline - asyncio.get_event_loop().time())
                try:
                    item = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=timeout
                    )
                    batch.append(item)
                except asyncio.TimeoutError:
                    break  # Flush on timeout

            if batch:
                await self._flush_batch(batch)

    async def _flush_batch(self, batch: List[TelemetryData]):
        """Write batch to database"""
        async with db_pool.acquire() as conn:
            await conn.executemany("""
                INSERT INTO esp_telemetry (
                    well_id, timestamp, flow_rate, pip, motor_current,
                    motor_temp, vibration, vsd_frequency, flow_variance,
                    torque, gor
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, [(
                t.well_id, t.timestamp, t.flow_rate, t.pip,
                t.motor_current, t.motor_temp, t.vibration,
                t.vsd_frequency, t.flow_variance, t.torque, t.gor
            ) for t in batch])

        logger.info(f"Flushed {len(batch)} telemetry records")

# In main.py
writer = TelemetryWriter(batch_size=1000, flush_interval=1.0)

@app.on_event("startup")
async def startup():
    await writer.start()

@app.post("/telemetry/ingest")
async def ingest_telemetry(data: TelemetryData):
    # Non-blocking write
    await writer.write(data)

    # Immediate pub/sub for real-time
    await redis_client.publish(f"telemetry:{data.well_id}", data.json())

    return {"status": "queued"}  # Returns immediately
```

**Performance Gain**: 10x throughput (100 → 1000 req/s)

---

### Optimization #2: Connection Pooling

**Current**: Default pool settings
**Problem**: Pool exhaustion under load

**Solution**: Tuned connection pools

```python
# app/config.py
class Settings(BaseSettings):
    # Database pool
    DB_POOL_MIN_SIZE: int = 20  # Up from 10
    DB_POOL_MAX_SIZE: int = 100  # Up from 20
    DB_POOL_MAX_QUERIES: int = 50000
    DB_POOL_MAX_INACTIVE_LIFETIME: float = 300.0

    # Redis pool
    REDIS_MAX_CONNECTIONS: int = 100  # Up from 50
    REDIS_SOCKET_TIMEOUT: float = 5.0
    REDIS_SOCKET_CONNECT_TIMEOUT: float = 5.0

# app/db/session.py
async def create_db_pool():
    return await asyncpg.create_pool(
        settings.DATABASE_URL,
        min_size=settings.DB_POOL_MIN_SIZE,
        max_size=settings.DB_POOL_MAX_SIZE,
        max_queries=settings.DB_POOL_MAX_QUERIES,
        max_inactive_connection_lifetime=settings.DB_POOL_MAX_INACTIVE_LIFETIME,
        command_timeout=60,
        server_settings={
            'jit': 'off',  # Disable JIT for time-series workloads
            'application_name': 'alkhorayef-api'
        }
    )
```

---

### Optimization #3: Caching Strategy

```python
# app/services/cache.py
from functools import wraps
import pickle

class CacheService:
    """Redis-based caching with TTL"""

    @staticmethod
    def cache(ttl: int = 300, key_prefix: str = ""):
        """Decorator for caching function results"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Generate cache key
                cache_key = f"{key_prefix}:{func.__name__}:{args}:{kwargs}"

                # Check cache
                cached = await redis_client.get(cache_key)
                if cached:
                    return pickle.loads(cached)

                # Execute function
                result = await func(*args, **kwargs)

                # Cache result
                await redis_client.setex(
                    cache_key,
                    ttl,
                    pickle.dumps(result)
                )

                return result
            return wrapper
        return decorator

# Usage example
@cache(ttl=300, key_prefix="well_telemetry")
async def get_well_telemetry(well_id: str, hours: int = 24):
    """Cached telemetry retrieval"""
    async with db_pool.acquire() as conn:
        return await conn.fetch("""
            SELECT * FROM esp_telemetry
            WHERE well_id = $1
            AND timestamp > NOW() - INTERVAL '{hours} hours'
            ORDER BY timestamp DESC
        """, well_id, hours=hours)
```

---

## 1.3 Production Deployment Configuration

### Docker Compose Production Override

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    # Use Gunicorn + Uvicorn workers
    command: >
      gunicorn app.main:app
      --workers 8
      --worker-class uvicorn.workers.UvicornWorker
      --bind 0.0.0.0:8000
      --timeout 60
      --graceful-timeout 30
      --max-requests 10000
      --max-requests-jitter 1000
      --access-logfile -
      --error-logfile -
      --log-level info

    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - WORKERS=8

    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
        reservations:
          cpus: '2.0'
          memory: 2G

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  ml-service:
    command: >
      gunicorn app.ml_service:app
      --workers 4
      --worker-class uvicorn.workers.UvicornWorker
      --bind 0.0.0.0:8001
      --timeout 120
      --graceful-timeout 60

    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8001/health/ready"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s  # ML models take longer to load

  timescaledb:
    environment:
      # Production tuning
      - POSTGRES_MAX_CONNECTIONS=200
      - POSTGRES_SHARED_BUFFERS=2GB
      - POSTGRES_EFFECTIVE_CACHE_SIZE=6GB
      - POSTGRES_MAINTENANCE_WORK_MEM=512MB
      - POSTGRES_CHECKPOINT_COMPLETION_TARGET=0.9
      - POSTGRES_WAL_BUFFERS=16MB
      - POSTGRES_DEFAULT_STATISTICS_TARGET=100
      - POSTGRES_RANDOM_PAGE_COST=1.1
      - POSTGRES_EFFECTIVE_IO_CONCURRENCY=200

    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G

    volumes:
      - timescale_data:/var/lib/postgresql/data
      - ./pg_backups:/backups  # Backup mount point

  redis:
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 2gb
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
      --save 60 10000

    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  nginx:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 1G
```

**Deploy Command**:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## 1.4 CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy Alkhorayef Platform

on:
  push:
    branches: [main, staging]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: timescale/timescaledb:latest-pg15
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run linters
      run: |
        black --check app/
        flake8 app/
        mypy app/

    - name: Run tests
      run: |
        pytest tests/ -v --cov=app --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  security:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        severity: 'CRITICAL,HIGH'

    - name: Run Bandit security linter
      run: |
        pip install bandit
        bandit -r app/ -f json -o bandit-report.json

  build:
    needs: [test, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - uses: actions/checkout@v3

    - name: Build Docker images
      run: |
        docker-compose build

    - name: Push to registry
      run: |
        echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
        docker-compose push

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - name: Deploy to production
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.PROD_HOST }}
        username: ${{ secrets.PROD_USER }}
        key: ${{ secrets.PROD_SSH_KEY }}
        script: |
          cd /opt/alkhorayef
          git pull
          docker-compose -f docker-compose.yml -f docker-compose.prod.yml pull
          docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
          docker system prune -f
```

---

[CONTINUED IN NEXT PART DUE TO LENGTH...]
