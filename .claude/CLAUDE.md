# iac1 Server - Quick Reference
# Version: 4.1 | Updated: October 17, 2025 20:00 UTC
# Server: 100.100.101.1 | Role: Azure VM Monitoring + DevSecOps + IEC 62443 + AI Remediation + CRM + AI Agents

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

ERPNext CRM (DEPLOYED - Oct 17, 2025):
  Implementation Guide: ~/QUOTATION_TOOLS_ADDED.md
  Gap Analysis: ~/ERPNEXT_CRM_GAP_ANALYSIS.md
  Docker Fix: ~/ERPNEXT_CRM_FIXED.md
  Web UI: http://100.100.101.1:9000
  Git Repo: ~/mcp-servers/erpnext-crm/
  MCP Server: ~/mcp-servers/erpnext-crm/server.py
  Tools: 16 (48% complete - quotations ready)

INSA CRM System (DEPLOYED - Oct 17, 2025):
  Project Root: ~/insa-crm-system/
  FastAPI Server: http://100.100.101.1:8003
  API Docs: http://100.100.101.1:8003/api/docs
  Database: PostgreSQL (insa_crm)
  Lead Qualification: AI-powered (0-100 scoring)
  Git Repo: ~/insa-crm-system/ (committed)
  Docs: ~/insa-crm-system/README.md
  Quick Start: ~/insa-crm-system/QUICKSTART.md

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

## 🤖 MCP SERVERS (7 Active)
```yaml
Config: ~/.mcp.json
Backup: ~/.mcp.json.backup-*
Total: 7 active MCP servers

azure-vm-monitor:
  Path: ~/mcp-servers/azure-vm-monitor/
  Size: 26MB
  Purpose: Azure VM health checks (every 5 min)

azure-alert:
  Path: ~/mcp-servers/azure-alert/
  Size: 16MB
  Purpose: Email alerts to w.aroca@insaing.com

host-config-agent:
  Path: ~/host-config-agent/mcp/server.js
  Size: ~150MB (Node + Python + DB)
  Purpose: Multi-agent server configuration management
  Tools: 10 tools (get_server_status, request_deployment, etc)
  Agents: Inventory Agent + Coordinator Agent (Claude Sonnet 4.5)
  Features: Real-time resource tracking, AI deployment decisions

defectdojo-iec62443:
  Path: ~/mcp-servers/defectdojo-iec62443/server.py
  Size: 14KB
  Purpose: IEC 62443 industrial security compliance automation
  Tools: 8 tools (get_findings, tag_finding, auto_tag_findings, etc)
  Features: Intelligent FR/SR tagging, compliance metrics, scan import
  Agent: defectdojo-compliance-agent.service (scans every hour)
  Dashboard: http://100.100.101.1:3004
  Full Docs: ~/DEFECTDOJO_IEC62443_SETUP_COMPLETE.md

stackstorm-health-monitor:
  Path: ~/mcp-servers/stackstorm-health-monitor/
  Size: ~16MB
  Purpose: Prevent runaway processes

chrome-devtools:
  Path: ~/mcp-servers/chrome-devtools/
  Size: ~70MB
  Purpose: UI/UX testing (screenshot, CSS inspection)

tailscale-devops:
  Path: ~/tailscale-devops-mcp.js
  Size: ~10KB
  Purpose: Network management for INSA infrastructure
  Tools: 10 tools (network status, SSH, tunnels, routing)

erpnext-crm (NEW - Oct 17, 2025):
  Path: ~/mcp-servers/erpnext-crm/server.py
  Size: ~16MB
  Purpose: CRM automation for INSA Automation Corp
  Tools: 16 tools (leads, opportunities, quotations, customers, contacts, analytics)
  Status: 48% complete - quotation generation ready
  Web UI: http://100.100.101.1:9000
  Docs: ~/QUOTATION_TOOLS_ADDED.md
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

## 🚦 STATUS (Oct 17, 2025 - 20:00 UTC)
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
- ✅ ERPNext CRM: Quotation tools deployed (16 tools, 48% complete)
  - Web UI: http://100.100.101.1:9000 ✅ ACTIVE
  - Container: frappe_docker_backend_1 (Docker exec method)
  - Docs: ~/QUOTATION_TOOLS_ADDED.md
  - Git: ~/mcp-servers/erpnext-crm/ (committed)
- ✅ INSA CRM System: AI-powered lead qualification (Phase 0 MVP)
  - FastAPI: http://100.100.101.1:8003 ✅ ACTIVE
  - Database: PostgreSQL (insa_crm) - 2 tables
  - Lead Scoring: 0-100 (5 criteria, AI-powered)
  - Process: nohup (PID 737557), logs: /tmp/insa-crm.log
  - Git: ~/insa-crm-system/ (committed - 3,870 lines)
- ✅ Container Orchestrator: 24/7 lifecycle management
- ✅ Host Config Agent: 24/7 resource tracking (ZERO API cost)
  - Database: /var/lib/host-config-agent/host_config.db
  - Claude Code subprocess integration working
- ✅ Security Hardening: Suricata IDS + Wazuh FIM + SSH restricted
- ✅ MCP Servers: 7 active servers
- ✅ Documentation: v4.1 - Added INSA CRM System
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
**Role:** Azure VM Monitoring + DevSecOps + AI Host Configuration + IEC 62443 + AI Remediation + CRM + AI Agents
**Access:** ssh 100.100.101.1
**Sudo:** [REDACTED]***
**Version:** 4.1 | Updated: October 17, 2025 20:00 UTC

## 🎯 QUICK LINKS
- **INSA CRM System:** http://100.100.101.1:8003 (✅ NEW - AI Agents)
- **INSA CRM API Docs:** http://100.100.101.1:8003/api/docs
- **DefectDojo Web UI:** http://100.100.101.1:8082 (✅ ACTIVE)
- **ERPNext CRM Web UI:** http://100.100.101.1:9000 (✅ ACTIVE)
- **IEC 62443 Dashboard:** http://100.100.101.1:3004
- **INSA CRM Guide:** `~/insa-crm-system/README.md` (NEW - Oct 17)
- **ERPNext CRM Guide:** `~/QUOTATION_TOOLS_ADDED.md`
- **CRM Gap Analysis:** `~/ERPNEXT_CRM_GAP_ANALYSIS.md`
- **Celery/Redis Fix:** `~/DEFECTDOJO_CELERY_REDIS_ISSUE_RESOLVED.md`
- **Email Reporting:** `~/EMAIL_SELF_HOSTED_SETUP_COMPLETE.md` (✅ CONFIGURED)
- **Autonomous Remediation:** `~/AUTONOMOUS_REMEDIATION_SYSTEM.md`
- **IEC 62443 Compliance:** `~/DEFECTDOJO_IEC62443_SETUP_COMPLETE.md`
- **Container Orchestrator:** `~/devops/container-orchestrator/README.md`
- **Host Config Agent:** `~/host-config-agent/README.md`
- **Learning Databases:** 3 total - DefectDojo, Host Config, INSA CRM
- **Git Repos:** `~/devops/devsecops-automation/defectdojo/` + `~/mcp-servers/erpnext-crm/` + `~/insa-crm-system/`
- **Always:** Update docs in git, keep CLAUDE.md light with links
- **Credit:** Made by Insa Automation Corp for OpSec

## 🤖 USING HOST CONFIG AGENT IN CLAUDE CODE
When deploying services, Claude Code can now:
- Check server resources: Use `get_server_status` MCP tool
- Find available ports: Use `find_available_port` MCP tool
- Request deployment approval: Use `request_deployment` MCP tool
- Ask questions: Use `ask_inventory_agent` with natural language
See: `~/host-config-agent/README.md` for all 10 MCP tools