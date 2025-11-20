# Rate Limiting Integration Guide

## Quick Start

This guide shows how to integrate the rate limiting system into your FastAPI application.

## Installation

Dependencies are already in `requirements.txt`:
```bash
pip install redis==5.0.1 hiredis==2.2.3
```

## Basic Integration

### Step 1: Initialize Redis Connection

```python
import redis.asyncio as redis
from app.core.rate_limiter import create_rate_limiter

# In your FastAPI app startup
@app.on_event("startup")
async def startup():
    # Create Redis client
    app.state.redis = await redis.from_url(
        "redis://localhost:6379/0",
        encoding="utf-8",
        decode_responses=True
    )

    # Create rate limiter
    app.state.rate_limiter = await create_rate_limiter(app.state.redis)
```

### Step 2: Add Middleware

```python
from app.api.middleware.rate_limit_middleware import RateLimitMiddleware

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    rate_limiter=app.state.rate_limiter,
    enable_rate_limiting=True
)
```

### Step 3: Add Admin Routes

```python
from app.api.routes.rate_limits import router as rate_limits_router

# Include admin routes
app.include_router(rate_limits_router)
```

## Complete Example

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis

from app.core.rate_limiter import create_rate_limiter
from app.api.middleware.rate_limit_middleware import RateLimitMiddleware
from app.api.routes.rate_limits import router as rate_limits_router

app = FastAPI(title="Alkhorayef ESP IoT Platform")

@app.on_event("startup")
async def startup():
    # Initialize Redis
    app.state.redis = await redis.from_url(
        "redis://localhost:6379/0",
        encoding="utf-8",
        decode_responses=True
    )

    # Initialize rate limiter
    app.state.rate_limiter = await create_rate_limiter(app.state.redis)

@app.on_event("shutdown")
async def shutdown():
    await app.state.redis.close()

# Add CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
app.add_middleware(
    RateLimitMiddleware,
    rate_limiter=app.state.rate_limiter,
    enable_rate_limiting=True
)

# Include admin routes
app.include_router(rate_limits_router)

# Your other routes
@app.get("/api/v1/data")
async def get_data():
    return {"data": "example"}
```

## Environment Configuration

Create `.env` file:

```bash
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
REDIS_DB=0

# Rate Limiting
RATE_LIMIT_ENABLED=true

# Admin Limits
RATE_LIMIT_ADMIN_PER_MINUTE=1000
RATE_LIMIT_ADMIN_PER_HOUR=50000
RATE_LIMIT_ADMIN_PER_DAY=1000000

# Operator Limits
RATE_LIMIT_OPERATOR_PER_MINUTE=500
RATE_LIMIT_OPERATOR_PER_HOUR=25000
RATE_LIMIT_OPERATOR_PER_DAY=500000

# Viewer Limits
RATE_LIMIT_VIEWER_PER_MINUTE=100
RATE_LIMIT_VIEWER_PER_HOUR=5000
RATE_LIMIT_VIEWER_PER_DAY=100000

# Anonymous Limits
RATE_LIMIT_ANONYMOUS_PER_MINUTE=10
RATE_LIMIT_ANONYMOUS_PER_HOUR=100
RATE_LIMIT_ANONYMOUS_PER_DAY=1000

# Global Limit
RATE_LIMIT_GLOBAL_PER_MINUTE=10000

# Burst Handling
RATE_LIMIT_BURST_MULTIPLIER=2.0
RATE_LIMIT_BURST_DURATION=10

# IP Whitelist (comma-separated)
RATE_LIMIT_WHITELIST_IPS=10.0.0.1,10.0.0.2
```

## Custom Rate Limits on Endpoints

Use the `@rate_limit` decorator:

```python
from app.core.rate_limiter import rate_limit

@app.post("/api/v1/expensive-operation")
@rate_limit(limit=10, per="hour", burst_multiplier=1.5)
async def expensive_operation():
    # Expensive computation
    return {"result": "success"}
```

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/test_rate_limiting.py -v

# Run performance tests
python scripts/test_rate_limiting_performance.py
```

## Monitoring

### Prometheus Metrics

Rate limiting automatically exports Prometheus metrics:

```python
from prometheus_client import make_asgi_app

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

Available metrics:
- `rate_limit_checks_total` - Total checks (with result, limit_type, role labels)
- `rate_limit_remaining` - Remaining tokens (with user_id, window, limit_type labels)
- `rate_limit_check_duration_seconds` - Check duration histogram

### Grafana Dashboard

Example PromQL queries:

```promql
# Rate limit check rate
rate(rate_limit_checks_total[5m])

# Rate limit denial rate
rate(rate_limit_checks_total{result="denied"}[5m])

# Average check duration
rate(rate_limit_check_duration_seconds_sum[5m]) / rate(rate_limit_check_duration_seconds_count[5m])

# Users hitting limits
count by (user_id) (rate_limit_checks_total{result="denied"})
```

## Production Deployment

### Redis High Availability

Use Redis Sentinel or Redis Cluster:

```python
from redis.sentinel import Sentinel

sentinel = Sentinel([
    ('sentinel1', 26379),
    ('sentinel2', 26379),
    ('sentinel3', 26379)
])

redis_client = sentinel.master_for(
    'mymaster',
    socket_timeout=0.1,
    decode_responses=True
)
```

### Performance Tuning

1. **Redis Connection Pooling**
```python
redis_pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50
)
redis_client = redis.Redis(connection_pool=redis_pool)
```

2. **Redis Pipeline (if needed)**
```python
# Already optimized with Lua scripts
# No additional pipelining needed
```

3. **Monitoring**
```python
# Log slow rate limit checks
import logging

logger = logging.getLogger(__name__)

if check_duration > 0.001:
    logger.warning(f"Slow rate limit check: {check_duration*1000:.2f}ms")
```

## Troubleshooting

### Redis Connection Issues

```python
# Add retry logic
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
async def connect_redis():
    return await redis.from_url("redis://localhost:6379/0")
```

### High Latency

```bash
# Check Redis latency
redis-cli --latency

# Check Redis performance
redis-cli --stat

# Monitor slow log
redis-cli slowlog get 10
```

### Rate Limit Not Working

1. Check if rate limiting is enabled:
```bash
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/data -v
# Should see X-RateLimit-* headers
```

2. Check Redis connection:
```bash
redis-cli ping
# Should return PONG
```

3. Check logs:
```bash
tail -f logs/app.log | grep rate_limit
```

## Next Steps

- Read [RATE_LIMITING.md](./RATE_LIMITING.md) for detailed documentation
- Configure alerts for rate limit abuse
- Set up Grafana dashboards for monitoring
- Implement custom rate limits for your use case

## Support

For issues or questions:
- Documentation: https://docs.alkhorayef-esp.com/rate-limiting
- GitHub Issues: https://github.com/alkhorayef/esp-platform/issues
