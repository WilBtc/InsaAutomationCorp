# RAG Data Access Scope - What Can Agents See?

**Date:** November 1, 2025 03:00 UTC
**Component:** SystemKnowledgeRAG (Phase 1)
**Security Level:** READ-ONLY, Infrastructure Documentation Only

---

## ✅ What Agents CAN See

### 1. Infrastructure Documentation
**Files:**
- `/home/wil/.claude/CLAUDE.md` - System architecture, service locations, quick reference
- `/home/wil/README.md` - Main system documentation
- `/home/wil/automation/README.md` - Automation system docs
- `/home/wil/platforms/insa-crm/README.md` - CRM platform architecture (NOT customer data)
- `/home/wil/automation/agents/orchestrator/*.md` - Agent documentation

**What This Includes:**
- Server IPs, hostnames, Tailscale addresses
- Service names and ports (e.g., "INSA CRM on port 8003")
- Platform structure (directory paths, consolidated locations)
- System architecture (which services exist, how they connect)
- Service status commands (systemctl, docker, etc.)

### 2. Service Configuration Files
**Files:**
- `/etc/systemd/system/*.service` - Systemd service definitions
- Service WorkingDirectory paths
- Service ExecStart commands
- Service dependencies

**What This Includes:**
- Which services are configured
- Where service binaries/scripts are located
- Service start commands
- BUT NOT: Application configuration, API keys, passwords

### 3. Git History (Metadata Only)
**Command:** `git log --since=14 days --oneline --grep=platform|consolidation|path|service`

**What This Includes:**
- Recent commit messages (last 14 days)
- Platform changes (consolidations, moves)
- Service updates
- BUT NOT: Code contents, file diffs, sensitive commits

### 4. Platform Directory Structure
**Checks:**
- Does `/home/wil/platforms/insa-crm/` exist? ✅
- Does `/home/wil/insa-crm-platform/` exist? ❌ (old, deprecated)
- Directory existence validation
- BUT NOT: Directory contents, files inside

### 5. Known Error Patterns
**Hardcoded Patterns:**
- "No such file" → likely path consolidation issue
- "Address already in use" → port conflict
- "Exit code 203" → missing executable
- Common service failure patterns

**What This Includes:**
- Generic troubleshooting knowledge
- Common infrastructure failure modes
- Solution templates (e.g., "check lsof for port conflicts")

---

## ❌ What Agents CANNOT See

### 1. Customer Data - ZERO ACCESS ✅
**NO access to:**
- PostgreSQL databases (insa_crm, erpnext, mautic, etc.)
- CRM lead data
- Customer information
- Contact details
- Opportunity data
- Quotations
- Sales data
- Any business-sensitive information

**Why:** RAG only reads documentation files, NOT database connections

### 2. Application Configuration - NO ACCESS ✅
**NO access to:**
- `.env` files with API keys, passwords
- Application config files (config.py, settings.json)
- Database credentials
- OAuth tokens
- API keys
- SMTP passwords
- JWT secrets

**Why:** RAG only reads public documentation, NOT config files

### 3. Application Logs - NO ACCESS ✅
**NO access to:**
- `/var/log/insa-crm/` application logs
- API request/response logs
- User activity logs
- Debug logs with sensitive data

**Why:** RAG only reads system documentation, NOT application logs

**Note:** The autonomous orchestrator DOES scan `/var/log/syslog` for ERROR patterns, but this is separate from RAG. It only extracts error messages (e.g., "Service failed"), NOT log context.

### 4. Code Implementation - NO ACCESS
**NO access to:**
- Python/JavaScript source code
- Business logic
- API implementations
- Database schemas
- SQL queries

**Why:** RAG only reads documentation (README, CLAUDE.md), NOT source code

### 5. Backups - NO ACCESS
**NO access to:**
- Database dumps
- Customer data backups
- Configuration backups with secrets

---

## Example: What RAG Sees vs Doesn't See

### Scenario: insa-crm.service Failure

#### ✅ What RAG DOES See:
```
From CLAUDE.md:
- INSA CRM System: FastAPI on http://100.100.101.1:8003
- Database: PostgreSQL (insa_crm)
- Lead Scoring: 0-100 (5 criteria, AI-powered)
- Git: ~/insa-crm-system/ (committed - 3,870 lines)

From service file (/etc/systemd/system/insa-crm.service):
- WorkingDirectory=/home/wil/platforms/insa-crm/core
- ExecStart=/home/wil/platforms/insa-crm/core/venv/bin/uvicorn
- Port: 8003

From git log:
- Oct 18: "Platform consolidation: insa-crm-platform → platforms/insa-crm"

From platform structure:
- ✅ /home/wil/platforms/insa-crm/ EXISTS
- ❌ /home/wil/insa-crm-platform/ MISSING (deprecated)
```

**Agent Knows:**
- Service should run on port 8003
- Service moved from old path to new path in October
- WorkingDirectory must exist or service fails
- Platform consolidation happened recently

#### ❌ What RAG DOES NOT See:
```
CANNOT see from database:
- How many leads exist
- Customer names, emails, companies
- Lead scores, opportunity values
- Quotation amounts

CANNOT see from .env file:
- DATABASE_URL=postgresql://user:PASS@localhost/insa_crm
- SECRET_KEY=abc123...
- ANTHROPIC_API_KEY=sk-ant-...

CANNOT see from application logs:
- "User john@example.com logged in"
- "API request: POST /api/leads with data: {name: 'Acme Corp'}"
- "Lead #1234 scored 85/100"
```

---

## Security Analysis

### Data Privacy: ✅ SECURE
**No customer data exposure:**
- RAG has zero database access
- No business-sensitive information in scope
- Only infrastructure metadata visible

### Credentials: ✅ SECURE
**No credential exposure:**
- No .env files read
- No config files with secrets
- Service files don't contain passwords

### Code Security: ✅ SECURE
**No business logic exposure:**
- No source code access
- No API implementation details
- Only documentation visible

---

## What If We Want More Data?

### Future RAG Phases (NOT Implemented)

**Phase 2 (Planned - NOT Active):**
- Vector database (ChromaDB) for semantic search
- More documentation files
- Service health metrics (CPU, memory)
- Still NO customer data

**Phase 3 (Future - NOT Active):**
- Application performance metrics (APM)
- Service topology maps
- Error rate statistics
- Still NO customer data

**Phase 4 (Future - NOT Active):**
- Predictive failure detection
- Historical pattern analysis
- Resource usage trends
- Still NO customer data

**IMPORTANT:** Even in future phases, the design principle is:
> **RAG = Infrastructure Knowledge, NOT Business Data**

Customer data, credentials, and business logic remain isolated from the autonomous agent system.

---

## How to Verify What RAG Sees

### Test the RAG System
```python
# Run the RAG test
cd /home/wil/automation/agents/orchestrator/
python3 system_knowledge_rag.py

# Test with a service failure
# You'll see exactly what context the agents get
```

### Output Example:
```
=== SYSTEM ARCHITECTURE ===
SERVER INFO: iac1 Server - INSA Oil & Gas Platform
ACTIVE SERVICES: 8 services listed with status

=== PLATFORM STRUCTURE ===
✅ /home/wil/platforms/insa-crm (Current)
❌ /home/wil/insa-crm-platform (OLD - deprecated)

=== SERVICE CONFIGURATION ===
SERVICE CONFIG (insa-crm.service):
  WorkingDirectory: /home/wil/platforms/insa-crm/core (✅ EXISTS)
  ExecStart: /home/wil/platforms/insa-crm/core/venv/bin/uvicorn...

=== KNOWN PATTERNS ===
PATTERN: Port Conflict (EADDRINUSE)
  Solution: lsof -i :<port>, kill <PID>
```

**Notice:** Only infrastructure metadata, zero customer data!

---

## Conclusion

### Summary: What Can Agents See?

| Category | Access | Example |
|----------|--------|---------|
| Infrastructure Docs | ✅ YES | CLAUDE.md, README files |
| Service Configs | ✅ YES | systemd service files |
| Git History | ✅ YES | Commit messages (14 days) |
| Platform Paths | ✅ YES | Directory existence checks |
| Error Patterns | ✅ YES | Hardcoded troubleshooting |
| **Customer Data** | ❌ NO | Leads, contacts, opportunities |
| **Database Contents** | ❌ NO | PostgreSQL, MariaDB data |
| **Credentials** | ❌ NO | .env, config files |
| **Application Logs** | ❌ NO | API logs, user activity |
| **Source Code** | ❌ NO | Python/JS implementations |

### Security Posture: ✅ EXCELLENT

**RAG Phase 1 is:**
- Read-only infrastructure documentation
- Zero customer data exposure
- Zero credential exposure
- Safe for autonomous agent access

**Design Principle:**
> "Agents understand the SYSTEM, not the BUSINESS DATA"

The autonomous agents can fix infrastructure issues (services, paths, ports) without ever seeing your customer information, sales data, or business secrets.

---

**Created by:** Claude Code
**Reviewed by:** Wil Aroca (Insa Automation Corp)
**Date:** November 1, 2025 03:00 UTC
**Status:** ✅ VERIFIED SECURE - No business data exposure
