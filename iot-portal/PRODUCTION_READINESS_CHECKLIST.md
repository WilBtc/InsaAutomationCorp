# Production Readiness Checklist - IoT Portal
**Created**: October 29, 2025
**Target**: 2-4 weeks to production-ready
**Status**: 🔴 NOT PRODUCTION READY (Critical fixes needed)

---

## 🎯 GOAL: Transform from "Development Complete" to "Production Ready"

**Current State**: Good MVP with core features working
**Target State**: Customer-ready platform with proven stability

---

## 🔴 CRITICAL PRIORITY (Must Complete - Week 1)

### 1. Security Fix: Migrate Password Hashing ⚠️ CRITICAL
**Current**: SHA256 without salt (MAJOR SECURITY VULNERABILITY)
**Target**: bcrypt with proper salt rounds

**Tasks**:
- [ ] Install bcrypt: `pip install bcrypt`
- [ ] Update `app_advanced.py` authentication functions
- [ ] Replace `hashlib.sha256()` with `bcrypt.hashpw()`
- [ ] Set salt rounds to 12 (industry standard)
- [ ] Rehash existing passwords in database
- [ ] Test login flow with bcrypt
- [ ] Update password reset flow

**Acceptance Criteria**:
- ✅ No SHA256 password hashing in codebase
- ✅ All user passwords use bcrypt with 12 rounds
- ✅ Login/registration working with bcrypt
- ✅ Password verification working correctly

**Effort**: 2-3 hours
**Risk**: HIGH if not fixed (credential theft possible)
**Owner**: Wil Aroca

---

### 2. Multi-Tenancy Bug Fixes
**Current**: 4/10 endpoints working, 500 errors on core endpoints
**Target**: 10/10 endpoints functional with proper isolation

**Tasks**:
- [ ] Debug `/api/v1/tenants` 500 error (list tenants)
- [ ] Add error logging to all tenant endpoints
- [ ] Fix JWT claims extraction in tenant context
- [ ] Verify database connection in endpoint context
- [ ] Test tenant creation endpoint
- [ ] Test user invitation workflow
- [ ] Test quota enforcement
- [ ] Verify tenant data isolation (no cross-tenant leaks)
- [ ] Load test with 10 tenants, 50 devices each

**Acceptance Criteria**:
- ✅ All 10 tenant endpoints return 200 OK (no 500 errors)
- ✅ Tenant data isolation verified (SQL audit)
- ✅ Quota enforcement working (devices, users, rules)
- ✅ Integration tests pass (tenant CRUD + isolation)

**Effort**: 6-8 hours
**Risk**: MEDIUM (feature incomplete, SaaS model blocked)
**Owner**: Wil Aroca

---

## 🟡 HIGH PRIORITY (Week 1-2)

### 3. Deploy Additional Protocols (CoAP, AMQP, OPC UA)
**Current**: Code exists but NOT deployed (0/3 protocols running)
**Target**: All 3 protocols deployed and tested

#### 3a. CoAP Server (RFC 7252)
**Tasks**:
- [ ] Install aiocoap: `pip install aiocoap`
- [ ] Start CoAP server on port 5683
- [ ] Test resource discovery: `coap-client -m get coap://localhost/.well-known/core`
- [ ] Test telemetry POST: Send JSON via coap-client
- [ ] Verify data in PostgreSQL telemetry table
- [ ] Document CoAP usage in README
- [ ] Add systemd service file for auto-start

**Acceptance Criteria**:
- ✅ CoAP server running on port 5683
- ✅ Resource discovery working
- ✅ Telemetry ingestion to database verified
- ✅ 10 test messages successfully processed

**Effort**: 3-4 hours
**Dependencies**: None

#### 3b. AMQP Consumer (RabbitMQ)
**Tasks**:
- [ ] Install pika: `pip install pika`
- [ ] Setup RabbitMQ: `docker run -d -p 5672:5672 -p 15672:15672 rabbitmq:3-management`
- [ ] Start AMQP consumer thread
- [ ] Create `iiot` exchange (topic, durable)
- [ ] Create `telemetry` queue (durable)
- [ ] Test message publishing via Python/RabbitMQ UI
- [ ] Verify data in PostgreSQL telemetry table
- [ ] Test consumer auto-reconnect on failure
- [ ] Document AMQP setup in README

**Acceptance Criteria**:
- ✅ RabbitMQ running and accessible
- ✅ AMQP consumer processing messages
- ✅ Telemetry stored in database correctly
- ✅ 100 test messages successfully processed
- ✅ Auto-reconnect tested (restart RabbitMQ)

**Effort**: 4-5 hours
**Dependencies**: Docker, RabbitMQ

#### 3c. OPC UA Server (IEC 62541)
**Tasks**:
- [ ] Install asyncua: `pip install asyncua`
- [ ] Start OPC UA server on port 4840
- [ ] Load devices from database into address space
- [ ] Setup auto-sync (telemetry from DB → OPC UA variables every 5s)
- [ ] Test with UA Expert client (browse, read, subscribe)
- [ ] Test SetStatus method call
- [ ] Verify database updates from method calls
- [ ] Document OPC UA setup in README

**Acceptance Criteria**:
- ✅ OPC UA server running on port 4840
- ✅ Device nodes browsable in UA Expert
- ✅ Telemetry variables updating (5s interval)
- ✅ Method calls working (SetStatus)
- ✅ Database updates verified

**Effort**: 4-5 hours
**Dependencies**: None (optional: UA Expert for testing)

**Total Protocol Deployment**: 11-14 hours

---

### 4. Production Infrastructure Setup
**Current**: Development setup (single process, no monitoring)
**Target**: Production-grade infrastructure

#### 4a. Production WSGI Server (Gunicorn)
**Tasks**:
- [ ] Install Gunicorn: `pip install gunicorn`
- [ ] Create Gunicorn config: `/etc/gunicorn/iiot-portal.conf`
- [ ] Configure 4 workers (2 × CPU cores)
- [ ] Set worker class: `gevent` (for WebSocket support)
- [ ] Configure timeout: 120s
- [ ] Create systemd service: `/etc/systemd/system/iiot-portal.service`
- [ ] Test startup: `systemctl start iiot-portal`
- [ ] Enable auto-start: `systemctl enable iiot-portal`
- [ ] Test graceful reload: `systemctl reload iiot-portal`

**Config Example**:
```python
# /etc/gunicorn/iiot-portal.conf
bind = "127.0.0.1:5002"
workers = 4
worker_class = "gevent"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
```

**Acceptance Criteria**:
- ✅ Gunicorn running with 4 workers
- ✅ WebSocket connections working (Socket.IO)
- ✅ Graceful restarts working (zero downtime)
- ✅ Auto-start on server reboot verified

**Effort**: 3-4 hours
**Risk**: MEDIUM (WebSocket compatibility with Gunicorn)

#### 4b. Nginx Reverse Proxy + SSL/TLS
**Tasks**:
- [ ] Install Nginx: `apt install nginx`
- [ ] Create Nginx config: `/etc/nginx/sites-available/iiot-portal`
- [ ] Configure reverse proxy to Gunicorn (127.0.0.1:5002)
- [ ] Setup WebSocket proxying (upgrade headers)
- [ ] Install Let's Encrypt: `apt install certbot python3-certbot-nginx`
- [ ] Obtain SSL certificate: `certbot --nginx -d yourdomain.com`
- [ ] Configure HTTP → HTTPS redirect
- [ ] Enable Nginx config: `ln -s /etc/nginx/sites-available/iiot-portal /etc/nginx/sites-enabled/`
- [ ] Test SSL: `nginx -t && systemctl reload nginx`
- [ ] Verify HTTPS in browser (no warnings)

**Nginx Config Example**:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io/ {
        proxy_pass http://127.0.0.1:5002/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Acceptance Criteria**:
- ✅ Nginx reverse proxy working
- ✅ HTTPS enabled with valid SSL certificate
- ✅ HTTP → HTTPS redirect working
- ✅ WebSocket connections working over WSS
- ✅ SSL Labs test: A or A+ rating

**Effort**: 2-3 hours
**Risk**: LOW

#### 4c. Monitoring (Prometheus + Grafana)
**Tasks**:
- [ ] Install Prometheus client: `pip install prometheus-client`
- [ ] Add metrics endpoint: `/metrics` in app_advanced.py
- [ ] Expose metrics: API requests, response time, errors, DB queries
- [ ] Install Prometheus: `apt install prometheus` or Docker
- [ ] Configure Prometheus scrape: `prometheus.yml`
- [ ] Add Prometheus as Grafana datasource
- [ ] Create monitoring dashboard (10 panels)
- [ ] Setup alerting rules (API errors, high latency, disk space)
- [ ] Test alert delivery (email/webhook)

**Key Metrics to Track**:
- HTTP request rate (requests/sec)
- HTTP response time (p50, p95, p99)
- HTTP error rate (4xx, 5xx)
- Database query time
- Redis hit rate
- Memory usage
- CPU usage
- Active WebSocket connections
- MQTT messages/sec

**Acceptance Criteria**:
- ✅ Prometheus scraping metrics from `/metrics`
- ✅ Grafana dashboard showing all key metrics
- ✅ Alerting rules configured and tested
- ✅ 24-hour monitoring without gaps

**Effort**: 4-5 hours
**Risk**: LOW

#### 4d. PostgreSQL Backups
**Tasks**:
- [ ] Create backup script: `/usr/local/bin/backup-iiot-db.sh`
- [ ] Configure pg_dump with compression
- [ ] Setup cron job: Daily 2 AM backups
- [ ] Configure backup retention: Keep 7 days
- [ ] Test backup restoration
- [ ] Store backups offsite (S3, rsync, or network share)
- [ ] Monitor backup success (alert on failure)
- [ ] Document restore procedure

**Backup Script**:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/postgresql"
DB_NAME="insa_iiot"

pg_dump -h localhost -U iiot_user $DB_NAME | gzip > $BACKUP_DIR/iiot_${DATE}.sql.gz

# Keep only last 7 days
find $BACKUP_DIR -name "iiot_*.sql.gz" -mtime +7 -delete
```

**Acceptance Criteria**:
- ✅ Daily backups running automatically
- ✅ Backup restoration tested successfully
- ✅ 7-day retention working
- ✅ Alert on backup failure configured

**Effort**: 2-3 hours
**Risk**: LOW

**Total Infrastructure Setup**: 11-15 hours

---

## 🟢 TESTING & VALIDATION (Week 2-3)

### 5. Load Testing
**Current**: Manual testing with single user
**Target**: Validated under production load

**Tasks**:
- [ ] Install load testing tool: `pip install locust`
- [ ] Create load test scenarios (5 scenarios)
- [ ] Test 1: 100 concurrent users, 1000 requests/min (API endpoints)
- [ ] Test 2: 50 WebSocket connections, 100 messages/sec
- [ ] Test 3: 1000 MQTT messages/sec (telemetry ingestion)
- [ ] Test 4: ML predictions: 500 predictions/min
- [ ] Test 5: Mixed workload (API + WebSocket + MQTT + ML)
- [ ] Monitor during tests: CPU, memory, DB connections, response times
- [ ] Identify bottlenecks (document findings)
- [ ] Tune performance (indexes, caching, connection pools)
- [ ] Repeat tests after tuning (verify improvements)

**Load Test Scenarios**:
```python
# locustfile.py
from locust import HttpUser, task, between

class IIoTPlatformUser(HttpUser):
    wait_time = between(1, 3)

    @task(10)
    def list_devices(self):
        self.client.get("/api/v1/devices", headers={"Authorization": f"Bearer {self.token}"})

    @task(5)
    def post_telemetry(self):
        self.client.post("/api/v1/telemetry", json={"device_id": "...", "data": {...}})

    @task(3)
    def ml_predict(self):
        self.client.post("/api/v1/ml/predict", json={"device_id": "...", "value": 25.0})
```

**Acceptance Criteria**:
- ✅ 100 concurrent users sustained for 10 minutes
- ✅ API response time <100ms (p95) under load
- ✅ Error rate <1% under load
- ✅ ML predictions <50ms (p95) under load
- ✅ Database connections <50 (no connection exhaustion)
- ✅ Memory usage <2GB under load
- ✅ Zero crashes during load tests

**Effort**: 8-10 hours
**Risk**: HIGH (may reveal critical performance issues)

---

### 6. Test Coverage Measurement
**Current**: 165 tests written, unknown code coverage
**Target**: >70% code coverage measured

**Tasks**:
- [ ] Install pytest-cov: `pip install pytest-cov`
- [ ] Run tests with coverage: `pytest --cov=. --cov-report=html tests/`
- [ ] Review coverage report: `open htmlcov/index.html`
- [ ] Identify uncovered critical paths
- [ ] Write tests for critical paths (<70% coverage)
- [ ] Prioritize security-critical code (authentication, authorization)
- [ ] Prioritize data-critical code (database writes, ML predictions)
- [ ] Re-run coverage: `pytest --cov=. --cov-report=html tests/`
- [ ] Document coverage in README

**Coverage Targets**:
- Critical modules: >90% (auth, RBAC, ML, tenancy)
- Core modules: >80% (API endpoints, rule engine, protocols)
- Utility modules: >60% (caching, logging, helpers)
- Overall: >70%

**Acceptance Criteria**:
- ✅ pytest-cov report generated successfully
- ✅ Overall code coverage >70%
- ✅ Critical modules >90% coverage
- ✅ No untested security-critical code

**Effort**: 6-8 hours
**Risk**: MEDIUM (may reveal low actual coverage)

---

### 7. Protocol Integration Tests
**Current**: Protocol code exists, no integration tests
**Target**: Full integration test suite for all 4 protocols

**Tasks**:
- [ ] Write MQTT integration tests (10 tests)
  - Connect, subscribe, publish, disconnect
  - QoS 0, 1, 2 verification
  - Telemetry ingestion to database
  - Error handling (broker down)
- [ ] Write CoAP integration tests (8 tests)
  - Resource discovery
  - POST telemetry (success/error)
  - GET devices
  - Error handling (invalid JSON)
- [ ] Write AMQP integration tests (8 tests)
  - Queue creation
  - Message publish/consume
  - ACK/NACK handling
  - Auto-reconnect on failure
- [ ] Write OPC UA integration tests (8 tests)
  - Server startup
  - Device node creation
  - Variable reads/writes
  - Method calls
- [ ] Run all protocol tests: `pytest tests/integration/test_protocols.py`
- [ ] Document test setup (RabbitMQ, test data)

**Acceptance Criteria**:
- ✅ 34 protocol integration tests written
- ✅ All tests passing (34/34)
- ✅ Tests run in CI/CD pipeline
- ✅ Test documentation complete

**Effort**: 8-10 hours
**Risk**: MEDIUM (protocol complexity)

---

### 8. ML Production Validation
**Current**: ML tested in dev, not validated under load
**Target**: ML performance proven under production load

**Tasks**:
- [ ] Load test: 500 predictions/min for 10 minutes
- [ ] Measure actual latency (p50, p95, p99)
- [ ] Test model training under load (concurrent requests)
- [ ] Test batch predictions (100 values/request)
- [ ] Monitor memory usage during ML operations
- [ ] Test model persistence (save/load under load)
- [ ] Verify anomaly detection accuracy (false positive rate)
- [ ] Test model retraining (weekly schedule)
- [ ] Document actual performance metrics

**Acceptance Criteria**:
- ✅ ML predictions <50ms (p95) under 500 predictions/min load
- ✅ Model training <30s for 1000 samples
- ✅ Batch predictions (100 values) <500ms
- ✅ Memory usage <500MB during ML operations
- ✅ False positive rate <10%
- ✅ Zero crashes during ML load tests

**Effort**: 4-6 hours
**Risk**: MEDIUM (performance may not meet claims)

---

## 📚 DOCUMENTATION (Week 3-4)

### 9. Production Deployment Runbook
**Current**: Development instructions only
**Target**: Complete production deployment guide

**Tasks**:
- [ ] Document server requirements (CPU, RAM, disk)
- [ ] Document OS setup (Ubuntu 22.04 LTS recommended)
- [ ] Document dependency installation (all packages)
- [ ] Document database setup (PostgreSQL, Redis, RabbitMQ)
- [ ] Document production configuration (env vars, secrets)
- [ ] Document systemd service setup (all services)
- [ ] Document Nginx + SSL setup
- [ ] Document monitoring setup (Prometheus + Grafana)
- [ ] Document backup/restore procedures
- [ ] Document rollback procedures (blue/green deployment)
- [ ] Document troubleshooting guide (common issues)
- [ ] Document scaling guide (horizontal/vertical)

**Acceptance Criteria**:
- ✅ Runbook covers complete deployment (zero to production)
- ✅ Runbook tested on clean Ubuntu 22.04 VM
- ✅ Deployment time <4 hours following runbook
- ✅ All commands copy-pasteable (no typos)

**Effort**: 6-8 hours
**Risk**: LOW

---

### 10. Update Documentation with Honest Status
**Current**: Optimistic claims in CLAUDE.md
**Target**: Accurate, realistic documentation

**Tasks**:
- [ ] Update CLAUDE.md with production status
- [ ] Remove "PRODUCTION READY" claims (replace with "Production Deployment: In Progress")
- [ ] Update protocol status (1/4 deployed → 4/4 after deployment)
- [ ] Update test coverage status (165 tests → X% coverage)
- [ ] Remove revenue projections ($2M-8M unrealistic)
- [ ] Add "Known Issues" section
- [ ] Add "Production Readiness Checklist" link
- [ ] Update version to "2.0 Beta" (not "2.0 Production")

**Acceptance Criteria**:
- ✅ No false claims in documentation
- ✅ Production status clearly marked as "In Progress"
- ✅ Known issues documented
- ✅ Realistic expectations set

**Effort**: 2-3 hours
**Risk**: NONE (accuracy improvement)

---

## 📊 PROGRESS TRACKING

### Week 1: Critical Fixes (24-28 hours)
- [ ] Security: bcrypt migration (2-3 hours)
- [ ] Multi-tenancy bug fixes (6-8 hours)
- [ ] Protocol deployment (11-14 hours)
- [ ] Production infrastructure (11-15 hours)

### Week 2: Testing & Validation (18-24 hours)
- [ ] Load testing (8-10 hours)
- [ ] Test coverage measurement (6-8 hours)
- [ ] Protocol integration tests (8-10 hours)
- [ ] ML production validation (4-6 hours)

### Week 3-4: Documentation & Polish (8-11 hours)
- [ ] Production deployment runbook (6-8 hours)
- [ ] Update documentation (2-3 hours)

**Total Effort**: 50-63 hours (approximately 2-4 weeks full-time)

---

## ✅ DEFINITION OF "PRODUCTION READY"

The platform is production-ready when:
1. ✅ All critical security vulnerabilities fixed (bcrypt)
2. ✅ All advertised features working (4/4 protocols, 10/10 tenant endpoints)
3. ✅ Load tested and validated (100 concurrent users, <1% error rate)
4. ✅ >70% test coverage measured
5. ✅ Production infrastructure deployed (Gunicorn, Nginx, SSL)
6. ✅ Monitoring operational (Prometheus + Grafana)
7. ✅ Backups automated and tested
8. ✅ Production deployment runbook complete
9. ✅ 7-day uptime demonstrated (no crashes)
10. ✅ Documentation accurate and honest

**NOT production-ready until all 10 criteria met.**

---

## 🚨 CRITICAL BLOCKERS

These MUST be fixed before ANY customer deployment:

1. **SHA256 password hashing** - CRITICAL SECURITY VULNERABILITY
2. **Multi-tenancy 500 errors** - SaaS model blocked
3. **Protocol deployment** - Only 1/4 protocols actually working
4. **No production infrastructure** - Single process, no monitoring
5. **Unknown test coverage** - Untested code in production is dangerous

---

## 🎯 REALISTIC TIMELINE

**Optimistic** (full-time, no blockers): 2 weeks
**Realistic** (part-time, 20 hours/week): 3-4 weeks
**Conservative** (blockers, learning curve): 6-8 weeks

**Start Date**: October 29, 2025
**Target Production Date**: November 26, 2025 (4 weeks, realistic)

---

**Document Owner**: Wil Aroca (w.aroca@insaing.com)
**Last Updated**: October 29, 2025
**Status**: 🔴 NOT PRODUCTION READY - 0/10 criteria met
