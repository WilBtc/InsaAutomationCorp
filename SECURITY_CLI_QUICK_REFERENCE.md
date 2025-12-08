# Security CLI Tools - Quick Reference
**INSA Automation Corp - Security Incident Management**
**Created**: December 8, 2025

---

## 🚨 Current Status

**ACTIVE ALERT**: Grafana Service Account Token exposed in `.mcp.json:120`
- Alert #1: Detected November 4, 2025
- Location: `.mcp.json` line 120 (commit: 120010b)
- **Action Required**: Rotate and remove from Git history

---

## Quick Commands

### Check for Security Alerts
```bash
cd ~/InsaAutomationCorp

# List all alerts
./security-incident-handler.sh list

# Check for new alerts and generate reports
./security-incident-handler.sh check

# Get details for specific alert
./security-incident-handler.sh details 1
```

### Rotate Exposed Credentials
```bash
# SMTP credentials
./rotate-credentials.sh smtp

# GitHub token
./rotate-credentials.sh github-token

# Generic API key
./rotate-credentials.sh api-key
```

### Resolve Alerts (After Fixing)
```bash
# After rotating credentials and cleaning history
./security-incident-handler.sh resolve 1 --reason revoked --comment "Token rotated and removed"

# Other resolution options:
# --reason false_positive  (not actually a secret)
# --reason wont_fix        (accepted risk)
# --reason used_in_tests   (test data only)
```

---

## 🔧 Automated Monitoring Setup

### Install Cron Job (Checks every 6 hours)
```bash
cd ~/InsaAutomationCorp

# Add to crontab
(crontab -l 2>/dev/null; echo "0 */6 * * * $HOME/InsaAutomationCorp/automated-security-monitor.sh") | crontab -

# Verify installation
crontab -l | grep security-monitor
```

### Manual Monitoring Run
```bash
# Run monitor manually
~/InsaAutomationCorp/automated-security-monitor.sh

# Check monitor logs
tail -f ~/security-incidents/monitor.log
```

---

## 🛡️ Enable Secret Scanning (If Not Already)

```bash
cd ~/InsaAutomationCorp

# Enable secret scanning with push protection
./security-incident-handler.sh enable

# Verify it's enabled
gh api /repos/WilBtc/InsaAutomationCorp | jq '.security_and_analysis'
```

---

## 🧹 Clean Git History (Remove Exposed Secrets)

### Method 1: BFG Repo-Cleaner (Recommended)
```bash
cd ~/InsaAutomationCorp

# Backup first
git clone --mirror https://github.com/WilBtc/InsaAutomationCorp.git ../backup.git

# Download BFG
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

# For Grafana token in .mcp.json
# Option A: Remove entire file from history
java -jar bfg-1.14.0.jar --delete-files .mcp.json .git

# Option B: Replace specific token pattern
echo "glsa_EXPOSED_TOKEN_HERE" > /tmp/secrets.txt
java -jar bfg-1.14.0.jar --replace-text /tmp/secrets.txt .git
shred -vfz -n 10 /tmp/secrets.txt

# Clean up
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (CAREFUL - rewrites history)
git push --force --all
git push --force --tags
```

### Method 2: git-filter-repo
```bash
# Install
pip install git-filter-repo

# Remove file completely
git filter-repo --path .mcp.json --invert-paths

# Or replace specific string
git filter-repo --replace-text <(echo "glsa_OLD_TOKEN==>***REMOVED***")

# Force push
git push --force --all
```

---

## 📋 Fix Current Grafana Token Issue

### Step 1: Generate New Grafana Token
```bash
# If you have access to Grafana UI
# 1. Login to Grafana: http://your-grafana-url
# 2. Administration → Service Accounts
# 3. Find "MCP Server" or similar
# 4. Delete old token
# 5. Generate new token with same permissions
# 6. Copy the new token

# Or via Grafana API
GRAFANA_URL="http://localhost:3000"
GRAFANA_ADMIN_TOKEN="your-admin-token"

# Create new service account token
curl -X POST "${GRAFANA_URL}/api/serviceaccounts/1/tokens" \
  -H "Authorization: Bearer ${GRAFANA_ADMIN_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name":"MCP Server - Dec 2025","role":"Admin"}'
```

### Step 2: Update .mcp.json Securely
```bash
cd ~/InsaAutomationCorp

# OPTION A: Move .mcp.json out of git
cp .mcp.json ~/.mcp.json
echo ".mcp.json" >> .gitignore
git rm --cached .mcp.json
git commit -m "security: Remove .mcp.json from git, moved to ~/.mcp.json"

# OPTION B: Use environment variable
# Edit .mcp.json to use: "token": "${GRAFANA_TOKEN}"
# Then set in environment:
echo "GRAFANA_TOKEN=glsa_NEW_TOKEN_HERE" >> ~/.env
chmod 600 ~/.env
```

### Step 3: Remove from Git History
```bash
# Use BFG method above, then:
./security-incident-handler.sh resolve 1 --reason revoked --comment "Grafana token rotated and removed from history"
```

---

## 🎯 Handling SMTP Alert (From GitGuardian)

The SMTP alert from July 2024 is likely already removed from current files but exists in history.

### Step 1: Verify Current State
```bash
cd ~/InsaAutomationCorp

# Search for SMTP credentials
./security-incident-handler.sh scan | grep -i smtp

# Check specific files
grep -r "smtp.*password" . --exclude-dir=.git 2>/dev/null
```

### Step 2: Rotate SMTP Credentials
```bash
./rotate-credentials.sh smtp
```

### Step 3: Clean Git History
```bash
# Create file with old password
echo "OLD_SMTP_PASSWORD" > /tmp/smtp-secrets.txt

# Remove from history
java -jar bfg-1.14.0.jar --replace-text /tmp/smtp-secrets.txt .git

# Clean and push
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force --all

# Secure cleanup
shred -vfz -n 10 /tmp/smtp-secrets.txt
```

---

## 📊 Monitoring & Alerts

### Check Monitor Status
```bash
# View recent monitor activity
tail -50 ~/security-incidents/monitor.log

# Check when last run
stat ~/security-incidents/.last_check

# Check current alert count
cat ~/security-incidents/.last_check
```

### Email Notifications
The automated monitor sends emails to: w.aroca@insaing.com

To configure email alerts:
```bash
# Edit the monitor script
nano ~/InsaAutomationCorp/automated-security-monitor.sh

# Change ALERT_EMAIL variable
ALERT_EMAIL="your-email@example.com"
```

---

## 🔍 Scan Current Files for Secrets

```bash
cd ~/InsaAutomationCorp

# Scan all current files
./security-incident-handler.sh scan

# More thorough scan with gitleaks
docker run --rm -v $(pwd):/repo zricethezav/gitleaks:latest detect --source /repo --verbose

# Or with truffleHog
docker run --rm -v $(pwd):/repo trufflesecurity/trufflehog:latest filesystem /repo
```

---

## 🚀 Post-Incident Checklist

After resolving a security incident:

- [ ] Credential rotated/revoked
- [ ] New credential stored securely (not in git)
- [ ] Git history cleaned (force pushed)
- [ ] GitHub alert resolved
- [ ] `.gitignore` updated
- [ ] Team notified (if applicable)
- [ ] Incident documented
- [ ] Monitoring enabled/verified
- [ ] Pre-commit hooks installed

---

## 📞 Support & Documentation

**Tools Documentation:**
- Main handler: `~/InsaAutomationCorp/security-incident-handler.sh help`
- Credential rotation: `~/InsaAutomationCorp/rotate-credentials.sh help`
- Incident reports: `~/security-incidents/`

**GitHub Resources:**
- Secret scanning: https://github.com/WilBtc/InsaAutomationCorp/security/secret-scanning
- Security policy: `~/InsaAutomationCorp/.github/SECRET_MANAGEMENT.md`

**Contact:**
- Security Lead: w.aroca@insaing.com
- GitHub Issues: https://github.com/WilBtc/InsaAutomationCorp/issues

---

## 🎓 Prevention Best Practices

1. **Never commit secrets** - Use environment variables or secret management tools
2. **Review before commit** - Always check `git diff` before pushing
3. **Use .gitignore** - Add all files with secrets (.env, config.json, etc.)
4. **Enable push protection** - Blocks commits with detected secrets
5. **Regular scans** - Automated monitoring catches issues early
6. **Rotate regularly** - Change credentials periodically even without exposure
7. **Use service accounts** - Limit permissions and scope

---

**Last Updated**: December 8, 2025
**Version**: 1.0
**Status**: Production Ready
