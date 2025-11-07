# INSA CRM Platform
**AI-Powered Industrial Automation CRM Ecosystem**

**Version:** 2.1.0 (Multi-Regional Operations)
**Date:** October 23, 2025
**Status:** ✅ PRODUCTION READY
**Server:** iac1 (100.100.101.1)

---

## 🎯 Overview

Complete, unified CRM platform for **INSA Automation Corp** combining AI-powered lead qualification, sales management, marketing automation, workflow orchestration, and inventory management.

### Zero-Touch Customer Journey
```
Lead Capture → AI Qualification → Marketing Nurture → Sales Conversion →
Project Execution → Invoice Generation → Customer Success → Repeat Sales
```

**All automated. All integrated. All AI-powered.**

### 🌎 Geographic Coverage

**Multi-Regional Operations:** Colombia 🇨🇴 + United States 🇺🇸

- **Colombia:** RETIE/NTC compliance, 220V/440V systems, Spanish operations
- **United States:** NEC/NFPA compliance, 480V systems, English operations
- **Bilingual Support:** All technical documentation in Spanish & English
- **Multi-Currency:** COP (Colombian Peso) + USD (US Dollar)
- **Regional Expertise:** Local vendors, regulations, business practices

See: **`docs/COLOMBIA_OPERATIONS_REFERENCE.md`** for comprehensive Colombia operations guide.

---

## 📁 Directory Structure

```
insa-crm-platform/                         # 🎯 YOU ARE HERE
├── README.md                              # This file
├── QUICKSTART.md                          # Get started in 5 minutes
│
├── core/                                  # AI CRM Core (151MB)
│   ├── api/                               # FastAPI REST API
│   ├── agents/                            # AI lead qualification agent
│   ├── knowledge/                         # RAG knowledge base
│   ├── docs/                              # API documentation
│   ├── venv/                              # Python environment
│   ├── .env                               # Configuration
│   └── README.md                          # Core system docs
│
├── mcp-servers/                           # MCP Integrations (161MB)
│   ├── erpnext-crm/                       # ERPNext (33 tools) ✅
│   ├── inventree-crm/                     # InvenTree (5 tools) ✅
│   ├── mautic-admin/                      # Mautic (27 tools) ✅
│   └── n8n-admin/                         # n8n (23 tools) ✅
│
├── automation/                            # Workflows & Templates
│   ├── workflows/                         # n8n workflow JSONs (6 workflows)
│   └── templates/                         # Mautic email templates (7 templates)
│
├── projects/                              # Customer Projects (66MB)
│   ├── customers/                         # Customer project files
│   │   └── INSAGTEC-6598/                # Reference project (63 files)
│   └── templates/                         # Generators
│       └── pid-generator/                 # P&ID automation scripts
│
├── legacy/                                # Archived/Deprecated (12MB)
│   └── insa-erp/                         # Old ERP files
│
└── docs/                                  # Documentation Hub
    ├── architecture/                      # System architecture
    ├── deployment/                        # Deployment guides
    └── guides/                            # User guides
```

**Total Size:** ~390MB

---

## 🚀 Quick Start

### 1. View System Status
```bash
cd ~/insa-crm-platform
tree -L 2
```

### 2. Start INSA CRM Core
```bash
cd ~/insa-crm-platform/core
source venv/bin/activate
python api/main.py
# API: http://100.100.101.1:8003
```

### 3. Test MCP Servers
All MCP servers are configured in `~/.mcp.json` and ready to use via Claude Code.

Ask Claude Code:
- "List my CRM leads" (ERPNext)
- "Show inventory parts" (InvenTree)
- "Get Mautic contacts" (Mautic)
- "List n8n workflows" (n8n)

---

## 🛠️ Components

### 1. INSA CRM Core (`core/`)
- **Purpose:** AI-powered lead qualification & industrial automation expertise
- **Technology:** FastAPI + PostgreSQL + Claude AI
- **API:** http://100.100.101.1:8003
- **Features:**
  - 0-100 lead scoring (5 criteria)
  - Priority classification (IMMEDIATE/HIGH/MEDIUM/LOW)
  - Automatic action recommendations
  - Multi-agent architecture ready
- **Skill Package:** Complete CRM capabilities (see `INSA_CRM_SKILL.md`)
  - Customer/Account Management (multi-currency, bilingual)
  - Project Management (P&ID, electrical design, energy optimization)
  - Technical Documentation (compliance: IEC 62443, RETIE, NERC CIP)
  - Equipment Library (PLCs, SCADA, VFDs, Industrial Networking)
  - Geographic Coverage: Colombia 🇨🇴 + United States 🇺🇸

### 2. ERPNext CRM MCP (`mcp-servers/erpnext-crm/`)
- **Purpose:** Complete sales cycle automation
- **Tools:** 33 (Phase 3b complete)
- **Coverage:**
  - Lead → Opportunity → Quotation → Sales Order
  - Project Management → Delivery Notes → Invoices → Payments
  - Customer Details + Product Catalog
- **Web UI:** http://100.100.101.1:9000

### 3. InvenTree MCP (`mcp-servers/inventree-crm/`)
- **Purpose:** Inventory & BOM management
- **Tools:** 5 (Phase 2 complete)
- **Features:**
  - Parts database
  - BOM creation & pricing
  - Customer equipment tracking
- **Web UI:** http://100.100.101.1:9600

### 4. Mautic Marketing (`mcp-servers/mautic-admin/`)
- **Purpose:** Marketing automation
- **Tools:** 27 (Phase 4 complete)
- **Features:**
  - Email campaigns (every 5 min)
  - Contact segmentation (every 15 min)
  - Landing pages, forms, webhooks
  - 13 automated cron jobs
- **Web UI:** http://100.100.101.1:9700
- **Database:** MariaDB 11.6 (157 tables)

### 5. n8n Workflows (`mcp-servers/n8n-admin/`)
- **Purpose:** Workflow automation & integration
- **Tools:** 23 (Phase 6 complete)
- **Workflows:** 5 deployed
  - New Lead Sync (ERPNext → Mautic)
  - Lead Score Update (Mautic → ERPNext)
  - Opportunity Conversion (ERPNext → Mautic)
  - Event Registration (Mautic → ERPNext)
  - Unsubscribe Sync (Mautic → ERPNext)
- **Web UI:** http://100.100.101.1:5678
- **Resource Limits:** 1GB RAM, 1 CPU core

---

## 📊 Integration Architecture

```
┌─────────────────────────────────────────────────────────┐
│         Claude Code (AI Orchestrator)                   │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│
│  │ ERPNext  │  │ InvenTree│  │  Mautic  │  │   n8n   ││
│  │   MCP    │  │   MCP    │  │   MCP    │  │   MCP   ││
│  │ 33 tools │  │ 5 tools  │  │ 27 tools │  │ 23 tools││
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘│
│       │             │              │              │     │
│       └─────────────┴──────────────┴──────────────┘     │
│                           │                              │
│                  ┌────────▼────────┐                    │
│                  │  INSA CRM Core  │                    │
│                  │ (AI Lead Qual)  │                    │
│                  └─────────────────┘                    │
└─────────────────────────────────────────────────────────┘
```

---

## 📚 Documentation

### Getting Started
- **QUICKSTART.md** - Get started in 5 minutes
- **INSA_CRM_SKILL.md** - Complete CRM skill package for Claude Code agents ⭐ NEW
- **core/README.md** - INSA CRM Core documentation
- **mcp-servers/*/README.md** - Individual MCP server guides

### Architecture
- **docs/architecture/INSA_CRM_COMPLETE_ARCHITECTURE_2025.md** - Complete system design
- **docs/deployment/PHASE*.md** - Phased deployment history

### Guides
- **docs/guides/MAUTIC_MCP_COMPLETE_GUIDE.md** - Mautic admin guide (48KB)
- **docs/guides/INSA_PROJECT_WORKFLOW_RAG_MEMORY.md** - Project workflow guide (900+ lines)
- **docs/guides/RESOURCE_PROTECTION_COMPLETE.md** - Resource protection strategies

### Regional Operations
- **docs/COLOMBIA_OPERATIONS_REFERENCE.md** - Complete Colombia operations guide ⭐ NEW
  - RETIE/NTC regulations and compliance
  - Voltage systems (220V/440V vs US 480V)
  - Equipment derating for altitude (Bogotá: 2,640m)
  - Local vendors, business practices, project checklists
  - Bilingual technical terminology (1,000+ lines)

---

## 🔧 Configuration

### MCP Servers (~/.mcp.json)
All MCP servers are configured and point to this directory:
```json
{
  "erpnext-crm": {
    "command": "/home/wil/insa-crm-platform/mcp-servers/erpnext-crm/venv/bin/python",
    "args": ["/home/wil/insa-crm-platform/mcp-servers/erpnext-crm/server.py"]
  }
  // ... additional MCP servers (inventree-crm, mautic-admin, n8n-admin, bitrix24-api, github, etc.)
}
```

### Environment Variables
Each component has its own `.env` file:
- `core/.env` - INSA CRM Core config
- `mcp-servers/*/venv/` - MCP server configs

---

## 🎯 Common Tasks

### View System Overview
```bash
cd ~/insa-crm-platform
du -sh */
```

### Start All Services
```bash
# INSA CRM Core
cd ~/insa-crm-platform/core && source venv/bin/activate && python api/main.py &

# MCP servers are auto-started by Claude Code
```

### Check Workflows
```bash
ls ~/insa-crm-platform/automation/workflows/
```

### Access Customer Projects
```bash
cd ~/insa-crm-platform/projects/customers/INSAGTEC-6598/
```

### Run P&ID Generator
```bash
cd ~/insa-crm-platform/projects/templates/pid-generator/
python separador_trifasico.py
```

---

## 🔐 Security & Compliance

- **IEC 62443 Compliance:** Automated via DefectDojo (separate server)
- **Authentication:** Each platform has its own credentials
- **Network:** Internal Tailscale VPN (100.100.101.1)
- **Backups:** Automated daily backups
- **Audit Trail:** All operations logged

---

## 📈 Performance Metrics

| Component | Tools | Status | Resource Usage |
|-----------|-------|--------|----------------|
| ERPNext CRM | 33 | ✅ PRODUCTION | ~40MB |
| InvenTree | 5 | ✅ PRODUCTION | ~40MB |
| Mautic | 27 | ✅ PRODUCTION | ~40MB, 13 crons |
| n8n | 23 | ✅ PRODUCTION | 1GB RAM, 1 CPU |
| INSA Core | 1 agent | ✅ PRODUCTION | ~150MB |

**Total:** 88 automated tools, ~390MB disk space

---

## 🛡️ Backup & Recovery

### Backup Location
Full backup created on consolidation:
```bash
~/insa-crm-backup-20251018.tar.gz (139MB)
```

### Restore from Backup
```bash
cd ~
tar xzf insa-crm-backup-20251018.tar.gz
# Restore to original locations if needed
```

---

## 🚀 Future Enhancements

- [ ] Phase 7: AI Quote Generation Agent
- [ ] Phase 8: Security Assessment Agent (IEC 62443)
- [ ] Phase 9: Proposal Writing Agent
- [ ] Phase 10: Full multi-agent orchestration via Temporal

---

## 📞 Support

**Project Owner:** INSA Automation Corp
**Email:** w.aroca@insaing.com
**Server:** iac1 (100.100.101.1)
**Documentation:** `~/insa-crm-platform/docs/`

---

## 📜 License

Proprietary - INSA Automation Corp © 2025

---

## 🎉 Changelog

### Version 2.1.0 (October 23, 2025) - Multi-Regional Operations
- ✅ Added comprehensive Colombia Operations Reference Guide
- ✅ Created INSA CRM Skill package for Claude Code agents
- ✅ Multi-regional support: Colombia 🇨🇴 + United States 🇺🇸
- ✅ RETIE/NTC compliance documentation
- ✅ Bilingual operations (Spanish/English)
- ✅ Multi-currency support (COP/USD)
- ✅ Equipment library with IEC/NEMA standards
- ✅ Regional vendor networks and business practices

### Version 2.0.0 (October 18, 2025) - Consolidated Platform
- ✅ Unified all CRM components into single directory
- ✅ Organized by function (core, mcp-servers, automation, projects)
- ✅ Updated all MCP configurations
- ✅ Centralized documentation
- ✅ Tested all components (100% working)
- ✅ Created comprehensive README
- ✅ Full backup created

### Version 1.0.0 (October 17, 2025) - Initial Deployment
- ✅ Phase 3: ERPNext full sales cycle (33 tools)
- ✅ Phase 4: Mautic marketing automation (27 tools)
- ✅ Phase 5: n8n workflow integration
- ✅ Phase 6: Complete CLI control

---

**Built with Claude Code for Industrial Automation Engineering**

🤖 Made by INSA Automation Corp
