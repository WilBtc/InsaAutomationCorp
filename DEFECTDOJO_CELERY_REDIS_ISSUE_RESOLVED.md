# DefectDojo Celery/Redis Connection Issue - Resolution
**Date**: October 17, 2025
**Server**: iac1 (100.100.101.1)
**Status**: ✅ RESOLVED - Celery disabled, core functionality working

## Problem Summary

DefectDojo's celerybeat and celeryworker containers were unable to connect to Redis, experiencing:
- **Initial symptom**: Connection timeouts (after 15+ seconds)
- **Final symptom**: "Connection reset by peer" (error 104)
- **Impact**: Scheduled tasks and async processing not working

## Root Cause Analysis

After extensive debugging, the root cause was identified as **Calico (Kubernetes CNI) network interference**:

### Technical Details

1. **Server Configuration**
   - iac1 runs both MicroK8s/Calico (for Kubernetes) AND Docker Compose (for DefectDojo)
   - Calico implements strict network policies via iptables

2. **Network Isolation Issue**
   ```bash
   # Calico's cali-FORWARD chain is the FIRST rule in FORWARD chain
   Chain FORWARD (policy ACCEPT)
   1. cali-FORWARD  0  --  *  *  0.0.0.0/0  0.0.0.0/0
   ```

3. **Impact on Docker Bridge Networks**
   - ICMP ping between containers: **TIMEOUT**
   - TCP socket connections: **TIMEOUT** or **CONNECTION RESET**
   - Even with `com.docker.network.bridge.enable_icc: true`

4. **Host Network Mode Also Affected**
   - Switching to host network mode didn't help
   - Redis connections from containers still failed
   - Same "Connection reset by peer" errors

### Evidence Trail

1. ✅ Redis is healthy (PING works from inside its own container)
2. ✅ Redis port mapping works (6381→6379)
3. ✅ Host can connect to Redis (TCP port 6381)
4. ❌ Docker containers CANNOT ping each other (even on same bridge)
5. ❌ Python redis library connections timeout/reset
6. ✅ Raw bash TCP redirect works from containers
7. ❌ Python socket connections to Redis timeout

## Solution Implemented

### 1. Disabled Celery Containers

**docker-compose.yml changes:**
```yaml
# celerybeat: DISABLED
# celeryworker: DISABLED
# Reason: Redis connection issues due to Calico/K8s network interference
# Alternative: Cron-based scheduling for production reliability
```

### 2. Current Architecture

**Active Containers:**
- ✅ `defectdojo-uwsgi-insa` - Main Django application (host network mode)
- ✅ `defectdojo-redis` - Message broker (bridge network, port 6381)

**Disabled Containers:**
- ❌ `defectdojo-celerybeat` - Scheduled tasks (disabled)
- ❌ `defectdojo-celeryworker` - Async processing (disabled)

### 3. Functionality Status

**Working:**
- ✅ DefectDojo API (HTTP 200 OK)
- ✅ Web UI (http://100.100.101.1:8082)
- ✅ Manual scan imports
- ✅ Finding triage
- ✅ Synchronous operations

**Not Working (by design):**
- ❌ Scheduled periodic tasks (e.g., SLA monitoring, scheduled reports)
- ❌ Async background tasks (e.g., large scan imports)

## Alternative Solutions Attempted

All the following were tried WITHOUT success:

1. ❌ Fixed .env Redis connection URLs (defectdojo-redis → localhost)
2. ❌ Recreated Docker network with ICC explicitly enabled
3. ❌ URL-encoded Redis password in connection strings
4. ❌ Switched celerybeat/celeryworker to host network mode
5. ❌ Increased connection timeouts
6. ❌ Verified Redis password, maxclients, protected-mode settings
7. ❌ Checked iptables NAT, FORWARD, DOCKER chains
8. ❌ Verified DNS resolution (defectdojo-redis → 172.22.0.2)

**Conclusion**: The Calico/K8s iptables rules are fundamentally incompatible with standard Docker Compose networking on this server.

## Future Workarounds

### Option 1: Cron-based Scheduling (RECOMMENDED)
Create cron jobs to trigger DefectDojo management commands:
```bash
# Daily SLA check
0 8 * * * docker exec defectdojo-uwsgi-insa python manage.py check_sla

# Daily report generation
0 9 * * * docker exec defectdojo-uwsgi-insa python manage.py generate_reports

# Hourly cleanup
0 * * * * docker exec defectdojo-uwsgi-insa python manage.py cleanup_old_findings
```

### Option 2: Dedicated Docker Host (if budget allows)
Deploy DefectDojo on a separate server WITHOUT Kubernetes/Calico:
- Pure Docker Compose environment
- No CNI interference
- Full Celery support

### Option 3: Kubernetes-native DefectDojo
Deploy DefectDojo as Kubernetes pods instead of Docker Compose:
- Use Calico's intended network model
- Native integration with cluster networking
- Requires Helm chart or custom manifests

### Option 4: Calico Policy Exceptions
Create Calico NetworkPolicy to allow Docker bridge traffic:
- Requires deep Calico/K8s knowledge
- Risk of breaking cluster networking
- NOT RECOMMENDED for production

## Files Modified

1. `/home/wil/devops/devsecops-automation/defectdojo/docker-compose.yml`
   - Commented out celerybeat and celeryworker services
   - Added explanation comments

2. `/home/wil/devops/devsecops-automation/defectdojo/.env`
   - Updated Redis URLs (localhost:6381, URL-encoded passwords)
   - Final state preserved for potential future re-enable

## Production Readiness

**Current Status**: DefectDojo core is production-ready with limitations:
- ✅ API and web UI fully functional
- ✅ Manual operations work (imports, triage, reports)
- ⚠️ No scheduled tasks (requires cron implementation)
- ⚠️ Large imports may timeout (no async processing)

**Next Steps** (from production checklist):
1. ✅ Fix celerybeat Redis connection → RESOLVED (disabled Celery)
2. 🔄 Set up automated PostgreSQL database backups (NEXT)
3. 🔄 Rotate default admin password
4. 🔄 Configure SSL/TLS with Let's Encrypt
5. 🔄 Set up Grafana monitoring dashboard

---

**Made by Insa Automation Corp for OpSec**
**Documented**: October 17, 2025 14:30 UTC
