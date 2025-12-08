# Security System - Complete Index
**INSA Automation Corp**
**Last Updated**: December 8, 2025

---

## 🎯 Start Here

**New to the security system?** → Read `SECURITY_TOOLS_README.md`

**AI Agent or automation tool?** → Read `.github/AGENT_GITHUB_ACCESS_GUIDE.md`

**Security alert received?** → Run `./security-incident-handler.sh details <number>`

---

## 📚 Documentation Map

### Quick Start
- **`SECURITY_TOOLS_README.md`** - Getting started guide
- **`SECURITY_CLI_QUICK_REFERENCE.md`** - Command cheat sheet

### For AI Agents & Automation
- **`.github/AGENT_GITHUB_ACCESS_GUIDE.md`** ⭐ Primary guide for agents
- **`.github/SECRET_MANAGEMENT.md`** - Security policies and best practices

### Historical Records
- **`~/SECURITY_ISSUES_FIXED_DEC8_2025.md`** - Incident report (Dec 8)
- **`~/SECURITY_INCIDENT_SMTP_EXPOSURE_DEC8_2025.md`** - SMTP details
- **`~/SECURITY_CLI_DEPLOYMENT_COMPLETE_DEC8_2025.md`** - Tool deployment
- **`~/DOCUMENTATION_COMPLETE_DEC8_2025.md`** - Documentation summary

---

## 🛠️ Tools Reference

### CLI Tools (in `~/InsaAutomationCorp/`)

**Main Tool**:
```bash
./security-incident-handler.sh
  list              # List all alerts
  check             # Check for new alerts
  details <num>     # Get alert details
  resolve <num>     # Resolve alert
  enable            # Enable secret scanning
  scan              # Scan current files
  help              # Show usage
```

**Credential Rotation**:
```bash
./rotate-credentials.sh
  smtp              # Rotate SMTP credentials
  github-token      # Rotate GitHub token
  api-key           # Rotate generic API key
  help              # Show usage
```

**Automated Monitor**:
```bash
~/InsaAutomationCorp/automated-security-monitor.sh
# Runs automatically every 6 hours via cron
# Logs: ~/security-incidents/monitor.log
```

---

## 🔍 Quick Commands

### Check Current Status
```bash
cd ~/InsaAutomationCorp
./security-incident-handler.sh list
tail ~/security-incidents/monitor.log
```

### Handle New Alert
```bash
# 1. Get details
./security-incident-handler.sh details <alert_number>

# 2. Rotate credential
./rotate-credentials.sh <type>

# 3. Clean history (see SECURITY_CLI_QUICK_REFERENCE.md)

# 4. Resolve
./security-incident-handler.sh resolve <alert_number> --reason revoked
```

---

## 🤖 For AI Agents

**Authentication**:
```bash
# Check if authenticated
gh auth status || exit 1
```

**Check Alerts**:
```bash
# Use CLI tool (recommended)
./security-incident-handler.sh list

# Or use gh directly
gh api /repos/WilBtc/InsaAutomationCorp/secret-scanning/alerts
```

**Complete Guide**: `.github/AGENT_GITHUB_ACCESS_GUIDE.md`

---

## 📊 System Status

**Current State** (as of Dec 8, 2025):
- ✅ 0 open security alerts
- ✅ Automated monitoring active (every 6 hours)
- ✅ Email notifications enabled
- ✅ All tools deployed and tested
- ✅ Documentation complete

**Monitor Status**:
```bash
# Check cron
crontab -l | grep security-monitor

# Check logs
ls -lh ~/security-incidents/
```

---

## 🎓 Learning Resources

### Real-World Examples
- **Grafana Token Incident** - See `SECURITY_ISSUES_FIXED_DEC8_2025.md`
- **SMTP Credentials** - See `SECURITY_INCIDENT_SMTP_EXPOSURE_DEC8_2025.md`
- **Complete Response** - Both incidents fully documented

### Best Practices
- Never commit secrets to Git
- Use environment variables (`.env` files)
- Review `git diff` before committing
- Enable GitHub secret scanning
- Respond to alerts within 24 hours

### Tools to Know
- **BFG Repo-Cleaner** - Clean Git history
- **GitHub CLI (gh)** - GitHub automation
- **git-filter-repo** - Alternative history cleaner
- **Gitleaks** - Secret detection (CI/CD)

---

## 🆘 Emergency Contacts

**Security Lead**: w.aroca@insaing.com

**GitHub**:
- Alerts: https://github.com/WilBtc/InsaAutomationCorp/security/secret-scanning
- Issues: https://github.com/WilBtc/InsaAutomationCorp/issues

**Automated Notifications**: Configured to alert w.aroca@insaing.com

---

## 🔄 Regular Maintenance

### Weekly
- [ ] Check security alerts: `./security-incident-handler.sh list`
- [ ] Review monitor log: `tail ~/security-incidents/monitor.log`
- [ ] Verify cron is running: `crontab -l`

### Monthly
- [ ] Review and update documentation
- [ ] Test credential rotation workflow
- [ ] Audit `.gitignore` patterns
- [ ] Check GitHub secret scanning settings

### Quarterly
- [ ] Rotate credentials (even without exposure)
- [ ] Review and update security policies
- [ ] Test emergency response procedures
- [ ] Update team on security practices

---

## 📂 File Locations

### Repository (`~/InsaAutomationCorp/`)
```
├── security-incident-handler.sh
├── automated-security-monitor.sh
├── rotate-credentials.sh
├── SECURITY_INDEX.md (this file)
├── SECURITY_TOOLS_README.md
├── SECURITY_CLI_QUICK_REFERENCE.md
└── .github/
    ├── AGENT_GITHUB_ACCESS_GUIDE.md
    └── SECRET_MANAGEMENT.md
```

### Home Directory (`~/`)
```
├── SECURITY_ISSUES_FIXED_DEC8_2025.md
├── SECURITY_INCIDENT_SMTP_EXPOSURE_DEC8_2025.md
├── SECURITY_CLI_DEPLOYMENT_COMPLETE_DEC8_2025.md
├── DOCUMENTATION_COMPLETE_DEC8_2025.md
├── security-incidents/
│   ├── monitor.log
│   ├── .last_check
│   └── incident_*.md (auto-generated reports)
└── InsaAutomationCorp-backup-20251208.git/ (449MB backup)
```

---

## 🎯 Key Concepts

### Secret Scanning
GitHub automatically scans commits for exposed secrets. When found, creates an alert that requires remediation.

### Git History Cleaning
Removing a file doesn't remove it from Git history. Must use BFG Repo-Cleaner or git-filter-repo to truly remove secrets.

### Force Push
Required after cleaning history. Rewrites remote repository. Anyone with local clones must re-clone or reset.

### Credential Rotation
Changing exposed credentials makes old ones useless. Always rotate BEFORE cleaning history for safety.

---

## 💡 Quick Tips

1. **For Users**: Start with `SECURITY_TOOLS_README.md`
2. **For Agents**: Start with `.github/AGENT_GITHUB_ACCESS_GUIDE.md`
3. **For Alerts**: Use `./security-incident-handler.sh`
4. **For History**: See `SECURITY_CLI_QUICK_REFERENCE.md`
5. **For Examples**: See real incidents in documentation

---

## ✅ Checklist for New Team Members

- [ ] Read `SECURITY_TOOLS_README.md`
- [ ] Read `.github/SECRET_MANAGEMENT.md`
- [ ] Authenticate GitHub CLI: `gh auth login`
- [ ] Test security tools: `./security-incident-handler.sh list`
- [ ] Review real incident: `SECURITY_ISSUES_FIXED_DEC8_2025.md`
- [ ] Set up `.env` files (with `.gitignore`)
- [ ] Subscribe to security notifications

---

**Everything you need is documented. Start with the guides above!** 📚

**Version**: 1.0
**Status**: ✅ Production Ready
**Maintained by**: INSA Automation Corp Security Team
