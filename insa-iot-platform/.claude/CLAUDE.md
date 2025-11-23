# InSa IoT Platform - Claude Code Instructions

## 🏗️ Platform Overview

This is the **InSa Industrial IoT Platform** - a comprehensive IIoT solution with three client-specific versions:

### Available Platform Versions

1. **Main InSa IoT Platform** (`remotes/insa-iot/main`)
   - Core industrial IoT platform
   - Multi-protocol support (MQTT, Modbus, CoAP, AMQP)
   - AI-powered security & compliance
   - Enterprise authentication (SSO/SAML, MFA)
   - Production deployment with PostgreSQL, K8s, Helm

2. **Vidrio Andino Edition** (`remotes/insa-iot/client/vidrio-andino`)
   - Glass manufacturing/enterprise customization
   - Predictive maintenance dashboards
   - Industry-specific templates

3. **Alkhorayef Edition** (`remotes/insa-iot/client/alkhorayef`) **← CURRENT**
   - Oil & Gas ESP pump diagnostics
   - Hybrid RAG system for diagnostics
   - Decision tree diagnostic engine
   - ML-based failure predictions

## 🚀 Current Deployment (Alkhorayef)

### Running Services
- **TimescaleDB (PostgreSQL)**: Port 5440 (container: alkhorayef-timescaledb)
- **Redis**: Port 6389 (container: alkhorayef-redis)
- **RabbitMQ**: Ports 5672, 15672 (container: alkhorayef-rabbitmq)
- **API Service**: Port 8100 → 8000 (container: alkhorayef-api)
- **ML Service**: Port 8101 → 8001 (container: alkhorayef-ml)
- **Grafana**: Port 3000 (container: alkhorayef-grafana)

### Architecture
```
Docker Compose Stack:
├── alkhorayef-timescaledb (PostgreSQL + TimescaleDB)
├── alkhorayef-redis (Caching + Pub/Sub)
├── alkhorayef-rabbitmq (Message Queue)
├── alkhorayef-api (FastAPI REST API)
├── alkhorayef-ml (ML Service)
├── alkhorayef-grafana (Dashboards)
├── alkhorayef-nginx (Reverse Proxy)
└── alkhorayef-tailscale (Secure Access)
```

### Key Files
- `app.py` - Main FastAPI application
- `run_alkhorayef_rag_system.py` - Diagnostic decision tree engine
- `ml_service.py` - Machine learning predictions
- `esp_telemetry_simulator.py` - ESP data simulator
- `docker-compose.yml` - Full stack deployment
- `requirements.txt` - Python dependencies

## 📊 Data Management

### IMPORTANT: Data Retention Policy

**Azure Backup System:**
- Stores only the **last 30 days** of IoT telemetry data
- Used for quick access and recent data analysis
- Optimized for performance and cost

**Full Backup System:**
- Contains **ALL historical IoT data** (complete history)
- Primary source of truth for long-term analytics
- Required for compliance and historical analysis
- Never delete without full backup verification

### Database Tables
- `esp_telemetry` - Real-time ESP pump telemetry
- `diagnostic_results` - AI diagnostic history
- Data retention: 30 days in Azure, full history in backup

## 🔧 Development Workflow

### Starting the Platform
```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d timescaledb redis api

# View logs
docker logs alkhorayef-api -f
```

### Testing the API
```bash
# Health check (from inside container)
docker exec alkhorayef-api curl -s http://localhost:8000/health

# Ingest telemetry
docker exec -i alkhorayef-api curl -s -X POST http://localhost:8000/telemetry/ingest \
  -H "Content-Type: application/json" -d @test_telemetry.json

# Run diagnostics
docker exec -i alkhorayef-api curl -s -X POST http://localhost:8000/api/v1/diagnostics/decision_tree \
  -H "Content-Type: application/json" -d @test_diagnostic.json
```

### Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (core only, torch has compatibility issues with Python 3.12)
pip install fastapi uvicorn asyncpg redis psycopg2-binary sqlalchemy pydantic python-dotenv
```

## 🔐 Environment Variables

### Database
- `DATABASE_URL`: `postgresql://alkhorayef:AlkhorayefESP2025!@timescaledb:5432/esp_telemetry`
- `DB_PASSWORD`: `AlkhorayefESP2025!`

### Redis
- `REDIS_URL`: `redis://:RedisAlkhorayef2025!@redis:6379`
- `REDIS_PASSWORD`: `RedisAlkhorayef2025!`

### RabbitMQ
- `RABBITMQ_URL`: `amqp://alkhorayef:RabbitAlkhorayef2025!@rabbitmq:5672`
- `RABBITMQ_PASSWORD`: `RabbitAlkhorayef2025!`

### Grafana
- `GRAFANA_PASSWORD`: `GrafanaAlkhorayef2025!`

### API Configuration
- `API_PORT`: `8000`
- `ML_SERVICE_PORT`: `8001`

## 🎯 API Endpoints

### Health & Metrics
- `GET /` - Serve platform HTML dashboard
- `GET /health` - Health check (Redis + PostgreSQL)
- `GET /metrics` - System metrics (wells, readings, diagnostics)

### Telemetry
- `POST /telemetry/ingest` - Ingest ESP telemetry data
- `GET /api/v1/wells/{well_id}/telemetry?hours=24` - Get telemetry history
- `WebSocket /ws/telemetry/{well_id}` - Real-time telemetry stream

### Diagnostics
- `POST /api/v1/diagnostics/decision_tree` - Run diagnostic decision tree
- `POST /api/v1/diagnostics/nlp_query` - Natural language query
- `GET /api/v1/wells/{well_id}/diagnostics` - Get diagnostic history

## 🤖 AI/ML Features

### Decision Tree Diagnostics
- Free Gas Lock detection
- Underpumping conditions
- Sand/Solids production
- Hydraulic wear
- VSD/Electrical issues
- Poor installation/selection

### Machine Learning Predictions
- Failure probability (24h forecast)
- Mean Time Between Failures (MTBF)
- Anomaly detection

### Knowledge Graph Integration
- Historical case matching
- Solution recommendations
- Pattern recognition

## 🐛 Known Issues

### Network Connectivity
- Host to container networking may have issues
- **Solution**: Execute API tests from inside containers using `docker exec`
- Port mappings work but direct host connection hangs

### Python Dependencies
- `torch==2.1.1` incompatible with Python 3.12
- **Solution**: Use Docker containers with compatible Python version
- Core dependencies work fine in venv without ML packages

### Database SQL Bug
- Telemetry history endpoint has SQL syntax error (interval parameter)
- **Status**: Known issue, diagnostic history works correctly

## 🔄 Switching Between Platforms

### To Main InSa IoT
```bash
git checkout -b main-iot remotes/insa-iot/main
docker-compose down
# Update docker-compose.yml for main platform
docker-compose up -d
```

### To Vidrio Andino
```bash
git checkout -b vidrio-andino remotes/insa-iot/client/vidrio-andino
docker-compose down
# Update configuration for Vidrio Andino
docker-compose up -d
```

### To Alkhorayef (Current)
```bash
git checkout -b alkhorayef remotes/insa-iot/client/alkhorayef
docker-compose down
docker-compose up -d
```

## 📝 Development Guidelines

### Code Style
- Follow FastAPI best practices
- Use type hints for all functions
- Document all API endpoints with docstrings
- Use Pydantic models for request/response validation

### Testing
- Test all endpoints from inside Docker containers
- Verify database connections before deploying
- Check Redis pub/sub functionality
- Validate ML predictions against known cases

### Deployment
- Always use Docker Compose for production
- Never expose credentials in code
- Use environment variables for all secrets
- Monitor container health checks

## 🔍 Debugging

### Check Container Status
```bash
docker ps --filter "name=alkhorayef"
docker logs alkhorayef-api --tail 50
```

### Database Queries
```bash
docker exec alkhorayef-timescaledb psql -U alkhorayef -d esp_telemetry -c "SELECT COUNT(*) FROM esp_telemetry;"
```

### Redis Check
```bash
docker exec alkhorayef-redis redis-cli -a RedisAlkhorayef2025! PING
```

## 📚 Documentation

- `README.md` - Project overview and setup
- `ARCHITECTURE_PLAN.md` - System architecture
- `PLATFORM_STRUCTURE.md` - Directory structure
- `PRODUCTION_SOLUTION.md` - Production deployment guide
- `CONTRIBUTING.md` - Contribution guidelines

## 🎓 Learning Resources

### ESP Pump Diagnostics
- Decision tree methodology
- Telemetry parameter interpretation
- Common failure modes
- Preventive maintenance strategies

### Oil & Gas Operations
- ESP system components
- Production optimization
- Well monitoring best practices
- Predictive maintenance ROI

---

**Last Updated**: 2025-11-20
**Platform Version**: Alkhorayef Edition
**Status**: ✅ Fully Operational
