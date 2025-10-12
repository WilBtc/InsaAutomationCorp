# Field Technician Installation Kit - Complete Documentation

**Insa Automation Corp - Managed Industrial SOC**
**Version**: 1.0
**Last Updated**: October 11, 2025

---

## Overview

This directory contains comprehensive field installation guides for deploying Insa Managed Industrial SOC services at customer sites. These guides are designed for field technicians traveling to customer facilities to install jump boxes and monitoring agents.

**Typical Deployment**: 3 days on-site + 1 day remote validation

---

## Document Index

### 1. FIELD_TECHNICIAN_GUIDE.md
**Purpose**: Master guide for complete on-site deployment
**Size**: 17 KB | 650+ lines
**Read Time**: 30 minutes

**Contents**:
- Pre-deployment checklist (1 week before)
- Day-by-day installation plan (3 days)
- Customer communication protocols
- Safety requirements and PPE
- Training delivery procedures
- Post-deployment validation
- Emergency procedures

**When to use**: Read completely before first deployment, reference daily during deployment

---

### 2. INSTALLATION_KIT_CONTENTS.md
**Purpose**: Complete equipment and software inventory
**Size**: 17 KB | 650+ lines
**Read Time**: 20 minutes

**Contents**:
- Jump box hardware specifications
- Network equipment and tools
- Software installers (Windows, Linux, embedded)
- Customer deliverables binder contents
- Personal equipment and PPE
- Kit maintenance procedures
- Sector-specific variations (pharma, energy, etc.)

**When to use**: 1 week before deployment (kit preparation), verify all items present before travel

---

### 3. JUMP_BOX_DEPLOYMENT.md
**Purpose**: Step-by-step jump box installation in customer DMZ
**Size**: 25 KB | 950+ lines
**Read Time**: 40 minutes

**Contents**:
- Pre-deployment network requirements
- Physical installation (rack mounting)
- OS configuration (networking, security)
- Software installation and certificates
- Testing and validation
- Troubleshooting common issues
- Maintenance procedures

**When to use**: Day 1 of deployment, reference during jump box installation

---

### 4. AGENT_DEPLOYMENT_CHECKLIST.md
**Purpose**: Comprehensive agent installation procedures per OS
**Size**: 31 KB | 1,200+ lines
**Read Time**: 45 minutes

**Contents**:
- Asset inventory validation
- Windows deployment (GPO and manual)
- Linux deployment (Ansible and manual)
- Embedded/IoT device monitoring
- OT-specific systems (HMI, SCADA, historian)
- Performance validation
- Troubleshooting

**When to use**: Day 2-3 of deployment, reference for each agent installation

---

### 5. SAFETY_SYSTEM_EXCLUSION.md ⚠️ CRITICAL
**Purpose**: Identify and avoid safety systems during deployment
**Size**: 18 KB | 700+ lines
**Read Time**: 30 minutes

**Contents**:
- What is a safety system (SIS, ESD, F&G, BMS, etc.)
- How to identify safety systems (visual, network, vendor)
- Safety system identification checklist
- Pre-deployment safety review process
- What to do if agent installed on safety system (emergency procedures)
- Alternative monitoring methods (network-level, SNMP)
- Regulatory considerations (OSHA, EPA, NERC-CIP, FDA, NRC)

**When to use**:
- **REQUIRED READING** before every deployment
- Day 1 morning (safety briefing with customer)
- Before installing agent on any OT system

**⚠️ WARNING**: Failure to follow this guide can result in catastrophic incidents, regulatory violations, and criminal liability.

---

### 6. ROLLBACK_PROCEDURE.md
**Purpose**: Emergency agent and jump box removal procedures
**Size**: 28 KB | 1,100+ lines
**Read Time**: 40 minutes

**Contents**:
- When to initiate rollback (emergency vs. planned)
- Immediate impact mitigation (stop agents)
- Agent uninstallation (Windows, Linux, embedded)
- Jump box decommissioning
- Network cleanup (firewall rules, DNS)
- Verification and testing
- Documentation and customer handoff
- Lessons learned process

**When to use**:
- When agent causes production impact
- When customer cancels contract
- When safety concern discovered
- Keep accessible during deployment (just in case)

---

## Quick Start Guide

### First-Time Field Technician
1. **Week before first deployment**:
   - [ ] Read all 6 documents (4 hours)
   - [ ] Complete Insa "Safety System Awareness" training (online, 1 hour)
   - [ ] Shadow experienced technician (recommended)
   - [ ] Verify installation kit inventory

2. **1 week before deployment**:
   - [ ] Review `FIELD_TECHNICIAN_GUIDE.md` Pre-Deployment Phase
   - [ ] Request customer safety system list
   - [ ] Prepare installation kit per `INSTALLATION_KIT_CONTENTS.md`
   - [ ] Generate customer-specific TLS certificates
   - [ ] Book travel and accommodations

3. **Day 1 (On-Site)**:
   - [ ] Safety briefing with customer
   - [ ] Review safety system list (`SAFETY_SYSTEM_EXCLUSION.md`)
   - [ ] Install jump box (`JUMP_BOX_DEPLOYMENT.md`)
   - [ ] Deploy first test agent (`AGENT_DEPLOYMENT_CHECKLIST.md` Section 1 or 2)

4. **Day 2 (On-Site)**:
   - [ ] Mass agent deployment (`AGENT_DEPLOYMENT_CHECKLIST.md`)
   - [ ] IT systems first, OT systems second (lower risk first)
   - [ ] Verify each agent checks in to DefectDojo

5. **Day 3 (On-Site)**:
   - [ ] Complete remaining agent deployments
   - [ ] System validation (`AGENT_DEPLOYMENT_CHECKLIST.md` Section 5-6)
   - [ ] Customer training (2 sessions)
   - [ ] Documentation handoff
   - [ ] Get customer sign-off

6. **Day 4 (Remote)**:
   - [ ] Monitor from Insa SOC
   - [ ] Be available for customer questions
   - [ ] Upload final field notes

### Experienced Technician
**Use as reference during deployment**:
- Day 1: `JUMP_BOX_DEPLOYMENT.md`
- Day 2-3: `AGENT_DEPLOYMENT_CHECKLIST.md`
- Always: `SAFETY_SYSTEM_EXCLUSION.md` (before touching any OT system)
- Emergency: `ROLLBACK_PROCEDURE.md`

---

## Deployment Process Flow

```
Pre-Deployment (1 week before)
├─ Review customer network diagram
├─ Request safety system list ⚠️
├─ Prepare installation kit
├─ Generate TLS certificates
└─ Travel arrangements

Day 1: Jump Box + Foundation
├─ Arrival and safety briefing
├─ Safety system review ⚠️
├─ Jump box installation (DMZ)
├─ Network connectivity testing
└─ First test agent deployment

Day 2: Mass Agent Deployment
├─ IT asset deployment (Windows GPO, Linux Ansible)
├─ OT asset deployment (manual, extra caution ⚠️)
└─ Integration testing

Day 3: Validation + Knowledge Transfer
├─ Final agent deployments
├─ System validation (health, performance, compliance)
├─ Customer training (2 sessions: IT team, OT team)
├─ Documentation handoff
└─ Customer sign-off

Day 4: Remote Monitoring
├─ Monitor from Insa SOC
├─ 24-hour burn-in period
└─ Transition to standard support

Week 1: Follow-Up
└─ Review first week of findings with customer

30 Days: Check-In
└─ Customer satisfaction survey, adjust thresholds
```

---

## Key Safety Considerations

### NEVER Install Agents On:
- [ ] Safety Instrumented Systems (SIS) - SIL rated
- [ ] Emergency Shutdown (ESD) systems
- [ ] Fire and Gas (F&G) detection systems
- [ ] Burner Management Systems (BMS)
- [ ] Safety PLCs (yellow/red colored)
- [ ] Any system labeled "Safety" or "Do Not Modify"
- [ ] Systems on separate safety networks

### Always Ask Before Installing:
- [ ] "Is this system safety-rated?"
- [ ] "Does this have a SIL rating?"
- [ ] "Is this required for emergency shutdown?"
- [ ] "Would failure cause injury or death?"

### If In Doubt:
- **STOP** immediately
- Ask customer safety engineer
- Do NOT proceed until written approval

**See**: `SAFETY_SYSTEM_EXCLUSION.md` for complete details

---

## Performance Targets

### Agent Performance
- CPU: < 5% (< 3% for OT systems)
- Memory: < 100MB (< 50MB for embedded)
- Network: < 10 KB/s per agent
- Telemetry interval: 60 seconds (IT), 300 seconds (OT)

### Jump Box Performance
- Throughput: 1,000 agents @ 1KB/min = ~17KB/s
- Latency: < 100ms agent-to-jump box, < 500ms jump box-to-SOC
- Cache: 7 days @ 1MB/min = ~10GB storage
- Availability: 99.9% uptime

### Deployment Success Metrics
- Agent deployment rate: 90%+ of planned assets
- Performance impact: < 5% CPU per agent
- Zero safety system touches
- Customer satisfaction: Signed acceptance form

---

## Troubleshooting Quick Reference

### Agent Won't Report to Jump Box
1. Check service running: `systemctl status insa-agent` (Linux) or `Get-Service InsaAgent` (Windows)
2. Check network connectivity: `nc -zv [JUMP_BOX_IP] 8443`
3. Check logs: `/var/log/insa-agent.log` or `C:\ProgramData\Insa\agent.log`
4. Verify PSK correct in config file
5. Check firewall rules (UFW on jump box, Windows Firewall on agent)

### Jump Box Can't Reach Insa SOC
1. Test connectivity: `ping 100.100.101.1` and `nc -zv 100.100.101.1 8082`
2. Check firewall rules (customer outbound rules)
3. Verify TLS certificate not expired: `openssl x509 -in /etc/insa/certs/jumpbox.crt -noout -dates`
4. Check logs: `sudo journalctl -u insa-heartbeat -n 100`

### Agent Using Too Much CPU
1. Check what's consuming: `top -p $(pgrep insa-agent)`
2. Reduce telemetry frequency in config: `interval = 300` (from 60)
3. Disable FIM if too intensive: `file_integrity_monitoring = no`
4. Restart agent and monitor for 15 minutes
5. If still high, contact Insa support

**See**: Each guide has detailed troubleshooting sections

---

## Customer Training Deliverables

### Training Session 1: IT Team (90 minutes)
**Topics**:
- DefectDojo platform overview (30 min)
- Agent management (30 min)
- Jump box administration (30 min)

**Materials** (in customer binder):
- DefectDojo quick start guide
- Agent troubleshooting flowchart
- Jump box admin procedures

### Training Session 2: OT/Security Team (90 minutes)
**Topics**:
- OT-specific monitoring (30 min)
- Incident response procedures (30 min)
- Compliance and reporting (30 min)

**Materials** (in customer binder):
- OT monitoring overview
- Incident escalation procedures
- Compliance report samples

---

## Documentation Standards

### Field Notes (Required Daily)
**Document**:
- Systems accessed (hostname, IP, actions taken)
- Agents deployed (success/failure)
- Issues encountered and resolutions
- Customer interactions (requests, concerns)
- Time spent per activity

**Upload to**: Insa project portal at end of each day

### Deployment Completion Report (Required)
**Include**:
- Deployment summary (totals, success rate)
- Network diagram (as-built)
- Asset inventory (with agent status)
- Outstanding items (if any)
- Customer sign-off (signature)
- Lessons learned

**Submit to**: Insa PM within 2 business days of completion

---

## Support Contacts

| Contact | Purpose | Availability |
|---------|---------|--------------|
| **Insa SOC** | Technical issues, production impact | 24/7 |
| **Project Manager** | Deployment questions, scope changes | M-F 8-6 |
| **Technical Support** | Agent issues, jump box issues | M-F 8-6 |
| **Emergency Escalation** | Safety concerns, critical incidents | 24/7 |

**Phone/Email**: See `FIELD_TECHNICIAN_GUIDE.md` Appendix or contact card in installation kit

---

## Revision History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2025-10-11 | Initial release - Complete field technician kit | Insa Automation Corp |

---

## Document Maintenance

### Review Schedule
- **Quarterly**: Review for technical accuracy, update software versions
- **Annually**: Major revision based on field feedback and lessons learned
- **As needed**: Update for regulatory changes, new sector requirements

### Feedback Process
Field technicians: Submit feedback via Insa project portal
- What worked well?
- What was unclear or missing?
- Suggestions for improvement

---

## License and Distribution

**Classification**: Internal Use - Insa Field Technicians Only
**Distribution**: Authorized Insa personnel only
**Copyright**: © 2025 Insa Automation Corp. All rights reserved.

**Do not distribute to**:
- Customers (provide customer-specific guides instead)
- Competitors
- Public forums or repositories

---

## Acknowledgments

This documentation set was developed by Insa Automation Corp DevSecOps team based on:
- Field deployment experience (50+ industrial facilities)
- Industry best practices (ISA/IEC 62443, NERC-CIP, FDA 21 CFR Part 11)
- Lessons learned from near-miss incidents
- Customer feedback and satisfaction surveys

Special thanks to field technicians who provided feedback during documentation review.

---

**Made by Insa Automation Corp for OpSec Excellence**

**Mission**: Deploy Managed Industrial SOC services safely, efficiently, and with zero safety system impact.

---

## Next Steps

**New Field Technician**:
1. Read this README completely
2. Read all 6 installation guides (4 hours)
3. Complete online safety training (1 hour)
4. Shadow experienced technician (1-2 deployments)
5. Solo deployment with PM oversight
6. Full autonomy after 3 successful deployments

**Experienced Technician**:
- Keep these guides accessible during deployments (laptop + printed backup)
- Review safety guide before every deployment
- Provide feedback for continuous improvement
- Mentor new technicians

**Project Manager**:
- Provide these guides to technicians 1 week before deployment
- Verify technician has completed safety training
- Review field notes daily during deployment
- Conduct lessons learned session after deployment

---

**Questions?** Contact Insa Technical Documentation Team: docs@insaing.com
