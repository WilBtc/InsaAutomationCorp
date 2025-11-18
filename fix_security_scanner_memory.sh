#!/bin/bash
# Fix Security Scanner Memory Limit
# Date: November 9, 2025
# Issue: OOM kill at 512MB, increasing to 2GB

set -e

echo "==================================================================="
echo "Security Scanner Memory Limit Fix"
echo "==================================================================="
echo ""
echo "Current limit: 512M"
echo "New limit: 2G (4x increase)"
echo ""

# Backup original
echo "[1/4] Creating backup..."
sudo cp /etc/systemd/system/security-scanner.service \
       /etc/systemd/system/security-scanner.service.backup-nov9-2025
echo "✅ Backup created: security-scanner.service.backup-nov9-2025"

# Apply fix
echo ""
echo "[2/4] Updating memory limit..."
sudo sed -i 's/MemoryLimit=512M/MemoryLimit=2G/' \
       /etc/systemd/system/security-scanner.service
echo "✅ Changed MemoryLimit=512M → MemoryLimit=2G"

# Reload systemd
echo ""
echo "[3/4] Reloading systemd daemon..."
sudo systemctl daemon-reload
echo "✅ systemd daemon reloaded"

# Restart service
echo ""
echo "[4/4] Restarting security-scanner service..."
sudo systemctl restart security-scanner.service
sleep 2
echo "✅ Service restarted"

# Verify
echo ""
echo "==================================================================="
echo "Verification"
echo "==================================================================="
echo ""

SERVICE_STATUS=$(systemctl is-active security-scanner.service)
MEMORY_LIMIT=$(systemctl show security-scanner.service -p MemoryLimit | cut -d= -f2)
MEMORY_CURRENT=$(systemctl show security-scanner.service -p MemoryCurrent | cut -d= -f2)

echo "Service Status: $SERVICE_STATUS"
echo "Memory Limit: $MEMORY_LIMIT bytes ($(numfmt --to=iec $MEMORY_LIMIT))"
echo "Current Usage: $MEMORY_CURRENT bytes ($(numfmt --to=iec $MEMORY_CURRENT))"

if [ "$SERVICE_STATUS" = "active" ] && [ "$MEMORY_LIMIT" = "2147483648" ]; then
    echo ""
    echo "✅ SUCCESS! Memory limit increased to 2G and service is running"
else
    echo ""
    echo "⚠️  WARNING: Verification failed, check service status"
    sudo systemctl status security-scanner.service --no-pager
fi

echo ""
echo "==================================================================="
echo "Monitoring Commands"
echo "==================================================================="
echo ""
echo "Watch memory usage:"
echo "  watch -n 60 'systemctl show security-scanner.service | grep Memory'"
echo ""
echo "Check for OOM kills:"
echo "  sudo journalctl -k --since today | grep -i 'out of memory'"
echo ""
echo "Service logs:"
echo "  journalctl -u security-scanner.service -f"
echo ""

echo "Fix complete! See /home/wil/SECURITY_SCANNER_MEMORY_FIX_NOV9_2025.md for details."
