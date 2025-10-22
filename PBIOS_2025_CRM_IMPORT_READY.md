# PBIOS 2025 - CRM Import Ready for Insa Automation Corp
**Date:** October 22, 2025
**Event:** Permian Basin International Oil Show 2025
**Prepared By:** Wil Aroca w.aroca@insaing.com
**Server:** iac1 (100.100.101.1)

---

## 📊 EXECUTIVE SUMMARY

**Total PBIOS Exhibitors Analyzed:** 678 companies
**Qualified Prospects Identified:** 258 companies (38% of total)
**Top 50 Highest-Scoring Prospects:** Ready for immediate CRM import

### Tier Breakdown

| Tier | Score Range | Count | Priority | Time Investment |
|------|-------------|-------|----------|-----------------|
| **TIER 1** 🔥 | 18-23 | **5 companies** | MUST VISIT | 30-45 min/booth |
| **TIER 2** 🌟 | 13-17 | **12 companies** | HIGH VALUE | 15-20 min/booth |
| **TIER 3** ✅ | 10-12 | **33 companies** | QUALIFIED | 5-10 min/booth |
| **TOTAL** | 10+ | **50 companies** | Import to CRM | - |

---

## 🔥 TIER 1: MUST-VISIT COMPANIES (5 Companies - Score 18+)

### 1. Saginaw Control & Engineering ⭐ **HIGHEST PRIORITY**
- **Score:** 23/23 (PERFECT MATCH)
- **Booth:** E-19
- **Category:** Control systems & engineering
- **Why Critical:**
  - Direct competitor/partner in control systems
  - Perfect alignment with INSA's core competencies
  - Engineering services + complex projects
- **Action Plan:**
  - Research their recent projects before event
  - Prepare custom INSA capabilities presentation
  - Schedule pre-event meeting if possible
  - Discuss collaboration on large projects
  - Explore subcontractor opportunities
- **Follow-up:** IMMEDIATE (within 24 hours post-event)

### 2. VanZandt Controls / Eagle Automation
- **Score:** 20/23
- **Booth:** J-123, J-124, J-125, OS193 (4 booths - MAJOR PRESENCE)
- **Category:** Oil & Gas Service Provider
- **Why Critical:**
  - Large multi-booth presence = major industry player
  - Control systems + automation focus
- **Action Plan:**
  - Identify their automation platform (PLC brands, SCADA)
  - Discuss integration capabilities
  - Explore mutual project opportunities
- **Follow-up:** HIGH (within 48 hours)

### 3. Vector Controls & Automation
- **Score:** 20/23
- **Booth:** A-3, A-4, A-5 (3 booths)
- **Category:** Automation Manufacturer
- **Why Critical:**
  - Direct overlap in automation services
  - Multi-booth presence indicates scale
- **Action Plan:**
  - Understand their product lines
  - Identify complementary vs. competing offerings
  - Explore OEM/reseller partnerships
- **Follow-up:** HIGH (within 48 hours)

### 4. FW Murphy Production Controls
- **Score:** 18/23
- **Booth:** A-1, A-2 (PRIME LOCATION - first booths at entrance)
- **Category:** Automation Equipment Manufacturer
- **Why Critical:**
  - Prime booth location = industry leader
  - Production control systems for oil & gas
- **Action Plan:**
  - Review their control panels and PLCs
  - Discuss integration with INSA's services
  - Explore becoming authorized integrator/installer
- **Follow-up:** HIGH (within 48 hours)

### 5. Vinson Process Controls Company
- **Score:** 18/23
- **Booth:** A-42, A-43, A-44, A-45 (4 booths - MAJOR PRESENCE)
- **Category:** Automation Equipment Manufacturer
- **Why Critical:**
  - Process control = INSA's core competency
  - 4-booth presence = substantial company
- **Action Plan:**
  - Deep dive into their process control solutions
  - Identify gaps where INSA can add value
  - Discuss becoming systems integrator
- **Follow-up:** HIGH (within 48 hours)

---

## 🌟 TIER 2: HIGH-VALUE PROSPECTS (12 Companies - Score 13-17)

### Engineering Firms (EPC Companies)
**Why Important:** These companies design and build facilities - they NEED automation integrators like INSA

6. **3S Engineering & Design** - Booth: J-119 (Score: 13)
7. **COMM Engineering** - Booth: D-32 (Score: 13)
8. **Crimson Engineering** - Booth: A-58, A-59 (Score: 13)
9. **KENCO Engineering** - Booth: B-92, B-93 (Score: 13)
10. **Lanmark Engineering** - Booth: D-104 (Score: 13)
11. **Wanner Engineering** - Booth: J-101 (Score: 13)

**Engagement Strategy for Engineering Firms:**
- Ask about upcoming projects requiring automation
- Share INSA's IEC 62443 compliance expertise (unique differentiator!)
- Offer to provide budgetary quotes for their proposals
- Exchange business cards for RFQ mailing list

### Control & Automation Companies
12. **Chicago Valves & Controls** - Booth: B-97 (Score: 13)
13. **Flo-Tite Valves & Controls** - Booth: C-84 (Score: 13)
14. **Legacy Flow Control** - Booth: J-10, J-8, J-9 (Score: 13)
15. **Pumps and Controls** - Booth: A-31 (Score: 13)

**Engagement Strategy:**
- Identify if they're manufacturers or distributors
- Explore integration partnership opportunities
- Discuss co-marketing for complete solutions

### Service & Equipment
16. **Filtration Systems / Fluid Power Energy** - Booth: E-57, E-58 (Score: 14)
17. **Central Power Systems & Services** - Booth: OS111, OS112 (Score: 13)

---

## ✅ TIER 3: QUALIFIED NETWORKING (33 Companies - Score 10-12)

**Strategy:** Quick visits, business card exchange
**Time Investment:** 5-10 minutes per booth
**Goal:** Build industry awareness, identify future opportunities

**Select TIER 3 Companies:**
18. 2A Energy Services - Booth: A-37, A-38 (Score: 12)
19. Creedence Energy Services - Booth: D-44 (Score: 12)
20. Double T Oilfield Services - Booth: E-7 (Score: 12)
21. Automation-X - Booth: B-63, B-64 (Score: 11)
22. Beckhoff Automation - Booth: B-22, B-23 (Score: 11) - Major PLC brand!
23. CONSPEC Controls - Booth: C-68, C-69 (Score: 11)
24. Edwards Automation and Design - Booth: E-117 (Score: 11)

*(Full list of 33 TIER 3 companies available in source data)*

---

## 📋 CRM IMPORT INSTRUCTIONS

### Using ERPNext MCP Tools via Claude Code

**TIER 1 Import (5 companies):**
```
In Claude Code, use:
erpnext_create_lead({
  "lead_name": "Company Name",
  "company_name": "Company Name",
  "source": "Event - PBIOS 2025",
  "status": "Open",
  "custom_booth": "Booth Number",
  "custom_tier": "TIER 1 - Must Visit",
  "custom_score": 23
})
```

**Lead Fields to Include:**
- **lead_name**: Company name
- **company_name**: Same as lead_name
- **source**: "Event - PBIOS 2025"
- **status**: "Open" (new lead, not yet contacted)
- **custom_booth**: Booth number(s)
- **custom_tier**: TIER 1/2/3 designation
- **custom_score**: Numerical score (10-23)
- **custom_priority**: "High" for TIER 1
- **notes**: Match reasons, engagement strategy

### Custom Fields Needed in ERPNext

If these custom fields don't exist, create them:
1. **custom_booth** (Data field) - Booth number
2. **custom_tier** (Select: TIER 1, TIER 2, TIER 3)
3. **custom_score** (Int) - Lead score 0-23
4. **custom_event_name** (Data) - Event name
5. **custom_priority** (Select: High, Medium, Low)

### Batch Import Approach

**Phase 1:** Import TIER 1 (5 companies) - IMMEDIATE
**Phase 2:** Import TIER 2 (12 companies) - Within 24 hours
**Phase 3:** Import TIER 3 (33 companies) - Within 1 week

---

## 🎯 KEY TALKING POINTS FOR INSA

### Unique Differentiators

1. **IEC 62443 Compliance Expertise** ⭐ (Few competitors have this)
   - "We specialize in industrial cybersecurity for automation systems"
   - "Our designs meet IEC 62443 requirements for oil & gas facilities"

2. **Full-Stack Automation Capabilities**
   - "From panel design to SCADA programming to commissioning"
   - "We handle the complete automation project lifecycle"

3. **Permian Basin Local Presence**
   - "Texas-based with deep Permian Basin experience"
   - "Fast response for service, modifications, and emergencies"

4. **Multi-Platform Expertise**
   - "Platform-agnostic: Allen-Bradley, Siemens, Schneider, Modicon, GE"
   - "We integrate whatever equipment you already have"

5. **Proven Oil & Gas Track Record**
   - Share specific examples (production automation, compressor stations, etc.)

### Questions to Ask Prospects

- "What automation projects do you have coming up in the next 6-12 months?"
- "What PLC/SCADA platforms do you typically work with?"
- "Do you have in-house automation engineering, or do you outsource?"
- "Are you familiar with IEC 62443 compliance requirements?"
- "What's your biggest challenge in current automation projects?"

---

## 📧 POST-EVENT FOLLOW-UP TIMELINE

### Day 1 After Event (Same Day if Possible)
- **TIER 1 Follow-up:** Email all 5 companies
  - Subject: "Great meeting you at PBIOS - [Specific topic discussed]"
  - Reference specific conversation points
  - Attach relevant INSA case study
  - Propose next steps (call, quote, meeting)

### Week 1
- **TIER 1:** Schedule follow-up calls (within 5 business days)
- **TIER 2:** Send personalized emails (reference booth conversation)
- **CRM Entry:** Ensure all contacts logged in ERPNext

### Week 2
- **TIER 1:** Send proposals/quotes if discussed
- **TIER 2:** Follow-up calls with interested prospects
- **TIER 3:** General follow-up email campaign

### Month 1-3
- Nurture campaign for all prospects
- Quarterly check-ins
- Share INSA news/case studies

---

## 📊 SUCCESS METRICS

### Event Goals
- [ ] Visit all 5 TIER 1 companies (100%)
- [ ] Visit at least 10 TIER 2 companies (83%)
- [ ] Collect 50+ qualified business cards
- [ ] Schedule 3+ post-event follow-up calls
- [ ] Identify 1-2 immediate project opportunities

### 30-Day Goals
- [ ] Convert 2+ TIER 1 prospects to active discussions
- [ ] Submit 2+ quotes/proposals
- [ ] Add all 50 prospects to ERPNext CRM
- [ ] Close 1 project within 90 days

### 90-Day Goals
- [ ] Win 1+ project from PBIOS leads
- [ ] Establish 2+ ongoing relationships
- [ ] Generate $50K+ in pipeline value

---

## 📁 DATA FILES REFERENCE

**Location:** `/home/wil/J.casas/`

1. **insa_prospect_analysis.json**
   - Complete prospect database (258 qualified)
   - Top 50 with detailed scoring
   - Match reasons and keywords
   - **USE THIS FOR CRM IMPORT**

2. **pbios_2025_exhibitors_FINAL.xlsx**
   - All 678 companies with contact data
   - Enriched with web research
   - Full address, phone, email (where available)

3. **INSA_TOP_PROSPECTS_PBIOS_2025.md**
   - Detailed engagement strategies
   - Pre-event action plan
   - Visit schedule recommendations

4. **PBIOS_2025_RESEARCH_PROGRESS_REPORT.md**
   - Research methodology
   - Data completeness analysis
   - Batch enrichment status

---

## 🚀 IMMEDIATE NEXT STEPS

### For Juan Casas / INSA Team

1. **Review This Report** ✅
   - Confirm TIER 1 priorities
   - Adjust strategy if needed

2. **Import to ERPNext CRM** 🔄 (IN PROGRESS)
   - Use ERPNext MCP tools via Claude Code
   - Start with TIER 1 (5 companies)
   - Then TIER 2 (12 companies)
   - Finally TIER 3 (33 companies)

3. **Prepare Marketing Materials**
   - INSA capabilities brochure
   - Business cards (bring 300+)
   - Case study one-pagers (2-3 relevant projects)
   - Highlight IEC 62443 compliance expertise

4. **Pre-Event Research** (TIER 1 only)
   - Visit websites of all 5 TIER 1 companies
   - Review LinkedIn profiles
   - Identify key contacts
   - Prepare custom talking points

5. **Optional: Pre-Event Outreach**
   - Email TIER 1 companies
   - Request 15-minute booth meeting
   - Subject: "PBIOS 2025 Meeting - Automation Integration Partnership"

---

## 💡 WHY THIS ANALYSIS MATTERS

**Strategic Value:**
- **Saves Time:** Focus on 50 qualified prospects instead of 678 random booths
- **Increases ROI:** 5 TIER 1 companies = highest conversion probability
- **Competitive Edge:** Pre-event research gives INSA advantage over walk-ins
- **Measurable:** Clear scoring system allows post-event analysis

**Expected Outcomes:**
- 2-3 immediate project opportunities from TIER 1
- 5-10 qualified proposals submitted within 30 days
- 1-2 projects won within 90 days
- Long-term relationships with 5+ new partners/clients

---

## 📞 CONTACT

**Prepared By:**
Wil Aroca
INSA Automation Corp
w.aroca@insaing.com
Server: iac1 (100.100.101.1)

**Data Sources:**
- PBIOS 2025 Official Exhibitor List (678 companies)
- AI-Powered Keyword Analysis
- Web Research & Enrichment (405 companies researched)
- INSA Competency Alignment Scoring

**Analysis Date:** October 21-22, 2025
**CRM Import Ready:** October 22, 2025

---

✅ **READY TO IMPORT INTO ERPNEXT CRM**
✅ **READY FOR EVENT EXECUTION**
✅ **READY TO GENERATE LEADS FOR INSA**

---

*This analysis identified 258 qualified prospects from 678 PBIOS exhibitors using AI-powered keyword matching aligned with INSA's core competencies in industrial automation, process control, and oil & gas systems integration.*

**Made by Insa Automation Corp for OpSec**
