# n8n Headless Control Solution for Claude Code (2025)
**Date:** October 18, 2025 18:30 UTC
**Server:** iac1 (100.100.101.1)
**Status:** 🎯 PRODUCTION-READY SOLUTION IDENTIFIED

---

## 🎯 Executive Summary

**Problem:** Cannot create n8n workflows programmatically due to API authentication conflicts.

**Root Cause:**
- `N8N_USER_MANAGEMENT_DISABLED=true` + `N8N_BASIC_AUTH_ACTIVE=true`
- Conflicting auth configuration causes API timeouts/401 errors

**Solution:** Install n8n MCP (Model Context Protocol) server for Claude Code
- **Enables full headless workflow control via MCP**
- **No UI required for workflow creation**
- **Production-ready in 2025**
- **Multiple MCP server implementations available**

---

## 🚀 PRODUCTION-READY SOLUTION

### Option 1: n8n-mcp by czlonkowski (RECOMMENDED)
**GitHub:** https://github.com/czlonkowski/n8n-mcp
**Status:** ✅ PRODUCTION READY (536 nodes, 90% docs coverage)

#### Features
- ✅ 536 n8n nodes supported
- ✅ 99% node property coverage
- ✅ 63.6% node operation coverage
- ✅ 90% documentation coverage
- ✅ 263 AI-capable nodes
- ✅ Direct workflow creation from Claude Code
- ✅ Comprehensive validation
- ✅ Docker support (280MB optimized image)

#### Installation

**Method 1: NPX (Fastest - No Installation)**
```bash
npx n8n-mcp
```

**Method 2: Docker (Recommended for Production)**
```bash
docker pull ghcr.io/czlonkowski/n8n-mcp:latest
```

**Method 3: Global NPM Installation**
```bash
npm install -g n8n-mcp
```

#### Configuration for Claude Code

Add to `~/.mcp.json`:
```json
{
  "mcpServers": {
    "n8n-nodes": {
      "command": "npx",
      "args": ["-y", "n8n-mcp"],
      "env": {
        "N8N_HOST": "http://100.100.101.1:5678",
        "N8N_API_KEY": "<your-api-key-here>"
      }
    }
  }
}
```

---

### Option 2: mcp-n8n-server by ahmadsoliman
**GitHub:** https://github.com/ahmadsoliman/mcp-n8n-server
**Status:** ✅ PRODUCTION READY (Workflow + webhook management)

#### Features
- ✅ List all workflows
- ✅ List workflow webhooks
- ✅ Call webhooks via GET/POST
- ✅ Supports self-hosted + cloud n8n
- ✅ API key authentication
- ✅ Simple setup

#### Installation
```bash
npm install -g @ahmad.soliman/mcp-n8n-server
```

#### Configuration for Claude Code

Add to `~/.mcp.json`:
```json
{
  "mcpServers": {
    "n8n": {
      "command": "npx",
      "args": ["-y", "@ahmad.soliman/mcp-n8n-server"],
      "env": {
        "N8N_HOST_URL": "http://100.100.101.1:5678",
        "N8N_API_KEY": "<your-api-key-here>",
        "PROJECT_ID": ""
      }
    }
  }
}
```

---

## 🔑 n8n API Key Setup (REQUIRED)

### Step 1: Enable User Management in n8n

**Current Configuration (BROKEN):**
```yaml
N8N_USER_MANAGEMENT_DISABLED: true
N8N_BASIC_AUTH_ACTIVE: true
```

**Fixed Configuration:**
```yaml
N8N_USER_MANAGEMENT_DISABLED: false  # Enable user management
N8N_BASIC_AUTH_ACTIVE: false  # Disable basic auth
```

**Update docker-compose.yml:**
```yaml
services:
  n8n_mautic_erpnext:
    image: docker.n8n.io/n8nio/n8n:latest
    environment:
      - N8N_HOST=100.100.101.1
      - N8N_PORT=5678
      - N8N_PROTOCOL=http
      - WEBHOOK_URL=http://100.100.101.1:5678/
      - GENERIC_TIMEZONE=UTC
      - N8N_ENCRYPTION_KEY=insa_n8n_encryption_key_2025_secure_random_32chars
      - N8N_USER_MANAGEMENT_DISABLED=false  # CHANGED
      - N8N_BASIC_AUTH_ACTIVE=false  # CHANGED
      - N8N_METRICS=true
      - EXECUTIONS_DATA_SAVE_ON_ERROR=all
      - EXECUTIONS_DATA_SAVE_ON_SUCCESS=all
      - EXECUTIONS_DATA_SAVE_MANUAL_EXECUTIONS=true
      - NODE_OPTIONS=--max_old_space_size=1024
    ports:
      - "5678:5678"
    volumes:
      - n8n_mautic_erpnext_data:/home/node/.n8n
      - /var/run/docker.sock:/var/run/docker.sock:ro
    restart: unless-stopped
```

**Recreate Container:**
```bash
cd /home/wil
docker-compose up -d n8n_mautic_erpnext
# Downtime: ~30 seconds
```

---

### Step 2: Create n8n User Account

1. Access http://100.100.101.1:5678
2. Complete setup wizard (first-time only)
3. Create admin account:
   - Email: `w.aroca@insaing.com`
   - Password: `n8n_admin_2025`
   - First Name: `INSA`
   - Last Name: `Admin`

---

### Step 3: Generate API Key

1. Login to n8n Web UI
2. Go to **Settings** → **n8n API**
3. Click **Create an API key**
4. Configure:
   - **Label:** `Claude Code MCP Server`
   - **Expiration:** Never (or 1 year)
   - **Scopes:** All (full access)
5. **Copy API key** (you won't see it again!)
6. Save to secure location: `~/.n8n_api_key`

```bash
# Save API key securely
echo "your-api-key-here" > ~/.n8n_api_key
chmod 600 ~/.n8n_api_key
```

---

## 📦 Complete Deployment Guide

### Step-by-Step Implementation

#### 1. Fix n8n Configuration (30 minutes)

```bash
# Backup current configuration
docker inspect n8n_mautic_erpnext > /tmp/n8n_config_backup.json

# Stop container
docker stop n8n_mautic_erpnext

# Update docker-compose.yml
cd /home/wil
# Edit docker-compose-n8n.yml (if exists) or create it
# Apply the fixed configuration from above

# Recreate container
docker-compose up -d n8n_mautic_erpnext

# Wait 30 seconds for startup
sleep 30

# Verify it's running
docker ps | grep n8n
curl -I http://100.100.101.1:5678
```

#### 2. Create n8n User & API Key (10 minutes)

```bash
# Open browser
xdg-open http://100.100.101.1:5678

# Follow setup wizard
# Create user: w.aroca@insaing.com / n8n_admin_2025
# Generate API key: Settings → n8n API → Create API key
# Save API key: echo "api-key-here" > ~/.n8n_api_key && chmod 600 ~/.n8n_api_key
```

#### 3. Install n8n MCP Server (5 minutes)

**Option A: Use czlonkowski/n8n-mcp (RECOMMENDED)**

```bash
# Test NPX installation (no installation needed)
npx -y n8n-mcp --help

# Verify it works
npx -y n8n-mcp
```

**Option B: Use ahmadsoliman/mcp-n8n-server**

```bash
# Install globally
npm install -g @ahmad.soliman/mcp-n8n-server

# Verify installation
mcp-n8n-server --version
```

#### 4. Configure MCP Server in Claude Code (5 minutes)

```bash
# Backup current MCP config
cp ~/.mcp.json ~/.mcp.json.backup-before-n8n-mcp

# Read API key
N8N_API_KEY=$(cat ~/.n8n_api_key)

# Add n8n MCP server to config
cat > /tmp/n8n_mcp_config.json <<EOF
{
  "command": "npx",
  "args": ["-y", "n8n-mcp"],
  "env": {
    "N8N_HOST": "http://100.100.101.1:5678",
    "N8N_API_KEY": "$N8N_API_KEY"
  },
  "_description": "n8n MCP Server - Full headless workflow control with 536 nodes, 90% docs coverage. Enables Claude Code to create, manage, and execute n8n workflows programmatically. Production-ready for ERPNext ↔ Mautic integration."
}
EOF

# Merge with existing config (manual step)
# Edit ~/.mcp.json and add the n8n-mcp server entry
```

**Manual Edit of ~/.mcp.json:**
```json
{
  "mcpServers": {
    "azure-vm-monitor": { ... },
    "azure-alert": { ... },
    ... existing servers ...,
    "n8n-mcp": {
      "command": "npx",
      "args": ["-y", "n8n-mcp"],
      "env": {
        "N8N_HOST": "http://100.100.101.1:5678",
        "N8N_API_KEY": "your-api-key-here"
      },
      "_description": "n8n MCP Server - Full headless workflow control"
    }
  }
}
```

#### 5. Test MCP Server (5 minutes)

```bash
# Restart Claude Code to load new MCP server
# (Close and reopen Claude Code)

# In Claude Code, ask:
# "List all n8n workflows using the MCP server"
# "Create a simple test workflow in n8n"
# "Show me available n8n nodes"
```

#### 6. Deploy 5 ERPNext ↔ Mautic Workflows (30 minutes)

Once MCP server is configured, simply ask Claude Code:

**Prompt:**
```
Using the n8n MCP server, create all 5 ERPNext ↔ Mautic integration workflows:

1. New Lead Sync (ERPNext → Mautic) - every 1 hour
2. Lead Scoring Update (Mautic → ERPNext) - every 6 hours
3. Opportunity Conversion (ERPNext → Mautic) - every 30 minutes
4. Event Participation Sync (Mautic → ERPNext) - every 4 hours
5. Unsubscribe Sync (Mautic → ERPNext) - every 2 hours

Use the specifications from ~/PHASE5_N8N_ERPNEXT_MAUTIC_INTEGRATION.md
```

Claude Code will use the MCP server to create workflows directly via API!

---

## 🔍 n8n API Endpoints Reference

### Workflow Management

**Create Workflow:**
```bash
POST https://100.100.101.1:5678/rest/workflows
Headers:
  X-N8N-API-KEY: your-api-key
  Content-Type: application/json
Body:
{
  "name": "Workflow Name",
  "nodes": [...],
  "connections": {...},
  "settings": {},
  "active": false
}
```

**List Workflows:**
```bash
GET https://100.100.101.1:5678/rest/workflows
Headers:
  X-N8N-API-KEY: your-api-key
```

**Get Workflow:**
```bash
GET https://100.100.101.1:5678/rest/workflows/{id}
Headers:
  X-N8N-API-KEY: your-api-key
```

**Update Workflow:**
```bash
PATCH https://100.100.101.1:5678/rest/workflows/{id}
Headers:
  X-N8N-API-KEY: your-api-key
  Content-Type: application/json
Body:
{
  "name": "Updated Name",
  "active": true
}
```

**Delete Workflow:**
```bash
DELETE https://100.100.101.1:5678/rest/workflows/{id}
Headers:
  X-N8N-API-KEY: your-api-key
```

**Activate Workflow:**
```bash
PATCH https://100.100.101.1:5678/rest/workflows/{id}
Body: {"active": true}
```

---

## 📊 Comparison: Before vs After

### Before (Current State)
```yaml
Method: Manual Web UI
Time: 2-3 hours for 5 workflows
Automation: None
Repeatability: Manual process
Error-prone: High (manual JSON editing)
Documentation: Screenshots/text
```

### After (With MCP Server)
```yaml
Method: Claude Code + MCP Server
Time: 5-10 minutes for 5 workflows
Automation: Full (natural language → workflows)
Repeatability: 100% (version controlled prompts)
Error-prone: Low (AI validation + MCP validation)
Documentation: Auto-generated from code
```

---

## ✅ Verification & Testing

### Test 1: MCP Server Connection
```bash
# In Claude Code, ask:
"Using n8n MCP server, list all available n8n nodes"

# Expected: List of 536+ nodes
```

### Test 2: Workflow Creation
```bash
# In Claude Code, ask:
"Using n8n MCP server, create a simple workflow:
- Schedule trigger (every 1 hour)
- HTTP Request to http://httpbin.org/get
- Set node to format response"

# Expected: Workflow created successfully with ID
```

### Test 3: Workflow Verification
```bash
# Check database
docker cp n8n_mautic_erpnext:/home/node/.n8n/database.sqlite /tmp/n8n_verify.sqlite
sqlite3 /tmp/n8n_verify.sqlite "SELECT id, name, active FROM workflow_entity;"

# Expected: New workflow appears in database
```

### Test 4: Workflow Execution
```bash
# In Claude Code, ask:
"Execute workflow ID 1 manually"

# Check n8n UI: Executions tab shows successful run
```

---

## 🛡️ Security Considerations

### API Key Security
```bash
# Store API key securely
echo "your-api-key" > ~/.n8n_api_key
chmod 600 ~/.n8n_api_key

# Reference in MCP config
N8N_API_KEY=$(cat ~/.n8n_api_key)
```

### API Key Rotation
```bash
# Generate new API key quarterly
# Update ~/.mcp.json with new key
# Restart Claude Code
```

### Scopes (Enterprise Only)
- Limit API key to workflow management only
- Prevent credential access
- Audit log all API calls

---

## 📁 Files to Create/Update

```yaml
Configuration:
  ~/.mcp.json: Add n8n-mcp server entry
  ~/.n8n_api_key: Store API key securely (600 permissions)

Docker:
  ~/docker-compose-n8n.yml: Update environment variables

Backup:
  ~/.mcp.json.backup-before-n8n-mcp: Backup before changes

Documentation:
  ~/N8N_HEADLESS_CONTROL_SOLUTION_2025.md: This file
  ~/N8N_MCP_DEPLOYMENT_COMPLETE.md: Deployment report (create after)
```

---

## 🚀 Implementation Timeline

### Phase 1: Fix n8n Configuration (30 min)
- [ ] Update docker-compose.yml
- [ ] Recreate n8n container
- [ ] Verify Web UI accessible
- [ ] Complete setup wizard

### Phase 2: API Key Generation (10 min)
- [ ] Login to n8n Web UI
- [ ] Navigate to Settings → n8n API
- [ ] Create API key with full access
- [ ] Save to ~/.n8n_api_key

### Phase 3: MCP Server Installation (5 min)
- [ ] Test npx n8n-mcp
- [ ] Verify connectivity
- [ ] Update ~/.mcp.json
- [ ] Restart Claude Code

### Phase 4: Validation (5 min)
- [ ] Test MCP server connection
- [ ] List available nodes
- [ ] Create test workflow
- [ ] Verify in database

### Phase 5: Deploy Production Workflows (30 min)
- [ ] Create Workflow 1 (New Lead Sync)
- [ ] Create Workflow 2 (Lead Scoring)
- [ ] Create Workflow 3 (Opportunity Conversion)
- [ ] Create Workflow 4 (Event Participation)
- [ ] Create Workflow 5 (Unsubscribe Sync)
- [ ] Verify all 5 workflows
- [ ] Test execution
- [ ] Activate workflows

**Total Time:** ~1.5 hours (vs 2-3 hours manual)

---

## 🎯 Success Criteria

### Technical
- ✅ n8n API authentication working (X-N8N-API-KEY)
- ✅ MCP server connected to Claude Code
- ✅ All 5 workflows created programmatically
- ✅ Workflows execute successfully
- ✅ ERPNext ↔ Mautic data sync verified

### Business
- ✅ Zero manual workflow creation
- ✅ Repeatable deployment process
- ✅ Version-controlled workflow definitions
- ✅ Audit trail of all changes
- ✅ 50%+ time savings vs manual approach

---

## 📞 Resources

### Documentation
- n8n MCP (czlonkowski): https://github.com/czlonkowski/n8n-mcp
- mcp-n8n-server (ahmadsoliman): https://github.com/ahmadsoliman/mcp-n8n-server
- n8n API Docs: https://docs.n8n.io/api/
- MCP Protocol: https://modelcontextprotocol.io/

### Local Files
- Workflow Specs: ~/PHASE5_N8N_ERPNEXT_MAUTIC_INTEGRATION.md
- Deployment Guide: ~/N8N_WORKFLOWS_DEPLOYMENT_GUIDE.md
- Status Report: ~/N8N_WORKFLOWS_STATUS_REPORT.md
- Python Script: ~/create_n8n_workflows.py (backup method)

### Support
- n8n Community: https://community.n8n.io
- MCP Community: https://github.com/modelcontextprotocol
- INSA DevOps: w.aroca@insaing.com

---

## 🏁 Conclusion

**The n8n MCP Server is the PRODUCTION-READY solution for headless n8n control in 2025.**

### Key Benefits
✅ **Zero UI Required** - Create workflows via Claude Code natural language
✅ **Production Ready** - 536 nodes, 90% docs coverage, battle-tested
✅ **Fast Deployment** - 5-10 minutes vs 2-3 hours manual
✅ **Repeatable** - Version-controlled, auditable, scriptable
✅ **Secure** - API key authentication, scope control (enterprise)

### Next Steps
1. **Fix n8n config** (30 min) - Enable user management, disable basic auth
2. **Generate API key** (10 min) - Settings → n8n API
3. **Install MCP server** (5 min) - npx n8n-mcp
4. **Deploy workflows** (30 min) - Ask Claude Code to create all 5 workflows

**Total Implementation Time:** 1.5 hours
**ROI:** 100% workflow automation + repeatable deployments

---

**Status:** 🎯 PRODUCTION-READY SOLUTION DOCUMENTED
**Priority:** HIGH (core CRM automation)
**Recommendation:** Implement immediately

**Created By:** Claude Code (Anthropic)
**Organization:** INSA Automation Corp
**Date:** October 18, 2025 18:30 UTC
