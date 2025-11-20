# Alkhorayef ESP IoT Platform - Quick Start Guide

## Prerequisites

- **Python 3.11+** installed
- **PostgreSQL 14+** with TimescaleDB extension
- **Redis 7+** for caching
- **Docker & Docker Compose** (optional, for containerized deployment)
- **Git** for version control

## 5-Minute Setup

### 1. Clone and Setup

```bash
# Clone repository
git clone <repository-url>
cd insa-iot-platform

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Generate secure secrets
python3 << EOF
import secrets
print(f"\n# Add these to your .env file:")
print(f"JWT_SECRET_KEY={secrets.token_urlsafe(32)}")
print(f"POSTGRES_PASSWORD={secrets.token_urlsafe(24)}")
print(f"REDIS_PASSWORD={secrets.token_urlsafe(24)}")
EOF

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.
```

**Minimum required changes in `.env`:**
```bash
# Replace these values
POSTGRES_PASSWORD=<generated-password>
REDIS_PASSWORD=<generated-password>
JWT_SECRET_KEY=<generated-secret>

# Update if not using localhost
POSTGRES_HOST=localhost
REDIS_HOST=localhost
```

### 3. Setup Database

```bash
# Option A: Local PostgreSQL
createdb esp_telemetry
psql esp_telemetry -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"

# Option B: Docker PostgreSQL
docker run -d \
  --name esp-postgres \
  -e POSTGRES_DB=esp_telemetry \
  -e POSTGRES_USER=alkhorayef \
  -e POSTGRES_PASSWORD=your-password \
  -p 5432:5432 \
  timescale/timescaledb:latest-pg14
```

### 4. Setup Redis

```bash
# Option A: Local Redis with password
redis-server --requirepass your-redis-password

# Option B: Docker Redis
docker run -d \
  --name esp-redis \
  -p 6379:6379 \
  redis:7-alpine \
  redis-server --requirepass your-redis-password
```

### 5. Run Application

```bash
# Development mode (with auto-reload)
make run-dev

# OR manually:
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# Production mode (with Gunicorn)
make run-prod
```

### 6. Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-11-20T12:00:00Z"
}

# API documentation (if enabled)
open http://localhost:8000/docs
```

## Docker Deployment (Recommended for Production)

### Quick Start with Docker Compose

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your values

# 2. Start all services
docker-compose up -d

# 3. Check status
docker-compose ps

# 4. View logs
docker-compose logs -f api

# 5. Access application
open http://localhost:8000
```

### Build and Run Manually

```bash
# Build image
docker build -t alkhorayef-esp:1.0.0 .

# Run container
docker run -d \
  --name alkhorayef-esp \
  --env-file .env \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/ml-models:/app/ml-models \
  alkhorayef-esp:1.0.0

# Check logs
docker logs -f alkhorayef-esp

# Health check
docker exec alkhorayef-esp curl -f http://localhost:8000/health
```

## Development Workflow

### Using Makefile Commands

```bash
# Setup development environment
make dev

# Format code
make format

# Run linters
make lint

# Run tests
make test

# Run with coverage
make test-cov

# View all available commands
make help
```

### Manual Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Format code
black . --line-length 100
isort . --profile black

# Lint code
flake8 .
mypy .

# Run tests
pytest -v

# Run with coverage
pytest --cov=. --cov-report=html
```

## Testing the Platform

### 1. Ingest Sample Telemetry

```bash
curl -X POST http://localhost:8000/telemetry/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "well_id": "WELL-001",
    "flow_rate": 850.5,
    "pip": 1250.0,
    "motor_current": 45.2,
    "motor_temp": 85.5,
    "vibration": 0.15,
    "vsd_frequency": 60.0,
    "flow_variance": 2.5,
    "torque": 75.0,
    "gor": 120.5
  }'
```

### 2. Run Diagnostic

```bash
curl -X POST http://localhost:8000/api/v1/diagnostics/decision_tree \
  -H "Content-Type: application/json" \
  -d @test_diagnostic.json
```

### 3. Natural Language Query

```bash
curl -X POST http://localhost:8000/api/v1/diagnostics/nlp_query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Why is pump performance degrading?",
    "well_id": "WELL-001",
    "include_history": true
  }'
```

### 4. WebSocket Real-time Data

```javascript
// JavaScript example
const ws = new WebSocket('ws://localhost:8000/ws/telemetry/WELL-001');

ws.onmessage = (event) => {
  const telemetry = JSON.parse(event.data);
  console.log('Real-time telemetry:', telemetry);
};
```

## Configuration Validation

### Check Configuration

```bash
# Validate environment variables are loaded
python3 << EOF
from dotenv import load_dotenv
import os

load_dotenv()

required_vars = [
    'POSTGRES_HOST',
    'POSTGRES_PASSWORD',
    'REDIS_URL',
    'JWT_SECRET_KEY',
]

missing = [var for var in required_vars if not os.getenv(var)]

if missing:
    print(f"❌ Missing variables: {', '.join(missing)}")
    exit(1)
else:
    print("✅ All required variables present")
EOF
```

### Test Database Connection

```bash
python3 << EOF
import asyncpg
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_db():
    try:
        conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
        version = await conn.fetchval('SELECT version()')
        print(f"✅ Database connected: {version}")
        await conn.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

asyncio.run(test_db())
EOF
```

### Test Redis Connection

```bash
python3 << EOF
import redis
import os
from dotenv import load_dotenv

load_dotenv()

try:
    r = redis.from_url(os.getenv('REDIS_URL'))
    r.ping()
    print("✅ Redis connected")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
EOF
```

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000
# or
netstat -tuln | grep 8000

# Kill process
kill -9 <PID>
```

#### Permission Denied (Docker)

```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or run with sudo
sudo docker-compose up
```

#### Database Connection Refused

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql

# Check if listening on correct port
sudo netstat -tuln | grep 5432
```

#### Redis Connection Refused

```bash
# Check if Redis is running
sudo systemctl status redis

# Start Redis
sudo systemctl start redis

# Test connection
redis-cli -a your-password ping
```

## Next Steps

1. **Configure Production Settings**: Review [CONFIGURATION.md](CONFIGURATION.md)
2. **Setup Monitoring**: Configure Grafana dashboards
3. **Enable Backups**: Setup automated backups (see `.env.example`)
4. **Security Hardening**: Rotate secrets, enable SSL/TLS
5. **Scale Application**: Adjust worker counts and connection pools

## Getting Help

- **Documentation**: See `/docs` directory
- **API Documentation**: http://localhost:8000/docs (when running)
- **Health Endpoint**: http://localhost:8000/health
- **Metrics**: http://localhost:8000/metrics

## Production Checklist

Before deploying to production:

- [ ] All secrets generated and stored securely
- [ ] `DEBUG_MODE=false` in production `.env`
- [ ] CORS origins restricted (no wildcards)
- [ ] SSL/TLS certificates configured
- [ ] Database backups automated
- [ ] Monitoring and alerting configured
- [ ] Resource limits set (CPU, memory)
- [ ] Log rotation configured
- [ ] Data retention policies implemented
- [ ] Security scan completed (`make security-scan`)

---

**Quick Commands Reference:**

```bash
# Development
make dev          # Setup dev environment
make run-dev      # Run with auto-reload
make test         # Run tests
make format       # Format code

# Production
make docker-build # Build Docker image
make deploy       # Deploy to production

# Utilities
make health-check # Check app health
make logs         # View logs
make clean        # Clean generated files
make help         # Show all commands
```
