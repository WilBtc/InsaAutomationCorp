# Installation Kit Contents - Managed SOC Deployment

**Insa Automation Corp - DevSecOps Platform**
**Version**: 1.0
**Last Updated**: October 11, 2025
**Purpose**: Complete equipment list for field technician deployment kit

---

## Overview

Every field technician must carry a standardized installation kit to customer sites. This ensures consistent deployments and reduces risk of missing critical components.

**Kit Weight**: ~25 lbs
**Kit Size**: Pelican 1510 case (carry-on sized)
**Total Value**: ~$8,000

---

## 1. Jump Box Hardware

### Primary Jump Box
- **Insa Jump Box Model JB-2024** (custom-built)
  - Dell PowerEdge R240 or equivalent
  - Specs: 16GB RAM, 512GB NVMe SSD, dual NICs
  - Pre-installed: Ubuntu 22.04 LTS + Insa agent relay software
  - Hostname: `insa-jumpbox-template` (will be renamed on-site)
  - Serial: [Record in deployment checklist]

- **Accessories**:
  - 2x Power cables (C13 to local plug + C13 to NEMA 5-15)
  - 2x Cat6 Ethernet cables (6ft, different colors for clarity)
  - 1x Console cable (RJ45 to USB-A)
  - 4x Rack mount screws and cage nuts
  - 1x Cable management kit

### Backup/Emergency Hardware
- **Raspberry Pi 4B (8GB)** - Emergency jump box
  - Pre-configured SD card with minimal agent relay
  - Use if primary jump box fails
  - Includes: case, power supply, heatsinks

- **USB-to-Ethernet adapter** (for laptop)
- **Serial console adapter** (USB-to-DB9)

---

## 2. Network Equipment

### Cables and Adapters
- [ ] 6x Cat6 Ethernet cables (assorted lengths: 3ft, 6ft, 10ft, 25ft, 50ft, 100ft)
- [ ] 2x Fiber optic cables (LC-LC, 10ft) - if customer uses fiber to DMZ
- [ ] 1x Console cable kit (RJ45, DB9, USB-C adapters)
- [ ] 2x USB-C to Ethernet adapters (1Gbps)
- [ ] 1x Travel router (for isolated testing)

### Testing Tools
- [ ] Fluke LinkRunner AT Network Tester (or equivalent)
  - Tests: link speed, PoE, switch port ID, VLAN
- [ ] Cable tester (for patch cable validation)
- [ ] Tone and probe kit (for cable tracing)
- [ ] Fiber optic tester (if customer uses fiber)

### Network Diagnostic Tools (Laptop-Based)
- [ ] Wireshark (pre-installed)
- [ ] Nmap
- [ ] Netcat
- [ ] iperf3 (bandwidth testing)
- [ ] Packet capture tools

---

## 3. Software and Installation Media

### Agent Installers (USB Drive #1 - "Agents")
**Labeled**: "Insa Agents - v2.4.1 - Oct 2025"
**Capacity**: 128GB USB 3.2 drive

**Contents**:
```
/agents/
  /windows/
    - InsaAgent-2.4.1-x64.msi (Windows Server 2012-2022, Win10/11)
    - InsaAgent-2.4.1-x86.msi (legacy 32-bit systems)
    - install.ps1 (automated deployment script)
    - GPO-deployment-guide.pdf

  /linux/
    - insa-agent-2.4.1-amd64.deb (Ubuntu/Debian)
    - insa-agent-2.4.1.x86_64.rpm (RHEL/CentOS)
    - insa-agent-2.4.1-arm64.deb (Raspberry Pi, ARM servers)
    - install.sh (automated deployment script)
    - systemd service files

  /embedded/
    - insa-agent-2.4.1-mips.tar.gz (for IIoT gateways)
    - insa-agent-2.4.1-arm.tar.gz (embedded Linux)
    - install-embedded.sh

  /config-templates/
    - agent.conf.template (generic)
    - agent.conf.pharma (FDA 21 CFR Part 11 optimized)
    - agent.conf.energy (NERC-CIP optimized)
    - agent.conf.manufacturing (ISA/IEC 62443 optimized)

  /docs/
    - Agent Installation Guide.pdf
    - Troubleshooting Guide.pdf
    - Configuration Reference.pdf
```

### Jump Box Software (USB Drive #2 - "Jump Box")
**Labeled**: "Insa Jump Box - v3.1.2 - Oct 2025"
**Capacity**: 64GB USB 3.2 drive

**Contents**:
```
/jumpbox/
  /os/
    - ubuntu-22.04.3-live-server-amd64.iso (for bare metal install)

  /software/
    - insa-jumpbox-setup-3.1.2.tar.gz (complete jump box stack)
    - defectdojo-agent-service-2.4.1.tar.gz
    - container-orchestrator-1.0.3.tar.gz

  /certificates/
    - [Customer-specific TLS certs - generated pre-deployment]
    - CA bundle
    - Certificate installation script

  /config/
    - jumpbox.conf.template
    - firewall-rules.txt (customer-specific)
    - network-config.yaml

  /docs/
    - Jump Box Deployment Guide.pdf
    - Network Architecture Diagram.pdf
    - Firewall Requirements.pdf
```

### Diagnostic and Utilities (USB Drive #3 - "Tools")
**Labeled**: "Insa Field Tools - Oct 2025"
**Capacity**: 32GB USB 3.2 drive

**Contents**:
```
/tools/
  /network/
    - Wireshark portable
    - nmap/zenmap portable
    - PuTTY portable (SSH/Telnet client)
    - Advanced IP Scanner
    - Angry IP Scanner

  /security/
    - OpenSSL tools
    - TLS certificate validator
    - Hash verification tools (sha256sum)

  /system/
    - Process Monitor (Windows)
    - htop/iotop (Linux)
    - Performance monitoring scripts

  /backup/
    - Agent uninstall scripts (for rollback)
    - Configuration backup scripts
    - Emergency data recovery tools
```

### Software Licenses and Keys (Encrypted USB Drive #4)
**Labeled**: "Insa Licenses - ENCRYPTED"
**Capacity**: 16GB encrypted USB drive
**Password**: [Provided by Insa PM on per-deployment basis]

**Contents**:
- DefectDojo API keys
- Jump box SSH private keys
- Customer-specific credentials (if pre-shared)
- Software license files
- Certificate private keys

**Security**: AES-256 encrypted, auto-locks after 15 min idle

---

## 4. Documentation and Procedures

### Customer Deliverables Binder (Physical)
**Binder Contents**:
1. **Tab 1: Overview**
   - Insa Managed SOC Overview (glossy handout)
   - Deployment summary (fill in on-site)
   - Contact list (Insa SOC, support, PM)

2. **Tab 2: Network Documentation**
   - Network diagram (as-built, mark up on-site)
   - Asset inventory checklist
   - Firewall rules (approved and implemented)
   - IP address assignments

3. **Tab 3: Jump Box**
   - Jump Box Deployment Guide
   - Jump Box admin credentials (sealed envelope)
   - Service restart procedures
   - Log locations

4. **Tab 4: Agents**
   - Agent installation guide (per OS)
   - Agent configuration reference
   - Troubleshooting flowchart
   - Update procedures

5. **Tab 5: Platform Access**
   - DefectDojo login instructions
   - User guide (quick start)
   - Reporting guide
   - Compliance mapping (sector-specific)

6. **Tab 6: Operations**
   - Incident response procedures
   - Escalation contacts
   - SLA reference
   - Change management process

7. **Tab 7: Compliance and Audit**
   - Audit evidence collection guide
   - Regulatory mapping (NERC-CIP, FDA, etc.)
   - Compliance report samples
   - Data retention policy

8. **Tab 8: Training**
   - Training slides (printed)
   - Quick reference cards
   - FAQ sheet
   - Knowledge base access

9. **Tab 9: Acceptance**
   - Deployment acceptance checklist
   - Sign-off form (get customer signature)
   - Outstanding items list
   - Follow-up schedule

### Field Technician Procedures (Laptop-Based)
**Stored on laptop + printed backup**:
- [ ] `FIELD_TECHNICIAN_GUIDE.md` (this master guide)
- [ ] `JUMP_BOX_DEPLOYMENT.md`
- [ ] `AGENT_DEPLOYMENT_CHECKLIST.md`
- [ ] `SAFETY_SYSTEM_EXCLUSION.md` (CRITICAL - also print)
- [ ] `ROLLBACK_PROCEDURE.md`
- [ ] Sector-specific compliance guides (pharma, energy, etc.)

---

## 5. Personal Equipment

### Technician Laptop
**Minimum Specs**:
- 16GB RAM
- 512GB SSD
- Windows 11 Pro or Ubuntu 22.04
- TPM 2.0 (for BitLocker/LUKS encryption)

**Required Software**:
- SSH client (PuTTY, OpenSSH, or Termius)
- VNC/RDP client (for remote desktop)
- Wireshark
- Text editor (VS Code, Notepad++, vim)
- PDF reader
- Insa VPN client (for remote support)
- DefectDojo web access (browser)
- Project management tool (for field notes)

**Laptop Accessories**:
- [ ] 2x Laptop chargers (1 backup)
- [ ] USB-C hub with Ethernet, HDMI, USB-A
- [ ] External mouse
- [ ] Portable monitor (optional, for dual-screen work)

### Personal Protective Equipment (PPE)
**Bring if required by customer site**:
- [ ] Safety glasses (ANSI Z87.1)
- [ ] Steel-toe boots (ASTM F2413)
- [ ] Hard hat (ANSI Z89.1)
- [ ] High-visibility vest
- [ ] Hearing protection (earplugs or muffs)
- [ ] FR (flame-resistant) clothing (for refineries, power plants)
- [ ] Latex/nitrile gloves (for dusty environments)

**Note**: Always verify customer PPE requirements 1 week before deployment.

### Tools and Accessories
- [ ] Multi-bit screwdriver (for rack mounting)
- [ ] Flashlight (for dark server rooms)
- [ ] Velcro cable ties (for cable management)
- [ ] Label maker or pre-printed labels
- [ ] Notebook and pens (for field notes)
- [ ] Business cards (for customer contacts)
- [ ] Badge holder/lanyard (for customer badge)

---

## 6. Emergency and Rollback Equipment

### Rollback Kit (In Case of Issues)
**See**: `ROLLBACK_PROCEDURE.md` for usage instructions

- [ ] Agent uninstall scripts (on Tools USB drive)
- [ ] Jump box decommission script
- [ ] Firewall rule removal instructions (customer-specific)
- [ ] Data export tools (to preserve logs if needed)
- [ ] Customer notification template (email/letter)

### Emergency Contact Info (Printed Card)
**Laminated card with**:
- Insa SOC 24/7 phone: [TBD]
- Insa Project Manager: [TBD]
- Insa Technical Support: [TBD]
- Insa Emergency Escalation: [TBD]
- Customer primary contact: [Fill in on-site]
- Customer emergency contact: [Fill in on-site]

---

## 7. Shipping and Transportation

### Checked Luggage (If Flying)
**Pelican 1650 case** (larger, for jump box hardware):
- Jump box server (well-padded)
- Power supplies
- Long network cables (50ft, 100ft)
- Rack mount hardware
- Backup Raspberry Pi

**TSA Considerations**:
- Remove lithium batteries from checked luggage
- Include "Fragile - Electronic Equipment" labels
- Use TSA-approved locks
- Include business card inside case with contact info

### Carry-On (Always Keep With You)
**Pelican 1510 case** (carry-on sized):
- USB drives with all software (Agents, Jump Box, Tools)
- Encrypted USB with credentials
- Laptop
- Console cables and adapters
- Customer deliverables binder
- Printed procedures (backup)

**Reason**: Cannot afford to lose software or credentials in checked luggage.

### Shipping to Customer Site (Alternative)
If kit is too large to fly with:
- Ship jump box hardware 1 week in advance to customer IT department
- Use FedEx/UPS with signature required
- Include packing list
- Coordinate delivery with customer contact
- Insure for full replacement value

---

## 8. Kit Maintenance and Inventory

### Pre-Deployment Checklist (1 Week Before)
- [ ] Verify all USB drives boot/load correctly
- [ ] Check laptop battery holds charge
- [ ] Update agent software to latest version
- [ ] Generate customer-specific TLS certificates
- [ ] Encrypt credentials USB with deployment password
- [ ] Print customer deliverables binder
- [ ] Test jump box powers on and POSTs
- [ ] Verify all cables and adapters functional
- [ ] Check PPE is in good condition (no cracks in safety glasses, etc.)
- [ ] Confirm all items from this list are in kit

### Post-Deployment Checklist (Return from Site)
- [ ] Inventory all equipment (nothing left at customer site)
- [ ] Wipe customer-specific data from USB drives
- [ ] Delete customer credentials from encrypted USB
- [ ] Remove customer TLS certificates
- [ ] Clean and sanitize equipment
- [ ] Recharge all batteries
- [ ] Replace any damaged cables or adapters
- [ ] Restock consumables (Velcro ties, labels, etc.)
- [ ] Update kit inventory log
- [ ] Report any missing or broken items to Insa PM

### Quarterly Kit Audit
Insa operations will audit all field kits quarterly:
- [ ] Verify all items present
- [ ] Check expiration on batteries
- [ ] Update software to latest versions
- [ ] Replace worn PPE
- [ ] Recalibrate network testing tools (if required)
- [ ] Update documentation to latest versions

---

## 9. Kit Variations by Sector

### Pharmaceutical/FDA
**Additional Items**:
- 21 CFR Part 11 compliance checklist
- Electronic signature validation tools
- Audit trail verification scripts
- GxP documentation templates

### Energy/Utilities (NERC-CIP)
**Additional Items**:
- NERC-CIP compliance mapping
- CIP-007 monitoring templates
- SCADA protocol analyzers (Modbus, DNP3)
- ICS-specific network diagrams

### Manufacturing (ISA/IEC 62443)
**Additional Items**:
- ISA/IEC 62443 compliance checklist
- Industrial protocol analyzers
- OPC UA testing tools
- Safety system identification guide (extra copies)

### Water/Wastewater
**Additional Items**:
- SCADA security best practices (AWWA)
- Water sector threat intelligence briefing
- Emergency response procedures (for critical infrastructure)

---

## 10. Cost and Procurement

### Kit Cost Breakdown
| Item | Quantity | Unit Cost | Total |
|------|----------|-----------|-------|
| Jump Box Hardware (Dell R240) | 1 | $2,500 | $2,500 |
| Raspberry Pi Backup | 1 | $150 | $150 |
| USB Drives (4x enterprise-grade) | 4 | $50 | $200 |
| Network Cables (assorted) | 12 | $15 | $180 |
| Fluke LinkRunner Tester | 1 | $1,200 | $1,200 |
| Pelican Cases (1510 + 1650) | 2 | $250 | $500 |
| Laptop Accessories | 1 set | $200 | $200 |
| PPE Kit (complete) | 1 set | $300 | $300 |
| Tools and Adapters | 1 set | $150 | $150 |
| Customer Deliverables (binder, printing) | 1 | $100 | $100 |
| **Total** | | | **$5,480** |

**Replacement Budget**: $2,000/year (for wear and tear)

### Procurement Process
1. Insa operations maintains 3 complete kits (for 3 concurrent deployments)
2. Kits are assigned to technician 1 week before deployment
3. Technician signs equipment checkout form
4. Any damaged/missing items reported within 24 hours of return
5. Insa operations restocks and audits kit before next deployment

---

## Appendix: Kit Photos and Diagrams

### Kit Layout Diagram
```
[Pelican 1510 - Carry-On]
┌─────────────────────────────────┐
│  Laptop (padded compartment)    │
├─────────────────────────────────┤
│  USB Drives (4x in foam cutout) │
├─────────────────────────────────┤
│  Cables (coiled, in mesh pocket)│
├─────────────────────────────────┤
│  Binder (customer deliverables) │
├─────────────────────────────────┤
│  Tools (small pouch)            │
└─────────────────────────────────┘

[Pelican 1650 - Checked/Shipped]
┌─────────────────────────────────┐
│  Jump Box (2U, foam padded)     │
├─────────────────────────────────┤
│  Power Supplies (2x)            │
├─────────────────────────────────┤
│  Long Cables (50ft, 100ft)      │
├─────────────────────────────────┤
│  Raspberry Pi Backup            │
├─────────────────────────────────┤
│  Network Tester                 │
└─────────────────────────────────┘
```

### Deployment Day 1 - Items to Bring to Server Room
**Minimal carry** (server rooms are often cramped):
- Laptop
- Jump box
- Power cable for jump box
- 2x Ethernet cables
- Console cable
- Screwdriver
- Flashlight
- Notebook

**Leave in staging area**:
- Everything else (retrieve as needed)

---

## Quick Reference: What to Bring Where

### Customer Meeting Room (Day 1 kickoff)
- Laptop
- Customer deliverables binder
- Notebook
- Business cards

### Server Room / Data Center
- Laptop
- Jump box + accessories
- Network cables
- Console cable
- Tools
- Flashlight

### OT Floor / Manufacturing Area
- Laptop
- Agent installer USB drives
- PPE (if required)
- Safety system exclusion guide (printed)
- Notebook

### Customer Training Room (Day 3)
- Laptop
- Customer deliverables binder
- Training slides (printed backup)
- Quick reference cards

---

**Document Version**: 1.0
**Last Updated**: October 11, 2025
**Owner**: Insa Automation Corp
**Classification**: Internal Use - Field Technicians Only

**Kit ID**: [Assign unique ID to each kit]
**Assigned Technician**: [Name]
**Deployment**: [Customer Name - Date]

---

*Made by Insa Automation Corp for OpSec Excellence*
