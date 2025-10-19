# IEC 62443 Compliance Automation Platform - Beta Program

**Program Name:** INSA IEC 62443 Compliance Pilot
**Launch Date:** Q4 2025 / Q1 2026
**Duration:** 90 days per customer
**Target:** 3-5 Oil & Gas / Critical Infrastructure companies
**Status:** READY TO LAUNCH

---

## 🎯 PROGRAM OVERVIEW

### What We're Offering

**INSA IEC 62443 Compliance Automation Platform** - The world's first automated Foundational Requirement (FR) and System Requirement (SR) tagging platform for industrial cybersecurity compliance.

**Beta Program Benefits:**
- ✅ **FREE 90-day pilot** (zero cost, zero commitment)
- ✅ **Dedicated support** (direct access to development team)
- ✅ **Custom configuration** for your environment
- ✅ **Training & documentation** (comprehensive onboarding)
- ✅ **Priority feature requests** (shape the product roadmap)
- ✅ **Exclusive pricing** (50% discount if you convert to paid after pilot)

### What We're Seeking

**Feedback Partners** who will:
- Deploy platform in production or staging environment
- Provide weekly feedback on usability, accuracy, features
- Share anonymized compliance metrics for case studies
- Participate in 2-3 video calls during pilot period
- Provide testimonial if pilot is successful

**Ideal Candidates:**
- Oil & Gas operators with ICS/SCADA systems
- Manufacturing facilities with industrial automation
- Utilities (power, water, gas) with OT environments
- Critical infrastructure owners/operators
- Currently struggling with manual IEC 62443 compliance

---

## 💼 PLATFORM CAPABILITIES

### Core Features

**1. Automated Vulnerability Scanning**
- Trivy container scanning (every hour)
- Integration with Semgrep, Gitleaks, Nuclei
- 200+ scanner types supported (via DefectDojo)
- Automated import and processing

**2. Intelligent FR/SR Tagging** ⭐ **UNIQUE**
- Automatic mapping of findings to IEC 62443 requirements
- Foundational Requirements (FR-1 through FR-7)
- System Requirements (SR-1.1 through SR-7.8)
- Content-based analysis for tag assignment
- 100% automated (zero manual tagging)

**3. Compliance Dashboard**
- Real-time compliance status (http://100.100.101.1:3004)
- Findings by FR/SR category
- Severity distribution
- Trend analysis over time
- Exportable reports (PDF, CSV, JSON)

**4. DefectDojo Integration**
- 8 MCP tools for programmatic access:
  - get_findings (advanced filtering)
  - tag_finding (manual override)
  - auto_tag_findings (batch automation)
  - get_compliance_summary (metrics)
  - create_engagement (testing phases)
  - import_scan (200+ formats)
  - get_products (application inventory)
  - get_security_metrics (dashboards)

**5. Security Metrics & Reporting**
- Mean time to remediation (MTTR)
- Vulnerability aging analysis
- Compliance score per product
- Executive summaries (automated)
- Email reporting (daily/weekly)

### Technical Stack

**Backend:**
- DefectDojo 2.x (open-source security orchestration)
- PostgreSQL database
- RabbitMQ message queue
- Python 3.12

**Scanning Tools:**
- Trivy (containers, IaC, filesystems)
- Semgrep (code analysis)
- Gitleaks (secrets detection)
- Nuclei (web vulnerabilities)
- 200+ additional scanners supported

**Deployment:**
- Docker Compose (simple deployment)
- Self-hosted (on-premises or cloud)
- Tailscale VPN (secure access)
- Ubuntu 24.04 LTS recommended

---

## 📋 BETA PROGRAM STRUCTURE

### Phase 1: Onboarding (Week 1-2)

**Goals:**
- Platform deployed in customer environment
- Initial scans completed
- Team trained on basic operation

**Activities:**
1. **Kickoff Call** (60 minutes)
   - Requirements gathering
   - Environment assessment
   - Success criteria definition
   - Schedule establishment

2. **Deployment** (remote assistance provided)
   - Docker Compose installation
   - DefectDojo configuration
   - Scanner setup (Trivy minimum)
   - Compliance agent activation

3. **Training Session** (90 minutes)
   - Platform walkthrough
   - Dashboard navigation
   - MCP tools demonstration
   - Report generation
   - Q&A

4. **Initial Scan**
   - First Trivy scan execution
   - FR/SR auto-tagging demonstration
   - Compliance dashboard review
   - Baseline metrics captured

**Deliverables:**
- Platform deployed and operational
- Team trained (2-3 users minimum)
- First compliance report generated
- Baseline metrics documented

---

### Phase 2: Production Use (Week 3-8)

**Goals:**
- Daily/hourly automated scanning
- Compliance tracking over time
- Feature feedback collection
- Issue identification and resolution

**Activities:**
1. **Weekly Check-ins** (30 minutes)
   - Status review
   - Issues/questions discussion
   - Feature requests capture
   - Metrics review

2. **Automated Operations**
   - Hourly Trivy scans (auto-tagged)
   - Daily compliance summaries
   - Weekly executive reports
   - Continuous FR/SR mapping

3. **Feedback Collection**
   - Tagging accuracy assessment
   - Feature usability ratings
   - Performance monitoring
   - Bug reports

4. **Customization**
   - Custom scan configurations
   - Report template adjustments
   - Dashboard modifications
   - Integration enhancements

**Deliverables:**
- 6 weeks of compliance data
- Feedback survey completed weekly
- Issue log maintained
- Feature request list prioritized

---

### Phase 3: Evaluation & Next Steps (Week 9-12)

**Goals:**
- Pilot success assessment
- ROI calculation
- Commercialization decision
- Testimonial collection

**Activities:**
1. **Final Review Meeting** (90 minutes)
   - Pilot results presentation
   - ROI analysis
   - Success criteria evaluation
   - Next steps discussion

2. **Case Study Development**
   - Anonymized metrics compilation
   - Before/after comparison
   - Time savings quantification
   - Accuracy measurements

3. **Testimonial & Reference**
   - Written testimonial (if successful)
   - Reference customer agreement
   - Logo usage permission
   - Case study participation

4. **Commercialization Options**
   ```
   Option 1: Convert to Paid License
   - 50% discount on first year
   - Pricing: $5K-10K per site annually
   - Continued support and updates
   - Priority feature development

   Option 2: Extended Pilot
   - Additional 90 days free
   - Expanded scope (more sites)
   - Additional features testing
   - Delayed commercialization decision

   Option 3: End Pilot
   - Thank you, no commercial relationship
   - Platform can remain deployed
   - Community support only
   - No future obligations
   ```

**Deliverables:**
- Final pilot report
- ROI analysis document
- Case study (anonymized)
- Testimonial (if positive)
- Commercial agreement (if converting)

---

## 📊 SUCCESS METRICS

### Primary Metrics (Pilot Success Criteria)

**1. Tagging Accuracy** (Target: ≥90%)
- Percentage of findings correctly tagged to FR/SR
- Measured through manual review of 100 sample findings
- Calculated: Correct tags / Total tags × 100

**2. Time Savings** (Target: ≥60% reduction)
- Manual compliance time (before): Hours per week
- Automated compliance time (after): Hours per week
- Measured through time tracking logs

**3. Compliance Visibility** (Target: 100% coverage)
- Percentage of applications scanned
- Percentage of findings tagged
- Dashboard uptime and accessibility

**4. User Satisfaction** (Target: ≥4.0/5.0)
- Weekly surveys (5-point scale)
- Categories: Usability, Accuracy, Performance, Support
- Averaged across pilot duration

### Secondary Metrics (Product Development)

**5. Scanner Integration**
- Number of scanners integrated (target: 2+)
- Scan frequency (hourly recommended)
- Scan success rate (target: ≥95%)

**6. Platform Reliability**
- Uptime percentage (target: ≥99%)
- Error rate (target: <1%)
- Performance (scan processing time)

**7. Feature Requests**
- Number of requests captured
- Categorized by priority (high/medium/low)
- Feasibility assessment

---

## 💰 PRICING & COMMERCIAL TERMS

### Beta Pilot Pricing

**Cost:** $0 (completely free for 90 days)

**What's Included:**
- Full platform access
- Unlimited scans
- Unlimited findings
- Compliance dashboard
- Email support (48-hour SLA)
- Weekly check-in calls
- Custom configuration
- Training sessions

**What's NOT Included:**
- 24/7 support (business hours only)
- On-site deployment (remote only)
- Custom development (unless strategically aligned)
- Liability/SLA guarantees (pilot program)

### Post-Pilot Pricing (If Converting)

**Beta Customer Discount:** 50% off first year

**Standard Pricing:**
```
Tier 1: Single Site
- 1 application/product
- Hourly scans
- Standard dashboard
- Email support
- Regular Price: $5,000/year
- Beta Price: $2,500/year (Year 1)

Tier 2: Multi-Site Small
- 2-5 applications/products
- Hourly scans
- Custom dashboards
- Priority email support
- Regular Price: $10,000/year
- Beta Price: $5,000/year (Year 1)

Tier 3: Enterprise
- Unlimited applications/products
- Custom scan frequency
- White-label dashboards
- Dedicated support
- Phone/video support
- Custom features
- Regular Price: $25,000/year
- Beta Price: $12,500/year (Year 1)
```

**Multi-Year Discounts:**
- 2-year commitment: Additional 10% off
- 3-year commitment: Additional 15% off

---

## 🎯 IDEAL BETA CUSTOMER PROFILE

### Target Industries

**Primary:**
1. **Oil & Gas** (exploration, production, refining, distribution)
2. **Manufacturing** (automotive, aerospace, chemicals, food)
3. **Utilities** (electric power, water, natural gas)
4. **Transportation** (rail, pipeline, port operations)

**Secondary:**
5. **Pharmaceuticals** (production facilities)
6. **Mining** (extraction, processing)
7. **Data Centers** (critical infrastructure)

### Company Characteristics

**Size:**
- Employees: 100-10,000
- IT/OT Staff: 5-50
- Annual Revenue: $10M-1B

**Technical Environment:**
- Industrial control systems (ICS/SCADA)
- OT networks (Modbus, DNP3, ENIP, S7Comm protocols)
- Containerized applications (preferred but not required)
- Compliance requirements (IEC 62443, NIST, ISO 27001)

**Compliance Maturity:**
- Currently pursuing IEC 62443 compliance
- Manual compliance processes (overwhelming)
- Struggling with asset inventory
- Difficulty tracking vulnerabilities
- Need for automated reporting

**Decision Makers:**
- CISO, Director of Cybersecurity, OT Security Manager
- Compliance Manager, Risk Manager
- IT/OT Director, Infrastructure Manager

---

## 📝 APPLICATION PROCESS

### How to Apply

**Step 1: Submit Interest Form**

Email w.aroca@insaing.com with:
```
Subject: IEC 62443 Beta Program - [Company Name]

Company Information:
- Company Name:
- Industry:
- Location:
- Company Size (employees):
- Annual Revenue (optional):

Technical Environment:
- Number of industrial control systems:
- OT protocols in use:
- Current compliance status:
- Existing scanning tools:

Beta Readiness:
- Can deploy in next 30 days? (Yes/No)
- Preferred deployment (on-prem/cloud):
- IT/OT staff available for pilot:
- Expected time commitment (hours/week):

Success Criteria:
- What defines success for you?
- Key compliance challenges:
- Expected outcomes:

Contact Information:
- Primary Contact Name:
- Title:
- Email:
- Phone:
- Backup Contact (Name, Email):
```

**Step 2: Qualification Call** (30 minutes)
- INSA reviews application
- Schedule exploratory call
- Assess fit and readiness
- Answer questions

**Step 3: Selection**
- Decision within 5 business days
- Accept 3-5 customers (max)
- Prioritize based on:
  - Industry diversity
  - Deployment readiness
  - Feedback capacity
  - Strategic value

**Step 4: Agreement**
- Beta program terms (simple 2-page agreement)
- No cost, no commitment beyond 90-day participation
- Data sharing terms (anonymized metrics only)
- Intellectual property (customer retains all data)

**Step 5: Onboarding**
- Kickoff scheduled within 2 weeks
- Platform deployment begins
- Pilot officially starts

---

## 🤝 EXPECTATIONS & COMMITMENTS

### What INSA Commits To

**1. Platform Delivery**
- Fully functional platform deployed in 1-2 weeks
- Hourly automated scanning operational
- Compliance dashboard accessible
- Initial training completed

**2. Support**
- Email support (48-hour response, business hours)
- Weekly 30-minute check-in calls
- Issue resolution (best effort)
- Feature requests consideration

**3. Documentation**
- Platform user guide
- MCP tools reference
- Compliance reporting guide
- Troubleshooting FAQ

**4. Professional Conduct**
- Respectful of customer time
- Transparent about capabilities/limitations
- Responsive to feedback
- Secure handling of customer data

### What We Ask From Beta Customers

**1. Time Commitment**
- 2-4 hours for initial deployment/training
- 30 minutes weekly for check-in calls
- 1-2 hours weekly for platform use/testing
- 1 hour for final review meeting

**Total: ~20-30 hours over 90 days**

**2. Feedback**
- Weekly survey completion (5 minutes)
- Bug reports when issues occur
- Feature requests when needs arise
- Honest assessment of value

**3. Data Sharing** (Anonymized)
- Compliance metrics (aggregate numbers only)
- Scanner integration data
- Performance statistics
- No customer-identifying information required

**4. Testimonial** (If Successful)
- Written quote (50-100 words)
- Logo usage permission
- Reference customer listing
- Optional case study participation

---

## 📞 CONTACT INFORMATION

**Program Manager:** Wil Aroca (Founder, Lead Developer)
**Email:** w.aroca@insaing.com
**Company:** INSA Automation Corp
**Website:** [To be created]
**Demo:** Available upon request

**Apply Now:** Email w.aroca@insaing.com with subject "IEC 62443 Beta Program"

**Questions?** We're happy to discuss:
- Platform capabilities
- Deployment requirements
- Integration options
- Pricing (post-pilot)
- Timeline and process

---

## 🎁 BETA PROGRAM BONUSES

### For All Beta Customers

1. **50% Discount on Year 1** (if converting to paid)
2. **Priority Feature Development** (your requests prioritized)
3. **Free Year 2 Upgrade** (major version updates included)
4. **Beta Customer Advisory Board** (ongoing input on roadmap)
5. **Co-Marketing Opportunities** (joint webinars, conference presentations)

### For First 3 Customers

6. **60% Discount on Year 1** (additional 10% off)
7. **Lifetime Priority Support** (permanent priority queue)
8. **Free Training Credits** ($2,500 value - for additional users)
9. **Custom Integration** (1 integration of your choice)
10. **Founder Access** (direct line to Wil Aroca)

---

## 📅 TIMELINE

**Q4 2025:**
- November 2025: Beta program materials finalized ✅
- November 2025: Applications accepted (rolling basis)
- December 2025: First 2-3 customers onboarded

**Q1 2026:**
- January 2026: Additional customers onboarded (up to 5 total)
- January-March 2026: Pilots in full production use
- March 2026: First pilots complete (90 days)

**Q2 2026:**
- April 2026: Platform refinements based on feedback
- May 2026: General availability launch
- June 2026: ISA conference presentation (if pilot successful)

---

## ❓ FAQ

**Q: Is this really free?**
A: Yes, 100% free for 90 days. No credit card, no commitment.

**Q: What happens after 90 days?**
A: You decide - convert to paid (50% discount), extend pilot, or end relationship. Platform can remain deployed even if you don't convert.

**Q: Can we deploy on-premises?**
A: Yes, recommended. Self-hosted on your infrastructure. We provide remote deployment assistance.

**Q: What if we find bugs?**
A: Report them! We'll fix issues on a best-effort basis during pilot. This is a beta program - some bugs are expected.

**Q: Can we customize the platform?**
A: Yes, within reason. We'll work with you on configurations, dashboards, and reports. Custom development depends on strategic alignment.

**Q: What data do you collect?**
A: Only anonymized compliance metrics (e.g., "40% of findings are FR-1 related"). No customer-identifying information, no vulnerability details, no source code.

**Q: How long does deployment take?**
A: 1-2 weeks typically. Faster if you have Docker experience. We provide remote assistance.

**Q: Can we add more sites during the pilot?**
A: Yes, if capacity allows. Start with 1 site, expand if successful.

**Q: What if we're not satisfied?**
A: End the pilot anytime, no questions asked. We appreciate honest feedback either way.

**Q: Can we get a demo first?**
A: Yes! Schedule a 30-minute demo call. We'll show the platform and answer questions.

---

**READY TO JOIN?**

Email: w.aroca@insaing.com
Subject: IEC 62443 Beta Program - [Your Company]

**Limited to 5 customers. First come, first served.**

---

**Made by INSA Automation Corp**
**Date:** October 19, 2025
**Program Status:** READY TO LAUNCH
**Target Start:** Q4 2025 / Q1 2026

**The world's first automated IEC 62443 FR/SR tagging platform.**
**Be among the first to experience the future of industrial cybersecurity compliance.**
