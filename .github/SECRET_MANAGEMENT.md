# Secret Management Guide
## INSA Automation Corp - Security Best Practices

## 🚨 CRITICAL: Never Commit These

### Absolutely Forbidden in Git
- ❌ API keys (Claude, OpenAI, GitHub, Azure, AWS, etc.)
- ❌ Passwords (database, service accounts, admin credentials)
- ❌ Authentication tokens (OAuth, JWT, session tokens)
- ❌ Private keys (RSA, SSH, TLS/SSL certificates)
- ❌ Database credentials (connection strings, passwords)
- ❌ Service account credentials
- ❌ Webhook secrets
- ❌ Encryption keys
- ❌ License keys (commercial software)

## ✅ Approved Secret Management Methods

### 1. GitHub Secrets (Preferred for CI/CD)
```bash
# Add secret via GitHub CLI
gh secret set SECRET_NAME --body "secret-value"

# Or via GitHub Web UI
Settings → Secrets and variables → Actions → New repository secret
```

**Usage in Workflows:**
```yaml
steps:
  - name: Deploy with secret
    env:
      API_KEY: ${{ secrets.API_KEY }}
    run: ./deploy.sh
```

### 2. Environment Variables (Preferred for Local Dev)
```bash
# .env file (MUST be in .gitignore)
DATABASE_URL=postgresql://user:password@localhost/db
API_KEY=your-api-key-here
CLAUDE_API_KEY=sk-ant-api...

# Load in Python
from dotenv import load_dotenv
load_dotenv()

# Load in Node.js
require('dotenv').config()
```

### 3. Secret Management Tools (Enterprise)
- **HashiCorp Vault** (self-hosted or cloud)
- **AWS Secrets Manager** (for AWS infrastructure)
- **Azure Key Vault** (for Azure infrastructure)
- **1Password CLI** (team password manager)

### 4. MCP Server Configuration (Local Development)
```json
// ~/.mcp.json or ~/mcp-servers/*/config.json
{
  "api_key": "ENV:API_KEY",  // Load from environment
  "github_token": "VAULT:github/token"  // Load from Vault
}
```

## 🔍 Detection & Prevention

### GitHub Secret Scanning is ENABLED ✅
This repository has THREE layers of protection:

1. **GitHub Native Secret Scanning** (enabled)
   - Scans all commits for known secret patterns
   - Alerts appear in Security tab
   - Covers 200+ secret types from major providers

2. **Push Protection** (enabled) ⭐
   - **BLOCKS** commits containing detected secrets
   - Prevents secrets from entering repository
   - Must be bypassed manually (logged and audited)

3. **CI/CD Workflow Scanning** (`.github/workflows/secret-scan.yml`)
   - Gitleaks: Open-source secret scanner
   - TruffleHog: Entropy-based detection
   - Runs on every push and PR

### Custom Patterns (`.github/secret_scanning.yml`)
We scan for INSA-specific secrets:
- `insa_api_*` - INSA API keys
- `insa_token_*` - INSA service tokens
- Database connection strings
- Claude/Anthropic API keys
- Industrial IoT credentials (ThingsBoard, Modbus)

## 🚨 If You Accidentally Commit a Secret

### Immediate Actions (Within 5 Minutes)
1. **STOP** - Do not push if you haven't already
2. **REVOKE/ROTATE** the credential immediately
   - GitHub tokens: Settings → Developer settings → Tokens → Delete
   - Claude API: Anthropic Console → API Keys → Revoke
   - Database: `ALTER USER username WITH PASSWORD 'new_password';`

3. **Alert security team**
   ```bash
   # Email immediately
   To: w.aroca@insaing.com
   Subject: [URGENT] Secret Exposure in Git - [SECRET_TYPE]
   ```

### Cleanup Git History (If Already Pushed)

**Option 1: BFG Repo-Cleaner (Fastest)**
```bash
# Install BFG
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

# Remove secrets
java -jar bfg-1.14.0.jar --replace-text passwords.txt
java -jar bfg-1.14.0.jar --delete-files config.env

# Rewrite history
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force
```

**Option 2: git-filter-repo (More Control)**
```bash
# Install
pip install git-filter-repo

# Remove file from history
git filter-repo --path config/secrets.env --invert-paths

# Remove string pattern
git filter-repo --replace-text <(echo "ghp_OLD_TOKEN==>***REMOVED***")

# Force push
git push --force
```

**Option 3: GitHub API (Nuclear Option)**
```bash
# Delete entire repository (last resort)
gh repo delete WilBtc/InsaAutomationCorp --confirm

# Re-create clean repository
gh repo create WilBtc/InsaAutomationCorp --private
```

### Post-Incident Checklist
- [ ] Credential rotated/revoked
- [ ] Security team notified
- [ ] Git history cleaned
- [ ] Incident documented
- [ ] Root cause identified
- [ ] Preventive measures implemented

## 📋 Pre-Commit Checklist

Before every commit, ask yourself:

1. ✅ Are all `.env*` files in `.gitignore`?
2. ✅ Did I use environment variables for credentials?
3. ✅ Did I review `git diff` for hardcoded secrets?
4. ✅ Are config files using placeholders (e.g., `API_KEY=your-key-here`)?
5. ✅ Did I remove debug print statements with credentials?

## 🛡️ .gitignore Patterns (Auto-Updated)

Essential patterns for secret protection:
```gitignore
# Environment variables
.env
.env.*
.envrc
*.env
*.env.*

# Credentials
*secret*
*secrets*
*credential*
*credentials*
*.pem
*.key
*.p12
*.pfx

# Configuration with secrets
config.json
config.local.json
*-config.json
.mcp.json.local

# Cloud provider configs
.aws/credentials
.azure/credentials
gcp-keyfile.json

# SSH keys
id_rsa
id_ecdsa
id_ed25519
*.ppk
```

## 🔐 Secure Configuration Examples

### Python (Using python-dotenv)
```python
# ✅ CORRECT
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv('CLAUDE_API_KEY')

# ❌ WRONG
API_KEY = "sk-ant-api03-xyz..."  # Never hardcode!
```

### Node.js (Using dotenv)
```javascript
// ✅ CORRECT
require('dotenv').config();
const apiKey = process.env.CLAUDE_API_KEY;

// ❌ WRONG
const apiKey = "sk-ant-api03-xyz...";  // Never hardcode!
```

### Docker Compose
```yaml
# ✅ CORRECT - Use environment variables
version: '3'
services:
  app:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - API_KEY=${API_KEY}

# ❌ WRONG - Hardcoded secrets
services:
  app:
    environment:
      - DATABASE_URL=postgresql://user:password123@db/prod
```

### GitHub Actions
```yaml
# ✅ CORRECT - Use GitHub Secrets
- name: Deploy
  env:
    API_KEY: ${{ secrets.API_KEY }}
  run: ./deploy.sh

# ❌ WRONG - Hardcoded in workflow
- name: Deploy
  env:
    API_KEY: sk-ant-api03-xyz...
```

## 📊 Secret Scanning Reports

### View Alerts
```bash
# List secret scanning alerts
gh api /repos/WilBtc/InsaAutomationCorp/secret-scanning/alerts

# View specific alert
gh api /repos/WilBtc/InsaAutomationCorp/secret-scanning/alerts/1
```

### Resolve Alerts
1. Revoke the exposed credential
2. Remove from git history
3. Mark alert as resolved in GitHub
   - Security → Secret scanning → [Alert] → Resolve → Revoked

## 🎓 Training Resources

- [GitHub Secret Scanning Docs](https://docs.github.com/en/code-security/secret-scanning)
- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [12-Factor App: Config](https://12factor.net/config)

## 📞 Security Contacts

- **Primary:** Wil Aroca (w.aroca@insaing.com)
- **Secondary:** Juan Casas (j.casas@insaing.com)
- **Emergency:** Create GitHub Issue with `security` label

---

**Remember:** Secrets in git history are **PERMANENT** unless actively removed. Prevention is 100x easier than cleanup.

---

## 🤖 For AI Agents & Automation

### GitHub Access for Agents

AI agents (Claude Code, automation scripts, CI/CD) should use GitHub CLI for authentication:

```bash
# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo "ERROR: GitHub CLI not authenticated"
    echo "Run: gh auth login"
    exit 1
fi

# Use gh commands
gh api /repos/WilBtc/InsaAutomationCorp/secret-scanning/alerts
```

**See**: `.github/AGENT_GITHUB_ACCESS_GUIDE.md` for complete agent documentation

### Automated Security Monitoring

**Tools Deployed**:
- `security-incident-handler.sh` - Main CLI tool for security alerts
- `automated-security-monitor.sh` - Runs every 6 hours via cron
- `rotate-credentials.sh` - Interactive credential rotation

**Check for alerts**:
```bash
cd ~/InsaAutomationCorp
./security-incident-handler.sh list
```

**Monitor logs**:
```bash
tail -f ~/security-incidents/monitor.log
```

---

## 📊 Real Incident: December 8, 2025

### What Happened
- **Alert #1**: Grafana Service Account Token exposed in `.mcp.json`
- **Alert #2**: SMTP credentials and admin passwords in Git history (July 2024)

### What We Did
1. ✅ Used BFG Repo-Cleaner to remove secrets from all Git history
2. ✅ Force pushed cleaned history to GitHub (662 commits modified, 1,823 refs updated)
3. ✅ Resolved GitHub security alerts
4. ✅ Deployed automated monitoring system
5. ✅ Created incident response tools

### Lessons Learned
1. **Don't commit config files with secrets** - Use environment variables or move outside repo
2. **Monitor alerts regularly** - Automated checks every 6 hours now active
3. **Respond quickly** - Tools now in place for immediate response
4. **Git history is permanent** - Requires force push to clean

### Time to Resolution
- **Before**: Months (alerts unnoticed)
- **After**: Minutes (automated detection + CLI tools)

**Full Report**: `~/SECURITY_ISSUES_FIXED_DEC8_2025.md`

---

## 🆘 If You Discover a Secret in Git

**STOP and follow these steps immediately:**

1. **Assess** - Is it in current files or just Git history?
   ```bash
   # Check current files
   ./security-incident-handler.sh scan

   # Check GitHub alerts
   ./security-incident-handler.sh list
   ```

2. **Rotate** - Change the credential immediately
   ```bash
   ./rotate-credentials.sh <type>
   # Types: smtp, github-token, api-key
   ```

3. **Clean History** - Remove from Git using BFG
   ```bash
   # Download BFG
   wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

   # Create backup
   git clone --mirror https://github.com/WilBtc/InsaAutomationCorp.git ../backup.git

   # Remove secret
   echo "SECRET_TO_REMOVE" > /tmp/secrets.txt
   java -jar bfg-1.14.0.jar --replace-text /tmp/secrets.txt .git

   # Clean up
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive

   # Force push (rewrites history!)
   git push --force origin main

   # Secure cleanup
   shred -vfz -n 10 /tmp/secrets.txt
   ```

4. **Resolve Alert** - Mark GitHub alert as fixed
   ```bash
   ./security-incident-handler.sh resolve <alert_number> --reason revoked
   ```

5. **Document** - Record what happened and how you fixed it

**Quick Reference**: `SECURITY_CLI_QUICK_REFERENCE.md`

---

**Remember:** Secrets in git history are **PERMANENT** unless actively removed. Prevention is 100x easier than cleanup.

Last Updated: December 8, 2025 (Post-Incident Update)
