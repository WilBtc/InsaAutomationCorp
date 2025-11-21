# Industrial Cybersecurity Knowledge Base for INSA CRM RAG

**Purpose:** Provide CRM agents with Industrial Cybersecurity expertise for Oil & Gas customer engagements
**Sources:** CISA, NIST, Industry White Papers (All Free & Public Domain)
**Date:** November 1, 2025
**Status:** ✅ OPERATIONAL (8 PDFs, 11 MB)

---

## 📁 Directory Structure

```
industrial-cyber/
├── cisa-ics/              # CISA Industrial Control Systems security (7.4 MB)
├── nist-framework/        # NIST Cybersecurity Framework (2.5 MB)
├── oil-gas/               # Oil & Gas specific guidance (664 KB)
├── iec-62443/             # IEC 62443 standards (empty - manual download required)
├── best-practices/        # Industry best practices (empty - manual download required)
├── threat-reports/        # Threat intelligence reports (empty)
├── README.md              # This file
└── QUICK_REFERENCE.md     # Agent quick reference guide
```

---

## 📚 What's Available

### CISA ICS Security (5 PDFs - 7.4 MB)
1. **cisa_ics_best_practices.pdf** (2.5 MB)
   - Comprehensive ICS/OT cybersecurity best practices
   - 7-step framework for defending industrial systems
   - Network segmentation, access controls, monitoring

2. **common_ics_vulnerabilities.pdf** (4.0 MB)
   - Database of common ICS vulnerabilities
   - SCADA, DCS, PLC-specific issues
   - Mitigation strategies and patches

3. **ics_incident_response.pdf** (489 KB)
   - Incident response procedures for OT environments
   - Containment strategies that preserve operations
   - Recovery procedures for industrial systems

4. **ics_monitoring_technologies.pdf** (179 KB)
   - Overview of ICS monitoring technologies
   - Network monitoring, anomaly detection
   - Protocol analysis (Modbus, DNP3, ENIP, S7Comm)

5. **seven_steps_defend_ics.pdf** (295 KB)
   - Quick reference: 7 steps to defend ICS
   - Risk management, network segmentation
   - Vulnerability management, incident response

### NIST Cybersecurity Framework (2 PDFs - 2.5 MB)
6. **nist_csf_2.0.pdf** (1.5 MB)
   - ⭐ Latest NIST CSF 2.0 (2024)
   - 5 Core Functions: Identify, Protect, Detect, Respond, Recover
   - Implementation Tiers (1-4) for maturity assessment
   - Critical Infrastructure focus

7. **nist_csf_1.1.pdf** (1.1 MB)
   - NIST CSF 1.1 (2018) - still widely used
   - Reference for legacy assessments
   - Mapping to other frameworks (ISO, COBIT, etc.)

### Oil & Gas Specific (1 PDF - 664 KB)
8. **definitive_guide_oil_gas_cyber.pdf** (662 KB)
   - Oil & Gas industry cybersecurity overview
   - Sector-specific threats and controls
   - SCADA/DCS security for upstream/downstream operations

---

## 🎯 Use Cases

### 1. Customer Security Assessments
**Query:** "What security controls should we recommend for an Oil & Gas SCADA system?"

**Answer Sources:**
- `cisa_ics_best_practices.pdf` → 7-step defense framework
- `nist_csf_2.0.pdf` → Protect function controls
- `ics_monitoring_technologies.pdf` → Monitoring recommendations
- `common_ics_vulnerabilities.pdf` → Vulnerabilities to address

### 2. Incident Response Planning
**Query:** "Customer had a PLC compromise. What's the response procedure?"

**Answer Sources:**
- `ics_incident_response.pdf` → OT-specific incident response steps
- `nist_csf_2.0.pdf` → Respond function guidelines
- `cisa_ics_best_practices.pdf` → Containment strategies

### 3. Compliance & Risk Assessments
**Query:** "How do we assess cybersecurity maturity for Oil & Gas customer?"

**Answer Sources:**
- `nist_csf_2.0.pdf` → Implementation Tiers (1-4)
- `cisa_ics_best_practices.pdf` → ICS control baseline
- `definitive_guide_oil_gas_cyber.pdf` → Industry benchmarks

### 4. Quote Generation - Security Services
**Query:** "Generate security assessment quote for Oil & Gas facility"

**Answer Sources:**
- `seven_steps_defend_ics.pdf` → Scope of work (7 areas)
- `nist_csf_2.0.pdf` → Assessment methodology (5 functions)
- `ics_monitoring_technologies.pdf` → Technology recommendations

### 5. Lead Qualification
**Query:** "Is this lead a good fit for ICS security services?"

**Answer Sources:**
- `cisa_ics_best_practices.pdf` → Determine if they have ICS
- `definitive_guide_oil_gas_cyber.pdf` → Sector-specific needs
- `common_ics_vulnerabilities.pdf` → Risk assessment

---

## 🔗 Integration with RAG System

### Query Path
1. **CRM Agent** receives customer question
2. **system_knowledge_rag.py** extracts keywords (ICS, SCADA, Oil & Gas, etc.)
3. **PDF Parser** searches relevant PDFs in industrial-cyber/
4. **Context Builder** combines relevant sections
5. **CRM Agent** generates answer with citations

### Expected Integration
```python
# In system_knowledge_rag.py:
self.docs_paths = {
    # ... existing paths ...
    'industrial_cyber_cisa': '/home/wil/automation/agents/orchestrator/knowledge/industrial-cyber/cisa-ics/*.pdf',
    'industrial_cyber_nist': '/home/wil/automation/agents/orchestrator/knowledge/industrial-cyber/nist-framework/*.pdf',
    'industrial_cyber_oil_gas': '/home/wil/automation/agents/orchestrator/knowledge/industrial-cyber/oil-gas/*.pdf',
}
```

### PDF Text Extraction
```python
from PyPDF2 import PdfReader

def extract_pdf_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text
```

---

## 📊 Coverage Analysis

### ✅ Strong Coverage
- **CISA ICS Best Practices**: Comprehensive (7.4 MB, 5 documents)
- **NIST Framework**: Complete (CSF 1.1 + 2.0)
- **Incident Response**: Covered
- **Vulnerability Management**: Covered
- **Monitoring Technologies**: Covered

### ⚠️ Partial Coverage
- **Oil & Gas Specific**: 1 of 5 documents (20%)
- **IEC 62443 Standards**: 0 of 3 documents (0%) ← Manual download required
- **Best Practices**: 0 of 2 documents (0%) ← Manual download required

### 📈 Overall Status
- **8 of 17 PDFs** = 47% complete
- **11 MB of 43 MB** = 26% of planned size
- **Critical Core Content**: ✅ Complete (CISA + NIST)
- **Industry-Specific Content**: ⚠️ Needs manual downloads

---

## 🚀 To Complete Knowledge Base

### Manual Downloads Required

1. **WEF Cyber Resilience Playbook for Oil & Gas** (Failed to auto-download)
   ```bash
   wget -O oil-gas/wef_cyber_resilience_oil_gas.pdf \
     "https://www3.weforum.org/docs/WEF_Board_Principles_Playbook_Oil_and_Gas_2021.pdf"
   ```

2. **IEC 62443 Resources** (Require form submission)
   - Visit: https://gca.isa.org/resources
   - Download: Quick Start Guide, Security Requirements PDFs
   - Save to: `iec-62443/`

3. **Additional Oil & Gas Guides**
   - Canadian Government: Oil & Gas Cyber Protection Guide
   - Fortinet: Oil & Gas Security White Paper
   - Cisco: Pipeline Cybersecurity Best Practices

4. **Best Practices**
   - AI-Powered ICS Security 2024
   - API 1164: Pipeline SCADA Security

---

## 🔐 Licensing

### CISA Documents (5 PDFs)
- **License**: Public Domain (US Government)
- **Attribution**: "Cybersecurity and Infrastructure Security Agency (CISA)"
- **Use**: Unrestricted
- **Redistribution**: Allowed

### NIST Documents (2 PDFs)
- **License**: Public Domain (US Government)
- **Attribution**: "National Institute of Standards and Technology (NIST)"
- **Use**: Unrestricted
- **Redistribution**: Allowed

### Oil & Gas Guide (1 PDF)
- **License**: Free download, no resale
- **Attribution**: "Biblioteca de Segurança" + URL
- **Use**: Internal reference only

---

## 🔄 Maintenance

### Monthly
- Check CISA for new ICS publications
- Monitor NIST for CSF updates
- Search for new Oil & Gas sector reports

### Quarterly
- Review agent usage statistics
- Identify knowledge gaps from failed queries
- Download additional resources based on needs

### Annually
- Archive outdated documents
- Verify all PDFs still downloadable
- Update this README with new content

---

## 📞 Contact

**Organization**: Insa Automation Corp
**Purpose**: Internal CRM knowledge base for Oil & Gas cybersecurity
**Email**: w.aroca@insaing.com

---

**Last Updated:** November 1, 2025 03:50 UTC
**Download Script:** `/home/wil/automation/agents/orchestrator/download_industrial_cyber_knowledge.sh`
