# Rollback Procedure - Emergency Agent and Jump Box Removal

**Insa Automation Corp - DevSecOps Platform**
**Version**: 1.0
**Last Updated**: October 11, 2025
**Purpose**: Complete procedure for uninstalling agents and decommissioning jump box

---

## Overview

This guide covers emergency rollback procedures for Insa Managed SOC deployments. Use this when:
- Customer requests removal of monitoring
- Agent causes unacceptable performance impact
- Safety concern discovered
- Deployment cancelled mid-installation
- Contract termination

**Goal**: Return customer environment to pre-deployment state with zero residual impact.

---

## When to Initiate Rollback

### Immediate Rollback (Emergency)
Execute rollback immediately if:
- [ ] Agent causes production system to crash or freeze
- [ ] Agent installed on safety system (see `SAFETY_SYSTEM_EXCLUSION.md`)
- [ ] Agent causes unacceptable performance degradation (> 10% CPU sustained)
- [ ] Network traffic from agent overwhelms customer network
- [ ] Customer safety officer demands immediate removal
- [ ] Regulatory violation detected

**Action**: Stop agent immediately, notify customer, begin rollback.

### Planned Rollback (Non-Emergency)
Schedule rollback if:
- [ ] Customer cancels contract
- [ ] Deployment pilot phase ends (not converting to production)
- [ ] Customer migrating to different SOC provider
- [ ] System being decommissioned
- [ ] Customer requests removal for any reason

**Action**: Schedule removal during maintenance window, follow full procedure.

---

## Rollback Authority and Approval

### Who Can Authorize Rollback?

**Emergency Rollback** (can be authorized by):
- Field technician on-site (if immediate safety concern)
- Insa project manager
- Customer safety engineer
- Customer CIO/CISO

**Planned Rollback** (requires approval from):
- Insa project manager (for contract/billing)
- Customer IT/OT manager (for scheduling)
- Written confirmation (email acceptable)

### Notification Requirements
Before starting rollback, notify:
- [ ] Customer IT/OT contact (primary)
- [ ] Insa project manager
- [ ] Insa SOC team (to stop monitoring)
- [ ] Customer security team (if they monitor DefectDojo)

**Template email**:
```
Subject: Insa SOC Deployment Rollback - [Customer Name]

Hi [Customer Contact],

We are initiating rollback of the Insa Managed SOC deployment per [reason].

Timeline:
- Start: [Date/Time]
- Expected completion: [Date/Time]
- Systems affected: [List or "all monitored systems"]

Activities:
1. Stop all agents
2. Uninstall agents from systems
3. Remove jump box from DMZ
4. Restore firewall rules
5. Verify no residual impact

You will receive a completion report with verification that all Insa components have been removed.

Please contact me with any questions.

Thank you,
[Your Name]
Insa Field Technician
Phone: [Your Phone]
Email: [Your Email]
```

---

## Phase 1: Immediate Impact Mitigation (Emergency Only)

**Time**: 5-10 minutes
**Goal**: Stop any ongoing impact while preserving evidence for investigation

### Step 1: Stop All Agents (DO NOT UNINSTALL YET)

**Windows (via PowerShell on each system)**:
```powershell
# Stop service immediately
Stop-Service -Name "InsaAgent" -Force

# Disable service (prevent restart on reboot)
Set-Service -Name "InsaAgent" -StartupType Disabled

# Verify stopped
Get-Service -Name "InsaAgent"
# Should show: Status = Stopped, StartType = Disabled

# Verify no lingering processes
Get-Process -Name "insa-agent" -ErrorAction SilentlyContinue
# Should return nothing
```

**Linux (via SSH to each system)**:
```bash
# Stop service immediately
sudo systemctl stop insa-agent

# Disable service
sudo systemctl disable insa-agent

# Verify stopped
sudo systemctl status insa-agent
# Should show: inactive (dead)

# Verify no lingering processes
ps aux | grep insa-agent
# Should return only grep process
```

**If Customer Has Ansible/Puppet/GPO** (mass stop):
```bash
# Ansible (fastest for many systems)
ansible -i inventory.ini all -m service -a "name=insa-agent state=stopped enabled=no" --become

# If deployed via GPO, disable GPO immediately
# On domain controller
Remove-GPLink -Name "Insa Agent Deployment" -Target "OU=Workstations,DC=customer,DC=com"
```

### Step 2: Stop Jump Box Services (DO NOT REMOVE YET)

```bash
# SSH to jump box
ssh insaadmin@[JUMP_BOX_IP]

# Stop all Insa services
sudo systemctl stop insa-agent-relay
sudo systemctl stop insa-cache-manager
sudo systemctl stop insa-heartbeat

# Disable services
sudo systemctl disable insa-agent-relay
sudo systemctl disable insa-cache-manager
sudo systemctl disable insa-heartbeat

# Verify stopped
sudo systemctl status insa-agent-relay
sudo systemctl status insa-cache-manager
sudo systemctl status insa-heartbeat
```

### Step 3: Verify Impact Stopped

**Check affected system**:
- [ ] CPU usage returned to normal (< 5 minutes after stop)
- [ ] System responsive (no lag)
- [ ] Production operations normal
- [ ] Customer confirms issue resolved

**If impact continues after stopping agents**:
- Agent may not be the root cause
- Investigate other changes made during deployment
- Check network (firewall rules, routing)
- Check other services installed

### Step 4: Notify Stakeholders

- [ ] Customer: "Agents stopped, impact mitigated, investigating root cause"
- [ ] Insa PM: "Emergency stop executed, beginning investigation"
- [ ] Insa SOC: "Stop monitoring customer [Name], agents offline"

### Step 5: Preserve Evidence (For Investigation)

Before uninstalling, collect:

**From affected system**:
```bash
# Logs
# Windows
Copy-Item "C:\ProgramData\Insa\agent.log" -Destination "C:\Temp\insa-agent-$(Get-Date -Format 'yyyyMMdd-HHmmss').log"

# Linux
sudo cp /var/log/insa-agent.log /tmp/insa-agent-$(date +%Y%m%d-%H%M%S).log

# Configuration
# Windows
Copy-Item "C:\Program Files\Insa\Agent\agent.conf" -Destination "C:\Temp\"

# Linux
sudo cp /etc/insa-agent/agent.conf /tmp/

# Performance data (if available)
# Windows
Get-Process -Name "insa-agent" | Export-Csv -Path "C:\Temp\insa-agent-process.csv"

# Linux
ps aux | grep insa-agent > /tmp/insa-agent-process.txt
```

**From jump box**:
```bash
# Logs
sudo cp /var/log/insa/agent-relay.log /tmp/agent-relay-$(date +%Y%m%d-%H%M%S).log

# Cache data (if space available)
sudo tar -czf /tmp/insa-cache-backup.tar.gz /var/lib/insa/cache

# Configuration
sudo cp /etc/insa/jumpbox.conf /tmp/
```

**Transfer evidence to Insa storage**:
```bash
# SCP to Insa server
scp /tmp/insa-*.log user@insa-server:/incident-reports/[customer]/
```

---

## Phase 2: Agent Uninstallation

**Time**: 30-60 minutes (depending on number of systems)
**Prerequisites**: Evidence collected, approval to proceed with full removal

### Step 1: Uninstall Windows Agents

#### Method 1: Group Policy Removal (Domain Environments)
**Time**: 5 minutes setup, 24-48 hours for all systems to process

1. **Remove deployment GPO**:
   - Open Group Policy Management Console on DC
   - Find "Insa Agent Deployment" GPO
   - Right-click GPO → **Delete**
   - Confirm deletion

2. **Create uninstall GPO**:
   - Create new GPO: "Insa Agent Removal"
   - Edit GPO
   - Navigate to: **Computer Configuration > Policies > Software Settings > Software Installation**
   - Find "InsaAgent" in list
   - Right-click → **All Tasks > Remove**
   - Select: **Immediately uninstall the software from users and computers**
   - Link GPO to same OUs as original deployment

3. **Force GPO update on test system**:
   ```powershell
   gpupdate /force
   shutdown /r /t 60  # Reboot to trigger uninstall
   ```

4. **Verify uninstall on test system**:
   ```powershell
   # After reboot, check service gone
   Get-Service -Name "InsaAgent" -ErrorAction SilentlyContinue
   # Should return error: "Cannot find service"

   # Check program files
   Test-Path "C:\Program Files\Insa\Agent"
   # Should return: False
   ```

5. **Monitor domain-wide rollout**:
   - Check GPO application: `gpresult /r` on random systems
   - Check uninstall success rate via domain query
   - May take 24-48 hours for all systems to process

#### Method 2: Manual Uninstall (Per System)
**Time**: 5 minutes per system

**Via GUI**:
1. Open **Programs and Features** (appwiz.cpl)
2. Find "Insa Agent"
3. Click **Uninstall**
4. Follow prompts (no reboot required)

**Via Command Line** (faster, can be scripted):
```powershell
# Find product code
$productCode = Get-WmiObject -Class Win32_Product | Where-Object {$_.Name -like "*Insa Agent*"} | Select-Object -ExpandProperty IdentifyingNumber

# Uninstall silently
msiexec /x $productCode /qn /norestart /l*v C:\Temp\insa-uninstall.log

# Verify uninstall
Start-Sleep -Seconds 30
Get-Service -Name "InsaAgent" -ErrorAction SilentlyContinue
# Should return error

Test-Path "C:\Program Files\Insa\Agent"
# Should return: False
```

**Via PowerShell Remoting** (mass uninstall):
```powershell
# Create list of target systems
$computers = Get-Content "C:\Temp\systems.txt"

# Uninstall on all systems
Invoke-Command -ComputerName $computers -ScriptBlock {
    $productCode = Get-WmiObject -Class Win32_Product | Where-Object {$_.Name -like "*Insa Agent*"} | Select-Object -ExpandProperty IdentifyingNumber
    if ($productCode) {
        msiexec /x $productCode /qn /norestart
    }
}

# Verify uninstall
Invoke-Command -ComputerName $computers -ScriptBlock {
    Get-Service -Name "InsaAgent" -ErrorAction SilentlyContinue
}
# Should return errors for all systems
```

### Step 2: Uninstall Linux Agents

#### Method 1: Ansible Uninstall (Preferred)
**Time**: 10 minutes

1. **Create uninstall playbook**:
   ```bash
   nano uninstall-insa-agent.yml
   ```

   ```yaml
   ---
   - name: Uninstall Insa Agent from Linux Servers
     hosts: all
     become: yes

     tasks:
       - name: Stop agent service
         systemd:
           name: insa-agent
           state: stopped
         ignore_errors: yes

       - name: Disable agent service
         systemd:
           name: insa-agent
           enabled: no
         ignore_errors: yes

       - name: Uninstall agent (Debian/Ubuntu)
         apt:
           name: insa-agent
           state: absent
           purge: yes
         when: ansible_os_family == "Debian"
         ignore_errors: yes

       - name: Uninstall agent (RHEL/CentOS)
         yum:
           name: insa-agent
           state: absent
         when: ansible_os_family == "RedHat"
         ignore_errors: yes

       - name: Remove config directory
         file:
           path: /etc/insa-agent
           state: absent

       - name: Remove logs
         file:
           path: /var/log/insa-agent.log
           state: absent

       - name: Remove cache
         file:
           path: /var/lib/insa-agent
           state: absent

       - name: Verify agent removed
         command: which insa-agent
         register: agent_check
         failed_when: agent_check.rc == 0
         ignore_errors: yes
   ```

2. **Run playbook**:
   ```bash
   ansible-playbook -i inventory.ini uninstall-insa-agent.yml

   # Expected output:
   # PLAY RECAP ***************
   # server1 : ok=7 changed=5 unreachable=0 failed=0
   # server2 : ok=7 changed=5 unreachable=0 failed=0
   ```

#### Method 2: Manual Uninstall (Per System)
**Time**: 5 minutes per system

**Debian/Ubuntu**:
```bash
# Stop and disable service
sudo systemctl stop insa-agent
sudo systemctl disable insa-agent

# Uninstall package
sudo dpkg -r insa-agent

# Purge config files
sudo dpkg -P insa-agent

# Manual cleanup (if any residuals)
sudo rm -rf /etc/insa-agent
sudo rm -rf /var/log/insa-agent.log
sudo rm -rf /var/lib/insa-agent
```

**RHEL/CentOS**:
```bash
# Stop and disable service
sudo systemctl stop insa-agent
sudo systemctl disable insa-agent

# Uninstall package
sudo yum remove insa-agent

# Manual cleanup
sudo rm -rf /etc/insa-agent
sudo rm -rf /var/log/insa-agent.log
sudo rm -rf /var/lib/insa-agent
```

**Verify uninstall**:
```bash
# Check service gone
sudo systemctl status insa-agent
# Should return: "Unit insa-agent.service could not be found"

# Check binary gone
which insa-agent
# Should return nothing

# Check config gone
ls /etc/insa-agent
# Should return: "No such file or directory"
```

### Step 3: Uninstall Embedded/IoT Agents

```bash
# SSH to embedded device
ssh user@device

# Stop service
sudo systemctl stop insa-agent

# Uninstall
cd /opt/insa-agent
sudo ./uninstall-embedded.sh

# Manual cleanup
sudo rm -rf /opt/insa-agent
sudo rm -rf /etc/insa-agent
sudo rm -rf /var/log/insa-agent.log

# Verify
ls /opt/insa-agent
# Should return: "No such file or directory"
```

### Step 4: Remove SNMP Monitoring (Network Devices)

```bash
# SSH to jump box
ssh insaadmin@[JUMP_BOX_IP]

# Edit SNMP targets
sudo nano /etc/insa/snmp-targets.conf

# Remove all entries (or comment out with #)

# Restart SNMP poller
sudo systemctl restart insa-snmp-poller

# Or disable entirely
sudo systemctl stop insa-snmp-poller
sudo systemctl disable insa-snmp-poller
```

**On network devices** (if SNMP was configured):
- Disable SNMP community string "insa-readonly"
- Or leave enabled (no harm if jump box is removed)

---

## Phase 3: Jump Box Decommissioning

**Time**: 30-45 minutes
**Prerequisites**: All agents uninstalled and verified

### Step 1: Drain Local Cache to SOC (Optional)

If customer wants logs preserved for audit:

```bash
# SSH to jump box
ssh insaadmin@[JUMP_BOX_IP]

# Check cache size
du -sh /var/lib/insa/cache

# Manually flush cache to SOC
sudo /opt/insa/bin/flush-cache.sh --force

# Wait for completion (may take 10-30 minutes depending on size)
# Monitor progress
sudo journalctl -u insa-cache-manager -f

# Verify cache empty
ls /var/lib/insa/cache
# Should be empty or minimal residual files
```

**Alternative: Archive locally and transfer to customer**:
```bash
# Archive cache
sudo tar -czf /tmp/insa-cache-archive-$(date +%Y%m%d).tar.gz /var/lib/insa/cache

# Transfer to customer storage (or USB drive)
scp /tmp/insa-cache-archive-*.tar.gz customer@storage:/backups/insa/
```

### Step 2: Export Configuration and Logs

```bash
# Export configuration (for documentation)
sudo tar -czf /tmp/insa-jumpbox-config-$(date +%Y%m%d).tar.gz \
  /etc/insa \
  /var/log/insa \
  /etc/netplan \
  /etc/systemd/system/insa-*

# Transfer to laptop
scp insaadmin@[JUMP_BOX_IP]:/tmp/insa-jumpbox-config-*.tar.gz ~/rollback-evidence/
```

### Step 3: Stop and Disable All Services

```bash
# Stop services
sudo systemctl stop insa-agent-relay
sudo systemctl stop insa-cache-manager
sudo systemctl stop insa-heartbeat
sudo systemctl stop insa-snmp-poller
sudo systemctl stop insa-self-monitor

# Disable services
sudo systemctl disable insa-agent-relay
sudo systemctl disable insa-cache-manager
sudo systemctl disable insa-heartbeat
sudo systemctl disable insa-snmp-poller
sudo systemctl disable insa-self-monitor

# Verify all stopped
sudo systemctl status insa-*
```

### Step 4: Uninstall Jump Box Software

```bash
# Run uninstaller
cd /opt/insa
sudo ./uninstall.sh

# Confirm uninstall when prompted
# Expected: "Insa jump box software removed successfully"

# Manual cleanup of residuals
sudo rm -rf /opt/insa
sudo rm -rf /etc/insa
sudo rm -rf /var/lib/insa
sudo rm -rf /var/log/insa

# Remove systemd services
sudo rm -f /etc/systemd/system/insa-*.service
sudo systemctl daemon-reload

# Verify uninstall
ls /opt/insa
# Should return: "No such file or directory"

sudo systemctl status insa-agent-relay
# Should return: "Unit insa-agent-relay.service could not be found"
```

### Step 5: Remove TLS Certificates and Credentials

```bash
# Remove certificates
sudo rm -rf /etc/insa/certs

# Remove PSK
sudo rm -f /etc/insa/agent_psk.key

# Remove SSH keys (if generated for Insa support)
rm -f ~/.ssh/insa_support*

# Clear bash history (remove any sensitive commands)
history -c
```

### Step 6: Physical Removal

**If jump box is customer-owned hardware** (staying on-site):
1. Verify all Insa software removed (steps above)
2. Customer can repurpose hardware
3. Recommend: Wipe and reinstall OS (optional, for clean slate)

**If jump box is Insa-owned hardware** (returning to Insa):
1. Shut down jump box:
   ```bash
   sudo shutdown -h now
   ```
2. Disconnect power and network cables
3. Remove from rack
4. Label: "Insa Jump Box - [Customer] - Removed [Date]"
5. Ship back to Insa (or next deployment)

**Wipe disk before repurposing** (security best practice):
```bash
# Boot from USB with DBAN (Darik's Boot and Nuke)
# Or use shred command before shutdown:
sudo shred -vfz -n 3 /dev/sda
# WARNING: This wipes ALL data, including OS. Only do if repurposing hardware.
```

---

## Phase 4: Network Cleanup

**Time**: 15 minutes
**Prerequisites**: Jump box removed

### Step 1: Remove Firewall Rules

**Work with customer network security team**:

**Inbound rules to remove** (customer firewall):
| Source | Destination | Port | Action |
|--------|-------------|------|--------|
| Any agent subnet | Jump box IP | 8443 | REMOVE |
| Customer IT subnet | Jump box IP | 22 | REMOVE |
| Customer IT subnet | Jump box IP | 443 | REMOVE |

**Outbound rules to remove**:
| Source | Destination | Port | Action |
|--------|-------------|------|--------|
| Jump box IP | 100.100.101.1 | 8082 | REMOVE |
| Jump box IP | 100.100.101.1 | 22 | REMOVE |

**Verify rules removed**:
```bash
# From customer IT system, test jump box IP (should timeout)
nc -zv [JUMP_BOX_IP] 8443
# Expected: "Connection timed out" (good, port closed)

# Test outbound to Insa SOC (should be allowed from other IPs, but not jump box)
curl -I https://100.100.101.1:8082
# Expected: "Connection timed out" if jump box IP blocked
```

### Step 2: Remove DNS Entries (If Created)

If jump box had DNS entry:
```bash
# Customer DNS admin
nslookup insa-jumpbox-[customer]
# Should return: "Non-existent domain" after removal
```

### Step 3: Release IP Address

- [ ] Notify customer network team that jump box IP is free
- [ ] Update customer IPAM (IP Address Management) database
- [ ] Document in rollback report

### Step 4: Remove Network Diagram Entries

- [ ] Update customer network diagram to remove jump box
- [ ] Remove from customer asset inventory
- [ ] Update firewall documentation

---

## Phase 5: Verification and Testing

**Time**: 30 minutes
**Goal**: Verify complete removal and no residual impact

### Step 1: Agent Verification (Sample Testing)

**Windows** (test 3-5 systems):
```powershell
# Service check
Get-Service -Name "InsaAgent" -ErrorAction SilentlyContinue
# Should return: Error (service not found)

# Process check
Get-Process -Name "insa-agent" -ErrorAction SilentlyContinue
# Should return: Nothing

# File system check
Test-Path "C:\Program Files\Insa"
# Should return: False

Test-Path "C:\ProgramData\Insa"
# Should return: False

# Registry check (if paranoid)
Get-ItemProperty "HKLM:\SOFTWARE\Insa" -ErrorAction SilentlyContinue
# Should return: Error (key not found)

# Network check (agent should not try to connect to jump box)
netstat -an | Select-String "[JUMP_BOX_IP]"
# Should return: Nothing
```

**Linux** (test 3-5 systems):
```bash
# Service check
sudo systemctl status insa-agent
# Should return: "Unit insa-agent.service could not be found"

# Process check
ps aux | grep insa-agent | grep -v grep
# Should return: Nothing

# File system check
ls /etc/insa-agent
ls /opt/insa-agent
ls /var/log/insa-agent.log
# All should return: "No such file or directory"

# Network check
sudo netstat -an | grep [JUMP_BOX_IP]
# Should return: Nothing
```

### Step 2: Jump Box Verification

```bash
# Try to SSH to jump box (should fail)
ssh insaadmin@[JUMP_BOX_IP]
# Expected: "Connection timed out" or "Connection refused"

# Try to ping jump box
ping -c 4 [JUMP_BOX_IP]
# Expected: "Request timeout" (if powered off or removed)
```

### Step 3: Performance Verification (OT Systems)

For HMI/SCADA/Historian systems:
- [ ] Check CPU usage (should return to pre-agent baseline)
- [ ] Check memory usage (should return to baseline)
- [ ] HMI screen refresh rate normal
- [ ] Historian data logging normally
- [ ] No error messages or alarms related to monitoring

**Get OT operator sign-off**:
- [ ] "System performance back to normal"
- [ ] Document verbal confirmation

### Step 4: DefectDojo Verification

- Login to DefectDojo: https://100.100.101.1:8082
- Navigate to customer engagement
- [ ] All assets show "Last seen: > [rollback time]"
- [ ] No new findings (agents stopped sending data)
- [ ] Jump box shows "Offline"

**Archive customer data in DefectDojo** (if contract terminated):
- Export all findings to CSV
- Export compliance reports
- Send archive to customer
- Deactivate customer engagement in DefectDojo

---

## Phase 6: Documentation and Handoff

**Time**: 30 minutes

### Step 1: Create Rollback Completion Report

**Template**:
```
Insa SOC Deployment Rollback Completion Report
Customer: [Name]
Rollback Date: [YYYY-MM-DD]
Executed By: [Your name]

Reason for Rollback:
[Emergency stop due to performance impact / Contract cancellation / etc.]

Systems Affected:
- Total agents deployed: [X]
- Total agents removed: [X]
- Jump box: Removed / Decommissioned

Rollback Activities:
1. [Date/Time] - All agents stopped
2. [Date/Time] - Agents uninstalled from [X] Windows systems
3. [Date/Time] - Agents uninstalled from [X] Linux systems
4. [Date/Time] - Jump box services stopped
5. [Date/Time] - Jump box software uninstalled
6. [Date/Time] - Jump box physically removed (if applicable)
7. [Date/Time] - Firewall rules removed
8. [Date/Time] - Verification completed

Verification Results:
- Sample systems tested: [List]
- Agent remnants found: None / [Details if any]
- Performance impact: Resolved / [Details if ongoing]
- Customer satisfaction: Confirmed / [Details if concerns]

Outstanding Items:
[None / List any items requiring follow-up]

Data Disposition:
- Customer logs: Archived and provided to customer / Deleted per policy
- Insa configuration: Archived at [location]
- Evidence collected: [If incident investigation]

Customer Sign-Off:
Name: _______________________
Title: _______________________
Signature: _______________________
Date: _______________________

Insa Project Manager Sign-Off:
Name: _______________________
Signature: _______________________
Date: _______________________
```

### Step 2: Customer Handoff Meeting

Schedule 30-minute meeting with customer to:
1. Review rollback completion report
2. Walk through verification results
3. Answer any questions
4. Provide archived data (if applicable)
5. Get customer sign-off
6. Discuss lessons learned (if appropriate)

### Step 3: Internal Lessons Learned

If rollback due to issue (not just contract end):
1. **Root Cause Analysis**: Why did deployment fail?
2. **Corrective Actions**: What will prevent recurrence?
3. **Process Improvements**: Update deployment procedures
4. **Training Needs**: Do technicians need additional training?

**Document in Insa internal wiki**:
- Incident summary
- Root cause
- Actions taken
- Preventive measures

### Step 4: Update Insa Systems

- [ ] Update Insa CRM: Customer status = "Inactive"
- [ ] Update DefectDojo: Engagement archived
- [ ] Update billing: Stop invoicing
- [ ] Update SOC monitoring: Remove from active monitoring list
- [ ] Update jump box inventory: Mark as "available for redeployment"

---

## Phase 7: Post-Rollback Follow-Up

### 1-Week Follow-Up (Planned Rollbacks Only)

If rollback was planned (contract end, pilot completion):
- [ ] Email customer: "Has anything changed since removal?"
- [ ] Offer re-engagement if needs change
- [ ] Request feedback survey (improve future deployments)

### 30-Day Follow-Up (Emergency Rollbacks Only)

If rollback was due to issue:
- [ ] Email customer: "Have you experienced any residual issues?"
- [ ] Offer to review systems remotely (no charge)
- [ ] Provide updated deployment plan (if customer wants to retry)
- [ ] Apologize for inconvenience (maintain relationship)

---

## Appendix A: Emergency Contact Information

### Insa Support Contacts
| Contact | Phone | Email | Availability |
|---------|-------|-------|--------------|
| Insa SOC | TBD | soc@insaing.com | 24/7 |
| Project Manager | TBD | pm@insaing.com | M-F 8-6 |
| Technical Support | TBD | support@insaing.com | M-F 8-6 |
| Emergency Escalation | TBD | emergency@insaing.com | 24/7 |

### When to Call
- **Immediate safety concern**: Emergency Escalation (24/7)
- **Production system down**: Insa SOC (24/7)
- **Rollback questions**: Project Manager (M-F) or Technical Support (M-F)
- **After-hours non-emergency**: Email, response next business day

---

## Appendix B: Rollback Checklist (Quick Reference)

**Print this page and use on-site**:

- [ ] **Phase 1: Immediate Mitigation**
  - [ ] Stop all agents (do not uninstall yet)
  - [ ] Stop jump box services
  - [ ] Verify impact stopped
  - [ ] Notify stakeholders
  - [ ] Preserve evidence

- [ ] **Phase 2: Agent Uninstallation**
  - [ ] Uninstall Windows agents (GPO or manual)
  - [ ] Uninstall Linux agents (Ansible or manual)
  - [ ] Remove embedded/IoT agents
  - [ ] Remove SNMP monitoring

- [ ] **Phase 3: Jump Box Decommissioning**
  - [ ] Drain local cache (optional)
  - [ ] Export configuration and logs
  - [ ] Stop and disable all services
  - [ ] Uninstall jump box software
  - [ ] Remove TLS certificates and credentials
  - [ ] Physical removal (power off, remove from rack)

- [ ] **Phase 4: Network Cleanup**
  - [ ] Remove firewall rules
  - [ ] Remove DNS entries
  - [ ] Release IP address
  - [ ] Update network diagram

- [ ] **Phase 5: Verification**
  - [ ] Sample agent verification (3-5 systems)
  - [ ] Jump box connectivity test (should fail)
  - [ ] Performance verification (OT systems)
  - [ ] DefectDojo verification

- [ ] **Phase 6: Documentation**
  - [ ] Create rollback completion report
  - [ ] Customer handoff meeting
  - [ ] Get customer sign-off
  - [ ] Internal lessons learned
  - [ ] Update Insa systems

- [ ] **Phase 7: Follow-Up**
  - [ ] 1-week follow-up (planned rollback)
  - [ ] 30-day follow-up (emergency rollback)

---

## Appendix C: Common Rollback Scenarios

### Scenario 1: Single Agent Causing Issues
**Situation**: One agent out of 50 is causing problems.

**Action**:
- Stop and uninstall ONLY the problematic agent
- Do NOT roll back entire deployment
- Investigate why that specific agent failed
- May be system-specific issue (antivirus conflict, old OS, etc.)

---

### Scenario 2: Jump Box Network Issues
**Situation**: Jump box cannot reach Insa SOC, but agents are fine.

**Action**:
- Do NOT uninstall agents (they will cache locally)
- Troubleshoot jump box network (firewall, routing)
- Agents can buffer data for up to 7 days
- Once jump box fixed, data syncs automatically

---

### Scenario 3: Customer Budget Cut Mid-Deployment
**Situation**: Customer cancels contract during Day 2 of deployment.

**Action**:
- Planned rollback (not emergency)
- Uninstall agents already deployed
- Return jump box to Insa (no installation in DMZ)
- Minimal cost to Insa (3 days labor)
- Maintain good relationship for future re-engagement

---

### Scenario 4: Regulatory Audit Failure
**Situation**: Customer's auditor says monitoring violates compliance.

**Action**:
- Emergency stop (stop agents, do not uninstall yet)
- Work with customer compliance team to resolve
- May be misunderstanding of regulations
- If confirmed violation, proceed with full rollback
- Document for legal protection

---

## Appendix D: Rollback SLA and Timing

### Emergency Rollback SLA
- **Stop agents**: Within 15 minutes of notification
- **Full rollback**: Within 4 hours (during business hours)
- **Verification**: Within 8 hours

### Planned Rollback SLA
- **Schedule**: 1 week notice preferred
- **Execution**: 1 business day on-site (or remote if possible)
- **Verification**: Same day
- **Documentation**: Within 2 business days

---

**Document Version**: 1.0
**Last Updated**: October 11, 2025
**Owner**: Insa Automation Corp
**Classification**: Internal Use - Field Technicians and Project Managers

---

*Made by Insa Automation Corp for OpSec Excellence*

**Rollback is not failure. It's protecting the customer.**
