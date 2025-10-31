# Bitrix24 Integration - Quick Start for Claude Code

**Use this guide when deploying Bitrix24 → INSA CRM integration workflows.**

---

## 🚀 Quick Deployment Commands (Natural Language)

### Step 1: Test Bitrix24 Connection

```
"List the first 10 leads from Bitrix24"
```
*Uses: bitrix24_list_leads tool*
*Expected: Returns 10 leads with ID, NAME, EMAIL, COMPANY_TITLE*

```
"Get full details for Bitrix24 lead ID 123"
```
*Uses: bitrix24_get_lead tool*
*Expected: Complete lead object with all fields*

---

### Step 2: Test ERPNext Connection

```
"List ERPNext leads filtered by email john@acme.com"
```
*Uses: erpnext_list_leads tool*
*Expected: Returns existing ERPNext leads or empty list*

```
"Create ERPNext lead for John Smith, email john@acme.com, company ACME Corp, score 85"
```
*Uses: erpnext_create_lead tool*
*Expected: Lead created successfully in ERPNext*

---

### Step 3: Test Mautic Connection

```
"Create Mautic contact for john@acme.com with tags: Bitrix24, Oil & Gas, HOT"
```
*Uses: mautic_create_contact tool*
*Expected: Contact created in Mautic with tags and points*

```
"Add Mautic contact ID 123 to segment 'Fast Track Sales'"
```
*Uses: mautic_add_contact_to_segment tool*
*Expected: Contact added to segment*

---

### Step 4: Create n8n Workflow

**Option A: Import JSON (Fastest)**

```
"Import n8n workflow from ~/insa-crm-platform/automation/workflows/bitrix24-autonomous-lead-sync.json"
```
*Uses: n8n_create_workflow tool*
*Expected: Workflow created in n8n with ID returned*

**Option B: Build from Scratch (More Control)**

See: `~/BITRIX24_AUTONOMOUS_INTEGRATION_GUIDE.md` for detailed specifications

---

### Step 5: Activate Workflow

```
"Activate n8n workflow ID 123"
```
*Uses: n8n_activate_workflow tool*
*Expected: Workflow status changed to active*

---

### Step 6: Test Workflow

```
"Trigger n8n workflow ID 123 manually with test data"
```
*Uses: n8n_trigger_workflow tool*
*Expected: Workflow executes, returns execution ID*

```
"Show me the last 10 n8n workflow executions"
```
*Uses: n8n_list_executions tool*
*Expected: List of recent executions with status (success/error)*

```
"Get execution details for n8n execution ID abc123"
```
*Uses: n8n_get_execution tool*
*Expected: Full execution log with input/output for each node*

---

## 📋 Common Operations

### Sync Single Lead from Bitrix24

```bash
# 1. Get lead from Bitrix24
"Get Bitrix24 lead ID 123"

# 2. Transform to INSA format (manual or via Code Node)

# 3. Create in ERPNext
"Create ERPNext lead for [name] with email [email], score [score]"

# 4. Create in Mautic
"Create Mautic contact for [email] with tags: Bitrix24, [pipeline], [priority]"

# 5. Add comment to Bitrix24
"Add comment to Bitrix24 lead 123: 'Synced to INSA CRM, Score: 85/100'"
```

---

### Monitor Integration Health

```bash
# Check recent workflow executions
"Show n8n executions for workflow 'Bitrix24 Lead Sync'"

# Check ERPNext lead count
"List ERPNext leads created in the last 24 hours"

# Check Mautic contact count
"List Mautic contacts with tag 'Bitrix24'"

# Check platform health
"Run platform health check"
# Uses: platform_health_check tool (Platform Admin MCP)
```

---

### Debug Failed Sync

```bash
# 1. Check n8n execution logs
"Get details for failed n8n execution ID abc123"

# 2. Check ERPNext logs
"Check ERPNext for lead with email john@acme.com"

# 3. Check Mautic logs
"Check Mautic for contact with email john@acme.com"

# 4. Retry manually
"Trigger n8n workflow ID 123 with input: {lead_id: 123}"
```

---

## 🔧 Troubleshooting

### Problem: Webhook not receiving events

**Solution:**
1. Check Bitrix24 webhook configuration (insa.bitrix24.es → Settings → Webhooks)
2. Verify n8n workflow webhook URL is correct
3. Test webhook manually:
   ```bash
   curl -X POST [webhook-url] -H "Content-Type: application/json" \
     -d '{"event": "ONCRMLEADADD", "data": {"FIELDS": {"ID": "123"}}}'
   ```

### Problem: Spam leads getting through

**Solution:**
Adjust spam filter in n8n Code Node (Step 3 of workflow):
- Add more keywords to exclude list
- Check SOURCE_ID patterns
- Add email domain blacklist

### Problem: AI scoring inaccurate

**Solution:**
Adjust scoring factors in n8n Code Node (Step 6 of workflow):
- Modify point values (+30, +20, +10, +5)
- Add new factors (industry keywords, country codes)
- Change category thresholds (80, 60, 40)

### Problem: Duplicate leads in ERPNext

**Solution:**
Enable duplicate check in n8n (Step 6):
```javascript
// Before erpnext_create_lead, add:
const existingLeads = await erpnext_list_leads({
  filters: {email_id: lead.email}
});

if (existingLeads.length > 0) {
  // Update instead of create
  await erpnext_update_lead(existingLeads[0].name, {
    custom_lead_score: score
  });
}
```

---

## 📊 Success Metrics

### Daily Checks
- [ ] n8n workflow execution success rate > 95%
- [ ] Average processing time < 10 seconds
- [ ] Zero critical errors in logs
- [ ] All 3 systems synced (Bitrix24, ERPNext, Mautic)

### Weekly Reviews
- [ ] Lead quality: 30%+ qualified (vs 20% before)
- [ ] Spam filtering: 80%+ filtered
- [ ] Deal conversion: Track trend (target 12% vs 8% baseline)
- [ ] Team feedback: Positive (NPS > 8)

### Monthly Analysis
- [ ] Revenue impact: Track deals sourced from automation
- [ ] Time savings: Calculate hours saved vs manual entry
- [ ] Data quality: Check ERPNext/Mautic data completeness
- [ ] System health: Review error logs and failure patterns

---

## 🔗 Related Documentation

**Primary:**
- `~/BITRIX24_AUTONOMOUS_INTEGRATION_GUIDE.md` - Complete implementation guide
- `~/BITRIX24_DEPLOYMENT_COMPLETE_OCT31_2025.md` - Project summary

**MCP Tools:**
- `~/insa-crm-platform/mcp-servers/bitrix24-crm/README.md` - Bitrix24 tools reference
- `~/platforms/insa-crm/mcp-servers/erpnext-crm/README.md` - ERPNext tools reference
- `~/platforms/insa-crm/mcp-servers/mautic-admin/README.md` - Mautic tools reference
- `~/platforms/insa-crm/mcp-servers/n8n-admin/README.md` - n8n tools reference

**Data Analysis:**
- `~/BITRIX24_DATA_ANALYSIS_INSA_INGENIERIA.md` - CRM data insights
- `~/BITRIX24_INTEGRATION_ARCHITECTURE.md` - Workflow specifications

---

## 💡 Pro Tips

1. **Always test with sample data first** - Create test leads in Bitrix24 before deploying to production

2. **Monitor n8n executions closely** - First 48 hours are critical for catching edge cases

3. **Adjust AI scoring based on real data** - Initial weights are estimates, tune based on conversion rates

4. **Keep webhooks secure** - Bitrix24 webhook URL contains secret token, don't share publicly

5. **Enable email alerts** - Configure n8n to send alerts on workflow failures

6. **Document customizations** - If you modify workflows, update this guide

7. **Use MCP tools, not HTTP requests** - MCP tools handle auth, validation, error handling automatically

8. **Backup workflows before changes** - Export n8n workflows to JSON before modifying

---

**Made by:** INSA Automation Corp
**For:** Insa Ingeniería SAS
**Last Updated:** October 31, 2025
**Status:** ✅ Ready for Deployment
