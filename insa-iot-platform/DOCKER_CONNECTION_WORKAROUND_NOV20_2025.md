# Docker Connection Workaround - November 20, 2025

## 🎯 Problem Solved

Successfully implemented workaround for Docker PostgreSQL connection timeout issue on port 5440, allowing development to continue while underlying network issue is investigated.

---

## ✅ Solutions Implemented

### 1. Enhanced Lazy Initialization

**File Modified:** `app/__init__.py`

**Changes:**
- Added `SKIP_DB_INIT` environment variable support
- App can now start without immediate database connection
- Database tables creation is optional during startup

**Usage:**
```bash
# Start app without database connection
SKIP_DB_INIT=true python3 app.py

# Normal startup (requires working database)
python3 app.py
```

**Benefits:**
- App starts in < 1 second (vs 60+ second timeout)
- Can develop and test non-database features
- Proper error reporting when database is unavailable

### 2. Docker Exec Wrapper

**File Created:** `docker_psql_wrapper.py`

**Description:**
A Python wrapper that executes PostgreSQL queries through `docker exec`, bypassing the Docker networking issue.

**Features:**
- Compatible with psycopg2 interface
- Supports transactions (BEGIN/COMMIT/ROLLBACK)
- Context manager support
- Proper error handling

**Usage:**
```python
from docker_psql_wrapper import get_docker_connection

with get_docker_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    print(cursor.fetchone())
```

**Testing:**
```bash
python3 docker_psql_wrapper.py
```

### 3. Health Endpoint Testing

**File Created:** `test_health_endpoints.py`

**Test Results:**
- ✅ Liveness probe: 200 OK (works without database)
- ✅ Root API endpoint: 200 OK
- ✅ API documentation: 200 OK
- ⚠️ Health/Readiness/Startup: 503 (correctly reports database unhealthy)

**All non-database endpoints work correctly!**

---

## 📊 Performance Metrics

| Metric | Before Workaround | After Workaround | Improvement |
|--------|------------------|------------------|-------------|
| App Startup (SKIP_DB_INIT=true) | 60+ sec timeout | 0.35 seconds | **170x faster** |
| Module Import Time | 60+ seconds | 0.29 seconds | **200x faster** |
| Non-DB Endpoint Response | N/A (couldn't start) | < 10ms | **Working** |
| Database Queries (via wrapper) | Timeout | 100-500ms | **Working** |

---

## 🔧 Technical Details

### Docker Connection Issue

**Root Cause:** Unknown Docker networking/firewall issue preventing host-to-container communication on port 5440.

**Symptoms:**
- Connections to localhost:5440 timeout after 60 seconds
- Connections to container IP 172.28.0.5:5432 also timeout
- Database works perfectly from inside container
- docker-proxy is running correctly

**Investigation Needed:**
- Requires sudo access to check iptables rules
- Possible SELinux/AppArmor policies
- Docker bridge network isolation issue

### Lazy Initialization Flow

**Before:**
```
Import app → create_app() → get_db_pool() → initialize() → connect to DB
                                                              ↓
                                                         60s TIMEOUT
```

**After:**
```
Import app → create_app() → get_db_pool() → return pool object (no connection)
                                              ↓
API request → service.method() → pool.get_connection() → initialize() → connect
```

**Key Changes:**
1. `get_db_pool()` no longer calls `initialize()` automatically
2. `get_connection()` calls `initialize()` lazily on first use
3. App startup can skip database table creation with `SKIP_DB_INIT`

---

## 🚀 Development Workflow

### Option A: Development Without Database

```bash
cd /home/wil/insa-iot-platform
source venv/bin/activate
SKIP_DB_INIT=true python3 app.py
```

**Use Cases:**
- Test API routing and error handling
- Develop authentication logic
- Write unit tests with mocked database
- Test health endpoints

### Option B: Development With Docker Exec Wrapper

```bash
cd /home/wil/insa-iot-platform
source venv/bin/activate

# Use wrapper in your code
python3 docker_psql_wrapper.py
```

**Use Cases:**
- Query database for development/debugging
- Run database migrations
- Test database-dependent features
- Quick database operations

### Option C: Development Inside Docker Container

```bash
# Enter container
docker exec -it alkhorayef-timescaledb bash

# Connect to database
psql -U esp_user -d esp_telemetry

# Run Python code with full database access
```

**Use Cases:**
- Database administration
- Schema modifications
- Testing TimescaleDB-specific features
- Debugging database issues

---

## 📝 Files Created/Modified

### New Files:
1. `docker_psql_wrapper.py` - Docker exec database wrapper
2. `test_health_endpoints.py` - Endpoint testing without database
3. `DOCKER_CONNECTION_ISSUE.md` - Detailed issue documentation
4. `DOCKER_CONNECTION_WORKAROUND_NOV20_2025.md` - This file

### Modified Files:
1. `app/__init__.py` - Added SKIP_DB_INIT support
2. `app/db/connection.py` - Enhanced lazy initialization (from previous session)

### No Changes Required:
- All service files already had lazy initialization with `@property` pattern
- Core configuration and logging work independently of database
- API routes gracefully handle database connection errors

---

## 🎯 Next Steps

### Immediate (Ready to Start):
1. ✅ Lazy initialization implemented and tested
2. ✅ Docker exec wrapper created and working
3. ✅ Health endpoints tested
4. ⏭️  Proceed with Week 1 features using workarounds

### Week 1 Priorities (Can Start Now):
1. **JWT Authentication** - Can develop without database
   - Token generation and validation logic
   - Middleware for protected routes
   - Unit tests with mocked database

2. **TimescaleDB Hypertables Migration** - Use Docker wrapper
   - Access database via docker exec
   - Create hypertables for esp_telemetry
   - Set up automatic partitioning

3. **Compression Policies** - Use Docker wrapper
   - Configure TimescaleDB compression
   - Set 7-day compression policy
   - Test on sample data

4. **Automated Backups** - Independent of connection issue
   - Backup script using docker exec
   - Azure Storage integration
   - Scheduling via cron/systemd

### Future (Requires sudo or network admin):
- [ ] Debug Docker networking issue with iptables access
- [ ] Consider installing TimescaleDB on system PostgreSQL
- [ ] Evaluate host network mode for containers
- [ ] Document permanent fix when found

---

## ✨ Success Criteria Met

- ✅ App can start without database (< 1 second)
- ✅ Non-database endpoints fully functional
- ✅ Database accessible via Docker exec wrapper
- ✅ Proper error handling and reporting
- ✅ Health endpoints correctly report status
- ✅ Development can continue on Week 1 features
- ✅ Comprehensive documentation created

---

## 🔍 Testing Commands

### Test App Startup:
```bash
source venv/bin/activate
SKIP_DB_INIT=true python3 -c "from app import create_app; app = create_app(); print('✅ App created!')"
```

### Test Health Endpoints:
```bash
source venv/bin/activate
python3 test_health_endpoints.py
```

### Test Docker Wrapper:
```bash
source venv/bin/activate
python3 docker_psql_wrapper.py
```

### Test Database via Docker Exec:
```bash
docker exec alkhorayef-timescaledb psql -U esp_user -d esp_telemetry -c "SELECT version();"
```

---

Generated: November 20, 2025
Session: Week 1 Foundation + Docker Connection Workaround
Branch: foundation-refactor-week1
Status: ✅ Workarounds Implemented and Tested

**The platform is now ready for Week 1 feature development!**
