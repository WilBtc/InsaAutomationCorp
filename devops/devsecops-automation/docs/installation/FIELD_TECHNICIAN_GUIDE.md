# Field Technician Guide - Managed Industrial SOC Deployment

**Insa Automation Corp - DevSecOps Platform**
**Version**: 1.0
**Last Updated**: October 11, 2025
**Purpose**: Complete guide for on-site SOC deployment by field technicians

---

## Overview

This guide covers the complete on-site deployment process for Insa Managed Industrial SOC services. Typical deployment timeline: **3 days on-site** plus 1 day remote validation.

### Deployment Scope
- Jump box installation in customer DMZ
- Agent deployment across OT/IT assets
- Network configuration and firewall rules
- Integration testing and validation
- Knowledge transfer to customer staff
- 24-hour burn-in monitoring

---

## Pre-Deployment Phase (1 Week Before)

### 1. Customer Documentation Review
- [ ] Review customer network diagram
- [ ] Identify all assets for monitoring (from asset inventory)
- [ ] Confirm DMZ location for jump box
- [ ] Verify firewall approval process
- [ ] Identify customer IT/OT contacts
- [ ] Review safety system list (DO NOT TOUCH)
- [ ] Confirm site access requirements

### 2. Technical Preparation
- [ ] Download latest agent packages for all customer OS types
- [ ] Generate TLS certificates for jump box
- [ ] Prepare configuration templates with customer-specific settings
- [ ] Test all installation USB drives
- [ ] Verify remote access to Insa SOC platform
- [ ] Review sector-specific compliance requirements (FDA, NERC-CIP, etc.)
- [ ] Prepare rollback plan

### 3. Equipment Check
**See**: `INSTALLATION_KIT_CONTENTS.md` for complete list
- [ ] Jump box hardware (tested and imaged)
- [ ] Network cables (various lengths)
- [ ] USB drives with agent installers
- [ ] Console cables and adapters
- [ ] Laptop with admin tools
- [ ] Customer deliverables binder
- [ ] Emergency contact list

### 4. Travel Preparation
- [ ] Book flights and hotel near customer site
- [ ] Rent car if needed
- [ ] Pack personal PPE (safety glasses, steel-toe boots if required)
- [ ] Print hardcopy of all procedures (in case of network issues)
- [ ] Bring backup laptop battery and chargers
- [ ] Customer site address and parking instructions
- [ ] Emergency contact numbers (customer + Insa management)

### 5. Customer Communication (3 Days Before)
Send email to customer with:
- [ ] Arrival date/time
- [ ] Technician name and photo (security badge)
- [ ] List of systems we'll access
- [ ] Expected downtime (if any) - typically ZERO
- [ ] Firewall rules needed (provide list)
- [ ] DMZ port/VLAN requirements
- [ ] Request for badge/escort if needed
- [ ] Day 1 meeting agenda

---

## Day 1: Jump Box Installation and Network Setup

### Morning (8:00 AM - 12:00 PM)

#### 8:00 - Arrival and Safety Briefing
- [ ] Check in with customer security
- [ ] Attend site safety briefing
- [ ] Get badge and escort assignment
- [ ] Review site emergency procedures
- [ ] Identify muster points
- [ ] Confirm PPE requirements for each area
- [ ] Meet primary IT/OT contacts

#### 9:00 - Network Assessment
- [ ] Verify DMZ physical location
- [ ] Check power availability (UPS preferred)
- [ ] Confirm network connectivity (switch port)
- [ ] Document VLAN/IP assignment
- [ ] Test internet access from DMZ
- [ ] Verify firewall rules are in place (or schedule with NetSec)
- [ ] Document actual network topology vs. plan

#### 10:00 - Jump Box Installation
**See**: `JUMP_BOX_DEPLOYMENT.md` for detailed steps

- [ ] Mount jump box in rack (2U space)
- [ ] Connect power (redundant if available)
- [ ] Connect network cable to DMZ switch
- [ ] Connect console cable for initial setup
- [ ] Power on and verify POST
- [ ] Configure static IP or DHCP reservation
- [ ] Set hostname: `insa-jumpbox-[customer-abbreviation]`
- [ ] Configure NTP to customer time source
- [ ] Install TLS certificates

#### 11:00 - Network Connectivity Testing
- [ ] Ping default gateway
- [ ] Ping customer DNS servers
- [ ] Test outbound connectivity to Insa SOC platform (100.100.101.1:8082)
- [ ] Verify TLS handshake
- [ ] Test reverse SSH tunnel (if required)
- [ ] Document latency and bandwidth
- [ ] Configure jump box monitoring agent

### Afternoon (1:00 PM - 5:00 PM)

#### 1:00 - Jump Box Service Configuration
- [ ] Start agent relay service
- [ ] Configure log aggregation
- [ ] Set up local SQLite cache (for offline resilience)
- [ ] Test DefectDojo integration
- [ ] Verify time sync (critical for SIEM)
- [ ] Enable jump box self-monitoring
- [ ] Document jump box credentials in customer vault

#### 2:00 - Asset Inventory Validation
- [ ] Meet with customer IT/OT teams
- [ ] Walk through asset list
- [ ] Identify any missing systems
- [ ] **CRITICAL**: Confirm safety systems to EXCLUDE (see `SAFETY_SYSTEM_EXCLUSION.md`)
- [ ] Prioritize assets (Tier 1: critical first)
- [ ] Schedule access to each system
- [ ] Get admin credentials (or schedule shadow sessions)
- [ ] Document any special access procedures (air-gapped systems, etc.)

#### 3:00 - First Agent Deployment (Test System)
- [ ] Select low-risk test system (IT workstation preferred)
- [ ] Install agent using appropriate method (Windows/Linux/embedded)
- [ ] Verify agent starts successfully
- [ ] Check connectivity to jump box
- [ ] Verify data appears in DefectDojo within 5 minutes
- [ ] Monitor CPU/memory impact (< 5% target)
- [ ] Test agent self-update mechanism
- [ ] Document any issues

#### 4:00 - Day 1 Wrap-Up
- [ ] Brief customer on progress
- [ ] Schedule Day 2 access to production systems
- [ ] Document any blockers (firewall rules, credentials, etc.)
- [ ] Upload field notes to Insa project portal
- [ ] Email status to Insa project manager
- [ ] Plan Day 2 activities

---

## Day 2: Mass Agent Deployment

### Morning (8:00 AM - 12:00 PM)

#### 8:00 - Day 2 Kickoff
- [ ] Brief meeting with customer team
- [ ] Review Day 1 test results
- [ ] Confirm access to production systems
- [ ] Review deployment order (critical systems last for safety)
- [ ] Assign customer shadow if required

#### 8:30 - IT Asset Deployment (Batch 1)
**See**: `AGENT_DEPLOYMENT_CHECKLIST.md` for detailed steps per OS

- [ ] Windows Servers (Group Policy deployment if available)
- [ ] Linux servers (Ansible/SSH if available, else manual)
- [ ] Network devices (SNMP monitoring only - no agents)
- [ ] Verify each agent checks in
- [ ] Monitor DefectDojo for new findings

#### 10:00 - OT Asset Deployment (Batch 2)
**CAUTION**: Extra care required. Read-only monitoring where possible.

- [ ] HMI/SCADA servers (Windows-based, treat as production)
- [ ] Engineering workstations
- [ ] Historian servers
- [ ] OPC servers
- [ ] Document any systems that refuse agent (firewalls, whitelisting)

### Afternoon (1:00 PM - 5:00 PM)

#### 1:00 - Embedded/IoT Device Monitoring
- [ ] IIoT gateways (if Linux-based, install agent)
- [ ] PLCs (network monitoring only via jump box packet capture)
- [ ] RTUs (network monitoring only)
- [ ] Industrial firewalls (SNMP if supported)
- [ ] Verify passive monitoring does not disrupt operations

#### 3:00 - Integration Testing
- [ ] Verify all agents report to jump box
- [ ] Check DefectDojo shows all assets
- [ ] Test alert routing (trigger test alert)
- [ ] Verify email alerts to customer SOC contact
- [ ] Test finding triage workflow
- [ ] Generate test compliance report
- [ ] Monitor jump box resource usage

#### 4:00 - Day 2 Wrap-Up
- [ ] Review deployment status (target: 80%+ complete)
- [ ] Document any systems that failed or were excluded
- [ ] Schedule Day 3 activities (validation + knowledge transfer)
- [ ] Brief customer on preliminary findings
- [ ] Upload logs and notes to Insa portal

---

## Day 3: Validation, Knowledge Transfer, and Handoff

### Morning (8:00 AM - 12:00 PM)

#### 8:00 - Final Agent Deployment
- [ ] Complete any remaining systems from Day 2
- [ ] Re-attempt any failed installations
- [ ] Document permanent exclusions with justification
- [ ] Achieve 90%+ coverage of planned assets

#### 9:00 - System Validation
**See**: `AGENT_DEPLOYMENT_CHECKLIST.md` Section 6 for validation tests

- [ ] Run health check on all agents
- [ ] Verify log ingestion rates (DefectDojo should show activity)
- [ ] Test compliance scans (CIS benchmarks)
- [ ] Generate sample vulnerability report
- [ ] Test incident response workflow (simulated critical finding)
- [ ] Verify backup/redundancy (jump box failover if configured)
- [ ] Performance check: no system shows > 5% CPU from agent

#### 10:30 - Customer Training Session 1 (IT Team)
**Duration**: 90 minutes

1. **DefectDojo Platform Overview** (30 min)
   - Login and dashboard tour
   - Finding severity levels
   - Triage workflow
   - Reporting capabilities

2. **Agent Management** (30 min)
   - How to check agent status
   - Reading agent logs
   - Troubleshooting connectivity issues
   - Agent update process

3. **Jump Box Administration** (30 min)
   - SSH access and credentials
   - Log locations
   - Service restart procedures
   - When to call Insa support

### Afternoon (1:00 PM - 5:00 PM)

#### 1:00 - Customer Training Session 2 (OT/Security Team)
**Duration**: 90 minutes

1. **OT-Specific Monitoring** (30 min)
   - ICS/SCADA protocol detection
   - Anomaly detection for OT
   - Safety system exclusions (reminder)
   - Compliance reporting (NERC-CIP, FDA 21 CFR Part 11, etc.)

2. **Incident Response** (30 min)
   - Alert escalation process
   - How Insa SOC responds to critical findings
   - Customer responsibilities
   - Communication channels (email, phone, portal)

3. **Compliance and Reporting** (30 min)
   - Scheduled reports (weekly, monthly)
   - Ad-hoc report generation
   - Audit evidence collection
   - Regulatory mapping (sector-specific)

#### 2:30 - 24-Hour Burn-In Start
- [ ] Enable full monitoring (no longer in test mode)
- [ ] Set alert thresholds to production levels
- [ ] Monitor for any performance issues
- [ ] Customer team shadows Insa SOC for first alerts
- [ ] Document baseline behavior

#### 3:00 - Documentation Handoff
Provide customer with binder containing:
- [ ] Network diagram (as-built)
- [ ] Asset inventory with agent status
- [ ] Jump box configuration details
- [ ] Firewall rules (approved and implemented)
- [ ] Credentials (in sealed envelope for customer vault)
- [ ] Emergency contact list
- [ ] Escalation procedures
- [ ] Signed acceptance checklist

#### 4:00 - Final Walkthrough
- [ ] Review all systems with customer
- [ ] Answer any remaining questions
- [ ] Confirm customer satisfaction
- [ ] Schedule 1-week follow-up call
- [ ] Provide direct contact for next 48 hours
- [ ] Get customer sign-off on acceptance form

#### 4:30 - Departure Checklist
- [ ] Remove personal tools/files from customer systems
- [ ] Return any borrowed equipment
- [ ] Turn in badge
- [ ] Thank customer team
- [ ] Pack equipment
- [ ] Upload final field notes to Insa portal
- [ ] Email completion report to Insa PM and customer

---

## Post-Deployment Phase (Remote)

### Day 4: Remote Monitoring
- [ ] Monitor all agents from Insa SOC (not on-site)
- [ ] Check for any overnight alerts
- [ ] Verify burn-in period completed successfully
- [ ] Be available for customer questions (phone/email)
- [ ] Document any issues in project log

### Week 1 Follow-Up (Day 7)
- [ ] Schedule call with customer IT/OT leads
- [ ] Review first week of findings
- [ ] Adjust alert thresholds if needed
- [ ] Answer questions about reports
- [ ] Confirm customer is comfortable with platform
- [ ] Transition to standard Insa SOC support

### 30-Day Check-In
- [ ] Generate 30-day summary report
- [ ] Customer satisfaction survey
- [ ] Identify any additional assets to monitor
- [ ] Review compliance posture
- [ ] Lessons learned session with customer

---

## Emergency Procedures

### Critical System Impact
If agent causes any production impact:
1. **IMMEDIATELY** shut down agent: `systemctl stop insa-agent` or `net stop InsaAgent`
2. Notify customer IT/OT lead
3. Call Insa SOC: [Phone number]
4. Document incident in field notes
5. See `ROLLBACK_PROCEDURE.md` if necessary

### Safety System Proximity
If you realize an agent was installed on or near a safety system:
1. **STOP** immediately
2. Notify customer safety officer
3. Call Insa project manager
4. Follow `SAFETY_SYSTEM_EXCLUSION.md` procedures
5. Uninstall agent if required
6. Document near-miss in incident report

### Personal Safety
If you feel unsafe or observe unsafe conditions:
1. **STOP WORK** immediately
2. Exit to safe location
3. Notify customer site supervisor
4. Call Insa management
5. Do not resume until safety is confirmed

### Network Outage
If jump box loses connectivity to Insa SOC:
1. Agents will cache data locally (up to 7 days)
2. Check jump box network connectivity
3. Verify firewall rules still in place
4. Contact customer NetSec team
5. Call Insa SOC to report outage
6. Data will sync automatically when connectivity restored

---

## Communication Protocols

### Daily Status Updates
Send email to:
- Insa Project Manager
- Customer IT/OT Lead
- Insa SOC Manager

**Template**:
```
Subject: [Customer Name] SOC Deployment - Day [X] Status

Deployment Progress:
- Jump Box: [Status]
- Agents Deployed: [X] of [Y] planned
- Systems Validated: [X] of [Y]
- Blockers: [List any issues]

Tomorrow's Plan:
- [Activity 1]
- [Activity 2]

Risks/Concerns:
- [Any red flags]

Technician: [Your Name]
Date: [YYYY-MM-DD]
```

### Customer Communication
- **Always professional and calm**, even under stress
- **Avoid FUD** (Fear, Uncertainty, Doubt) - focus on solutions
- **Translate technical to business impact** when speaking to executives
- **Escalate early** if you sense customer concern
- **Document all commitments** made to customer in field notes

### Insa Management Escalation
Call Insa Project Manager if:
- Customer requests scope change
- Safety concern identified
- Deployment will exceed 3 days
- Customer dissatisfaction detected
- Technical blocker cannot be resolved in 4 hours
- Any incident that could impact Insa reputation

---

## Quality Checklist (Before You Leave Site)

### Technical Validation
- [ ] All agents reporting to jump box
- [ ] Jump box reporting to Insa SOC
- [ ] DefectDojo shows all assets
- [ ] Test alert successfully sent and received
- [ ] No agents consuming > 5% CPU
- [ ] No network performance degradation
- [ ] Compliance scan completed successfully
- [ ] Backup/failover tested (if configured)

### Documentation
- [ ] Network diagram updated with as-built
- [ ] All credentials documented and secured
- [ ] Asset inventory matches reality
- [ ] Firewall rules documented
- [ ] Customer binder complete and handed off
- [ ] Field notes uploaded to Insa portal
- [ ] Lessons learned documented

### Customer Satisfaction
- [ ] Customer IT lead verbally confirms satisfaction
- [ ] Customer OT lead verbally confirms no operational impact
- [ ] Training completed (IT and OT teams)
- [ ] Questions answered
- [ ] Acceptance form signed
- [ ] Follow-up call scheduled

### Safety
- [ ] No safety systems touched
- [ ] No near-miss incidents
- [ ] All safety procedures followed
- [ ] PPE requirements met
- [ ] Site safety rules followed

---

## Tips for Success

### Building Customer Trust
1. **Arrive early** - shows professionalism
2. **Listen more than you talk** - understand customer concerns
3. **Under-promise, over-deliver** - be conservative with timelines
4. **Show, don't just tell** - demonstrate the platform in real-time
5. **Be transparent** - admit when something goes wrong and fix it
6. **Respect OT culture** - they prioritize safety and uptime over security

### Technical Efficiency
1. **Automate where possible** - use scripts for mass deployment
2. **Test on IT first** - lower risk than OT
3. **Work during customer business hours** - easier to get help
4. **Bring redundant equipment** - cables, USB drives, etc.
5. **Document as you go** - don't wait until Day 3
6. **Use checklists** - prevents missed steps

### Common Pitfalls to Avoid
1. **Rushing deployment** - speed causes mistakes
2. **Skipping safety reviews** - could cause catastrophic impact
3. **Poor communication** - customer surprises lead to dissatisfaction
4. **Assuming network access** - always verify firewall rules first
5. **Ignoring OT team input** - they know their systems best
6. **Forgetting credentials** - document in customer vault before you leave

---

## Support Contacts

| Contact | Phone | Email | Availability |
|---------|-------|-------|--------------|
| Insa SOC | TBD | soc@insaing.com | 24/7 |
| Project Manager | TBD | pm@insaing.com | M-F 8-6 |
| Technical Support | TBD | support@insaing.com | M-F 8-6 |
| Emergency Escalation | TBD | emergency@insaing.com | 24/7 |

---

**Document Version**: 1.0
**Last Updated**: October 11, 2025
**Owner**: Insa Automation Corp
**Classification**: Internal Use - Field Technicians Only

---

*Made by Insa Automation Corp for OpSec Excellence*
