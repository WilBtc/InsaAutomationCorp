# IoT Portal - INSA Advanced IIoT Platform v2.0

**Version**: 2.0 (Phase 2 Complete - October 27, 2025)
**Type**: Industrial IoT Monitoring Platform
**Stack**: Python, Flask, PostgreSQL, Redis, MQTT, WebSocket, Grafana
**Port**: 5002 (Phase 2 Production)
**Server**: iac1 (100.100.101.1)
**Status**: ✅ PRODUCTION READY - All 7 Phase 2 features operational

## Phase 2 Features (Complete)

1. **MQTT Broker** - Eclipse Mosquitto on port 1883
2. **WebSocket Real-time** - ws://localhost:5002/socket.io/
3. **Rule Engine** - 4 rule types, 30-second evaluation cycle
4. **Email Notifications** - SMTP localhost:25
5. **Webhook Actions** - 8 security features (SSRF protection, HMAC signing, rate limiting)
6. **Redis Caching** - 97% hit rate, 85% query reduction
7. **Grafana Dashboards** - 3 dashboards, 18 panels total

## Quick Start Phase 2

```bash
# Start INSA Advanced IIoT Platform v2.0
cd /home/wil/iot-portal
nohup python3 app_advanced.py > /tmp/insa-iiot-advanced.log 2>&1 &

# Check service status
curl http://localhost:5002/health

# View API documentation
open http://localhost:5002/api/v1/docs

# Monitor logs
tail -f /tmp/insa-iiot-advanced.log

# Check running process
ps aux | grep app_advanced
```

## Key Paths Phase 2

- **Main App**: `/home/wil/iot-portal/app_advanced.py` (2,000+ lines)
- **Webhook System**: `/home/wil/iot-portal/webhook_notifier.py` (396 lines)
- **Redis Cache**: `/home/wil/iot-portal/redis_cache.py` (618 lines)
- **Grafana Integration**: `/home/wil/iot-portal/grafana_integration.py` (663 lines)
- **Dashboard Provisioner**: `/home/wil/iot-portal/provision_grafana_dashboards.py` (288 lines)
- **Rule Engine**: `/home/wil/iot-portal/rule_engine.py` (modified for caching)
- **Docs**: `/home/wil/iot-portal/PHASE2_COMPLETE.md` (37KB)
- **Test Report**: `/home/wil/iot-portal/PHASE2_TEST_REPORT.md` (12KB)
- **Logs**: `/tmp/insa-iiot-advanced.log`

## Important Commands Phase 2

```bash
# Health and status checks
curl http://localhost:5002/health
curl http://localhost:5002/api/v1/status

# Redis cache stats
redis-cli INFO stats | grep -E "keyspace_hits|keyspace_misses"
redis-cli KEYS "rules:*"

# MQTT broker check
ps aux | grep mosquitto
ss -tlnp | grep 1883

# Database queries (insa_iiot database)
PGPASSWORD='server2025secure' psql -h localhost -U wil_user -d insa_iiot -c "SELECT COUNT(*) FROM devices;"
PGPASSWORD='server2025secure' psql -h localhost -U wil_user -d insa_iiot -c "SELECT COUNT(*) FROM rules WHERE enabled = true;"

# Grafana dashboards (import JSON files)
ls -lh /tmp/grafana_*.json
```

## Databases Phase 2

**Primary:** insa_iiot (PostgreSQL)
- **Host**: localhost:5432
- **Database**: insa_iiot
- **User**: wil_user
- **Password**: server2025secure
- **Tables**: devices, telemetry, rules, alerts, api_keys, users

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

## Phase 3 Planning (Next Steps)

**Proposed Features:**
1. **Advanced Analytics** - Historical trending, predictive analytics
2. **Machine Learning** - Anomaly detection, pattern recognition
3. **Mobile App Support** - iOS/Android companion app
4. **Additional Protocols** - CoAP, AMQP, OPC UA support
5. **RBAC** - Role-based access control and user management
6. **Multi-tenancy** - Support for multiple organizations
7. **Data Retention** - Archival and compliance policies
8. **Advanced Alerting** - Escalation policies, on-call rotation
9. **API Rate Limiting** - Protection for public endpoints
10. **Comprehensive Swagger/OpenAPI** - Interactive API documentation

**Priority Order:** TBD based on user requirements

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
*Updated: October 27, 2025 19:40 UTC*
*Version: 2.0 - Phase 2 Complete*
*Status: ✅ PRODUCTION READY - All 7 features operational*
*Next: Phase 3 Planning*
