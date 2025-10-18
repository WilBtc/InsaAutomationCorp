# INSA CRM System

**AI-Powered Customer Relationship Management for Industrial Automation Engineering**

Built for **INSA Automation Corp** - Industrial Automation | Energy Optimization | Industrial Cybersecurity

---

## 🚀 Overview

This is a next-generation CRM system powered by **Claude Code AI agents** and integrated with modern open-source tools. It automates lead qualification, quote generation, security assessments, and proposal writing for industrial automation projects.

### Key Features

- **AI Lead Qualification**: Automatic scoring of leads based on budget, timeline, technical complexity, decision authority, and industry fit
- **Multi-Agent Architecture**: Coordinated AI agents for different CRM workflows
- **MCP Integration**: Model Context Protocol servers for ERPNext, PostgreSQL, Security Tools, InvenTree, and more
- **Zero API Costs**: Uses Claude Code subscription (no separate API keys needed for agents)
- **Industrial Focus**: Built specifically for PLC programming, SCADA, IEC 62443 compliance, and OT cybersecurity

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│  INSA CRM SYSTEM (iac1 - 100.100.101.1)                │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  [FastAPI Orchestrator]                                  │
│  ├─ REST API (port 8000)                                │
│  ├─ Background task queues                              │
│  └─ Agent coordination                                   │
│                                                           │
│  [AI Agents - Claude Code]                              │
│  ├─ Lead Qualification Agent (MVP ✅)                   │
│  ├─ Quote Generation Agent (Phase 2)                    │
│  ├─ Security Assessment Agent (Phase 3)                 │
│  ├─ Proposal Writing Agent (Phase 4)                    │
│  └─ Compliance Tracking Agent (Phase 4)                 │
│                                                           │
│  [MCP Servers]                                           │
│  ├─ ERPNext CRM (existing - configured)                 │
│  ├─ PostgreSQL (agent execution logs)                   │
│  ├─ Security Tools (Nmap, IEC 62443 checks)             │
│  ├─ InvenTree (BOM, parts, pricing) [future]            │
│  ├─ Qdrant (vector DB for RAG) [future]                 │
│  └─ FreeCAD (P&ID automation) [future]                  │
│                                                           │
│  [Databases]                                             │
│  ├─ PostgreSQL 16 (agent logs, lead scores)             │
│  ├─ Redis 7.4 (task queues, caching)                    │
│  └─ ERPNext DB (customers, leads, projects)             │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **AI/Agents** | Claude Code | Latest | Multi-agent orchestration |
| **CRM Platform** | ERPNext | 15.x | Core CRM, DocTypes |
| **API Framework** | FastAPI | 0.115+ | REST API, orchestrator |
| **Database** | PostgreSQL | 16+ | Relational data |
| **Cache/Queue** | Redis | 7.4+ | Task queues, sessions |
| **Inventory** | InvenTree | 0.16+ | BOM, parts, pricing (future) |
| **CAD** | FreeCAD | 0.21+ | P&ID automation (future) |
| **Vector DB** | Qdrant | 1.12+ | RAG, embeddings (future) |

---

## 🚦 Current Status

**Phase 0: Foundation (COMPLETED ✅)**

- ✅ Project structure created
- ✅ FastAPI application skeleton
- ✅ Database models (AgentExecution, LeadScore)
- ✅ MCP manager for multi-server coordination
- ✅ API endpoints (leads, agents, MCP status)
- ✅ Lead Qualification Agent (MVP)
- ✅ Comprehensive documentation

**Next Steps:**

- Install dependencies
- Create PostgreSQL database
- Configure ERPNext connection
- Deploy FastAPI application
- Test Lead Qualification Agent
- Begin Phase 2 (Quote Generation)

---

## 📋 Installation Guide

### Prerequisites

- Ubuntu 24.04 LTS (or similar)
- Python 3.11+
- PostgreSQL 16+
- Redis 7.4+
- ERPNext 15.x (already installed)
- Docker (optional, for containerized deployment)

### Step 1: Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip \
    postgresql-client redis-tools git build-essential
```

### Step 2: Set Up Python Environment

```bash
cd ~/insa-crm-system

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Create PostgreSQL Database

```bash
# Create database (adjust credentials as needed)
sudo -u postgres psql <<EOF
CREATE DATABASE insa_crm;
CREATE USER insa_crm_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE insa_crm TO insa_crm_user;
\c insa_crm
CREATE EXTENSION IF NOT EXISTS pg_trgm;
EOF
```

### Step 4: Configure Environment

```bash
# Copy example config
cp .env.example .env

# Edit with your actual values
nano .env
```

**Required settings:**
- `DATABASE_URL`: PostgreSQL connection string
- `ERPNEXT_API_URL`: Your ERPNext instance URL
- `ERPNEXT_API_KEY`: API key from ERPNext
- `SECRET_KEY`: Generate with `openssl rand -hex 32`

### Step 5: Initialize Database

```bash
# Run migrations (creates tables)
source venv/bin/activate
cd api
python -c "import asyncio; from core.database import init_db; asyncio.run(init_db())"
```

### Step 6: Start Application

```bash
# Development mode
python api/main.py

# Production mode (using Uvicorn)
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Step 7: Verify Installation

```bash
# Health check
curl http://localhost:8000/health

# MCP status
curl http://localhost:8000/api/v1/mcp/status

# API docs
xdg-open http://localhost:8000/api/docs
```

---

## 🧪 Testing the Lead Qualification Agent

### Option 1: Via API (Recommended)

```bash
curl -X POST "http://localhost:8000/api/v1/leads/qualify/LEAD-2025-001" \
  -H "Content-Type: application/json"

# Expected response:
# {
#   "status": "processing",
#   "lead_id": "LEAD-2025-001",
#   "message": "Lead qualification in progress"
# }

# Check results (after a few seconds)
curl "http://localhost:8000/api/v1/leads/scores/LEAD-2025-001"
```

### Option 2: Python Script

```python
import asyncio
from agents.lead_qualification_agent import lead_qualification_agent

async def test_qualification():
    lead_data = {
        "name": "LEAD-TEST-001",
        "lead_name": "Jane Doe",
        "company_name": "ABC Manufacturing",
        "designation": "VP of Operations",
        "industry": "Manufacturing",
        "notes": "Need IEC 62443 compliance. Budget $200K."
    }

    result = await lead_qualification_agent.qualify_lead(lead_data)
    print(f"Score: {result['qualification_score']}")
    print(f"Priority: {result['priority']}")
    print(f"Action: {result['recommended_action']}")
    print(f"Reasoning: {result['reasoning']}")

asyncio.run(test_qualification())
```

---

## 📊 API Endpoints

### Lead Management

- **POST** `/api/v1/leads/qualify/{lead_id}` - Trigger AI qualification
- **GET** `/api/v1/leads/scores` - List all lead scores
- **GET** `/api/v1/leads/scores/{lead_id}` - Get specific lead score

### Agent Management

- **GET** `/api/v1/agents/executions` - List agent execution history
- **GET** `/api/v1/agents/stats` - Agent statistics (tokens, costs)

### MCP Status

- **GET** `/api/v1/mcp/status` - MCP server status
- **GET** `/api/v1/mcp/servers/{server_name}/tools` - List available tools

### System

- **GET** `/health` - Health check
- **GET** `/metrics` - Prometheus metrics
- **GET** `/api/docs` - Interactive API documentation (Swagger)

---

## 🤖 Agent System

### Lead Qualification Agent (MVP ✅)

**Purpose**: Automatically score and prioritize incoming leads

**Scoring Criteria:**
- Budget Score (0-25 points)
- Timeline Score (0-25 points)
- Technical Complexity Score (0-25 points)
- Decision Authority Score (0-15 points)
- Industry Fit Score (0-10 points)

**Priority Levels:**
- **IMMEDIATE** (80-100): Contact within 24 hours
- **HIGH** (60-79): Schedule demo/meeting
- **MEDIUM** (40-59): Send proposal
- **LOW** (20-39): Nurture campaign
- **DISQUALIFY** (0-19): Poor fit

**Example Output:**
```json
{
  "qualification_score": 92,
  "priority": "IMMEDIATE",
  "recommended_action": "IMMEDIATE_CONTACT",
  "reasoning": "High-value IEC 62443 project with clear budget...",
  "confidence_level": 0.92,
  "key_factors": [
    "IEC 62443 compliance required",
    "$150K budget confirmed",
    "VP-level contact"
  ],
  "next_steps": [
    "Contact within 24 hours",
    "Prepare IEC 62443 overview",
    "Involve cybersecurity team lead"
  ]
}
```

---

## 🔧 Configuration

### Environment Variables

See `.env.example` for all available configuration options.

**Critical settings:**
- `ENABLE_AGENT_EXECUTION`: Enable/disable AI agent execution
- `MAX_CONCURRENT_AGENTS`: Limit parallel agent executions (default: 5)
- `DEFAULT_AGENT_MODEL`: Claude model for agents (default: Sonnet 4.5)
- `ENABLE_SECURITY_SCANS`: Require approval for security scans (default: false)

### MCP Servers

MCP servers are configured in the MCP manager (`api/core/mcp_manager.py`).

**Available servers:**
- `erpnext`: ERPNext CRM integration (configured ✅)
- `postgres`: PostgreSQL direct access (pending)
- `security`: Security tools (pending)
- `inventree`: InvenTree BOM/parts (not installed)
- `qdrant`: Qdrant vector DB (not configured)
- `freecad`: FreeCAD automation (future)

---

## 📖 Development Roadmap

### ✅ Phase 0: Foundation (COMPLETED)
- Project structure
- FastAPI skeleton
- Database models
- MCP manager
- Lead Qualification Agent MVP
- API endpoints
- Documentation

### Phase 1: Lead Management (Weeks 5-8)
- [ ] ERPNext custom DocTypes for industrial automation
- [ ] Real-time ERPNext integration via MCP
- [ ] Email notifications for high-priority leads
- [ ] Dashboard for lead qualification metrics
- [ ] Human override/feedback system

### Phase 2: Quote & Contact Management (Weeks 9-16)
- [ ] InvenTree installation and BOM setup
- [ ] Quote Generation Agent
- [ ] Parts database integration
- [ ] Automated quote PDF generation
- [ ] Qdrant vector DB for similar quote search

### Phase 3: Technical & Security Agents (Weeks 17-24)
- [ ] Security Assessment Agent
- [ ] IEC 62443 compliance checking
- [ ] OT network scanning (safe mode)
- [ ] FreeCAD P&ID generation
- [ ] Electrical schematic automation (ezdxf)

### Phase 4: Proposal & Compliance (Weeks 25-30)
- [ ] Proposal Writing Agent
- [ ] Multi-section proposal templates
- [ ] Compliance Tracking Agent
- [ ] Temporal workflow orchestration
- [ ] Multi-agent coordination

### Phase 5: Production Hardening (Weeks 31-36)
- [ ] Security audit & penetration testing
- [ ] OAuth 2.1 with MFA
- [ ] RBAC for agents
- [ ] Kubernetes deployment
- [ ] Monitoring & observability (Prometheus, Grafana, AgentOps)
- [ ] Cost optimization & model routing

---

## 🔐 Security Considerations

- All agent executions are logged to PostgreSQL audit trail
- Sensitive data is encrypted at rest (AES-256)
- API uses TLS 1.3 in production
- Network segmentation for data zone (no internet access)
- Security scans require explicit approval (configurable)
- RBAC controls which agents can access which tools

---

## 📞 Support & Contact

**Project Owner**: INSA Automation Corp
**Email**: w.aroca@insaing.com
**Server**: iac1 (100.100.101.1)
**Documentation**: `~/insa-crm-system/README.md`

---

## 📜 License

Proprietary - INSA Automation Corp © 2025

---

## 🎯 Quick Commands

```bash
# Start application
cd ~/insa-crm-system
source venv/bin/activate
python api/main.py

# Run tests
pytest tests/

# Check logs
tail -f logs/crm_system.log

# Database migrations
alembic upgrade head

# View API docs
xdg-open http://localhost:8000/api/docs

# Agent statistics
curl http://localhost:8000/api/v1/agents/stats

# MCP status
curl http://localhost:8000/api/v1/mcp/status
```

---

**Generated**: October 17, 2025
**Version**: 0.1.0 (Phase 0 MVP)
**Status**: Foundation Complete ✅

Made with Claude Code for Industrial Automation Engineering
