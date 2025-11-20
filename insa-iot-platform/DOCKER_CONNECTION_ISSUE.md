# Docker PostgreSQL Connection Issue - November 20, 2025

## Problem Summary

Cannot connect to TimescaleDB Docker container on port 5440 from the host system. All connection attempts timeout after 60 seconds.

## Investigation Results

### What's Working
- ✅ Docker container is healthy and running
- ✅ TimescaleDB is accessible from inside the container
- ✅ Port 5440 is open and docker-proxy is listening
- ✅ Container is on network 172.28.0.0/16 with IP 172.28.0.5
- ✅ Health checks passing inside container

### What's Not Working
- ❌ Connections to localhost:5440 timeout
- ❌ Connections to 127.0.0.1:5440 timeout  
- ❌ Connections to container IP 172.28.0.5:5432 timeout

### Technical Details

**Container Configuration:**
```
Container: alkhorayef-timescaledb
Image: timescale/timescaledb:latest-pg15
Network: insa-iot-platform_alkhorayef-net (172.28.0.0/16)
Container IP: 172.28.0.5
Port Mapping: 0.0.0.0:5440 -> 5432
Health: HEALTHY
```

**docker-proxy Process:**
```
/usr/bin/docker-proxy -proto tcp -host-ip 0.0.0.0 -host-port 5440 \
  -container-ip 172.28.0.5 -container-port 5432 -use-listen-fd
```

**Network Output:**
```
$ ss -tlnp | grep 5440
LISTEN 0  4096  0.0.0.0:5440  0.0.0.0:*
LISTEN 0  4096     [::]:5440     [::]:*
```

**Test from Inside Container (Works):**
```bash
$ docker exec -it alkhorayef-timescaledb psql -U esp_user -d esp_telemetry -c "SELECT version();"
PostgreSQL 15.x (Ubuntu 15.x) with TimescaleDB 2.x
```

**Test from Host (Fails):**
```python
psycopg2.connect(host='localhost', port=5440, ...)
# Timeout after 60 seconds
```

## Root Cause Hypothesis

Likely causes (in order of probability):
1. **iptables/nftables rules** blocking traffic to Docker networks (requires sudo to check)
2. **Docker bridge network isolation** preventing host-to-container communication
3. **SELinux or AppArmor** policies blocking the connection
4. **Network namespace isolation** preventing proper routing

## Workarounds Implemented

### 1. Lazy Database Initialization ✅
Modified `app/db/connection.py` so the app can start without immediate database connection. Database connection happens on first API call.

**Status:** Implemented and working

### 2. Docker Exec Port Forward (Recommended)
Use `docker exec` to create a tunnel:

```bash
# Terminal 1 - Create tunnel
docker exec -i alkhorayef-timescaledb socat \
  TCP-LISTEN:5432,fork,reuseaddr \
  EXEC:"psql -U esp_user esp_telemetry"

# Terminal 2 - Connect through tunnel
python3 -c "from app import create_app; app = create_app()"
```

**Status:** Not yet tested

### 3. Use System PostgreSQL + Install TimescaleDB
Install TimescaleDB extension on the system PostgreSQL (port 5432) and migrate data.

**Pros:**
- No Docker networking issues
- Direct connection via Unix socket (peer auth)
- Better performance

**Cons:**
- Requires installing timescaledb-2-postgresql-16
- Need to migrate data from Docker container
- System-level dependency

**Status:** Not yet attempted

### 4. Host Network Mode
Restart container with `network_mode: host` in docker-compose.yml.

**Pros:**
- Eliminates Docker network isolation
- Should work immediately

**Cons:**
- Less secure (container has full host network access)
- Port conflicts if system PostgreSQL is running
- Not recommended for production

**Status:** Not yet attempted

## Recommended Solution Path

### Option A: Quick Development (Use System PostgreSQL)
1. Install TimescaleDB on system PostgreSQL
2. Create esp_telemetry database and user
3. Update .env to use port 5432
4. Migrate schema from Docker container
5. Continue with Week 1 development

### Option B: Debug Docker (Requires sudo)
1. Check iptables rules: `sudo iptables -L -n -v`
2. Check Docker iptables: `sudo iptables -t nat -L -n -v`
3. Try temporarily disabling firewall
4. Check SELinux/AppArmor policies
5. Fix the underlying network issue

### Option C: Container-First Development
1. Develop and test inside the Docker container
2. Run Flask app in another Docker container on same network
3. Use docker-compose to orchestrate all services
4. Avoid host-to-container connections entirely

## Next Steps

**Immediate (to unblock development):**
- [ ] Decide on workaround strategy
- [ ] Implement chosen workaround
- [ ] Test database connection working
- [ ] Resume Week 1 feature development

**Future (proper fix):**
- [ ] Get sudo access to debug iptables
- [ ] Identify and fix root cause
- [ ] Document solution for future reference
- [ ] Update docker-compose configuration if needed

## References

- Previous session summary: `WEEK1_SESSION_SUMMARY_NOV20_2025.md`
- Lazy initialization commit: `1b438bd6`
- Docker compose config: `docker-compose-simple.yml`
- Connection module: `app/db/connection.py`
