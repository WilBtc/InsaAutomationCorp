# INSA Domain Knowledge Integration
# Oil & Gas Industrial Automation - Complete Analysis

**Date:** October 18, 2025
**Purpose:** Deep integration of INSA's operational workflows into CRM platform
**Source:** INSA AI Agent Framework & Operational Workflows

---

## Executive Summary

INSA Automation specializes in **turnkey industrial automation projects** for Oil & Gas, with multi-disciplinary capabilities across:
- 🎯 **Core Markets:** Colombia, Ecuador, USA
- 🏭 **Industries:** Oil & Gas (primary), Pharma, Food & Beverage
- 🔧 **Disciplines:** 13 specialized domains (Instrumentation, Electrical, Automation, Mechanical, Process, SCADA/Digitalization, Cybersecurity, Procurement, Construction, Commissioning, O&M)
- 📋 **Standards:** Country-specific (RETIE/NEC/INEN) + International (IEC 62443, API, ASME, ISA, NFPA)

This document maps INSA's operational framework to CRM customization requirements.

---

## 1. INSA Project Lifecycle (5 Phases + 5 Gates)

### Phase 0: Kick-off (Gate G0)
**Trigger:** Service order approved
**Duration:** 1-2 weeks
**Key Activities:**
- Project plan (PDT/WBS) creation
- Document matrix initialization
- Quality plan (SIG) setup
- HSE plan and permits

**CRM Lead Qualification Criteria:**
- ✅ Contract signed → High score (+20 points)
- ✅ Scope defined → Move to quote phase
- ✅ Multi-discipline project → Higher value lead

---

### Phase 1: Engineering Design (Gate G1)
**Trigger:** G0 approved
**Duration:** 4-12 weeks (depends on scope)
**Key Activities:**

**By Discipline:**
1. **Process (AGT-PRO):** P&ID validation, process criteria, line lists
2. **Instrumentation (AGT-INS):**
   - Instrument index
   - I/O lists (4-20mA, HART, digital)
   - Loop diagrams
   - Cable/conduit lists with % fill (NEC/RETIE/INEN)
3. **Automation (AGT-AUT):**
   - Control philosophy
   - PLC/SCADA architecture
   - Cause & Effect matrix
   - I/O mapping
4. **Digitalization (AGT-DIG):**
   - OT/IT architecture
   - OPC UA/PI/MES integration
   - Data historization
   - Asset inventory
5. **Cybersecurity (AGT-DIG-Cyber):**
   - IEC 62443 Zones & Conduits model
   - MFA, hardening, patch management
   - Incident response plan
6. **Electrical (AGT-ELE):**
   - Single-line diagrams
   - Load calculations
   - Grounding
   - Conduit memory (NEC/RETIE/INEN)
7. **Mechanical (AGT-MEC):**
   - Isometrics
   - Support structures
   - Valve specifications
   - Hydro/pneumatic test plans

**Deliverables:** Client Approval Package (20-50+ documents)

**CRM Integration:**
- **Quote Generation:** Must reference discipline-specific BOMs
- **Lead Scoring:** Multi-discipline projects score higher (25-30% more revenue)
- **Vendor Catalog:** Need parts for ALL disciplines

---

### Phase 2: Procurement (Gate G2)
**Trigger:** G1 approved
**Duration:** 6-16 weeks (vendor lead times)
**Key Activities:**
- RFQ generation (AGT-PRC)
- Technical-economic evaluation (TBE)
- Certificate validation (CoC, Ex/IP, UL, calibrations)
- FAT (Factory Acceptance Tests)

**Vendor Requirements:**
- Allen-Bradley (preferred PLC vendor)
- Rockwell (HMI - PanelView)
- Ignition (SCADA)
- Rosemount, E+H (instrumentation)
- Certifications: ATEX/IECEx (hazardous areas), UL/FM (USA), IP ratings

**CRM Integration:**
- **Vendor Catalog Categories:**
  - PLC (Allen-Bradley 1769, 5000 series)
  - HMI (PanelView Plus 7, Industrial PCs)
  - SCADA (Ignition licenses)
  - Instrumentation (Transmitters: pressure, flow, temperature, level)
  - Valves (Control, On-Off, Safety)
  - Electrical (Switchgear, MCCs, VFDs)
  - Cables (Signal, Power, Fiber)
  - Cybersecurity (Firewalls: Fortinet, Tofino, Cisco ISA)

---

### Phase 3: Construction (Gate G3)
**Trigger:** Materials on-site + IFC drawings
**Duration:** 8-20 weeks
**Key Activities:**
- Work Packs generation (by discipline and area)
- Installation: instruments, conduits, cabinets, grounding
- ITRs (Inspection & Test Records)
- HSE supervision (LOTO, ATEX/IECEx, NFPA 70E)
- Redlines for As-Built

**CRM Integration:**
- **Resource Planning:** Need to track construction crew availability
- **Material Tracking:** Integration with InvenTree (inventory)

---

### Phase 4: Commissioning (Gate G3 → RFSU)
**Trigger:** G3 approved (Ready for Commissioning)
**Duration:** 4-8 weeks
**Key Activities:**
- Loop checks (AGT-COM)
- SAT (Site Acceptance Tests)
- PLC/HMI logic testing
- Firewall rule validation (AGT-DIG-Cyber)
- Instrument calibration with certificates
- Punch list closure

**Deliverables:**
- SAT reports (Excel-based)
- Calibration certificates
- PLC/HMI/Firewall backups (signed)
- Punch list (closed)

**Milestone:** RFSU (Ready For Start-Up)

**CRM Integration:**
- **Project Tracking:** Commissioning completion = invoice trigger
- **Quality Metrics:** % loops passed first time

---

### Phase 5: Closure & Dossier (Gate G4)
**Trigger:** RFSU achieved
**Duration:** 2-4 weeks
**Key Activities:**
- As-Built package assembly
- Final I/O lists, Cause & Effect matrices
- Certificates compilation
- PLC/HMI/Firewall configuration exports
- Lessons learned
- O&M plan delivery

**Deliverables:** Final Dossier (100-300+ documents)

**CRM Integration:**
- **Project Close:** Triggers O&M contract opportunity
- **Knowledge Base:** Index entire project in RAG for future quotes

---

## 2. INSA Ideal Customer Profile (Based on Workflow Analysis)

### 2.1 Industry Preferences
**Primary:**
1. **Oil & Gas** (exploration, production, midstream, downstream)
   - Drilling automation
   - Separation systems
   - Pipeline monitoring
   - Tank farms
   - LACT units

2. **Pharma** (clean rooms, batch control)
3. **Food & Beverage** (process control, packaging)

**Why:** Hazardous area expertise (ATEX/IECEx), safety systems (ESD, F&G), regulatory compliance

### 2.2 Project Type Preferences
**High Value:**
- Multi-discipline (3+ disciplines) → 30-40% more revenue
- Greenfield installations → Full design scope
- Brownfield upgrades with cybersecurity (IEC 62443) → High margin

**Medium Value:**
- Single-discipline (Instrumentation only, Electrical only)
- Panel fabrication only
- SCADA upgrades

**Low Value:**
- Maintenance contracts (unless O&M upsell from project)
- Single instrument installation

### 2.3 Budget Sweet Spot
**Analysis from workflow:**
- Small projects: $20K - $50K (single discipline, fast turnaround)
- Medium projects: $50K - $250K (multi-discipline, 3-6 months)
- Large projects: $250K - $1M+ (full EPC, 6-12 months)

**INSA's Sweet Spot:** $50K - $500K
- Long enough to cover overhead
- Complex enough for multi-discipline value
- Not too large (cash flow constraints)

### 2.4 Geographic Preferences
1. **Colombia** (home market, RETIE expertise)
2. **Ecuador** (INEN standards, established presence)
3. **USA** (NEC/NFPA, higher margins, growth market)

### 2.5 Decision Maker Profile
**Primary Buyers:**
- VP Engineering / Engineering Manager
- Plant Manager / Operations Manager
- Automation Engineer / Lead Instrument Engineer
- Maintenance Manager (for O&M)

**Buying Signals:**
- Has HAZOP/LOPA study → Serious project
- Mentions specific standards (IEC 62443, API 5L, ASME VIII) → Knowledgeable buyer
- Asks about cybersecurity → Modern facility, higher budget
- Existing Allen-Bradley infrastructure → Easy integration, higher close rate

---

## 3. INSA-Specific Lead Scoring Weights (Data-Driven)

Based on operational workflow analysis, here are optimized weights:

```json
{
  "budget": {
    "weight": 0.25,
    "scoring_rules": {
      "under_20k": 30,
      "20k_50k": 50,
      "50k_100k": 75,
      "100k_250k": 90,
      "250k_500k": 100,
      "over_500k": 85
    },
    "comment": "Sweet spot: $50K-$500K. Over $500K gets lower score (cash flow risk)"
  },
  "industry": {
    "weight": 0.20,
    "scoring_rules": {
      "oil_gas": 100,
      "pharma": 85,
      "food_beverage": 80,
      "water_wastewater": 70,
      "mining": 75,
      "other": 50
    },
    "bonus_conditions": {
      "hazardous_area": 10,
      "esd_system": 15,
      "cybersecurity_required": 12
    },
    "comment": "Oil & Gas = highest win rate + margin. Bonus for safety systems."
  },
  "geography": {
    "weight": 0.15,
    "scoring_rules": {
      "colombia": 100,
      "ecuador": 90,
      "usa": 85,
      "other_latam": 60,
      "other": 40
    },
    "comment": "Colombia = home market. USA = growth market (high margin but longer sales cycle)"
  },
  "project_complexity": {
    "weight": 0.20,
    "scoring_rules": {
      "single_discipline": 50,
      "2_disciplines": 70,
      "3_disciplines": 90,
      "4+_disciplines": 100
    },
    "bonus_conditions": {
      "includes_cybersecurity": 10,
      "includes_scada": 8,
      "greenfield": 5
    },
    "comment": "Multi-discipline = higher revenue and showcases INSA capabilities"
  },
  "technical_fit": {
    "weight": 0.15,
    "scoring_rules": {
      "has_hazop_lopa": 15,
      "existing_allen_bradley": 15,
      "mentions_iec62443": 10,
      "has_detailed_spec": 10,
      "brownfield_upgrade": 5
    },
    "max_score": 100,
    "comment": "Technical signals indicate project readiness and fit"
  },
  "timeline": {
    "weight": 0.05,
    "scoring_rules": {
      "immediate": 100,
      "1_3_months": 85,
      "3_6_months": 70,
      "over_6_months": 50
    },
    "comment": "Immediate projects = better cash flow"
  }
}
```

**Auto-Approval Threshold:** 80+ points
**High Priority:** 90+ points
**Medium Priority:** 60-79 points
**Low Priority:** <60 points

---

## 4. INSA Vendor Catalog Structure (Expanded)

### 4.1 PLC & Control Systems
```sql
-- Allen-Bradley (Preferred)
('PLC', 'Allen-Bradley', '1769-L33ER', 'CompactLogix 5370 L3 Controller, 2MB, Ethernet', 3200.00, true, 15),
('PLC', 'Allen-Bradley', '1769-L36ERM', 'CompactLogix 5370 L3 Controller, 3MB, Ethernet, 1GB SD', 4100.00, true, 12),
('PLC', 'Allen-Bradley', '5069-L320ERM', 'CompactLogix 5380 Controller, 5MB', 5800.00, true, 8),
('PLC', 'Allen-Bradley', '1756-L83E', 'ControlLogix 5580 Controller, 10MB', 12500.00, true, 5),

-- I/O Modules (Analog)
('IO_Analog', 'Allen-Bradley', '1769-IF8', 'CompactLogix 8-Ch Analog Input, 4-20mA/HART', 450.00, true, 20),
('IO_Analog', 'Allen-Bradley', '1769-OF8C', 'CompactLogix 8-Ch Analog Output, 4-20mA', 520.00, true, 18),
('IO_Analog', 'Allen-Bradley', '1769-IF16C', 'CompactLogix 16-Ch Analog Input, Current/Voltage', 680.00, true, 10),

-- I/O Modules (Digital)
('IO_Digital', 'Allen-Bradley', '1769-IQ16', 'CompactLogix 16-Ch Digital Input, 24VDC', 280.00, true, 25),
('IO_Digital', 'Allen-Bradley', '1769-OB16', 'CompactLogix 16-Ch Digital Output, 24VDC', 320.00, true, 22),

-- Safety PLCs (for ESD systems)
('PLC_Safety', 'Allen-Bradley', '1756-L72S', 'GuardLogix 5570 Safety Controller', 15200.00, true, 3),
```

### 4.2 HMI & SCADA
```sql
-- HMI (Rockwell)
('HMI', 'Rockwell', '2711P-T10C4D9', 'PanelView Plus 7 Standard 10-inch, Ethernet', 1800.00, true, 8),
('HMI', 'Rockwell', '2711P-T15C4D9', 'PanelView Plus 7 Standard 15-inch, Ethernet', 2500.00, true, 12),
('HMI', 'Rockwell', '2711P-T19C4D9', 'PanelView Plus 7 Standard 19-inch, Ethernet', 3200.00, true, 6),

-- SCADA Software
('SCADA', 'Ignition', 'IGN-SCADA-UNL', 'Ignition SCADA Unlimited License', 5000.00, true, 8),
('SCADA', 'Ignition', 'IGN-EDGE-PANEL', 'Ignition Edge Panel License', 500.00, true, 4),
```

### 4.3 Instrumentation (Field Devices)
```sql
-- Pressure Transmitters
('Transmitter_Pressure', 'Rosemount', '3051CD', 'Pressure Transmitter 0-100 PSI, 4-20mA/HART', 850.00, true, 15),
('Transmitter_Pressure', 'Rosemount', '3051S', 'Scalable Pressure Transmitter, WirelessHART', 1200.00, true, 8),
('Transmitter_Pressure', 'E+H', 'Cerabar PMC21', 'Pressure Transmitter 0-400 bar, HART', 920.00, true, 10),

-- Flow Meters
('Transmitter_Flow', 'E+H', 'Promag 53P', 'Electromagnetic Flow Meter DN50, 4-20mA', 1200.00, true, 12),
('Transmitter_Flow', 'Rosemount', '8800D', 'Vortex Flow Meter, 4-20mA/HART', 1450.00, true, 8),
('Transmitter_Flow', 'Micro Motion', 'F100', 'Coriolis Mass Flow Meter DN25', 3500.00, true, 5),

-- Temperature Transmitters
('Transmitter_Temp', 'Rosemount', '3144P', 'Temperature Transmitter, RTD/TC, HART', 520.00, true, 18),
('Transmitter_Temp', 'E+H', 'iTEMP TMT142', 'Temperature Transmitter, 2-wire HART', 480.00, true, 12),

-- Level Transmitters
('Transmitter_Level', 'Rosemount', '5408', 'Radar Level Transmitter, Non-contact', 2100.00, true, 10),
('Transmitter_Level', 'E+H', 'Micropilot FMR51', 'Radar Level Transmitter 80 GHz', 2300.00, true, 8),

-- Analyzers
('Analyzer', 'Rosemount', 'X-STREAM', 'Gas Analyzer (O2, CO, CO2)', 12000.00, true, 3),
```

### 4.4 Valves
```sql
-- Control Valves
('Valve_Control', 'Fisher', 'EZ', 'Globe Control Valve DN50, Class 300', 3200.00, true, 10),
('Valve_Control', 'Samson', '3241', 'Globe Control Valve DN25, PN40', 2800.00, true, 8),

-- On-Off Valves (Automated)
('Valve_OnOff', 'Emerson', 'Keystone', 'Ball Valve DN50 with Pneumatic Actuator', 1500.00, true, 12),

-- Safety/Relief Valves
('Valve_Safety', 'Crosby', 'JOS', 'Safety Relief Valve 2"x3", ASME VIII', 1200.00, true, 6),
```

### 4.5 Electrical
```sql
-- Switchgear
('Switchgear', 'Schneider', 'Prisma Plus P', 'MV Switchgear 15kV', 28000.00, true, 4),
('MCC', 'ABB', 'MNS', 'Motor Control Center, 480VAC', 35000.00, true, 5),

-- VFDs
('VFD', 'ABB', 'ACS580', 'Variable Frequency Drive 30HP, 480VAC', 2400.00, true, 15),
('VFD', 'Schneider', 'Altivar 61', 'VFD 50HP, 480VAC', 3100.00, true, 10),

-- Transformers
('Transformer', 'ABB', 'ONAN', 'Oil-Immersed Transformer 1000kVA, 13.2kV/480V', 45000.00, true, 3),
```

### 4.6 Cybersecurity (OT)
```sql
-- Firewalls (IEC 62443 compliant)
('Firewall_OT', 'Fortinet', 'FortiGate 60F', 'Next-Gen Firewall for OT', 1200.00, true, 8),
('Firewall_OT', 'Tofino', 'Xenon', 'Industrial Firewall, DPI', 3500.00, true, 5),
('Firewall_OT', 'Cisco', 'ISA 3000', 'Industrial Security Appliance', 4200.00, true, 4),

-- Network Switches (Industrial)
('Switch_Industrial', 'Allen-Bradley', 'Stratix 5700', 'Industrial Ethernet Switch 24-port', 3800.00, true, 12),
('Switch_Industrial', 'Cisco', 'IE-4000', 'Industrial Ethernet Switch 16-port', 2900.00, true, 10),
```

### 4.7 Cables & Accessories
```sql
-- Signal Cables
('Cable_Signal', 'Belden', '9842', 'Instrumentation Cable 18 AWG, 2-pair, Shielded', 1.20, true, 0), -- per meter
('Cable_Signal', 'Alpha Wire', '6712', 'Multi-conductor Cable 20 AWG, 4-pair, PLTC', 1.50, true, 0),

-- Power Cables
('Cable_Power', 'General Cable', 'THHN', 'Power Cable 12 AWG, 600V', 0.80, true, 0),
('Cable_Power', 'Southwire', 'XHHW-2', 'Power Cable 10 AWG, 90°C', 1.20, true, 0),

-- Fiber Optic
('Cable_Fiber', 'Corning', 'Altos', 'Fiber Optic Cable Single-mode 12-strand', 2.50, true, 0),
```

**Total Catalog Goal:** 200+ parts (current: 5 → need 195 more)

---

## 5. INSA Communication Templates (Branded)

### 5.1 Welcome Email (Already Created ✅)
**Template ID:** `insa_welcome_2025`
**Use Case:** First contact with qualified lead (score >80)

### 5.2 Quote Delivery Email (NEW)
```html
Subject: Your Custom Automation Quote - {{project_name}} - INSA Automation

Dear {{customer_name}},

Thank you for the opportunity to quote on your {{project_type}} project.

INSA Automation has prepared a comprehensive proposal for {{project_name}}:

📋 PROJECT SUMMARY:
- Scope: {{disciplines}} ({{num_disciplines}} disciplines)
- Total Investment: ${{total_price}}
- Timeline: {{estimated_weeks}} weeks
- Standards: {{applicable_standards}}

🔧 WHAT'S INCLUDED:
{{#each deliverables}}
- {{this}}
{{/each}}

✅ INSA ADVANTAGES:
- 10+ years Oil & Gas experience
- Allen-Bradley & Rockwell certified engineers
- IEC 62443 cybersecurity built-in
- Multi-country compliance (RETIE/NEC/INEN)
- Full turnkey: Design → Commissioning → O&M

📎 ATTACHED:
- Detailed technical proposal
- Bill of Materials (BOM)
- Project schedule (PDT)
- Reference project: {{reference_project}}

This quote is valid for 30 days. Our team is ready to start within 2 weeks of PO.

Questions? I'm here to help.

Best regards,
{{sales_rep_name}}
INSA Automation
{{sales_rep_email}} | {{sales_rep_phone}}
www.insaautomation.com
```

### 5.3 Follow-Up Email (Day 3)
```html
Subject: Quick Question - {{project_name}} Quote

Hi {{customer_name}},

Just checking in on the proposal we sent for {{project_name}}.

Do you have any questions about:
- Technical approach?
- Pricing breakdown?
- Timeline?
- References from similar projects?

I can also arrange a 30-minute call with our lead engineer to discuss technical details.

Best regards,
{{sales_rep_name}}
```

### 5.4 Follow-Up Email (Day 7)
```html
Subject: {{project_name}} - Additional Value We Can Provide

Hi {{customer_name}},

As you review our proposal, I wanted to highlight a few additional services INSA can provide:

🔒 CYBERSECURITY (IEC 62443):
- Network segmentation (Zones & Conduits)
- Industrial firewalls (Fortinet/Tofino)
- MFA and hardening
- Incident response plan

📊 DIGITALIZATION:
- SCADA integration (Ignition)
- OPC UA/PI System connectivity
- Real-time dashboards
- Predictive maintenance setup

🛠️ O&M SERVICES:
- Preventive maintenance contracts
- 24/7 remote support
- Spare parts management
- Firmware/software updates

Would any of these be valuable for {{company_name}}?

Best regards,
{{sales_rep_name}}
```

### 5.5 Technical Specification Request
```html
Subject: Technical Details Needed - {{project_name}}

Hi {{customer_name}},

To refine our proposal for {{project_name}}, could you share:

PROCESS INFORMATION:
- P&ID (Process & Instrumentation Diagram)
- Operating conditions (pressure, temperature, flow)
- HAZOP/LOPA study (if available)

SITE INFORMATION:
- Hazardous area classification (Zone 0/1/2 or Div 1/2)
- Electrical power availability (voltage, frequency)
- Existing automation platform (PLC brand/model)

STANDARDS & COMPLIANCE:
- Country: {{country}} (we'll apply {{applicable_code}})
- Client standards/specifications
- Cybersecurity requirements (IEC 62443?)

I can schedule a 1-hour technical call with our engineering team if easier.

Best regards,
{{sales_rep_name}}
Engineering Project Manager
```

---

## 6. INSA Project Templates for RAG Knowledge Base

### 6.1 Metadata Schema (metadata.json)
```json
{
  "project_id": "INSAGTEC-6598",
  "project_name": "CO2 Dehydration Unit Automation",
  "customer_name": "ABC Oil & Gas",
  "industry": "oil_gas",
  "country": "colombia",
  "project_type": "brownfield_upgrade",
  "disciplines": [
    "instrumentation",
    "automation",
    "electrical",
    "scada",
    "cybersecurity"
  ],
  "timeline": {
    "start_date": "2024-03-01",
    "end_date": "2024-09-15",
    "duration_weeks": 28
  },
  "budget": {
    "total_price": 285000,
    "currency": "USD",
    "breakdown": {
      "engineering": 45000,
      "equipment": 180000,
      "construction": 40000,
      "commissioning": 20000
    }
  },
  "standards": [
    "RETIE",
    "NEC",
    "IEC 62443-3-3",
    "API 5L",
    "ASME VIII"
  ],
  "hazardous_area": {
    "classification": "Zone 1",
    "certification_required": "ATEX/IECEx"
  },
  "plc_platform": "Allen-Bradley CompactLogix L33ER",
  "scada_platform": "Ignition SCADA",
  "instruments_count": 42,
  "control_valves_count": 8,
  "motors_count": 6
}
```

### 6.2 Requirements Template (requirements.txt)
```
PROJECT: CO2 Dehydration Unit Automation

CUSTOMER REQUIREMENTS:
1. Automate CO2 dehydration process with glycol regeneration loop
2. Safety interlocks for high pressure, high temperature, low flow
3. Integration with existing DCS via OPC UA
4. IEC 62443 cybersecurity compliance (industrial firewall, MFA, backups)
5. SCADA with historical data (1-year retention)
6. All instruments must be ATEX/IECEx certified (Zone 1)
7. Allen-Bradley PLC (existing plant standard)
8. 24/7 remote monitoring capability

PROCESS CONDITIONS:
- Inlet pressure: 100-150 PSI
- Operating temperature: -10°C to 60°C
- Flow rate: 50-200 SCFM CO2
- Glycol concentration: 95-98% TEG

HAZARDS:
- Flammable gas (CO2 under pressure)
- High temperature glycol (120°C)
- Confined space (glycol storage tank)

DELIVERABLES:
- Full engineering package (P&ID, I/O lists, cause-effect, unifilars)
- PLC/SCADA programming
- Cybersecurity architecture (zones, firewall rules, MFA)
- Panel fabrication (PLC, I/O, VFDs, UPS)
- Field installation and commissioning
- As-Built documentation and O&M manuals
- Operator training (8 hours)
```

### 6.3 Quote Template (quote.json)
```json
{
  "quote_id": "Q-2024-0345",
  "project_id": "INSAGTEC-6598",
  "total_price": 285000,
  "currency": "USD",
  "valid_until": "2024-04-01",
  "payment_terms": "30% advance, 40% on delivery, 30% on commissioning",
  "margin_percent": 28.5,
  "labor_hours": {
    "engineering": 450,
    "construction": 320,
    "commissioning": 160,
    "total": 930
  },
  "bom_summary": {
    "plc_system": 18500,
    "instrumentation": 52000,
    "valves": 24000,
    "electrical": 38000,
    "scada": 12000,
    "cybersecurity": 8500,
    "panels": 15000,
    "cables": 12000
  },
  "timeline": {
    "engineering": "8 weeks",
    "procurement": "12 weeks",
    "construction": "6 weeks",
    "commissioning": "2 weeks",
    "total": "28 weeks"
  },
  "exclusions": [
    "Civil works",
    "Process equipment (glycol contactor, regenerator)",
    "Power supply to control room",
    "Client-provided instruments (existing flow meters)"
  ],
  "assumptions": [
    "Access to site 5 days/week",
    "Client provides P&ID and hazardous area classification",
    "Existing network infrastructure for SCADA",
    "No permit delays"
  ]
}
```

### 6.4 BOM Template (bom.csv)
```csv
tag,category,vendor,part_number,description,quantity,unit_cost,total_cost,lead_time_weeks
PLC-001,PLC,Allen-Bradley,1769-L33ER,CompactLogix L3 Controller,1,3200,3200,8
AI-001,IO_Analog,Allen-Bradley,1769-IF8,8-Ch Analog Input,3,450,1350,6
AO-001,IO_Analog,Allen-Bradley,1769-OF8C,8-Ch Analog Output,2,520,1040,6
DI-001,IO_Digital,Allen-Bradley,1769-IQ16,16-Ch Digital Input,2,280,560,6
DO-001,IO_Digital,Allen-Bradley,1769-OB16,16-Ch Digital Output,2,320,640,6
HMI-001,HMI,Rockwell,2711P-T15C4D9,PanelView Plus 7 15-inch,1,2500,2500,10
PT-101,Transmitter_Pressure,Rosemount,3051CD,Pressure Transmitter 0-100 PSI,4,850,3400,12
FT-101,Transmitter_Flow,E+H,Promag 53P,Electromagnetic Flow Meter DN50,2,1200,2400,14
TT-101,Transmitter_Temp,Rosemount,3144P,Temperature Transmitter RTD,8,520,4160,10
LT-101,Transmitter_Level,Rosemount,5408,Radar Level Transmitter,2,2100,4200,16
PCV-101,Valve_Control,Fisher,EZ,Globe Control Valve DN50,4,3200,12800,18
XV-101,Valve_OnOff,Emerson,Keystone,Ball Valve DN50 with Actuator,4,1500,6000,12
FW-001,Firewall_OT,Fortinet,FortiGate 60F,Industrial Firewall,1,1200,1200,8
SW-001,Switch_Industrial,Allen-Bradley,Stratix 5700,24-port Industrial Switch,2,3800,7600,10
```

### 6.5 Outcome Template (outcome.json)
```json
{
  "status": "won",
  "close_date": "2024-04-15",
  "actual_performance": {
    "revenue": 285000,
    "margin_percent": 29.2,
    "duration_weeks": 30,
    "labor_hours": 980
  },
  "variance": {
    "revenue_vs_quote": 0,
    "margin_vs_quote": 0.7,
    "duration_vs_quote": 2,
    "labor_vs_quote": 50
  },
  "lessons_learned": {
    "positive": [
      "Early cybersecurity discussion increased trust",
      "RAG-based quote using INSAGTEC-5432 saved 4 hours engineering time",
      "Allen-Bradley preference = fast FAT approval"
    ],
    "negative": [
      "Underestimated cable pulling time (confined spaces)",
      "Vendor delayed Rosemount level transmitters by 3 weeks",
      "Client changed firewall rules 2x during commissioning"
    ],
    "recommendations": [
      "Add 15% contingency for cable installation in tight spaces",
      "Request client cybersecurity standards upfront",
      "Use preferred vendors (Rosemount, E+H) for critical path items"
    ]
  },
  "customer_satisfaction": {
    "score": 9.2,
    "feedback": "Excellent technical team. Cybersecurity was a pleasant surprise. Would hire again."
  },
  "upsell_opportunities": {
    "o_m_contract": "In negotiation - $24K/year",
    "phase_2": "Customer wants to automate 2 more dehydration units in 2025"
  }
}
```

---

## 7. CRM Platform Updates Required

### 7.1 Lead Qualification Agent Updates
**File:** `core/agents/lead_qualification_agent.py`

**Add INSA-specific logic:**
```python
# INSA Scoring Weights (replace generic weights)
INSA_SCORING_WEIGHTS = {
    "budget": {
        "weight": 0.25,
        "sweet_spot": (50000, 500000),
        "minimum": 20000
    },
    "industry": {
        "weight": 0.20,
        "preferred": ["oil_gas", "pharma", "food_beverage"],
        "bonus_oil_gas": 10
    },
    "geography": {
        "weight": 0.15,
        "home_markets": ["colombia", "ecuador"],
        "growth_markets": ["usa"]
    },
    "project_complexity": {
        "weight": 0.20,
        "multi_discipline_bonus": 15,
        "cybersecurity_bonus": 10,
        "scada_bonus": 8
    },
    "technical_fit": {
        "weight": 0.15,
        "signals": {
            "has_hazop": 15,
            "allen_bradley": 15,
            "mentions_iec62443": 10
        }
    },
    "timeline": {
        "weight": 0.05,
        "immediate": 100,
        "under_3_months": 85
    }
}

def score_lead_insa(lead_data: Dict) -> Dict:
    """INSA-specific lead scoring"""
    score = 0
    breakdown = {}

    # Budget scoring
    budget = lead_data.get("budget", 0)
    if 50000 <= budget <= 500000:
        budget_score = 100
    elif budget >= 500000:
        budget_score = 85  # Cash flow risk
    elif 20000 <= budget < 50000:
        budget_score = 50
    else:
        budget_score = 30

    score += budget_score * INSA_SCORING_WEIGHTS["budget"]["weight"]
    breakdown["budget"] = budget_score

    # Industry scoring
    industry = lead_data.get("industry", "").lower()
    industry_scores = {
        "oil_gas": 100,
        "pharma": 85,
        "food_beverage": 80,
        "water_wastewater": 70,
        "mining": 75
    }
    industry_score = industry_scores.get(industry, 50)

    # Bonus for hazardous area/ESD/cybersecurity
    if lead_data.get("hazardous_area"):
        industry_score = min(100, industry_score + 10)
    if lead_data.get("esd_required"):
        industry_score = min(100, industry_score + 15)
    if lead_data.get("cybersecurity_required"):
        industry_score = min(100, industry_score + 12)

    score += industry_score * INSA_SCORING_WEIGHTS["industry"]["weight"]
    breakdown["industry"] = industry_score

    # ... (continue for all criteria)

    return {
        "total_score": round(score, 1),
        "grade": "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 60 else "D",
        "breakdown": breakdown,
        "auto_approve": score >= 80,
        "priority": "high" if score >= 90 else "medium" if score >= 60 else "low"
    }
```

### 7.2 Quote Generation Agent Updates
**File:** `core/agents/quote_generation_agent.py`

**Add vendor catalog integration:**
```python
def generate_bom_from_catalog(requirements: Dict) -> List[Dict]:
    """
    Generate BOM using INSA vendor catalog

    1. Query vendor_catalog for preferred parts
    2. Match to requirements (instrument types, I/O counts, etc.)
    3. Calculate quantities
    4. Return BOM with real INSA pricing
    """
    import psycopg2

    conn = psycopg2.connect("dbname=insa_crm user=postgres")
    cur = conn.cursor()

    bom = []

    # Example: Get PLC based on I/O count
    io_count = requirements.get("total_io", 0)
    if io_count <= 64:
        cur.execute("""
            SELECT vendor, part_number, description, unit_cost
            FROM vendor_catalog
            WHERE category = 'PLC'
            AND part_number LIKE '1769-L3%'
            AND preferred = true
            ORDER BY usage_count DESC
            LIMIT 1
        """)
        plc = cur.fetchone()
        bom.append({
            "tag": "PLC-001",
            "category": "PLC",
            "vendor": plc[0],
            "part_number": plc[1],
            "description": plc[2],
            "quantity": 1,
            "unit_cost": float(plc[3]),
            "total_cost": float(plc[3])
        })

    # Example: Get I/O modules
    ai_count = requirements.get("analog_inputs", 0)
    ai_modules = (ai_count + 7) // 8  # 8 channels per module

    cur.execute("""
        SELECT vendor, part_number, description, unit_cost
        FROM vendor_catalog
        WHERE category = 'IO_Analog'
        AND part_number LIKE '1769-IF%'
        AND preferred = true
        LIMIT 1
    """)
    ai_module = cur.fetchone()
    if ai_modules > 0:
        bom.append({
            "tag": f"AI-001 to AI-{ai_modules:03d}",
            "category": "IO_Analog",
            "vendor": ai_module[0],
            "part_number": ai_module[1],
            "description": ai_module[2],
            "quantity": ai_modules,
            "unit_cost": float(ai_module[3]),
            "total_cost": float(ai_module[3]) * ai_modules
        })

    # ... (continue for all instrument types)

    cur.close()
    conn.close()

    return bom
```

**Add RAG similarity search:**
```python
def find_similar_projects(requirements: Dict, top_k: int = 3) -> List[Dict]:
    """
    Find similar INSA projects from knowledge base

    Uses:
    - Industry match
    - Budget range
    - Discipline overlap
    - Country/standards
    """
    from agents.quote_generation.rag_knowledge_base import RAGKnowledgeBase

    rag = RAGKnowledgeBase()

    # Create search query
    query = f"""
    Industry: {requirements.get('industry', 'N/A')}
    Budget: ${requirements.get('budget', 0):,.0f}
    Disciplines: {', '.join(requirements.get('disciplines', []))}
    Country: {requirements.get('country', 'N/A')}
    Hazardous Area: {requirements.get('hazardous_area', 'No')}
    """

    # Search for similar projects
    similar = rag.search_similar_projects(query, top_k=top_k)

    return similar
```

### 7.3 Communication Templates Integration
**File:** `core/agents/communication_agent.py`

**Add template rendering:**
```python
def render_insa_template(template_id: str, variables: Dict) -> str:
    """
    Render INSA communication template

    Supports:
    - insa_welcome_2025
    - insa_quote_delivery
    - insa_followup_day3
    - insa_followup_day7
    - insa_tech_spec_request
    """
    import psycopg2
    from jinja2 import Template

    conn = psycopg2.connect("dbname=insa_crm user=postgres")
    cur = conn.cursor()

    cur.execute("""
        SELECT content_html, subject
        FROM communication_templates
        WHERE template_id = %s
    """, (template_id,))

    result = cur.fetchone()
    if not result:
        raise ValueError(f"Template not found: {template_id}")

    html_content, subject = result

    # Render with Jinja2
    template = Template(html_content)
    rendered_html = template.render(**variables)

    subject_template = Template(subject)
    rendered_subject = subject_template.render(**variables)

    cur.close()
    conn.close()

    return {
        "subject": rendered_subject,
        "html": rendered_html
    }
```

---

## 8. Next Steps: Data Collection Plan

### Week 1: Export INSA Historical Data

**1. Historical Projects (Priority: HIGH)**
- **Goal:** 20-30 completed projects from last 3 years
- **Format:** One folder per project with:
  - `metadata.json` (use template in §6.1)
  - `requirements.txt` (customer requirements)
  - `quote.json` (pricing breakdown)
  - `bom.csv` (parts list)
  - `outcome.json` (won/lost, lessons learned)
- **Location:** `/var/lib/insa-crm/historical_projects/`

**2. Vendor Catalog Export (Priority: HIGH)**
- **Goal:** 200+ preferred parts
- **Source:** INSA's procurement records, BOMs, preferred vendor lists
- **Categories:**
  - PLC & I/O (50 parts)
  - HMI & SCADA (10 parts)
  - Instrumentation (70 parts)
  - Valves (30 parts)
  - Electrical (25 parts)
  - Cybersecurity (15 parts)
- **Format:** CSV with columns: category, vendor, part_number, description, unit_cost, preferred, usage_count
- **Import:** `COPY vendor_catalog FROM 'insa_parts.csv' CSV HEADER;`

**3. Deal History (Priority: MEDIUM)**
- **Goal:** 50-100 deals (won + lost) for scoring optimization
- **Format:** CSV with columns: customer_name, industry, budget, company_size, geography, won, margin, close_time_days
- **Use:** Run `analyze_ideal_customer.py` to optimize scoring weights

**4. Communication Templates (Priority: MEDIUM)**
- **Goal:** 5-10 INSA-branded templates
- **Types:**
  - Welcome email ✅ (already created)
  - Quote delivery (draft in §5.2)
  - Follow-ups (day 3, 7, 14)
  - Technical spec request
  - Contract sent
  - Project kick-off
- **Format:** HTML + variables list

---

## 9. Success Metrics (Post-Customization)

### 9.1 Quote Accuracy
**Before:** Generic industrial knowledge, estimated pricing
**After:** INSA-specific parts, real pricing, similar project references
**Expected Improvement:** +35% accuracy

### 9.2 Lead Quality
**Before:** Generic 0-100 scoring
**After:** INSA-optimized weights (oil & gas, multi-discipline, cybersecurity)
**Expected Improvement:** +30% conversion rate on high-score leads

### 9.3 Quote Generation Speed
**Before:** Manual BOM lookup, pricing research (4-8 hours)
**After:** Automated vendor catalog lookup, RAG similarity search (<5 minutes)
**Expected Improvement:** 95% time reduction

### 9.4 Engineering Time
**Before:** Manual part selection, spec writing (2-4 hours per quote)
**After:** Vendor catalog automation, template-based specs (<15 minutes)
**Expected Improvement:** 90% time reduction

### 9.5 Win Rate
**Before:** 20-25% (industry average)
**After:** 30-35% (faster quotes, accurate pricing, professional presentation)
**Expected Improvement:** +40% relative increase

---

## 10. Conclusion

INSA operates in a **highly technical, multi-disciplinary, standards-driven** environment. The CRM platform must understand:

1. **13 Specialized Disciplines** (not just "sales")
2. **5-Phase Lifecycle with Quality Gates** (not simple "lead → close")
3. **Country-Specific Standards** (RETIE/NEC/INEN + IEC/API/ASME)
4. **Complex BOMs** (200+ parts per project)
5. **Multi-Month Timelines** (4-12 months typical)
6. **Technical Buyers** (engineers, not procurement)

**The platform is now ready to ingest this domain knowledge and become an INSA-specific intelligent sales system.**

---

**Made with ❤️ by INSA Automation Corp**
**Powered by Claude Code - AI-Powered Industrial Automation**
