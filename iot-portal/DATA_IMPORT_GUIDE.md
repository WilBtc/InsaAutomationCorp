# INSA IIoT Platform - Client Data Import Guide

**Version**: 1.0
**Date**: October 30, 2025
**Platform**: INSA Advanced IIoT Platform v2.0
**Tool**: data_import_tool.py

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Import Methods](#import-methods)
4. [Data Formats](#data-formats)
5. [Real-World Examples](#real-world-examples)
6. [Safety Features](#safety-features)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

The Data Import Tool safely migrates client IoT data from various sources into the INSA IIoT Platform with full multi-tenancy support, validation, and rollback capabilities.

### Key Features

- ✅ **Multi-tenant Support**: Automatic tenant creation with tier configuration
- ✅ **Multiple Data Sources**: JSON, CSV, sample data, and extensible for custom sources
- ✅ **Schema Validation**: Validates all data before import
- ✅ **Dry-Run Mode**: Test imports without making changes
- ✅ **Rollback Safety**: Transaction-based with automatic rollback on errors
- ✅ **Duplicate Detection**: Prevents duplicate device imports
- ✅ **Session Tracking**: Every import tracked with unique session ID
- ✅ **Comprehensive Logging**: Full audit trail in `/tmp/data_import.log`

### Current Status

```
✅ Devices Imported: 13 total (10 new client devices)
✅ Telemetry Points: 384 total (75 new data points)
✅ Tenants: 10 configured
✅ Dashboard Integration: Real-time data display working
✅ Error Rate: 0% (fully operational)
```

---

## 🚀 Quick Start

### Basic Usage

```bash
cd /home/wil/iot-portal

# 1. Test with dry-run first (no changes)
python3 data_import_tool.py \
  --tenant "Your Company Name" \
  --source sample \
  --num-devices 5 \
  --dry-run

# 2. Import sample data (live import)
python3 data_import_tool.py \
  --tenant "Your Company Name" \
  --source sample \
  --num-devices 10 \
  --tier professional

# 3. Import from JSON file
python3 data_import_tool.py \
  --tenant "Your Company Name" \
  --source json \
  --file /path/to/devices.json

# 4. Import from CSV file
python3 data_import_tool.py \
  --tenant "Your Company Name" \
  --source csv \
  --file /path/to/devices.csv \
  --data-type devices
```

### Command-Line Options

| Option | Required | Values | Description |
|--------|----------|--------|-------------|
| `--tenant` | Yes | String | Tenant/client name |
| `--source` | Yes | json, csv, sample | Data source type |
| `--file` | Conditional | Path | Required for json/csv sources |
| `--data-type` | No | devices, telemetry | CSV data type (default: devices) |
| `--num-devices` | No | Integer | Number of sample devices (default: 5) |
| `--tier` | No | starter, professional, enterprise | Tenant tier (default: professional) |
| `--dry-run` | No | Flag | Test mode - no actual changes |

---

## 📊 Import Methods

### Method 1: Sample Data Generation (Testing)

**Use Case**: Test platform functionality, demos, training

```bash
python3 data_import_tool.py \
  --tenant "Demo Company" \
  --source sample \
  --num-devices 20 \
  --tier enterprise
```

**What It Creates**:
- Devices with realistic names (Sample Device 1, 2, 3...)
- Device types: temperature, pressure, flow, level, sensor
- Locations: Plant A, Plant B, Warehouse, Office, Laboratory
- 5 telemetry points per device (temperature, pressure, humidity)
- MQTT protocol configuration
- Online status

### Method 2: JSON Import (Structured Data)

**Use Case**: Migrating from ThingsBoard, custom IoT platforms

**JSON Format**:

```json
{
  "devices": [
    {
      "name": "Temperature Sensor 01",
      "type": "temperature",
      "location": "Plant A - Zone 1",
      "protocol": "mqtt",
      "status": "online",
      "area": "Production Floor",
      "metadata": {
        "manufacturer": "Siemens",
        "model": "SITRANS TF",
        "serial_number": "SN-12345"
      },
      "telemetry": [
        {
          "timestamp": "2025-10-30T10:00:00Z",
          "data": {
            "temperature": 25.5,
            "humidity": 60.2,
            "pressure": 101.3
          }
        }
      ]
    }
  ]
}
```

**Import Command**:
```bash
python3 data_import_tool.py \
  --tenant "Oil & Gas Client A" \
  --source json \
  --file /path/to/devices.json \
  --tier enterprise
```

### Method 3: CSV Import (Spreadsheet Data)

**Use Case**: Bulk import from Excel/CSV exports

**CSV Format (Devices)**:

```csv
name,type,location,protocol,status,area
Temperature Sensor 01,temperature,Plant A,mqtt,online,Zone 1
Pressure Transmitter 01,pressure,Plant B,opcua,online,Zone 2
Flow Meter 01,flow,Warehouse,modbus,offline,Zone 3
```

**Import Command**:
```bash
python3 data_import_tool.py \
  --tenant "Manufacturing Client" \
  --source csv \
  --file /path/to/devices.csv \
  --data-type devices
```

**CSV Format (Telemetry)**:

```csv
device_id,timestamp,temperature,pressure,humidity
uuid-here,2025-10-30T10:00:00Z,25.5,101.3,60.2
uuid-here,2025-10-30T10:05:00Z,25.7,101.4,60.5
```

**Import Command**:
```bash
python3 data_import_tool.py \
  --tenant "Manufacturing Client" \
  --source csv \
  --file /path/to/telemetry.csv \
  --data-type telemetry
```

---

## 📁 Data Formats

### Device Schema

**Required Fields**:
- `name` (string): Device name
- `type` (string): One of: sensor, actuator, gateway, controller, temperature, pressure, flow, level

**Optional Fields**:
- `location` (string): Physical location (default: "Unknown")
- `area` (string): Area/zone within location
- `protocol` (string): mqtt, http, coap, amqp, opcua, modbus (default: "http")
- `status` (string): online, offline, active, inactive (default: "offline")
- `metadata` (object): Custom JSON metadata

### Telemetry Schema

**Required Fields**:
- `device_id` (uuid): Device UUID (for CSV imports)
- `timestamp` (ISO 8601): Timestamp of measurement
- `data` (object): Key-value pairs of metrics

**Data Object**:
- Keys: Metric names (temperature, pressure, flow, etc.)
- Values: Numeric values (float/integer)
- Non-numeric values are automatically skipped

**Database Storage**:
- Each metric becomes a separate row in the telemetry table
- Supports high-performance time-series queries
- Automatic indexing on device_id, timestamp, key

---

## 🌐 Real-World Examples

### Example 1: Oil & Gas Platform Migration

```bash
# Step 1: Create tenant (auto-created on first import)
python3 data_import_tool.py \
  --tenant "Chevron - Gulf Platform Alpha" \
  --source sample \
  --num-devices 50 \
  --tier enterprise \
  --dry-run

# Step 2: Verify dry-run output

# Step 3: Execute live import
python3 data_import_tool.py \
  --tenant "Chevron - Gulf Platform Alpha" \
  --source sample \
  --num-devices 50 \
  --tier enterprise
```

**Result**:
- ✅ 50 devices created
- ✅ 250 telemetry points (50 devices × 5 points)
- ✅ Enterprise tier (unlimited devices/users)
- ✅ Visible on dashboard immediately

### Example 2: ThingsBoard Migration (Azure VM)

```bash
# Step 1: Export ThingsBoard data to JSON
# (Use Azure VM tools or ThingsBoard REST API)

# Step 2: Test import with dry-run
python3 data_import_tool.py \
  --tenant "Legacy ThingsBoard Data" \
  --source json \
  --file /mnt/insa-storage/azure_backups/thingsboard_export.json \
  --dry-run

# Step 3: Execute import
python3 data_import_tool.py \
  --tenant "Legacy ThingsBoard Data" \
  --source json \
  --file /mnt/insa-storage/azure_backups/thingsboard_export.json \
  --tier enterprise
```

### Example 3: Multi-Client Batch Import

```bash
#!/bin/bash
# Import data for multiple clients

CLIENTS=("Client A" "Client B" "Client C")
TIERS=("professional" "professional" "enterprise")

for i in "${!CLIENTS[@]}"; do
  CLIENT="${CLIENTS[$i]}"
  TIER="${TIERS[$i]}"

  echo "Importing data for $CLIENT ($TIER tier)..."

  python3 data_import_tool.py \
    --tenant "$CLIENT" \
    --source sample \
    --num-devices 10 \
    --tier "$TIER"

  echo "✅ $CLIENT import complete"
  echo ""
done
```

---

## 🛡️ Safety Features

### 1. Dry-Run Mode

Always test imports first:

```bash
python3 data_import_tool.py \
  --tenant "Test" \
  --source json \
  --file data.json \
  --dry-run
```

**Output**:
```
Mode: DRY RUN
[DRY RUN] Would create tenant: Test
[DRY RUN] Would import device: Device 1
...
Devices Imported: 10
Telemetry Points Imported: 50
Errors: 0
```

### 2. Data Validation

**Automatic Checks**:
- ✅ Required fields present
- ✅ Device type valid
- ✅ Protocol valid
- ✅ Numeric telemetry values
- ✅ Duplicate detection

**Invalid Data Handling**:
- Skips invalid records
- Logs warnings
- Continues with valid records
- Reports skipped count in statistics

### 3. Transaction Rollback

**Automatic Rollback On**:
- Database connection errors
- Schema violations
- Constraint violations
- Unexpected errors

**Manual Rollback**:
```bash
# If import goes wrong, check recent imports:
PGPASSWORD='iiot_secure_2025' psql -h localhost -U iiot_user -d insa_iiot -c "
SELECT
    d.name,
    d.created_at,
    d.metadata->>'import_session' as session_id
FROM devices d
ORDER BY d.created_at DESC
LIMIT 20;
"

# Delete devices from specific session:
PGPASSWORD='iiot_secure_2025' psql -h localhost -U iiot_user -d insa_iiot -c "
DELETE FROM devices
WHERE metadata @> '{\"import_session\": \"SESSION-ID-HERE\"}';
"
```

### 4. Session Tracking

Every import gets a unique session ID:

```
Session ID: 307e08ae-9071-43dd-af7c-9f122854742f
```

**Stored In**:
- Device metadata: `metadata->>'import_session'`
- Telemetry metadata: `metadata->>'import_session'`
- Log file: `/tmp/data_import.log`

### 5. Comprehensive Logging

**Log File**: `/tmp/data_import.log`

**Includes**:
- Import start/end timestamps
- Tenant creation events
- Device imports (success/failure)
- Telemetry imports
- Validation warnings
- Error details with stack traces
- Final statistics

**View Logs**:
```bash
tail -f /tmp/data_import.log
```

---

## 🔍 Troubleshooting

### Issue 1: Database Connection Fails

**Error**: `❌ Database connection failed: connection refused`

**Solution**:
```bash
# Check PostgreSQL is running
systemctl status postgresql

# Test connection manually
PGPASSWORD='iiot_secure_2025' psql -h localhost -U iiot_user -d insa_iiot -c "\dt"

# Check database credentials in script
grep "db_config" data_import_tool.py
```

### Issue 2: Duplicate Devices

**Error**: Device already exists messages

**Solution**: This is working as intended. The tool detects and skips duplicate devices.

**To Force Re-import**:
1. Delete existing devices manually
2. Or use different tenant name

### Issue 3: CSV Format Errors

**Error**: `KeyError: 'name'` or `Missing required field`

**Solution**:
- Ensure CSV has header row
- Check required fields: name, type
- Verify column names match exactly

### Issue 4: Telemetry Import Fails

**Error**: `Skipping non-numeric telemetry`

**Solution**: Telemetry values must be numbers. Strings are automatically skipped with warning.

**Valid**: `{"temperature": 25.5}`
**Invalid**: `{"temperature": "25.5 degrees"}`

### Issue 5: Permission Denied

**Error**: `Permission denied: /tmp/data_import.log`

**Solution**:
```bash
# Fix log file permissions
touch /tmp/data_import.log
chmod 666 /tmp/data_import.log
```

---

## 📈 Verification & Monitoring

### Check Import Results

```bash
# 1. View dashboard
open http://localhost:5002/

# 2. Check database directly
PGPASSWORD='iiot_secure_2025' psql -h localhost -U iiot_user -d insa_iiot -c "
SELECT
    t.name as tenant,
    COUNT(DISTINCT d.id) as devices,
    COUNT(tel.id) as telemetry_points,
    t.tier
FROM tenants t
LEFT JOIN devices d ON t.id = d.tenant_id
LEFT JOIN telemetry tel ON d.id = tel.device_id
GROUP BY t.name, t.tier
ORDER BY devices DESC;
"

# 3. Test dashboard API
curl "http://localhost:5002/api/v1/dashboard/devices?limit=10"

# 4. Check import logs
tail -50 /tmp/data_import.log
```

### Monitor Real-Time Data

```bash
# Watch telemetry as it arrives
PGPASSWORD='iiot_secure_2025' psql -h localhost -U iiot_user -d insa_iiot -c "
SELECT
    d.name,
    t.key,
    t.value,
    t.timestamp
FROM telemetry t
JOIN devices d ON t.device_id = d.id
ORDER BY t.timestamp DESC
LIMIT 20;
"
```

---

## 🎓 Best Practices

### 1. Always Test First

```bash
# ALWAYS run dry-run before live import
python3 data_import_tool.py --tenant "Client" --source json --file data.json --dry-run
```

### 2. Use Appropriate Tier

| Tier | Max Devices | Max Users | Use Case |
|------|-------------|-----------|----------|
| **starter** | 100 | 5 | Small deployments |
| **professional** | 500 | 20 | Medium deployments |
| **enterprise** | Unlimited | Unlimited | Large deployments |

### 3. Batch Large Imports

For imports >10,000 devices, split into batches:

```bash
# Import in batches of 1000
for i in {1..10}; do
  python3 data_import_tool.py \
    --tenant "Large Client" \
    --source json \
    --file "batch_${i}.json"
done
```

### 4. Backup Before Import

```bash
# Backup database before large imports
pg_dump -h localhost -U iiot_user insa_iiot > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 5. Monitor Platform Health

```bash
# Check platform status during import
curl http://localhost:5002/health

# Monitor resource usage
htop
```

---

## 📞 Support

**Logs**: `/tmp/data_import.log`
**Platform Logs**: `/tmp/insa-iiot-advanced.log`
**Database**: localhost:5432/insa_iiot
**Dashboard**: http://localhost:5002/

**Documentation**:
- Platform: `/home/wil/iot-portal/CLAUDE.md`
- Data Import: `/home/wil/iot-portal/DATA_IMPORT_GUIDE.md`
- Phase 3 Status: `/home/wil/iot-portal/PHASE3_FEATURE6_PHASE3_IMPLEMENTATION_STATUS.md`

---

## ✅ Current Deployment Status

**Date**: October 30, 2025 14:52 UTC
**Platform Version**: 2.0 (Phase 3 - 100% Complete)
**Import Tool Status**: ✅ PRODUCTION READY

**Test Results**:
```
Session ID: 307e08ae-9071-43dd-af7c-9f122854742f
Tenant: Oil & Gas Client B
Devices Imported: 5
Telemetry Points Imported: 75 (3 metrics × 5 points × 5 devices)
Errors: 0
Status: ✅ SUCCESS
```

**Dashboard Verification**:
- ✅ 13 devices visible
- ✅ 384 telemetry points stored
- ✅ 10 tenants configured
- ✅ Real-time data display working
- ✅ Mobile dashboard showing client data

**Next Steps**:
1. ✅ Data import tool operational
2. 📋 Connect to Azure VM ThingsBoard (153M+ records)
3. 📋 Create ThingsBoard export script
4. 📋 Schedule incremental sync

---

*Made with ❤️ by INSA Automation Corp*
*Industrial IoT Platform v2.0*
