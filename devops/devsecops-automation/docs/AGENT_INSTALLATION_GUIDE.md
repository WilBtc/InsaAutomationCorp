# Agent Installation Guide
**Project**: Insa Automation Corp SecureOps Platform
**Component**: Agent Installation & Configuration
**Date**: 2025-10-11
**Version**: 1.0
**Status**: Production Ready

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (One-Line Installer)](#quick-start-one-line-installer)
3. [Installation by Platform](#installation-by-platform)
4. [Configuration Scenarios](#configuration-scenarios)
5. [Proxy Configuration](#proxy-configuration)
6. [Offline Installation](#offline-installation)
7. [Verification & Testing](#verification--testing)
8. [Troubleshooting](#troubleshooting)
9. [Uninstallation](#uninstallation)

---

## Prerequisites

### System Requirements

```yaml
Minimum:
  CPU: 1 core (2.0 GHz)
  Memory: 256 MB RAM
  Disk: 500 MB free space
  Network: Outbound HTTPS (port 443)

Recommended:
  CPU: 2 cores
  Memory: 512 MB RAM
  Disk: 2 GB free space
  Network: 10 Mbps outbound

Operating Systems:
  Linux:
    - Ubuntu 20.04, 22.04, 24.04 (x86_64, ARM64)
    - Debian 10, 11, 12 (x86_64, ARM64)
    - RHEL/CentOS 7, 8, 9 (x86_64)
    - Rocky Linux 8, 9 (x86_64)
    - AlmaLinux 8, 9 (x86_64)
    - Amazon Linux 2, 2023 (x86_64, ARM64)
    - SLES 15+ (x86_64)

  Windows:
    - Windows Server 2016, 2019, 2022 (x86_64)
    - Windows 10, 11 Pro/Enterprise (x86_64)

  macOS:
    - macOS 11 (Big Sur) or later (x86_64, ARM64)

  Containers:
    - Docker 20.10+
    - Podman 3.0+
    - Kubernetes 1.20+

Required Information:
  - API Key (from Insa portal)
  - Client ID (provided during onboarding)
  - Deployment scenario (direct, proxy, ot-gateway)
```

### Firewall Requirements

```yaml
Outbound Rules Required:

Direct Internet:
  - Destination: api.insa-automation.com
    Protocol: HTTPS
    Port: 443
    Purpose: Agent API communication

  - Destination: updates.insa-automation.com
    Protocol: HTTPS
    Port: 443
    Purpose: Agent auto-updates

Corporate Proxy:
  - Destination: proxy.corp.com (your proxy)
    Protocol: HTTP/HTTPS
    Port: 8080 or 3128 (your proxy port)
    Purpose: All outbound traffic via proxy

OT Gateway:
  - Destination: 172.16.0.10 (your gateway IP)
    Protocol: HTTPS
    Port: 8443
    Purpose: Gateway communication

DNS Resolution:
  - Protocol: DNS
    Port: 53 (UDP/TCP)
    Purpose: Domain name resolution
```

---

## Quick Start (One-Line Installer)

### Linux (Ubuntu/Debian/RHEL/CentOS)

```bash
# Direct Internet scenario
curl -sSL https://install.insa-automation.com/agent.sh | sudo bash -s -- \
  --api-key "YOUR_API_KEY_HERE" \
  --client-id "client_yourcompany" \
  --scenario direct

# Corporate Proxy scenario
curl -sSL https://install.insa-automation.com/agent.sh | sudo bash -s -- \
  --api-key "YOUR_API_KEY_HERE" \
  --client-id "client_yourcompany" \
  --scenario proxy \
  --proxy-url "http://proxy.corp.com:8080"

# OT Gateway scenario
curl -sSL https://install.insa-automation.com/agent.sh | sudo bash -s -- \
  --api-key "YOUR_API_KEY_HERE" \
  --client-id "client_yourcompany" \
  --scenario ot-gateway \
  --gateway-host "172.16.0.10" \
  --gateway-port "8443"
```

### What the Installer Does

1. Detects OS and architecture
2. Downloads the appropriate agent binary
3. Verifies GPG signature and checksum
4. Installs to `/opt/insa-agent/`
5. Creates systemd service (Linux) or Windows service
6. Generates configuration file
7. Starts the agent
8. Registers with Insa platform
9. Prints status and verification steps

---

## Installation by Platform

### Linux (Package Manager Installation)

#### Ubuntu/Debian (.deb package)

```bash
# 1. Add Insa repository
curl -fsSL https://packages.insa-automation.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/insa-archive-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/insa-archive-keyring.gpg] https://packages.insa-automation.com/deb stable main" | \
  sudo tee /etc/apt/sources.list.d/insa-agent.list

# 2. Update package list
sudo apt update

# 3. Install agent
sudo apt install insa-agent

# 4. Configure agent
sudo insa-agent configure \
  --api-key "YOUR_API_KEY_HERE" \
  --client-id "client_yourcompany"

# 5. Start agent
sudo systemctl start insa-agent
sudo systemctl enable insa-agent

# 6. Check status
sudo systemctl status insa-agent
```

#### RHEL/CentOS/Rocky/Alma (.rpm package)

```bash
# 1. Add Insa repository
sudo tee /etc/yum.repos.d/insa-agent.repo <<EOF
[insa-agent]
name=Insa SecureOps Agent
baseurl=https://packages.insa-automation.com/rpm/\$basearch
enabled=1
gpgcheck=1
gpgkey=https://packages.insa-automation.com/gpg
EOF

# 2. Install agent
sudo yum install insa-agent
# Or for dnf-based systems:
sudo dnf install insa-agent

# 3. Configure agent
sudo insa-agent configure \
  --api-key "YOUR_API_KEY_HERE" \
  --client-id "client_yourcompany"

# 4. Start agent
sudo systemctl start insa-agent
sudo systemctl enable insa-agent

# 5. Check status
sudo systemctl status insa-agent
```

#### Manual Binary Installation (All Linux Distributions)

```bash
# 1. Download agent binary
AGENT_VERSION="2.0.5"
ARCH="amd64"  # or arm64
wget https://releases.insa-automation.com/insa-agent-${AGENT_VERSION}-linux-${ARCH}.tar.gz

# 2. Verify checksum
wget https://releases.insa-automation.com/insa-agent-${AGENT_VERSION}-linux-${ARCH}.tar.gz.sha256
sha256sum -c insa-agent-${AGENT_VERSION}-linux-${ARCH}.tar.gz.sha256

# 3. Extract
sudo tar -xzf insa-agent-${AGENT_VERSION}-linux-${ARCH}.tar.gz -C /opt/

# 4. Create directories
sudo mkdir -p /etc/insa-agent /var/log/insa-agent /var/lib/insa-agent/cache

# 5. Create configuration
sudo tee /etc/insa-agent/config.yaml <<EOF
platform:
  api_url: "https://api.insa-automation.com"
  api_key: "YOUR_API_KEY_HERE"

agent:
  id: "agent_$(hostname)"
  client_id: "client_yourcompany"
  version: "${AGENT_VERSION}"

network:
  scenario: "direct"  # or proxy or ot-gateway

modules:
  wazuh:
    enabled: true
  trivy:
    enabled: true
  nmap:
    enabled: true
  log_collector:
    enabled: true
EOF

# 6. Create systemd service
sudo tee /etc/systemd/system/insa-agent.service <<EOF
[Unit]
Description=Insa SecureOps Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/opt/insa-agent/bin/insa-agent --config /etc/insa-agent/config.yaml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 7. Reload systemd and start
sudo systemctl daemon-reload
sudo systemctl start insa-agent
sudo systemctl enable insa-agent

# 8. Check status
sudo systemctl status insa-agent
sudo journalctl -u insa-agent -f
```

---

### Windows Installation

#### Method 1: MSI Installer (GUI)

```powershell
# 1. Download installer
# Visit: https://releases.insa-automation.com/insa-agent-2.0.5.msi
# Or use PowerShell:
Invoke-WebRequest -Uri "https://releases.insa-automation.com/insa-agent-2.0.5.msi" `
  -OutFile "C:\Temp\insa-agent-2.0.5.msi"

# 2. Run installer (GUI)
Start-Process "C:\Temp\insa-agent-2.0.5.msi"

# Follow GUI wizard:
#   - Accept license
#   - Choose installation directory (default: C:\Program Files\Insa\Agent)
#   - Enter API Key
#   - Enter Client ID
#   - Choose scenario (Direct/Proxy/Gateway)
#   - Click Install

# 3. Verify service is running
Get-Service -Name "InsaAgent"
```

#### Method 2: MSI Silent Install (CLI)

```powershell
# Silent installation with parameters
msiexec /i "C:\Temp\insa-agent-2.0.5.msi" /quiet /qn /norestart `
  API_KEY="YOUR_API_KEY_HERE" `
  CLIENT_ID="client_yourcompany" `
  SCENARIO="direct" `
  INSTALLDIR="C:\Program Files\Insa\Agent"

# Check installation
Get-Service -Name "InsaAgent"
```

#### Method 3: PowerShell Script Installation

```powershell
# 1. Download and extract agent
$version = "2.0.5"
$url = "https://releases.insa-automation.com/insa-agent-$version-windows-amd64.zip"
$outFile = "$env:TEMP\insa-agent-$version.zip"

Invoke-WebRequest -Uri $url -OutFile $outFile
Expand-Archive -Path $outFile -DestinationPath "C:\Program Files\Insa\Agent"

# 2. Create configuration
$config = @"
platform:
  api_url: "https://api.insa-automation.com"
  api_key: "YOUR_API_KEY_HERE"

agent:
  id: "agent_$($env:COMPUTERNAME)"
  client_id: "client_yourcompany"
  version: "$version"

network:
  scenario: "direct"

modules:
  wazuh:
    enabled: true
  trivy:
    enabled: true
  log_collector:
    enabled: true
"@

Set-Content -Path "C:\Program Files\Insa\Agent\config.yaml" -Value $config

# 3. Install as Windows Service
New-Service -Name "InsaAgent" `
  -BinaryPathName '"C:\Program Files\Insa\Agent\insa-agent.exe" --config "C:\Program Files\Insa\Agent\config.yaml"' `
  -DisplayName "Insa SecureOps Agent" `
  -Description "Security monitoring agent for Insa SecureOps Platform" `
  -StartupType Automatic

# 4. Start service
Start-Service -Name "InsaAgent"

# 5. Verify
Get-Service -Name "InsaAgent"
Get-Content "C:\Program Files\Insa\Agent\logs\agent.log" -Tail 50
```

---

### macOS Installation

#### Method 1: Homebrew

```bash
# 1. Add Insa tap
brew tap insa-automation/agent

# 2. Install agent
brew install insa-agent

# 3. Configure
sudo insa-agent configure \
  --api-key "YOUR_API_KEY_HERE" \
  --client-id "client_yourcompany"

# 4. Start as LaunchDaemon
sudo brew services start insa-agent

# 5. Check status
sudo brew services list | grep insa-agent
tail -f /usr/local/var/log/insa-agent/agent.log
```

#### Method 2: Manual Installation

```bash
# 1. Download agent
AGENT_VERSION="2.0.5"
ARCH="amd64"  # or arm64 for Apple Silicon
curl -L https://releases.insa-automation.com/insa-agent-${AGENT_VERSION}-darwin-${ARCH}.tar.gz -o insa-agent.tar.gz

# 2. Verify checksum
curl -L https://releases.insa-automation.com/insa-agent-${AGENT_VERSION}-darwin-${ARCH}.tar.gz.sha256 -o insa-agent.tar.gz.sha256
shasum -a 256 -c insa-agent.tar.gz.sha256

# 3. Extract
sudo tar -xzf insa-agent.tar.gz -C /usr/local/opt/

# 4. Create directories
sudo mkdir -p /etc/insa-agent /var/log/insa-agent /var/lib/insa-agent/cache

# 5. Create configuration
sudo tee /etc/insa-agent/config.yaml <<EOF
platform:
  api_url: "https://api.insa-automation.com"
  api_key: "YOUR_API_KEY_HERE"

agent:
  id: "agent_$(hostname)"
  client_id: "client_yourcompany"
  version: "${AGENT_VERSION}"

network:
  scenario: "direct"

modules:
  wazuh:
    enabled: true
  trivy:
    enabled: true
  log_collector:
    enabled: true
EOF

# 6. Create LaunchDaemon
sudo tee /Library/LaunchDaemons/com.insa-automation.agent.plist <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.insa-automation.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/opt/insa-agent/bin/insa-agent</string>
        <string>--config</string>
        <string>/etc/insa-agent/config.yaml</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/insa-agent/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/insa-agent/stderr.log</string>
</dict>
</plist>
EOF

# 7. Load and start
sudo launchctl load /Library/LaunchDaemons/com.insa-automation.agent.plist

# 8. Check status
sudo launchctl list | grep insa-automation
tail -f /var/log/insa-agent/agent.log
```

---

### Docker Container Installation

#### Method 1: Docker Run

```bash
# Basic deployment
docker run -d \
  --name insa-agent \
  --restart always \
  --hostname $(hostname) \
  -v /var/log:/host/var/log:ro \
  -v /etc:/host/etc:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -e INSA_API_KEY="YOUR_API_KEY_HERE" \
  -e INSA_CLIENT_ID="client_yourcompany" \
  -e INSA_SCENARIO="direct" \
  insaautomation/agent:2.0.5

# With proxy configuration
docker run -d \
  --name insa-agent \
  --restart always \
  --hostname $(hostname) \
  -v /var/log:/host/var/log:ro \
  -v /etc:/host/etc:ro \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -e INSA_API_KEY="YOUR_API_KEY_HERE" \
  -e INSA_CLIENT_ID="client_yourcompany" \
  -e INSA_SCENARIO="proxy" \
  -e HTTP_PROXY="http://proxy.corp.com:8080" \
  -e HTTPS_PROXY="http://proxy.corp.com:8080" \
  -e NO_PROXY="localhost,127.0.0.1" \
  insaautomation/agent:2.0.5

# Check logs
docker logs -f insa-agent
```

#### Method 2: Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  insa-agent:
    image: insaautomation/agent:2.0.5
    container_name: insa-agent
    restart: always
    hostname: ${HOSTNAME}
    environment:
      - INSA_API_KEY=YOUR_API_KEY_HERE
      - INSA_CLIENT_ID=client_yourcompany
      - INSA_SCENARIO=direct
      # Optional: Proxy configuration
      # - HTTP_PROXY=http://proxy.corp.com:8080
      # - HTTPS_PROXY=http://proxy.corp.com:8080
      # - NO_PROXY=localhost,127.0.0.1
    volumes:
      - /var/log:/host/var/log:ro
      - /etc:/host/etc:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - insa-agent-cache:/var/lib/insa-agent/cache
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

volumes:
  insa-agent-cache:
```

```bash
# Deploy with Docker Compose
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f insa-agent

# Stop
docker-compose down
```

---

### Kubernetes Installation

#### Method 1: DaemonSet (Recommended)

```yaml
# insa-agent-daemonset.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: insa-agent

---
apiVersion: v1
kind: Secret
metadata:
  name: insa-agent-credentials
  namespace: insa-agent
type: Opaque
stringData:
  api-key: "YOUR_API_KEY_HERE"
  client-id: "client_yourcompany"

---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: insa-agent
  namespace: insa-agent
  labels:
    app: insa-agent
spec:
  selector:
    matchLabels:
      app: insa-agent
  template:
    metadata:
      labels:
        app: insa-agent
    spec:
      serviceAccountName: insa-agent
      hostNetwork: true
      hostPID: true
      hostIPC: true
      containers:
      - name: insa-agent
        image: insaautomation/agent:2.0.5
        imagePullPolicy: Always
        env:
        - name: INSA_API_KEY
          valueFrom:
            secretKeyRef:
              name: insa-agent-credentials
              key: api-key
        - name: INSA_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: insa-agent-credentials
              key: client-id
        - name: INSA_SCENARIO
          value: "direct"
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        resources:
          limits:
            memory: "512Mi"
            cpu: "500m"
          requests:
            memory: "128Mi"
            cpu: "100m"
        volumeMounts:
        - name: host-root
          mountPath: /host
          readOnly: true
        - name: docker-sock
          mountPath: /var/run/docker.sock
          readOnly: true
        - name: containerd-sock
          mountPath: /run/containerd/containerd.sock
          readOnly: true
        securityContext:
          privileged: true
      volumes:
      - name: host-root
        hostPath:
          path: /
      - name: docker-sock
        hostPath:
          path: /var/run/docker.sock
          type: Socket
      - name: containerd-sock
        hostPath:
          path: /run/containerd/containerd.sock
          type: Socket
      tolerations:
      - operator: Exists

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: insa-agent
  namespace: insa-agent

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: insa-agent
rules:
- apiGroups: [""]
  resources: ["pods", "nodes", "namespaces"]
  verbs: ["get", "list", "watch"]
- apiGroups: ["apps"]
  resources: ["deployments", "daemonsets", "statefulsets"]
  verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: insa-agent
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: insa-agent
subjects:
- kind: ServiceAccount
  name: insa-agent
  namespace: insa-agent
```

```bash
# Deploy
kubectl apply -f insa-agent-daemonset.yaml

# Check status
kubectl get daemonset -n insa-agent
kubectl get pods -n insa-agent -o wide

# View logs
kubectl logs -n insa-agent -l app=insa-agent --tail=100 -f

# Delete
kubectl delete -f insa-agent-daemonset.yaml
```

#### Method 2: Helm Chart

```bash
# Add Insa Helm repository
helm repo add insa https://charts.insa-automation.com
helm repo update

# Install agent
helm install insa-agent insa/agent \
  --namespace insa-agent \
  --create-namespace \
  --set apiKey="YOUR_API_KEY_HERE" \
  --set clientId="client_yourcompany" \
  --set scenario="direct"

# With custom values
cat <<EOF > values.yaml
apiKey: "YOUR_API_KEY_HERE"
clientId: "client_yourcompany"
scenario: "direct"

resources:
  limits:
    memory: 512Mi
    cpu: 500m
  requests:
    memory: 128Mi
    cpu: 100m

modules:
  wazuh:
    enabled: true
  trivy:
    enabled: true
  nmap:
    enabled: false

# Proxy configuration (optional)
proxy:
  enabled: false
  httpProxy: "http://proxy.corp.com:8080"
  httpsProxy: "http://proxy.corp.com:8080"
  noProxy: "localhost,127.0.0.1,10.0.0.0/8"
EOF

helm install insa-agent insa/agent -f values.yaml -n insa-agent --create-namespace

# Check status
helm status insa-agent -n insa-agent
kubectl get pods -n insa-agent

# Upgrade
helm upgrade insa-agent insa/agent -f values.yaml -n insa-agent

# Uninstall
helm uninstall insa-agent -n insa-agent
```

---

## Configuration Scenarios

### Scenario 1: Direct Internet (Default)

```yaml
# /etc/insa-agent/config.yaml

platform:
  api_url: "https://api.insa-automation.com"
  api_key: "YOUR_API_KEY_HERE"

agent:
  id: "agent_webserver01"  # Unique identifier
  client_id: "client_yourcompany"
  version: "2.0.5"
  hostname: "webserver01.example.com"

network:
  scenario: "direct"

  # Certificate pinning (optional but recommended)
  certificate_pinning:
    enabled: true
    expected_thumbprint: "sha256:abc123...def456"

  # Connection settings
  timeout_seconds: 30
  retry:
    max_retries: 5
    backoff_multiplier: 2

  # Heartbeat interval
  heartbeat_interval_seconds: 60

modules:
  wazuh:
    enabled: true
    monitored_dirs:
      - /etc
      - /var/www
      - /home
    monitored_files:
      - /var/log/auth.log
      - /var/log/syslog

  trivy:
    enabled: true
    scan_images: true
    scan_filesystem: true

  nmap:
    enabled: true
    scan_local_network: true
    scan_interval_hours: 24

  log_collector:
    enabled: true
    sources:
      - /var/log/nginx/*.log
      - /var/log/apache2/*.log
```

---

### Scenario 2: Corporate Proxy

```yaml
# /etc/insa-agent/config.yaml

platform:
  api_url: "https://api.insa-automation.com"
  api_key: "YOUR_API_KEY_HERE"

agent:
  id: "agent_appserver01"
  client_id: "client_yourcompany"
  version: "2.0.5"

network:
  scenario: "proxy"

  # Proxy configuration
  proxy:
    enabled: true
    http_proxy: "http://proxy.corp.com:8080"
    https_proxy: "http://proxy.corp.com:8080"
    no_proxy: "localhost,127.0.0.1,10.0.0.0/8,*.corp.com"

    # Proxy authentication (if required)
    auth:
      enabled: true
      username: "agent_user"
      password: "encrypted:abc123..."  # Use encrypted password
      # For NTLM (Windows):
      auth_type: "ntlm"
      domain: "CORP"

    # SSL inspection handling
    ssl_inspection:
      enabled: true
      trust_custom_ca: true
      custom_ca_bundle: "/etc/ssl/certs/corporate-ca.pem"

  # Certificate pinning (adjusted for SSL inspection)
  certificate_pinning:
    enabled: false  # Disable if proxy does SSL inspection

  timeout_seconds: 60  # Longer timeout for proxy
  heartbeat_interval_seconds: 60

modules:
  wazuh:
    enabled: true
  trivy:
    enabled: true
  nmap:
    enabled: false  # Often disabled in corporate environments
  log_collector:
    enabled: true
```

#### Proxy Authentication Setup

```bash
# Encrypt password for config file
sudo insa-agent encrypt-password --password "your_proxy_password"
# Output: encrypted:abc123def456...

# For NTLM authentication (Windows environments)
# config.yaml:
network:
  proxy:
    auth:
      auth_type: "ntlm"
      domain: "CORP"
      username: "agent_user"
      password: "encrypted:abc123..."

# For Kerberos (enterprise environments)
network:
  proxy:
    auth:
      auth_type: "kerberos"
      principal: "agent_user@CORP.COM"
      keytab: "/etc/insa-agent/agent.keytab"
```

---

### Scenario 3: OT Gateway (Air-Gapped)

#### OT Agent Configuration (Inside OT Network)

```yaml
# /etc/insa-agent/config.yaml (OT Network Devices)

platform:
  # NOT connecting directly to cloud
  api_url: "https://172.16.0.10:8443"  # Gateway in DMZ
  api_key: "OT_AGENT_TOKEN_abc123"

agent:
  id: "agent_ot_plc01"
  client_id: "client_yourcompany"
  mode: "ot_readonly"  # Special OT mode
  hostname: "plc01.ot.example.com"

network:
  scenario: "ot-gateway"

  gateway:
    enabled: true
    gateway_host: "172.16.0.10"  # DMZ jump box
    gateway_port: 8443
    protocol: "https"

  # Extended offline caching for OT
  offline_cache:
    enabled: true
    max_size_mb: 1000  # 1GB cache
    retention_hours: 168  # 7 days
    cache_path: "/var/lib/insa-agent/cache"

# OT Safety Controls
safety:
  read_only: true  # NEVER write to OT devices
  max_cpu_percent: 2  # Very low resource usage
  max_memory_mb: 30
  priority: "low"

modules:
  wazuh:
    enabled: true
    mode: "read_only"
    monitored_files:
      - /var/log/plc/*.log
    fim_enabled: true
    rootkit_check: false  # Too invasive

  trivy:
    enabled: false  # No scanning on PLCs

  nmap:
    enabled: false  # No active scanning

  log_collector:
    enabled: true
    sources:
      - /var/log/plc/operations.log
      - /var/log/plc/alarms.log
```

#### Gateway Configuration (DMZ Jump Box)

See [IT_OT_GATEWAY_SETUP.md](IT_OT_GATEWAY_SETUP.md) for complete gateway setup.

---

## Proxy Configuration

### Environment Variables Method

```bash
# Set proxy environment variables (system-wide)
sudo tee -a /etc/environment <<EOF
http_proxy="http://proxy.corp.com:8080"
https_proxy="http://proxy.corp.com:8080"
no_proxy="localhost,127.0.0.1,10.0.0.0/8"
HTTP_PROXY="http://proxy.corp.com:8080"
HTTPS_PROXY="http://proxy.corp.com:8080"
NO_PROXY="localhost,127.0.0.1,10.0.0.0/8"
EOF

# Reload environment
source /etc/environment

# Test proxy connection
curl -v https://api.insa-automation.com/v2/health
```

### Corporate CA Certificate Installation

```bash
# Ubuntu/Debian
sudo cp corporate-ca.crt /usr/local/share/ca-certificates/
sudo update-ca-certificates

# RHEL/CentOS
sudo cp corporate-ca.crt /etc/pki/ca-trust/source/anchors/
sudo update-ca-trust

# Windows (PowerShell as Administrator)
Import-Certificate -FilePath "C:\Temp\corporate-ca.crt" -CertStoreLocation Cert:\LocalMachine\Root

# macOS
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain corporate-ca.crt

# Update agent config to use custom CA
# /etc/insa-agent/config.yaml
network:
  proxy:
    ssl_inspection:
      enabled: true
      custom_ca_bundle: "/etc/ssl/certs/ca-certificates.crt"  # Linux
      # custom_ca_bundle: "C:\\ProgramData\\ca-bundle.crt"  # Windows
```

---

## Offline Installation

For air-gapped environments or networks without internet access.

### Step 1: Download Offline Package

```bash
# On a machine with internet access:
# Download offline installer package (includes all dependencies)
wget https://releases.insa-automation.com/insa-agent-2.0.5-offline.tar.gz
wget https://releases.insa-automation.com/insa-agent-2.0.5-offline.tar.gz.sha256

# Verify checksum
sha256sum -c insa-agent-2.0.5-offline.tar.gz.sha256

# Transfer to target machine via USB, SCP, etc.
scp insa-agent-2.0.5-offline.tar.gz user@target-machine:/tmp/
```

### Step 2: Install on Air-Gapped Machine

```bash
# Extract offline package
tar -xzf insa-agent-2.0.5-offline.tar.gz
cd insa-agent-2.0.5-offline/

# Review package contents
ls -lah
# Contents:
#   - install.sh (installer script)
#   - insa-agent (agent binary)
#   - trivy-db/ (vulnerability database)
#   - nmap-data/ (Nmap NSE scripts)
#   - docs/ (offline documentation)
#   - config-template.yaml

# Run offline installer
sudo ./install.sh --offline \
  --api-key "YOUR_API_KEY_HERE" \
  --client-id "client_yourcompany" \
  --gateway-host "172.16.0.10" \
  --gateway-port "8443"

# The installer will:
#   1. Install agent binary to /opt/insa-agent/
#   2. Install Trivy database (no internet needed)
#   3. Install Nmap data files
#   4. Create configuration for gateway scenario
#   5. Create systemd service
#   6. Start agent
```

### Step 3: Update Offline Database (Periodic)

```bash
# On internet-connected machine, download latest vulnerability DB
wget https://updates.insa-automation.com/trivy-db-latest.tar.gz

# Transfer to air-gapped machine
scp trivy-db-latest.tar.gz user@target-machine:/tmp/

# On air-gapped machine, update Trivy DB
sudo tar -xzf /tmp/trivy-db-latest.tar.gz -C /var/lib/insa-agent/trivy-db/
sudo systemctl restart insa-agent
```

---

## Verification & Testing

### Check Agent Status

```bash
# Linux (systemd)
sudo systemctl status insa-agent

# Expected output:
# ● insa-agent.service - Insa SecureOps Agent
#    Loaded: loaded (/etc/systemd/system/insa-agent.service; enabled)
#    Active: active (running) since ...
#    Process: ...
#    Main PID: ...
#    Memory: 45.2M
#    CGroup: ...

# Windows
Get-Service -Name "InsaAgent"
# Status should be "Running"

# Docker
docker ps | grep insa-agent
docker logs insa-agent --tail 50

# Kubernetes
kubectl get pods -n insa-agent
kubectl logs -n insa-agent -l app=insa-agent --tail=50
```

### Check Agent Logs

```bash
# Linux (systemd journal)
sudo journalctl -u insa-agent -f

# Linux (log file)
sudo tail -f /var/log/insa-agent/agent.log

# Windows
Get-Content "C:\Program Files\Insa\Agent\logs\agent.log" -Tail 50 -Wait

# Docker
docker logs -f insa-agent

# Kubernetes
kubectl logs -n insa-agent -l app=insa-agent -f
```

### Test Connectivity

```bash
# Test API connectivity
sudo insa-agent test-connection

# Expected output:
# [OK] DNS resolution: api.insa-automation.com → 104.26.x.x
# [OK] TCP connection: api.insa-automation.com:443
# [OK] TLS handshake: TLS 1.3, cipher: TLS_AES_256_GCM_SHA384
# [OK] Certificate validation: Valid until 2025-12-31
# [OK] API authentication: Client authenticated successfully
# [OK] Heartbeat: Sent and acknowledged
#
# Agent Status: HEALTHY

# Test with proxy
sudo insa-agent test-connection --proxy http://proxy.corp.com:8080

# Test gateway connection (OT scenario)
sudo insa-agent test-connection --gateway 172.16.0.10:8443
```

### Verify Agent Registration

```bash
# Check if agent is registered with platform
sudo insa-agent status

# Expected output:
# Agent ID: agent_webserver01
# Client ID: client_yourcompany
# Status: HEALTHY
# Last Heartbeat: 2025-10-11 20:45:30 (10 seconds ago)
# Platform Connection: CONNECTED
# Modules Status:
#   - Wazuh: ACTIVE
#   - Trivy: ACTIVE
#   - Nmap: ACTIVE
#   - Log Collector: ACTIVE
# Next Scan: 2025-10-11 22:00:00
```

### Verify in Insa Portal

1. Log in to https://portal.insa-automation.com
2. Navigate to **Assets** > **Agents**
3. Verify your agent appears in the list with status "Online"
4. Click on agent to view details and recent activity

---

## Troubleshooting

### Common Issues

#### Issue 1: Agent won't start

```bash
# Check logs for errors
sudo journalctl -u insa-agent -n 100 --no-pager

# Common causes:
# 1. Invalid API key
#    Solution: Verify API key in config.yaml, regenerate if needed

# 2. Network connectivity issues
#    Solution: Test connectivity: curl -v https://api.insa-automation.com/v2/health

# 3. Permission issues
#    Solution: Ensure agent runs as root (Linux) or Administrator (Windows)

# 4. Port conflicts
#    Solution: Check if another process is using required ports
```

#### Issue 2: Agent not appearing in portal

```bash
# Verify agent is sending heartbeats
sudo journalctl -u insa-agent | grep "Heartbeat"

# Check if API key is valid
sudo insa-agent test-connection

# Verify client_id matches your account
cat /etc/insa-agent/config.yaml | grep client_id

# Check firewall rules
sudo iptables -L -n | grep 443
```

#### Issue 3: Proxy connection failures

```bash
# Test proxy connectivity
curl -v --proxy http://proxy.corp.com:8080 https://api.insa-automation.com/v2/health

# Check proxy authentication
# If NTLM: ensure domain, username, password are correct
# If Kerberos: verify keytab is valid

# Test with proxy credentials
curl -v --proxy http://username:password@proxy.corp.com:8080 https://api.insa-automation.com/v2/health

# Check SSL inspection
openssl s_client -connect api.insa-automation.com:443 -showcerts -proxy proxy.corp.com:8080

# If corporate CA is needed:
curl -v --cacert /etc/ssl/certs/corporate-ca.pem https://api.insa-automation.com/v2/health
```

#### Issue 4: High CPU/Memory usage

```bash
# Check resource usage
top -p $(pgrep insa-agent)

# Common causes:
# 1. Active scan in progress (normal, temporary)
# 2. Large log files being processed
# 3. Misconfigured scan frequency

# Temporary solution: Lower scan frequency
# /etc/insa-agent/config.yaml
modules:
  trivy:
    scan_interval_hours: 24  # Increase interval
  nmap:
    enabled: false  # Disable if not needed

# Restart agent
sudo systemctl restart insa-agent
```

#### Issue 5: OT gateway not receiving data

```bash
# On OT agent, test gateway connectivity
ping 172.16.0.10
curl -k https://172.16.0.10:8443/health

# Check OT agent logs
sudo journalctl -u insa-agent | grep gateway

# On gateway, check if agents are connecting
sudo journalctl -u insa-gateway | grep "agent_ot_"

# Verify firewall rules allow OT → DMZ traffic
sudo iptables -L -n -v | grep 172.16.0.10
```

### Enable Debug Logging

```yaml
# /etc/insa-agent/config.yaml

logging:
  level: "debug"  # Change from "info" to "debug"
  output: "file"  # or "journal" for systemd
  file_path: "/var/log/insa-agent/agent-debug.log"
  max_size_mb: 100
  max_backups: 5

# Restart agent
sudo systemctl restart insa-agent

# View debug logs
sudo tail -f /var/log/insa-agent/agent-debug.log
```

### Collect Diagnostics Bundle

```bash
# Generate diagnostics bundle (includes logs, config, system info)
sudo insa-agent diagnostics --output /tmp/insa-diagnostics.zip

# Bundle includes:
#   - Agent logs (last 7 days)
#   - Configuration file (API key redacted)
#   - System information (OS, CPU, memory, disk)
#   - Network connectivity tests
#   - Module status
#   - Recent scan results

# Send bundle to support
# Upload to: https://support.insa-automation.com/upload
# Or email: support@insa-automation.com
```

---

## Uninstallation

### Linux (Package Manager)

```bash
# Ubuntu/Debian
sudo apt remove insa-agent
sudo apt purge insa-agent  # Also remove config files

# RHEL/CentOS
sudo yum remove insa-agent

# Clean up remaining files
sudo rm -rf /etc/insa-agent /var/lib/insa-agent /var/log/insa-agent
```

### Linux (Manual Installation)

```bash
# Stop and disable service
sudo systemctl stop insa-agent
sudo systemctl disable insa-agent

# Remove service file
sudo rm /etc/systemd/system/insa-agent.service
sudo systemctl daemon-reload

# Remove agent files
sudo rm -rf /opt/insa-agent /etc/insa-agent /var/lib/insa-agent /var/log/insa-agent
```

### Windows

```powershell
# Uninstall via Control Panel
# Or via MSI:
msiexec /x "C:\Temp\insa-agent-2.0.5.msi" /quiet

# Or via PowerShell:
$app = Get-WmiObject -Class Win32_Product | Where-Object { $_.Name -eq "Insa SecureOps Agent" }
$app.Uninstall()

# Clean up remaining files
Remove-Item -Recurse -Force "C:\Program Files\Insa\Agent"
Remove-Item -Recurse -Force "C:\ProgramData\Insa\Agent"
```

### Docker

```bash
# Stop and remove container
docker stop insa-agent
docker rm insa-agent

# Remove image
docker rmi insaautomation/agent:2.0.5
```

### Kubernetes

```bash
# Delete DaemonSet
kubectl delete -f insa-agent-daemonset.yaml

# Or via Helm
helm uninstall insa-agent -n insa-agent

# Delete namespace
kubectl delete namespace insa-agent
```

---

## Support

For installation assistance:

- **Documentation**: https://docs.insa-automation.com
- **Support Portal**: https://support.insa-automation.com
- **Email**: support@insa-automation.com
- **Phone**: +1 (555) 123-4567 (24/7)

---

**Document**: AGENT_INSTALLATION_GUIDE.md
**Status**: Complete
**Date**: 2025-10-11
**Author**: Claude Code for Insa Automation Corp
