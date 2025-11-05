# SANS Knowledge Base for RAG System

**Purpose:** Enhance autonomous agent security intelligence
**Source:** SANS Institute (free resources)
**Date:** November 1, 2025

## Directory Structure

```
sans/
├── ics-ot/              # ICS/OT cybersecurity reports (CRITICAL for Oil & Gas)
├── general/             # General cybersecurity reports
├── threat-intel/        # Live threat feeds from SANS ISC (updated hourly)
├── reading-room/        # SANS Reading Room papers (download manually)
├── DOWNLOAD_INSTRUCTIONS.md
└── README.md (this file)
```

## What's Here

### Threat Intelligence (Auto-updated)
- **blocklist.txt** - Top malicious IPs (block these)
- **top_100_ips.txt** - Top 100 attackers
- **threat_intel.txt** - Comprehensive threat intelligence feed

Update frequency: Hourly (max) via cron job

### White Papers (Manual download required)
See `DOWNLOAD_INSTRUCTIONS.md` for URLs and process.

Priority downloads:
1. SANS 2024 State of ICS/OT Cybersecurity
2. 2025 ICS/OT Budget Report
3. IEC 62443 Implementation Guide

## Integration with RAG

The `system_knowledge_rag.py` module will query these files when agents need:
- Security threat information
- ICS/OT best practices
- IEC 62443 compliance guidance
- Incident response procedures
- Budget planning data

## Licensing

**SANS ISC Feeds:**
- License: Creative Commons "Share Alike"
- Use: Free for non-commercial with attribution
- Attribution: "SANS Technology Institute, Internet Storm Center"

**SANS White Papers:**
- License: Free download, no resale
- Use: Internal training and reference
- Attribution: "SANS Institute" + URL

## Maintenance

**Weekly:**
- Check for new SANS white papers (2025 surveys/reports)
- Download relevant Reading Room papers

**Hourly (automated via cron):**
- Update ISC threat feeds
- Refresh blocklist

**Monthly:**
- Review usage statistics
- Add papers based on agent queries

## Contact

User-Agent for ISC API: "INSA-Automation w.aroca@insaing.com"
Organization: Insa Automation Corp
Purpose: Internal cybersecurity automation
