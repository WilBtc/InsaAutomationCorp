#!/bin/bash
# SANS ISC Threat Feed Updater (Runs hourly via cron)

BASE_DIR="/home/wil/automation/agents/orchestrator/knowledge/sans/threat-intel"
USER_AGENT="INSA-Automation w.aroca@insaing.com"

# Download blocklist
wget -q -U "$USER_AGENT" -O "$BASE_DIR/blocklist.txt" https://isc.sans.edu/block.txt

# Download top IPs
wget -q -U "$USER_AGENT" -O "$BASE_DIR/top_100_ips.txt" https://isc.sans.edu/api/topips/records/100?text

# Download threat intel feed
wget -q -U "$USER_AGENT" -O "$BASE_DIR/threat_intel.txt" https://isc.sans.edu/feeds/threatintel.txt

# Log update
echo "$(date): SANS ISC feeds updated" >> "$BASE_DIR/update.log"
