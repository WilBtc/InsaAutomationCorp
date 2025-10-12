# Agent Deployment Checklist

**Insa Automation Corp - DevSecOps Platform**
**Version**: 1.0
**Last Updated**: October 11, 2025
**Purpose**: Step-by-step agent installation per OS and validation procedures

---

## Overview

This checklist guides field technicians through agent deployment across customer IT/OT assets. Agents are lightweight monitoring software that:
- Collect system telemetry (CPU, memory, disk, network)
- Monitor security events (logins, file changes, process starts)
- Scan for vulnerabilities and compliance violations
- Report to jump box in customer DMZ

**Target Performance**: < 5% CPU, < 100MB RAM per agent

---

## Pre-Deployment Planning

### 1. Asset Inventory Validation
**Time**: 30 minutes (before Day 2)

1. **Review customer asset list**:
   - [ ] Total assets to monitor: _______
   - [ ] Windows systems: _______
   - [ ] Linux systems: _______
   - [ ] Embedded/IoT devices: _______
   - [ ] Network devices (SNMP only): _______

2. **Prioritize deployment order**:
   - **Tier 1** (deploy first - lowest risk):
     - [ ] IT workstations
     - [ ] IT file servers
     - [ ] Non-production test systems
   - **Tier 2** (deploy second - moderate risk):
     - [ ] Production IT servers (web, database, email)
     - [ ] Engineering workstations (OT)
   - **Tier 3** (deploy last - highest risk):
     - [ ] HMI/SCADA servers
     - [ ] Historian servers
     - [ ] OPC servers
     - [ ] IIoT gateways

3. **Identify safety systems to EXCLUDE**:
   **See**: `SAFETY_SYSTEM_EXCLUSION.md`
   - [ ] Safety PLCs (DO NOT TOUCH)
   - [ ] Emergency shutdown systems (ESD)
   - [ ] Fire and gas detection systems
   - [ ] Safety instrumented systems (SIS)
   - [ ] Any system with SIL rating (SIL 1/2/3/4)
   - [ ] Burner management systems (BMS)

4. **Gather credentials**:
   - [ ] Windows domain admin (for Group Policy deployment)
   - [ ] Local admin for each system (if no domain)
   - [ ] SSH keys or root password for Linux systems
   - [ ] Jump box PSK (from `JUMP_BOX_DEPLOYMENT.md` step 4.4.2)

### 2. Configuration Template Preparation
**Time**: 15 minutes

1. **Create agent config file** (will use for all deployments):
   ```bash
   # On your laptop
   cd ~/deployment/[customer-name]
   cp /mnt/usb/agents/config-templates/agent.conf.template agent.conf

   # Edit with customer-specific settings
   nano agent.conf
   ```

2. **Key configuration parameters**:
   ```ini
   [General]
   customer_id = [Customer abbreviation]
   deployment_id = [Deployment date YYYYMMDD]

   [JumpBox]
   server = [Jump box IP]:8443
   protocol = https
   verify_tls = yes
   ca_bundle = /etc/insa-agent/ca-bundle.crt

   [Authentication]
   method = psk
   psk = [Pre-shared key from jump box]

   [Telemetry]
   interval = 60  # seconds (how often to send data)
   metrics = cpu,memory,disk,network,processes
   log_forwarding = yes

   [Security]
   file_integrity_monitoring = yes
   fim_paths = /etc,/usr/bin,/usr/sbin,/opt  # Linux
   # fim_paths = C:\Windows\System32,C:\Program Files  # Windows

   vulnerability_scanning = yes
   scan_interval = 86400  # daily

   compliance_frameworks = cis_benchmark
   # Options: cis_benchmark, nerc_cip, fda_21cfr11, isa62443

   [Performance]
   cpu_limit = 5  # Max 5% CPU usage
   memory_limit = 100  # Max 100MB RAM

   [Logging]
   level = INFO
   local_log = /var/log/insa-agent.log  # Linux
   # local_log = C:\ProgramData\Insa\agent.log  # Windows
   ```

3. **Copy config to USB drive** (for easy deployment):
   ```bash
   cp agent.conf /mnt/usb/agents/agent-[customer].conf
   ```

---

## Section 1: Windows Agent Deployment

### 1.1 Windows Group Policy Deployment (Preferred - Domain Environments)
**Time**: 30 minutes (for entire domain)
**Benefit**: Deploy to 100s of systems at once

#### Prerequisites
- [ ] Domain admin credentials
- [ ] Access to domain controller
- [ ] Agent MSI file: `InsaAgent-2.4.1-x64.msi`
- [ ] Config file: `agent-[customer].conf`

#### Steps

1. **Copy installer to domain controller**:
   ```powershell
   # On domain controller
   # Create GPO software distribution folder
   mkdir \\[DC-NAME]\SYSVOL\[DOMAIN]\Policies\InsaAgent

   # Copy MSI
   copy InsaAgent-2.4.1-x64.msi \\[DC-NAME]\SYSVOL\[DOMAIN]\Policies\InsaAgent\

   # Copy config
   copy agent-[customer].conf \\[DC-NAME]\SYSVOL\[DOMAIN]\Policies\InsaAgent\agent.conf
   ```

2. **Create Group Policy Object**:
   - Open **Group Policy Management Console** (gpmc.msc)
   - Right-click domain or OU → **Create a GPO in this domain**
   - Name: "Insa Agent Deployment"

3. **Configure software installation**:
   - Right-click GPO → **Edit**
   - Navigate to: **Computer Configuration > Policies > Software Settings > Software Installation**
   - Right-click → **New > Package**
   - Browse to: `\\[DC-NAME]\SYSVOL\[DOMAIN]\Policies\InsaAgent\InsaAgent-2.4.1-x64.msi`
   - Deployment method: **Assigned** (installs at next reboot/login)
   - Click **OK**

4. **Deploy config file via GPO**:
   - Navigate to: **Computer Configuration > Preferences > Windows Settings > Files**
   - Right-click → **New > File**
   - Source: `\\[DC-NAME]\SYSVOL\[DOMAIN]\Policies\InsaAgent\agent.conf`
   - Destination: `C:\Program Files\Insa\Agent\agent.conf`
   - Action: **Update**

5. **Link GPO to OU**:
   - In Group Policy Management Console
   - Right-click target OU (e.g., "Workstations")
   - **Link an Existing GPO** → Select "Insa Agent Deployment"

6. **Force GPO update on test machine**:
   ```powershell
   # On a test Windows machine
   gpupdate /force

   # Reboot to trigger software installation
   shutdown /r /t 60
   ```

7. **Verify installation on test machine** (after reboot):
   ```powershell
   # Check service running
   Get-Service -Name "InsaAgent"

   # Should show: Status = Running

   # Check logs
   Get-Content "C:\ProgramData\Insa\agent.log" -Tail 20

   # Should see: "Agent started successfully"
   ```

8. **Roll out to remaining systems**:
   - [ ] Link GPO to additional OUs
   - [ ] Allow 24-48 hours for all systems to update
   - [ ] Monitor DefectDojo for new systems appearing

#### Troubleshooting GPO Deployment
```powershell
# On client machine - check GPO applied
gpresult /r

# Should show "Insa Agent Deployment" under Applied GPOs

# Check software installation log
Get-WinEvent -LogName Application | Where-Object {$_.Source -eq "MsiInstaller"} | Select-Object -First 10

# Force reinstall if failed
gpupdate /force
```

---

### 1.2 Windows Manual Installation (Non-Domain or Individual Systems)
**Time**: 5 minutes per system

#### Steps

1. **Copy installer to target system**:
   - Via USB drive, RDP copy/paste, or network share

2. **Install agent**:
   ```powershell
   # Run as Administrator
   msiexec /i InsaAgent-2.4.1-x64.msi /qn /l*v install.log

   # /qn = quiet mode (no UI)
   # /l*v = verbose logging
   ```

3. **Copy configuration**:
   ```powershell
   # Copy config file
   copy agent-[customer].conf "C:\Program Files\Insa\Agent\agent.conf"
   ```

4. **Start service**:
   ```powershell
   # Start Insa Agent service
   Start-Service -Name "InsaAgent"

   # Set to auto-start
   Set-Service -Name "InsaAgent" -StartupType Automatic
   ```

5. **Verify installation**:
   ```powershell
   # Check service status
   Get-Service -Name "InsaAgent"

   # Check process
   Get-Process -Name "insa-agent"

   # Check CPU usage (should be < 5%)
   Get-Process -Name "insa-agent" | Select-Object CPU,WorkingSet

   # Check logs
   Get-Content "C:\ProgramData\Insa\agent.log" -Tail 20
   ```

6. **Record deployment**:
   - [ ] Hostname: ___________
   - [ ] IP Address: ___________
   - [ ] OS Version: ___________
   - [ ] Agent Version: 2.4.1
   - [ ] Installation Time: ___________
   - [ ] Status: Running / Failed

---

### 1.3 Windows Deployment Checklist (Per System)
- [ ] Verify system is NOT a safety system (check `SAFETY_SYSTEM_EXCLUSION.md`)
- [ ] Backup agent credentials (if needed for rollback)
- [ ] Install agent
- [ ] Copy config file
- [ ] Start service
- [ ] Verify CPU < 5%
- [ ] Verify connectivity to jump box (check logs)
- [ ] Verify system appears in DefectDojo within 5 minutes
- [ ] Document in asset inventory

---

## Section 2: Linux Agent Deployment

### 2.1 Linux Ansible Deployment (Preferred - If Customer Has Ansible)
**Time**: 20 minutes (for all Linux systems)

#### Prerequisites
- [ ] Ansible control node (customer's or your laptop)
- [ ] SSH access to all target systems
- [ ] Agent DEB/RPM files
- [ ] Ansible inventory file

#### Steps

1. **Create Ansible inventory**:
   ```bash
   # On Ansible control node
   nano inventory.ini
   ```

   ```ini
   [linux_servers]
   server1.customer.com ansible_user=root
   server2.customer.com ansible_user=sysadmin ansible_become=yes
   server3.customer.com ansible_user=sysadmin ansible_become=yes

   [linux_servers:vars]
   ansible_ssh_private_key_file=~/.ssh/customer_key
   ```

2. **Create Ansible playbook**:
   ```bash
   nano deploy-insa-agent.yml
   ```

   ```yaml
   ---
   - name: Deploy Insa Agent to Linux Servers
     hosts: linux_servers
     become: yes

     vars:
       agent_version: "2.4.1"
       jumpbox_ip: "[Jump box IP]"
       jumpbox_psk: "[PSK from jump box]"

     tasks:
       - name: Copy agent DEB package (Debian/Ubuntu)
         copy:
           src: ./insa-agent-{{ agent_version }}-amd64.deb
           dest: /tmp/insa-agent.deb
         when: ansible_os_family == "Debian"

       - name: Install agent (Debian/Ubuntu)
         apt:
           deb: /tmp/insa-agent.deb
           state: present
         when: ansible_os_family == "Debian"

       - name: Copy agent RPM package (RHEL/CentOS)
         copy:
           src: ./insa-agent-{{ agent_version }}.x86_64.rpm
           dest: /tmp/insa-agent.rpm
         when: ansible_os_family == "RedHat"

       - name: Install agent (RHEL/CentOS)
         yum:
           name: /tmp/insa-agent.rpm
           state: present
         when: ansible_os_family == "RedHat"

       - name: Copy agent configuration
         template:
           src: ./agent.conf.j2
           dest: /etc/insa-agent/agent.conf
           owner: root
           group: root
           mode: '0600'

       - name: Copy CA bundle
         copy:
           src: ./ca-bundle.crt
           dest: /etc/insa-agent/ca-bundle.crt
           owner: root
           group: root
           mode: '0644'

       - name: Start and enable agent service
         systemd:
           name: insa-agent
           state: started
           enabled: yes

       - name: Verify agent is running
         systemd:
           name: insa-agent
           state: started
         register: agent_status
         failed_when: agent_status.status.ActiveState != "active"
   ```

3. **Create config template**:
   ```bash
   nano agent.conf.j2
   ```

   ```ini
   [General]
   customer_id = [customer]
   hostname = {{ ansible_hostname }}

   [JumpBox]
   server = {{ jumpbox_ip }}:8443
   protocol = https
   verify_tls = yes
   ca_bundle = /etc/insa-agent/ca-bundle.crt

   [Authentication]
   method = psk
   psk = {{ jumpbox_psk }}

   [Telemetry]
   interval = 60
   metrics = cpu,memory,disk,network,processes

   [Security]
   file_integrity_monitoring = yes
   fim_paths = /etc,/usr/bin,/usr/sbin,/opt
   vulnerability_scanning = yes
   compliance_frameworks = cis_benchmark

   [Performance]
   cpu_limit = 5
   memory_limit = 100

   [Logging]
   level = INFO
   local_log = /var/log/insa-agent.log
   ```

4. **Run playbook**:
   ```bash
   ansible-playbook -i inventory.ini deploy-insa-agent.yml

   # Expected output:
   # PLAY RECAP ***************
   # server1.customer.com : ok=6 changed=5 unreachable=0 failed=0
   # server2.customer.com : ok=6 changed=5 unreachable=0 failed=0
   ```

5. **Verify deployment**:
   ```bash
   # Check all hosts
   ansible -i inventory.ini linux_servers -m shell -a "systemctl status insa-agent"

   # Check agent CPU usage
   ansible -i inventory.ini linux_servers -m shell -a "ps aux | grep insa-agent"
   ```

---

### 2.2 Linux Manual Installation (Individual Systems)
**Time**: 5 minutes per system

#### Debian/Ubuntu Systems

1. **Copy agent package to target**:
   ```bash
   # Via SCP from your laptop
   scp insa-agent-2.4.1-amd64.deb user@targethost:/tmp/
   ```

2. **Install agent**:
   ```bash
   # SSH to target system
   ssh user@targethost

   # Install package
   sudo dpkg -i /tmp/insa-agent-2.4.1-amd64.deb

   # If dependencies missing
   sudo apt-get install -f
   ```

3. **Configure agent**:
   ```bash
   # Copy config
   sudo nano /etc/insa-agent/agent.conf
   # Paste config from your template (section 0.2)

   # Copy CA bundle
   sudo cp /tmp/ca-bundle.crt /etc/insa-agent/
   sudo chmod 644 /etc/insa-agent/ca-bundle.crt
   ```

4. **Start service**:
   ```bash
   sudo systemctl start insa-agent
   sudo systemctl enable insa-agent
   ```

5. **Verify**:
   ```bash
   # Check service
   sudo systemctl status insa-agent

   # Check logs
   sudo tail -f /var/log/insa-agent.log

   # Check CPU/memory
   ps aux | grep insa-agent
   top -p $(pgrep insa-agent)
   ```

#### RHEL/CentOS Systems

1. **Copy and install**:
   ```bash
   scp insa-agent-2.4.1.x86_64.rpm user@targethost:/tmp/
   ssh user@targethost
   sudo yum install /tmp/insa-agent-2.4.1.x86_64.rpm
   ```

2. **Configure and start** (same as Debian steps 3-5)

---

### 2.3 Linux Deployment Checklist (Per System)
- [ ] Verify system is NOT a safety system
- [ ] Install agent package (DEB or RPM)
- [ ] Copy config file to `/etc/insa-agent/agent.conf`
- [ ] Copy CA bundle to `/etc/insa-agent/ca-bundle.crt`
- [ ] Start and enable service
- [ ] Verify CPU < 5% (`top -p $(pgrep insa-agent)`)
- [ ] Verify connectivity to jump box (check logs)
- [ ] Verify system appears in DefectDojo within 5 minutes
- [ ] Document in asset inventory

---

## Section 3: Embedded/IoT Device Monitoring

### 3.1 Embedded Linux Devices (IIoT Gateways, ARM Systems)
**Time**: 10 minutes per device
**Examples**: Raspberry Pi, IIoT gateways, industrial computers

#### Steps

1. **Verify device is capable**:
   - [ ] Linux-based OS (not RTOS)
   - [ ] At least 100MB free RAM
   - [ ] Network connectivity
   - [ ] SSH or console access

2. **Check architecture**:
   ```bash
   # SSH to device
   uname -m

   # Output examples:
   # armv7l  (32-bit ARM - Raspberry Pi)
   # aarch64 (64-bit ARM - newer Pi, ARM servers)
   # mips    (MIPS - some IIoT gateways)
   ```

3. **Install agent**:
   ```bash
   # Copy appropriate tar.gz to device
   scp insa-agent-2.4.1-arm64.tar.gz user@device:/tmp/

   # SSH to device
   ssh user@device

   # Extract
   cd /opt
   sudo tar -xzf /tmp/insa-agent-2.4.1-arm64.tar.gz

   # Install script
   cd insa-agent
   sudo ./install-embedded.sh
   ```

4. **Configure**:
   ```bash
   # Copy config
   sudo nano /etc/insa-agent/agent.conf
   # Paste config

   # Adjust performance limits (embedded devices have less CPU)
   [Performance]
   cpu_limit = 10  # Allow up to 10% on embedded
   memory_limit = 50  # Only 50MB RAM

   # Reduce telemetry frequency
   [Telemetry]
   interval = 300  # Every 5 minutes instead of 1
   ```

5. **Start service**:
   ```bash
   sudo systemctl start insa-agent
   sudo systemctl enable insa-agent
   ```

6. **Monitor impact** (critical on resource-constrained devices):
   ```bash
   # Watch CPU for 5 minutes
   top -p $(pgrep insa-agent)

   # If CPU > 10%, reduce monitoring frequency or disable FIM
   sudo nano /etc/insa-agent/agent.conf
   # Set: file_integrity_monitoring = no
   sudo systemctl restart insa-agent
   ```

---

### 3.2 Network Devices (SNMP Monitoring Only)
**Time**: 5 minutes per device
**Examples**: Switches, routers, firewalls, PLCs with SNMP

#### Prerequisites
- [ ] Device supports SNMP v2c or v3
- [ ] SNMP community string or credentials
- [ ] Jump box can reach device on UDP 161

#### Steps

1. **Configure SNMP on device** (if not already enabled):
   - Consult device documentation
   - Enable SNMP
   - Set community string (e.g., "insa-readonly")
   - Restrict access to jump box IP only (security)

2. **Add device to jump box SNMP monitoring**:
   ```bash
   # SSH to jump box
   ssh insaadmin@[JUMP_BOX_IP]

   # Edit SNMP targets
   sudo nano /etc/insa/snmp-targets.conf
   ```

   ```ini
   [device-name]
   ip = [Device IP]
   snmp_version = 2c
   community = insa-readonly
   port = 161
   poll_interval = 300  # seconds
   metrics = uptime,interfaces,cpu,memory
   ```

3. **Test SNMP connectivity**:
   ```bash
   # From jump box
   snmpwalk -v2c -c insa-readonly [Device IP] sysDescr

   # Should return device description
   ```

4. **Restart SNMP poller**:
   ```bash
   sudo systemctl restart insa-snmp-poller

   # Check logs
   sudo journalctl -u insa-snmp-poller -n 50
   ```

5. **Verify in DefectDojo**:
   - Device should appear as "Network Device" asset type
   - Metrics will be different (no agent running)

---

## Section 4: OT-Specific Systems (EXTRA CAUTION)

### 4.1 HMI/SCADA Servers
**Risk Level**: HIGH - These systems control industrial processes

#### Pre-Installation Checks
- [ ] Verify NOT a safety system (`SAFETY_SYSTEM_EXCLUSION.md`)
- [ ] Get approval from OT manager in writing
- [ ] Schedule during maintenance window (if possible)
- [ ] Have OT operator standing by
- [ ] Test on non-production HMI first (if available)

#### Installation Steps (Same as Windows, but with extra verification)

1. **Install agent** (manual method, not GPO):
   ```powershell
   # Install in quiet mode
   msiexec /i InsaAgent-2.4.1-x64.msi /qn /l*v install.log
   ```

2. **Configure for low impact**:
   ```ini
   [Performance]
   cpu_limit = 3  # Even lower limit for HMI
   memory_limit = 50

   [Telemetry]
   interval = 300  # Every 5 minutes (not 1)

   [Security]
   file_integrity_monitoring = no  # Disable FIM (too CPU-intensive)
   vulnerability_scanning = no     # Disable scanning (do from jump box)
   ```

3. **Monitor for 30 minutes after installation**:
   ```powershell
   # Watch HMI screen - verify no lag or freezing

   # Watch agent CPU
   while($true) {
       Get-Process -Name "insa-agent" | Select-Object CPU,WorkingSet
       Start-Sleep -Seconds 10
   }

   # If CPU > 5%, stop agent immediately
   Stop-Service -Name "InsaAgent"
   ```

4. **Verify no impact on HMI**:
   - [ ] Screen refresh rate normal (no lag)
   - [ ] Alarm response time normal
   - [ ] Historian data still logging
   - [ ] OT operator confirms no issues

5. **If ANY impact detected**:
   - STOP agent immediately
   - Uninstall agent (see `ROLLBACK_PROCEDURE.md`)
   - Document issue
   - Escalate to Insa technical team

---

### 4.2 Historian Servers
**Risk Level**: MEDIUM-HIGH - Critical for operations data

#### Special Considerations
- Historians are write-heavy (lots of disk I/O)
- Agent FIM can cause I/O contention
- Install during low-traffic hours

#### Installation
1. Same as Windows manual installation
2. **Disable FIM**: `file_integrity_monitoring = no`
3. **Monitor disk I/O** after installation:
   ```powershell
   # Watch disk I/O
   Get-Counter '\PhysicalDisk(*)\Avg. Disk Queue Length' -Continuous

   # Should stay < 2.0
   # If > 5.0, agent may be causing contention
   ```

---

### 4.3 OPC Servers
**Risk Level**: MEDIUM-HIGH - Critical for OT/IT data exchange

#### Special Considerations
- OPC servers bridge OT and IT
- High network traffic
- Agent should not interfere with OPC connections

#### Installation
1. Same as Windows manual installation
2. **Test OPC connectivity after installation**:
   - Use OPC client to connect
   - Verify tag reads/writes work
   - Check OPC latency (should not increase)
3. **Monitor for 1 hour** before considering successful

---

## Section 5: Deployment Validation

### 5.1 Individual System Validation
**Time**: 2 minutes per system

For each system after agent installation:

1. **Check agent service**:
   - Windows: `Get-Service -Name "InsaAgent"` → Should be "Running"
   - Linux: `systemctl status insa-agent` → Should be "active (running)"

2. **Check agent logs** (last 20 lines):
   - Windows: `Get-Content "C:\ProgramData\Insa\agent.log" -Tail 20`
   - Linux: `sudo tail -20 /var/log/insa-agent.log`
   - Look for: "Connected to jump box successfully"
   - No ERROR messages

3. **Check CPU and memory**:
   - Windows: `Get-Process -Name "insa-agent" | Select-Object CPU,WorkingSet`
   - Linux: `ps aux | grep insa-agent`
   - CPU should be < 5% (< 3% for OT systems)
   - Memory should be < 100MB (< 50MB for embedded)

4. **Check connectivity to jump box**:
   - Windows: `Test-NetConnection -ComputerName [JUMP_BOX_IP] -Port 8443`
   - Linux: `nc -zv [JUMP_BOX_IP] 8443`
   - Should show "Connected" or "succeeded"

5. **Record in asset inventory**:
   ```
   [✓] Hostname: _____________
   [✓] Agent Version: 2.4.1
   [✓] Status: Running
   [✓] CPU: ___% (< 5%)
   [✓] Memory: ___MB (< 100MB)
   [✓] Jump Box Connectivity: Yes
   [✓] Deployed By: [Your name]
   [✓] Date/Time: [YYYY-MM-DD HH:MM]
   ```

---

### 5.2 Jump Box Validation
**Time**: 10 minutes (after all agents deployed)

1. **Check jump box received connections**:
   ```bash
   # SSH to jump box
   ssh insaadmin@[JUMP_BOX_IP]

   # Check connected agents
   sudo journalctl -u insa-agent-relay -n 200 | grep "New agent connected"

   # Count unique agent connections
   sudo cat /var/log/insa/agent-relay.log | grep "agent_id" | sort -u | wc -l

   # Should match number of deployed agents
   ```

2. **Check jump box resource usage**:
   ```bash
   # CPU and memory
   htop

   # Network traffic (should see steady inbound from agents)
   nethogs

   # Disk usage (cache should be growing)
   du -sh /var/lib/insa/cache
   ```

3. **Check cache is storing data**:
   ```bash
   # List cache files
   ls -lh /var/lib/insa/cache/

   # Should see files with recent timestamps
   ```

---

### 5.3 DefectDojo Platform Validation
**Time**: 15 minutes

1. **Login to DefectDojo**:
   - URL: https://100.100.101.1:8082
   - Navigate to: **Assets** or **Engagement > [Customer]**

2. **Verify all agents appear**:
   - [ ] Total assets shown: ______
   - [ ] Should match deployed agent count
   - [ ] Each asset shows: hostname, IP, OS, last seen

3. **Check "Last Seen" timestamps**:
   - All agents should show "Last seen: < 5 minutes ago"
   - If any show "> 10 minutes ago", troubleshoot that agent

4. **Verify telemetry data**:
   - Click on an asset
   - Navigate to **Metrics** tab
   - Should see graphs for:
     - CPU usage
     - Memory usage
     - Disk usage
     - Network traffic

5. **Trigger test finding**:
   ```bash
   # SSH to one deployed system
   # Create a test file in monitored directory (will trigger FIM alert)

   # Linux
   sudo touch /etc/insa-test-alert

   # Windows
   New-Item -Path "C:\Windows\System32\insa-test-alert.txt" -ItemType File
   ```

   - Wait 2-3 minutes
   - Check DefectDojo → **Findings**
   - Should see new finding: "File Integrity Monitoring: New file detected"

6. **Run compliance scan**:
   - In DefectDojo, select customer engagement
   - Click **Start Scan** → **CIS Benchmark**
   - Wait 5-10 minutes
   - Verify scan results appear

---

### 5.4 Performance Validation
**Time**: 10 minutes per OT system (critical systems only)

For HMI/SCADA/Historian systems, perform extra validation:

1. **Baseline performance before agent** (if you recorded):
   - Compare CPU usage before and after
   - Should be < 3% increase

2. **HMI-specific tests**:
   - [ ] Screen refresh rate normal (no lag when navigating)
   - [ ] Alarm acknowledgment responsive (< 1 second delay)
   - [ ] Trend charts loading normally
   - [ ] No error popups or warnings

3. **Historian-specific tests**:
   - [ ] Tag data still logging (check historian database)
   - [ ] Query response time normal
   - [ ] No missed samples or gaps in data

4. **OPC-specific tests**:
   - [ ] OPC clients can still connect
   - [ ] Tag reads/writes functional
   - [ ] Latency not increased (< 50ms for local OPC)

5. **Get OT operator sign-off**:
   - [ ] Show operator the system is monitored
   - [ ] Confirm no impact on operations
   - [ ] Document verbal confirmation in notes

---

## Section 6: Post-Deployment Tasks

### 6.1 Documentation
**Time**: 30 minutes

1. **Update asset inventory**:
   - Mark all systems as "Agent Deployed"
   - Record agent version, deployment date, deployed by
   - Note any excluded systems with reason

2. **Update network diagram**:
   - Show agents on customer assets
   - Show connections to jump box
   - Include in customer binder (Tab 2)

3. **Create deployment summary**:
   ```
   Insa Agent Deployment Summary
   Customer: [Name]
   Date: [YYYY-MM-DD]
   Deployed By: [Your name]

   Totals:
   - Planned: [X] systems
   - Deployed: [Y] systems
   - Excluded: [Z] systems (safety systems)
   - Success Rate: [Y/X * 100]%

   By Platform:
   - Windows: [X] deployed
   - Linux: [X] deployed
   - Embedded: [X] deployed
   - Network (SNMP): [X] configured

   By Tier:
   - IT Systems: [X] deployed
   - OT Systems: [X] deployed
   - Critical OT: [X] deployed (with extra validation)

   Issues Encountered:
   - [List any systems that failed, reasons, resolutions]

   Performance:
   - Average CPU per agent: [X]%
   - Average memory per agent: [X] MB
   - Jump box CPU: [X]%
   - Jump box bandwidth: [X] KB/s

   Validation:
   - All agents reporting: Yes/No
   - DefectDojo shows all assets: Yes/No
   - Test finding triggered: Yes/No
   - Compliance scan completed: Yes/No
   - OT operator sign-off: Yes/No
   ```

4. **Include in customer binder** (Tab 4: Agents)

---

### 6.2 Customer Training on Agent Management
**Time**: 30 minutes (during Day 3 training)

Teach customer IT team:

1. **How to check agent status**:
   - Show service status commands
   - Show logs
   - Show DefectDojo "Last Seen"

2. **How to troubleshoot agent issues**:
   - Agent not reporting → Check service, logs, network
   - High CPU → Check config, reduce frequency
   - Config changes → Edit config file, restart service

3. **Agent update process**:
   - Insa will push updates via jump box
   - Customer can opt-in to auto-updates
   - Or manual update process

4. **When to uninstall agent**:
   - System decommissioned → Follow `ROLLBACK_PROCEDURE.md`
   - Performance impact → Contact Insa support

---

### 6.3 Handoff to Insa SOC
**Time**: 15 minutes

1. **Send deployment report to Insa SOC**:
   - Email or upload to Insa project portal
   - Include deployment summary (from 6.1.3)
   - Include asset inventory CSV

2. **Transfer monitoring ownership**:
   - Field technician: Installation and validation
   - Insa SOC: Ongoing monitoring and triage
   - Customer: Day-to-day operations

3. **Schedule 1-week follow-up call**:
   - Review first week of findings
   - Adjust alert thresholds if needed
   - Answer customer questions

---

## Section 7: Troubleshooting Common Issues

### Agent Won't Install

**Windows**:
```powershell
# Check MSI install logs
Get-Content C:\Windows\Logs\insa-agent-install.log

# Common fixes:
# - Requires .NET Framework 4.8 (install from Microsoft)
# - Requires Visual C++ Redistributable (included in MSI, but may fail)
# - Antivirus blocking (whitelist Insa Agent)
```

**Linux**:
```bash
# Check package manager logs
sudo tail /var/log/dpkg.log  # Debian
sudo tail /var/log/yum.log   # RHEL

# Common fixes:
# - Missing dependencies: sudo apt-get install -f
# - Python 3.6+ required: sudo apt install python3
```

---

### Agent Installed But Not Reporting

**Check 1: Service running?**
```bash
# Windows
Get-Service -Name "InsaAgent"

# Linux
sudo systemctl status insa-agent

# If not running, check logs for errors
```

**Check 2: Network connectivity?**
```bash
# Windows
Test-NetConnection -ComputerName [JUMP_BOX_IP] -Port 8443

# Linux
nc -zv [JUMP_BOX_IP] 8443

# If fails, check firewall rules
```

**Check 3: Configuration correct?**
```bash
# Verify jump box IP, PSK, TLS settings
# Common mistake: wrong PSK

# Test authentication manually
curl -k https://[JUMP_BOX_IP]:8443/auth -H "Authorization: PSK [PSK_VALUE]"
# Should return 200 OK
```

**Check 4: TLS certificate issue?**
```bash
# Verify CA bundle is correct
# Windows: C:\Program Files\Insa\Agent\ca-bundle.crt
# Linux: /etc/insa-agent/ca-bundle.crt

# Test TLS handshake
openssl s_client -connect [JUMP_BOX_IP]:8443 -CAfile ca-bundle.crt
```

---

### Agent Using Too Much CPU

**Step 1: Check what's consuming CPU**
```bash
# Linux
sudo strace -p $(pgrep insa-agent) -c -f

# Look for high-frequency syscalls (file I/O, network)
```

**Step 2: Reduce monitoring frequency**
```ini
# Edit agent.conf
[Telemetry]
interval = 300  # Change from 60 to 300 seconds

[Security]
file_integrity_monitoring = no  # Disable if too intensive
```

**Step 3: Restart agent**
```bash
# Windows
Restart-Service -Name "InsaAgent"

# Linux
sudo systemctl restart insa-agent
```

**Step 4: If still high, contact Insa support**

---

## Appendix A: Agent Architecture

### How Agents Work
```
[Asset] → [Insa Agent] → [Local Buffer] → [TLS] → [Jump Box] → [DefectDojo]
           ↓
      [Metrics Collection]
      [Log Forwarding]
      [FIM Scanning]
      [Vuln Scanning]
```

### Agent Components
- **Collector**: Gathers metrics (CPU, mem, disk, net)
- **Log Forwarder**: Tails important logs (syslog, event log)
- **FIM Scanner**: Monitors file changes in sensitive directories
- **Vuln Scanner**: Runs periodic vulnerability scans (uses local CVE database)
- **Compliance Checker**: Validates against CIS benchmarks
- **Uploader**: Sends data to jump box (compressed, encrypted)

### Data Flow
1. Agent collects data every 60 seconds (configurable)
2. Data stored in local buffer (up to 6 hours if jump box unreachable)
3. Data compressed (gzip) and encrypted (TLS 1.2+)
4. Data sent to jump box on port 8443
5. Jump box forwards to DefectDojo API
6. DefectDojo processes and stores in PostgreSQL
7. DefectDojo AI triages findings
8. Alerts sent to customer SOC via email

---

## Appendix B: Quick Reference Commands

### Windows
```powershell
# Install agent
msiexec /i InsaAgent-2.4.1-x64.msi /qn

# Check service
Get-Service -Name "InsaAgent"

# Start/stop service
Start-Service -Name "InsaAgent"
Stop-Service -Name "InsaAgent"

# Check logs
Get-Content "C:\ProgramData\Insa\agent.log" -Tail 50

# Check CPU/memory
Get-Process -Name "insa-agent" | Select-Object CPU,WorkingSet

# Uninstall
msiexec /x InsaAgent-2.4.1-x64.msi /qn
```

### Linux
```bash
# Install agent (Debian)
sudo dpkg -i insa-agent-2.4.1-amd64.deb

# Install agent (RHEL)
sudo yum install insa-agent-2.4.1.x86_64.rpm

# Check service
sudo systemctl status insa-agent

# Start/stop service
sudo systemctl start insa-agent
sudo systemctl stop insa-agent

# Check logs
sudo tail -f /var/log/insa-agent.log

# Check CPU/memory
ps aux | grep insa-agent

# Uninstall (Debian)
sudo dpkg -r insa-agent

# Uninstall (RHEL)
sudo yum remove insa-agent
```

---

**Document Version**: 1.0
**Last Updated**: October 11, 2025
**Owner**: Insa Automation Corp
**Classification**: Internal Use - Field Technicians Only

---

*Made by Insa Automation Corp for OpSec Excellence*
