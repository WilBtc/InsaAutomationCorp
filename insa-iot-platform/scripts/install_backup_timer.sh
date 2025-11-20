#!/bin/bash
#
# Installation script for TimescaleDB backup timer
#
# This script installs and enables the systemd timer and service
# for automated daily backups of TimescaleDB.
#
# Usage:
#   sudo ./install_backup_timer.sh
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "This script must be run as root (use sudo)"
    exit 1
fi

log_info "Installing TimescaleDB backup timer and service..."

# Verify source files exist
SERVICE_FILE="$SCRIPT_DIR/timescaledb-backup.service"
TIMER_FILE="$SCRIPT_DIR/timescaledb-backup.timer"

if [ ! -f "$SERVICE_FILE" ]; then
    log_error "Service file not found: $SERVICE_FILE"
    exit 1
fi

if [ ! -f "$TIMER_FILE" ]; then
    log_error "Timer file not found: $TIMER_FILE"
    exit 1
fi

# Create backups directory if it doesn't exist
BACKUP_DIR="/home/wil/insa-iot-platform/backups"
if [ ! -d "$BACKUP_DIR" ]; then
    log_info "Creating backup directory: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    chown wil:wil "$BACKUP_DIR"
    chmod 755 "$BACKUP_DIR"
fi

# Copy service and timer files to systemd directory
log_info "Copying service file to /etc/systemd/system/"
cp "$SERVICE_FILE" /etc/systemd/system/timescaledb-backup.service
chmod 644 /etc/systemd/system/timescaledb-backup.service

log_info "Copying timer file to /etc/systemd/system/"
cp "$TIMER_FILE" /etc/systemd/system/timescaledb-backup.timer
chmod 644 /etc/systemd/system/timescaledb-backup.timer

# Reload systemd daemon
log_info "Reloading systemd daemon..."
systemctl daemon-reload

# Enable the timer
log_info "Enabling timer to start on boot..."
systemctl enable timescaledb-backup.timer

# Start the timer
log_info "Starting timer..."
systemctl start timescaledb-backup.timer

# Verify installation
log_info ""
log_info "=========================================="
log_info "Installation completed successfully!"
log_info "=========================================="
log_info ""

# Show timer status
log_info "Timer status:"
systemctl status timescaledb-backup.timer --no-pager || true

log_info ""
log_info "Next scheduled run:"
systemctl list-timers timescaledb-backup.timer --no-pager || true

log_info ""
log_info "=========================================="
log_info "Quick Reference Commands:"
log_info "=========================================="
echo "# Check timer status:"
echo "  systemctl status timescaledb-backup.timer"
echo ""
echo "# View next scheduled runs:"
echo "  systemctl list-timers"
echo ""
echo "# Run backup manually:"
echo "  sudo systemctl start timescaledb-backup.service"
echo ""
echo "# View backup logs:"
echo "  journalctl -u timescaledb-backup -f"
echo ""
echo "# Stop/disable timer:"
echo "  sudo systemctl stop timescaledb-backup.timer"
echo "  sudo systemctl disable timescaledb-backup.timer"
echo ""

log_info "For more information, see: $PROJECT_DIR/docs/BACKUP_AUTOMATION.md"
