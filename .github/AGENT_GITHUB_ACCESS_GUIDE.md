# Agent GitHub Access Guide
**For AI Agents & Automation Tools**
**INSA Automation Corp - Security & Access Control**
**Last Updated**: December 8, 2025

---

## 🎯 Purpose

This guide explains how AI agents (Claude Code, custom automation, CI/CD bots) should access GitHub securely and handle security alerts automatically.

---

## 🔐 Authentication Methods

### Method 1: GitHub CLI (Recommended for Interactive Agents)

**Best for**: Claude Code, interactive CLI agents, manual operations

**Setup**:
```bash
# Install GitHub CLI
sudo apt update
sudo apt install gh

# Authenticate (interactive)
gh auth login

# Follow prompts:
# 1. Choose: GitHub.com
# 2. Choose: HTTPS
# 3. Authenticate with: Login with a web browser (or paste token)
# 4. Copy one-time code and open browser

# Verify authentication
gh auth status
```

**Advantages**:
- ✅ Interactive authentication (no hardcoded tokens)
- ✅ Automatic token refresh
- ✅ Scoped permissions
- ✅ Works with 2FA
- ✅ Can be used by multiple tools

**Usage in Scripts**:
```bash
#!/bin/bash
# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "ERROR: GitHub CLI not authenticated"
    echo "Run: gh auth login"
    exit 1
fi

# Use gh commands
gh api /repos/WilBtc/InsaAutomationCorp/secret-scanning/alerts
gh issue create --title "Security Alert" --body "Details..."
gh pr create --title "Fix" --body "Description..."
```

---

### Method 2: Personal Access Token (PAT)

**Best for**: Automated scripts, CI/CD, headless environments

**Create Token**:
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: "INSA Automation Agent - [Purpose]"
4. Select scopes:
   - `repo` (full control of private repositories)
   - `workflow` (update GitHub Action workflows)
   - `read:org` (read organization data)
   - `write:packages` (if needed for packages)
5. Generate token and **copy immediately**

**Store Securely**:
```bash
# Option A: In .env file (NOT in git)
echo "GITHUB_TOKEN=ghp_xxxxxxxxxxxx" >> ~/.env
chmod 600 ~/.env

# Option B: In environment variable
export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"

# Add to ~/.bashrc for persistence
echo 'export GITHUB_TOKEN="ghp_xxxxxxxxxxxx"' >> ~/.bashrc
```

**Usage in Scripts**:
```bash
#!/bin/bash
# Load from .env
source ~/.env

# Or use directly from environment
GITHUB_TOKEN="${GITHUB_TOKEN}"

# Use with gh CLI
gh auth login --with-token <<< "$GITHUB_TOKEN"

# Use with API directly
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/WilBtc/InsaAutomationCorp/secret-scanning/alerts
```

---

### Method 3: GitHub App (Enterprise)

**Best for**: Organization-wide automation, multiple repositories

**Not covered here** - Contact GitHub support for setup

---

## 🤖 For AI Agents (Claude Code, etc.)

### How Claude Code Should Access GitHub

**Preferred Method**: Use GitHub CLI (gh)

**Why**:
1. Already authenticated via `gh auth login`
2. No need to manage tokens
3. Automatic authentication
4. Secure and auditable

**Example Pattern**:
```bash
# Agent checks authentication first
if ! gh auth status &> /dev/null; then
    echo "⚠️  GitHub CLI not authenticated"
    echo "User needs to run: gh auth login"
    exit 1
fi

# Agent can now safely use gh commands
gh api /user
gh repo list
gh issue list
```

### Security Alert Handling Workflow

**When agent detects a security issue:**

```bash
#!/bin/bash
# 1. Check for security alerts
ALERTS=$(gh api /repos/WilBtc/InsaAutomationCorp/secret-scanning/alerts \
  --jq '[.[] | select(.state == "open")] | length')

if [ "$ALERTS" -gt 0 ]; then
    echo "🚨 Found $ALERTS open security alert(s)"

    # 2. Generate incident report
    ./security-incident-handler.sh check

    # 3. Notify user
    echo "Reports generated in: ~/security-incidents/"
    echo "Review and follow remediation steps"

    # 4. For automated fixing (optional):
    # - Rotate credentials using: ./rotate-credentials.sh
    # - Clean git history using: BFG Repo-Cleaner
    # - Resolve alert: ./security-incident-handler.sh resolve <number>
fi
```

---

## 📋 Best Practices for Agents

### 1. Always Check Authentication First

```bash
check_github_auth() {
    if ! gh auth status &> /dev/null; then
        echo "❌ ERROR: GitHub not authenticated"
        echo "👉 Run: gh auth login"
        return 1
    fi
    return 0
}

# Use in scripts
if ! check_github_auth; then
    exit 1
fi
```

### 2. Use Read-Only When Possible

```bash
# Safe - read operations
gh api /repos/WilBtc/InsaAutomationCorp
gh api /repos/WilBtc/InsaAutomationCorp/secret-scanning/alerts

# Requires confirmation - write operations
gh issue create
gh pr create
```

### 3. Verify Before Destructive Operations

```bash
# DANGEROUS - requires user confirmation
force_push() {
    echo "⚠️  WARNING: This will rewrite Git history!"
    echo "Repository: $REPO"
    echo "Branch: $BRANCH"
    read -p "Type 'YES' to confirm: " confirm

    if [ "$confirm" != "YES" ]; then
        echo "Aborted"
        return 1
    fi

    git push --force origin "$BRANCH"
}
```

### 4. Log All Actions

```bash
LOG_FILE="$HOME/agent-activity.log"

log_action() {
    local action="$1"
    echo "[$(date)] $action" >> "$LOG_FILE"
}

# Usage
log_action "Checked security alerts: found 2 open"
log_action "Generated incident report: ~/security-incidents/incident_1_20251208.md"
```

### 5. Handle Rate Limits

```bash
# Check rate limit before intensive operations
check_rate_limit() {
    local remaining=$(gh api /rate_limit --jq '.resources.core.remaining')
    local limit=$(gh api /rate_limit --jq '.resources.core.limit')

    echo "GitHub API Rate Limit: $remaining/$limit remaining"

    if [ "$remaining" -lt 100 ]; then
        echo "⚠️  WARNING: Low rate limit remaining"
        return 1
    fi
    return 0
}
```

---

## 🔒 Security Alert Automation

### Automated Response Workflow

**File**: `automated-security-monitor.sh` (already deployed)

**How it works**:
1. Runs every 6 hours via cron
2. Checks for new security alerts using `gh api`
3. If new alerts found:
   - Generates detailed incident report
   - Sends email notification
   - Logs to audit trail
4. User reviews and takes action

**Configuration**:
```bash
# Location
~/InsaAutomationCorp/automated-security-monitor.sh

# Cron schedule
0 */6 * * * ~/InsaAutomationCorp/automated-security-monitor.sh

# Email recipient (edit in script)
ALERT_EMAIL="w.aroca@insaing.com"

# Log file
~/security-incidents/monitor.log
```

---

## 🛠️ Common Agent Operations

### Check for Security Alerts

```bash
# List all alerts
gh api /repos/WilBtc/InsaAutomationCorp/secret-scanning/alerts \
  --jq '.[] | {number, state, secret_type: .secret_type_display_name}'

# Count open alerts
gh api /repos/WilBtc/InsaAutomationCorp/secret-scanning/alerts \
  --jq '[.[] | select(.state == "open")] | length'

# Get specific alert details
gh api /repos/WilBtc/InsaAutomationCorp/secret-scanning/alerts/1
```

### Create Issue from Security Alert

```bash
#!/bin/bash
create_security_issue() {
    local alert_number="$1"
    local alert=$(gh api "/repos/WilBtc/InsaAutomationCorp/secret-scanning/alerts/$alert_number")

    local secret_type=$(echo "$alert" | jq -r '.secret_type_display_name')
    local created=$(echo "$alert" | jq -r '.created_at')

    gh issue create \
      --title "🚨 Security: $secret_type exposed" \
      --body "Alert #$alert_number detected on $created

See: https://github.com/WilBtc/InsaAutomationCorp/security/secret-scanning/$alert_number

**Immediate Actions Required:**
1. Rotate/revoke the exposed credential
2. Remove from Git history using BFG Repo-Cleaner
3. Resolve alert: \`./security-incident-handler.sh resolve $alert_number\`

**Documentation:**
- Quick Reference: \`SECURITY_CLI_QUICK_REFERENCE.md\`
- Incident Handler: \`./security-incident-handler.sh help\`
" \
      --label "security,urgent" \
      --assignee "WilBtc"
}

# Usage
create_security_issue 1
```

### Resolve Alert After Fixing

```bash
#!/bin/bash
resolve_security_alert() {
    local alert_number="$1"
    local resolution="${2:-revoked}"  # revoked, false_positive, wont_fix, used_in_tests
    local comment="$3"

    gh api -X PATCH "/repos/WilBtc/InsaAutomationCorp/secret-scanning/alerts/$alert_number" \
      -f state=resolved \
      -f resolution="$resolution" \
      -f resolution_comment="$comment"

    echo "✅ Alert #$alert_number resolved ($resolution)"
}

# Usage
resolve_security_alert 1 revoked "Token rotated and removed from Git history on Dec 8, 2025"
```

---

## 📚 Reference: GitHub API Endpoints

### Secret Scanning

```bash
# List all secret scanning alerts
GET /repos/{owner}/{repo}/secret-scanning/alerts

# Get specific alert
GET /repos/{owner}/{repo}/secret-scanning/alerts/{alert_number}

# Get alert locations (where secret appears)
GET /repos/{owner}/{repo}/secret-scanning/alerts/{alert_number}/locations

# Update alert (resolve/reopen)
PATCH /repos/{owner}/{repo}/secret-scanning/alerts/{alert_number}

# Response format
{
  "state": "resolved",
  "resolution": "revoked",
  "resolution_comment": "Credential rotated"
}
```

### Repository

```bash
# Get repository info
GET /repos/{owner}/{repo}

# Get security settings
GET /repos/{owner}/{repo}
# Returns: .security_and_analysis.secret_scanning.status

# Enable secret scanning
PATCH /repos/{owner}/{repo}
{
  "security_and_analysis": {
    "secret_scanning": {"status": "enabled"},
    "secret_scanning_push_protection": {"status": "enabled"}
  }
}
```

### Issues

```bash
# Create issue
POST /repos/{owner}/{repo}/issues

# List issues
GET /repos/{owner}/{repo}/issues

# Update issue
PATCH /repos/{owner}/{repo}/issues/{issue_number}
```

---

## 🚨 Emergency Response Template

**When agent detects critical security exposure:**

```bash
#!/bin/bash
# Emergency Security Response Script

ALERT_NUMBER="$1"
REPO="WilBtc/InsaAutomationCorp"

echo "🚨 EMERGENCY SECURITY RESPONSE"
echo "================================"
echo "Alert: #$ALERT_NUMBER"
echo "Repository: $REPO"
echo "Time: $(date)"
echo ""

# 1. Get alert details
echo "📋 Fetching alert details..."
ALERT=$(gh api "/repos/$REPO/secret-scanning/alerts/$ALERT_NUMBER")
SECRET_TYPE=$(echo "$ALERT" | jq -r '.secret_type_display_name')

echo "Secret Type: $SECRET_TYPE"
echo ""

# 2. Create incident report
echo "📝 Generating incident report..."
./security-incident-handler.sh check

# 3. Create GitHub issue
echo "🎫 Creating GitHub issue..."
gh issue create \
  --title "🚨 CRITICAL: $SECRET_TYPE Exposure - Alert #$ALERT_NUMBER" \
  --body "**CRITICAL SECURITY INCIDENT**

Alert #$ALERT_NUMBER requires immediate attention.

**Detected**: $(date)
**Type**: $SECRET_TYPE

**IMMEDIATE ACTIONS REQUIRED**:
1. ⚠️  Rotate/revoke exposed credential NOW
2. 🧹 Clean from Git history using BFG
3. ✅ Resolve alert after fixing

**Resources**:
- Incident Report: \`~/security-incidents/\`
- Quick Reference: \`SECURITY_CLI_QUICK_REFERENCE.md\`
- Rotation Tool: \`./rotate-credentials.sh\`

**Status**: OPEN - Awaiting remediation
" \
  --label "security,critical,urgent" \
  --assignee "WilBtc"

# 4. Send email notification
echo "📧 Sending email notification..."
mail -s "🚨 CRITICAL: Security Alert #$ALERT_NUMBER" w.aroca@insaing.com << EOF
CRITICAL SECURITY ALERT

Alert: #$ALERT_NUMBER
Type: $SECRET_TYPE
Repository: $REPO
Time: $(date)

IMMEDIATE ACTION REQUIRED:
1. Review incident report in ~/security-incidents/
2. Rotate exposed credentials
3. Clean Git history
4. Resolve alert

Tools:
- ./security-incident-handler.sh details $ALERT_NUMBER
- ./rotate-credentials.sh
- ./security-incident-handler.sh resolve $ALERT_NUMBER

This is an automated alert from INSA Security Monitor.
EOF

echo ""
echo "✅ Emergency response complete"
echo "📋 Review incident report: ~/security-incidents/"
echo "🎫 GitHub issue created"
echo "📧 Email notification sent"
```

---

## 🔍 Troubleshooting

### Issue: "gh: command not found"

```bash
# Install GitHub CLI
sudo apt update
sudo apt install gh

# Or via snap
sudo snap install gh
```

### Issue: "gh auth status" fails

```bash
# Re-authenticate
gh auth logout
gh auth login

# Check token permissions
gh auth status -t
```

### Issue: Rate limit exceeded

```bash
# Check rate limit
gh api /rate_limit

# Wait for reset or use different authentication
# Rate limits reset every hour
```

### Issue: Permission denied

```bash
# Check token scopes
gh auth status -t

# Token needs these scopes:
# - repo (for private repos)
# - workflow (for actions)
# - read:org (for organization)

# Generate new token with correct scopes
```

---

## 📖 Additional Resources

**GitHub Documentation**:
- [Secret Scanning API](https://docs.github.com/en/rest/secret-scanning)
- [GitHub CLI Manual](https://cli.github.com/manual/)
- [Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

**INSA Documentation**:
- Security CLI Tools: `SECURITY_CLI_QUICK_REFERENCE.md`
- Secret Management: `.github/SECRET_MANAGEMENT.md`
- Incident Handler: `./security-incident-handler.sh help`

**Tools**:
- GitHub CLI: https://cli.github.com/
- BFG Repo-Cleaner: https://rtyley.github.io/bfg-repo-cleaner/
- Gitleaks: https://github.com/gitleaks/gitleaks

---

## ✅ Quick Reference

```bash
# Authentication
gh auth login                    # Authenticate GitHub CLI
gh auth status                   # Check authentication
gh auth refresh                  # Refresh token

# Security Alerts
gh api /repos/OWNER/REPO/secret-scanning/alerts                    # List alerts
gh api /repos/OWNER/REPO/secret-scanning/alerts/1                  # Get alert details
gh api /repos/OWNER/REPO/secret-scanning/alerts/1/locations        # Get locations

# Resolve Alert
gh api -X PATCH /repos/OWNER/REPO/secret-scanning/alerts/1 \
  -f state=resolved \
  -f resolution=revoked \
  -f resolution_comment="Fixed"

# Custom Tools
./security-incident-handler.sh list        # List all alerts
./security-incident-handler.sh check       # Check for new alerts
./security-incident-handler.sh resolve 1   # Resolve alert #1
./rotate-credentials.sh smtp               # Rotate SMTP credentials
```

---

**Version**: 1.0
**Last Updated**: December 8, 2025
**Maintained by**: INSA Automation Corp Security Team
**Contact**: w.aroca@insaing.com
