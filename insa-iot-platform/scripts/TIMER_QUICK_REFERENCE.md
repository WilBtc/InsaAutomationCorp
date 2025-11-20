# TimescaleDB Backup Timer - Quick Reference

## Installation

```bash
sudo /home/wil/insa-iot-platform/scripts/install_backup_timer.sh
```

## Common Commands

### View Timer Status
```bash
systemctl status timescaledb-backup.timer
```

### View Next Scheduled Run
```bash
systemctl list-timers timescaledb-backup.timer
```

### Run Manual Backup
```bash
sudo systemctl start timescaledb-backup.service
```

### View Backup Logs (Real-time)
```bash
journalctl -u timescaledb-backup -f
```

### View Recent Logs
```bash
journalctl -u timescaledb-backup -n 100
```

### View Logs for Specific Date
```bash
journalctl -u timescaledb-backup --since "2025-11-19" --until "2025-11-20"
```

### Check Backup Files
```bash
ls -lh /home/wil/insa-iot-platform/backups/
```

### View Backup Metrics
```bash
cat /home/wil/insa-iot-platform/backups/backup_metrics.txt
```

## Management

### Stop Timer
```bash
sudo systemctl stop timescaledb-backup.timer
```

### Start Timer
```bash
sudo systemctl start timescaledb-backup.timer
```

### Disable Timer (no auto-start on boot)
```bash
sudo systemctl disable timescaledb-backup.timer
```

### Enable Timer (auto-start on boot)
```bash
sudo systemctl enable timescaledb-backup.timer
```

### Restart Timer (after config changes)
```bash
sudo systemctl daemon-reload
sudo systemctl restart timescaledb-backup.timer
```

## Troubleshooting

### Check Service Status
```bash
systemctl status timescaledb-backup.service
```

### View Detailed Backup Log
```bash
cat /home/wil/insa-iot-platform/backups/backup.log | tail -n 100
```

### Test Backup Manually
```bash
/home/wil/insa-iot-platform/scripts/backup_timescaledb.sh
```

### Verify Container Running
```bash
docker ps | grep timescaledb
```

### Check Disk Space
```bash
df -h /home/wil/insa-iot-platform/backups
```

## Configuration Files

- **Service**: `/etc/systemd/system/timescaledb-backup.service`
- **Timer**: `/etc/systemd/system/timescaledb-backup.timer`
- **Backup Script**: `/home/wil/insa-iot-platform/scripts/backup_timescaledb.sh`
- **Environment**: `/home/wil/insa-iot-platform/.env`

## Backup Schedule

Default: Daily at 2:00 AM UTC

To change, edit `/etc/systemd/system/timescaledb-backup.timer`:
```ini
OnCalendar=*-*-* 02:00:00  # Daily at 2 AM
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart timescaledb-backup.timer
```

## Full Documentation

See: `/home/wil/insa-iot-platform/docs/BACKUP_AUTOMATION.md`
