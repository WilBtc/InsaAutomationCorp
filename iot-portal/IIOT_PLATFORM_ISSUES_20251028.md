# INSA IIoT Platform - Issue Report
**Generated**: October 28, 2025 16:35 UTC
**Platform**: INSA IIoT Platform v2.0
**Server**: iac1 (100.100.101.1)
**Scanned**: Last 24 hours of system logs
**Total Errors**: 8,794 errors detected

---

## 🚨 CRITICAL ISSUES (Priority 1)

### Issue #1: insa-iiot-advanced Service Restart Loop
**Status**: ACTIVE - Service failing continuously
**Impact**: HIGH - Core IIoT service unavailable via systemd
**Root Cause**: Port 5002 conflict

**Details**:
- Systemd service: `insa-iiot-advanced.service`
- Service status: `activating (auto-restart)` with exit code 1
- Port 5002 already occupied by manual process (PID 2248702)
- Manual process is working correctly (health endpoint responds)

**Evidence**:
```bash
# Service status
Active: activating (auto-restart) (Result: exit-code)
Process: 222877 ExitCode=status=1/FAILURE

# Port usage
LISTEN 0 50 0.0.0.0:5002 users:(("python3",pid=2248702,fd=8))

# Health check (manual process)
curl localhost:5002/health
{"database":"ok","status":"healthy","timestamp":"2025-10-28T16:30:21.222668","version":"2.0"}
```

**Recommended Fix**:
1. Option A: Stop manual process (kill 2248702), let systemd service manage it
2. Option B: Disable systemd service, rely on manual process management
3. Option C: Change systemd service to use different port (e.g., 5003)

**Files Involved**:
- `/home/wil/iot-portal/app_advanced.py` (application)
- `/etc/systemd/system/insa-iiot-advanced.service` (systemd unit)
- Manual process command line (need to identify startup method)

---

### Issue #2: Integrated Healing System KeyError: 'url'
**Status**: RECURRING - Multiple failures per hour
**Impact**: HIGH - Healing system cannot check PostgreSQL/MariaDB services
**Root Cause**: Missing 'url' key in service_config for database services

**Details**:
- Component: `integrated_healing_system.py`
- Error: `KeyError: 'url'` when accessing `service_config['url']`
- Affected services: PostgreSQL, MariaDB (database services don't have HTTP URLs)
- Frequency: 50+ occurrences in last 24 hours

**Evidence**:
```python
# Error from logs
KeyError: 'url'
  File "integrated_healing_system.py", line XXX
    url = service_config['url']
```

**Recommended Fix**:
1. Add conditional check: `if 'url' in service_config`
2. Use different health check method for database services (e.g., connection test)
3. Update service_config schema to mark 'url' as optional

**Files Involved**:
- `/home/wil/insa-crm-platform/core/agents/integrated_healing_system.py`
- Service configuration files (need to identify location)

---

### Issue #3: PostgreSQL/MariaDB Sudo Privilege Errors
**Status**: RECURRING - Blocking healing system checks
**Impact**: MEDIUM - Cannot restart database services automatically
**Root Cause**: "no new privileges" flag prevents sudo elevation

**Details**:
- Error: "sudo: The "no new privileges" flag is set, which prevents sudo from running as root."
- Affected: PostgreSQL and MariaDB healing checks
- Frequency: 30+ occurrences in last 24 hours
- Related to: SystemD security settings (NoNewPrivileges=true)

**Evidence**:
```
sudo: The "no new privileges" flag is set, which prevents sudo from running as root.
sudo: If sudo is running in a container, you may need to adjust the container configuration to disable the flag.
```

**Recommended Fix**:
1. Remove NoNewPrivileges=true from systemd service files
2. Use systemctl without sudo (if service runs as correct user)
3. Add CAP_SYS_ADMIN capability to service
4. Use alternative restart method (e.g., Docker restart for containerized DBs)

**Files Involved**:
- `/etc/systemd/system/integrated-healing-system.service` (or similar)
- Database service unit files

---

## ⚠️ MODERATE ISSUES (Priority 2)

### Issue #4: Network Dispatcher Unknown Interface Errors
**Status**: RECURRING - Multiple per hour
**Impact**: MEDIUM - Network event handling may be degraded
**Root Cause**: Unknown - interface index mismatches

**Details**:
- Component: `networkd-dispatcher`
- Error: "Unknown interface index X for Y event on interface Z"
- Frequency: 100+ occurrences in last 24 hours

**Recommended Fix**:
1. Restart networkd-dispatcher service
2. Check for stale network interfaces
3. Update network configuration
4. Consider disabling networkd-dispatcher if not needed

---

### Issue #5: ERPNext Unknown Service Type
**Status**: RECURRING - Healing system confusion
**Impact**: MEDIUM - Cannot heal ERPNext service automatically
**Root Cause**: Service type "docker_exec" not recognized

**Details**:
- Component: Integrated healing system
- Error: "Unknown service type: docker_exec"
- Service: ERPNext headless CRM
- Context: ERPNext uses Docker exec instead of HTTP (headless mode)

**Recommended Fix**:
1. Add "docker_exec" as valid service type to healing system
2. Implement healing logic for Docker exec services
3. Update service configuration to use recognized type

**Files Involved**:
- `/home/wil/insa-crm-platform/core/agents/integrated_healing_system.py`
- ERPNext service configuration

---

### Issue #6: Prometheus Client Missing Histogram Quantile
**Status**: RECURRING - Metrics collection errors
**Impact**: LOW - Non-critical metric calculation issues
**Root Cause**: prometheus_client library issue

**Details**:
- Error: AttributeError related to histogram quantile calculations
- Frequency: 10+ occurrences in last 24 hours
- May be version compatibility issue

**Recommended Fix**:
1. Update prometheus_client library: `pip install --upgrade prometheus-client`
2. Check for deprecated API usage
3. Consider alternative metric calculation method

---

## 📊 ERROR STATISTICS

**Total Errors**: 8,794
- Error level: 7,281 (82.8%)
- Traceback: 1,502 (17.1%)
- Critical: 8 (0.09%)
- Service failed: 3 (0.03%)

**Top Error Sources**:
1. Integrated healing system: ~5,000 errors (56.8%)
2. Network dispatcher: ~2,000 errors (22.7%)
3. SystemD services: ~1,000 errors (11.4%)
4. Other: ~794 errors (9.0%)

---

## 🎯 RECOMMENDED ACTION PLAN

### Phase 1: Immediate Fixes (Critical)
1. ✅ Fix insa-iiot-advanced port conflict (Issue #1)
2. ✅ Fix integrated healing KeyError (Issue #2)
3. ✅ Fix PostgreSQL/MariaDB sudo errors (Issue #3)

### Phase 2: System Improvements (Moderate)
4. Fix network dispatcher errors (Issue #4)
5. Add docker_exec support to healing system (Issue #5)
6. Update prometheus_client library (Issue #6)

### Phase 3: Monitoring
7. Verify all fixes with 24-hour monitoring period
8. Update healing system patterns based on fixes
9. Document changes in CLAUDE.md

---

## 📁 FILES TO MODIFY

**Priority 1 (Critical)**:
- `/home/wil/iot-portal/app_advanced.py` or systemd service config
- `/home/wil/insa-crm-platform/core/agents/integrated_healing_system.py`
- SystemD unit files with NoNewPrivileges settings

**Priority 2 (Moderate)**:
- ERPNext service configuration
- networkd-dispatcher configuration
- Python requirements.txt (prometheus_client)

---

## 🔍 ADDITIONAL NOTES

**Working Systems** (verified):
- ✅ Database connectivity: PostgreSQL insa_iiot database accessible
- ✅ Health endpoint: localhost:5002/health responds correctly
- ✅ Manual IIoT application: Running and functional on port 5002
- ✅ Bug hunter system: Successfully scanned and categorized errors

**Questions for Investigation**:
1. How was the manual process on port 5002 started? (startup script? cron? manual?)
2. Should systemd manage the IIoT application or manual process?
3. What is the correct 'url' field for database services in healing system?
4. Is networkd-dispatcher needed for this server configuration?

---

**Generated by**: Claude Code + bug-hunter MCP
**Next Step**: Trigger autonomous task orchestrator to process these issues
**Reference**: `/home/wil/autonomous-task-orchestrator/`

🤖 Made by INSA Automation Corp for OpSec Excellence
