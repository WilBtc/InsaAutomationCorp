# INSA CRM System - Architecture Documentation

## System Architecture

### Overview

The INSA CRM System is built on a **multi-agent AI architecture** using Claude Code agents orchestrated through FastAPI, with Model Context Protocol (MCP) servers providing seamless integration with backend systems.

---

## Core Components

### 1. FastAPI Orchestrator

**Purpose**: Central API gateway and agent coordinator

**Responsibilities**:
- REST API endpoints for external clients
- Background task queuing (Celery/RQ)
- Agent lifecycle management
- MCP server coordination
- Authentication & authorization
- Monitoring & logging

**Technology**: FastAPI 0.115+, Uvicorn, Pydantic

**Key Files**:
- `api/main.py` - Application entry point
- `api/core/config.py` - Configuration management
- `api/core/database.py` - Database connection pooling
- `api/core/mcp_manager.py` - MCP server manager

---

### 2. AI Agent System

**Purpose**: Intelligent automation of CRM workflows

#### Agent Types:

**a) Lead Qualification Agent** (MVP ✅)
- Analyzes incoming leads
- Scores based on 5 criteria (budget, timeline, complexity, authority, fit)
- Recommends actions (immediate contact, demo, nurture, disqualify)
- Location: `agents/lead_qualification_agent.py`

**b) Quote Generation Agent** (Phase 2)
- Analyzes customer requirements
- Searches parts database (InvenTree)
- Calculates materials + labor costs
- Generates quote PDF
- Location: `agents/quote_generation_agent.py` (future)

**c) Security Assessment Agent** (Phase 3)
- Performs safe OT network scans
- Checks IEC 62443 compliance
- Risk assessment & prioritization
- Generates security reports
- Location: `agents/security_assessment_agent.py` (future)

**d) Proposal Writing Agent** (Phase 4)
- Multi-section technical proposals
- Auto-generates architecture diagrams
- Compliance documentation
- Location: `agents/proposal_writing_agent.py` (future)

**e) Compliance Tracking Agent** (Phase 4)
- Tracks project compliance requirements
- Automated evidence collection
- Audit trail management
- Location: `agents/compliance_tracking_agent.py` (future)

#### Agent Execution Flow:

```
1. API Request → FastAPI Endpoint
2. Validate Input → Queue Background Task
3. Spawn Agent → Load System Prompt
4. Agent Execution:
   a. Query MCP tools (ERPNext, PostgreSQL, etc.)
   b. Analyze data using Claude Code
   c. Generate structured output
   d. Call MCP tools to save results
5. Log Execution → PostgreSQL audit trail
6. Return Results → API response
```

---

### 3. MCP Server Layer

**Purpose**: Unified interface to backend systems

#### MCP Servers:

**a) ERPNext CRM MCP** (Configured ✅)
- Path: Configured in ~/.mcp.json
- Tools: 8+ tools (list_leads, create_lead, update_lead, etc.)
- Status: Active

**b) PostgreSQL MCP** (Pending)
- Direct SQL access for agent execution logs
- Tools: save_agent_execution, get_customer_history, query_lead_scores
- Status: Pending implementation

**c) Security Tools MCP** (Pending)
- Safe OT network scanning (Nmap)
- IEC 62443 compliance checks
- Vulnerability assessment
- Status: Pending implementation

**d) InvenTree MCP** (Future)
- BOM management
- Parts pricing
- Supplier integration
- Status: Not installed

**e) Qdrant Vector DB MCP** (Future)
- Document embeddings (IEC 62443 standards, datasheets)
- RAG for proposals
- Similar quote search
- Status: Not configured

**f) FreeCAD Automation MCP** (Future)
- P&ID diagram generation
- ISA symbol libraries
- DXF export
- Status: Future

#### MCP Communication:

```
Agent ←→ MCP Server ←→ Backend System

Example: Lead Qualification
1. Agent calls: mcp__erpnext__get_lead(lead_id)
2. MCP server fetches from ERPNext API
3. Returns structured JSON to agent
4. Agent analyzes data
5. Agent calls: mcp__erpnext__update_lead(lead_id, score)
6. MCP server updates ERPNext
```

---

### 4. Database Layer

#### PostgreSQL 16+

**Purpose**: Agent execution logs, lead scores, audit trail

**Tables**:

**agent_executions**
- Tracks all agent runs
- Columns: id, agent_type, status, input_data, output_data, tokens_used, cost, timestamps
- Indexes: agent_type, status, customer_id, lead_id

**lead_scores**
- AI-generated lead qualifications
- Columns: lead_id, qualification_score, priority, recommended_action, reasoning, factor_scores
- Indexes: lead_id (unique), priority

**Future tables**:
- quotes
- security_assessments
- proposals
- compliance_tracking

#### ERPNext Database

**Purpose**: Core CRM data (customers, leads, opportunities, projects)

**Access**: Via ERPNext MCP server (API-based)

**Custom DocTypes** (to be created):
- Lead Score (AI qualification data)
- Automation Requirements (technical specs)
- OT Asset Inventory (security assessments)
- Cybersecurity Assessment (IEC 62443 compliance)

#### Redis 7.4+

**Purpose**: Task queues, caching, session storage

**Usage**:
- Celery/RQ backend for background tasks
- API response caching
- Rate limiting
- Pub/sub messaging between agents

---

### 5. External Services

#### Claude Code

**Purpose**: AI agent execution engine

**Integration**: Via Claude CLI (no API key needed)

**Models**:
- **Haiku**: Fast, cheap ($0.005/task) - Simple lead qualification
- **Sonnet 4.5**: Balanced ($0.10-0.20/task) - Quote generation, security assessments
- **Opus**: Expensive ($1.50/task) - Complex technical design (rare)

**Prompt Caching**: 90% cost savings on large contexts (IEC 62443 standards)

#### InvenTree (Future)

**Purpose**: BOM management, parts database, pricing

**Integration**: REST API + MCP server

**Data**:
- PLCs, HMIs, sensors, network equipment
- Vendor pricing
- BOM templates for common projects

#### FreeCAD (Future)

**Purpose**: P&ID and electrical schematic automation

**Integration**: Python scripting API

**Output**: DXF files for proposals

---

## Data Flow Diagrams

### Lead Qualification Flow

```
┌─────────────┐
│   ERPNext   │ New Lead Created
│     CRM     │─────────────────┐
└─────────────┘                 │
                                ▼
                        ┌───────────────┐
                        │   FastAPI     │
                        │  POST /leads/ │
                        │  qualify/{id} │
                        └───────┬───────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  Background Task      │
                    │  Queue (Redis)        │
                    └───────────┬───────────┘
                                │
                                ▼
                ┌───────────────────────────────┐
                │ Lead Qualification Agent      │
                │ (Claude Sonnet 4.5)           │
                │                               │
                │ 1. Fetch lead data (MCP)      │
                │ 2. Analyze requirements       │
                │ 3. Score on 5 criteria        │
                │ 4. Generate reasoning         │
                │ 5. Recommend action           │
                └───────────┬───────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
        ┌───────────────┐      ┌───────────────┐
        │  PostgreSQL   │      │   ERPNext     │
        │ (lead_scores) │      │ (update lead) │
        └───────────────┘      └───────────────┘

                            ▼
                    ┌───────────────┐
                    │ Email Alert   │
                    │ (if IMMEDIATE)│
                    └───────────────┘
```

---

## Security Architecture

### Network Segmentation (On-Premise Deployment)

```
[Corporate Network] (Enterprise Zone)
        ↓ Firewall (DMZ allow: 80/443)
[Application DMZ] (Load Balancer, FastAPI)
        ↓ Firewall (Agent Zone allow: internal APIs)
[Agent Execution Zone] (Claude Agents, MCP Servers, Qdrant)
        ↓ Firewall with Egress Filtering (Data Zone NO INTERNET)
[Data Zone] (PostgreSQL, Redis, File Storage)
```

### Authentication & Authorization

- OAuth 2.1 with MFA (Phase 5)
- JWT tokens (RS256 algorithm)
- RBAC for agents:
  - Agent type → Allowed MCP tools
  - Data access restrictions
  - Approval required for sensitive operations

### Audit Trail

All agent executions logged to PostgreSQL:
- Input data (sanitized)
- Output data
- MCP tools called
- Tokens used & estimated cost
- Execution duration
- User context (who triggered the agent)

---

## Scalability & Performance

### Horizontal Scaling

- FastAPI: Multiple Uvicorn workers
- Agents: Parallel execution (configurable max concurrency)
- Database: Read replicas for reporting
- Redis: Sentinel for high availability

### Performance Targets

- Lead qualification: <5 seconds
- Quote generation: <10 minutes
- Security assessment: <2 hours
- Proposal generation: <30 minutes
- API response time: <200ms (excluding agent execution)

### Cost Optimization

**Intelligent Model Routing**:
- Simple tasks → Haiku (cheap)
- Complex reasoning → Sonnet (balanced)
- Critical accuracy → Opus (rare, expensive)

**Prompt Caching**:
- IEC 62443 standards (200K tokens) cached for 24 hours
- 90% cost reduction on repeated contexts

**Batch Processing**:
- Queue lead qualifications in batches
- Process during off-peak hours (lower costs)

---

## Monitoring & Observability

### Metrics (Prometheus)

- Agent executions per minute
- Success/failure rates by agent type
- Average execution duration
- Token usage & costs
- MCP server response times
- Database query performance

### Logging (Structlog)

- JSON-formatted logs
- Correlation IDs across agent execution
- Error tracking with stack traces
- Integration with ELK stack

### Alerting

- Agent failure rate >5%
- Database connection pool exhaustion
- MCP server unavailable
- Cost spike (>$10/hour)

---

## Deployment Architecture

### Development (iac1)

- Single server deployment
- SQLite for testing (optional)
- Local MCP servers
- Direct Claude Code CLI integration

### Production (Kubernetes)

```yaml
Namespaces:
  - insa-crm-api (FastAPI pods)
  - insa-crm-agents (agent execution pods)
  - insa-crm-mcp (MCP server pods)
  - insa-crm-data (PostgreSQL, Redis)

Services:
  - LoadBalancer (Nginx Ingress)
  - FastAPI (3 replicas)
  - Agent Workers (5 replicas, auto-scale)
  - PostgreSQL (StatefulSet, persistent volume)
  - Redis (StatefulSet)
```

---

## Technology Decisions & Rationale

### Why FastAPI?
- Async/await support (critical for agents)
- Automatic OpenAPI documentation
- Pydantic validation
- High performance (comparable to Node.js)
- Python ecosystem for AI/ML

### Why Claude Code?
- No API key management (uses your subscription)
- Multi-agent coordination built-in
- MCP tool integration
- Superior reasoning for complex industrial automation

### Why MCP Architecture?
- Unified interface to diverse systems
- Tool discovery and validation
- Automatic schema generation
- Security controls (tool-level permissions)
- Future-proof (new integrations easy to add)

### Why PostgreSQL over MongoDB?
- ACID compliance (critical for CRM)
- Complex queries (joins, aggregations)
- pgvector extension for embeddings
- Mature ecosystem
- Better for structured CRM data

### Why ERPNext over Custom CRM?
- Industrial-grade CRM features out-of-box
- Customizable DocTypes
- Active community
- Cost-effective (open-source)
- Already familiar to INSA team

---

## Future Enhancements

### Q2 2025
- Mobile app (React Native)
- Voice interface for agents (Whisper + TTS)
- Real-time collaboration (WebSockets)

### Q3 2025
- Multi-tenant SaaS version
- White-label for partners
- Marketplace for agent templates

### Q4 2025
- Computer vision for P&ID parsing (OCR)
- Predictive analytics (ML models)
- IoT integration (ThingsBoard data in quotes)

---

**Document Version**: 1.0
**Last Updated**: October 17, 2025
**Maintained By**: INSA Automation Corp
