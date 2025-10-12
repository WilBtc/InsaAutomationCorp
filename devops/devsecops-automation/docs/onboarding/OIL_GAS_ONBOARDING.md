# Oil & Gas Sector - Client Onboarding Playbook
**Insa Automation Corp | Energy Infrastructure Security**
Version: 1.0 | Date: October 11, 2025

---

## Executive Summary

Oil and gas operations span vast geographic areas with distributed SCADA systems, remote wellheads, pipelines, and processing facilities. This playbook addresses the unique challenges of securing geographically dispersed critical energy infrastructure.

### Sector Characteristics
- **Critical Priority**: Safety first, then production continuity
- **Key Assets**: Pipeline SCADA, RTUs, PLCs, flow computers, compressor stations, refineries
- **Common Protocols**: Modbus, DNP3, OPC, proprietary (Fisher ROC, ABB TotalFlow)
- **Regulatory**: API 1164, TSA Pipeline Security, PHMSA, BSEE (offshore)
- **Risk Profile**: Nation-state targeting, ransomware, environmental sabotage
- **Geographic Challenge**: Remote sites with satellite/cellular connectivity
- **Unique Concern**: Safety Instrumented Systems (SIS) - SIL 3/4 exclusions

---

## Phase 1: Pre-Sales Discovery

### Discovery Questionnaire

#### Organization Profile
```yaml
Company Type:
  [ ] Upstream (Exploration & Production)
  [ ] Midstream (Pipelines & Transportation)
  [ ] Downstream (Refining & Distribution)
  [ ] Integrated (All of the above)
  [ ] Oilfield Services

Operations:
  Upstream (if applicable):
    - Onshore wells: _____
    - Offshore platforms: _____
    - Production volume: _____ bbl/day (oil), _____ MMcf/day (gas)
    - Remote monitoring: [ ] Satellite [ ] Cellular [ ] Radio [ ] VSAT

  Midstream (if applicable):
    - Pipeline miles (oil): _____
    - Pipeline miles (gas): _____
    - Compressor stations: _____
    - Pump stations: _____
    - Storage facilities: _____
    - TSA Critical Pipeline: [ ] Yes [ ] No

  Downstream (if applicable):
    - Refineries: _____ (capacity: _____ bbl/day)
    - Terminals: _____
    - Retail stations: _____ (corporate-owned)

Geographic Footprint:
  - States/Provinces: _______
  - Countries: _______
  - Most remote site distance from HQ: _____ miles
  - International operations: [ ] Yes [ ] No
```

#### SCADA & Automation Environment
```yaml
Control Centers:
  - Primary control center location: _______
  - Backup control center: [ ] Yes [ ] No - Location: _______
  - 24/7 staffing: [ ] Yes [ ] No
  - SCADA system: [ ] Inductive Automation [ ] WonderWare [ ] AVEVA [ ] Emerson DeltaV [ ] Custom

Pipeline SCADA (Midstream):
  - Leak detection system (LDS): Vendor _______
  - Computational Pipeline Monitoring (CPM): [ ] Yes [ ] No
  - RTU vendor: [ ] Fisher ROC [ ] ABB TotalFlow [ ] Emerson FB [ ] Schneider [ ] Other: _____
  - Communication: [ ] Satellite (VSAT/Iridium) [ ] Cellular (4G/5G) [ ] Radio (900MHz/UHF) [ ] Fiber

  Protocol in use:
    [ ] Modbus (RTU/TCP)
    [ ] DNP3
    [ ] OPC (DA/UA)
    [ ] Proprietary (Fisher ROC, TotalFlow)
    [ ] HART (field devices)

Wellhead Automation (Upstream):
  - PLC/RTU per site: [ ] Yes [ ] No
  - Artificial lift control: [ ] ESP [ ] Gas lift [ ] Beam pumps [ ] None
  - Well monitoring: [ ] Real-time [ ] Daily batch [ ] Manual visits
  - Automated shutdowns (high/low pressure): [ ] Yes [ ] No

Refinery DCS (Downstream):
  - Distributed Control System: [ ] Emerson DeltaV [ ] Honeywell Experion [ ] Yokogawa Centum [ ] ABB 800xA
  - Process units: _____ (CDU, FCC, hydrocracker, etc.)
  - SIS (Safety Instrumented System): [ ] Yes [ ] No - Vendor: _______
  - Safety Integrity Level: [ ] SIL 1 [ ] SIL 2 [ ] SIL 3 [ ] SIL 4
  - Safety system monitoring: [ ] EXCLUDED (required) [ ] Read-only [ ] TBD
```

#### Network Infrastructure
```yaml
WAN Topology:
  - Headquarters network: _______
  - Field site connectivity:
      [ ] Satellite (VSAT) - Bandwidth: _____ kbps, Latency: _____ ms
      [ ] Cellular (4G LTE/5G) - Carrier: _______
      [ ] Private microwave - Frequency: _______
      [ ] Fiber optic (leased/owned)
      [ ] Radio (licensed 900MHz, unlicensed 2.4/5.8GHz)
      [ ] Iridium satellite (low-bandwidth backup)

  - Bandwidth per remote site: Typical _____ kbps, Min _____ kbps
  - Latency tolerance: Pipeline SCADA <500ms, Refinery DCS <100ms

Network Segmentation:
  [ ] Flat network (all sites same subnet) - HIGH RISK
  [ ] VLAN segmentation (by geography/function)
  [ ] Air-gapped safety systems (best practice)
  [ ] Firewall between IT/OT: [ ] Yes [ ] No

Remote Access:
  - VPN: [ ] Yes [ ] No - Type: [ ] IPsec [ ] SSL/TLS [ ] MPLS
  - Vendor access: [ ] Yes [ ] No - Vendors: _______
  - Third-party SCADA hosting: [ ] Yes [ ] No (cloud SCADA)
```

#### Safety Systems (CRITICAL - NO COMPROMISE)
```yaml
Safety Instrumented Systems (SIS):
  Present: [ ] Yes [ ] No
  Vendor: [ ] Schneider Triconex [ ] Siemens FS [ ] Honeywell FSC [ ] Yokogawa ProSafe [ ] Emerson DeltaV SIS

  Safety Integrity Level (SIL):
    [ ] SIL 1 (Risk Reduction Factor 10-100x)
    [ ] SIL 2 (RRF 100-1,000x)
    [ ] SIL 3 (RRF 1,000-10,000x) ◄── Typical for oil & gas
    [ ] SIL 4 (RRF >10,000x) ◄── Rare, nuclear-level safety

  Safety Functions:
    [ ] Emergency Shutdown (ESD) - Process units, pipelines
    [ ] Fire & Gas (F&G) - Detection and suppression
    [ ] Burner Management System (BMS) - Furnaces, boilers
    [ ] High-Integrity Pressure Protection (HIPPS)

  INSA MONITORING POLICY (MANDATORY):
    ⚠️ SIL 3/SIL 4 systems: EXCLUDED from active monitoring (no SPAN port)
    ✅ Passive monitoring MAY be allowed: Read-only, no writes, no scans
    ✅ Network boundary monitoring: Traffic IN/OUT of safety zone allowed
    ⚠️ Any monitoring requires: Safety engineer approval + TUV/IEC 61511 review

Emergency Shutdown (ESD) Systems:
  - Manual ESD stations: _____ locations
  - Automatic ESD triggers: [ ] High pressure [ ] High temp [ ] Gas detection [ ] Fire detection
  - ESD valves: [ ] Pneumatic [ ] Hydraulic [ ] Motor-operated
  - Network-connected: [ ] Yes (RISK) [ ] No (preferred)

  MONITORING EXCLUSION:
    [ ] Acknowledged: ESD systems will NOT be monitored by Insa sensor
    [ ] Rationale: Cannot risk false positives triggering production shutdown
```

#### Regulatory Compliance
```yaml
API 1164 (Pipeline SCADA Security):
  [ ] Compliance required (major interstate pipelines)
  [ ] Last assessment: _______
  [ ] Findings: _____ open items
  [ ] Next audit: _______

TSA Pipeline Security Directive:
  [ ] TSA SD Pipeline-2021-02 (Cyber reporting)
  [ ] Cybersecurity Coordinator: Name _______
  [ ] Incident reporting to CISA: <24 hours
  [ ] Cybersecurity Assessment Plan: [ ] Completed [ ] In progress

PHMSA (Pipeline & Hazardous Materials Safety Admin):
  [ ] Part 192 (Gas pipelines) or Part 195 (Liquid pipelines)
  [ ] Control room management (49 CFR 192.631): [ ] Compliant
  [ ] SCADA alarm management: [ ] Documented [ ] Needs improvement

BSEE (Bureau of Safety & Environmental Enforcement - Offshore):
  [ ] Applicable: Offshore platforms in U.S. waters
  [ ] SEMS (Safety & Environmental Management System): [ ] Yes [ ] No
  [ ] Cybersecurity Program (30 CFR 250): [ ] Documented

Other Standards:
  [ ] NIST CSF (Cybersecurity Framework) - Maturity: Tier _____
  [ ] ISA/IEC 62443 (Industrial Cybersecurity)
  [ ] ISO 27001 (Information Security)
  [ ] ITAR (if defense-related pipelines, e.g., military fuel)
```

#### Incident History
```yaml
Past Cyber Incidents:
  - Ransomware: [ ] Yes [ ] No - Year: _____ - Impact: _______
  - Unauthorized access: [ ] Yes [ ] No - Details: _______
  - Malware detection: [ ] Yes [ ] No - Type: _______
  - Insider threat: [ ] Yes [ ] No - Outcome: _______

Notable Industry Incidents (Awareness):
  - Colonial Pipeline (2021): Ransomware, 5-day shutdown, $4.4M ransom
  - Oldsmar Water (2021): Remote access compromise (water, but relevant)
  - Saudi Aramco Shamoon (2012): Data wiper malware
  - Ukrainian pipeline (2020): Ransomware targeting SCADA

Risk Tolerance:
  - Acceptable downtime per incident: _____ hours
  - Cyber insurance coverage: $_____ million
  - Incident response retainer: [ ] Yes [ ] No - Vendor: _______
```

---

## Phase 2: Site Assessment

### Pre-Deployment Checklist

#### Week 1-2: Remote Discovery
```yaml
Documentation Review:
  [ ] Pipeline route maps (geographic, not just network)
  [ ] P&ID (Piping & Instrumentation Diagrams) - Refinery/plants
  [ ] SCADA architecture diagrams
  [ ] RTU/PLC inventory (asset register)
  [ ] Communication matrix (site-to-site connectivity)
  [ ] Emergency response plan (ERP)
  [ ] Cyber incident response plan (CIRP)

GIS/Mapping Analysis:
  [ ] Import pipeline routes into GIS (if available)
  [ ] Identify high-value targets: Major compressor stations, refineries, export terminals
  [ ] Assess physical security: Fencing, cameras, access control
  [ ] Environmental risks: Flood zones, seismic areas (impacts comms)

Remote Connectivity Test (if permitted):
  [ ] VPN access to control center SCADA
  [ ] Ping test to sample RTUs (verify latency)
  [ ] Review SCADA alarm history (1 month)
  [ ] Identify communication failures (gaps in data)
```

#### Week 3: Control Center Assessment (2 days)
```yaml
Primary Control Center Visit:
  [ ] Security clearance obtained (background check may take 2-4 weeks)
  [ ] Escort arranged
  [ ] Safety briefing (if co-located with operations)

  Control Room Walkthrough:
    [ ] Pipeline controller workstations
    [ ] Large display walls (pipeline SCADA overview)
    [ ] Leak detection system (LDS) displays
    [ ] Historian server(s)
    [ ] Engineering workstations
    [ ] Communication gateway racks

  Network Infrastructure:
    [ ] Core switch location (optimal for SPAN port)
    [ ] WAN router/aggregation
    [ ] Firewall (IT/OT boundary)
    [ ] Satellite modem rack (if VSAT used)
    [ ] Cellular gateway (if LTE used)
    [ ] Radio base station (if licensed radio network)

  Interviews:
    [ ] Pipeline Controller (operational needs)
    [ ] SCADA Administrator (system details)
    [ ] Telecom Engineer (WAN challenges)
    [ ] HSE Manager (safety system exclusions)
    [ ] IT Security Manager (compliance, policies)
```

#### Week 4-6: Field Site Visits (Representative Sample)
```yaml
Site Selection (visit 3-5 sites):
  - 1x Major compressor/pump station (high-value target)
  - 1x Remote wellhead (worst-case connectivity)
  - 1x Processing facility (if upstream client)
  - 1x Refinery (if downstream client)
  - 1x Offshore platform (if applicable, requires helicopter/boat)

Per-Site Checklist:
  [ ] Site access approval (may require TWIC card for offshore/ports)
  [ ] PPE: Hard hat, steel toes, FR clothing (if H2S/flammable gas present)
  [ ] Gas detector: 4-gas monitor (O2, LEL, H2S, CO) - if entering process areas

  Control House/Shelter:
    [ ] RTU/PLC model and firmware version
    [ ] Communication equipment (satellite terminal, cellular modem, radio)
    [ ] Environmental: HVAC, temperature extremes (affects reliability)
    [ ] Power: Solar + battery, generator, utility grid
    [ ] Physical security: Fencing, locks, cameras, intrusion detection

  Communication Performance:
    [ ] Measure latency: Ping from RTU to control center
    [ ] Bandwidth test: Speedtest or iperf (if allowed)
    [ ] Signal strength: Cellular RSSI, satellite C/N0 (carrier-to-noise)
    [ ] Packet loss: Extended ping test (100 packets)

  Process Observation:
    [ ] What does this site do? (pumping, compression, metering, separation)
    [ ] Safety hazards: H2S, high pressure, high temp, flammable liquids
    [ ] Consequence of failure: Environmental spill, explosion, service disruption
    [ ] Monitoring priority: HIGH / MEDIUM / LOW
```

---

## Phase 3: Network Diagram Template

### Oil & Gas Midstream (Pipeline) Network Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     CORPORATE IT NETWORK                        │
│  (HQ, Email, ERP, Engineering, Internet)                       │
└──────────────────────────┬─────────────────────────────────────┘
                           │
                 ┌─────────▼─────────┐
                 │   DMZ / Jump Zone │
                 │  ┌──────────────┐ │
                 │  │  Insa Sensor │ │◄── Corporate visibility
                 │  │  (DMZ)       │ │    (read-only historian)
                 │  └──────────────┘ │
                 └─────────┬─────────┘
                           │
                 ┌─────────▼─────────┐
                 │  Firewall (IT/OT) │
                 │  + VPN Gateway    │
                 └─────────┬─────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│               CONTROL CENTER OT NETWORK                          │
│                                                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐      │
│  │  Primary      │  │   Backup      │  │  Leak Detect  │      │
│  │  SCADA Server │  │   SCADA       │  │  System (LDS) │      │
│  └───────────────┘  └───────────────┘  └───────────────┘      │
│         │                   │                   │               │
│         └───────────┬───────┴───────────────────┘               │
│                     │                                           │
│           ┌─────────▼─────────┐                                 │
│           │  OT Core Switch   │ ◄── MONITORING POINT           │
│           │  (SPAN Port)      │     Insa Sensor: 10.50.1.250   │
│           └─────────┬─────────┘                                 │
│                     │                                           │
└─────────────────────┼───────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┬─────────────────┐
        │                           │                 │
┌───────▼────────┐        ┌─────────▼──────┐  ┌──────▼───────┐
│  VSAT Gateway  │        │ Cellular       │  │  Radio Base  │
│  (Satellite)   │        │ Router (4G/5G) │  │  Station     │
│  Hughes/Viasat │        │ Cradlepoint    │  │  (900MHz)    │
└───────┬────────┘        └─────────┬──────┘  └──────┬───────┘
        │                           │                 │
        │         WAN TRANSPORT (Latency 200-800ms)   │
        │                           │                 │
┌───────┴────────┬──────────────────┴────────┬────────┴────────┐
│                │                           │                  │
▼                ▼                           ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐  ┌──────────────┐
│ Compressor   │ │ Pump Station │ │ Metering     │  │ Remote       │
│ Station A    │ │ B            │ │ Station C    │  │ Wellhead D   │
│              │ │              │ │              │  │              │
│ ┌──────────┐ │ │ ┌──────────┐ │ │ ┌──────────┐ │  │ ┌──────────┐ │
│ │ RTU      │ │ │ │ RTU      │ │ │ │ Flow     │ │  │ │ PLC/RTU  │ │
│ │ Fisher   │ │ │ │ TotalFlow│ │ │ │ Computer │ │  │ │ (Solar + │ │
│ │ ROC 800  │ │ │ │ (Modbus) │ │ │ │ (OPC)    │ │  │ │ Battery) │ │
│ └──────────┘ │ │ └──────────┘ │ │ └──────────┘ │  │ └──────────┘ │
│   DNP3/Modbus│ │   Modbus TCP │ │   OPC DA/UA  │  │   Modbus RTU │
│ 10.100.x.1   │ │ 10.100.x.2   │ │ 10.100.x.3   │  │ 10.100.x.4   │
└──────────────┘ └──────────────┘ └──────────────┘  └──────────────┘
   (~100 sites)    (~50 sites)     (~30 sites)       (~200 wells)

LEGEND:
═══════  Critical control path
───────  Standard monitoring
◄── SPAN Sensor monitoring point
📡      Satellite/Cellular/Radio WAN
```

### Refinery DCS Network (Downstream)

```
┌────────────────────────────────────────────────────────────────┐
│                    CORPORATE IT NETWORK                         │
│  (Business applications, engineering tools)                    │
└──────────────────────────┬─────────────────────────────────────┘
                           │
                 ┌─────────▼─────────┐
                 │  DMZ Historian    │ ◄── Data Diode (one-way)
                 │  (read-only)      │     From DCS to IT
                 └─────────┬─────────┘
                           │
                 ┌─────────▼─────────┐
                 │  IT/OT Firewall   │
                 └─────────┬─────────┘
                           │
┌──────────────────────────┴──────────────────────────────────────┐
│             LEVEL 3: OPERATIONS & ENGINEERING                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Engineering  │  │  Operator    │  │  Insa Sensor │◄── SPAN  │
│  │ Workstations │  │  HMIs        │  │  10.10.1.250 │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└──────────────────────────┬─────────────────────────────────────┘
                           │
                 ┌─────────▼─────────┐
                 │   LEVEL 2 Switch  │
                 │   (DCS Network)   │
                 └─────────┬─────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐  ┌──────▼──────┐  ┌───────▼────────┐
│ DCS Controllers│  │ DCS         │  │ DCS            │
│ CDU Unit       │  │ Controllers │  │ Controllers    │
│ (Refining)     │  │ FCC Unit    │  │ Hydrocracker   │
└───────┬────────┘  └──────┬──────┘  └───────┬────────┘
        │                  │                  │
        │    LEVEL 1: PROCESS CONTROL        │
        │                  │                  │
┌───────▼──────────────────▼──────────────────▼────────┐
│                  LEVEL 0: FIELD DEVICES               │
│  Sensors, Transmitters, Valves, Pumps, Analyzers     │
│  (4-20mA, HART, Foundation Fieldbus, Profibus)       │
└───────────────────────────────────────────────────────┘

        ⚠️ SAFETY NETWORK (AIR-GAPPED) ⚠️
┌───────────────────────────────────────────────────────┐
│      SAFETY INSTRUMENTED SYSTEM (SIS) - EXCLUDED      │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │
│  │ Triconex SIS │  │ ESD Valves   │  │ F&G Panels  │ │
│  │ (SIL 3)      │  │ (Failsafe)   │  │ (Detection) │ │
│  └──────────────┘  └──────────────┘  └─────────────┘ │
│  NO MONITORING BY INSA (Safety-critical)              │
└───────────────────────────────────────────────────────┘

LEGEND:
Level 4/5: Corporate IT (business)
Level 3: Operations (HMI, engineering)
Level 2: Control (DCS, PLC)
Level 1: I/O (field controllers)
Level 0: Sensors/actuators
SIS: Separate, air-gapped safety network
```

---

## Phase 4: Installation Procedure

### Pre-Installation (2-4 weeks)

#### Regulatory & Safety Approvals
```yaml
Management of Change (MOC):
  [ ] MOC form submitted (required in oil & gas)
  [ ] Risk assessment: HAZOP or LOPA (if touching process)
  [ ] Safety review: HSE department approval
  [ ] Operations approval: Production manager sign-off
  [ ] IT/OT approval: Cybersecurity team
  [ ] Implementation plan: Reviewed and approved

  MOC Documentation:
    - Reason for change: "Install cybersecurity monitoring sensor"
    - Impact analysis: "Passive monitoring, no process control"
    - Rollback plan: "Remove SPAN port configuration"
    - Training required: "Control room operators (1-hour overview)"

Physical Access (Field Sites):
  [ ] TWIC card (if port/offshore facility)
  [ ] SafeLand USA training (oil & gas industry standard)
  [ ] Site-specific safety orientation
  [ ] H2S awareness (if sour gas present)
  [ ] Confined space entry (if required, e.g., pump stations)
  [ ] Hot work permit (if any welding/drilling needed)

Equipment Preparation:
  [ ] Insa sensor (ruggedized for field deployment if needed)
  [ ] Satellite modem (if sensor deployed at remote site)
  [ ] Cellular router (if LTE connectivity)
  [ ] UPS (industrial-grade, wide temperature range)
  [ ] Enclosure (NEMA 4X if outdoor installation)
  [ ] Grounding kit (lightning protection for field sites)
```

#### Deployment Strategy Selection

```yaml
Deployment Model A: Centralized (Control Center Only)
  Pros:
    - Single sensor installation (lower cost)
    - High-bandwidth connectivity
    - Easy maintenance
  Cons:
    - Limited visibility to field site details (only sees SCADA polling)
    - Misses local device-to-device traffic
    - WAN latency may hide fast attacks

  Best for:
    - Midstream (pipelines) with hundreds of remote RTUs
    - Upstream (wells) with low-bandwidth satellite links
    - Budget-conscious deployments

Deployment Model B: Distributed (Control Center + Key Field Sites)
  Pros:
    - Deep visibility at critical sites (compressor stations, refineries)
    - Captures local HMI-to-PLC traffic
    - Faster anomaly detection
  Cons:
    - Multiple sensors (higher cost)
    - Cellular/satellite backhaul costs
    - More complex management

  Best for:
    - Downstream (refineries) with complex DCS
    - High-value midstream assets (major compressor stations)
    - Regulatory requirements (e.g., TSA SD compliance)

Deployment Model C: Hybrid (Central + Cloud Edge)
  Pros:
    - Lightweight agents at field sites (low cost)
    - Cloud aggregation and analytics
    - Scalable to thousands of sites
  Cons:
    - Requires internet access from field (security risk if not VPN)
    - Cloud dependency (latency, availability)
    - Data sovereignty concerns (cross-border pipelines)

  Best for:
    - Large-scale well monitoring (100+ sites)
    - Multi-national operations
    - Modern cloud-first organizations
```

### Installation Day - Control Center

#### Hour 0-1: Physical Setup
```yaml
Site Arrival:
  [ ] Check in with security
  [ ] Safety briefing (hard hat, safety glasses, steel toes)
  [ ] Escort to control center
  [ ] Pre-installation checklist review with ops team

Sensor Installation:
  [ ] Install in secure network rack (Level 3 operations network)
  [ ] Connect to UPS (verify >1 hour runtime)
  [ ] Dual power supplies (if available)
  [ ] Cable management (industrial-grade, labeled)
  [ ] Grounding (verify low impedance to facility ground)
  [ ] Environmental: Verify HVAC (sensor operating temp: 0-50°C)
```

#### Hour 1-2: Network Configuration
```yaml
SPAN Port Configuration (Control Center Switch):
  Target traffic:
    - SCADA server uplink (to/from field RTUs)
    - Engineering workstation VLAN (for PLC programming detection)
    - Historian data feeds (optional)

  Example (Cisco):
    monitor session 1 source interface Gi1/0/5 rx
    monitor session 1 source vlan 100 rx  ! SCADA VLAN
    monitor session 1 destination interface Gi1/0/24
    ! Gi1/0/24 = Insa sensor

  [ ] Verify: tcpdump on sensor shows Modbus/DNP3 traffic
  [ ] Verify: No packet loss (SPAN oversubscription check)

Management Network:
  [ ] Static IP: 10.50.1.250 (from approved asset list)
  [ ] Subnet: 255.255.255.0
  [ ] Gateway: 10.50.1.1
  [ ] DNS: (corporate DNS servers)
  [ ] NTP: (corporate NTP, GPS-synced if available)
  [ ] Firewall rule: Allow sensor to send alerts via SMTP/syslog
```

#### Hour 2-3: Protocol Configuration (Oil & Gas Specific)
```yaml
Protocol Parsers:
  [ ] Modbus TCP (port 502):
      - Most common in oil & gas
      - Unit ID range: 1-247 (learn from traffic)

  [ ] Modbus RTU (serial encapsulated):
      - If serial-to-Ethernet converters present
      - Baud rates: 9600, 19200 (common)

  [ ] DNP3 (port 20000):
      - Midstream pipelines (similar to utilities)
      - Master/Outstation addressing

  [ ] OPC DA (port 135 + dynamic):
      - Legacy, Windows-based (refinery DCS)
      - Security concern: DCOM, no authentication

  [ ] OPC UA (port 4840):
      - Modern, secure replacement for OPC DA
      - Certificate-based authentication

  [ ] Proprietary Protocols:
      [ ] Fisher ROC (port 4000-4999):
          - Custom parser (if available from Insa)
          - Fallback: Monitor as generic TCP
      [ ] ABB TotalFlow (Modbus-like):
          - Often compatible with Modbus parser
      [ ] Enron Modbus (variant of Modbus):
          - Special handling for flow computers

Baseline Learning:
  [ ] Duration: 14-21 days (oil & gas has longer cycles)
  [ ] Rationale: Batch operations, maintenance windows, seasonal changes
  [ ] Asset discovery: RTUs, PLCs, flow computers, HMIs
  [ ] Communication patterns: Polling intervals, report-by-exception
  [ ] Alarm thresholds: Establish normal rates (avoid false positives)
```

#### Hour 3-4: Integration & Safety Checks
```yaml
Alert Configuration:
  Critical Alerts (Safety/Environmental):
    - Unauthorized write to ESD system (if monitored boundary)
    - High-rate Modbus writes (potential ransomware/wiper)
    - RTU communication loss >5 minutes (leak detection failure)
    - Firmware upload to safety PLC (SIS boundary violation)

  High Alerts:
    - New device on SCADA network
    - Engineering software connection outside maintenance window
    - Abnormal data exfiltration (large file transfers)

  Medium Alerts:
    - Failed authentication attempts (threshold: 3 in 15 min)
    - Protocol anomaly (malformed Modbus, unexpected function code)
    - Certificate expiration warnings (OPC UA)

  Notification:
    - Email: control.center@client.com, cybersecurity@client.com
    - SMS: On-call SCADA administrator (CRITICAL only)
    - Integration: Client SIEM (syslog CEF format)

Safety System Exclusion Verification:
  [ ] Confirm: NO monitoring of SIS network (air-gapped)
  [ ] Confirm: NO SPAN port on safety switch
  [ ] Confirm: Sensor CANNOT communicate with safety PLCs
  [ ] Document: Exclusion acknowledged in installation report
  [ ] Sign-off: HSE manager approval

Operational Testing:
  [ ] SCADA system: Normal operation (no latency increase)
  [ ] RTU communication: All sites responding
  [ ] Leak detection: Functioning normally
  [ ] Pipeline controller confirmation: "No issues observed"
```

---

## Phase 5: Sector-Specific Monitoring Templates

### Oil & Gas Detection Rules

#### Rule Set 1: Pipeline SCADA Protection
```yaml
Name: Unauthorized Valve/Pump Control
Severity: CRITICAL
Trigger:
  - Modbus: Write to coil/register controlling valve/pump
  - DNP3: OPERATE command (function code 0x05) to actuator
  - Source: NOT in authorized SCADA master list
Action:
  - Immediate SMS to pipeline controller
  - Email to control center + management
  - Preserve 1-hour PCAP (before/after)
  - Escalate to TSA/PHMSA if sabotage suspected

Context:
  - Differentiate: Manual local control (acceptable) vs. network-based (suspicious)
  - Whitelist: Primary SCADA 10.50.10.1, Backup SCADA 10.50.10.2
  - Exclusion: Maintenance window (scheduled in advance)

Compliance: TSA SD Pipeline-2021-02 (reportable incident)
```

#### Rule Set 2: Leak Detection System (LDS) Tampering
```yaml
Name: LDS Communication Failure
Severity: HIGH (Environmental/Safety Risk)
Trigger:
  - RTU communication timeout >5 minutes (critical for leak detection)
  - LDS software process stopped/crashed
  - Abnormal pressure/flow data (sensor tampering indicator)
Action:
  - Alert pipeline controller (may indicate real leak OR cyber attack)
  - Initiate backup leak detection (manual walk-through if needed)
  - Review: SCADA logs, RTU status, field reports

Context:
  - Pipeline leak detection is life-safety critical
  - False negatives (missed leak) = environmental disaster + regulatory fines
  - Cyber attack on LDS is high-impact scenario (disable detection before physical attack)
```

#### Rule Set 3: Ransomware/Wiper Detection
```yaml
Name: Rapid Modbus Write Campaign
Severity: CRITICAL (Potential Wiper Malware)
Trigger:
  - >100 Modbus write commands in <1 minute
  - Targeting multiple RTUs (distributed attack)
  - Function codes: 0x05, 0x06, 0x0F, 0x10 (write coils/registers)
Action:
  - EMERGENCY: Isolate SCADA network at firewall (if safe)
  - Activate backup control center
  - Preserve all logs (forensic evidence)
  - Engage incident response team (cyber insurance, FBI if critical infrastructure)

Context:
  - Similar to: TRISIS malware (targeted Triconex SIS, 2017)
  - Similar to: Industroyer (targeted Ukrainian power grid, 2016)
  - Oil & gas sector is HIGH-VALUE target for nation-state actors

Compliance: Report to CISA within 24 hours (critical infrastructure)
```

#### Rule Set 4: Insider Threat (Geographically Anomalous)
```yaml
Name: Engineering Access from Unexpected Location
Severity: MEDIUM
Trigger:
  - PLC programming software connection (e.g., RSLogix, TIA Portal)
  - Source IP: Outside normal locations (HQ, known integrator VPN)
  - Or: Access during off-hours (2 AM) when engineer not on-call
Action:
  - Alert cybersecurity team
  - Verify: Call engineer's mobile phone (out-of-band confirmation)
  - Review: What changes were made (compare PLC config backups)

Context:
  - Insider threat: Disgruntled employee, contractor with stolen credentials
  - Geographic anomaly: Houston office engineer accessing from foreign IP
  - Oil & gas has high employee turnover (contractors, seasonal workers)
```

#### Rule Set 5: Remote Access Abuse
```yaml
Name: Unauthorized VPN Connection
Severity: HIGH
Trigger:
  - VPN login from unknown device (MAC address not in asset inventory)
  - Or: VPN login from blacklisted country (geo-IP: China, Russia, Iran, N. Korea)
  - Or: Concurrent VPN sessions for same user (impossible if legitimate)
Action:
  - Terminate VPN session immediately
  - Force password reset for user account
  - Review: VPN logs for past 90 days (check for prior compromise)
  - Escalate: If credentials stolen, assume broader breach

Context:
  - Colonial Pipeline attack vector: Compromised VPN password (no MFA)
  - Oil & gas uses extensive remote access (vendors, consultants)
  - Best practice: MFA required, IP whitelisting, limited access hours
```

### Oil & Gas KPIs

```yaml
Operational Metrics:
  - SCADA uptime: 99.9%+ (critical for pipeline safety)
  - RTU communication success: >99% (per API 1164)
  - Leak detection availability: 99.99% (environmental mandate)
  - Control center response time: <5 minutes (for alarms)

Security Metrics:
  - Mean Time to Detect (MTTD): <10 minutes (faster than Colonial Pipeline)
  - Mean Time to Respond (MTTR): <30 minutes
  - Unauthorized access attempts: Trend toward ZERO
  - Malware detections: Any = incident investigation

Compliance Metrics:
  - TSA SD reporting: 100% within 24 hours
  - API 1164 compliance: All controls implemented
  - PHMSA audit findings: ZERO high-priority
  - Vulnerability scans: Quarterly (all accessible assets)

Asset Visibility:
  - RTU inventory accuracy: 100%
  - Firmware version tracking: 95%+ (challenging with remote sites)
  - Unauthorized device detection: <1 hour
  - Remote site health monitoring: 100% coverage
```

---

## Phase 6: Compliance Requirements

### API 1164 (Pipeline SCADA Security)

```yaml
Section 5: Security Program
  [ ] Documented cybersecurity policy (company-wide)
  [ ] Risk assessment (SCADA-specific)
  [ ] Incident response plan (tested annually)
  [ ] Security awareness training (all SCADA users)

Section 6: Asset Management
  Insa sensor provides:
    [ ] Automated asset discovery (RTUs, PLCs, HMIs)
    [ ] Firmware version tracking
    [ ] Communication pattern documentation

Section 7: Controls & Practices
  7.1 Access Control:
    [ ] Insa monitors: Failed login attempts, unauthorized access
  7.2 Security Monitoring:
    [ ] Insa provides: 24/7 protocol-aware anomaly detection
  7.3 Patching:
    [ ] Insa alerts: CVE applicability to discovered assets

Section 8: Incident Response
  [ ] Insa integration: Automated alert to IR team
  [ ] Evidence preservation: PCAP, logs (90-day retention)
```

### TSA Security Directive (Pipeline)

```yaml
TSA SD Pipeline-2021-02 (Cyber Reporting):
  Requirements:
    [ ] Designated Cybersecurity Coordinator (name: _______)
    [ ] Report cyber incidents to CISA within 24 hours
    [ ] Annual cybersecurity review
    [ ] Implementation of TSA-approved security measures

  Insa Sensor Support:
    [ ] Automated incident detection (reduces detection time)
    [ ] Pre-formatted incident report templates
    [ ] Evidence package for CISA submission
    [ ] Timestamp synchronization (NTP, GPS)

  Reportable Incidents:
    - Unauthorized access to SCADA
    - Ransomware/malware on OT network
    - Denial of service (SCADA unavailable)
    - Data breach (pipeline operational data)
```

### PHMSA (Pipeline Safety Regulations)

```yaml
49 CFR 192.631 (Gas) / 195.446 (Liquid): Control Room Management
  Requirements:
    [ ] Alarm management (documented procedures)
    [ ] Fatigue management (operator schedules)
    [ ] Training (SCADA system operations)

  Insa Contribution:
    [ ] Alarm rate monitoring (identify alarm floods)
    [ ] Operator response time tracking (audit trail)
    [ ] Training: Cyber incident response (augment existing training)

49 CFR 192.935: SCADA Security (Integrity Management)
  [ ] Annual review of SCADA security controls
  [ ] Vulnerability assessment
  [ ] Insa sensor: Continuous monitoring (exceeds annual requirement)
```

### BSEE (Offshore Oil & Gas - U.S. Waters)

```yaml
30 CFR 250.1910: Cybersecurity for Offshore Platforms
  Requirements:
    [ ] Risk assessment (OT systems on platform)
    [ ] Cybersecurity program (documented)
    [ ] Incident response plan (platform-specific)

  Offshore Challenges:
    - Limited connectivity (satellite only, high latency)
    - Remote workforce (fly-in/fly-out, contractors)
    - Physical access control (helicopter, boat)
    - Environmental hazards (hurricanes, salt water corrosion)

  Insa Deployment Considerations:
    [ ] Ruggedized sensor (NEMA 4X, salt fog rated)
    [ ] Satellite backhaul (VSAT, Iridium for alerts)
    [ ] Local logging (30-day buffer if connectivity lost)
    [ ] Annual on-site maintenance (during platform shutdown)
```

---

## Phase 7: Success Criteria

### 90-Day Milestones (Extended for Oil & Gas)

```yaml
Days 1-30 (Learning & Baseline):
  [ ] 100% of RTUs/PLCs discovered (verify against asset register)
  [ ] Communication patterns documented (polling intervals, batch reports)
  [ ] Protocol decoding accuracy: >95% (Modbus, DNP3, OPC)
  [ ] Zero impact to SCADA operations
  [ ] Field site connectivity verified (if distributed deployment)

Days 31-60 (Tuning & Integration):
  [ ] Alert rules customized (differentiate normal vs. anomalous)
  [ ] False positive rate: <5% (oil & gas tolerates fewer FPs due to 24/7 ops)
  [ ] Integration with SIEM/SOC (if applicable)
  [ ] API 1164 compliance dashboards operational
  [ ] Incident response drill (tabletop exercise)

Days 61-90 (Active Monitoring & Validation):
  [ ] Transition to enforcement mode (real alerts enabled)
  [ ] First security finding detected and resolved (e.g., unauthorized access attempt)
  [ ] SCADA uptime maintained: 99.9%+
  [ ] Operator acceptance: "Sensor is invisible to daily ops"
  [ ] Management review: Security posture improvement quantified
```

### Long-Term Success Indicators

```yaml
Safety & Environmental:
  - Pipeline incidents: Zero cyber-related
  - Leak detection uptime: 99.99%+
  - ESD system integrity: 100% (no compromise from monitoring)
  - Regulatory fines: $0 (avoidance of multi-million dollar penalties)

Security Maturity:
  - API 1164 compliance: All recommendations implemented
  - TSA SD reporting: 100% on-time
  - Cyber incidents detected: 100% (vs. historical ~30% detection rate)
  - Mean Time to Detect: <10 minutes (industry average: hours to days)

Business Value:
  - Cyber insurance premium: Reduced by 20-40% (due to improved controls)
  - Audit preparation: Reduced by 70% (automated evidence collection)
  - Incident response cost: $0 (prevention vs. $5M+ average ransomware cost)
  - Expansion: Deploy to additional pipelines, refineries, offshore platforms

Operational Efficiency:
  - SCADA alarm noise: Reduced by 30% (filtering false positives)
  - Security analyst time: Focus on response, not log review (80% time savings)
  - Asset inventory: Real-time, always accurate (vs. annual spreadsheet update)
```

---

## Phase 8: Geographic & Connectivity Challenges

### Remote Site Deployment (Wellheads, Compressor Stations)

```yaml
Challenge: Low Bandwidth, High Latency
  Satellite (VSAT):
    - Bandwidth: 512 kbps - 2 Mbps (shared)
    - Latency: 500-800ms (geostationary orbit)
    - Cost: $500-2,000/month per site

  Cellular (4G LTE/5G):
    - Bandwidth: 1-50 Mbps (variable by location)
    - Latency: 50-200ms
    - Cost: $50-200/month per site
    - Coverage: Limited in rural areas (Dead zones)

  Radio (Licensed 900MHz, Unlicensed 2.4/5.8GHz):
    - Bandwidth: 100 kbps - 10 Mbps
    - Latency: 10-50ms
    - Cost: Infrastructure investment (towers, repeaters)
    - Line-of-sight required (terrain challenges)

Insa Sensor Optimization for Remote Sites:
  [ ] Data compression: Reduce bandwidth usage by 80%
  [ ] Local buffering: Store 30 days logs (if connectivity lost)
  [ ] Smart alerting: Only send high/critical alerts via satellite (reduce costs)
  [ ] Scheduled reporting: Daily summary during off-peak hours (cheaper satellite rates)
  [ ] Edge processing: Detect anomalies locally, send only alerts (not raw traffic)

Alternative: Hub-and-Spoke Model
  [ ] Deploy sensor at control center (hub) only
  [ ] Monitor RTU-to-SCADA traffic (centralized visibility)
  [ ] Trade-off: Miss local attacks (device-to-device at field site)
  [ ] Benefit: 90% cost reduction (single sensor vs. 100+ sensors)
```

### International Operations (Cross-Border Pipelines)

```yaml
Challenge: Data Sovereignty & Jurisdiction
  Scenario: Pipeline from Canada to U.S., or U.S. to Mexico
    - Canadian data: Subject to PIPEDA (privacy law)
    - U.S. data: Subject to CFIUS (foreign investment restrictions)
    - Mexican data: Subject to Federal Data Protection Law

  Insa Deployment:
    [ ] Regional sensors (one per country)
    [ ] Data residency: Logs stay in-country (no cross-border transfer)
    [ ] Aggregated reporting: Anonymized, high-level dashboards only
    [ ] Compliance: Legal review required (client responsibility)

Challenge: Language & Support
  [ ] Sensor UI: Multi-language support (English, Spanish, French)
  [ ] Alerts: Localized (Spanish for Mexico operations)
  [ ] Insa support: 24/7 in client's timezone (Latin America, Middle East, Asia)
```

### Offshore Platforms (Extreme Environments)

```yaml
Challenge: Physical Environment
  - Temperature: -20°C to +50°C (Arctic to Gulf of Mexico)
  - Humidity: 100% (salt water spray)
  - Vibration: Drilling rigs, compressors
  - Power: Unreliable (generator-dependent)

Insa Sensor Ruggedization:
  [ ] NEMA 4X / IP66 enclosure (waterproof, salt-fog rated)
  [ ] Extended temperature range: -40°C to +70°C
  [ ] Shock-mounted: Military-grade vibration resistance
  [ ] UPS: 24-hour battery backup (platform power outages)
  [ ] Dual power supplies: 110V / 220V (international compatibility)

Challenge: Limited Physical Access
  - Platform visits: Quarterly (via helicopter/boat, weather-dependent)
  - Maintenance window: 4 hours during planned shutdown
  - Remote hands: Train platform technician (non-cybersecurity expert)

  Remote Management Strategy:
    [ ] Redundant connectivity: VSAT + Iridium satellite (backup)
    [ ] Remote reboot: Power cycling via managed PDU
    [ ] Automated health checks: Daily self-test, alert if failure
    [ ] Pre-staged spares: Keep backup sensor on platform (swap if failure)
```

---

## Appendix A: Oil & Gas Protocol Quick Reference

### Modbus (Most Common in Oil & Gas)
```yaml
Variants:
  - Modbus RTU: Serial (RS-232/485), used at wellheads, pump stations
  - Modbus TCP: Ethernet, used in control centers, refineries
  - Enron Modbus: Flow computer variant (Daniel/Emerson)

Function Codes (Critical for Monitoring):
  - 01: Read Coils (digital inputs/outputs)
  - 02: Read Discrete Inputs
  - 03: Read Holding Registers (analog values, setpoints)
  - 04: Read Input Registers (sensor data)
  - 05: Write Single Coil (CONTROL - high risk)
  - 06: Write Single Register (CONTROL - high risk)
  - 15: Write Multiple Coils (batch control)
  - 16: Write Multiple Registers (program upload)

Monitoring Focus:
  - Write commands (05, 06, 15, 16) from unauthorized IPs
  - Excessive polling (DDoS to RTU)
  - Read of sensitive registers (reconnaissance before attack)

Security: NO native encryption, NO authentication (add VPN or firewall rules)
```

### DNP3 (Pipeline SCADA, Similar to Utilities)
```yaml
Use Case: RTU-to-SCADA for pipelines, similar to electric utilities
Port: 20000/TCP (or serial)
Addressing: Master (control center) / Outstation (RTU)

Function Codes:
  - 0x01: READ (normal polling)
  - 0x02: WRITE (control commands)
  - 0x05: OPERATE (direct control - SELECT/OPERATE sequence)
  - 0x14: COLD_RESTART (reboot RTU - suspicious if unexpected)

DNP3 Secure Authentication (SAv5):
  - Optional encryption layer (rarely deployed in oil & gas)
  - If present: Look for failed authentication attempts

Monitoring Focus:
  - OPERATE commands from unauthorized master
  - Firmware uploads (file transfer objects)
  - Restart commands (may indicate ransomware preparation)
```

### OPC (OLE for Process Control - Refinery DCS)
```yaml
OPC DA (Data Access - Legacy):
  - Technology: Microsoft DCOM (Component Object Model)
  - Port: 135 (RPC endpoint) + dynamic high ports (1024-65535)
  - Security: Weak (Windows credentials, often default "Administrator")
  - Risk: Remote code execution vulnerabilities (e.g., MS17-010 EternalBlue)

OPC UA (Unified Architecture - Modern):
  - Technology: Service-oriented architecture (SOA), platform-independent
  - Port: 4840/TCP (standard)
  - Security: TLS encryption, X.509 certificates, user authentication
  - Services:
      - Read/Write (data access)
      - HistoricalAccess (query historian)
      - AddNodes (schema modification - high risk)

Monitoring Focus:
  - OPC DA: Should be deprecated (migrate to OPC UA)
  - OPC UA: Monitor for certificate errors, unauthorized writes
  - Unusual data reads (large volume = data exfiltration)
```

### Proprietary Protocols (Vendor-Specific)
```yaml
Fisher ROC (Remote Operations Controller):
  - Vendor: Emerson
  - Use: Flow computers, wellhead controllers
  - Protocol: ROC (proprietary, Modbus-like)
  - Port: 4000-4999/TCP
  - Monitoring: Use generic TCP parser, watch for writes to config registers

ABB TotalFlow:
  - Vendor: ABB
  - Use: Flow computers (gas metering)
  - Protocol: TotalFlow (Modbus variant)
  - Monitoring: Compatible with Modbus parser (test and verify)

Emerson FloBoss:
  - Use: Remote flow measurement
  - Protocol: FloBoss (proprietary)
  - Monitoring: Limited parser availability (capture as unknown protocol)

Best Practice:
  - Contact Insa for protocol parser availability
  - Fallback: Monitor TCP connections (source/dest, frequency, volume)
  - Request: Vendor documentation (for custom parser development)
```

---

## Appendix B: Incident Response (Oil & Gas Scenarios)

### Scenario A: Ransomware Hits SCADA
```yaml
Detection (via Insa Sensor):
  - Rapid Modbus writes to multiple RTUs (wiper malware)
  - Or: SMB traffic spike (lateral movement, EternalBlue)
  - Or: SCADA server becomes unresponsive (encrypted files)

Immediate Response (First 15 Minutes):
  1. Isolate SCADA network at firewall (STOP propagation)
  2. Activate backup control center (if available)
  3. Switch to manual control (operators at field sites)
  4. Preserve forensic evidence (do NOT reboot infected systems)
  5. Notify: Management, cybersecurity team, cyber insurance, legal

Investigation (Hours 1-4):
  1. Insa sensor: Export 24-hour PCAP (pre/post infection)
  2. Identify: Patient zero (first infected system)
  3. Lateral movement: Map attacker's path (SMB, RDP logs)
  4. Impact assessment: Which RTUs/PLCs affected?
  5. Exfiltration check: Did attacker steal data? (large outbound transfers)

Recovery (Days 1-7):
  1. Restore SCADA from clean backups (test in isolated environment first)
  2. Re-image all infected workstations (do NOT trust "cleaned" systems)
  3. Patch vulnerabilities (e.g., MS17-010 if EternalBlue used)
  4. Reset all passwords (assume credentials compromised)
  5. Enhanced monitoring: Insa sensor rules tightened (lower thresholds)

Post-Incident (Weeks 1-4):
  1. Root cause analysis: How did attacker gain initial access? (phishing, VPN, USB)
  2. Compliance reporting: TSA (24 hours), CISA, cyber insurance, shareholders
  3. Lessons learned: Update IR plan, conduct tabletop exercise
  4. Business continuity: Review backup/recovery procedures (reduce RTO)

Cost Avoidance (Colonial Pipeline Example):
  - Downtime: 5 days = $90M+ revenue loss (Colonial Pipeline, 2021)
  - Ransom: $4.4M paid (partially recovered)
  - Regulatory fines: Potential millions (TSA SD violation if applicable)
  - Insa sensor value: Early detection = stop attack before widespread impact
```

### Scenario B: Insider Sabotages Pipeline
```yaml
Detection (via Insa Sensor):
  - Authorized engineer account accesses PLC outside work hours (3 AM)
  - Downloads ladder logic program (backup before modification?)
  - Uploads modified program (malicious logic inserted)
  - Command: Close all block valves (shutdown pipeline)

Immediate Response (First 5 Minutes):
  1. Pipeline controller: Manual override (open valves locally if safe)
  2. Revoke insider's access (Active Directory, VPN, badge)
  3. Insa sensor: Compare PLC programs (before/after) - what changed?
  4. Alert: Management, HR (potential termination/arrest)

Investigation (Hours 1-24):
  1. Motive: Disgruntled employee? Coercion (blackmail)? Competitor espionage?
  2. Scope: What else did insider access? (exfiltrate IP, plant logic bombs)
  3. Accomplices: Review access logs (did insider share credentials?)
  4. Legal: Preserve evidence for prosecution (chain of custody)

Recovery:
  1. Restore trusted PLC programs (from known-good backups)
  2. Manual inspection: Physical field devices (check for tampering)
  3. Enhanced access control: Remove "god mode" accounts, implement least privilege
  4. Monitoring: Flag any access by former employees (stale accounts)

Prevention (Going Forward):
  1. Insider threat program: Behavioral monitoring (HR + cybersecurity)
  2. Code review: Peer review for all PLC program changes (two-person rule)
  3. Separation of duties: No single person can authorize + implement change
  4. Insa sensor: Baseline "normal" engineer behavior (time, location, actions)
```

---

## Appendix C: Contact & Escalation

```yaml
Insa Automation Corp:
  Sales Engineering: w.aroca@insaing.com
  Oil & Gas Specialists: oilgas-support@insaing.com (if available)
  24/7 Emergency Hotline: ____________

Client Escalation Path (Customize per Client):
  Tier 1: SCADA Operator / Pipeline Controller
    - Phone: ____________
    - Response: Immediate (for operational issues)
    - Authority: Emergency shutdown if safety risk

  Tier 2: SCADA Administrator / Automation Engineer
    - Phone: ____________
    - Response: <1 hour
    - Authority: Technical troubleshooting, system restarts

  Tier 3: Cybersecurity Manager / IT Manager
    - Phone: ____________
    - Response: <15 minutes (for cyber incidents)
    - Authority: Network isolation, forensic analysis

  Tier 4: VP Operations / Plant Manager
    - Phone: ____________
    - Response: <1 hour
    - Authority: Business decisions (pay ransom? shutdown production?)

External Coordination:
  CISA (DHS): Report via CISA.gov/report (within 24 hours for critical infrastructure)
  TSA (Pipelines): Cybersecurity Coordinator contact
  FBI Cyber Division: Local field office (for nation-state, ransomware)
  Cyber Insurance: Claims hotline (activate IR retainer)
  Legal Counsel: Data breach notification requirements (state laws)

Industry Information Sharing:
  OOC-ISAC (Downstream Oil ISAC): https://www.ooc-isac.com
  ONG-ISAC (Oil & Natural Gas ISAC): https://ong-isac.org
  E-ISAC (Electricity ISAC): If co-located power generation
```

### Incident Severity Matrix (Oil & Gas Specific)

```yaml
CRITICAL (Response: <5 min, Notify: CEO + Regulators):
  - Pipeline shutdown due to cyber attack
  - Safety system (ESD, F&G) compromise
  - Environmental release (leak undetected due to LDS failure)
  - Ransomware encryption of SCADA
  - Nation-state attack indicators

HIGH (Response: <15 min, Notify: VP Ops + Cybersecurity):
  - Unauthorized control commands (blocked)
  - Malware detection on OT network
  - Insider threat (sabotage attempt)
  - Data exfiltration of pipeline operational data

MEDIUM (Response: <1 hour, Notify: SCADA Admin + IT):
  - Failed access attempts (brute force)
  - Protocol anomaly (malformed packets)
  - Unapproved configuration change
  - Vulnerability scan detected

LOW (Response: Next business day, Notify: Weekly report):
  - Informational alerts (new device, routine change)
  - Certificate expiration warning (>30 days)
  - Asset inventory updates
```

---

**Document Control**
Version: 1.0
Author: Insa Automation Corp
Date: October 11, 2025
Classification: Client Confidential - Sensitive Security Information (SSI)
Review Cycle: Annual (or upon regulatory change)

**Made by Insa Automation Corp for OpSec**
