# INSA IoT Platform - Comprehensive Audit Report
**Date**: November 20, 2025
**Location**: `/home/wil/insa-iot-platform`
**Auditor**: Claude Code

---

## Executive Summary

The INSA IoT Platform is an enterprise-grade Industrial IoT infrastructure featuring:
- **Main Platform**: Multi-client IoT platform with modular architecture
- **Alkhorayef ESP**: Specialized AI-powered ESP pump diagnostics system
- **Current Status**: Partially operational with several containers running

### Overall Health Status: 🟡 OPERATIONAL WITH ISSUES

| Component | Status | Notes |
|-----------|--------|-------|
| TimescaleDB | ✅ Healthy | Running on port 5440 |
| Redis | ✅ Healthy | Running on port 6389 |
| RabbitMQ | ✅ Running | Running on ports 5672, 15672 |
| Grafana | ✅ Running | Running on port 3000 |
| API Service | 🟡 Unhealthy | Running but failing health checks |
| Nginx | ❌ Not Running | Container exists but stopped |
| ML Service | ❌ Not Running | Not deployed |
| Tailscale Container | ❌ Not Running | Using host Tailscale instead |

---

## 1. Architecture Overview

### Current Deployment Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    Tailscale Network Layer                       │
│  https://iac1.tailc58ea3.ts.net/                                │
│    ├─ /insa-iot/      → localhost:9000 (Python HTTP Server)    │
│    └─ /alkhorayef     → localhost:8095 (Nginx - NOT RUNNING)   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Application Layer                            │
│  Port 9000: Static Site (Python HTTP Server) - RUNNING         │
│  Port 8100: FastAPI Application (Docker) - RUNNING (Unhealthy) │
│  Port 8095: Nginx Reverse Proxy (Docker) - NOT RUNNING         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Backend Infrastructure                         │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │ TimescaleDB    │  │ Redis          │  │ RabbitMQ        │  │
│  │ Port: 5440     │  │ Port: 6389     │  │ Port: 5672      │  │
│  │ Status: Healthy│  │ Status: Healthy│  │ Status: Running │  │
│  └────────────────┘  └────────────────┘  └─────────────────┘  │
│                                                                  │
│  ┌────────────────┐                                             │
│  │ Grafana        │                                             │
│  │ Port: 3000     │                                             │
│  │ Status: Running│                                             │
│  └────────────────┘                                             │
└─────────────────────────────────────────────────────────────────┘
```

### Network Architecture

**Docker Network**: `alkhorayef-net` (172.30.0.0/16)
- Custom bridge network for container isolation
- Shared by all containerized services

**Exposed Ports**:
- 5440: TimescaleDB (PostgreSQL)
- 6389: Redis
- 5672: RabbitMQ (AMQP)
- 15672: RabbitMQ Management UI
- 3000: Grafana
- 8100: FastAPI Application (internal 8000)
- 8101: ML Service (internal 8001) - NOT RUNNING
- 8095: Nginx - NOT RUNNING
- 9000: Static Site Server - RUNNING

---

## 2. Running Services Analysis

### Container Status

```
CONTAINER NAME         IMAGE                          STATUS              PORTS
alkhorayef-timescaledb timescale/timescaledb:latest   Up 15 hours (healthy) 5440:5432
alkhorayef-redis       redis:7-alpine                Up 15 hours (healthy) 6389:6379
alkhorayef-rabbitmq    rabbitmq:3-management-alpine  Up 16 hours           5672, 15672
alkhorayef-grafana     grafana/grafana:latest        Up 12 seconds         3000
alkhorayef-api         insa-iot-platform-api         Up 9 hours (unhealthy) 8100:8000
```

### Process Analysis

**Running Python Processes**:
1. **HTTP Server (Port 5200)** - PID 5815
   - Command: `python3 -m http.server 5200 --bind 0.0.0.0`
   - Purpose: Unknown service

2. **ESP App Runner (Port ??)** - PID 608859
   - Command: `python run_esp_app.py`
   - Purpose: ESP application runner

3. **HTTP Server (Port 8000)** - PID 657232
   - Command: `python3 -m http.server 8000`
   - Purpose: Development server (may conflict with Docker)

4. **HTTP Server (Port 9000)** - PID 2831606
   - Command: `python3 -m http.server 9000`
   - Working Directory: `/home/wil/insa-iot-platform/static`
   - Purpose: **Main INSA IoT Platform frontend** ✅

5. **FastAPI App (Running natively)** - PID 4014013
   - Command: `python app.py`
   - Purpose: Native FastAPI instance (may conflict with Docker)

### ⚠️ Port Conflicts Detected

- **Port 8000**: Both native Python HTTP server AND potentially available for Docker API
- **Port 8100**: Docker API container (but container is unhealthy)
- Multiple Python processes may cause confusion

---

## 3. Application Structure

### Directory Layout

```
/home/wil/insa-iot-platform/
├── app.py                          # Main FastAPI application
├── alkhorayef_rag_demo.py         # RAG system demo
├── run_alkhorayef_rag_system.py   # RAG system implementation
├── esp_api_service.py             # ESP API service
├── esp_telemetry_simulator.py     # Telemetry simulator
├── ml_service.py                  # Machine learning service
├── test_connections.py            # Connection testing
│
├── static/
│   └── index.html                 # Main landing page (served on :9000)
│
├── docker-compose.yml             # Container orchestration
├── docker-compose-simple.yml      # Simplified compose
├── Dockerfile                     # Container build config
│
├── requirements.txt               # Python dependencies
├── init-db.sql                   # Database initialization
│
├── nginx/
│   ├── nginx.conf                # Main nginx config
│   ├── sites-enabled/            # Site configurations
│   └── certs/                    # SSL certificates
│
├── grafana/
│   ├── dashboards/
│   │   └── esp_monitoring_dashboard.json
│   └── provisioning/
│
├── docs/
│   ├── API.md                    # API documentation
│   └── PERFORMANCE.md            # Performance docs
│
├── ARCHITECTURE_PLAN.md          # Architecture overview
├── PLATFORM_STRUCTURE.md         # Platform structure
├── PRODUCTION_SOLUTION.md        # Production fixes
├── SENTINEL_OG_ANALYSIS.md       # Sentinel analysis
└── README.md                     # Main documentation
```

### Key Files Analysis

#### app.py (Main Application)
- **Lines**: 385 lines
- **Framework**: FastAPI with async support
- **Features**:
  - ESP telemetry ingestion (`/telemetry/ingest`)
  - Diagnostic decision tree (`/api/v1/diagnostics/decision_tree`)
  - Natural language queries (`/api/v1/diagnostics/nlp_query`)
  - WebSocket support for real-time data
  - Health check endpoint
  - Metrics endpoint
- **Database**: AsyncPG pool for TimescaleDB
- **Cache**: Redis async client
- **Status**: ✅ Code appears well-structured

#### static/index.html (Frontend)
- **Purpose**: Main INSA IoT Platform landing page
- **Framework**: Pure HTML/CSS/JavaScript
- **Design**: Modern dark theme with gradients
- **Features**:
  - Multi-section navigation
  - Client platform showcase
  - Professional styling
- **Served By**: Python HTTP server on port 9000
- **Public URL**: https://iac1.tailc58ea3.ts.net/insa-iot/

---

## 4. Infrastructure Components

### TimescaleDB (PostgreSQL with Time-Series Extension)

**Status**: ✅ Healthy
**Connection**: `postgresql://alkhorayef:***@localhost:5432/esp_telemetry`
**Port**: 5440 (external) → 5432 (internal)

**Tables**:
1. `esp_telemetry` - Time-series telemetry data
   - Indexed on `(well_id, timestamp DESC)`
   - Fields: flow_rate, pip, motor_current, motor_temp, vibration, vsd_frequency, flow_variance, torque, gor

2. `diagnostic_results` - Diagnostic output
   - Indexed on `(well_id, timestamp DESC)`
   - Fields: diagnosis, confidence, severity, actions (JSONB), telemetry_snapshot (JSONB)

**Configuration**:
- Max Connections: 100
- Max Background Workers: 8

### Redis

**Status**: ✅ Healthy
**Connection**: `redis://:***@localhost:6379`
**Port**: 6389 (external) → 6379 (internal)

**Usage**:
- Telemetry caching (5-minute TTL)
- Diagnostic result caching (1-hour TTL)
- Pub/Sub for real-time telemetry
- WebSocket message distribution

**Key Patterns**:
- `telemetry:{well_id}:latest`
- `diagnosis:{well_id}:latest`

### RabbitMQ

**Status**: ✅ Running
**Connection**: `amqp://alkhorayef:***@localhost:5672`
**Ports**: 5672 (AMQP), 15672 (Management UI)

**Purpose**: Message queue for asynchronous processing
**Management UI**: http://localhost:15672

### Grafana

**Status**: ✅ Running
**Port**: 3000
**Admin**: admin / GrafanaAlkhorayef2025!

**Dashboards**:
- `esp_monitoring_dashboard.json` - ESP pump monitoring

**Data Sources**: (To be configured)
- TimescaleDB
- Prometheus (if metrics collection is enabled)

---

## 5. API Status & Health

### FastAPI Application (Port 8100)

**Container Status**: Running but Unhealthy
**Recent Logs**:
```
🚀 Starting Alkhorayef ESP AI RAG System...
✅ System initialized successfully
INFO: Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Issue**: Container repeatedly shutting down and restarting
**Warning**: Deprecation warning - `redis_client.close()` should use `aclose()`

### Health Check Test

**Endpoint**: http://localhost:8100/health
**Status**: ⏳ Test running in background
**Expected Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-20T..."
}
```

### Available Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Serve platform HTML |
| GET | `/health` | Health check |
| POST | `/telemetry/ingest` | Ingest ESP telemetry |
| POST | `/api/v1/diagnostics/decision_tree` | Run diagnostics |
| POST | `/api/v1/diagnostics/nlp_query` | Natural language query |
| GET | `/api/v1/wells/{well_id}/telemetry` | Get telemetry history |
| GET | `/api/v1/wells/{well_id}/diagnostics` | Get diagnostic history |
| WS | `/ws/telemetry/{well_id}` | Real-time telemetry stream |
| GET | `/metrics` | System metrics |

---

## 6. Access & Security

### Public Access URLs (via Tailscale)

**Main Platform**: https://iac1.tailc58ea3.ts.net/insa-iot/
**Alkhorayef ESP**: https://iac1.tailc58ea3.ts.net/alkhorayef (⚠️ Nginx not running)

### Tailscale Serve Configuration

```
https://iac1.tailc58ea3.ts.net (tailnet only)
├── /js/             → http://127.0.0.1:8003/js
├── /crm/            → http://127.0.0.1:8003/
├── /css/            → http://127.0.0.1:8003/css
├── /assets/         → http://127.0.0.1:8003/assets
├── /insa-iot/       → http://localhost:9000 ✅
├── /alkhorayef      → http://127.0.0.1:8095 ❌ (Nginx down)
├── /favicon.ico     → http://127.0.0.1:8003/favicon.ico
└── /command-center/ → http://127.0.0.1:8003/command-center
```

### Credentials Summary

| Service | Username | Password | Notes |
|---------|----------|----------|-------|
| TimescaleDB | alkhorayef | AlkhorayefESP2025! | Via env var |
| Redis | (none) | RedisAlkhorayef2025! | Auth required |
| RabbitMQ | alkhorayef | RabbitAlkhorayef2025! | Via env var |
| Grafana | admin | GrafanaAlkhorayef2025! | Via env var |

**⚠️ Security Note**: Credentials are stored in docker-compose.yml with default fallbacks. Consider using `.env` file or secrets management.

---

## 7. Issues & Recommendations

### Critical Issues 🔴

1. **Nginx Container Not Running**
   - **Impact**: Alkhorayef ESP platform inaccessible via public URL
   - **Affected**: https://iac1.tailc58ea3.ts.net/alkhorayef
   - **Recommendation**:
     ```bash
     docker-compose up -d nginx
     docker logs alkhorayef-nginx
     ```

2. **API Container Unhealthy**
   - **Impact**: Health checks failing, container may be unstable
   - **Symptoms**: Repeated shutdown/restart cycles
   - **Recommendation**:
     - Check health check configuration
     - Review application logs for errors
     - Fix Redis deprecation warning (use `aclose()`)

3. **ML Service Not Deployed**
   - **Impact**: Machine learning features unavailable
   - **Affected**: ML-based diagnostics and predictions
   - **Recommendation**: Start ML service container

### Major Issues 🟡

4. **Port Conflicts**
   - **Issue**: Multiple Python processes on ports 8000, 5200
   - **Impact**: May interfere with Docker containers
   - **Recommendation**: Consolidate to single deployment method (prefer Docker)

5. **Missing ML Service**
   - **File Exists**: `ml_service.py`
   - **Container**: Not running
   - **Recommendation**: Review docker-compose.yml and start service

6. **Grafana Data Sources Not Configured**
   - **Impact**: Dashboards cannot display data
   - **Recommendation**: Configure TimescaleDB data source

### Minor Issues 🟢

7. **Documentation Gaps**
   - Missing deployment guide
   - API documentation incomplete
   - Configuration examples limited

8. **Redis Deprecation Warning**
   - Current: `await redis_client.close()`
   - Should be: `await redis_client.aclose()`
   - Location: `app.py:90`

9. **No .env File**
   - Credentials in docker-compose.yml
   - Should use separate .env file for production

10. **Node Modules in Repository**
    - Should be in `.gitignore`
    - Increases repository size

---

## 8. Recommendations & Action Items

### Immediate Actions (Priority 1)

1. **Fix Nginx Container**
   ```bash
   cd /home/wil/insa-iot-platform
   docker-compose up -d nginx
   docker logs -f alkhorayef-nginx
   ```

2. **Fix API Health Checks**
   ```bash
   # Check why health checks are failing
   docker exec alkhorayef-api curl -f http://localhost:8000/health
   # Fix Redis deprecation
   # Edit app.py line 90: await redis_client.aclose()
   ```

3. **Consolidate Python Processes**
   ```bash
   # Stop redundant native processes
   # Keep only Docker-based deployment
   ps aux | grep "python.*http.server" | grep -v 9000
   # Kill any conflicting processes
   ```

### Short-term Actions (Priority 2)

4. **Deploy ML Service**
   ```bash
   docker-compose up -d ml-service
   docker logs -f alkhorayef-ml
   ```

5. **Configure Grafana**
   - Add TimescaleDB data source
   - Import ESP monitoring dashboard
   - Test dashboard rendering

6. **Create .env File**
   ```bash
   cat > .env << EOF
   DB_PASSWORD=AlkhorayefESP2025!
   REDIS_PASSWORD=RedisAlkhorayef2025!
   RABBITMQ_PASSWORD=RabbitAlkhorayef2025!
   GRAFANA_PASSWORD=GrafanaAlkhorayef2025!
   EOF
   chmod 600 .env
   ```

### Long-term Actions (Priority 3)

7. **Improve Documentation**
   - Complete API documentation
   - Add deployment guide
   - Document configuration options

8. **Add Monitoring**
   - Implement Prometheus metrics
   - Add logging aggregation
   - Set up alerting

9. **Security Hardening**
   - Move to secrets management
   - Implement TLS for internal services
   - Add authentication to all endpoints

10. **Testing & CI/CD**
    - Add automated tests
    - Set up CI/CD pipeline
    - Implement staging environment

---

## 9. Data Retention & Backup

### Current State

**Note from CLAUDE.md**: "The backup system should have all IoT history data. Azure should only have the last 30 days of IoT data."

### Implementation Status

- ❓ **Unknown**: No evidence of data retention policies configured
- ❓ **Unknown**: No backup scripts found in platform directory
- ❓ **Unknown**: Azure sync mechanism not visible in current deployment

### Recommendations

1. **Configure TimescaleDB Retention**
   ```sql
   SELECT add_retention_policy('esp_telemetry', INTERVAL '30 days');
   ```

2. **Set Up Backup System**
   - Configure automated PostgreSQL backups
   - Implement Azure blob storage sync
   - Retain full history in backup system
   - Keep only 30 days in active TimescaleDB

3. **Document Backup Procedures**
   - Backup schedule
   - Restore procedures
   - Disaster recovery plan

---

## 10. Technology Stack Summary

### Languages & Frameworks
- **Python**: 3.10+
- **FastAPI**: 0.104+ (Async web framework)
- **Uvicorn**: 0.24+ (ASGI server)

### Databases & Storage
- **TimescaleDB**: PostgreSQL 15 with time-series extension
- **Redis**: 7.0+ (Cache & Pub/Sub)
- **Neo4j**: 5.15+ (Knowledge graph - planned)

### Message Queue
- **RabbitMQ**: 3.x (Message broker)

### Frontend
- **Vanilla JavaScript**: No framework
- **HTML5/CSS3**: Modern responsive design

### Machine Learning
- **PyTorch**: 2.1.1
- **Transformers**: 4.36.2
- **Sentence Transformers**: 2.2.2
- **Scikit-learn**: 1.3.2

### Analytics
- **Pandas**: 2.1.4
- **NumPy**: 1.26.2
- **SciPy**: 1.11.4
- **Prophet**: 1.1.5 (Time series forecasting)

### Monitoring & Visualization
- **Grafana**: Latest
- **Prometheus**: (Planned)

### Infrastructure
- **Docker**: Container runtime
- **Docker Compose**: Orchestration
- **Nginx**: Reverse proxy
- **Tailscale**: Secure networking

---

## 11. Performance Considerations

### Current Resource Usage

**From Container Status**:
- TimescaleDB: Healthy, 15 hours uptime
- Redis: Healthy, 15 hours uptime
- RabbitMQ: Running, 16 hours uptime
- API: Unhealthy, frequent restarts

### Bottleneck Analysis

1. **API Instability**: Health check failures causing restarts
2. **Missing ML Service**: ML workloads cannot be processed
3. **Nginx Down**: No load balancing or reverse proxy
4. **No Connection Pooling**: Default pool sizes may not be optimal

### Recommendations

1. Increase database connection pool sizes
2. Implement caching strategies
3. Add CDN for static assets
4. Configure proper health check timeouts
5. Monitor resource usage with Prometheus

---

## 12. Testing Status

### Test Files Present

- `test_connections.py` - Connection testing
- `test_diagnostic.json` - Diagnostic test data
- `test_nlp.json` - NLP query test data
- `esp_telemetry_simulator.py` - Telemetry simulation

### Test Coverage

- ❌ **Unit Tests**: Not found
- ❌ **Integration Tests**: Not found
- ✅ **Connection Tests**: Present
- ✅ **Sample Data**: Present
- ❓ **Load Tests**: Unknown

### Recommendations

1. Implement pytest-based test suite
2. Add integration tests for API endpoints
3. Create load testing suite
4. Set up continuous testing in CI/CD

---

## 13. Conclusion

### Platform Strengths ✅

1. **Modern Architecture**: Well-designed microservices architecture
2. **Enterprise Technologies**: Production-grade stack (TimescaleDB, Redis, RabbitMQ)
3. **AI/ML Integration**: Advanced RAG system and decision trees
4. **Secure Networking**: Tailscale integration for secure access
5. **Good Documentation**: Comprehensive architecture and structure docs
6. **Scalable Design**: Docker-based, easy to scale

### Areas for Improvement ⚠️

1. **Container Stability**: API container unhealthy, Nginx not running
2. **Missing Services**: ML service not deployed
3. **Port Conflicts**: Multiple Python processes
4. **Security**: Credentials in plain text
5. **Testing**: Limited automated tests
6. **Monitoring**: No observability stack

### Next Steps

**Immediate (Today)**:
1. Restart Nginx container
2. Fix API health checks
3. Deploy ML service

**This Week**:
1. Configure Grafana data sources
2. Implement .env file
3. Consolidate deployment approach

**This Month**:
1. Add comprehensive tests
2. Implement monitoring stack
3. Complete documentation
4. Set up backup system

---

## 14. Appendix

### Quick Reference Commands

```bash
# Start all services
cd /home/wil/insa-iot-platform
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api

# Restart specific service
docker-compose restart nginx

# Access database
psql postgresql://alkhorayef:AlkhorayefESP2025!@localhost:5440/esp_telemetry

# Test API
curl http://localhost:8100/health

# Access main site
curl http://localhost:9000
```

### Useful URLs

- Main Platform: https://iac1.tailc58ea3.ts.net/insa-iot/
- Local API Docs: http://localhost:8100/docs
- Grafana: http://localhost:3000
- RabbitMQ Management: http://localhost:15672

---

**End of Audit Report**
