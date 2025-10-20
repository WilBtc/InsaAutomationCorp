# INSA Command Center - HTTPS Mixed Content Fix
## October 20, 2025 03:35 UTC

### Issue
- Command Center V3 loaded via HTTPS had mixed content error
- Browser blocked HTTP requests to `http://100.100.101.1:5000/health`
- Error: "Blocked loading mixed active content"

### Root Cause
- Page loaded via `https://iac1.tailc58ea3.ts.net/command-center/...`
- Backend API hardcoded to `http://100.100.101.1:5000`
- Modern browsers block HTTP requests from HTTPS pages (security policy)

### Solution (2 changes)

#### 1. Added Tailscale HTTPS Route for Backend API
```bash
sudo tailscale serve --bg --https 443 --set-path /backend http://localhost:5000
```

**Result:**
- Backend now accessible at: `https://iac1.tailc58ea3.ts.net/backend`
- Health check: `https://iac1.tailc58ea3.ts.net/backend/health` ✅

#### 2. Updated Command Center to Use Protocol-Aware API URL
**File:** `~/insa-crm-platform/crm voice/insa-command-center-v3.html:862`

**Before:**
```javascript
const API_BASE = 'http://100.100.101.1:5000';
```

**After:**
```javascript
// Determine API URL based on how page is accessed
let API_BASE;
if (window.location.protocol === 'https:') {
    // HTTPS via Tailscale - use /backend path
    API_BASE = window.location.origin + '/backend';
} else {
    // HTTP local access - use port 5000
    API_BASE = 'http://' + window.location.hostname + ':5000';
}
```

### Results
✅ **HTTPS Access:** https://iac1.tailc58ea3.ts.net/command-center/insa-command-center-v3.html
✅ **Backend API:** https://iac1.tailc58ea3.ts.net/backend/health
✅ **No Mixed Content:** All requests use HTTPS when page loaded via HTTPS
✅ **Backward Compatible:** HTTP access still works for local development

### Updated Tailscale Routes (17 total)
```
https://iac1.tailc58ea3.ts.net/
|-- / → http://127.0.0.1:8007 (Command Center home)
|-- /api → http://localhost:8005/api (Auth API)
|-- /backend → http://localhost:5000 (CRM Voice Backend) ⭐ NEW
|-- /command-center → http://127.0.0.1:8007 (Command Center V3)
|-- /n8n → http://localhost:5678
|-- /crm → http://localhost:8003
|-- /code → http://127.0.0.1:8080
|-- /mautic → http://localhost:9700
|-- /erpnext → http://localhost:9000
|-- /manager → http://127.0.0.1:8002
|-- /grafana → http://localhost:3002
|-- /iec62443 → http://localhost:3004
|-- /keycloak → http://127.0.0.1:8090
|-- /admin-api → http://127.0.0.1:8001
|-- /inventree → http://localhost:9600
|-- /defectdojo → http://localhost:8082
```

### Authentication Status
✅ **Login Fixed:** https://iac1.tailc58ea3.ts.net/command-center/login.html
- **Email:** w.aroca@insaing.com
- **Password:** Insa2025

### Testing
```bash
# Test HTTPS health check
curl -k https://iac1.tailc58ea3.ts.net/backend/health

# Expected response:
{
    "status": "ok",
    "whisper_model": "base",
    "device": "cpu",
    "claude_path": "claude"
}
```

### Related Documentation
- **Login Fix:** See previous session (Tailscale route for `/api`)
- **Command Center V3:** `~/insa-crm-platform/crm voice/insa-command-center-v3.html`
- **Backend API:** `~/insa-crm-platform/crm voice/crm-backend.py`
- **Main Guide:** `~/.claude/CLAUDE.md` (update section on Command Center)

---
**Status:** ✅ PRODUCTION READY
**Impact:** Full HTTPS support for Command Center + 8 AI Agents
**Security:** All traffic encrypted via Tailscale VPN + HTTPS
