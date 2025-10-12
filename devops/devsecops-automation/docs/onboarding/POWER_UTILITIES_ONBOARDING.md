# Power & Utilities Sector - Client Onboarding Playbook
**Insa Automation Corp | Critical Infrastructure Security**
Version: 1.0 | Date: October 11, 2025

---

## Executive Summary

Power generation, transmission, and distribution facilities are classified as Critical Infrastructure with stringent regulatory requirements. This playbook addresses the unique challenges of securing substations, control centers, and generation facilities.

### Sector Characteristics
- **Critical Priority**: Grid reliability (99.999% uptime requirement)
- **Key Assets**: RTUs, SCADA, substation automation, protective relays, DERMS
- **Common Protocols**: DNP3, IEC 61850, Modbus, IEC 60870-5-101/104
- **Regulatory**: NERC CIP, TSA Security Directives, State PUC requirements
- **Risk Profile**: Nation-state attacks, coordinated grid disruption, ransomware
- **Incident Response SLA**: <5 minutes for grid-impacting events

---

## Phase 1: Pre-Sales Discovery

### Discovery Questionnaire

#### Utility Profile
```yaml
Organization Type:
  [ ] Investor-Owned Utility (IOU)
  [ ] Municipal Utility
  [ ] Cooperative (Co-op)
  [ ] Independent Power Producer (IPP)
  [ ] Transmission Operator (TO)
  [ ] Balancing Authority (BA)

Service Territory:
  - Population served: _______
  - MW capacity: _______
  - Transmission lines: _____ miles
  - Distribution substations: _____
  - Generation facilities: _____

NERC Registration:
  [ ] Balancing Authority (BA)
  [ ] Reliability Coordinator (RC)
  [ ] Transmission Operator (TOP)
  [ ] Transmission Owner (TO)
  [ ] Generator Owner (GO)
  [ ] Generator Operator (GOP)
  [ ] Distribution Provider (DP)

  Registered Entity ID: __________
```

#### Critical Infrastructure Assets
```yaml
Generation Facilities:
  [ ] Coal-fired plants: _____
  [ ] Natural gas combined cycle: _____
  [ ] Nuclear: _____ (requires NRC coordination)
  [ ] Hydro: _____
  [ ] Solar farms: _____
  [ ] Wind farms: _____
  [ ] Battery storage: _____ MWh

Substations (by voltage class):
  - 765kV / 500kV (EHV): _____
  - 345kV / 230kV (HV): _____
  - 138kV / 115kV (HV): _____
  - 69kV / 46kV (Sub-transmission): _____
  - 34.5kV / 12.47kV (Distribution): _____

  NERC CIP Classification:
    - High Impact BES Cyber Systems: _____
    - Medium Impact BES Cyber Systems: _____
    - Low Impact BES Cyber Systems: _____
    - Non-BES assets: _____

Control Centers:
  - Primary Control Center: Location _______
  - Backup Control Center: Location _______
  - Energy Management System (EMS): Vendor _______
  - SCADA system: Vendor _______
  - Historian: Vendor _______
```

#### SCADA/OT Environment
```yaml
Communication Infrastructure:
  [ ] Private microwave network
  [ ] Leased fiber (carrier: ______)
  [ ] Cellular/LTE (carrier: ______)
  [ ] Satellite (vendor: ______)
  [ ] Private LTE (CBRS spectrum)

Protocols in Use:
  [ ] DNP3 (serial and/or TCP) - Port 20000
  [ ] IEC 61850 (MMS) - Port 102
  [ ] IEC 60870-5-104 - Port 2404
  [ ] Modbus TCP - Port 502
  [ ] ICCP/TASE.2 (inter-utility) - Port 102
  [ ] IEEE C37.118 (synchrophasors) - Port 4712

RTU/IED Inventory:
  - RTUs (Remote Terminal Units): _____ units
    - Vendor(s): [ ] SEL [ ] ABB [ ] Schneider [ ] GE [ ] Other: _____
  - Intelligent Electronic Devices (IEDs): _____ units
    - Protective relays (SEL-351, SEL-421, etc.): _____
    - Phasor Measurement Units (PMUs): _____
    - Digital fault recorders: _____

Substation Automation:
  - Protocol: [ ] IEC 61850 [ ] DNP3 [ ] Modbus [ ] Proprietary
  - Gateway/concentrator: Vendor _______
  - Engineering access: [ ] Serial only [ ] Network [ ] Airgapped
```

#### Regulatory Compliance Status
```yaml
NERC CIP Standards:
  CIP-002 (BES Cyber Asset Categorization):
    - Last categorization review: _______
    - High Impact BCS: _____ assets
    - Medium Impact BCS: _____ assets

  CIP-003 (Security Management Controls):
    - Senior Manager approval: [ ] Yes [ ] No
    - Policy review cycle: [ ] Annual [ ] Biennial

  CIP-005 (Electronic Security Perimeter):
    - ESPs defined: _____ zones
    - External Routable Connectivity (ERC): _____ points
    - Interactive Remote Access: [ ] Yes [ ] No

  CIP-007 (System Security Management):
    - Patch management: _____ day window
    - Port/service management: [ ] Documented [ ] Automated
    - Malware prevention: Vendor _______

  CIP-010 (Configuration Change Management):
    - Baseline configurations: [ ] Yes [ ] No
    - Change control process: [ ] Automated [ ] Manual

  CIP-011 (Information Protection):
    - BES Cyber System Information (BCSI): Storage location _______
    - Encryption: [ ] At rest [ ] In transit

  Next NERC Audit:
    - Date: _______
    - Type: [ ] Compliance [ ] Spot check [ ] Investigation
    - Auditor: _______

Other Regulations:
  [ ] TSA Security Directive (pipeline/rail co-located)
  [ ] NRC 10 CFR 73.54 (nuclear plant cyber)
  [ ] State PUC cybersecurity requirements
  [ ] FERC Order 887 (cybersecurity incentives)
```

#### Incident Response & Recovery
```yaml
Current Capabilities:
  - Security Operations Center (SOC): [ ] 24/7 [ ] Business hours [ ] Outsourced
  - Incident Response Team: _____ members
  - Cyber Mutual Assistance: [ ] E-ISAC member [ ] Regional partnership
  - Backup control center: [ ] Hot standby [ ] Warm standby [ ] Cold standby

Recovery Time Objectives:
  - Control center failover: _____ minutes
  - Substation RTU replacement: _____ hours
  - SCADA system recovery: _____ hours
  - Grid restoration (black start): _____ hours

Reporting Requirements:
  - DOE OE-417 (emergency report): Within 1 hour of event
  - NERC EOP-004 (event reporting): Within 24 hours
  - FBI/CISA (cyber incident): Immediate notification
  - State PUC: Per tariff requirements
```

---

## Phase 2: Site Assessment

### Pre-Deployment Checklist

#### Week 1-2: Regulatory & Documentation Review
```yaml
Compliance Documentation:
  [ ] NERC CIP compliance artifacts (last 3 years)
  [ ] Electronic Security Perimeter (ESP) diagrams
  [ ] BES Cyber Asset inventory
  [ ] Risk assessment reports
  [ ] Vulnerability assessment reports (CIP-010)
  [ ] Incident response plan (CIP-008)

Network Architecture:
  [ ] One-line diagrams (electrical)
  [ ] Network topology diagrams (cyber)
  [ ] SCADA system architecture
  [ ] Wide Area Network (WAN) maps
  [ ] Firewall rule sets
  [ ] Access control lists (routers/switches)
  [ ] VPN configurations

Physical Security:
  [ ] PSP (Physical Security Perimeter) boundaries
  [ ] Access badge system
  [ ] Camera/surveillance coverage
  [ ] Environmental monitoring (substations)
```

#### Week 3-4: Control Center Assessment (2-3 days)
```yaml
Primary Control Center Visit:
  [ ] Badge access approval (background check may be required)
  [ ] Escort arrangements
  [ ] NDA/clearance verification

  EMS/SCADA Room:
    [ ] Operator workstation inventory
    [ ] Dispatcher consoles
    [ ] Large display walls (situational awareness)
    [ ] Engineering workstations
    [ ] Historian servers
    [ ] Communication gateways

  Network Operations:
    [ ] Core routing/switching gear
    [ ] Firewall/IDS/IPS placement
    [ ] WAN aggregation points
    [ ] Optimal sensor placement (SPAN ports)
    [ ] Out-of-band management network

  Interviews:
    [ ] System Operator (grid operations)
    [ ] SCADA Administrator (system maintenance)
    [ ] Telecom Engineer (WAN infrastructure)
    [ ] Cybersecurity Lead (CIP compliance)
    [ ] Senior Manager (business priorities)
```

#### Week 5: Substation Site Visits (Select High/Medium Impact)
```yaml
Site Selection Criteria:
  - 1x High Impact substation (if applicable)
  - 2x Medium Impact substations (different voltage classes)
  - 1x Remote substation (communication challenges)

Per-Site Checklist:
  [ ] Site access approval (utility staff escort required)
  [ ] Safety briefing (arc flash, high voltage hazards)
  [ ] PPE requirements verified

  Control House Inspection:
    [ ] RTU/gateway location
    [ ] Communication equipment (radio, cellular, fiber)
    [ ] Protective relay panels
    [ ] Ethernet switches (if networked)
    [ ] Power supply (AC/DC, battery backup)
    [ ] Environmental (HVAC, temperature monitoring)

  Network Connectivity:
    [ ] Communication medium (fiber, microwave, cellular)
    [ ] Bandwidth: _____ kbps/Mbps
    [ ] Latency to control center: _____ ms
    [ ] Redundant path: [ ] Yes [ ] No

  Security Observations:
    [ ] Perimeter fence (physical security)
    [ ] Access control (locks, badges)
    [ ] Camera surveillance
    [ ] Motion detection
    [ ] Cyber: Serial-only vs. network-accessible
```

---

## Phase 3: Network Diagram Template

### Power Utility Network Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      CORPORATE IT NETWORK                         │
│  (Email, ERP, Engineering Tools, Internet)                       │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                   ┌─────────▼─────────┐
                   │  Demilitarized    │
                   │  Zone (DMZ)       │
                   │  ┌──────────────┐ │
                   │  │ Historian    │ │◄── Data Diode (one-way)
                   │  │ (read-only)  │ │
                   │  └──────────────┘ │
                   └─────────┬─────────┘
                             │
                   ┌─────────▼─────────┐
                   │  CIP-005 ESP      │ ◄── NERC Critical Infrastructure
                   │  Firewall         │     Protection Boundary
                   │  (Stateful + IDS) │
                   └─────────┬─────────┘
                             │
┌─────────────────────────────┴──────────────────────────────────────┐
│              OT NETWORK (BES Cyber Systems - High Impact)          │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │   Primary    │  │   Backup     │  │   Insa       │◄── SPAN    │
│  │   EMS/SCADA  │  │   EMS/SCADA  │  │   Sensor     │    Port    │
│  │   (Active)   │  │   (Standby)  │  │              │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│         │                  │                                       │
│         └──────────┬───────┘                                       │
│                    │                                               │
│          ┌─────────▼─────────┐                                     │
│          │  OT Core Switch   │ ◄── MONITORING POINT 1             │
│          │  (Redundant Pair) │                                     │
│          └─────────┬─────────┘                                     │
│                    │                                               │
└────────────────────┼───────────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┬───────────────────┐
         │           │           │                   │
┌────────▼────┐ ┌────▼────┐ ┌────▼────┐      ┌──────▼──────┐
│  Microwave  │ │  Fiber  │ │ Cellular│      │  Satellite  │
│  Network    │ │  Ring   │ │ Gateway │      │  Terminal   │
└────────┬────┘ └────┬────┘ └────┬────┘      └──────┬──────┘
         │           │           │                   │
    ┌────▼───────────▼───────────▼───────────────────▼────┐
    │           WAN Transport Network                      │
    │  (Private microwave, leased fiber, LTE, satellite)  │
    └────┬───────────┬───────────┬───────────────────┬────┘
         │           │           │                   │
┌────────▼────┐ ┌────▼────┐ ┌────▼────┐      ┌──────▼──────┐
│ Substation  │ │ Substation│ │Substation│    │ Generation  │
│ A (500kV)   │ │ B (230kV) │ │ C (115kV)│    │ Plant       │
│             │ │           │ │          │    │             │
│ ┌─────────┐ │ │┌─────────┐│ │┌────────┐│    │┌──────────┐ │
│ │RTU/IEDs │ │ ││RTU/IEDs ││ ││RTU/IEDs││    ││ Plant DCS│ │
│ │DNP3/    │ │ ││IEC 61850││ ││Modbus  ││    ││ Modbus   │ │
│ │IEC 61850│ │ │└─────────┘│ │└────────┘│    │└──────────┘ │
│ └─────────┘ │ └───────────┘ └──────────┘    └─────────────┘
└─────────────┘   (Medium Impact) (Low Impact)  (High Impact)

LEGEND:
═══════  Critical BES Cyber System path
───────  Standard monitoring path
◄── SPAN Network tap/mirror port
🔒      NERC CIP boundary
```

### NERC CIP Zone Segmentation
```yaml
Zone 1 - Corporate IT (Non-BES):
  Network: 10.0.0.0/16
  Access: Internet-connected, standard IT controls

Zone 2 - DMZ (Electronic Access Point):
  Network: 192.168.100.0/24
  Controls: Data diode, read-only historian, web HMI
  Insa Sensor: 192.168.100.250 (for corporate visibility)

Zone 3 - ESP (Electronic Security Perimeter):
  Network: 172.16.0.0/16
  Controls: Firewall, IDS/IPS, MFA for remote access
  Assets: EMS/SCADA, engineering workstations
  Insa Sensor: 172.16.1.250 (primary monitoring)

Zone 4 - Control Center LAN (High Impact BCS):
  Network: 10.100.0.0/16
  Controls: CIP-005/007 compliant
  Assets: Operator HMIs, real-time databases

Zone 5 - Substation Networks (per site):
  Network: 10.200.x.0/24 (where x = site ID)
  Protocols: DNP3, IEC 61850, serial communications
  Monitoring: Distributed sensors or backhaul to central
```

---

## Phase 4: Installation Procedure

### Pre-Installation (2-4 weeks before)

#### Regulatory Approval Process
```yaml
NERC CIP Change Management (CIP-010):
  [ ] Change request submitted
  [ ] Impact analysis: "Adding passive monitoring sensor"
  [ ] Baseline configuration update planned
  [ ] Senior Manager approval obtained
  [ ] Testing plan documented
  [ ] Rollback procedure defined

  Change Control Board (CCB):
    - Date: _______
    - Attendees: Operations, Engineering, Cybersecurity, Management
    [ ] Approved [ ] Conditional [ ] Denied

Physical Security Perimeter (PSP) Access:
  [ ] Background check completed (7-10 days)
  [ ] Badge/credentials issued
  [ ] Escort assigned (if required)
  [ ] Site-specific safety training (online)

Equipment & Licensing:
  [ ] Insa sensor appliance (CIP-007 hardened)
  [ ] NERC CIP compliance certificate (firmware signed)
  [ ] Protocol parsers: DNP3, IEC 61850, Modbus, ICCP
  [ ] TLS certificates (ECC-256 or RSA-2048)
  [ ] Redundant power supplies
  [ ] Rack mount kit (EIA-310 compliant)
  [ ] Serial console cable (RJ45-to-DB9)
```

#### Coordination
```yaml
Stakeholder Notifications (per CIP-008):
  - Control center operators: 2 weeks advance notice
  - Telecom team: Fiber/switch access coordination
  - Cybersecurity team: Firewall rule staging
  - NERC compliance officer: Change ticket reference

Outage Planning:
  - Preferred: No outage (passive SPAN port)
  - If required: <1 hour during low-load period
  - Backup control center: [ ] Activated [ ] Standby [ ] Not required
  - Grid impact: NONE (monitoring only)
```

### Installation Day - Control Center

#### Hour 0-1: Physical Installation
```yaml
Arrival:
  [ ] Badge in at security checkpoint
  [ ] Safety briefing (arc flash, lockout/tagout if applicable)
  [ ] Escort to control center
  [ ] Pre-installation photo documentation

Sensor Placement:
  [ ] Install in secure network rack (lockable cabinet)
  [ ] Zone 3 (ESP) or Zone 4 (Control Center LAN)
  [ ] Connect to UPS (verify runtime >30 min)
  [ ] Redundant power supply (if available)
  [ ] Cable management (labeled per site standards)
  [ ] Serial console access cable
```

#### Hour 1-2: Network Configuration
```yaml
Core Switch SPAN Configuration:
  [ ] Configure monitor session:
      - Source: EMS/SCADA trunk port(s)
      - Source: WAN uplink(s) to substations
      - Destination: Port X (Insa sensor)
      - Direction: RX only (no TX - passive)
      - Filter: VLAN 100 (SCADA), VLAN 200 (RTUs) if applicable

  Example (Cisco):
    monitor session 1 source interface Gi1/0/1 rx
    monitor session 1 destination interface Gi1/0/24
    ! Port Gi1/0/24 connected to Insa sensor

  [ ] Verify no broadcast storms (SPAN port can overload)
  [ ] Test: tcpdump on sensor sees DNP3/IEC 61850 traffic

Management Network:
  [ ] Assign static IP (from approved asset list)
      - IP: 172.16.1.250
      - Subnet: 255.255.255.0
      - Gateway: 172.16.1.1 (ESP firewall)
      - DNS: (utility internal DNS)

  [ ] Configure NTP (CIP-007 requirement):
      - Primary: (utility NTP server - GPS-synced)
      - Secondary: (backup NTP server)
      - Stratum: ≤2 (for accurate event correlation)

  [ ] Enable SSH (key-based authentication only):
      - Disable password auth
      - Install utility admin public keys
      - Disable root login
```

#### Hour 2-3: Sensor Configuration
```yaml
Initial Hardening (CIP-007 Compliance):
  [ ] Set strong admin password (16+ chars, complexity)
  [ ] Disable unnecessary services:
      - Telnet (use SSH only)
      - FTP (use SFTP/SCP only)
      - HTTP (use HTTPS only)
      - SNMP v1/v2 (use v3 with encryption)

  [ ] Enable audit logging (CIP-007 R4):
      - Log all authentication attempts
      - Log all configuration changes
      - Syslog to SIEM (if applicable)
      - Local retention: 90 days minimum

  [ ] Patch level verification:
      - OS: Latest stable (signed by Insa)
      - Applications: No known CVEs
      - Document versions in asset inventory

Protocol Parsers (Utilities-Specific):
  [ ] DNP3 (serial and TCP):
      - Port: 20000
      - Variants: Level 2/Level 3
      - Unsolicited responses: Enabled
      - Master/Outstation mode: Learn both

  [ ] IEC 61850:
      - MMS (port 102)
      - GOOSE (multicast 01-0C-CD-01-00-00 to 00-FF)
      - Sampled Values (if PMUs present)

  [ ] IEC 60870-5-104:
      - Port: 2404
      - ASDU parsing enabled

  [ ] Modbus TCP (legacy RTUs):
      - Port: 502

  [ ] ICCP/TASE.2 (inter-utility exchanges):
      - Port: 102
      - May require coordination with neighboring utilities

  [ ] IEEE C37.118 (synchrophasors):
      - Port: 4712
      - PDC (Phasor Data Concentrator) IP: _______

Baseline Learning Mode:
  [ ] Enable 14-day learning period (utilities need longer)
  [ ] Passive monitoring only
  [ ] Asset discovery: RTUs, IEDs, SCADA servers
  [ ] Communication pattern profiling
  [ ] No alerts to operators (reduce noise)
```

#### Hour 3-4: Integration & Testing
```yaml
SIEM/SOC Integration:
  [ ] Syslog forwarding to utility SOC
  [ ] Log format: CEF (Common Event Format)
  [ ] Test log ingestion
  [ ] Correlation rules: Map to NERC CIP violations

Alert Configuration (Post-Learning):
  Critical Alerts (Grid Impact):
    - Unauthorized DNP3 control commands (function code 0x05 OPERATE)
    - IEC 61850 trip commands from unknown source
    - RTU firmware upload attempts
    - GPS time sync loss (CIP-007 violation)

  High Alerts (CIP Compliance):
    - Failed login attempts (threshold: 3 in 15 min)
    - New device on SCADA network
    - Protocol anomaly (malformed DNP3/IEC 61850)
    - Unencrypted remote access attempt

  Medium Alerts:
    - Configuration change outside change window
    - Abnormal traffic volume to RTU
    - Certificate expiration (30 days warning)

  Notification:
    - Email: soc@utility.com, cip-compliance@utility.com
    - SMS: On-call operator (for CRITICAL only)
    - SIEM ticket auto-creation

Compliance Verification:
  [ ] CIP-005: Sensor within ESP boundary ✓
  [ ] CIP-007: Ports/services documented ✓
  [ ] CIP-007: Patch level current ✓
  [ ] CIP-010: Baseline configuration saved ✓
  [ ] CIP-011: BCSI protection (sensor admin access restricted) ✓
```

### Post-Installation Validation

#### Same Day Testing
```yaml
Functional Tests:
  [ ] Capture DNP3 traffic (verify decoding)
  [ ] Capture IEC 61850 GOOSE messages (multicast)
  [ ] Verify RTU asset discovery (compare to known inventory)
  [ ] Test alert generation (safe method: dummy device)
  [ ] Confirm NTP sync (CIP-007 requirement)
  [ ] No impact to grid operations observed

Grid Operator Confirmation:
  [ ] EMS/SCADA system: Normal operation
  [ ] RTU communication: No latency increase
  [ ] Alarm system: No spurious alarms
  [ ] Operator feedback: "No noticeable change" (success criteria)

Documentation (CIP-010):
  [ ] Updated network diagram (sensor location)
  [ ] Updated BES Cyber Asset inventory
  [ ] Configuration baseline exported
  [ ] Installation report (signed by utility engineer)
  [ ] Change ticket closed (successful)
```

---

## Phase 5: Sector-Specific Monitoring Templates

### Power & Utilities Detection Rules

#### Rule Set 1: Grid Protection
```yaml
Name: Unauthorized Substation Trip Command
Severity: CRITICAL
Trigger:
  - DNP3: OPERATE command (function code 0x05) to breaker control point
  - IEC 61850: TripCircuitBreaker GOOSE message
  - Source IP: NOT in authorized master list
Action:
  - SMS to on-call operator (immediate)
  - Email to SOC + CIP compliance
  - Auto-generate NERC EOP-004 incident report draft
  - Preserve 1 hour of pre/post PCAP (forensics)

Whitelist:
  - Primary SCADA: 172.16.10.1
  - Backup SCADA: 172.16.10.2
  - Engineering workstation: 172.16.20.5 (during maintenance window only)

Context:
  - Differentiate from: Protective relay (expected trip due to fault)
  - Flag if: Remote/network-initiated without operator confirmation
```

#### Rule Set 2: CIP Compliance Violations
```yaml
Name: Unauthorized Physical/Logical Access
Severity: HIGH (CIP-006/CIP-005)
Trigger:
  - Failed SSH login attempts: ≥3 in 15 minutes
  - Remote access from non-VPN IP
  - Access during non-authorized hours (outside maintenance window)
Action:
  - Alert CIP compliance officer
  - Log to access control system
  - Quarterly audit report flag

Name: Missing Security Patch (CIP-007 R2)
Severity: HIGH
Trigger:
  - CVE published affecting BES Cyber System
  - Patch not applied within 35 days (CIP requirement)
Action:
  - Alert cybersecurity team (day 30)
  - Escalate to Senior Manager (day 33)
  - Potential NERC violation report (day 36)
```

#### Rule Set 3: Protocol Anomaly Detection
```yaml
Name: DNP3 Function Code Anomaly
Severity: MEDIUM
Trigger:
  - Unusual DNP3 function code (not in baseline)
  - Example: READ_FILE_INFO (0x1C) - rare in substations
  - Or: Excessive polling rate (>1 request/sec to single RTU)
Action:
  - Alert protocol engineer
  - Log for trend analysis
  - May indicate reconnaissance/attack preparation

Name: IEC 61850 GOOSE Storm
Severity: HIGH
Trigger:
  - GOOSE message rate >100/sec (normal: 1-4/sec)
  - May indicate: Network loop, compromised IED, DDoS attempt
Action:
  - Alert network operations
  - Potential to isolate affected VLAN
  - Grid impact assessment required
```

#### Rule Set 4: Inter-Utility Data Exchange
```yaml
Name: ICCP Data Injection Attempt
Severity: CRITICAL
Trigger:
  - ICCP/TASE.2 message from unknown bilateral agreement partner
  - Modification of interchange schedule without RC approval
  - Abnormal load forecast data (>20% deviation)
Action:
  - Alert Reliability Coordinator (RC)
  - Suspend ICCP data acceptance (manual override)
  - Verify with neighboring utility via phone (out-of-band)

Context:
  - Known partners: [List of neighboring BAs/TOPs]
  - Expected message rate: 1-minute intervals
  - Critical data points: Actual net interchange, frequency, voltage
```

### Power Utilities KPIs

```yaml
Grid Reliability:
  - SCADA availability: 99.999% (5 minutes downtime/year)
  - RTU communication success rate: >99.9%
  - EMS processing latency: <100ms (real-time requirement)
  - Substation automation response: <4ms (IEC 61850 requirement)

Security Metrics (NERC CIP):
  - Mean Time to Detect (MTTD): <5 minutes (CIP mandate)
  - Mean Time to Report (MTTR): <15 minutes (internal SLA)
  - NERC violation risk: ZERO
  - Audit findings: Minimal (no HIGH/SEVERE)
  - Incident response drill: Quarterly (CIP-008)

Asset Visibility:
  - BES Cyber Asset inventory accuracy: 100%
  - RTU/IED firmware version tracking: 100%
  - Unauthorized device detection: <1 hour
  - Configuration drift detection: Daily scans

Compliance Automation:
  - CIP-007 patch compliance: 100% within 35 days
  - CIP-010 baseline verification: Weekly automated
  - CIP-011 BCSI access logs: Daily review
  - Vulnerability scans (CIP-010 R2): At least every 15 months
```

---

## Phase 6: Compliance Requirements

### NERC CIP Standards Implementation

#### CIP-005: Electronic Security Perimeter (ESP)
```yaml
Insa Sensor Placement within ESP:
  [ ] Deployed inside ESP boundary (Zone 3 or 4)
  [ ] All external communication through ESP firewall
  [ ] No direct internet access from sensor
  [ ] Management access via secure jump host or VPN (MFA required)

External Routable Connectivity (ERC):
  [ ] If sensor has ERC (e.g., cloud reporting):
      - Document ERC in CIP-005 Table
      - Require VPN or encrypted tunnel
      - Inbound traffic: Deny all (default)
      - Outbound traffic: Whitelist only (Insa cloud IPs)

Electronic Access Points (EAP):
  [ ] Sensor management port: Documented as EAP
  [ ] Firewall rules: Least-privilege (deny-all, permit-by-exception)
  [ ] Monitoring: Log all EAP traffic for 90 days

Interactive Remote Access:
  [ ] Insa support access: Via client-controlled VPN only
  [ ] Multi-Factor Authentication (MFA): Required
  [ ] Session logging: All keystrokes/commands recorded
  [ ] Annual review: List of authorized Insa personnel
```

#### CIP-007: Systems Security Management
```yaml
Ports & Services (R1):
  [ ] Document all listening ports:
      - 22/TCP: SSH (management)
      - 443/TCP: HTTPS (web UI)
      - 514/UDP: Syslog (outbound)
      - Passive ports: None (monitor mode)

  [ ] Disable unnecessary services (see installation checklist)
  [ ] Annual review: Revalidate required ports

Patch Management (R2):
  [ ] Insa sensor patch cycle: Monthly (or per CVE urgency)
  [ ] Utility testing window: 7 days (pre-production)
  [ ] Deployment: Within 35 days of release (CIP mandate)
  [ ] Track: CVE applicability, patch version, install date

Malware Prevention (R3):
  [ ] Host-based antivirus: Enabled (if sensor OS supports)
  [ ] Or: Network-based malware detection (via SPAN traffic analysis)
  [ ] Signature updates: Weekly (automated)
  [ ] Mitigation: If AV not feasible, document compensating control

Security Event Monitoring (R4):
  [ ] Log all authentication attempts (success/failure)
  [ ] Log all configuration changes (who, what, when)
  [ ] Retention: 90 calendar days minimum
  [ ] Review: Weekly (automated alerts for anomalies)

System Accounts (R5):
  [ ] Default passwords: Changed on day 1
  [ ] Password complexity: 16+ chars, upper/lower/number/special
  [ ] Password change: Every 15 months maximum
  [ ] Shared accounts: Prohibited (individual user accounts only)
```

#### CIP-010: Configuration Change Management
```yaml
Baseline Configuration (R1):
  [ ] Initial baseline: Captured within 30 days of deployment
  [ ] Includes: OS version, app versions, network config, user accounts
  [ ] Storage: Secure repository (CIP-011 BCSI protection)
  [ ] Review: At least every 15 months

Change Control (R1):
  [ ] All changes require approved change ticket
  [ ] Testing: In lab/non-production (if feasible)
  [ ] Rollback plan: Documented before implementation
  [ ] Post-change verification: Compare to baseline

Monitoring for Changes (R1):
  [ ] Automated: Daily integrity check (file checksums)
  [ ] Alert: If unauthorized change detected
  [ ] Investigation: Within 24 hours

Vulnerability Assessments (R2):
  [ ] Frequency: At least every 15 months (CIP requirement)
  [ ] Scope: Sensor OS, applications, network services
  [ ] Tools: Nessus, Qualys, or approved scanner
  [ ] Remediation: Per CIP-007 R2 patch timeline
```

#### CIP-011: Information Protection
```yaml
BES Cyber System Information (BCSI):
  Insa sensor contains BCSI:
    - Network diagrams (topology)
    - IP addressing schemes
    - Security configurations
    - Vulnerability assessment results

  Protection Measures:
    [ ] Storage: Encrypted at rest (AES-256)
    [ ] Transmission: TLS 1.2+ or VPN
    [ ] Access control: Role-based (RBAC)
    [ ] Disposal: Secure wipe (NIST SP 800-88) when decommissioned

  Reuse/Disposal:
    [ ] Before return to Insa (if leased): DOD 5220.22-M wipe
    [ ] Certificate: Provide data destruction certificate to utility
```

### TSA Security Directives (if applicable)

```yaml
Pipeline + Electric Co-location:
  If utility operates natural gas pipeline + electric:
    [ ] TSA SD Pipeline-2021-02 compliance
    [ ] Cybersecurity Coordinator designated
    [ ] Incident reporting to CISA (24 hours)
    [ ] OT network segmentation verified
```

### State PUC Cybersecurity Requirements

```yaml
Example: California PUC (CPUC) Cybersecurity Requirements:
  [ ] Annual cybersecurity report to PUC
  [ ] Third-party security assessment (every 3 years)
  [ ] Customer data protection (if sensor touches AMI/smart meters)
  [ ] Incident disclosure (to customers if PII impacted)

Insa Sensor Considerations:
  [ ] Does NOT handle customer PII (out of scope)
  [ ] Focus: Grid operations security only
  [ ] May be included in PUC audit scope (utility responsibility)
```

---

## Phase 7: Success Criteria

### 60-Day Milestones (Extended for Utilities)

```yaml
Week 1-2 (Learning Mode):
  [ ] 100% of RTUs/IEDs discovered and baselined
  [ ] Protocol decoding accuracy: >99% (DNP3, IEC 61850)
  [ ] Zero false positives to operators (critical)
  [ ] NERC CIP change ticket closed successfully

Week 3-4 (Tuning):
  [ ] Alert rules customized to utility operations
  [ ] Integration with SOC SIEM verified
  [ ] CIP compliance dashboards operational
  [ ] Substation communication patterns documented

Week 5-6 (Active Monitoring):
  [ ] Transition to enforcement mode (alerts enabled)
  [ ] First security finding detected and mitigated
  [ ] No grid reliability impact (99.999% maintained)
  [ ] Operator acceptance achieved

Week 7-8 (Validation):
  [ ] Simulated incident response drill (CIP-008)
  [ ] NERC compliance officer sign-off
  [ ] Quarterly business review with Senior Manager
  [ ] Documentation complete for next audit
```

### Long-Term Success Indicators

```yaml
Regulatory Excellence:
  - NERC audit: ZERO violations related to monitoring
  - CIP compliance: 100% (all standards applicable)
  - Incident reporting: Automated draft reports (save hours)
  - Regulatory fines: $0 (avoidance value: potential millions)

Operational Resilience:
  - Grid incidents prevented: Quantify (e.g., 3 unauthorized access attempts blocked)
  - Response time improvement: 80% faster detection
  - Asset visibility: 100% (previously ~70% with manual tracking)
  - Outage reduction: Fewer cyber-related grid disturbances

Business Value:
  - Cyber insurance premium: Reduced by 20-30%
  - Audit preparation time: Reduced by 60% (automated evidence)
  - Staff efficiency: Security team focuses on response, not log review
  - Expansion: Deploy to additional control centers/substations
```

---

## Phase 8: Incident Response (Grid-Specific)

### Incident Classification (NERC EOP-004)

```yaml
Category 1: Reportable Cyber Security Incident (IMMEDIATE)
  Definition: Cyber compromise that impacts BES operations
  Examples:
    - Successful malware infection of EMS/SCADA
    - Unauthorized control of circuit breakers
    - Data exfiltration of BCSI

  Insa Sensor Actions:
    1. Preserve forensic evidence (PCAP, logs) - do NOT rotate
    2. Alert Senior Manager + CIP compliance officer
    3. Notify NERC ES-ISAC (within 1 hour via portal)
    4. Notify E-ISAC (Electricity ISAC)
    5. Draft EOP-004 report (Insa assists with technical details)
    6. Coordinate with FBI/CISA (if nation-state suspected)

Category 2: Attempted Cyber Security Incident (24-hour reporting)
  Definition: Unsuccessful attack attempt detected
  Examples:
    - Blocked malware delivery
    - Failed unauthorized login attempts
    - Reconnaissance activity (port scans)

  Insa Sensor Actions:
    1. Log incident with evidence
    2. Alert cybersecurity team
    3. Include in monthly NERC report (if multiple attempts)
    4. Enhance detection rules (prevent future)

Category 3: Vulnerability Disclosure (15-month tracking)
  Definition: Newly discovered CVE affecting BES Cyber Systems
  Insa Sensor Actions:
    1. Alert if sensor detects vulnerable system
    2. Track remediation per CIP-007 timeline
    3. Escalate if patch not applied by day 30
```

### Grid Emergency Scenarios

#### Scenario A: Coordinated Attack on Multiple Substations
```yaml
Detection:
  - Insa sensor detects simultaneous DNP3 control commands to 3+ substations
  - Commands originate from IP outside normal SCADA range
  - Timestamp: Within 5-minute window (coordinated)

Response (per EOP-008 Cyber Recovery Plan):
  1. Immediately notify Reliability Coordinator (RC)
  2. Activate backup control center (if primary compromised)
  3. Isolate affected SCADA segments (if safe)
  4. Switch to manual control (operator at substation)
  5. Engage cyber mutual assistance (E-ISAC members)

Insa Support:
  - Provide real-time threat intelligence (IOCs)
  - Assist with forensic analysis (Wireshark, DNP3 dissectors)
  - Coordinate with other utilities (if regional attack)
```

#### Scenario B: Insider Threat (Authorized User Gone Rogue)
```yaml
Detection:
  - Authorized engineer workstation (whitelisted IP)
  - Issues abnormal commands (e.g., trip all feeders)
  - Outside normal work hours (3 AM vs. 9 AM maintenance)

Response:
  1. Do NOT block immediately (may be legitimate emergency)
  2. Voice confirmation: Call engineer's desk + mobile
  3. If unconfirmed: Revoke access credentials (Active Directory)
  4. Review: Audit logs for past 90 days (CIP-007 requirement)

Insa Sensor Intelligence:
  - Correlate: User login time vs. command time
  - Behavior analysis: Deviation from historical patterns
  - Evidence: Screenshots, keystroke logs (if session recording enabled)
```

---

## Appendix A: Utility Protocol Quick Reference

### DNP3 (Distributed Network Protocol)
```yaml
Use Case: RTU-to-SCADA, substation automation
Port: 20000/TCP (or serial RS-232/485)
Variants:
  - DNP3 Level 2: Basic SCADA
  - DNP3 Level 3: Advanced features (time sync, file transfer)
  - DNP3 Secure Authentication (SAv5): Encrypted, rare deployment

Critical Function Codes:
  - 0x01: READ
  - 0x02: WRITE
  - 0x05: OPERATE (direct control - high risk)
  - 0x14: COLD_RESTART (reboot RTU)
  - 0x1C: READ_FILE_INFO (reconnaissance)

Security Concerns:
  - No native encryption (plaintext)
  - Replay attacks (if no sequence numbers)
  - Spoofing (IP-based authentication only)

Monitoring Focus:
  - OPERATE commands from unauthorized masters
  - Firmware uploads (function 0x1C + file transfer)
  - Excessive polling (DDoS to RTU)
```

### IEC 61850 (Substation Automation)
```yaml
Use Case: Digital substations, IED communication
Protocols:
  - MMS (Manufacturing Message Specification): Port 102/TCP
  - GOOSE (Generic Object-Oriented Substation Event): Multicast, Layer 2
  - Sampled Values (SV): High-speed sampling, multicast

GOOSE Messages:
  - Purpose: Fast protection signaling (<4ms)
  - Format: Ethernet multicast (01-0C-CD-01-00-XX)
  - Use: Trip commands, interlocking, status
  - Security: NO encryption, MAC-based filtering only

Critical Services (MMS):
  - GetDirectory (asset discovery)
  - SetDataValues (write to IED)
  - SelectWithValue (circuit breaker control prep)
  - Operate (execute control)

Security Concerns:
  - GOOSE replay attacks (capture/replay trip command)
  - MMS write access (often unrestricted)
  - Engineering access (SCL files expose full config)

Monitoring Focus:
  - GOOSE from unauthorized MAC addresses
  - MMS write commands outside maintenance windows
  - Engineering software connections (IET600, DigSilent)
```

### IEC 60870-5-104 (European SCADA)
```yaml
Use Case: Common in EU utilities, increasing in U.S.
Port: 2404/TCP
Similar to: DNP3 (but different encoding)

Critical ASDUs (Application Service Data Units):
  - C_SC_NA_1: Single command (OPERATE)
  - C_DC_NA_1: Double command (ON/OFF)
  - M_SP_NA_1: Single-point status (read)

Security Concerns:
  - Less common in U.S. = less understood by defenders
  - No built-in encryption (use VPN/IPsec)
  - Originator address (OA) can be spoofed

Monitoring Focus:
  - Control commands (C_* ASDU types)
  - Interrogation floods (DoS risk)
```

### ICCP / TASE.2 (Inter-Control Center Protocol)
```yaml
Use Case: Data exchange between utilities (load, voltage, schedules)
Port: 102/TCP (same as IEC 61850 MMS - can confuse firewalls)
Bilateral Agreements: Each pair of utilities has legal agreement

Data Blocks:
  - Actual net interchange (MW flow)
  - Frequency deviation
  - Voltage profiles
  - Scheduled interchanges

Security Concerns:
  - Man-in-the-middle (if not encrypted)
  - Data injection (false load data to neighboring BA)
  - Cascading failures (bad data propagates)

Monitoring Focus:
  - Connections from IPs outside bilateral agreement list
  - Data values outside statistical norms (>3 sigma)
  - Unscheduled data updates (normal: 1-minute intervals)
```

---

## Appendix B: NERC Audit Preparation

### Evidence Collection (Insa Sensor Assists)

```yaml
CIP-005 Evidence:
  [ ] Network diagram showing ESP boundary + sensor location
  [ ] Firewall rules (sensor management access)
  [ ] VPN configuration (if remote access enabled)
  [ ] Evidence of review: Annual ESP boundary verification

CIP-007 Evidence:
  [ ] Ports & services list (from sensor config export)
  [ ] Patch management logs (sensor updates within 35 days)
  [ ] Security event logs (90-day retention verified)
  [ ] Password policy compliance (complexity, age)

CIP-010 Evidence:
  [ ] Baseline configuration file (dated <15 months ago)
  [ ] Change control tickets referencing sensor
  [ ] Vulnerability scan reports (sensor included)
  [ ] Integrity monitoring alerts (if config drift detected)

CIP-011 Evidence:
  [ ] BCSI designation: Sensor contains diagrams, IP lists
  [ ] Encryption verification: TLS 1.2+ for all management
  [ ] Access control list: Only authorized users can login
  [ ] Disposal procedure: Document for sensor decommissioning

Audit Tips:
  - Insa provides "CIP Compliance Package" (pre-formatted evidence)
  - Export logs in auditor-friendly format (CSV, PDF)
  - Screenshots of sensor UI showing timestamp sync (CIP-007 R6)
```

---

## Appendix C: Contact & Escalation

```yaml
Insa Automation Corp:
  Sales Engineering: w.aroca@insaing.com
  NERC CIP Support: cip-support@insaing.com (if available)
  24/7 SOC: noc@insaing.com

Utility Escalation (Client-Specific):
  Tier 1: System Operator (real-time grid operations)
    - Phone: ___________
    - Response: Immediate (for grid impact)

  Tier 2: SCADA Administrator (technical issues)
    - Phone: ___________
    - Response: <1 hour

  Tier 3: Cybersecurity Lead (security incidents)
    - Phone: ___________
    - Response: <15 minutes (per CIP-008)

  Tier 4: Senior Manager (CIP responsible)
    - Phone: ___________
    - Response: <1 hour (for reportable incidents)

External Coordination:
  NERC ES-ISAC: https://www.esisac.com (portal login)
  FBI Cyber Division: (local field office)
  CISA (DHS): CISA.gov/report
  E-ISAC (Electricity): E-ISAC.com
```

### Incident Severity Matrix

```yaml
CRITICAL (Response: <5 min, Notify: NERC + FBI + CISA):
  - Active grid attack (breakers tripping)
  - Malware on EMS/SCADA
  - Loss of situational awareness (operator displays down)
  - Unauthorized control center access

HIGH (Response: <15 min, Notify: CIP Manager + SOC):
  - Attempted unauthorized access (blocked)
  - Protocol anomaly detected
  - Vulnerability exploitation attempt
  - Data exfiltration of BCSI

MEDIUM (Response: <1 hour, Notify: Cybersecurity team):
  - Policy violation (change w/o approval)
  - Asset configuration drift
  - Failed authentication (not threshold)

LOW (Response: Next business day, Notify: Weekly report):
  - Informational alerts
  - Asset inventory updates
  - Certificate expiration warnings (>30 days out)
```

---

**Document Control**
Version: 1.0
Author: Insa Automation Corp
Date: October 11, 2025
Classification: Client Confidential - NERC CIP BCSI
Review Cycle: Annual (or upon standard revision)

**Made by Insa Automation Corp for OpSec**
