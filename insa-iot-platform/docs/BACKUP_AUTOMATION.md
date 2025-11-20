# TimescaleDB Backup Automation

This document describes the automated backup system for TimescaleDB using systemd timers.

## Overview

The backup system performs daily automated backups of the TimescaleDB database with:

- **Scheduled Execution**: Daily at 2 AM (configurable)
- **Local Storage**: Compressed backups in `/home/wil/insa-iot-platform/backups/`
- **Retention Policy**: 30-day local retention (configurable)
- **Azure Integration**: Optional upload to Azure Blob Storage
- **Monitoring**: Systemd journal logging and metrics
- **Reliability**: Automatic catch-up if server was down during scheduled time

## Architecture

```
┌─────────────────────────────────────────┐
│  timescaledb-backup.timer               │
│  Runs daily at 2 AM                     │
└─────────────────┬───────────────────────┘
                  │ triggers
                  ▼
┌─────────────────────────────────────────┐
│  timescaledb-backup.service             │
│  Executes backup script as user 'wil'  │
└─────────────────┬───────────────────────┘
                  │ runs
                  ▼
┌─────────────────────────────────────────┐
│  backup_timescaledb.sh                  │
│  - Dumps database                       │
│  - Compresses backup                    │
│  - Verifies integrity                   │
│  - Uploads to Azure (optional)          │
│  - Cleans old backups                   │
│  - Records metrics                      │
└─────────────────────────────────────────┘
```

## Installation

### Prerequisites

1. **TimescaleDB running in Docker**:
   ```bash
   docker ps | grep timescaledb
   ```

2. **Backup script executable**:
   ```bash
   chmod +x /home/wil/insa-iot-platform/scripts/backup_timescaledb.sh
   ```

3. **Environment configured**:
   Ensure `.env` file exists with database credentials:
   ```
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5440
   POSTGRES_DB=esp_telemetry
   POSTGRES_USER=esp_user
   POSTGRES_PASSWORD=your_password
   TIMESCALEDB_CONTAINER=alkhorayef-timescaledb
   ```

### Install Timer

Run the installation script with sudo:

```bash
cd /home/wil/insa-iot-platform
sudo ./scripts/install_backup_timer.sh
```

This will:
1. Copy service and timer files to `/etc/systemd/system/`
2. Reload systemd daemon
3. Enable timer to start on boot
4. Start the timer immediately
5. Display status and next scheduled run

### Verify Installation

Check that the timer is active:

```bash
systemctl status timescaledb-backup.timer
```

Expected output:
```
● timescaledb-backup.timer - Daily TimescaleDB Backup Timer
     Loaded: loaded (/etc/systemd/system/timescaledb-backup.timer; enabled)
     Active: active (waiting) since ...
```

View next scheduled runs:

```bash
systemctl list-timers timescaledb-backup.timer
```

## Usage

### Manual Backup

To run a backup manually (without waiting for the scheduled time):

```bash
sudo systemctl start timescaledb-backup.service
```

Monitor the backup in real-time:

```bash
journalctl -u timescaledb-backup -f
```

### View Logs

View recent backup logs:

```bash
journalctl -u timescaledb-backup -n 100
```

View logs for a specific date:

```bash
journalctl -u timescaledb-backup --since "2025-11-19" --until "2025-11-20"
```

View logs from the last backup run:

```bash
journalctl -u timescaledb-backup --since today
```

Detailed backup log file:

```bash
cat /home/wil/insa-iot-platform/backups/backup.log
```

### Check Backup Files

List all backups:

```bash
ls -lh /home/wil/insa-iot-platform/backups/
```

Check backup metrics:

```bash
cat /home/wil/insa-iot-platform/backups/backup_metrics.txt
```

Verify backup integrity:

```bash
# Check gzip integrity
gzip -t /home/wil/insa-iot-platform/backups/timescaledb_backup_*.sql.gz

# Verify checksum
cd /home/wil/insa-iot-platform/backups
md5sum -c timescaledb_backup_*.sql.gz.md5
```

### Timer Management

**Stop the timer** (keeps it enabled for next boot):

```bash
sudo systemctl stop timescaledb-backup.timer
```

**Start the timer**:

```bash
sudo systemctl start timescaledb-backup.timer
```

**Disable the timer** (prevents automatic start on boot):

```bash
sudo systemctl disable timescaledb-backup.timer
```

**Enable the timer** (start on boot):

```bash
sudo systemctl enable timescaledb-backup.timer
```

**Restart the timer** (apply configuration changes):

```bash
sudo systemctl restart timescaledb-backup.timer
```

## Configuration

### Backup Schedule

Edit `/etc/systemd/system/timescaledb-backup.timer`:

```ini
[Timer]
# Run daily at 2 AM
OnCalendar=*-*-* 02:00:00
```

Common schedule examples:

- **Daily at 3 AM**: `OnCalendar=*-*-* 03:00:00`
- **Twice daily** (6 AM and 6 PM): `OnCalendar=*-*-* 06,18:00:00`
- **Every 12 hours**: `OnCalendar=*-*-* 00/12:00:00`
- **Weekly on Sunday at 1 AM**: `OnCalendar=Sun *-*-* 01:00:00`
- **First day of month**: `OnCalendar=*-*-01 02:00:00`

After editing, reload systemd:

```bash
sudo systemctl daemon-reload
sudo systemctl restart timescaledb-backup.timer
```

### Backup Retention

Edit `/etc/systemd/system/timescaledb-backup.service`:

```ini
[Service]
Environment="BACKUP_RETENTION_DAYS=30"  # Change to desired retention period
```

Then reload:

```bash
sudo systemctl daemon-reload
```

### Backup Location

To change the backup directory, edit the service file:

```ini
[Service]
Environment="BACKUP_LOCAL_PATH=/your/custom/path"
```

Ensure the directory exists and has proper permissions:

```bash
sudo mkdir -p /your/custom/path
sudo chown wil:wil /your/custom/path
sudo chmod 755 /your/custom/path
```

### Azure Storage (Optional)

To enable Azure Blob Storage uploads, add to `.env`:

```bash
AZURE_STORAGE_ACCOUNT=your_storage_account
AZURE_STORAGE_CONTAINER=timescaledb-backups
AZURE_STORAGE_KEY=your_storage_key  # Optional if using az login
```

Install Azure CLI if not already installed:

```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

Authenticate:

```bash
az login
```

## Monitoring

### Check Timer Status

```bash
# Is the timer running?
systemctl is-active timescaledb-backup.timer

# Is the timer enabled?
systemctl is-enabled timescaledb-backup.timer

# Full status
systemctl status timescaledb-backup.timer
```

### Monitor Backup Success

Check if the last backup was successful:

```bash
systemctl status timescaledb-backup.service
```

Look for `Active: inactive (dead)` with exit code 0 (success).

### Automated Monitoring

The backup script creates metrics in `/home/wil/insa-iot-platform/backups/backup_metrics.txt`:

```bash
last_backup_timestamp=1732137809
last_backup_size=118413
last_backup_success=1
backup_duration_seconds=45
```

You can monitor these metrics with:

- **Prometheus**: Scrape the metrics file with node_exporter textfile collector
- **Grafana**: Create dashboard showing backup status, size, and duration
- **Nagios/Zabbix**: Check timestamp age and success flag

### Email Notifications (Optional)

To receive email notifications on backup failure, configure systemd to send mail:

1. Install mail utilities:
   ```bash
   sudo apt install mailutils
   ```

2. Configure systemd to send mail on failure:
   ```bash
   sudo systemctl edit timescaledb-backup.service
   ```

3. Add:
   ```ini
   [Service]
   OnFailure=status-email@%n.service
   ```

## Troubleshooting

### Timer Not Running

**Symptom**: Timer shows as inactive or dead

**Solution**:
```bash
# Check timer status
sudo systemctl status timescaledb-backup.timer

# Check for errors
journalctl -u timescaledb-backup.timer -n 50

# Restart timer
sudo systemctl restart timescaledb-backup.timer
```

### Backup Fails

**Symptom**: Service shows as failed in logs

**Solution**:
```bash
# View detailed logs
journalctl -u timescaledb-backup -n 100

# Common issues:

# 1. Container not running
docker ps | grep timescaledb
docker start alkhorayef-timescaledb

# 2. Database not ready
docker exec alkhorayef-timescaledb pg_isready

# 3. Insufficient disk space
df -h /home/wil/insa-iot-platform/backups

# 4. Permission issues
ls -ld /home/wil/insa-iot-platform/backups
sudo chown -R wil:wil /home/wil/insa-iot-platform/backups

# 5. Test manually
sudo -u wil /home/wil/insa-iot-platform/scripts/backup_timescaledb.sh
```

### Timer Missed Execution

**Symptom**: Timer missed a scheduled run (server was down)

**Solution**: The timer has `Persistent=true`, which means it will run automatically when the system boots up if a scheduled run was missed.

Check if it caught up:
```bash
journalctl -u timescaledb-backup --since "1 week ago"
```

### Backup Files Too Large

**Symptom**: Backup files consuming too much disk space

**Solution**:

1. **Increase compression**:
   ```ini
   Environment="BACKUP_COMPRESSION_LEVEL=9"  # Maximum compression
   ```

2. **Reduce retention**:
   ```ini
   Environment="BACKUP_RETENTION_DAYS=7"  # Keep only 7 days
   ```

3. **Clean old backups manually**:
   ```bash
   find /home/wil/insa-iot-platform/backups -name "*.sql.gz" -mtime +30 -delete
   ```

### Azure Upload Fails

**Symptom**: Backup succeeds but Azure upload fails

**Solution**:
```bash
# Check Azure CLI installation
az --version

# Re-authenticate
az login

# Test upload manually
az storage blob upload \
    --account-name YOUR_ACCOUNT \
    --container-name timescaledb-backups \
    --name test.txt \
    --file /tmp/test.txt

# Check service logs
journalctl -u timescaledb-backup | grep -i azure
```

### Backup Verification Fails

**Symptom**: "Backup file is corrupted" error

**Solution**:
```bash
# Test gzip manually
gzip -t /home/wil/insa-iot-platform/backups/timescaledb_backup_*.sql.gz

# Check file size
ls -lh /home/wil/insa-iot-platform/backups/

# If corrupt, remove and run new backup
rm /home/wil/insa-iot-platform/backups/timescaledb_backup_*.sql.gz
sudo systemctl start timescaledb-backup.service
```

## Restoration

To restore from a backup, use the restoration script:

```bash
# List available backups
ls -lh /home/wil/insa-iot-platform/backups/

# Restore from specific backup
sudo -u wil /home/wil/insa-iot-platform/scripts/restore_timescaledb.sh \
    /home/wil/insa-iot-platform/backups/timescaledb_backup_20251120_164329.sql.gz
```

For more details, see the restoration script documentation.

## Security Considerations

### File Permissions

The systemd service is configured with security hardening:

- `NoNewPrivileges=true`: Prevents privilege escalation
- `PrivateTmp=true`: Uses private /tmp directory
- `ProtectSystem=strict`: Read-only filesystem except allowed paths
- `ProtectHome=read-only`: Read-only home directory except backup location
- `ReadWritePaths=/home/wil/insa-iot-platform/backups`: Only backup directory is writable

### Credentials

Database credentials are stored in:
- `.env` file (should be in .gitignore)
- Environment variables passed to service

**Never commit credentials to version control!**

### Backup File Security

Backup files contain sensitive data. Ensure:

1. **Restricted permissions**:
   ```bash
   chmod 600 /home/wil/insa-iot-platform/backups/*.sql.gz
   ```

2. **Encrypted storage**: Consider encrypting backups at rest
   ```bash
   gpg --encrypt timescaledb_backup_*.sql.gz
   ```

3. **Azure encryption**: Azure Blob Storage encrypts data by default

## Performance Tuning

### Resource Limits

The service has default resource limits:

```ini
TimeoutStartSec=30min    # Maximum backup duration
CPUQuota=50%            # Use max 50% of one CPU core
MemoryLimit=2G          # Maximum 2GB RAM
```

Adjust in `/etc/systemd/system/timescaledb-backup.service` if needed.

### Compression Level

Balance between backup size and CPU usage:

- **Level 1**: Fastest, largest files
- **Level 6**: Default, good balance
- **Level 9**: Slowest, smallest files

```ini
Environment="BACKUP_COMPRESSION_LEVEL=6"
```

### Concurrent Operations

If running multiple database operations, schedule backups during low-traffic periods:

```ini
OnCalendar=*-*-* 02:00:00  # 2 AM when traffic is lowest
```

## Integration with Monitoring

### Prometheus Integration

Export metrics using node_exporter:

1. Install node_exporter textfile collector
2. Symlink metrics file:
   ```bash
   ln -s /home/wil/insa-iot-platform/backups/backup_metrics.txt \
         /var/lib/node_exporter/textfile_collector/timescaledb_backup.prom
   ```

### Grafana Dashboard

Create alerts for:
- Backup age > 25 hours (missed backup)
- Last backup failed
- Backup size anomalies
- Backup duration increasing

### Log Aggregation

Forward systemd journal to log aggregation:

```bash
# Example: Forward to rsyslog
journalctl -u timescaledb-backup -f | logger -t timescaledb-backup
```

## Uninstallation

To remove the backup automation:

```bash
# Stop and disable timer
sudo systemctl stop timescaledb-backup.timer
sudo systemctl disable timescaledb-backup.timer

# Remove systemd files
sudo rm /etc/systemd/system/timescaledb-backup.service
sudo rm /etc/systemd/system/timescaledb-backup.timer

# Reload systemd
sudo systemctl daemon-reload

# Optionally remove backup files
# rm -rf /home/wil/insa-iot-platform/backups/*
```

## References

- [systemd.timer documentation](https://www.freedesktop.org/software/systemd/man/systemd.timer.html)
- [systemd.service documentation](https://www.freedesktop.org/software/systemd/man/systemd.service.html)
- [TimescaleDB backup best practices](https://docs.timescale.com/self-hosted/latest/backup-and-restore/)
- [PostgreSQL pg_dump documentation](https://www.postgresql.org/docs/current/app-pgdump.html)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review systemd journal logs
3. Examine `/home/wil/insa-iot-platform/backups/backup.log`
4. Test the backup script manually
5. Contact the platform administrator

---

**Last Updated**: 2025-11-20
**Version**: 1.0.0
**Maintainer**: Platform Operations Team
