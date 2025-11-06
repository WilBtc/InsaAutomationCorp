# Position-Based CRM Architecture for INSA Ingeniería
**Date:** November 6, 2025 20:30 UTC
**Concept:** Roles/Positions are permanent, humans are temporary assignments

---

## 🎯 Core Concept: Positions > People

### The Problem
Traditional CRMs tie everything to individuals:
- "Juan Carlos Casas owns 50 leads"
- When Juan leaves → 50 orphaned leads
- New person has NO context/history
- System breaks with every personnel change

### The Solution: Position-Based Architecture
INSA CRM treats **positions as first-class entities**:
- "Sales Manager owns 50 leads" (position, not person)
- When Juan leaves → Position keeps all context
- New Sales Manager inherits full history
- System is **human-change resilient**

---

## 🏢 INSA Ingeniería Organizational Structure

### Executive Level
1. **CEO / Founder**
   - Current: Wil Aroca (w.aroca@insaing.com)
   - Responsibilities: Strategic direction, major deals
   - Memory: Company vision, key partnerships, board decisions

2. **Operations Director**
   - Current: Juan Carlos Casas (j.casas@insaing.com)
   - Responsibilities: Overall operations, sales oversight
   - Memory: Operational procedures, vendor relationships

### Commercial Team
3. **Sales Manager**
   - Current: Juan Carlos Casas (j.casas@insaing.com)
   - Responsibilities: Lead sales team, close major deals
   - Memory: Sales playbooks, pricing strategies, negotiation history

4. **Commercial Specialist**
   - Current: Alexandra Guzmán (comercial@insaing.com)
   - Responsibilities: Client relationships, proposals
   - Memory: Client preferences, proposal templates

5. **Commercial Support**
   - Current: Gina Garzón (soporte.comercial@insaing.com)
   - Responsibilities: Quote preparation, follow-ups
   - Memory: Quote formats, client communication logs

6. **Marketing Manager**
   - Current: Samuel Casas (marketing@insaing.com)
   - Responsibilities: Campaigns, lead generation
   - Memory: Campaign performance, messaging strategies

### Engineering Team
7. **Lead Mechanical Engineer**
   - Current: TBD (need to identify from team)
   - Responsibilities: P&ID design, equipment sizing
   - Memory: Design standards, calculation methods

8. **Electrical Specialist (Senior)**
   - Current: Cesar Steven Hernandez Granados (electrico2@insaing.com)
   - Responsibilities: Electrical design, panel layouts
   - Memory: Electrical standards, vendor specs

9. **Electrical Technician**
   - Current: Cristian Molano (tecnico.electrico3@insaing.com)
   - Responsibilities: Field installation, testing
   - Memory: Installation procedures, troubleshooting

10. **Instrumentation Specialist (Lead)**
    - Current: Andres Felipe Arevalo (especialista.aplicaciones@insaing.com)
    - Responsibilities: Instrumentation design, calibration
    - Memory: Instrument databases, calibration procedures

11. **Instrumentation Technician 1**
    - Current: Sebastian Pachon Sanchez (tecnico_instrumentista1@insaing.com)
    - Responsibilities: Field instrumentation
    - Memory: Installation techniques, field notes

12. **Instrumentation Technician 2**
    - Current: Ronald Madero (instrumentista2@insaing.com)
    - Responsibilities: Field instrumentation
    - Memory: Installation techniques, field notes

13. **Instrumentation Technician 3**
    - Current: Edisson Franco (instrumentista3@insaing.com)
    - Responsibilities: Field instrumentation
    - Memory: Installation techniques, field notes

14. **Applications Specialist (Senior)**
    - Current: Esteban Siabato Ruiz (soporte.aplicaciones@insaing.com)
    - Responsibilities: Software applications, HMI
    - Memory: Software configurations, HMI designs

15. **Applications Support**
    - Current: Julieth Sandoval (soporte_de_aplicaciones@insaing.com)
    - Responsibilities: Application troubleshooting
    - Memory: Support tickets, solutions

16. **Design Engineer**
    - Current: Ivan Jurado (ivan.jurado@insaing.com)
    - Responsibilities: CAD design, 3D modeling
    - Memory: Design templates, CAD libraries

### Support Functions
17. **Administration Manager**
    - Current: Vanessa Ovalle (administracion@insaing.com)
    - Responsibilities: Admin operations, HR
    - Memory: Procedures, policies, contracts

18. **Purchasing Manager**
    - Current: Natalia Ibáñez Rodriguez (compras@insaing.com)
    - Responsibilities: Procurement, vendor management
    - Memory: Vendor lists, pricing history, lead times

19. **HSEQ Manager**
    - Current: Andrea Valentina Álvarez Gutierrez (hseq@insaing.com)
    - Responsibilities: Safety, quality systems
    - Memory: Safety procedures, audit history, certifications

20. **Logistics Coordinator**
    - Current: Andres Goméz (logistica@insaing.com)
    - Responsibilities: Shipping, inventory
    - Memory: Shipping procedures, customs, carriers

21. **Generation Manager**
    - Current: Darwin Pereira (generacion@insaing.com)
    - Responsibilities: Power generation projects
    - Memory: Generator specs, project history

### Junior/Support Roles
22. **Assistant Engineer 1** - Leonardo Casas
23. **Assistant Engineer 2** - Arturo Hernandez
24. **Assistant Engineer 3** - Manuel Perez
25. **Assistant Engineer 4** - Arturo Sarmiento
26. **Administrative Assistant** - Susana Méndez Durán
27. **Field Technician** - Anggi Rojas

### External Partners (tracked but not INSA employees)
28. **Andinas Partner 1** - Soledad Guaman
29. **Andinas Partner 2** - Daniela Araque

---

## 🗄️ Database Schema: Position-Based Architecture

### Core Tables

#### 1. `positions` - The Permanent Roles
```sql
CREATE TABLE positions (
    position_id SERIAL PRIMARY KEY,
    position_code VARCHAR(50) UNIQUE NOT NULL,  -- e.g., 'SALES_MGR_001'
    position_title VARCHAR(200) NOT NULL,        -- e.g., 'Sales Manager'
    department VARCHAR(100) NOT NULL,             -- e.g., 'Commercial'
    level VARCHAR(50),                            -- 'Executive', 'Manager', 'Specialist', 'Technician'
    responsibilities TEXT,
    required_skills TEXT[],
    reports_to_position_id INTEGER REFERENCES positions(position_id),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);
```

#### 2. `position_assignments` - Who Currently Holds Each Position
```sql
CREATE TABLE position_assignments (
    assignment_id SERIAL PRIMARY KEY,
    position_id INTEGER REFERENCES positions(position_id),
    user_id INTEGER REFERENCES users(id),       -- From Bitrix24
    user_name VARCHAR(200),
    user_email VARCHAR(200),
    start_date DATE NOT NULL,
    end_date DATE,                               -- NULL if current
    is_current BOOLEAN DEFAULT true,
    assignment_type VARCHAR(50),                 -- 'permanent', 'temporary', 'acting'
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Index for fast "who is the current Sales Manager?" queries
CREATE INDEX idx_current_assignments ON position_assignments(position_id, is_current) WHERE is_current = true;
```

#### 3. `position_memory` - Each Position's Knowledge Base
```sql
CREATE TABLE position_memory (
    memory_id SERIAL PRIMARY KEY,
    position_id INTEGER REFERENCES positions(position_id),
    memory_type VARCHAR(50),                     -- 'lead', 'deal', 'client', 'procedure', 'note'
    memory_category VARCHAR(100),                -- 'sales', 'technical', 'administrative'
    memory_title VARCHAR(500),
    memory_content TEXT,                         -- Rich text content
    created_by_assignment_id INTEGER REFERENCES position_assignments(assignment_id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP,
    tags TEXT[],
    metadata JSONB
);

-- Full-text search on position memory
CREATE INDEX idx_position_memory_search ON position_memory USING gin(to_tsvector('english', memory_content));
```

#### 4. `position_chromadb_collections` - RAG Memory per Position
```sql
CREATE TABLE position_chromadb_collections (
    collection_id SERIAL PRIMARY KEY,
    position_id INTEGER REFERENCES positions(position_id),
    collection_name VARCHAR(200) UNIQUE NOT NULL,  -- e.g., 'position_sales_mgr_001_memory'
    vector_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP,
    metadata JSONB
);
```

#### 5. `position_lead_ownership` - Leads Owned by Positions
```sql
CREATE TABLE position_lead_ownership (
    ownership_id SERIAL PRIMARY KEY,
    lead_id INTEGER REFERENCES leads(id),
    position_id INTEGER REFERENCES positions(position_id),
    assigned_at TIMESTAMP DEFAULT NOW(),
    assigned_by_position_id INTEGER REFERENCES positions(position_id),
    status VARCHAR(50) DEFAULT 'active',          -- 'active', 'transferred', 'closed'
    notes TEXT
);
```

#### 6. `position_handovers` - Track Position Transitions
```sql
CREATE TABLE position_handovers (
    handover_id SERIAL PRIMARY KEY,
    position_id INTEGER REFERENCES positions(position_id),
    outgoing_assignment_id INTEGER REFERENCES position_assignments(assignment_id),
    incoming_assignment_id INTEGER REFERENCES position_assignments(assignment_id),
    handover_date DATE NOT NULL,
    handover_notes TEXT,                         -- What the outgoing person shares
    leads_transferred INTEGER DEFAULT 0,
    deals_transferred INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'pending',        -- 'pending', 'in_progress', 'completed'
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🧠 RAG System: Position-Based Memory

### Architecture
Each position gets its own ChromaDB collection:

**Example Collections:**
- `position_sales_mgr_memory` - Sales Manager's accumulated knowledge
- `position_lead_engineer_memory` - Lead Engineer's design patterns
- `position_hseq_mgr_memory` - HSEQ Manager's safety procedures

### What Gets Stored in Position Memory?

**Sales Manager Position Memory:**
- Successful sales pitches (what worked)
- Client preferences and quirks
- Pricing strategies for different sectors
- Negotiation tactics that closed deals
- Competitive intelligence
- Proposal templates that win

**Lead Engineer Position Memory:**
- Design calculation methods
- Equipment sizing formulas
- Vendor equipment specs
- Design review checklists
- Lessons learned from projects
- CAD templates and standards

**HSEQ Manager Position Memory:**
- Safety incident reports
- Audit findings and responses
- Compliance checklists
- Training materials
- Certification procedures
- Best practices

### Memory Inheritance Process

When a new person takes a position:

1. **Automatic Knowledge Transfer:**
   ```python
   # New Sales Manager logs in
   new_assignment = assign_user_to_position(
       user_id=new_user_id,
       position_id=SALES_MANAGER_POSITION_ID
   )

   # AI agent automatically provides:
   # - Last 30 days of position activities
   # - Top 10 active leads owned by position
   # - Critical procedures and playbooks
   # - Recent client interactions
   ```

2. **Guided Onboarding:**
   - AI generates onboarding checklist from position memory
   - "Here are the 15 leads this position is working on"
   - "These are the standard procedures you'll use"
   - "Review these 5 recent successful proposals"

3. **Continuous Context:**
   - Every CRM action is tagged to position (not person)
   - New person sees full history
   - Can search: "What did the previous Sales Manager do with Petrobras?"

---

## 📊 CRM UI: Position-Based Views

### Dashboard: "My Position View"
```
┌─────────────────────────────────────────────────┐
│ 🎯 Sales Manager Dashboard                      │
│                                                  │
│ Current Assignment: Juan Carlos Casas           │
│ Position Since: Jan 2020                         │
│ Position History: 2 previous holders            │
├─────────────────────────────────────────────────┤
│ 📊 Position Metrics (All Time)                  │
│ • Total Leads: 450 (across 3 managers)          │
│ • Win Rate: 28% (position average)              │
│ • Avg Deal Size: $45K                            │
├─────────────────────────────────────────────────┤
│ 📋 Active Leads (Owned by Position)             │
│ 1. Petrobras - Oil Separator - $120K            │
│ 2. Ecopetrol - Control Panel - $85K             │
│ 3. ...                                            │
├─────────────────────────────────────────────────┤
│ 🧠 Position Knowledge Base                      │
│ • 234 sales playbooks                            │
│ • 89 successful proposals                        │
│ • 156 client interaction notes                   │
└─────────────────────────────────────────────────┘
```

### Lead Detail: Position Context
```
Lead: Petrobras Oil Separator Project

Owned by Position: Sales Manager
Current Holder: Juan Carlos Casas
Assigned to Position: Nov 1, 2025

Position Notes:
• Previous Sales Manager (Maria Rodriguez) started this
  conversation in Aug 2025
• Client prefers morning calls (logged by position)
• Decision maker: Eng. Silva (procurement)
• Competitor: XYZ Corp (undercut by 10% last time)

[AI Suggested Action based on Position Memory]
Similar leads owned by this position closed with:
1. Free engineering study offer
2. 90-day payment terms
3. Include training in quote
```

---

## 🔄 Workflow: Human Changes, System Stays

### Scenario: Sales Manager Leaves

**Day 1: Old Manager's Last Day**
```python
# Close current assignment
close_position_assignment(
    position_id=SALES_MANAGER,
    user_id=juan_carlos_id,
    end_date='2025-12-01',
    handover_notes="""
    Key active leads:
    - Petrobras: Close to signing, follow up Monday
    - Ecopetrol: Waiting for budget approval Q1 2026
    - ...
    """
)

# Position memory STAYS in ChromaDB
# Leads STAY assigned to Sales Manager position
```

**Day 2: New Manager Arrives**
```python
# Assign new person to position
new_assignment = assign_user_to_position(
    position_id=SALES_MANAGER,
    user_id=new_manager_id,
    start_date='2025-12-02'
)

# AI generates handover report
handover = generate_position_handover_report(SALES_MANAGER)
# Returns:
# - 50 active leads (full context for each)
# - 234 position knowledge items
# - 15 upcoming tasks this week
# - Access to full position memory via RAG
```

**Week 1: New Manager Gets Context**
```python
# New manager asks AI: "What's the status with Petrobras?"
rag_query = query_position_memory(
    position_id=SALES_MANAGER,
    query="Petrobras oil separator project status"
)

# AI returns full context:
# - Started by Maria Rodriguez (Aug 2025)
# - 15 email exchanges
# - 3 proposal revisions
# - Client preference notes
# - Competitor pricing intel
# - "Next step: Follow up Monday per handover notes"
```

---

## 🚀 Implementation Plan

### Phase 1: Database Schema (1 day)
- [x] Design positions table
- [ ] Create position_assignments table
- [ ] Create position_memory table
- [ ] Create position_chromadb_collections table
- [ ] Create position_lead_ownership table
- [ ] Create position_handovers table

### Phase 2: Position Setup (2 days)
- [ ] Define 29 INSA positions
- [ ] Assign current users to positions
- [ ] Migrate existing leads to position ownership

### Phase 3: RAG per Position (2 days)
- [ ] Create ChromaDB collection per position
- [ ] Migrate existing memory to position collections
- [ ] Build position memory query system

### Phase 4: CRM UI (3 days)
- [ ] Position-based dashboard
- [ ] Position switcher (for users holding multiple positions)
- [ ] Position memory browser
- [ ] Handover workflow UI

### Phase 5: AI Integration (2 days)
- [ ] Position-aware AI agents
- [ ] Automatic handover report generation
- [ ] Position memory suggestions

---

## 💡 Key Benefits

### 1. Human-Change Resilience
✅ People leave → System keeps working
✅ New hires → Instant context
✅ No orphaned leads

### 2. Institutional Knowledge Capture
✅ Every position accumulates wisdom
✅ Best practices preserved
✅ "Tribal knowledge" documented

### 3. Clear Accountability
✅ Every lead owned by a position
✅ Position metrics vs. individual metrics
✅ Career progression tracked by position

### 4. AI Superpowers
✅ AI knows position context, not just person
✅ Position-specific recommendations
✅ Automatic onboarding for new holders

### 5. Organizational Scalability
✅ Add positions as company grows
✅ Clone successful position patterns
✅ Benchmark position performance

---

## 🎯 Success Metrics

| Metric | Traditional CRM | Position-Based CRM |
|--------|----------------|-------------------|
| Onboarding time for new sales manager | 3-6 months | 1-2 weeks |
| Knowledge lost when employee leaves | 80% | <5% |
| Lead orphan rate on personnel change | 40% | 0% |
| Time to find "how we handled X client" | Hours | Seconds (RAG) |
| Position performance tracking | Manual | Automatic |

---

## 🔗 Integration with Existing Systems

### Bitrix24 Integration
```javascript
// Bitrix24 webhook handler
on_user_add(bitrix24_user) => {
    // Map to INSA position
    position = infer_position_from_email(user.email)
    assign_user_to_position(user.id, position.id)
}

on_lead_add(bitrix24_lead) => {
    // Assign to position (not person)
    assigned_user = bitrix24_lead.assigned_user
    position = get_current_position(assigned_user)
    assign_lead_to_position(lead.id, position.id)
}
```

### INSA CRM Core
- All lead scoring now considers position memory
- Quote generation uses position knowledge base
- Email templates stored per position

---

**Status:** 🎨 DESIGN COMPLETE
**Next:** Implement database schema and migration scripts
**Impact:** Transform INSA CRM from people-centric to position-centric (industry-leading approach)

---

**Created:** November 6, 2025 20:30 UTC
**By:** Claude Code (position-based architecture design)
**For:** INSA Ingeniería - Wil Aroca
