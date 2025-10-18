#!/bin/bash
################################################################################
# INSA CRM Platform - Quick Customization Script
# Run this to get started with INSA-specific customization
################################################################################

set -e  # Exit on error

echo "================================================================================"
echo "INSA CRM Platform - Quick Customization"
echo "================================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Create directories
echo "Step 1: Creating directories for INSA data..."
sudo mkdir -p /var/lib/insa-crm/historical_projects
sudo mkdir -p /var/lib/insa-crm/vendor_catalog
sudo mkdir -p /var/lib/insa-crm/templates
sudo chown -R wil:wil /var/lib/insa-crm
echo -e "${GREEN}✅ Directories created${NC}"
echo ""

# Step 2: Check existing indexed projects
echo "Step 2: Checking existing indexed projects..."
cd ~/insa-crm-platform/core
source venv/bin/activate
python3 -c "
from agents.quote_generation.rag_knowledge_base import RAGKnowledgeBase
rag = RAGKnowledgeBase()
stats = rag.get_statistics()
print(f'Projects in knowledge base: {stats.get(\"total_projects\", 0)}')
if stats.get('total_projects', 0) > 0:
    print('✅ Knowledge base is operational')
    print('Projects:', stats.get('projects', []))
else:
    print('⚠️  No projects indexed yet')
"
echo ""

# Step 3: Create vendor catalog table
echo "Step 3: Creating vendor catalog table..."
sudo -u postgres psql -d insa_crm <<'SQL'
-- Create vendor catalog if not exists
CREATE TABLE IF NOT EXISTS vendor_catalog (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    vendor VARCHAR(100) NOT NULL,
    part_number VARCHAR(100) NOT NULL,
    description TEXT,
    unit_cost NUMERIC(10,2),
    currency VARCHAR(3) DEFAULT 'USD',
    lead_time_days INTEGER,
    preferred BOOLEAN DEFAULT false,
    usage_count INTEGER DEFAULT 0,
    last_used_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vendor_catalog_category ON vendor_catalog(category);
CREATE INDEX IF NOT EXISTS idx_vendor_catalog_preferred ON vendor_catalog(preferred);

-- Insert INSA's common parts (Allen-Bradley PLCs)
INSERT INTO vendor_catalog (category, vendor, part_number, description, unit_cost, preferred, usage_count) VALUES
('PLC', 'Allen-Bradley', '1769-L33ER', 'CompactLogix 5370 L3 Controller, 2MB, Ethernet', 3200.00, true, 15),
('PLC', 'Allen-Bradley', '1769-IF8', 'CompactLogix 8-Ch Analog Input Module', 450.00, true, 20),
('PLC', 'Allen-Bradley', '1769-OF8C', 'CompactLogix 8-Ch Analog Output Module', 520.00, true, 18),
('HMI', 'Rockwell', '2711P-T15C4D9', 'PanelView Plus 7 Standard 15-inch', 2500.00, true, 12),
('HMI', 'Ignition', 'IGN-SCADA-UNL', 'Ignition SCADA Unlimited License', 5000.00, true, 8)
ON CONFLICT DO NOTHING;

SELECT 'Vendor catalog created! Parts: ' || COUNT(*) FROM vendor_catalog;
SQL

echo -e "${GREEN}✅ Vendor catalog created${NC}"
echo ""

# Step 4: Add INSA communication templates
echo "Step 4: Adding INSA communication templates..."
sudo -u postgres psql -d insa_crm <<'SQL'
-- INSA-specific templates
INSERT INTO communication_templates (template_id, channel, name, subject, content_html, content_text, category, variables) VALUES
('insa_welcome_2025', 'email', 'INSA Welcome Email (2025)',
'Welcome to INSA Automation - {{customer_name}}',
'<html><body style="font-family: Arial;"><h1 style="color: #003366;">INSA Automation</h1><p>Dear {{customer_name}},</p><p>Thank you for reaching out to INSA Automation. We specialize in delivering turnkey industrial control solutions for oil & gas, pharma, and food & beverage industries.</p><p><strong>What makes INSA different:</strong></p><ul><li>✅ 10+ years experience</li><li>✅ Allen-Bradley & Siemens certified engineers</li><li>✅ IEC 62443 cybersecurity compliance built-in</li></ul><p>Our team will have a detailed quote for you within 24 hours.</p><p>Best regards,<br><strong>The INSA Team</strong></p></body></html>',
'Dear {{customer_name}}, Thank you for reaching out to INSA Automation...',
'welcome',
'{"customer_name": "string", "company": "string", "industry": "string"}'::jsonb)
ON CONFLICT (template_id) DO UPDATE SET
    content_html = EXCLUDED.content_html,
    updated_at = CURRENT_TIMESTAMP;

SELECT 'INSA templates added! Total: ' || COUNT(*) FROM communication_templates;
SQL

echo -e "${GREEN}✅ INSA templates added${NC}"
echo ""

# Step 5: Create customization guide
echo "Step 5: Creating customization checklist..."
cat > /tmp/insa_customization_checklist.txt <<'CHECKLIST'
================================================================================
INSA CRM Platform - Customization Checklist
================================================================================

WEEK 1: DATA COLLECTION
------------------------
[ ] Export historical project data (last 2-3 years)
    Location: /var/lib/insa-crm/historical_projects/
    Format: One folder per project with metadata.json, quote.json, bom.csv

[ ] Export INSA vendor catalog (Excel → CSV)
    Current: 5 sample parts added (Allen-Bradley PLCs)
    Todo: Add remaining preferred parts

[ ] Export historical deal data (win/loss analysis)
    For: Lead scoring optimization
    Format: CSV with columns: customer, industry, budget, won, margin

[ ] Gather INSA email templates & brand assets
    Current: 1 welcome template added
    Todo: Quote delivery, follow-up templates

WEEK 2: DATA INGESTION
-----------------------
[ ] Run historical project ingestion script
    Script: ~/insa-crm-platform/scripts/ingest_historical_projects.py
    Target: RAG knowledge base (ChromaDB)

[ ] Import vendor catalog into database
    Table: vendor_catalog (✅ Created)
    Current: 5 parts | Goal: 50+ parts

[ ] Analyze ideal customer profile
    Script: ~/insa-crm-platform/scripts/analyze_ideal_customer.py
    Output: INSA-specific scoring weights

[ ] Update lead scoring weights
    File: core/agents/lead_qualification_agent.py
    Add: INSA_SCORING_WEIGHTS

WEEK 3: WORKFLOW CUSTOMIZATION
-------------------------------
[ ] Interview sales team (30 min)
    Document: INSA's actual sales process
    Output: config/insa_sales_workflow.yaml

[ ] Code INSA-specific workflow
    File: core/agents/automation_orchestrator.py
    Function: create_insa_sales_workflow()

[ ] Test end-to-end with real lead
    Expected: Quote with real INSA parts

[ ] Setup Slack integration (optional)
    Channels: #sales-leads, #engineering
    Notifications: High-value leads, quotes generated

WEEK 4: TEAM TRAINING & LAUNCH
-------------------------------
[ ] Train sales team (30 min)
    Topics: Dashboard, lead review, quote approval

[ ] Train engineering team (30 min)
    Topics: Vendor catalog, BOM customization

[ ] Go live with 1-2 test leads
    Monitor: Accuracy, quality, edge cases

[ ] Weekly review meeting
    Schedule: Every Monday 9 AM
    Agenda: Review leads, quotes, continuous improvement

QUICK WINS (TODAY):
-------------------
[✅] Vendor catalog created (5 parts)
[✅] INSA welcome template added
[✅] Directory structure created
[ ] Index INSAGTEC-6598 project (if not already)
[ ] Add 10 more preferred parts to catalog
[ ] Create first test lead

================================================================================
Next Steps:
1. Review ~/insa-crm-platform/COMPANY_CUSTOMIZATION_ROADMAP.md
2. Start with data collection (historical projects)
3. Reach out for help: w.aroca@insaing.com
================================================================================
CHECKLIST

cat /tmp/insa_customization_checklist.txt
echo ""

# Step 6: Summary
echo "================================================================================"
echo "CUSTOMIZATION SETUP COMPLETE!"
echo "================================================================================"
echo ""
echo -e "${GREEN}✅ Directories created${NC}"
echo -e "${GREEN}✅ Vendor catalog initialized (5 parts)${NC}"
echo -e "${GREEN}✅ INSA templates added (1 template)${NC}"
echo -e "${GREEN}✅ Customization checklist created${NC}"
echo ""
echo "Next Steps:"
echo "1. Review: ~/insa-crm-platform/COMPANY_CUSTOMIZATION_ROADMAP.md"
echo "2. Check: cat /tmp/insa_customization_checklist.txt"
echo "3. Start: Collect historical project data"
echo ""
echo "Quick Test:"
echo "  cd ~/insa-crm-platform/core"
echo "  source venv/bin/activate"
echo "  python3 agents/automation_orchestrator.py"
echo ""
echo "Vendor Catalog:"
echo "  sudo -u postgres psql -d insa_crm -c 'SELECT * FROM vendor_catalog;'"
echo ""
echo "================================================================================"
