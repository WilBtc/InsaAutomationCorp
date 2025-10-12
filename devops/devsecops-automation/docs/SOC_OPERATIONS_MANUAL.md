# SOC Operations Manual (INTERNAL ONLY)
**Insa Automation Corp - Managed Industrial SOC 24/7**
**Document Classification**: CONFIDENTIAL - INTERNAL USE ONLY
**Version**: 1.0
**Date**: October 12, 2025
**Status**: Active

---

## Document Control

**Purpose**: This manual defines internal operations for Insa Automation Corp's Managed Industrial SOC 24/7 service.

**Audience**: SOC analysts, SOC managers, platform engineers

**Classification**: CONFIDENTIAL - DO NOT SHARE WITH CLIENTS

**Key Principle**: External messaging emphasizes "expert SOC analysts." Internally, we leverage AI automation to achieve 95%+ automation rate, enabling 1 analyst to monitor 50+ clients simultaneously.

---

## Table of Contents

1. [Service Overview](#service-overview)
2. [Technology Stack](#technology-stack)
3. [Staffing Model](#staffing-model)
4. [Daily Operations Workflow](#daily-operations-workflow)
5. [Shift Handoff Procedures](#shift-handoff-procedures)
6. [AI-Human Collaboration Model](#ai-human-collaboration-model)
7. [Incident Response Playbooks](#incident-response-playbooks)
8. [Client Communication Protocols](#client-communication-protocols)
9. [SLA Tracking and Compliance](#sla-tracking-and-compliance)
10. [Tools and Systems](#tools-and-systems)
11. [Metrics and KPIs](#metrics-and-kpis)
12. [Escalation Procedures](#escalation-procedures)
13. [Quality Assurance](#quality-assurance)

---

## Service Overview

### What We Promise Clients

**External Messaging** (from sales materials):
- "24/7 SOC monitoring by expert security analysts"
- "Human-verified threat triage and prioritization"
- "Experienced analysts review every critical finding"
- "Comprehensive incident response"
- "Quarterly on-site security reviews"

### Internal Reality

**Actual Service Delivery**:
- **AI Automation**: 95%+ of routine triage handled by AI triage engine
- **Human Analysts**: Focus on critical incidents, client communication, and complex investigations
- **Hybrid Model**: AI + human verification = superior outcomes at scale
- **Economics**: 1 analyst can effectively monitor 50+ clients
- **Margin**: 80%+ gross margin on managed services

### Service Tiers

| Tier | Monthly Price | Monitoring Scope | Response Time | Analyst Attention |
|------|---------------|------------------|---------------|-------------------|
| **Basic** | $2,000/mo | Up to 50 assets | 24 hours | AI-only, human review for Critical only |
| **Professional** | $5,000/mo | Up to 200 assets | 4 hours | AI + daily human review |
| **Enterprise** | $15,000/mo | Unlimited assets | 1 hour | AI + continuous human oversight + dedicated analyst |

**Note**: All tiers receive AI-powered triage. Human analyst involvement scales with tier.

---

## Technology Stack

### Platform Components

```yaml
Primary Platform: iac1 (100.100.101.1)
Role: Multi-Tenant SOC Platform
OS: Ubuntu 22.04 LTS

Core Systems:
  DefectDojo:
    Version: Latest
    Port: 8082
    Purpose: Vulnerability management, multi-tenant finding database
    URL: http://100.100.101.1:8082

  AI Triage Engine:
    Location: /home/wil/devops/devsecops-automation/defectdojo/agents/
    Components:
      - autonomous_agent.py (24/7 monitoring service)
      - triage_engine.py (AI decision logic)
      - claude_code_agent.py (local Claude Code integration)
      - learning_engine.py (SQLite-based ML)
      - feedback_collector.py (human override monitoring)

    AI Model: Claude Code (local subprocess, zero API costs)
    Learning DB: /var/lib/defectdojo/learning.db
    Logs: /var/log/defectdojo_agent.log

  GroupMQ (Message Queue):
    Port: 6379
    Purpose: Job distribution, real-time notifications
    Topics:
      - scans/queued/{client_id}
      - triage/pending/{client_id}
      - alerts/{client_id}/critical
      - alerts/{client_id}/high

  Scanner Pool:
    Workers: 3-5 Docker containers
    Scanners:
      - Trivy (container/dependency scanning)
      - OWASP ZAP (web app scanning)
      - Nmap (network discovery)
      - Nikto (web server scanning)
      - Custom scanners (client-specific)

  Monitoring:
    Prometheus: Metrics collection
    Grafana: Dashboards (http://100.81.103.99:3001)
    Wazuh: Host-based intrusion detection
    Suricata: Network intrusion detection

Internal Reference SOC: netg (100.121.213.50)
  Purpose: INSA's internal security monitoring
  Components: Same stack as iac1 (reference architecture)
```

### Data Flow Architecture

```
Client Assets (Wazuh Agents, Scanners)
  ↓
[Scanner Workers] → Import Results → DefectDojo
  ↓
[GroupMQ] → Publish to triage/pending/{client_id}
  ↓
[AI Triage Workers] → Analyze with Claude Code + EPSS
  ↓
Decision:
  - Low confidence (<70%): Flag for human review
  - High confidence (≥70%): Auto-triage + log decision
  ↓
Critical/High Severity? → [GroupMQ alerts/{client_id}/critical]
  ↓
  ├─→ Email alert to analyst
  ├─→ Slack notification
  ├─→ Jira ticket creation
  └─→ WebSocket to client portal (real-time)
  ↓
[Human Analyst] → Review, communicate, escalate
  ↓
[Learning Engine] → Collect feedback, update patterns
```

---

## Staffing Model

### Analyst Roles

**SOC Analyst (Tier 1)**
- **Count**: 2-3 per shift
- **Responsibility**: Monitor alerts, verify AI triage decisions, handle client inquiries
- **Workload**: Up to 50 clients per analyst
- **Focus**: Critical/High severity findings flagged by AI
- **Hours**: 8-hour shifts (rotating: night/day/evening)

**Senior SOC Analyst (Tier 2)**
- **Count**: 1 per shift
- **Responsibility**: Complex investigations, client escalations, AI tuning
- **Workload**: 20-30 clients (higher complexity)
- **Focus**: Enterprise clients, incident response, root cause analysis
- **Hours**: Day shift (8 AM - 5 PM)

**SOC Manager (Tier 3)**
- **Count**: 1
- **Responsibility**: Oversight, client relationships, SLA compliance, analyst training
- **Workload**: All clients (strategic level)
- **Focus**: Metrics, process improvement, major incidents
- **Hours**: Business hours + on-call

### Shift Schedule

```
24/7 Coverage:

Night Shift (10 PM - 6 AM):
  - 1x SOC Analyst
  - AI handles 90%+ of work
  - Analyst monitors critical alerts only
  - Minimal client communication (emergency only)

Day Shift (6 AM - 2 PM):
  - 2x SOC Analysts
  - 1x Senior SOC Analyst
  - Peak client communication hours
  - Quarterly on-site visits scheduled during this shift

Evening Shift (2 PM - 10 PM):
  - 2x SOC Analysts
  - Client communication (West Coast hours)
  - Scan scheduling and report generation

Weekends:
  - 1x SOC Analyst per shift
  - AI automation + on-call senior analyst
```

### Workload Distribution (AI vs Human)

| Task | AI Automation | Human Involvement | Volume |
|------|---------------|-------------------|--------|
| **Low/Info findings triage** | 100% | 0% (reviewed weekly in aggregate) | ~80% of findings |
| **Medium findings triage** | 95% | 5% spot checks | ~15% of findings |
| **High findings triage** | 80% | 20% verification | ~4% of findings |
| **Critical findings triage** | 50% | 50% immediate review | ~1% of findings |
| **False positive detection** | 90% | 10% confirmation | ~30% of findings |
| **Client communication** | 10% (auto-reports) | 90% | Daily/weekly |
| **Incident response** | 20% (data gathering) | 80% (decision-making) | 2-5/month |
| **Report generation** | 95% | 5% (review/customize) | Daily/weekly |
| **Scan scheduling** | 100% | 0% (client self-service or auto) | 50+/day |

**Key Insight**: AI enables 1 analyst to do the work of 20 traditional analysts.

---

## Daily Operations Workflow

### AI Autonomous Operations (Continuous)

**Every 5 Minutes** (automated, no human intervention):
```yaml
1. Query DefectDojo for new unverified findings
   - Filter: status = 'unverified', created_at > last_check

2. For each finding:
   a. Check learning database for similar past decisions
   b. Send finding details to Claude Code (subprocess):
      Prompt: "Analyze this security finding and provide:
               - Is it a false positive? (yes/no)
               - Risk level (Critical/High/Medium/Low)
               - Confidence (0-100%)
               - Reasoning (2-3 sentences)
               - Recommended action (escalate/ignore/monitor)"

   c. Claude Code returns decision in JSON format

   d. Adjust confidence based on learned patterns:
      - Pattern "Critical + CVE" success rate: 95% → multiply confidence by 1.2
      - Pattern "Test file FP" success rate: 60% → multiply confidence by 0.8

   e. Decision logic:
      IF confidence >= 70%:
        - Apply AI decision automatically
        - Log to DefectDojo with comment: "AI-triaged (confidence: 92%)"
        - Record in learning DB
      ELSE:
        - Flag for human review
        - Add to analyst queue
        - Send alert if Critical/High severity

3. Escalation (if Critical/High severity):
   - Create Jira ticket
   - Send Slack alert to #soc-critical channel
   - Email analyst on duty
   - Push to client portal (WebSocket)

4. Record decision in learning database:
   - Finding ID, client ID, AI decision, confidence, timestamp
   - Wait for human feedback (checked every 2 hours)
```

**Every 2 Hours** (automated):
```yaml
Feedback Collection:
  1. Query DefectDojo for findings triaged by AI in last 2 hours
  2. Check if human analyst modified AI decision:
     - Status changed?
     - Severity adjusted?
     - Closed as false positive after AI marked valid?
  3. If override detected:
     - Log as feedback in learning DB
     - Adjust pattern confidence:
       * If AI correct: increase confidence multiplier
       * If AI wrong: decrease confidence multiplier
     - Alert SOC manager if accuracy drops below 85%
```

**Daily at 8 AM** (automated):
```yaml
Daily Security Report Generation:
  1. Query DefectDojo for last 24 hours:
     - Total findings imported
     - Findings by severity (Critical/High/Medium/Low)
     - Findings by product (client)
     - AI triage statistics (auto-triaged %, confidence avg)
     - SLA status (breaches, at-risk findings)

  2. Generate report (Markdown/HTML):
     - Executive summary
     - Top 5 critical findings (with AI reasoning)
     - False positive rate
     - Client-specific summaries

  3. Distribute:
     - Email to SOC manager
     - Post to Slack #soc-daily-reports
     - Upload to client portals
```

**Weekly (Monday 9 AM)** (automated):
```yaml
AI Learning Performance Report:
  1. Calculate accuracy metrics:
     - AI decisions made: X
     - Human overrides: Y
     - Accuracy rate: (X-Y)/X * 100%

  2. Confidence calibration:
     - Plot predicted confidence vs actual accuracy
     - Identify overconfident or underconfident patterns

  3. Improvement recommendations:
     - Patterns to adjust
     - New patterns detected
     - Outlier findings for manual review

  4. Send to SOC manager + senior analysts for review
```

### Human Analyst Daily Workflow

**Start of Shift (15 minutes)**:
```yaml
1. Review handoff notes from previous shift:
   - Read Slack #soc-handoff channel
   - Check Jira for open critical tickets
   - Review flagged findings in DefectDojo

2. Check AI agent health:
   - Verify defectdojo-agent.service is running:
     sudo systemctl status defectdojo-agent.service
   - Check logs for errors:
     tail -f /var/log/defectdojo_agent.log
   - Verify GroupMQ queue depths:
     redis-cli -p 6379 LLEN scans/queued/*

3. Review overnight critical alerts:
   - Open Slack #soc-critical channel
   - Check email for critical finding notifications
   - Prioritize: Enterprise clients first, then Pro, then Basic

4. Check SLA dashboard:
   - Open Grafana: http://100.81.103.99:3001/d/sla-dashboard
   - Identify findings approaching SLA breach (< 4 hours remaining)
   - Create action plan for at-risk findings
```

**During Shift (6-7 hours)**:
```yaml
Primary Tasks (in priority order):

1. Critical Finding Review (30% of time):
   - AI flags all Critical findings for human verification
   - Review AI reasoning
   - Validate with:
     * EPSS score (exploit probability)
     * CVE details (NVD, vendor advisories)
     * Client context (production vs dev, internet-facing?)
     * False positive patterns
   - Decision:
     * Agree with AI → Add comment "Verified by [analyst]", close ticket
     * Disagree → Override, document reasoning, trigger learning feedback
   - Communicate to client if genuine threat (see Client Communication section)

2. High Severity Queue (20% of time):
   - Review AI-flagged High severity findings
   - Spot check 20% of auto-triaged High findings (random sampling)
   - Focus on:
     * New CVEs (published < 7 days ago)
     * Client-specific risks (e.g., OT environments)
     * Findings with low AI confidence (70-80%)

3. Client Communication (25% of time):
   - Respond to client inquiries (Slack, email, portal messages)
   - Send critical finding notifications (template-based)
   - Schedule quarterly on-site visits
   - Provide context and remediation guidance
   - Update Jira tickets with client responses

4. Incident Response (15% of time):
   - Active incidents: coordinate response, gather forensics, communicate
   - Post-incident: document timeline, root cause, lessons learned
   - Assist clients with remediation validation

5. AI Oversight (10% of time):
   - Review AI learning reports
   - Manually triage flagged findings (low confidence)
   - Provide feedback to improve AI accuracy:
     * Click "Override AI decision" in DefectDojo
     * Add comment explaining why AI was wrong
     * Learning engine automatically adjusts patterns

6. Reporting (5% of time):
   - Review auto-generated daily reports
   - Customize for Enterprise clients (add context, recommendations)
   - Generate ad-hoc reports for client requests
   - Weekly/monthly summary reports
```

**End of Shift (15 minutes)**:
```yaml
Handoff Preparation:
  1. Summarize shift activity:
     - Critical findings reviewed: X
     - Client communications: Y
     - Active incidents: Z (status, next steps)

  2. Post handoff note to Slack #soc-handoff:
     Template:
     ```
     Shift Handoff - [Date] [Shift]
     Analyst: [Your Name]

     🚨 Critical Items:
     - Client ABC: Critical SQLi finding in production app (Jira: SOC-1234)
       * Client notified at 2 PM, awaiting patch timeline
       * Follow up in 4 hours

     ⚠️ High Priority:
     - Client XYZ: 5 High findings from Trivy scan
       * AI triaged, verified 3 as valid, 2 as FP
       * No immediate action needed

     📊 Metrics:
     - Findings reviewed: 45
     - AI accuracy today: 94%
     - SLA breaches: 0

     📝 Notes:
     - AI agent running smoothly, no issues
     - GroupMQ scan queue depth normal (~20 jobs)
     ```

  3. Update Jira tickets:
     - Add comments with status updates
     - Reassign to next shift if handoff needed
     - Close resolved tickets

  4. Check AI learning feedback:
     - Review any AI overrides you made during shift
     - Ensure learning engine captured feedback
```

---

## Shift Handoff Procedures

### Handoff Checklist

**Outgoing Analyst**:
- [ ] Post handoff note to Slack #soc-handoff (template above)
- [ ] Update Jira tickets for open critical incidents
- [ ] Flag any at-risk SLA findings (< 2 hours remaining)
- [ ] Document any AI agent issues (service down, errors)
- [ ] Note any client escalations or pending communications
- [ ] Verify next shift analyst acknowledged handoff (Slack reaction: ✅)

**Incoming Analyst**:
- [ ] Read handoff note in Slack #soc-handoff
- [ ] Review open Jira tickets (filter: status = 'In Progress' AND assignee = 'SOC Team')
- [ ] Check AI agent health (systemctl status defectdojo-agent.service)
- [ ] Review overnight critical alerts (Slack #soc-critical)
- [ ] Acknowledge handoff (Slack reaction: ✅ on handoff note)
- [ ] Contact outgoing analyst if clarification needed (within 30 minutes)

### Critical Incident Handoff (Special Procedure)

If an active critical incident is in progress during handoff:

1. **Outgoing Analyst**:
   - Schedule 15-minute handoff call (phone or Zoom)
   - Prepare incident summary:
     * Client name
     * Finding details (CVE, affected systems)
     * Timeline (when detected, client notified)
     * Current status (investigating, remediating, monitoring)
     * Next steps (with deadlines)
     * Client contact (who you've been communicating with)
   - Transfer ownership of Jira ticket to incoming analyst
   - Stay available for 1 hour after handoff for questions

2. **Incoming Analyst**:
   - Join handoff call
   - Take detailed notes
   - Review DefectDojo finding and Jira ticket
   - Confirm understanding of situation
   - Take ownership of client communication
   - Update client within 30 minutes of taking over

3. **SOC Manager**:
   - Always CC'd on critical incident handoffs
   - Monitors progress on Slack #soc-critical
   - Escalates to senior leadership if incident severity increases

---

## AI-Human Collaboration Model

### When AI Escalates to Humans

**Automatic Escalation Triggers**:

1. **Low Confidence** (< 70%):
   - AI cannot confidently classify finding
   - Example: "New vulnerability type, insufficient historical data"
   - Action: Flag in DefectDojo with tag "human-review-needed"
   - Analyst queue: Reviewed within 4 hours (Professional/Enterprise) or 24 hours (Basic)

2. **Critical or High Severity**:
   - AI always flags Critical findings for human verification
   - High findings flagged 20% of the time (random sampling)
   - Action: Real-time alert (Slack + Email)
   - Response time: Immediate (< 15 minutes for Critical)

3. **Active Exploit Detected**:
   - EPSS score > 0.8 (80%+ probability of exploitation)
   - CVE with known exploit code (ExploitDB, Metasploit)
   - Action: Immediate escalation to senior analyst + SOC manager
   - Response time: < 5 minutes

4. **Client-Specific Context Needed**:
   - Finding in production environment
   - OT/ICS systems affected
   - Compliance-sensitive data (PCI, HIPAA, etc.)
   - Action: Flag for human review with client context note
   - Response time: Within SLA (varies by tier)

5. **Pattern Anomaly**:
   - Finding doesn't match known patterns
   - Example: "Critical severity but no CVE or exploit evidence"
   - Action: Flag for human investigation
   - Response time: 24 hours

### When Humans Override AI

**Analyst Override Process**:

1. **In DefectDojo**:
   - Navigate to finding
   - Click "Edit" button
   - Change status/severity as needed
   - Add comment: "Override AI decision. Reason: [explain]"
   - Click "Override AI" checkbox (triggers learning feedback)
   - Save

2. **Learning Engine Captures**:
   - Original AI decision (stored in finding notes)
   - Human override decision
   - Reason provided by analyst
   - Timestamp and analyst name
   - Client context

3. **Pattern Adjustment**:
   - Learning engine analyzes override
   - If pattern identified (e.g., "AI missed test file indicator"):
     * Reduce confidence for similar findings by 10%
     * Alert SOC manager if pattern seen > 5 times/week
   - If one-off mistake:
     * No pattern adjustment
     * Log for future model retraining

4. **Feedback Loop**:
   - Every 2 hours, feedback collector runs
   - Sends summary to Slack #soc-ai-learning:
     ```
     AI Learning Update - 2 PM

     Overrides in last 2 hours: 3
     1. Finding #456 (Client ABC): AI said valid, analyst marked FP
        Reason: "Test environment, not production"
        Pattern adjusted: "Test" keyword confidence -10%

     2. Finding #457 (Client XYZ): AI said FP, analyst marked valid
        Reason: "Actually affects production API"
        Pattern adjusted: "API" keyword confidence +5%

     Current AI accuracy: 94% (target: 90%+)
     ```

### Analyst Responsibilities in AI Collaboration

**DO**:
- ✅ Trust AI for routine Low/Medium findings (spot check 5-10%)
- ✅ Always verify Critical findings (AI is 85-90% accurate, not 100%)
- ✅ Override AI when you have client-specific context
- ✅ Document reasoning for every override (teaches AI)
- ✅ Escalate patterns of AI mistakes to SOC manager
- ✅ Provide constructive feedback (not just "AI is wrong")

**DON'T**:
- ❌ Blindly accept AI decisions without spot checks
- ❌ Override AI without documenting reason (breaks learning loop)
- ❌ Ignore low confidence findings (they need human review)
- ❌ Distrust AI entirely (it's 90%+ accurate on routine tasks)
- ❌ Skip learning reports (they show AI improvement over time)

### Workload Distribution Example

**Scenario**: 50 clients, 1000 findings imported today

**AI Handles** (95%):
- 800 Low/Info findings → 100% auto-triaged (0 analyst minutes)
- 150 Medium findings → 95% auto-triaged (analyst spot checks 8 findings = 30 minutes)
- 40 High findings → 80% auto-triaged (analyst reviews 8 flagged = 60 minutes)
- 10 Critical findings → 50% auto-triaged (analyst reviews all 10 = 90 minutes)

**Total Analyst Time**: 180 minutes (3 hours) for triage
**Remaining Time**: 5 hours for client communication, incident response, reporting

**Without AI**: 1000 findings × 3 min/finding = 3000 minutes (50 hours) → impossible for 1 analyst

**Conclusion**: AI enables 1 analyst to do the work of 16+ traditional analysts.

---

## Incident Response Playbooks

### Playbook 1: Critical Vulnerability in Production

**Trigger**: Critical severity finding, CVSS ≥ 9.0, production environment

**Response Timeline**:
- **T+0 min**: AI detects, escalates to analyst
- **T+15 min**: Analyst validates, contacts client
- **T+30 min**: Client acknowledges, begins investigation
- **T+2 hours**: Remediation plan in place
- **T+24 hours**: Patch applied or workaround implemented
- **T+48 hours**: Vulnerability validated as closed

**Steps**:

1. **Initial Assessment (15 minutes)**:
   ```yaml
   - Verify finding is genuine (not false positive)
   - Check EPSS score (exploit probability)
   - Search ExploitDB for active exploits
   - Review client asset inventory (affected systems)
   - Determine if internet-facing
   - Check if already compromised (SIEM logs, Wazuh alerts)
   ```

2. **Client Notification (Immediate)**:
   ```
   Template: CRITICAL_FINDING_NOTIFICATION.md

   Subject: [CRITICAL] Security Vulnerability Detected - Immediate Action Required

   Dear [Client Contact],

   Our SOC has identified a CRITICAL security vulnerability in your environment:

   Finding: [Title]
   Severity: Critical (CVSS 9.8)
   Affected Systems: [List]
   Exploit Probability: HIGH (EPSS 0.92)
   Known Exploits: YES - Active exploitation in the wild

   RECOMMENDED ACTIONS (Immediate):
   1. [Specific remediation steps]
   2. [Workarounds if patch not available]
   3. [Monitoring guidance]

   Our SOC is standing by to assist. Please respond within 30 minutes to confirm receipt.

   Jira Ticket: SOC-1234
   SOC Analyst: [Your Name]
   Contact: [Phone] | [Email]
   ```

3. **Escalation (if no client response in 30 minutes)**:
   - Call client emergency contact (phone)
   - CC SOC manager on email
   - Escalate to client account owner
   - Document all contact attempts in Jira

4. **Remediation Assistance**:
   - Provide step-by-step patch instructions
   - Review vendor advisories
   - Suggest temporary workarounds (WAF rules, firewall blocks)
   - Offer to join client bridge call for critical incidents

5. **Validation**:
   - Re-scan affected systems after patch
   - Confirm vulnerability no longer present
   - Check for signs of compromise (logs, forensics)
   - Update DefectDojo finding status: "Closed - Remediated"
   - Document timeline in Jira

6. **Post-Incident**:
   - Generate incident report (timeline, root cause, lessons learned)
   - Share with client
   - Update SOC runbook if process improvements identified
   - Add to quarterly review discussion

### Playbook 2: False Positive Pattern Detected

**Trigger**: AI marks finding as valid, but analyst determines it's a false positive (and similar findings exist)

**Steps**:

1. **Confirm False Positive**:
   - Verify finding is not exploitable
   - Check client environment (test vs production)
   - Review similar findings for client

2. **Document Pattern**:
   - What made it a false positive?
     * Test file (not production code)
     * Mitigated by network controls (not internet-facing)
     * Already patched (scanner out of date)
     * Known accepted risk (documented exception)

3. **Update Learning Engine**:
   - Override AI decision in DefectDojo
   - Add comment with pattern details:
     "FP Pattern: Test files in /test/ directory are not production code"
   - Learning engine reduces confidence for similar findings

4. **Bulk Triage Similar Findings**:
   - Use DefectDojo bulk operations:
     * Filter: severity = 'High' AND title LIKE '%test%'
     * Bulk action: Close as False Positive
     * Add bulk comment: "Test files, not production"

5. **Client Communication** (if client noticed):
   - Explain false positive
   - Reassure that system is secure
   - Note that AI will learn from this pattern

### Playbook 3: Active Compromise Suspected

**Trigger**: Wazuh alert + DefectDojo critical finding + unusual network traffic

**Response** (IMMEDIATE):

1. **Activate Incident Response Team**:
   - Alert SOC manager (call immediately)
   - Alert senior analyst
   - Alert client CISO/IT director
   - Open war room (Slack #incident-[client]-[date])

2. **Containment** (T+0 to T+15 min):
   - Advise client to isolate affected systems (network segmentation)
   - Do NOT shut down systems (preserve forensic evidence)
   - Enable enhanced logging (Wazuh, Suricata, firewall)
   - Capture memory dump if possible

3. **Investigation** (T+15 min to T+2 hours):
   - Forensic timeline:
     * When was vulnerability introduced?
     * When was it first exploited?
     * What actions did attacker take?
   - Collect evidence:
     * Wazuh FIM logs (file changes)
     * Suricata network captures
     * System logs (auth, syslog, application)
     * DefectDojo vulnerability history

4. **Eradication** (T+2 hours to T+12 hours):
   - Patch vulnerability
   - Remove attacker access (backdoors, accounts)
   - Reset credentials
   - Rebuild compromised systems if necessary

5. **Recovery** (T+12 hours to T+48 hours):
   - Restore from clean backups (if needed)
   - Validate systems are clean
   - Resume normal operations
   - Enhanced monitoring for 30 days

6. **Post-Incident Report** (T+1 week):
   - Executive summary
   - Timeline of events
   - Root cause analysis
   - Lessons learned
   - Recommendations to prevent recurrence
   - Deliver to client + INSA leadership

---

## Client Communication Protocols

### Communication Channels by Tier

| Tier | Email | Slack/Teams | Phone | On-Site | Portal |
|------|-------|-------------|-------|---------|--------|
| **Basic** | ✅ Daily reports | ❌ | ❌ | ❌ | ✅ Self-service |
| **Professional** | ✅ Daily + incident | ✅ Shared channel | ⚠️ Critical only | ⚠️ Annual | ✅ Self-service |
| **Enterprise** | ✅ Real-time | ✅ Dedicated channel | ✅ Anytime | ✅ Quarterly | ✅ Self-service |

### Email Templates

**1. Daily Security Summary** (Automated, AI-generated):
```
Subject: [Insa SOC] Daily Security Report - [Client Name] - [Date]

Good morning [Client Name],

Your daily security summary from Insa SOC:

SUMMARY:
- New findings: 12 (0 Critical, 2 High, 7 Medium, 3 Low)
- Closed findings: 8
- Active findings: 45 (0 Critical, 5 High, 30 Medium, 10 Low)
- SLA status: ✅ All within compliance

TOP FINDINGS:
1. [HIGH] SQL Injection vulnerability in login.php
   - CVSS: 7.5
   - Status: Under review by your team
   - Recommendation: Apply patch within 72 hours

2. [MEDIUM] Outdated OpenSSL version detected
   - CVSS: 5.3
   - Status: Auto-triaged, no immediate risk
   - Recommendation: Schedule update during next maintenance window

AI TRIAGE STATISTICS:
- Findings auto-triaged: 10/12 (83%)
- False positives identified: 2
- Average confidence: 91%

UPCOMING SCANS:
- Weekly vulnerability scan: [Date]
- Monthly compliance scan: [Date]

Questions? Contact your SOC analyst: [analyst@insaing.com]

Portal: https://portal.insa-automation.com

--
Insa Automation Corp SOC
24/7 Security Monitoring
```

**2. Critical Finding Alert** (Manual, analyst-sent):
```
Subject: [URGENT] Critical Security Vulnerability Detected - [Client Name]

[Use Playbook 1 template above]
```

**3. Weekly Executive Summary** (Automated, AI-generated with analyst review):
```
Subject: [Insa SOC] Weekly Security Executive Summary - [Client Name]

Dear [Executive Name],

Your weekly security posture summary:

WEEK HIGHLIGHTS:
✅ Zero critical vulnerabilities
✅ 95% of findings remediated within SLA
✅ 23 scans completed successfully
⚠️ 3 High severity findings require attention

SECURITY METRICS:
- Total findings: 156 (down 12% from last week)
- Mean time to remediate: 48 hours (target: 72 hours)
- False positive rate: 8% (excellent)
- Compliance status: 100% (PCI DSS, SOC 2)

TOP RISKS:
1. Web application vulnerabilities (5 High findings)
   Recommendation: Code review and WAF deployment

2. Unpatched systems (3 Medium findings)
   Recommendation: Automate patch management

AI INSIGHTS:
Our AI triage system processed 156 findings this week with 92% accuracy,
enabling our analysts to focus on genuine threats and strategic guidance.

NEXT STEPS:
- Quarterly security review scheduled for [Date]
- Penetration test planned for [Date]

Questions? Schedule a call: [calendly link]

--
[Analyst Name], Senior SOC Analyst
Insa Automation Corp
```

### Slack/Teams Communication

**Shared Channel Etiquette**:
- Use threads for detailed discussions
- Tag @client-name for urgent items
- Provide context in every message (don't assume client remembers previous conversation)
- Professional tone (no emojis unless client uses them first)
- Response time: < 1 hour during business hours

**Example Slack Message**:
```
:warning: Critical Finding Alert - Action Required

Client: ACME Corp
Finding: SQL Injection in customer portal
Severity: Critical (CVSS 9.8)
Affected: https://portal.acme.com/login

Our SOC detected a critical SQL injection vulnerability. We've opened
Jira ticket SOC-1234 with detailed remediation steps.

Please confirm you've received this alert within 30 minutes.

SOC Analyst: Alice Smith
```

### Phone Communication

**When to Call**:
- Critical finding + no email response in 30 minutes
- Active compromise suspected
- SLA breach imminent (< 2 hours remaining)
- Client escalation requested

**Phone Script**:
```
"Hello, this is [Your Name] from Insa Automation Corp's Security Operations Center.
I'm calling regarding a critical security finding we've detected in your environment.

Do you have a few minutes to discuss?

[If yes:]
We've identified [finding description] with a CVSS score of [score].
This vulnerability [explain impact] and we recommend [immediate action].

I've sent you a detailed email to [email address] with remediation steps.
Can you confirm you'll be able to address this within [SLA timeframe]?

[If no:]
I understand you're busy. This is urgent - when would be a good time for me to call back?
In the meantime, please check your email from soc@insaing.com marked URGENT.

Thank you."
```

### Quarterly On-Site Visits (Enterprise Tier)

**Agenda** (3 hours):
1. **Security Posture Review** (60 min):
   - Findings trend analysis (past quarter)
   - SLA compliance
   - Top risks identified
   - Remediation progress

2. **AI System Review** (30 min):
   - How AI triage works (high-level, no technical details)
   - AI accuracy metrics for your organization
   - Analyst verification process
   - Learning and improvement over time

3. **Strategic Recommendations** (45 min):
   - Architecture improvements
   - Security tooling upgrades
   - Compliance roadmap (SOC 2, ISO 27001, etc.)
   - Incident response preparedness

4. **Q&A and Planning** (45 min):
   - Client questions
   - Next quarter scan schedule
   - Special projects (pen tests, audits, etc.)
   - Feedback on SOC service

**Deliverable**: Quarterly Security Report (PDF, 20-30 pages)

---

## SLA Tracking and Compliance

### SLA Definitions by Tier

| Tier | Critical | High | Medium | Low |
|------|----------|------|--------|-----|
| **Basic** | 24 hours | 7 days | 30 days | Best effort |
| **Professional** | 4 hours | 48 hours | 14 days | 30 days |
| **Enterprise** | 1 hour | 24 hours | 7 days | 14 days |

**SLA Clock Starts**: When finding is first imported into DefectDojo

**SLA Clock Stops**: When finding status changes to:
- "Closed - Remediated"
- "Closed - False Positive"
- "Accepted Risk" (with client approval)

**SLA Paused**: When:
- Client explicitly requests delay (documented in Jira)
- Finding requires client action (patch, restart) and client is working on it
- Maintenance window required but not yet scheduled

### SLA Monitoring

**Automated** (every 5 minutes):
```yaml
AI Agent checks:
  1. Query DefectDojo: findings WHERE sla_deadline < NOW() + 4 hours
  2. Calculate time remaining
  3. If < 4 hours:
     - Send alert to analyst
     - Flag finding in DefectDojo with tag "SLA-AT-RISK"
  4. If SLA breached:
     - Send alert to SOC manager
     - Create Jira ticket
     - Log to SLA breach tracker
```

**Analyst Responsibilities**:
- Check SLA dashboard at start of shift
- Prioritize at-risk findings
- Escalate to senior analyst if breach unavoidable
- Document reason for breach (client delay, complexity, etc.)

### SLA Dashboard (Grafana)

**URL**: http://100.81.103.99:3001/d/sla-dashboard

**Metrics**:
- Findings by SLA status (on-track, at-risk, breached)
- Time remaining until SLA deadline (heatmap)
- SLA compliance rate (% of findings closed within SLA)
- Mean time to remediate (MTTR) by severity
- SLA breaches by client (identify problem clients)

**Alerts**:
- Slack alert when finding < 2 hours from SLA breach
- Email to SOC manager when SLA breach occurs
- Weekly SLA report to INSA leadership

### SLA Breach Procedure

**If SLA breach is unavoidable**:

1. **Notify SOC Manager** (immediately):
   - Explain situation
   - Provide reason (client unresponsive, complexity, etc.)
   - Request approval to extend SLA

2. **Notify Client**:
   ```
   Subject: SLA Extension Request - [Finding Title]

   Dear [Client],

   We are working on [finding description] which is approaching its SLA deadline.
   Due to [reason], we request a 24-hour SLA extension to ensure proper remediation.

   Current status: [status]
   Remaining work: [tasks]
   New estimated completion: [date/time]

   Please confirm this extension is acceptable.
   ```

3. **Document in Jira**:
   - Add comment with SLA extension request
   - Attach client approval (email screenshot)
   - Update SLA deadline field

4. **Post-Breach Review**:
   - Root cause analysis (why did breach occur?)
   - Process improvement (how to prevent future breaches?)
   - Share lessons learned with SOC team

---

## Tools and Systems

### Primary Tools

| Tool | Purpose | URL/Access | Credentials |
|------|---------|------------|-------------|
| **DefectDojo** | Vulnerability management | http://100.100.101.1:8082 | SSO / API token |
| **Jira** | Ticket tracking | https://insaing.atlassian.net | SSO |
| **Slack** | Team communication | https://insaing.slack.com | SSO |
| **Grafana** | Dashboards and metrics | http://100.81.103.99:3001 | admin / [password] |
| **Client Portal** | Client self-service | https://portal.insa-automation.com | Client-specific |
| **Wazuh** | HIDS monitoring | https://wazuh.insaing.com | SSO |
| **Suricata** | NIDS monitoring | (logs in SIEM) | N/A |

### AI Triage System

**Service**: defectdojo-agent.service

**Commands**:
```bash
# Check status
sudo systemctl status defectdojo-agent.service

# View logs (live)
sudo journalctl -u defectdojo-agent -f

# View logs (recent)
tail -f /var/log/defectdojo_agent.log

# Restart service (if needed)
sudo systemctl restart defectdojo-agent.service

# Check learning database
sqlite3 /var/lib/defectdojo/learning.db "SELECT * FROM decisions ORDER BY timestamp DESC LIMIT 10;"

# View AI accuracy
sqlite3 /var/lib/defectdojo/learning.db "SELECT AVG(confidence) FROM decisions WHERE result='correct';"
```

**Troubleshooting**:
- If service stops: Check logs for errors, restart service, alert SOC manager
- If AI accuracy drops below 85%: Review recent overrides, retrain patterns, escalate to platform engineer
- If Claude Code subprocess fails: Verify `/home/wil/.npm-global/bin/claude` is accessible, check timeouts

### Scanner Pool

**View active scanners**:
```bash
docker ps | grep scanner
```

**View scan queue depth**:
```bash
redis-cli -p 6379 LLEN scans/queued/*
```

**Manually trigger scan** (if needed):
```bash
cd /home/wil/devops/devsecops-automation/defectdojo/scanners
./semgrep_scanner.py /path/to/code [engagement_id]
```

### GroupMQ (Message Queue)

**Connection**: localhost:6379 (Redis-compatible)

**Monitor queues**:
```bash
redis-cli -p 6379
> KEYS *
> LLEN scans/queued/client_acme
> LRANGE scans/queued/client_acme 0 10
```

**Common topics**:
- `scans/queued/{client_id}` - Pending scans
- `triage/pending/{client_id}` - Findings awaiting AI triage
- `alerts/{client_id}/critical` - Critical finding alerts
- `alerts/{client_id}/high` - High finding alerts

---

## Metrics and KPIs

### SOC Performance Metrics

**Daily** (auto-generated by AI):
```yaml
Findings Metrics:
  - Total findings imported: 1,234
  - By severity: Critical (5), High (45), Medium (600), Low (584)
  - Auto-triaged by AI: 1,150 (93%)
  - Flagged for human review: 84 (7%)
  - False positives identified: 120 (10%)

Response Metrics:
  - Mean time to triage: 8 minutes (target: < 15 min)
  - Mean time to client notification (Critical): 12 minutes (target: < 30 min)
  - Mean time to remediate (Critical): 18 hours (target: < 24 hours)

SLA Metrics:
  - SLA compliance rate: 98% (target: 95%+)
  - SLA breaches: 2 (both client-caused delays)
  - At-risk findings: 5 (< 4 hours remaining)

AI Metrics:
  - AI accuracy: 94% (target: 90%+)
  - AI confidence average: 87%
  - Human overrides: 72 (6% of AI decisions)
  - Learning database size: 15,000 decisions
```

**Weekly** (reviewed by SOC manager):
```yaml
Client Metrics:
  - Active clients: 52
  - New clients onboarded: 2
  - Client escalations: 3 (all resolved)
  - Client satisfaction (CSAT): 4.7/5.0 (target: 4.5+)

Analyst Metrics:
  - Findings reviewed per analyst: 450/week
  - Client communications per analyst: 80/week
  - Incidents handled: 4 (2 Critical, 2 High)

Financial Metrics:
  - Revenue (MRR): $180,000/month
  - Analyst cost: $25,000/month (3 analysts)
  - Gross margin: 86%
```

**Monthly** (executive report):
```yaml
Strategic Metrics:
  - Client retention rate: 98%
  - Client churn: 1 (reason: acquired by larger company)
  - Net promoter score (NPS): 72 (excellent)
  - Upsells (Basic → Pro): 3
  - Cross-sells (added pen testing): 2

Operational Efficiency:
  - Findings per analyst per month: 18,000
  - AI automation rate: 95%
  - Cost per finding triaged: $0.12 (vs $3.50 industry avg)
  - ROI on AI investment: 2,900%
```

### Target KPIs

| Metric | Target | Current | Trend |
|--------|--------|---------|-------|
| **AI Accuracy** | ≥ 90% | 94% | ✅ Stable |
| **SLA Compliance** | ≥ 95% | 98% | ✅ Exceeding |
| **MTTR (Critical)** | < 24 hours | 18 hours | ✅ Ahead |
| **MTTR (High)** | < 72 hours | 52 hours | ✅ Ahead |
| **False Positive Rate** | < 15% | 10% | ✅ Excellent |
| **Client Satisfaction** | ≥ 4.5/5 | 4.7/5 | ✅ Exceeding |
| **Analyst Utilization** | 70-80% | 75% | ✅ Optimal |
| **Gross Margin** | ≥ 80% | 86% | ✅ Exceeding |

---

## Escalation Procedures

### Escalation Paths

**Level 1: SOC Analyst (You)**
- Routine findings
- Client communication
- AI oversight
- SLA monitoring

**Level 2: Senior SOC Analyst**
- Complex investigations
- Repeat SLA breaches
- AI accuracy degradation
- Client escalations

**Level 3: SOC Manager**
- Critical incidents (active compromise)
- SLA breach requiring executive approval
- Client dissatisfaction
- Analyst performance issues

**Level 4: VP of Security / CTO**
- Major security breach
- Legal/regulatory issues
- Client contract disputes
- Platform architecture decisions

### When to Escalate

**Immediate Escalation (call + Slack)**:
- Active compromise suspected
- Critical finding with exploit in the wild
- Client reports breach
- AI agent down for > 15 minutes
- GroupMQ message queue depth > 10,000

**Same-Shift Escalation (Slack)**:
- SLA breach unavoidable
- Client unresponsive for 2+ hours on Critical finding
- AI accuracy drops below 85%
- Multiple false positives for same client (pattern)

**Next-Day Escalation (Email + Jira)**:
- Client feature request
- Process improvement idea
- Non-urgent technical issue
- Training request

### Escalation Templates

**Slack Escalation (Critical)**:
```
@soc-manager URGENT ESCALATION

Client: ACME Corp
Issue: Active compromise suspected
Details:
- Wazuh alert: Unauthorized root access at 3:42 PM
- DefectDojo: Critical RCE vulnerability (CVE-2023-12345)
- Client notified: 3:45 PM (no response yet)

Actions taken:
- Advised client to isolate affected server
- Opened Jira: SOC-5678
- Collected initial forensics (Wazuh logs attached)

Requesting:
- Senior analyst assistance with forensics
- Authorization to engage external IR firm if needed

Analyst: Alice Smith
```

**Email Escalation (SLA Breach)**:
```
Subject: SLA Breach Notification - ACME Corp - SOC-5678

[SOC Manager],

I need to report an SLA breach for the following finding:

Client: ACME Corp
Finding: SQL Injection in customer portal (Finding #456)
Severity: Critical
SLA Deadline: Oct 11, 2025 5:00 PM
Actual Closure: Oct 11, 2025 6:30 PM (1.5 hours late)

Root Cause:
Client did not respond to initial notification for 3 hours despite multiple
contact attempts (email, Slack, phone). When client finally responded,
they required additional time to schedule maintenance window.

Client approved extension: Yes (email attached)

Lessons Learned:
- Need escalation to client executive for critical findings if primary contact unresponsive
- Update playbook to require executive contact info during onboarding

No further action required. Documenting for monthly SLA report.

Analyst: Alice Smith
```

---

## Quality Assurance

### Analyst Performance Review

**Monthly Peer Review**:
- Each analyst reviews 10 random findings triaged by peers
- Check for:
  * Correct severity assessment
  * Proper false positive identification
  * Clear documentation in DefectDojo
  * Appropriate client communication
- Score: 1-5 (1=poor, 5=excellent)
- Feedback shared in 1-on-1 with SOC manager

**Quarterly Metrics Review**:
- AI override rate (target: < 10%)
- Client satisfaction score (target: ≥ 4.5/5)
- SLA compliance (target: ≥ 95%)
- Mean time to triage (target: < 15 min)

**Annual Performance Goals**:
- Complete 2 security certifications (GIAC, OSCP, etc.)
- Contribute 5 AI learning improvements
- Mentor 1 junior analyst
- Zero critical SLA breaches (client-caused excluded)

### AI Quality Assurance

**Weekly AI Audit**:
- Senior analyst reviews 20 random AI decisions
- Verify accuracy (agree/disagree with AI)
- Identify systematic errors (pattern vs one-off)
- Update learning patterns if needed

**Monthly AI Accuracy Report**:
- Overall accuracy: X% (target: ≥ 90%)
- Accuracy by severity: Critical (85%), High (92%), Medium (95%), Low (98%)
- False positive rate: Y% (target: < 15%)
- False negative rate: Z% (target: < 5%)
- Confidence calibration plot (predicted vs actual)

**Quarterly AI Model Retrain**:
- Export learning database (15,000+ decisions)
- Retrain patterns with updated weights
- A/B test new model vs production model (on test data)
- Deploy if accuracy improvement ≥ 2%

### Client Satisfaction Tracking

**After Every Critical Incident**:
- Email 3-question survey:
  1. How satisfied were you with our response time? (1-5)
  2. How satisfied were you with our communication? (1-5)
  3. How satisfied were you with our remediation guidance? (1-5)
- Follow up on scores < 4

**Quarterly Client Survey**:
- 10-question comprehensive survey
- Topics: service quality, AI transparency, analyst expertise, value for money
- Net Promoter Score (NPS): "How likely are you to recommend Insa SOC?" (0-10)
- Open-ended feedback

**Annual Client Review**:
- In-person or Zoom meeting with client stakeholders
- Review metrics, incidents, improvements
- Discuss future needs
- Contract renewal discussion

---

## Appendix: AI System Architecture (Internal Reference)

### How It Works (Technical Overview)

```yaml
AI Triage Pipeline:

1. New Finding Import:
   Scanner → DefectDojo API → PostgreSQL
   Trigger: GroupMQ message to triage/pending/{client_id}

2. AI Worker Picks Up:
   Subscribe to GroupMQ triage/pending/*
   Fetch finding details from DefectDojo API

3. Historical Pattern Lookup:
   Query SQLite learning DB:
     SELECT * FROM patterns
     WHERE pattern_type IN (
       'title_keyword', 'cve_exists', 'epss_threshold', 'client_history'
     )
     AND client_id = 'client_acme'

   Result: Similar past decisions with confidence multipliers

4. Claude Code Analysis (Local Subprocess):
   Command: /home/wil/.npm-global/bin/claude
   Prompt: Analyze this finding: [JSON]
   Timeout: 120 seconds
   Output: JSON decision (valid/fp, confidence, reasoning)

5. Confidence Adjustment:
   Base confidence (from Claude): 0.85
   Pattern multipliers:
     - "Critical + CVE" pattern success rate 95% → ×1.1 = 0.935
     - "Web app" pattern success rate 88% → ×1.0 = 0.935
   Final confidence: 93.5%

6. Decision Logic:
   IF confidence >= 0.70:
     Apply AI decision automatically
     Log to DefectDojo: "AI-triaged (93.5% confidence)"
     Record in learning DB
   ELSE:
     Flag for human review
     Alert analyst

7. Escalation (if Critical/High):
   - Create Jira ticket via API
   - Send Slack webhook to #soc-critical
   - Email analyst on duty
   - WebSocket push to client portal

8. Learning Feedback Loop (every 2 hours):
   Query DefectDojo for AI-triaged findings
   Check for human overrides (status changed, severity modified)
   IF override detected:
     - Determine if AI was correct or wrong
     - Update pattern confidence in learning DB:
       * Correct: confidence × 1.05 (up to max 1.5)
       * Wrong: confidence × 0.95 (down to min 0.5)
     - Log feedback event

9. Weekly Learning Report:
   Calculate AI accuracy: (correct_decisions / total_decisions) × 100%
   Identify underperforming patterns (accuracy < 80%)
   Generate recommendations for retraining
   Email to SOC manager + senior analysts
```

### Learning Database Schema

```sql
-- /var/lib/defectdojo/learning.db

CREATE TABLE decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    finding_id INTEGER NOT NULL,
    client_id TEXT NOT NULL,
    defectdojo_finding_id INTEGER,
    ai_decision TEXT NOT NULL,  -- 'valid', 'false_positive', 'unsure'
    ai_confidence REAL NOT NULL,  -- 0.0 to 1.0
    ai_reasoning TEXT,
    final_confidence REAL,  -- After pattern adjustment
    patterns_applied TEXT,  -- JSON array of pattern IDs used
    human_override BOOLEAN DEFAULT 0,
    human_decision TEXT,  -- If overridden
    human_reasoning TEXT,
    outcome TEXT,  -- 'correct', 'incorrect', 'pending'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT NOT NULL,  -- 'title_keyword', 'cve_exists', 'severity', etc.
    pattern_value TEXT NOT NULL,  -- e.g., 'SQL Injection', 'has_cve=true'
    confidence_multiplier REAL DEFAULT 1.0,  -- 0.5 to 1.5
    success_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    accuracy_rate REAL,  -- success_count / (success_count + failure_count)
    client_id TEXT,  -- NULL for global patterns, client_id for client-specific
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date DATE NOT NULL,
    total_decisions INTEGER NOT NULL,
    ai_auto_triaged INTEGER NOT NULL,
    human_reviewed INTEGER NOT NULL,
    overrides INTEGER NOT NULL,
    accuracy_rate REAL NOT NULL,
    avg_confidence REAL NOT NULL,
    false_positive_rate REAL,
    false_negative_rate REAL
);

-- Indexes for performance
CREATE INDEX idx_decisions_client ON decisions(client_id);
CREATE INDEX idx_decisions_timestamp ON decisions(timestamp);
CREATE INDEX idx_patterns_type ON patterns(pattern_type);
CREATE INDEX idx_patterns_client ON patterns(client_id);
```

### AI Cost Analysis

**Traditional SOC Model** (no AI):
- 1 analyst can triage ~40 findings/day (8 hours, 12 min/finding)
- To handle 1,000 findings/day: 25 analysts
- Cost: 25 analysts × $80k/year = $2M/year

**Insa AI-Powered SOC Model**:
- AI auto-triages 950 findings/day (95%)
- Analysts review 50 findings/day (Critical/High + spot checks)
- Analysts needed: 2 analysts (with buffer)
- Cost:
  - 3 analysts × $80k/year = $240k/year
  - AI infrastructure (Claude Code license + compute): $0/year (local, zero API cost)
  - Platform (iac1 server): $500/month = $6k/year
- **Total Cost**: $246k/year

**Savings**: $2M - $246k = $1.754M/year (87.7% cost reduction)

**With 50 Clients @ $5k/month**:
- Revenue: 50 × $5,000 × 12 = $3M/year
- Cost: $246k/year
- Gross Profit: $2.754M
- **Gross Margin: 91.8%**

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-12 | Claude Code | Initial release |

---

**END OF DOCUMENT**

**CONFIDENTIAL - INTERNAL USE ONLY**
**Insa Automation Corp - SOC Operations Manual**
