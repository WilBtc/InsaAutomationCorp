# iac1 Server - Quick Reference
# Version: 5.1 | Updated: October 18, 2025 22:30 UTC (PHASE 7 COMPLETE ✅)
# Server: 100.100.101.1 | Role: Azure VM Monitoring + DevSecOps + IEC 62443 + AI Remediation + CRM Platform (Unified) + Marketing Automation + Workflow Automation + AI Agents + P&ID Generation + AI Quote Generation

## 🚨 CRITICAL RULES
- **Server Role**: Azure VM monitoring ONLY (READ-ONLY)
- **Email**: w.aroca@insaing.com (alerts only)
- **Sudo Password**: [REDACTED]***
- **No Production Data**: This is a monitoring server

## 🔑 QUICK ACCESS
```yaml
Server:
  IP: 100.100.101.1
  Hostname: iac1
  User: wil
  SSH: ssh 100.100.101.1
  Tailscale: iac1 ([REDACTED]@)

Azure VM (Monitoring Target):
  Tailscale IP: 100.107.50.52
  Hostname: azure-vm-thingsboard
  SSH: ssh -i ~/.ssh/azure_vm_key -p 2222 sysadmin@100.107.50.52
  Public IP: 172.208.66.188 (legacy/fallback)
  Status: ACTIVE - 153M+ records
  Agent: READ-ONLY monitoring via Tailscale VPN

INSA ERP (Production):
  IP: 100.105.64.109
  Status: OFFLINE (Tailscale relay)
  Database: insa_cloud_db (426GB)
  Access: Via workstation only

Workstation (Development):
  IP: 100.81.103.99
  Hostname: LU1
  Role: Full stack development
```

## 📁 DOCUMENTATION PATHS
```yaml
Local Docs:
  This file: ~/.claude/CLAUDE.md
  Git guide: ~/.claude/GIT_QUICK_REFERENCE.md
  MCP guide: ~/.claude/MCP_QUICK_REFERENCE.md
  Audit: /tmp/IAC1_MCP_AUDIT_REPORT.md

Azure VM Monitoring:
  Tailscale Integration: ~/azure-monitor-docs/AZURE_TAILSCALE_INTEGRATION.md
  Agent Script: ~/azure_autonomous_agent.py
  MCP Server: ~/mcp-servers/azure-vm-monitor/server.py
  Agent Logs: ~/azure_agent.log

DevSecOps Projects:
  DefectDojo SOC: ~/devops/devsecops-automation/defectdojo/README.md
  DefectDojo Web UI: http://100.100.101.1:8082 (✅ ACTIVE)
  Celery/Redis Fix: ~/DEFECTDOJO_CELERY_REDIS_ISSUE_RESOLVED.md (Oct 17, 2025)
  IEC 62443 Compliance: ~/DEFECTDOJO_IEC62443_SETUP_COMPLETE.md (Oct 17, 2025)
  Autonomous Remediation: ~/AUTONOMOUS_REMEDIATION_SYSTEM.md (Oct 17, 2025)
  Email Reporting: ~/EMAIL_SELF_HOSTED_SETUP_COMPLETE.md (✅ CONFIGURED)
  Compliance Dashboard: http://100.100.101.1:3004
  Container Orchestrator: ~/devops/container-orchestrator/README.md
  Learning DB: /var/lib/defectdojo/learning.db

Host Configuration Agent (DEPLOYED):
  Start Here: ~/host-config-agent/START_HERE.md
  Deployment Success: ~/host-config-agent/DEPLOYMENT_SUCCESS.md
  Zero API Cost: ~/host-config-agent/ZERO_API_COST_SUCCESS.md
  Full Docs: ~/host-config-agent/README.md
  Quick Start: ~/host-config-agent/QUICKSTART.md
  Architecture: ~/host-config-agent/ARCHITECTURE.txt
  Database: /var/lib/host-config-agent/host_config.db

INSA CRM Platform (CONSOLIDATED - Oct 18, 2025): ⭐ NEW UNIFIED LOCATION
  Platform Root: ~/insa-crm-platform/ (679MB total, 24K+ files)
  Master Guide: ~/insa-crm-platform/README.md (11 KB)
  Consolidation Report: ~/INSA_CRM_CONSOLIDATION_COMPLETE.md
  Status: ✅ PRODUCTION READY - All components organized & tested

  Core (AI Lead Qualification + Quote Generation):
    Path: ~/insa-crm-platform/core/
    FastAPI Server: http://100.100.101.1:8003
    API Docs: http://100.100.101.1:8003/api/docs
    Database: PostgreSQL (insa_crm)
    Features:
      - Phase 1: AI-powered 0-100 lead scoring
      - Phase 7: AI quote generation (<1s, RAG-powered) ⭐ NEW
    Storage: /var/lib/insa-crm/ (ChromaDB + quotes)
    Docs: ~/insa-crm-platform/core/README.md
    Phase 7 Docs: ~/insa-crm-platform/PHASE7_AI_QUOTE_GENERATION_COMPLETE.md

  MCP Servers (4 integrated platforms):
    ERPNext CRM:
      Path: ~/insa-crm-platform/mcp-servers/erpnext-crm/
      Web UI: http://100.100.101.1:9000
      Tools: 33 (Phase 3b complete - full sales cycle + projects)
      Docs: ~/insa-crm-platform/mcp-servers/erpnext-crm/README.md

    InvenTree:
      Path: ~/insa-crm-platform/mcp-servers/inventree-crm/
      Web UI: http://100.100.101.1:9600
      Tools: 5 (inventory + BOM management)

    Mautic:
      Path: ~/insa-crm-platform/mcp-servers/mautic-admin/
      Web UI: http://100.100.101.1:9700
      Tools: 27 (marketing automation)
      Database: MariaDB 11.6 (157 tables)
      Automation: 13 cron jobs

    n8n:
      Path: ~/insa-crm-platform/mcp-servers/n8n-admin/
      Web UI: http://100.100.101.1:5678
      Tools: 23 (workflow automation)
      Resource Limits: 1GB RAM, 1 CPU

  Automation:
    Workflows: ~/insa-crm-platform/automation/workflows/ (6 n8n JSONs)
    Templates: ~/insa-crm-platform/automation/templates/ (7 Mautic emails)

  Projects:
    Customer Files: ~/insa-crm-platform/projects/customers/INSAGTEC-6598/
    P&ID Generator: ~/insa-crm-platform/projects/templates/pid-generator/
    Reference Project: INSAGTEC-6598 (63 files, 66 MB)

  Documentation:
    Architecture: ~/insa-crm-platform/docs/architecture/
    Deployment: ~/insa-crm-platform/docs/deployment/ (8 PHASE*.md files)
    Guides: ~/insa-crm-platform/docs/guides/
      - MAUTIC_MCP_COMPLETE_GUIDE.md (48 KB)
      - INSA_PROJECT_WORKFLOW_RAG_MEMORY.md (35 KB, 900+ lines)
      - RESOURCE_PROTECTION_COMPLETE.md
      - PROYECTO_PID_CRM_WORKFLOW_COMPLETE.md

Infrastructure Docs (on INSA ERP):
  Network: ~/INSA_INFRASTRUCTURE_MAP_2025.md
  Status: ~/INSA_INFRASTRUCTURE_STATUS_2025.md
  Backups: ~/BACKUP_LOCATIONS_GUIDE.md

Project Docs (on Workstation):
  Full MCP: /tmp/FULLSTACK_MCP_SETUP_COMPLETE.md
  Performance: /tmp/PERFORMANCE_OPTIMIZATION_COMPLETE.md

Security (iac1):
  Hardening Report: ~/devops/devsecops-automation/docs/SECURITY_HARDENING_2025-10-11.md
  Wazuh Config: /var/ossec/etc/ossec.conf
  Suricata Config: /etc/suricata/suricata.yaml
  Security Logs: /var/log/{suricata,aide_check,rkhunter_scan,lynis_audit}.log
```

## 🤖 MCP SERVERS (11 Active - 7 Working ✅, 2 Pending ⏳, 2 Unknown ❓)
```yaml
Config: ~/.mcp.json
Backup: ~/.mcp.json.backup-*
Total: 11 active MCP servers (7 working ✅, 2 pending ⏳, 2 unknown ❓)
New Today: n8n-admin (Oct 18, 2025 17:30 UTC) ⭐ PHASE 6 COMPLETE
Upgraded Today: defectdojo-iec62443 + grafana-admin (Oct 18, 2025)
Status Report: ~/N8N_MCP_DEPLOYMENT_COMPLETE.md (Oct 18, 2025 - NEW)

azure-vm-monitor:
  Path: ~/mcp-servers/azure-vm-monitor/
  Size: 26MB
  Purpose: Azure VM health checks (every 5 min)
  Status: ⚠️ NEEDS PROTOCOL UPGRADE (old JSON protocol)

azure-alert:
  Path: ~/mcp-servers/azure-alert/
  Size: 16MB
  Purpose: Email alerts to w.aroca@insaing.com
  Status: ⚠️ NEEDS PROTOCOL UPGRADE (old JSON protocol)

host-config-agent:
  Path: ~/host-config-agent/mcp/server.js
  Size: ~150MB (Node + Python + DB)
  Purpose: Multi-agent server configuration management
  Tools: 10 tools (get_server_status, request_deployment, etc)
  Agents: Inventory Agent + Coordinator Agent (Claude Sonnet 4.5)
  Features: Real-time resource tracking, AI deployment decisions

defectdojo-iec62443:
  Path: ~/mcp-servers/defectdojo-iec62443/server.py
  Size: 14KB → 557 lines (upgraded Oct 18, 2025)
  Purpose: IEC 62443 industrial security compliance automation
  Tools: 8 tools (get_findings, tag_finding, auto_tag_findings, etc)
  Status: ✅ UPGRADED TO MCP SDK (Oct 18, 2025)
  Protocol: Official MCP SDK (from old custom JSON)
  Features: Intelligent FR/SR tagging, compliance metrics, scan import
  Agent: defectdojo-compliance-agent.service (scans every hour)
  Dashboard: http://100.100.101.1:3004
  Full Docs: ~/DEFECTDOJO_IEC62443_SETUP_COMPLETE.md
  Upgrade Docs: ~/MCP_UPGRADE_COMPLETE_DEFECTDOJO.md

chrome-devtools:
  Path: ~/mcp-servers/chrome-devtools/
  Size: ~70MB
  Purpose: UI/UX testing (screenshot, CSS inspection)

tailscale-devops:
  Path: ~/tailscale-devops-mcp.js
  Size: ~10KB
  Purpose: Network management for INSA infrastructure
  Tools: 10 tools (network status, SSH, tunnels, routing)

erpnext-crm (Phase 3b Complete - CONSOLIDATED Oct 18, 2025):
  Path: ~/insa-crm-platform/mcp-servers/erpnext-crm/server.py ⭐ NEW LOCATION
  Size: ~40MB (with venv)
  Purpose: CRM automation for INSA Automation Corp - FULL LIFECYCLE
  Tools: 33 tools (100% complete)
  Status: ✅ PRODUCTION READY - Complete sales cycle + project management
  Web UI: http://100.100.101.1:9000
  Docs: ~/insa-crm-platform/docs/deployment/PHASE3_ERPNEXT_PROJECTS_COMPLETE.md

inventree-crm (Phase 2 Complete - CONSOLIDATED Oct 18, 2025):
  Path: ~/insa-crm-platform/mcp-servers/inventree-crm/server.py ⭐ NEW LOCATION
  Size: ~40MB (with venv)
  Purpose: Inventory management and BOM tracking - PRODUCTION READY
  Tools: 5 tools (100% complete)
  Status: ✅ OPERATIONAL
  Web UI: http://100.100.101.1:9600

cadquery-mcp:
  Path: ~/mcp-servers/mcp-cadquery/server_stdio.sh
  Size: ~15MB
  Purpose: Headless 3D CAD generation (bertvanbrakel/mcp-cadquery)
  Status: ✅ PRODUCTION READY
  Docs: ~/mcp-servers/mcp-cadquery/README.md
  Integration: BOM-driven CAD for ERPNext/InvenTree

mautic-admin (Phase 4 Complete - CONSOLIDATED Oct 18, 2025):
  Path: ~/insa-crm-platform/mcp-servers/mautic-admin/server.py ⭐ NEW LOCATION
  Size: ~38MB (with venv)
  Purpose: Marketing automation master admin - FULL PROGRAMMATIC CONTROL
  Tools: 27 tools (100% complete)
  Status: ✅ PRODUCTION READY - CLI + API dual execution
  Web UI: http://100.100.101.1:9700 ✅ ACTIVE
  Database: MariaDB 11.6 (port 3306)
  Automation: 13 cron jobs (segments, campaigns, emails, maintenance)
  Docs: ~/insa-crm-platform/docs/guides/MAUTIC_MCP_COMPLETE_GUIDE.md ⭐ PRIMARY (48 KB)

grafana-admin (NEW - Oct 18, 2025):
  Path: ~/mcp-servers/grafana-admin/server.py
  Size: ~26 KB → 900 lines (upgraded Oct 18, 2025)
  Purpose: Grafana analytics dashboard management - FULL ADMIN CONTROL
  Tools: 23 tools (dashboards, data sources, users, alerts, admin)
  Status: ✅ UPGRADED TO MCP SDK (Oct 18, 2025)
  Protocol: Official MCP SDK (from old JSON-RPC)
  Web UI: http://100.100.101.1:3002

n8n-admin (Phase 6 Complete - CONSOLIDATED Oct 18, 2025):
  Path: ~/insa-crm-platform/mcp-servers/n8n-admin/server.py ⭐ NEW LOCATION
  Size: ~41MB (with venv)
  Purpose: n8n workflow automation - FULL AUTONOMOUS CONTROL
  Tools: 23 tools (100% complete - PRODUCTION READY)
  Status: ✅ BUILT FROM SCRATCH (Oct 18, 2025)
  Web UI: http://100.100.101.1:5678
  Integration: ERPNext ↔ Mautic workflow automation
  Workflows: 6 deployed (in ~/insa-crm-platform/automation/workflows/)
  Docs: ~/insa-crm-platform/mcp-servers/n8n-admin/README.md
```

## ⚡ ACTIVE SYSTEMS
```yaml
Services:
  - azure-monitor-agent.service (auto-start enabled)
  - defectdojo-agent.service (24/7 SOC automation - deprecated)
  - defectdojo-compliance-agent.service (NEW - IEC 62443 compliance)
  - container-orchestrator.service (lifecycle mgmt)
  - host-config-agent.service (24/7 resource tracking)
  - tailscaled.service (VPN)
  - ssh.service (remote access)

Automation:
  - Azure VM Monitor: Every 5 min (READ-ONLY)
  - DefectDojo IEC 62443: Every 1 hour (Trivy scans + FR/SR tagging)
  - Container Orchestrator: Every 5 min
  - Host Config Agent: Every 5 min (resource inventory)
  - Mautic Marketing: 13 cron jobs (campaigns, emails, segments, maintenance)
  - Email Alerts: Disk, services, backups
  - Daily Reports: 8 AM comprehensive status

Monitoring Targets:
  - Azure VM (100.107.50.52 via Tailscale)
  - DefectDojo (100.100.101.1:8082)
  - Docker Containers (22 active)
  - ThingsBoard Pro (7 devices on Azure VM)
  - PostgreSQL backups
  - iac1 Resources: Ports, services, containers, CPU, memory, disk
```

## 🔒 SECURITY STACK (Hardened Oct 11, 2025)
```yaml
Active Defense:
  ✅ Suricata IDS/IPS - 45,777 rules (ET Open + OT protocols)
  ✅ Wazuh Agent - FIM (15+ dirs) + Log collection (10 files)
  ✅ ClamAV - Weekly full scans
  ✅ Fail2ban - Brute-force protection
  ✅ UFW Firewall - SSH via Tailscale only (100.0.0.0/8)
  ✅ AppArmor - 116 profiles
  ✅ Auditd - System call auditing

Automated Scans:
  Weekly: Lynis (Sun 2AM), ClamAV (Sat 1AM)
  Daily: AIDE (3AM), Rkhunter (4AM), Suricata rules (midnight)
  Every 6h: Disk space monitoring

Full Report: ~/devops/devsecops-automation/docs/SECURITY_HARDENING_2025-10-11.md
```

## 🔧 KEY SCRIPTS & SERVICES
```yaml
Monitoring:
  Agent: ~/azure-monitor-agent/agent.py
  Service: systemctl status azure-monitor-agent.service
  Logs: journalctl -u azure-monitor-agent -f

DefectDojo SOC (Simplified Architecture):
  Web UI: http://100.100.101.1:8082 (✅ ACTIVE)
  Containers: uwsgi + redis only (celery disabled - Calico/K8s conflict)
  Remediation Agent: systemctl status defectdojo-remediation-agent.service
  Logs: tail -f /var/log/defectdojo_remediation_agent.log
  Issue Details: ~/DEFECTDOJO_CELERY_REDIS_ISSUE_RESOLVED.md
  MCP Tools: 8 tools (get_findings, triage_finding, etc)

Container Orchestrator:
  Service: systemctl status container-orchestrator.service
  Config: ~/devops/container-orchestrator/config/containers.yml
  Logs: journalctl -u container-orchestrator -f

Host Config Agent (DEPLOYED - Multi-Agent System):
  Service: systemctl status host-config-agent.service (ACTIVE)
  Logs: journalctl -u host-config-agent -f
  Database: /var/lib/host-config-agent/host_config.db
  MCP Tools: 10 tools (deployment guidance, resource queries)
  Agents: Inventory + Coordinator (via Claude Code subprocess - ZERO API cost!)
  Features: AI deployment decisions, conflict prevention
  Status Docs: ~/host-config-agent/DEPLOYMENT_SUCCESS.md

MCP Development:
  Servers: ~/mcp-servers/
  Test: ~/mcp-servers/test-mcp-servers.sh
  Deploy: ~/mcp-servers/deploy-insa-network.sh

Git:
  Check status: "Show git status"
  Create branch: "Create branch feature/name"
  Commit: "Commit with message: ..."
```

## 🚦 STATUS (Oct 18, 2025 - 02:00 UTC)
- ✅ Azure Agent: 24/7 monitoring via Tailscale VPN
- ✅ Azure VM: Integrated into Tailscale (100.107.50.52)
- ✅ DefectDojo: **SIMPLIFIED** - Celery disabled due to Calico/K8s network conflict
  - Web UI: http://100.100.101.1:8082 ✅ ACTIVE
  - Containers: uwsgi + redis (celerybeat/worker disabled)
  - Remediation Agent: ✅ ACTIVE (defectdojo-remediation-agent.service)
  - Issue Analysis: ~/DEFECTDOJO_CELERY_REDIS_ISSUE_RESOLVED.md
  - Production Status: Core functionality working, scheduled tasks need cron
- ✅ DefectDojo IEC 62443: Compliance automation (hourly scans, FR/SR tagging)
  - Service: defectdojo-compliance-agent.service ACTIVE
  - Dashboard: http://100.100.101.1:3004 ONLINE
  - Full Docs: ~/DEFECTDOJO_IEC62443_SETUP_COMPLETE.md
- ✅ ERPNext CRM: Phase 3b Complete (33 tools, 100% complete) ✅ PRODUCTION READY
  - Web UI: http://100.100.101.1:9000 ✅ ACTIVE
  - Container: frappe_docker_backend_1 (Docker exec method)
  - Phase 3b: Project Management (4 tools - Oct 18) ⭐ NEW
  - Phase 3a: Sales orders, delivery notes, invoices, payments (10 tools - Oct 17)
  - Phase 2: Customer details + product catalog (3 tools)
  - Complete Lifecycle: Lead → Opportunity → Quotation → SO → Project → DN → Invoice → Payment
  - Docs: ~/PHASE3_ERPNEXT_PROJECTS_COMPLETE.md
  - Git: ~/mcp-servers/erpnext-crm/ (pending commit - Phase 3b)
- ✅ InvenTree CRM: Phase 2 Complete (5 tools, 100% complete) ✅ PRODUCTION READY
  - Web UI: http://100.100.101.1:9600 ✅ ACTIVE
  - Containers: inventree_web + postgres:5434 + redis:6380 (host network mode)
  - Tools: list_parts, get_part_details, create_bom, get_pricing, track_customer_equipment
  - Blocker RESOLVED: Was thought blocked, but operational (commit 4381304)
  - Docs: ~/INVENTREE_DEPLOYMENT_RESOLVED.md
  - Git: ~/mcp-servers/inventree-crm/
- ✅ INSA CRM System: AI-powered lead qualification (Phase 0 MVP)
  - FastAPI: http://100.100.101.1:8003 ✅ ACTIVE
  - Database: PostgreSQL (insa_crm) - 2 tables
  - Lead Scoring: 0-100 (5 criteria, AI-powered)
  - Process: nohup (PID 737557), logs: /tmp/insa-crm.log
  - Git: ~/insa-crm-system/ (committed - 3,870 lines)
- ✅ Mautic Marketing Automation: Phase 4 Complete (27 tools, 100% complete) ✅ PRODUCTION READY
  - Web UI: http://100.100.101.1:9700 ✅ ACTIVE
  - Version: 5.2.1 (latest stable)
  - Database: MariaDB 11.6 (port 3306, 157 tables)
  - MCP Tools: 27 (CLI + API dual execution - master admin control)
  - Automation: 13 cron jobs (campaigns every 5min, emails every 5min, segments every 15min)
  - Status: Contact creation tested ✅, API authentication working ✅
  - Docs: ~/MAUTIC_MCP_COMPLETE_GUIDE.md (48 KB complete guide)
  - Deployment: ~/PHASE4_MAUTIC_DEPLOYMENT_COMPLETE.md
  - Git: ~/mcp-servers/mautic-admin/ (pending commit)
- ✅ Container Orchestrator: 24/7 lifecycle management
- ✅ Host Config Agent: 24/7 resource tracking (ZERO API cost)
  - Database: /var/lib/host-config-agent/host_config.db
  - Claude Code subprocess integration working
- ✅ Security Hardening: Suricata IDS + Wazuh FIM + SSH restricted
- ✅ MCP Servers: 10 active (6 working ✅, 2 pending ⏳, 2 unknown ❓)
  - defectdojo-iec62443 ✅ UPGRADED (critical compliance)
  - grafana-admin ✅ UPGRADED (analytics management)
  - See ~/MCP_UPGRADES_COMPLETE_2_SERVERS.md
- ✅ Documentation: v4.6 - Mautic Phase 4 Complete (100%)
- ✅ Learning System: Evolutionary AI with SQLite (3 databases)
- ⚠️ INSA ERP: Offline (Tailscale relay)
- 🐳 Docker: 28 containers tracked

## 🗂️ INSTALLED MCP SERVERS
```yaml
Active (~192MB):
  ✅ azure-vm-monitor (26MB)
  ✅ azure-alert (16MB)
  ✅ host-config-agent (150MB) - NEW

Installed but NOT configured (672MB):
  ⚠️ consolidated (524MB)
  ⚠️ chrome-devtools (70MB)
  ⚠️ insa-security-platform (41MB)
  ⚠️ insa-saas (37MB)

Recommendation: Clean unused servers to save space
```

## 📞 CONTACTS & EMAIL
```yaml
Email Alerts: w.aroca@insaing.com
SMTP: localhost:25 (Self-hosted Postfix)
Status: ✅ CONFIGURED (Oct 17, 2025)
Authentication: None required
Test Results: 4/4 email templates working
```

---
**Role:** Azure VM Monitoring + DevSecOps + AI Host Configuration + IEC 62443 + AI Remediation + CRM + Inventory + Marketing Automation + Workflow Automation + AI Agents + P&ID Generation
**Access:** ssh 100.100.101.1
**Sudo:** [REDACTED]***
**Version:** 4.8 | Updated: October 18, 2025 18:15 UTC

## 🎯 QUICK LINKS

### Web UIs
- **INSA CRM System:** http://100.100.101.1:8003 (✅ AI Agents)
- **DefectDojo:** http://100.100.101.1:8082 (✅ ACTIVE)
- **ERPNext CRM:** http://100.100.101.1:9000 (✅ ACTIVE)
- **InvenTree:** http://100.100.101.1:9600 (✅ OPERATIONAL)
- **Mautic:** http://100.100.101.1:9700 (✅ PHASE 4)
- **n8n:** http://100.100.101.1:5678 (✅ PHASE 5)
- **IEC 62443:** http://100.100.101.1:3004

### Key Documentation (See Git)
- **INSA Project Workflow (RAG):** `~/INSA_PROJECT_WORKFLOW_RAG_MEMORY.md` ⭐ NEW (900+ lines)
- **Project Completion Report:** `~/PROYECTO_PID_CRM_WORKFLOW_COMPLETE.md` ⭐ NEW
- **Mautic Guide:** `~/MAUTIC_MCP_COMPLETE_GUIDE.md` (48 KB)
- **n8n Integration:** `~/PHASE5_N8N_ERPNEXT_MAUTIC_INTEGRATION.md`
- **Resource Protection:** `~/RESOURCE_PROTECTION_COMPLETE.md` ⭐ CRITICAL
- **ERPNext Projects:** `~/PHASE3_ERPNEXT_PROJECTS_COMPLETE.md`
- **IEC 62443:** `~/DEFECTDOJO_IEC62443_SETUP_COMPLETE.md`
- **Host Config Agent:** `~/host-config-agent/README.md`
- **INSA CRM:** `~/insa-crm-system/README.md`

### Project Files
- **CRM Storage:** `~/crm-files/` (organized by customer)
- **P&ID Generator:** `~/pid-generator/separador_trifasico.py`
- **Reference Project:** `~/crm-files/INSAGTEC-6598/` (63 files, 66 MB)

### Git Repos
- **DevSecOps:** `~/devops/devsecops-automation/`
- **MCP Servers:** `~/mcp-servers/`
- **INSA CRM:** `~/insa-crm-system/`

### Best Practices
- **Always:** Update docs in git, keep CLAUDE.md light with links
- **Credit:** Made by Insa Automation Corp for OpSec

## 🤖 USING HOST CONFIG AGENT IN CLAUDE CODE
When deploying services, Claude Code can now:
- Check server resources: Use `get_server_status` MCP tool
- Find available ports: Use `find_available_port` MCP tool
- Request deployment approval: Use `request_deployment` MCP tool
- Ask questions: Use `ask_inventory_agent` with natural language
See: `~/host-config-agent/README.md` for all 10 MCP tools
- only use free ports , dont change port config for other apps