# INSA Advanced IIoT Platform - Phase 2 Implementation Plan

**Version:** 2.0
**Date:** October 27, 2025
**Status:** In Progress (25% Complete)

---

## 📋 Phase 2 Overview

Phase 2 transforms the INSA IIoT Platform from a basic REST API into a fully real-time, automated industrial IoT solution with event-driven architecture, intelligent alerting, and multi-channel notifications.

### Goals
1. **Real-time Communication** - WebSocket updates for live dashboards
2. **Intelligent Automation** - Rule engine for automated alerts and actions
3. **Multi-channel Notifications** - Email and Webhook integrations
4. **Performance Optimization** - Redis caching for high-throughput scenarios
5. **Monitoring Integration** - Grafana dashboard connectivity

---

## 🎯 Feature Roadmap

### ✅ Feature 1: MQTT Broker Integration (COMPLETE)
**Status:** ✅ Complete
**Completion Date:** October 27, 2025

- Eclipse Mosquitto 2.0.18 installed
- 4 MQTT topics configured
- Automatic telemetry ingestion
- Command delivery to devices
- Database integration working

---

### ⏳ Feature 2: WebSocket Real-time Updates
**Status:** Pending
**Priority:** HIGH
**Estimated Time:** 3-4 hours

#### Architecture
```
Flask-SocketIO Server
    ↓
WebSocket Connections (clients)
    ↓
Real-time Events:
  - telemetry_update
  - device_status_change
  - alert_triggered
  - alert_acknowledged
```

#### Implementation Tasks
1. Install Flask-SocketIO and dependencies
2. Create WebSocket event handlers
3. Add SocketIO initialization to app
4. Implement real-time event emitters:
   - On telemetry ingestion (HTTP + MQTT)
   - On device status change
   - On alert creation/update
5. Create connection management (rooms per device)
6. Add authentication for WebSocket connections

#### API Events
```python
# Client → Server
'connect'
'authenticate' - JWT token validation
'subscribe_device' - Subscribe to device updates
'unsubscribe_device'

# Server → Client
'telemetry_update' - New telemetry data
'device_status' - Device online/offline
'alert' - New alert triggered
'alert_update' - Alert acknowledged/resolved
```

#### Testing Plan
- Connect WebSocket client
- Publish MQTT telemetry → verify real-time event
- Trigger alert → verify instant notification
- Multiple concurrent clients

---

### ⏳ Feature 3: Rule Engine
**Status:** Pending
**Priority:** HIGH
**Estimated Time:** 4-5 hours

#### Architecture
```
Rule Evaluation Engine (background thread)
    ↓
Check Rules Every 30 Seconds
    ↓
Query Latest Telemetry
    ↓
Evaluate Conditions
    ↓
Trigger Actions (Alert, Email, Webhook)
```

#### Rule Types

**1. Threshold Rules**
```json
{
  "type": "threshold",
  "condition": {
    "key": "temperature",
    "operator": ">",  // >, <, >=, <=, ==, !=
    "value": 50,
    "duration": 300  // Sustained for 5 minutes
  },
  "action": {
    "type": "alert",
    "severity": "warning",
    "message": "Temperature exceeded 50°C"
  }
}
```

**2. Comparison Rules**
```json
{
  "type": "comparison",
  "condition": {
    "key1": "temperature",
    "operator": ">",
    "key2": "setpoint"
  },
  "action": {...}
}
```

**3. Time-based Rules**
```json
{
  "type": "time_based",
  "condition": {
    "schedule": "0 8 * * *",  // Cron expression
    "check": "device_offline"
  },
  "action": {...}
}
```

**4. Statistical Rules**
```json
{
  "type": "statistical",
  "condition": {
    "key": "temperature",
    "function": "avg",  // avg, max, min, stddev
    "window": 3600,     // 1 hour
    "operator": ">",
    "value": 45
  },
  "action": {...}
}
```

#### Implementation Tasks
1. Create rules table in database (already exists)
2. Create rule_engine.py module
3. Implement rule evaluator for each type
4. Create background scheduler (APScheduler)
5. Add rule evaluation logic
6. Implement action executors:
   - Create alert
   - Send email
   - Call webhook
7. Add rule state tracking (prevent duplicate alerts)

#### API Endpoints
```
POST   /api/v1/rules          - Create rule
GET    /api/v1/rules          - List rules
GET    /api/v1/rules/:id      - Get rule details
PUT    /api/v1/rules/:id      - Update rule
DELETE /api/v1/rules/:id      - Delete rule
POST   /api/v1/rules/:id/test - Test rule evaluation
```

---

### ⏳ Feature 4: Email Notification System
**Status:** Pending
**Priority:** MEDIUM
**Estimated Time:** 2-3 hours

#### Architecture
```
SMTP Configuration
    ↓
Email Template Engine (Jinja2)
    ↓
Async Email Queue (background thread)
    ↓
Send via SMTP (TLS/SSL)
```

#### Implementation Tasks
1. Install email dependencies (smtplib built-in, jinja2)
2. Create email_notifier.py module
3. Add SMTP configuration (localhost:25 already configured)
4. Create email templates:
   - Alert notification
   - Daily report
   - Device offline
5. Implement async email queue
6. Add email action to rule engine

#### Email Templates
- `templates/email/alert.html` - Alert notification
- `templates/email/report.html` - Daily summary
- `templates/email/device_offline.html` - Device offline notice

#### Configuration
```python
EMAIL_CONFIG = {
    'smtp_host': 'localhost',
    'smtp_port': 25,
    'from_address': 'noreply@insa-iiot.local',
    'recipient': 'w.aroca@insaing.com'
}
```

---

### ⏳ Feature 5: Webhook Action System
**Status:** Pending
**Priority:** MEDIUM
**Estimated Time:** 2 hours

#### Architecture
```
Webhook Event
    ↓
HTTP POST with JSON payload
    ↓
Retry Logic (3 attempts)
    ↓
Log success/failure
```

#### Implementation Tasks
1. Create webhook_notifier.py module
2. Implement webhook caller with retry logic
3. Add webhook logging (success/failure)
4. Add webhook action to rule engine
5. Add webhook testing endpoint

#### Webhook Payload
```json
{
  "event_type": "alert",
  "timestamp": "2025-10-27T17:00:00Z",
  "device_id": "uuid",
  "device_name": "Temperature Sensor 01",
  "alert": {
    "severity": "critical",
    "message": "Temperature exceeded threshold",
    "value": 55.2,
    "threshold": 50
  }
}
```

---

### ⏳ Feature 6: Performance Optimization (Redis)
**Status:** Pending
**Priority:** LOW
**Estimated Time:** 2 hours

#### Architecture
```
Redis Cache
    ↓
Cache Keys:
  - device:{id}:latest_telemetry (TTL: 60s)
  - device:{id}:status (TTL: 300s)
  - rules:active (TTL: 60s)
```

#### Implementation Tasks
1. Install Redis and python redis library
2. Create redis_cache.py module
3. Add caching layer for:
   - Latest telemetry queries
   - Device status
   - Active rules list
4. Implement cache invalidation on updates

#### Cache Strategy
- Cache latest telemetry (60s TTL)
- Cache device status (5min TTL)
- Cache rules list (60s TTL)
- Invalidate on write operations

---

### ⏳ Feature 7: Grafana Integration
**Status:** Pending
**Priority:** LOW
**Estimated Time:** 1-2 hours

#### Implementation Tasks
1. Add Prometheus metrics endpoint
2. Expose metrics:
   - Device count (online/offline/total)
   - Telemetry ingestion rate
   - Alert count by severity
   - API request rate
   - MQTT message rate
3. Document Grafana dashboard setup

---

## 📊 Phase 2 Progress Tracker

| Feature | Status | Progress | Priority |
|---------|--------|----------|----------|
| MQTT Broker | ✅ Complete | 100% | HIGH |
| WebSocket Updates | ⏳ Pending | 0% | HIGH |
| Rule Engine | ⏳ Pending | 0% | HIGH |
| Email Notifications | ⏳ Pending | 0% | MEDIUM |
| Webhook Actions | ⏳ Pending | 0% | MEDIUM |
| Redis Caching | ⏳ Pending | 0% | LOW |
| Grafana Integration | ⏳ Pending | 0% | LOW |

**Overall Phase 2 Progress: 14% (1/7 features)**

---

## 🎯 Implementation Order

### Priority 1 (Core Functionality)
1. ✅ MQTT Broker - COMPLETE
2. WebSocket Real-time Updates - Next
3. Rule Engine (all 4 types)

### Priority 2 (Automation & Notifications)
4. Email Notification System
5. Webhook Action System

### Priority 3 (Performance & Monitoring)
6. Redis Caching
7. Grafana Integration

---

## 📁 New Files to Create

```
iot-portal/
├── socketio_server.py          # WebSocket server (150+ lines)
├── rule_engine.py               # Rule evaluation engine (400+ lines)
├── email_notifier.py            # Email notification system (150+ lines)
├── webhook_notifier.py          # Webhook caller (100+ lines)
├── redis_cache.py               # Redis caching layer (100+ lines)
├── templates/
│   └── email/
│       ├── alert.html
│       ├── report.html
│       └── device_offline.html
└── PHASE2_COMPLETE.md          # Final documentation
```

---

## 🧪 Testing Strategy

### Unit Tests
- Rule evaluation logic for each type
- Email template rendering
- Webhook retry logic
- Cache hit/miss scenarios

### Integration Tests
- End-to-end real-time flow: MQTT → WebSocket
- Rule trigger → Email → Alert
- Multiple concurrent WebSocket clients
- Cache performance under load

### Performance Tests
- 100 concurrent WebSocket connections
- 1000 telemetry points/second
- Rule evaluation at scale (100+ rules)

---

## 📈 Success Criteria

- [ ] WebSocket clients receive real-time updates <100ms latency
- [ ] Rule engine evaluates all rules within 30 seconds
- [ ] Email notifications delivered within 60 seconds
- [ ] Webhooks called with 3x retry on failure
- [ ] Redis cache reduces DB queries by 50%+
- [ ] System handles 10,000 telemetry points/minute
- [ ] Zero message loss during normal operation
- [ ] Complete API documentation for all new endpoints

---

## 🚀 Deployment Checklist

- [ ] All dependencies installed (Flask-SocketIO, APScheduler, Redis, Jinja2)
- [ ] Database schema updated (no changes needed)
- [ ] Service restarted with new features
- [ ] Email SMTP tested
- [ ] Grafana dashboard imported
- [ ] Documentation updated
- [ ] Git commit with comprehensive changelog
- [ ] Performance benchmarks documented

---

**Next Step:** Implement WebSocket real-time updates with Flask-SocketIO
