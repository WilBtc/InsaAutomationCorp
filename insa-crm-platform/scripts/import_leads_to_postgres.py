#!/usr/bin/env python3
"""
Business Card Lead Import Script - PostgreSQL Direct
Imports 24 leads from business card collection into INSA CRM PostgreSQL database
"""

import psycopg2
from datetime import datetime
import hashlib

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'insa_crm',
    'user': 'insa_crm_user',
    'password': '[REDACTED]'
}

# Lead data from business card collection
LEADS_DATA = [
    {
        "lead_name": "Richard Hoydell",
        "company_name": "Accel Compression, Inc.",
        "email": None,
        "phone": "(432) 563-1376",
        "mobile": None,
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
        "notes": """TOP PRIORITY - Tier 1 Contact (Opportunity Score: 9.5/10)

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
        "opportunity_score": 9.5,
        "priority_tier": 1
    },
    {
        "lead_name": "Mike Van Tyn",
        "company_name": "Titan Industries / Titan Solutions",
        "email": None,
        "phone": None,
        "mobile": None,
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
        "notes": """TOP PRIORITY - Tier 1 Contact (Opportunity Score: 9.0/10)

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
        "opportunity_score": 9.0,
        "priority_tier": 1
    },
    {
        "lead_name": "Nathan Oakes",
        "company_name": "Crume Sales, Inc.",
        "email": None,
        "phone": None,
        "mobile": None,
        "designation": "Sales Representative",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Industrial Controls",
        "city": "Odessa",
        "state": "Texas",
        "country": "United States",
        "notes": """TOP PRIORITY - Tier 1 Contact (Opportunity Score: 8.5/10)

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
        "opportunity_score": 8.5,
        "priority_tier": 1
    },
    {
        "lead_name": "Luis Galindo",
        "company_name": "UP&S Inc. (United Pump & Supply)",
        "email": "luis@up-s.com",
        "phone": "(432) 332-9753",
        "mobile": None,
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
        "notes": """EXECUTIVE PRIORITY - Tier 1 Contact (Opportunity Score: 9.0/10)

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
        "opportunity_score": 9.0,
        "priority_tier": 1
    },
    {
        "lead_name": "Haiden Hayward",
        "company_name": "Imperative Chemical Partners",
        "email": "Haiden.Hayward@imperativechemicals.com",
        "phone": "(432) 556-8036",
        "mobile": "(877) 523-3147",
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
        "notes": """TOP PRIORITY - Tier 1 Contact (Opportunity Score: 9.0/10)

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
        "opportunity_score": 9.0,
        "priority_tier": 1
    },
    {
        "lead_name": "Mike Von Ruff",
        "company_name": "Titan Pump Manufacturing, Inc.",
        "email": "mvonruff@titanpumpsinc.com",
        "phone": "(281) 817-5611",
        "mobile": "(512) 508-5800",
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
        "notes": """TOP PRIORITY - Tier 1 Contact (Opportunity Score: 9.0/10)

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
        "opportunity_score": 9.0,
        "priority_tier": 1
    },
    {
        "lead_name": "Thomas P. Geoca",
        "company_name": "South Coast Hydraulics",
        "email": "tomgeoca@schydraulics.com",
        "phone": "(713) 895-7814",
        "mobile": "(832) 891-2722",
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
        "notes": """EXECUTIVE PRIORITY - Tier 1 Contact (Opportunity Score: 8.5/10)

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
        "opportunity_score": 8.5,
        "priority_tier": 1
    },
    {
        "lead_name": "Haeng J. Son",
        "company_name": "SPower Electronics",
        "email": None,
        "phone": None,
        "mobile": None,
        "designation": "Regional Representative",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Power Electronics",
        "city": "Florida",
        "state": "Florida",
        "country": "United States",
        "website": "www.spowerstech.com",
        "notes": """Tier 2 Contact (Opportunity Score: 8.5/10)

Company Type: Power Electronics - UPS Systems
Geographic Focus: North America (Italy-based parent)
Founded: 1987

Products/Services:
- UPS systems (industrial grade)
- Power protection for harsh environments
- Data center power solutions
- Telecommunications power

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

Next Action: Discovery call
Action Date: 2025-11-13
Tags: tier2, power_systems, florida, critical_infrastructure, nerc_cip""",
        "opportunity_score": 8.5,
        "priority_tier": 2
    },
    {
        "lead_name": "Carlos A. Chavez",
        "company_name": "WJM Pumps",
        "email": None,
        "phone": None,
        "mobile": None,
        "designation": "Sales Manager",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Industrial Equipment",
        "state": "Florida",
        "country": "United States",
        "notes": """Tier 2 Contact (Opportunity Score: 8.0/10)

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

Next Action: Territory qualification call
Action Date: 2025-11-13
Tags: tier2, pumps, florida, water_sector, municipal""",
        "opportunity_score": 8.0,
        "priority_tier": 2
    },
    {
        "lead_name": "Hong T. Sun",
        "company_name": "mPower Electronics",
        "email": "htsun@mpowerinc.com",
        "phone": "(408) 878-5597",
        "mobile": None,
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
        "notes": """EXECUTIVE - Tier 2 Contact (Opportunity Score: 7.5/10)

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

Next Action: Executive outreach
Action Date: 2025-11-13
Tags: tier2, executive, power_electronics, sensors, california, texas""",
        "opportunity_score": 7.5,
        "priority_tier": 2
    },
    {
        "lead_name": "Luis Galindo (IKA Works)",
        "company_name": "IKA Works",
        "email": None,
        "phone": None,
        "mobile": None,
        "designation": "Sales Representative",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Process Equipment",
        "website": "www.ika.com",
        "country": "United States",
        "notes": """Tier 2 Contact (Opportunity Score: 7.5/10)

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

Next Action: Discovery call
Action Date: 2025-11-20
Tags: tier2, process_equipment, pharmaceutical, battery, gmp_compliance""",
        "opportunity_score": 7.5,
        "priority_tier": 2
    },
    {
        "lead_name": "Meghan Crawford",
        "company_name": "Hawkeye Industries Inc.",
        "email": "meghan.crawford@hawkeye.com",
        "phone": "(825) 533-3447",
        "mobile": None,
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
        "notes": """Tier 2 Contact (Opportunity Score: 7.5/10)

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

Next Action: Qualification call
Action Date: 2025-11-20
Tags: tier2, canada, distribution, industrial, international""",
        "opportunity_score": 7.5,
        "priority_tier": 2
    },
    {
        "lead_name": "Roy Murillo",
        "company_name": "UP&S (United Pump & Supply) - Carlsbad",
        "email": "rmurillo@up-s.com",
        "phone": "(575) 748-5501",
        "mobile": None,
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
        "notes": """Tier 2 Contact (Opportunity Score: 7.0/10)

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

Third UP&S contact - operations manager for Carlsbad.

Next Action: Discovery call
Action Date: 2025-11-20
Tags: tier2, pumps, new_mexico, mining, permian_basin""",
        "opportunity_score": 7.0,
        "priority_tier": 2
    },
    {
        "lead_name": "Lee Ybarra",
        "company_name": "BPI (Bertrem Products, Inc.)",
        "email": "lybarra@bertrem.com",
        "phone": "(432) 559-6555",
        "mobile": None,
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
        "notes": """Tier 2 Contact (Opportunity Score: 7.0/10)

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

Next Action: Qualification call
Action Date: 2025-11-20
Tags: tier2, process_control, texas, odessa, automation""",
        "opportunity_score": 7.0,
        "priority_tier": 2
    },
    {
        "lead_name": "Bynum Vincent",
        "company_name": "IMC (Instrument Maintenance Center), Inc.",
        "email": "b.vincent@imco1.bz",
        "phone": "(432) 687-4900",
        "mobile": "(432) 634-9644",
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
        "notes": """Tier 2 Contact (Opportunity Score: 7.5/10)

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

Next Action: Discovery call
Action Date: 2025-11-20
Tags: tier2, instrumentation, texas, midland, field_service""",
        "opportunity_score": 7.5,
        "priority_tier": 2
    },
    {
        "lead_name": "WIES Contact",
        "company_name": "WIES (Wholesale Industrial Electric Supply)",
        "email": None,
        "phone": None,
        "mobile": None,
        "designation": "Unknown",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Electrical Distribution",
        "city": "Miami",
        "state": "Florida",
        "country": "United States",
        "notes": """Tier 3 Contact (Opportunity Score: 6.5/10)

Company Type: Electrical Distribution
Geographic Focus: South Florida

Products/Services:
- Electrical equipment
- Automation products
- Industrial controls

Strategic Value:
Local Miami distributor, access to industrial customer base.

Partnership Potential:
Distribution channel, local market referrals.

Immediate Opportunities:
- Control panel security
- Automation cybersecurity referrals
- Local industrial clients

No specific contact visible on card. Local Miami presence = convenient for INSA.

Next Action: Identify contact, qualification call
Action Date: 2025-12-01
Tags: tier3, electrical, florida, miami, distribution""",
        "opportunity_score": 6.5,
        "priority_tier": 3
    },
    {
        "lead_name": "Karla Kenney",
        "company_name": "Unknown Company",
        "email": None,
        "phone": None,
        "mobile": None,
        "designation": "Unknown",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Unknown",
        "country": "United States",
        "notes": """Tier 3 Contact (Opportunity Score: 6.0/10)

Company Type: Unknown
Strategic Value: Insufficient information.

Partnership Potential:
Requires qualification.

Immediate Opportunities:
Determine business and relevance.

Name only visible on card. Requires follow-up to gather basic information.

Next Action: Qualification outreach
Action Date: 2025-12-01
Tags: tier3, unknown, needs_qualification""",
        "opportunity_score": 6.0,
        "priority_tier": 3
    },
    {
        "lead_name": "MANA Contact - Nic Herr",
        "company_name": "MANA",
        "email": None,
        "phone": None,
        "mobile": None,
        "designation": "Unknown",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Unknown",
        "city": "Houston",
        "state": "Texas",
        "country": "United States",
        "notes": """Tier 3 Contact (Opportunity Score: 6.5/10)

Company Type: Unknown - Houston area
Geographic Focus: Houston, TX

Contacts: Nic Herr, Alvey Gonzalez

Strategic Value:
Houston location suggests oil & gas relevance.

Partnership Potential:
Requires qualification.

Houston location = likely oil & gas or industrial. Two contacts visible.

Next Action: Qualification call with Nic Herr
Action Date: 2025-12-01
Tags: tier3, houston, unknown, needs_qualification""",
        "opportunity_score": 6.5,
        "priority_tier": 3
    },
    {
        "lead_name": "Imperative LP Contact",
        "company_name": "Imperative Limited Partners",
        "email": None,
        "phone": None,
        "mobile": None,
        "designation": "Unknown",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Investment/Finance",
        "country": "United States",
        "notes": """Tier 3 Contact (Opportunity Score: 6.0/10)

Company Type: Investment/Private Equity

Products/Services:
- Investment capital
- Private equity
- Strategic partnerships

Strategic Value:
Potential investment capital or portfolio company access.

Partnership Potential:
Investment or strategic introductions.

Investment/PE context. Could provide capital or portfolio company access.
REQUIRES CAREFUL QUALIFICATION and due diligence.

Next Action: Careful qualification call
Action Date: 2025-12-01
Tags: tier3, investment, private_equity, needs_qualification, caution""",
        "opportunity_score": 6.0,
        "priority_tier": 3
    },
    {
        "lead_name": "Kamfere Contact",
        "company_name": "Kamfere",
        "email": None,
        "phone": None,
        "mobile": None,
        "designation": "Unknown",
        "status": "Lead",
        "source": "Business Card",
        "territory": "United States",
        "industry": "Unknown",
        "country": "United States",
        "notes": """Tier 3 Contact (Opportunity Score: 6.0/10)

Company Type: Unknown

Strategic Value:
Insufficient information.

Partnership Potential:
Requires qualification.

Yellow card visible but no clear contact information extracted.

Next Action: Qualification outreach
Action Date: 2025-12-01
Tags: tier3, unknown, needs_qualification, low_priority""",
        "opportunity_score": 6.0,
        "priority_tier": 3
    }
]


def generate_lead_id(lead_name, company_name):
    """Generate unique lead ID from name and company"""
    raw_id = f"{lead_name}_{company_name}".lower().replace(" ", "_")
    # Hash it for uniqueness and reasonable length
    hash_suffix = hashlib.md5(raw_id.encode()).hexdigest()[:8]
    return f"LEAD-{hash_suffix}"


def import_leads():
    """Import all leads into PostgreSQL"""
    print("=" * 80)
    print("INSA CRM - Business Card Lead Import (PostgreSQL Direct)")
    print(f"Importing {len(LEADS_DATA)} leads")
    print("=" * 80)

    try:
        # Connect to database
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        success_count = 0
        failure_count = 0

        for idx, lead in enumerate(LEADS_DATA, 1):
            try:
                # Generate unique lead ID
                lead_id = generate_lead_id(lead["lead_name"], lead["company_name"])

                print(f"\n[{idx}/{len(LEADS_DATA)}] Importing: {lead['lead_name']} ({lead['company_name']})")

                # Insert lead
                cursor.execute("""
                    INSERT INTO leads (
                        lead_id, lead_name, company_name, email, phone, mobile,
                        designation, status, source, territory, industry,
                        address_line1, city, state, country, pincode, website,
                        notes, opportunity_score, priority_tier
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (lead_id) DO UPDATE SET
                        lead_name = EXCLUDED.lead_name,
                        company_name = EXCLUDED.company_name,
                        email = EXCLUDED.email,
                        phone = EXCLUDED.phone,
                        mobile = EXCLUDED.mobile,
                        designation = EXCLUDED.designation,
                        status = EXCLUDED.status,
                        source = EXCLUDED.source,
                        territory = EXCLUDED.territory,
                        industry = EXCLUDED.industry,
                        address_line1 = EXCLUDED.address_line1,
                        city = EXCLUDED.city,
                        state = EXCLUDED.state,
                        country = EXCLUDED.country,
                        pincode = EXCLUDED.pincode,
                        website = EXCLUDED.website,
                        notes = EXCLUDED.notes,
                        opportunity_score = EXCLUDED.opportunity_score,
                        priority_tier = EXCLUDED.priority_tier,
                        updated_at = NOW()
                """, (
                    lead_id,
                    lead["lead_name"],
                    lead["company_name"],
                    lead.get("email"),
                    lead.get("phone"),
                    lead.get("mobile"),
                    lead.get("designation"),
                    lead.get("status", "Lead"),
                    lead.get("source", "Business Card"),
                    lead.get("territory", "United States"),
                    lead.get("industry"),
                    lead.get("address_line1"),
                    lead.get("city"),
                    lead.get("state"),
                    lead.get("country", "United States"),
                    lead.get("pincode"),
                    lead.get("website"),
                    lead.get("notes"),
                    lead.get("opportunity_score"),
                    lead.get("priority_tier")
                ))

                print(f"  ✓ Lead imported successfully! ID: {lead_id}")
                success_count += 1

            except Exception as e:
                print(f"  ✗ Error importing lead: {str(e)}")
                failure_count += 1

        # Commit all changes
        conn.commit()

        # Get summary stats
        cursor.execute("SELECT COUNT(*) FROM leads")
        total_leads = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM leads WHERE priority_tier = 1")
        tier1_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM leads WHERE priority_tier = 2")
        tier2_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM leads WHERE priority_tier = 3")
        tier3_count = cursor.fetchone()[0]

        # Close connection
        cursor.close()
        conn.close()

        # Print summary
        print("\n" + "=" * 80)
        print("IMPORT SUMMARY")
        print("=" * 80)
        print(f"Total leads processed: {len(LEADS_DATA)}")
        print(f"Successfully imported: {success_count}")
        print(f"Failed to import: {failure_count}")
        print(f"Success rate: {(success_count/len(LEADS_DATA)*100):.1f}%")
        print("=" * 80)

        print("\nDATABASE STATS:")
        print(f"Total leads in database: {total_leads}")
        print(f"Tier 1 (IMMEDIATE): {tier1_count} leads")
        print(f"Tier 2 (HIGH): {tier2_count} leads")
        print(f"Tier 3 (MEDIUM): {tier3_count} leads")

        print("\nNEXT STEPS:")
        print("1. View leads in INSA CRM: http://100.100.101.1:8003")
        print("2. Contact Tier 1 leads within 1 week (Nov 4-8, 2025)")
        print("3. Execute sales strategy per priority tier")
        print("4. Track follow-ups and pipeline progression")

        print("\nQUERY EXAMPLES:")
        print("  # View all leads:")
        print("  PGPASSWORD='[REDACTED]' psql -h localhost -U insa_crm_user -d insa_crm -c 'SELECT lead_id, lead_name, company_name, opportunity_score, priority_tier FROM leads ORDER BY opportunity_score DESC;'")
        print("\n  # View Tier 1 leads only:")
        print("  PGPASSWORD='[REDACTED]' psql -h localhost -U insa_crm_user -d insa_crm -c 'SELECT lead_name, company_name, phone, email FROM leads WHERE priority_tier = 1 ORDER BY opportunity_score DESC;'")

    except Exception as e:
        print(f"\n✗ Database error: {str(e)}")
        return False

    return True


if __name__ == "__main__":
    import_leads()
