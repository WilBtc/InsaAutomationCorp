# Agent Deployment Quick Reference
**Insa Automation Corp SecureOps Platform**
**Version**: 1.0 | **Date**: 2025-10-11

---

## 📚 Documentation Index

### Core Documents (START HERE)

1. **AGENT_DEPLOYMENT_SUMMARY.md** (16 KB)
   - Overview of entire architecture
   - Key decisions and features
   - Quick links to detailed docs

2. **AGENT_DEPLOYMENT_ARCHITECTURE.md** (57 KB)
   - Technical architecture for all 3 scenarios
   - Network diagrams
   - Security features
   - Communication protocols

3. **AGENT_INSTALLATION_GUIDE.md** (32 KB)
   - OS-specific installation steps
   - One-line installer examples
   - Proxy configuration
   - Troubleshooting

4. **IT_OT_GATEWAY_SETUP.md** (47 KB)
   - Jump box installation
   - Gateway configuration
   - Firewall rules
   - Purdue Model compliance

---

## 🚀 Quick Start Commands

### Direct Internet Deployment
```bash
curl -sSL https://install.insa-automation.com/agent.sh | sudo bash -s -- \
  --api-key "YOUR_API_KEY" \
  --client-id "client_yourcompany" \
  --scenario direct
```

### Corporate Proxy Deployment
```bash
curl -sSL https://install.insa-automation.com/agent.sh | sudo bash -s -- \
  --api-key "YOUR_API_KEY" \
  --client-id "client_yourcompany" \
  --scenario proxy \
  --proxy-url "http://proxy.corp.com:8080"
```

### OT Gateway Deployment
```bash
curl -sSL https://install.insa-automation.com/agent.sh | sudo bash -s -- \
  --api-key "YOUR_API_KEY" \
  --client-id "client_yourcompany" \
  --scenario ot-gateway \
  --gateway-host "172.16.0.10" \
  --gateway-port "8443"
```

---

## 🏗️ Architecture Overview

### Scenario 1: Direct Internet
```
[Agent] → [Firewall] → [Internet] → [Insa Cloud]
```
**Use**: SMBs, cloud-native companies
**Latency**: <100ms

### Scenario 2: Corporate Proxy
```
[Agent] → [Proxy] → [Firewall] → [Internet] → [Insa Cloud]
```
**Use**: Enterprises with strict egress filtering
**Latency**: 100-500ms

### Scenario 3: IT/OT Gateway
```
[OT Agent] → [Gateway DMZ] → [Firewall] → [Internet] → [Insa Cloud]
```
**Use**: Manufacturing, utilities, critical infrastructure
**Latency**: Variable (5-min batches)

---

## 📦 Agent Components

```yaml
Core Modules:
  - Wazuh Agent (FIM, log analysis, rootkit detection)
  - Trivy Scanner (container/filesystem vulnerabilities)
  - Nmap (network discovery, port scanning)
  - Log Collector (syslog, JSON, multi-source)

Resource Footprint:
  Binary: 48 MB (compressed), 75 MB (installed)
  CPU: <1% idle, <5% average, 20% peak
  Memory: 25 MB idle, <50 MB average
  Disk: 200 MB total
  Network: 1 KB/min idle, 100 KB/min average
```

---

## 🔐 Security Features

```yaml
Transport:
  - TLS 1.3 (AES-256-GCM)
  - mTLS client certificates
  - Certificate pinning

Authentication:
  - API key (Bearer token)
  - Client certificate (mTLS)
  - Gateway token (OT)

Data Protection:
  - Encrypted in transit (TLS)
  - Encrypted at rest (AES-256)
  - PII filtering
  - Log sanitization
```

---

## 🛠️ Platform Support

### Operating Systems
- ✅ Ubuntu 20.04+ (x86_64, ARM64)
- ✅ Debian 10+ (x86_64, ARM64)
- ✅ RHEL/CentOS 7+ (x86_64)
- ✅ Rocky Linux 8+ (x86_64)
- ✅ Windows Server 2016+ (x86_64)
- ✅ Windows 10/11 (x86_64)
- ✅ macOS 11+ (x86_64, ARM64)

### Containers
- ✅ Docker 20.10+
- ✅ Podman 3.0+
- ✅ Kubernetes 1.20+

---

## 🏭 Industrial (OT) Platforms

| Vendor | Product | Support |
|--------|---------|---------|
| Siemens | SIMATIC | ✅ Full |
| Rockwell | ControlLogix | ✅ Full |
| Schneider | Modicon | ✅ Full |
| ABB | AC 800M | ✅ Full |
| Honeywell | Experion | ✅ Full |

---

## 🔧 Common Commands

### Check Agent Status
```bash
# Linux
sudo systemctl status insa-agent
sudo journalctl -u insa-agent -f

# Windows
Get-Service -Name "InsaAgent"
Get-Content "C:\Program Files\Insa\Agent\logs\agent.log" -Tail 50 -Wait

# Docker
docker logs -f insa-agent

# Kubernetes
kubectl logs -n insa-agent -l app=insa-agent -f
```

### Test Connectivity
```bash
# Direct
sudo insa-agent test-connection

# Proxy
sudo insa-agent test-connection --proxy http://proxy.corp.com:8080

# Gateway
sudo insa-agent test-connection --gateway 172.16.0.10:8443
```

### Verify Registration
```bash
sudo insa-agent status
```

---

## 🐛 Troubleshooting

### Agent Won't Start
```bash
# Check logs
sudo journalctl -u insa-agent -n 100 --no-pager

# Verify API key
sudo cat /etc/insa-agent/config.yaml | grep api_key

# Test connectivity
curl -v https://api.insa-automation.com/v2/health
```

### Proxy Connection Issues
```bash
# Test proxy
curl -v --proxy http://proxy.corp.com:8080 https://api.insa-automation.com/v2/health

# Check SSL inspection
openssl s_client -connect api.insa-automation.com:443 -showcerts -proxy proxy.corp.com:8080
```

### Gateway Issues
```bash
# Test OT → Gateway
ping 192.168.100.254
curl -k https://192.168.100.254:8443/health

# Check gateway logs
sudo journalctl -u insa-gateway | grep ERROR

# Check buffer
sudo -u postgres psql -d insa_gateway_buffer -c "SELECT COUNT(*) FROM findings_buffer WHERE forwarded = FALSE;"
```

---

## 📞 Support

- **Documentation**: https://docs.insa-automation.com
- **Support Portal**: https://support.insa-automation.com
- **Email**: support@insa-automation.com
- **OT Support**: ot-support@insa-automation.com
- **Emergency**: +1 (555) 123-4567 (24/7)

---

## 📋 Firewall Rules (Quick Reference)

### Direct Internet
```bash
# Allow outbound HTTPS to Insa API
iptables -A OUTPUT -p tcp -d api.insa-automation.com --dport 443 -j ACCEPT
iptables -A OUTPUT -p tcp -d updates.insa-automation.com --dport 443 -j ACCEPT
```

### OT → DMZ
```bash
# Allow OT agents to gateway
iptables -A FORWARD -s 192.168.100.0/24 -d 172.16.0.10 -p tcp --dport 8443 -j ACCEPT

# DENY ALL DMZ → OT (data diode)
iptables -A FORWARD -s 172.16.0.0/24 -d 192.168.100.0/24 -j DROP
```

### DMZ → Internet
```bash
# Allow gateway to cloud
iptables -A FORWARD -s 172.16.0.10 -d api.insa-automation.com -p tcp --dport 443 -j ACCEPT
iptables -A FORWARD -s 172.16.0.10 -d updates.insa-automation.com -p tcp --dport 443 -j ACCEPT
```

---

## 📁 File Locations

### Linux
```
/opt/insa-agent/                    # Agent binary
/etc/insa-agent/config.yaml         # Configuration
/var/log/insa-agent/agent.log       # Logs
/var/lib/insa-agent/cache/          # Offline cache
/etc/systemd/system/insa-agent.service  # Systemd service
```

### Windows
```
C:\Program Files\Insa\Agent\        # Agent binary
C:\Program Files\Insa\Agent\config.yaml  # Configuration
C:\Program Files\Insa\Agent\logs\agent.log  # Logs
C:\ProgramData\Insa\Agent\cache\    # Offline cache
```

### Gateway (DMZ)
```
/opt/insa-gateway/                  # Gateway binary
/etc/insa-gateway/config.yaml       # Configuration
/etc/insa-gateway/certs/            # mTLS certificates
/var/log/insa-gateway/gateway.log   # Logs
/var/lib/insa-gateway/db/           # PostgreSQL buffer
```

---

**Made by Insa Automation Corp for OpSec**

**Document**: AGENT_QUICK_REFERENCE.md
**Last Updated**: 2025-10-11
