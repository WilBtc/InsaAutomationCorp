# INSA CRM Platform - Company Customization Roadmap
**Goal:** Make the platform deeply familiar with INSA's workflows, processes, and domain knowledge
**Status:** Ready for customization
**Priority:** HIGH (maximize platform value)

---

## 🎯 Executive Summary

The platform is **100% autonomous** but currently uses **generic industrial automation knowledge**. To maximize value, we need to train it on:

1. **INSA's specific workflows** (your actual sales process)
2. **Past project data** (quotes, BOMs, timelines, pricing)
3. **Domain expertise** (PLC vendors you prefer, typical customer requirements)
4. **Communication templates** (your brand voice, email templates)
5. **Pricing strategies** (your margin targets, competitive positioning)

**Result:** Platform becomes an **expert in INSA's way of doing business**, not just generic automation.

---

## 📊 Current State vs Desired State

### Current State (Generic Knowledge)
| Component | Knowledge Source | Limitation |
|-----------|-----------------|------------|
| Lead Qualification | Generic criteria (5 factors) | Doesn't know INSA's ideal customer profile |
| Quote Generation | Industry averages | Doesn't know INSA's actual pricing/margins |
| BOM Generation | Generic components | Doesn't know INSA's preferred vendors/parts |
| Communication | Generic templates | Doesn't match INSA's brand voice |
| Workflows | Generic 5-step sequence | Doesn't match INSA's actual sales process |

### Desired State (INSA-Specific Knowledge)
| Component | Knowledge Source | Benefit |
|-----------|-----------------|---------|
| Lead Qualification | INSA's historical win/loss data | **90%+ accuracy** in identifying high-value leads |
| Quote Generation | INSA's past 100+ projects | **Accurate pricing** based on actual data |
| BOM Generation | INSA's preferred vendor catalog | **Real part numbers**, real costs |
| Communication | INSA's email templates & brand guide | **Consistent brand voice** |
| Workflows | INSA's documented sales process | **Matches actual workflow** |

---

## 🗂️ Phase 10: Company Knowledge Base Integration

### 10.1 - Ingest Historical Project Data

**Goal:** Train the RAG system on ALL past INSA projects

**What to collect:**
```
For each past project:
├── Project metadata (customer, industry, timeline, budget)
├── Requirements (RFP, emails, notes)
├── Quote details (total, breakdown, margin)
├── BOM (actual parts used, vendors, costs)
├── Labor (actual hours vs estimated)
├── Outcome (won/lost, actual margin, lessons learned)
├── Communications (emails, calls, meetings)
└── Deliverables (P&IDs, code, documentation)
```

**How to implement:**

**Step 1: Create data collection script**
```python
# File: scripts/ingest_historical_projects.py

import json
from pathlib import Path
from agents.quote_generation.rag_knowledge_base import ProjectRAG

def ingest_project(project_folder: Path):
    """
    Ingest a single historical project into RAG

    Expected structure:
    project_folder/
    ├── metadata.json (customer, industry, timeline)
    ├── requirements.txt or .pdf
    ├── quote.json (pricing, BOM, labor)
    ├── bom.csv (parts list)
    ├── outcome.json (won/lost, actual vs estimated)
    └── communications/ (emails, call notes)
    """

    rag = ProjectRAG()

    # Load metadata
    with open(project_folder / "metadata.json") as f:
        metadata = json.load(f)

    # Load quote
    with open(project_folder / "quote.json") as f:
        quote = json.load(f)

    # Load outcome
    with open(project_folder / "outcome.json") as f:
        outcome = json.load(f)

    # Combine into searchable document
    project_doc = {
        "project_code": metadata['project_code'],
        "customer": metadata['customer'],
        "industry": metadata['industry'],
        "timeline": metadata['timeline'],
        "budget": quote['total'],
        "margin": outcome['actual_margin'],
        "won": outcome['won'],
        "requirements": load_requirements(project_folder),
        "bom": load_bom(project_folder),
        "lessons_learned": outcome.get('lessons_learned', '')
    }

    # Index in ChromaDB
    rag.add_project(project_doc)

    print(f"✅ Indexed: {metadata['project_code']}")

# Process all projects
projects_dir = Path("/var/lib/insa-crm/historical_projects")
for project_folder in projects_dir.iterdir():
    if project_folder.is_dir():
        ingest_project(project_folder)
```

**Action items:**
1. ✅ Create folder: `/var/lib/insa-crm/historical_projects/`
2. 📝 Export past projects (Excel/CSV → JSON)
3. 🔄 Run ingestion script
4. ✅ Platform now has **INSA's project memory**

**Expected benefit:** Quote accuracy improves from 76% → **90%+**

---

### 10.2 - Build INSA-Specific Vendor Catalog

**Goal:** Replace generic BOM with INSA's actual vendor catalog

**What to collect:**
```
INSA Vendor Catalog:
├── PLCs (Allen-Bradley, Siemens, Schneider, etc.)
│   ├── Model numbers
│   ├── Current pricing
│   ├── Lead times
│   ├── Preferred vendors
│   └── Usage frequency (which you use most)
├── HMI/SCADA (FactoryTalk, WinCC, Ignition, etc.)
├── Instrumentation (pressure, temp, flow, level sensors)
├── Panels & Enclosures
├── Cables & Wiring
└── Networking equipment
```

**How to implement:**

**Step 1: Create vendor catalog database**
```sql
-- File: migrations/010_vendor_catalog.sql

CREATE TABLE vendor_catalog (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,  -- PLC, HMI, Instrumentation, etc.
    vendor VARCHAR(100) NOT NULL,    -- Allen-Bradley, Siemens, etc.
    part_number VARCHAR(100) NOT NULL,
    description TEXT,
    unit_cost NUMERIC(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    lead_time_days INTEGER,
    preferred BOOLEAN DEFAULT false,  -- INSA's preferred parts
    usage_count INTEGER DEFAULT 0,    -- How often INSA uses this
    last_used_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_vendor_catalog_category ON vendor_catalog(category);
CREATE INDEX idx_vendor_catalog_preferred ON vendor_catalog(preferred);

-- Example data (Allen-Bradley PLCs that INSA commonly uses)
INSERT INTO vendor_catalog (category, vendor, part_number, description, unit_cost, preferred, usage_count) VALUES
('PLC', 'Allen-Bradley', '1769-L33ER', 'CompactLogix 5370 L3 Controller, 2MB, Ethernet', 3200.00, true, 15),
('PLC', 'Allen-Bradley', '1769-IF8', 'CompactLogix 8-Ch Analog Input Module', 450.00, true, 20),
('PLC', 'Allen-Bradley', '1769-OF8C', 'CompactLogix 8-Ch Analog Output Module', 520.00, true, 18),
('HMI', 'Rockwell', 'PanelView Plus 7 Standard 15-inch', 'Graphic Terminal, Ethernet', 2500.00, true, 12),
('HMI', 'Ignition', 'Ignition SCADA Unlimited License', 'Unlimited tags, unlimited clients', 5000.00, true, 8);
```

**Step 2: Update BOM generator to use INSA catalog**
```python
# In bom_generator.py

def get_preferred_plc(io_count: int, vendor: str = "allen-bradley") -> Dict:
    """Get INSA's preferred PLC for given I/O count"""

    # Query INSA catalog
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT part_number, description, unit_cost
            FROM vendor_catalog
            WHERE category = 'PLC'
              AND vendor ILIKE %s
              AND preferred = true
            ORDER BY usage_count DESC
            LIMIT 1
        """, (vendor,))

        result = cursor.fetchone()

        if result:
            return {
                "part_number": result[0],
                "description": result[1],
                "unit_cost": result[2],
                "source": "insa_catalog"  # Real INSA part!
            }
        else:
            # Fallback to generic
            return generic_plc_estimate(io_count, vendor)
```

**Action items:**
1. 📋 Export INSA's preferred parts list (Excel → CSV)
2. 🔄 Import into vendor_catalog table
3. ✅ BOM generator now uses **INSA's actual parts**

**Expected benefit:** BOM accuracy improves from 79% → **95%+**, real part numbers

---

### 10.3 - Customize Lead Qualification Criteria

**Goal:** Teach the agent what makes a good INSA customer

**What to analyze:**
```
Historical Win/Loss Data:
├── Won deals: Common characteristics
│   ├── Industries (oil & gas, pharma, food & beverage?)
│   ├── Budget ranges ($50K-$500K?)
│   ├── Timeline (urgent vs planned?)
│   ├── Technical complexity (simple loops vs complex batch?)
│   └── Geography (local vs remote?)
├── Lost deals: Common patterns
│   ├── Budget too low (< $20K?)
│   ├── Timeline too aggressive (< 1 month?)
│   ├── Technology mismatch (non-standard PLCs?)
│   └── Competition (lost to who? why?)
└── Profitability: Which deals were most profitable?
```

**How to implement:**

**Step 1: Analyze historical data**
```python
# File: scripts/analyze_ideal_customer.py

import pandas as pd

# Load historical deals
deals = pd.read_csv('/var/lib/insa-crm/historical_deals.csv')

# Won deals analysis
won_deals = deals[deals['outcome'] == 'won']

print("INSA's Ideal Customer Profile:")
print(f"Top Industries: {won_deals['industry'].value_counts().head(3)}")
print(f"Avg Budget: ${won_deals['budget'].mean():,.0f}")
print(f"Avg Timeline: {won_deals['timeline_months'].mean():.1f} months")
print(f"Win Rate by Industry: {won_deals.groupby('industry')['outcome'].value_counts(normalize=True)}")

# Profitability analysis
profitable_deals = won_deals[won_deals['actual_margin'] > 0.25]  # >25% margin
print(f"Most Profitable Industry: {profitable_deals['industry'].mode()[0]}")
print(f"Most Profitable Budget Range: ${profitable_deals['budget'].quantile([0.25, 0.75])}")
```

**Step 2: Update qualification scoring weights**
```python
# In lead_qualification_agent.py

# INSA's custom scoring weights (based on historical data)
INSA_SCORING_WEIGHTS = {
    "budget": {
        "weight": 0.30,  # Budget is critical for INSA
        "ideal_range": (50000, 500000),  # Sweet spot: $50K-$500K
        "minimum": 20000  # Don't pursue < $20K
    },
    "timeline": {
        "weight": 0.20,
        "ideal_range": (2, 6),  # 2-6 months ideal
        "urgent_bonus": 10  # +10 points if urgent but reasonable
    },
    "industry": {
        "weight": 0.25,  # Industry fit matters
        "preferred": ["oil_gas", "pharma", "food_beverage"],  # INSA's strong industries
        "bonus": 15  # +15 points for preferred industry
    },
    "technical_fit": {
        "weight": 0.15,
        "preferred_plcs": ["allen-bradley", "siemens"],  # What INSA knows best
        "complexity": "medium_to_high"  # INSA excels at complex projects
    },
    "decision_authority": {
        "weight": 0.10
    }
}
```

**Action items:**
1. 📊 Export historical deal data (CRM → CSV)
2. 🔍 Run analysis script
3. ⚙️ Update scoring weights
4. ✅ Agent now knows **INSA's ideal customer**

**Expected benefit:** Lead scoring accuracy improves from 85% → **95%+**

---

### 10.4 - Build INSA Communication Templates

**Goal:** Match INSA's brand voice and style

**What to create:**
```
INSA Communication Library:
├── Email Templates
│   ├── Welcome email (new lead)
│   ├── Quote delivery (professional)
│   ├── Follow-up (day 2, 5, 7, 14)
│   ├── Case study sharing
│   └── Meeting scheduling
├── SMS Templates
│   ├── Quick reminder
│   ├── Meeting confirmation
│   └── Urgent follow-up
├── Phone AI Scripts
│   ├── Inbound greeting
│   ├── Qualification questions
│   ├── Objection handling
│   └── Meeting scheduling
└── Brand Guidelines
    ├── Tone: Professional but approachable
    ├── Language: Technical but clear
    ├── Signature: INSA team format
    └── Legal: Disclaimers, compliance
```

**How to implement:**

**Step 1: Create INSA-branded templates**
```sql
-- Insert INSA-specific templates

INSERT INTO communication_templates (template_id, channel, name, subject, content_html, content_text, category) VALUES

-- Welcome email (INSA style)
('insa_welcome_v1', 'email', 'INSA Welcome Email',
'Welcome to INSA Automation - {{customer_name}}',
'
<html>
<body style="font-family: Arial, sans-serif; color: #333;">
    <div style="background: #003366; color: white; padding: 20px; text-align: center;">
        <h1>INSA Automation</h1>
        <p style="font-size: 14px;">Industrial Control Systems Since 2015</p>
    </div>

    <div style="padding: 30px;">
        <p>Dear {{customer_name}},</p>

        <p>Thank you for reaching out to INSA Automation. We specialize in delivering
        turnkey industrial control solutions that help companies like {{company}}
        optimize their processes.</p>

        <p><strong>What makes INSA different:</strong></p>
        <ul>
            <li>✅ 10+ years experience in oil & gas, pharma, and food & beverage</li>
            <li>✅ Allen-Bradley & Siemens certified engineers</li>
            <li>✅ IEC 62443 cybersecurity compliance built-in</li>
            <li>✅ Average project delivery: 3-4 months</li>
        </ul>

        <p>Our team is reviewing your requirements and will have a detailed quote
        for you within 24 hours.</p>

        <p>In the meantime, feel free to check out a recent similar project we
        completed for {{similar_customer}} in the {{industry}} industry.</p>

        <p>Best regards,<br>
        <strong>The INSA Team</strong><br>
        w.aroca@insaing.com | +1-555-0100</p>
    </div>

    <div style="background: #f4f4f4; padding: 15px; text-align: center; font-size: 12px;">
        <p>INSA Automation Corp | 100.100.101.1 | Tailscale Network</p>
        <p>© 2025 INSA Automation. All rights reserved.</p>
    </div>
</body>
</html>
',
'Dear {{customer_name}}, Thank you for reaching out to INSA Automation...',
'welcome'),

-- INSA Quote Email
('insa_quote_v1', 'email', 'INSA Quote Delivery',
'Your Custom Quote - {{quote_id}} | INSA Automation',
'[INSA-branded quote email template with logo, professional layout]',
'[Plain text version]',
'quote_delivery');
```

**Action items:**
1. 📝 Review INSA's current email templates
2. 🎨 Get INSA logo/brand colors
3. ✍️ Write INSA-specific templates
4. ✅ Platform now uses **INSA's brand voice**

---

### 10.5 - Map INSA's Actual Sales Process

**Goal:** Customize workflows to match INSA's real process

**Current (Generic 5-step):**
1. Lead captured → Qualify
2. High-value → Welcome email
3. Generate quote
4. Send quote
5. Follow-up campaign (5 steps over 14 days)

**Discover INSA's Actual Process:**
```
Questions to answer:
├── How do leads come in? (Website? Referral? Trade shows?)
├── Who qualifies leads? (Sales? Engineering? Both?)
├── How long does quoting take? (Same day? 2-3 days?)
├── Who approves quotes? (Sales manager? Engineering?)
├── Follow-up cadence? (Call within 2 hours? Email next day?)
├── When do you involve engineering? (After qual? After quote?)
├── Project kickoff process? (Kickoff meeting? SOW signed first?)
└── Post-sale process? (Customer success check-in? Support?)
```

**How to implement:**

**Step 1: Document INSA's workflow**
```yaml
# File: config/insa_sales_workflow.yaml

insa_sales_process:

  stage_1_lead_capture:
    sources:
      - website_form (80%)
      - referral (15%)
      - trade_show (5%)
    immediate_actions:
      - Send auto-reply (within 5 minutes)
      - Notify sales team (Slack/email)
      - Create ERPNext Lead

  stage_2_qualification:
    who: Sales + Engineering (for technical fit)
    timeline: Within 2 hours
    criteria:
      - Budget check (>$20K minimum)
      - Timeline check (>1 month minimum)
      - Technical fit (PLCs we support)
    actions:
      - If qualified: Schedule discovery call
      - If not qualified: Polite decline email

  stage_3_discovery:
    format: 30-minute video call (Zoom/Teams)
    attendees: Sales + Lead Engineer
    goal: Gather detailed requirements
    deliverable: Scope document

  stage_4_quoting:
    who: Engineering team
    timeline: 1-2 business days
    approval: Engineering Manager reviews
    components:
      - Technical solution
      - BOM with real part numbers
      - Labor estimate (conservative +20%)
      - Pricing (25-35% margin target)

  stage_5_quote_delivery:
    method: Email with PDF + video walkthrough
    follow_up:
      - Day 0: Quote sent
      - Day 1: "Did you receive it?" email
      - Day 3: Phone call
      - Day 7: "Questions?" email
      - Day 14: "Expiring soon" email

  stage_6_negotiation:
    typical: 1-2 rounds of revisions
    flexibility: 5-10% on price, timeline negotiable

  stage_7_close:
    contract: SOW + MSA
    payment_terms: 30/40/30 (deposit/milestone/completion)
    kickoff: Within 1 week of signing

  stage_8_delivery:
    phases:
      - Design (2-4 weeks)
      - Programming (3-6 weeks)
      - FAT (1 week)
      - Installation (1-2 weeks)
      - SAT (1 week)
    communication: Weekly status updates

  stage_9_customer_success:
    check_ins:
      - 1 week after SAT
      - 1 month after SAT
      - 3 months after SAT
    goal: Identify upsell opportunities
```

**Step 2: Create INSA-specific workflow**
```python
# In automation_orchestrator.py

def create_insa_sales_workflow(lead_data: Dict) -> WorkflowExecution:
    """
    INSA's actual sales workflow (based on documented process)
    """
    workflow_id = f"insa-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

    workflow = WorkflowExecution(
        workflow_id=workflow_id,
        workflow_type="insa_complete_sales",
        metadata={"lead_data": lead_data}
    )

    # Step 1: Immediate auto-reply (within 5 min)
    workflow.steps.append(WorkflowStep(
        stage=WorkflowStage.LEAD_CAPTURE,
        agent="communication",
        action="send_auto_reply",
        params={"template": "insa_auto_reply_v1"}
    ))

    # Step 2: Notify sales team (Slack)
    workflow.steps.append(WorkflowStep(
        stage=WorkflowStage.LEAD_CAPTURE,
        agent="communication",
        action="notify_slack",
        params={"channel": "#sales-leads", "urgency": "high"}
    ))

    # Step 3: Qualify lead (Sales + Engineering review)
    workflow.steps.append(WorkflowStep(
        stage=WorkflowStage.QUALIFICATION,
        agent="lead_qualification",
        action="insa_score_lead",
        params={"use_insa_weights": True}
    ))

    # Step 4: If qualified (>75), schedule discovery call
    workflow.steps.append(WorkflowStep(
        stage=WorkflowStage.DISCOVERY,
        agent="communication",
        action="schedule_discovery_call",
        params={"calendly_link": "https://calendly.com/insa-sales/discovery"}
    ))

    # ... (continue with INSA's actual 9-stage process)

    return workflow
```

**Action items:**
1. 📋 Interview INSA sales team (30-minute session)
2. 📝 Document actual workflow (use template above)
3. 💻 Code INSA-specific workflow
4. ✅ Platform now matches **INSA's real process**

---

## 🎓 Phase 11: Team Training & Adoption

### 11.1 - Create INSA Platform User Guide

**Goal:** Make it easy for INSA team to use the platform

**What to create:**
```
INSA Platform User Guide:
├── Quick Start (5 minutes)
│   ├── How to check new leads
│   ├── How to generate a quote
│   └── How to send a quote
├── Daily Operations
│   ├── Morning routine (check dashboard)
│   ├── Lead review process
│   └── Quote approval process
├── Advanced Features
│   ├── Customizing communication templates
│   ├── Adjusting pricing strategies
│   └── Viewing analytics
└── Troubleshooting
    ├── What if quote confidence is low?
    ├── What if lead score seems wrong?
    └── Who to contact for help
```

### 11.2 - Setup Slack Integration

**Goal:** Real-time notifications for INSA team

```python
# Notify #sales-leads when high-value lead comes in
if lead_score >= 80:
    slack_notify(
        channel="#sales-leads",
        message=f"🔥 High-value lead: {company_name} (Score: {lead_score}/100)\n"
                f"Industry: {industry} | Budget: ${budget:,}\n"
                f"View: http://100.100.101.1:8003/leads/{lead_id}"
    )

# Notify #engineering when quote generated
if quote_generated:
    slack_notify(
        channel="#engineering",
        message=f"📋 New quote generated: {quote_id}\n"
                f"Customer: {customer_name} | Total: ${total:,}\n"
                f"Confidence: {confidence:.0%} | Review: {review_url}"
    )
```

### 11.3 - Weekly Review Meeting

**Goal:** Continuous improvement based on outcomes

**Agenda:**
1. Review past week's leads (quality, conversion)
2. Review quotes generated (accuracy, win rate)
3. Discuss edge cases (where AI struggled)
4. Update knowledge base (new lessons learned)
5. Adjust scoring/pricing as needed

---

## 📈 Expected Impact After Customization

| Metric | Current (Generic) | After Customization | Improvement |
|--------|------------------|---------------------|-------------|
| Lead Scoring Accuracy | 85% | 95%+ | +12% |
| Quote Accuracy | 76% | 90%+ | +18% |
| BOM Accuracy | 79% (generic parts) | 95%+ (real parts) | +20% |
| Win Rate | 6% (estimated) | 8-10% (INSA-tuned) | +33-67% |
| Quote Generation Time | 0.6s | 0.6s (same) | -- |
| Customer Satisfaction | Good | Excellent (brand voice) | +High |

**Additional savings from higher accuracy:**
- Fewer quote revisions: -50% rework
- Higher win rate: +33-67% more revenue
- Better margins: Optimized pricing
- Faster sales cycles: Better qualification

---

## 🚀 Quick Start: Customization Checklist

### Week 1: Data Collection
- [ ] Export historical project data (last 2-3 years)
- [ ] Create project folders in `/var/lib/insa-crm/historical_projects/`
- [ ] Export INSA vendor catalog (Excel → CSV)
- [ ] Export historical deal data (win/loss analysis)
- [ ] Gather INSA email templates & brand assets

### Week 2: Data Ingestion
- [ ] Run historical project ingestion script
- [ ] Import vendor catalog into database
- [ ] Analyze ideal customer profile
- [ ] Update lead scoring weights
- [ ] Create INSA communication templates

### Week 3: Workflow Customization
- [ ] Interview sales team (document actual process)
- [ ] Code INSA-specific workflow
- [ ] Test end-to-end with real lead
- [ ] Setup Slack integration
- [ ] Create user guide

### Week 4: Team Training & Launch
- [ ] Train sales team (30-minute session)
- [ ] Train engineering team (30-minute session)
- [ ] Go live with 1-2 test leads
- [ ] Monitor first week closely
- [ ] Weekly review meeting (ongoing)

---

## 💡 Quick Wins (Can Do Today)

### 1. Index INSAGTEC-6598 Project (Reference Project)
```bash
# Already exists in ~/insa-crm-platform/projects/customers/INSAGTEC-6598/
# Just need to ensure it's in ChromaDB
cd ~/insa-crm-platform/core
python3 -c "
from agents.quote_generation.quote_orchestrator import QuoteOrchestrator
orch = QuoteOrchestrator()
stats = orch.rag.get_statistics()
print(f'Projects in RAG: {stats}')
"
```

**Expected:** Should show INSAGTEC-6598 already indexed

### 2. Create First INSA Template
```sql
-- Add INSA welcome email
INSERT INTO communication_templates (
    template_id, channel, name, subject, content_html, category
) VALUES (
    'insa_welcome_2025', 'email',
    'INSA Welcome Email (2025)',
    'Welcome to INSA Automation - {{customer_name}}',
    '<h1>Welcome!</h1><p>Thanks for reaching out...</p>',
    'welcome'
);
```

### 3. Add INSA's Most Common PLC
```sql
-- Add Allen-Bradley CompactLogix (INSA's go-to)
INSERT INTO vendor_catalog (
    category, vendor, part_number, description,
    unit_cost, preferred, usage_count
) VALUES (
    'PLC', 'Allen-Bradley', '1769-L33ER',
    'CompactLogix 5370 L3 Controller, 2MB, Ethernet',
    3200.00, true, 15
);
```

---

## 🎯 Success Criteria

**After customization, the platform should:**
1. ✅ Generate quotes using INSA's actual preferred parts
2. ✅ Score leads based on INSA's ideal customer profile
3. ✅ Send emails in INSA's brand voice
4. ✅ Follow INSA's actual sales workflow (not generic)
5. ✅ Learn from INSA's historical projects
6. ✅ Integrate with INSA's tools (Slack, etc.)

**Result:** Platform becomes an **expert INSA salesperson**, not just a generic AI.

---

## 📞 Next Steps

**Ready to customize? Here's how we start:**

1. **Data Collection Session** (1 hour)
   - Review what historical data is available
   - Identify which projects to use as training data
   - Export vendor catalog

2. **Sales Process Interview** (30 min)
   - Walk through actual sales process
   - Identify critical decision points
   - Document current pain points

3. **Implementation** (1 week)
   - Ingest historical data
   - Customize workflows
   - Train team

4. **Launch** (Go live!)
   - Monitor first week closely
   - Weekly review meetings
   - Continuous improvement

---

**Ready to make this platform truly INSA's?** Let's start with data collection!

**Made with ❤️ by INSA Automation Corp**
**Platform Customization Roadmap**
**Created:** October 18, 2025
