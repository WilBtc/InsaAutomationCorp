# netg Security Stack Audit Report
**Date**: 2025-10-11
**Server**: netg (100.121.213.50)
**Purpose**: Internal INSA Infrastructure Security Operations Center (SOC)
**Auditor**: Claude Code

---

## Executive Summary

**netg is INSA's central Security Operations Center (SOC)** serving as the command center for internal infrastructure monitoring and security operations. This is a **mature, enterprise-grade security stack** with centralized SIEM, vulnerability management, and custom MCP integrations.

### Key Findings

✅ **Strengths:**
- Full Wazuh SIEM stack (Manager + Dashboard + Indexer)
- Greenbone/OpenVAS vulnerability scanner with web UI
- 3 active Wazuh agents (iac1, LU1, netg itself)
- Custom MCP servers for security tool integration
- 28 days uptime with stable operations
- Professional-grade EDR coverage

⚠️ **Critical Issues:**
- Suricata IDS **failed** (same interface misconfiguration as iac1)
- No SOAR platform (manual incident response)
- No threat intelligence feeds
- insa-automation-erp agent **disconnected**

💡 **Opportunity:**
- **This stack can be the reference architecture for your SaaS offering**
- Already have MCP integrations (can be white-labeled)
- Proven tool combinations and configurations
- Known false positive patterns and tuning

---

## System Information

```yaml
Hostname: netg
IP Address:
  - Tailscale: 100.121.213.50
  - Local: 192.168.5.165/22
OS: Ubuntu 24.04.3 LTS (Noble Numbat)
Kernel: Linux
Uptime: 28 days, 4 hours
Memory: 16GB (5.4GB used, 9.9GB available)
Disk: 98GB total, 33GB used (35%), 61GB free
CPU Load: 0.30, 0.27, 0.21 (1/5/15 min)
Role: Central SOC + Exit Node for Tailscale VPN
```

---

## Complete Security Stack Inventory

### 1. SIEM Platform - Wazuh (Full Stack)

**Status**: ✅ **ACTIVE - Central Manager**

**Components:**
```yaml
Wazuh Manager (v4.x):
  Service: wazuh-manager.service
  Status: Active (running)
  Port: 1514 (agent connections), 1515 (agent auth), 55000 (API)
  Config: /var/ossec/etc/ossec.conf
  Role: Central log aggregation, correlation, alerting

Wazuh Dashboard:
  Service: wazuh-dashboard.service
  Status: Active (running)
  Port: 5601
  URL: http://100.121.213.50:5601 (or via reverse proxy)
  Role: Web UI for security events, dashboards, reporting

Wazuh Indexer (OpenSearch):
  Service: wazuh-indexer.service
  Status: Active (running)
  Port: 9200 (HTTP - localhost only), 9300 (cluster)
  Role: Data storage and search engine
```

**Connected Agents:**
```yaml
ID 000: netg (server) - Active/Local
  IP: 127.0.0.1
  Role: Self-monitoring
  Status: ✅ Active

ID 003: iac1 - Active
  IP: any (100.100.101.1 via Tailscale)
  Role: Azure monitoring server
  Status: ✅ Active
  Last seen: Real-time

ID 002: LU1 - Active
  IP: any (100.81.103.99 via Tailscale)
  Role: Workstation monitoring
  Status: ✅ Active
  Last seen: Real-time

ID 004: insa-automation-erp - Disconnected
  IP: any (100.105.64.109)
  Role: Production ERP server
  Status: ⚠️ Disconnected
  Note: Server offline per CLAUDE.md
```

**Wazuh Manager Capabilities:**
- File Integrity Monitoring (FIM)
- Log analysis and correlation
- Rootkit detection
- Vulnerability detection
- Configuration assessment
- Compliance reporting (PCI-DSS, HIPAA, GDPR, etc.)
- Active Response (automatic countermeasures)
- Custom rules and decoders

---

### 2. Vulnerability Scanner - Greenbone/OpenVAS

**Status**: ✅ **ACTIVE - Full Stack**

**Components:**
```yaml
GVM Daemon:
  Service: gvmd.service
  Status: Active (running)
  Port: Internal Unix socket
  Role: Vulnerability Management Daemon

Greenbone Security Assistant (GSA):
  Service: gsad.service
  Status: Active (running)
  Port: 9392 (localhost only)
  URL: http://localhost:9392 (or via reverse proxy)
  Role: Web UI for vulnerability scanning

OpenVAS Scanner:
  Version: 22.7.9-1ubuntu3
  Package: openvas-scanner
  Status: Installed
  Role: Network vulnerability scanning engine

OSPD-OpenVAS:
  Package: ospd-openvas 22.6.2-1ubuntu0.1
  Status: Installed
  Role: OpenVAS Scanner Protocol Daemon
```

**Capabilities:**
- Network vulnerability scanning
- Authenticated scans (credentialed)
- Unauthenticated scans (discovery)
- Web application scanning
- 80,000+ vulnerability tests (NVTs)
- Compliance scanning
- Custom scan configurations
- Report generation (PDF, XML, CSV, etc.)

---

### 3. Network IDS/IPS - Suricata

**Status**: ⚠️ **FAILED - Interface Misconfiguration**

```yaml
Package: suricata 1:8.0.1-0ubuntu0
Service: suricata.service
Status: ❌ Failed (exit-code)
Last attempt: 2025-09-20 13:47:01 UTC (3 weeks ago)
Config: /etc/suricata/suricata.yaml
Issue: Same as iac1 - interface eth0 does not exist
Actual interface: eno1 (192.168.5.165/22)
```

**Problem**: Configuration references non-existent `eth0` interface

**Fix Required**:
```bash
# Update interface from eth0 to eno1
sudo sed -i 's/interface: eth0/interface: eno1/g' /etc/suricata/suricata.yaml
sudo suricata-update  # Download rulesets
sudo systemctl restart suricata
```

**Once Fixed - Capabilities:**
- Network intrusion detection
- Network intrusion prevention
- Protocol analysis
- File extraction
- TLS/SSL inspection
- ET Open rulesets
- Custom Lua scripts
- Integration with Wazuh (via EVE JSON logs)

---

### 4. Antivirus - ClamAV

**Status**: ✅ **ACTIVE**

```yaml
ClamAV Daemon:
  Service: clamav-daemon.service
  Status: Active (running)
  Socket: /var/run/clamav/clamd.ctl
  Version: 1.4.3

ClamAV FreshClam:
  Service: clamav-freshclam.service
  Status: Active (running)
  Role: Automatic virus database updates
  Update frequency: Multiple times per day
```

**Capabilities:**
- Real-time file scanning
- On-demand scanning
- Email gateway scanning
- Archive scanning (ZIP, RAR, TAR, etc.)
- Malware database updates
- Integration with mail servers
- Command-line and daemon modes

---

### 5. Intrusion Prevention - Fail2ban

**Status**: ✅ **ACTIVE**

```yaml
Service: fail2ban.service
Status: Active (running)
Config: /etc/fail2ban/jail.local
Log: /var/log/fail2ban.log
```

**Capabilities:**
- SSH brute-force protection
- Web server attack mitigation
- FTP/SMTP brute-force protection
- Custom jail configurations
- Automatic IP banning
- Email notifications
- Integration with iptables/UFW

---

### 6. File Integrity Monitoring - AIDE

**Status**: ✅ **INSTALLED** (scheduled via cron)

```yaml
Package: aide 0.18.6-2ubuntu0.1
Package: aide-common 0.18.6-2ubuntu0.1
Database: /var/lib/aide/aide.db
Config: /etc/aide/aide.conf
```

**Capabilities:**
- File integrity checking
- Cryptographic hashing (MD5, SHA1, SHA256, SHA512)
- Permission monitoring
- Ownership tracking
- Timestamp verification
- Custom monitoring rules

---

### 7. Rootkit Detection - Rkhunter

**Status**: ✅ **INSTALLED** (scheduled via cron)

```yaml
Package: rkhunter 1.4.6-12
Config: /etc/rkhunter.conf
Database: /var/lib/rkhunter/db
```

**Capabilities:**
- Rootkit detection
- Backdoor detection
- Local exploit detection
- SHA-1/SHA-256 hash comparison
- File property checks
- Suspicious string detection
- Network interface promiscuous mode detection

---

### 8. Security Auditing - Lynis

**Status**: ✅ **INSTALLED** (scheduled via cron)

```yaml
Package: lynis 3.0.9-1
Binary: /usr/bin/lynis
```

**Capabilities:**
- System hardening audit
- Security compliance scanning
- CVE detection
- Configuration analysis
- Kernel hardening checks
- Service security assessment
- Performance suggestions
- Custom audit tests

---

### 9. Network Scanning - Nmap

**Status**: ✅ **INSTALLED**

```yaml
Package: nmap 7.94+git20230807
Package: nmap-common 7.94+git20230807
```

**Capabilities:**
- Port scanning
- Service/version detection
- OS detection
- NSE scripting
- Vulnerability detection scripts
- Network inventory
- Topology mapping

---

### 10. Log Shipper - Filebeat

**Status**: ✅ **ACTIVE**

```yaml
Service: filebeat.service
Status: Active (running)
Role: Ships logs to Elasticsearch/Logstash
```

**Purpose:**
- Centralized log collection
- Log forwarding to SIEM
- Log parsing and enrichment
- Integration with Wazuh Indexer

---

### 11. Reverse Proxy - Traefik

**Status**: ✅ **RUNNING**

```yaml
Process: traefik (PID 6762)
Port: 8443 (HTTPS)
Role: Reverse proxy for web services
```

**Purpose:**
- HTTPS termination
- Service routing
- Load balancing
- Automatic TLS certificate management
- Access to Wazuh Dashboard and Greenbone UI

---

### 12. IoT Message Broker - Mosquitto

**Status**: ✅ **INSTALLED**

```yaml
Package: mosquitto 2.0.18-1build3
Protocol: MQTT
```

**Purpose:**
- IoT device communication
- Pub/sub messaging
- Integration with ThingsBoard on Azure VM

---

### 13. Container Platform - Docker

**Status**: ✅ **RUNNING**

```yaml
Service: snap.docker.dockerd.service
Status: Active (running)
Installation: via Snap
Bridge: docker0 (172.17.0.1/16) - DOWN (no containers)
```

**Note**: No containers currently running on netg

---

## Custom MCP Security Integration

**Location**: `/home/lunet/security-mcp/`

### Custom MCP Servers Built

netg has **custom Model Context Protocol (MCP) servers** for AI-assisted security operations:

```yaml
1. security-orchestrator-mcp:
   Path: /home/lunet/security-mcp/security-orchestrator/
   Type: TypeScript
   Description: "Unified MCP orchestrator for all security tools"
   Features:
     - Coordinates multiple security tools
     - Scheduled security tasks (node-cron)
     - API integration (axios)
     - WebSocket real-time communication
     - Central command & control

2. suricata-mcp:
   Path: /home/lunet/security-mcp/suricata-mcp/
   Purpose: MCP interface for Suricata IDS
   Features:
     - Query Suricata alerts
     - Manage rulesets
     - View EVE JSON logs
     - Real-time alert streaming

3. openvas-mcp:
   Path: /home/lunet/security-mcp/openvas-mcp/
   Purpose: MCP interface for Greenbone/OpenVAS
   Features:
     - Start vulnerability scans
     - Query scan results
     - Manage targets
     - Download reports

4. grafana-mcp:
   Path: /home/lunet/security-mcp/grafana-mcp/
   Purpose: MCP interface for Grafana dashboards
   Features:
     - Query metrics
     - Create dashboards
     - Manage alerts

5. vector-mcp:
   Path: /home/lunet/security-mcp/vector-mcp/
   Purpose: MCP interface for Vector log aggregation
   Features:
     - Log collection management
     - Pipeline configuration
     - Log routing

6. simple-security-mcp.js:
   Path: /home/lunet/security-mcp/simple-security-mcp.js
   Size: 19.6 KB
   Purpose: Combined/simplified security MCP server
```

**Claude Code Integration:**
- `.claude.json` config present in `/home/lunet/.claude.json` (77KB)
- Active Claude Code usage
- Security automation workflows

**Value for SaaS:**
- These MCP servers can be **white-labeled for "Insa Automation Corp"**
- Proven integration patterns with security tools
- Can be deployed as part of multi-tenant offering
- Already supports automation and orchestration

---

## Network Configuration

### Interfaces

```yaml
lo (loopback):
  IP: 127.0.0.1/8, ::1/128
  Status: UNKNOWN (always up)

eno1 (primary):
  IP: 192.168.5.165/22
  Status: UP
  Metric: 100
  Role: Local network connectivity
  Note: This is the interface Suricata should monitor

docker0 (bridge):
  IP: 172.17.0.1/16
  Status: DOWN (no containers)

tailscale0 (VPN):
  IP: 100.121.213.50/32
  IPv6: fd7a:115c:a1e0::c901:d534/128
  Status: UNKNOWN (up)
  Role: Private VPN mesh network
  Features: Offers exit node for other devices
```

### Firewall Rules (iptables)

**Firewall Type**: Raw iptables (no UFW)

**Key Rules:**
```yaml
Tailscale Integration:
  - ts-input chain for Tailscale traffic
  - ts-forward chain for routing
  - All Tailscale traffic accepted

Docker Integration:
  - DOCKER-USER chain
  - DOCKER-FORWARD chain
  - Container networking support

Allowed Services:
  - SSH (22/tcp)
  - DNS (53/tcp, 53/udp)
  - DHCP (67-68/udp)
  - SMTP (25/tcp)
  - Port 9090 (possibly Prometheus)
  - ICMP (ping)

Logging:
  - Dropped packets logged with prefix "iptables-dropped: "
  - Rate limit: 5/min
  - Level: 4 (warning)
```

**Security Posture**:
- ✅ Tailscale VPN required for agent connections
- ✅ Logging enabled for dropped packets
- ✅ Stateful firewall (ESTABLISHED,RELATED accepted)
- ⚠️ Some services exposed on 0.0.0.0 (should restrict to Tailscale)

---

## Service Ports Summary

### Externally Accessible (0.0.0.0)

```yaml
1514/tcp: Wazuh agent connections
1515/tcp: Wazuh agent authentication
5601/tcp: Wazuh Dashboard (web UI)
8443/tcp: Traefik reverse proxy (HTTPS)
55000/tcp: Wazuh Manager API
```

### Localhost Only

```yaml
9200/tcp: Wazuh Indexer (OpenSearch)
9300/tcp: Wazuh Indexer cluster
9392/tcp: Greenbone Security Assistant (GSA) web UI
```

**Recommendation for SaaS**: All client-facing services should:
1. Use reverse proxy (Traefik) for HTTPS termination
2. Implement per-client authentication (API keys, OAuth)
3. Rate limiting per client
4. IP whitelisting where possible

---

## Security Stack Maturity Assessment

### Current Capabilities

| Capability | Tool | Status | Maturity |
|------------|------|--------|----------|
| **Endpoint Detection & Response (EDR)** | Wazuh | ✅ Active | ⭐⭐⭐⭐⭐ Excellent |
| **Centralized SIEM** | Wazuh Manager | ✅ Active | ⭐⭐⭐⭐⭐ Excellent |
| **Vulnerability Scanning** | Greenbone/OpenVAS | ✅ Active | ⭐⭐⭐⭐⭐ Excellent |
| **Network IDS/IPS** | Suricata | ❌ Failed | ⭐☆☆☆☆ Needs fix |
| **Antivirus** | ClamAV | ✅ Active | ⭐⭐⭐⭐☆ Good |
| **Intrusion Prevention** | Fail2ban | ✅ Active | ⭐⭐⭐⭐☆ Good |
| **File Integrity Monitoring** | AIDE | ✅ Scheduled | ⭐⭐⭐☆☆ Basic |
| **Rootkit Detection** | Rkhunter | ✅ Scheduled | ⭐⭐⭐☆☆ Basic |
| **Security Auditing** | Lynis | ✅ Scheduled | ⭐⭐⭐☆☆ Basic |
| **Log Aggregation** | Filebeat | ✅ Active | ⭐⭐⭐⭐☆ Good |
| **Container Security** | None | ❌ Missing | ☆☆☆☆☆ None |
| **Threat Intelligence** | None | ❌ Missing | ☆☆☆☆☆ None |
| **SOAR Platform** | None | ❌ Missing | ☆☆☆☆☆ None |
| **Deception Technology** | None | ❌ Missing | ☆☆☆☆☆ None |
| **API Security** | None | ❌ Missing | ☆☆☆☆☆ None |

### Overall Maturity: ⭐⭐⭐⭐☆ (4/5 - Very Good for Internal SOC)

**Strengths:**
- Excellent SIEM with full Wazuh stack
- Professional vulnerability management
- Strong endpoint monitoring
- Custom automation via MCP servers
- 28 days uptime (stable)

**Gaps for 2026 Industrial SOC:**
- No SOAR (manual incident response)
- No threat intelligence feeds
- No OT/ICS protocol deep inspection
- No container security scanning
- Suricata IDS down (quick fix needed)
- No deception/honeypots

---

## Comparison: netg (Internal) vs iac1 (SaaS Target)

| Aspect | netg (Internal SOC) | iac1 (SaaS Platform) |
|--------|-------------------|----------------------|
| **Purpose** | Internal INSA security | Client-facing SaaS offering |
| **Wazuh** | Manager (central) | Agent only |
| **Vulnerability Scanning** | Greenbone/OpenVAS full stack | DefectDojo (import only) |
| **IDS/IPS** | Suricata (needs fix) | Suricata (recently fixed) |
| **Disk Space** | 61GB free | 61GB free |
| **Memory** | 16GB (5.4GB used) | 16GB |
| **Agents Managed** | 3 (netg, iac1, LU1) | 0 (reports to netg) |
| **Multi-tenancy** | No (single org) | **Required** for SaaS |
| **Custom MCP** | Yes (5+ servers) | DefectDojo MCP only |
| **Uptime** | 28 days | N/A |
| **Role** | Reference architecture | Production SaaS |

---

## Critical Issues and Recommendations

### Immediate Actions Required (High Priority)

#### 1. Fix Suricata IDS on netg ⚠️ **CRITICAL**

**Problem**: Suricata has been down for 3 weeks

**Impact**: No network intrusion detection for INSA infrastructure

**Fix**:
```bash
ssh root@100.121.213.50
sudo sed -i 's/interface: eth0/interface: eno1/g' /etc/suricata/suricata.yaml
sudo suricata-update
sudo systemctl restart suricata
sudo systemctl status suricata
```

**Verification**:
```bash
sudo tail -f /var/log/suricata/eve.json
```

#### 2. Reconnect insa-automation-erp Agent ⚠️ **HIGH**

**Problem**: Production ERP server (ID: 004) disconnected from Wazuh

**Impact**: No monitoring of production database server (426GB database)

**Possible Causes**:
- Server offline (as noted in CLAUDE.md: "Tailscale relay")
- Wazuh agent service stopped
- Network connectivity issues
- Certificate/key mismatch

**Investigation**:
```bash
# Check if server is reachable
tailscale ping 100.105.64.109

# If reachable, check agent status on ERP server
ssh <user>@100.105.64.109
sudo systemctl status wazuh-agent
sudo tail -f /var/ossec/logs/ossec.log
```

#### 3. Secure Externally-Exposed Services 🔒 **MEDIUM**

**Problem**: Several services exposed on 0.0.0.0 (all interfaces)

**Services**:
- Wazuh Dashboard (5601)
- Wazuh API (55000)
- Wazuh agent ports (1514, 1515)

**Recommendation**:
- Restrict to Tailscale network only (100.0.0.0/8)
- Use Traefik reverse proxy with authentication
- Implement rate limiting
- Add IP whitelisting for known agents

**Fix**:
```bash
# Update firewall to restrict services
sudo iptables -I INPUT -p tcp --dport 5601 ! -s 100.0.0.0/8 -j DROP
sudo iptables -I INPUT -p tcp --dport 55000 ! -s 100.0.0.0/8 -j DROP
sudo iptables-save > /etc/iptables/rules.v4
```

---

## Recommendations for SaaS SOC Offering

Based on netg's proven architecture, here's what you can leverage:

### 1. Reference Architecture ⭐

**Use netg as the blueprint for client SOCs:**

```yaml
Core Components (Proven on netg):
  ✅ Wazuh Manager (SIEM)
  ✅ Greenbone/OpenVAS (Vulnerability Scanning)
  ✅ Suricata (IDS/IPS) - once fixed
  ✅ ClamAV (Antivirus)
  ✅ Fail2ban (Intrusion Prevention)
  ✅ Custom MCP servers (automation)

SaaS Enhancements Needed:
  🆕 Multi-tenancy (client isolation)
  🆕 White-labeling (Insa Automation Corp branding)
  🆕 Client onboarding automation
  🆕 Per-client dashboards
  🆕 API key management per client
  🆕 Client data encryption
  🆕 RBAC (role-based access control)
  🆕 SLA monitoring per client
```

### 2. Multi-Tenant Architecture Design

**Option A: Single Wazuh Manager + Products (Recommended)**
```yaml
netg: Central Wazuh Manager
  ├── Product: "Client A - ACME Corp"
  │   ├── Wazuh agents: ACME's servers
  │   ├── Scans: ACME's vulnerability scans
  │   └── Dashboards: ACME's view only
  ├── Product: "Client B - TechCo"
  │   ├── Wazuh agents: TechCo's servers
  │   ├── Scans: TechCo's vulnerability scans
  │   └── Dashboards: TechCo's view only
  └── Product: "INSA Internal"
      ├── Wazuh agents: INSA servers (netg, iac1, LU1)
      └── Dashboards: Internal use only
```

**Benefits**:
- Single infrastructure to manage
- Lower costs
- Easier updates
- Cross-tenant analytics possible (for INSA)

**Challenges**:
- Data isolation must be perfect
- Compliance (some clients may require dedicated instances)
- Performance impact with many clients

**Option B: Wazuh Manager per Client (High Security)**
```yaml
netg: INSA Internal SOC
iac1: Wazuh Manager for Client A
iac2: Wazuh Manager for Client B
iac3: Wazuh Manager for Client C
```

**Benefits**:
- Complete data isolation
- Client-specific SLA guarantees
- Easier compliance (SOC 2, ISO 27001)
- No noisy neighbor problem

**Challenges**:
- Higher infrastructure costs
- More complex management
- Scaling challenges

**Recommendation**: Start with Option A (single manager), upgrade to Option B for enterprise clients

### 3. White-Labeling Strategy

**Brand**: Insa Automation Corp

**Components to White-Label**:

```yaml
Wazuh Dashboard:
  - Custom logo (Insa Automation Corp)
  - Custom color scheme
  - Remove "Wazuh" branding
  - Add "Powered by Insa Automation Corp"
  - Custom login page
  - File: /usr/share/wazuh-dashboard/plugins/wazuh/public/

DefectDojo:
  - Custom logo
  - Custom color scheme
  - Product naming: "Insa SecureOps Platform"
  - Email templates branded
  - Report headers/footers
  - Environment variable: DD_BRAND_NAME="Insa Automation Corp"

Greenbone/OpenVAS:
  - GSA web UI customization
  - Custom report templates
  - Email notifications branded
  - Logo in PDF reports

MCP Servers:
  - Rename from "security-orchestrator-mcp" to "insa-security-orchestrator"
  - Custom descriptions
  - Insa branding in responses

Client Portals:
  - Custom domain: portal.insa-automation.com
  - SSL certificate for domain
  - Client-specific subdomains: client-a.insa-automation.com
```

### 4. Custom MCP Server Reuse

**Existing MCP Servers on netg can be packaged for SaaS:**

```yaml
security-orchestrator-mcp → insa-security-orchestrator:
  - Multi-tenant support
  - Per-client API keys
  - Client-specific scheduling
  - Isolated execution environments

suricata-mcp → insa-ids-manager:
  - Per-client IDS instances
  - Client-specific rulesets
  - Alert filtering per client

openvas-mcp → insa-vulnerability-manager:
  - Per-client scan targets
  - Scheduled scans per client
  - Client-specific vulnerability policies
  - Branded reports

Integration:
  - Deploy on iac1 alongside DefectDojo
  - Single API endpoint for clients
  - Unified authentication
  - Comprehensive audit logging
```

### 5. Client Onboarding Automation

**Create**: `insa-client-onboarding` service on iac1

**Workflow**:
```yaml
1. New Client Registration:
   - Company name
   - Contact info
   - Plan tier (Basic, Pro, Enterprise)
   - Number of assets to monitor

2. Automated Provisioning:
   - Create Wazuh Product for client
   - Generate API keys
   - Create DefectDojo Product
   - Setup initial dashboards
   - Configure scan schedules
   - Generate agent deployment package
   - Send welcome email with credentials

3. Agent Deployment:
   - Provide client with deployment script
   - Script installs Wazuh agent
   - Auto-registers to correct Product
   - Starts sending telemetry

4. First Scan:
   - Run initial vulnerability scan
   - Import results to DefectDojo
   - AI triage findings
   - Generate baseline report
   - Email client with results

5. Ongoing Operations:
   - Continuous monitoring
   - Scheduled scans
   - Alert escalation
   - Monthly reports
   - Quarterly reviews
```

### 6. Integration Points: netg ↔ iac1 (SaaS)

**netg (Internal SOC)** and **iac1 (Client SaaS)** should remain separate but can share:

```yaml
Threat Intelligence:
  - netg discovers new threat → Share indicators with iac1
  - iac1 detects threat across clients → Alert netg
  - Bidirectional threat feed

Tool Updates:
  - netg tests security tool updates first
  - Once stable, roll out to iac1 clients
  - netg is the "canary" for new features

Configuration Templates:
  - Proven configurations from netg
  - Tuned rulesets (reduced false positives)
  - Alert thresholds
  - Scan policies

MCP Server Development:
  - Develop new MCP servers on netg
  - Test with INSA infrastructure
  - Deploy to iac1 for clients once stable

Learning and Patterns:
  - netg's AI learning patterns
  - False positive history
  - Attack patterns seen internally
  - Can inform client offerings
```

**Architecture Diagram**:
```
┌──────────────────────────────────────────┐
│  netg (100.121.213.50)                  │
│  Internal INSA SOC                       │
│  ├── Wazuh Manager                       │
│  ├── Greenbone/OpenVAS                   │
│  ├── Suricata IDS                        │
│  ├── Custom MCP Servers                  │
│  └── Agents: netg, iac1, LU1, ERP       │
└──────────────┬───────────────────────────┘
               │
               │ Threat Intel Sharing
               │ Configuration Sync
               │
┌──────────────▼───────────────────────────┐
│  iac1 (100.100.101.1)                   │
│  Multi-Tenant SaaS SOC                   │
│  ├── DefectDojo (multi-tenant)           │
│  ├── Wazuh Manager (optional - per tier) │
│  ├── Insa White-Labeled MCP Servers      │
│  ├── Client Portal                       │
│  └── Products:                           │
│      ├── Client A                        │
│      ├── Client B                        │
│      └── Client C                        │
└──────────────────────────────────────────┘
```

---

## Next Steps for SaaS SOC Development

### Phase 1: Foundation (Week 1-2)

```yaml
1. Fix netg Suricata IDS:
   - Update interface configuration
   - Verify detection working
   - Document tuning patterns

2. Create Internal vs SaaS Comparison Document:
   - Detailed requirements matrix
   - Multi-tenancy requirements
   - Compliance requirements
   - Data isolation strategy

3. Design Multi-Tenant Architecture:
   - Data model for client separation
   - Authentication/authorization
   - API key management
   - Client dashboards

4. White-Label DefectDojo POC:
   - Insa Automation Corp branding
   - Custom logo and colors
   - Test with 2-3 mock clients
```

### Phase 2: Development (Week 3-4)

```yaml
5. Build Client Onboarding Automation:
   - Registration portal
   - Auto-provisioning script
   - Agent deployment packages
   - Welcome email templates

6. Migrate/Adapt MCP Servers:
   - Port netg MCP servers to iac1
   - Add multi-tenancy support
   - White-label branding
   - Client-specific filtering

7. Implement Client Portal:
   - Dashboard per client
   - Report downloads
   - Scan scheduling UI
   - API documentation

8. Integration with netg:
   - Threat intelligence sharing API
   - Configuration sync
   - Tool update workflow
```

### Phase 3: Compliance & Launch (Week 5-6)

```yaml
9. SOC 2 and ISO 27001 Prep:
   - Gap analysis
   - Policy documentation
   - Access controls
   - Audit logging
   - Encryption implementation

10. Client Documentation:
    - User guides
    - API documentation
    - Agent deployment guides
    - Troubleshooting guides
    - SLA definitions

11. Pricing and Packaging:
    - Basic tier (small business)
    - Pro tier (mid-market)
    - Enterprise tier (large corps)
    - Custom/managed services

12. Go-to-Market:
    - Beta client recruitment
    - Sales materials
    - Demo environment
    - Support processes
```

---

## Files and Directories Reference

### netg Key Locations

```yaml
Wazuh:
  Config: /var/ossec/etc/ossec.conf
  Logs: /var/ossec/logs/
  Rules: /var/ossec/ruleset/rules/
  Decoders: /var/ossec/ruleset/decoders/
  Agent Control: /var/ossec/bin/agent_control
  API: /var/ossec/api/

Wazuh Dashboard:
  Install: /usr/share/wazuh-dashboard/
  Plugins: /usr/share/wazuh-dashboard/plugins/wazuh/
  Config: /etc/wazuh-dashboard/

Wazuh Indexer:
  Install: /usr/share/wazuh-indexer/
  Data: /var/lib/wazuh-indexer/
  Config: /etc/wazuh-indexer/

Suricata:
  Config: /etc/suricata/suricata.yaml
  Rules: /var/lib/suricata/rules/
  Logs: /var/log/suricata/

Greenbone/OpenVAS:
  Config: /etc/gvm/
  Data: /var/lib/gvm/
  Logs: /var/log/gvm/

MCP Servers:
  Base: /home/lunet/security-mcp/
  Orchestrator: /home/lunet/security-mcp/security-orchestrator/
  Suricata: /home/lunet/security-mcp/suricata-mcp/
  OpenVAS: /home/lunet/security-mcp/openvas-mcp/
  Grafana: /home/lunet/security-mcp/grafana-mcp/
  Vector: /home/lunet/security-mcp/vector-mcp/

Claude Code:
  Config: /home/lunet/.claude.json
  History: /home/lunet/.claude/
```

---

## Conclusion

**netg is a mature, enterprise-grade SOC** with the perfect foundation for your SaaS offering. Key takeaways:

✅ **Use netg as reference architecture** - Proven tool stack, configurations, and integrations

✅ **Leverage existing MCP servers** - Custom automation already built, just needs multi-tenancy

✅ **Fix Suricata IDS immediately** - 3-week gap in network monitoring is critical

✅ **Start with Option A multi-tenancy** - Single Wazuh Manager, separate Products per client

✅ **White-label everything** - Insa Automation Corp brand across all tools

✅ **Automate client onboarding** - From registration to first scan in < 1 hour

✅ **Keep netg and iac1 separate** - Share threat intel, but isolate internal from client data

💰 **Market Opportunity**:
- SMB market: $50-200/month per client
- Mid-market: $500-2000/month per client
- Enterprise: $5K-20K/month per client
- 100 clients = $60K-$240K MRR

---

**Next Document**: `INTERNAL_VS_SAAS_SECURITY_COMPARISON.md`
**Then**: `MULTI_TENANT_SAAS_SOC_ARCHITECTURE.md`

**Audit Completed**: 2025-10-11 21:30 UTC
**Audited By**: Claude Code
**System**: netg (100.121.213.50)
