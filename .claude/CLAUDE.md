# iac1 Server - Quick Reference
# Version: 3.5 | Updated: October 11, 2025
# Server: 100.100.101.1 | Role: Azure VM Monitoring + DevSecOps Automation

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
  Container Orchestrator: ~/devops/container-orchestrator/README.md
  Config: ~/devops/devsecops-automation/defectdojo/.env.defectdojo
  Learning DB: /var/lib/defectdojo/learning.db

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

## 🤖 MCP SERVERS (2 Active - Azure Focus)
```yaml
Config: ~/.mcp.json
Backup: ~/.mcp.json.backup-*
Total: 2 Azure monitoring servers

azure-vm-monitor:
  Path: ~/mcp-servers/azure-vm-monitor/
  Size: 26MB
  Purpose: Azure VM health checks (every 5 min)

azure-alert:
  Path: ~/mcp-servers/azure-alert/
  Size: 16MB
  Purpose: Email alerts to w.aroca@insaing.com
```

## ⚡ ACTIVE SYSTEMS
```yaml
Services:
  - azure-monitor-agent.service (auto-start enabled)
  - defectdojo-agent.service (24/7 SOC automation)
  - container-orchestrator.service (lifecycle mgmt)
  - tailscaled.service (VPN)
  - ssh.service (remote access)

Automation:
  - Azure VM Monitor: Every 5 min (READ-ONLY)
  - DefectDojo SOC: Every 5 min + AI learning
  - Container Orchestrator: Every 5 min
  - Email Alerts: Disk, services, backups
  - Daily Reports: 8 AM comprehensive status

Monitoring Targets:
  - Azure VM (100.107.50.52 via Tailscale)
  - DefectDojo (100.100.101.1:8082)
  - Docker Containers (22 active)
  - ThingsBoard Pro (7 devices on Azure VM)
  - PostgreSQL backups
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

DefectDojo SOC (24/7 AI-powered):
  Service: systemctl status defectdojo-agent.service
  Logs: tail -f /var/log/defectdojo_agent.log
  Config: ~/devops/devsecops-automation/defectdojo/.env.defectdojo
  Web UI: http://100.100.101.1:8082
  MCP Tools: 8 tools (get_findings, triage_finding, etc)

Container Orchestrator:
  Service: systemctl status container-orchestrator.service
  Config: ~/devops/container-orchestrator/config/containers.yml
  Logs: journalctl -u container-orchestrator -f

MCP Development:
  Servers: ~/mcp-servers/
  Test: ~/mcp-servers/test-mcp-servers.sh
  Deploy: ~/mcp-servers/deploy-insa-network.sh

Git:
  Check status: "Show git status"
  Create branch: "Create branch feature/name"
  Commit: "Commit with message: ..."
```

## 🚦 STATUS (Oct 11, 2025)
- ✅ Azure Agent: 24/7 monitoring via Tailscale VPN
- ✅ Azure VM: Integrated into Tailscale (100.107.50.52)
- ✅ DefectDojo SOC: 24/7 AI-powered triage (zero API costs)
- ✅ Container Orchestrator: 24/7 lifecycle management
- ✅ Security Hardening: Suricata IDS + Wazuh FIM + SSH restricted
- ✅ MCP Servers: 2 servers (42MB active)
- ✅ Documentation: Updated to v3.5 + Security hardening report
- ✅ Learning System: Evolutionary AI with SQLite
- ⚠️ INSA ERP: Offline (Tailscale relay)
- 💾 Disk: 672MB unused MCP servers (can be cleaned)
- 🐳 Docker: 22 containers running, 0 stopped

## 🗂️ INSTALLED MCP SERVERS
```yaml
Active (42MB):
  ✅ azure-vm-monitor (26MB)
  ✅ azure-alert (16MB)

Installed but NOT configured (672MB):
  ⚠️ consolidated (524MB)
  ⚠️ chrome-devtools (70MB)
  ⚠️ insa-security-platform (41MB)
  ⚠️ insa-saas (37MB)

Recommendation: Clean unused servers to save space
```

## 📞 CONTACTS
```yaml
Email Alerts: w.aroca@insaing.com
SMTP: Gmail (w.aroca@insaing.com)
```

---
**Role:** Azure VM Monitoring + DevSecOps Automation
**Access:** ssh 100.100.101.1
**Sudo:** [REDACTED]***
**Version:** 3.5 | Updated: October 11, 2025

## 🎯 QUICK LINKS
- DefectDojo SOC Docs: `~/devops/devsecops-automation/defectdojo/README.md`
- Container Orchestrator: `~/devops/container-orchestrator/README.md`
- Learning Database: `/var/lib/defectdojo/learning.db`
- Service Logs: `journalctl -u defectdojo-agent -f`
- always update docs git and keep claude code md light with paths and links to docs and git