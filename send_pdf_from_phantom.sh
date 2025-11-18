#!/bin/bash
# Script to run on phantom-ops laptop to send PDF to iac1
# User: aaliy
# Date: October 18, 2025

echo "==================================="
echo "Send Instrumentation PDF to iac1"
echo "==================================="
echo ""

PDF_FILE="/home/aaliy/Downloads/instrumentacion-industrial-antonio-creus.pdf"
TARGET_HOST="iac1"

# Check if file exists
if [ ! -f "$PDF_FILE" ]; then
    echo "ERROR: PDF file not found at: $PDF_FILE"
    echo ""
    echo "Available files in Downloads:"
    ls -lh /home/aaliy/Downloads/*.pdf 2>/dev/null || echo "No PDF files found"
    exit 1
fi

# Check file size
FILE_SIZE=$(stat -f%z "$PDF_FILE" 2>/dev/null || stat -c%s "$PDF_FILE" 2>/dev/null)
FILE_SIZE_MB=$(echo "scale=2; $FILE_SIZE / 1024 / 1024" | bc)

echo "File found: $PDF_FILE"
echo "Size: ${FILE_SIZE_MB} MB"
echo ""
echo "Sending to $TARGET_HOST via Tailscale..."
echo ""

# Send file via Tailscale
tailscale file cp "$PDF_FILE" "$TARGET_HOST:"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! File sent to iac1"
    echo ""
    echo "On iac1, the user should run:"
    echo "  tailscale file get ~/"
    echo ""
else
    echo ""
    echo "❌ FAILED to send file"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check Tailscale is running: tailscale status"
    echo "2. Verify iac1 is online: tailscale ping iac1"
    echo "3. Check file permissions: ls -l $PDF_FILE"
    echo ""
fi
