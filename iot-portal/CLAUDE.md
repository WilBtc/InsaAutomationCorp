# IoT Portal - INSA Advanced IIoT Platform v2.0

**Version**: 2.0 (Phase 3 In Progress - October 28, 2025)
**Type**: Industrial IoT Monitoring Platform
**Stack**: Python, Flask, PostgreSQL, Redis, MQTT, WebSocket, Grafana
**Port**: 5002 (Production)
**Server**: iac1 (100.100.101.1)
**Status**: ✅ PRODUCTION READY - Phase 2 complete + 4 Phase 3 features operational (40%)

## Phase 2 Features (Complete ✅)

1. **MQTT Broker** - Eclipse Mosquitto on port 1883
2. **WebSocket Real-time** - ws://localhost:5002/socket.io/
3. **Rule Engine** - 4 rule types, 30-second evaluation cycle
4. **Email Notifications** - SMTP localhost:25
5. **Webhook Actions** - 8 security features (SSRF protection, HMAC signing, rate limiting)
6. **Redis Caching** - 97% hit rate, 85% query reduction
7. **Grafana Dashboards** - 3 dashboards, 18 panels total

## Phase 3 Features (In Progress)

**Completed Features (4/10):**

1. ✅ **Feature 9: API Rate Limiting** - Flask-limiter with memory backend
   - 5/min login protection, variable limits per endpoint
   - HTTP 429 responses, brute force protection

2. ✅ **Feature 10: Swagger/OpenAPI Documentation** - Interactive API docs
   - Flasgger integration at /api/v1/docs
   - Complete endpoint documentation with examples

3. ✅ **Feature 5: RBAC (Role-Based Access Control)** - Complete security system
   - 4 roles: admin, developer, operator, viewer
   - 11 API endpoints (user/role management, audit logs)
   - Permission-based authorization with @require_permission decorator
   - Complete audit trail (audit_logs table)
   - 100% test pass rate (8/8 integration tests)
   - Docs: PHASE3_FEATURE5_RBAC_COMPLETE.md + PHASE3_FEATURE5_TEST_REPORT.md

4. ✅ **Feature 1: Advanced Analytics** - Complete time-series analysis system (100%)
   - 5/5 sub-features complete (794 lines of code)
   - Feature 1a: Time-series analysis (moving avg, rate of change)
   - Feature 1b: Trend detection (slope, R², classification)
   - Feature 1c: Statistical functions (mean, median, percentiles, CV, IQR)
   - Feature 1d: Correlation analysis (Pearson coefficient, Cohen's strength)
   - Feature 1e: Simple forecasting (linear regression, confidence intervals)
   - 5 API endpoints, 100% test coverage
   - Docs: PHASE3_FEATURE1_PROGRESS.md + PHASE3_FEATURE1_REVIEW.md

**In Progress:**

None currently

**Pending (6 features):**

5. **Feature 2**: Machine Learning - Anomaly Detection
6. **Feature 3**: Mobile App Support
7. **Feature 4**: Additional Protocols (CoAP, AMQP, OPC UA)
8. **Feature 6**: Multi-tenancy
9. **Feature 7**: Data Retention Policies
10. **Feature 8**: Advanced Alerting (Escalation policies)

## Quick Start

```bash
# Start INSA Advanced IIoT Platform v2.0
cd /home/wil/iot-portal
nohup python3 app_advanced.py > /tmp/insa-iiot-advanced.log 2>&1 &

# Check service status
curl http://localhost:5002/health

# View API documentation (Swagger)
open http://localhost:5002/api/v1/docs

# Test RBAC authentication
curl -X POST http://localhost:5002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@insa.com","password":"Admin123!"}'

# Monitor logs
tail -f /tmp/insa-iiot-advanced.log

# Check running process
ps aux | grep app_advanced

# Run RBAC integration tests
python3 test_rbac_integration.py
```

## Key Paths

**Application Files:**
- **Main App**: `/home/wil/iot-portal/app_advanced.py` (2,800+ lines with RBAC)
- **Webhook System**: `/home/wil/iot-portal/webhook_notifier.py` (396 lines)
- **Redis Cache**: `/home/wil/iot-portal/redis_cache.py` (618 lines)
- **Grafana Integration**: `/home/wil/iot-portal/grafana_integration.py` (663 lines)
- **Dashboard Provisioner**: `/home/wil/iot-portal/provision_grafana_dashboards.py` (288 lines)
- **Rule Engine**: `/home/wil/iot-portal/rule_engine.py` (modified for caching)
- **Rate Limiter**: `/home/wil/iot-portal/rate_limiter.py` (Flask-limiter config)

**Testing:**
- **RBAC Integration Tests**: `/home/wil/iot-portal/test_rbac_integration.py` (220 lines)

**Documentation:**
- **Phase 2 Complete**: `/home/wil/iot-portal/PHASE2_COMPLETE.md` (37KB)
- **Phase 2 Tests**: `/home/wil/iot-portal/PHASE2_TEST_REPORT.md` (12KB)
- **Phase 3 Plan**: `/home/wil/iot-portal/PHASE3_IMPLEMENTATION_PLAN.md`
- **RBAC Implementation**: `/home/wil/iot-portal/PHASE3_FEATURE5_RBAC_COMPLETE.md` (565 lines)
- **RBAC Test Report**: `/home/wil/iot-portal/PHASE3_FEATURE5_TEST_REPORT.md` (NEW)

**Logs:**
- **Application**: `/tmp/insa-iiot-advanced.log`

## Important Commands

```bash
# Health and status checks
curl http://localhost:5002/health
curl http://localhost:5002/api/v1/status

# RBAC - Test authentication
curl -X POST http://localhost:5002/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@insa.com","password":"Admin123!"}'

# RBAC - List users (requires JWT token)
curl http://localhost:5002/api/v1/users \
  -H "Authorization: Bearer {your_token}"

# RBAC - Get audit logs
curl "http://localhost:5002/api/v1/audit/logs?limit=10" \
  -H "Authorization: Bearer {your_token}"

# Redis cache stats
redis-cli INFO stats | grep -E "keyspace_hits|keyspace_misses"
redis-cli KEYS "rules:*"

# MQTT broker check
ps aux | grep mosquitto
ss -tlnp | grep 1883

# Database queries (insa_iiot database)
psql -h localhost -U iiot_user -d insa_iiot -c "SELECT COUNT(*) FROM devices;"
psql -h localhost -U iiot_user -d insa_iiot -c "SELECT COUNT(*) FROM rules WHERE enabled = true;"
psql -h localhost -U iiot_user -d insa_iiot -c "SELECT COUNT(*) FROM users;"
psql -h localhost -U iiot_user -d insa_iiot -c "SELECT name, description FROM roles;"

# Grafana dashboards (import JSON files)
ls -lh /tmp/grafana_*.json
```

## Databases

**Primary:** insa_iiot (PostgreSQL)
- **Host**: localhost:5432
- **Database**: insa_iiot
- **User**: iiot_user
- **Password**: iiot_secure_2025
- **Tables**:
  - Phase 2: devices, telemetry, rules, alerts, api_keys
  - Phase 3: users, roles, user_roles, audit_logs (RBAC)

**Cache:** Redis
- **Host**: localhost:6379
- **Database**: 0
- **Memory**: ~1MB
- **Hit Rate**: 97%+

## Protected Operations ❌
- Changing database credentials without updating configs
- `DROP TABLE` on production database
- Modifying webhook security settings (SSRF protection)
- Disabling Redis caching (performance impact)
- Changing MQTT broker configuration
- Manual git pushes (use SSH key from user account)

## Full Documentation Phase 2

**Implementation Docs:**
- `PHASE2_COMPLETE.md` - Complete technical documentation (37KB, 977 lines)
- `PHASE2_TEST_REPORT.md` - Testing and verification report (12KB, 489 lines)
- `PHASE2_IMPLEMENTATION_PLAN.md` - Original implementation plan (9.7KB)

**Code Structure:**
- `app_advanced.py` - Main application (60KB, 2000+ lines)
- `webhook_notifier.py` - Secure webhook system (13KB, 396 lines)
- `redis_cache.py` - Performance caching layer (33KB, 618 lines)
- `grafana_integration.py` - Dashboard provisioning (33KB, 663 lines)
- `provision_grafana_dashboards.py` - Setup automation (8.3KB, 288 lines)
- `rule_engine.py` - Rule evaluation engine (modified for Redis)

**Performance Metrics:**
- API Response: 45ms avg (55% better than target)
- Rule Evaluation: 120ms (76% better than target)
- Cache Hit Rate: 97% (7% better than target)
- Memory Usage: 124MB (76% under target)
- Uptime: 24+ minutes continuous, zero crashes

## Phase 3 Progress (4/10 Complete - 40%)

**✅ Completed Features:**
1. ✅ **API Rate Limiting** (Feature 9) - Flask-limiter, 5/min login protection
2. ✅ **Swagger/OpenAPI** (Feature 10) - Flasgger at /api/v1/docs
3. ✅ **RBAC** (Feature 5) - 4 roles, 11 endpoints, audit logging, 100% tests passing
4. ✅ **Advanced Analytics** (Feature 1) - 5/5 sub-features, 794 lines, 5 endpoints, 100% tests

**🔄 In Progress:**
None currently - Ready for Feature 2 (Machine Learning)

**📋 Remaining Features:**
5. **Machine Learning** (Feature 2) - Anomaly detection, pattern recognition
6. **Mobile App Support** (Feature 3) - iOS/Android companion app
7. **Additional Protocols** (Feature 4) - CoAP, AMQP, OPC UA support
8. **Multi-tenancy** (Feature 6) - Multiple organizations
9. **Data Retention** (Feature 7) - Archival and compliance policies
10. **Advanced Alerting** (Feature 8) - Escalation policies, on-call rotation

**Implementation Order:** B (Security) → C (Intelligence) → A (Quick Wins)
- ✅ Features 9, 10 (A - Quick Wins)
- ✅ Feature 5 (B - Security Foundation)
- 🔄 Feature 1 (C - AI Intelligence)

## Related Services

**Production (iac1 - 100.100.101.1):**
- INSA Advanced IIoT Platform v2.0 @ localhost:5002 ✅ ACTIVE
- Grafana Analytics @ 100.100.101.1:3002
- MQTT Broker @ localhost:1883 (Eclipse Mosquitto)
- Redis Cache @ localhost:6379
- PostgreSQL @ localhost:5432 (insa_iiot database)

**Legacy (LU1 - 100.81.103.99):**
- ThingsBoard @ 100.105.64.109:7777 (data source)
- Old IoT Portal @ Port 5000 (retired)

## Git Repository

**Local Commits:**
- c4f6f651 - Phase 2 Complete (October 27, 2025)
- c9469629 - Grafana Dashboard Integration
- bf36e883 - Secure Webhook System
- 898691ff - Email Notifications
- 51059db1 - Rule Engine Complete

**GitHub:** `WilBtc/InsaAutomationCorp` (requires SSH key for push)

---
*Updated: October 28, 2025 01:45 UTC*
*Version: 2.0 - Phase 3 In Progress (4/10 features complete - 40%)*
*Status: ✅ PRODUCTION READY - Phase 2 (7) + Phase 3 Analytics complete*
*Current: Ready for Feature 2 (Machine Learning - Anomaly Detection)*
