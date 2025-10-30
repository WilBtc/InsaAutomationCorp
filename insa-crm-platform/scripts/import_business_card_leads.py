#!/usr/bin/env python3
"""
Business Card Lead Import Script
Imports 24 leads from business card collection into ERPNext CRM
"""

import json
import subprocess
import time
from datetime import datetime

# Lead data from business card collection
LEADS_DATA = [
    {
        "lead_name": "Richard Hoydell",
        "company_name": "Accel Compression, Inc.",
        "email_id": None,
        "phone": "(432) 563-1376",
        "mobile_no": None,
        "designation": "Sales Representative",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Oil & Gas - Upstream",
        "address_line1": "4500 SCR 1310",
        "city": "Odessa",
        "state": "Texas",
        "country": "United States",
        "pincode": "79765",
        "website": "www.accelcompression.com",
        "notes": f"""TOP PRIORITY - Tier 1 Contact (Opportunity Score: 9.5/10)

Company Type: Oil & Gas Equipment - Compression
Geographic Focus: Permian Basin, Eagle Ford Shale

Products/Services:
- Natural gas compressors (small horsepower)
- Vapor recovery units (VRU)
- Wellhead pressure reduction
- Air compressors
- Field service and repair

Strategic Value:
Perfect fit for TSA pipeline security compliance, remote SCADA cybersecurity, Colombian oil market expansion.

Partnership Potential:
OEM integration, joint solutions for remote compressor security.

Compliance Drivers:
- TSA Pipeline Security Directives
- EPA emissions reporting
- API 1164 SCADA security

Technology Stack:
- PLCs for compressor control
- VFDs for speed control
- Remote monitoring (cellular/radio)
- SCADA integration

Immediate Opportunities:
- Secure remote monitoring solutions
- TSA compliance support
- Vapor recovery system cybersecurity

Also represents WJM Pumps - multi-line representative with broad industrial contacts.
KEY STRATEGIC CONTACT for Texas oil & gas market entry.

Next Action: Initial contact call within 1 week
Action Date: 2025-11-06
Tags: tier1, oil_gas, texas, remote_operations, tsa_compliance, permian_basin""",
        "custom_opportunity_score": 9.5,
        "custom_priority_tier": 1
    },
    {
        "lead_name": "Mike Van Tyn",
        "company_name": "Titan Industries / Titan Solutions",
        "email_id": None,
        "phone": None,
        "mobile_no": None,
        "designation": "Sales Representative",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Chemical Processing",
        "address_line1": "22335 Gosling Rd",
        "city": "Spring",
        "state": "Texas",
        "country": "United States",
        "pincode": "77389",
        "website": "www.titan-solutions.com",
        "notes": f"""TOP PRIORITY - Tier 1 Contact (Opportunity Score: 9.0/10)

Company Type: Chemical Equipment Manufacturing
Geographic Focus: US (bulk fuel terminals, pipelines)

Products/Services:
- Chemical additive injection systems
- Wireless data acquisition
- Metering and delivery solutions
- Butane blending systems
- Turnkey installations
- VRU systems

Strategic Value:
Chemical equipment with sophisticated controls, TSA/CFATS compliance driver, wireless systems requiring security.

Partnership Potential:
OEM cybersecurity integration, joint compliance solutions.

Compliance Drivers:
- TSA Pipeline Security
- CFATS (chemical facilities)
- API standards

Technology Stack:
- Microcontroller-based injectors
- Wireless data acquisition
- PLCs and HMIs
- Pipeline SCADA integration

Immediate Opportunities:
- Secure wireless data systems
- TSA/CFATS compliance
- Chemical injection system hardening

World leader in chemical equipment innovation with patented technologies. Largest butane blending system in US.
Prime target for OT security integration.

Next Action: Initial contact call this week
Action Date: 2025-11-06
Tags: tier1, chemical, pipelines, texas, tsa_compliance, wireless_security""",
        "custom_opportunity_score": 9.0,
        "custom_priority_tier": 1
    },
    {
        "lead_name": "Nathan Oakes",
        "company_name": "Crume Sales, Inc.",
        "email_id": None,
        "phone": None,
        "mobile_no": None,
        "designation": "Sales Representative",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Industrial Controls",
        "city": "Odessa",
        "state": "Texas",
        "country": "United States",
        "notes": f"""TOP PRIORITY - Tier 1 Contact (Opportunity Score: 8.5/10)

Company Type: Industrial Valves & Controls
Geographic Focus: Texas, Oklahoma, nationwide coverage

Products/Services:
- Industrial valves (all types)
- Valve automation and controls
- Smart positioners
- Emergency shutdown (ESD) systems
- In-house service and repair
- Onsite field service
- PRV recertification

Strategic Value:
Valve automation with sophisticated controls, ESD system security, West Texas market access.

Partnership Potential:
Service partnership, valve control security, ESD protection.

Compliance Drivers:
- TSA Pipeline Security
- API 1164
- Safety Integrity Level (SIL) requirements

Technology Stack:
- Smart valve positioners
- PLCs for valve sequencing
- ESD control systems
- SCADA integration
- Digital actuators

Immediate Opportunities:
- ESD system cybersecurity
- Smart valve network security
- Pipeline valve TSA compliance

Industry leader in valve business. Family-owned with strong customer relationships.
Service business = recurring revenue opportunity.

Next Action: Initial contact call within 1 week
Action Date: 2025-11-06
Tags: tier1, valves, oil_gas, texas, oklahoma, esd_systems""",
        "custom_opportunity_score": 8.5,
        "custom_priority_tier": 1
    },
    {
        "lead_name": "Luis Galindo",
        "company_name": "UP&S Inc. (United Pump & Supply)",
        "email_id": "luis@up-s.com",
        "phone": "(432) 332-9753",
        "mobile_no": None,
        "designation": "Vice President / Chief Operating Officer",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Oil & Gas",
        "address_line1": "212 East 2nd Street",
        "city": "Odessa",
        "state": "Texas",
        "country": "United States",
        "pincode": "79761",
        "website": "www.up-s.com",
        "notes": f"""EXECUTIVE PRIORITY - Tier 1 Contact (Opportunity Score: 9.0/10)

EXECUTIVE LEVEL: Vice President / Chief Operating Officer

Company Type: Industrial Pump Distribution
Geographic Focus: West Texas, Permian Basin

Products/Services:
- Industrial pumps (all types)
- Pump systems and packages
- Controls and automation
- Service and repair
- VFD systems

Strategic Value:
EXECUTIVE LEVEL CONTACT - VP/COO. Pump systems with extensive automation, Permian Basin market leader.

Partnership Potential:
Strategic partnership, executive sponsorship, market access.

Compliance Drivers:
- API standards
- TSA pipeline security
- Municipal water security

Technology Stack:
- Pump control PLCs
- VFD systems
- SCADA integration
- Remote monitoring

Immediate Opportunities:
- Executive partnership discussion
- Pump SCADA security
- Strategic account referrals

VP/COO level - strategic partnership opportunity. Also represents IKA Works.
Key executive for Permian Basin market penetration. This is a TOP-TIER contact.

Next Action: Executive meeting request
Action Date: 2025-11-04 (IMMEDIATE)
Tags: tier1, executive, pumps, oil_gas, texas, permian_basin, strategic_partner""",
        "custom_opportunity_score": 9.0,
        "custom_priority_tier": 1
    },
    {
        "lead_name": "Haeng J. Son",
        "company_name": "SPower Electronics",
        "email_id": None,
        "phone": None,
        "mobile_no": None,
        "designation": "Regional Representative",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Power Electronics",
        "city": "Florida",
        "state": "Florida",
        "country": "United States",
        "website": "www.spowerstech.com",
        "notes": f"""Tier 2 Contact (Opportunity Score: 8.5/10)

Company Type: Power Electronics - UPS Systems
Geographic Focus: North America (Italy-based parent)
Founded: 1987

Products/Services:
- UPS systems (industrial grade)
- Power protection for harsh environments
- Data center power solutions
- Telecommunications power
- Educational equipment
- Agricultural equipment

Strategic Value:
Power protection + cybersecurity = complete OT resilience. NERC CIP compliance synergy.

Partnership Potential:
Joint 'Complete OT Resilience' offering, power + cyber solutions.

Compliance Drivers:
- NERC CIP (power sector)
- IEC 62443
- Data center standards

Technology Stack:
- Smart UPS monitoring
- Network-connected power systems
- Remote management platforms

Immediate Opportunities:
- Power + cybersecurity bundled solutions
- NERC CIP compliance support
- UPS monitoring integration with SIEM

Global player with strong engineering. Power reliability is critical for SCADA/ICS systems.
Natural partnership for critical infrastructure.

Next Action: Discovery call
Action Date: 2025-11-13
Tags: tier2, power_systems, florida, critical_infrastructure, nerc_cip""",
        "custom_opportunity_score": 8.5,
        "custom_priority_tier": 2
    },
    {
        "lead_name": "Carlos A. Chavez",
        "company_name": "WJM Pumps",
        "email_id": None,
        "phone": None,
        "mobile_no": None,
        "designation": "Sales Manager",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Industrial Equipment",
        "state": "Florida",
        "country": "United States",
        "notes": f"""Tier 2 Contact (Opportunity Score: 8.0/10)

Company Type: Industrial Pumps
Geographic Focus: Florida, Southeast

Products/Services:
- Industrial pumps
- Pump control systems
- VFD integration
- Service and maintenance

Strategic Value:
Pump systems with extensive automation, water sector compliance drivers.

Partnership Potential:
Joint pump + security solutions, water sector focus.

Compliance Drivers:
- EPA water security
- AWWA standards
- Municipal requirements

Technology Stack:
- Pump control PLCs
- VFD systems
- SCADA integration
- Remote monitoring

Immediate Opportunities:
- Water treatment plant security
- Pump SCADA protection
- Municipal compliance support

Second WJM contact - compare with Richard Hoydell territory.
May cover different geography or verticals.

Next Action: Territory qualification call
Action Date: 2025-11-13
Tags: tier2, pumps, florida, water_sector, municipal""",
        "custom_opportunity_score": 8.0,
        "custom_priority_tier": 2
    },
    {
        "lead_name": "Luis Galindo (IKA Works)",
        "company_name": "IKA Works",
        "email_id": None,
        "phone": None,
        "mobile_no": None,
        "designation": "Sales Representative",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Process Equipment",
        "website": "www.ika.com",
        "country": "United States",
        "notes": f"""Tier 2 Contact (Opportunity Score: 7.5/10)

Company Type: Process Equipment Manufacturing
Geographic Focus: US (Germany-based parent)
Founded: 1910 (900+ employees global)

Products/Services:
- Laboratory equipment
- Process technology (mixers, dispersers)
- Turnkey process plants
- Bioreactors
- High-pressure homogenizers

Strategic Value:
Process control security, FDA/GMP compliance, battery plant cybersecurity.

Partnership Potential:
OEM integration, turnkey plant security design.

Compliance Drivers:
- FDA regulations
- GMP requirements
- IEC 62443

Technology Stack:
- Process control PLCs
- SCADA systems
- Batch control systems
- Laboratory automation

Immediate Opportunities:
- Battery plant cybersecurity
- Pharmaceutical facility protection
- Process control security

Same Luis Galindo as UP&S VP/COO - he represents IKA as well.
Global company with major customers (BASF, Bayer, P&G). Growing battery market opportunity.

Next Action: Discovery call
Action Date: 2025-11-20
Tags: tier2, process_equipment, pharmaceutical, battery, gmp_compliance""",
        "custom_opportunity_score": 7.5,
        "custom_priority_tier": 2
    },
    {
        "lead_name": "Haiden Hayward",
        "company_name": "Imperative Chemical Partners",
        "email_id": "Haiden.Hayward@imperativechemicals.com",
        "phone": "(432) 556-8036",
        "mobile_no": "(877) 523-3147",
        "designation": "Business Development Executive - IOS",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Chemical Services",
        "address_line1": "11002 W County Rd. 77",
        "city": "Midland",
        "state": "Texas",
        "country": "United States",
        "pincode": "79707",
        "website": "www.imperativechemicals.com",
        "notes": f"""TOP PRIORITY - Tier 1 Contact (Opportunity Score: 9.0/10)

Company Type: Chemical Distribution/Services
Geographic Focus: Permian Basin, West Texas

Products/Services:
- Chemical supply and services
- Oilfield chemicals
- Chemical management
- Technical services

Strategic Value:
Chemical services in Permian Basin, CFATS compliance needs, production optimization.

Partnership Potential:
Joint chemical + cybersecurity solutions, CFATS compliance.

Compliance Drivers:
- CFATS (chemical facility security)
- TSA pipeline security
- EPA regulations

Technology Stack:
- Chemical injection systems
- Monitoring and control systems
- Data management platforms

Immediate Opportunities:
- CFATS compliance support
- Chemical injection system security
- Custody transfer protection

Chemical partners in heart of Permian Basin. Business development role = strategic discussions.
Perfect for CFATS/TSA compliance partnership.

Next Action: Initial contact call
Action Date: 2025-11-06
Tags: tier1, chemical, oil_gas, texas, permian_basin, cfats""",
        "custom_opportunity_score": 9.0,
        "custom_priority_tier": 1
    },
    {
        "lead_name": "Mike Von Ruff",
        "company_name": "Titan Pump Manufacturing, Inc.",
        "email_id": "mvonruff@titanpumpsinc.com",
        "phone": "(281) 817-5611",
        "mobile_no": "(512) 508-5800",
        "designation": "Regional Sales Executive",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Pump Manufacturing",
        "address_line1": "9447 Bamboo Rd.",
        "city": "Houston",
        "state": "Texas",
        "country": "United States",
        "pincode": "77041",
        "website": "www.titanpumpsinc.com",
        "notes": f"""TOP PRIORITY - Tier 1 Contact (Opportunity Score: 9.0/10)

Company Type: Pump Manufacturing
Geographic Focus: Texas, Gulf Coast

Products/Services:
- High-performance pumps
- Process pumps
- Custom pump solutions
- Parts and service
- Pump packages

Strategic Value:
Pump manufacturer with process control, Houston industrial market access, refinery connections.

Partnership Potential:
OEM integration, pump control security, refinery cybersecurity.

Compliance Drivers:
- API standards
- TSA pipeline security
- Process safety management

Technology Stack:
- Pump monitoring systems
- Control panels
- VFD integration
- SCADA connectivity

Immediate Opportunities:
- Secure pump control systems
- Refinery pump protection
- Process safety system security

Related to Titan Industries (chemical equipment). Houston = major refining hub.
Manufacturing vs distribution = OEM opportunity. Strong process industry connections.

Next Action: Initial contact call
Action Date: 2025-11-06
Tags: tier1, pumps, manufacturing, houston, refineries, oem_partner""",
        "custom_opportunity_score": 9.0,
        "custom_priority_tier": 1
    },
    {
        "lead_name": "Thomas P. Geoca",
        "company_name": "South Coast Hydraulics",
        "email_id": "tomgeoca@schydraulics.com",
        "phone": "(713) 895-7814",
        "mobile_no": "(832) 891-2722",
        "designation": "President",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Hydraulics",
        "address_line1": "10010 Comanche Lane",
        "city": "Houston",
        "state": "Texas",
        "country": "United States",
        "pincode": "77041",
        "website": "www.schydraulics.com",
        "notes": f"""EXECUTIVE PRIORITY - Tier 1 Contact (Opportunity Score: 8.5/10)

EXECUTIVE LEVEL: President

Company Type: Hydraulics & Fluid Power
Geographic Focus: Houston, Texas, Gulf Coast

Products/Services:
- Hydraulic systems
- Fluid power solutions
- Hydraulic controls
- System design
- Service and repair

Strategic Value:
PRESIDENT-LEVEL CONTACT. Hydraulic controls = industrial automation. Houston market access.

Partnership Potential:
Executive partnership, hydraulic control security, strategic account access.

Compliance Drivers:
- Industrial safety standards
- API requirements
- Maritime regulations

Technology Stack:
- Hydraulic control systems
- Electronic controls
- Proportional valves
- Remote monitoring

Immediate Opportunities:
- Hydraulic control system security
- Industrial automation protection
- Marine system cybersecurity

PRESIDENT = strategic decision maker. Fluid Power Specialist since 1968.
Houston location = major industrial hub. Small company = agile partnership potential.

Next Action: Executive meeting request
Action Date: 2025-11-04 (IMMEDIATE)
Tags: tier1, executive, hydraulics, houston, industrial_automation""",
        "custom_opportunity_score": 8.5,
        "custom_priority_tier": 1
    },
    {
        "lead_name": "Meghan Crawford",
        "company_name": "Hawkeye Industries Inc.",
        "email_id": "meghan.crawford@hawkeye.com",
        "phone": "(825) 533-3447",
        "mobile_no": None,
        "designation": "Technical Sales",
        "status": "Lead",
        "source": "Business Card",
        "territory": "Canada",
        "industry": "Industrial Distribution",
        "address_line1": "2110 70 Ave NW",
        "city": "Edmonton",
        "state": "AB",
        "country": "Canada",
        "pincode": "T6P 1N6",
        "website": "www.hawk-eye.com",
        "notes": f"""Tier 2 Contact (Opportunity Score: 7.5/10)

Company Type: Industrial Products Distribution
Geographic Focus: Western Canada, potentially US

Products/Services:
- Industrial products
- Technical solutions
- Distribution services

Strategic Value:
Canadian market access, industrial distribution network.

Partnership Potential:
Distribution channel, Canadian market development.

Compliance Drivers:
- Canadian cybersecurity standards
- NERC CIP (if power sector)
- Pipeline security (Canada)

Immediate Opportunities:
- Canadian market entry
- Industrial automation security
- Pipeline security (if applicable)

Canadian contact - potential entry point for Alberta oil sands market.
Technical sales role = understands customer applications.

Next Action: Qualification call
Action Date: 2025-11-20
Tags: tier2, canada, distribution, industrial, international""",
        "custom_opportunity_score": 7.5,
        "custom_priority_tier": 2
    },
    {
        "lead_name": "Roy Murillo",
        "company_name": "UP&S (United Pump & Supply) - Carlsbad",
        "email_id": "rmurillo@up-s.com",
        "phone": "(575) 748-5501",
        "mobile_no": None,
        "designation": "Carlsbad Operations Manager",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Industrial Distribution",
        "address_line1": "402 S. Canyon",
        "city": "Carlsbad",
        "state": "New Mexico",
        "country": "United States",
        "pincode": "88220",
        "website": "www.up-s.com",
        "notes": f"""Tier 2 Contact (Opportunity Score: 7.0/10)

Company Type: Industrial Pump Distribution
Geographic Focus: Southeast New Mexico, Permian Basin

Products/Services:
- Industrial pumps
- Pump systems
- Controls and automation
- Service and repair

Strategic Value:
Carlsbad operations = Permian Basin east side, potash mining, oil & gas.

Partnership Potential:
Regional partnership, mining sector security.

Compliance Drivers:
- MSHA (mining)
- API standards
- TSA pipeline security

Technology Stack:
- Pump control systems
- VFD systems
- SCADA integration

Immediate Opportunities:
- Mining pump security
- Permian Basin (NM side) penetration
- Regional pump system protection

Third UP&S contact - operations manager for Carlsbad. Potash mining = unique market opportunity.
Connect through Luis Galindo introduction.

Next Action: Discovery call
Action Date: 2025-11-20
Tags: tier2, pumps, new_mexico, mining, permian_basin""",
        "custom_opportunity_score": 7.0,
        "custom_priority_tier": 2
    },
    {
        "lead_name": "Lee Ybarra",
        "company_name": "BPI (Bertrem Products, Inc.)",
        "email_id": "lybarra@bertrem.com",
        "phone": "(432) 559-6555",
        "mobile_no": None,
        "designation": "Outside Sales Representative",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Process Control",
        "address_line1": "1725 E. 2nd St.",
        "city": "Odessa",
        "state": "Texas",
        "country": "United States",
        "pincode": "79761",
        "notes": f"""Tier 2 Contact (Opportunity Score: 7.0/10)

Company Type: Process Control Products
Geographic Focus: West Texas
Founded: 1985

Products/Services:
- Engineered products for process control
- Industrial automation components
- Control systems

Strategic Value:
Process control products = direct automation cybersecurity relevance.

Partnership Potential:
Product distribution, process control security.

Compliance Drivers:
- IEC 62443
- API standards
- ISA security standards

Technology Stack:
- Process controllers
- Instrumentation
- Control panels

Immediate Opportunities:
- Secure process control systems
- Control panel hardening
- Instrumentation cybersecurity

Established since 1985. West Texas location = Permian Basin access.
Process control products directly align with INSA expertise.

Next Action: Qualification call
Action Date: 2025-11-20
Tags: tier2, process_control, texas, odessa, automation""",
        "custom_opportunity_score": 7.0,
        "custom_priority_tier": 2
    },
    {
        "lead_name": "Bynum Vincent",
        "company_name": "IMC (Instrument Maintenance Center), Inc.",
        "email_id": "b.vincent@imco1.bz",
        "phone": "(432) 687-4900",
        "mobile_no": "(432) 634-9644",
        "designation": "Sales/Operations",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Instrumentation",
        "address_line1": "4580 W Wall",
        "city": "Midland",
        "state": "Texas",
        "country": "United States",
        "pincode": "79703",
        "notes": f"""Tier 2 Contact (Opportunity Score: 7.5/10)

Company Type: Instrumentation Services
Geographic Focus: Permian Basin, West Texas

Products/Services:
- Instrument calibration
- Maintenance services
- Control system services
- Field instrumentation

Strategic Value:
Instrumentation services = ongoing customer access, field presence.

Partnership Potential:
Service partnership, field cybersecurity assessments.

Compliance Drivers:
- ISA standards
- API requirements
- Calibration accuracy for custody transfer

Technology Stack:
- Field instruments
- Smart transmitters
- Control system interfaces

Immediate Opportunities:
- Smart instrument security
- Field device hardening
- Calibration data integrity

Instrumentation services = trusted field access to customer sites.
Could identify cybersecurity needs during service calls. Midland location = Permian Basin.

Next Action: Discovery call
Action Date: 2025-11-20
Tags: tier2, instrumentation, texas, midland, field_service""",
        "custom_opportunity_score": 7.5,
        "custom_priority_tier": 2
    },
    {
        "lead_name": "Hong T. Sun",
        "company_name": "mPower Electronics",
        "email_id": "htsun@mpowerinc.com",
        "phone": "(408) 878-5597",
        "mobile_no": None,
        "designation": "President",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Power Electronics",
        "address_line1": "2910 Scott Boulevard",
        "city": "Santa Clara",
        "state": "California",
        "country": "United States",
        "pincode": "95054",
        "website": "www.mpowerinc.com",
        "notes": f"""EXECUTIVE - Tier 2 Contact (Opportunity Score: 7.5/10)

EXECUTIVE LEVEL: President

Company Type: Power Electronics/Sensors
Geographic Focus: California (HQ), Texas product center (Midland, TX 79703)

Products/Services:
- Power electronics
- Sensors ("Making Powerful Senses")
- Electronic components
- Industrial electronics

Strategic Value:
PRESIDENT-LEVEL. Power + sensors = industrial monitoring systems. Midland product center = Permian Basin.

Partnership Potential:
Executive partnership, sensor security, industrial monitoring.

Compliance Drivers:
- Industrial standards
- Quality certifications
- Electronics security

Technology Stack:
- Industrial sensors
- Power management systems
- Electronic monitoring

Immediate Opportunities:
- Sensor network security
- Industrial monitoring protection
- IoT device hardening

PRESIDENT = strategic decision maker. Dual locations (CA + Midland TX) interesting.
'Making Powerful Senses' = sensor focus. IoT/sensor security growing concern.

Next Action: Executive outreach
Action Date: 2025-11-13
Tags: tier2, executive, power_electronics, sensors, california, texas""",
        "custom_opportunity_score": 7.5,
        "custom_priority_tier": 2
    },
    {
        "lead_name": "WIES Contact",
        "company_name": "WIES (Wholesale Industrial Electric Supply)",
        "email_id": None,
        "phone": None,
        "mobile_no": None,
        "designation": "Unknown",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Electrical Distribution",
        "city": "Miami",
        "state": "Florida",
        "country": "United States",
        "notes": f"""Tier 3 Contact (Opportunity Score: 6.5/10)

Company Type: Electrical Distribution
Geographic Focus: South Florida

Products/Services:
- Electrical equipment
- Automation products
- Industrial controls
- Wire and cable

Strategic Value:
Local Miami distributor, access to industrial customer base.

Partnership Potential:
Distribution channel, local market referrals.

Immediate Opportunities:
- Control panel security
- Automation cybersecurity referrals
- Local industrial clients

No specific contact visible on card. Local Miami presence = convenient for INSA.
Need to identify decision maker. Lower priority than out-of-area strategic partners.

Next Action: Identify contact, qualification call
Action Date: 2025-12-01
Tags: tier3, electrical, florida, miami, distribution""",
        "custom_opportunity_score": 6.5,
        "custom_priority_tier": 3
    },
    {
        "lead_name": "Karla Kenney",
        "company_name": "Unknown Company",
        "email_id": None,
        "phone": None,
        "mobile_no": None,
        "designation": "Unknown",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Unknown",
        "country": "United States",
        "notes": f"""Tier 3 Contact (Opportunity Score: 6.0/10)

Company Type: Unknown
Geographic Focus: Unknown

Strategic Value:
Insufficient information.

Partnership Potential:
Requires qualification.

Immediate Opportunities:
Determine business and relevance.

Name only visible on card. Requires follow-up to gather basic information.

Next Action: Qualification outreach
Action Date: 2025-12-01
Tags: tier3, unknown, needs_qualification""",
        "custom_opportunity_score": 6.0,
        "custom_priority_tier": 3
    },
    {
        "lead_name": "MANA Contact - Nic Herr",
        "company_name": "MANA",
        "email_id": None,
        "phone": None,
        "mobile_no": None,
        "designation": "Unknown",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Unknown",
        "city": "Houston",
        "state": "Texas",
        "country": "United States",
        "notes": f"""Tier 3 Contact (Opportunity Score: 6.5/10)

Company Type: Unknown - Houston area
Geographic Focus: Houston, TX

Contacts: Nic Herr, Alvey Gonzalez

Strategic Value:
Houston location suggests oil & gas relevance.

Partnership Potential:
Requires qualification.

Immediate Opportunities:
Determine business focus.

Houston location = likely oil & gas or industrial. Two contacts visible (Nic Herr, Alvey Gonzalez).
Need qualification call to understand business.

Next Action: Qualification call with Nic Herr
Action Date: 2025-12-01
Tags: tier3, houston, unknown, needs_qualification""",
        "custom_opportunity_score": 6.5,
        "custom_priority_tier": 3
    },
    {
        "lead_name": "Imperative LP Contact",
        "company_name": "Imperative Limited Partners",
        "email_id": None,
        "phone": None,
        "mobile_no": None,
        "designation": "Unknown",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Investment/Finance",
        "country": "United States",
        "notes": f"""Tier 3 Contact (Opportunity Score: 6.0/10)

Company Type: Investment/Private Equity
Geographic Focus: Unknown

Products/Services:
- Investment capital
- Private equity
- Strategic partnerships

Strategic Value:
Potential investment capital or portfolio company access.

Partnership Potential:
Investment or strategic introductions.

Immediate Opportunities:
- Potential investment capital
- Portfolio company introductions
- Strategic partnerships

Investment/PE context. Could provide capital or portfolio company access.
REQUIRES CAREFUL QUALIFICATION and due diligence. Don't share sensitive info prematurely.

Next Action: Careful qualification call
Action Date: 2025-12-01
Tags: tier3, investment, private_equity, needs_qualification, caution""",
        "custom_opportunity_score": 6.0,
        "custom_priority_tier": 3
    },
    {
        "lead_name": "Kamfere Contact",
        "company_name": "Kamfere",
        "email_id": None,
        "phone": None,
        "mobile_no": None,
        "designation": "Unknown",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Unknown",
        "country": "United States",
        "notes": f"""Tier 3 Contact (Opportunity Score: 6.0/10)

Company Type: Unknown - Yellow business card
Geographic Focus: Unknown

Strategic Value:
Insufficient information.

Partnership Potential:
Requires qualification.

Immediate Opportunities:
Determine business and relevance.

Yellow card visible but no clear contact information extracted.
Lower priority for initial outreach. Qualify when convenient.

Next Action: Qualification outreach
Action Date: 2025-12-01
Tags: tier3, unknown, needs_qualification, low_priority""",
        "custom_opportunity_score": 6.0,
        "custom_priority_tier": 3
    }
]


def docker_exec_api(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Make API call via docker exec to ERPNext"""
    try:
        if method == "POST":
            json_data = json.dumps(data) if data else '{}'
            # Escape quotes for shell
            json_escaped = json_data.replace("'", "'\\''")
            curl_cmd = f"curl -s -b /tmp/cookies.txt -c /tmp/cookies.txt -X POST -H 'Content-Type: application/json' -d '{json_escaped}' 'http://frontend:8080{endpoint}'"
        else:
            curl_cmd = f"curl -s -b /tmp/cookies.txt -c /tmp/cookies.txt 'http://frontend:8080{endpoint}'"

        result = subprocess.run(
            ["docker", "exec", "frappe_docker_backend_1", "sh", "-c", curl_cmd],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"error": f"Invalid JSON response: {result.stdout[:200]}"}
        else:
            return {"error": f"Docker exec failed: {result.stderr}"}

    except Exception as e:
        return {"error": str(e)}


def authenticate():
    """Authenticate with ERPNext"""
    print("Authenticating with ERPNext...")
    auth_cmd = f"curl -s -c /tmp/cookies.txt -X POST -H 'Content-Type: application/json' -d '{{\"usr\": \"Administrator\", \"pwd\": \"admin\"}}' 'http://frontend:8080/api/method/login'"

    result = subprocess.run(
        ["docker", "exec", "frappe_docker_backend_1", "sh", "-c", auth_cmd],
        capture_output=True,
        text=True,
        timeout=10
    )

    if result.returncode == 0:
        try:
            response_data = json.loads(result.stdout)
            if "message" in response_data and response_data["message"] == "Logged In":
                print("✓ Successfully authenticated with ERPNext")
                return True
        except json.JSONDecodeError:
            pass

    print(f"✗ Authentication failed: {result.stdout}")
    return False


def create_lead(lead_data: dict) -> bool:
    """Create a single lead in ERPNext"""
    print(f"\nCreating lead: {lead_data['lead_name']} ({lead_data['company_name']})")

    # Prepare ERPNext lead data
    erpnext_lead = {
        "doctype": "Lead",
        "lead_name": lead_data["lead_name"],
        "company_name": lead_data["company_name"],
        "email_id": lead_data.get("email_id"),
        "phone": lead_data.get("phone"),
        "mobile_no": lead_data.get("mobile_no"),
        "designation": lead_data.get("designation"),
        "status": lead_data.get("status", "Lead"),
        "source": lead_data.get("source", "Business Card"),
        "territory": lead_data.get("territory", "United States"),
        "industry": lead_data.get("industry"),
        "address_line1": lead_data.get("address_line1"),
        "city": lead_data.get("city"),
        "state": lead_data.get("state"),
        "country": lead_data.get("country", "United States"),
        "pincode": lead_data.get("pincode"),
        "website": lead_data.get("website"),
        "notes": lead_data.get("notes"),
        "custom_opportunity_score": lead_data.get("custom_opportunity_score"),
        "custom_priority_tier": lead_data.get("custom_priority_tier")
    }

    # Remove None values
    erpnext_lead = {k: v for k, v in erpnext_lead.items() if v is not None}

    result = docker_exec_api("/api/resource/Lead", "POST", erpnext_lead)

    if "data" in result:
        lead_id = result["data"].get("name", "unknown")
        print(f"✓ Lead created successfully! ID: {lead_id}")
        return True
    else:
        error_msg = result.get("error", result.get("exc", "Unknown error"))
        print(f"✗ Error creating lead: {error_msg}")
        return False


def main():
    """Main import function"""
    print("=" * 80)
    print("INSA CRM - Business Card Lead Import")
    print(f"Importing {len(LEADS_DATA)} leads from business card collection")
    print("=" * 80)

    # Authenticate
    if not authenticate():
        print("\n✗ Failed to authenticate with ERPNext. Exiting.")
        return

    # Import leads
    success_count = 0
    failure_count = 0

    for idx, lead_data in enumerate(LEADS_DATA, 1):
        print(f"\n[{idx}/{len(LEADS_DATA)}] ", end="")

        if create_lead(lead_data):
            success_count += 1
        else:
            failure_count += 1

        # Small delay to avoid overwhelming the system
        time.sleep(0.5)

    # Summary
    print("\n" + "=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)
    print(f"Total leads processed: {len(LEADS_DATA)}")
    print(f"Successfully imported: {success_count}")
    print(f"Failed to import: {failure_count}")
    print(f"Success rate: {(success_count/len(LEADS_DATA)*100):.1f}%")
    print("=" * 80)

    # Priority breakdown
    tier1_count = sum(1 for lead in LEADS_DATA if lead.get("custom_priority_tier") == 1)
    tier2_count = sum(1 for lead in LEADS_DATA if lead.get("custom_priority_tier") == 2)
    tier3_count = sum(1 for lead in LEADS_DATA if lead.get("custom_priority_tier") == 3)

    print("\nPRIORITY BREAKDOWN:")
    print(f"Tier 1 (IMMEDIATE): {tier1_count} leads")
    print(f"Tier 2 (HIGH): {tier2_count} leads")
    print(f"Tier 3 (MEDIUM): {tier3_count} leads")

    print("\nNEXT STEPS:")
    print("1. Review imported leads in ERPNext: http://100.100.101.1:9000")
    print("2. Contact Tier 1 leads within 1 week (Nov 4-8, 2025)")
    print("3. Execute sales strategy per priority tier")
    print("4. Track follow-ups and pipeline progression")


if __name__ == "__main__":
    main()
