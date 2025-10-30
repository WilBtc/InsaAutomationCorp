# Phase 3 Remaining Implementation Plan

**Date**: October 28, 2025 01:50 UTC
**Current Progress**: 4/10 features complete (40%)
**Remaining**: 6 features (60%)
**Estimated Completion**: 4-6 weeks

---

## Executive Summary

With Feature 1 (Advanced Analytics) complete, we have a solid foundation of time-series analysis and statistical capabilities. The remaining 6 features build on this foundation to add AI intelligence, enterprise capabilities, and broader protocol support.

**Recommended Implementation Order:**
1. Feature 2: Machine Learning (Week 1-2) - Builds on analytics foundation
2. Feature 7: Data Retention (Week 2) - Critical for production scalability
3. Feature 8: Advanced Alerting (Week 3) - Enhances existing alert system
4. Feature 6: Multi-tenancy (Week 4) - Enterprise requirement
5. Feature 4: Additional Protocols (Week 5-6) - Expands connectivity
6. Feature 3: Mobile App (Week 6+) - Optional, can be Phase 4

---

## Feature 2: Machine Learning - Anomaly Detection

**Priority**: HIGH (Next to implement)
**Estimated Time**: 2 weeks
**Complexity**: High
**Dependencies**: Feature 1 (Analytics) ✅

### Scope

Implement AI-powered anomaly detection to automatically identify unusual patterns in sensor data.

**Sub-features:**
1. Statistical anomaly detection (Z-score, IQR methods)
2. Time-series anomaly detection (isolation forest, LSTM)
3. Multi-dimensional anomaly detection (correlation-based)
4. Anomaly scoring and severity classification
5. Automatic baseline learning
6. Anomaly alert integration

### Technical Approach

**Algorithm Selection:**
- **Z-score method**: For simple univariate detection (lightweight)
- **Isolation Forest**: For multivariate detection (sklearn)
- **LSTM Autoencoder**: For time-series patterns (TensorFlow/PyTorch - optional)
- **Statistical Process Control**: For industrial metrics (3-sigma rule)

**Database Schema:**
```sql
-- New tables
CREATE TABLE anomaly_models (
    id SERIAL PRIMARY KEY,
    device_id UUID REFERENCES devices(id),
    metric VARCHAR(50),
    model_type VARCHAR(50),  -- 'zscore', 'isolation_forest', 'lstm'
    parameters JSONB,
    baseline_start TIMESTAMP,
    baseline_end TIMESTAMP,
    trained_at TIMESTAMP,
    accuracy_score FLOAT
);

CREATE TABLE anomalies (
    id SERIAL PRIMARY KEY,
    device_id UUID REFERENCES devices(id),
    metric VARCHAR(50),
    timestamp TIMESTAMP,
    value FLOAT,
    expected_value FLOAT,
    anomaly_score FLOAT,  -- 0-1, higher = more anomalous
    severity VARCHAR(20),  -- 'low', 'medium', 'high', 'critical'
    method VARCHAR(50),
    model_id INTEGER REFERENCES anomaly_models(id),
    acknowledged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_anomalies_device_time ON anomalies(device_id, timestamp DESC);
CREATE INDEX idx_anomalies_severity ON anomalies(severity, acknowledged);
```

**API Endpoints (6 new):**
1. `POST /api/v1/ml/models` - Train anomaly detection model
2. `GET /api/v1/ml/models` - List trained models
3. `GET /api/v1/ml/models/{id}` - Get model details
4. `DELETE /api/v1/ml/models/{id}` - Delete model
5. `POST /api/v1/ml/detect` - Run anomaly detection on data
6. `GET /api/v1/ml/anomalies` - List detected anomalies

**Implementation Steps:**

**Week 1: Statistical Methods & Infrastructure**
1. Install ML dependencies (scikit-learn, numpy)
2. Create database schema (anomaly_models, anomalies tables)
3. Implement Z-score anomaly detection
4. Implement IQR (Interquartile Range) method
5. Create baseline learning functionality
6. Build model training API endpoint

**Week 2: Advanced Methods & Integration**
1. Implement Isolation Forest for multivariate detection
2. Create anomaly scoring system (0-1 scale)
3. Integrate with existing alert system
4. Build anomaly dashboard queries
5. Create anomaly acknowledgment workflow
6. Performance optimization and caching

**Testing Strategy:**
- Inject synthetic anomalies into test data
- Validate detection accuracy (precision/recall)
- Test false positive rate (<5% target)
- Load test with 1000+ devices
- Integration with alert system

**Success Metrics:**
- Detection accuracy: >95% for obvious anomalies
- False positive rate: <5%
- Training time: <30 seconds for 1000 data points
- Detection latency: <200ms per metric

**Estimated Lines of Code**: ~600 lines

---

## Feature 7: Data Retention Policies

**Priority**: HIGH (Week 2)
**Estimated Time**: 3-5 days
**Complexity**: Medium
**Dependencies**: None

### Scope

Implement automatic data archival and cleanup to prevent database bloat and ensure compliance.

**Sub-features:**
1. Configurable retention policies per metric/device
2. Automatic data archival to cold storage
3. Data aggregation (downsample old data)
4. Automatic cleanup of expired data
5. Retention policy API management
6. Compliance reporting

### Technical Approach

**Retention Tiers:**
- **Hot data**: 0-7 days (full resolution, PostgreSQL)
- **Warm data**: 7-90 days (1-minute aggregates, PostgreSQL)
- **Cold data**: 90+ days (1-hour aggregates, compressed files or S3)
- **Expired data**: Delete after retention period

**Database Schema:**
```sql
CREATE TABLE retention_policies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    device_id UUID REFERENCES devices(id),  -- NULL for default policy
    metric VARCHAR(50),  -- NULL for all metrics
    hot_days INTEGER DEFAULT 7,
    warm_days INTEGER DEFAULT 90,
    cold_days INTEGER DEFAULT 365,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Aggregated data tables
CREATE TABLE telemetry_1min (
    device_id UUID,
    key VARCHAR(50),
    timestamp TIMESTAMP,
    avg_value FLOAT,
    min_value FLOAT,
    max_value FLOAT,
    count INTEGER,
    PRIMARY KEY (device_id, key, timestamp)
);

CREATE TABLE telemetry_1hour (
    device_id UUID,
    key VARCHAR(50),
    timestamp TIMESTAMP,
    avg_value FLOAT,
    min_value FLOAT,
    max_value FLOAT,
    count INTEGER,
    PRIMARY KEY (device_id, key, timestamp)
);
```

**Implementation Steps:**

**Day 1-2: Infrastructure**
1. Create retention policy tables
2. Create aggregated data tables
3. Build policy management API (CRUD)
4. Create archival worker script

**Day 3-4: Archival Logic**
1. Implement 1-minute aggregation function
2. Implement 1-hour aggregation function
3. Create data export to JSON/Parquet
4. Build cleanup scheduler (cron job)

**Day 5: Testing & Optimization**
1. Test with large datasets (1M+ records)
2. Optimize aggregation queries
3. Verify data integrity after cleanup
4. Create monitoring dashboard

**API Endpoints (5 new):**
1. `POST /api/v1/retention/policies` - Create policy
2. `GET /api/v1/retention/policies` - List policies
3. `PUT /api/v1/retention/policies/{id}` - Update policy
4. `DELETE /api/v1/retention/policies/{id}` - Delete policy
5. `POST /api/v1/retention/run` - Manual archival run

**Estimated Lines of Code**: ~400 lines

---

## Feature 8: Advanced Alerting

**Priority**: MEDIUM-HIGH (Week 3)
**Estimated Time**: 1 week
**Complexity**: Medium
**Dependencies**: Feature 2 (ML) recommended but not required

### Scope

Enhance existing alert system with escalation policies, on-call schedules, and advanced notification routing.

**Sub-features:**
1. Escalation policies (multi-level)
2. On-call schedules and rotations
3. Alert grouping and deduplication
4. Alert severity levels (critical/high/medium/low)
5. Snooze and acknowledgment workflows
6. Integration with PagerDuty/Slack/Teams

### Technical Approach

**Database Schema:**
```sql
CREATE TABLE escalation_policies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    levels JSONB,  -- [{level: 1, wait_minutes: 5, contacts: [...]}, ...]
    enabled BOOLEAN DEFAULT TRUE
);

CREATE TABLE oncall_schedules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'UTC',
    rotations JSONB,  -- [{day: 'monday', start: '09:00', end: '17:00', user_id: 1}, ...]
    enabled BOOLEAN DEFAULT TRUE
);

CREATE TABLE alert_incidents (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES alerts(id),
    status VARCHAR(20),  -- 'open', 'acknowledged', 'resolved', 'snoozed'
    severity VARCHAR(20),  -- 'critical', 'high', 'medium', 'low'
    escalation_level INTEGER DEFAULT 1,
    assigned_to INTEGER REFERENCES users(id),
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    snoozed_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE alert_notifications (
    id SERIAL PRIMARY KEY,
    incident_id INTEGER REFERENCES alert_incidents(id),
    channel VARCHAR(50),  -- 'email', 'sms', 'slack', 'webhook'
    recipient VARCHAR(255),
    status VARCHAR(20),  -- 'pending', 'sent', 'failed'
    sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Implementation Steps:**

**Day 1-2: Infrastructure**
1. Create escalation and on-call tables
2. Build escalation policy API
3. Create on-call schedule API
4. Implement alert severity classification

**Day 3-4: Escalation Logic**
1. Build escalation engine (background worker)
2. Implement alert grouping (same device/metric)
3. Create acknowledgment/snooze workflows
4. Build notification routing logic

**Day 5: Integrations**
1. Slack integration (webhook)
2. PagerDuty integration (optional)
3. SMS integration (Twilio - optional)
4. Dashboard for alert management

**API Endpoints (8 new):**
1. `POST /api/v1/alerts/escalation-policies` - Create policy
2. `GET /api/v1/alerts/escalation-policies` - List policies
3. `POST /api/v1/alerts/oncall-schedules` - Create schedule
4. `GET /api/v1/alerts/oncall-schedules` - List schedules
5. `GET /api/v1/alerts/incidents` - List alert incidents
6. `POST /api/v1/alerts/incidents/{id}/acknowledge` - Acknowledge
7. `POST /api/v1/alerts/incidents/{id}/snooze` - Snooze alert
8. `POST /api/v1/alerts/incidents/{id}/resolve` - Resolve alert

**Estimated Lines of Code**: ~500 lines

---

## Feature 6: Multi-tenancy

**Priority**: MEDIUM (Week 4)
**Estimated Time**: 1 week
**Complexity**: High
**Dependencies**: Feature 5 (RBAC) ✅

### Scope

Add support for multiple organizations/tenants with data isolation and separate billing.

**Sub-features:**
1. Tenant/organization management
2. Data isolation (row-level security)
3. Tenant-specific configuration
4. Cross-tenant user access (optional)
5. Tenant usage tracking
6. API key per tenant

### Technical Approach

**Database Schema:**
```sql
CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    subdomain VARCHAR(50) UNIQUE,  -- e.g., 'acme' for acme.iot-portal.com
    plan VARCHAR(50) DEFAULT 'free',  -- 'free', 'pro', 'enterprise'
    max_devices INTEGER,
    max_users INTEGER,
    settings JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- Add tenant_id to all main tables
ALTER TABLE devices ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
ALTER TABLE users ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
ALTER TABLE telemetry ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
ALTER TABLE alerts ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
-- ... etc for all tables

-- Row-level security policies
CREATE POLICY tenant_isolation ON devices
    USING (tenant_id = current_setting('app.current_tenant')::INTEGER);

CREATE TABLE tenant_usage (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id),
    date DATE,
    device_count INTEGER,
    telemetry_count BIGINT,
    api_calls INTEGER,
    storage_mb FLOAT
);
```

**Implementation Steps:**

**Day 1-2: Schema Migration**
1. Create tenants table
2. Add tenant_id to all tables
3. Migrate existing data to default tenant
4. Create row-level security policies

**Day 3-4: Tenant Management**
1. Build tenant CRUD API
2. Implement tenant context middleware
3. Create tenant switching logic
4. Build usage tracking system

**Day 5-7: Testing & Polish**
1. Test data isolation thoroughly
2. Create tenant admin dashboard
3. Build tenant billing queries
4. Documentation and examples

**API Endpoints (6 new):**
1. `POST /api/v1/tenants` - Create tenant (superadmin only)
2. `GET /api/v1/tenants` - List tenants
3. `GET /api/v1/tenants/{id}` - Get tenant details
4. `PUT /api/v1/tenants/{id}` - Update tenant
5. `GET /api/v1/tenants/{id}/usage` - Get usage stats
6. `POST /api/v1/tenants/{id}/switch` - Switch active tenant

**Estimated Lines of Code**: ~600 lines

---

## Feature 4: Additional Protocols

**Priority**: MEDIUM-LOW (Week 5-6)
**Estimated Time**: 2 weeks
**Complexity**: High
**Dependencies**: None

### Scope

Add support for industrial IoT protocols beyond MQTT.

**Protocols to Add:**
1. **CoAP** (Constrained Application Protocol) - Lightweight for constrained devices
2. **AMQP** (Advanced Message Queuing Protocol) - Enterprise messaging
3. **OPC UA** (Open Platform Communications) - Industrial automation standard

### Technical Approach

**CoAP Server (Week 5, Day 1-3):**
- Python library: `aiocoap`
- Port: 5683 (standard CoAP)
- Resource discovery: `/.well-known/core`
- Observe pattern for real-time updates

**AMQP Support (Week 5, Day 4-5):**
- Use RabbitMQ as broker
- Python library: `pika`
- Port: 5672 (standard AMQP)
- Exchange/queue setup for device messages

**OPC UA Server (Week 6):**
- Python library: `asyncua`
- Port: 4840 (standard OPC UA)
- Node structure for devices/metrics
- Subscription support for real-time updates

**Implementation Steps:**

**Week 5:**
1. Install CoAP server (aiocoap)
2. Create CoAP endpoints for telemetry
3. Test CoAP client connectivity
4. Install RabbitMQ for AMQP
5. Create AMQP consumer for device messages
6. Test AMQP client connectivity

**Week 6:**
1. Install OPC UA server (asyncua)
2. Create OPC UA node structure
3. Implement telemetry publishing
4. Test OPC UA client connectivity
5. Create protocol documentation
6. Build protocol selection in device config

**Estimated Lines of Code**: ~800 lines (across 3 protocols)

---

## Feature 3: Mobile App Support

**Priority**: LOW (Week 6+, or Phase 4)
**Estimated Time**: 3-4 weeks
**Complexity**: Very High
**Dependencies**: None (can be separate project)

### Scope

Create companion mobile apps for iOS and Android.

**Recommendation**: **Defer to Phase 4**

**Reasoning:**
1. Mobile app is a separate codebase (React Native/Flutter)
2. Requires app store approval process
3. Backend API already supports mobile via REST
4. Lower priority than core platform features
5. Can be developed in parallel by dedicated mobile team

**If Implemented in Phase 3:**

**Approach**: Progressive Web App (PWA) first, native apps later

**PWA Features (2 weeks):**
1. Responsive design (mobile-first)
2. Offline support (service workers)
3. Push notifications (Web Push API)
4. Home screen installation
5. Camera access for QR code scanning

**Native App Features (if needed, 2+ weeks):**
1. React Native or Flutter framework
2. Biometric authentication
3. Background location tracking (optional)
4. Native push notifications
5. App store deployment

**Estimated Lines of Code**:
- PWA: ~1000 lines
- Native apps: ~3000 lines each (iOS + Android)

**Recommendation**: Build PWA in Phase 3, defer native apps to Phase 4

---

## Implementation Timeline

### Recommended Order & Timeline

**Month 1 (Weeks 1-4):**
- **Week 1**: Feature 2 (ML) - Part 1 (Statistical methods)
- **Week 2**: Feature 2 (ML) - Part 2 (Advanced methods) + Feature 7 (Retention)
- **Week 3**: Feature 8 (Advanced Alerting)
- **Week 4**: Feature 6 (Multi-tenancy)

**Month 2 (Weeks 5-6):**
- **Week 5**: Feature 4 (Protocols) - CoAP + AMQP
- **Week 6**: Feature 4 (Protocols) - OPC UA + Feature 3 (PWA decision)

**Total Estimated Time**: 6 weeks for 5 features (defer Feature 3 mobile)

### Alternative Order (Production-First)

If prioritizing production readiness over features:

**Priority 1 (Immediate):**
1. Feature 7: Data Retention (prevent database bloat)
2. Feature 8: Advanced Alerting (improve operations)

**Priority 2 (Near-term):**
3. Feature 2: Machine Learning (AI capabilities)
4. Feature 6: Multi-tenancy (enterprise requirement)

**Priority 3 (Later):**
5. Feature 4: Additional Protocols (expand connectivity)
6. Feature 3: Mobile App (nice-to-have)

---

## Resource Requirements

### Infrastructure

**Additional Services:**
- **RabbitMQ**: For AMQP support (~500MB RAM)
- **Redis**: For ML model caching (already installed)
- **PostgreSQL**: May need storage expansion for retention tiers

**Estimated Additional Storage:**
- Raw telemetry: ~1GB/month for 100 devices
- Aggregated data: ~100MB/month
- ML models: ~50MB total
- Total: Plan for 20GB+ for 1 year retention

### Dependencies

**Python Packages:**
```bash
# Feature 2 (ML)
scikit-learn==1.3.2
numpy==1.24.3
pandas==2.1.3
joblib==1.3.2

# Feature 4 (Protocols)
aiocoap==0.4.7
pika==1.3.2
asyncua==1.0.0

# Feature 8 (Alerting)
python-slack-sdk==3.23.0
twilio==8.10.0  # optional
```

### Testing Requirements

**Test Data Needs:**
- 10,000+ telemetry records for ML training
- 50+ devices for multi-tenancy testing
- Synthetic anomaly injection scripts
- Protocol client simulators (CoAP, AMQP, OPC UA)

---

## Success Metrics

### Feature 2 (ML)
- [ ] Anomaly detection accuracy >95%
- [ ] False positive rate <5%
- [ ] Model training time <30s
- [ ] Detection latency <200ms

### Feature 7 (Retention)
- [ ] Database size reduction >50% after 90 days
- [ ] Aggregation accuracy >99%
- [ ] Archival process <5 minutes
- [ ] Zero data loss during cleanup

### Feature 8 (Alerting)
- [ ] Escalation delay <60 seconds
- [ ] Notification delivery >99.5%
- [ ] Alert deduplication >90%
- [ ] Zero missed critical alerts

### Feature 6 (Multi-tenancy)
- [ ] Complete data isolation (0% leakage)
- [ ] Performance impact <10%
- [ ] Tenant switching <100ms
- [ ] Support 100+ tenants

### Feature 4 (Protocols)
- [ ] CoAP throughput >1000 msg/sec
- [ ] AMQP reliability >99.9%
- [ ] OPC UA latency <100ms
- [ ] Zero message loss

---

## Risk Assessment

### High Risk
- **Feature 2 (ML)**: Complex algorithms, potential performance issues
  - Mitigation: Start with simple methods, optimize incrementally
- **Feature 6 (Multi-tenancy)**: Data isolation bugs could be catastrophic
  - Mitigation: Extensive testing, code review, row-level security

### Medium Risk
- **Feature 4 (Protocols)**: New protocol stacks, compatibility issues
  - Mitigation: Use mature libraries, thorough client testing
- **Feature 8 (Alerting)**: Escalation logic complexity
  - Mitigation: Clear state machine, comprehensive testing

### Low Risk
- **Feature 7 (Retention)**: Well-understood problem
  - Mitigation: Test with production-like data volumes

---

## Documentation Requirements

### Per Feature
1. Implementation guide (PHASE3_FEATURE{N}_IMPLEMENTATION.md)
2. API documentation (add to Swagger)
3. User guide (how to configure/use)
4. Test report (PHASE3_FEATURE{N}_TEST_REPORT.md)
5. Performance benchmarks

### Overall Phase 3
1. Complete Phase 3 summary document
2. Migration guide (if schema changes)
3. Deployment checklist
4. Monitoring and observability guide

---

## Next Steps

**Immediate (This Week):**
1. Review and approve this plan
2. Set up ML development environment
3. Install scikit-learn and dependencies
4. Create Feature 2 detailed design document
5. Prepare test dataset for ML training

**Next Week:**
1. Begin Feature 2 implementation
2. Create anomaly detection database schema
3. Implement Z-score and IQR methods
4. Build model training API

---

## Questions for Stakeholder

1. **Priority Confirmation**: Agree with ML → Retention → Alerting order?
2. **Mobile App**: Defer to Phase 4 or build PWA now?
3. **Multi-tenancy**: Required for launch or can wait?
4. **Protocols**: Which protocol is highest priority (CoAP/AMQP/OPC UA)?
5. **Timeline**: Is 6-week timeline acceptable?
6. **Resources**: Need additional infrastructure budget for RabbitMQ/storage?

---

**Created**: October 28, 2025 01:50 UTC
**Author**: AI Assistant (Claude Code)
**Status**: DRAFT - Awaiting Approval
**Version**: 1.0
