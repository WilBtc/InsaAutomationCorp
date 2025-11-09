#!/bin/bash
# Security Scanner Best Practices - Complete Fix
# Run: sudo bash APPLY_SECURITY_SCANNER_FIXES.sh
# Date: November 9, 2025

set -e

echo "==================================================================="
echo "Security Scanner - Best Practices Implementation"
echo "Date: $(date)"
echo "==================================================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run with sudo: sudo bash $0"
    exit 1
fi

echo "Phase 1: Memory Limit Fix"
echo "-------------------------------------------------------------------"

# Backup
echo "[1/3] Creating backup..."
cp /etc/systemd/system/security-scanner.service \
   /etc/systemd/system/security-scanner.service.backup-nov9-2025
echo "✅ Backup: security-scanner.service.backup-nov9-2025"

# Update memory limit
echo ""
echo "[2/3] Updating memory limit (512M → 2G)..."
sed -i 's/MemoryLimit=512M/MemoryLimit=2G/' /etc/systemd/system/security-scanner.service
echo "✅ Changed: MemoryLimit=512M → MemoryLimit=2G"

# Apply changes
echo ""
echo "[3/3] Applying changes..."
systemctl daemon-reload
systemctl restart security-scanner.service
sleep 3
echo "✅ Service restarted"

# Verify
echo ""
echo "==================================================================="
echo "Verification"
echo "==================================================================="
STATUS=$(systemctl is-active security-scanner.service)
LIMIT=$(systemctl show security-scanner.service -p MemoryLimit | cut -d= -f2)
CURRENT=$(systemctl show security-scanner.service -p MemoryCurrent | cut -d= -f2)

echo "Service Status: $STATUS"
echo "Memory Limit: $(numfmt --to=iec $LIMIT) (was 512M)"
echo "Current Usage: $(numfmt --to=iec $CURRENT)"

if [ "$STATUS" = "active" ] && [ "$LIMIT" = "2147483648" ]; then
    echo ""
    echo "✅ SUCCESS! Phase 1 complete"
else
    echo ""
    echo "⚠️ WARNING: Verification failed"
    systemctl status security-scanner.service --no-pager
    exit 1
fi

echo ""
echo "==================================================================="
echo "Phase 2: Code Optimizations (Manual)"
echo "==================================================================="
echo ""
echo "Next steps to implement best practices:"
echo ""
echo "1. Add archive exclusions (reduces scan by 60-70%):"
echo "   - Edit: /home/wil/security-scanner/security_agent.py"
echo "   - Exclude: */archive/*, */node_modules/*, */.git/*, */venv/*"
echo ""
echo "2. Implement memory-aware batching:"
echo "   - Add psutil for memory monitoring"
echo "   - Batch size: 50 files max"
echo "   - Memory threshold: 1.5GB (pause if exceeded)"
echo ""
echo "3. Add Wazuh monitoring alert:"
echo "   - Alert if memory > 1.5GB for 5+ minutes"
echo "   - Email: w.aroca@insaing.com"
echo ""
echo "4. Clean up archives:"
echo "   - Move /home/wil/mcp-servers/archive/* to cold storage"
echo "   - Saves ~3GB scan time"
echo ""
echo "Phase 1 fix applied! See logs:"
echo "  journalctl -u security-scanner.service -f"
echo ""
