# IT/OT Gateway Setup Guide
**Project**: Insa Automation Corp SecureOps Platform
**Component**: IT/OT Gateway (DMZ Jump Box)
**Date**: 2025-10-11
**Version**: 1.0
**Status**: Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Hardware Requirements](#hardware-requirements)
4. [Network Design](#network-design)
5. [Jump Box Installation](#jump-box-installation)
6. [Gateway Software Setup](#gateway-software-setup)
7. [OT Agent Deployment](#ot-agent-deployment)
8. [Firewall Configuration](#firewall-configuration)
9. [Security Hardening](#security-hardening)
10. [Purdue Model Compliance](#purdue-model-compliance)
11. [Testing & Validation](#testing--validation)
12. [Monitoring & Maintenance](#monitoring--maintenance)
13. [Troubleshooting](#troubleshooting)

---

## Overview

The **IT/OT Gateway** (also called "Jump Box") is a critical security component for industrial environments deploying the Insa SecureOps Platform. It enables secure monitoring of OT (Operational Technology) networks while maintaining strict isolation between OT and IT/Internet.

### Key Features

- **Unidirectional Data Flow**: OT → DMZ → Cloud (never reverse)
- **Data Diode Enforcement**: Software or hardware enforcement
- **Local Buffer**: 72-hour cache for network outages
- **Batch Forwarding**: Aggregates data from multiple OT agents
- **Read-Only OT Access**: Agents never write to OT devices
- **Purdue Model Level 3 Compliant**: Follows IEC 62443 guidelines

### Use Cases

1. **Air-Gapped OT Networks**: Manufacturing plants, refineries, power plants
2. **Industrial Control Systems**: SCADA, DCS, PLC monitoring
3. **Critical Infrastructure**: Water treatment, energy distribution
4. **Regulated Industries**: FDA (pharma), NERC CIP (utilities)
5. **Defense/Government**: Classified or sensitive OT environments

---

## Architecture

### High-Level Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    OT Network (Level 0-2)                       │
│                      Air-Gapped / Isolated                      │
│                     192.168.100.0/24                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │   PLC 1  │  │   PLC 2  │  │   HMI    │  │  SCADA   │       │
│  │  [Agent] │  │  [Agent] │  │  [Agent] │  │  [Agent] │       │
│  │ READ-ONLY│  │ READ-ONLY│  │ READ-ONLY│  │ READ-ONLY│       │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘       │
│        │             │             │             │             │
│        └─────────────┴─────────────┴─────────────┘             │
│                      │                                         │
│              ┌───────▼──────────┐                              │
│              │  OT Switch       │                              │
│              │  VLAN 100        │                              │
│              └───────┬──────────┘                              │
│                      │                                         │
└──────────────────────┼─────────────────────────────────────────┘
                       │
                       │ Firewall 1: OT → DMZ (Unidirectional)
                       │ ✅ Allow: OT agents → Gateway:8443
                       │ ❌ Deny: ALL DMZ → OT traffic
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DMZ (Level 3)                             │
│                    172.16.0.0/24                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │          IT/OT Gateway (Jump Box)                        │  │
│  │          Ubuntu 22.04 LTS Server                         │  │
│  │          172.16.0.10                                     │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Insa Gateway Service                              │ │  │
│  │  │  - Listens on :8443 (mTLS)                         │ │  │
│  │  │  - Receives from OT agents                         │ │  │
│  │  │  - Stores in PostgreSQL buffer                     │ │  │
│  │  │  - Forwards to cloud (batch)                       │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  PostgreSQL Database                               │ │  │
│  │  │  - 72-hour buffer (7 days retention)               │ │  │
│  │  │  - Compressed & encrypted                          │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │  Local Monitoring                                  │ │  │
│  │  │  - Grafana (dashboards)                            │ │  │
│  │  │  - Prometheus (metrics)                            │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  │                                                          │  │
│  └──────────────────────┬───────────────────────────────────┘  │
│                         │                                      │
└─────────────────────────┼──────────────────────────────────────┘
                          │
                          │ Firewall 2: DMZ → Internet
                          │ ✅ Allow: Gateway → api.insa-automation.com:443
                          │ ❌ Deny: ALL Internet → DMZ traffic
                          │
                          ▼
              ┌──────────────────────┐
              │  Corporate Firewall  │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │      Internet        │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────────────┐
              │  Insa SecureOps Platform     │
              │  api.insa-automation.com     │
              │  (iac1: 100.100.101.1)       │
              └──────────────────────────────┘
```

### Data Flow

```yaml
Step-by-Step Data Flow:

Step 1: Detection in OT Network
  - PLC agent detects security event (e.g., unauthorized access)
  - Agent formats finding JSON
  - Agent encrypts data (AES-256-GCM)

Step 2: Push to Gateway
  - Agent sends HTTPS POST to gateway (172.16.0.10:8443)
  - mTLS authentication (client cert verification)
  - Gateway validates agent identity
  - Gateway stores in PostgreSQL buffer

Step 3: Aggregation in DMZ
  - Gateway collects buffered findings (every 5 min)
  - Gateway compresses batch (gzip)
  - Gateway encrypts batch (AES-256)
  - Gateway signs batch (HMAC-SHA256)

Step 4: Forward to Cloud
  - Gateway sends HTTPS POST to Insa platform (api.insa-automation.com)
  - Platform authenticates gateway (API key + cert)
  - Platform decrypts & decompresses batch
  - Platform imports findings to DefectDojo

Step 5: Acknowledgment
  - Platform returns success response
  - Gateway marks findings as forwarded
  - Gateway logs transaction
  - Local monitoring updated

Critical: No reverse traffic allowed (Cloud → DMZ → OT)
```

---

## Hardware Requirements

### Jump Box Specifications

```yaml
Physical Server (Recommended for High-Security):
  CPU: 4 cores (Intel Xeon or AMD EPYC)
  Memory: 16 GB RAM
  Disk: 500 GB SSD (RAID 1 for redundancy)
  Network: 2x 1 Gbps NICs (one for OT, one for Internet)
  Power: Dual power supplies (redundant)
  Form Factor: 1U rackmount server

Virtual Machine (Acceptable for Most Deployments):
  CPU: 4 vCPUs
  Memory: 8 GB RAM
  Disk: 250 GB (thin-provisioned)
  Network: 2x vNICs (separate VLANs)
  Hypervisor: VMware ESXi, Hyper-V, or KVM

Minimum Specifications (Small Deployments):
  CPU: 2 cores
  Memory: 4 GB RAM
  Disk: 100 GB
  Network: 1x NIC (VLAN tagging)

Hardware Data Diode (Optional, High-Security):
  Device: Waterfall Unidirectional Gateway
  Or: Owl Cyber Defense Data Diode
  Or: BAE Systems Data Diode
  Purpose: Hardware-enforced unidirectional data flow
  Installation: Between OT switch and DMZ gateway
```

### Supported Platforms

```yaml
Operating Systems:
  ✅ Ubuntu 22.04 LTS Server (Recommended)
  ✅ Ubuntu 20.04 LTS Server
  ✅ Red Hat Enterprise Linux 8, 9
  ✅ Rocky Linux 8, 9
  ✅ CentOS Stream 8, 9
  ✅ Debian 11, 12

Hypervisors (for VM deployment):
  ✅ VMware ESXi 7.0+
  ✅ Microsoft Hyper-V 2019+
  ✅ Proxmox VE 7.0+
  ✅ KVM/QEMU
  ✅ Red Hat Virtualization (RHV)
```

---

## Network Design

### IP Addressing Scheme

```yaml
OT Network (Level 1-2):
  Subnet: 192.168.100.0/24
  Gateway: 192.168.100.1 (OT Firewall inside interface)
  VLAN: 100 (OT Production)

  Device Assignments:
    - 192.168.100.10-50: PLCs
    - 192.168.100.51-100: HMIs
    - 192.168.100.101-150: SCADA/DCS servers
    - 192.168.100.200-250: Engineering workstations

DMZ Network (Level 3):
  Subnet: 172.16.0.0/24
  Gateway: 172.16.0.1 (DMZ Firewall)
  VLAN: 300 (DMZ Monitoring)

  Device Assignments:
    - 172.16.0.10: IT/OT Gateway (primary)
    - 172.16.0.11: IT/OT Gateway (secondary, for HA)
    - 172.16.0.20: Local monitoring server (Grafana/Prometheus)

Corporate Network (Level 4-5):
  Subnet: 10.0.0.0/8
  Not directly connected to OT or DMZ
```

### VLAN Configuration

```yaml
VLAN Design:

VLAN 100 (OT Production):
  Purpose: Production OT devices
  Security: Highest (air-gapped)
  Access: Engineers only (physical console or local HMI)

VLAN 200 (OT Monitoring):
  Purpose: Read-only monitoring interfaces
  Security: High (unidirectional to DMZ)
  Access: Insa agents on OT devices

VLAN 300 (DMZ):
  Purpose: IT/OT gateway and monitoring
  Security: Medium (isolated from both OT and IT)
  Access: Restricted (firewall rules)

VLAN 400 (Corporate IT):
  Purpose: Business network
  Security: Standard IT controls
  Access: Employees, guests (segmented)

Switch Configuration:
  - Port-based VLANs (no dynamic VLAN assignment)
  - Private VLANs for OT devices (device-to-device blocking)
  - MAC address filtering (whitelist only)
  - Port security (disable unused ports)
```

### Firewall Topology

```yaml
Firewall 1: OT Network → DMZ
  Type: Industrial firewall (e.g., Palo Alto PA-220, Fortinet FortiGate 60F)
  Purpose: Protect OT network, allow monitoring data out only

  Inside Interface: 192.168.100.1 (VLAN 100)
  Outside Interface: 172.16.0.1 (VLAN 300)

  Rules:
    1. Allow OT agents (192.168.100.0/24) → Gateway (172.16.0.10:8443)
    2. Allow established/related traffic (stateful)
    3. DENY ALL DMZ → OT (data diode)
    4. DENY ALL other traffic
    5. LOG ALL denied attempts

Firewall 2: DMZ → Internet
  Type: Enterprise firewall (e.g., Palo Alto PA-3220, Fortinet FortiGate 200F)
  Purpose: Control DMZ egress to cloud

  Inside Interface: 172.16.0.254 (VLAN 300)
  Outside Interface: Public IP (Internet)

  Rules:
    1. Allow Gateway (172.16.0.10) → api.insa-automation.com:443
    2. Allow Gateway (172.16.0.10) → updates.insa-automation.com:443
    3. Allow established/related traffic
    4. DENY ALL Internet → DMZ (no inbound)
    5. DENY ALL other traffic
    6. LOG ALL traffic
```

---

## Jump Box Installation

### Step 1: OS Installation

```bash
# Install Ubuntu 22.04 LTS Server (minimal installation)
# During installation:
#   - Hostname: ot-gateway
#   - Username: otadmin
#   - Disable SSH password authentication (use keys only)
#   - Install OpenSSH server
#   - Do NOT install any other packages

# After installation, update system
sudo apt update
sudo apt upgrade -y
sudo apt autoremove -y

# Reboot
sudo reboot
```

### Step 2: Network Configuration

```yaml
# /etc/netplan/01-netcfg.yaml

network:
  version: 2
  renderer: networkd
  ethernets:
    # Interface 1: OT Network (listening)
    ens18:
      addresses:
        - 192.168.100.254/24
      # No gateway (do not route OT traffic)
      nameservers:
        addresses:
          - 192.168.100.1  # OT DNS (or use DMZ DNS)

    # Interface 2: DMZ Network (forwarding to Internet)
    ens19:
      addresses:
        - 172.16.0.10/24
      gateway4: 172.16.0.1  # DMZ firewall
      nameservers:
        addresses:
          - 1.1.1.1
          - 8.8.8.8
```

```bash
# Apply network configuration
sudo netplan apply

# Verify interfaces
ip addr show
ip route show

# Test OT network connectivity
ping -c 3 192.168.100.10  # PLC

# Test Internet connectivity
ping -c 3 api.insa-automation.com
```

### Step 3: Install Required Packages

```bash
# Update package list
sudo apt update

# Install dependencies
sudo apt install -y \
  curl \
  wget \
  git \
  python3 \
  python3-pip \
  python3-venv \
  postgresql \
  postgresql-contrib \
  nginx \
  certbot \
  ufw \
  fail2ban \
  auditd \
  aide \
  rkhunter \
  logrotate \
  ntp

# Install Docker (for containerized gateway)
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker otadmin

# Install Docker Compose
sudo apt install -y docker-compose
```

---

## Gateway Software Setup

### Step 1: Install Insa Gateway

```bash
# Create installation directory
sudo mkdir -p /opt/insa-gateway
cd /opt/insa-gateway

# Download gateway software
GATEWAY_VERSION="2.0.5"
sudo wget https://releases.insa-automation.com/insa-gateway-${GATEWAY_VERSION}-linux-amd64.tar.gz

# Verify checksum
sudo wget https://releases.insa-automation.com/insa-gateway-${GATEWAY_VERSION}-linux-amd64.tar.gz.sha256
sudo sha256sum -c insa-gateway-${GATEWAY_VERSION}-linux-amd64.tar.gz.sha256

# Extract
sudo tar -xzf insa-gateway-${GATEWAY_VERSION}-linux-amd64.tar.gz

# Create directories
sudo mkdir -p /etc/insa-gateway/{certs,keys}
sudo mkdir -p /var/log/insa-gateway
sudo mkdir -p /var/lib/insa-gateway/{cache,db}
```

### Step 2: Configure PostgreSQL Buffer

```bash
# Create database and user
sudo -u postgres psql <<EOF
CREATE DATABASE insa_gateway_buffer;
CREATE USER insa_gateway WITH PASSWORD 'STRONG_PASSWORD_HERE';
GRANT ALL PRIVILEGES ON DATABASE insa_gateway_buffer TO insa_gateway;
\q
EOF

# Create schema
sudo -u postgres psql -d insa_gateway_buffer <<EOF
CREATE TABLE findings_buffer (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    client_id VARCHAR(100) NOT NULL,
    finding_data JSONB NOT NULL,
    received_at TIMESTAMP DEFAULT NOW(),
    forwarded BOOLEAN DEFAULT FALSE,
    forwarded_at TIMESTAMP,
    compressed BOOLEAN DEFAULT FALSE,
    encrypted BOOLEAN DEFAULT TRUE,
    batch_id VARCHAR(100)
);

CREATE INDEX idx_findings_buffer_agent_id ON findings_buffer(agent_id);
CREATE INDEX idx_findings_buffer_forwarded ON findings_buffer(forwarded);
CREATE INDEX idx_findings_buffer_received_at ON findings_buffer(received_at);

CREATE TABLE gateway_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(100) NOT NULL,
    metric_value NUMERIC NOT NULL,
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_gateway_metrics_recorded_at ON gateway_metrics(recorded_at);

-- Retention policy (auto-delete old data after 7 days)
CREATE OR REPLACE FUNCTION cleanup_old_findings() RETURNS void AS \$\$
BEGIN
    DELETE FROM findings_buffer WHERE forwarded = TRUE AND forwarded_at < NOW() - INTERVAL '7 days';
    DELETE FROM gateway_metrics WHERE recorded_at < NOW() - INTERVAL '30 days';
END;
\$\$ LANGUAGE plpgsql;

-- Schedule cleanup (requires pg_cron extension)
-- Or run via cron: 0 2 * * * psql -U insa_gateway -d insa_gateway_buffer -c "SELECT cleanup_old_findings();"
EOF

# Tune PostgreSQL for gateway workload
sudo tee -a /etc/postgresql/14/main/postgresql.conf <<EOF
# Insa Gateway Tuning
shared_buffers = 512MB
effective_cache_size = 2GB
maintenance_work_mem = 256MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1  # For SSD
work_mem = 8MB
min_wal_size = 1GB
max_wal_size = 4GB
EOF

sudo systemctl restart postgresql
```

### Step 3: Generate Certificates (mTLS)

```bash
# Create CA for OT agents (self-signed)
cd /etc/insa-gateway/certs

# Generate CA private key
sudo openssl genrsa -out ca.key 4096

# Generate CA certificate
sudo openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -out ca.crt \
  -subj "/C=US/ST=State/L=City/O=YourCompany/OU=OT/CN=OT-Gateway-CA"

# Generate gateway server certificate
sudo openssl genrsa -out gateway.key 4096
sudo openssl req -new -key gateway.key -out gateway.csr \
  -subj "/C=US/ST=State/L=City/O=YourCompany/OU=OT/CN=172.16.0.10"

sudo openssl x509 -req -in gateway.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
  -out gateway.crt -days 730 -sha256

# Generate client certificates for each OT agent
for i in {1..10}; do
  sudo openssl genrsa -out agent_ot_plc${i}.key 4096
  sudo openssl req -new -key agent_ot_plc${i}.key -out agent_ot_plc${i}.csr \
    -subj "/C=US/ST=State/L=City/O=YourCompany/OU=OT/CN=agent_ot_plc${i}"
  sudo openssl x509 -req -in agent_ot_plc${i}.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
    -out agent_ot_plc${i}.crt -days 730 -sha256
done

# Set permissions
sudo chmod 600 *.key
sudo chmod 644 *.crt
```

### Step 4: Create Gateway Configuration

```yaml
# /etc/insa-gateway/config.yaml

gateway:
  id: "gateway_acme_ot_dmz01"
  role: "aggregator"
  hostname: "ot-gateway.dmz.example.com"
  version: "2.0.5"

# Listening for OT agents
listener:
  enabled: true
  bind_address: "192.168.100.254"  # Listen on OT interface
  port: 8443
  protocol: "https"

  # mTLS for OT agents
  tls:
    enabled: true
    cert: "/etc/insa-gateway/certs/gateway.crt"
    key: "/etc/insa-gateway/certs/gateway.key"
    client_ca: "/etc/insa-gateway/certs/ca.crt"
    require_client_cert: true
    min_version: "1.3"

  # Rate limiting per OT agent
  rate_limiting:
    enabled: true
    max_requests_per_minute: 60
    max_connections: 50
    burst_size: 10

  # Request validation
  validation:
    max_body_size_mb: 10
    require_agent_id: true
    require_client_id: true

# Cloud forwarding
cloud:
  api_url: "https://api.insa-automation.com"
  api_key: "YOUR_GATEWAY_API_KEY_HERE"  # Obtain from Insa portal

  # Batch forwarding (aggregate OT data)
  batching:
    enabled: true
    batch_size: 500  # Forward 500 findings at once
    batch_interval_seconds: 300  # Every 5 minutes
    max_batch_age_seconds: 600  # Force send after 10 minutes

  # Retry with exponential backoff
  retry:
    enabled: true
    max_retries: 10
    backoff_multiplier: 2
    max_backoff_seconds: 3600  # 1 hour
    retry_on_network_error: true
    retry_on_server_error: true  # 5xx errors

  # Connection timeouts
  timeout:
    connect_seconds: 30
    read_seconds: 60
    write_seconds: 60

# Local buffer database
storage:
  type: "postgresql"
  host: "localhost"
  port: 5432
  database: "insa_gateway_buffer"
  user: "insa_gateway"
  password: "STRONG_PASSWORD_HERE"
  ssl_mode: "require"

  # Connection pool
  pool:
    max_connections: 20
    min_connections: 5
    max_idle_time_seconds: 300

  # Buffer retention
  retention:
    max_days: 7  # Keep 7 days of buffered data
    max_size_gb: 50  # Purge old data if exceeds 50GB
    auto_cleanup: true
    cleanup_interval_hours: 6

# Security controls
security:
  # Data diode simulation (unidirectional)
  unidirectional:
    enabled: true
    direction: "ot_to_cloud"  # Only OT → Cloud, never Cloud → OT

    # Block any commands from cloud to OT
    block_remote_commands: true
    block_config_updates: true  # OT agents cannot be reconfigured remotely

  # Encryption at rest
  encryption:
    enabled: true
    algorithm: "AES-256-GCM"
    key_file: "/etc/insa-gateway/keys/encryption.key"
    rotate_key_days: 90

  # Authentication
  authentication:
    require_mtls: true
    require_api_key: false  # mTLS is sufficient for OT agents
    agent_whitelist_enabled: true
    agent_whitelist:
      - "agent_ot_plc1"
      - "agent_ot_plc2"
      - "agent_ot_plc3"
      # Add all authorized agents

# Logging
logging:
  level: "info"  # debug, info, warn, error
  output: "file"
  file_path: "/var/log/insa-gateway/gateway.log"
  max_size_mb: 100
  max_backups: 10
  compress: true

  # Audit logging
  audit:
    enabled: true
    log_all_requests: true
    log_all_responses: false  # Too verbose
    audit_log_path: "/var/log/insa-gateway/audit.log"

# Monitoring
monitoring:
  enabled: true

  # Prometheus metrics endpoint
  prometheus:
    enabled: true
    listen_address: "127.0.0.1"  # Localhost only (access via reverse proxy)
    listen_port: 9090
    path: "/metrics"

  # Gateway health metrics
  metrics:
    - buffer_size_bytes
    - buffer_entries_count
    - ot_agents_connected
    - findings_queued
    - findings_forwarded_total
    - findings_forwarded_rate
    - cloud_connection_status
    - cloud_api_latency_ms
    - last_successful_sync_timestamp
    - batch_forward_errors_total
    - mtls_auth_failures_total

  # Health check endpoint
  health_check:
    enabled: true
    listen_address: "127.0.0.1"
    listen_port: 8080
    path: "/health"

  # Alerts (email to OT team)
  alerts:
    enabled: true
    email:
      smtp_host: "smtp.example.com"
      smtp_port: 587
      smtp_user: "gateway@example.com"
      smtp_password: "encrypted:abc123..."
      from: "gateway@example.com"
      to:
        - "ot-team@example.com"
        - "w.aroca@insaing.com"

    # Alert conditions
    rules:
      - name: "High buffer usage"
        condition: "buffer_size_gb > 40"
        action: "email"
        cooldown_minutes: 60

      - name: "Cloud connection down"
        condition: "cloud_connection_down_duration > 1h"
        action: "email"
        cooldown_minutes: 30

      - name: "OT agent offline"
        condition: "ot_agent_offline_duration > 10m"
        action: "email"
        cooldown_minutes: 60

      - name: "mTLS auth failures"
        condition: "mtls_auth_failures_count > 10 in 1m"
        action: "email"
        cooldown_minutes: 15
```

### Step 5: Create Systemd Service

```ini
# /etc/systemd/system/insa-gateway.service

[Unit]
Description=Insa SecureOps Gateway
Documentation=https://docs.insa-automation.com/gateway
After=network-online.target postgresql.service
Wants=network-online.target
Requires=postgresql.service

[Service]
Type=simple
User=root
Group=root
ExecStart=/opt/insa-gateway/bin/insa-gateway --config /etc/insa-gateway/config.yaml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/insa-gateway /var/lib/insa-gateway

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start gateway
sudo systemctl enable insa-gateway
sudo systemctl start insa-gateway

# Check status
sudo systemctl status insa-gateway
sudo journalctl -u insa-gateway -f
```

---

## OT Agent Deployment

### Step 1: Prepare OT Agent Configuration

```yaml
# /etc/insa-agent/config.yaml (on OT device)

platform:
  # NOT connecting directly to cloud
  api_url: "https://192.168.100.254:8443"  # Gateway in DMZ
  api_key: "OT_AGENT_TOKEN_plc1"  # Not used with mTLS, but keep for consistency

agent:
  id: "agent_ot_plc1"
  client_id: "client_yourcompany"
  mode: "ot_readonly"  # Special OT mode
  hostname: "plc1.ot.example.com"
  version: "2.0.5"

network:
  scenario: "ot-gateway"

  gateway:
    enabled: true
    gateway_host: "192.168.100.254"  # Gateway OT interface
    gateway_port: 8443
    protocol: "https"

    # mTLS client certificate
    tls:
      client_cert: "/etc/insa-agent/certs/agent_ot_plc1.crt"
      client_key: "/etc/insa-agent/certs/agent_ot_plc1.key"
      ca_cert: "/etc/insa-agent/certs/ca.crt"
      verify_server: true

  # Extended offline caching for OT
  offline_cache:
    enabled: true
    max_size_mb: 1000  # 1GB cache
    retention_hours: 168  # 7 days
    cache_path: "/var/lib/insa-agent/cache"

  # Heartbeat interval
  heartbeat_interval_seconds: 60

# OT Safety Controls
safety:
  read_only: true  # NEVER write to OT devices
  max_cpu_percent: 2  # Very low resource usage
  max_memory_mb: 30
  priority: "low"  # Background process

  # No remote commands from platform
  remote_commands:
    enabled: false

  # No configuration updates from cloud
  remote_config_updates:
    enabled: false

modules:
  wazuh:
    enabled: true
    mode: "read_only"
    monitored_files:
      - /var/log/plc/*.log
      - /var/log/plc/alarms.log
    fim_enabled: true
    fim_directories:
      - /etc/plc/config
      - /opt/plc/firmware
    rootkit_check: false  # Too invasive for OT

  trivy:
    enabled: false  # No scanning on PLCs

  nmap:
    enabled: false  # No active scanning

  log_collector:
    enabled: true
    batch_interval_seconds: 300  # Every 5 minutes
    sources:
      - path: "/var/log/plc/operations.log"
        type: "syslog"
      - path: "/var/log/plc/alarms.log"
        type: "json"
      - path: "/var/log/plc/security.log"
        type: "syslog"

logging:
  level: "info"
  output: "file"
  file_path: "/var/log/insa-agent/agent.log"
  max_size_mb: 50
  max_backups: 5
```

### Step 2: Deploy Client Certificates to OT Agents

```bash
# On gateway server, copy client certificates
# Method 1: SCP (if SSH enabled on OT device)
scp /etc/insa-gateway/certs/agent_ot_plc1.crt otadmin@192.168.100.10:/tmp/
scp /etc/insa-gateway/certs/agent_ot_plc1.key otadmin@192.168.100.10:/tmp/
scp /etc/insa-gateway/certs/ca.crt otadmin@192.168.100.10:/tmp/

# Method 2: USB transfer (for air-gapped PLCs)
# Copy certificates to USB drive, physically transfer to PLC

# On OT device (PLC), install certificates
sudo mkdir -p /etc/insa-agent/certs
sudo mv /tmp/agent_ot_plc1.crt /etc/insa-agent/certs/
sudo mv /tmp/agent_ot_plc1.key /etc/insa-agent/certs/
sudo mv /tmp/ca.crt /etc/insa-agent/certs/

# Set permissions
sudo chmod 600 /etc/insa-agent/certs/agent_ot_plc1.key
sudo chmod 644 /etc/insa-agent/certs/agent_ot_plc1.crt
sudo chmod 644 /etc/insa-agent/certs/ca.crt
```

### Step 3: Install Insa Agent on OT Device

```bash
# Download agent (offline installer for air-gapped PLCs)
# Transfer insa-agent-2.0.5-offline.tar.gz to OT device

# On OT device:
tar -xzf insa-agent-2.0.5-offline.tar.gz
cd insa-agent-2.0.5-offline/

# Run offline installer
sudo ./install.sh --offline \
  --gateway-host "192.168.100.254" \
  --gateway-port "8443" \
  --agent-id "agent_ot_plc1" \
  --client-id "client_yourcompany"

# Verify agent is running
sudo systemctl status insa-agent

# Check logs
sudo journalctl -u insa-agent -f
```

---

## Firewall Configuration

### Firewall 1: OT → DMZ (Unidirectional)

#### iptables Rules (on OT Firewall or Gateway)

```bash
# Flush existing rules
sudo iptables -F
sudo iptables -X
sudo iptables -Z

# Default policies
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# Allow loopback
sudo iptables -A INPUT -i lo -j ACCEPT

# Allow established/related connections
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

# CRITICAL: Allow OT agents to gateway (port 8443)
sudo iptables -A FORWARD -s 192.168.100.0/24 -d 192.168.100.254 -p tcp --dport 8443 -m state --state NEW,ESTABLISHED -j ACCEPT

# CRITICAL: DENY ALL DMZ → OT traffic (data diode)
sudo iptables -A FORWARD -s 172.16.0.0/24 -d 192.168.100.0/24 -j LOG --log-prefix "BLOCKED-DMZ-TO-OT: "
sudo iptables -A FORWARD -s 172.16.0.0/24 -d 192.168.100.0/24 -j DROP

# DENY all other OT → DMZ traffic
sudo iptables -A FORWARD -s 192.168.100.0/24 -d 172.16.0.0/24 -j LOG --log-prefix "BLOCKED-OT-TO-DMZ: "
sudo iptables -A FORWARD -s 192.168.100.0/24 -d 172.16.0.0/24 -j DROP

# Allow SSH from OT management network (optional, for troubleshooting)
# sudo iptables -A INPUT -s 192.168.100.200/29 -p tcp --dport 22 -j ACCEPT

# Log all dropped packets
sudo iptables -A INPUT -j LOG --log-prefix "DROPPED-INPUT: "
sudo iptables -A FORWARD -j LOG --log-prefix "DROPPED-FORWARD: "

# Save rules
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

### Firewall 2: DMZ → Internet

#### iptables Rules (on DMZ Firewall or Gateway)

```bash
# Flush existing rules
sudo iptables -F
sudo iptables -X
sudo iptables -Z

# Default policies
sudo iptables -P INPUT DROP
sudo iptables -P FORWARD DROP
sudo iptables -P OUTPUT ACCEPT

# Allow loopback
sudo iptables -A INPUT -i lo -j ACCEPT

# Allow established/related connections
sudo iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
sudo iptables -A FORWARD -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow gateway to Insa API (port 443)
sudo iptables -A FORWARD -s 172.16.0.10 -d api.insa-automation.com -p tcp --dport 443 -m state --state NEW,ESTABLISHED -j ACCEPT

# Allow gateway to Insa Updates (port 443)
sudo iptables -A FORWARD -s 172.16.0.10 -d updates.insa-automation.com -p tcp --dport 443 -m state --state NEW,ESTABLISHED -j ACCEPT

# Allow DNS resolution
sudo iptables -A FORWARD -s 172.16.0.10 -p udp --dport 53 -j ACCEPT
sudo iptables -A FORWARD -s 172.16.0.10 -p tcp --dport 53 -j ACCEPT

# DENY all Internet → DMZ traffic (no inbound)
sudo iptables -A FORWARD -d 172.16.0.0/24 -j LOG --log-prefix "BLOCKED-INTERNET-TO-DMZ: "
sudo iptables -A FORWARD -d 172.16.0.0/24 -j DROP

# DENY all other DMZ → Internet traffic
sudo iptables -A FORWARD -s 172.16.0.0/24 -j LOG --log-prefix "BLOCKED-DMZ-TO-INTERNET: "
sudo iptables -A FORWARD -s 172.16.0.0/24 -j DROP

# Log all dropped packets
sudo iptables -A INPUT -j LOG --log-prefix "DROPPED-INPUT: "
sudo iptables -A FORWARD -j LOG --log-prefix "DROPPED-FORWARD: "

# Save rules
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

### Commercial Firewall Configuration (Palo Alto Example)

```yaml
# Palo Alto Firewall Configuration (CLI or GUI)

# Security Zone: OT
# Interface: ethernet1/1 (192.168.100.1)
# Security Level: Highest

# Security Zone: DMZ
# Interface: ethernet1/2 (172.16.0.1)
# Security Level: Medium

# Security Zone: Internet
# Interface: ethernet1/3 (Public IP)
# Security Level: Lowest

# Security Policy: Allow OT Agents to Gateway
Rule Name: Allow_OT_Agents_to_Gateway
Source Zone: OT
Source Address: 192.168.100.0/24
Destination Zone: DMZ
Destination Address: 172.16.0.10
Application: ssl
Service: tcp/8443
Action: Allow
Profile Type: Profiles
Security Profiles: IPS + Antivirus + URL Filtering
Log Setting: Log at Session End

# Security Policy: Deny DMZ to OT (Data Diode)
Rule Name: Block_DMZ_to_OT
Source Zone: DMZ
Destination Zone: OT
Action: Deny
Log Setting: Log at Session Start

# Security Policy: Allow Gateway to Cloud
Rule Name: Allow_Gateway_to_Cloud
Source Zone: DMZ
Source Address: 172.16.0.10
Destination Zone: Internet
Destination Address: api.insa-automation.com, updates.insa-automation.com
Application: ssl
Service: tcp/443
Action: Allow
Profile Type: Profiles
Security Profiles: IPS + Antivirus + URL Filtering
Log Setting: Log at Session End

# Security Policy: Deny all other traffic
Rule Name: Deny_All
Source Zone: Any
Destination Zone: Any
Action: Deny
Log Setting: Log at Session Start
```

---

## Security Hardening

### Gateway Server Hardening

```bash
# 1. Disable unused services
sudo systemctl disable bluetooth
sudo systemctl disable cups
sudo systemctl disable avahi-daemon

# 2. Enable firewall (UFW)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 192.168.100.0/24 to any port 8443 proto tcp  # OT agents
sudo ufw allow from 127.0.0.1 to any port 9090 proto tcp  # Prometheus (localhost)
sudo ufw enable

# 3. Install and configure fail2ban
sudo apt install -y fail2ban
sudo tee /etc/fail2ban/jail.local <<EOF
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port    = 22
logpath = /var/log/auth.log

[insa-gateway]
enabled  = true
port     = 8443
logpath  = /var/log/insa-gateway/gateway.log
maxretry = 10
EOF
sudo systemctl restart fail2ban

# 4. Install AIDE (file integrity monitoring)
sudo apt install -y aide
sudo aideinit
sudo mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Schedule daily AIDE checks
sudo tee /etc/cron.daily/aide-check <<EOF
#!/bin/bash
/usr/bin/aide --check | mail -s "AIDE Report for \$(hostname)" ot-team@example.com
EOF
sudo chmod +x /etc/cron.daily/aide-check

# 5. Install and configure auditd
sudo apt install -y auditd
sudo tee -a /etc/audit/rules.d/insa-gateway.rules <<EOF
# Monitor gateway configuration changes
-w /etc/insa-gateway/ -p wa -k insa_gateway_config

# Monitor gateway binary
-w /opt/insa-gateway/bin/insa-gateway -p x -k insa_gateway_exec

# Monitor certificate changes
-w /etc/insa-gateway/certs/ -p wa -k insa_gateway_certs

# Monitor database access
-w /var/lib/insa-gateway/db/ -p wa -k insa_gateway_db
EOF
sudo augenrules --load
sudo systemctl restart auditd

# 6. Harden SSH (if needed for remote management)
sudo tee /etc/ssh/sshd_config.d/hardening.conf <<EOF
PermitRootLogin no
PasswordAuthentication no
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
AllowUsers otadmin
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
EOF
sudo systemctl restart sshd

# 7. Install rkhunter (rootkit detection)
sudo apt install -y rkhunter
sudo rkhunter --update
sudo rkhunter --propupd

# Schedule weekly scans
sudo tee /etc/cron.weekly/rkhunter-scan <<EOF
#!/bin/bash
/usr/bin/rkhunter --check --skip-keypress --report-warnings-only | mail -s "Rkhunter Report for \$(hostname)" ot-team@example.com
EOF
sudo chmod +x /etc/cron.weekly/rkhunter-scan

# 8. Enable automatic security updates (Ubuntu)
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

---

## Purdue Model Compliance

### Alignment with IEC 62443

```yaml
Purdue Model Level Mapping:

Level 0 (Physical Process):
  Components: Sensors, Actuators, Motors, Valves
  Insa Agent: NOT INSTALLED (safety-critical, never touch)
  Monitoring: None (Level 1 PLCs collect data)

Level 1 (Basic Control):
  Components: PLCs, RTUs, Field Controllers
  Insa Agent: Installed in READ-ONLY mode
  Monitoring: Passive (log collection, FIM)
  Network: VLAN 100 (OT Production)
  Security: Highest (air-gapped)

Level 2 (Supervisory Control):
  Components: SCADA, HMI, Historian
  Insa Agent: Installed in READ-ONLY mode
  Monitoring: Passive (log collection, FIM)
  Network: VLAN 100 (OT Production)
  Security: High (segmented from IT)

Level 3 (Operations Management):
  Components: IT/OT Gateway (DMZ Jump Box)
  Insa Agent: Gateway software (aggregator)
  Monitoring: Active (aggregates Level 1-2 data)
  Network: VLAN 300 (DMZ)
  Security: Medium (data diode enforced)

Level 3.5 (DMZ):
  Components: Firewall, Data Diode
  Purpose: Security boundary between OT and IT/Internet
  Security: Unidirectional (OT → Internet only)

Level 4 (Business Planning):
  Components: ERP, MES, Business Systems
  Insa Agent: Standard agent (full features)
  Network: VLAN 400 (Corporate IT)
  Security: Standard IT controls

Level 5 (Enterprise):
  Components: Cloud services, Insa Platform
  Purpose: Security analytics, reporting
  Network: Internet
  Security: SaaS platform (SOC 2 compliant)

Data Flow (Unidirectional):
  Level 0-1-2 → Level 3 (Gateway) → Level 3.5 (Firewall) → Level 5 (Cloud)
  No reverse flow allowed
```

---

## Testing & Validation

### Functional Testing

```bash
# 1. Test OT Agent → Gateway Connectivity
# On OT agent:
sudo insa-agent test-connection --gateway 192.168.100.254:8443

# Expected: [OK] mTLS handshake successful

# 2. Test Gateway → Cloud Connectivity
# On gateway:
sudo insa-gateway test-connection --cloud

# Expected: [OK] API authentication successful

# 3. Send Test Finding from OT Agent
# On OT agent:
sudo insa-agent send-test-finding

# Expected: Finding sent to gateway and queued for forwarding

# 4. Verify Finding in Gateway Buffer
# On gateway:
sudo -u postgres psql -d insa_gateway_buffer -c "SELECT COUNT(*) FROM findings_buffer WHERE forwarded = FALSE;"

# Expected: Count > 0

# 5. Trigger Manual Batch Forward
# On gateway:
sudo insa-gateway force-forward

# Expected: Batch sent to cloud successfully

# 6. Verify Finding in Insa Portal
# Log in to https://portal.insa-automation.com
# Navigate to Findings
# Search for test finding

# Expected: Finding appears in portal
```

### Security Testing

```bash
# 1. Test Data Diode (DMZ → OT should fail)
# On gateway, try to ping OT device:
ping -c 3 192.168.100.10

# Expected: No response or "Destination Host Unreachable"

# 2. Test Firewall Rules (unauthorized connection should fail)
# From external machine, try to connect to gateway:
telnet 172.16.0.10 8443

# Expected: Connection refused or timeout

# 3. Test mTLS Authentication (without client cert should fail)
# On OT agent, temporarily remove client cert:
sudo mv /etc/insa-agent/certs/agent_ot_plc1.crt /tmp/

# Try to send data:
sudo insa-agent send-test-finding

# Expected: "mTLS authentication failed"

# Restore cert:
sudo mv /tmp/agent_ot_plc1.crt /etc/insa-agent/certs/

# 4. Test Rate Limiting
# On OT agent, flood gateway with requests:
for i in {1..100}; do sudo insa-agent send-test-finding; done

# Expected: After 60 requests/min, gateway returns "Rate limit exceeded"

# Check gateway logs:
sudo journalctl -u insa-gateway | grep "Rate limit"
```

### Performance Testing

```bash
# 1. Measure Gateway Latency
# On OT agent:
time sudo insa-agent send-test-finding

# Expected: < 100ms for local network

# 2. Test Batch Forwarding Performance
# On gateway, queue 1000 findings:
# (Use script to generate test data)

# Trigger batch forward and measure:
time sudo insa-gateway force-forward

# Expected: 1000 findings forwarded in < 10 seconds

# 3. Monitor Gateway Resource Usage
# On gateway:
htop  # or top

# Expected:
#   CPU: < 10% (idle), < 50% (during batch forward)
#   Memory: < 500 MB
#   Disk I/O: < 10 MB/s

# 4. Test Offline Mode (disconnect Internet)
# On gateway, disable Internet interface:
sudo ifconfig ens19 down

# Send findings from OT agents for 1 hour
# Re-enable Internet:
sudo ifconfig ens19 up

# Expected: All buffered findings forwarded within 10 minutes
```

---

## Monitoring & Maintenance

### Monitoring Dashboard (Grafana)

```bash
# Install Grafana on gateway (localhost only)
sudo apt install -y grafana

# Configure Grafana to scrape Prometheus metrics
sudo tee /etc/grafana/provisioning/datasources/prometheus.yaml <<EOF
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
EOF

# Start Grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# Access Grafana (via SSH tunnel or local console)
# http://localhost:3000 (default user/pass: admin/admin)

# Import Insa Gateway Dashboard
# Download dashboard JSON from https://dashboards.insa-automation.com/gateway.json
# Import via Grafana UI
```

### Key Metrics to Monitor

```yaml
Gateway Health:
  - gateway_uptime_seconds
  - gateway_version

Buffer Status:
  - findings_buffer_size_bytes
  - findings_buffer_entries_count
  - findings_buffer_oldest_entry_age_seconds

OT Agent Connectivity:
  - ot_agents_connected_count
  - ot_agent_last_seen_timestamp (per agent)
  - mtls_auth_failures_total

Cloud Connectivity:
  - cloud_connection_status (0=down, 1=up)
  - cloud_api_latency_ms
  - cloud_api_errors_total
  - last_successful_batch_forward_timestamp

Data Throughput:
  - findings_received_total
  - findings_forwarded_total
  - findings_forwarded_rate (findings/second)
  - bytes_received_total
  - bytes_forwarded_total

System Resources:
  - cpu_usage_percent
  - memory_usage_bytes
  - disk_usage_percent
  - network_tx_bytes_total
  - network_rx_bytes_total

Alerts to Configure:
  - Buffer > 80% capacity
  - Cloud connection down > 1 hour
  - OT agent offline > 10 minutes
  - mTLS auth failures > 10 in 1 minute
  - Disk usage > 90%
```

### Maintenance Tasks

```yaml
Daily:
  - Review gateway logs for errors
  - Check OT agent connectivity
  - Verify batch forwarding is working

Weekly:
  - Review Grafana dashboards
  - Check database size and retention
  - Review firewall logs for anomalies
  - Test failover to secondary gateway (if HA)

Monthly:
  - Update gateway software (if updates available)
  - Rotate encryption keys
  - Review and renew TLS certificates (if expiring soon)
  - Conduct security audit (AIDE, rkhunter)

Quarterly:
  - Full system backup (gateway + database)
  - Disaster recovery drill
  - Review and update firewall rules
  - Penetration testing (optional)

Annually:
  - Hardware maintenance (physical servers)
  - Certificate renewal (CA + all agent certs)
  - Compliance audit (IEC 62443, NERC CIP)
```

---

## Troubleshooting

### Issue 1: OT Agent Cannot Connect to Gateway

```bash
# Symptom: Agent logs show "Connection refused" or "Connection timeout"

# Diagnostics:
# 1. Verify network connectivity (ping)
ping -c 3 192.168.100.254

# 2. Verify gateway is listening on port 8443
sudo netstat -tuln | grep 8443

# 3. Check firewall rules
sudo iptables -L -n -v | grep 8443

# 4. Test mTLS handshake
openssl s_client -connect 192.168.100.254:8443 \
  -cert /etc/insa-agent/certs/agent_ot_plc1.crt \
  -key /etc/insa-agent/certs/agent_ot_plc1.key \
  -CAfile /etc/insa-agent/certs/ca.crt

# Expected: "Verify return code: 0 (ok)"

# 5. Check gateway logs
sudo journalctl -u insa-gateway | grep ERROR
```

### Issue 2: Gateway Cannot Forward to Cloud

```bash
# Symptom: Findings accumulate in buffer, not forwarded to cloud

# Diagnostics:
# 1. Test Internet connectivity
curl -v https://api.insa-automation.com/v2/health

# 2. Verify API key
sudo cat /etc/insa-gateway/config.yaml | grep api_key

# 3. Check gateway logs
sudo journalctl -u insa-gateway | grep "cloud"

# 4. Check buffer size
sudo -u postgres psql -d insa_gateway_buffer -c "SELECT COUNT(*) FROM findings_buffer WHERE forwarded = FALSE;"

# 5. Manually trigger forward
sudo insa-gateway force-forward

# 6. Check for network issues (DNS, proxy, firewall)
traceroute api.insa-automation.com
```

### Issue 3: High Buffer Usage

```bash
# Symptom: Buffer > 80% capacity, risk of data loss

# Immediate action:
# 1. Check cloud connectivity
curl https://api.insa-automation.com/v2/health

# If cloud is down: Wait for connectivity
# If cloud is up: Trigger manual forward
sudo insa-gateway force-forward

# 2. Temporarily increase buffer size
sudo -u postgres psql -d insa_gateway_buffer <<EOF
-- Delete old forwarded findings
DELETE FROM findings_buffer WHERE forwarded = TRUE AND forwarded_at < NOW() - INTERVAL '1 day';
EOF

# 3. Increase batch size to forward more at once
sudo nano /etc/insa-gateway/config.yaml
# Set: batching.batch_size = 1000
sudo systemctl restart insa-gateway

# 4. Monitor buffer in real-time
watch -n 5 'sudo -u postgres psql -d insa_gateway_buffer -t -c "SELECT COUNT(*) FROM findings_buffer WHERE forwarded = FALSE;"'
```

### Issue 4: mTLS Authentication Failures

```bash
# Symptom: OT agents rejected by gateway, "mTLS auth failed" errors

# Diagnostics:
# 1. Verify client certificate is valid
openssl x509 -in /etc/insa-agent/certs/agent_ot_plc1.crt -noout -dates

# 2. Verify certificate chain
openssl verify -CAfile /etc/insa-agent/certs/ca.crt /etc/insa-agent/certs/agent_ot_plc1.crt

# Expected: "OK"

# 3. Check certificate CN matches agent_id
openssl x509 -in /etc/insa-agent/certs/agent_ot_plc1.crt -noout -subject

# Expected: "CN=agent_ot_plc1"

# 4. Re-issue certificate if expired or invalid
# On gateway:
sudo openssl genrsa -out /etc/insa-gateway/certs/agent_ot_plc1.key 4096
sudo openssl req -new -key /etc/insa-gateway/certs/agent_ot_plc1.key \
  -out /etc/insa-gateway/certs/agent_ot_plc1.csr \
  -subj "/CN=agent_ot_plc1"
sudo openssl x509 -req -in /etc/insa-gateway/certs/agent_ot_plc1.csr \
  -CA /etc/insa-gateway/certs/ca.crt \
  -CAkey /etc/insa-gateway/certs/ca.key \
  -CAcreateserial \
  -out /etc/insa-gateway/certs/agent_ot_plc1.crt \
  -days 730 -sha256

# Transfer new cert to OT agent
```

---

## Support

For IT/OT gateway assistance:

- **Documentation**: https://docs.insa-automation.com/gateway
- **Support Portal**: https://support.insa-automation.com
- **Email**: ot-support@insa-automation.com
- **Emergency Hotline**: +1 (555) 123-4567 (24/7)

---

**Document**: IT_OT_GATEWAY_SETUP.md
**Status**: Complete
**Date**: 2025-10-11
**Author**: Claude Code for Insa Automation Corp
