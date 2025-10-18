# INSA CRM System - Complete Implementation Roadmap

**36-Week Development Plan: From Foundation to Production**

---

## Executive Summary

This roadmap details the complete implementation of the INSA CRM System, an AI-powered CRM for industrial automation engineering. The project is divided into 6 phases over 36 weeks, delivering working functionality at each milestone.

**Total Estimated Cost**: ~$2,000-5,000 (primarily infrastructure, all software is OSS)
**Team Size**: 1-2 developers (leveraging AI agents)
**Deployment**: On-premise (iac1 server) initially, Kubernetes in Phase 5

---

## ✅ PHASE 0: FOUNDATION (COMPLETED)

**Duration**: Weeks 1-4
**Status**: COMPLETED ✅
**Date Completed**: October 17, 2025

### Deliverables

✅ Project directory structure
✅ FastAPI application skeleton
✅ Database models (AgentExecution, LeadScore)
✅ MCP manager for multi-server coordination
✅ API endpoints (leads, agents, MCP status)
✅ Lead Qualification Agent (MVP)
✅ Comprehensive documentation (README, Architecture)

### Files Created

```
insa-crm-system/
├── api/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── mcp_manager.py
│   ├── models/
│   │   ├── agent_execution.py
│   │   └── lead_score.py
│   └── api/v1/
│       └── endpoints/
│           ├── leads.py
│           ├── agents.py
│           └── mcp_status.py
├── agents/
│   └── lead_qualification_agent.py
├── docs/
│   ├── ARCHITECTURE.md
│   └── IMPLEMENTATION_ROADMAP.md
├── requirements.txt
├── .env.example
└── README.md
```

### Next Steps

1. Install dependencies (`pip install -r requirements.txt`)
2. Create PostgreSQL database
3. Configure `.env` file
4. Test Lead Qualification Agent
5. Begin Phase 1

---

## PHASE 1: MVP - LEAD MANAGEMENT (Weeks 5-8)

**Goal**: Fully functional lead qualification system integrated with ERPNext

### Week 5: ERPNext Integration

**Tasks:**

1. **Create Custom DocTypes in ERPNext**
   - `Lead Score` (custom fields for AI data)
   - `Automation Requirements` (technical specifications)
   - `Industry Vertical` (select field with 10+ industries)
   - `Project Type` (automation/energy/cybersecurity)

2. **Extend ERPNext MCP Server**
   - Add custom field support to existing MCP tools
   - Implement `update_lead_custom_fields` tool
   - Add `get_lead_with_custom_data` tool
   - Test ERPNext API integration

3. **Update Lead Qualification Agent**
   - Replace simulated responses with real Claude Code SDK calls
   - Add ERPNext MCP tool calls
   - Implement error handling & retries

**Deliverables:**
- ERPNext custom DocTypes configured
- MCP server updated and tested
- Real-time lead data fetching working

---

### Week 6: Database & Agent Refinement

**Tasks:**

1. **PostgreSQL Schema Enhancements**
   - Add indexes for performance
   - Create views for reporting
   - Implement database migrations (Alembic)

2. **Agent Execution Tracking**
   - Log all agent runs to `agent_executions` table
   - Track token usage and costs
   - Implement correlation IDs for tracing

3. **Human Feedback Loop**
   - Create API endpoint for human override of scores
   - Track accuracy metrics (AI vs. human)
   - Implement learning from corrections

**Deliverables:**
- Complete database schema with migrations
- Agent execution audit trail working
- Human override functionality

---

### Week 7: Notifications & Dashboard

**Tasks:**

1. **Email Notifications**
   - High-priority lead alerts to sales team
   - Daily digest of new qualified leads
   - Use existing Postfix on iac1

2. **API Enhancements**
   - Webhook support for real-time ERPNext updates
   - Batch lead qualification endpoint
   - Export lead scores to CSV/Excel

3. **Metrics Dashboard** (Phase 1 of UI)
   - Simple web dashboard (React or Vue.js)
   - Lead qualification metrics
   - Agent performance stats

**Deliverables:**
- Email alerts configured and tested
- API webhooks implemented
- Basic metrics dashboard deployed

---

### Week 8: Testing & Optimization

**Tasks:**

1. **Unit Tests**
   - Test all API endpoints (pytest)
   - Test agent qualification logic
   - Test database operations

2. **Integration Tests**
   - End-to-end lead qualification flow
   - MCP server integration tests
   - ERPNext sync tests

3. **Performance Optimization**
   - Database query optimization
   - Agent execution time reduction
   - API response time tuning

**Deliverables:**
- 80%+ test coverage
- Performance benchmarks met (<5s qualification)
- Phase 1 deployment ready

### Phase 1 Success Criteria
- ✅ 100 leads qualified with >85% accuracy
- ✅ <5 second average qualification time
- ✅ Email alerts working reliably
- ✅ Dashboard deployed and accessible

---

## PHASE 2: QUOTE & CONTACT MANAGEMENT (Weeks 9-16)

**Goal**: AI-powered quote generation with BOM management

### Week 9-10: InvenTree Installation

**Tasks:**

1. **Deploy InvenTree**
   - Install InvenTree 0.16+ on iac1
   - Configure PostgreSQL backend
   - Set up Nginx reverse proxy
   - Create admin account and API token

2. **Initial Data Import**
   - Create part categories (PLCs, HMIs, Sensors, etc.)
   - Import 50-100 common parts with pricing
   - Set up supplier integrations (Siemens, Rockwell, etc.)
   - Create BOM templates for standard projects

3. **InvenTree MCP Server**
   - Implement MCP server: `~/mcp-servers/inventree/server.py`
   - Tools: `get_part`, `search_parts`, `get_bom_cost`, `create_bom`
   - Test API integration

**Deliverables:**
- InvenTree deployed and configured
- 100+ parts in database
- InvenTree MCP server operational

---

### Week 11-12: Quote Generation Agent

**Tasks:**

1. **Quote Generation Agent Development**
   - System prompt for quote generation
   - Multi-step workflow:
     1. Parse customer requirements
     2. Search InvenTree for parts
     3. Calculate material costs
     4. Estimate labor hours
     5. Apply markup (30-40%)
     6. Generate line items
   - Integration with ERPNext Quotation DocType

2. **Pricing Logic**
   - Labor rate calculator (varies by complexity)
   - Material markup by category
   - Volume discounts
   - Compliance cost adders (IEC 62443 = +15%)

3. **Quote PDF Generation**
   - Install Carbone.io and WeasyPrint
   - Create professional quote template
   - Generate PDFs with company branding
   - Include T&Cs, payment terms

**Deliverables:**
- Quote Generation Agent working
- PDF generation functional
- ERPNext quotations created automatically

---

### Week 13-14: Qdrant Vector Database

**Tasks:**

1. **Qdrant Installation** (on Azure VM 100.107.50.52)
   - Install Qdrant 1.12+
   - Configure persistent storage
   - Set up authentication

2. **Document Indexing**
   - Index IEC 62443 standards (PDF to chunks)
   - Index product datasheets (100+ PDFs)
   - Index past quotes (similarity search)
   - Use sentence-transformers for embeddings

3. **Qdrant MCP Server**
   - Implement RAG tools: `search_standards`, `find_similar_quotes`
   - Integration with Quote Generation Agent
   - Test embedding quality

**Deliverables:**
- Qdrant deployed with 1000+ embeddings
- RAG working for quote generation
- Similar quote search functional

---

### Week 15-16: Testing & Refinement

**Tasks:**

1. **Quote Accuracy Testing**
   - Generate 20 test quotes
   - Compare with manual quotes (±15% accuracy)
   - Refine pricing algorithms

2. **Customer History Integration**
   - Fetch past quotes for repeat customers
   - Preferred pricing based on history
   - Upsell/cross-sell recommendations

3. **API Enhancements**
   - Quote approval workflow
   - Quote versioning
   - PDF email delivery

**Deliverables:**
- 90%+ quote accuracy (within ±15% of manual)
- <10 min quote generation time
- Phase 2 production ready

### Phase 2 Success Criteria
- ✅ 50 quotes generated with acceptable accuracy
- ✅ <10 minute average quote time
- ✅ InvenTree BOM integration working
- ✅ PDF output professional quality

---

## PHASE 3: TECHNICAL & SECURITY AGENTS (Weeks 17-24)

**Goal**: Security assessments, compliance checking, technical diagram generation

### Week 17-18: Security Tools Setup

**Tasks:**

1. **Security Tools Installation**
   - Nmap (safe OT scanning parameters)
   - OpenVAS (vulnerability scanning)
   - IEC 62443 compliance checker (custom Python script)

2. **Security MCP Server**
   - Tools: `scan_network`, `check_compliance`, `assess_vulnerabilities`
   - Safe mode for OT devices (no aggressive scans)
   - Integration with DefectDojo (existing on iac1)

3. **ERPNext Security DocTypes**
   - `Cybersecurity Assessment`
   - `OT Asset Inventory`
   - `Security Finding`
   - `Compliance Tracking`

**Deliverables:**
- Security tools configured
- Security MCP server operational
- ERPNext security DocTypes created

---

### Week 19-20: Security Assessment Agent

**Tasks:**

1. **Agent Development**
   - Multi-phase assessment workflow:
     1. Asset discovery
     2. Network topology mapping
     3. Vulnerability scanning
     4. IEC 62443 compliance check
     5. Risk prioritization
     6. Remediation recommendations
   - Integration with DefectDojo for findings
   - Generate PDF security reports

2. **IEC 62443 Compliance Checker**
   - Check 7 Foundational Requirements (FRs)
   - Determine Security Level (SL1-SL4)
   - Gap analysis
   - Remediation roadmap

3. **Safety Considerations**
   - Require human approval for scans
   - Safe scan profiles for OT devices
   - Logging and audit trail

**Deliverables:**
- Security Assessment Agent working
- IEC 62443 compliance checks functional
- Integrated with DefectDojo

---

### Week 21-22: FreeCAD & P&ID Automation

**Tasks:**

1. **FreeCAD Setup**
   - Install FreeCAD 0.21+ system-wide
   - Create ISA symbol library (Python scripts)
   - Test Python scripting API

2. **FreeCAD MCP Server**
   - Tools: `generate_pid`, `add_component`, `export_dxf`
   - Component types: pumps, valves, sensors, tanks, etc.
   - ISA 5.1 symbol standards

3. **P&ID Generation Agent**
   - Parse text descriptions of processes
   - Generate P&IDs with correct symbols
   - Export to DXF for AutoCAD compatibility

**Deliverables:**
- FreeCAD automation working
- P&ID generated from text description
- DXF export functional

---

### Week 23-24: Electrical Schematics & Testing

**Tasks:**

1. **ezdxf Integration**
   - Install ezdxf Python library
   - Create electrical schematic templates
   - Component library (breakers, relays, motors, etc.)

2. **Schematic Generator**
   - Generate ladder logic diagrams
   - Panel wiring diagrams
   - Motor control circuits
   - Auto-wire numbering

3. **Phase 3 Integration Testing**
   - End-to-end security assessment flow
   - P&ID generation from project requirements
   - Electrical schematic generation

**Deliverables:**
- Electrical schematic automation working
- Phase 3 agents deployed
- Documentation updated

### Phase 3 Success Criteria
- ✅ Security assessments completed in <2 hours
- ✅ 90%+ vulnerability detection rate
- ✅ Usable P&ID generated from text description
- ✅ Electrical schematics correct and readable

---

## PHASE 4: PROPOSAL & COMPLIANCE (Weeks 25-30)

**Goal**: Automated proposal generation and compliance tracking

### Week 25-26: Proposal Templates

**Tasks:**

1. **Template Development**
   - Executive summary template
   - Technical approach template
   - System architecture diagram templates
   - Project timeline (Gantt chart)
   - Pricing & payment terms
   - References & case studies

2. **Carbone.io Templates**
   - DOCX templates with placeholders
   - PDF styling and branding
   - Multi-section assembly

3. **Proposal Writing Agent**
   - Multi-agent coordination:
     - Technical writer agent
     - Diagram generator agent
     - Pricing analyst agent
   - Sequential workflow execution
   - Final proposal assembly

**Deliverables:**
- Professional proposal templates
- Proposal Writing Agent operational
- 20-page proposals generated in <30 min

---

### Week 27-28: Compliance Tracking

**Tasks:**

1. **Compliance DocTypes**
   - `Compliance Tracking` (ERPNext custom DocType)
   - `Evidence` (file attachments)
   - `Audit Log` (change tracking)

2. **Compliance Agent**
   - Auto-generate compliance checklists for projects
   - Track completion status
   - Schedule reviews and reminders
   - Generate compliance reports

3. **Standards Database**
   - Index all applicable standards in Qdrant
   - IEC 62443, NIST CSF, ISA 99, NERC CIP
   - Requirement mapping to projects

**Deliverables:**
- Compliance tracking system operational
- Automated compliance checklists
- Standards database searchable

---

### Week 29-30: Temporal Workflow Orchestration

**Tasks:**

1. **Temporal Installation**
   - Install Temporal.io on iac1
   - Configure PostgreSQL backend
   - Set up web UI

2. **Durable Workflows**
   - Opportunity-to-Proposal workflow (multi-day)
   - Lead-to-Customer conversion workflow
   - Project lifecycle workflow
   - Handle retries, timeouts, failures

3. **Multi-Agent Coordination**
   - Parallel agent execution
   - Agent output dependencies
   - Conditional workflows
   - Human-in-the-loop approvals

**Deliverables:**
- Temporal workflows deployed
- Multi-agent coordination working
- Durable workflows handling failures gracefully

### Phase 4 Success Criteria
- ✅ 20-page proposal in <30 minutes
- ✅ <1 hour editing needed for proposals
- ✅ Compliance tracking automated
- ✅ Workflows handle failures without data loss

---

## PHASE 5: PRODUCTION HARDENING (Weeks 31-36)

**Goal**: Security audit, monitoring, Kubernetes deployment, cost optimization

### Week 31-32: Security Audit

**Tasks:**

1. **Penetration Testing**
   - Hire external security firm (or use internal resources)
   - Test API endpoints for vulnerabilities
   - Test agent prompt injection attacks
   - Test database access controls

2. **OAuth 2.1 & MFA**
   - Implement OAuth 2.1 authentication
   - Multi-factor authentication (TOTP)
   - Session management
   - Token refresh

3. **RBAC for Agents**
   - Define agent permissions
   - Tool-level access controls
   - Data access restrictions
   - Approval workflows for sensitive operations

**Deliverables:**
- Security audit passed
- OAuth 2.1 implemented
- RBAC configured

---

### Week 33-34: Kubernetes Deployment

**Tasks:**

1. **Containerization**
   - Create Dockerfiles for all components
   - Multi-stage builds for optimization
   - Image scanning (Trivy)
   - Private container registry

2. **Kubernetes Manifests**
   - Deployments, Services, Ingresses
   - ConfigMaps and Secrets
   - Persistent Volumes (PostgreSQL, file storage)
   - Horizontal Pod Autoscaling

3. **Network Segmentation**
   - Corporate → Application DMZ (firewall)
   - Application DMZ → Agent Zone (firewall)
   - Agent Zone → Data Zone (no internet access)

**Deliverables:**
- All services containerized
- Kubernetes cluster deployed
- Network segmentation implemented

---

### Week 35: Monitoring & Observability

**Tasks:**

1. **Prometheus & Grafana**
   - Install Prometheus for metrics collection
   - Create Grafana dashboards:
     - Agent execution metrics
     - API performance
     - Database query times
     - Cost tracking

2. **AgentOps Integration**
   - Sign up for AgentOps (or self-hosted alternative)
   - Track agent performance
   - Token usage analytics
   - Error rate monitoring

3. **Alerting**
   - PagerDuty/Slack integration
   - Alert on agent failures
   - Alert on cost spikes
   - Alert on database issues

**Deliverables:**
- Monitoring dashboards operational
- Alerting configured
- 24/7 visibility into system health

---

### Week 36: Cost Optimization & Launch

**Tasks:**

1. **Cost Optimization**
   - Intelligent model routing (Haiku/Sonnet/Opus)
   - Prompt caching implementation
   - Batch processing during off-peak hours
   - Resource utilization optimization

2. **Load Testing**
   - Test with 10 concurrent agents
   - 10,000 lead database
   - 1,000 requests/hour
   - Verify 99.5% uptime

3. **User Training & Documentation**
   - User manual
   - Video tutorials
   - Admin guide
   - Troubleshooting playbook

4. **Production Launch**
   - Phased rollout (10% → 50% → 100%)
   - Monitor for issues
   - Collect user feedback
   - Iterate and improve

**Deliverables:**
- Cost optimizations implemented
- Load testing passed
- User training completed
- Production launch successful! 🚀

### Phase 5 Success Criteria
- ✅ Security audit passed
- ✅ 99.5% uptime under load
- ✅ <$0.50/task average cost
- ✅ Users trained and productive

---

## Post-Launch: Continuous Improvement

### Q2 2025
- Mobile app (React Native)
- Voice interface for agents (Whisper + TTS)
- Real-time collaboration (WebSockets)
- Customer portal

### Q3 2025
- Multi-tenant SaaS version
- White-label for partners
- Marketplace for agent templates
- Integration with more CAD tools

### Q4 2025
- Computer vision for P&ID parsing (OCR)
- Predictive analytics (ML models)
- IoT integration (ThingsBoard data)
- Blockchain for audit trails (optional)

---

## Resource Requirements

### Team
- **Phase 0-1**: 1 developer (with AI assistance)
- **Phase 2-4**: 1-2 developers
- **Phase 5**: 1 developer + 1 DevOps engineer

### Infrastructure (On-Premise)
- **iac1 server**: Existing (100.100.101.1)
- **Azure VM**: Existing (100.107.50.52) - for Qdrant
- **Additional servers**: None needed for Phases 0-4

### Infrastructure (Kubernetes - Phase 5)
- **Cluster**: 3 nodes minimum (16GB RAM, 4 CPU each)
- **Storage**: 500GB persistent storage
- **Network**: 1Gbps internal, 100Mbps external

### Budget Estimate
- **Phase 0-1**: $0 (all OSS, existing infrastructure)
- **Phase 2-4**: ~$1,000 (cloud storage, backup, testing)
- **Phase 5**: ~$3,000-5,000 (Kubernetes cluster, security audit)
- **Ongoing**: ~$500/month (Claude API usage, hosting)

---

## Risk Management

### Technical Risks
- **Agent hallucinations**: Mitigate with validation layers, human review
- **MCP server failures**: Implement retry logic, circuit breakers
- **Database performance**: Use read replicas, caching, query optimization

### Business Risks
- **Low adoption**: Conduct user training, gather feedback early
- **Inaccurate quotes**: Start with human review, improve over time
- **Cost overruns**: Implement cost monitoring, model routing

### Security Risks
- **Data breaches**: Network segmentation, encryption, access controls
- **Prompt injection**: Input validation, sandboxing, audit logs
- **Agent misuse**: RBAC, approval workflows, comprehensive logging

---

## Conclusion

This 36-week roadmap provides a clear path from foundation to production for the INSA CRM System. Each phase delivers working functionality, allowing for iterative feedback and course corrections.

**Key Milestones**:
- ✅ Week 4: Foundation complete (MVP agent working)
- Week 8: Lead management production-ready
- Week 16: Quote generation operational
- Week 24: Security & technical agents deployed
- Week 30: Full proposal automation
- Week 36: Production launch with monitoring

**Next Immediate Steps** (Phase 1):
1. Install dependencies: `pip install -r requirements.txt`
2. Create PostgreSQL database
3. Configure ERPNext custom DocTypes
4. Test Lead Qualification Agent
5. Begin Week 5 tasks

---

**Document Version**: 1.0
**Created**: October 17, 2025
**Maintained By**: INSA Automation Corp
**Questions**: w.aroca@insaing.com
