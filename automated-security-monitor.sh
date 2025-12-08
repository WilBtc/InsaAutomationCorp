#!/bin/bash
################################################################################
# Automated Security Monitor
# Purpose: Runs periodically to check for security alerts and notify admin
# Author: INSA Automation Corp
# Date: December 8, 2025
################################################################################

set -euo pipefail

# Configuration
REPO="WilBtc/InsaAutomationCorp"
HANDLER_SCRIPT="$HOME/InsaAutomationCorp/security-incident-handler.sh"
ALERT_EMAIL="w.aroca@insaing.com"
LOG_FILE="$HOME/security-incidents/monitor.log"
LAST_CHECK_FILE="$HOME/security-incidents/.last_check"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_alert_email() {
    local subject="$1"
    local body="$2"

    # Try multiple methods to send email
    if command -v mail &> /dev/null; then
        echo "$body" | mail -s "$subject" "$ALERT_EMAIL" 2>/dev/null || true
    elif command -v sendmail &> /dev/null; then
        echo -e "Subject: $subject\n\n$body" | sendmail "$ALERT_EMAIL" 2>/dev/null || true
    fi

    # Also log the alert
    log "ALERT: $subject"
}

check_for_alerts() {
    log "Running security check..."

    # Get current alert count
    local current_alerts=$(gh api "/repos/$REPO/secret-scanning/alerts" \
        --jq '[.[] | select(.state == "open")] | length' 2>/dev/null || echo "0")

    # Get last known alert count
    local last_alerts=0
    if [ -f "$LAST_CHECK_FILE" ]; then
        last_alerts=$(cat "$LAST_CHECK_FILE")
    fi

    log "Current open alerts: $current_alerts (last check: $last_alerts)"

    # If new alerts detected
    if [ "$current_alerts" -gt "$last_alerts" ]; then
        local new_count=$((current_alerts - last_alerts))
        log "⚠️  NEW SECURITY ALERTS DETECTED: $new_count"

        # Run full check and generate reports
        local report_output=$("$HANDLER_SCRIPT" check 2>&1)

        # Send email notification
        send_alert_email \
            "🚨 [SECURITY] $new_count New Secret(s) Exposed in $REPO" \
            "New security alert(s) detected in $REPO

Alert Count: $new_count new alert(s)
Total Open: $current_alerts alert(s)

$report_output

IMMEDIATE ACTION REQUIRED:
1. Review reports in: $HOME/security-incidents/
2. Rotate exposed credentials
3. Clean Git history
4. Resolve alerts using: $HANDLER_SCRIPT resolve <alert_number>

View alerts: $HANDLER_SCRIPT list
Get details: $HANDLER_SCRIPT details <number>

This is an automated alert from the INSA Security Monitor.
"

    elif [ "$current_alerts" -eq 0 ]; then
        log "✅ No security alerts (all clear)"
    else
        log "ℹ️  $current_alerts open alert(s) (no change)"
    fi

    # Update last check
    echo "$current_alerts" > "$LAST_CHECK_FILE"
}

# Main execution
log "=========================================="
log "Automated Security Monitor - Starting"
log "Repository: $REPO"
log "=========================================="

# Check dependencies
if ! command -v gh &> /dev/null; then
    log "❌ GitHub CLI (gh) not installed"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    log "❌ GitHub CLI not authenticated"
    exit 1
fi

# Run check
check_for_alerts

log "Monitor run completed"
log ""
