# SOC Analyst Workflows (INTERNAL)
**Insa Automation Corp - Managed Industrial SOC 24/7**
**Document Classification**: CONFIDENTIAL - INTERNAL USE ONLY
**Version**: 1.0
**Date**: October 12, 2025

---

## Purpose

This document provides step-by-step workflows for common SOC analyst tasks at Insa Automation Corp. Use these procedures to ensure consistent, high-quality service delivery.

---

## Table of Contents

1. [Shift Start Workflow](#shift-start-workflow)
2. [Critical Finding Escalation](#critical-finding-escalation)
3. [Client Notification Templates](#client-notification-templates)
4. [AI Triage Verification](#ai-triage-verification)
5. [False Positive Processing](#false-positive-processing)
6. [SLA Management](#sla-management)
7. [Incident Response](#incident-response)
8. [Report Generation](#report-generation)
9. [Quarterly On-Site Visit Checklist](#quarterly-on-site-visit-checklist)
10. [Knowledge Base Maintenance](#knowledge-base-maintenance)
11. [Shift Handoff Workflow](#shift-handoff-workflow)

---

## Shift Start Workflow

**Duration**: 15 minutes
**Frequency**: Start of every 8-hour shift

### Checklist

- [ ] **Step 1: Review Handoff Notes** (5 minutes)
  ```
  1. Open Slack #soc-handoff channel
  2. Read most recent handoff note from previous shift
  3. React with ✅ emoji to acknowledge
  4. Note any critical items requiring immediate attention
  5. Check for tagged action items assigned to you
  ```

- [ ] **Step 2: Check AI Agent Health** (3 minutes)
  ```bash
  # SSH to iac1
  ssh 100.100.101.1

  # Check service status
  sudo systemctl status defectdojo-agent.service

  # Expected output: "active (running)"
  # If not running, restart and alert SOC manager:
  sudo systemctl restart defectdojo-agent.service
  sudo systemctl status defectdojo-agent.service

  # Check recent logs for errors
  sudo journalctl -u defectdojo-agent -n 50 --no-pager

  # Check for error patterns:
  grep -i error /var/log/defectdojo_agent.log | tail -20

  # Verify AI accuracy (should be ≥ 90%)
  sqlite3 /var/lib/defectdojo/learning.db \
    "SELECT COUNT(*) as total,
     SUM(CASE WHEN outcome='correct' THEN 1 ELSE 0 END) as correct,
     ROUND(SUM(CASE WHEN outcome='correct' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as accuracy
     FROM decisions
     WHERE timestamp > datetime('now', '-24 hours');"

  # Check GroupMQ queue depths
  redis-cli -p 6379 <<EOF
  LLEN scans/queued/*
  LLEN triage/pending/*
  LLEN alerts/critical/*
  EOF

  # Expected: < 100 per queue
  # If > 500, alert SOC manager (backlog)
  ```

  **If Issues Found**:
  - AI agent not running → Restart service, check logs, alert SOC manager if fails again
  - AI accuracy < 85% → Review recent overrides, check for pattern issues, alert SOC manager
  - Queue depths > 500 → Check scanner workers, verify GroupMQ connectivity, alert platform engineer

- [ ] **Step 3: Review Critical Alerts** (5 minutes)
  ```
  1. Open Slack #soc-critical channel
  2. Check for overnight/previous shift critical findings
  3. Sort by unread messages
  4. For each critical alert:
     - Open associated Jira ticket
     - Check current status
     - If unresolved:
       * Review finding in DefectDojo
       * Check if client has been notified
       * Determine next action (follow up, escalate, etc.)
  5. Prioritize action items:
     - Enterprise clients first
     - Active incidents
     - SLA approaching (< 4 hours)
  ```

- [ ] **Step 4: Check SLA Dashboard** (2 minutes)
  ```
  1. Open Grafana SLA Dashboard:
     URL: http://100.81.103.99:3001/d/sla-dashboard

  2. Review panels:
     - Findings by SLA Status (on-track, at-risk, breached)
     - Time Remaining Heatmap
     - SLA Compliance Rate (should be ≥ 95%)

  3. Identify at-risk findings (< 4 hours remaining):
     - Note finding IDs and clients
     - Add to priority action list

  4. If SLA breaches detected:
     - Review breach details
     - Notify SOC manager (if not already aware)
     - Determine root cause and corrective action
  ```

### Expected Outcome

After 15 minutes, you should have:
- ✅ Clear understanding of overnight activity
- ✅ List of prioritized tasks for the shift
- ✅ Confirmation that AI agent and infrastructure are healthy
- ✅ Awareness of any critical incidents or SLA risks

---

## Critical Finding Escalation

**When to Use**: AI flags a Critical severity finding (CVSS ≥ 9.0) requiring immediate human verification and client notification.

**Timeline**: Complete within 15 minutes of alert

### Workflow

**Step 1: Validate Finding** (5 minutes)
```
1. Open finding in DefectDojo:
   - Navigate to URL from Slack alert
   - Review finding details:
     * Title
     * Description
     * Severity (CVSS score)
     * CWE/CVE
     * Affected component/system
     * AI triage comment

2. Verify finding is legitimate (not false positive):

   Check #1: Is it production?
   - Review asset inventory for affected system
   - Check DefectDojo product tags (production vs dev/test)
   - If test environment: Downgrade severity, add comment, notify AI

   Check #2: Is it exploitable?
   - Search CVE on NVD: https://nvd.nist.gov/vuln/search/results?form_type=Basic&query=CVE-XXXX-XXXX
   - Check EPSS score (if available): https://www.first.org/epss/
     * EPSS > 0.8 = High probability of exploitation
     * EPSS < 0.1 = Low probability
   - Search ExploitDB: https://www.exploit-db.com/search?cve=CVE-XXXX-XXXX
   - Check Metasploit modules: https://www.rapid7.com/db/search?q=CVE-XXXX-XXXX

   Check #3: Is it already patched/mitigated?
   - Review Wazuh FIM logs (recent patches applied?)
   - Check with client (email sent in last 7 days about this CVE?)
   - Verify scanner results are recent (not stale data)

   Check #4: Is it a known false positive?
   - Query learning DB:
     sqlite3 /var/lib/defectdojo/learning.db \
       "SELECT * FROM decisions WHERE title LIKE '%[title keyword]%' AND ai_decision='false_positive' LIMIT 10;"
   - Check DefectDojo notes for similar past findings

3. Decision:
   ✅ VALID THREAT → Proceed to Step 2 (Client Notification)
   ❌ FALSE POSITIVE → Update finding:
     - Status: "Closed - False Positive"
     - Add comment: "Analyst review: [reason it's FP]"
     - Override AI decision (for learning)
     - Close Jira ticket
     - Post to #soc-critical: "RESOLVED: [Finding] - False Positive"
```

**Step 2: Client Notification** (5 minutes)
```
1. Determine client contact:
   - Enterprise tier: Use dedicated Slack channel + email + phone
   - Professional tier: Use Slack channel + email
   - Basic tier: Email only

2. Gather information for notification:
   - Finding title and description
   - CVSS score
   - Affected systems (hostnames, IPs)
   - Exploit status (in the wild? proof-of-concept available?)
   - Recommended remediation steps:
     * Check vendor advisory for patch
     * Check if workaround available
     * Suggest temporary mitigation (WAF rule, firewall block, service restart)
   - SLA deadline for remediation

3. Send notification using template:
   [See "Client Notification Templates" section below]

4. Create Jira ticket (if not auto-created):
   - Project: SOC
   - Issue Type: Incident
   - Summary: [Client Name] - [Finding Title]
   - Priority: Critical
   - Description: [Paste finding details + client notification]
   - Assignee: You
   - Labels: critical-finding, [client_id]
   - Due Date: [SLA deadline]

5. Log notification in DefectDojo:
   - Add comment: "Client notified via [channel] at [timestamp]"
   - Update finding tags: "client-notified"
```

**Step 3: Monitor and Follow Up** (ongoing)
```
1. Set timer for 30 minutes
   - If no client response, follow up:
     * Enterprise: Call client emergency contact
     * Professional: Send second email + Slack ping
     * Basic: Email follow-up

2. Track client response:
   - When client responds, log in Jira:
     "Client acknowledged at [timestamp]. ETA for remediation: [date/time]"
   - Update DefectDojo finding:
     Add comment: "Client response: [summary]"
     Change status: "Under Review" → "Remediation in Progress"

3. Request validation:
   - When client reports patching complete:
     * Schedule rescan to validate
     * Or request evidence (screenshot, patch logs)
   - If validated:
     * Close finding: "Closed - Remediated"
     * Close Jira ticket
     * Send confirmation to client (optional, for Enterprise tier)

4. If client does not respond within SLA:
   - Escalate to SOC manager
   - Request SLA extension approval
   - Document in Jira
```

### Expected Outcome

- ✅ Valid critical findings identified and communicated within 15 minutes
- ✅ False positives closed with feedback to AI
- ✅ Client acknowledges and provides remediation timeline
- ✅ Jira ticket tracks incident to resolution

---

## Client Notification Templates

### Template 1: Critical Finding Notification (Email)

**Subject**: `[CRITICAL] Security Vulnerability Detected - Immediate Action Required`

**Body**:
```
Dear [Client Contact Name],

Our Security Operations Center has identified a CRITICAL security vulnerability in your environment that requires immediate attention.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 CRITICAL SECURITY ALERT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Finding: [Full Finding Title]
Severity: Critical (CVSS [Score])
CVE: [CVE-XXXX-XXXX] (if applicable)

Affected Systems:
- [Hostname/IP 1]
- [Hostname/IP 2]
- [Add more as needed]

Risk Assessment:
- Exploit Probability: [HIGH/MEDIUM/LOW] (EPSS: [score])
- Known Exploits: [YES/NO] - [ExploitDB link if available]
- Attack Complexity: [Low/Medium/High]
- Potential Impact: [Brief description of what attacker could do]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDED ACTIONS (Immediate)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. [Primary Remediation]:
   [Specific steps, e.g., "Apply vendor patch version X.Y.Z"]
   Vendor Advisory: [Link]

2. [Temporary Mitigation] (if patch requires maintenance window):
   [Specific steps, e.g., "Disable vulnerable service", "Apply WAF rule"]

3. [Validation]:
   [How to verify remediation, e.g., "Restart service and verify version"]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SLA & NEXT STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Remediation Deadline: [Date/Time] ([X] hours from detection)

Please confirm receipt of this alert and provide an estimated remediation timeline within 30 minutes.

We are standing by to assist with remediation. If you need help, please reply to this email or contact us via:
- Email: [analyst email]
- Phone: [analyst phone] (Enterprise tier only)
- Slack: #[client-channel] (if applicable)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TRACKING INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Jira Ticket: [SOC-XXXX] - [Link]
DefectDojo Finding: [Finding ID] - [Link to client portal]
Detected: [Timestamp]
SOC Analyst: [Your Name]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If you have any questions or need clarification, please don't hesitate to reach out.

Best regards,

[Your Name]
Security Operations Analyst
Insa Automation Corp - 24/7 SOC
Email: [your email]
Phone: [your phone] (Enterprise tier only)
Portal: https://portal.insa-automation.com

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This is an automated security alert from Insa SecureOps Platform.
Confidential - For authorized personnel only.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Template 2: High Severity Finding Notification (Email)

**Subject**: `[HIGH] Security Vulnerability Detected - Action Required`

**Body**:
```
Dear [Client Contact Name],

Our SOC has identified a HIGH severity security vulnerability in your environment.

Finding: [Full Finding Title]
Severity: High (CVSS [Score])
CVE: [CVE-XXXX-XXXX] (if applicable)

Affected Systems:
- [List systems]

Recommended Actions:
1. [Remediation steps]
2. [Timeline recommendation, e.g., "Apply patch within 72 hours"]

This finding has been triaged by our AI-powered analysis system and verified by our security analysts.

Remediation Deadline (SLA): [Date/Time]

For detailed information and remediation guidance, please visit:
[Link to DefectDojo finding in client portal]

Questions? Reply to this email or contact your SOC analyst:
[Your Name] - [Email]

Jira Ticket: [SOC-XXXX]

Best regards,
Insa Automation Corp - SOC Team
```

### Template 3: Critical Finding Slack Notification

**Channel**: Client dedicated channel (e.g., `#client-acme-soc`)

**Message**:
```
🚨 **CRITICAL SECURITY ALERT** 🚨

**Finding**: [Title]
**Severity**: Critical (CVSS [score])
**CVE**: [CVE-XXXX-XXXX]

**Affected Systems**:
• [System 1]
• [System 2]

**Exploit Risk**: HIGH - Active exploits available

**Action Required**:
[Specific remediation step]

**SLA Deadline**: [Date/Time] ([X] hours)

📧 **Detailed email sent to**: [email addresses]
🎫 **Jira Ticket**: [SOC-XXXX] - [Link]

Please acknowledge this alert by reacting with ✅

Need help? Tag @soc-analyst or call [phone] (Enterprise tier)

---
_Detected by Insa SecureOps AI at [timestamp]_
```

### Template 4: Follow-Up (Client Unresponsive)

**Subject**: `[FOLLOW-UP] Critical Security Alert - Response Required`

**Body**:
```
Dear [Client Contact Name],

This is a follow-up to our critical security alert sent at [timestamp].

We have not yet received acknowledgment of this alert. This vulnerability poses significant risk to your environment and requires immediate attention.

Original Alert: [Brief summary]
SLA Deadline: [Date/Time] - [X] hours remaining

URGENT: Please confirm receipt and provide an estimated remediation timeline.

If you need assistance or an SLA extension, please contact us immediately:
- Reply to this email
- Call: [phone] (Enterprise tier)
- Slack: [channel]

Thank you,
[Your Name]
Insa Automation Corp - SOC
```

### Template 5: Remediation Confirmed

**Subject**: `[RESOLVED] Security Vulnerability Remediated - [Finding Title]`

**Body**:
```
Dear [Client Contact Name],

Great news! We have confirmed that the following security vulnerability has been successfully remediated:

Finding: [Title]
Original Severity: [Critical/High]
Affected Systems: [List]

Remediation Actions Taken:
- [Action 1]
- [Action 2]

Validation:
✅ Rescan completed: [timestamp]
✅ Vulnerability no longer detected
✅ Finding closed in DefectDojo

Timeline:
- Detected: [timestamp]
- Client Notified: [timestamp]
- Remediated: [timestamp]
- **Total Time**: [X] hours (SLA: [Y] hours) ✅

This finding has been closed. No further action is required.

Thank you for your prompt response and remediation.

Best regards,
[Your Name]
Insa Automation Corp - SOC

Jira Ticket: [SOC-XXXX] (Closed)
```

---

## AI Triage Verification

**Purpose**: Spot-check AI triage decisions to ensure accuracy and provide feedback for learning.

**Frequency**: Ongoing throughout shift (target: 10-20 findings/shift)

### Workflow

**Step 1: Select Findings for Review** (2 minutes)
```
Method A - Random Sampling:
  1. Open DefectDojo
  2. Navigate to Findings
  3. Filter:
     - Status: "Closed - Mitigated" OR "Closed - False Positive"
     - Tags: "ai-triaged"
     - Date: Last 24 hours
  4. Sort by: Random (or select every 10th finding)
  5. Review 10-20 findings

Method B - Targeted Review:
  1. Focus on specific patterns:
     - Low AI confidence (70-80%) that were auto-triaged
     - New vulnerability types (first seen in last 7 days)
     - Client-specific patterns (new client, or client with history of FPs)
  2. Review 5-10 findings per pattern

Method C - High Severity Spot Check:
  1. Filter:
     - Severity: High
     - Tags: "ai-triaged"
     - Status: "Closed"
     - Date: Last 24 hours
  2. Review 20% of findings (random sample)
```

**Step 2: Evaluate AI Decision** (3 minutes per finding)
```
For each finding, answer these questions:

1. Was the AI decision correct?
   ✅ Correct: Finding was properly classified (valid threat or false positive)
   ❌ Incorrect: Finding was misclassified

2. Was the AI reasoning sound?
   - Read AI comment in DefectDojo
   - Does reasoning make sense given the evidence?
   - Did AI consider relevant factors (EPSS, CVE, client context)?

3. Would you have made the same decision?
   - As a human analyst, review the finding independently
   - Compare your conclusion to AI decision

4. If AI was incorrect, why?
   Possible reasons:
   - Missing context (e.g., test environment not tagged properly)
   - New vulnerability type (no historical data)
   - Client-specific exception (e.g., accepted risk)
   - False positive pattern not yet learned
   - EPSS score misleading
   - CVE details incomplete

5. Document your evaluation:
   If CORRECT:
     - No action needed (spot check complete)
     - Optionally add comment: "Analyst verified - AI decision correct ✓"

   If INCORRECT:
     - Click "Override AI Decision"
     - Change finding status/severity to correct value
     - Add detailed comment explaining why AI was wrong:
       "Override: AI marked as false positive, but this is a genuine threat.
        Reason: [specific details]. This affects production systems and
        requires remediation. AI missed [key factor]."
     - Learning engine will capture this feedback automatically
```

**Step 3: Track Override Patterns** (5 minutes at end of shift)
```
1. Review your overrides for the shift:
   - How many findings reviewed: [X]
   - How many overrides: [Y]
   - Override rate: [Y/X × 100]%

2. Identify patterns in overrides:
   - Same vulnerability type? (e.g., multiple SQL injection FPs)
   - Same client? (client-specific issue)
   - Same severity? (AI consistently wrong on Medium severity)
   - New CVEs? (AI lacks data on recent vulnerabilities)

3. If pattern detected (≥3 similar overrides):
   - Post to Slack #soc-ai-learning:
     "Pattern detected: AI incorrectly classifying [description] as [FP/valid].
      Reviewed [X] findings, [Y] incorrect. Recommend pattern adjustment.
      Example findings: [IDs]"
   - Alert SOC manager
   - Request AI pattern update

4. Document in shift handoff:
   "AI Spot Check: Reviewed [X] findings, [Y] overrides ([Z]% accuracy).
    Pattern noted: [description if applicable]."
```

### AI Verification Metrics

**Target Metrics**:
- AI Accuracy: ≥ 90%
- Analyst Override Rate: ≤ 10%
- False Positive Rate: ≤ 15%
- False Negative Rate: ≤ 5%

**If Metrics Out of Range**:
- AI Accuracy < 85% → Alert SOC manager immediately, review recent changes
- Override Rate > 15% → Check for systematic issues, may need AI retraining
- FP Rate > 20% → Review FP patterns, update learning DB
- FN Rate > 10% → CRITICAL, may be missing genuine threats, escalate immediately

---

## False Positive Processing

**When to Use**: Finding is determined to be a false positive (not a genuine security threat).

**Goal**: Close false positive and provide feedback to AI to improve future accuracy.

### Workflow

**Step 1: Confirm False Positive** (3 minutes)
```
Verify finding is genuinely a false positive:

Common False Positive Patterns:
1. Test/Development Environment:
   - Finding in /test/, /dev/, or non-production system
   - Example: "Critical SQLi in test_login.php"

2. Mitigated by Controls:
   - Vulnerability exists but is not exploitable due to network segmentation, WAF, etc.
   - Example: "Port 22 open" but only accessible via VPN

3. Already Patched:
   - Scanner results are stale
   - Example: "CVE-2023-12345" but client patched 2 weeks ago

4. Known Accepted Risk:
   - Client has documented exception
   - Example: "Weak cipher enabled" but required for legacy device compatibility

5. Scanner Error:
   - Scanner misidentified benign code as vulnerable
   - Example: "Hardcoded password" but it's a test constant in comment

6. Not Applicable:
   - Vulnerability does not apply to client's configuration
   - Example: "Windows vuln" detected on Linux system (scanner confusion)

Decision:
✅ Confirmed False Positive → Proceed to Step 2
❌ Not a False Positive → Re-evaluate as valid finding, escalate if needed
```

**Step 2: Close Finding in DefectDojo** (2 minutes)
```
1. Open finding in DefectDojo
2. Click "Edit" button
3. Update fields:
   - Status: "Closed - False Positive" (or "Accepted Risk" if client-approved exception)
   - Add comment:
     "Analyst Review: False Positive
      Reason: [Specific reason, e.g., 'Test file in /test/ directory, not production code']
      Verified by: [Your Name]
      Date: [Timestamp]"
   - Tags: Add "false-positive", "analyst-verified"
   - If AI decision was wrong, check "Override AI Decision" box

4. Click "Save"

5. If associated Jira ticket exists:
   - Transition ticket to "Closed"
   - Add comment: "False positive confirmed. Finding closed in DefectDojo."
```

**Step 3: Provide AI Feedback** (1 minute)
```
AI Learning Engine automatically captures:
- Original AI decision (if it marked as valid threat)
- Your override decision (false positive)
- Your reasoning (from DefectDojo comment)
- Pattern analysis (does this match known FP patterns?)

Feedback is processed every 2 hours and AI confidence is adjusted.

No manual action required unless pattern is urgent (see Step 4).
```

**Step 4: Check for Pattern** (2 minutes)
```
If you notice multiple similar false positives:

1. Search DefectDojo for similar findings:
   - Filter by title keywords
   - Check if multiple findings have same root cause

2. If pattern found (≥3 similar findings):
   - Bulk close similar findings:
     * Select all matching findings
     * Bulk action: "Close as False Positive"
     * Bulk comment: "FP Pattern: [description]. Bulk closed by [Your Name]."

   - Alert AI learning system:
     * Post to Slack #soc-ai-learning:
       "FP Pattern detected: [description]
        Count: [X] findings
        Clients affected: [list]
        Recommendation: Update AI pattern to reduce confidence for [pattern type]"

   - Document in knowledge base:
     * Add entry to "Known False Positive Patterns" (see Knowledge Base section)
     * Include detection criteria and resolution steps
```

**Step 5: Communicate to Client (if needed)** (2 minutes)
```
If client inquired about the finding or was previously notified:

1. Send follow-up email:
   Subject: [RESOLVED] False Positive - [Finding Title]

   Body:
   "Dear [Client Name],

   We have reviewed the security finding we previously reported:

   Finding: [Title]
   Initial Severity: [Severity]

   After thorough analysis, our team has determined this is a FALSE POSITIVE.

   Reason: [Explanation in non-technical terms]

   No action is required on your part. This finding has been closed in our system.

   Our AI triage system has been updated to improve detection of similar
   false positives in the future.

   If you have any questions, please let us know.

   Best regards,
   [Your Name]
   Insa Automation Corp - SOC"

2. Log communication in DefectDojo:
   - Add comment: "Client notified of false positive at [timestamp]"
```

### Bulk False Positive Processing

**When to Use**: Multiple findings (10+) identified as same false positive pattern.

**Workflow**:
```
1. Identify pattern:
   - Example: "All findings in /test/ directory are false positives"

2. DefectDojo bulk operation:
   - Navigate to Findings
   - Filter:
     * Title contains: "test"
     * Status: "Open" or "Under Review"
   - Select all matching findings (or sample 10 for review, then bulk)
   - Bulk Actions dropdown:
     * Action: "Close findings"
     * Status: "Closed - False Positive"
     * Comment: "Bulk FP closure: Test files, not production code. Verified by [Your Name]."
   - Click "Apply"

3. Alert AI:
   - Post pattern to Slack #soc-ai-learning
   - Learning engine will update confidence for this pattern

4. Document:
   - Update knowledge base with pattern details
   - Add to shift handoff notes
```

---

## SLA Management

**Goal**: Ensure all findings are remediated or triaged within SLA deadlines.

**SLA Definitions** (reference):
- **Basic Tier**: Critical (24h), High (7d), Medium (30d)
- **Professional Tier**: Critical (4h), High (48h), Medium (14d)
- **Enterprise Tier**: Critical (1h), High (24h), Medium (7d)

### Daily SLA Monitoring Workflow

**Step 1: Check SLA Dashboard** (every 2 hours during shift)
```
1. Open Grafana SLA Dashboard:
   http://100.81.103.99:3001/d/sla-dashboard

2. Review panels:
   A. Findings by SLA Status:
      - On Track (green): > 50% time remaining
      - At Risk (yellow): 10-50% time remaining
      - Critical (red): < 10% time remaining
      - Breached (black): Past deadline

   B. Time Remaining Heatmap:
      - Visual representation of findings by time remaining
      - Darker red = more urgent

   C. SLA Compliance Rate:
      - Current: [X]% (Target: ≥ 95%)
      - Trend over past 30 days

3. Export at-risk findings:
   - Click "Export" button
   - Download CSV of findings with < 4 hours remaining
   - Import into your work queue
```

**Step 2: Prioritize At-Risk Findings** (5 minutes)
```
Sort at-risk findings by:
  1. Client tier (Enterprise > Professional > Basic)
  2. Time remaining (ascending)
  3. Severity (Critical > High > Medium)

Create action plan:
  Finding ID | Client | Severity | Time Left | Status | Action Needed
  -----------|--------|----------|-----------|--------|---------------
  12345      | ACME   | Critical | 30 min    | Open   | Call client NOW
  12346      | XYZ    | High     | 2 hours   | In Progress | Follow up on patch status
  12347      | ABC    | High     | 3 hours   | Under Review | Verify false positive, close
```

**Step 3: Take Action** (varies)
```
For each at-risk finding:

  If Status = "Open" (not yet triaged):
    → Triage immediately (even if AI should have handled it)
    → Alert SOC manager if AI missed this finding
    → Document issue for AI improvement

  If Status = "Under Review" (awaiting client action):
    → Contact client for status update:
      * Email: "Following up on [finding]. SLA deadline in [X] hours. Please provide update."
      * Slack: Tag client contact in dedicated channel
      * Phone (Enterprise only): Call if < 30 min remaining on Critical finding
    → Document client response in Jira and DefectDojo

  If Status = "False Positive" (incorrectly open):
    → Close immediately
    → Add comment explaining why it was not closed earlier
    → Alert SOC manager if process breakdown

  If Status = "Remediation in Progress" (client working on it):
    → Request ETA if < 1 hour remaining
    → If client cannot meet SLA:
      * Escalate to SOC manager for SLA extension approval
      * Document reason and client approval
      * Update SLA deadline in DefectDojo
```

**Step 4: Escalate if Needed** (immediate)
```
Escalate to SOC Manager if:
- SLA breach unavoidable (< 15 min remaining, client unresponsive)
- Client explicitly requests SLA extension
- Multiple SLA breaches for same client (pattern of delays)
- AI agent failed to triage findings on time (system issue)

Escalation message (Slack #soc-escalations):
"SLA Breach Escalation

Client: [Name]
Finding: [ID] - [Title]
Severity: [Critical/High/Medium]
SLA Deadline: [Timestamp] ([X] minutes ago/remaining)
Status: [Current status]

Root Cause: [Why breach occurred, e.g., 'Client unresponsive for 3 hours']

Action Taken: [What you've done, e.g., '3 email attempts, 2 Slack pings, 1 phone call']

Requesting: [What you need, e.g., 'Approval for 24h SLA extension', 'Executive escalation']

Analyst: [Your Name]"
```

### SLA Extension Process

**When Client Cannot Meet SLA**:
```
1. Client requests extension:
   - Document request in Jira:
     Add comment: "Client requests SLA extension. Reason: [reason]. Proposed new deadline: [date]."

2. Evaluate request:
   - Valid reasons: Maintenance window not available, requires vendor patch, testing required
   - Invalid reasons: Forgot, too busy, don't care

3. Approve/Deny:
   - Analyst can approve up to 24-hour extension for High/Medium findings
   - SOC Manager must approve Critical finding extensions or > 24h extensions

4. Update DefectDojo:
   - Edit finding
   - Update "SLA Deadline" field to new date/time
   - Add comment: "SLA extension approved by [Name]. New deadline: [date]. Reason: [reason]."
   - Tag: "sla-extended"

5. Confirm with client:
   - Email: "We have approved your SLA extension request. New deadline: [date]. Please ensure remediation is completed by this time."

6. Log for reporting:
   - SLA extensions are tracked separately from breaches
   - Monthly report includes: # extensions, avg extension duration, reasons
```

---

## Incident Response

**Definition**: Security incident requiring coordinated response (active compromise suspected or confirmed).

**Severity Levels**:
- **P1 (Critical)**: Active breach, data exfiltration, ransomware
- **P2 (High)**: Attempted breach, suspicious activity, critical vuln being exploited
- **P3 (Medium)**: Unusual activity, policy violation, non-critical compromise

### Incident Response Workflow

**Step 1: Incident Declaration** (immediate)
```
When to declare incident:
- Wazuh alert + DefectDojo critical finding + suspicious network activity
- Client reports potential breach
- Multiple critical findings + evidence of exploitation
- Ransomware/malware detected
- Unauthorized access detected (root/admin)

Action:
1. Post to Slack #incidents:
   "🚨 INCIDENT DECLARED

   Client: [Name]
   Severity: P[1/2/3]
   Summary: [Brief description]
   Analyst: [Your Name]
   Timestamp: [Time]"

2. Alert SOC Manager (call if P1, Slack if P2/P3)

3. Create Jira Incident ticket:
   - Project: SOC
   - Issue Type: Incident
   - Priority: Critical/High
   - Summary: "[P1/P2/P3] [Client] - [Brief Description]"
   - Description: [Detailed incident info]
   - Assignee: You
   - Watchers: SOC Manager, Senior Analyst

4. Create incident war room:
   - Slack channel: #incident-[client]-[date]
   - Invite: SOC team, client contacts (if appropriate)
```

**Step 2: Containment** (T+0 to T+15 min for P1)
```
Immediate actions to stop attack from spreading:

1. Contact client immediately:
   - Phone call (don't wait for email)
   - Explain situation clearly and calmly
   - Provide specific containment recommendations:

   Example:
   "We have detected [suspicious activity] indicating potential compromise of [system].
    We recommend you immediately:
    1. Isolate affected systems from network (don't shut down - preserve evidence)
    2. Reset passwords for [affected accounts]
    3. Enable enhanced logging on [systems]
    4. Do NOT delete any files or logs (needed for forensics)

    We will assist you with investigation and recovery. Are you able to take these actions now?"

2. Document containment actions in Jira:
   - What client did
   - When they did it
   - Outcome

3. Verify containment:
   - Check Wazuh for ongoing suspicious activity
   - Check Suricata for malicious network traffic
   - Confirm with client that systems are isolated
```

**Step 3: Investigation** (T+15 min to T+2 hours for P1)
```
Gather evidence and build timeline:

1. Collect logs:
   - Wazuh FIM logs (file changes)
   - Wazuh auth logs (login attempts, privilege escalation)
   - Suricata network captures (malicious IPs, C2 communication)
   - Application logs from affected systems
   - Firewall logs
   - Proxy logs (if available)

2. Build timeline:
   Create spreadsheet or document:
   Timestamp | Event | Source | Evidence
   ----------|-------|--------|----------
   Oct 11 14:32 | Initial compromise (CVE-2023-12345 exploit) | Suricata | PCAP shows exploit payload
   Oct 11 14:35 | Privilege escalation to root | Wazuh | /var/ossec/logs/auth.log
   Oct 11 14:40 | Lateral movement to DB server | Suricata | RDP connection to 192.168.1.50
   Oct 11 14:50 | Data staging in /tmp/ | Wazuh FIM | /tmp/customer_data.zip created

3. Determine scope:
   - Which systems were compromised?
   - What data was accessed/exfiltrated?
   - How did attacker gain access?
   - What was attacker's goal?
   - Are there other compromised systems not yet detected?

4. Document findings in Jira (continuously update)
```

**Step 4: Eradication** (T+2 hours to T+12 hours)
```
Remove attacker access and persistence:

1. Identify attacker's foothold:
   - Backdoors (web shells, SSH keys, scheduled tasks)
   - Malicious accounts (new admin accounts)
   - Malware/rootkits
   - Modified system files

2. Remove attacker access:
   - Delete backdoors (document before deletion!)
   - Remove unauthorized accounts
   - Reset all credentials (passwords, API keys, SSH keys)
   - Patch vulnerable software
   - Update firewall rules to block attacker IPs

3. Verify eradication:
   - Rescan systems with multiple scanners (Wazuh, ClamAV, rkhunter)
   - Check for persistence mechanisms
   - Monitor for attacker return (enhanced logging for 7 days)

4. Consider full rebuild:
   - If rootkit suspected or integrity cannot be verified
   - Rebuild from known-good backups (before compromise)
   - Reinstall OS and applications
```

**Step 5: Recovery** (T+12 hours to T+48 hours)
```
Restore normal operations:

1. Bring systems back online (in order):
   - Non-critical systems first (test recovery process)
   - Critical systems last (ensure they're clean)

2. Validate data integrity:
   - Check backups for completeness
   - Verify no malicious modifications

3. Enhanced monitoring:
   - 24/7 watch for 7 days
   - Alert on any unusual activity
   - Daily check-ins with client

4. Update Jira status:
   - Transition to "Recovery"
   - Document recovery steps and timeline
```

**Step 6: Post-Incident Report** (T+1 week)
```
1. Write comprehensive incident report:
   Template sections:
   - Executive Summary (1 page)
   - Incident Timeline (detailed)
   - Root Cause Analysis (how did this happen?)
   - Scope of Compromise (what was affected?)
   - Actions Taken (containment, eradication, recovery)
   - Evidence Collected (logs, screenshots, etc.)
   - Lessons Learned (what went well, what didn't)
   - Recommendations (how to prevent recurrence)
     * Technical controls (patches, segmentation, etc.)
     * Process improvements (change management, monitoring)
     * Training (security awareness for client staff)

2. Deliver report to:
   - Client (C-level and technical contacts)
   - SOC Manager
   - INSA leadership (if major incident)

3. Conduct lessons learned meeting:
   - Internal SOC team debrief
   - What did we do well?
   - What could we improve?
   - Update runbooks/playbooks
   - Train on new techniques

4. Close Jira incident ticket:
   - Final comment: "Incident resolved. Post-incident report delivered to client."
   - Attach report PDF
   - Transition to "Closed"
```

---

## Report Generation

**Purpose**: Provide clients with regular security reports (daily, weekly, monthly).

**Automation**: 95% automated by AI, analyst reviews and customizes.

### Daily Security Report

**Frequency**: Daily at 8 AM (automated)

**Analyst Workflow** (5 minutes):
```
1. Check your email for "Daily Security Report - [Date]" from soc@insaing.com
   - This is auto-generated by AI agent

2. Review report for accuracy:
   - Findings count (does it match DefectDojo?)
   - Top findings (are these actually the most important?)
   - AI statistics (accuracy rate should be ≥ 90%)

3. Customize for Enterprise clients:
   - Add analyst commentary:
     "Note: The Critical finding (#123) requires attention from your dev team.
      We recommend scheduling a patch deployment this week."
   - Provide context not visible to AI:
     "The spike in Medium findings is due to scheduled Trivy scan of new containers."

4. Review and send:
   - Basic tier: No customization needed (auto-sent)
   - Professional tier: Quick review, add note if needed, send
   - Enterprise tier: Detailed review, add commentary, send with personal message

5. If report errors detected:
   - Alert SOC manager
   - Manually generate corrected report
   - Investigate AI issue (bad data, API error, etc.)
```

**Manual Generation** (if needed):
```bash
# SSH to iac1
ssh 100.100.101.1

# Run report generator manually
cd /home/wil/devops/devsecops-automation/defectdojo/reporting
./daily_report_generator.py --client-id client_acme --date 2025-10-11

# Output: report saved to /tmp/daily_report_client_acme_2025-10-11.html

# Email report
python3 email_report.py --client-id client_acme --report /tmp/daily_report_client_acme_2025-10-11.html
```

### Weekly Executive Summary

**Frequency**: Monday 9 AM (automated)

**Analyst Workflow** (15 minutes):
```
1. Review auto-generated weekly report

2. Add executive insights:
   - Trend analysis: "Findings decreased 15% this week due to proactive patching"
   - Risk assessment: "Top risk remains web application vulnerabilities. Recommend security code review."
   - Recommendations: "Consider implementing automated patch management for faster remediation"

3. Customize charts/graphs (if needed):
   - Export data from DefectDojo
   - Create custom visualizations in Excel/Google Sheets
   - Embed in report

4. Review with SOC manager (for Enterprise clients):
   - Ensure messaging aligns with client expectations
   - Verify recommendations are actionable

5. Send report:
   - Professional tier: Email report as attachment
   - Enterprise tier: Email + schedule call to review (if requested)

6. Log report delivery in Jira
```

### Monthly Security Report

**Frequency**: First Monday of month (manual with AI assistance)

**Analyst Workflow** (1 hour per Enterprise client):
```
1. Gather data:
   - Export DefectDojo metrics for past month:
     * Total findings
     * Findings by severity
     * Findings by category (web app, infrastructure, etc.)
     * MTTR (mean time to remediate) by severity
     * SLA compliance rate
     * False positive rate

2. AI-assisted report generation:
   - Run monthly report script:
     ./monthly_report_generator.py --client-id client_acme --month 2025-10

   - AI generates:
     * Summary statistics
     * Trend charts (findings over time)
     * Top 10 findings
     * Remediation progress
     * Compliance status

3. Analyst customization:
   A. Executive Summary (write 1-2 paragraphs):
      "Overall, [Client] demonstrated strong security posture this month with 98% SLA compliance.
       We identified and remediated [X] critical vulnerabilities within SLA. Key focus areas for
       next month include [recommendations]."

   B. Highlight significant incidents (if any):
      - Include incident timeline
      - Remediation actions taken
      - Lessons learned

   C. Add strategic recommendations:
      - Based on trends (e.g., recurring vulnerability types → training needed)
      - Industry best practices (e.g., new OWASP Top 10 items)
      - Compliance requirements (e.g., SOC 2, PCI DSS updates)

   D. Customize for audience:
      - C-level: Focus on risk, business impact, compliance
      - Technical: Include detailed findings, remediation guidance, metrics

4. Review with SOC manager:
   - Quality check
   - Align messaging with client relationship

5. Deliver report:
   - Email PDF report
   - Enterprise tier: Schedule quarterly review call to discuss

6. Archive report:
   - Save to client folder: /var/lib/defectdojo/clients/[client_id]/reports/
   - Upload to client portal (if applicable)
```

### Quarterly On-Site Report (Enterprise Only)

**Frequency**: Quarterly (on-site visit)

**Analyst Workflow** (3 hours to prepare + 3 hours on-site):
```
Preparation (1 week before visit):

1. Generate comprehensive report:
   - 3-month trend analysis
   - All findings (detailed list)
   - Incident summaries
   - AI triage statistics
   - Comparison to industry benchmarks
   - Compliance scorecard (if applicable)

2. Create presentation (PowerPoint/Google Slides):
   - Slides for each section
   - Executive summary
   - Key metrics (with visuals)
   - Top risks
   - Recommendations
   - Q&A

3. Review with SOC manager:
   - Practice presentation
   - Anticipate client questions
   - Align on recommendations

On-Site Visit:

1. Introduction (15 min):
   - Introductions (attendees: C-level, IT director, SecOps team)
   - Agenda overview
   - Set expectations

2. Security Posture Review (60 min):
   - Present metrics and trends
   - Discuss findings (Critical/High)
   - Review incident responses (if any)
   - Celebrate wins (improved MTTR, zero breaches, etc.)

3. AI System Overview (30 min):
   - How our AI triage works (high-level, not technical)
   - Benefits: Faster triage, 24/7 coverage, continuous learning
   - Accuracy metrics for your organization
   - Human analyst verification process

4. Strategic Recommendations (45 min):
   - Present top 5 recommendations
   - Discuss feasibility and priorities
   - Create action plan with timelines
   - Assign owners (client side)

5. Q&A and Planning (30 min):
   - Open discussion
   - Address concerns
   - Schedule next quarter activities (scans, pen tests, etc.)
   - Collect feedback on SOC service

Post-Visit:

1. Send follow-up email:
   - Thank client for time
   - Attach presentation slides
   - Attach detailed quarterly report (PDF)
   - Summarize action items with deadlines

2. Update Jira with action items:
   - Create tickets for follow-up tasks
   - Assign to appropriate analysts

3. Document feedback:
   - What went well in presentation?
   - What could be improved?
   - Client concerns or requests?
   - Share with SOC team for continuous improvement
```

---

## Quarterly On-Site Visit Checklist

**(Enterprise Tier Clients Only)**

### Pre-Visit (1 Week Before)

**Logistics**:
- [ ] Confirm date/time with client (email + calendar invite)
- [ ] Confirm location (client office address, meeting room)
- [ ] Confirm attendees (client: C-level, IT director, SecOps; INSA: Analyst, SOC manager optional)
- [ ] Book travel (flight, hotel, car) if needed
- [ ] Pack materials (laptop, presentation, business cards, notebook)

**Content Preparation**:
- [ ] Generate quarterly report (see Report Generation section above)
- [ ] Create presentation slides (see template below)
- [ ] Review all incidents from past quarter
- [ ] Prepare talking points for top 5 recommendations
- [ ] Gather client-specific context (industry, compliance requirements, etc.)
- [ ] Review client history (past quarterly meetings, recurring issues)

**Internal Coordination**:
- [ ] Review presentation with SOC manager
- [ ] Practice presentation (30 min rehearsal)
- [ ] Prepare for Q&A (anticipate tough questions)
- [ ] Align on pricing/upsell opportunities (if applicable)

### Day of Visit

**Setup** (15 min before start):
- [ ] Arrive early
- [ ] Test AV equipment (projector, screen sharing)
- [ ] Distribute printed materials (if applicable)
- [ ] Greet attendees as they arrive

**Agenda** (3 hours total):
- [ ] **Introduction** (15 min):
  - Introductions and role of each attendee
  - Agenda overview
  - Review objectives for meeting

- [ ] **Security Posture Review** (60 min):
  - Present metrics dashboard:
    * Total findings (trend over 3 months)
    * MTTR by severity
    * SLA compliance rate
    * Top vulnerability categories
  - Discuss Critical/High findings:
    * How many detected
    * How many remediated
    * Outstanding items requiring attention
  - Incident summary (if any):
    * What happened
    * How we responded
    * Outcome and lessons learned
  - Celebrate successes:
    * Improved metrics (faster remediation, fewer findings)
    * Zero breaches
    * Strong partnership

- [ ] **AI System Transparency** (30 min):
  - Explain hybrid AI-human model:
    * "Our service combines advanced AI triage with expert analyst verification"
    * "AI handles 95% of routine findings, freeing analysts for complex threats"
    * "Every Critical finding is human-verified"
  - Show client-specific AI statistics:
    * Findings auto-triaged: X%
    * AI accuracy rate: Y% (should be ≥ 90%)
    * False positive rate: Z%
  - Emphasize benefits:
    * 24/7 coverage (AI never sleeps)
    * Faster triage (minutes vs hours)
    * Continuous learning (improves over time)
  - Address concerns:
    * "Can we trust AI?" → "AI is supervised by analysts, not autonomous"
    * "Will AI miss threats?" → "AI accuracy is 90%+, and all Critical findings are human-verified"

- [ ] **Strategic Recommendations** (45 min):
  - Present top 5 recommendations:
    1. [Example: Implement automated patch management]
       - Current: Manual patching, avg 7 days MTTR
       - Proposed: Automated with Ansible/Chef, target 2 days MTTR
       - Benefit: Reduce attack surface, faster remediation
       - Effort: Medium (2-3 weeks implementation)
       - Owner: [Client IT director]

    2. [Example: Deploy WAF for web applications]
       - Current: 60% of findings are web app vulns
       - Proposed: ModSecurity or cloud WAF
       - Benefit: Mitigate OWASP Top 10 risks
       - Effort: Low (1 week)
       - Owner: [Client DevOps]

    [... continue for all 5 recommendations]

  - Prioritize together:
    * What is most critical?
    * What is most feasible?
    * Create action plan with timelines

- [ ] **Next Quarter Planning** (20 min):
  - Schedule next quarterly review
  - Plan special activities:
    * Penetration testing (annual)
    * Compliance audit (if needed)
    * Security awareness training
  - Adjust scan schedules if needed
  - Discuss service changes (new assets, new applications)

- [ ] **Q&A** (30 min):
  - Open floor for questions
  - Address concerns
  - Collect feedback on SOC service:
    * What's working well?
    * What could be improved?
    * Any new requirements?

**Wrap-Up**:
- [ ] Thank attendees for their time
- [ ] Confirm action items and owners
- [ ] Provide contact info for follow-up questions
- [ ] Collect business cards (if new contacts)

### Post-Visit (Within 24 Hours)

**Follow-Up**:
- [ ] Send thank you email with:
  - Presentation slides attached
  - Quarterly report PDF attached
  - Summary of action items with deadlines
  - Next steps (e.g., "We'll follow up on WAF deployment in 2 weeks")

**Documentation**:
- [ ] Log meeting notes in Jira:
  - Create ticket: "Quarterly Review - [Client] - [Date]"
  - Attach slides and report
  - Document action items (create sub-tickets for each)
  - Note any concerns or feedback

**Internal Debrief**:
- [ ] Discuss with SOC manager:
  - What went well?
  - What could be improved?
  - Any red flags (client dissatisfaction, churn risk)?
  - Upsell opportunities identified?
- [ ] Update client profile with insights
- [ ] Share lessons learned with SOC team (if applicable)

---

## Knowledge Base Maintenance

**Purpose**: Document common patterns, solutions, and lessons learned for team efficiency.

**Location**: Internal wiki or shared drive (e.g., Confluence, Notion, SharePoint)

### Knowledge Base Structure

```
Insa SOC Knowledge Base/
├── Vulnerability Patterns/
│   ├── Common False Positives
│   ├── Critical CVEs (prioritized list)
│   ├── OT/ICS Vulnerabilities (industrial environments)
│   └── Web Application Vulnerabilities
├── Client-Specific Notes/
│   ├── [Client A]/
│   │   ├── Environment Details
│   │   ├── Accepted Risks
│   │   ├── Contact Information
│   │   └── Special Considerations
│   ├── [Client B]/
│   └── ...
├── Incident Playbooks/
│   ├── Ransomware Response
│   ├── Data Breach Response
│   ├── Insider Threat Investigation
│   └── DDoS Mitigation
├── Tool Documentation/
│   ├── DefectDojo Tips and Tricks
│   ├── AI Triage System Overview
│   ├── GroupMQ Usage
│   └── Scanner Configuration
├── Templates/
│   ├── Client Notification Emails
│   ├── Incident Reports
│   ├── Quarterly Review Presentations
│   └── Shift Handoff Notes
└── Lessons Learned/
    ├── Incident Post-Mortems
    ├── SLA Breach Root Causes
    └── Process Improvements
```

### Analyst Responsibilities

**When to Update Knowledge Base**:
- Encountered new false positive pattern → Add to "Common False Positives"
- Resolved unique/complex finding → Document solution
- Completed incident response → Write lessons learned
- Identified process improvement → Document and share
- Client provided feedback → Update client-specific notes

**How to Contribute** (5 minutes):
```
1. Identify knowledge to share:
   - New FP pattern: "SQL injection in test files (ending with .test.php)"
   - Complex finding: "CVE-2023-12345 false positive on Debian patched systems"
   - Incident lesson: "Ransomware: Always check for secondary payloads"

2. Navigate to appropriate section in knowledge base

3. Create new article:
   Title: [Descriptive title]
   Date: [Today]
   Author: [Your Name]
   Category: [Vulnerability/Client/Incident/Tool/etc.]

   Content template:
   ---
   ## Summary
   [Brief 1-2 sentence description]

   ## Details
   [Comprehensive explanation]

   ## Detection
   [How to identify this pattern/issue]

   ## Resolution
   [Step-by-step solution]

   ## Prevention
   [How to avoid in future]

   ## Related
   [Links to similar articles, Jira tickets, DefectDojo findings]
   ---

4. Tag article with keywords (for searchability):
   Tags: false-positive, sql-injection, test-files, web-app

5. Share with team:
   - Post to Slack #soc-knowledge: "New KB article: [link] - [brief summary]"
```

**Example Knowledge Base Article**:
```
Title: False Positive - SQL Injection in WordPress Login Page
Date: 2025-10-11
Author: Alice Smith
Category: Vulnerability Patterns / Common False Positives

## Summary
Semgrep scanner frequently reports SQL injection in WordPress wp-login.php,
but this is a false positive when WordPress core is up to date and using
prepared statements.

## Details
Semgrep's generic SQL injection rule triggers on SQL keywords in wp-login.php
even though WordPress uses $wpdb->prepare() which safely escapes user input.

This false positive has been seen in:
- WordPress 5.x and 6.x
- Various themes/plugins
- Both self-hosted and managed WordPress

## Detection
Finding characteristics:
- Title: "SQL Injection in wp-login.php" or similar
- Scanner: Semgrep
- CWE: CWE-89 (SQL Injection)
- Code line: Around line 450-500 in wp-login.php
- Pattern: SQL keywords in variable assignment (e.g., $sql = "SELECT...")

## Resolution
1. Verify WordPress version:
   - If WordPress >= 5.0: False positive (uses prepared statements)
   - If WordPress < 5.0: Recommend upgrade (security best practice)

2. Close finding in DefectDojo:
   - Status: "Closed - False Positive"
   - Comment: "WordPress uses prepared statements ($wpdb->prepare) which
     prevents SQL injection. Semgrep rule is generic and does not account
     for framework-specific protections."

3. Override AI decision (if AI marked as valid):
   - Check "Override AI Decision"
   - AI learning engine will adjust confidence for similar findings

## Prevention
- Update AI learning patterns:
  * Add pattern: "WordPress wp-login.php + Semgrep = likely FP"
  * Reduce confidence for this pattern by 20%

- Client-specific:
  * For WordPress-heavy clients, adjust Semgrep rules to exclude wp-login.php
  * Or switch to WordPress-specific scanner (WPScan)

## Related
- DefectDojo Finding: #12345 (example)
- Semgrep Rule: generic-sql-injection.yaml
- WordPress Security Documentation: https://wordpress.org/support/article/hardening-wordpress/
```

### Monthly Knowledge Base Review

**SOC Manager Responsibility** (30 minutes):
```
1. Review KB statistics:
   - Articles added this month: [X]
   - Most viewed articles: [list]
   - Stale articles (not updated in 6+ months): [list]

2. Identify gaps:
   - New vulnerability types not documented?
   - Client patterns not captured?
   - Analyst questions that could be KB articles?

3. Assign article updates:
   - Stale articles → Assign analyst to review and update
   - New topics → Assign analyst to create article

4. Share highlights:
   - Post to #soc-team: "KB Update: New articles this month [links]. Most helpful: [article]."
```

---

## Shift Handoff Workflow

**Duration**: 15 minutes (end of shift)

**Purpose**: Ensure continuity between shifts and no critical items are missed.

### Checklist

- [ ] **Step 1: Summarize Shift Activity** (5 minutes)
  ```
  Review your shift:
  - Critical findings reviewed: [count]
  - High findings reviewed: [count]
  - AI overrides: [count]
  - Client communications: [count]
  - Incidents: [count and status]
  - SLA issues: [any breaches or at-risk findings?]

  Note any outstanding items:
  - Open Jira tickets requiring follow-up
  - Clients awaiting response
  - At-risk SLA findings (< 4 hours)
  - AI agent issues (if any)
  ```

- [ ] **Step 2: Post Handoff Note to Slack** (5 minutes)
  ```
  Channel: #soc-handoff

  Template:
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  📋 Shift Handoff - [Date] [Shift Name]
  Analyst: [Your Name] → [Next Analyst Name]
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  🚨 **CRITICAL ITEMS** (Immediate attention required):
  [If none, write "None"]

  Example:
  - Client ABC: Critical SQLi in production app (Finding #456, Jira: SOC-789)
    * Client notified at 2:30 PM, no response yet
    * SLA deadline: 6:30 PM (4 hours remaining)
    * ACTION NEEDED: Follow up with client in 30 min if no response

  ⚠️ **HIGH PRIORITY**:
  [If none, write "None"]

  Example:
  - Client XYZ: 5 High findings from Trivy scan (Findings #461-465)
    * AI triaged, verified 3 valid, 2 FP
    * Client notified via daily report
    * No immediate action needed, tracking in Jira SOC-790

  📊 **SHIFT METRICS**:
  - Findings reviewed: [X]
  - AI overrides: [Y] ([Z]% of reviewed)
  - Client communications: [X emails, Y Slack messages]
  - SLA status: [X on-track, Y at-risk, Z breached]
  - AI accuracy today: [X]% (based on spot checks)

  🤖 **AI AGENT STATUS**:
  ✅ Running normally
  [OR]
  ⚠️ [Describe any issues, e.g., "Restarted at 3 PM due to timeout errors, now stable"]

  📝 **NOTES**:
  [Any other context next shift should know]

  Example:
  - GroupMQ scan queue depth was high (150 jobs) at start of shift, cleared by 1 PM
  - Client ABC requested SLA extension for Finding #456, approved until tomorrow 6 PM

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Next shift: Please acknowledge with ✅ reaction
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ```

- [ ] **Step 3: Update Jira Tickets** (3 minutes)
  ```
  For each open ticket you're working on:

  1. Add status update comment:
     "Shift handoff: [Summary of progress]. Next steps: [What needs to be done]."

  2. If handoff needed:
     - Reassign to next shift analyst OR
     - Leave assigned to you (if you'll continue tomorrow) and add comment for next shift awareness

  3. If ticket can be closed:
     - Close it now (don't leave for next shift)
     - Add resolution comment
  ```

- [ ] **Step 4: Verify AI Agent Health** (2 minutes)
  ```bash
  # Quick final check
  sudo systemctl status defectdojo-agent.service
  tail -n 20 /var/log/defectdojo_agent.log

  # If any issues, document in handoff note and alert SOC manager
  ```

- [ ] **Step 5: Await Acknowledgment** (within 30 minutes)
  ```
  Wait for next shift analyst to:
  - React with ✅ to your handoff note in Slack
  - Reply with any clarifying questions

  If no acknowledgment within 30 minutes:
  - Ping next analyst directly: "@[analyst] - please confirm handoff"
  - If still no response, alert SOC manager
  ```

### Critical Incident Handoff (Special Procedure)

**If active incident in progress during shift change**:

- [ ] **Schedule Handoff Call** (15 minutes)
  ```
  1. Instead of Slack-only handoff, schedule Zoom/phone call
  2. Invite: Outgoing analyst, incoming analyst, SOC manager
  3. Duration: 15 minutes
  ```

- [ ] **Prepare Incident Briefing** (5 minutes before call)
  ```
  Document to share:
  - Client name
  - Incident summary (what happened?)
  - Timeline (chronological events)
  - Current status (containment, investigation, eradication, recovery?)
  - Evidence collected (logs, files, screenshots)
  - Client communications (who have you talked to? what did they say?)
  - Next steps (what needs to happen next? when?)
  - Jira ticket link
  - Slack #incident-[client]-[date] channel
  ```

- [ ] **Conduct Handoff Call**
  ```
  Agenda:
  1. Outgoing analyst: Present incident briefing (5 min)
  2. Incoming analyst: Ask clarifying questions (5 min)
  3. Confirm understanding: Incoming analyst summarizes situation back (3 min)
  4. Transfer ownership: Reassign Jira ticket, update incident channel (2 min)
  ```

- [ ] **Post-Call Actions**
  ```
  Outgoing analyst:
  - Transfer Jira ticket ownership to incoming analyst
  - Post to #incident-[client]-[date]: "[Incoming analyst] is now leading this incident response."
  - Stay available for 1 hour after handoff for questions

  Incoming analyst:
  - Review all documentation
  - Contact client within 30 minutes to introduce yourself and confirm continuity
  - Post to #incident-[client]-[date]: "I've taken over incident response. Current status: [brief summary]."
  ```

---

## Appendix: Quick Reference Commands

### DefectDojo

```bash
# SSH to iac1
ssh 100.100.101.1

# Check DefectDojo service
sudo systemctl status defectdojo

# View DefectDojo logs
sudo docker logs -f defectdojo-uwsgi-1

# Access DefectDojo shell (for manual operations)
sudo docker exec -it defectdojo-uwsgi-1 bash
cd /app
python manage.py shell
```

### AI Agent

```bash
# Check AI agent service
sudo systemctl status defectdojo-agent.service

# View AI agent logs (live)
sudo journalctl -u defectdojo-agent -f

# View AI agent logs (recent)
tail -f /var/log/defectdojo_agent.log

# Restart AI agent (if needed)
sudo systemctl restart defectdojo-agent.service

# Query learning database
sqlite3 /var/lib/defectdojo/learning.db "SELECT * FROM decisions ORDER BY timestamp DESC LIMIT 10;"

# Check AI accuracy (last 24 hours)
sqlite3 /var/lib/defectdojo/learning.db \
  "SELECT
     COUNT(*) as total,
     SUM(CASE WHEN outcome='correct' THEN 1 ELSE 0 END) as correct,
     ROUND(SUM(CASE WHEN outcome='correct' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as accuracy_pct
   FROM decisions
   WHERE timestamp > datetime('now', '-24 hours');"
```

### GroupMQ

```bash
# Connect to GroupMQ (Redis-compatible)
redis-cli -p 6379

# Check queue depths
redis-cli -p 6379 LLEN scans/queued/client_acme
redis-cli -p 6379 LLEN triage/pending/client_acme

# View queue contents (first 10 items)
redis-cli -p 6379 LRANGE scans/queued/client_acme 0 10

# Clear queue (use with caution!)
redis-cli -p 6379 DEL scans/queued/client_acme
```

### Wazuh

```bash
# Check Wazuh agent on iac1
sudo systemctl status wazuh-agent

# View Wazuh alerts
sudo tail -f /var/ossec/logs/alerts/alerts.log

# Search for specific alert
sudo grep "192.168.1.50" /var/ossec/logs/alerts/alerts.log
```

---

**END OF DOCUMENT**

**Document Classification**: CONFIDENTIAL - INTERNAL USE ONLY
**Insa Automation Corp - SOC Analyst Workflows**
**Version**: 1.0
**Date**: October 12, 2025
