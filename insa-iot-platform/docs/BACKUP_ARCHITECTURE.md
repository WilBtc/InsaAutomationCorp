# Automated Backup System Architecture

## Overview

The automated backup system ensures ALL IoT telemetry data is preserved permanently while the live TimescaleDB database maintains only the last 30 days for operational performance.

## Requirements (from CLAUDE.md)

- **Backup System**: Must have ALL IoT history data (unlimited retention)
- **Azure/Live Database**: Only last 30 days of IoT data
- **No Data Loss**: Backups must capture data before 30-day retention policy deletes it

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Flow Architecture                        │
└─────────────────────────────────────────────────────────────────┘

ESP Devices → TimescaleDB (30 days) → Automated Backup (Forever)
                     │
                     ├─→ Daily Full Backup → Local Storage
                     │                       (compressed)
                     │
                     └─→ Daily Incremental → Azure Blob Storage
                                            (long-term archive)
```

## Components

### 1. Local Backup System
**Location**: `/var/backups/timescaledb/`
**Retention**: 30 days (rolling)
**Format**: Compressed PostgreSQL dump
**Frequency**: Daily at 2 AM
**Purpose**: Fast local recovery, disaster recovery

### 2. Azure Blob Storage (Long-term Archive)
**Location**: Azure Storage Account
**Retention**: Unlimited (all historical data)
**Format**: Compressed PostgreSQL dump + metadata
**Frequency**: Daily at 3 AM (after local backup)
**Purpose**: Permanent archive, compliance, analytics

### 3. Backup Orchestrator Service
**Service**: `timescaledb-backup.service`
**Schedule**: Systemd timer (daily at 2 AM)
**Functions**:
- Execute pg_dump with optimal settings
- Compress backups (gzip level 6)
- Upload to Azure Blob Storage
- Verify backup integrity
- Clean up old local backups (>30 days)
- Send alerts on failure

## Backup Strategy

### Daily Full Backups
- **Time**: 2:00 AM (low traffic period)
- **Method**: `pg_dump` with custom format
- **Compression**: gzip level 6 (~90% compression)
- **Verification**: Checksum validation

### Incremental Data Capture
- **Method**: TimescaleDB continuous aggregates
- **Captures**: Only data at risk of deletion (>25 days old)
- **Frequency**: Daily

### Backup Rotation
- **Local**: Keep last 30 days
- **Azure**: Keep forever (with lifecycle policies)

## Implementation Details

### Backup Script Features
1. **Pre-backup validation**
   - Database connectivity check
   - Disk space check (require 10GB free)
   - Azure credentials validation

2. **Backup execution**
   - Use `pg_dump` with `--format=custom`
   - Include hypertable metadata
   - Capture TimescaleDB policies
   - Stream to gzip for compression

3. **Post-backup validation**
   - Calculate MD5 checksum
   - Test backup integrity with `pg_restore --list`
   - Verify file size (must be > 100KB)

4. **Azure upload**
   - Use Azure CLI or Python SDK
   - Upload with metadata (date, size, checksum)
   - Set blob tier to "Cool" for cost optimization

5. **Monitoring**
   - Log all operations
   - Send alerts on failure
   - Update Prometheus metrics
   - Record last successful backup time

## Data Retention Timeline

```
Day 0:  New data arrives → Stored in TimescaleDB
Day 7:  Data compressed (via compression policy)
Day 25: Data backed up to local + Azure (safety margin)
Day 30: Data deleted from TimescaleDB (via retention policy)
Day 60: Local backup deleted (via rotation)
Forever: Data remains in Azure Blob Storage
```

## Disaster Recovery

### Scenario 1: Database Corruption
**Recovery Time**: < 30 minutes
**Process**:
1. Stop application
2. Restore from latest local backup
3. Verify data integrity
4. Restart application

### Scenario 2: Complete Data Loss
**Recovery Time**: < 2 hours
**Process**:
1. Provision new TimescaleDB instance
2. Download backup from Azure
3. Restore with `pg_restore`
4. Verify hypertable configuration
5. Restart application

### Scenario 3: Point-in-Time Recovery
**Recovery Time**: Variable
**Process**:
1. Identify target date from Azure backups
2. Download backup for that date
3. Restore to separate database
4. Extract required data
5. Import to production

## Security

### Encryption
- **At Rest**: Azure Storage encryption enabled
- **In Transit**: HTTPS for Azure uploads
- **Backup Files**: Encrypted with GPG (optional)

### Access Control
- **Local Backups**: Root-only access (700 permissions)
- **Azure Storage**: Service principal with minimal permissions
- **Database Credentials**: Stored in environment variables

### Audit Trail
- All backup operations logged
- Upload success/failure tracked
- Access to backups audited

## Cost Optimization

### Azure Storage Tiers
- **Hot**: Recent backups (0-30 days) - Fast access
- **Cool**: Older backups (30-365 days) - Lower cost
- **Archive**: Ancient backups (>365 days) - Lowest cost

### Estimated Costs (per month)
- Storage: $5-10 (100GB compressed)
- Transactions: $1-2 (daily uploads)
- Egress: $0 (minimal downloads)
- **Total**: ~$10-15/month for unlimited retention

## Monitoring & Alerts

### Metrics Tracked
- Last successful backup timestamp
- Backup file size trend
- Upload success rate
- Disk space utilization
- Azure storage usage

### Alerts
- Backup failure (immediate)
- Backup >24 hours old (warning)
- Disk space <10GB (critical)
- Azure upload failure (immediate)

## Testing Plan

### Backup Testing
1. **Weekly**: Verify backup files exist and are non-zero
2. **Monthly**: Test restore to staging database
3. **Quarterly**: Full disaster recovery drill

### Validation
- Automated: Checksum validation on every backup
- Manual: Monthly restore test with data verification

## Future Enhancements

1. **Incremental Backups**: Use WAL archiving for point-in-time recovery
2. **Multi-region**: Replicate backups to multiple Azure regions
3. **Automated Testing**: Daily backup restore to test database
4. **Data Lake Integration**: Export old data to data lake for analytics
5. **Blockchain Verification**: Immutable audit trail of backups

## Configuration Files

### Environment Variables
```bash
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5440
POSTGRES_DB=esp_telemetry
POSTGRES_USER=esp_user
POSTGRES_PASSWORD=***

# Azure Storage
AZURE_STORAGE_ACCOUNT=alkhorayefbackups
AZURE_STORAGE_CONTAINER=timescaledb-backups
AZURE_STORAGE_KEY=***

# Backup Settings
BACKUP_LOCAL_PATH=/var/backups/timescaledb
BACKUP_RETENTION_DAYS=30
BACKUP_COMPRESSION_LEVEL=6
```

### Systemd Timer
```ini
[Unit]
Description=TimescaleDB Daily Backup
Requires=timescaledb-backup.service

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

## Success Criteria

- ✅ All backups automated (no manual intervention)
- ✅ No data loss during retention cleanup
- ✅ Restore time <30 minutes for local backups
- ✅ All historical data preserved in Azure
- ✅ Monitoring and alerts operational
- ✅ Tested disaster recovery procedures
- ✅ Cost <$15/month
- ✅ Zero manual maintenance required

---

**Status**: Design Complete - Ready for Implementation
**Date**: November 20, 2025
**Version**: 1.0
