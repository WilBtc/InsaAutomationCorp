#!/bin/bash
################################################################################
# Credential Rotation Helper
# Purpose: Assists with rotating exposed credentials
# Author: INSA Automation Corp
# Date: December 8, 2025
################################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_usage() {
    cat << EOF
Credential Rotation Helper
Usage: $0 <credential_type>

Supported credential types:
  smtp              Rotate SMTP/email credentials
  github-token      Rotate GitHub personal access token
  api-key           Rotate API keys
  database          Rotate database credentials
  ssh-key           Rotate SSH keys

Example:
  $0 smtp

This script provides step-by-step guidance for rotating credentials.

EOF
}

rotate_smtp() {
    cat << 'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SMTP Credential Rotation Guide
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Generate New SMTP Credentials
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Choose your email provider:

Gmail:
  1. Go to: https://myaccount.google.com/apppasswords
  2. Sign in with your Google account
  3. Create new app password: "INSA Automation"
  4. Copy the 16-character password

Office 365:
  1. Go to: https://outlook.office.com/mail/
  2. Settings → View all Outlook settings → Mail → Sync email
  3. Generate new app password
  4. Copy the password

SendGrid:
  1. Go to: https://app.sendgrid.com/settings/api_keys
  2. Create API Key → Full Access
  3. Name: "INSA Automation - Dec 2025"
  4. Copy the API key

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2: Store New Credentials Securely
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Create .env file (NOT in git):

EOF

    read -p "Enter SMTP server (e.g., smtp.gmail.com): " smtp_server
    read -p "Enter SMTP port (default 587): " smtp_port
    smtp_port=${smtp_port:-587}
    read -p "Enter SMTP username/email: " smtp_user
    read -sp "Enter NEW SMTP password: " smtp_pass
    echo

    local env_file="$HOME/InsaAutomationCorp/.env"

    cat > "$env_file" << ENVFILE
# SMTP Configuration
# Generated: $(date)
# DO NOT COMMIT THIS FILE TO GIT

SMTP_SERVER=$smtp_server
SMTP_PORT=$smtp_port
SMTP_USER=$smtp_user
SMTP_PASSWORD=$smtp_pass
SMTP_FROM=$smtp_user
SMTP_USE_TLS=true
ENVFILE

    chmod 600 "$env_file"
    log_success "Credentials stored in: $env_file"

    cat << 'EOF'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 3: Test New Credentials
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF

    # Create test script
    local test_script=$(mktemp)
    cat > "$test_script" << 'TESTSCRIPT'
#!/usr/bin/env python3
import smtplib
import os
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

try:
    server = smtplib.SMTP(os.getenv('SMTP_SERVER'), int(os.getenv('SMTP_PORT')))
    server.starttls()
    server.login(os.getenv('SMTP_USER'), os.getenv('SMTP_PASSWORD'))

    # Send test email
    msg = MIMEText('SMTP credentials verified successfully!')
    msg['Subject'] = 'INSA Security - SMTP Test'
    msg['From'] = os.getenv('SMTP_FROM')
    msg['To'] = os.getenv('SMTP_USER')

    server.send_message(msg)
    server.quit()

    print("✅ SUCCESS: SMTP credentials work!")
    print("✅ Test email sent to:", os.getenv('SMTP_USER'))
except Exception as e:
    print("❌ ERROR:", str(e))
    exit(1)
TESTSCRIPT

    if command -v python3 &> /dev/null; then
        log_info "Testing SMTP connection..."
        cd ~/InsaAutomationCorp
        python3 "$test_script" && log_success "SMTP test passed!" || log_error "SMTP test failed"
    fi

    rm -f "$test_script"

    cat << 'EOF'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 4: Update .gitignore
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF

    cd ~/InsaAutomationCorp

    if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
        log_info "Adding .env to .gitignore..."
        cat >> .gitignore << 'GITIGNORE'

# Environment files with secrets
.env
.env.*
*.env
GITIGNORE
        log_success "Updated .gitignore"
    else
        log_success ".gitignore already contains .env"
    fi

    cat << EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 5: Revoke Old Credentials
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Now that new credentials are working, REVOKE the old exposed ones:

Gmail:
  1. Go to: https://myaccount.google.com/apppasswords
  2. Find the old password entry
  3. Click "Remove" to revoke it

Office 365:
  1. Go to your Office 365 settings
  2. Find app passwords
  3. Revoke the old password

SendGrid:
  1. Go to: https://app.sendgrid.com/settings/api_keys
  2. Find the old API key
  3. Click "Delete"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ SMTP Rotation Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Next steps:
1. Clean Git history (if not already done)
2. Update production systems with new credentials
3. Document rotation in incident report

Credentials location: $env_file
Keep this file secure and NEVER commit it to Git!

EOF
}

rotate_github_token() {
    cat << 'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GitHub Token Rotation Guide
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Generate New Token
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Name: "INSA Automation - Dec 2025"
4. Select scopes needed:
   - repo (full control)
   - workflow
   - read:org
   - write:packages (if needed)
5. Click "Generate token"
6. COPY THE TOKEN NOW (you won't see it again!)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2: Update GitHub CLI Authentication
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF

    log_info "Re-authenticating GitHub CLI..."
    gh auth login

    cat << 'EOF'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 3: Update Environment Variables
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF

    read -sp "Paste your new GitHub token: " github_token
    echo

    local env_file="$HOME/InsaAutomationCorp/.env"

    if [ -f "$env_file" ]; then
        # Update existing
        if grep -q "^GITHUB_TOKEN=" "$env_file"; then
            sed -i "s|^GITHUB_TOKEN=.*|GITHUB_TOKEN=$github_token|" "$env_file"
        else
            echo "GITHUB_TOKEN=$github_token" >> "$env_file"
        fi
    else
        echo "GITHUB_TOKEN=$github_token" > "$env_file"
        chmod 600 "$env_file"
    fi

    log_success "GitHub token updated in: $env_file"

    cat << 'EOF'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 4: Revoke Old Token
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Go to: https://github.com/settings/tokens
2. Find the old exposed token
3. Click "Delete" to revoke it

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ GitHub Token Rotation Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF
}

rotate_api_key() {
    cat << 'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
API Key Rotation Guide
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Identify the Service
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Which service's API key was exposed?

Common services:
  - Anthropic/Claude AI
  - OpenAI
  - AWS
  - Azure
  - Stripe
  - Twilio
  - Other

EOF

    read -p "Service name: " service_name
    read -p "Service API console URL: " service_url

    cat << EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2: Generate New API Key
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Go to: $service_url
2. Navigate to API keys section
3. Generate new key with appropriate permissions
4. Copy the new key

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 3: Store Securely
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF

    read -sp "Paste new API key: " api_key
    echo

    local env_file="$HOME/InsaAutomationCorp/.env"
    local env_var_name=$(echo "${service_name}_API_KEY" | tr '[:lower:]' '[:upper:]' | tr ' ' '_')

    if [ -f "$env_file" ]; then
        echo "$env_var_name=$api_key" >> "$env_file"
    else
        echo "$env_var_name=$api_key" > "$env_file"
        chmod 600 "$env_file"
    fi

    log_success "API key stored as: $env_var_name"

    cat << EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 4: Revoke Old Key
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. Return to: $service_url
2. Find the old exposed API key
3. Revoke/Delete it immediately

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ API Key Rotation Complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF
}

# Main
case "${1:-help}" in
    smtp)
        rotate_smtp
        ;;
    github-token)
        rotate_github_token
        ;;
    api-key)
        rotate_api_key
        ;;
    *)
        show_usage
        ;;
esac
