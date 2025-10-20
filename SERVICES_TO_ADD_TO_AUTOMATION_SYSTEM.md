# Services & Processes to Add to Automation System
**Date:** October 20, 2025 18:45 UTC
**Server:** iac1 (100.100.101.1)
**Current Systems:** Auto-Deployment ✅ + Auto-Git ✅

---

## 🎯 Current Automation Coverage

### ✅ Already Automated (Oct 20, 2025)
1. **Port Assignment** - auto_deploy_service (MANDATORY)
2. **Service Deployment** - Docker/systemd/process (MANDATORY)
3. **Git Commits** - auto_git_commit (MANDATORY)

### 🔍 Analysis Methodology

I analyzed:
- 62 listening ports (from previous audit)
- 21 Docker containers (from previous audit)
- Current git status (many uncommitted files)
- systemd services on iac1
- Autonomous agents already running
- Documentation and backup processes

---

## 📋 Services & Processes to Automate

### 🔴 CRITICAL PRIORITY (Add Immediately)

#### 1. **Automatic Documentation Updates** ⭐ HIGH VALUE
**Why:** We have 100+ .md files that need to be kept in sync

**Current Problem:**
- `.claude/CLAUDE.md` manually updated
- `README.md` files scattered everywhere
- Status docs often outdated
- Version numbers not synchronized

**Proposed Solution:**
```javascript
// New MCP Tool: auto_update_docs
auto_update_docs({
  files: ["CLAUDE.md", "README.md"],
  sync_version: true,        // Update version numbers
  sync_status: true,         // Update status sections
  sync_timestamps: true      // Update "Last Updated" fields
})
```

**Features:**
- Detect documentation files needing updates
- AI-generate changelog entries
- Sync version numbers across all docs
- Update "Last Updated" timestamps
- Validate markdown syntax
- Check for broken links

**Files to Track:**
- `~/.claude/CLAUDE.md` (7.2 → 7.3 when git automation added)
- `~/host-config-agent/README.md`
- `~/insa-crm-platform/README.md`
- All `*/COMPLETE.md` status reports
- All `*/QUICK_REFERENCE.md` files

#### 2. **Automatic Service Health Monitoring** ⭐ HIGH VALUE
**Why:** We have 8 production services that need constant monitoring

**Current State:**
- Platform Admin MCP exists but only does health checks
- No automatic restart on failure
- No automatic issue creation
- No automatic root cause analysis

**Proposed Solution:**
```javascript
// New MCP Tool: auto_monitor_service
auto_monitor_service({
  service: "erpnext",
  auto_restart: true,         // Restart if unhealthy
  auto_diagnose: true,        // Run diagnostics
  auto_fix: true,            // Apply known fixes
  escalate_after: 3          // Escalate after 3 failures
})
```

**Services to Monitor:**
- INSA Command Center V3 (3 processes)
- INSA CRM Core API (port 8003)
- ERPNext (port 9000)
- InvenTree (port 9600)
- Mautic (port 9700)
- n8n (port 5678)
- DefectDojo (port 8082)
- Grafana (port 3002)

**Features:**
- Every 5 min health check (already exists in platform-admin)
- **NEW:** Auto-restart on failure (with max 3 attempts)
- **NEW:** Auto-diagnosis (check logs, resources, dependencies)
- **NEW:** Auto-fix known issues (from learning database)
- **NEW:** Create GitHub issue if can't fix
- **NEW:** Slack/email notification on escalation

#### 3. **Automatic Backup Orchestration** ⭐ HIGH VALUE
**Why:** Currently backups are manual or script-based, no orchestration

**Current Problem:**
- PostgreSQL backup script exists but not integrated
- No backup verification
- No automatic restore testing
- No backup rotation
- Backups not tracked in database

**Proposed Solution:**
```javascript
// New MCP Tool: auto_backup
auto_backup({
  targets: ["postgresql", "sqlite", "docker-volumes"],
  schedule: "daily",           // or "hourly", "weekly"
  verify: true,               // Verify backup integrity
  test_restore: true,         // Test restore monthly
  rotate: "30d",              // Keep 30 days
  remote_copy: true           // Copy to Azure VM
})
```

**Targets to Backup:**
1. **PostgreSQL Databases:**
   - insa_crm (Lead scoring, Communication)
   - erpnext (Full sales cycle)
   - defectdojo (Security findings)

2. **SQLite Databases:**
   - `/var/lib/host-config-agent/host_config.db` ⭐ NEW
   - `/var/lib/defectdojo/learning.db`
   - `/var/lib/insa-crm/learning.db`

3. **Docker Volumes:**
   - InvenTree data
   - Mautic data
   - n8n workflows
   - Grafana dashboards

4. **Configuration Files:**
   - `~/.claude/CLAUDE.md`
   - `~/.mcp.json`
   - All `docker-compose.yml` files
   - All systemd service files

**Features:**
- Automatic daily backups (3 AM UTC)
- Verify backup integrity (checksum validation)
- Test restore monthly (automated restore test)
- Rotate old backups (keep 30 days)
- Remote copy to Azure VM via Tailscale
- Track in database (backup_history table)
- Slack notification on success/failure

---

### 🟠 HIGH PRIORITY (Add Within 1 Week)

#### 4. **Automatic MCP Server Deployment**
**Why:** We have 12 MCP servers, deploying new ones is manual

**Current Problem:**
- Creating new MCP server requires multiple manual steps
- No template system
- No automatic registration in `.mcp.json`
- No automatic service file creation

**Proposed Solution:**
```javascript
// New MCP Tool: auto_deploy_mcp_server
auto_deploy_mcp_server({
  name: "new-service-mcp",
  type: "stdio",              // or "sse"
  template: "python-fastmcp", // or "nodejs-sdk"
  tools: [
    { name: "tool1", description: "..." }
  ],
  auto_register: true,        // Add to .mcp.json
  auto_service: true          // Create systemd service
})
```

**Features:**
- Generate MCP server from template
- Auto-register in `.mcp.json`
- Create systemd service file (optional)
- Auto-start service
- Validate tools work
- Auto-commit to git

#### 5. **Automatic Log Rotation & Analysis**
**Why:** Logs growing unbounded, no automatic analysis

**Current Problem:**
- Log files in `/tmp/` never rotated
- No automatic error detection
- No automatic alert on critical errors
- Logs not analyzed for patterns

**Proposed Solution:**
```javascript
// New MCP Tool: auto_manage_logs
auto_manage_logs({
  log_files: [
    "/tmp/insa-crm.log",
    "/tmp/crm-backend.log",
    "~/azure_agent.log"
  ],
  rotate: "100MB",            // Rotate at 100MB
  compress: true,             // gzip old logs
  keep: "30d",               // Keep 30 days
  analyze: true,             // AI analysis for errors
  alert_on: ["ERROR", "CRITICAL", "FATAL"]
})
```

**Logs to Manage:**
- `/tmp/insa-crm.log` (CRM API logs)
- `/tmp/crm-backend.log` (Voice backend)
- `/tmp/insa-crm-auth-api.log` (Auth API)
- `~/azure_agent.log` (Azure monitor)
- `~/defectdojo_remediation_agent.log`
- All `~/insa-crm-platform/crm voice/*.log` files

**Features:**
- Rotate at size or time interval
- Compress old logs (gzip)
- Delete logs older than retention
- AI analysis for error patterns
- Alert on critical errors
- Weekly summary report

#### 6. **Automatic Database Maintenance**
**Why:** Databases need regular maintenance (vacuum, analyze, backup)

**Current Problem:**
- PostgreSQL never vacuumed
- SQLite never optimized
- No automatic index analysis
- No slow query detection

**Proposed Solution:**
```javascript
// New MCP Tool: auto_maintain_database
auto_maintain_database({
  database: "postgresql://insa_crm",
  vacuum: "weekly",           // VACUUM ANALYZE
  optimize: "daily",          // Optimize indexes
  analyze_slow: true,         // Detect slow queries
  auto_index: true           // Suggest new indexes
})
```

**Databases to Maintain:**
- PostgreSQL: insa_crm, erpnext, defectdojo
- SQLite: host_config.db, learning.db (2x)
- MariaDB: mautic

**Features:**
- Weekly VACUUM ANALYZE (PostgreSQL)
- Daily OPTIMIZE TABLE (MariaDB)
- Daily VACUUM (SQLite)
- Analyze slow queries (> 1 second)
- Suggest new indexes based on query patterns
- Track database size growth
- Alert on rapid growth

---

### 🟡 MEDIUM PRIORITY (Add Within 2 Weeks)

#### 7. **Automatic Docker Cleanup**
**Why:** Docker images/volumes accumulate, disk space wasted

**Proposed Solution:**
```javascript
auto_cleanup_docker({
  remove_unused: true,        // Remove unused images
  remove_dangling: true,      // Remove dangling images
  prune_volumes: false,       // Keep volumes (safety)
  max_age: "30d"             // Remove images older than 30d
})
```

#### 8. **Automatic Security Scanning**
**Why:** We have Trivy/Semgrep/Nuclei but they're manual

**Proposed Solution:**
```javascript
auto_security_scan({
  targets: ["docker-images", "source-code", "config-files"],
  scanners: ["trivy", "semgrep", "nuclei"],
  schedule: "daily",
  auto_fix: true,             // Auto-fix known vulnerabilities
  upload_to_defectdojo: true
})
```

#### 9. **Automatic Dependency Updates**
**Why:** Dependencies get outdated, security vulnerabilities accumulate

**Proposed Solution:**
```javascript
auto_update_dependencies({
  package_managers: ["npm", "pip", "apt"],
  security_only: true,        // Only security updates
  auto_test: true,           // Run tests after update
  auto_commit: true,         // Commit via auto_git_commit
  auto_pr: false             // Create PR instead of direct commit
})
```

#### 10. **Automatic Performance Monitoring**
**Why:** No automatic performance baseline or anomaly detection

**Proposed Solution:**
```javascript
auto_monitor_performance({
  metrics: ["cpu", "memory", "disk", "network", "response-time"],
  baseline: "7d",            // 7-day baseline
  alert_threshold: "2x",     // Alert if 2x baseline
  auto_scale: false          // Don't auto-scale (single server)
})
```

---

### 🟢 LOW PRIORITY (Add When Time Permits)

#### 11. **Automatic Code Quality Checks**
**Why:** No automatic code review, style checking, complexity analysis

**Proposed Solution:**
```javascript
auto_check_code_quality({
  linters: ["eslint", "pylint", "shellcheck"],
  formatters: ["prettier", "black"],
  complexity: true,          // Check cyclomatic complexity
  auto_fix: true            // Auto-fix style issues
})
```

#### 12. **Automatic API Testing**
**Why:** APIs deployed without automatic testing

**Proposed Solution:**
```javascript
auto_test_api({
  endpoints: [
    "http://localhost:8003/api/health",
    "http://localhost:9000/api/method/ping"
  ],
  schedule: "hourly",
  alert_on_failure: true
})
```

#### 13. **Automatic Documentation Generation**
**Why:** API docs often outdated or missing

**Proposed Solution:**
```javascript
auto_generate_docs({
  type: "openapi",           // OpenAPI/Swagger
  source: "source-code",     // Generate from code
  output: "docs/api.html",
  auto_commit: true
})
```

---

## 📊 Priority Matrix

| Service/Process | Impact | Effort | Priority | ETA |
|----------------|--------|--------|----------|-----|
| 1. Auto Documentation | HIGH | LOW | 🔴 CRITICAL | 1 day |
| 2. Auto Health Monitoring | HIGH | MEDIUM | 🔴 CRITICAL | 2 days |
| 3. Auto Backup | HIGH | MEDIUM | 🔴 CRITICAL | 2 days |
| 4. Auto MCP Deployment | MEDIUM | MEDIUM | 🟠 HIGH | 3 days |
| 5. Auto Log Management | MEDIUM | LOW | 🟠 HIGH | 1 day |
| 6. Auto DB Maintenance | MEDIUM | LOW | 🟠 HIGH | 1 day |
| 7. Auto Docker Cleanup | LOW | LOW | 🟡 MEDIUM | 4 hours |
| 8. Auto Security Scan | MEDIUM | HIGH | 🟡 MEDIUM | 3 days |
| 9. Auto Dependency Updates | MEDIUM | HIGH | 🟡 MEDIUM | 3 days |
| 10. Auto Performance Monitor | LOW | MEDIUM | 🟡 MEDIUM | 2 days |
| 11. Auto Code Quality | LOW | LOW | 🟢 LOW | 1 day |
| 12. Auto API Testing | LOW | LOW | 🟢 LOW | 1 day |
| 13. Auto Doc Generation | LOW | MEDIUM | 🟢 LOW | 2 days |

---

## 🎯 Recommended Implementation Order

### Phase 1 (This Week - Critical)
1. **Auto Documentation Updates** (1 day)
   - Immediate value: Keep CLAUDE.md, README.md in sync
   - Reduces manual work by 80%

2. **Auto Health Monitoring** (2 days)
   - Prevents service downtime
   - Auto-restart failed services
   - Platform-admin already exists, just enhance it

3. **Auto Backup Orchestration** (2 days)
   - Critical for data safety
   - Currently backups are ad-hoc
   - Easy to implement (scripts exist)

### Phase 2 (Next Week - High Priority)
4. **Auto Log Management** (1 day)
5. **Auto DB Maintenance** (1 day)
6. **Auto MCP Deployment** (3 days)

### Phase 3 (Following Weeks - Medium/Low Priority)
7. Auto Docker Cleanup
8. Auto Security Scanning
9. Auto Dependency Updates
10. Auto Performance Monitoring
11. Auto Code Quality
12. Auto API Testing
13. Auto Doc Generation

---

## 💡 Architecture Pattern (Consistent with Existing)

All new automation should follow the same pattern as deployment + git:

```javascript
// 1. Helper Module
// ~/host-config-agent/agents/[service]-helpers.js
export async function executeOperation() { ... }

// 2. Coordinator Method
// ~/host-config-agent/agents/coordinator-agent.js
async execute[Service][Operation](request) {
  // 7-step process
  // 1. Analyze, 2. Validate, 3. Plan, 4. Execute,
  // 5. Verify, 6. Register DB, 7. Log decision
}

// 3. Database Table
// /var/lib/host-config-agent/host_config.db
CREATE TABLE [service]_operations (...)

// 4. MCP Tool
// ~/host-config-agent/mcp/server.js
{
  name: 'auto_[operation]',
  description: 'AUTOMATIC [OPERATION] - MANDATORY...',
  inputSchema: { ... }
}

// 5. CLAUDE.md Policy
// ~/.claude/CLAUDE.md
## ⚡ MANDATORY [SERVICE] POLICY
REQUIRED: Use auto_[operation] for ALL [operations]

// 6. Documentation
// ~/[SERVICE]_AUTOMATION_IMPLEMENTATION_COMPLETE.md
```

---

## 🔒 Common Features for All Automation

Every automation should include:

1. **Validation** - Pre-execution checks
2. **Execution** - The actual operation
3. **Verification** - Post-execution validation
4. **Database Tracking** - Audit trail
5. **Rollback** - Undo on failure
6. **Logging** - Decision logging
7. **Alerting** - Notify on failure
8. **Documentation** - Auto-generate docs

---

## 📞 Questions to Clarify

1. **Which Phase 1 service should we start with?**
   - Auto Documentation (easiest, immediate value)
   - Auto Health Monitoring (most critical)
   - Auto Backup (data safety)

2. **Should all automation be MANDATORY?**
   - Yes for critical operations (backups, security)
   - No for optional tasks (code quality, doc generation)

3. **Should automation run on schedule or on-demand?**
   - Schedule: Backups, health checks, DB maintenance
   - On-demand: Deployments, git commits, doc updates
   - Both: Security scans (scheduled + pre-commit)

4. **What should happen when automation fails?**
   - Retry 3 times with exponential backoff
   - Create GitHub issue if still failing
   - Send Slack/email alert
   - Never auto-rollback destructive operations (backups, deployments)

---

## ✅ Next Steps

**Recommendation:** Start with **Auto Documentation Updates**

**Why:**
- Easiest to implement (1 day)
- Immediate value (80% time savings)
- Low risk (doesn't affect running services)
- Good pattern to follow for other automation

**Command:**
```
"Implement auto documentation updates next"
```

---

**Made by Insa Automation Corp for OpSec**
**Analysis Date:** October 20, 2025 18:45 UTC
**Version:** 1.0 - Automation Roadmap
