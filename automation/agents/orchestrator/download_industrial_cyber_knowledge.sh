#!/bin/bash
#
# Industrial Cybersecurity Knowledge Base Downloader for INSA CRM RAG
# Focuses on Oil & Gas, ICS/OT, IEC 62443, and critical infrastructure
# Date: November 1, 2025
# Author: Insa Automation Corp
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}Industrial Cybersecurity Knowledge Base for INSA CRM RAG${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# Create directory structure
BASE_DIR="/home/wil/automation/agents/orchestrator/knowledge/industrial-cyber"

echo -e "${YELLOW}Creating directory structure...${NC}"
mkdir -p "$BASE_DIR/cisa-ics"           # CISA ICS security
mkdir -p "$BASE_DIR/nist-framework"     # NIST Cybersecurity Framework
mkdir -p "$BASE_DIR/oil-gas"            # Oil & Gas specific
mkdir -p "$BASE_DIR/iec-62443"          # IEC 62443 standards
mkdir -p "$BASE_DIR/best-practices"     # Industry best practices
mkdir -p "$BASE_DIR/threat-reports"     # Threat intelligence

echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Download function
download_file() {
    local url="$1"
    local output="$2"
    local description="$3"

    echo -e "${YELLOW}Downloading: ${description}...${NC}"

    if wget -q --show-progress --timeout=30 -O "$output" "$url" 2>/dev/null; then
        local size=$(du -h "$output" | cut -f1)
        echo -e "${GREEN}✅ Downloaded: $(basename "$output") (${size})${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed: ${description}${NC}"
        echo -e "${YELLOW}   Manual download: ${url}${NC}"
        rm -f "$output" 2>/dev/null
        return 1
    fi
}

# =====================================
# CISA ICS SECURITY DOCUMENTS
# =====================================
echo -e "${BLUE}Downloading CISA ICS Security Documents...${NC}"

download_file \
    "https://www.cisa.gov/sites/default/files/publications/Cybersecurity_Best_Practices_for_Industrial_Control_Systems_508.pdf" \
    "$BASE_DIR/cisa-ics/cisa_ics_best_practices.pdf" \
    "CISA ICS Best Practices (Primary)"

download_file \
    "https://www.cisa.gov/sites/default/files/documents/Seven Steps to Effectively Defend Industrial Control Systems_S508C.pdf" \
    "$BASE_DIR/cisa-ics/seven_steps_defend_ics.pdf" \
    "Seven Steps to Defend ICS"

download_file \
    "https://www.cisa.gov/sites/default/files/2023-01/final-RP_ics_cybersecurity_incident_response_100609.pdf" \
    "$BASE_DIR/cisa-ics/ics_incident_response.pdf" \
    "ICS Incident Response Guide"

download_file \
    "https://www.cisa.gov/sites/default/files/recommended_practices/DHS_Common_Cybersecurity_Vulnerabilities_ICS_2010.pdf" \
    "$BASE_DIR/cisa-ics/common_ics_vulnerabilities.pdf" \
    "Common ICS Vulnerabilities"

download_file \
    "https://www.cisa.gov/sites/default/files/publications/ICS-Monitoring-Technology-Considerations-Final-v2_508c.pdf" \
    "$BASE_DIR/cisa-ics/ics_monitoring_technologies.pdf" \
    "ICS Monitoring Technologies"

echo ""

# =====================================
# NIST CYBERSECURITY FRAMEWORK
# =====================================
echo -e "${BLUE}Downloading NIST Cybersecurity Framework...${NC}"

download_file \
    "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.29.pdf" \
    "$BASE_DIR/nist-framework/nist_csf_2.0.pdf" \
    "NIST CSF 2.0 (Latest - 2024)"

download_file \
    "https://nvlpubs.nist.gov/nistpubs/cswp/nist.cswp.04162018.pdf" \
    "$BASE_DIR/nist-framework/nist_csf_1.1.pdf" \
    "NIST CSF 1.1 (Critical Infrastructure)"

echo ""

# =====================================
# OIL & GAS CYBERSECURITY
# =====================================
echo -e "${BLUE}Downloading Oil & Gas Cybersecurity Resources...${NC}"

download_file \
    "https://www.bibliotecadeseguranca.com.br/wp-content/uploads/2021/11/definitive-guide-to-cybersecurity-for-the-oil-gas-industry.pdf" \
    "$BASE_DIR/oil-gas/definitive_guide_oil_gas_cyber.pdf" \
    "Definitive Guide to O&G Cybersecurity"

download_file \
    "https://www3.weforum.org/docs/WEF_Board_Principles_Playbook_Oil_and_Gas_2021.pdf" \
    "$BASE_DIR/oil-gas/wef_cyber_resilience_oil_gas.pdf" \
    "WEF Cyber Resilience O&G Playbook"

download_file \
    "https://www.fortinet.com/content/dam/fortinet/assets/reports/report-cybersecurity-oil-and-gas.pdf" \
    "$BASE_DIR/oil-gas/fortinet_oil_gas_ot_security.pdf" \
    "Fortinet O&G OT Security Report"

download_file \
    "https://www.cyber.gc.ca/sites/default/files/cyber-threat-oil-gas-e.pdf" \
    "$BASE_DIR/oil-gas/canada_cyber_threat_oil_gas.pdf" \
    "Canadian Cyber Threat Assessment - O&G"

download_file \
    "https://www.infosys.com/services/cyber-security/documents/oil-gas-operations.pdf" \
    "$BASE_DIR/oil-gas/infosys_oil_gas_cyber_risks.pdf" \
    "Infosys Industrial Cyber Risks - O&G"

echo ""

# =====================================
# IEC 62443 STANDARDS
# =====================================
echo -e "${BLUE}Downloading IEC 62443 Resources...${NC}"

download_file \
    "https://gca.isa.org/hubfs/ISAGCA Quick Start Guide FINAL.pdf" \
    "$BASE_DIR/iec-62443/isagca_quick_start_guide.pdf" \
    "ISAGCA IEC 62443 Quick Start Guide"

download_file \
    "https://www.isa.org/getmedia/b75b5611-1fa8-4807-99e5-d8707b7cff18/Phinneydone.pdf" \
    "$BASE_DIR/iec-62443/isa_iec62443_industrial_network_security.pdf" \
    "ISA IEC 62443 Industrial Network Security"

download_file \
    "https://isagca.org/hubfs/2023 ISA Website Redesigns/ISAGCA/PDFs/Industrial Cybersecurity Knowledge FINAL.pdf" \
    "$BASE_DIR/iec-62443/isagca_industrial_cyber_knowledge.pdf" \
    "ISAGCA Industrial Cybersecurity Knowledge"

echo ""

# =====================================
# BEST PRACTICES & INDUSTRY GUIDES
# =====================================
echo -e "${BLUE}Downloading Best Practices...${NC}"

download_file \
    "https://prosiding.aritekin.or.id/index.php/ICONFES/article/download/31/42/178" \
    "$BASE_DIR/best-practices/ai_powered_ics_security_2024.pdf" \
    "AI-Powered ICS Security (2024)"

download_file \
    "https://www.cisco.com/c/en/us/td/docs/solutions/Verticals/Oil_and_Gas/Pipeline/SecurityReference/Security-IRD.pdf" \
    "$BASE_DIR/best-practices/cisco_pipeline_security_reference.pdf" \
    "Cisco Pipeline Security Reference"

echo ""

# =====================================
# CREATE INDEX & DOCUMENTATION
# =====================================
echo -e "${BLUE}Creating documentation...${NC}"

# Create comprehensive README
cat > "$BASE_DIR/README.md" << 'EOF'
# Industrial Cybersecurity Knowledge Base for INSA CRM RAG

**Purpose:** Provide industrial cybersecurity expertise to INSA CRM autonomous agents
**Focus:** Oil & Gas, ICS/OT, IEC 62443, Critical Infrastructure
**Date:** November 1, 2025

---

## Directory Structure

```
industrial-cyber/
├── cisa-ics/           # CISA ICS security guidance (US Government - CRITICAL)
├── nist-framework/     # NIST Cybersecurity Framework (Industry standard)
├── oil-gas/            # Oil & Gas specific cybersecurity (INSA focus)
├── iec-62443/          # IEC 62443 standards resources (Compliance)
├── best-practices/     # Industry best practices & vendor guides
├── threat-reports/     # Threat intelligence reports (future)
└── README.md          # This file
```

---

## What's Inside

### 🏛️ CISA ICS Security (US Government)

**Authority:** Cybersecurity and Infrastructure Security Agency (CISA)
**Focus:** Critical infrastructure protection

1. **cisa_ics_best_practices.pdf** ⭐ PRIMARY REFERENCE
   - Collaborative: CISA + DOE + UK NCSC
   - Comprehensive ICS security best practices
   - Network security, access control, monitoring

2. **seven_steps_defend_ics.pdf**
   - Practical defense strategies
   - Based on real incident response experiences
   - Quick reference for agents

3. **ics_incident_response.pdf**
   - How to respond to ICS cybersecurity incidents
   - Defines ICS, SCADA, DCS, embedded systems
   - Step-by-step incident handling

4. **common_ics_vulnerabilities.pdf**
   - Most common ICS cybersecurity vulnerabilities
   - Vulnerability types and mitigation strategies

5. **ics_monitoring_technologies.pdf**
   - ICS/OT monitoring technology considerations
   - Tool selection guidance

### 🎯 NIST Cybersecurity Framework (Industry Standard)

**Authority:** National Institute of Standards and Technology (NIST)
**Focus:** Risk management framework for critical infrastructure

1. **nist_csf_2.0.pdf** ⭐ LATEST (2024)
   - Most recent version of the framework
   - Applicable to all organizations
   - Core functions: Identify, Protect, Detect, Respond, Recover

2. **nist_csf_1.1.pdf** (2018)
   - Previous version (still widely referenced)
   - Executive Order 13636 compliance

### 🛢️ Oil & Gas Cybersecurity (INSA Focus)

**Relevance:** CRITICAL - Direct application to INSA's Oil & Gas clients

1. **definitive_guide_oil_gas_cyber.pdf**
   - ONG-C2M2 (Oil & Natural Gas Cybersecurity Capability Maturity Model)
   - IT + OT security
   - Developed by US Department of Energy

2. **wef_cyber_resilience_oil_gas.pdf** ⭐ BOARD-LEVEL
   - World Economic Forum playbook
   - Board principles for cyber resilience
   - Executive guidance

3. **fortinet_oil_gas_ot_security.pdf**
   - Securing OT environments in O&G
   - Vendor perspective with practical solutions

4. **canada_cyber_threat_oil_gas.pdf**
   - Government threat assessment
   - Specific threats to O&G sector
   - Canadian Centre for Cyber Security

5. **infosys_oil_gas_cyber_risks.pdf**
   - Industrial cybersecurity risks
   - O&G operations focus

### 🔒 IEC 62443 Standards (Compliance)

**Authority:** International Society of Automation (ISA) / IEC
**Focus:** Industrial automation and control systems security

1. **isagca_quick_start_guide.pdf** ⭐ START HERE
   - ISAGCA official first work product
   - User-friendly overview of IEC 62443 series
   - World's only consensus-based automation cybersecurity standards

2. **isa_iec62443_industrial_network_security.pdf**
   - Industrial network and system security
   - Technical implementation details

3. **isagca_industrial_cyber_knowledge.pdf**
   - Curricular guidance for industrial cybersecurity
   - SCADA and OT systems
   - ISA Global Cybersecurity Alliance

### 📚 Best Practices & Vendor Guides

1. **ai_powered_ics_security_2024.pdf** (2024)
   - AI/ML for ICS security
   - Emerging cyber threats
   - SCADA vulnerabilities + AI-driven solutions

2. **cisco_pipeline_security_reference.pdf**
   - Pipeline security (critical for O&G)
   - Technical reference document
   - Network architecture and security controls

---

## Use Cases for INSA CRM Agents

### 1. Customer Security Assessments

**Before:**
```
Agent: "Generic security assessment template"
```

**After (with Industrial Cyber knowledge):**
```
Agent: "Oil & Gas Security Assessment based on:
  - CISA ICS Best Practices (7-step framework)
  - NIST CSF 2.0 (Identify, Protect, Detect, Respond, Recover)
  - IEC 62443 Security Levels (SL1-SL4)
  - ONG-C2M2 Maturity Model

Specific checks for SCADA, DCS, PLCs:
  ✓ Network segmentation (Purdue Model)
  ✓ Access controls and authentication
  ✓ Vulnerability management
  ✓ Incident response procedures

Source: CISA ICS Best Practices + IEC 62443 Quick Start Guide"
```

### 2. Quotation Generation (AI-powered)

**Before:**
```
Generate quote for "SCADA security project"
Result: Generic equipment list
```

**After:**
```
Generate quote for "SCADA security project" using industrial cyber knowledge:

Based on CISA "Seven Steps to Defend ICS":
  1. Network Segmentation
     - Firewall for OT network: $15,000
     - DMZ implementation: $8,000

  2. IDS/IPS Deployment
     - Industrial IDS (per NIST CSF): $25,000
     - Monitoring solution: $12,000

  3. IEC 62443 Compliance Assessment
     - Security Level evaluation: $6,000
     - Gap analysis: $4,000

Total: $70,000

References:
  - CISA Seven Steps to Defend ICS (steps 1-3)
  - NIST CSF 2.0 (Detect function)
  - IEC 62443-3-3 (System security requirements)
```

### 3. Lead Scoring Enhancement

**Before:**
```
Lead: "Oil & Gas company needs cybersecurity help"
Score: 75/100 (generic criteria)
```

**After:**
```
Lead: "Oil & Gas company needs cybersecurity help"

Enhanced scoring with industrial cyber context:
  + High value: Oil & Gas sector (critical infrastructure)
  + Regulatory pressure: IEC 62443, NIST CSF
  + Threat landscape: High (per Canada Cyber Threat Assessment)
  + Budget availability: Above average (per WEF O&G Playbook)

Score: 92/100 (PRIORITY)

Recommended approach:
  1. Security assessment (CISA framework)
  2. IEC 62443 gap analysis
  3. SCADA network segmentation project

References:
  - WEF Cyber Resilience in O&G (board-level urgency)
  - Canada Cyber Threat Assessment (threat drivers)
```

### 4. Security Incident Response

**Before:**
```
Customer: "Our SCADA system was hacked"
Agent: "Contact IT security"
```

**After:**
```
Customer: "Our SCADA system was hacked"

Agent (using CISA ICS Incident Response guide):

IMMEDIATE ACTIONS (First 24 hours):
  1. ISOLATE affected systems (do NOT power off)
  2. PRESERVE evidence (memory, logs)
  3. NOTIFY CISA ICS-CERT (888-282-0870)
  4. ACTIVATE incident response team

ASSESSMENT (per CISA guide):
  - Type: ICS/SCADA compromise
  - Sector: Oil & Gas (critical infrastructure)
  - Potential impact: Safety + production + environment

RESPONSE TEAM:
  - IT security + OT engineers + safety team
  - Legal + communications (per WEF O&G Playbook)
  - Senior executives (board-level incident)

Next steps:
  - Forensic analysis (preserve evidence)
  - Root cause investigation
  - Remediation + hardening
  - Post-incident review

References:
  - CISA ICS Incident Response Guide (comprehensive)
  - WEF O&G Playbook (stakeholder collaboration)
```

---

## Integration with RAG System

### File: `system_knowledge_rag.py`

Add industrial cybersecurity paths:

```python
self.docs_paths = {
    # ... existing paths ...

    # Industrial Cybersecurity
    'cisa_ics': '/home/wil/automation/agents/orchestrator/knowledge/industrial-cyber/cisa-ics/*.pdf',
    'nist_framework': '/home/wil/automation/agents/orchestrator/knowledge/industrial-cyber/nist-framework/*.pdf',
    'oil_gas_cyber': '/home/wil/automation/agents/orchestrator/knowledge/industrial-cyber/oil-gas/*.pdf',
    'iec_62443': '/home/wil/automation/agents/orchestrator/knowledge/industrial-cyber/iec-62443/*.pdf',
    'best_practices': '/home/wil/automation/agents/orchestrator/knowledge/industrial-cyber/best-practices/*.pdf',
}
```

### Query Examples

```python
# Query for ICS security best practices
rag.query({
    'type': 'security_assessment',
    'sector': 'oil_gas',
    'topic': 'SCADA security'
})

# Returns: Relevant sections from CISA ICS, NIST CSF, IEC 62443

# Query for incident response
rag.query({
    'type': 'incident',
    'asset': 'SCADA',
    'severity': 'high'
})

# Returns: CISA ICS Incident Response procedures
```

---

## Licensing & Attribution

### CISA Documents
**License:** Public domain (US Government work)
**Use:** Unlimited - no attribution required
**Distribution:** Freely distribute

### NIST Documents
**License:** Public domain (US Government work)
**Use:** Unlimited
**Citation:** "NIST Cybersecurity Framework Version X.X"

### Oil & Gas Resources
**License:** Varies by publisher
**Use:** Educational/internal use
**Attribution Required:**
  - WEF: "World Economic Forum"
  - Fortinet, Infosys, Cisco: Vendor attribution

### ISA/IEC 62443 Free Resources
**License:** Free download from ISA Global Cybersecurity Alliance
**Use:** Educational purpose
**Attribution:** "ISA Global Cybersecurity Alliance"
**Note:** Full standards require purchase; these are free overviews

---

## Knowledge Base Statistics

| Category | Files | ~Total Size | Authority |
|----------|-------|-------------|-----------|
| CISA ICS | 5 | ~10 MB | US Government |
| NIST Framework | 2 | ~5 MB | NIST |
| Oil & Gas | 5 | ~15 MB | WEF, Gov, Vendors |
| IEC 62443 | 3 | ~8 MB | ISA/IEC |
| Best Practices | 2 | ~5 MB | Industry |
| **Total** | **17** | **~43 MB** | **Authoritative** |

---

## Next Steps

### Week 1
- [x] Download core documents ✅
- [ ] Extract key sections for RAG
- [ ] Test queries with SCADA security topics
- [ ] Integrate with CRM lead scoring

### Week 2
- [ ] Add threat intelligence (CISA alerts)
- [ ] Index PDFs with ChromaDB (semantic search)
- [ ] Create citation system
- [ ] Measure CRM agent improvement

### Month 2
- [ ] Download additional IEC 62443 resources
- [ ] Add vendor-specific guides (Siemens, Rockwell, etc.)
- [ ] Integrate with quotation generation system
- [ ] Customer security assessment templates

---

## Maintenance

**Quarterly:**
- Check for CISA ICS alert updates
- Download new NIST framework versions
- Update Oil & Gas threat assessments

**Annually:**
- Review IEC 62443 standard updates
- Download annual industry reports
- Archive outdated documents

---

## Support & Resources

**CISA ICS:** https://www.cisa.gov/topics/industrial-control-systems
**NIST CSF:** https://www.nist.gov/cyberframework
**ISA/IEC 62443:** https://gca.isa.org/
**SANS ICS:** https://www.sans.org/cyber-security-focus-areas/industrial-control-systems-security

**INSA Contact:** w.aroca@insaing.com

---

**Created:** November 1, 2025
**Purpose:** Enhance INSA CRM with industrial cybersecurity expertise
**Impact:** Transform generic CRM into Oil & Gas security specialist
EOF

# Create quick reference index
cat > "$BASE_DIR/QUICK_REFERENCE.md" << 'EOF'
# Industrial Cybersecurity Quick Reference for INSA Agents

## Top 3 Must-Read Documents

1. **CISA ICS Best Practices** (cisa-ics/cisa_ics_best_practices.pdf)
   - Start here for any ICS security question
   - Comprehensive, authoritative, practical

2. **NIST CSF 2.0** (nist-framework/nist_csf_2.0.pdf)
   - Framework for security program structure
   - Maps to all other standards

3. **ISAGCA Quick Start Guide** (iec-62443/isagca_quick_start_guide.pdf)
   - IEC 62443 overview
   - Compliance requirements

## Quick Answers

**"How to secure SCADA?"**
→ cisa-ics/seven_steps_defend_ics.pdf

**"What is IEC 62443?"**
→ iec-62443/isagca_quick_start_guide.pdf

**"Oil & Gas cyber threats?"**
→ oil-gas/canada_cyber_threat_oil_gas.pdf

**"Incident response for ICS?"**
→ cisa-ics/ics_incident_response.pdf

**"Network segmentation?"**
→ cisa-ics/cisa_ics_best_practices.pdf (Section 3.2)

## Security Levels (IEC 62443)

- **SL 1:** Protection against casual or coincidental violation
- **SL 2:** Protection against intentional violation using simple means
- **SL 3:** Protection against intentional violation using sophisticated means
- **SL 4:** Protection against intentional violation using sophisticated means with extended resources

**Oil & Gas Recommendation:** SL 2-3 for most facilities

## NIST CSF Core Functions

1. **Identify** - Asset management, risk assessment
2. **Protect** - Access control, data security
3. **Detect** - Anomalies, continuous monitoring
4. **Respond** - Response planning, communications
5. **Recover** - Recovery planning, improvements

## Purdue Model (Network Segmentation)

```
Level 5: Enterprise Network (IT)
   ↕ Firewall/DMZ
Level 4: Business Planning & Logistics
   ↕ Firewall/DMZ
Level 3: Site Operations & Control
   ↕ Firewall (CRITICAL)
Level 2: Area Supervisory Control (SCADA/HMI)
Level 1: Basic Control (PLCs, RTUs)
Level 0: Process (Sensors, Actuators)
```

**Key:** Strong isolation between Level 3-4 (IT/OT boundary)
EOF

echo -e "${GREEN}✅ Documentation created${NC}"
echo ""

# Summary
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}Download Summary${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

echo -e "${GREEN}Downloaded Documents:${NC}"
for dir in cisa-ics nist-framework oil-gas iec-62443 best-practices; do
    count=$(ls -1 "$BASE_DIR/$dir"/*.pdf 2>/dev/null | wc -l)
    size=$(du -sh "$BASE_DIR/$dir" 2>/dev/null | cut -f1)
    echo "  $dir: $count files ($size)"
done

echo ""
total_size=$(du -sh "$BASE_DIR" | cut -f1)
total_files=$(find "$BASE_DIR" -name "*.pdf" 2>/dev/null | wc -l)

echo -e "${GREEN}Total: $total_files PDFs (~$total_size)${NC}"
echo ""

echo -e "${BLUE}Documentation:${NC}"
echo "  • README.md - Complete knowledge base guide"
echo "  • QUICK_REFERENCE.md - Agent quick reference"
echo ""

echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Review: $BASE_DIR/README.md"
echo "  2. Test: Open any PDF to verify downloads"
echo "  3. Integrate: Update system_knowledge_rag.py"
echo "  4. Query: 'What are CISA's 7 steps to defend ICS?'"
echo ""

echo -e "${GREEN}✅ Industrial Cybersecurity Knowledge Base Ready!${NC}"
echo -e "${GREEN}Your CRM agents now have Oil & Gas security expertise!${NC}"
