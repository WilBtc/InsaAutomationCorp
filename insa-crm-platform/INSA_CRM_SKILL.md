# INSA Automation Corp - Complete CRM Skill Package
## Industrial Automation | Energy Optimization | Industrial Cybersecurity

**Version:** 2.0 (Colombia + US Operations)
**Last Updated:** October 23, 2025
**Coverage:** Colombia & United States
**Languages:** Spanish & English

---

## 📋 Skill Overview

This comprehensive skill enables Claude Code agents to operate Insa Automation Corp's CRM system for:
- Industrial automation engineering (PLC, SCADA, DCS, HMI)
- Energy optimization and efficiency projects
- Industrial cybersecurity (IEC 62443, NERC CIP, NIST CSF)
- Multi-regional operations (Colombia & United States)
- Compliance management and documentation

---

## 🌎 Geographic Coverage

### Colombia 🇨🇴
- **Primary Markets**: Oil & Gas, Mining, Manufacturing, Food & Beverage, Utilities
- **Key Regions**: Bogotá, Medellín, Cali, Barranquilla, Llanos Orientales, Caribbean Coast
- **Regulations**: RETIE, NTC Standards, MinMinas, SG-SST
- **Voltage**: 220V/440V, 60Hz (IEC equipment)
- **Language**: Spanish (mandatory)
- **Complete Guide**: `READ ~/insa-crm-platform/docs/COLOMBIA_OPERATIONS_REFERENCE.md`

### United States 🇺🇸
- **Primary Markets**: Manufacturing, Chemical, Oil & Gas, Utilities, Pharmaceuticals
- **Regulations**: NEC, NERC CIP, NIST CSF, OSHA, EPA
- **Voltage**: 208V/480V/600V, 60Hz (NEMA equipment)
- **Language**: English
- **Standards**: UL, ANSI, IEEE, ISA, NFPA

---

## 🎯 Core Capabilities

### 1. Customer & Account Management

**Customer Profile Management**
- Track industrial clients across multiple sectors
- Geographic coverage: Colombia and United States
- Bilingual documentation (Spanish/English)
- Facility profiles with site details
- Equipment inventories and installed systems
- Organizational structure and key contacts

**Compliance Tracking**
- **Colombia**: RETIE, NTC 2050/3701/4552/5019, MinMinas, SG-SST
- **United States**: NEC, IEC 62443, NIST CSF, NERC CIP, ISA 99, OSHA
- Industry-specific: FDA 21 CFR Part 11, API, ASME, ISO standards
- Automatic compliance requirement mapping by sector

**Regional Customization**
- Colombian voltage systems (220V/440V)
- US voltage systems (208V/480V/600V)
- Equipment standards (IEC vs NEMA)
- Currency handling (COP vs USD)
- Tax considerations (VAT in Colombia, Sales Tax in US)
- Time zones (COT, EST, CST, MST, PST)

### 2. Project Management

**Automation Projects**
- PLC programming (Siemens, Allen-Bradley, Schneider, Mitsubishi)
- SCADA systems (Wonderware, Ignition, WinCC, iFIX)
- HMI development (FactoryTalk View, InTouch, WinCC Flex)
- DCS configuration (Honeywell Experion, Emerson DeltaV, Yokogawa CENTUM)
- MES/MOM integration (Rockwell FactoryTalk, SAP ME)
- Network infrastructure (Profinet, EtherNet/IP, Modbus, OPC UA)

**Energy Optimization**
- Energy audits (ASHRAE Level 1, 2, 3)
- Monitoring and targeting systems
- Efficiency retrofits (lighting, HVAC, compressed air, motors)
- Renewable integration (solar, wind, cogeneration)
- ISO 50001 energy management systems
- Utility incentive program management

**Cybersecurity Assessments**
- IEC 62443 security assessments (all 4 parts, SL 1-4)
- NERC CIP compliance (CIP-002 through CIP-011)
- NIST Cybersecurity Framework implementation
- Vulnerability assessments and penetration testing
- Security architecture reviews (zones & conduits)
- Incident response planning

**Project Phases**
1. Discovery: Requirements, site assessment, risk analysis
2. Design: Engineering, vendor selection, FAT planning
3. Implementation: Procurement, installation, commissioning
4. Validation: SAT, performance verification, security testing
5. Handover: Training, documentation, support transition

### 3. Technical Documentation

**Engineering Documentation**
- P&IDs (Piping & Instrumentation Diagrams)
- Electrical one-lines and schematics
- Network topology diagrams (IT/OT convergence)
- Control narratives and functional specifications
- I/O lists and device databases
- Loop diagrams and wiring schedules

**Compliance Documentation**
- Risk assessments (IEC 62443, HAZOP, LOPA)
- Security policies and procedures
- Energy baseline reports and M&V plans
- Audit trails and evidence collection
- Incident investigation reports
- Training records and certifications

**Operational Documentation**
- O&M manuals (Spanish/English)
- Troubleshooting guides
- Spare parts lists with local vendors
- Maintenance schedules (preventive/predictive)
- Emergency response procedures
- As-built drawings

### 4. Opportunity & Quote Management

**Opportunity Tracking**
- RFP/RFQ from industrial clients
- Multi-discipline project opportunities
- Government procurement (Colombia: SECOP, US: SAM.gov)
- Win/loss analysis with lessons learned
- Competitive intelligence
- Pipeline forecasting by service line

**Quote Generation**
- Equipment pricing (with currency conversion)
- Labor estimates (Colombia vs US rates)
- Engineering hours by discipline
- Import duties and taxes (VAT in Colombia)
- Profit margins by project type
- Payment terms and currency risk

**Proposal Development**
- Technical specifications
- Project schedules (accounting for holidays)
- Team qualifications and CVs
- Past performance references
- Compliance matrices
- Risk mitigation strategies

---

## 📂 File Structure

```
/home/wil/insa-crm-platform/
│
├── customers/                     # Customer records
│   └── {customer_id}/
│       ├── profile.json          # Company info, contacts
│       ├── facilities.json       # Site locations
│       ├── equipment_inventory.json
│       ├── compliance_records.json
│       └── contracts/
│
├── projects/                      # Active and archived projects
│   └── {project_id}/
│       ├── project_details.json  # Scope, budget, team
│       ├── timeline.json         # Schedule with milestones
│       ├── technical_specs/      # Engineering documents
│       ├── drawings/             # CAD files, schematics
│       ├── commissioning_reports/
│       └── invoices/
│
├── opportunities/                 # Sales pipeline
│   └── {opportunity_id}/
│       ├── details.json          # Customer, scope, value
│       ├── quotes/               # Pricing proposals
│       ├── proposals/            # Technical proposals
│       └── competition_intel.json
│
├── knowledge_base/                # Reference library
│   ├── equipment_library/        # Vendor specs
│   │   ├── PLCs/
│   │   ├── SCADA/
│   │   ├── VFDs/
│   │   ├── instruments/
│   │   └── networking/
│   ├── standards/                # Codes and standards
│   │   ├── Colombia/             # NTC, RETIE
│   │   ├── US/                   # NEC, NFPA
│   │   └── international/        # IEC, ISA, IEEE
│   ├── templates/                # Document templates
│   │   ├── compliance/
│   │   ├── project_docs/
│   │   └── reports/
│   └── threat_intelligence/      # Cybersecurity intel
│
├── docs/                          # Documentation
│   ├── COLOMBIA_OPERATIONS_REFERENCE.md  # 🇨🇴 Complete guide
│   ├── equipment_library.md      # Equipment specs
│   ├── compliance_templates.md   # Assessment templates
│   └── guides/                   # How-to guides
│
├── scripts/                       # Automation scripts
│   ├── project_management.py     # CRUD operations
│   ├── energy_calculator.py      # ROI calculations
│   ├── compliance_checker.py     # Verify documentation
│   └── equipment_inventory.py    # Manage equipment DB
│
├── mcp-servers/                   # MCP integrations
│   ├── erpnext-crm/              # 33 tools - full sales cycle
│   ├── inventree-crm/            # 5 tools - BOM management
│   ├── mautic-admin/             # 27 tools - marketing
│   └── n8n-admin/                # 23 tools - workflows
│
└── README.md                      # Main documentation

```

---

## 📊 Data Standards

### Customer Profile Schema

```json
{
  "customer_id": "CUST-2025-001",
  "company_name": "Petróleos Andinos S.A.",
  "industry_sector": "Oil & Gas Production",
  "country": "CO",
  "region": "South America",
  "primary_language": "es",
  "facilities": [
    {
      "name": "Campo Rubiales",
      "location": "Villavicencio, Meta, Colombia",
      "address": "Llanos Orientales",
      "coordinates": "4.1420° N, 73.6266° W",
      "voltage": "34.5kV / 440V",
      "installed_systems": ["SCADA", "RTU", "Telemetry"],
      "production": "15,000 BOPD"
    }
  ],
  "primary_contact": {
    "name": "Carlos Rodríguez",
    "title": "Gerente de Automatización",
    "email": "crodriguez@petroandinos.com.co",
    "phone": "+57-310-555-0789",
    "language": "es"
  },
  "compliance_frameworks": ["RETIE", "NTC 2050", "IEC 62443-3-3", "ISO 27001"],
  "relationship_status": "active",
  "total_contract_value": 650000,
  "currency": "USD",
  "risk_level": "critical",
  "time_zone": "America/Bogota",
  "fiscal_year_end": "December 31",
  "payment_terms": "NET 60",
  "tax_id": "NIT 900.123.456-7"
}
```

### Project Schema

```json
{
  "project_id": "PROJ-2025-CO-001",
  "project_name": "Sistema SCADA Pozos Petroleros - Campo Rubiales",
  "customer_id": "CUST-2025-001",
  "project_type": "automation",
  "status": "implementation",
  "start_date": "2025-01-15",
  "completion_date": "2025-06-30",
  "country": "CO",
  "site_location": "Villavicencio, Meta",
  "systems_involved": ["SCADA", "RTU", "Telemetry", "Modbus"],
  "vendors": ["Siemens Colombia", "Phoenix Contact Andina"],
  "budget": 650000,
  "currency": "USD",
  "budget_breakdown": {
    "equipment": 400000,
    "engineering": 100000,
    "installation": 80000,
    "commissioning": 40000,
    "training": 20000,
    "contingency": 10000
  },
  "team_members": ["ENG-002", "ENG-004", "ENG-008"],
  "security_classification": "restricted",
  "compliance_requirements": ["RETIE", "NTC 2050", "IEC 62443-3-3"],
  "language": "es",
  "voltage_system": "440V 3-phase 60Hz",
  "milestones": [
    {"name": "Design Review", "date": "2025-02-15", "status": "completed"},
    {"name": "Equipment Procurement", "date": "2025-03-30", "status": "in_progress"},
    {"name": "FAT", "date": "2025-04-30", "status": "pending"},
    {"name": "Installation", "date": "2025-05-31", "status": "pending"},
    {"name": "SAT", "date": "2025-06-15", "status": "pending"},
    {"name": "RETIE Certification", "date": "2025-06-25", "status": "pending"}
  ]
}
```

---

## 🔧 Equipment Library

### PLCs (Programmable Logic Controllers)

**Siemens SIMATIC**
- S7-1500: High-performance, scalable, integrated motion
  - Voltage: 24VDC, 120/230VAC
  - Cycle time: <1ms
  - Memory: Up to 10MB
  - Communication: Profinet, Profibus, EtherNet/IP (with CM)
  - Programming: TIA Portal V17+
  - **Availability**: Colombia (Siemens Colombia), US (nationwide)

- S7-1200: Compact, cost-effective, modular
  - Voltage: 24VDC, 120/230VAC
  - Cycle time: 10-100ms
  - Memory: 50-125KB
  - Communication: Profinet, Modbus TCP
  - Programming: TIA Portal
  - **Availability**: Colombia & US (2-4 week lead time)

**Allen-Bradley (Rockwell Automation)**
- ControlLogix: Distributed control, high availability
  - Voltage: 24VDC (typical)
  - Platforms: 1756-L7x (standard), 1756-L8x (GuardLogix)
  - Communication: EtherNet/IP, ControlNet, DeviceNet
  - Programming: Studio 5000 Logix Designer
  - **Availability**: US (excellent), Colombia (via distributors)

- CompactLogix: Modular, scalable, integrated safety
  - Voltage: 24VDC
  - Platforms: 5380 (current), 5069 (compact)
  - Communication: EtherNet/IP, USB
  - Programming: Studio 5000
  - **Availability**: US (2-4 weeks), Colombia (4-8 weeks)

**Schneider Electric Modicon**
- M580: Ethernet-based, cybersecurity built-in
  - Voltage: 24VDC
  - Communication: Modbus TCP/IP, EtherNet/IP
  - Programming: Unity Pro, EcoStruxure Control Expert
  - **Availability**: Colombia (Schneider Electric Colombia), US (good)

- M340: Mid-range, proven reliability
  - Voltage: 24VDC
  - Communication: Modbus, Ethernet
  - Programming: Unity Pro
  - **Availability**: Colombia & US (local stock)

**Mitsubishi Electric**
- iQ-R Series: High-speed, motion control
- iQ-F Series: Compact, cost-effective
- **Availability**: Better in Asia, limited in Colombia/US

### SCADA Systems

**Wonderware System Platform (AVEVA)**
- Architecture: Client/server
- Redundancy: Built-in
- Connectivity: 350+ device drivers
- HMI: InTouch, InTouch OMI
- Historian: Historian 2020
- **Licensing**: Per tag/connection
- **Languages**: Multi-language including Spanish
- **Support**: Colombia & US (excellent)

**Ignition by Inductive Automation**
- Architecture: Web-based, unlimited clients
- Redundancy: Standard in all editions
- Connectivity: OPC UA, Modbus, database
- HMI: Perspective (web), Vision (desktop)
- Historian: Built-in
- **Licensing**: Per server (unlimited tags!)
- **Languages**: Spanish, English, 20+ others
- **Support**: US (excellent), Colombia (growing)
- **Cost**: Very competitive ($7,500-15,000/server)

**Siemens WinCC**
- Architecture: Client/server or HMI
- Redundancy: Optional (separate license)
- Connectivity: S7 native, OPC DA/UA
- Versions: WinCC V7 (desktop), WinCC Unified (web)
- Historian: WinCC Historian
- **Licensing**: Per client, PowerTags
- **Languages**: Spanish, English, 30+ others
- **Support**: Colombia (Siemens Colombia), US (excellent)

**GE Digital iFIX**
- Architecture: Distributed client/server
- Redundancy: Automatic failover
- Connectivity: OPC, native drivers
- HMI: iFIX SCADA
- Historian: Proficy Historian
- **Support**: US (good), Colombia (limited)

**Citect (Schneider Electric)**
- Now: AVEVA Citect SCADA
- Connectivity: Wide driver support
- **Availability**: Colombia (Schneider), US

### VFDs (Variable Frequency Drives)

**Siemens SINAMICS**
- G120: General purpose, 0.37-250kW
  - Input: 380-480V (US), 380-440V (Colombia)
  - Control: V/f, vector, servo
  - Communication: Profinet, Profibus, Modbus RTU/TCP, USS
  - **Lead time**: 2-4 weeks (Colombia), 1-2 weeks (US)

- G130/G150: High power, 75-1,200kW
  - Input: MV available
  - Regenerative braking
  - **Applications**: Large motors, cranes, mining

**ABB ACS/ACH Series**
- ACS580: General purpose, wall-mount
- ACH580: HVAC optimized
- **Availability**: Colombia & US (good)

**Allen-Bradley PowerFlex**
- PowerFlex 525: Compact, 0.4-22kW
  - Input: 200-240V, 380-480V
  - Communication: EtherNet/IP, Modbus TCP
  - Programming: Connected Components Workbench
  - **Availability**: US (excellent), Colombia (via distributors)

- PowerFlex 755: High performance, 0.75-1,250kW
  - Advanced motor control
  - Safety (Safe Torque Off)
  - **Applications**: Critical processes

**Schneider Electric Altivar**
- ATV320: Compact, book-style
- ATV600: Process-oriented
- **Availability**: Colombia (Schneider Colombia), US (good)

### Communication Protocols & Networking

**Industrial Ethernet**
- Profinet (Siemens)
- EtherNet/IP (Rockwell, ODVA)
- Modbus TCP/IP (Schneider, universal)
- OPC UA (platform-independent, IEC 62541)

**Serial Protocols**
- Modbus RTU (RS-485, most common)
- Profibus DP (legacy Siemens)
- DeviceNet (legacy Rockwell)
- CC-Link (Mitsubishi)

**Wireless**
- WirelessHART (IEC 62591)
- ISA100.11a (IEC 62734)
- Wi-Fi (IEEE 802.11, use with caution in OT)
- LoRaWAN (long-range, low-power)
- Private LTE/5G (for large campuses)

### Cybersecurity Tools

**ICS Firewalls**
- Fortinet FortiGate: Deep packet inspection, OT visibility
- Palo Alto Networks: Advanced threat protection
- Claroty: Purpose-built for ICS/OT
- **Placement**: Between IT and OT networks (DMZ)

**Network Monitoring**
- Nozomi Networks: Asset discovery, anomaly detection
- Dragos Platform: ICS threat detection
- CyberX (Microsoft): OT monitoring
- **Deployment**: Passive TAP or SPAN port

**SIEM Integration**
- Splunk: Universal log aggregation
- IBM QRadar: Security analytics
- **Use**: Correlate IT + OT events

**Vulnerability Scanners**
- Tenable.ot (formerly Indegy): Agentless OT scanning
- Rapid7 Nexpose: Network vulnerability scanning
- **Use**: Identify unpatched systems, misconfigurations

---

## 🏭 Industry-Specific Considerations

### Oil & Gas
- **Compliance**: API standards, OSHA PSM, NFPA 70, IEC 61511 (SIS)
- **Equipment**: Explosion-proof (Class I Div 1/2), intrinsic safety
- **Communication**: RTU for remote wells, satellite/cellular
- **Challenges**: Remote locations, hazardous areas, high consequence
- **Colombia**: Llanos Orientales, offshore Caribbean

### Mining
- **Compliance**: MSHA (US), MinMinas (Colombia), IEC 61936
- **Equipment**: Rugged, high IP ratings, vibration resistance
- **Applications**: Conveyor control, crushing/milling, dewatering
- **Challenges**: Dust, remote sites, altitude (Colombia Andes)
- **Colombia**: Coal (Cesar, La Guajira), gold (Antioquia), emeralds (Boyacá)

### Manufacturing
- **Compliance**: ISO 9001, FDA (pharma), FSMA (food)
- **Equipment**: Fast cycle times, high reliability, MES integration
- **Applications**: Assembly lines, packaging, batch processing
- **Trends**: Industry 4.0, IoT, predictive maintenance
- **Colombia**: Bogotá, Medellín, Cali industrial zones

### Utilities (Power, Water)
- **Compliance**: NERC CIP (US), RETIE (Colombia), IEC 61850
- **Equipment**: High availability, redundancy, secure remote access
- **Applications**: Generation control, distribution SCADA, AMI
- **Challenges**: Cybersecurity, aging infrastructure
- **Colombia**: 70% hydro, 30% thermal; Emgesa, EPM, Codensa

### Food & Beverage
- **Compliance**: FDA FSMA, HACCP, GMP, INVIMA (Colombia)
- **Equipment**: Sanitary design (3-A, EHEDG), washdown (IP69K)
- **Applications**: Batch control, CIP/SIP, traceability
- **Colombia**: Coffee, flowers, palm oil, sugar

---

## 📋 Compliance Frameworks

### IEC 62443 (Industrial Cybersecurity)

**Structure:**
- IEC 62443-1: General (concepts, models, terminology)
- IEC 62443-2: Policies & Procedures
  - 2-1: Security program requirements
  - 2-4: Security program requirements for IACS service providers
- IEC 62443-3: System
  - 3-2: Security risk assessment
  - 3-3: System security requirements (zones & conduits)
- IEC 62443-4: Component
  - 4-1: Product development lifecycle
  - 4-2: Technical security requirements for components

**Security Levels (SL):**
- **SL 1**: Protection against casual or coincidental violation
- **SL 2**: Protection against intentional violation using simple means
- **SL 3**: Protection against intentional violation using sophisticated means
- **SL 4**: Protection against intentional violation using sophisticated means with extended resources

**Common Implementation:**
- Asset inventory and criticality assessment
- Network segmentation (zones & conduits)
- Risk assessment per IEC 62443-3-2
- Security policies and procedures
- Technical controls (firewall, authentication, logging)

**Tools:**
- `READ ~/insa-crm-platform/docs/compliance_templates.md` for assessment templates

### NERC CIP (North American Electric Reliability Corporation - US)

**Applicable to:** Bulk Electric System (BES) owners/operators

**Standards:**
- CIP-002: BES Cyber System Categorization
- CIP-003: Security Management Controls
- CIP-004: Personnel & Training
- CIP-005: Electronic Security Perimeters (ESP)
- CIP-006: Physical Security
- CIP-007: System Security Management
- CIP-008: Incident Reporting & Response
- CIP-009: Recovery Plans
- CIP-010: Configuration Change Management
- CIP-011: Information Protection

**Enforcement:** Mandatory, fines up to $1M/day for violations

### NIST Cybersecurity Framework (US)

**Functions:**
1. **Identify**: Asset management, risk assessment, governance
2. **Protect**: Access control, data security, protective technology
3. **Detect**: Anomaly detection, security monitoring
4. **Respond**: Response planning, communications, mitigation
5. **Recover**: Recovery planning, improvements, communications

**Tiers:**
- Tier 1: Partial (ad hoc)
- Tier 2: Risk Informed
- Tier 3: Repeatable
- Tier 4: Adaptive

**Application:** Voluntary framework, widely adopted for OT cybersecurity

### Colombia-Specific

**RETIE (Reglamento Técnico de Instalaciones Eléctricas)**
- Mandatory for ALL electrical installations
- Covers: Safety, grounding, protection, labeling
- Inspection required before energization
- Certificate valid 5 years
- **See:** `READ ~/insa-crm-platform/docs/COLOMBIA_OPERATIONS_REFERENCE.md`

**NTC Standards**
- NTC 2050: Colombian Electrical Code (based on NEC)
- NTC 3701: Automation systems
- NTC 4552: Electrical safety
- NTC 5019: Grounding systems

**SG-SST (Sistema de Gestión de Seguridad y Salud en el Trabajo)**
- Occupational health and safety management
- Mandatory for all Colombian companies
- Decree 1072 of 2015, Resolution 0312 of 2019

---

## 💰 Energy Optimization

### Energy Audit Levels (ASHRAE)

**Level 1: Walk-Through**
- Duration: 1 day
- Cost: $2,000-5,000
- Deliverables: Opportunity list, rough savings estimates
- Accuracy: ±30%

**Level 2: Detailed Survey and Analysis**
- Duration: 1-2 weeks
- Cost: $10,000-30,000
- Deliverables: Detailed energy model, financial analysis, recommendations
- Accuracy: ±20%
- Most common for industrial clients

**Level 3: Investment-Grade Audit**
- Duration: 4-8 weeks
- Cost: $50,000-200,000
- Deliverables: Detailed engineering, M&V plan, firm quotes
- Accuracy: ±10%
- Required for large capital projects, ESCO contracts

### Common Energy Measures

**Lighting Upgrades**
- T12/T8 to LED: 50-70% savings
- Metal halide to LED: 60-75% savings
- Add controls: Additional 20-40% savings
- Typical payback: 1-3 years

**VFD Installation**
- Variable speed on fans/pumps
- Affinity laws: Power ∝ Speed³
- Typical savings: 30-50% on HVAC, 20-40% on pumps
- Payback: 1-4 years

**Compressed Air Optimization**
- Leak repairs: 20-30% savings (typical 30% leakage)
- Pressure reduction: 1% savings per 2 psi reduction
- Improved controls
- Payback: <1 year for leak repairs

**HVAC Optimization**
- VFDs on AHUs
- Economizer controls
- Demand-controlled ventilation (CO2 sensors)
- Chiller optimization
- Savings: 20-40%

**Motor Efficiency**
- Replace with IE3 (Premium Efficiency)
- Right-sizing (eliminate oversized motors)
- Typical savings: 2-8% (motor only), 20-40% with VFD

### Financial Analysis

**Simple Payback Period**
```
Payback = Initial Cost / Annual Savings
```

**Net Present Value (NPV)**
```
NPV = Σ (Cash Flow_t / (1 + r)^t) - Initial Cost
```
Where: r = discount rate, t = time period

**Internal Rate of Return (IRR)**
- Discount rate where NPV = 0
- Compare to cost of capital

**Scripts:**
- `python ~/insa-crm-platform/scripts/energy_calculator.py` for automated calculations

---

## 🚀 Using This Skill

### Common Commands

**Customer Management**
```python
# Create new customer
python scripts/project_management.py create-customer \
  --name "Petróleos Andinos S.A." \
  --industry "Oil & Gas" \
  --country "CO" \
  --compliance "RETIE,IEC 62443" \
  --contact-name "Carlos Rodríguez" \
  --contact-email "crodriguez@petroandinos.com.co"

# List customers
python scripts/project_management.py list-customers

# List customers by country
python scripts/project_management.py list-customers --country CO
```

**Project Management**
```python
# Create new project
python scripts/project_management.py create-project \
  --customer-id CUST-2025-001 \
  --name "Sistema SCADA Pozos Petroleros" \
  --type automation \
  --country CO \
  --budget 650000 \
  --currency USD

# List projects
python scripts/project_management.py list-projects

# Update project status
python scripts/project_management.py update-status \
  --project-id PROJ-2025-CO-001 \
  --status implementation
```

**Energy Calculations**
```python
# Calculate VFD savings
python scripts/energy_calculator.py vfd-savings \
  --hp 100 \
  --hours 8000 \
  --load-factor 0.70 \
  --electricity-rate 0.13 \
  --installation-cost 12000

# Calculate lighting ROI
python scripts/energy_calculator.py lighting-roi \
  --fixtures 200 \
  --watts-old 400 \
  --watts-new 100 \
  --hours 4500 \
  --electricity-rate 0.12 \
  --install-cost-per-fixture 150
```

### Natural Language Queries

**Customer Information**
- "List all customers in the oil & gas industry in Colombia"
- "Show me facilities for customer CUST-2025-001"
- "What compliance requirements apply to this customer?"

**Project Tracking**
- "Create a project for SCADA upgrade at Petróleos Andinos"
- "What projects are in the implementation phase?"
- "Show me projects with RETIE compliance requirements"

**Equipment Selection**
- "What's the best PLC for a water treatment plant with 150 I/O points?"
- "Compare Siemens S7-1500 vs Allen-Bradley ControlLogix"
- "What VFD do I need for a 100 HP motor in Colombia (440V)?"

**Energy Analysis**
- "Calculate ROI for LED upgrade of 300 fixtures running 5,000 hours/year"
- "What savings can I expect from a VFD on a 75 HP air handler?"
- "Estimate energy cost for compressed air leaks of 50 CFM"

**Compliance**
- "What are the RETIE requirements for a 34.5kV substation?"
- "Generate an IEC 62443 risk assessment for a chemical plant"
- "What's required for NERC CIP compliance?"

---

## 🌐 Regional Operations

### Colombia 🇨🇴

**Key Contacts**
- Ministry of Mines and Energy: minenergia.gov.co
- ICONTEC (Standards): icontec.org
- SENA (Training): senasofiaplus.edu.co
- ACIEM (Engineers Association): aciem.org

**Major Vendors**
- Siemens Colombia: (+57) 1 4238000
- Schneider Electric Colombia: (+57) 1 6544888
- ABB Colombia
- Phoenix Contact Andina

**Critical Success Factors**
- Spanish language mandatory
- RETIE compliance from day one
- 440V equipment (not 480V!)
- Build relationships (confianza)
- Plan for 5-10 week import lead times
- Customs broker essential
- Currency risk management

**Complete Guide:** `READ ~/insa-crm-platform/docs/COLOMBIA_OPERATIONS_REFERENCE.md`

### United States 🇺🇸

**Key Standards**
- NEC (National Electrical Code)
- NFPA (Fire Protection)
- OSHA (Safety)
- IEEE (Electrical/Electronics)
- ISA (Automation)

**Major Vendors**
- Siemens USA
- Rockwell Automation
- Schneider Electric
- Emerson
- Honeywell

**Critical Success Factors**
- NEC compliance
- NEMA standards for equipment
- 480V most common industrial voltage
- Strong local support infrastructure
- Faster lead times than Colombia
- NERC CIP for utilities

---

## 🎓 Training & Resources

### For New Users
1. Read this skill document
2. Review Colombia Operations Guide (if working in Colombia)
3. Generate sample data: `python scripts/generate_sample_data.py`
4. Explore customer and project structures
5. Practice with test queries

### Key Documents
- **This file**: Complete skill overview
- **Colombia Guide**: `~/insa-crm-platform/docs/COLOMBIA_OPERATIONS_REFERENCE.md`
- **Equipment Library**: `~/insa-crm-platform/docs/equipment_library.md`
- **Compliance Templates**: `~/insa-crm-platform/docs/compliance_templates.md`
- **Main README**: `~/insa-crm-platform/README.md`

### External Resources
- IEC 62443: https://www.isa.org/standards-and-publications/isa-standards/isa-iec-62443-series-of-standards
- NERC CIP: https://www.nerc.com/pa/Stand/Pages/CIPStandards.aspx
- NIST CSF: https://www.nist.gov/cyberframework
- ASHRAE: https://www.ashrae.org
- RETIE (Colombia): https://www.minenergia.gov.co

---

## 🔐 Security & Privacy

**Data Protection**
- Never store credentials in CRM records
- Encrypt sensitive customer data
- Follow principle of least privilege
- Maintain separate environments (prod/test)
- Log all access to confidential information

**Compliance**
- Customer data handled per contracts
- Security classifications enforced
- Audit trails maintained
- Incident response procedures
- Regular backups

---

## 📈 Key Performance Indicators

**Sales Metrics**
- Customer acquisition cost (CAC)
- Customer lifetime value (CLV)
- Win rate by service line
- Pipeline value by country
- Average deal size

**Operational Metrics**
- On-time delivery percentage
- Budget variance
- Resource utilization
- Customer satisfaction scores (CSAT)
- Net Promoter Score (NPS)

**Technical Metrics**
- RETIE inspection pass rate (Colombia)
- SAT punch list items
- Training effectiveness
- Warranty claims
- Repeat business rate

---

## ✅ Project Checklist

### Pre-Project (Colombia)
- [ ] RETIE requirements identified
- [ ] Voltage system confirmed (220V/440V)
- [ ] Altitude derating calculated if >1,000m
- [ ] Spanish documentation requirements confirmed
- [ ] Import lead times in schedule (add 5-10 weeks)
- [ ] Currency and payment terms agreed
- [ ] Local partners identified if needed

### Pre-Project (United States)
- [ ] NEC compliance requirements identified
- [ ] Voltage system confirmed (208V/480V/600V)
- [ ] State/local codes researched
- [ ] NERC CIP applicability determined (utilities)
- [ ] Lead times realistic
- [ ] Payment terms agreed

### Design (All Projects)
- [ ] Equipment ratings appropriate for voltage
- [ ] Environmental conditions assessed
- [ ] Cybersecurity requirements defined
- [ ] Communication protocols selected
- [ ] Spanish/English documentation scope defined
- [ ] Training requirements identified

### Procurement
- [ ] RETIE certification for equipment (Colombia)
- [ ] UL/CSA/NRTL certification (US)
- [ ] Lead times include customs (Colombia)
- [ ] Spare parts strategy developed
- [ ] Local distributor support confirmed

### Implementation
- [ ] Certified electricians (RETIE in Colombia)
- [ ] Safety compliance (SG-SST in Colombia, OSHA in US)
- [ ] Documentation in appropriate language
- [ ] Daily progress reports
- [ ] Quality control inspections

### Commissioning
- [ ] FAT completed
- [ ] SAT with customer sign-off
- [ ] RETIE inspection and certificate (Colombia)
- [ ] Performance verification
- [ ] Training delivered and documented

### Closeout
- [ ] As-built documentation delivered
- [ ] O&M manuals in Spanish/English
- [ ] Training completed with certificates
- [ ] Warranty terms clear
- [ ] Support procedures established

---

## 🆘 Getting Help

**Documentation**
1. Review this skill document
2. Check region-specific guides (Colombia)
3. Read equipment library for specs
4. Review compliance templates

**Ask Claude**
- "Explain the RETIE requirements for a 440V installation"
- "What's the difference between IEC and NEMA motor frames?"
- "How do I calculate VFD savings?"
- "What documents do I need for Colombian customs?"

**Escalation**
- Technical questions: Senior engineers
- Colombia operations: w.aroca@insaing.com
- Compliance: Compliance officer
- Urgent issues: Operations manager

---

## 📊 Success Metrics

This skill has been designed to improve:
- **Speed**: Customer setup 83% faster (30 min → 5 min)
- **Accuracy**: Standardized calculations and compliance
- **Consistency**: Templates and procedures
- **Knowledge**: Centralized reference library
- **Compliance**: Built-in requirement tracking
- **Multi-regional**: Seamless Colombia + US operations

---

## 🚀 Next Steps

1. **Generate test data**: `python scripts/generate_sample_data.py`
2. **Explore**: Browse customers and projects
3. **Test queries**: Ask Claude about customers, projects, equipment
4. **Customize**: Add your company's equipment preferences
5. **Deploy**: Use for real projects
6. **Iterate**: Provide feedback for improvements

---

**Version:** 2.0 - Colombia & United States Operations
**Last Updated:** October 23, 2025
**Maintainer:** Insa Automation Corp
**Contact:** w.aroca@insaing.com

**Made by Insa Automation Corp for OpSec Excellence** 🏭🔒⚡

---

*This skill integrates seamlessly with INSA CRM Platform's 8 MCP servers:*
- ERPNext CRM (33 tools - full sales cycle)
- InvenTree (5 tools - BOM management)
- Mautic (27 tools - marketing automation)
- n8n (23 tools - workflow automation)
- DefectDojo (8 tools - IEC 62443 compliance)
- Grafana (23 tools - analytics)
- Platform Admin (8 tools - health monitoring)
- Host Config Agent (19 tools - deployment automation)
