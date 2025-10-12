# Safety System Exclusion Guide - CRITICAL

**Insa Automation Corp - DevSecOps Platform**
**Version**: 1.0
**Last Updated**: October 11, 2025
**Classification**: CRITICAL - READ BEFORE ANY DEPLOYMENT

---

## ⚠️ CRITICAL WARNING ⚠️

**NEVER INSTALL MONITORING AGENTS ON SAFETY SYSTEMS**

Safety systems are designed to protect human life, equipment, and the environment. Installing unauthorized software on these systems can:
- Interfere with safety functions
- Void safety certifications (TÜV, UL, FM, etc.)
- Violate regulatory requirements (OSHA, EPA, etc.)
- Cause catastrophic incidents
- Result in criminal liability

**When in doubt, DO NOT INSTALL. Ask the customer safety engineer.**

---

## What is a Safety System?

A **safety system** is any system designed to:
- Prevent injury or death
- Prevent environmental damage
- Prevent equipment damage
- Shut down unsafe processes automatically
- Provide redundant protection layers

Safety systems operate independently of normal control systems and are subject to strict regulations and certifications.

---

## Types of Safety Systems (DO NOT TOUCH)

### 1. Safety Instrumented Systems (SIS)
**Description**: Systems that automatically take a process to a safe state when dangerous conditions are detected.

**Common Names**:
- SIS (Safety Instrumented System)
- ESD (Emergency Shutdown System)
- F&G (Fire and Gas Detection System)
- HIPPS (High Integrity Pressure Protection System)
- SIF (Safety Instrumented Function)

**Identifiers**:
- Safety Integrity Level (SIL) rating: SIL 1, SIL 2, SIL 3, or SIL 4
- Red or yellow colored systems (common safety color coding)
- Labels: "Safety System - Do Not Modify"
- Separate network from control system (safety network)
- Vendors: Honeywell Safety Manager, Siemens Safety Integrated, Rockwell GuardLogix, Schneider Triconex, Yokogawa ProSafe-RS

**Examples**:
- Overpressure shutdown valves
- Emergency depressurization systems
- Toxic gas leak shutdown
- Fire suppression activation

**Rule**: **NEVER INSTALL** any software on SIS controllers or HMIs.

---

### 2. Emergency Shutdown (ESD) Systems
**Description**: Systems that rapidly shut down equipment in emergency situations.

**Common in**:
- Oil and gas (offshore platforms, refineries)
- Chemical plants
- Power generation

**Identifiers**:
- ESD push buttons (red mushroom buttons)
- ESD logic solvers
- Networks labeled "Safety Network" or "SIS Network"
- Dedicated UPS (uninterruptible power supply) for safety systems

**Rule**: **NEVER INSTALL** agents on ESD servers or controllers.

---

### 3. Fire and Gas (F&G) Detection Systems
**Description**: Systems that detect fire, smoke, or gas leaks and trigger alarms or suppression systems.

**Identifiers**:
- Fire alarm panels
- Gas detection controllers
- Flame detectors, smoke detectors, gas sensors
- Integration with fire suppression (sprinklers, CO2, foam)

**Rule**: **NEVER INSTALL** agents on F&G detection servers. Network monitoring (SNMP) may be acceptable IF approved by fire safety engineer.

---

### 4. Burner Management Systems (BMS)
**Description**: Systems that safely start, monitor, and shut down industrial burners (boilers, heaters, furnaces).

**Why Critical**: Improper burner operation can cause explosions.

**Identifiers**:
- BMS panels
- Flame scanners and flame safeguard relays
- Purge timers
- Vendors: Honeywell Flame Safety, Fireye, Siemens LMV

**Rule**: **NEVER INSTALL** agents on BMS controllers.

---

### 5. Machine Safety Systems
**Description**: Systems that protect operators from moving machinery.

**Common Components**:
- Safety PLCs (e.g., Siemens S7-F, Rockwell GuardLogix)
- Safety relays
- E-stops (emergency stop buttons)
- Light curtains, safety mats, interlocks
- Two-hand control systems

**Identifiers**:
- Yellow safety PLCs or relays
- EN 954-1, ISO 13849, or IEC 61508 certification labels
- "Category 3" or "Category 4" rated

**Rule**: **NEVER INSTALL** agents on safety PLCs or safety relay servers.

---

### 6. Access Control and Personnel Safety
**Description**: Systems that prevent unauthorized access to hazardous areas.

**Examples**:
- Safety interlocks (doors, gates)
- LOTO (Lockout/Tagout) systems
- Confined space monitoring
- Man-down alarms

**Rule**: **DO NOT INSTALL** agents on interlock controllers or safety access systems.

---

### 7. Radiation Safety Systems
**Description**: Systems in nuclear, medical, or industrial facilities that monitor and control radiation exposure.

**Identifiers**:
- Radiation detectors
- Dosimetry systems
- Emergency radiation shutdown systems

**Rule**: **NEVER INSTALL** agents on radiation safety systems. Requires NRC (Nuclear Regulatory Commission) approval.

---

### 8. Aviation and Rail Safety Systems
**Description**: Safety-critical systems in transportation.

**Examples**:
- Air traffic control systems
- Railway signaling systems
- Positive Train Control (PTC)

**Rule**: **NEVER INSTALL** agents without explicit approval from aviation or rail authority (FAA, FRA, etc.).

---

## How to Identify Safety Systems

### Ask These Questions:
1. **"Is this system safety-rated or safety-certified?"**
   - If yes → DO NOT INSTALL

2. **"Does this system have a SIL rating (SIL 1/2/3/4)?"**
   - If yes → DO NOT INSTALL

3. **"Is this system required for emergency shutdown?"**
   - If yes → DO NOT INSTALL

4. **"Would a failure of this system cause injury, death, or environmental harm?"**
   - If yes → DO NOT INSTALL

5. **"Does this system control a safety function (E-stops, interlocks, fire suppression)?"**
   - If yes → DO NOT INSTALL

6. **"Is this system on a separate safety network?"**
   - If yes → Likely a safety system → DO NOT INSTALL

7. **"Does modifying this system void safety certification?"**
   - If yes or unsure → DO NOT INSTALL

### Visual Identifiers:
- [ ] Red or yellow colored equipment
- [ ] "Safety" labels or placards
- [ ] SIL rating labels (SIL 1, 2, 3, 4)
- [ ] TÜV, UL, FM, or other safety certification labels
- [ ] "Do Not Modify" or "Authorized Personnel Only" warnings
- [ ] Separate network labeled "Safety Network"
- [ ] Dual or triple redundant controllers (common in safety systems)

### Network Identifiers:
- [ ] Separate VLANs for safety (not connected to IT network)
- [ ] Safety network protocols: SafetyNET p, SafetyBUS p, PROFIsafe
- [ ] No internet connectivity (safety systems are typically air-gapped)

### Vendor Identifiers:
Known safety system vendors (this list is not exhaustive):
- Honeywell Safety Manager
- Siemens Safety Integrated (S7-F PLCs)
- Rockwell GuardLogix
- Schneider Triconex
- Yokogawa ProSafe-RS
- HIMA Safety Systems
- ABB System 800xA Safety
- Emerson DeltaV Safety Instrumented System (SIS)

If you see these vendors in a safety context, **verify before installing**.

---

## Pre-Deployment Safety Review Process

### Step 1: Request Safety System List (1 Week Before Arrival)
Send email to customer:

**Subject**: Insa SOC Deployment - Safety System Identification Required

```
Hi [Customer Contact],

As part of our pre-deployment planning for Insa Managed SOC services, we need to identify all safety systems that should be excluded from monitoring.

Safety systems (SIS, ESD, F&G, BMS, etc.) will NOT have agents installed. We can monitor these systems via network-level monitoring (SNMP) if approved by your safety team.

Please provide:
1. List of all safety-rated systems (hostnames, IP addresses, descriptions)
2. Network diagram showing safety networks (if separate from control network)
3. Contact information for your site safety engineer or safety manager

We will review this list with your safety team before any deployment activity.

Thank you,
[Your Name]
Insa Field Technician
```

### Step 2: Review Safety System List
- [ ] Receive safety system list from customer
- [ ] Mark all safety systems as "EXCLUDED" in asset inventory
- [ ] Highlight in red on network diagram
- [ ] Print list and keep with you during deployment

### Step 3: Safety Briefing On-Site (Day 1 Morning)
- [ ] Meet with customer safety engineer or OT manager
- [ ] Review safety system list together
- [ ] Walk through list of planned agent deployments
- [ ] Get verbal confirmation of systems to exclude
- [ ] Ask: "Are there any other systems I should avoid?"
- [ ] Document conversation in field notes

### Step 4: Get Written Approval (Day 1 Afternoon)
- [ ] Provide customer with final list of systems for agent deployment
- [ ] Get written sign-off (email or signature on deployment plan)
- [ ] Include statement: "The above list excludes all safety systems as identified by [Customer Safety Engineer Name]"

### Step 5: Double-Check Before Each Installation
Before installing agent on ANY OT system:
- [ ] Verify system is NOT on safety exclusion list
- [ ] Ask OT operator: "Is this a safety system?"
- [ ] If any doubt, STOP and consult customer safety engineer

---

## What If You Accidentally Install on a Safety System?

### Immediate Actions:
1. **STOP** immediately if you realize during installation
2. **Uninstall agent immediately** (see `ROLLBACK_PROCEDURE.md`)
3. **Notify customer safety engineer immediately**
   - Explain what was installed
   - Explain that it has been removed
   - Provide uninstall verification
4. **Notify Insa project manager immediately**
   - Document incident
   - Prepare incident report
5. **Do NOT continue deployment** until safety engineer confirms no impact

### If Already Installed and Running:
1. **Notify customer safety engineer IMMEDIATELY**
2. **Do NOT uninstall without safety engineer approval**
   - Uninstalling might disrupt system if agent is integrated
   - Safety engineer must assess impact
3. **Document current state**:
   - Agent version
   - Configuration
   - Services running
   - Performance impact (CPU, memory)
4. **Follow safety engineer's instructions**
   - They may want to monitor system for a period before removal
   - They may require formal incident investigation
5. **Prepare for formal incident report**:
   - Root cause analysis (why was system misidentified?)
   - Corrective actions (additional training, process improvements)
   - Preventive actions (how to prevent recurrence)

### If Safety Certification is Impacted:
- Customer may need to re-certify safety system (expensive, time-consuming)
- Insa may be liable for re-certification costs
- Escalate to Insa legal and insurance teams
- Full cooperation with customer investigation

---

## Alternative Monitoring for Safety Systems

### Option 1: Network-Level Monitoring (Recommended)
**What**: Monitor safety systems via network traffic analysis, not agents.

**How**:
- Configure jump box to mirror safety network traffic (SPAN port)
- Use passive monitoring (no agents on safety systems)
- Detect anomalies in network patterns

**Benefits**:
- No software on safety system
- Does not void certifications
- Still provides visibility

**Requires**:
- Customer approval
- Safety engineer sign-off
- Network team to configure SPAN port

### Option 2: SNMP Monitoring (If Supported)
**What**: Use SNMP to query basic metrics from safety system controllers.

**How**:
- Enable SNMP on safety controller (read-only community string)
- Configure jump box to poll SNMP (see `AGENT_DEPLOYMENT_CHECKLIST.md` Section 3.2)
- Limit to basic metrics (uptime, CPU, memory) - no control functions

**Benefits**:
- No agent required
- SNMP is often pre-approved by vendors

**Requires**:
- Safety engineer approval
- SNMP supported by safety controller
- Verify SNMP polling does not impact controller performance

### Option 3: Separate Safety SIEM (Advanced)
**What**: Deploy a separate Insa SOC instance dedicated to safety systems.

**How**:
- Install separate jump box on safety network (air-gapped from IT)
- Deploy agents only after safety certification review
- Use safety-rated agent build (if available)

**Requires**:
- Customer has budget for separate SOC
- Insa offers safety-rated agent (currently in development)
- Full safety certification process (IEC 61508, etc.)
- Timeline: 6-12 months for certification

---

## Regulatory and Compliance Considerations

### OSHA (Occupational Safety and Health Administration)
- OSHA requires safety systems to be maintained per manufacturer specifications
- Installing unauthorized software may violate OSHA 1910.119 (Process Safety Management)
- Customer could face OSHA fines if safety system is compromised

### EPA (Environmental Protection Agency)
- EPA requires safety systems in chemical facilities (RMP - Risk Management Plan)
- Unauthorized modifications can violate EPA regulations

### NERC-CIP (Energy Sector)
- Critical Cyber Assets (CCA) in energy sector
- Safety systems may be classified as CCA
- Requires change management and cybersecurity controls
- Installing agent without NERC-CIP change process is a violation

### FDA (Pharmaceutical and Medical Devices)
- 21 CFR Part 11 requires validation of computerized systems
- Safety systems in pharmaceutical plants must be validated
- Installing agent requires revalidation (expensive, time-consuming)

### Nuclear Regulatory Commission (NRC)
- Strictest safety requirements
- Any modification to safety systems requires NRC approval
- Process takes months to years
- **DO NOT TOUCH** nuclear safety systems without NRC approval

---

## Training and Certification

### Field Technician Requirements:
- [ ] Read and understand this guide before deployment
- [ ] Complete Insa "Safety System Awareness" training (online, 1 hour)
- [ ] Acknowledge understanding via signed form
- [ ] Annual refresher training required

### Customer Safety Engineer Involvement:
- Require customer safety engineer to:
  - Participate in pre-deployment planning
  - Approve final list of monitored systems
  - Be available during deployment (phone or on-site)
  - Sign-off on deployment completion

---

## Case Studies (Lessons Learned)

### Case Study 1: ESD System Unintended Impact
**Incident**: Field technician installed agent on a server that interfaced with ESD system. Agent's vulnerability scanner triggered a network scan that caused ESD controller to log a fault (false alarm).

**Impact**: Operators investigated false alarm, wasted 2 hours.

**Root Cause**: Technician did not realize server was connected to ESD network.

**Corrective Action**: Updated pre-deployment checklist to explicitly ask about system interfaces, not just primary function.

### Case Study 2: BMS Certification Voided
**Incident**: Agent installed on Burner Management System HMI. Customer's insurance inspector discovered during audit. BMS vendor stated that certification was voided by unauthorized software.

**Impact**: Customer had to pay $50,000 for BMS re-certification. Production halted for 1 week.

**Root Cause**: Technician did not recognize BMS as a safety system.

**Corrective Action**: Added BMS to safety system list in this guide. Enhanced technician training.

### Case Study 3: Near-Miss on Safety PLC
**Incident**: Technician prepared to install agent on yellow-colored PLC. OT operator stopped technician, explaining it was a safety PLC for E-stops.

**Impact**: None (near-miss, agent not installed).

**Root Cause**: Asset inventory did not flag system as safety PLC.

**Corrective Action**: Added visual identifier check (yellow equipment) to pre-installation checklist. Reinforced "when in doubt, ask" culture.

---

## Red Flags and Warning Signs

**If you see any of these, STOP and verify**:
- [ ] System labeled "Safety" or "SIS"
- [ ] Red or yellow equipment
- [ ] SIL rating labels
- [ ] Separate safety network
- [ ] Vendor names associated with safety (Triconex, Tristation, etc.)
- [ ] System not on IT network (air-gapped)
- [ ] OT operator says "be careful with that one"
- [ ] System has redundant controllers (1oo2, 2oo3, etc. - safety voting)
- [ ] Fire alarm panels nearby
- [ ] E-stop buttons connected to system

**When in doubt, DO NOT INSTALL. Ask the customer safety engineer.**

---

## Acknowledgment and Sign-Off

I, _________________________ (Field Technician Name), acknowledge that I have read and understood the Safety System Exclusion Guide. I understand that:
- Safety systems protect human life and must not be modified without authorization
- I must identify and exclude safety systems before deploying agents
- I will stop and consult the customer safety engineer if I have any doubt
- Failure to follow this guide can result in catastrophic consequences

**Signature**: _________________________
**Date**: _________________________
**Deployment**: _________________________ (Customer Name)

---

## Appendix: Safety System Identification Checklist

Use this checklist on-site:

**System Name**: _________________________
**Hostname/IP**: _________________________

- [ ] Is this system safety-rated or safety-certified?
- [ ] Does this system have a SIL rating?
- [ ] Is this system required for emergency shutdown?
- [ ] Would a failure of this system cause injury, death, or environmental harm?
- [ ] Does this system control a safety function (E-stops, interlocks, fire suppression)?
- [ ] Is this system on a separate safety network?
- [ ] Does modifying this system void safety certification?
- [ ] Is this system red or yellow colored?
- [ ] Does this system have safety certification labels (TÜV, UL, FM)?
- [ ] Is this system from a known safety vendor (Triconex, Safety Manager, etc.)?

**If any answer is YES → DO NOT INSTALL**

**Customer Safety Engineer Approval**: _________________________
**Date**: _________________________

---

**Document Version**: 1.0
**Last Updated**: October 11, 2025
**Owner**: Insa Automation Corp
**Classification**: CRITICAL - Required Reading for All Field Technicians

---

*Made by Insa Automation Corp for OpSec Excellence*

**Safety is not negotiable. When in doubt, DO NOT INSTALL.**
