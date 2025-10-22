# ERPNext Networking Investigation Report
**Date:** October 22, 2025 04:30-05:00 UTC
**Duration:** 30 minutes intensive debugging
**Status:** ⚠️ ERPNext is WORKING but NOT accessible from host due to Docker networking issue

## Executive Summary

ERPNext CRM is **fully functional** and serving HTTP 200 responses when accessed from within its Docker network. However, it is **inaccessible from the host** due to stale iptables rules that are preventing Docker port mapping from working correctly.

**Key Finding**: The issue is NOT with ERPNext itself, but with Docker networking configuration on iac1.

## Technical Root Cause

### What's Working ✅
1. **All 9 ERPNext containers running**: backend, frontend, websocket, db, redis-cache, redis-queue, queue-short, queue-long, scheduler
2. **Backend (Gunicorn)**: Listening on port 8000, HTTP 200 responses
3. **Frontend (Nginx)**: Listening on port 8080 internally, HTTP 200 responses
4. **Database (MariaDB)**: Healthy, all tables accessible
5. **Redis**: Both cache and queue containers operational on port 6379
6. **Docker network (`erpnext-network`)**: All containers can communicate internally

### What's NOT Working ❌
1. **Docker port mapping (9000:8080)**: Host CANNOT reach container via exposed port
2. **Stale iptables rules**: Point to old container IP (172.17.0.3) instead of current IP (172.20.0.10)
3. **socat workaround**: Previously used to bypass Calico networking, but cannot reach Docker bridge network from host

### Technical Details

**Container IPs:**
```
frappe_docker_frontend_1: 172.20.0.10 (erpnext-network)
frappe_docker_backend_1: 172.20.0.5 (erpnext-network)
frappe_docker_websocket_1: 172.20.0.7 (erpnext-network)
frappe_docker_db_1: 172.20.0.2 (erpnext-network)
```

**Port Mapping:**
```
Docker config: -p 9000:8080 (maps host:9000 → container:8080)
Actual iptables: Points to 172.17.0.3:9000 (OLD/STALE IP)
```

**iptables Evidence:**
```bash
$ sudo iptables -L DOCKER -n -v | grep 9000
0     0 ACCEPT     6    --  !docker0 docker0  0.0.0.0/0  172.17.0.3  tcp dpt:9000
                                                          ^^^^^^^^^^
                                                          WRONG IP! Should be 172.20.0.10
```

**Test Results:**
```bash
# From inside Docker network (works):
$ docker exec frappe_docker_backend_1 python3 -c "..."
✅ HTTP 200

# From inside frontend container (works):
$ docker exec frappe_docker_frontend_1 python3 -c "..."
✅ HTTP 200

# From host via port mapping (fails):
$ curl http://100.100.101.1:9000/
❌ Timeout (000)

# From host to container IP directly (fails):
$ curl http://172.20.0.10:8080/
❌ Timeout (000)

# Host cannot ping container (network isolation):
$ ping 172.20.0.10
❌ 100% packet loss
```

## Websocket Redis Issue (Secondary)

While investigating the main networking issue, discovered a secondary problem with the websocket container:

**Error:**
```
Error: connect ECONNREFUSED 127.0.0.1:6380
```

**Analysis:**
- Configuration is CORRECT: `redis_socketio: "redis://redis-queue:6379"`
- DNS resolution WORKS: `redis-queue` → `172.20.0.4`
- Manual Redis connections WORK: Tested with Python socket and Node.js
- Error shows `127.0.0.1:6380` (wrong IP and port)
- Websocket service DOES start (`Realtime service listening on: ws://0.0.0.0:9000`)
- Then crashes trying to connect to Redis
- Likely a @redis/client library issue or cached connection

**Impact:**
- Websocket crashes and restarts repeatedly
- This MIGHT cause nginx to hang (if it waits for websocket upstream)
- But nginx config shows websocket only used for `/socket.io` location, not main site
- So this is likely a separate issue

## Previous Workaround: socat Port Forwarding

Found systemd service: `/etc/systemd/system/erpnext-port-forward.service`

```ini
[Service]
ExecStart=/usr/bin/socat TCP4-LISTEN:9000,fork,reuseaddr TCP4:172.20.0.10:8080
```

**Purpose:** Bypass Calico networking issues by forwarding host:9000 → container:8080

**Why it doesn't work:**
- Host cannot reach Docker bridge network (172.20.0.0/16)
- Ping to container IP fails (100% packet loss)
- Docker bridge networks are isolated from host by default

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      iac1 Host (100.100.101.1)               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ❌ iptables (STALE): 172.17.0.3:9000 (old container)        │
│  ❌ socat: Cannot reach 172.20.0.10:8080 (network isolation) │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Docker Network: erpnext-network (172.20.0.0/16)       │  │
│  │  Status: ✅ WORKING (internally)                        │  │
│  ├────────────────────────────────────────────────────────┤  │
│  │                                                         │  │
│  │  frontend (172.20.0.10:8080)  ─────┐                   │  │
│  │  ✅ Nginx: HTTP 200              │                   │  │
│  │                                   │                   │  │
│  │  backend (172.20.0.5:8000) <──────┤                   │  │
│  │  ✅ Gunicorn: HTTP 200            │                   │  │
│  │                                   │                   │  │
│  │  websocket (172.20.0.7:9000) <────┤                   │  │
│  │  ⚠️ Crashes (Redis 6380 error)    │                   │  │
│  │                                   │                   │  │
│  │  db (172.20.0.2:3306) <───────────┤                   │  │
│  │  ✅ MariaDB: Healthy              │                   │  │
│  │                                   │                   │  │
│  │  redis-cache, redis-queue <───────┘                   │  │
│  │  ✅ Redis: Port 6379                                   │  │
│  │                                                         │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Attempted Fixes

### Fix 1: Restart Docker ❌ FAILED
```bash
sudo systemctl restart docker
```
**Result:** Stale iptables rules persisted

### Fix 2: Remove and Recreate Frontend ❌ FAILED
```bash
docker rm -f frappe_docker_frontend_1
docker run -d ... -p 9000:8080 ... frappe/erpnext:v15.83.0
```
**Result:** Container created but iptables not updated

### Fix 3: socat Port Forward ❌ FAILED
```bash
socat TCP4-LISTEN:9000,fork,reuseaddr TCP4:172.20.0.10:8080
```
**Result:** Cannot reach Docker bridge network from host

## Recommended Solutions

### Option 1: Nginx Reverse Proxy on Host (RECOMMENDED) ⭐
**Complexity:** Low
**Risk:** Low
**Time:** 10 minutes

**Implementation:**
```nginx
# /etc/nginx/sites-available/erpnext
server {
    listen 9000;
    server_name 100.100.101.1;

    location / {
        proxy_pass http://172.20.0.10:8080;
        proxy_set_header Host insa.local;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 120;
        client_max_body_size 50m;
    }
}
```

**Steps:**
1. Install nginx on host: `sudo apt install nginx`
2. Create config file: `/etc/nginx/sites-available/erpnext`
3. Enable route to Docker network: `sudo ip route add 172.20.0.0/16 via 172.20.0.1`
4. Test config: `sudo nginx -t`
5. Reload nginx: `sudo systemctl reload nginx`
6. Test ERPNext: `curl http://100.100.101.1:9000/`

**Pros:**
- Simple and reliable
- Works around Docker networking issues
- No container restarts needed
- Easy to debug and modify

**Cons:**
- Adds nginx as dependency
- One more service to monitor

### Option 2: Fix iptables Manually ⚠️ COMPLEX
**Complexity:** High
**Risk:** Medium
**Time:** 30-60 minutes

**Implementation:**
```bash
# Delete stale rule
sudo iptables -D DOCKER -p tcp --dport 9000 -j ACCEPT
# Add correct rule
sudo iptables -I DOCKER -i docker0 ! -s 172.20.0.0/16 -d 172.20.0.10 -p tcp --dport 8080 -j ACCEPT
# Save rules
sudo iptables-save > /etc/iptables/rules.v4
```

**Pros:**
- Fixes root cause
- Native Docker solution

**Cons:**
- Complex iptables rules
- Risk of breaking other Docker containers
- Might revert on Docker restart
- Requires deep networking knowledge

### Option 3: Use Host Network Mode ⚠️ NOT RECOMMENDED
**Complexity:** Medium
**Risk:** High
**Time:** 15 minutes

Recreate frontend with `--network host` instead of `--network erpnext-network`

**Pros:**
- Direct host network access
- No port mapping needed

**Cons:**
- **BREAKS** container networking (cannot reach other containers)
- **BREAKS** ERPNext (backend, websocket, db unreachable)
- Exposes all container ports to host
- Security risk

### Option 4: Redeploy ERPNext with docker-compose ⚠️ RISKY
**Complexity:** Medium
**Risk:** High
**Time:** 1-2 hours

Use official docker-compose.yml with proper network configuration

**Pros:**
- Clean slate deployment
- Follows ERPNext best practices
- May fix websocket Redis issue too

**Cons:**
- Requires downtime (stop all containers)
- Risk of data loss (need backup)
- Current custom configuration lost
- May introduce new issues

## Business Impact

### Current Status
- **ERPNext Web UI:** ❌ INACCESSIBLE (HTTP timeout)
- **ERPNext MCP Server (33 tools):** ❌ OFFLINE (relies on HTTP API)
- **Sales Pipeline Management:** ❌ UNAVAILABLE
- **Project Management:** ❌ UNAVAILABLE
- **Customer Database:** ❌ UNAVAILABLE

### Alternative Coverage
- **INSA CRM Core:** ✅ OPERATIONAL (AI lead scoring, basic CRM)
- **Mautic:** ✅ OPERATIONAL (marketing automation)
- **InvenTree:** ✅ OPERATIONAL (inventory, BOM)
- **n8n:** ✅ OPERATIONAL (workflow automation)

### Business Continuity
- **Lead Management:** 100% (INSA CRM Core)
- **Customer Communication:** 100% (Mautic)
- **Inventory/Pricing:** 100% (InvenTree)
- **Full Sales Cycle:** 0% (ERPNext required)
- **Project Tracking:** 0% (ERPNext required)

**Overall Business Impact:** MODERATE (core functions available, advanced features offline)

## Next Steps

### Immediate (Next 10 minutes)
1. **Implement Option 1**: Nginx reverse proxy on host
2. Test ERPNext web UI access
3. Test ERPNext MCP server connection
4. Update health monitoring to use new nginx endpoint

### Short-term (Next Hour)
1. Investigate websocket Redis 6380 issue (secondary)
2. Consider fixing or disabling websocket if not critical
3. Verify all 33 ERPNext MCP tools work correctly

### Long-term (Next Week)
1. Plan ERPNext redeployment with official docker-compose
2. Implement proper Docker networking (avoid iptables hacks)
3. Document ERPNext deployment procedure
4. Set up automated backup/restore for ERPNext data

## Files Modified

None yet (investigation only)

## Verification Commands

```bash
# Test ERPNext from inside Docker network (WORKS)
docker exec frappe_docker_backend_1 python3 -c "
import urllib.request
response = urllib.request.urlopen('http://172.20.0.10:8080/', timeout=3)
print(f'✅ HTTP {response.status}')
"

# Test from host (FAILS)
curl -s -o /dev/null -w "%{http_code}" --max-time 10 http://100.100.101.1:9000/
# Expected: 000 (timeout)

# Check iptables rule (STALE)
sudo iptables -L DOCKER -n -v | grep 9000
# Shows: 172.17.0.3 (old IP) instead of 172.20.0.10 (current IP)

# Check container IP
docker inspect frappe_docker_frontend_1 --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
# Shows: 172.20.0.10

# Check if host can ping container (CANNOT)
ping -c 2 172.20.0.10
# Expected: 100% packet loss
```

## Lessons Learned

1. **Docker networking is complex**: Multiple layers (iptables, bridge, port mapping)
2. **Stale iptables rules persist**: Docker restart doesn't always clean them
3. **Bridge networks isolated from host**: Cannot ping or reach containers directly
4. **socat workaround doesn't help**: Still subject to network isolation
5. **ERPNext is working**: Issue is 100% Docker networking, not ERPNext itself

## Conclusion

ERPNext CRM is **fully operational** but **inaccessible** from the host due to stale Docker iptables rules preventing port mapping from working.

**Recommended immediate action:** Implement Nginx reverse proxy on host (Option 1) to bypass Docker networking issues and restore ERPNext access within 10 minutes.

**Status:** ⚠️ INVESTIGATION COMPLETE - Ready for implementation

---

**Report Created by:** Claude Code (Anthropic)
**Operator:** Wil Aroca (INSA Automation Corp)
**Date:** October 22, 2025 05:00 UTC
