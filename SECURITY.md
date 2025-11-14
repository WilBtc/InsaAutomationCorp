# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| main    | ✅ Yes             |
| develop | ✅ Yes             |
| < 1.0   | ❌ No              |

## Automated Security Scanning

We use multiple security tools to protect our codebase:

### 🔍 CodeQL (Static Analysis)
- **Runs**: On every push, PR, and weekly schedule
- **Languages**: Python
- **Queries**: Security-extended + Quality checks
- **Results**: GitHub Security tab → Code scanning alerts

### 🔒 Secret Scanning
- **Runs**: On every commit
- **Detects**: API keys, passwords, tokens
- **Protection**: Push protection enabled (blocks commits)

### 📦 Dependabot (Dependencies)
- **Runs**: Weekly
- **Scans**: Python, Docker, GitHub Actions
- **Action**: Auto-creates PRs for vulnerable dependencies

## Reporting a Vulnerability

**DO NOT** create a public GitHub issue for security vulnerabilities.

Instead:
1. Email: w.aroca@insaing.com
2. Subject: [SECURITY] Brief description
3. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

**Response Time**:
- Critical: 24 hours
- High: 48 hours
- Medium: 1 week
- Low: 2 weeks

## Security Updates

Security fixes are released as soon as possible after verification.

Check the Security tab for all current vulnerabilities.

## Security Best Practices

### For Developers
- Never commit secrets, API keys, or credentials
- Use environment variables for sensitive data
- Review CodeQL alerts before merging PRs
- Keep dependencies up to date
- Run security scans locally before pushing

### For Users
- Always use the latest version from main branch
- Report security issues privately via email
- Review security advisories regularly
- Use strong authentication for all services

## Security Architecture

INSA Automation Corp implements defense-in-depth security:

1. **Code Analysis**: CodeQL static analysis on every commit
2. **Network Security**: Tailscale VPN for all remote access
3. **IDS/IPS**: Suricata with 62,019+ rules
4. **SIEM**: Wazuh central monitoring
5. **Compliance**: IEC 62443 industrial cybersecurity standards
6. **Container Security**: Regular Trivy scans
7. **Host Hardening**: AppArmor, auditd, ClamAV

## Compliance

We maintain compliance with:
- IEC 62443 (Industrial Cybersecurity)
- NIST Cybersecurity Framework 2.0
- CISA Industrial Control Systems guidelines

For compliance documentation, contact: w.aroca@insaing.com
