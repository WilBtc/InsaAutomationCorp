# Manufacturing Sector - Client Onboarding Playbook
**Insa Automation Corp | Industrial Security & Automation**
Version: 1.0 | Date: October 11, 2025

---

## Executive Summary

Manufacturing environments require specialized security approaches that balance production uptime with security monitoring. This playbook guides the onboarding process for discrete and process manufacturing facilities.

### Sector Characteristics
- **Critical Priority**: Production uptime (99.9%+ SLA)
- **Key Assets**: PLCs, SCADA, HMIs, robots, CNCs, vision systems
- **Common Protocols**: Modbus TCP/RTU, EtherNet/IP, Profinet, OPC-UA
- **Risk Profile**: Ransomware targeting production lines, intellectual property theft
- **Deployment Window**: Non-production hours or planned maintenance windows

---

## Phase 1: Pre-Sales Discovery

### Discovery Questionnaire

#### Production Environment
```yaml
Facility Profile:
  - Facility type: [ ] Discrete [ ] Process [ ] Hybrid
  - Production lines: _______
  - Shift schedule: [ ] 24/7 [ ] 2-shift [ ] 1-shift
  - Annual production value: $_______
  - Cost per hour of downtime: $_______

  Planned Maintenance Windows:
    - Frequency: [ ] Weekly [ ] Monthly [ ] Quarterly
    - Duration: _____ hours
    - Day/time: _____________
```

#### Manufacturing Assets Inventory
```yaml
PLCs (Programmable Logic Controllers):
  - Vendor: [ ] Allen-Bradley [ ] Siemens [ ] Schneider [ ] Mitsubishi [ ] Other
  - Models: _________________
  - Quantity: _____
  - Firmware versions: _______
  - Network segments: _______

SCADA Systems:
  - Software: [ ] WonderWare [ ] Ignition [ ] FactoryTalk [ ] WinCC [ ] Custom
  - Version: _______
  - Servers: _____
  - Clients: _____
  - Database: [ ] MS SQL [ ] MySQL [ ] Historian

HMIs (Human-Machine Interfaces):
  - Panel count: _____
  - Vendor: __________
  - Connection type: [ ] Ethernet [ ] Serial [ ] Wireless

Industrial Robots:
  - Vendor: [ ] Fanuc [ ] ABB [ ] KUKA [ ] Yaskawa [ ] Universal Robots
  - Quantity: _____
  - Controller IP range: _______

CNC Machines:
  - Quantity: _____
  - Networked: [ ] Yes [ ] No
  - Control system: _______

Vision/Quality Systems:
  - Vendor: _______
  - Integration: [ ] Standalone [ ] PLC integrated [ ] SCADA integrated
```

#### Network Infrastructure
```yaml
OT Network:
  - Flat network: [ ] Yes [ ] No
  - VLANs implemented: [ ] Yes [ ] No
  - Firewall between IT/OT: [ ] Yes [ ] No
  - Air-gapped systems: [ ] Yes [ ] No

  Network protocols in use:
    [ ] Modbus TCP (port 502)
    [ ] Modbus RTU (serial)
    [ ] EtherNet/IP (port 44818)
    [ ] Profinet (port 34964)
    [ ] OPC-UA (port 4840)
    [ ] DNP3 (port 20000)
    [ ] BACnet (port 47808)
    [ ] MQTT (port 1883/8883)

Remote Access:
  - VPN: [ ] Yes [ ] No - Vendor: _______
  - Remote desktop: [ ] Yes [ ] No
  - Vendor access: [ ] Yes [ ] No - Frequency: _______
  - Third-party integrators: [ ] Yes [ ] No
```

#### Safety Systems (CRITICAL)
```yaml
Safety Instrumented Systems (SIS):
  - Present: [ ] Yes [ ] No
  - Vendor: _______
  - Safety Integrity Level (SIL): [ ] SIL 1 [ ] SIL 2 [ ] SIL 3 [ ] SIL 4
  - MUST be excluded from active monitoring: [ ] Acknowledged

Emergency Shutdown Systems:
  - Location: _______
  - Network-connected: [ ] Yes [ ] No
  - Monitoring exclusion required: [ ] Yes [ ] No
```

#### Compliance Requirements
```yaml
Standards:
  [ ] ISO 27001 (Information Security)
  [ ] IEC 62443 (Industrial Cybersecurity)
  [ ] NIST CSF (Cybersecurity Framework)
  [ ] FDA 21 CFR Part 11 (Pharma/Medical)
  [ ] ITAR (Defense manufacturing)
  [ ] Industry-specific: _______

Audit Frequency:
  - Internal: [ ] Quarterly [ ] Annual
  - External: [ ] Annual [ ] Biennial
  - Regulator: _______
```

---

## Phase 2: Site Assessment

### Pre-Deployment Checklist

#### Week 1-2: Remote Assessment
```yaml
Documentation Review:
  [ ] Network diagrams (IT and OT)
  [ ] Asset inventory spreadsheet
  [ ] Firewall rule sets
  [ ] VPN configurations
  [ ] Maintenance schedules
  [ ] Incident response plan
  [ ] Business continuity plan

Remote Discovery (if permitted):
  [ ] Nmap passive scan (authorized)
  [ ] Protocol analyzer (read-only)
  [ ] SNMP walk (if available)
  [ ] Review DHCP/DNS logs
  [ ] Identify network segments
```

#### Week 3: On-Site Assessment (1-2 days)
```yaml
Physical Walkthrough:
  [ ] Production floor layout
  [ ] Control room location
  [ ] Server/network closets
  [ ] Wireless coverage areas
  [ ] Security camera coverage
  [ ] Badge access zones
  [ ] Emergency exits/assembly points

Asset Verification:
  [ ] Visual inspection of all PLCs
  [ ] HMI panel inventory
  [ ] Robot controller access
  [ ] SCADA server room
  [ ] Network switch locations
  [ ] Photograph all control panels (with permission)

Network Tap Points:
  [ ] Identify optimal SPAN/mirror port locations
  [ ] Core switch access
  [ ] Production line switches
  [ ] Power/cooling availability
  [ ] Physical security of tap locations

Interviews:
  [ ] Production manager (uptime requirements)
  [ ] Maintenance lead (change windows)
  [ ] IT/OT manager (network architecture)
  [ ] Plant manager (business priorities)
  [ ] Safety officer (exclusion zones)
```

---

## Phase 3: Network Diagram Template

### Manufacturing Network Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CORPORATE IT NETWORK                      │
│  (ERP, Email, Office PCs, Internet)                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  IT/OT Firewall │ ◄── MONITORING POINT 1
                    │  (IDS/IPS Here) │
                    └────────┬────────┘
                             │
┌─────────────────────────────┴────────────────────────────────────┐
│                      DMZ / OT MANAGEMENT ZONE                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  SCADA   │  │ Historian│  │   Jump   │  │   Insa   │        │
│  │  Server  │  │  Server  │  │   Host   │  │ Sensor   │◄── TAP │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────┬────────────────────────────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  OT Core Switch   │ ◄── MONITORING POINT 2
                    │  (SPAN Port Here) │
                    └─────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼───────┐   ┌─────────▼─────────┐  ┌───────▼───────┐
│ Production    │   │  Packaging Line   │  │  Quality Lab  │
│ Line 1 Switch │   │  Switch           │  │  Switch       │
└───────┬───────┘   └─────────┬─────────┘  └───────┬───────┘
        │                     │                     │
┌───────┴───────┐   ┌─────────┴─────────┐  ┌───────┴───────┐
│ PLC 1 - Robot │   │ PLC 2 - Conveyor  │  │ Vision System │
│ HMI Panel     │   │ HMI Panel         │  │ PLC 3         │
│ 192.168.10.x  │   │ 192.168.20.x      │  │ 192.168.30.x  │
└───────────────┘   └───────────────────┘  └───────────────┘

LEGEND:
═══════  Critical path (NO interruption allowed)
───────  Standard monitoring allowed
◄── TAP  Network tap/SPAN port location
```

### IP Addressing Scheme Template
```yaml
Network Segmentation:
  Corporate IT: 10.0.0.0/16
  OT Management: 192.168.1.0/24
  Production Line 1: 192.168.10.0/24
  Production Line 2: 192.168.20.0/24
  Quality/Lab: 192.168.30.0/24
  Robotics: 192.168.40.0/24

  Insa Sensor: 192.168.1.254 (static)
```

---

## Phase 4: Installation Procedure

### Pre-Installation (1 week before)

#### Technical Preparation
```bash
Equipment Checklist:
  [ ] Insa SecureOps sensor appliance
  [ ] Network cables (Cat6, various lengths)
  [ ] Console cable (USB-to-serial)
  [ ] Power supplies (redundant if available)
  [ ] Rack mount kit or shelf
  [ ] Cable labels and tags
  [ ] Laptop with configuration tools
  [ ] Backup storage (USB drive)

Software/Configuration:
  [ ] Sensor firmware (latest stable)
  [ ] Protocol parsers (Modbus, ENIP, Profinet, OPC-UA)
  [ ] SSL certificates generated
  [ ] VPN configuration (if remote monitoring)
  [ ] Email alert templates
  [ ] Client-specific detection rules
```

#### Coordination
```yaml
Stakeholder Notifications:
  - Production manager: Install date/time confirmed
  - Maintenance team: Escort/access arranged
  - IT team: Firewall rules pre-staged
  - Security: Badge access granted
  - Integrator: Verify no conflicting work

Change Control:
  - Change ticket number: _______
  - Approval signatures: _______
  - Rollback plan: _______
  - Emergency contact: _______
```

### Installation Day

#### Hour 0-1: Physical Installation
```yaml
Tasks:
  [ ] Badge in, safety briefing
  [ ] PPE donned (as required)
  [ ] Equipment inventory check
  [ ] Photo documentation (before state)

  Sensor Placement:
    [ ] Install in OT management zone (preferred)
    [ ] Mount in 19" rack or secure shelf
    [ ] Connect to UPS (if available)
    [ ] Label all cables clearly
    [ ] Verify cooling/airflow
```

#### Hour 1-2: Network Configuration
```yaml
Core Switch Configuration:
  [ ] Configure SPAN/mirror port:
      - Source: OT core switch uplink(s)
      - Destination: Port X (Insa sensor)
      - Direction: RX only (read-only monitoring)

  [ ] Assign management IP:
      - IP: 192.168.1.254
      - Subnet: 255.255.255.0
      - Gateway: 192.168.1.1
      - DNS: (client DNS servers)

  [ ] Test connectivity:
      - Ping gateway
      - Ping SCADA server
      - DNS resolution test
      - NTP sync verification
```

#### Hour 2-3: Sensor Configuration
```yaml
Initial Setup:
  [ ] Console access (serial cable)
  [ ] Set admin password (client-specific)
  [ ] Configure network interface
  [ ] Enable SSH (key-based auth)
  [ ] Set timezone (plant local time)
  [ ] Configure NTP server
  [ ] Enable syslog forwarding (to client SIEM if applicable)

Protocol Detection:
  [ ] Enable Modbus TCP parser (port 502)
  [ ] Enable EtherNet/IP parser (port 44818)
  [ ] Enable Profinet parser (port 34964)
  [ ] Enable OPC-UA parser (port 4840)
  [ ] Enable DNP3 parser (if present)
  [ ] Disable unused parsers (reduce noise)

Baseline Learning Mode:
  [ ] Enable 7-day learning mode
  [ ] Passive monitoring only
  [ ] No alerts generated
  [ ] Asset discovery active
  [ ] Protocol behavior profiling
```

#### Hour 3-4: Integration & Testing
```yaml
Alert Configuration:
  [ ] Email: security@client.com, ops@client.com
  [ ] SMTP server: (client mail relay)
  [ ] Test alert delivery

  Alert thresholds:
    - Critical: Unauthorized PLC writes, firmware changes
    - High: New devices, protocol anomalies
    - Medium: Configuration changes, unusual traffic
    - Low: Informational, asset inventory updates

DefectDojo Integration:
  [ ] API key configured
  [ ] Product created: "Manufacturing Plant - {Client Name}"
  [ ] Engagement: "OT Security Monitoring"
  [ ] Test finding upload
  [ ] Verify triage automation

SIEM Integration (if applicable):
  [ ] Syslog forwarding enabled
  [ ] Log format: CEF or JSON
  [ ] Test log ingestion
  [ ] Verify parsing rules
```

### Post-Installation (Same Day)

#### Validation Testing
```yaml
Passive Monitoring Verification:
  [ ] Confirm traffic capture (tcpdump)
  [ ] Verify protocol decoding
  [ ] Check asset discovery (PLCs appearing)
  [ ] Review baseline traffic patterns
  [ ] No production impact observed

Functional Tests:
  [ ] Generate test alert (safe method)
  [ ] Verify email delivery
  [ ] Check DefectDojo finding creation
  [ ] Test web UI access (HTTPS)
  [ ] Backup configuration

Documentation:
  [ ] "As-built" network diagram
  [ ] IP address assignments
  [ ] SPAN port configuration
  [ ] Admin credentials (in vault)
  [ ] Photo documentation (after state)
  [ ] Installation report signed off
```

---

## Phase 5: Sector-Specific Monitoring Templates

### Manufacturing-Specific Detection Rules

#### Rule Set 1: PLC Protection
```yaml
Name: Unauthorized PLC Program Upload
Severity: CRITICAL
Trigger: Modbus function code 16 (Write Multiple Registers) to PLC
  OR EtherNet/IP CIP Set_Attribute_Single
  FROM: Source IP NOT in authorized engineer list
Action:
  - Immediate email alert
  - Log to DefectDojo (auto-escalate)
  - Optional: Block at firewall (if inline mode)

False Positive Mitigation:
  - Whitelist: SCADA server IPs
  - Maintenance window: Suppress during planned downtime
  - Engineer workstations: 192.168.1.10-20 (authorized)
```

#### Rule Set 2: Production Disruption Detection
```yaml
Name: Unexpected PLC Stop Command
Severity: CRITICAL
Trigger:
  - Modbus: Write to coil/register known to halt production
  - EtherNet/IP: Controller mode change (RUN -> PROGRAM)
  - Profinet: Emergency stop signal
Action:
  - SMS alert to plant manager
  - Immediate investigation
  - Preserve forensic logs

Context:
  - Differentiate from normal E-stop (physical button)
  - Flag if remote/network-initiated
```

#### Rule Set 3: Asset Anomaly Detection
```yaml
Name: Rogue Device on Production Network
Severity: HIGH
Trigger:
  - New MAC address detected
  - Device NOT in asset inventory
  - ARP spoofing detected
Action:
  - Alert security team
  - Isolate to VLAN if possible
  - Investigate before production shift

Exceptions:
  - Maintenance laptops (pre-register MAC)
  - Contractor equipment (temporary whitelist)
```

#### Rule Set 4: Data Exfiltration
```yaml
Name: Unusual Data Upload from SCADA
Severity: HIGH
Trigger:
  - Large outbound transfer (>100MB in 1 hour)
  - To external IP (non-corporate)
  - During off-hours
Action:
  - Block at firewall
  - Alert IR team
  - Preserve network capture

Context:
  - Normal: SCADA historian backups (known destination)
  - Abnormal: HTTP/FTP to unknown cloud storage
```

### Manufacturing KPIs to Monitor

```yaml
Production Metrics:
  - OT network uptime: 99.9%+
  - SCADA availability: 99.95%+
  - PLC communication latency: <10ms average
  - Packet loss: <0.01%

Security Metrics:
  - Mean Time to Detect (MTTD): <5 minutes
  - Mean Time to Respond (MTTR): <15 minutes
  - False positive rate: <2% of total alerts
  - Asset inventory accuracy: 98%+

Compliance Metrics:
  - Vulnerability scan coverage: 100% of assets
  - Patch compliance: 95%+ (with plant approval)
  - Audit log retention: 1 year minimum
  - Incident response drill: Quarterly
```

---

## Phase 6: Compliance Requirements

### IEC 62443 Alignment

```yaml
IEC 62443-3-3 (System Security Requirements):
  SR 1.1 - Human User Identification:
    - Monitor: Failed login attempts to HMIs/SCADA
    - Alert: Brute force attacks detected

  SR 2.1 - Authorization Enforcement:
    - Monitor: Privilege escalation attempts
    - Alert: Admin-level access from unauthorized sources

  SR 3.3 - Use Control:
    - Monitor: Execution of unauthorized programs on PLCs
    - Alert: Firmware uploads outside maintenance windows

  SR 4.1 - Information Confidentiality:
    - Monitor: Unencrypted OT traffic (if policy requires encryption)
    - Alert: Cleartext credentials detected

  SR 7.1 - Denial of Service Protection:
    - Monitor: Network flooding, resource exhaustion
    - Alert: Abnormal traffic volumes to PLCs
```

### FDA 21 CFR Part 11 (Pharmaceutical Manufacturing)

```yaml
Electronic Records:
  [ ] Audit trail of all configuration changes
  [ ] Tamper-proof logging (WORM storage)
  [ ] User accountability (who changed what, when)
  [ ] System validation documentation

Electronic Signatures:
  [ ] Two-factor authentication for critical changes
  [ ] Signature manifests archived
  [ ] Annual recertification

System Validation (if regulated device):
  [ ] Installation Qualification (IQ)
  [ ] Operational Qualification (OQ)
  [ ] Performance Qualification (PQ)
  [ ] Annual revalidation
```

### ITAR (Defense Manufacturing)

```yaml
Access Control:
  [ ] U.S. persons only for sensor administration
  [ ] No foreign national access to system
  [ ] Encryption: FIPS 140-2 validated
  [ ] Data residency: U.S. data centers only

Audit Requirements:
  [ ] DFARS 252.204-7012 compliance
  [ ] NIST SP 800-171 controls implemented
  [ ] Annual third-party assessment
  [ ] Incident reporting to DIBNET (within 72 hours)
```

---

## Phase 7: Success Criteria

### 30-Day Milestones

```yaml
Week 1 (Learning Mode):
  [ ] 95%+ of production assets discovered
  [ ] Protocol baselines established
  [ ] Zero production disruptions from monitoring
  [ ] Stakeholder training completed

Week 2 (Tuning):
  [ ] Alert rules customized to plant operations
  [ ] False positive rate <5%
  [ ] Integration with client SIEM verified
  [ ] Backup/recovery tested

Week 3 (Active Monitoring):
  [ ] Transition from learning to enforcement mode
  [ ] First security finding detected and resolved
  [ ] Maintenance window procedures documented
  [ ] 24/7 monitoring confirmed

Week 4 (Optimization):
  [ ] Client self-service dashboard training
  [ ] Quarterly business review scheduled
  [ ] Continuous improvement plan documented
  [ ] Success metrics baseline established
```

### Long-Term Success Indicators

```yaml
Operational Excellence:
  - Production uptime maintained or improved
  - Security incidents detected before impact
  - Compliance audit findings: Zero
  - Client satisfaction score: 8+/10

Business Outcomes:
  - Cyber insurance premium reduced
  - Audit preparation time reduced by 50%
  - Incident response time <15 minutes
  - Regulatory fine avoidance

Strategic Value:
  - Expansion to additional sites
  - Integration with predictive maintenance
  - Supply chain security visibility
  - Board-level security reporting
```

---

## Phase 8: Maintenance Window Planning

### Pre-Planned Downtime Coordination

```yaml
Quarterly Maintenance Windows:
  Week of: ___________
  Duration: 4-8 hours
  Time: Saturday 6 AM - 2 PM (example)

  Insa Tasks During Window:
    [ ] Sensor firmware updates
    [ ] Database optimization
    [ ] Rule set updates
    [ ] Performance tuning
    [ ] Backup verification
    [ ] Certificate renewal (annual)

  Client Tasks:
    [ ] PLC firmware updates
    [ ] SCADA patching
    [ ] Network infrastructure upgrades
    [ ] Security testing (penetration test)

  Coordination:
    - Joint change control board review
    - Rollback plan documented
    - Success criteria defined
    - Post-maintenance validation checklist
```

### Emergency Maintenance Procedures

```yaml
Sensor Failure (RTO: 4 hours):
  1. Switch to redundant sensor (if deployed)
  2. Restore from last backup
  3. Contact Insa support (24/7 hotline)
  4. Root cause analysis within 24 hours

Production Emergency (Sensor Impact):
  1. Insa sensor can be bypassed (passive monitoring)
  2. Remove SPAN port configuration
  3. Production continues uninterrupted
  4. Resume monitoring post-incident

Security Incident Response:
  1. Preserve sensor logs (forensic evidence)
  2. Engage IR team
  3. Continuous monitoring during remediation
  4. Post-incident report within 72 hours
```

---

## Appendix A: Manufacturing Protocol Quick Reference

### Modbus TCP/RTU
```yaml
Use Case: PLCs, meters, sensors
Port: 502 (TCP) or serial (RTU)
Security Concerns:
  - No authentication
  - No encryption
  - Easy to spoof
Critical Function Codes:
  - 05: Write Single Coil (control relay)
  - 06: Write Single Register (set value)
  - 15: Write Multiple Coils (batch control)
  - 16: Write Multiple Registers (program upload)
Monitoring Focus: Writes from unauthorized sources
```

### EtherNet/IP (Allen-Bradley)
```yaml
Use Case: ControlLogix, CompactLogix PLCs
Port: 44818 (TCP), 2222 (UDP)
Security Concerns:
  - Default credentials common
  - Weak CIP authentication
  - Firmware vulnerabilities
Critical CIP Services:
  - 0x10: Set_Attribute_Single (modify PLC)
  - 0x4B: Forward_Open (establish connection)
  - 0x52: Execute_PCCC (legacy protocol)
Monitoring Focus: Controller mode changes, program downloads
```

### Profinet (Siemens)
```yaml
Use Case: S7-1200, S7-1500 PLCs
Port: 34964 (UDP)
Security Concerns:
  - Multicast traffic (harder to filter)
  - Real-time requirements (low latency)
  - Firmware downgrade attacks
Critical Frames:
  - DCP (Discovery/Configuration)
  - Cyclic data (I/O updates)
  - Alarms/diagnostics
Monitoring Focus: Topology changes, alarm floods
```

### OPC-UA
```yaml
Use Case: SCADA-to-PLC communication
Port: 4840 (TCP)
Security Concerns:
  - Certificate validation often disabled
  - Anonymous access allowed
  - Insufficient access control
Critical Services:
  - Write (modify process values)
  - CreateMonitoredItems (surveillance)
  - AddNodes (schema manipulation)
Monitoring Focus: Unauthorized writes, certificate anomalies
```

---

## Appendix B: Contact & Escalation

```yaml
Insa Automation Corp Support:
  General Inquiries: w.aroca@insaing.com
  24/7 NOC: noc@insaing.com (if available)
  Emergency Hotline: _____________

Client Escalation Path:
  Tier 1: Plant Operator (immediate production issues)
  Tier 2: Production Manager (operational decisions)
  Tier 3: Plant Manager (business impact)
  Tier 4: Corporate Security (data breach, legal)

Severity Levels:
  CRITICAL: Production down, safety risk, active attack
    - Response: 15 minutes
    - Escalation: Immediate to Tier 3

  HIGH: Unauthorized access, system compromise
    - Response: 1 hour
    - Escalation: Tier 2 within 2 hours

  MEDIUM: Policy violation, anomaly detected
    - Response: 4 hours
    - Escalation: Daily summary report

  LOW: Informational, asset changes
    - Response: Next business day
    - Escalation: Weekly report
```

---

**Document Control**
Version: 1.0
Author: Insa Automation Corp
Date: October 11, 2025
Classification: Client Confidential
Review Cycle: Quarterly

**Made by Insa Automation Corp for OpSec**
