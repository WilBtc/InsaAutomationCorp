#!/bin/bash
#
# SANS Knowledge Base Downloader
# Downloads free SANS white papers and threat intelligence for RAG system
# Date: November 1, 2025
# Author: Insa Automation Corp
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}SANS Knowledge Base Downloader for RAG System${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# Create directory structure
BASE_DIR="/home/wil/automation/agents/orchestrator/knowledge/sans"

echo -e "${YELLOW}Creating directory structure...${NC}"
mkdir -p "$BASE_DIR/ics-ot"
mkdir -p "$BASE_DIR/general"
mkdir -p "$BASE_DIR/threat-intel"
mkdir -p "$BASE_DIR/reading-room"

echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Function to download with retry
download_file() {
    local url="$1"
    local output="$2"
    local description="$3"

    echo -e "${YELLOW}Downloading: ${description}...${NC}"

    if wget -q --show-progress -O "$output" "$url" 2>/dev/null; then
        echo -e "${GREEN}✅ Downloaded: $(basename "$output")${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  Failed to download ${description}${NC}"
        echo -e "${YELLOW}   You may need to download manually from: ${url}${NC}"
        return 1
    fi
}

# Download SANS ISC Threat Feeds (Always work - these are direct text files)
echo -e "${BLUE}Downloading SANS ISC Threat Feeds...${NC}"

download_file \
    "https://isc.sans.edu/block.txt" \
    "$BASE_DIR/threat-intel/blocklist.txt" \
    "ISC Blocklist (Top Malicious IPs)"

download_file \
    "https://isc.sans.edu/api/topips/records/100?text" \
    "$BASE_DIR/threat-intel/top_100_ips.txt" \
    "Top 100 Attacking IPs"

download_file \
    "https://isc.sans.edu/feeds/threatintel.txt" \
    "$BASE_DIR/threat-intel/threat_intel.txt" \
    "Threat Intelligence Feed"

echo ""
echo -e "${BLUE}White Papers (PDFs require manual download)${NC}"
echo -e "${YELLOW}Note: SANS PDFs often require form submission. Downloading what's available...${NC}"
echo ""

# Note: Most SANS white papers require email submission, so we'll document the URLs
# and let the user download manually if needed

cat > "$BASE_DIR/DOWNLOAD_INSTRUCTIONS.md" << 'EOF'
# SANS White Papers Manual Download Instructions

The following white papers require manual download (email submission):

## Critical for INSA (ICS/OT Focus)

1. **SANS 2024 State of ICS/OT Cybersecurity** (2.31 MB)
   - URL: https://www.sans.org/white-papers/sans-2024-state-ics-ot-cybersecurity
   - Save to: ics-ot/sans_ics_ot_2024.pdf
   - Priority: CRITICAL

2. **2025 ICS/OT Cybersecurity Budget Report**
   - URL: https://www.sans.org/white-papers/2025-ics-ot-cybersecurity-budget-spending-trends-challenges-future
   - Save to: ics-ot/sans_ics_budget_2025.pdf
   - Priority: HIGH

3. **How to Use IEC 62443 (2020)**
   - URL: https://www.sans.org/webcasts/downloads/116935/slides
   - Save to: ics-ot/sans_iec62443_2020.pdf
   - Priority: CRITICAL

## General Reports (Optional but Recommended)

4. **SANS 2025 SOC Survey**
   - URL: https://www.sans.org/white-papers/sans-2025-soc-survey
   - Save to: general/sans_soc_2025.pdf

5. **SANS 2025 AI Survey**
   - URL: https://www.sans.org/white-papers/sans-2025-ai-survey-measuring-ai-impact-security-three-years-later
   - Save to: general/sans_ai_2025.pdf

6. **SANS Attack Surface Management Survey 2025**
   - URL: https://www.sans.org/white-papers/sans-attack-surface-management-survey-2025
   - Save to: general/sans_asm_2025.pdf

## Download Process

1. Visit each URL above
2. Fill out the brief form (name, email, company)
3. Download PDF
4. Save to the specified location

## SANS Reading Room (1000+ Papers)

Visit: https://www.sans.org/reading-room/

Search for:
- "Industrial Control Systems"
- "SCADA"
- "OT Security"
- "Oil and Gas"
- "Critical Infrastructure"

Save papers to: reading-room/

## Threat Intelligence (Already Downloaded)

✅ ISC Blocklist: threat-intel/blocklist.txt
✅ Top 100 IPs: threat-intel/top_100_ips.txt
✅ Threat Intel Feed: threat-intel/threat_intel.txt

These update hourly (max). Use cron job to refresh.
EOF

echo -e "${GREEN}✅ Download instructions created: $BASE_DIR/DOWNLOAD_INSTRUCTIONS.md${NC}"
echo ""

# Check what we downloaded
echo -e "${BLUE}Summary:${NC}"
echo ""
echo -e "${GREEN}Threat Intelligence Feeds (Auto-downloaded):${NC}"
ls -lh "$BASE_DIR/threat-intel/" 2>/dev/null || echo "  (directory empty)"
echo ""

echo -e "${YELLOW}White Papers (Require manual download):${NC}"
echo "  See: $BASE_DIR/DOWNLOAD_INSTRUCTIONS.md"
echo ""

# Create README
cat > "$BASE_DIR/README.md" << 'EOF'
# SANS Knowledge Base for RAG System

**Purpose:** Enhance autonomous agent security intelligence
**Source:** SANS Institute (free resources)
**Date:** November 1, 2025

## Directory Structure

```
sans/
├── ics-ot/              # ICS/OT cybersecurity reports (CRITICAL for Oil & Gas)
├── general/             # General cybersecurity reports
├── threat-intel/        # Live threat feeds from SANS ISC (updated hourly)
├── reading-room/        # SANS Reading Room papers (download manually)
├── DOWNLOAD_INSTRUCTIONS.md
└── README.md (this file)
```

## What's Here

### Threat Intelligence (Auto-updated)
- **blocklist.txt** - Top malicious IPs (block these)
- **top_100_ips.txt** - Top 100 attackers
- **threat_intel.txt** - Comprehensive threat intelligence feed

Update frequency: Hourly (max) via cron job

### White Papers (Manual download required)
See `DOWNLOAD_INSTRUCTIONS.md` for URLs and process.

Priority downloads:
1. SANS 2024 State of ICS/OT Cybersecurity
2. 2025 ICS/OT Budget Report
3. IEC 62443 Implementation Guide

## Integration with RAG

The `system_knowledge_rag.py` module will query these files when agents need:
- Security threat information
- ICS/OT best practices
- IEC 62443 compliance guidance
- Incident response procedures
- Budget planning data

## Licensing

**SANS ISC Feeds:**
- License: Creative Commons "Share Alike"
- Use: Free for non-commercial with attribution
- Attribution: "SANS Technology Institute, Internet Storm Center"

**SANS White Papers:**
- License: Free download, no resale
- Use: Internal training and reference
- Attribution: "SANS Institute" + URL

## Maintenance

**Weekly:**
- Check for new SANS white papers (2025 surveys/reports)
- Download relevant Reading Room papers

**Hourly (automated via cron):**
- Update ISC threat feeds
- Refresh blocklist

**Monthly:**
- Review usage statistics
- Add papers based on agent queries

## Contact

User-Agent for ISC API: "INSA-Automation w.aroca@insaing.com"
Organization: Insa Automation Corp
Purpose: Internal cybersecurity automation
EOF

echo -e "${GREEN}✅ README created: $BASE_DIR/README.md${NC}"
echo ""

# Create cron job for threat feed updates
CRON_SCRIPT="/home/wil/automation/agents/orchestrator/update_sans_feeds.sh"

cat > "$CRON_SCRIPT" << 'EOF'
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
EOF

chmod +x "$CRON_SCRIPT"
echo -e "${GREEN}✅ Cron update script created: $CRON_SCRIPT${NC}"
echo ""

# Final summary
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Summary & Next Steps${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${GREEN}✅ Completed:${NC}"
echo "  • Directory structure created"
echo "  • SANS ISC threat feeds downloaded"
echo "  • Documentation created"
echo "  • Cron update script ready"
echo ""
echo -e "${YELLOW}⚠️  Manual action required:${NC}"
echo "  1. Read: $BASE_DIR/DOWNLOAD_INSTRUCTIONS.md"
echo "  2. Download priority PDFs (3 critical files)"
echo "  3. Set up hourly cron job:"
echo "     sudo ln -s $CRON_SCRIPT /etc/cron.hourly/sans-feeds"
echo ""
echo -e "${BLUE}Then:${NC}"
echo "  4. Update system_knowledge_rag.py to include SANS paths"
echo "  5. Test RAG with: 'What are current ICS threats?'"
echo ""
echo -e "${GREEN}Your agents are ready for SANS security intelligence!${NC}"
