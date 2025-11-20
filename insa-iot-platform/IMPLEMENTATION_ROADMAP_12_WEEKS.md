# 12-Week Implementation Roadmap: Alkhorayef ESP Platform

**Platform**: Alkhorayef ESP Systems (INSA IoT Platform)
**Timeline**: 12 weeks (November 20, 2025 - February 12, 2026)
**Total Effort**: ~160 development hours
**Team**: 1 senior developer (part-time allocation)

---

## Quick Reference

| Phase | Weeks | Focus | Key Deliverables | Hours |
|-------|-------|-------|------------------|-------|
| **Phase 1** | 1-3 | Critical Stabilization | Health checks, Hypertables, JWT, Compression | 48h |
| **Phase 2** | 4-6 | Security & Data Quality | RBAC, Audit logs, ETL, Aggregates, Backups | 52h |
| **Phase 3** | 7-9 | Performance & Scalability | Caching, Vault, Monitoring, Archival | 36h |
| **Phase 4** | 10-12 | DevOps & Testing | Tests, CI/CD, Documentation, Load testing | 24h |

---

## Phase 1: Critical Stabilization (Weeks 1-3) 🔥

### Week 1: Foundation & Health Checks

**Objective**: Establish modular codebase and comprehensive health monitoring

**Tasks**:

#### Day 1-2: Modular Refactoring
- [ ] Create new directory structure:
  ```
  app/
  ├── main.py
  ├── config.py
  ├── api/v1/
  ├── core/
  ├── db/
  ├── services/
  ├── schemas/
  └── tests/
  ```
- [ ] Extract diagnostic logic from `app.py` to `app/core/diagnostics/decision_tree.py`
- [ ] Create Pydantic schemas in `app/schemas/telemetry.py`
- [ ] Set up environment config with Pydantic Settings in `app/config.py`
- [ ] Update imports across codebase

**Estimated Time**: 12 hours

**Verification**:
```bash
# Test application starts successfully
docker-compose down
docker-compose up -d
curl http://localhost:8095/docs  # Should return OpenAPI docs
```

---

#### Day 3-4: Comprehensive Health Checks
- [ ] Create `app/api/v1/routes/health.py`:
  - `/health/live` - Simple liveness check
  - `/health/ready` - Readiness with dependency checks
  - `/health` - Legacy compatibility endpoint
- [ ] Implement health check service `app/services/health_check.py`:
  ```python
  class HealthCheck:
      @staticmethod
      async def check_postgres() -> bool
      @staticmethod
      async def check_redis() -> bool
      @staticmethod
      async def check_rabbitmq() -> bool
  ```
- [ ] Update Docker Compose health checks:
  ```yaml
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8095/health/ready"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
  ```
- [ ] Test health check failure scenarios (stop Redis, verify API returns 503)

**Estimated Time**: 8 hours

**Verification**:
```bash
# Stop Redis
docker-compose stop redis
curl http://localhost:8095/health/ready  # Should return 503

# Restart Redis
docker-compose start redis
sleep 10
curl http://localhost:8095/health/ready  # Should return 200
```

---

#### Day 5: Testing & Documentation
- [ ] Write unit tests for health checks (`app/tests/test_health.py`)
- [ ] Document API endpoints in README.md
- [ ] Create runbook entry for health check failures

**Estimated Time**: 4 hours

**Week 1 Deliverables**:
- ✅ Modular codebase structure
- ✅ Comprehensive health check endpoints
- ✅ Docker health checks configured
- ✅ Basic test suite

**Week 1 Total**: 24 hours

---

### Week 2: TimescaleDB Hypertable Migration

**Objective**: Convert telemetry table to hypertable for 10x performance gain

**Tasks**:

#### Day 1: Backup & Preparation
- [ ] Create full database backup:
  ```bash
  docker exec alkhorayef-timescaledb pg_dump \
    -U alkhorayef_user -F c alkhorayef_db \
    > /var/backups/pre_migration_$(date +%Y%m%d).dump
  ```
- [ ] Test backup restoration on local development environment
- [ ] Document current table row counts and sizes:
  ```sql
  SELECT
    pg_size_pretty(pg_total_relation_size('telemetry')) AS size,
    COUNT(*) AS rows
  FROM telemetry;
  ```
- [ ] Create staging environment for migration testing

**Estimated Time**: 4 hours

---

#### Day 2-3: Migration Script Development
- [ ] Create migration SQL script: `app/db/migrations/001_create_hypertables.sql`
  ```sql
  -- Drop old table (after backup!)
  DROP TABLE IF EXISTS telemetry;

  -- Create optimized hypertable
  CREATE TABLE telemetry (
      timestamp TIMESTAMPTZ NOT NULL,
      device_id TEXT NOT NULL,
      temperature REAL CHECK (temperature BETWEEN -50 AND 200),
      vibration REAL CHECK (vibration >= 0),
      pressure REAL CHECK (pressure >= 0),
      flow_rate REAL CHECK (flow_rate >= 0),
      motor_current REAL CHECK (motor_current >= 0),
      rpm REAL CHECK (rpm >= 0),
      intake_pressure REAL,
      discharge_pressure REAL,
      data_quality_score REAL DEFAULT 1.0,
      is_anomaly BOOLEAN DEFAULT FALSE,
      ingestion_timestamp TIMESTAMPTZ DEFAULT NOW(),
      source_system TEXT DEFAULT 'scada'
  );

  -- Convert to hypertable
  SELECT create_hypertable('telemetry', 'timestamp', chunk_time_interval => INTERVAL '1 day');

  -- Create indexes
  CREATE INDEX ix_telemetry_device_time ON telemetry (device_id, timestamp DESC);
  CREATE INDEX ix_telemetry_anomaly ON telemetry (device_id, timestamp DESC) WHERE is_anomaly = TRUE;
  ```

- [ ] Create Python migration script with rollback: `app/db/migrations/migrate_to_hypertable.py`
- [ ] Test migration on staging environment with sample data
- [ ] Verify row counts match before/after

**Estimated Time**: 10 hours

---

#### Day 4: Production Migration
- [ ] Schedule maintenance window (off-peak hours)
- [ ] Execute migration on production:
  ```bash
  python app/db/migrations/migrate_to_hypertable.py
  ```
- [ ] Verify data integrity:
  ```sql
  -- Check row counts match
  SELECT COUNT(*) FROM telemetry;
  SELECT COUNT(*) FROM telemetry_backup;

  -- Verify hypertable created
  SELECT * FROM timescaledb_information.hypertables;
  ```
- [ ] Update application code to use new schema
- [ ] Restart API containers
- [ ] Monitor for 24 hours

**Estimated Time**: 4 hours

---

#### Day 5: Performance Benchmarking
- [ ] Run query performance tests:
  ```sql
  EXPLAIN ANALYZE
  SELECT device_id, AVG(temperature)
  FROM telemetry
  WHERE timestamp > NOW() - INTERVAL '24 hours'
  GROUP BY device_id;
  ```
- [ ] Compare query times (before vs after migration)
- [ ] Document performance improvements
- [ ] Delete backup table if all tests pass

**Estimated Time**: 4 hours

**Week 2 Deliverables**:
- ✅ TimescaleDB hypertable deployed
- ✅ 10x query performance improvement
- ✅ Verified backup/restore procedures
- ✅ Performance benchmarks documented

**Week 2 Total**: 22 hours

---

### Week 3: JWT Authentication & Compression

**Objective**: Secure all API endpoints and enable data compression

**Tasks**:

#### Day 1-2: JWT Authentication Implementation
- [ ] Create user model and table: `app/db/models.py`
  ```python
  class User(Base):
      __tablename__ = "users"
      id: int
      username: str
      email: str
      hashed_password: str
      role: str  # admin, operator, analyst, viewer
      is_active: bool
      created_at: datetime
  ```
- [ ] Implement authentication service: `app/core/security/auth.py`
  ```python
  class AuthService:
      @staticmethod
      def hash_password(password: str) -> str:
          # Argon2 hashing

      @staticmethod
      def verify_password(plain: str, hashed: str) -> bool:

      @staticmethod
      def create_access_token(data: dict) -> str:
          # JWT token generation

      @staticmethod
      def decode_token(token: str) -> dict:
  ```
- [ ] Create auth routes: `app/api/v1/routes/auth.py`
  - `POST /api/v1/auth/login` - Get JWT token
  - `POST /api/v1/auth/refresh` - Refresh token
  - `POST /api/v1/auth/logout` - Blacklist token
- [ ] Add authentication dependency:
  ```python
  async def get_current_user(token: str = Depends(oauth2_scheme)):
      # Verify JWT token
  ```

**Estimated Time**: 12 hours

---

#### Day 3: Secure Existing Endpoints
- [ ] Add `Depends(get_current_user)` to all protected endpoints
- [ ] Create API key authentication for M2M (SCADA systems)
- [ ] Update OpenAPI docs with security schemes
- [ ] Test authenticated requests:
  ```bash
  # Get token
  TOKEN=$(curl -X POST http://localhost:8095/api/v1/auth/login \
    -d '{"username":"admin","password":"secret"}' | jq -r .access_token)

  # Use token
  curl -H "Authorization: Bearer $TOKEN" \
    http://localhost:8095/api/v1/telemetry
  ```

**Estimated Time**: 6 hours

---

#### Day 4: Compression Policies
- [ ] Enable compression on hypertable:
  ```sql
  ALTER TABLE telemetry SET (
      timescaledb.compress,
      timescaledb.compress_segmentby = 'device_id',
      timescaledb.compress_orderby = 'timestamp DESC'
  );

  SELECT add_compression_policy('telemetry', INTERVAL '7 days');
  ```
- [ ] Monitor compression job:
  ```sql
  SELECT * FROM timescaledb_information.jobs
  WHERE proc_name = 'policy_compression';
  ```
- [ ] Verify storage reduction after 7 days
- [ ] Document compression statistics

**Estimated Time**: 4 hours

---

#### Day 5: Integration Testing
- [ ] Test authentication flow end-to-end
- [ ] Test API key authentication for M2M
- [ ] Verify compression policy running
- [ ] Load testing with authenticated requests
- [ ] Update deployment documentation

**Estimated Time**: 4 hours

**Week 3 Deliverables**:
- ✅ JWT authentication on all endpoints
- ✅ API key support for M2M clients
- ✅ Compression policies active (7-day threshold)
- ✅ 90% storage reduction (after compression runs)

**Week 3 Total**: 26 hours

**Phase 1 Total**: 72 hours (24 + 22 + 26)

---

## Phase 2: Security & Data Quality (Weeks 4-6) ⚡

### Week 4: RBAC & Audit Logging

**Objective**: Implement role-based access control and comprehensive audit trails

**Tasks**:

#### Day 1-2: RBAC System
- [ ] Define roles and permissions:
  ```python
  class Role(str, Enum):
      ADMIN = "admin"
      OPERATOR = "operator"
      ANALYST = "analyst"
      VIEWER = "viewer"
      API_CLIENT = "api_client"

  ROLE_PERMISSIONS = {
      Role.ADMIN: ["*"],
      Role.OPERATOR: ["telemetry:write", "diagnostics:read"],
      Role.ANALYST: ["telemetry:read", "diagnostics:read"],
      Role.VIEWER: ["diagnostics:read"],
      Role.API_CLIENT: ["telemetry:write"]
  }
  ```
- [ ] Implement RBAC service: `app/core/security/rbac.py`
  ```python
  class RBACService:
      @staticmethod
      def check_permission(user: User, permission: str) -> bool:
  ```
- [ ] Create permission decorator:
  ```python
  def require_permission(permission: str):
      def decorator(func):
          # Check user has permission
  ```
- [ ] Apply permissions to endpoints:
  ```python
  @router.post("/telemetry")
  @require_permission("telemetry:write")
  async def ingest_telemetry(...):
  ```

**Estimated Time**: 10 hours

---

#### Day 3-4: Audit Logging System
- [ ] Create audit log hypertable:
  ```sql
  CREATE TABLE audit_log (
      timestamp TIMESTAMPTZ NOT NULL,
      event_type TEXT NOT NULL,
      user_id INT,
      username TEXT,
      ip_address INET,
      endpoint TEXT,
      method TEXT,
      status_code INT,
      request_body JSONB,
      response_time_ms REAL,
      error_message TEXT
  );

  SELECT create_hypertable('audit_log', 'timestamp', chunk_time_interval => INTERVAL '7 days');
  ```
- [ ] Implement audit middleware: `app/core/security/audit.py`
  ```python
  @app.middleware("http")
  async def audit_middleware(request: Request, call_next):
      start_time = time.time()
      response = await call_next(request)
      duration = (time.time() - start_time) * 1000

      # Log to audit_log table
      await log_audit_event(
          event_type="api.request",
          user_id=request.state.user.id if hasattr(request.state, 'user') else None,
          endpoint=request.url.path,
          method=request.method,
          status_code=response.status_code,
          response_time_ms=duration
      )
  ```
- [ ] Create audit log query API:
  ```python
  @router.get("/api/v1/audit")
  @require_permission("audit:read")
  async def get_audit_logs(...):
  ```

**Estimated Time**: 10 hours

---

#### Day 5: Testing & Verification
- [ ] Test RBAC: Admin can access all endpoints, Viewer cannot write
- [ ] Test audit logging: All requests logged correctly
- [ ] Performance test: Audit logging doesn't slow API >10ms
- [ ] Create audit log dashboard in Grafana

**Estimated Time**: 4 hours

**Week 4 Deliverables**:
- ✅ RBAC system with 5 roles
- ✅ Comprehensive audit logging
- ✅ Permission-based endpoint protection
- ✅ Audit log query interface

**Week 4 Total**: 24 hours

---

### Week 5: ETL Pipeline & Continuous Aggregates

**Objective**: Implement data validation pipeline and pre-computed aggregates

**Tasks**:

#### Day 1-2: ETL Pipeline
- [ ] Create ETL service: `app/services/etl_pipeline.py`
  ```python
  class ETLPipeline:
      async def _transform(self, raw_data):
          # Schema validation
          # Unit conversion
          # Data quality scoring
          # Anomaly detection
          # Metadata enrichment

      async def _load_batch(self, data):
          # Batch write to TimescaleDB
  ```
- [ ] Implement data quality scoring:
  ```python
  async def _calculate_quality_score(self, data) -> float:
      # Completeness (all fields present)
      # Validity (values in range)
      # Consistency (matches historical patterns)
      # Timeliness (recent timestamp)
  ```
- [ ] Add anomaly detection (Z-score based)
- [ ] Set up dead letter queue for failed validations

**Estimated Time**: 12 hours

---

#### Day 3-4: Continuous Aggregates
- [ ] Create 1-minute aggregates:
  ```sql
  CREATE MATERIALIZED VIEW telemetry_1min
  WITH (timescaledb.continuous) AS
  SELECT
      device_id,
      time_bucket('1 minute', timestamp) AS bucket,
      AVG(temperature) AS temp_avg,
      MAX(temperature) AS temp_max,
      MIN(temperature) AS temp_min,
      AVG(vibration) AS vib_avg,
      AVG(pressure) AS pressure_avg,
      COUNT(*) AS sample_count,
      COUNT(*) FILTER (WHERE is_anomaly = TRUE) AS anomaly_count
  FROM telemetry
  GROUP BY device_id, bucket;

  SELECT add_continuous_aggregate_policy('telemetry_1min',
      start_offset => INTERVAL '1 hour',
      end_offset => INTERVAL '30 seconds',
      schedule_interval => INTERVAL '30 seconds'
  );
  ```
- [ ] Create 1-hour and daily aggregates (similar structure)
- [ ] Update API queries to use aggregates:
  ```python
  # Instead of querying raw table
  # SELECT AVG(temperature) FROM telemetry WHERE ...

  # Query pre-aggregated view
  SELECT AVG(temp_avg) FROM telemetry_1hour WHERE ...
  ```
- [ ] Benchmark query performance (before vs after)

**Estimated Time**: 10 hours

---

#### Day 5: Grafana Dashboard Updates
- [ ] Update Grafana dashboards to query aggregates
- [ ] Create data quality dashboard (quality scores over time)
- [ ] Test dashboard load times (<2 seconds)
- [ ] Document query optimization

**Estimated Time**: 4 hours

**Week 5 Deliverables**:
- ✅ ETL pipeline with data validation
- ✅ Data quality scoring (>95% target)
- ✅ Continuous aggregates (1min/1hr/daily)
- ✅ 166x faster dashboard queries

**Week 5 Total**: 26 hours

---

### Week 6: Backup Automation

**Objective**: Implement automated backup and disaster recovery

**Tasks**:

#### Day 1-2: Backup Scripts
- [ ] Create backup script: `scripts/backup_timescaledb.sh`
  ```bash
  # Dump database
  pg_dump -h localhost -U alkhorayef_user -F c \
    -f /var/backups/alkhorayef_$(date +%Y%m%d_%H%M%S).dump \
    alkhorayef_db

  # Compress
  gzip /var/backups/alkhorayef_*.dump

  # Upload to Azure
  az storage blob upload \
    --account-name insaiotbackups \
    --container-name alkhorayef-backups \
    --name alkhorayef_$(date +%Y%m%d_%H%M%S).dump.gz \
    --file /var/backups/alkhorayef_*.dump.gz

  # Cleanup local backups >7 days old
  find /var/backups -name "*.dump.gz" -mtime +7 -delete
  ```
- [ ] Create restore script: `scripts/restore_pitr.sh`
- [ ] Test backup/restore cycle

**Estimated Time**: 8 hours

---

#### Day 3: WAL Archiving (Continuous Backup)
- [ ] Configure PostgreSQL WAL archiving:
  ```
  wal_level = replica
  archive_mode = on
  archive_command = 'az storage blob upload --container-name alkhorayef-wal --name %f --file %p'
  ```
- [ ] Test WAL archiving
- [ ] Document point-in-time recovery procedure

**Estimated Time**: 4 hours

---

#### Day 4: Backup Automation
- [ ] Deploy backup scheduler:
  ```python
  # scripts/backup_scheduler.py
  from apscheduler.schedulers.blocking import BlockingScheduler

  scheduler = BlockingScheduler()

  @scheduler.scheduled_job(CronTrigger(minute=0))  # Hourly
  def hourly_snapshot():
      subprocess.run(['/scripts/backup_timescaledb.sh'])

  @scheduler.scheduled_job(CronTrigger(hour=2, minute=0))  # Daily 2 AM
  def daily_azure_backup():
      subprocess.run(['/scripts/backup_to_azure.sh'])
  ```
- [ ] Add backup container to Docker Compose
- [ ] Configure Azure Blob Storage credentials

**Estimated Time**: 6 hours

---

#### Day 5: Disaster Recovery Testing
- [ ] Simulate disaster (delete production database)
- [ ] Restore from latest backup
- [ ] Measure recovery time (should be <1 hour)
- [ ] Verify data integrity post-restore
- [ ] Document recovery runbook

**Estimated Time**: 4 hours

**Week 6 Deliverables**:
- ✅ Automated hourly local backups
- ✅ Daily Azure Blob Storage backups
- ✅ WAL archiving (continuous backup)
- ✅ Point-in-time recovery capability
- ✅ Tested disaster recovery (<1 hour RTO)

**Week 6 Total**: 22 hours

**Phase 2 Total**: 72 hours (24 + 26 + 22)

---

## Phase 3: Performance & Scalability (Weeks 7-9) 📊

### Week 7: Redis Caching Layer

**Objective**: Implement intelligent caching for query acceleration

**Tasks**:

#### Day 1-2: Cache Service Implementation
- [ ] Create caching service: `app/services/cache_service.py`
  ```python
  class CacheService:
      def __init__(self, redis_client):
          self.redis = redis_client

      async def get_or_set(self, key: str, fetch_func, ttl: int = 300):
          # Try cache first
          cached = await self.redis.get(key)
          if cached:
              return json.loads(cached)

          # Cache miss - fetch from DB
          data = await fetch_func()
          await self.redis.setex(key, ttl, json.dumps(data))
          return data

      async def invalidate(self, pattern: str):
          # Invalidate cache entries matching pattern
  ```
- [ ] Create caching decorator:
  ```python
  def cached(ttl: int = 300, key_prefix: str = ""):
      def decorator(func):
          async def wrapper(*args, **kwargs):
              cache_key = f"{key_prefix}:{func.__name__}:{args}:{kwargs}"
              return await cache_service.get_or_set(
                  cache_key,
                  lambda: func(*args, **kwargs),
                  ttl
              )
          return wrapper
      return decorator
  ```

**Estimated Time**: 8 hours

---

#### Day 3: Apply Caching to Endpoints
- [ ] Cache diagnostic queries:
  ```python
  @router.get("/diagnostics/{device_id}")
  @cached(ttl=300, key_prefix="diagnostics")
  async def get_diagnostics(device_id: str):
      # Expensive query cached for 5 minutes
  ```
- [ ] Cache device statistics
- [ ] Cache aggregated metrics
- [ ] Implement cache invalidation on data ingestion

**Estimated Time**: 4 hours

---

#### Day 4-5: Performance Testing
- [ ] Benchmark cache hit ratio (target >90%)
- [ ] Measure query latency reduction
- [ ] Load test with caching enabled
- [ ] Monitor Redis memory usage
- [ ] Configure Redis eviction policy (allkeys-lru)

**Estimated Time**: 6 hours

**Week 7 Deliverables**:
- ✅ Redis caching layer operational
- ✅ >90% cache hit ratio
- ✅ 50%+ query latency reduction
- ✅ Intelligent cache invalidation

**Week 7 Total**: 18 hours

---

### Week 8: HashiCorp Vault & Data Quality Monitoring

**Objective**: Eliminate plaintext secrets and monitor data quality

**Tasks**:

#### Day 1-2: Vault Deployment
- [ ] Add Vault to Docker Compose:
  ```yaml
  vault:
    image: vault:1.15
    container_name: alkhorayef-vault
    ports:
      - "8200:8200"
    environment:
      VAULT_DEV_ROOT_TOKEN_ID: ${VAULT_ROOT_TOKEN}
    cap_add:
      - IPC_LOCK
  ```
- [ ] Initialize Vault:
  ```bash
  vault secrets enable -path=alkhorayef kv-v2
  vault kv put alkhorayef/database \
    password='${DB_PASSWORD}' \
    username='alkhorayef_user'
  vault kv put alkhorayef/jwt \
    secret_key='${JWT_SECRET}'
  ```
- [ ] Update application to fetch secrets from Vault:
  ```python
  import hvac

  client = hvac.Client(url='http://vault:8200', token=os.getenv('VAULT_TOKEN'))
  db_creds = client.secrets.kv.v2.read_secret_version(path='database', mount_point='alkhorayef')
  DB_PASSWORD = db_creds['data']['data']['password']
  ```

**Estimated Time**: 8 hours

---

#### Day 3: Migrate All Secrets
- [ ] Move database credentials to Vault
- [ ] Move JWT secret key to Vault
- [ ] Move API keys to Vault
- [ ] Remove plaintext secrets from `.env` files
- [ ] Verify codebase has zero hardcoded secrets:
  ```bash
  grep -r "password\|secret\|key" app/ | grep -v "vault"
  # Should return 0 matches
  ```

**Estimated Time**: 4 hours

---

#### Day 4-5: Data Quality Monitoring
- [ ] Deploy data quality service: `app/services/data_quality.py`
  ```python
  class DataQualityMonitor:
      async def calculate_metrics(self, hours: int = 24):
          # Completeness, validity, consistency, timeliness
          return {
              "completeness": 98.5,
              "validity": 97.2,
              "consistency": 95.8,
              "timeliness": 99.1,
              "overall": 97.6
          }
  ```
- [ ] Create data quality dashboard in Grafana
- [ ] Set up alerts for quality score <90%
- [ ] Schedule daily quality reports

**Estimated Time**: 6 hours

**Week 8 Deliverables**:
- ✅ HashiCorp Vault deployed
- ✅ Zero plaintext secrets in codebase
- ✅ Data quality monitoring active
- ✅ Quality score >95%

**Week 8 Total**: 18 hours

---

### Week 9: Performance Monitoring & Data Archival

**Objective**: Implement comprehensive monitoring and long-term archival

**Tasks**:

#### Day 1-2: Performance Monitoring
- [ ] Deploy Prometheus metrics exporter:
  ```python
  from prometheus_client import Gauge, Counter

  db_size_bytes = Gauge('timescaledb_size_bytes', 'Database size')
  query_latency_ms = Gauge('query_latency_ms', 'Query latency', ['query_type'])
  cache_hit_ratio = Gauge('cache_hit_ratio', 'Redis cache hit ratio')
  ```
- [ ] Create performance monitoring service: `app/services/performance_monitor.py`
- [ ] Set up Grafana performance dashboard
- [ ] Configure alerts for performance degradation

**Estimated Time**: 8 hours

---

#### Day 3-4: Data Archival
- [ ] Implement archival service: `app/services/data_archival.py`
  ```python
  class DataArchivalService:
      async def archive_old_data(self, days_old: int = 25):
          # Query old data
          rows = await conn.fetch("""
              SELECT * FROM telemetry
              WHERE timestamp < NOW() - INTERVAL '{days_old} days'
          """)

          # Convert to Parquet
          df = pd.DataFrame(rows)
          parquet_buffer = df.to_parquet(compression='snappy')

          # Upload to Azure
          blob_client.upload_blob(parquet_buffer)
  ```
- [ ] Schedule daily archival (runs before retention policy deletes data)
- [ ] Test data restoration from archive
- [ ] Document archival procedures

**Estimated Time**: 8 hours

---

#### Day 5: Integration & Testing
- [ ] Test full monitoring stack (Prometheus + Grafana)
- [ ] Test archival and restoration cycle
- [ ] Verify retention policy doesn't delete unarchived data
- [ ] Document operational procedures

**Estimated Time**: 4 hours

**Week 9 Deliverables**:
- ✅ Prometheus metrics exported
- ✅ Performance monitoring dashboard
- ✅ Automated data archival to Azure
- ✅ Data restoration tested

**Week 9 Total**: 20 hours

**Phase 3 Total**: 56 hours (18 + 18 + 20)

---

## Phase 4: DevOps & Testing (Weeks 10-12) 🔬

### Week 10: Test Suite Development

**Objective**: Achieve >80% test coverage

**Tasks**:

#### Day 1-3: Unit Tests
- [ ] Set up pytest infrastructure:
  ```python
  # app/tests/conftest.py
  @pytest.fixture
  async def db_pool():
      pool = await asyncpg.create_pool(TEST_DATABASE_URL)
      yield pool
      await pool.close()

  @pytest.fixture
  async def test_client():
      async with AsyncClient(app=app, base_url="http://test") as client:
          yield client
  ```
- [ ] Write unit tests for core modules:
  - `test_diagnostics.py` - Diagnostic decision tree logic
  - `test_auth.py` - JWT authentication
  - `test_rbac.py` - Permission checking
  - `test_data_quality.py` - Quality scoring
  - `test_etl.py` - ETL transformation logic
- [ ] Achieve >80% coverage on core modules

**Estimated Time**: 12 hours

---

#### Day 4-5: Integration Tests
- [ ] Write integration tests:
  - `test_api_telemetry.py` - End-to-end telemetry ingestion
  - `test_api_auth.py` - Login flow
  - `test_api_diagnostics.py` - Diagnostic queries
  - `test_database.py` - Database operations
  - `test_cache.py` - Redis caching
- [ ] Run test suite:
  ```bash
  pytest --cov=app --cov-report=html
  # Should show >80% coverage
  ```

**Estimated Time**: 8 hours

**Week 10 Deliverables**:
- ✅ >80% test coverage
- ✅ Automated test suite (pytest)
- ✅ Coverage reports generated

**Week 10 Total**: 20 hours

---

### Week 11: CI/CD Pipeline

**Objective**: Automate testing and deployment

**Tasks**:

#### Day 1-2: GitHub Actions CI Pipeline
- [ ] Create `.github/workflows/ci.yml`:
  ```yaml
  name: CI Pipeline

  on: [push, pull_request]

  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - name: Set up Python
          uses: actions/setup-python@v4
          with:
            python-version: '3.11'
        - name: Install dependencies
          run: |
            pip install -r requirements.txt
            pip install pytest pytest-cov
        - name: Run tests
          run: pytest --cov=app --cov-fail-under=80
        - name: Security scan (Bandit)
          run: bandit -r app/
        - name: Lint (Flake8)
          run: flake8 app/
  ```
- [ ] Test CI pipeline on feature branch
- [ ] Ensure all checks pass

**Estimated Time**: 8 hours

---

#### Day 3-4: CD Pipeline (Deployment)
- [ ] Create deployment workflow:
  ```yaml
  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          ssh deploy@server "cd /app && git pull && docker-compose up -d --build"
      - name: Health check
        run: curl -f http://production-url/health/ready || exit 1
  ```
- [ ] Set up deployment secrets (SSH keys, etc.)
- [ ] Test deployment to staging environment

**Estimated Time**: 8 hours

---

#### Day 5: Documentation
- [ ] Update README.md with CI/CD instructions
- [ ] Document deployment process
- [ ] Create troubleshooting guide

**Estimated Time**: 4 hours

**Week 11 Deliverables**:
- ✅ CI/CD pipeline operational (GitHub Actions)
- ✅ Automated testing on every commit
- ✅ Automated deployment to production
- ✅ Deployment documentation complete

**Week 11 Total**: 20 hours

---

### Week 12: Load Testing & Final Documentation

**Objective**: Validate production readiness and complete documentation

**Tasks**:

#### Day 1-2: Load Testing
- [ ] Create load test script (Locust or k6):
  ```python
  from locust import HttpUser, task, between

  class ESPUser(HttpUser):
      wait_time = between(1, 3)

      @task
      def ingest_telemetry(self):
          self.client.post("/api/v1/telemetry",
              json={
                  "device_id": "ESP001",
                  "timestamp": "2025-11-20T10:00:00Z",
                  "temperature": 85.0,
                  "vibration": 0.05,
                  "pressure": 250.0,
                  "flow_rate": 1500.0
              },
              headers={"Authorization": f"Bearer {self.token}"}
          )

      @task
      def get_diagnostics(self):
          self.client.get("/api/v1/diagnostics/ESP001")
  ```
- [ ] Run load tests:
  - 1,000 concurrent users
  - 10,000 requests/second ingestion rate
  - Measure latency (p50, p95, p99)
  - Monitor resource usage (CPU, RAM, disk I/O)

**Estimated Time**: 10 hours

---

#### Day 3-4: Performance Tuning
- [ ] Analyze load test results
- [ ] Tune database connection pool
- [ ] Tune Gunicorn workers (CPU × 2 + 1)
- [ ] Optimize slow queries
- [ ] Re-run load tests to verify improvements

**Estimated Time**: 8 hours

---

#### Day 5: Final Documentation
- [ ] Complete API documentation (OpenAPI)
- [ ] Create operational runbook:
  - How to deploy
  - How to backup/restore
  - How to monitor
  - How to troubleshoot common issues
- [ ] Create architecture diagram (updated)
- [ ] Knowledge transfer session with team

**Estimated Time**: 6 hours

**Week 12 Deliverables**:
- ✅ Load testing completed (10,000 req/s sustained)
- ✅ Performance optimized
- ✅ Complete operational documentation
- ✅ Production readiness verified

**Week 12 Total**: 24 hours

**Phase 4 Total**: 64 hours (20 + 20 + 24)

---

## Total Effort Summary

| Phase | Hours | Percentage |
|-------|-------|------------|
| Phase 1: Critical Stabilization | 72h | 37% |
| Phase 2: Security & Data Quality | 72h | 37% |
| Phase 3: Performance & Scalability | 56h | 28% |
| Phase 4: DevOps & Testing | 64h | 33% |
| **Total** | **264h** | **100%** |

**Note**: Original estimate was 160h, revised to 264h after detailed task breakdown. More realistic for production-grade implementation.

**Weekly Breakdown**:
- Average: 22 hours/week
- Peak: Week 2 & 5 (26 hours each)
- Minimum: Week 7 & 8 (18 hours each)

---

## Success Checklist

### Phase 1 ✅
- [ ] Modular codebase structure
- [ ] Health checks operational (99.9% uptime)
- [ ] Hypertable migration complete (10x performance)
- [ ] JWT authentication on all endpoints
- [ ] Compression policies active (80% storage reduction)

### Phase 2 ✅
- [ ] RBAC system deployed (5 roles)
- [ ] Audit logging capturing 100% of requests
- [ ] ETL pipeline validating data quality (>95%)
- [ ] Continuous aggregates (166x dashboard speed)
- [ ] Automated backups to Azure (100% success)

### Phase 3 ✅
- [ ] Redis caching (>90% hit ratio)
- [ ] Vault managing all secrets
- [ ] Performance monitoring dashboard
- [ ] Data archival to Azure operational

### Phase 4 ✅
- [ ] Test coverage >80%
- [ ] CI/CD pipeline deployed
- [ ] Load testing passed (10,000 req/s)
- [ ] Documentation complete

---

## Risk Management

### High-Risk Weeks

**Week 2 (Hypertable Migration)**:
- **Risk**: Data loss during migration
- **Mitigation**: Full backup, staging test, rollback plan

**Week 3 (JWT Authentication)**:
- **Risk**: Breaking existing API clients
- **Mitigation**: API versioning, backwards compatibility layer

**Week 6 (Backup Testing)**:
- **Risk**: Backup corruption not detected
- **Mitigation**: Test restore, verify checksums

### Contingency Buffer

- **Planned**: 264 hours over 12 weeks
- **Buffer**: +20% (53 hours) for unexpected issues
- **Total**: 317 hours maximum

---

## Deployment Schedule (Recommended)

**Low-Risk Deployments (Anytime)**:
- Health checks
- Monitoring
- Testing infrastructure
- Documentation

**Medium-Risk Deployments (Off-Peak Hours)**:
- JWT authentication (backward compatible)
- RBAC (doesn't break existing functionality)
- Caching (transparent to clients)

**High-Risk Deployments (Scheduled Maintenance)**:
- Hypertable migration (Week 2, Day 4)
- Database schema changes
- Breaking API changes

**Recommended Maintenance Windows**:
- **Day**: Sunday
- **Time**: 2:00 AM - 6:00 AM (Local time, Saudi Arabia)
- **Frequency**: Bi-weekly for major changes

---

## Next Steps

**Immediate (This Week)**:
1. Review and approve this roadmap
2. Set up development environment
3. Create Git feature branches for Phase 1 tasks
4. Schedule Week 2 maintenance window (hypertable migration)

**Ongoing**:
- Weekly progress review meetings
- Daily standups (15 minutes)
- Bi-weekly stakeholder demos

---

**Document Status**: ✅ Complete and Ready for Execution
**Last Updated**: November 20, 2025
**Next Review**: End of Phase 1 (Week 3)
