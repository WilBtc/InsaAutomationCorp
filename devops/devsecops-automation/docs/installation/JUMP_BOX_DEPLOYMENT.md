# Jump Box Deployment Guide

**Insa Automation Corp - DevSecOps Platform**
**Version**: 1.0
**Last Updated**: October 11, 2025
**Purpose**: Step-by-step jump box installation and configuration for customer DMZ

---

## Overview

The **Insa Jump Box** is the secure relay between customer OT/IT assets and the Insa SOC platform. It sits in the customer's DMZ and acts as:
- **Agent relay**: Collects telemetry from customer agents
- **TLS termination**: Encrypts data before sending to Insa SOC
- **Local cache**: Stores up to 7 days of data if WAN link fails
- **Protocol translator**: Normalizes data formats for DefectDojo

### Jump Box Architecture
```
[Customer Assets] --> [Agents] --> [Jump Box (DMZ)] --> [Internet] --> [Insa SOC Platform]
                                         ↓
                                   [Local Cache]
                                   (7-day buffer)
```

**Deployment Time**: 2-3 hours
**Requires**: Physical access to customer data center, network port in DMZ, firewall rules

---

## 1. Pre-Deployment Preparation

### 1.1 Customer Network Information (Collect Before Arrival)
- [ ] DMZ VLAN ID: _____________
- [ ] Available IP address for jump box: _____________
- [ ] Subnet mask: _____________
- [ ] Default gateway: _____________
- [ ] DNS servers (primary, secondary): _____________, _____________
- [ ] NTP server (if not internet-accessible): _____________
- [ ] Switch port number in DMZ: _____________
- [ ] Firewall rules approved? (Yes/No): _____

### 1.2 Firewall Rules Required

**Inbound to Jump Box** (from customer network):
| Source | Destination | Port | Protocol | Purpose |
|--------|-------------|------|----------|---------|
| Any agent subnet | Jump box IP | 8443 | TCP | Agent telemetry (HTTPS) |
| Customer IT subnet | Jump box IP | 22 | TCP | SSH management |
| Customer IT subnet | Jump box IP | 443 | TCP | Local web UI (optional) |

**Outbound from Jump Box** (to internet):
| Source |DestinationFirewall | Port | Protocol | Purpose |
|--------|------------|------|----------|---------|
| Jump box IP | 100.100.101.1 | 8082 | TCP | DefectDojo API (Insa SOC) |
| Jump box IP | 100.100.101.1 | 22 | TCP | Reverse SSH tunnel (optional) |
| Jump box IP | Any NTP server | 123 | UDP | Time sync (critical) |
| Jump box IP | Any DNS server | 53 | UDP | DNS lookups |
| Jump box IP | Any | 80, 443 | TCP | Software updates (Ubuntu apt) |

**Critical**: NTP must work. SIEM correlation requires accurate timestamps.

### 1.3 TLS Certificates (Generate Before Arrival)
```bash
# On Insa admin workstation (before deployment)
cd ~/deployment-prep/[customer-name]

# Generate CA-signed certificate for jump box
openssl req -new -newkey rsa:4096 -nodes \
  -keyout jumpbox.key \
  -out jumpbox.csr \
  -subj "/C=US/ST=State/L=City/O=Insa Automation Corp/OU=SOC/CN=insa-jumpbox-[customer]"

# Send CSR to Insa CA for signing (or use Let's Encrypt if public IP)
# Receive back: jumpbox.crt, ca-bundle.crt

# Copy to USB drive for deployment
cp jumpbox.key jumpbox.crt ca-bundle.crt /media/usb/certificates/
```

### 1.4 Jump Box Hardware Checklist
- [ ] Dell PowerEdge R240 (or equivalent 1U/2U server)
- [ ] Pre-installed OS: Ubuntu 22.04 LTS
- [ ] Hostname: `insa-jumpbox-template` (will rename on-site)
- [ ] Default credentials: `insaadmin` / `ChangeMe123!` (will change on-site)
- [ ] Serial number recorded: _____________
- [ ] POST test passed: (Yes/No): _____

---

## 2. Physical Installation

### 2.1 Rack Mounting
**Time**: 15-20 minutes

1. **Verify rack space**:
   - [ ] Locate 2U of available space in customer rack
   - [ ] Verify clearance for cables (rear)
   - [ ] Check ambient temperature (< 85°F / 30°C)
   - [ ] Verify rack is grounded

2. **Mount server**:
   - [ ] Attach rail kit to rack (if not already installed)
   - [ ] Slide jump box into rails
   - [ ] Secure with 4x screws (2 per side)
   - [ ] Verify server is level and secure

3. **Cable management**:
   - [ ] Route power cable through cable management arm
   - [ ] Route network cables through cable management
   - [ ] Use Velcro ties (not zip ties) for flexibility
   - [ ] Leave 6" of slack for serviceability
   - [ ] Label all cables: "Insa Jump Box - [Customer]"

### 2.2 Network Connectivity
**Time**: 10 minutes

1. **Connect to DMZ switch**:
   - [ ] Plug Cat6 cable into NIC1 (primary network interface)
   - [ ] Verify link light on NIC and switch
   - [ ] Document switch port number: _____________
   - [ ] Document VLAN: _____________

2. **Optional: Redundant network** (if customer has dual switches):
   - [ ] Plug second Cat6 cable into NIC2
   - [ ] Configure bonding (active/passive) later in OS

3. **Console access**:
   - [ ] Connect console cable (RJ45 or USB) to laptop
   - [ ] Open terminal: `screen /dev/ttyUSB0 115200` (Linux) or PuTTY (Windows)
   - [ ] Verify console output visible

### 2.3 Power Connection
**Time**: 5 minutes

1. **Connect power**:
   - [ ] Plug power cable into PDU (UPS-backed preferred)
   - [ ] Do NOT power on yet (will do in next section)
   - [ ] Document PDU port: _____________

2. **Optional: Redundant PSU** (if jump box has dual PSUs):
   - [ ] Connect second power cable to different PDU/circuit
   - [ ] Verify redundancy later after boot

---

## 3. Initial OS Configuration

### 3.1 First Boot
**Time**: 10 minutes

1. **Power on**:
   - [ ] Press power button on jump box
   - [ ] Watch POST via console
   - [ ] Verify no hardware errors (beep codes, red LEDs)
   - [ ] Wait for login prompt (~60 seconds)

2. **Login**:
   ```bash
   # Via console
   Username: insaadmin
   Password: ChangeMe123!
   ```

3. **Verify boot**:
   ```bash
   # Check uptime
   uptime

   # Check disk space
   df -h

   # Check network interfaces detected
   ip link show
   ```

### 3.2 Network Configuration
**Time**: 15 minutes

1. **Set static IP** (preferred for servers):
   ```bash
   # Edit netplan config
   sudo nano /etc/netplan/01-netcfg.yaml
   ```

   **Configuration**:
   ```yaml
   network:
     version: 2
     ethernets:
       eno1:  # Primary NIC (verify with 'ip link')
         addresses:
           - [CUSTOMER_IP]/[SUBNET_MASK]  # e.g., 192.168.100.50/24
         gateway4: [CUSTOMER_GATEWAY]     # e.g., 192.168.100.1
         nameservers:
           addresses:
             - [DNS1]                      # e.g., 8.8.8.8
             - [DNS2]                      # e.g., 8.8.4.4
         dhcp4: no
       eno2:  # Secondary NIC (if used for redundancy)
         dhcp4: no
   ```

2. **Apply network config**:
   ```bash
   sudo netplan apply

   # Verify IP assigned
   ip addr show eno1

   # Test connectivity
   ping -c 4 [CUSTOMER_GATEWAY]
   ping -c 4 8.8.8.8
   ping -c 4 google.com  # Tests DNS
   ```

3. **Set hostname**:
   ```bash
   # Set hostname to customer-specific value
   sudo hostnamectl set-hostname insa-jumpbox-[customer-abbreviation]

   # Example: sudo hostnamectl set-hostname insa-jumpbox-acme

   # Verify
   hostname
   ```

4. **Configure NTP** (CRITICAL for SIEM):
   ```bash
   # Check current time sync status
   timedatectl status

   # If customer has internal NTP server
   sudo nano /etc/systemd/timesyncd.conf
   ```

   **Configuration**:
   ```ini
   [Time]
   NTP=[CUSTOMER_NTP_SERVER]  # e.g., 192.168.1.10
   FallbackNTP=pool.ntp.org   # Internet fallback
   ```

   ```bash
   # Restart time sync
   sudo systemctl restart systemd-timesyncd

   # Verify
   timedatectl status
   # Should show: "System clock synchronized: yes"
   ```

### 3.3 Security Hardening
**Time**: 20 minutes

1. **Change default password**:
   ```bash
   # Generate strong random password
   sudo apt install pwgen -y
   pwgen 24 1

   # Change password for insaadmin
   passwd
   # Enter new password (record in customer vault)

   # Disable root login
   sudo passwd -l root
   ```

2. **Configure SSH**:
   ```bash
   # Generate SSH key for Insa remote support (optional)
   ssh-keygen -t ed25519 -C "insa-support@insaing.com" -f ~/.ssh/insa_support

   # Harden SSH config
   sudo nano /etc/ssh/sshd_config
   ```

   **Key settings**:
   ```bash
   PermitRootLogin no
   PasswordAuthentication yes  # Change to 'no' after key-based auth tested
   PubkeyAuthentication yes
   AllowUsers insaadmin
   ClientAliveInterval 300
   ClientAliveCountMax 2
   MaxAuthTries 3
   ```

   ```bash
   # Restart SSH
   sudo systemctl restart sshd

   # Test SSH from your laptop (open new terminal, DO NOT close console yet)
   ssh insaadmin@[JUMP_BOX_IP]
   ```

3. **Configure firewall (UFW)**:
   ```bash
   # Enable UFW
   sudo ufw enable

   # Allow SSH from customer IT subnet only
   sudo ufw allow from [CUSTOMER_IT_SUBNET] to any port 22 proto tcp
   # Example: sudo ufw allow from 192.168.10.0/24 to any port 22 proto tcp

   # Allow agent connections from customer asset subnets
   sudo ufw allow from [CUSTOMER_OT_SUBNET] to any port 8443 proto tcp
   sudo ufw allow from [CUSTOMER_IT_SUBNET] to any port 8443 proto tcp

   # Allow outbound (default allow, just document)
   sudo ufw default allow outgoing

   # Deny all other inbound
   sudo ufw default deny incoming

   # Verify rules
   sudo ufw status verbose
   ```

4. **Enable automatic security updates**:
   ```bash
   sudo apt install unattended-upgrades -y
   sudo dpkg-reconfigure -plow unattended-upgrades
   # Select 'Yes' when prompted
   ```

---

## 4. Jump Box Software Installation

### 4.1 Install Dependencies
**Time**: 15 minutes

```bash
# Update package lists
sudo apt update

# Install required packages
sudo apt install -y \
  python3 python3-pip python3-venv \
  docker.io docker-compose \
  postgresql-client \
  sqlite3 \
  curl wget git \
  htop iotop nethogs \
  tmux screen \
  jq \
  net-tools

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add insaadmin to docker group (to run docker without sudo)
sudo usermod -aG docker insaadmin

# Log out and back in for group to take effect
exit
# (SSH back in)
```

### 4.2 Install Jump Box Software
**Time**: 20 minutes

1. **Copy installer from USB**:
   ```bash
   # Mount USB drive
   sudo mkdir -p /mnt/usb
   sudo mount /dev/sdb1 /mnt/usb  # Adjust device as needed

   # Copy installer
   cp /mnt/usb/jumpbox/software/insa-jumpbox-setup-3.1.2.tar.gz ~/
   cd ~
   tar -xzf insa-jumpbox-setup-3.1.2.tar.gz
   cd insa-jumpbox-setup-3.1.2/
   ```

2. **Run installer**:
   ```bash
   sudo ./install.sh
   ```

   **Installer prompts**:
   - Customer name: `[Enter customer abbreviation]`
   - Jump box hostname: `[Auto-detected from system]`
   - Insa SOC platform URL: `https://100.100.101.1:8082`
   - Agent listening port: `8443` (default)
   - Enable local cache: `yes` (recommended)
   - Cache retention days: `7` (default)

3. **Verify installation**:
   ```bash
   # Check services installed
   sudo systemctl list-units | grep insa

   # Should see:
   # - insa-agent-relay.service
   # - insa-cache-manager.service
   # - insa-heartbeat.service
   ```

### 4.3 Install TLS Certificates
**Time**: 10 minutes

1. **Copy certificates from USB**:
   ```bash
   sudo mkdir -p /etc/insa/certs
   sudo cp /mnt/usb/certificates/jumpbox.key /etc/insa/certs/
   sudo cp /mnt/usb/certificates/jumpbox.crt /etc/insa/certs/
   sudo cp /mnt/usb/certificates/ca-bundle.crt /etc/insa/certs/

   # Set permissions
   sudo chown root:root /etc/insa/certs/*
   sudo chmod 600 /etc/insa/certs/jumpbox.key
   sudo chmod 644 /etc/insa/certs/jumpbox.crt
   sudo chmod 644 /etc/insa/certs/ca-bundle.crt

   # Unmount USB
   sudo umount /mnt/usb
   ```

2. **Configure jump box to use certificates**:
   ```bash
   sudo nano /etc/insa/jumpbox.conf
   ```

   **Update certificate paths**:
   ```ini
   [TLS]
   certificate = /etc/insa/certs/jumpbox.crt
   private_key = /etc/insa/certs/jumpbox.key
   ca_bundle = /etc/insa/certs/ca-bundle.crt
   verify_client_certs = yes
   ```

3. **Restart services**:
   ```bash
   sudo systemctl restart insa-agent-relay
   sudo systemctl restart insa-heartbeat

   # Check status
   sudo systemctl status insa-agent-relay
   sudo systemctl status insa-heartbeat
   ```

### 4.4 Configure Jump Box Settings
**Time**: 15 minutes

1. **Edit main configuration**:
   ```bash
   sudo nano /etc/insa/jumpbox.conf
   ```

   **Key configuration sections**:
   ```ini
   [General]
   customer_name = [Customer Abbreviation]
   deployment_date = [YYYY-MM-DD]
   jump_box_id = [Generate: uuidgen]

   [Network]
   agent_listen_port = 8443
   agent_listen_interface = 0.0.0.0  # All interfaces
   soc_platform_url = https://100.100.101.1:8082
   soc_api_endpoint = /api/v2/jumpbox/telemetry
   heartbeat_interval = 60  # seconds

   [Cache]
   enabled = yes
   storage_path = /var/lib/insa/cache
   max_retention_days = 7
   max_storage_gb = 50
   compression = gzip

   [Monitoring]
   enable_self_monitoring = yes
   log_level = INFO
   log_path = /var/log/insa/jumpbox.log
   metrics_port = 9090  # Prometheus metrics

   [Security]
   enforce_tls = yes
   min_tls_version = 1.2
   agent_authentication = psk  # Pre-shared key
   psk_rotation_days = 90
   ```

2. **Generate agent pre-shared key (PSK)**:
   ```bash
   # Generate strong PSK
   openssl rand -base64 32 | sudo tee /etc/insa/agent_psk.key
   sudo chmod 600 /etc/insa/agent_psk.key

   # Record PSK (will need for agent configuration)
   cat /etc/insa/agent_psk.key
   # Copy to deployment notes
   ```

3. **Create cache storage**:
   ```bash
   sudo mkdir -p /var/lib/insa/cache
   sudo chown insaadmin:insaadmin /var/lib/insa/cache
   sudo chmod 755 /var/lib/insa/cache
   ```

4. **Restart all services**:
   ```bash
   sudo systemctl restart insa-agent-relay
   sudo systemctl restart insa-cache-manager
   sudo systemctl restart insa-heartbeat

   # Enable services to start on boot
   sudo systemctl enable insa-agent-relay
   sudo systemctl enable insa-cache-manager
   sudo systemctl enable insa-heartbeat
   ```

---

## 5. Testing and Validation

### 5.1 Local Health Checks
**Time**: 15 minutes

1. **Verify services running**:
   ```bash
   sudo systemctl status insa-agent-relay
   sudo systemctl status insa-cache-manager
   sudo systemctl status insa-heartbeat

   # All should show: "active (running)"
   ```

2. **Check listening ports**:
   ```bash
   sudo ss -tlnp | grep insa

   # Should see:
   # 0.0.0.0:8443  (agent relay)
   # 127.0.0.1:9090 (metrics)
   ```

3. **Test TLS certificate**:
   ```bash
   # From jump box
   openssl s_client -connect localhost:8443 -showcerts

   # Verify:
   # - Certificate CN matches hostname
   # - Certificate not expired
   # - No SSL errors
   ```

4. **Check logs**:
   ```bash
   sudo journalctl -u insa-agent-relay -n 50 --no-pager
   sudo journalctl -u insa-heartbeat -n 50 --no-pager

   # Look for:
   # - "Agent relay started successfully"
   # - "Heartbeat sent to SOC platform"
   # - No ERROR messages
   ```

5. **Check cache storage**:
   ```bash
   ls -lh /var/lib/insa/cache/
   df -h /var/lib/insa/cache/

   # Should show:
   # - Directory created
   # - Minimal usage initially (will grow as agents connect)
   ```

### 5.2 Network Connectivity Tests
**Time**: 10 minutes

1. **Test outbound to Insa SOC**:
   ```bash
   # Test TLS connection to DefectDojo
   curl -v https://100.100.101.1:8082/api/v2/status

   # Should return: {"status": "ok", "version": "2.4.1"}
   ```

2. **Test from customer IT subnet** (use laptop on customer network):
   ```bash
   # From your laptop
   curl -k https://[JUMP_BOX_IP]:8443/health

   # Should return: {"status": "healthy", "uptime": "..."}
   ```

3. **Test NTP sync**:
   ```bash
   timedatectl status

   # Verify:
   # - "System clock synchronized: yes"
   # - "NTP service: active"
   ```

4. **Test DNS resolution**:
   ```bash
   nslookup google.com
   nslookup 100.100.101.1

   # Should resolve without errors
   ```

### 5.3 Integration Test with Insa SOC
**Time**: 10 minutes

1. **Verify jump box registered with SOC**:
   ```bash
   # Check heartbeat logs
   sudo journalctl -u insa-heartbeat -f

   # Should see periodic logs every 60 seconds:
   # "Heartbeat sent successfully"
   ```

2. **Check DefectDojo for jump box**:
   - Login to DefectDojo: https://100.100.101.1:8082
   - Navigate to: **Configuration > Jump Boxes**
   - Verify new jump box appears with:
     - Customer name
     - Jump box ID
     - Status: "Online"
     - Last heartbeat: < 2 minutes ago

3. **Test alert routing**:
   ```bash
   # Trigger test alert from jump box
   sudo /opt/insa/bin/send-test-alert.sh

   # Check DefectDojo
   # - Navigate to: Findings
   # - Look for: "Test Alert from Jump Box"
   # - Should appear within 5 minutes
   ```

---

## 6. Documentation and Handoff

### 6.1 Record Jump Box Details
**Time**: 10 minutes

**Fill in customer deliverables binder** (Tab 3: Jump Box):
- Hostname: `insa-jumpbox-[customer]`
- IP Address: `[Jump box IP]`
- Subnet/VLAN: `[Network details]`
- Gateway: `[Gateway IP]`
- DNS Servers: `[DNS IPs]`
- Rack Location: `[Rack # / U position]`
- Power: PDU port `[Port #]`
- Network: Switch `[Name]` port `[#]`
- Serial Number: `[From hardware]`
- Installation Date: `[YYYY-MM-DD]`
- Installed By: `[Your name]`

**Credentials** (place in sealed envelope):
- SSH Username: `insaadmin`
- SSH Password: `[New password from step 3.3]`
- SSH Key: `[If generated, public key]`
- Agent PSK: `[From step 4.4.2]`

### 6.2 Create Jump Box Diagram
**Time**: 5 minutes

Draw network diagram showing:
- Jump box location in DMZ
- Connections to customer switch
- Firewall rules (numbered)
- Connection to Insa SOC (over internet)
- Agent subnets that will connect

**Include in customer binder** (Tab 2: Network Documentation).

### 6.3 Jump Box Monitoring Setup
**Time**: 5 minutes

1. **Enable self-monitoring agent**:
   ```bash
   # Install monitoring agent on jump box itself
   sudo /opt/insa/agents/install-self-monitor.sh

   # Verify agent running
   sudo systemctl status insa-self-monitor
   ```

2. **Configure alerts for jump box health**:
   - CPU > 80%
   - Memory > 90%
   - Disk > 80%
   - Service down
   - Heartbeat missed (3x consecutive)

---

## 7. Common Issues and Troubleshooting

### Issue: Jump box cannot reach Insa SOC platform
**Symptoms**: Heartbeat logs show connection errors
**Causes**:
- Firewall blocking outbound traffic
- Incorrect SOC platform URL
- TLS certificate mismatch

**Resolution**:
```bash
# Test basic connectivity
ping 100.100.101.1

# Test port 8082 reachable
nc -zv 100.100.101.1 8082

# Test TLS handshake
openssl s_client -connect 100.100.101.1:8082

# Check logs for specific error
sudo journalctl -u insa-heartbeat -n 100 | grep ERROR

# Common fix: Verify firewall rules with customer NetSec
```

### Issue: Agents cannot connect to jump box
**Symptoms**: Agent logs show "Connection refused" or "Timeout"
**Causes**:
- Jump box firewall (UFW) blocking agent subnet
- Network routing issue
- Jump box service not listening

**Resolution**:
```bash
# Verify service listening
sudo ss -tlnp | grep 8443

# Check UFW rules
sudo ufw status verbose

# Add agent subnet if missing
sudo ufw allow from [AGENT_SUBNET] to any port 8443 proto tcp

# Test from agent machine
curl -k https://[JUMP_BOX_IP]:8443/health
```

### Issue: Time sync failing
**Symptoms**: Timedatectl shows "System clock synchronized: no"
**Causes**:
- NTP server unreachable
- Firewall blocking UDP 123
- Incorrect NTP server configured

**Resolution**:
```bash
# Test NTP connectivity
sudo ntpdate -q [NTP_SERVER]

# Check firewall
sudo ufw allow out 123/udp

# Restart time sync
sudo systemctl restart systemd-timesyncd

# Verify
timedatectl status
```

### Issue: Certificate errors
**Symptoms**: TLS handshake fails, agents reject jump box certificate
**Causes**:
- Expired certificate
- Hostname mismatch
- Missing CA bundle

**Resolution**:
```bash
# Check certificate expiration
openssl x509 -in /etc/insa/certs/jumpbox.crt -noout -dates

# Check certificate CN
openssl x509 -in /etc/insa/certs/jumpbox.crt -noout -subject

# Verify CA bundle
openssl verify -CAfile /etc/insa/certs/ca-bundle.crt /etc/insa/certs/jumpbox.crt

# If expired, generate new certificate (contact Insa ops)
```

### Issue: Jump box running out of disk space
**Symptoms**: Cache full, logs show disk space errors
**Causes**:
- Agents sending too much data
- Cache not rotating properly
- Logs growing too large

**Resolution**:
```bash
# Check disk usage
df -h
du -sh /var/lib/insa/cache
du -sh /var/log/insa

# Manually purge old cache (if cache manager fails)
sudo /opt/insa/bin/purge-cache.sh --older-than 7d

# Rotate logs
sudo logrotate -f /etc/logrotate.d/insa

# Increase cache retention cleanup frequency
sudo nano /etc/insa/jumpbox.conf
# Set: cache_cleanup_interval = 3600  (hourly instead of daily)
```

---

## 8. Maintenance Procedures

### 8.1 Software Updates
**Frequency**: Monthly (or as needed for security patches)

```bash
# SSH to jump box
ssh insaadmin@[JUMP_BOX_IP]

# Update OS packages
sudo apt update
sudo apt upgrade -y

# Update Insa jump box software
cd /opt/insa
sudo ./update.sh

# Restart services
sudo systemctl restart insa-agent-relay
sudo systemctl restart insa-cache-manager
sudo systemctl restart insa-heartbeat

# Verify health
sudo systemctl status insa-agent-relay
```

### 8.2 Certificate Renewal
**Frequency**: Annually (or 30 days before expiration)

```bash
# Generate new CSR
sudo openssl req -new -key /etc/insa/certs/jumpbox.key -out /tmp/jumpbox-renewal.csr

# Send CSR to Insa ops for signing
# Receive new certificate

# Install new certificate
sudo cp jumpbox-new.crt /etc/insa/certs/jumpbox.crt
sudo systemctl restart insa-agent-relay

# Verify
openssl x509 -in /etc/insa/certs/jumpbox.crt -noout -dates
```

### 8.3 Cache Cleanup (Manual)
**Frequency**: As needed if automatic cleanup fails

```bash
# Check cache size
du -sh /var/lib/insa/cache

# Stop cache manager (to avoid conflicts)
sudo systemctl stop insa-cache-manager

# Purge data older than 7 days
sudo find /var/lib/insa/cache -type f -mtime +7 -delete

# Restart cache manager
sudo systemctl start insa-cache-manager
```

### 8.4 Log Rotation
**Frequency**: Automatic (daily), manual if needed

```bash
# Force log rotation
sudo logrotate -f /etc/logrotate.d/insa

# View current log sizes
du -sh /var/log/insa/*

# Archive old logs to external storage (if needed)
sudo tar -czf insa-logs-$(date +%Y%m%d).tar.gz /var/log/insa
# Transfer to customer backup or Insa storage
```

---

## 9. Jump Box Decommissioning

**See**: `ROLLBACK_PROCEDURE.md` for complete decommissioning steps.

**Quick checklist**:
1. Notify all agents to stop sending data (or uninstall agents first)
2. Drain local cache to SOC platform
3. Shut down services
4. Export configuration and logs for archive
5. Uninstall software
6. Wipe disk (DBAN or similar)
7. Remove from rack
8. Return to Insa or repurpose

---

## Appendix A: Jump Box Specifications

### Hardware Requirements (Minimum)
- **CPU**: Quad-core x86_64 (Intel Xeon or AMD EPYC)
- **RAM**: 16GB DDR4 ECC
- **Storage**: 512GB NVMe SSD (for OS + cache)
- **Network**: 2x 1Gbps Ethernet (primary + backup)
- **Form Factor**: 1U or 2U rack mount
- **Power**: Redundant PSU preferred
- **IPMI/iLO**: Remote management (optional but recommended)

### Software Stack
- **OS**: Ubuntu 22.04 LTS (with security updates)
- **Runtime**: Python 3.10+
- **Database**: SQLite (local cache)
- **Containerization**: Docker 24.0+ (for microservices)
- **Monitoring**: Prometheus node exporter
- **Log Shipping**: Filebeat or Fluentd

### Performance Targets
- **Throughput**: 1,000 agents @ 1KB/min each = 1MB/min sustained
- **Latency**: < 100ms agent-to-jump box, < 500ms jump box-to-SOC
- **Availability**: 99.9% uptime (8.76 hours downtime/year)
- **Cache**: 7 days @ 1MB/min = ~10GB storage needed

---

## Appendix B: Quick Reference Commands

### Service Management
```bash
# Status
sudo systemctl status insa-agent-relay
sudo systemctl status insa-cache-manager
sudo systemctl status insa-heartbeat

# Restart
sudo systemctl restart insa-agent-relay

# Logs (live tail)
sudo journalctl -u insa-agent-relay -f

# Logs (last 100 lines)
sudo journalctl -u insa-agent-relay -n 100 --no-pager
```

### Monitoring
```bash
# CPU and memory
htop

# Network traffic
nethogs

# Disk I/O
iotop

# Listening ports
sudo ss -tlnp

# Connected agents
sudo netstat -an | grep 8443 | grep ESTABLISHED | wc -l
```

### Configuration Paths
```bash
/etc/insa/jumpbox.conf        # Main config
/etc/insa/certs/              # TLS certificates
/etc/insa/agent_psk.key       # Agent pre-shared key
/var/lib/insa/cache/          # Local cache storage
/var/log/insa/                # Logs
/opt/insa/                    # Software installation
```

---

**Document Version**: 1.0
**Last Updated**: October 11, 2025
**Owner**: Insa Automation Corp
**Classification**: Internal Use - Field Technicians Only

---

*Made by Insa Automation Corp for OpSec Excellence*
