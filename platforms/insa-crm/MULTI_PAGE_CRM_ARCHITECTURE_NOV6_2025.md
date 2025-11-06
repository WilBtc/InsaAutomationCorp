# Multi-Page CRM Architecture for INSA Employees
**Date:** November 6, 2025 20:00 UTC
**Purpose:** Transform V5 into a practical, multi-page CRM system
**For:** INSA sales team, engineers, managers

---

## 🎯 INSA Employee Workflows

### Sales Team Workflow
```
1. Dashboard → See today's tasks
2. Leads → Qualify incoming inquiries
3. Opportunities → Track active deals
4. Quotes → Generate proposals
5. Follow-ups → Schedule calls/meetings
```

### Engineering Team Workflow
```
1. Dashboard → See assigned projects
2. Sizing → Equipment dimensioning
3. CAD → Generate 3D models
4. BOMs → Create bills of materials
5. Projects → Track deliverables
```

### Management Workflow
```
1. Dashboard → Company metrics
2. Pipeline → Sales forecast
3. Team → Performance metrics
4. Reports → Weekly/monthly summaries
5. Settings → System configuration
```

---

## 📄 Multi-Page Structure

### Page 1: Dashboard (Home)
**Purpose:** At-a-glance overview + quick actions

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ INSA CRM │ Dashboard │ Leads │ Opportunities │ ... │
├─────────────────────────────────────────────────────┤
│                                                     │
│  My Tasks Today (5)          Recent Activity        │
│  ┌─────────────────────┐    ┌─────────────────┐   │
│  │ □ Follow up: Acme   │    │ Lead qualified   │   │
│  │ □ Quote: TechCorp   │    │ Quote sent       │   │
│  │ □ Call: Global Oil  │    │ Meeting scheduled│   │
│  └─────────────────────┘    └─────────────────┘   │
│                                                     │
│  Pipeline Metrics              Top Opportunities    │
│  ┌──────┐ ┌──────┐ ┌──────┐  1. $50K - Separator  │
│  │ 25   │ │ 18   │ │ 12   │  2. $30K - Controls  │
│  │Leads │ │Opps  │ │Quote │  3. $20K - Retrofit  │
│  └──────┘ └──────┘ └──────┘                        │
│                                                     │
│  Quick Actions                                      │
│  [+ New Lead] [+ New Quote] [Schedule Meeting]     │
└─────────────────────────────────────────────────────┘
```

**Key Elements:**
- Task checklist (from ERPNext ToDo)
- Real-time metrics (counts from database)
- Recent activity feed
- Top opportunities by value
- Quick action buttons

---

### Page 2: Leads
**Purpose:** Manage incoming inquiries and qualify leads

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ INSA CRM │ Dashboard │ Leads │ Opportunities │ ... │
├─────────────────────────────────────────────────────┤
│ Leads (25)                                          │
│                                                     │
│ Filters: [All] [New] [Qualified] [Contacted]       │
│ Search: [____________]  Sort: [Date ▼]            │
│                                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ □ Acme Industries                    NEW        ││
│ │   Contact: John Smith | john@acme.com          ││
│ │   Need: Separator for oil field | $50K        ││
│ │   Source: Website | Today 10:30 AM            ││
│ │   [Qualify] [Convert] [Archive]                ││
│ ├─────────────────────────────────────────────────┤│
│ │ □ TechCorp Solutions              QUALIFIED   ││
│ │   Contact: Jane Doe | jane@tech.com           ││
│ │   Need: Control system upgrade | $30K        ││
│ │   Source: Referral | Yesterday 3:00 PM       ││
│ │   [Convert to Opp] [Schedule Call] [Notes]    ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ [+ New Lead]                     Showing 1-10/25   │
└─────────────────────────────────────────────────────┘
```

**Key Features:**
- Status filters (New, Qualified, Contacted, Lost)
- Search by name, company, email
- Sort by date, value, source
- Bulk actions (assign, archive)
- Quick qualify button
- Lead scoring indicator
- Convert to opportunity

**MCP Tools Used:**
- `list_leads` - Get leads with filters
- `get_lead` - View lead details
- `create_lead` - Add new lead
- `convert_lead_to_opportunity` - Convert qualified leads

---

### Page 3: Opportunities
**Purpose:** Track sales pipeline and close deals

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ INSA CRM │ Dashboard │ Leads │ Opportunities │ ... │
├─────────────────────────────────────────────────────┤
│ Sales Pipeline (18)                  Value: $850K   │
│                                                     │
│ Kanban View: [Qualification] [Proposal] [Negotiation] [Won]│
│                                                     │
│ ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────┐│
│ │ Separator│  │ Controls │  │ Retrofit │  │ Oil │  │
│ │ $50K     │  │ $30K     │  │ $20K     │  │$15K ││
│ │ 70%      │  │ 50%      │  │ 80%      │  │100% ││
│ │ Jan 15   │  │ Jan 30   │  │ Dec 20   │  │DONE ││
│ │ [View]   │  │ [View]   │  │ [View]   │  │[✓]  ││
│ └──────────┘  └──────────┘  └──────────┘  └─────┘│
│                                                     │
│ List View Toggle: [═] Kanban | [☰] List           │
│                                                     │
│ [+ New Opportunity]            [Generate Quote]     │
└─────────────────────────────────────────────────────┘
```

**Key Features:**
- Kanban board (drag & drop stages)
- List view alternative
- Probability percentage
- Expected close date
- Value indicators
- Stage progression
- Quick quote generation

**MCP Tools Used:**
- `list_opportunities` - Get pipeline
- `get_opportunity` - View details
- `create_opportunity` - New opportunity
- `update_opportunity` - Change stage/probability

---

### Page 4: Quotes & Proposals
**Purpose:** Generate and track quotations

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ INSA CRM │ Dashboard │ Leads │ Opportunities │ ... │
├─────────────────────────────────────────────────────┤
│ Quotes (12)                                         │
│                                                     │
│ Status: [All] [Draft] [Sent] [Accepted] [Expired] │
│                                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ QUOTE-2025-001                          SENT    ││
│ │ Customer: Acme Industries | $50,000            ││
│ │ Items: Separator X-1000, Installation          ││
│ │ Sent: Jan 10 | Valid until: Feb 10            ││
│ │ [View PDF] [Send Reminder] [Mark Won]         ││
│ ├─────────────────────────────────────────────────┤│
│ │ QUOTE-2025-002                         DRAFT   ││
│ │ Customer: TechCorp | $30,000                   ││
│ │ Items: Control Panel, PLC, HMI                 ││
│ │ Created: Jan 12 | Not sent yet                 ││
│ │ [Edit] [Generate PDF] [Send to Customer]      ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ [+ New Quote]  [AI Quote Generator]                │
└─────────────────────────────────────────────────────┘
```

**Key Features:**
- Status tracking (Draft, Sent, Accepted, Rejected, Expired)
- PDF generation
- Email integration
- Price calculator
- AI-powered quote generation
- Template library
- Approval workflow

**MCP Tools Used:**
- `list_quotations` - Get all quotes
- `create_quotation` - New quote
- `get_quotation` - View details
- Plus: AI Sizing Agent for automated quotes

---

### Page 5: Projects
**Purpose:** Track project execution and deliverables

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ INSA CRM │ Dashboard │ Leads │ Opportunities │ ... │
├─────────────────────────────────────────────────────┤
│ Projects (8 Active)                                 │
│                                                     │
│ Filters: [Active] [Planning] [On Hold] [Completed] │
│                                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ PRJ-2025-001: Oil Field Separator               ││
│ │ Customer: Acme | Value: $50K | Status: ACTIVE  ││
│ │ Progress: ████████░░░░░░░░░ 60%                ││
│ │ Tasks: 15/25 complete | Due: Feb 15, 2025      ││
│ │                                                  ││
│ │ Milestones:                                     ││
│ │ ✓ Design approved     ✓ CAD completed          ││
│ │ ◌ Manufacturing       ◌ Testing                ││
│ │ ◌ Delivery            ◌ Installation           ││
│ │                                                  ││
│ │ Team: Wil (PM), Juan (Eng), Maria (QC)        ││
│ │ [View Details] [Add Task] [Update Status]      ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ [+ New Project]                                     │
└─────────────────────────────────────────────────────┘
```

**Key Features:**
- Progress tracking
- Milestone management
- Task assignment
- Team collaboration
- Document storage
- Time tracking
- Gantt chart view

**MCP Tools Used:**
- `list_projects` - Get all projects
- `create_project` - New project
- `get_project` - View details
- Plus: Task management, team assignments

---

### Page 6: Customers
**Purpose:** Manage customer relationships and history

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ INSA CRM │ Dashboard │ Leads │ Opportunities │ ... │
├─────────────────────────────────────────────────────┤
│ Customers (45)                                      │
│                                                     │
│ Search: [____________]  Filter: [Active ▼]        │
│                                                     │
│ ┌─────────────────────────────────────────────────┐│
│ │ 🏢 Acme Industries                   ★★★★★      ││
│ │ Contact: John Smith | john@acme.com             ││
│ │ Industry: Oil & Gas | Location: Texas          ││
│ │                                                  ││
│ │ Relationship:                                   ││
│ │ • 3 Opportunities ($150K total)                 ││
│ │ • 2 Active Projects                             ││
│ │ • Last contact: 2 days ago                      ││
│ │ • Account Manager: Wil Aroca                    ││
│ │                                                  ││
│ │ [View History] [New Opportunity] [Schedule Call]││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ [+ New Customer]                                    │
└─────────────────────────────────────────────────────┘
```

**Key Features:**
- Company profile
- Contact management
- Relationship history
- Revenue tracking
- Activity timeline
- Credit limit
- Payment terms

**MCP Tools Used:**
- `list_customers` - Get all customers
- `get_customer` - View profile
- `create_customer` - Add customer
- Plus: Contact management, notes

---

### Page 7: Equipment Sizing (Engineering)
**Purpose:** Calculate equipment dimensions and specifications

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ INSA CRM │ Dashboard │ Leads │ Opportunities │ ... │
├─────────────────────────────────────────────────────┤
│ Equipment Sizing Calculator                         │
│                                                     │
│ Equipment Type: [Separator ▼]                      │
│                                                     │
│ Input Parameters:                                   │
│ ┌─────────────────────────────────────────────────┐│
│ │ Flow Rate:        [1000] m³/h                   ││
│ │ Pressure:         [50] bar                      ││
│ │ Temperature:      [60] °C                       ││
│ │ Fluid Type:       [Oil/Gas/Water]               ││
│ │ Density:          [850] kg/m³                   ││
│ │ Viscosity:        [20] cP                       ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ [Calculate] [AI Sizing] [Load Template]            │
│                                                     │
│ Results:                                            │
│ ┌─────────────────────────────────────────────────┐│
│ │ Recommended Model: X-1000                       ││
│ │ Dimensions: 2.5m diameter × 8m length          ││
│ │ Weight: 3,500 kg                                ││
│ │ Estimated Cost: $45,000                         ││
│ │ Delivery Time: 8 weeks                          ││
│ │                                                  ││
│ │ [Generate Quote] [Create CAD] [Save to Project]││
│ └─────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

**Key Features:**
- Equipment type selector
- Input parameter forms
- AI-powered calculations
- Template library
- Result visualization
- Quote generation
- CAD integration

**MCP Tools Used:**
- AI Sizing Agent (internal)
- CAD automation MCP
- Quote generation

---

### Page 8: Reports & Analytics
**Purpose:** Business intelligence and reporting

**Layout:**
```
┌─────────────────────────────────────────────────────┐
│ INSA CRM │ Dashboard │ Leads │ Opportunities │ ... │
├─────────────────────────────────────────────────────┤
│ Reports & Analytics                                 │
│                                                     │
│ Time Period: [This Month ▼]  Export: [PDF] [Excel]│
│                                                     │
│ Sales Performance                                   │
│ ┌─────────────────────────────────────────────────┐│
│ │ Revenue: $850K (↑ 15% vs last month)           ││
│ │ [Chart: Monthly revenue trend]                  ││
│ │                                                  ││
│ │ Pipeline by Stage:                              ││
│ │ Qualification: $200K (5 opps)                   ││
│ │ Proposal:      $300K (8 opps)                   ││
│ │ Negotiation:   $350K (5 opps)                   ││
│ │                                                  ││
│ │ Win Rate: 65% | Avg Deal Size: $47K            ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ Team Performance                                    │
│ ┌─────────────────────────────────────────────────┐│
│ │ Wil Aroca:   10 deals | $250K | 70% win rate  ││
│ │ Juan Casas:  8 deals  | $180K | 60% win rate  ││
│ │ Maria Lopez: 6 deals  | $120K | 75% win rate  ││
│ └─────────────────────────────────────────────────┘│
│                                                     │
│ [Generate Report] [Schedule Email] [More Analytics]│
└─────────────────────────────────────────────────────┘
```

**Key Features:**
- Revenue metrics
- Pipeline analysis
- Win/loss reports
- Team performance
- Forecast accuracy
- Custom reports
- Scheduled emails

---

## 🧭 Navigation System

### Top Navigation Bar
```
┌─────────────────────────────────────────────────────┐
│ INSA [Logo] │ Navigation Tabs                │ User │
│                                                     │
│ [Dashboard] [Leads] [Opportunities] [Quotes]       │
│ [Projects] [Customers] [Reports] [More ▼]          │
│                                            [Wil ▼]  │
└─────────────────────────────────────────────────────┘
```

### Global Search (Ctrl+K)
```
┌─────────────────────────────────────────────────────┐
│ 🔍 Search leads, opportunities, customers...        │
│                                                     │
│ Recent:                                             │
│ → Acme Industries (Customer)                        │
│ → QUOTE-2025-001 (Quote)                           │
│                                                     │
│ Quick Actions:                                      │
│ → + New Lead                                        │
│ → + New Opportunity                                 │
│ → Generate Quote                                    │
└─────────────────────────────────────────────────────┘
```

### User Menu
```
┌──────────────────────┐
│ Wil Aroca            │
│ w.aroca@insaing.com  │
├──────────────────────┤
│ My Tasks (5)         │
│ My Opportunities (12)│
│ Settings             │
│ Help & Support       │
│ Logout               │
└──────────────────────┘
```

---

## 🔧 Technical Implementation

### Routing System (Hash-based)
```javascript
// Simple client-side routing
const routes = {
  '#/dashboard': renderDashboard,
  '#/leads': renderLeads,
  '#/opportunities': renderOpportunities,
  '#/quotes': renderQuotes,
  '#/projects': renderProjects,
  '#/customers': renderCustomers,
  '#/sizing': renderSizing,
  '#/reports': renderReports
};

window.addEventListener('hashchange', () => {
  const route = window.location.hash || '#/dashboard';
  routes[route]?.();
});
```

### State Management
```javascript
const appState = {
  currentPage: 'dashboard',
  currentUser: { name: 'Wil Aroca', email: 'w.aroca@insaing.com' },
  filters: {},
  searchQuery: '',
  selectedItems: []
};
```

### API Integration
```javascript
// Connect to backend MCP tools
async function getLeads(filters = {}) {
  const response = await fetch('/api/erpnext/leads', {
    method: 'POST',
    body: JSON.stringify({ filters })
  });
  return await response.json();
}
```

---

## 📊 Database Schema (Simplified)

```sql
-- Leads table
CREATE TABLE leads (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255),
  company VARCHAR(255),
  email VARCHAR(255),
  phone VARCHAR(50),
  status VARCHAR(50), -- New, Qualified, Contacted, Converted, Lost
  source VARCHAR(100),
  value DECIMAL(10,2),
  assigned_to VARCHAR(255),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

-- Opportunities table
CREATE TABLE opportunities (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255),
  customer_id INTEGER,
  value DECIMAL(10,2),
  probability INTEGER,
  stage VARCHAR(50), -- Qualification, Proposal, Negotiation, Won, Lost
  expected_close DATE,
  assigned_to VARCHAR(255),
  created_at TIMESTAMP
);

-- Quotes table
CREATE TABLE quotes (
  id SERIAL PRIMARY KEY,
  quote_number VARCHAR(50),
  opportunity_id INTEGER,
  customer_id INTEGER,
  total_value DECIMAL(10,2),
  status VARCHAR(50), -- Draft, Sent, Accepted, Rejected, Expired
  valid_until DATE,
  items JSONB,
  created_at TIMESTAMP
);
```

---

## 🎯 Next Steps

1. **Implement routing system** - Hash-based navigation
2. **Create page templates** - Reusable layouts
3. **Build Leads page first** - Most critical workflow
4. **Add MCP tool integration** - Connect to ERPNext
5. **Implement search** - Global Ctrl+K search
6. **Add filters & sorting** - Table interactions
7. **Create forms** - New lead, opportunity, quote
8. **Build dashboard** - Metrics and widgets

---

**Status:** Architecture complete, ready to implement
**Priority:** Leads → Opportunities → Quotes → Dashboard
**Timeline:** 4-6 hours for full implementation

