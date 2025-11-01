# Industrial Cybersecurity - Quick Reference for CRM Agents

**For:** Autonomous CRM agents (lead qualification, quote generation, customer communication)
**Knowledge Base:** 8 PDFs, 11 MB of authoritative ICS/OT cybersecurity content
**Sources:** CISA (US Gov), NIST (US Gov), Industry White Papers

---

## 🎯 When to Use This Knowledge

### Trigger Keywords in Customer Queries
- **ICS/OT**: Industrial Control Systems, Operational Technology
- **SCADA**: Supervisory Control and Data Acquisition
- **DCS**: Distributed Control Systems
- **PLC**: Programmable Logic Controllers
- **Oil & Gas**: Upstream, midstream, downstream operations
- **Cybersecurity**: Risk assessment, compliance, incident response
- **Standards**: IEC 62443, NIST CSF, CISA

### Customer Engagement Scenarios
1. **Lead Qualification** → Use CISA best practices to assess ICS security maturity
2. **Quote Generation** → Use NIST CSF functions to scope security assessments
3. **Customer Questions** → Use PDFs to provide authoritative answers
4. **Risk Assessment** → Use common vulnerabilities database
5. **Incident Response** → Use CISA IR procedures

---

## 📚 Document Quick Reference

### 🏛️ CISA ICS Best Practices (2.5 MB)
**File:** `cisa-ics/cisa_ics_best_practices.pdf`

**When to Use:**
- Customer asks: "What security controls do we need for SCADA?"
- Quote Generation: Scoping ICS security assessments
- Lead Qualification: Determining customer maturity level

**Key Content:**
- **7 Steps to Defend ICS:**
  1. Risk Management
  2. Network Segmentation (Purdue Model)
  3. Access Controls & Authentication
  4. Monitoring & Detection
  5. Vulnerability Management
  6. Incident Response
  7. Awareness & Training

**Example Answer:**
```
"Based on CISA's ICS Best Practices, your SCADA system should implement:
1. Network segmentation following the Purdue Model (Level 0-4)
2. Multi-factor authentication for all remote access
3. Continuous monitoring with protocol-aware tools
4. Regular vulnerability scanning (quarterly minimum)
5. Documented incident response procedures
6. Annual security awareness training

INSA can provide a comprehensive assessment based on these 7 CISA-recommended steps."
```

---

### 🏛️ NIST Cybersecurity Framework 2.0 (1.5 MB)
**File:** `nist-framework/nist_csf_2.0.pdf`

**When to Use:**
- Customer asks: "How do we assess our cybersecurity maturity?"
- Quote Generation: Structuring security assessment offerings
- Compliance Discussions: Industry-standard framework

**Key Content:**
- **5 Core Functions:**
  1. **Identify** - Asset management, risk assessment
  2. **Protect** - Access controls, training, maintenance
  3. **Detect** - Monitoring, anomaly detection
  4. **Respond** - Incident response, communications
  5. **Recover** - Recovery planning, improvements

- **Implementation Tiers (Maturity Levels):**
  - Tier 1: Partial (ad hoc, reactive)
  - Tier 2: Risk Informed (risk management approved but not policy)
  - Tier 3: Repeatable (formal policies and procedures)
  - Tier 4: Adaptive (continuous improvement, threat intelligence)

**Example Answer:**
```
"Using NIST CSF 2.0, we assess your cybersecurity across 5 functions:

1. IDENTIFY: Current assets, risks, vulnerabilities
2. PROTECT: Access controls, security training
3. DETECT: Monitoring systems, anomaly detection
4. RESPOND: Incident response procedures
5. RECOVER: Business continuity plans

Our assessment determines your Implementation Tier (1-4) and creates a roadmap
to achieve Tier 3 (Repeatable) or Tier 4 (Adaptive) maturity.

Estimated Cost: $15,000-25,000 for full NIST CSF assessment"
```

---

### 🛡️ Common ICS Vulnerabilities (4.0 MB)
**File:** `cisa-ics/common_ics_vulnerabilities.pdf`

**When to Use:**
- Customer mentions specific ICS vendors (Siemens, Rockwell, Schneider Electric)
- Risk assessment discussions
- Vulnerability scanning quotes

**Key Content:**
- Known vulnerabilities by ICS vendor and product
- CVE database for SCADA/DCS/PLC systems
- Recommended patches and mitigations
- Severity ratings (Critical, High, Medium, Low)

**Example Answer:**
```
"Based on CISA's ICS vulnerability database, your Allen-Bradley PLCs
have 3 known Critical vulnerabilities:

1. CVE-2024-XXXX: Authentication bypass (CVSS 9.8)
2. CVE-2024-YYYY: Remote code execution (CVSS 9.1)
3. CVE-2024-ZZZZ: Denial of service (CVSS 7.5)

INSA recommends:
- Immediate patching to firmware version X.X
- Network segmentation to isolate vulnerable PLCs
- Enhanced monitoring for exploit attempts

Vulnerability Assessment + Remediation: $8,000-12,000"
```

---

### 🚨 ICS Incident Response (489 KB)
**File:** `cisa-ics/ics_incident_response.pdf`

**When to Use:**
- Customer reports security incident or breach
- Incident response planning discussions
- Post-incident analysis

**Key Content:**
- OT-specific incident response procedures
- Containment strategies that preserve operations
- Evidence collection for industrial systems
- Recovery procedures for SCADA/DCS/PLCs
- Coordination with IT incident response

**Example Answer:**
```
"For your PLC compromise, CISA's ICS Incident Response Guide recommends:

IMMEDIATE (0-4 hours):
1. Isolate affected PLCs (maintain safe state, do NOT shut down)
2. Capture network traffic for forensics
3. Document all actions (legal/regulatory requirements)

SHORT-TERM (4-24 hours):
4. Analyze malware/attack vector
5. Apply patches/firmware updates
6. Restore from known-good backups

LONG-TERM (1-7 days):
7. Root cause analysis
8. Update network segmentation
9. Enhance monitoring
10. Lessons learned document

INSA provides 24/7 OT incident response retainer: $5,000/month"
```

---

### 📊 ICS Monitoring Technologies (179 KB)
**File:** `cisa-ics/ics_monitoring_technologies.pdf`

**When to Use:**
- Customer asks: "How do we monitor our SCADA network?"
- Technology recommendations for quotes
- Security monitoring service discussions

**Key Content:**
- Network monitoring approaches (passive taps, SPAN ports)
- Protocol-aware monitoring (Modbus, DNP3, ENIP, S7Comm, OPC UA)
- Anomaly detection techniques
- SIEM integration for OT
- Commercial and open-source tools

**Example Answer:**
```
"Based on CISA's ICS Monitoring Technologies guide, we recommend:

NETWORK MONITORING:
- Nozomi Networks or Claroty for OT-specific monitoring
- Passive network taps (no impact to operations)
- Protocol analysis: Modbus TCP, DNP3, ENIP, S7Comm

ANOMALY DETECTION:
- Baseline normal SCADA traffic patterns
- Alert on unauthorized commands to PLCs
- Detect new devices on OT network

SIEM INTEGRATION:
- Forward OT alerts to centralized SIEM
- Correlate IT + OT security events

Hardware: $25,000-50,000 (sensors + appliances)
Software Licensing: $10,000-20,000/year
INSA Installation & Integration: $15,000-25,000"
```

---

### 📖 Seven Steps to Defend ICS (295 KB)
**File:** `cisa-ics/seven_steps_defend_ics.pdf`

**When to Use:**
- Quick reference for customer calls
- Lead qualification checklists
- Security roadmap creation

**Key Content:**
- Simplified 7-step framework (quick version of best practices)
- Checklist format for each step
- Prioritization guidance

**Example Answer:**
```
"CISA's 7 Steps to Defend Your ICS provides a roadmap:

✓ Step 1: Risk Management (identify critical assets)
✓ Step 2: Network Segmentation (Purdue Model zones)
✓ Step 3: Access Controls (MFA, least privilege)
✓ Step 4: Monitoring (protocol-aware detection)
✓ Step 5: Vulnerability Management (patch management)
✓ Step 6: Incident Response (OT-specific procedures)
✓ Step 7: Awareness Training (ICS security focus)

INSA offers a 7-Step Security Roadmap service:
- Phase 1: Assessment (Steps 1-2) - $15,000
- Phase 2: Implementation (Steps 3-5) - $35,000-50,000
- Phase 3: Operations (Steps 6-7) - $10,000 + ongoing retainer"
```

---

### 🏛️ NIST CSF 1.1 (1.1 MB)
**File:** `nist-framework/nist_csf_1.1.pdf`

**When to Use:**
- Customer references older NIST CSF
- Legacy system assessments
- Comparison to NIST CSF 2.0

**Key Content:**
- 5 Core Functions (same as 2.0 but different categories)
- Mapping to other frameworks (ISO 27001, COBIT, CIS Controls)
- Implementation examples

**Example Answer:**
```
"Your current NIST CSF 1.1 assessment is still valid, but we recommend
upgrading to NIST CSF 2.0 (released 2024) because:

1. Enhanced OT/ICS guidance
2. Supply chain risk management
3. Updated threat landscape
4. Better alignment with IEC 62443

Gap Analysis (CSF 1.1 → 2.0): $5,000-8,000
Full CSF 2.0 Re-assessment: $15,000-25,000"
```

---

### 🛢️ Definitive Guide to Oil & Gas Cybersecurity (662 KB)
**File:** `oil-gas/definitive_guide_oil_gas_cyber.pdf`

**When to Use:**
- Oil & Gas specific customer engagements
- Upstream/midstream/downstream operations
- Sector-specific threats and controls

**Key Content:**
- Oil & Gas threat landscape
- Sector-specific vulnerabilities
- SCADA/DCS security for O&G operations
- Regulatory compliance (NERC CIP, API 1164)

**Example Answer:**
```
"For Oil & Gas operations, the Definitive Guide highlights unique risks:

UPSTREAM (Exploration/Production):
- Remote SCADA sites with limited physical security
- Satellite/wireless communications (vulnerable to intercept)
- Legacy RTUs without modern security features

MIDSTREAM (Pipelines/Storage):
- Pipeline SCADA monitoring (API 1164 compliance)
- Leak detection systems (safety-critical)
- NERC CIP requirements for oil pipelines

DOWNSTREAM (Refining/Distribution):
- DCS for refinery process control
- Blending systems (product quality + safety)
- Loading rack automation

INSA specializes in Oil & Gas ICS security:
- NERC CIP compliance audits
- API 1164 gap assessments
- SCADA hardening for remote sites"
```

---

## 🎯 Quick Decision Tree for Agents

### Is customer in Oil & Gas sector?
- **YES** → Start with `definitive_guide_oil_gas_cyber.pdf`
- **NO** → Start with `cisa_ics_best_practices.pdf`

### What is customer asking for?
- **"How mature are we?"** → Use `nist_csf_2.0.pdf` (Implementation Tiers)
- **"What should we do first?"** → Use `seven_steps_defend_ics.pdf` (Roadmap)
- **"We had an incident"** → Use `ics_incident_response.pdf` (IR procedures)
- **"What are our risks?"** → Use `common_ics_vulnerabilities.pdf` (CVE database)
- **"How do we monitor?"** → Use `ics_monitoring_technologies.pdf` (Tools/approaches)

### What is the engagement type?
- **Lead Qualification** → Use `seven_steps_defend_ics.pdf` checklist
- **Quote Generation** → Use `nist_csf_2.0.pdf` for scope + pricing
- **Customer Questions** → Use all PDFs for comprehensive answers with citations

---

## 💰 Pricing Guidance Based on Documents

### NIST CSF Assessment
- **Tier 1 → Tier 2**: $10,000-15,000 (basic risk management)
- **Tier 2 → Tier 3**: $20,000-35,000 (formal policies + procedures)
- **Tier 3 → Tier 4**: $40,000-60,000 (adaptive + threat intelligence)

### CISA 7-Step Roadmap
- **Assessment (Steps 1-2)**: $15,000
- **Implementation (Steps 3-5)**: $35,000-50,000
- **Operations (Steps 6-7)**: $10,000 + $5,000/month retainer

### Specialized Services
- **Vulnerability Assessment**: $8,000-12,000
- **Incident Response (24/7 retainer)**: $5,000/month
- **ICS Monitoring (installation + 1-year)**: $50,000-75,000
- **Oil & Gas SCADA Hardening**: $25,000-40,000 per site

---

## 📊 Citation Format for Answers

Always cite sources when referencing knowledge base:

**Good Example:**
```
"According to CISA's ICS Best Practices (2022), network segmentation
using the Purdue Model is essential for defending industrial control systems."
```

**Bad Example:**
```
"You need network segmentation." (No source citation)
```

**Include Document Details:**
- Source: CISA, NIST, or Industry name
- Document: ICS Best Practices, NIST CSF 2.0, etc.
- Year: (2022), (2024), etc.

---

## 🚀 Future Enhancements (Coming Soon)

### When IEC 62443 PDFs are added:
- Use for compliance discussions
- Security Level (SL) recommendations (SL1-SL4)
- Zone & Conduit architecture diagrams

### When additional Oil & Gas PDFs are added:
- WEF Cyber Resilience Playbook → Board-level guidance
- Canadian Gov Guide → Regulatory compliance
- API 1164 → Pipeline-specific requirements

---

**Last Updated:** November 1, 2025 03:55 UTC
**For Support:** Contact w.aroca@insaing.com
**Knowledge Base Location:** `/home/wil/automation/agents/orchestrator/knowledge/industrial-cyber/`
