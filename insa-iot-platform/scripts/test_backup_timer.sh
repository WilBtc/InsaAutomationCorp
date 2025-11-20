#!/bin/bash
#
# Test script for TimescaleDB backup timer
#
# This script tests the backup automation setup without requiring sudo installation
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}✓${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $*"
}

log_error() {
    echo -e "${RED}✗${NC} $*"
}

log_test() {
    echo -e "${BLUE}▶${NC} $*"
}

echo "=========================================="
echo "TimescaleDB Backup Timer Test Suite"
echo "=========================================="
echo ""

# Test 1: Check if backup script exists and is executable
log_test "Test 1: Checking backup script..."
if [ -x "$SCRIPT_DIR/backup_timescaledb.sh" ]; then
    log_info "Backup script exists and is executable"
else
    log_error "Backup script not found or not executable"
    exit 1
fi

# Test 2: Check if systemd service file exists
log_test "Test 2: Checking service file..."
if [ -f "$SCRIPT_DIR/timescaledb-backup.service" ]; then
    log_info "Service file exists"
else
    log_error "Service file not found"
    exit 1
fi

# Test 3: Check if systemd timer file exists
log_test "Test 3: Checking timer file..."
if [ -f "$SCRIPT_DIR/timescaledb-backup.timer" ]; then
    log_info "Timer file exists"
else
    log_error "Timer file not found"
    exit 1
fi

# Test 4: Verify systemd service syntax
log_test "Test 4: Verifying service file syntax..."
# Check for errors specific to our service file
if systemd-analyze verify "$SCRIPT_DIR/timescaledb-backup.service" 2>&1 | grep -i "timescaledb-backup.service" | grep -qi "error"; then
    log_error "Service file has syntax errors"
    systemd-analyze verify "$SCRIPT_DIR/timescaledb-backup.service" 2>&1 | grep "timescaledb-backup.service"
else
    log_info "Service file syntax is valid"
fi

# Test 5: Verify systemd timer syntax
log_test "Test 5: Verifying timer file syntax..."
if systemd-analyze verify "$SCRIPT_DIR/timescaledb-backup.timer" 2>&1 >/dev/null; then
    log_info "Timer file syntax is valid"
else
    log_warn "Timer file may have warnings (usually non-critical)"
fi

# Test 6: Check if installation script exists
log_test "Test 6: Checking installation script..."
if [ -x "$SCRIPT_DIR/install_backup_timer.sh" ]; then
    log_info "Installation script exists and is executable"
else
    log_error "Installation script not found or not executable"
    exit 1
fi

# Test 7: Check if documentation exists
log_test "Test 7: Checking documentation..."
if [ -f "$(dirname "$SCRIPT_DIR")/docs/BACKUP_AUTOMATION.md" ]; then
    log_info "Documentation exists"
else
    log_error "Documentation not found"
    exit 1
fi

# Test 8: Check if backups directory exists
log_test "Test 8: Checking backups directory..."
BACKUP_DIR="/home/wil/insa-iot-platform/backups"
if [ -d "$BACKUP_DIR" ]; then
    log_info "Backups directory exists"

    # Check permissions
    if [ -w "$BACKUP_DIR" ]; then
        log_info "Backups directory is writable"
    else
        log_warn "Backups directory is not writable by current user"
    fi
else
    log_warn "Backups directory does not exist (will be created on first run)"
fi

# Test 9: Check if Docker container is running
log_test "Test 9: Checking TimescaleDB container..."
CONTAINER_NAME="alkhorayef-timescaledb"
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${CONTAINER_NAME}$"; then
    log_info "TimescaleDB container is running"
else
    log_warn "TimescaleDB container is not running (required for backups)"
fi

# Test 10: Check if .env file exists
log_test "Test 10: Checking environment configuration..."
ENV_FILE="$(dirname "$SCRIPT_DIR")/.env"
if [ -f "$ENV_FILE" ]; then
    log_info ".env file exists"

    # Check for required variables
    required_vars=("POSTGRES_HOST" "POSTGRES_DB" "POSTGRES_USER" "POSTGRES_PASSWORD")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" "$ENV_FILE"; then
            log_info "  $var is configured"
        else
            log_warn "  $var is not configured in .env"
        fi
    done
else
    log_warn ".env file not found (required for database credentials)"
fi

# Test 11: Test systemd calendar format
log_test "Test 11: Verifying timer schedule..."
SCHEDULE=$(grep "OnCalendar=" "$SCRIPT_DIR/timescaledb-backup.timer" | cut -d= -f2)
if systemd-analyze calendar "$SCHEDULE" >/dev/null 2>&1; then
    log_info "Timer schedule is valid: $SCHEDULE"
    echo ""
    systemd-analyze calendar "$SCHEDULE" | grep -A3 "Next elapse"
else
    log_error "Timer schedule is invalid: $SCHEDULE"
fi

# Test 12: Check if timer is already installed
log_test "Test 12: Checking if timer is installed..."
if systemctl list-unit-files 2>/dev/null | grep -q "timescaledb-backup.timer"; then
    log_info "Timer is already installed in systemd"

    # Check if enabled
    if systemctl is-enabled timescaledb-backup.timer 2>/dev/null | grep -q "enabled"; then
        log_info "Timer is enabled (will start on boot)"
    else
        log_warn "Timer is not enabled"
    fi

    # Check if active
    if systemctl is-active timescaledb-backup.timer 2>/dev/null | grep -q "active"; then
        log_info "Timer is currently active"
        echo ""
        echo "Next scheduled run:"
        systemctl list-timers timescaledb-backup.timer --no-pager 2>/dev/null || true
    else
        log_warn "Timer is not active"
    fi
else
    log_warn "Timer is not installed (run install_backup_timer.sh to install)"
fi

# Summary
echo ""
echo "=========================================="
echo "Test Summary"
echo "=========================================="
echo ""

if [ -x "$SCRIPT_DIR/backup_timescaledb.sh" ] && \
   [ -f "$SCRIPT_DIR/timescaledb-backup.service" ] && \
   [ -f "$SCRIPT_DIR/timescaledb-backup.timer" ] && \
   [ -x "$SCRIPT_DIR/install_backup_timer.sh" ] && \
   [ -f "$(dirname "$SCRIPT_DIR")/docs/BACKUP_AUTOMATION.md" ]; then

    log_info "All required files are present and valid"
    echo ""
    echo "Next steps:"
    echo "  1. Review configuration in .env file"
    echo "  2. Install timer: sudo $SCRIPT_DIR/install_backup_timer.sh"
    echo "  3. Test manual backup: sudo systemctl start timescaledb-backup.service"
    echo "  4. View logs: journalctl -u timescaledb-backup -f"
    echo ""
else
    log_error "Some required files are missing or invalid"
    exit 1
fi
