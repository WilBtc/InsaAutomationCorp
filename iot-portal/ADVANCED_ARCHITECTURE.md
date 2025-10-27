# INSA Advanced IIoT Platform - Architecture Design
**Version:** 2.0
**Date:** October 27, 2025
**Status:** 🚧 In Development

---

## 1. Architecture Overview

### 1.1 System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    INSA Advanced IIoT Platform                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Web UI     │  │  Mobile App  │  │  3rd Party   │          │
│  │  (Vue.js)    │  │ (React Native)│  │    Apps      │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│         └──────────────────┴──────────────────┘                  │
│                            │                                      │
│  ┌─────────────────────────▼──────────────────────────┐         │
│  │              REST API Layer                         │         │
│  │  /api/v1/devices  /api/v1/telemetry               │         │
│  │  /api/v1/alerts   /api/v1/rules                   │         │
│  │  /api/v1/reports  /api/v1/dashboards              │         │
│  └─────────────────────────┬──────────────────────────┘         │
│                            │                                      │
│  ┌─────────────────────────▼──────────────────────────┐         │
│  │           WebSocket / Real-time Layer              │         │
│  │  Socket.IO: Live telemetry, alerts, status        │         │
│  └─────────────────────────┬──────────────────────────┘         │
│                            │                                      │
│  ┌────────────────────┬────▼────┬─────────────────────┐         │
│  │  Device Manager    │ Rule    │  Report Generator   │         │
│  │  • Registration    │ Engine  │  • Excel            │         │
│  │  • Config          │ • Alerts│  • PDF              │         │
│  │  • Status          │ • Actions│ • ZIP              │         │
│  └────────┬───────────┴────┬────┴─────────┬───────────┘         │
│           │                 │              │                      │
│  ┌────────▼─────────────────▼──────────────▼───────────┐        │
│  │              Data Processing Layer                    │        │
│  │  • Time-series aggregation                           │        │
│  │  • Anomaly detection                                 │        │
│  │  • Data validation                                   │        │
│  └────────┬──────────────────────────────────┬──────────┘        │
│           │                                   │                   │
│  ┌────────▼────────────┐           ┌─────────▼────────┐         │
│  │  MQTT Broker        │           │  HTTP Ingestion  │         │
│  │  (Mosquitto)        │           │  (REST API)      │         │
│  │  Port: 1883/8883    │           │  Port: 5001      │         │
│  └────────┬────────────┘           └─────────┬────────┘         │
│           │                                   │                   │
│           └───────────────┬───────────────────┘                  │
│                           │                                       │
│  ┌────────────────────────▼──────────────────────────┐          │
│  │            PostgreSQL Database                      │          │
│  │  • devices (id, name, type, config, status)       │          │
│  │  • telemetry (timestamp, device_id, key, value)   │          │
│  │  • alerts (id, device_id, rule_id, timestamp)     │          │
│  │  • rules (id, condition, action, enabled)         │          │
│  │  • dashboards (id, user_id, widgets, layout)      │          │
│  └───────────────────────────────────────────────────┘          │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

        ▲                          ▲                    ▲
        │                          │                    │
   IoT Devices              SCADA Systems         Edge Gateways
   (MQTT/HTTP)              (OPC-UA/Modbus)       (Local processing)
```

### 1.2 Technology Stack

**Backend:**
- Flask 3.0+ (API framework)
- Flask-SocketIO 5.3+ (WebSocket support)
- Flask-CORS (Cross-origin support)
- Flask-JWT-Extended (Authentication)
- Celery 5.3+ (Task queue)
- Redis 7.2+ (Cache + message broker)

**Database:**
- PostgreSQL 16 (Primary data store)
- TimescaleDB extension (Time-series optimization)
- Redis (Cache + real-time data)

**MQTT:**
- Eclipse Mosquitto 2.0+ (MQTT broker)
- paho-mqtt 2.1+ (Python client)

**Data Processing:**
- pandas 2.2+ (Data analysis)
- numpy 1.26+ (Numerical operations)
- scipy 1.11+ (Statistical analysis)

**Visualization:**
- Chart.js 4.4+ (Charts)
- Plotly 5.24+ (Advanced charts)
- Grafana integration (Dashboards)

**Security:**
- JWT tokens (API authentication)
- API keys (Device authentication)
- TLS/SSL (Encrypted communication)
- OAuth2 (SSO support)

---

## 2. Database Schema

### 2.1 Core Tables

```sql
-- Devices table
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL, -- sensor, actuator, gateway
    location VARCHAR(255),
    area VARCHAR(100),
    protocol VARCHAR(50), -- mqtt, http, modbus, opcua
    connection_string TEXT,
    config JSONB, -- Device-specific configuration
    status VARCHAR(20) DEFAULT 'offline', -- online, offline, error
    last_seen TIMESTAMP,
    metadata JSONB, -- Manufacturer, model, firmware, etc
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Telemetry data (TimescaleDB hypertable)
CREATE TABLE telemetry (
    timestamp TIMESTAMP NOT NULL,
    device_id UUID NOT NULL REFERENCES devices(id),
    key VARCHAR(100) NOT NULL, -- temperature, humidity, pressure, etc
    value DOUBLE PRECISION,
    unit VARCHAR(20), -- C, F, %, Pa, etc
    quality INTEGER DEFAULT 100, -- 0-100 data quality score
    metadata JSONB
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('telemetry', 'timestamp');

-- Alerts table
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID REFERENCES devices(id),
    rule_id UUID REFERENCES rules(id),
    severity VARCHAR(20), -- info, warning, critical
    message TEXT,
    value DOUBLE PRECISION,
    threshold DOUBLE PRECISION,
    status VARCHAR(20) DEFAULT 'active', -- active, acknowledged, resolved
    acknowledged_by UUID,
    acknowledged_at TIMESTAMP,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Rules table (rule engine)
CREATE TABLE rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    device_id UUID REFERENCES devices(id),
    condition JSONB NOT NULL, -- {key: "temperature", operator: ">", value: 50}
    action JSONB NOT NULL, -- {type: "alert", params: {...}}
    enabled BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 50,
    cooldown_seconds INTEGER DEFAULT 300, -- Prevent alert spam
    last_triggered TIMESTAMP,
    trigger_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Dashboards table
CREATE TABLE dashboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    user_id UUID, -- For future multi-user support
    layout JSONB NOT NULL, -- Grid layout configuration
    widgets JSONB NOT NULL, -- Widget definitions
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- API keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash VARCHAR(255) NOT NULL UNIQUE, -- SHA256 hash
    name VARCHAR(255) NOT NULL,
    device_id UUID REFERENCES devices(id),
    permissions JSONB, -- {read: true, write: true, admin: false}
    rate_limit INTEGER DEFAULT 1000, -- Requests per hour
    expires_at TIMESTAMP,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Users table (for future auth)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'viewer', -- admin, engineer, viewer
    permissions JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);
```

### 2.2 Indexes for Performance

```sql
-- Telemetry indexes
CREATE INDEX idx_telemetry_device_time ON telemetry (device_id, timestamp DESC);
CREATE INDEX idx_telemetry_key ON telemetry (key);

-- Devices indexes
CREATE INDEX idx_devices_status ON devices (status);
CREATE INDEX idx_devices_type ON devices (type);
CREATE INDEX idx_devices_area ON devices (area);

-- Alerts indexes
CREATE INDEX idx_alerts_device ON alerts (device_id);
CREATE INDEX idx_alerts_status ON alerts (status);
CREATE INDEX idx_alerts_created ON alerts (created_at DESC);

-- Rules indexes
CREATE INDEX idx_rules_device ON rules (device_id);
CREATE INDEX idx_rules_enabled ON rules (enabled);
```

---

## 3. REST API Specification

### 3.1 Authentication Endpoints

```
POST   /api/v1/auth/login          - User login (JWT token)
POST   /api/v1/auth/refresh        - Refresh JWT token
POST   /api/v1/auth/logout         - Logout
POST   /api/v1/auth/register       - Register new user (admin only)
```

### 3.2 Device Management

```
GET    /api/v1/devices             - List all devices
POST   /api/v1/devices             - Register new device
GET    /api/v1/devices/{id}        - Get device details
PUT    /api/v1/devices/{id}        - Update device
DELETE /api/v1/devices/{id}        - Delete device
GET    /api/v1/devices/{id}/status - Get device status
POST   /api/v1/devices/{id}/config - Update device config
```

### 3.3 Telemetry & Data

```
GET    /api/v1/telemetry           - Query telemetry data
POST   /api/v1/telemetry           - Ingest telemetry (device API)
GET    /api/v1/telemetry/latest    - Get latest values
GET    /api/v1/telemetry/aggregate - Aggregated data (avg, min, max)
```

### 3.4 Alerts & Rules

```
GET    /api/v1/alerts              - List alerts
GET    /api/v1/alerts/{id}         - Get alert details
PUT    /api/v1/alerts/{id}/ack     - Acknowledge alert
PUT    /api/v1/alerts/{id}/resolve - Resolve alert

GET    /api/v1/rules               - List rules
POST   /api/v1/rules               - Create rule
GET    /api/v1/rules/{id}          - Get rule details
PUT    /api/v1/rules/{id}          - Update rule
DELETE /api/v1/rules/{id}          - Delete rule
POST   /api/v1/rules/{id}/test     - Test rule
```

### 3.5 Dashboards

```
GET    /api/v1/dashboards          - List dashboards
POST   /api/v1/dashboards          - Create dashboard
GET    /api/v1/dashboards/{id}     - Get dashboard
PUT    /api/v1/dashboards/{id}     - Update dashboard
DELETE /api/v1/dashboards/{id}     - Delete dashboard
```

### 3.6 Reports (Existing + Enhanced)

```
POST   /api/v1/reports/excel       - Generate Excel report
POST   /api/v1/reports/pdf         - Generate PDF report
POST   /api/v1/reports/zip         - Generate ZIP archive
GET    /api/v1/reports/scheduled   - List scheduled reports
POST   /api/v1/reports/schedule    - Schedule report
```

---

## 4. WebSocket Events (Socket.IO)

### 4.1 Client → Server

```javascript
// Subscribe to device telemetry
socket.emit('subscribe', {
  type: 'device',
  device_id: 'uuid',
  keys: ['temperature', 'humidity']
});

// Unsubscribe
socket.emit('unsubscribe', {
  type: 'device',
  device_id: 'uuid'
});

// Subscribe to alerts
socket.emit('subscribe', {
  type: 'alerts',
  severity: ['warning', 'critical']
});
```

### 4.2 Server → Client

```javascript
// Real-time telemetry
socket.on('telemetry', (data) => {
  // {device_id, timestamp, key, value, unit}
});

// Device status change
socket.on('device_status', (data) => {
  // {device_id, status, timestamp}
});

// New alert
socket.on('alert', (data) => {
  // {id, device_id, severity, message, timestamp}
});

// Alert acknowledged/resolved
socket.on('alert_update', (data) => {
  // {id, status, timestamp}
});
```

---

## 5. Rule Engine Specification

### 5.1 Rule Types

**1. Threshold Rules**
```json
{
  "type": "threshold",
  "condition": {
    "key": "temperature",
    "operator": ">",
    "value": 50,
    "duration_seconds": 300
  },
  "action": {
    "type": "alert",
    "severity": "warning",
    "message": "High temperature detected"
  }
}
```

**2. Comparison Rules**
```json
{
  "type": "comparison",
  "condition": {
    "left": {"device": "device1", "key": "temperature"},
    "operator": ">",
    "right": {"device": "device2", "key": "temperature"}
  },
  "action": {
    "type": "alert",
    "severity": "info"
  }
}
```

**3. Time-based Rules**
```json
{
  "type": "schedule",
  "condition": {
    "schedule": "0 8 * * *", // Cron format
    "action": {
      "type": "report",
      "format": "excel"
    }
  }
}
```

**4. Statistical Rules**
```json
{
  "type": "statistical",
  "condition": {
    "key": "temperature",
    "function": "stddev",
    "window": "1h",
    "operator": ">",
    "value": 5
  },
  "action": {
    "type": "alert",
    "severity": "critical",
    "message": "Temperature instability detected"
  }
}
```

### 5.2 Actions

- **alert** - Create alert in database + WebSocket notification
- **email** - Send email via SMTP
- **webhook** - HTTP POST to external URL
- **mqtt** - Publish MQTT message
- **script** - Execute Python script
- **n8n** - Trigger n8n workflow

---

## 6. MQTT Integration

### 6.1 Topic Structure

```
insa/devices/{device_id}/telemetry/{key}     - Device publishes data
insa/devices/{device_id}/status              - Device status (online/offline)
insa/devices/{device_id}/config              - Platform sends config
insa/devices/{device_id}/command             - Platform sends commands
insa/alerts/{severity}                       - Alert notifications
```

### 6.2 Message Format (JSON)

```json
{
  "timestamp": "2025-10-27T16:30:00Z",
  "device_id": "uuid",
  "telemetry": {
    "temperature": {"value": 25.5, "unit": "C"},
    "humidity": {"value": 65, "unit": "%"}
  },
  "metadata": {
    "quality": 100,
    "source": "sensor-1"
  }
}
```

---

## 7. Security Architecture

### 7.1 Authentication Flow

```
1. User logs in → Receives JWT access token (15 min) + refresh token (7 days)
2. Client includes JWT in Authorization header: "Bearer {token}"
3. API validates JWT signature + expiration
4. Refresh token used to get new access token when expired
```

### 7.2 Device Authentication

```
Option 1: API Key
- Device includes API key in header: "X-API-Key: {key}"
- Key linked to specific device ID
- Rate limiting enforced

Option 2: MQTT Client Certificates
- mTLS authentication
- Device certificate signed by CA
- Automatic device registration
```

### 7.3 Authorization Levels

| Role | Permissions |
|------|-------------|
| **Admin** | Full access to all endpoints, user management |
| **Engineer** | Read/write devices, rules, dashboards. No user management |
| **Operator** | Read devices, acknowledge alerts. No config changes |
| **Viewer** | Read-only access to dashboards and reports |
| **Device** | Write telemetry only for assigned device |

---

## 8. Performance Optimization

### 8.1 Caching Strategy

**Redis Cache:**
- Latest device status (TTL: 60s)
- Latest telemetry values (TTL: 30s)
- Dashboard configurations (TTL: 300s)
- API rate limit counters (TTL: 3600s)

**Database:**
- TimescaleDB continuous aggregates for historical data
- Materialized views for common queries
- Connection pooling (max 20 connections)

### 8.2 Scaling Strategy

**Horizontal Scaling:**
- Stateless Flask app (multiple instances behind load balancer)
- Redis pub/sub for WebSocket message distribution
- Celery workers for background tasks

**Vertical Scaling:**
- Database optimization (indexes, query tuning)
- TimescaleDB compression for old data
- Archive old telemetry to S3/object storage

---

## 9. Monitoring & Observability

### 9.1 Metrics to Track

**System Metrics:**
- API response time (p50, p95, p99)
- WebSocket connection count
- MQTT message rate
- Database query performance
- Cache hit ratio
- Celery task queue length

**Business Metrics:**
- Active devices count
- Telemetry points per second
- Alert rate (by severity)
- Rule execution count
- Report generation count
- Active users count

### 9.2 Integration

- Prometheus metrics endpoint: `/metrics`
- Grafana dashboards for visualization
- Alert integration with existing INSA monitoring

---

## 10. Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer (Nginx)                     │
│                  Port 443 (HTTPS/WSS)                       │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐     ┌─────────┐     ┌─────────┐
   │ Flask   │     │ Flask   │     │ Flask   │
   │ App 1   │     │ App 2   │     │ App 3   │
   │ :5001   │     │ :5002   │     │ :5003   │
   └────┬────┘     └────┬────┘     └────┬────┘
        │               │               │
        └───────┬───────┴───────┬───────┘
                │               │
        ┌───────▼───────┐ ┌─────▼──────┐
        │  PostgreSQL   │ │   Redis    │
        │    :5432      │ │   :6379    │
        └───────────────┘ └────────────┘
                │
        ┌───────▼───────┐
        │   Mosquitto   │
        │  :1883/8883   │
        └───────────────┘
```

---

## 11. Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- ✅ REST API framework
- ✅ Database schema
- ✅ Device management
- ✅ Authentication (JWT)
- ✅ Basic telemetry ingestion

### Phase 2: Real-time Features (Week 3-4)
- ⏳ WebSocket integration (Socket.IO)
- ⏳ Real-time telemetry streaming
- ⏳ Live device status updates
- ⏳ MQTT broker setup

### Phase 3: Advanced Features (Week 5-6)
- ⏳ Rule engine implementation
- ⏳ Alert system
- ⏳ Dashboard builder
- ⏳ Report scheduling

### Phase 4: Polish & Production (Week 7-8)
- ⏳ Performance optimization
- ⏳ Security hardening
- ⏳ Comprehensive testing
- ⏳ Documentation
- ⏳ Production deployment

---

**Next Steps:**
1. Implement Phase 1 features in `app_advanced.py`
2. Set up database schema
3. Create REST API endpoints
4. Add authentication system
5. Test with existing ThingsBoard data

**Status:** 🚧 Ready for implementation
**Estimated Completion:** 6-8 weeks
**Expected Outcome:** Enterprise-grade IIoT platform matching ThingsBoard Pro capabilities
