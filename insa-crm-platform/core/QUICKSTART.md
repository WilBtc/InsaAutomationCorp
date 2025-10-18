# INSA CRM System - Quick Start Guide

**Get your AI-powered CRM running in 15 minutes!**

---

## Prerequisites Checklist

Before starting, ensure you have:

- ✅ Ubuntu 24.04 LTS (or iac1 server access)
- ✅ Python 3.11+ installed
- ✅ PostgreSQL 16+ running
- ✅ Redis 7.4+ running
- ✅ ERPNext instance accessible
- ✅ Sudo access (for system packages)

---

## Step-by-Step Installation

### 1. Navigate to Project Directory

```bash
cd ~/insa-crm-system
```

### 2. Set Up Python Virtual Environment

```bash
# Activate virtual environment (already created)
source venv/bin/activate

# Verify Python version
python --version  # Should be 3.11+

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

Expected output: ~50 packages installed in 2-3 minutes

### 3. Create PostgreSQL Database

```bash
# Connect as postgres user
sudo -u postgres psql

# In psql prompt:
CREATE DATABASE insa_crm;
CREATE USER insa_crm_user WITH PASSWORD 'secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE insa_crm TO insa_crm_user;
\c insa_crm
GRANT ALL ON SCHEMA public TO insa_crm_user;
\q
```

### 4. Configure Environment Variables

```bash
# Copy example config
cp .env.example .env

# Edit configuration
nano .env
```

**Minimum required settings:**

```env
DATABASE_URL=postgresql://insa_crm_user:secure_password_here@localhost:5432/insa_crm
REDIS_URL=redis://localhost:6379/0
ERPNEXT_API_URL=http://100.105.64.109:8000/api
ERPNEXT_API_KEY=your_erpnext_api_key
ERPNEXT_API_SECRET=your_erpnext_secret
SECRET_KEY=run_this_command: openssl rand -hex 32
```

**Optional settings (can use defaults):**

```env
QDRANT_HOST=100.107.50.52
INVENTREE_API_URL=http://localhost:8002/api
```

Save and exit (`Ctrl+X`, `Y`, `Enter`)

### 5. Initialize Database Tables

```bash
# Run database initialization
python -c "import asyncio; from api.core.database import init_db; asyncio.run(init_db())"
```

Expected output: `database_tables_created`

Verify tables created:

```bash
psql -U insa_crm_user -d insa_crm -c "\dt"
```

You should see: `agent_executions`, `lead_scores`

### 6. Start the Application

```bash
# Development mode (with auto-reload)
python api/main.py
```

Expected output:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 7. Verify Installation

Open new terminal and run:

```bash
# Health check
curl http://localhost:8000/health

# Expected: {"status":"healthy","service":"insa-crm-system","version":"0.1.0"}

# MCP server status
curl http://localhost:8000/api/v1/mcp/status

# Expected: JSON with initialized MCP servers

# API documentation
xdg-open http://localhost:8000/api/docs
```

You should see interactive Swagger documentation!

---

## Test Drive: Qualify Your First Lead

### Option 1: Via API (using curl)

```bash
# Trigger lead qualification
curl -X POST "http://localhost:8000/api/v1/leads/qualify/LEAD-TEST-001" \
  -H "Content-Type: application/json"

# Response:
# {
#   "status": "processing",
#   "lead_id": "LEAD-TEST-001",
#   "message": "Lead qualification in progress"
# }

# Wait 2-3 seconds, then check results:
curl "http://localhost:8000/api/v1/leads/scores/LEAD-TEST-001"
```

### Option 2: Via API Documentation UI

1. Open http://localhost:8000/api/docs
2. Find **POST /api/v1/leads/qualify/{lead_id}**
3. Click "Try it out"
4. Enter `LEAD-TEST-001` as lead_id
5. Click "Execute"
6. Wait a few seconds
7. Find **GET /api/v1/leads/scores/{lead_id}**
8. Enter same lead_id
9. See qualification results!

### Option 3: Python Script

```bash
# Create test script
cat > test_agent.py << 'EOF'
import asyncio
import httpx

async def test_qualification():
    async with httpx.AsyncClient() as client:
        # Trigger qualification
        response = await client.post(
            "http://localhost:8000/api/v1/leads/qualify/LEAD-TEST-001"
        )
        print("Triggered:", response.json())

        # Wait for processing
        await asyncio.sleep(2)

        # Get results
        response = await client.get(
            "http://localhost:8000/api/v1/leads/scores/LEAD-TEST-001"
        )
        result = response.json()

        print(f"\n🎯 Lead Qualification Results:")
        print(f"   Score: {result['qualification_score']}/100")
        print(f"   Priority: {result['priority']}")
        print(f"   Action: {result['recommended_action']}")
        print(f"\n💡 Reasoning:\n{result['reasoning']}")

asyncio.run(test_qualification())
EOF

# Run test
python test_agent.py
```

---

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'fastapi'"

**Solution:**

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "psycopg2.OperationalError: could not connect to server"

**Solution:**

```bash
# Check PostgreSQL is running
systemctl status postgresql

# Start if needed
sudo systemctl start postgresql

# Verify DATABASE_URL in .env is correct
cat .env | grep DATABASE_URL
```

### Issue: "redis.exceptions.ConnectionError"

**Solution:**

```bash
# Check Redis is running
systemctl status redis

# Start if needed
sudo systemctl start redis

# Verify REDIS_URL in .env
cat .env | grep REDIS_URL
```

### Issue: "ERPNext API connection failed"

**Solution:**

```bash
# Test ERPNext API manually
curl -X GET "http://100.105.64.109:8000/api/resource/Lead" \
  -H "Authorization: token your_key:your_secret"

# If fails, check:
# 1. ERPNext is running
# 2. API credentials are correct in .env
# 3. Network connectivity (ping 100.105.64.109)
```

### Issue: Port 8000 already in use

**Solution:**

```bash
# Find what's using port 8000
sudo lsof -i :8000

# Kill the process or change port
uvicorn api.main:app --port 8001
```

---

## Next Steps

### For Development:

1. **Explore API**: Browse http://localhost:8000/api/docs
2. **View logs**: Watch agent execution in terminal
3. **Test more leads**: Create different scenarios
4. **Modify agent**: Edit `agents/lead_qualification_agent.py`

### For Integration:

1. **Connect to real ERPNext**:
   - Get API credentials from ERPNext
   - Update `.env` file
   - Test with actual leads

2. **Set up ERPNext custom DocTypes**:
   - See `docs/IMPLEMENTATION_ROADMAP.md` Week 5
   - Create Lead Score custom fields
   - Add Automation Requirements DocType

3. **Configure email alerts**:
   - Use existing Postfix on iac1
   - Edit `SMTP_*` settings in `.env`
   - Test with high-priority leads

### For Production:

1. **Follow Phase 1 roadmap**: See `docs/IMPLEMENTATION_ROADMAP.md`
2. **Set up systemd service**: Auto-start on boot
3. **Configure Nginx**: Reverse proxy with SSL
4. **Enable monitoring**: Prometheus metrics at `/metrics`

---

## Useful Commands

```bash
# Start application
cd ~/insa-crm-system
source venv/bin/activate
python api/main.py

# View logs (in separate terminal)
tail -f logs/crm_system.log  # (if logging to file)

# Check database
psql -U insa_crm_user -d insa_crm

# Query agent executions
psql -U insa_crm_user -d insa_crm -c "SELECT * FROM agent_executions ORDER BY started_at DESC LIMIT 5;"

# Query lead scores
psql -U insa_crm_user -d insa_crm -c "SELECT lead_id, qualification_score, priority FROM lead_scores;"

# Run tests (when implemented)
pytest tests/

# Code formatting
black api/ agents/

# Type checking
mypy api/ agents/
```

---

## Getting Help

- **Documentation**: See `README.md`, `docs/ARCHITECTURE.md`
- **Roadmap**: See `docs/IMPLEMENTATION_ROADMAP.md`
- **Issues**: Check logs in terminal output
- **Contact**: w.aroca@insaing.com

---

## Production Deployment

For production deployment, see:

- **Phase 1**: `docs/IMPLEMENTATION_ROADMAP.md` Weeks 5-8
- **Systemd Service**: Create `/etc/systemd/system/insa-crm.service`
- **Nginx Reverse Proxy**: Configure at `/etc/nginx/sites-available/insa-crm`
- **SSL Certificate**: Use Let's Encrypt (`certbot`)
- **Monitoring**: Prometheus + Grafana setup

---

**You're all set!** 🚀

Your INSA CRM System is now running and ready to qualify leads with AI.

**Test the system, explore the API docs, and start building the future of industrial automation CRM!**
