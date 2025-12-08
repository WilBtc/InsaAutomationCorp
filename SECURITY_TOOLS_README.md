# Security Tools - Quick Start
**INSA Automation Corp - Automated Security Management**

---

## 🛡️ What's Installed

Three powerful CLI tools for managing GitHub security alerts:

1. **`security-incident-handler.sh`** - Main security management tool
2. **`automated-security-monitor.sh`** - Background monitoring (cron)
3. **`rotate-credentials.sh`** - Interactive credential rotation

---

## 🚀 Quick Start

### Check for Security Alerts

```bash
cd ~/InsaAutomationCorp

# List all security alerts
./security-incident-handler.sh list

# Check for new alerts (generates reports)
./security-incident-handler.sh check

# Get details for specific alert
./security-incident-handler.sh details 1
```

### Rotate Exposed Credentials

```bash
# SMTP/Email credentials
./rotate-credentials.sh smtp

# GitHub personal access token
./rotate-credentials.sh github-token

# Generic API key
./rotate-credentials.sh api-key
```

### Resolve Alerts (After Fixing)

```bash
# After rotating credentials and cleaning history
./security-incident-handler.sh resolve 1 --reason revoked --comment "Fixed on Dec 8, 2025"
```

---

## 📊 Current Status

As of December 8, 2025:
- ✅ All security alerts resolved
- ✅ Automated monitoring active (every 6 hours)
- ✅ Email notifications configured
- ✅ Git history cleaned

---

## 📚 Documentation

**Comprehensive Guides**:
- **Quick Reference**: `SECURITY_CLI_QUICK_REFERENCE.md` - All commands and workflows
- **Agent Guide**: `.github/AGENT_GITHUB_ACCESS_GUIDE.md` - For AI agents and automation
- **Secret Management**: `.github/SECRET_MANAGEMENT.md` - Best practices and policies
- **Incident Report**: `~/SECURITY_ISSUES_FIXED_DEC8_2025.md` - What we fixed

**Get Help**:
```bash
./security-incident-handler.sh help
./rotate-credentials.sh help
```

---

## 🤖 For Future Agents

If you're an AI agent or automation tool that needs to handle GitHub security:

1. **Authenticate**: Use GitHub CLI (`gh auth login`)
2. **Check Auth**: Always verify `gh auth status` before operations
3. **Read Guide**: See `.github/AGENT_GITHUB_ACCESS_GUIDE.md`
4. **Use Tools**: Leverage the installed CLI tools
5. **Log Actions**: All operations are logged in `~/security-incidents/monitor.log`

**Example Agent Pattern**:
```bash
#!/bin/bash
# Check authentication
if ! gh auth status &> /dev/null; then
    echo "ERROR: GitHub not authenticated"
    exit 1
fi

# Check for alerts
./security-incident-handler.sh list

# Generate reports if needed
./security-incident-handler.sh check
```

---

## 🔔 Automated Monitoring

The system automatically checks for new security alerts every 6 hours.

**Check Status**:
```bash
# View cron job
crontab -l | grep security-monitor

# View recent activity
tail -50 ~/security-incidents/monitor.log

# Run manual check
~/InsaAutomationCorp/automated-security-monitor.sh
```

**Email Alerts**: Notifications sent to `w.aroca@insaing.com`

---

## 🆘 Emergency Response

If you receive a security alert:

1. **Don't Panic** - The tools are ready to help
2. **Assess** - Run `./security-incident-handler.sh details <number>`
3. **Rotate** - Run `./rotate-credentials.sh <type>`
4. **Clean** - Follow BFG instructions in `SECURITY_CLI_QUICK_REFERENCE.md`
5. **Resolve** - Run `./security-incident-handler.sh resolve <number>`

---

## 📞 Support

**Contact**: w.aroca@insaing.com
**GitHub Issues**: https://github.com/WilBtc/InsaAutomationCorp/issues
**Security Alerts**: https://github.com/WilBtc/InsaAutomationCorp/security/secret-scanning

---

**Last Updated**: December 8, 2025
**Version**: 1.0
**Status**: ✅ Production Ready
