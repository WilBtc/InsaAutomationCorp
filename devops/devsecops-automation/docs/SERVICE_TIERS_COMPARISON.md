# Service Tiers Comparison - Insa Automation Corp SecureOps Platform
**Version**: 1.0
**Date**: 2025-10-11
**Document Type**: Sales & Technical Reference

---

## Executive Summary

Insa Automation Corp offers **two distinct service tiers** for industrial cybersecurity monitoring and vulnerability management:

1. **Self-Service SaaS Tiers** ($99-$2,499/month) - For customers with internal IT/OT teams who can deploy agents and manage findings
2. **Managed SOC 24/7 Service** ($5,000-$50,000/month) - For customers requiring white-glove service with on-site installation and 24/7 expert monitoring

This document provides a comprehensive comparison to help prospects select the appropriate service tier.

---

## Service Tier Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    INSA AUTOMATION CORP SECURITY SERVICES                │
└─────────────────────────────────────────────────────────────────────────┘

        SELF-SERVICE SaaS                          MANAGED SOC 24/7
┌───────────────────────────────┐         ┌──────────────────────────────┐
│                               │         │                              │
│  🔧 You Install & Manage      │         │  🛡️  We Install & Monitor   │
│  💰 $99 - $2,499/month        │         │  💰 $5K - $50K/month         │
│  👤 Your team triages         │         │  👤 Our experts manage       │
│  📊 AI-assisted platform      │         │  📊 Full SOC operations      │
│                               │         │                              │
│  ┌─────────────────────────┐ │         │  ┌────────────────────────┐ │
│  │ STARTER    $99/mo       │ │         │  │ PROFESSIONAL  $5K/mo   │ │
│  │ • 10 assets             │ │         │  │ • Single site          │ │
│  │ • Basic scanning        │ │         │  │ • On-site install      │ │
│  │ • Email support         │ │         │  │ • 8x5 monitoring       │ │
│  └─────────────────────────┘ │         │  └────────────────────────┘ │
│                               │         │                              │
│  ┌─────────────────────────┐ │         │  ┌────────────────────────┐ │
│  │ BUSINESS   $499/mo      │ │         │  │ ENTERPRISE    $15K/mo  │ │
│  │ • 100 assets            │ │         │  │ • Multi-site           │ │
│  │ • Advanced scanning     │ │         │  │ • 24x7 monitoring      │ │
│  │ • Chat support          │ │         │  │ • Incident response    │ │
│  └─────────────────────────┘ │         │  └────────────────────────┘ │
│                               │         │                              │
│  ┌─────────────────────────┐ │         │  ┌────────────────────────┐ │
│  │ ENTERPRISE $2,499/mo    │ │         │  │ CRITICAL      $50K/mo  │ │
│  │ • Unlimited assets      │ │         │  │ • Critical infra       │ │
│  │ • API access            │ │         │  │ • Dedicated SOC team   │ │
│  │ • SSO/SAML              │ │         │  │ • Red team exercises   │ │
│  └─────────────────────────┘ │         │  └────────────────────────┘ │
│                               │         │                              │
└───────────────────────────────┘         └──────────────────────────────┘
```

---

## Self-Service SaaS Tiers (Do-It-Yourself)

### Overview

**Who is this for?**
- Companies with IT/OT staff (1-5 people)
- Organizations comfortable installing agents and managing findings
- Customers seeking cost-effective security monitoring
- Fast-growing companies needing scalability

**What you get:**
- Cloud-based vulnerability management platform
- AI-powered triage assistance (reduces manual work by 80%)
- Web dashboard with real-time findings
- Email/webhook notifications
- Comprehensive reporting
- API access (Business tier and above)

**What you do:**
- Deploy Wazuh/Trivy agents on your servers
- Review and remediate findings
- Configure scanning schedules
- Manage user accounts

---

### Tier 1: STARTER - $99/month

**Ideal for:** Small businesses, startups, single-site operations

#### What's Included

**Assets & Scanning:**
- Up to **10 monitored assets** (servers, devices, containers)
- **10 vulnerability scans per month**
  - Trivy container/image scanning
  - Nmap network discovery
  - Basic web application scanning (Nikto)
- Automated daily scanning schedule
- EPSS-based risk prioritization

**Features:**
- Cloud dashboard (single user)
- AI-assisted triage (confidence scoring)
- Finding deduplication
- Basic compliance reports (CIS, NIST CSF)
- 100 API calls/hour
- 10 GB data storage (scan results, reports)

**Support:**
- Email support (72-hour response)
- Knowledge base access
- Video tutorials
- Community forum

**Use Case Examples:**
- Software development shop with 5 servers + 3 containers
- E-commerce website (single site)
- Small manufacturing facility (office IT only)

**Technical Limits:**
- 1 user account
- 100 API requests/hour
- Basic scans only (no authenticated scans)
- 30-day data retention

---

### Tier 2: BUSINESS - $499/month

**Ideal for:** Mid-sized companies, multi-team organizations, growing manufacturers

#### What's Included

**Assets & Scanning:**
- Up to **100 monitored assets**
- **50 vulnerability scans per month**
  - All Starter scanners plus:
  - OWASP ZAP active web scanning
  - Authenticated scans (SSH, SMB)
  - Custom scan policies
- Continuous monitoring option (agent-based)
- Advanced EPSS + exploit availability checks

**Features:**
- Cloud dashboard (up to 10 users)
- Role-Based Access Control (RBAC):
  - Admin, Analyst, Read-Only roles
- AI-assisted bulk triage (process 100+ findings at once)
- Advanced reporting:
  - Executive dashboards
  - Trend analysis
  - Compliance reports (PCI-DSS, HIPAA, IEC 62443)
- Webhook integrations (Slack, Teams, PagerDuty)
- 1,000 API calls/hour
- 50 GB data storage
- 90-day data retention

**Support:**
- Live chat support (24-hour response)
- Email support (24-hour response)
- Monthly check-in calls
- Dedicated customer success manager

**Use Case Examples:**
- Manufacturing facility with 30 servers + 50 PLCs/SCADA devices + 20 containers
- Multi-location retail chain (3-5 stores)
- Healthcare clinic with HIPAA compliance needs
- Utility company with OT/ICS environment

**Technical Limits:**
- 10 user accounts
- 1,000 API requests/hour
- Basic integration options

---

### Tier 3: ENTERPRISE - $2,499/month

**Ideal for:** Large enterprises, critical infrastructure, complex OT environments

#### What's Included

**Assets & Scanning:**
- **Unlimited monitored assets**
- **Unlimited vulnerability scans**
  - All Business scanners plus:
  - Custom scanner integrations
  - Advanced OT/ICS protocol scanning (Modbus, DNP3, ENIP)
  - Compliance scanning (NERC CIP, IEC 62443)
- Continuous real-time monitoring
- Advanced threat intelligence (MISP integration)
- Zero-day vulnerability alerting

**Features:**
- Cloud dashboard (unlimited users)
- Advanced RBAC with custom roles
- Multi-tenant support (divisions, subsidiaries)
- White-label branding option
- AI-assisted triage with learning system
- Premium reporting:
  - Board-level executive reports
  - Risk scoring & forecasting
  - Compliance audit reports
  - Custom report builder
- Full API access (10,000 calls/hour)
- SSO/SAML integration (Okta, Azure AD, Google)
- Unlimited data storage
- 7-year data retention (compliance)

**Support:**
- Priority phone support (4-hour response)
- 24/7 email support (4-hour response)
- Dedicated Technical Account Manager (TAM)
- Quarterly business reviews
- Custom training sessions
- Early access to new features

**Use Case Examples:**
- Multi-site manufacturing operations (10+ facilities)
- Electric utility with NERC CIP compliance requirements
- Water/wastewater treatment plant
- Oil & gas pipeline operations
- Large hospital system with 500+ medical devices

**Technical Limits:**
- Unlimited users
- 10,000 API requests/hour (custom limits available)
- Advanced integrations (SIEM, ticketing, CMDB)
- Custom SLA available

---

## Self-Service SaaS Feature Matrix

| Feature | STARTER<br>$99/mo | BUSINESS<br>$499/mo | ENTERPRISE<br>$2,499/mo |
|---------|-------------------|---------------------|-------------------------|
| **Assets** |
| Monitored Assets | 10 | 100 | Unlimited |
| Vulnerability Scans/Month | 10 | 50 | Unlimited |
| Continuous Monitoring | ❌ | ✅ | ✅ |
| **Scanning Tools** |
| Trivy (containers) | ✅ | ✅ | ✅ |
| Nmap (network) | ✅ | ✅ | ✅ |
| Nikto (web servers) | ✅ | ✅ | ✅ |
| OWASP ZAP (web apps) | ❌ | ✅ | ✅ |
| Authenticated Scans | ❌ | ✅ | ✅ |
| Custom Scanners | ❌ | ❌ | ✅ |
| OT/ICS Protocol Scanning | ❌ | Basic | Advanced |
| **Features** |
| Users | 1 | 10 | Unlimited |
| RBAC | ❌ | ✅ | ✅ Advanced |
| AI Triage | Basic | Advanced | Premium + Learning |
| Data Retention | 30 days | 90 days | 7 years |
| Storage | 10 GB | 50 GB | Unlimited |
| API Calls/Hour | 100 | 1,000 | 10,000 |
| Webhooks | ❌ | ✅ | ✅ |
| SSO/SAML | ❌ | ❌ | ✅ |
| White-Label Branding | ❌ | ❌ | ✅ |
| **Reporting** |
| Basic Reports | ✅ | ✅ | ✅ |
| Executive Dashboards | ❌ | ✅ | ✅ |
| Trend Analysis | ❌ | ✅ | ✅ |
| Custom Reports | ❌ | ❌ | ✅ |
| Board-Level Reports | ❌ | ❌ | ✅ |
| **Compliance** |
| CIS Controls | ✅ | ✅ | ✅ |
| NIST CSF | ✅ | ✅ | ✅ |
| PCI-DSS | ❌ | ✅ | ✅ |
| HIPAA | ❌ | ✅ | ✅ |
| IEC 62443 | ❌ | ✅ | ✅ |
| NERC CIP | ❌ | ❌ | ✅ |
| **Support** |
| Email Support | 72h | 24h | 4h |
| Chat Support | ❌ | ✅ | ✅ |
| Phone Support | ❌ | ❌ | ✅ Priority |
| TAM | ❌ | ❌ | ✅ Dedicated |
| Training | Videos | Monthly calls | Custom sessions |

---

## Managed SOC 24/7 Service (White-Glove Service)

### Overview

**Who is this for?**
- Companies **without dedicated cybersecurity staff**
- Critical infrastructure operators (utilities, manufacturing)
- Organizations with **compliance requirements** (NERC CIP, IEC 62443)
- Customers requiring **24/7 expert monitoring** and incident response
- High-risk environments (ransomware targets)

**What you get:**
- **On-site installation** by certified technicians
- **24/7 monitoring** by industrial cybersecurity experts
- **Incident response** services (P0/P1 incidents)
- **Quarterly on-site visits** for system health checks
- **Dedicated SOC team** assigned to your account
- **Comprehensive reporting** (weekly + monthly + quarterly)

**What you do:**
- Provide network access during installation
- Approve remediation actions (we recommend, you approve)
- Attend quarterly business reviews

---

### Tier 1: PROFESSIONAL - $5,000/month

**Ideal for:** Single-site operations, small manufacturing facilities, regional utilities

#### What's Included

**Installation & Setup:**
- **On-site installation** (1-2 days)
  - Wazuh agent deployment (up to 25 assets)
  - Network sensor installation (Suricata IDS)
  - Firewall rule review and hardening
  - Baseline security assessment
- Initial vulnerability scan and remediation roadmap
- Staff training (4 hours): "How to work with our SOC"

**Monitoring & Management:**
- **8x5 monitoring** (business hours, M-F)
  - Real-time alert triage by SOC analysts
  - Security event correlation
  - Threat intelligence integration
- **Up to 25 monitored assets**
  - Servers, workstations, ICS/OT devices
- Weekly vulnerability scanning
- Monthly patch management reports
- Quarterly on-site health checks (1 day)

**Incident Response:**
- P1/P2 incident response (4-hour response time)
- Malware containment and remediation
- Forensic analysis (basic)
- Post-incident reports

**Reporting:**
- Weekly summary emails (key metrics)
- Monthly detailed reports (findings, trends, recommendations)
- Quarterly executive presentations (on-site or virtual)

**Support:**
- Direct phone/email to assigned SOC team
- Dedicated account manager
- Emergency hotline (for critical incidents)

**Use Case Examples:**
- Small manufacturing plant (single facility, 20 servers + 5 PLCs)
- Regional water utility (single treatment plant)
- Food processing facility (FDA compliance)
- Small hospital (25 beds)

**Technical Specifications:**
- 25 monitored assets
- 8x5 coverage (40 hours/week)
- 4-hour incident response SLA
- Quarterly on-site visits (1 day)

**Annual Cost:** $60,000/year

---

### Tier 2: ENTERPRISE - $15,000/month

**Ideal for:** Multi-site operations, critical infrastructure, large manufacturers

#### What's Included

**Installation & Setup:**
- **Multi-site on-site installation** (3-5 days per site)
  - Wazuh agent deployment (up to 150 assets)
  - Network sensor installation (Suricata + Zeek)
  - Firewall + IDS/IPS tuning
  - Network segmentation review (Purdue Model)
  - Baseline security assessment per site
- Initial vulnerability scan and prioritized remediation plan
- Staff training (8 hours): "Cybersecurity for OT/ICS teams"

**Monitoring & Management:**
- **24x7 monitoring** (around the clock, every day)
  - Dedicated SOC analysts assigned to your account
  - Real-time alert triage and correlation
  - Advanced threat hunting (weekly)
  - Proactive vulnerability management
- **Up to 150 monitored assets** across multiple sites
  - Servers, workstations, ICS/SCADA, PLCs, HMIs
- Continuous vulnerability scanning
- Monthly patch management coordination
- Monthly on-site health checks (1 day per site)

**Incident Response:**
- **P0/P1 incident response** (1-hour response time)
- Malware containment and eradication
- Advanced forensic analysis
- Threat actor attribution
- Recovery coordination
- Post-incident reports with recommendations

**Compliance Support:**
- IEC 62443 compliance monitoring
- NERC CIP compliance support (if applicable)
- Audit readiness assessments
- Compliance evidence collection
- Audit support (on-site during audits)

**Reporting:**
- Weekly detailed reports (findings, incidents, actions taken)
- Monthly comprehensive reports (trends, metrics, KPIs)
- Quarterly executive presentations (on-site with C-level)
- Annual risk assessment report

**Support:**
- 24/7 emergency hotline
- Direct access to SOC team (phone, email, Slack)
- Dedicated Technical Account Manager
- Quarterly business reviews
- Custom training programs

**Use Case Examples:**
- Manufacturing operations (3-5 facilities, 100 servers + 50 ICS devices)
- Electric utility with multiple substations (NERC CIP compliance)
- Water/wastewater utility (5 treatment plants)
- Mid-sized hospital system (3 hospitals, 200+ medical devices)
- Chemical processing plant (hazardous materials)

**Technical Specifications:**
- 150 monitored assets across multiple sites
- 24x7 coverage (168 hours/week)
- 1-hour P0/P1 incident response SLA
- Monthly on-site visits (1 day per site)
- Dedicated SOC analyst team (3-5 analysts)

**Annual Cost:** $180,000/year

---

### Tier 3: CRITICAL INFRASTRUCTURE - $50,000/month (Custom)

**Ideal for:** Critical infrastructure, large utilities, high-risk facilities, Fortune 500

#### What's Included

**Installation & Setup:**
- **Enterprise-wide deployment** (custom timeline)
  - Wazuh agent deployment (unlimited assets)
  - Advanced network monitoring (Suricata + Zeek + custom sensors)
  - Zero-trust architecture implementation
  - OT network segmentation (full Purdue Model)
  - Red team assessment (initial security validation)
  - Baseline security assessment (comprehensive)
- Prioritized remediation plan with timeline
- Executive staff training (C-level + board)
- OT/ICS staff training (comprehensive)

**Monitoring & Management:**
- **24x7 monitoring** by **dedicated SOC team** (your team only)
  - 3-5 SOC analysts assigned exclusively to your organization
  - Real-time alert triage and correlation
  - Daily threat hunting exercises
  - Proactive vulnerability management
  - Threat intelligence integration (MISP, STIX/TAXII)
- **Unlimited monitored assets** across all sites
  - Enterprise IT + OT/ICS + cloud infrastructure
- Continuous vulnerability scanning
- Patch management coordination (testing + deployment)
- Weekly on-site visits (1 day per week)

**Incident Response:**
- **P0 incident response** (<30 minute response time)
- Advanced threat containment and eradication
- Forensic investigation (deep dive)
- Threat actor attribution and TTPs analysis
- Recovery coordination with your teams
- Legal/law enforcement coordination (if needed)
- Post-incident root cause analysis
- Tabletop exercises (quarterly)

**Compliance & Audit:**
- Full NERC CIP compliance program management
- IEC 62443 compliance program management
- Continuous compliance monitoring
- Audit readiness (year-round)
- Audit support (on-site during audits)
- Compliance evidence management
- Regulatory reporting assistance

**Red Team & Testing:**
- Quarterly penetration testing
- Annual red team exercise
- Social engineering testing
- Physical security testing (optional)
- Purple team exercises (SOC + Red Team collaboration)

**Reporting:**
- Daily summary emails (critical events)
- Weekly detailed reports
- Monthly comprehensive reports with KPIs
- Quarterly executive presentations (on-site with board)
- Annual comprehensive risk assessment
- Custom reports on demand

**Support:**
- 24/7 emergency hotline (direct to SOC supervisor)
- Dedicated Slack/Teams channel
- Direct access to SOC analysts
- Dedicated CISO-level advisor
- Executive Technical Account Manager
- Unlimited training and workshops

**Use Case Examples:**
- Large electric utility (regional/national grid)
- Large water utility (municipal water system)
- Major manufacturing operations (10+ facilities)
- Oil & gas pipeline operations
- Large hospital system (10+ hospitals)
- Data center operations (Fortune 500)

**Technical Specifications:**
- Unlimited monitored assets across all sites
- 24x7 coverage with dedicated team
- 30-minute P0 incident response SLA
- Weekly on-site visits
- Dedicated SOC team (3-5 analysts + supervisor)
- Custom SLA negotiable

**Annual Cost:** $600,000/year (starting price, custom pricing available)

---

## Managed SOC 24/7 Feature Matrix

| Feature | PROFESSIONAL<br>$5K/mo | ENTERPRISE<br>$15K/mo | CRITICAL INFRA<br>$50K/mo |
|---------|------------------------|------------------------|---------------------------|
| **Installation** |
| On-Site Installation | ✅ 1-2 days | ✅ 3-5 days/site | ✅ Custom timeline |
| Monitored Assets | 25 | 150 | Unlimited |
| Sites Covered | Single site | Multi-site | Enterprise-wide |
| Network Segmentation | Basic review | Purdue Model review | Full implementation |
| Red Team Assessment | ❌ | ❌ | ✅ Initial + quarterly |
| **Monitoring** |
| Coverage Hours | 8x5 (40h/week) | 24x7 (168h/week) | 24x7 (168h/week) |
| SOC Team | Shared pool | Assigned team | Dedicated team (3-5) |
| Threat Hunting | ❌ | Weekly | Daily |
| Vulnerability Scanning | Weekly | Continuous | Continuous + advanced |
| **Incident Response** |
| Response Time | 4 hours | 1 hour | 30 minutes |
| Incident Types | P1/P2 | P0/P1 | All priorities |
| Forensics | Basic | Advanced | Deep dive |
| Threat Attribution | ❌ | ✅ | ✅ Advanced |
| Recovery Support | ✅ | ✅ Advanced | ✅ Full coordination |
| **Compliance** |
| IEC 62443 Support | ❌ | ✅ Monitoring | ✅ Full program |
| NERC CIP Support | ❌ | ✅ Support | ✅ Full program |
| Audit Support | ❌ | ✅ On-site | ✅ Year-round |
| Compliance Reports | ❌ | ✅ | ✅ Advanced |
| **On-Site Visits** |
| Health Checks | Quarterly (1 day) | Monthly (1 day/site) | Weekly (1 day/week) |
| Business Reviews | Quarterly | Quarterly | Quarterly + monthly |
| Training | 4 hours initial | 8 hours initial | Unlimited |
| **Reporting** |
| Summary Emails | Weekly | Weekly | Daily |
| Detailed Reports | Monthly | Monthly | Monthly + weekly |
| Executive Presentations | Quarterly | Quarterly | Quarterly + board |
| Annual Risk Assessment | ❌ | ✅ | ✅ Comprehensive |
| **Support** |
| Emergency Hotline | ✅ | ✅ 24/7 | ✅ 24/7 direct |
| Account Manager | ✅ | ✅ Dedicated TAM | ✅ Executive TAM |
| CISO Advisor | ❌ | ❌ | ✅ Dedicated |

---

## Self-Service vs Managed SOC Comparison

| Dimension | Self-Service SaaS | Managed SOC 24/7 |
|-----------|-------------------|------------------|
| **Installation** |
| Who installs? | Customer installs agents | INSA installs on-site |
| Installation time | 1-3 hours (DIY) | 1-5 days (professional) |
| Network changes required? | Minimal (agent outbound) | Requires coordination |
| Training provided? | Video tutorials | On-site training (4-8h) |
| **Monitoring** |
| Who monitors alerts? | Customer's IT team | INSA SOC analysts 24/7 |
| Alert triage | Customer (AI-assisted) | INSA SOC team |
| Threat hunting | None (self-service) | Weekly/daily (Managed) |
| Incident response | Customer handles | INSA handles + coordinates |
| **Staffing Required** |
| Customer staff needed | 1-3 IT/security staff | No dedicated staff needed |
| Cybersecurity expertise | Basic to intermediate | None (INSA provides) |
| On-call requirements | Customer team on-call | INSA team on-call |
| **Reporting** |
| Who generates reports? | Platform auto-generates | INSA analysts + platform |
| Report customization | Limited templates | Custom reports available |
| Executive presentations | None | Quarterly on-site |
| **Compliance** |
| Compliance reports | Automated templates | Custom compliance program |
| Audit support | Platform data export | On-site audit assistance |
| Evidence collection | Customer responsibility | INSA maintains evidence |
| **Cost** |
| Base cost | $99 - $2,499/month | $5,000 - $50,000/month |
| Hidden costs | Staff time (20-40h/week) | None (all-inclusive) |
| Total cost (25 assets) | ~$5K/month (staff + SaaS) | $5K/month (all-inclusive) |
| **Best For** |
| Organization type | Have IT/security staff | No security staff |
| Risk profile | Low to medium risk | Medium to high risk |
| Compliance needs | Basic compliance | NERC CIP, IEC 62443 |
| IT maturity | Moderate to high | Any (INSA fills gaps) |

---

## Customer Profile & Tier Selection Guide

### Who Should Choose Self-Service SaaS?

**✅ Good Fit If:**
- You have 1-5 IT/security staff members
- Your team has basic cybersecurity knowledge
- You can dedicate 10-20 hours/week to security monitoring
- Your risk profile is low to medium
- You need cost-effective monitoring
- You have compliance needs but not NERC CIP/IEC 62443

**❌ Not a Good Fit If:**
- You have no dedicated IT staff
- Your risk profile is high (critical infrastructure)
- You require 24/7 monitoring coverage
- You have regulatory compliance requirements (NERC CIP)
- You cannot dedicate staff time to security monitoring

**Industries Best Suited:**
- Software/SaaS companies
- E-commerce
- Professional services
- Small manufacturing (non-critical)
- Healthcare clinics (HIPAA)
- Retail

---

### Who Should Choose Managed SOC 24/7?

**✅ Good Fit If:**
- You have no dedicated cybersecurity staff
- You are critical infrastructure (utilities, manufacturing)
- You require regulatory compliance (NERC CIP, IEC 62443)
- You need 24/7 expert monitoring
- You are a high-risk target (ransomware, state actors)
- You need incident response capabilities

**❌ Not a Good Fit If:**
- You have a mature cybersecurity team (5+ staff)
- You already have a SOC
- You only need vulnerability scanning (not monitoring)
- Your budget is limited (<$60K/year for security)

**Industries Best Suited:**
- Electric utilities (NERC CIP)
- Water/wastewater utilities
- Manufacturing (critical operations)
- Oil & gas
- Chemical processing
- Healthcare systems (large)
- Transportation

---

## Tier Selection Decision Tree

```
START: How many dedicated IT/security staff do you have?

┌──────────────────────────────────────────────────┐
│ 0-1 staff (no dedicated security)               │
│                                                  │
│ → Are you critical infrastructure or high-risk? │
│    ✅ YES → Managed SOC 24/7                     │
│    ❌ NO  → Can you dedicate 10h/week?          │
│              ✅ YES → Self-Service STARTER       │
│              ❌ NO  → Managed PROFESSIONAL       │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│ 2-5 staff (some security knowledge)             │
│                                                  │
│ → Do you need 24/7 monitoring?                  │
│    ✅ YES → Managed SOC ENTERPRISE               │
│    ❌ NO  → How many assets?                     │
│              < 100 → Self-Service BUSINESS       │
│              > 100 → Self-Service ENTERPRISE     │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│ 5+ staff (mature security team)                 │
│                                                  │
│ → Do you already have a SOC?                    │
│    ✅ YES → Self-Service ENTERPRISE (augment)    │
│    ❌ NO  → Do you have regulatory compliance?  │
│              ✅ YES (NERC CIP) → Managed SOC     │
│              ❌ NO → Self-Service ENTERPRISE     │
└──────────────────────────────────────────────────┘
```

---

## Pricing Deep Dive

### Self-Service SaaS Pricing Factors

**What affects your price?**

1. **Number of assets monitored**
   - Starter: 10 assets
   - Business: 100 assets
   - Enterprise: Unlimited (fair use)

2. **Scan frequency**
   - Starter: 10 scans/month
   - Business: 50 scans/month
   - Enterprise: Unlimited

3. **Users**
   - Starter: 1 user
   - Business: 10 users
   - Enterprise: Unlimited

4. **Data retention**
   - Starter: 30 days
   - Business: 90 days
   - Enterprise: 7 years

5. **Support level**
   - Starter: Email (72h)
   - Business: Chat (24h)
   - Enterprise: Phone (4h)

**Overage charges:**
- Assets over limit: $5/asset/month
- Extra scans: $10/scan
- Extra users: $20/user/month

**Annual discount:** Pay annually, save 20%

---

### Managed SOC 24/7 Pricing Factors

**What affects your price?**

1. **Number of sites**
   - Professional: Single site
   - Enterprise: 2-5 sites
   - Critical Infrastructure: Unlimited

2. **Number of monitored assets**
   - Professional: Up to 25 assets
   - Enterprise: Up to 150 assets
   - Critical Infrastructure: Unlimited

3. **Coverage hours**
   - Professional: 8x5 (40 hours/week)
   - Enterprise: 24x7 (168 hours/week)
   - Critical Infrastructure: 24x7 with dedicated team

4. **Complexity of environment**
   - IT-only: Base price
   - IT + OT/ICS: +30%
   - Critical infrastructure (high-risk): +50%

5. **Compliance requirements**
   - No compliance: Base price
   - IEC 62443: +20%
   - NERC CIP: +40% (extensive reporting)

6. **On-site visit frequency**
   - Professional: Quarterly
   - Enterprise: Monthly
   - Critical Infrastructure: Weekly

**Example Pricing Calculation (Enterprise Tier):**
```
Base price (150 assets, 24x7):        $15,000/month
IT + OT environment (+30%):            $4,500/month
NERC CIP compliance (+40%):            $6,000/month
─────────────────────────────────────
Total:                                $25,500/month

Annual contract discount (-10%):      -$2,550/month
─────────────────────────────────────
Final price:                          $22,950/month
                                      ($275,400/year)
```

---

## Add-On Services (Both Tiers)

### Optional Add-Ons (Self-Service SaaS)

1. **Professional Services**
   - Initial security assessment: $5,000 (one-time)
   - Remediation planning: $2,500
   - Compliance readiness assessment: $10,000

2. **Custom Integrations**
   - SIEM integration (Splunk, QRadar): $5,000 (one-time) + $500/month
   - Ticketing integration (ServiceNow, Jira): $2,500 (one-time)
   - Custom scanner integration: $10,000 (one-time)

3. **Training**
   - On-site training (1 day): $2,500
   - Virtual training workshops: $1,000/session

4. **Managed Detection and Response (MDR)**
   - Upgrade to managed monitoring: $2,000/month (adds 8x5 SOC monitoring)

---

### Optional Add-Ons (Managed SOC 24/7)

1. **Red Team Services**
   - Penetration testing: $15,000/test
   - Red team exercise (full): $50,000
   - Social engineering testing: $10,000

2. **Additional Sites**
   - Professional: +$2,000/month per site
   - Enterprise: +$5,000/month per site
   - Critical Infrastructure: Custom pricing

3. **Incident Retainer**
   - Emergency incident response hours: $10,000 (10 hours, 1-year validity)
   - Forensic investigation retainer: $25,000 (20 hours)

4. **Compliance Program Management**
   - ISO 27001 certification support: $50,000 (one-time)
   - SOC 2 Type II certification support: $75,000 (one-time)

---

## Migration Path Between Tiers

### Self-Service Tier Upgrades

**Starter → Business:**
- Automatic upgrade when you exceed 10 assets or 10 scans/month
- Pro-rated pricing for current month
- All data migrates automatically

**Business → Enterprise:**
- Contact account manager for custom onboarding
- Includes migration planning and SSO setup
- 30-day parallel access for testing

**Self-Service → Managed SOC:**
- Requires 60-day notice (for SOC team staffing)
- On-site assessment visit (included)
- Migration plan and timeline provided
- Data migrates to managed platform

---

### Managed SOC Tier Changes

**Professional → Enterprise:**
- Requires 30-day notice (for 24x7 staffing)
- Additional on-site installation visit
- No data migration needed

**Enterprise → Critical Infrastructure:**
- Requires 90-day notice (for dedicated team)
- Comprehensive re-assessment
- Custom SLA negotiation

**Managed SOC → Self-Service (Downgrade):**
- Requires 90-day notice
- Exit planning and knowledge transfer (10 hours included)
- Data export to self-service platform

---

## Contract Terms

### Self-Service SaaS

**Contract Type:** Month-to-month or annual

**Cancellation:**
- Month-to-month: 30 days notice
- Annual: End of term (no early termination refund)

**Payment Terms:**
- Credit card (auto-charge monthly)
- Invoice (annual contracts only, NET 30)

**SLA:**
- Platform uptime: 99.5% (monthly)
- Support response time: Per tier
- No uptime penalty (best effort)

---

### Managed SOC 24/7

**Contract Type:** Annual (minimum 1 year)

**Cancellation:**
- Professional/Enterprise: 90 days notice
- Critical Infrastructure: 180 days notice (due to staffing)

**Payment Terms:**
- Monthly invoicing (NET 15)
- Quarterly prepay option (5% discount)
- Annual prepay option (10% discount)

**SLA:**
- Monitoring uptime: 99.9% (monthly)
- Incident response time: Per tier
- Uptime penalty: 10% monthly fee per 0.1% below target

---

## Frequently Asked Questions

### General Questions

**Q: Can I try before I buy?**
- Self-Service: 14-day free trial (no credit card)
- Managed SOC: Free initial assessment + pilot program (30 days, $2,500)

**Q: What if I exceed my tier limits?**
- Self-Service: Automatic overage charges or upgrade prompt
- Managed SOC: Contact account manager to upgrade tier

**Q: Can I pause service temporarily?**
- Self-Service: Yes (cancel and restart anytime, data retained 90 days)
- Managed SOC: No (annual contract), but can reduce monitored assets

**Q: Do you offer discounts?**
- Annual prepay: 10-20% discount
- Multi-year contracts: Up to 25% discount
- Non-profits: 20% discount
- Educational institutions: 30% discount

---

### Self-Service SaaS Questions

**Q: How long does setup take?**
- Account creation: 5 minutes
- Agent deployment: 1-3 hours (depending on asset count)
- First scan results: 30 minutes after deployment

**Q: What if I need help installing agents?**
- Email support included (all tiers)
- Professional services available ($2,500 for full setup)

**Q: Can I integrate with my existing tools?**
- Business/Enterprise: Yes (webhooks, API, SIEM connectors)
- Starter: Limited (email notifications only)

---

### Managed SOC Questions

**Q: How long is the initial installation?**
- Professional: 1-2 days on-site
- Enterprise: 3-5 days per site
- Critical Infrastructure: Custom timeline (usually 2-4 weeks)

**Q: What network access does INSA need?**
- Read-only access to monitored assets (Wazuh agents)
- Firewall rules for log forwarding (outbound only)
- VPN access for on-site visits (optional)

**Q: Do you work with our existing tools?**
- Yes, we integrate with existing SIEM, ticketing, CMDB
- We complement (not replace) existing tools

**Q: What happens if you detect an incident?**
- We immediately notify designated contacts (phone, email, Slack)
- We provide containment recommendations
- You approve actions, we execute
- Full incident report within 24 hours

---

## Getting Started

### Self-Service SaaS

1. **Sign up:** https://portal.insa-automation.com/signup
2. **Choose tier:** Starter, Business, or Enterprise
3. **Deploy agents:** Follow quick start guide
4. **Run first scan:** See results in 30 minutes

**Support:** support@insa-automation.com

---

### Managed SOC 24/7

1. **Schedule consultation:** sales@insa-automation.com
2. **Free assessment:** On-site or virtual (1-2 hours)
3. **Proposal:** Custom pricing and SOW
4. **Contract signing:** NET 15 payment terms
5. **Installation:** Scheduled within 30 days

**Sales Contact:** sales@insa-automation.com | +1-XXX-XXX-XXXX

---

## Conclusion

Insa Automation Corp offers flexible security monitoring solutions for every organization:

- **Self-Service SaaS** ($99-$2,499/month): Perfect for organizations with IT staff seeking cost-effective, AI-powered vulnerability management
- **Managed SOC 24/7** ($5K-$50K/month): Ideal for critical infrastructure and organizations requiring white-glove, 24/7 expert monitoring

**Not sure which tier is right for you?** Contact our sales team for a free consultation.

---

**Document Version:** 1.0
**Last Updated:** 2025-10-11
**Contact:** sales@insa-automation.com
**Website:** https://www.insa-automation.com

---

*Made by Insa Automation Corp for OpSec*
