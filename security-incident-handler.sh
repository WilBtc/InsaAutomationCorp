#!/bin/bash
################################################################################
# GitHub CLI Security Incident Handler
# Purpose: Automatically detect, report, and remediate secret exposures
# Author: INSA Automation Corp
# Date: December 8, 2025
################################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO="WilBtc/InsaAutomationCorp"
INCIDENT_DIR="$HOME/security-incidents"
ALERT_EMAIL="w.aroca@insaing.com"

################################################################################
# Functions
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."

    local missing_deps=()

    command -v gh &> /dev/null || missing_deps+=("gh (GitHub CLI)")
    command -v jq &> /dev/null || missing_deps+=("jq")
    command -v git &> /dev/null || missing_deps+=("git")

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing_deps[*]}"
        log_info "Install with: sudo apt-get install gh jq git"
        exit 1
    fi

    # Check gh authentication
    if ! gh auth status &> /dev/null; then
        log_error "GitHub CLI not authenticated"
        log_info "Run: gh auth login"
        exit 1
    fi

    log_success "All dependencies satisfied"
}

create_incident_dir() {
    mkdir -p "$INCIDENT_DIR"
    log_info "Incident directory: $INCIDENT_DIR"
}

fetch_secret_alerts() {
    log_info "Fetching secret scanning alerts from GitHub..."

    local alerts_json="$INCIDENT_DIR/alerts_$(date +%Y%m%d_%H%M%S).json"

    gh api "/repos/$REPO/secret-scanning/alerts" \
        --jq '.[] | select(.state == "open")' > "$alerts_json" 2>/dev/null || {
        log_warning "Could not fetch alerts. Checking if secret scanning is enabled..."

        # Check if secret scanning is available
        local repo_info=$(gh api "/repos/$REPO")
        local has_secret_scanning=$(echo "$repo_info" | jq -r '.security_and_analysis.secret_scanning.status // "disabled"')

        if [ "$has_secret_scanning" = "disabled" ]; then
            log_error "Secret scanning is not enabled on this repository"
            log_info "Enable with: gh api -X PATCH /repos/$REPO -f security_and_analysis[secret_scanning][status]=enabled"
            return 1
        fi

        log_info "No open alerts found (this is good!)"
        return 0
    }

    if [ -s "$alerts_json" ]; then
        local alert_count=$(wc -l < "$alerts_json")
        log_warning "Found $alert_count open secret scanning alert(s)"
        echo "$alerts_json"
    else
        log_success "No open secret scanning alerts"
        rm -f "$alerts_json"
        return 0
    fi
}

analyze_alert() {
    local alert_json="$1"

    log_info "Analyzing alert..."

    local alert_number=$(jq -r '.number' <<< "$alert_json")
    local secret_type=$(jq -r '.secret_type_display_name' <<< "$alert_json")
    local created_at=$(jq -r '.created_at' <<< "$alert_json")
    local html_url=$(jq -r '.html_url' <<< "$alert_json")
    local state=$(jq -r '.state' <<< "$alert_json")

    cat << EOF

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 SECURITY ALERT #$alert_number
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Secret Type:  $secret_type
Status:       $state
Detected:     $created_at
URL:          $html_url
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOF

    # Try to get location information
    local locations=$(gh api "/repos/$REPO/secret-scanning/alerts/$alert_number/locations" 2>/dev/null || echo "[]")

    if [ "$(echo "$locations" | jq '. | length')" -gt 0 ]; then
        log_info "Secret locations:"
        echo "$locations" | jq -r '.[] | "  - \(.details.path):\(.details.start_line) (commit: \(.details.commit_sha[0:7]))"'
    fi
}

generate_incident_report() {
    local alert_json="$1"
    local report_file="$2"

    local alert_number=$(jq -r '.number' <<< "$alert_json")
    local secret_type=$(jq -r '.secret_type_display_name' <<< "$alert_json")
    local created_at=$(jq -r '.created_at' <<< "$alert_json")

    cat > "$report_file" << EOF
# Security Incident Report - Alert #$alert_number
**Generated**: $(date)
**Alert Number**: $alert_number
**Secret Type**: $secret_type
**Detected**: $created_at
**Repository**: $REPO
**Severity**: HIGH

---

## Alert Details

$(echo "$alert_json" | jq .)

---

## Immediate Actions Required

### 1. ⏰ IMMEDIATE (Do Now)

#### A. Verify if credentials are still active
Test the exposed credentials to determine if they're still valid.

#### B. Rotate/Revoke credentials IMMEDIATELY
1. Log into the service provider
2. Rotate or revoke the exposed credential
3. Generate new credentials
4. Store securely (NOT in git)

### 2. 📅 URGENT (Within 24 Hours)

#### A. Remove from Git history

**Using BFG Repo-Cleaner:**
\`\`\`bash
cd ~/InsaAutomationCorp

# Backup first
git clone --mirror https://github.com/$REPO.git backup.git

# Download BFG
wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar

# Create passwords file
echo "EXPOSED_SECRET_HERE" > /tmp/secrets.txt

# Clean history
java -jar bfg-1.14.0.jar --replace-text /tmp/secrets.txt .git

# Cleanup
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (rewrites history!)
git push --force --all

# Secure cleanup
shred -vfz -n 10 /tmp/secrets.txt
\`\`\`

#### B. Update application to use secure storage
- Use environment variables
- Use secrets management system (Vault, AWS Secrets Manager, etc.)
- Update documentation

### 3. 🔐 IMPORTANT (Within 48 Hours)

#### A. Update .gitignore
Add patterns to prevent future exposures:
\`\`\`bash
cat >> .gitignore << 'GITIGNORE'
# Secrets (added $(date +%Y-%m-%d))
.env
.env.*
*.env
*secret*
*credential*
*.key
*.pem
GITIGNORE
\`\`\`

#### B. Enable GitHub secret scanning protection
\`\`\`bash
gh api -X PATCH /repos/$REPO \\
  -f security_and_analysis[secret_scanning][status]=enabled \\
  -f security_and_analysis[secret_scanning_push_protection][status]=enabled
\`\`\`

### 4. 🛡️ Verification

After remediation, mark the alert as resolved:
\`\`\`bash
# Close this alert
~/InsaAutomationCorp/security-incident-handler.sh --resolve $alert_number --reason "revoked"
\`\`\`

---

## Resolution Commands

\`\`\`bash
# Get alert details
gh api /repos/$REPO/secret-scanning/alerts/$alert_number

# Resolve alert (after fixing)
gh api -X PATCH /repos/$REPO/secret-scanning/alerts/$alert_number \\
  -f state=resolved \\
  -f resolution=revoked \\
  -f resolution_comment="Credentials rotated and removed from history"

# Verify resolution
gh api /repos/$REPO/secret-scanning/alerts/$alert_number | jq '{state, resolved_at, resolved_by}'
\`\`\`

---

**Status**: REQUIRES ACTION
**Incident ID**: SEC-$(date +%Y%m%d)-$alert_number
**Report Location**: $report_file

EOF

    log_success "Incident report created: $report_file"
}

resolve_alert() {
    local alert_number="$1"
    local resolution="${2:-revoked}"
    local comment="${3:-Credentials rotated and removed from Git history}"

    log_info "Resolving alert #$alert_number..."

    # Valid resolutions: false_positive, wont_fix, revoked, used_in_tests
    gh api -X PATCH "/repos/$REPO/secret-scanning/alerts/$alert_number" \
        -f state=resolved \
        -f resolution="$resolution" \
        -f resolution_comment="$comment" &> /dev/null

    log_success "Alert #$alert_number marked as resolved ($resolution)"
}

list_all_alerts() {
    log_info "Fetching all secret scanning alerts..."

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Secret Scanning Alerts for $REPO"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    gh api "/repos/$REPO/secret-scanning/alerts" \
        --jq '.[] | "\(.number)\t\(.state)\t\(.secret_type_display_name)\t\(.created_at)"' \
        2>/dev/null | while IFS=$'\t' read -r number state type created; do

        if [ "$state" = "open" ]; then
            echo -e "${RED}#$number${NC}\t$state\t$type\t$created"
        else
            echo -e "${GREEN}#$number${NC}\t$state\t$type\t$created"
        fi
    done || log_warning "Could not fetch alerts (secret scanning may not be enabled)"

    echo ""
}

get_alert_details() {
    local alert_number="$1"

    log_info "Fetching details for alert #$alert_number..."

    local alert=$(gh api "/repos/$REPO/secret-scanning/alerts/$alert_number" 2>/dev/null)

    if [ -z "$alert" ]; then
        log_error "Alert #$alert_number not found"
        exit 1
    fi

    analyze_alert "$alert"

    # Get locations
    log_info "Fetching secret locations..."
    gh api "/repos/$REPO/secret-scanning/alerts/$alert_number/locations" \
        --jq '.[] | {path: .details.path, line: .details.start_line, commit: .details.commit_sha}' \
        2>/dev/null | jq -s '.'
}

enable_secret_scanning() {
    log_info "Enabling secret scanning for $REPO..."

    gh api -X PATCH "/repos/$REPO" \
        -f security_and_analysis[secret_scanning][status]=enabled \
        -f security_and_analysis[secret_scanning_push_protection][status]=enabled \
        &> /dev/null

    log_success "Secret scanning enabled with push protection"
}

scan_current_files() {
    log_info "Scanning current files for potential secrets..."

    cd ~/InsaAutomationCorp

    # Common secret patterns
    local patterns=(
        "password.*=.*['\"][^'\"]{8,}"
        "api[_-]?key.*=.*['\"][^'\"]{16,}"
        "secret.*=.*['\"][^'\"]{8,}"
        "token.*=.*['\"][^'\"]{16,}"
        "smtp.*password"
        "-----BEGIN.*PRIVATE KEY-----"
    )

    local found_issues=0

    for pattern in "${patterns[@]}"; do
        if grep -rn -E "$pattern" . \
            --exclude-dir=.git \
            --exclude-dir=node_modules \
            --exclude-dir=venv \
            --exclude="*.log" 2>/dev/null | head -10; then
            found_issues=1
        fi
    done

    if [ $found_issues -eq 0 ]; then
        log_success "No obvious secrets found in current files"
    else
        log_warning "Potential secrets detected (see above)"
        log_info "Review these files and move secrets to environment variables"
    fi
}

show_usage() {
    cat << EOF
GitHub CLI Security Incident Handler
Usage: $0 [COMMAND] [OPTIONS]

Commands:
  list                    List all secret scanning alerts
  check                   Check for new open alerts and generate reports
  details <number>        Get detailed information about a specific alert
  resolve <number>        Resolve an alert (mark as fixed)
  enable                  Enable secret scanning on repository
  scan                    Scan current files for potential secrets
  help                    Show this help message

Options:
  --reason <reason>       Resolution reason (revoked|false_positive|wont_fix|used_in_tests)
  --comment <comment>     Resolution comment

Examples:
  # List all alerts
  $0 list

  # Check for open alerts
  $0 check

  # Get details for alert #5
  $0 details 5

  # Resolve alert #5 as revoked
  $0 resolve 5 --reason revoked --comment "Credentials rotated"

  # Enable secret scanning
  $0 enable

  # Scan current files
  $0 scan

Repository: $REPO
Incident Directory: $INCIDENT_DIR

EOF
}

################################################################################
# Main
################################################################################

main() {
    local command="${1:-help}"

    case "$command" in
        list)
            check_dependencies
            list_all_alerts
            ;;

        check)
            check_dependencies
            create_incident_dir

            local alerts_file=$(fetch_secret_alerts)

            if [ -n "$alerts_file" ] && [ -f "$alerts_file" ]; then
                log_warning "Processing open alerts..."

                while IFS= read -r alert_json; do
                    analyze_alert "$alert_json"

                    local alert_number=$(jq -r '.number' <<< "$alert_json")
                    local report_file="$INCIDENT_DIR/incident_${alert_number}_$(date +%Y%m%d_%H%M%S).md"

                    generate_incident_report "$alert_json" "$report_file"

                    log_info "Next steps:"
                    echo "  1. Review report: cat $report_file"
                    echo "  2. Rotate credentials"
                    echo "  3. Clean git history"
                    echo "  4. Resolve alert: $0 resolve $alert_number --reason revoked"
                    echo ""
                done < "$alerts_file"
            else
                log_success "No security incidents detected"
            fi
            ;;

        details)
            check_dependencies
            local alert_number="${2:-}"

            if [ -z "$alert_number" ]; then
                log_error "Alert number required"
                log_info "Usage: $0 details <alert_number>"
                exit 1
            fi

            get_alert_details "$alert_number"
            ;;

        resolve)
            check_dependencies
            local alert_number="${2:-}"
            local reason="revoked"
            local comment="Credentials rotated and removed from Git history"

            if [ -z "$alert_number" ]; then
                log_error "Alert number required"
                log_info "Usage: $0 resolve <alert_number> [--reason <reason>] [--comment <comment>]"
                exit 1
            fi

            shift 2
            while [ $# -gt 0 ]; do
                case "$1" in
                    --reason)
                        reason="$2"
                        shift 2
                        ;;
                    --comment)
                        comment="$2"
                        shift 2
                        ;;
                    *)
                        log_error "Unknown option: $1"
                        exit 1
                        ;;
                esac
            done

            resolve_alert "$alert_number" "$reason" "$comment"
            ;;

        enable)
            check_dependencies
            enable_secret_scanning
            ;;

        scan)
            scan_current_files
            ;;

        help|--help|-h)
            show_usage
            ;;

        *)
            log_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
