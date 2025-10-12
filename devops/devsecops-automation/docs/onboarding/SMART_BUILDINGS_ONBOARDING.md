# Smart Buildings Sector - Client Onboarding Playbook
**Insa Automation Corp | Building Automation Security**
Version: 1.0 | Date: October 11, 2025

---

## Executive Summary

Smart buildings integrate Building Management Systems (BMS), HVAC, lighting, access control, and energy management. This playbook addresses the unique challenges of securing multi-tenant commercial buildings, campuses, and intelligent facilities.

### Sector Characteristics
- **Critical Priority**: Occupant comfort and safety, energy efficiency
- **Key Assets**: BMS, HVAC controllers, lighting systems, access control, fire alarm
- **Common Protocols**: BACnet, Modbus, MQTT, LonWorks, KNX
- **Risk Profile**: Ransomware, physical security bypass, tenant data privacy
- **Unique Challenge**: Multi-tenant isolation, legacy protocol integration
- **Energy Focus**: LEED certification, utility demand response, carbon reporting

---

## Phase 1: Pre-Sales Discovery

### Discovery Questionnaire

#### Building Profile
```yaml
Property Type:
  [ ] Commercial office building
  [ ] Mixed-use (retail + residential + office)
  [ ] Data center
  [ ] Hospital/Healthcare
  [ ] University campus
  [ ] Hotel/Hospitality
  [ ] Government facility
  [ ] Industrial facility with office buildings

Building Details:
  - Square footage: _______ sq ft
  - Number of floors: _______
  - Year built: _______ (impacts legacy systems)
  - LEED certification: [ ] Platinum [ ] Gold [ ] Silver [ ] Certified [ ] None
  - Occupancy: _______ people (average)
  - Operating hours: [ ] 24/7 [ ] Business hours [ ] Mixed

Multi-Tenant:
  [ ] Single tenant (owner-occupied)
  [ ] Multi-tenant (shared building)
  - Number of tenants: _______
  - Tenant types: [ ] Corporate [ ] Retail [ ] Residential [ ] Mixed
  - Tenant network isolation: [ ] Yes [ ] No [ ] Partial
```

#### Building Automation Systems (BAS/BMS)
```yaml
Primary BMS Platform:
  [ ] Johnson Controls Metasys
  [ ] Schneider Electric (Andover Continuum, EcoStruxure)
  [ ] Siemens Desigo
  [ ] Honeywell Enterprise Buildings Integrator (EBI)
  [ ] Tridium Niagara
  [ ] Delta Controls enteliWEB
  [ ] Custom/Proprietary: _______

BMS Architecture:
  - Central server location: _______
  - Number of controllers: _______
  - Operator workstations: _______
  - Web-based access: [ ] Yes [ ] No
  - Mobile app: [ ] Yes [ ] No (vendor: ______)

Protocols in Use:
  [ ] BACnet/IP (UDP 47808) - Most common
  [ ] BACnet/MSTP (serial, RS-485)
  [ ] Modbus TCP (port 502)
  [ ] LonWorks (ISO/IEC 14908)
  [ ] KNX (European standard, TP/IP)
  [ ] MQTT (port 1883/8883) - IoT devices
  [ ] Proprietary (vendor-specific)
```

#### HVAC (Heating, Ventilation, Air Conditioning)
```yaml
HVAC Control:
  - Chiller plant: _____ tons (cooling capacity)
  - Boiler plant: _____ BTU/hr (heating capacity)
  - Air Handling Units (AHUs): _____ units
  - Variable Air Volume (VAV) boxes: _____ units
  - Fan Coil Units (FCUs): _____ units

Control Hierarchy:
  - BMS: Central supervisory control (setpoints, schedules)
  - DDC (Direct Digital Controllers): Zone-level control (per floor, per zone)
  - Sensors: Temperature, humidity, CO2, pressure
  - Actuators: Dampers, valves, VFDs (Variable Frequency Drives)

Energy Management:
  - Demand response: [ ] Yes [ ] No (utility program)
  - Load shedding: [ ] Automated [ ] Manual [ ] None
  - Energy metering: [ ] Sub-metered (per tenant) [ ] Whole-building [ ] None
  - Renewable energy: [ ] Solar [ ] Geothermal [ ] None
```

#### Lighting Control Systems
```yaml
Lighting Platform:
  [ ] Lutron (Quantum, Vive)
  [ ] Philips (Dynalite)
  [ ] Crestron
  [ ] Integrated with BMS (BACnet)
  [ ] Manual switches only (no automation)

Features:
  [ ] Daylight harvesting (auto-dim based on natural light)
  [ ] Occupancy sensing (PIR, ultrasonic)
  [ ] Scheduled lighting (7 AM on, 7 PM off)
  [ ] Emergency lighting (fire alarm integration)

Protocol:
  [ ] DMX512 (theatrical lighting)
  [ ] DALI (Digital Addressable Lighting Interface)
  [ ] BACnet (integrated with BMS)
  [ ] KNX
  [ ] MQTT (smart LED fixtures)
```

#### Physical Access Control Systems (PACS)
```yaml
Access Control Platform:
  [ ] Honeywell ProWatch
  [ ] Lenel OnGuard
  [ ] Genetec Security Center
  [ ] S2 Security
  [ ] HID Global
  [ ] Brivo (cloud-based)
  [ ] Integrated with BMS: [ ] Yes [ ] No

Components:
  - Card readers: _____ (RFID, NFC, biometric)
  - Electronic locks: _____ (mag locks, electric strikes)
  - Turnstiles/gates: _____
  - Visitor management: [ ] Yes [ ] No (vendor: ______)

Integration:
  [ ] Fire alarm (auto-unlock doors on alarm)
  [ ] Video surveillance (badge + camera correlation)
  [ ] Elevator control (badge for floor access)
  [ ] BMS (HVAC follows occupancy)

Security Concerns:
  - Badge cloning: [ ] Mitigated (encrypted cards) [ ] Risk (legacy Wiegand)
  - Shared credentials: [ ] Yes (cleaning crew) [ ] No (individual badges)
  - Remote unlock: [ ] Yes (security desk) [ ] No
```

#### Fire Alarm & Life Safety
```yaml
Fire Alarm System:
  - Vendor: [ ] Simplex [ ] Notifier [ ] Edwards [ ] Other: _______
  - Protocol: [ ] BACnet [ ] Proprietary [ ] Analog
  - Integration with BMS: [ ] Yes (smoke damper control, HVAC shutdown) [ ] No

CRITICAL MONITORING POLICY:
  ⚠️ Life safety systems (fire alarm): EXCLUDED from active monitoring
  ✅ Network boundary monitoring: Allowed (traffic to/from fire panel)
  ✅ Integration points: Monitor BMS commands to fire system (e.g., HVAC shutdown)
  ⚠️ Any monitoring requires: Fire marshal approval + UL/NFPA compliance review

Emergency Systems:
  [ ] Emergency lighting (battery-backed)
  [ ] Voice evacuation (EVAC)
  [ ] Smoke control (stairwell pressurization)
  [ ] Elevator recall (firefighter service)
```

#### Network Infrastructure
```yaml
Building Network Topology:
  [ ] Flat network (all systems same subnet) - HIGH RISK
  [ ] VLAN segmentation (by system type)
  [ ] Dedicated OT network (air-gapped from IT)
  [ ] Converged IT/OT (shared infrastructure)

Network Ownership:
  [ ] Building owner (facilities team)
  [ ] Tenant IT departments (multi-tenant complexity)
  [ ] Managed service provider (MSP)
  [ ] BMS vendor (outsourced operations)

Connectivity:
  - BMS network: _____ Mbps (typically 10/100 Mbps)
  - Internet access: [ ] Yes (cloud BMS, remote vendor) [ ] No (air-gapped)
  - Remote access: [ ] VPN [ ] Cloud portal [ ] TeamViewer/LogMeIn [ ] None
  - Wireless: [ ] Wi-Fi for BMS (risky) [ ] Wired only (preferred)

IoT Devices (Growing Trend):
  [ ] Smart thermostats (Nest, Ecobee)
  [ ] Occupancy sensors (Cisco Meraki, Vergesense)
  [ ] Air quality monitors (Awair, Kaiterra)
  [ ] Smart plugs (energy monitoring)
  [ ] IP cameras (surveillance)

  IoT Security Concerns:
    - Default credentials (often unchanged)
    - No patching (abandoned devices)
    - Cloud dependencies (vendor shutdown = device brick)
    - VLAN isolation: [ ] Yes (IoT quarantine) [ ] No (same as BMS)
```

#### Compliance & Standards
```yaml
Energy & Environmental:
  [ ] LEED (Leadership in Energy & Environmental Design)
      - Certification level: _______
      - Energy monitoring required: Yes (prerequisite)
  [ ] Energy Star (EPA)
  [ ] WELL Building Standard (health & wellness)
  [ ] ISO 50001 (Energy Management)

Cybersecurity:
  [ ] NIST CSF (Cybersecurity Framework) - Maturity: Tier _____
  [ ] ISA/IEC 62443 (Industrial Cybersecurity)
  [ ] ISO 27001 (Information Security)
  [ ] HIPAA (if healthcare facility)
  [ ] GDPR/CCPA (if tenant data processed)

Physical Security:
  [ ] ASIS GDL PSC-1 (Security Management for Buildings)
  [ ] UL 2050 (Cybersecurity for Building Automation)
  [ ] NFPA 730 (Security Systems)

Insurance:
  - Cyber insurance: [ ] Yes [ ] No - Coverage: $_______
  - Property insurance: [ ] Covers cyber-physical (e.g., frozen pipes from HVAC hack) [ ] TBD
```

---

## Phase 2: Site Assessment

### Pre-Deployment Checklist

#### Week 1: Remote Discovery
```yaml
Documentation Review:
  [ ] Building floor plans (architectural)
  [ ] BMS network diagram
  [ ] HVAC sequence of operations (SOO)
  [ ] Lighting control diagrams
  [ ] Access control zones
  [ ] Fire alarm riser diagram
  [ ] IT network topology (if converged)

Energy & Operational Data:
  [ ] Utility bills (1 year) - identify anomalies
  [ ] BMS alarm history (1 month) - noise level
  [ ] Energy dashboard access (if available)
  [ ] Tenant comfort complaints (indicates HVAC issues)

Remote Access Test (if permitted):
  [ ] VPN to BMS (verify connectivity)
  [ ] Web portal access (operator view)
  [ ] Review: User accounts (default passwords?)
  [ ] Review: Software versions (patching status)
```

#### Week 2: On-Site Assessment (1-2 days)
```yaml
Arrival & Orientation:
  [ ] Check in with building management
  [ ] Escort: Facilities manager or chief engineer
  [ ] PPE: Safety glasses, hard hat (mechanical rooms)

BMS Central Plant Tour:
  [ ] Chiller room (cooling plant)
      - Chiller controllers (often networked)
      - Chilled water pumps, cooling towers
      - Energy efficiency (kW/ton)

  [ ] Boiler room (heating plant)
      - Boiler controllers (burner management)
      - Hot water pumps, expansion tanks
      - Natural gas/oil supply (safety interlocks)

  [ ] Electrical room (power distribution)
      - Main switchgear, panels
      - Energy meters (sub-metering)
      - UPS for critical systems (BMS, fire alarm)

BMS Server Room:
  [ ] BMS server(s) location
  [ ] Operator workstations
  [ ] Network switches (optimal SPAN port location)
  [ ] Environmental: HVAC, temperature monitoring
  [ ] Physical security: Locked door, badge access

Floor-by-Floor Walkthrough (Sample Floors):
  [ ] Typical office floor:
      - VAV boxes (above ceiling)
      - Temperature sensors (wall-mounted)
      - Lighting control panels
      - Access card readers

  [ ] Common areas (lobby, conference rooms):
      - Visitor management kiosk
      - Digital signage (networked?)
      - Public Wi-Fi (isolated from BMS?)

  [ ] Parking garage:
      - CO sensors (ventilation control)
      - Lighting (occupancy/daylight)
      - Access gates (integrated with PACS)

Interviews:
  [ ] Facilities manager (operational priorities)
  [ ] Chief engineer (HVAC expertise, maintenance windows)
  [ ] IT manager (network architecture, segmentation)
  [ ] Security manager (PACS, camera systems)
  [ ] Tenants (if applicable, comfort concerns)
```

---

## Phase 3: Network Diagram Template

### Smart Building Network Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                      CORPORATE IT NETWORK                         │
│  (Tenant networks, internet, office applications)                │
└────────────────────────────┬─────────────────────────────────────┘
                             │
                   ┌─────────▼─────────┐
                   │  Firewall (IT/OT) │
                   │  VLAN Routing     │
                   └─────────┬─────────┘
                             │
┌─────────────────────────────┴──────────────────────────────────────┐
│                    BUILDING AUTOMATION NETWORK                      │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  BMS Server  │  │  Lighting    │  │  Access      │            │
│  │  (Niagara)   │  │  Controller  │  │  Control     │            │
│  │  10.20.1.10  │  │  (Lutron)    │  │  (Lenel)     │            │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘            │
│         │                 │                  │                     │
│         └─────────────────┼──────────────────┘                     │
│                           │                                        │
│                 ┌─────────▼─────────┐                              │
│                 │  OT Core Switch   │ ◄── MONITORING POINT        │
│                 │  (SPAN Port)      │     Insa Sensor: 10.20.1.250│
│                 └─────────┬─────────┘                              │
│                           │                                        │
└───────────────────────────┼────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┬─────────────────┐
        │                   │                   │                 │
┌───────▼───────┐  ┌────────▼────────┐  ┌──────▼─────┐  ┌────────▼────────┐
│ HVAC Network  │  │ Lighting Network│  │ PACS       │  │ IoT Devices     │
│ VLAN 100      │  │ VLAN 200        │  │ VLAN 300   │  │ VLAN 400        │
│ BACnet/IP     │  │ DMX/DALI/BACnet │  │ Proprietary│  │ MQTT/HTTP       │
└───────┬───────┘  └────────┬────────┘  └──────┬─────┘  └────────┬────────┘
        │                   │                   │                 │
┌───────▼────────────────────▼───────────────────▼─────────────────▼────────┐
│                     FIELD DEVICES (LEVEL 0)                                │
│                                                                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ Chiller  │  │ AHU      │  │ VAV Box  │  │ Card     │  │ Smart    │  │
│  │ DDC      │  │ DDC      │  │ (zone)   │  │ Reader   │  │ Thermo   │  │
│  │ BACnet   │  │ BACnet   │  │ MSTP     │  │ Wiegand  │  │ MQTT     │  │
│  │10.20.10.1│  │10.20.10.2│  │10.20.10.x│  │10.20.30.x│  │10.20.40.x│  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
│  (Mechanical   (Air Handling) (Per floor)  (Per door)    (Per room)     │
│   room)                                                                  │
└──────────────────────────────────────────────────────────────────────────┘

        ⚠️ LIFE SAFETY NETWORK (ISOLATED) ⚠️
┌──────────────────────────────────────────────────────────────────────────┐
│                  FIRE ALARM SYSTEM - EXCLUDED                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │ Fire Alarm   │  │ Smoke        │  │ Sprinkler    │                  │
│  │ Panel (FACP) │  │ Detectors    │  │ Flow Switch  │                  │
│  │ (Simplex)    │  │              │  │              │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│  Interface to BMS: Dry contact relay ONLY (no IP monitoring)            │
└──────────────────────────────────────────────────────────────────────────┘

MULTI-TENANT ISOLATION:
┌──────────────────────────────────────────────────────────────────────────┐
│                      TENANT NETWORKS (ISOLATED)                           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐            │
│  │ Tenant A       │  │ Tenant B       │  │ Tenant C       │            │
│  │ Floors 1-5     │  │ Floors 6-10    │  │ Floors 11-15   │            │
│  │ VLAN 501       │  │ VLAN 502       │  │ VLAN 503       │            │
│  │ No BMS access  │  │ No BMS access  │  │ No BMS access  │            │
│  └────────────────┘  └────────────────┘  └────────────────┘            │
│  Tenants do NOT see each other or BMS network (security requirement)    │
└──────────────────────────────────────────────────────────────────────────┘

LEGEND:
═══════  Critical HVAC control path
───────  Standard monitoring allowed
◄── SPAN Sensor monitoring point
🔒      VLAN isolation boundary
⚠️      Life safety - NO monitoring
```

### VLAN Segmentation Best Practice
```yaml
VLAN 10: BMS Management (Servers, Workstations)
  - 10.20.1.0/24
  - Access: Facilities team only
  - Security: MFA, strong passwords

VLAN 100: HVAC Control (DDC controllers, chillers, boilers)
  - 10.20.10.0/24
  - Protocol: BACnet/IP, Modbus TCP
  - Monitoring: Insa sensor (primary focus)

VLAN 200: Lighting Control
  - 10.20.20.0/24
  - Protocol: DALI, DMX, BACnet
  - Integration: Time schedules from BMS

VLAN 300: Physical Access Control
  - 10.20.30.0/24
  - Protocol: Proprietary (Lenel, Honeywell)
  - Security: PCI-DSS if integrated with payment (parking)

VLAN 400: IoT Devices (Quarantine)
  - 10.20.40.0/24
  - High risk: Default passwords, no patching
  - Firewall: Deny inbound, allow outbound only (cloud reporting)

VLAN 500+: Tenant networks (isolated per tenant)
  - 10.30.x.0/24 (where x = tenant ID)
  - No access to BMS VLANs
  - Internet-facing only
```

---

## Phase 4: Installation Procedure

### Pre-Installation (1-2 weeks)

#### Building Access & Coordination
```yaml
Approvals:
  [ ] Building management approval
  [ ] Tenant notification (if multi-tenant, "network maintenance")
  [ ] Facilities team coordination (access to server room, mechanical rooms)
  [ ] IT department (if converged network)

Change Control:
  [ ] Change ticket submitted (building management system)
  [ ] Impact analysis: "Passive monitoring, no BMS changes"
  [ ] Installation window: Non-business hours (e.g., Saturday morning)
  [ ] Rollback plan: Remove SPAN port configuration

Equipment:
  [ ] Insa sensor appliance
  [ ] Network cables (Cat6)
  [ ] Rack mount kit (if server room installation)
  [ ] Power supply (verify voltage: 110V/220V)
  [ ] Laptop with configuration tools
  [ ] BACnet discovery tools (YABE, Visual BACnet, if needed)
```

### Installation Day

#### Hour 0-1: Physical Setup
```yaml
Site Arrival:
  [ ] Check in with building security
  [ ] Escort: Facilities manager or chief engineer
  [ ] Access to BMS server room / network closet

Sensor Installation:
  [ ] Install in BMS network rack (secure, climate-controlled)
  [ ] Connect to UPS (if available)
  [ ] Cable to OT core switch (SPAN port destination)
  [ ] Label cables: "Insa Sensor - Security Monitoring"
  [ ] Power on, verify boot (console cable or remote KVM)
```

#### Hour 1-2: Network Configuration
```yaml
SPAN Port Configuration (OT Switch):
  Target VLANs:
    - VLAN 100 (HVAC)
    - VLAN 200 (Lighting) - optional
    - VLAN 300 (PACS) - optional (privacy concerns, coordinate with security)

  Example (Cisco):
    monitor session 1 source vlan 100 rx
    monitor session 1 destination interface Gi1/0/24
    ! Gi1/0/24 = Insa sensor

  [ ] Verify: tcpdump shows BACnet traffic (UDP 47808)
  [ ] Verify: No packet loss (SPAN oversubscription check)

Management Network:
  [ ] Static IP: 10.20.1.250 (BMS management VLAN)
  [ ] Subnet: 255.255.255.0
  [ ] Gateway: 10.20.1.1
  [ ] DNS: (building or corporate DNS)
  [ ] NTP: (corporate NTP server)
  [ ] Firewall rule: Allow sensor to send email/syslog alerts
```

#### Hour 2-3: Protocol Configuration (Smart Buildings)
```yaml
Protocol Parsers:
  [ ] BACnet/IP (UDP 47808):
      - Most common in smart buildings
      - Device discovery: Who-Is broadcast
      - Object types: Analog Input, Binary Output, Schedule, etc.

  [ ] BACnet/MSTP (serial, if present):
      - Over RS-485 networks
      - Requires serial-to-Ethernet converter

  [ ] Modbus TCP (port 502):
      - Legacy HVAC controllers
      - Energy meters (power monitoring)

  [ ] MQTT (port 1883/8883):
      - IoT devices (smart thermostats, sensors)
      - Topic structure: building/floor/room/device

  [ ] Proprietary protocols:
      - LonWorks (limited parser availability)
      - KNX (European, rare in U.S.)
      - Vendor-specific (Johnson Controls N2, etc.)

BACnet Asset Discovery:
  [ ] Enable BACnet scanner (Who-Is broadcast)
  [ ] Wait 15 minutes for responses (I-Am messages)
  [ ] Export device list: Object name, Object instance, IP address
  [ ] Compare to known BMS inventory (identify rogue devices)

Baseline Learning Mode:
  [ ] Duration: 7-14 days (buildings have weekly schedules)
  [ ] Capture: Weekday vs. weekend patterns (HVAC setback)
  [ ] Capture: Seasonal variations (heating vs. cooling)
  [ ] Occupancy patterns: 7 AM ramp-up, 6 PM setback
  [ ] Alarm rate baseline: Normal HVAC alarms (sensor faults, etc.)
```

#### Hour 3-4: Integration & Testing
```yaml
Alert Configuration (Smart Buildings):
  Critical Alerts:
    - Unauthorized BACnet writes (Priority Array override)
    - Chiller/boiler emergency stop command (from network)
    - New BACnet device (rogue controller)
    - Access control database modification (badge cloning)

  High Alerts:
    - BMS password change (unauthorized user)
    - Abnormal HVAC schedule change (after-hours heating)
    - IoT device communication to unknown cloud (data exfiltration)
    - MQTT credential change (smart device compromise)

  Medium Alerts:
    - Failed BMS login attempts (brute force)
    - BACnet communication timeout (controller offline)
    - Energy anomaly (unexpected consumption spike)

  Notification:
    - Email: facilities@client.com, security@client.com
    - SMS: Chief engineer (CRITICAL only, after-hours)
    - Building dashboard: Real-time alert widget

Integration with Building Systems:
  [ ] CMMS (Computerized Maintenance Management System):
      - Auto-create work orders for critical alerts
      - Example: "Unauthorized BMS access - investigate"

  [ ] Energy Management Platform:
      - Forward energy data for carbon reporting
      - LEED certification evidence

  [ ] Tenant portal (if applicable):
      - Anonymized comfort metrics (no security details)
      - "Building is secure" status indicator

Functional Testing:
  [ ] BACnet traffic: Visible in sensor dashboard
  [ ] Asset discovery: All major controllers found (>95%)
  [ ] Test alert: Generate safe alert (test device)
  [ ] Email delivery: Verify receipt by facilities team
  [ ] BMS operation: No latency increase, no alarms
  [ ] Occupant comfort: No complaints (HVAC normal)
```

---

## Phase 5: Sector-Specific Monitoring Templates

### Smart Building Detection Rules

#### Rule Set 1: BACnet Security
```yaml
Name: Unauthorized BACnet Priority Override
Severity: CRITICAL
Trigger:
  - BACnet: WriteProperty to Priority Array (slots 1-16)
  - Target: HVAC setpoints, damper positions, valve commands
  - Source: NOT in authorized BMS operator list
  - Priority: High-priority slot (1-8, manual override)
Action:
  - Immediate alert to facilities manager
  - Identify: Which controller? Which point? What value?
  - Revert: BMS operator restores original setpoint
  - Investigate: Compromised BMS account? Rogue device?

Context:
  - BACnet Priority Array: 16 slots (1=highest, 16=lowest)
  - Slot 1-8: Manual override (operator, emergency)
  - Slot 9-16: Automated (schedules, logic)
  - Attack: Attacker writes priority 1 (overrides all automation)

Whitelist:
  - BMS server: 10.20.1.10
  - Operator workstations: 10.20.1.11-15
  - Vendor remote access: (IP range, if VPN)
```

#### Rule Set 2: HVAC Tampering
```yaml
Name: Chiller Emergency Stop (Network Command)
Severity: CRITICAL (Building Impact)
Trigger:
  - BACnet: WriteProperty to chiller enable point (value=OFF)
  - Or: Modbus write to chiller run command (value=0)
  - Source: Unexpected (not BMS schedule or operator)
Action:
  - URGENT: Alert chief engineer (SMS)
  - Impact: Building cooling loss (occupant discomfort, server room overheating)
  - Response: Manual restart via BMS or chiller local panel
  - Investigation: Cyber attack vs. system malfunction?

Context:
  - Chiller shutdown: Can cause $100K+ damage (frozen pipes in winter if heating lost)
  - Occupant safety: Heatstroke risk in summer (elderly, healthcare facilities)
  - Data center cooling: Server shutdown if CRAC units fail

Prevention:
  - BMS access control: Least privilege (not all users can stop chillers)
  - Physical lockout: Critical equipment has key-switch override
  - Monitoring: Insa sensor detects unauthorized commands before impact
```

#### Rule Set 3: Physical Security Bypass
```yaml
Name: Access Control Database Modification
Severity: HIGH (Physical Security Risk)
Trigger:
  - Access control system: User database write (add user, change permissions)
  - Or: Badge ID cloning detected (same badge, two locations simultaneously)
  - Or: Door unlock command (outside normal pattern)
Action:
  - Alert security manager
  - Review: Who was added? What access granted?
  - Badge audit: Compare to HR database (terminate stale badges)
  - Camera correlation: Video of person using cloned badge

Context:
  - Insider threat: Disgruntled employee adds badge for accomplice
  - Credential theft: Stolen laptop with PACS software
  - Social engineering: "IT support" tricks security into granting access

Integration:
  - Insa sensor monitors: PACS network traffic (badge add/delete commands)
  - Does NOT replace: PACS native audit logs (use both for full visibility)
```

#### Rule Set 4: IoT Device Compromise
```yaml
Name: Smart Thermostat C2 Communication
Severity: MEDIUM (Potential Botnet)
Trigger:
  - MQTT or HTTP: IoT device (smart thermostat, sensor) communicates to unknown IP
  - Destination: NOT vendor's cloud (e.g., NOT ecobee.com, NOT nest.com)
  - Pattern: Beaconing (periodic check-in to command-and-control server)
Action:
  - Isolate device: Move to quarantine VLAN (if possible)
  - Investigate: Factory reset device, update firmware
  - Vendor notification: Report compromised device model

Context:
  - Mirai botnet (2016): IoT devices (cameras, DVRs) recruited for DDoS
  - Smart building risk: Thousands of IoT devices = large attack surface
  - Default passwords: "admin/admin" (never changed by installer)

Prevention:
  - VLAN isolation: IoT devices in separate VLAN (VLAN 400)
  - Firewall: Deny inbound, allow outbound to vendor cloud only (whitelist IPs)
  - Password policy: Force change on first boot (if device supports)
```

#### Rule Set 5: Energy Theft Detection
```yaml
Name: Tenant Energy Sub-Meter Tampering (Multi-Tenant)
Severity: MEDIUM (Financial Fraud)
Trigger:
  - Energy meter: Modbus register write (meter calibration factor)
  - Result: Under-reporting of energy usage (tenant pays less)
  - Detection: Comparison of tenant sub-meters vs. main building meter (mismatch)
Action:
  - Alert property management
  - Investigate: Which tenant? Meter location?
  - Financial audit: Recalculate energy bills (back-charge tenant)

Context:
  - Multi-tenant billing: Tenants pay proportional energy costs
  - Incentive: Malicious tenant manipulates meter to reduce bill
  - Attack vector: Unsecured Modbus TCP (no authentication)

Prevention:
  - Meter network: Separate VLAN, read-only access to tenants
  - Tamper detection: Physical seals on meters (like residential meters)
  - Insa monitoring: Log all writes to meter registers (audit trail)
```

### Smart Building KPIs

```yaml
Operational Metrics:
  - BMS uptime: 99.9%+
  - HVAC response time: <5 minutes (comfort complaint to resolution)
  - Energy efficiency: kWh per sq ft per year (track trend)
  - Occupant comfort score: Survey-based (quarterly)

Security Metrics:
  - Unauthorized BACnet commands: Target ZERO
  - Rogue device detection: <1 hour (from appearance to alert)
  - PACS audit log review: 100% compliance (daily review)
  - IoT device vulnerability: <5% (outdated firmware)

Compliance Metrics (LEED):
  - Energy monitoring: 100% sub-metering coverage
  - Reporting: Monthly energy reports to LEED portal
  - Anomaly detection: Flag energy waste (e.g., after-hours HVAC)

Asset Management:
  - BMS asset inventory accuracy: 95%+
  - Firmware version tracking: 90%+
  - Unauthorized device detection: <1 hour
  - Device lifecycle management: Replace EOL devices (5-7 year cycle)
```

---

## Phase 6: Compliance Requirements

### LEED (Green Building Certification)

```yaml
Energy & Atmosphere (EA) Credit:
  EA Prerequisite 3: Fundamental Commissioning & Verification
    - Insa sensor: Monitor BMS sequences of operation (SOO)
    - Verify: HVAC operates per design intent
    - Evidence: Trending data for LEED auditor

  EA Credit 3: Advanced Energy Metering
    - Requirement: Sub-metering of major energy uses (HVAC, lighting, plug loads)
    - Insa sensor: Collect Modbus data from energy meters
    - Reporting: Automated reports to LEED portal

  EA Credit 5: Optimize Energy Performance
    - Goal: Reduce energy use vs. baseline (ASHRAE 90.1)
    - Insa contribution: Detect energy waste (e.g., simultaneous heating/cooling)
    - Alerts: "AHU-3 heating and cooling valves both open" (economizer fault)

Innovation (IN) Credit:
  IN Credit: Cybersecurity for Smart Buildings (Pilot Credit)
    - Emerging: LEED recognizes cybersecurity as sustainability (business continuity)
    - Insa sensor: Evidence of OT security monitoring
    - Documentation: Incident response plan, penetration test results
```

### ISO 50001 (Energy Management)

```yaml
Energy Performance Indicators (EnPIs):
  [ ] kWh per sq ft per year (normalized for weather)
  [ ] kWh per occupant per day
  [ ] Peak demand (kW) - reduce utility demand charges

Insa Sensor Support:
  [ ] Continuous monitoring of energy meters (Modbus, BACnet)
  [ ] Anomaly detection: Sudden increase (equipment fault, unauthorized use)
  [ ] Regression analysis: Energy vs. outside air temperature (verify correlation)

Management Review:
  [ ] Quarterly energy reports (auto-generated from Insa data)
  [ ] Action items: Fix identified inefficiencies (e.g., stuck dampers)
```

### UL 2050 (Cybersecurity for Building Automation)

```yaml
Requirements:
  [ ] Risk assessment (building automation systems)
  [ ] Network segmentation (IT/OT separation)
  [ ] Access control (least privilege, MFA)
  [ ] Security monitoring (continuous, not just annual audit)
  [ ] Incident response plan (tested annually)

Insa Compliance Support:
  [ ] Network segmentation verification: Map VLANs, identify violations
  [ ] Continuous monitoring: 24/7 detection (exceeds UL 2050 requirement)
  [ ] Audit evidence: Logs, alerts, response actions (timestamped)

Certification Process:
  [ ] Third-party audit by UL-approved lab
  [ ] Insa provides: Technical documentation, system architecture, test results
  [ ] Certification: Valid 3 years, annual surveillance audits
```

### HIPAA (Healthcare Facilities)

```yaml
Applicability:
  - If hospital/clinic: BMS may be in scope (if same network as medical devices)
  - If office building: BMS typically out of scope (no PHI)

HIPAA Security Rule:
  [ ] Access control: Unique user IDs, MFA for BMS
  [ ] Audit controls: Log all BMS access (who, what, when)
  [ ] Integrity controls: Detect unauthorized changes (configuration baselines)
  [ ] Transmission security: Encrypt BMS remote access (VPN, TLS)

Insa Sensor (Healthcare Scenario):
  [ ] Monitor BMS for unauthorized access (protect patient comfort = indirect patient care)
  [ ] NO patient data: Sensor does not touch medical devices, EHR, PACS
  [ ] Physical security: BMS controls HVAC to operating rooms (temp/humidity critical)

Business Associate Agreement (BAA):
  [ ] If Insa has access to PHI: BAA required (unlikely for BMS-only monitoring)
  [ ] If Insa stores BMS logs: NOT PHI (unless logs contain patient names, rooms)
```

---

## Phase 7: Success Criteria

### 30-Day Milestones

```yaml
Week 1 (Discovery & Baseline):
  [ ] 95%+ of BACnet devices discovered (controllers, sensors)
  [ ] Communication patterns documented (BMS polling intervals)
  [ ] Energy baseline established (kWh per day, per sq ft)
  [ ] Zero occupant complaints (HVAC, lighting normal)

Week 2 (Tuning):
  [ ] Alert rules customized (reduce false positives)
  [ ] Integration with CMMS/ticketing system verified
  [ ] Facilities team training completed (dashboard, alerts)
  [ ] Energy anomaly detection: 1st efficiency opportunity identified

Week 3 (Active Monitoring):
  [ ] Transition to enforcement mode (alerts enabled)
  [ ] First security finding: Detected and resolved (e.g., default password)
  [ ] BMS uptime: 100% (no sensor-related issues)
  [ ] Tenant satisfaction: No complaints (multi-tenant)

Week 4 (Optimization):
  [ ] Monthly report generated (security, energy, asset inventory)
  [ ] Quarterly business review scheduled (property management)
  [ ] Continuous improvement plan: Next 3 priorities documented
  [ ] LEED evidence package: Exported for certification audit
```

### Long-Term Success Indicators

```yaml
Building Performance:
  - Energy reduction: 10-20% (by identifying waste, faults)
  - Uptime improvement: BMS availability 99.9%+
  - Occupant comfort: Fewer HVAC complaints (faster issue detection)
  - LEED recertification: Pass audit with zero findings

Security Posture:
  - Cyber incidents: Zero (prevention via early detection)
  - Rogue devices: Detected <1 hour (vs. never detected before)
  - Access control: 100% audit compliance (daily log review)
  - Vendor access: Tracked and approved (no unauthorized remote access)

Business Value:
  - Insurance: Cyber policy premium reduced by 15-25%
  - Property value: Enhanced by cybersecurity + energy efficiency
  - Tenant retention: Happy tenants (comfort, security, sustainability)
  - Expansion: Deploy to additional properties (portfolio-wide)

Regulatory & Certification:
  - LEED: Maintain or upgrade certification (Gold to Platinum)
  - ISO 50001: Pass annual surveillance audit
  - UL 2050: Achieve certification (if pursued)
  - Insurance audits: Zero findings (property, cyber)
```

---

## Phase 8: Multi-Tenant Considerations

### Tenant Isolation Requirements

```yaml
Challenge: Tenants Must NOT Access BMS or Other Tenants
  - Tenant A (Law firm): Requires confidential network (cannot see Tenant B)
  - Tenant B (Startup): Wants control of their own thermostats (but not others)
  - Building owner: Needs global BMS control (energy management, maintenance)

Network Segmentation:
  [ ] VLAN per tenant (e.g., VLAN 501, 502, 503...)
  [ ] Firewall rules: Deny inter-tenant traffic
  [ ] BMS VLAN: Accessible ONLY to building owner (facilities team)
  [ ] Tenant portal: Web-based, read-only (see their own energy use, temperature)

Monitoring Strategy:
  [ ] Insa sensor: Monitors BMS VLAN (owner-controlled HVAC)
  [ ] Insa sensor: Does NOT monitor tenant VLANs (privacy, scope creep)
  [ ] Exception: If tenant contracts separately (Tenant C wants their own monitoring)

Access Control:
  [ ] Tenant employees: Badge access to their suite only (no mechanical rooms)
  [ ] Facilities team: Master access (all floors, mechanical rooms)
  [ ] Vendors: Escorted access (logged, time-limited)
```

### Tenant-Specific Use Cases

```yaml
Scenario 1: Data Center Tenant (High Cooling Demand)
  - Tenant: Colocation provider (server racks on floors 10-12)
  - Need: 24/7 cooling (CRAC units), 99.99% uptime
  - BMS integration: Dedicated AHUs for data center floors
  - Monitoring: Insa sensor alerts if CRAC unit fails (critical for tenant SLA)

Scenario 2: Restaurant Tenant (Lobby Level)
  - Tenant: Restaurant with commercial kitchen
  - Need: Exhaust fans (grease-laden vapor), make-up air
  - BMS integration: Interlock exhaust fan with fire suppression (Ansul system)
  - Monitoring: Insa sensor detects if exhaust fan commanded OFF (fire risk)

Scenario 3: Retail Tenant (Extended Hours)
  - Tenant: 24-hour pharmacy (ground floor)
  - Need: HVAC during off-hours (when rest of building is setback)
  - BMS integration: Zone-specific schedule (floors 1 vs. floors 2-15)
  - Monitoring: Detect unauthorized schedule changes (tenant tries to heat entire building)

Scenario 4: Residential Tenant (Mixed-Use Building)
  - Tenants: Apartments (floors 16-30)
  - Need: Individual thermostats (occupant control), hot water (domestic)
  - BMS integration: Central plant (boilers), distributed fan coils (per unit)
  - Privacy: Insa sensor monitors central plant only (NOT individual apartments)
```

---

## Appendix A: Smart Building Protocol Quick Reference

### BACnet (Building Automation and Control Networks)
```yaml
Standard: ASHRAE/ANSI 135, ISO 16484-5
Port: 47808/UDP (BACnet/IP), Serial (BACnet/MSTP)

Use Case:
  - HVAC controllers (AHU, VAV, chiller, boiler)
  - Lighting control (if integrated)
  - Energy meters (if BACnet-compatible)

Key Services:
  - Who-Is / I-Am: Device discovery (broadcast)
  - ReadProperty / WriteProperty: Read/write values (temp, setpoint, enable)
  - SubscribeCOV: Subscribe to Change-of-Value (efficient updates)

Object Types (Common):
  - Analog Input (AI): Temperature sensor, pressure sensor
  - Analog Output (AO): Valve position, damper position
  - Binary Input (BI): Status (on/off), alarm
  - Binary Output (BO): Command (start/stop, enable/disable)
  - Schedule: Time-based control (7 AM = occupied, 6 PM = unoccupied)

Priority Array (16 Levels):
  - 1-2: Manual override (life safety, operator emergency)
  - 3-7: Temporary operator control
  - 8: Manual operator (standard)
  - 9-15: Automated control (schedules, logic)
  - 16: Default (fallback if all higher priorities are NULL)

Security Concerns:
  - NO native authentication (anyone can write)
  - NO encryption (plaintext)
  - Broadcast discovery (easy reconnaissance)
  - Mitigation: VLAN isolation, BACnet Secure Connect (new, rare)

Monitoring Focus:
  - WriteProperty to critical points (priority 1-8 override)
  - Who-Is scans from unknown IPs (reconnaissance)
  - Device binding changes (attacker replaces controller)
```

### Modbus TCP (Legacy HVAC)
```yaml
Port: 502/TCP
Use Case:
  - Legacy chillers, boilers (pre-BACnet era)
  - Energy meters (common, simple protocol)
  - VFDs (Variable Frequency Drives)

Function Codes:
  - 01: Read Coils (digital outputs)
  - 03: Read Holding Registers (analog values, setpoints)
  - 05: Write Single Coil (ON/OFF command)
  - 06: Write Single Register (setpoint change)
  - 16: Write Multiple Registers (program upload, rare)

Security:
  - NO authentication
  - NO encryption
  - Easy to spoof
  - Common attack: Write to register 40001 (chiller enable = 0)

Monitoring Focus:
  - Write commands (05, 06, 16) from unauthorized IPs
  - Excessive polling (DDoS to meter/controller)
```

### MQTT (IoT Devices)
```yaml
Port: 1883/TCP (unencrypted), 8883/TCP (TLS)
Use Case:
  - Smart thermostats (Nest, Ecobee)
  - Occupancy sensors (Cisco Meraki)
  - Air quality monitors (Awair)

Publish/Subscribe Model:
  - Topic structure: building/floor/room/device/property
  - Example: "building1/floor5/room501/thermostat/temperature"
  - Devices publish: Current state (temp = 72°F)
  - BMS subscribes: Aggregate data for analytics

Security Concerns:
  - Default credentials: "mqtt" / "mqtt" (never changed)
  - No TLS: Credentials in plaintext (packet sniffing)
  - Open broker: Anyone can subscribe (data leakage)

Monitoring Focus:
  - MQTT to unknown broker (C2 communication)
  - Topic enumeration (attacker discovers all devices)
  - Credential brute-force (CONNECT packets with multiple passwords)
```

### LonWorks (Legacy, Proprietary)
```yaml
Standard: ISO/IEC 14908
Use Case: Legacy lighting, HVAC (1990s-2000s installations)
Protocol: LonTalk (Layer 7), over TP/FT-10 (twisted pair), IP, or power line

Security:
  - Proprietary = security through obscurity (weak)
  - Authentication: Optional, rarely enabled
  - Parser availability: Limited (Insa may not support)

Monitoring Strategy:
  - If LonWorks present: Monitor at network boundary (gateway to BMS)
  - Or: Upgrade to BACnet (LonWorks sunset by many vendors)
```

---

## Appendix B: Energy Efficiency Use Cases (Bonus Value)

### Insa Sensor as Energy Management Tool

```yaml
Use Case 1: Simultaneous Heating & Cooling Detection
  Problem: AHU heats air, then VAV box re-cools (energy waste)
  Detection: Insa monitors BACnet:
    - AHU heating valve >50% open
    - Downstream VAV cooling valve >50% open
    - Simultaneously (logic error)
  Alert: "AHU-3 fighting itself - economizer fault"
  Savings: 5-10% HVAC energy (common fault)

Use Case 2: After-Hours HVAC (Unauthorized Use)
  Problem: Tenant overrides schedule (thermostat to 68°F at 11 PM)
  Detection: Insa monitors BACnet:
    - Schedule object: Should be "unoccupied" (76°F setback)
    - Actual: Heating/cooling active
    - Occupancy sensor: No motion detected (empty building)
  Alert: "Floor 5 HVAC running after-hours - no occupancy"
  Savings: 10-20% HVAC energy (unoccupied hours)

Use Case 3: Stuck Damper (Outdoor Air Waste)
  Problem: Economizer damper stuck open (100% outside air in winter = excessive heating)
  Detection: Insa monitors BACnet:
    - Damper command: 20% open (per logic)
    - Damper feedback: 100% open (stuck)
    - Outside air temp: 20°F (expensive to heat)
  Alert: "AHU-1 economizer damper stuck - heating energy spike"
  Savings: $500-2,000/month (per AHU, winter months)

Use Case 4: Rogue Space Heater (Electrical Load)
  Problem: Tenant plugs in 1,500W space heater (personal comfort)
  Detection: Insa monitors Modbus (energy meter):
    - Tenant sub-meter: Baseline 5 kW (lights, PCs)
    - Spike to 6.5 kW (space heater added)
    - Time pattern: 8 AM - 5 PM (occupant's work hours)
  Alert: "Tenant A electrical anomaly - investigate"
  Savings: Enforce lease terms (no space heaters, fire hazard)
```

---

## Appendix C: Contact & Escalation

```yaml
Insa Automation Corp:
  Sales Engineering: w.aroca@insaing.com
  Smart Buildings Team: buildings-support@insaing.com (if available)
  24/7 Support: (if contracted)

Client Escalation Path (Building-Specific):
  Tier 1: Facilities Technician (On-site, 24/7 if large building)
    - Phone: ____________
    - Response: Immediate (for comfort complaints, equipment alarms)

  Tier 2: Chief Engineer / Facilities Manager
    - Phone: ____________
    - Response: <30 minutes (for BMS issues, cybersecurity alerts)
    - Authority: Restart equipment, override schedules

  Tier 3: Property Manager
    - Phone: ____________
    - Response: <1 hour (for business impact, tenant issues)
    - Authority: Budget approvals, vendor contracts

  Tier 4: IT/Security Manager (if converged network)
    - Phone: ____________
    - Response: <15 minutes (for cyber incidents)
    - Authority: Network isolation, forensic analysis

External Resources:
  BMS Vendor Support: (Johnson Controls, Siemens, etc.)
  Cybersecurity Consultant: (if major incident)
  Insurance: Property, cyber insurance claims
```

### Incident Severity Matrix (Smart Buildings)

```yaml
CRITICAL (Response: <15 min, Notify: Property Manager + Tenants):
  - Chiller/boiler emergency stop (building-wide impact)
  - Ransomware on BMS (loss of control)
  - Physical access breach (unauthorized entry via PACS hack)
  - Life safety compromise (fire alarm integration failure)

HIGH (Response: <1 hour, Notify: Facilities Manager):
  - Unauthorized BMS access (privilege escalation)
  - HVAC setpoint override (occupant discomfort)
  - Energy anomaly (unexpected spike, potential tampering)
  - IoT device compromise (botnet enrollment)

MEDIUM (Response: <4 hours, Notify: Facilities Team):
  - Failed BMS login attempts (brute force)
  - BACnet communication timeout (controller offline)
  - Rogue device detected (investigation needed)
  - Certificate expiration warning (BMS SSL)

LOW (Response: Next business day, Notify: Weekly report):
  - Informational alerts (new device, routine change)
  - Energy efficiency opportunity (optimization, not threat)
  - Asset inventory update (firmware version change)
```

---

**Document Control**
Version: 1.0
Author: Insa Automation Corp
Date: October 11, 2025
Classification: Client Confidential
Review Cycle: Annual (or upon standard revision)

**Made by Insa Automation Corp for OpSec**
