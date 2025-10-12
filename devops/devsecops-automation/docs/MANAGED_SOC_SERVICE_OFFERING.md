# Managed SOC Service Offering - Insa Automation Corp
**Version**: 1.0
**Date**: 2025-10-11
**Service Type**: Industrial Cybersecurity Managed Services

---

## Executive Summary

Insa Automation Corp provides **comprehensive 24/7 Security Operations Center (SOC) services** specifically designed for **industrial, manufacturing, and critical infrastructure** organizations.

**Our Promise:**
- We install, configure, and manage your security monitoring infrastructure
- We monitor your systems 24/7/365 with expert industrial cybersecurity analysts
- We detect, triage, and coordinate response to security incidents
- We provide quarterly on-site visits for system health and relationship building
- We deliver comprehensive reporting to executive leadership

**You Focus On:** Running your operations safely and efficiently

**We Handle:** Protecting your IT and OT/ICS infrastructure from cyber threats

---

## Service Philosophy: "We Do The Work, You Stay Informed"

### What Makes Our Managed SOC Different?

**Traditional SOC Services:**
- Alert you when something happens
- You figure out what to do
- You execute remediation
- Limited understanding of OT/ICS environments

**Insa Automation Corp Managed SOC:**
- ✅ We detect threats in real-time (IT + OT/ICS)
- ✅ We triage and investigate (99% false positive filtering)
- ✅ We provide actionable remediation plans
- ✅ We coordinate with your team for execution
- ✅ We understand industrial protocols (Modbus, DNP3, ENIP, S7Comm)
- ✅ We know your environment cannot tolerate downtime

---

## What We Do vs. What You Do

### Our Responsibilities (The Heavy Lifting)

#### Phase 1: Installation & Onboarding (Days 1-30)

**Week 1-2: On-Site Installation**
- ✅ Deploy Wazuh agents on all monitored assets
  - Windows servers, Linux servers, workstations
  - ICS/SCADA systems, PLCs, HMIs (where supported)
  - Cloud infrastructure (AWS, Azure, GCP)
- ✅ Install network sensors (Suricata IDS/IPS)
  - Production network monitoring
  - OT/ICS network monitoring (with passive taps)
  - DMZ and external perimeter
- ✅ Configure firewalls and network rules
  - Review existing firewall rules
  - Implement security hardening recommendations
  - Configure secure log forwarding (outbound only)
- ✅ Establish secure communication channels
  - VPN for on-site visits
  - Encrypted log forwarding
  - Secure API access for monitoring

**Week 2-3: Baseline Security Assessment**
- ✅ Vulnerability scanning (initial baseline)
  - Network vulnerability scan (Nmap + OpenVAS)
  - Web application scanning (OWASP ZAP)
  - Configuration audit (Lynis, CIS benchmarks)
- ✅ Security posture evaluation
  - Identify critical vulnerabilities
  - Risk prioritization (CVSS + EPSS + business impact)
  - Remediation roadmap with timelines
- ✅ Compliance gap analysis (if applicable)
  - NERC CIP, IEC 62443, NIST CSF, etc.

**Week 3-4: Tuning & Training**
- ✅ Alert tuning (reduce false positives)
  - Baseline "normal" network behavior
  - Whitelist legitimate traffic patterns
  - Tune IDS rules for your environment
- ✅ Staff training (4-8 hours on-site)
  - "How to work with our SOC team"
  - Incident escalation procedures
  - How to read our reports
  - Best practices for your environment
- ✅ Establish communication protocols
  - Primary/secondary contacts
  - Escalation matrix (who to call for what)
  - Preferred communication channels (phone, email, Slack)

---

#### Phase 2: Ongoing Monitoring (24/7/365)

**Real-Time Security Monitoring:**
- ✅ Alert triage and investigation (365 days/year)
  - SOC analysts review every alert
  - 99% false positive filtering (you only see real threats)
  - Mean time to triage: <15 minutes
- ✅ Threat correlation and analysis
  - Cross-reference multiple data sources
  - Identify advanced persistent threats (APTs)
  - Detect lateral movement and privilege escalation
- ✅ Threat intelligence integration
  - MISP threat feeds (indicators of compromise)
  - Zero-day vulnerability tracking
  - Ransomware campaign monitoring
- ✅ Security event logging
  - Centralized log collection and storage
  - 90-day hot storage, 7-year cold storage (compliance)
  - Tamper-proof audit trails

**Proactive Security Activities:**
- ✅ Weekly threat hunting (Enterprise/Critical tiers)
  - Hypothesis-driven investigation
  - Search for signs of compromise
  - Identify dormant threats
- ✅ Vulnerability management
  - Continuous vulnerability scanning
  - Patch prioritization (EPSS-based)
  - Monthly patch reports with recommendations
- ✅ Security posture monitoring
  - Configuration drift detection
  - Unauthorized changes to critical systems
  - User privilege monitoring

---

#### Phase 3: Incident Response (When Things Go Wrong)

**Incident Detection & Notification:**
- ✅ Immediate notification (P0/P1 incidents)
  - Phone call to primary contact (within SLA)
  - Email with incident summary
  - Slack/Teams notification (if configured)
- ✅ Incident severity classification
  - P0 (Critical): Active breach, ransomware, safety impact
  - P1 (High): Attempted intrusion, malware, data exfiltration
  - P2 (Medium): Policy violation, suspicious activity
  - P3 (Low): False positive, informational

**Incident Investigation:**
- ✅ Forensic data collection
  - Memory dumps, disk images (if needed)
  - Network packet captures
  - Log file analysis
- ✅ Root cause analysis
  - How did attackers get in?
  - What vulnerabilities were exploited?
  - What data was accessed/exfiltrated?
- ✅ Threat actor profiling
  - TTPs (Tactics, Techniques, Procedures)
  - Attribution (if possible)
  - Motivation assessment

**Incident Containment & Remediation:**
- ✅ Containment recommendations
  - Isolate affected systems
  - Block malicious IP addresses
  - Disable compromised accounts
- ✅ Remediation coordination
  - **We recommend, you approve, we execute**
  - Step-by-step remediation plan
  - Rollback plan in case of issues
- ✅ Post-incident validation
  - Verify threat is eradicated
  - Confirm systems are clean
  - Restore normal operations

**Incident Reporting:**
- ✅ Post-incident report (within 24 hours)
  - Timeline of events
  - Root cause analysis
  - Actions taken
  - Recommendations to prevent recurrence
- ✅ Lessons learned session
  - Review incident with your team
  - Identify process improvements
  - Update incident response playbooks

---

#### Phase 4: Reporting & Communication (Ongoing)

**Weekly Reporting (All Tiers):**
- ✅ Summary email every Monday morning
  - Key security metrics (alerts, incidents, scans)
  - Notable events from the past week
  - Actions taken by SOC team
  - Upcoming activities
- ✅ Critical alerts (as they happen)
  - Immediate notification for P0/P1
  - Daily summary for P2/P3

**Monthly Reporting (All Tiers):**
- ✅ Comprehensive security report (15-20 pages)
  - Executive summary (1-page)
  - Detailed metrics and trends
  - Vulnerability summary (top 10 risks)
  - Incident summary (if any)
  - Recommendations for next month
- ✅ Patch management report
  - Critical patches released by vendors
  - Patch prioritization for your environment
  - Patch deployment recommendations

**Quarterly Reporting (All Tiers):**
- ✅ Quarterly business review (on-site or virtual)
  - Executive presentation (30-60 minutes)
  - C-level and board-ready content
  - Year-over-year trend analysis
  - ROI analysis (cost of incidents prevented)
  - Strategic recommendations
- ✅ Compliance status report (if applicable)
  - NERC CIP, IEC 62443, etc.
  - Compliance metrics and KPIs
  - Audit readiness assessment
  - Gap remediation progress

**Annual Reporting (Enterprise/Critical tiers):**
- ✅ Annual risk assessment (comprehensive)
  - Organization-wide risk profile
  - Cyber maturity assessment (CMM)
  - Multi-year security roadmap
  - Budget recommendations for next year

---

#### Phase 5: Continuous Improvement (Ongoing)

**Regular On-Site Visits:**
- ✅ Professional Tier: Quarterly (1 day/quarter)
- ✅ Enterprise Tier: Monthly (1 day/month per site)
- ✅ Critical Infrastructure Tier: Weekly (1 day/week)

**On-Site Visit Activities:**
- ✅ System health checks
  - Verify agents are functioning
  - Review sensor performance
  - Update software/signatures
- ✅ Relationship building
  - Face-to-face meetings with your team
  - Answer questions and provide guidance
  - Build trust and understanding
- ✅ Security posture review
  - Walkthrough of facility (if needed)
  - Review physical security controls
  - Identify new assets to monitor
- ✅ Training and knowledge transfer
  - Mini-training sessions (1-2 hours)
  - Best practice sharing
  - Emerging threat briefings

**Continuous Tuning:**
- ✅ Alert rule optimization
  - Reduce false positives over time
  - Add detections for new threats
  - Tune for your specific environment
- ✅ Process improvements
  - Refine incident response procedures
  - Update escalation matrix
  - Improve communication workflows

---

### Your Responsibilities (What We Need From You)

#### During Installation (Days 1-30)

**Week 1-2: Provide Access**
- ❗ Provide network access during installation
  - Temporary credentials for agent deployment
  - Firewall rule approval for log forwarding (outbound)
  - VPN access for remote management (optional)
- ❗ Identify key contacts
  - Primary/secondary technical contacts
  - Escalation contacts (manager, executive)
  - 24/7 emergency contact (for critical incidents)
- ❗ Provide asset inventory
  - List of servers, workstations, ICS devices
  - Network diagrams (if available)
  - Critical system identification

**Week 2-3: Baseline Assessment Coordination**
- ❗ Schedule maintenance windows
  - For initial vulnerability scanning
  - To minimize impact on production
- ❗ Review and approve remediation roadmap
  - Prioritize which vulnerabilities to fix first
  - Set timelines for remediation

**Week 3-4: Training & Tuning**
- ❗ Attend training sessions (4-8 hours)
  - Bring key staff members
  - Ask questions and engage
- ❗ Provide feedback on alert tuning
  - Confirm which alerts are false positives
  - Help us understand "normal" for your environment

---

#### During Ongoing Operations (Daily/Weekly/Monthly)

**Incident Response:**
- ❗ Be available for critical incident calls
  - Answer phone within SLA (P0: 30 min, P1: 1 hour)
  - Respond to email notifications
- ❗ Approve remediation actions
  - **We recommend, you approve, we execute**
  - Confirm downtime windows for remediation
  - Authorize account lockouts, firewall changes
- ❗ Provide incident context
  - Was this expected activity? (e.g., maintenance)
  - Are any systems behaving unusually?
  - Are there business factors we should know?

**Patch Management:**
- ❗ Review monthly patch reports
  - Prioritize patches for your environment
  - Schedule patch deployment windows
- ❗ Test patches in non-production (if required)
  - We recommend, you test, you approve deployment

**Communication:**
- ❗ Read weekly summary emails (5 minutes)
- ❗ Review monthly reports (30 minutes)
- ❗ Attend quarterly business reviews (60 minutes)

**On-Site Visit Coordination:**
- ❗ Schedule on-site visits
  - Coordinate calendar with your team
  - Arrange facility access for INSA staff
- ❗ Provide escort for facility access (if required)
- ❗ Gather any questions/concerns beforehand

**Continuous Improvement:**
- ❗ Provide feedback on our services
  - What's working well?
  - What can we improve?
- ❗ Notify us of environment changes
  - New servers, new applications
  - Network changes, IP address changes
  - Staff turnover (update contact list)

---

## Service Deliverables

### Installation & Onboarding Deliverables

**Documents Provided:**
- ✅ System architecture diagram (as-built)
- ✅ Agent deployment checklist (completed)
- ✅ Baseline security assessment report (20-30 pages)
- ✅ Remediation roadmap (prioritized action plan)
- ✅ SOC contact guide (who to call for what)
- ✅ Incident response procedures (tailored for your org)
- ✅ Training materials and recordings

**Technical Deliverables:**
- ✅ Wazuh agents deployed on all monitored assets
- ✅ Network sensors installed and configured
- ✅ Firewall rules reviewed and hardened
- ✅ Alert rules tuned for your environment
- ✅ Secure communication channels established
- ✅ Monitoring dashboard credentials

---

### Monthly Service Deliverables

**Reports:**
- ✅ Monthly security report (15-20 pages)
  - Executive summary (1 page)
  - Alert metrics (total alerts, by severity, by type)
  - Incident summary (if any)
  - Vulnerability summary (top 10 risks)
  - Threat intelligence summary (relevant to your industry)
  - Recommendations for next month
- ✅ Patch management report
  - Critical patches released by vendors
  - Patch prioritization matrix
  - Recommended patch schedule

**Activities:**
- ✅ Continuous 24/7 monitoring (or 8x5 for Professional tier)
- ✅ Alert triage and investigation (all alerts)
- ✅ Incident response (as needed)
- ✅ Vulnerability scanning (weekly or continuous)
- ✅ Threat hunting (Enterprise/Critical tiers only)
- ✅ Log retention and management

---

### Quarterly Service Deliverables

**Reports:**
- ✅ Quarterly business review (QBR) presentation
  - Executive presentation (PowerPoint + in-person)
  - C-level and board-ready content
  - Trend analysis (quarter-over-quarter)
  - Strategic recommendations
  - ROI analysis
- ✅ Compliance status report (if applicable)
  - NERC CIP, IEC 62443, etc.
  - Compliance metrics and KPIs
  - Audit readiness assessment
  - Gap remediation progress

**Activities:**
- ✅ On-site visit (Professional tier)
  - System health check (1 day)
  - Face-to-face meeting with your team
  - Mini-training session
- ✅ Security posture review
  - Review of security improvements
  - Validation of remediation progress
  - Identification of new risks

---

### Annual Service Deliverables (Enterprise/Critical Tiers)

**Reports:**
- ✅ Annual risk assessment (comprehensive)
  - Organization-wide risk profile
  - Cyber maturity assessment (CMM Level 1-5)
  - Multi-year security roadmap (3-5 years)
  - Budget recommendations for next year
- ✅ Compliance audit support
  - Audit readiness assessment
  - Evidence collection and organization
  - On-site support during audits (if needed)

**Activities:**
- ✅ Red team exercise (Critical tier only)
  - Simulated attack on your environment
  - Test SOC detection capabilities
  - Test incident response procedures
  - Post-exercise report with recommendations
- ✅ Tabletop exercise (Critical tier only)
  - Simulated incident scenario
  - Test communication and decision-making
  - Identify process gaps
  - Update incident response playbooks

---

## Service Level Agreements (SLAs)

### Monitoring Uptime SLA

**Guaranteed Uptime:**
- Professional Tier: 99.5% uptime (8x5 coverage)
- Enterprise Tier: 99.9% uptime (24x7 coverage)
- Critical Infrastructure Tier: 99.95% uptime (24x7 coverage)

**Uptime Calculation:**
- Measured monthly
- Excludes scheduled maintenance (announced 48h in advance)
- Excludes customer-caused outages (network issues, etc.)

**Uptime Penalty:**
- For every 0.1% below target: **10% monthly fee credit**
- Example: 99.8% uptime (0.1% below 99.9%) = 10% credit
- Maximum penalty: 50% monthly fee

**Scheduled Maintenance:**
- Professional Tier: Up to 8 hours/month (announced 48h advance)
- Enterprise/Critical Tier: Up to 2 hours/month (announced 7 days advance)
- Emergency maintenance: Announced 24h in advance (if possible)

---

### Incident Response Time SLA

**Response Time Commitments:**

| Severity | Professional Tier | Enterprise Tier | Critical Infrastructure Tier |
|----------|-------------------|-----------------|------------------------------|
| **P0 - Critical** | N/A (best effort) | 1 hour | 30 minutes |
| **P1 - High** | 4 hours | 1 hour | 30 minutes |
| **P2 - Medium** | 24 hours | 8 hours | 4 hours |
| **P3 - Low** | 72 hours | 24 hours | 24 hours |

**Incident Severity Definitions:**

- **P0 - Critical**
  - Active breach in progress
  - Ransomware encryption
  - Safety system compromise
  - Critical infrastructure outage
  - Data exfiltration in progress

- **P1 - High**
  - Attempted intrusion (blocked)
  - Malware infection (contained)
  - Unauthorized access to sensitive systems
  - DDoS attack
  - Compliance violation (serious)

- **P2 - Medium**
  - Policy violation (non-critical)
  - Suspicious activity (under investigation)
  - Vulnerability exploitation attempt (failed)
  - Configuration drift
  - Failed patch deployment

- **P3 - Low**
  - Informational alerts
  - False positives
  - General security questions
  - Feature requests
  - Non-urgent recommendations

**Response Time Measurement:**
- Starts: When alert is generated in our SOC
- Ends: When primary contact is notified (phone call, email, Slack)
- Excludes: Time waiting for customer response

**Incident Response Penalty:**
- For each SLA miss: **5% monthly fee credit**
- Maximum penalty: 25% monthly fee

---

### Report Delivery SLA

**Report Delivery Schedule:**
- Weekly summary: Every Monday by 9 AM (customer timezone)
- Monthly report: By 5th business day of following month
- Quarterly report: Within 15 days of quarter end
- Annual report: Within 30 days of year end (Enterprise/Critical only)

**Report Delivery Penalty:**
- For each late report: **2% monthly fee credit**
- Maximum penalty: 10% monthly fee

---

### On-Site Visit SLA

**On-Site Visit Schedule:**
- Professional Tier: Quarterly (4 visits/year)
- Enterprise Tier: Monthly (12 visits/year per site)
- Critical Infrastructure Tier: Weekly (52 visits/year)

**Scheduling:**
- Visits scheduled 30 days in advance
- Can be rescheduled once (14 days notice)
- Emergency visits available (Critical tier only, 48h notice)

**On-Site Visit Penalty:**
- For each missed visit (INSA fault): **10% monthly fee credit**
- For each missed visit (customer fault): No penalty

---

## Incident Response Process

### Step 1: Detection (Real-Time)

**How We Detect Incidents:**
- Security alert from Wazuh agent (file change, malware, suspicious process)
- IDS/IPS alert from Suricata (network attack, malware C2)
- Threat intelligence match (IOC detected in your environment)
- Anomaly detection (unusual user behavior, data exfiltration)
- Vulnerability exploitation attempt
- Manual report from your team

**SOC Analyst Review:**
- Alert appears in SOC queue within seconds
- Analyst reviews alert details (source, destination, payload)
- Cross-reference with threat intelligence
- Check if this is a known false positive
- Classify severity (P0, P1, P2, P3)

**Mean Time to Detect (MTTD):**
- P0/P1: <5 minutes (real-time monitoring)
- P2: <15 minutes
- P3: <1 hour

---

### Step 2: Notification (Within SLA)

**Immediate Notification (P0/P1):**
1. **Phone call** to primary contact
   - SOC analyst calls directly
   - Leaves voicemail if no answer
   - Escalates to secondary contact
2. **Email** with incident summary
   - Severity, affected systems
   - Initial findings
   - Recommended immediate actions
3. **Slack/Teams** notification (if configured)
   - @channel mention for P0
   - Direct message for P1

**Standard Notification (P2/P3):**
1. **Email** with incident details
2. **Slack/Teams** notification (if configured)
3. **Phone call** if no response within 2 hours

**Escalation Process:**
- If primary contact doesn't respond within 30 minutes (P0) or 1 hour (P1)
- SOC supervisor calls secondary contact
- If no response, escalate to manager/executive contact
- For P0, we continue escalation until we reach someone

---

### Step 3: Investigation (1-4 Hours)

**Forensic Data Collection:**
- SOC analyst gathers evidence
  - Log files from affected systems
  - Network packet captures (if available)
  - Memory dumps (for malware analysis)
  - User activity logs
- Preserves chain of custody (for legal/compliance)

**Root Cause Analysis:**
- How did the incident occur?
  - Phishing email? Unpatched vulnerability? Misconfiguration?
- What systems are affected?
  - Scope of compromise
  - Lateral movement assessment
- What data was accessed/exfiltrated?
  - File access logs
  - Network traffic analysis
- Who is the threat actor?
  - Ransomware gang? State-sponsored? Insider?

**Timeline Reconstruction:**
- When did the incident start?
- What actions did the attacker take?
- Are they still active?

**Mean Time to Investigate (MTTI):**
- P0: 1-2 hours (initial findings)
- P1: 2-4 hours
- P2: 4-8 hours
- P3: 24-48 hours

---

### Step 4: Containment (Immediate)

**Containment Recommendations:**
- SOC analyst provides immediate containment plan
  - Isolate affected systems (disconnect from network)
  - Block malicious IP addresses (firewall rules)
  - Disable compromised user accounts
  - Quarantine malware samples
  - Preserve evidence (don't reboot systems)

**Customer Approval:**
- **We recommend, you approve**
- SOC analyst explains each action
- Customer approves (verbal or email)
- If customer unavailable (P0), we execute emergency containment per pre-approved procedures

**Containment Execution:**
- INSA SOC executes approved actions
  - Firewall rule changes
  - Account lockouts
  - Network isolation
- Validates containment was successful
- Monitors for continued attacker activity

**Mean Time to Contain (MTTC):**
- P0: <30 minutes (after approval)
- P1: <1 hour
- P2: <4 hours
- P3: <24 hours

---

### Step 5: Remediation (Hours to Days)

**Remediation Plan:**
- SOC supervisor creates detailed remediation plan
  - Eradicate malware
  - Patch exploited vulnerabilities
  - Reset compromised credentials
  - Restore affected systems
  - Validate systems are clean
- Includes rollback plan (in case of issues)

**Customer Coordination:**
- Schedule remediation window
  - May require system downtime
  - Coordinate with your operations team
- Review remediation steps
- Obtain approval

**Remediation Execution:**
- INSA SOC executes remediation plan
  - Customer can observe (screen share)
  - We document every action
- Validates remediation was successful
  - Re-scan systems for malware
  - Verify attacker access is removed
  - Confirm systems are functioning normally

**Post-Remediation Monitoring:**
- Increased monitoring for 7-30 days
- Watch for signs of persistence or re-infection
- Validate no lateral movement occurred

**Mean Time to Remediate (MTTR):**
- P0: 4-24 hours (varies by incident complexity)
- P1: 24-72 hours
- P2: 3-7 days
- P3: 7-30 days

---

### Step 6: Post-Incident Report (24 Hours)

**Report Contents:**
- Executive summary (1 page)
  - What happened?
  - What was the impact?
  - What did we do?
- Detailed timeline of events
- Root cause analysis
- Actions taken (containment, remediation)
- Recommendations to prevent recurrence
  - Patch this vulnerability
  - Improve user training
  - Implement MFA
- Lessons learned

**Post-Incident Review Meeting:**
- Scheduled within 1 week
- Review incident with your team
- Discuss lessons learned
- Update incident response playbooks
- Answer questions

---

## Escalation Procedures

### Standard Escalation Path

```
Level 1: SOC Analyst
  ↓ (if unable to resolve or P0/P1)
Level 2: SOC Supervisor
  ↓ (if unable to resolve or prolonged P0)
Level 3: SOC Manager
  ↓ (if customer requests or major incident)
Level 4: INSA Executive (VP of Operations)
```

**Escalation Triggers:**
- P0 incident lasting >2 hours
- P1 incident lasting >8 hours
- Customer requests escalation
- SOC analyst unable to resolve issue
- Customer dissatisfaction

**Customer Escalation Path:**

```
You → Primary SOC Contact (Analyst)
  ↓ (if unsatisfied)
You → SOC Supervisor
  ↓ (if unsatisfied)
You → Your Account Manager
  ↓ (if unsatisfied)
You → INSA Executive (VP of Operations)
```

**24/7 Emergency Contact:**
- Professional Tier: SOC hotline (8x5 coverage only)
- Enterprise Tier: SOC hotline (24x7 coverage)
- Critical Infrastructure Tier: Direct cell phone to SOC supervisor (24x7)

---

## Communication Channels

### Primary Communication Methods

**For Routine Matters:**
- Email: your-account@insa-soc.com
- Response time: 24-72 hours (depends on tier)

**For Urgent Matters (Non-Incident):**
- SOC hotline: +1-XXX-XXX-XXXX (24/7 for Enterprise/Critical tiers)
- Response time: 1-4 hours

**For Incidents (P0/P1):**
- SOC hotline: +1-XXX-XXX-XXXX
- We call you immediately upon detection
- Response time: Per SLA (30 min - 4 hours)

**For Collaboration:**
- Slack/Teams channel: #insa-soc-your-company (optional)
- Real-time chat with SOC team
- File sharing for logs, screenshots

**For Scheduled Meetings:**
- Video conferencing: Zoom, Teams, or Google Meet
- Quarterly business reviews
- Post-incident review meetings
- On-site visits

---

## Compliance Support

### What We Provide

**NERC CIP Compliance:**
- ✅ CIP-007-6 (Security monitoring) evidence collection
- ✅ CIP-005-7 (Access control) monitoring and reporting
- ✅ CIP-010-4 (Configuration management) change detection
- ✅ Audit readiness assessments (quarterly)
- ✅ On-site support during audits (Enterprise/Critical tiers)
- ✅ Compliance report generation (automated)

**IEC 62443 Compliance:**
- ✅ Security Level (SL) assessment assistance
- ✅ SR 3.3 (Security Audit) log collection and retention
- ✅ SR 2.1 (Authorization) access monitoring
- ✅ SR 7.2 (IDS/IPS) network monitoring
- ✅ Compliance gap analysis
- ✅ Remediation roadmap

**Other Compliance Frameworks:**
- NIST CSF 2.0 (Cybersecurity Framework)
- PCI-DSS (Payment Card Industry)
- HIPAA (Healthcare)
- ISO 27001 (Information Security)
- SOC 2 Type II (Service Organization Controls)

### What We Don't Provide

**Compliance Certification:**
- ❌ We do not certify your organization as compliant
- ❌ We do not conduct official audits
- ✅ We provide evidence and support for your auditors

**Compliance Liability:**
- ❌ We are not liable for your compliance failures
- ❌ Compliance is ultimately your responsibility
- ✅ We help you achieve and maintain compliance

---

## Service Exclusions (What's NOT Included)

### Out of Scope

**Not Included in Managed SOC:**
- ❌ Penetration testing (available as add-on)
- ❌ Red team exercises (available as add-on for Critical tier)
- ❌ Physical security assessments
- ❌ Social engineering testing
- ❌ Compliance certification audits
- ❌ Vendor risk assessments
- ❌ Policy/procedure writing (we provide templates)
- ❌ Remediation execution without approval (except emergency containment)
- ❌ Patch deployment (we recommend, you deploy)
- ❌ Backup/disaster recovery
- ❌ Antivirus management (you manage, we monitor)

**Customer Responsibilities:**
- ❌ Patch deployment and testing
- ❌ User security awareness training (we provide materials)
- ❌ Password management
- ❌ Backup management
- ❌ Disaster recovery planning and execution
- ❌ Physical security controls
- ❌ Vendor management

### Add-On Services Available

**Available for Additional Cost:**
- Red team exercises: $50,000/exercise
- Penetration testing: $15,000/test
- Social engineering testing: $10,000/test
- Compliance certification support (ISO 27001, SOC 2): $50,000-$75,000
- Custom policy/procedure development: $10,000-$25,000
- On-site training workshops: $2,500/day
- Emergency incident response hours (beyond contract): $500/hour

---

## Success Metrics & Reporting

### Key Performance Indicators (KPIs)

**Security Metrics:**
- Mean Time to Detect (MTTD): <5 minutes for P0/P1
- Mean Time to Respond (MTTR): Per SLA
- False Positive Rate: <5% (target <1%)
- Vulnerability Remediation Rate: >80% critical/high within 30 days
- Incident Count: Trend over time
- Security Posture Score: CMM Level 1-5

**Operational Metrics:**
- Monitoring Uptime: 99.5% - 99.95%
- Alert Volume: Trend over time
- SOC Analyst Utilization: 70-85% (not overloaded)
- Customer Satisfaction Score: >4.5/5.0

**Business Metrics:**
- Incidents Prevented: Estimated based on blocked attacks
- Cost Avoidance: Estimated cost of prevented breaches
- Compliance Status: % of controls met
- ROI: Cost of service vs. cost of incidents prevented

---

## Getting Started

### Onboarding Timeline

**Month 1: Installation & Baseline**
- Week 1-2: On-site installation
- Week 2-3: Baseline security assessment
- Week 3-4: Tuning and training
- Week 4: Go-live (full monitoring begins)

**Month 2-3: Optimization**
- Alert tuning and false positive reduction
- Incident response procedure testing
- Relationship building with your team

**Month 4+: Steady State**
- 24/7 monitoring (or 8x5 for Professional)
- Regular reporting and on-site visits
- Continuous improvement

---

## Frequently Asked Questions

**Q: Do we need to hire security staff?**
A: No, that's the point of Managed SOC. We are your security team.

**Q: What if we already have some security tools?**
A: We integrate with your existing tools (SIEM, firewalls, etc.). We complement, not replace.

**Q: Can you guarantee we won't get breached?**
A: No one can guarantee that. But we significantly reduce your risk and minimize damage if a breach occurs.

**Q: How quickly can you start?**
A: Initial assessment within 1 week. Full installation within 30-60 days (depending on complexity).

**Q: Can we cancel anytime?**
A: Annual contracts required (1-year minimum). 90-day notice for cancellation.

**Q: What if we outgrow your services?**
A: Great problem to have! We help you transition to your own SOC (knowledge transfer included).

**Q: What if you make a mistake?**
A: Professional liability insurance covers errors. We take full responsibility and make it right.

---

## Contact Information

**Sales Inquiries:**
- Email: sales@insa-automation.com
- Phone: +1-XXX-XXX-XXXX
- Website: https://www.insa-automation.com

**Existing Customer Support:**
- Email: support@insa-automation.com
- SOC Hotline: +1-XXX-XXX-XXXX (24/7 for Enterprise/Critical)
- Emergency Incidents: +1-XXX-XXX-XXXX (immediate response)

---

**Document Version:** 1.0
**Last Updated:** 2025-10-11
**Service Level:** Professional | Enterprise | Critical Infrastructure

---

*Made by Insa Automation Corp for OpSec*
