#!/usr/bin/env python3
"""
Azure VM Autonomous Monitoring Agent - Enhanced
24/7 READ-ONLY monitoring from iac1 + Sync Status Tracking
"""

import json
import subprocess
import time
import logging
import os
import glob
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/wil/azure_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AzureAgentEnhanced:
    def __init__(self):
        self.monitor_path = "/home/wil/mcp-servers/active/azure-vm-monitor"
        self.alert_path = "/home/wil/mcp-servers/active/azure-alert"

        # Alert thresholds
        self.thresholds = {
            "disk_warning": 85,     # % disk usage
            "disk_critical": 90,
            "memory_warning": 85,   # % memory usage
            "backup_age_warning": 36,  # hours since last backup
            "sync_age_warning": 60,  # minutes since last sync
            "gap_critical": 10000000  # 10M records gap is critical
        }

        self.check_interval = 300  # 5 minutes
        self.last_alert = {}  # Track last alert time to avoid spam

    def call_mcp(self, server, method, params={}):
        """Call MCP server"""
        try:
            request = json.dumps({"method": method, "params": params})
            server_path = self.monitor_path if server == "monitor" else self.alert_path

            result = subprocess.run(
                [f"{server_path}/venv/bin/python", f"{server_path}/server.py"],
                input=request + "\n",
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                logger.error(f"MCP call failed: {result.stderr}")
                return None

            return json.loads(result.stdout.strip())
        except Exception as e:
            logger.error(f"Error calling MCP: {e}")
            return None

    def check_sync_status(self):
        """Check backup sync status"""
        sync_status = {
            "last_sync_time": None,
            "last_sync_age_minutes": None,
            "gap_september": 0,
            "gap_october": 0,
            "total_gap": 0,
            "sync_running": False,
            "last_error": None,
            "records_synced_today": 0
        }

        try:
            # Check if sync is currently running
            ps_result = subprocess.run(
                ["pgrep", "-f", "azure_complete_sync.sh"],
                capture_output=True,
                text=True
            )
            sync_status["sync_running"] = ps_result.returncode == 0

            # Get latest log file
            log_pattern = "/mnt/insa-storage/azure_backups/logs/*sync*.log"
            log_files = glob.glob(log_pattern)

            if log_files:
                latest_log = max(log_files, key=os.path.getmtime)

                # Check last sync time
                mtime = os.path.getmtime(latest_log)
                last_sync = datetime.fromtimestamp(mtime)
                sync_status["last_sync_time"] = last_sync.isoformat()
                sync_status["last_sync_age_minutes"] = int((datetime.now() - last_sync).total_seconds() / 60)

                # Check for errors in log
                with open(latest_log, 'r') as f:
                    log_content = f.read()
                    if "ERROR" in log_content:
                        errors = [line for line in log_content.split('\n') if "ERROR" in line]
                        sync_status["last_error"] = errors[-1] if errors else None

            # Get current database gaps
            # September partition gap
            local_sept = subprocess.run(
                ["sudo", "-u", "postgres", "psql", "-d", "thingsboard", "-t", "-c",
                 "SELECT COUNT(*) FROM ts_kv_2025_09;"],
                capture_output=True,
                text=True
            )

            if local_sept.returncode == 0:
                local_sept_count = int(local_sept.stdout.strip())

                # Get Azure count (hardcoded for now to avoid SSH overhead every 5 min)
                # Will update during daily report
                azure_sept_count = 85961281  # Update this in daily report
                sync_status["gap_september"] = max(0, azure_sept_count - local_sept_count)

            # October partition gap
            local_oct = subprocess.run(
                ["sudo", "-u", "postgres", "psql", "-d", "thingsboard", "-t", "-c",
                 "SELECT COUNT(*) FROM ts_kv_2025_10;"],
                capture_output=True,
                text=True
            )

            if local_oct.returncode == 0:
                local_oct_count = int(local_oct.stdout.strip())

                # Get Azure count
                azure_oct_count = 57142721  # Update this in daily report
                sync_status["gap_october"] = max(0, azure_oct_count - local_oct_count)

            sync_status["total_gap"] = sync_status["gap_september"] + sync_status["gap_october"]

            # Get records synced today
            today_logs = glob.glob(f"/mnt/insa-storage/azure_backups/logs/turbo_cron.log") + glob.glob(f"/mnt/insa-storage/azure_backups/logs/complete_sync_{datetime.now().strftime('%Y%m%d')}.log")
            if today_logs:
                with open(today_logs[0], 'r') as f:
                    content = f.read()
                    # Count "Imported" messages
                    import_lines = [line for line in content.split('\n') if "Imported" in line and "new records" in line]
                    for line in import_lines:
                        try:
                            # Extract number before "new records"
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if "Imported:" in part or "Imported" in part:
                                    # Next number is the count
                                    for j in range(i+1, len(parts)):
                                        if parts[j].isdigit():
                                            sync_status["records_synced_today"] += int(parts[j])
                                            break
                        except:
                            pass

        except Exception as e:
            logger.error(f"Error checking sync status: {e}")
            sync_status["last_error"] = str(e)

        return sync_status

    def check_health(self):
        """Perform health check (READ-ONLY)"""
        logger.info("Running READ-ONLY health check on Azure VM...")

        response = self.call_mcp("monitor", "tools/call", {
            "name": "check_health",
            "arguments": {}
        })

        if not response or "content" not in response:
            logger.error("Health check failed - no response")
            return None

        health_text = response["content"][0]["text"]
        logger.info("Health check complete")
        return health_text

    def parse_health_data(self, health_text):
        """Parse health check output for monitoring"""
        data = {
            "disk_percent": 0,
            "memory_percent": 0,
            "services": {},
            "uptime": ""
        }

        try:
            lines = health_text.split("\n")
            for line in lines:
                if "Disk:" in line and "%" in line:
                    parts = line.split()
                    for part in parts:
                        if "%" in part:
                            data["disk_percent"] = int(part.replace("%", ""))
                            break

                elif "Memory:" in line and "Gi" in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        total = float(parts[2].replace("Gi", ""))
                        used = float(parts[3].replace("Gi", ""))
                        if total > 0:
                            data["memory_percent"] = int((used / total) * 100)

                elif "ThingsBoard:" in line:
                    data["services"]["thingsboard"] = "active" in line.lower()
                elif "PostgreSQL:" in line:
                    data["services"]["postgresql"] = "active" in line.lower()
                elif "Syncthing:" in line:
                    data["services"]["syncthing"] = "active" in line.lower()
                elif "Uptime:" in line:
                    data["uptime"] = line.replace("Uptime:", "").strip()

        except Exception as e:
            logger.error(f"Error parsing health data: {e}")

        return data

    def should_alert(self, alert_key):
        """Check if we should send alert (avoid spam)"""
        now = time.time()
        last_time = self.last_alert.get(alert_key, 0)

        # Don't send same alert more than once per hour
        if now - last_time < 3600:
            return False

        self.last_alert[alert_key] = now
        return True

    def send_alert(self, title, severity, details, metrics=""):
        """Send email alert"""
        logger.info(f"Sending {severity} alert: {title}")

        response = self.call_mcp("alert", "tools/call", {
            "name": "send_alert",
            "arguments": {
                "title": title,
                "severity": severity,
                "details": details,
                "metrics": metrics
            }
        })

        if response and "content" in response:
            logger.info(f"Alert sent: {response['content'][0]['text']}")
        else:
            logger.error("Failed to send alert")

    def check_and_alert(self):
        """Main monitoring logic - READ ONLY + Sync Monitoring"""
        try:
            # Get Azure VM health data (READ-ONLY SSH check)
            health_text = self.check_health()
            if health_text:
                data = self.parse_health_data(health_text)

                # Check disk usage
                disk = data["disk_percent"]
                if disk >= self.thresholds["disk_critical"]:
                    if self.should_alert("disk_critical"):
                        self.send_alert(
                            title=f"Azure VM Disk Critical: {disk}%",
                            severity="critical",
                            details=f"Disk usage is at {disk}%, exceeding critical threshold!\n\nImmediate action required.",
                            metrics=health_text
                        )
                elif disk >= self.thresholds["disk_warning"]:
                    if self.should_alert("disk_warning"):
                        self.send_alert(
                            title=f"Azure VM Disk Warning: {disk}%",
                            severity="warning",
                            details=f"Disk usage is at {disk}%, exceeding warning threshold.",
                            metrics=health_text
                        )

                # Check services
                for service, status in data["services"].items():
                    if not status:
                        alert_key = f"service_down_{service}"
                        if self.should_alert(alert_key):
                            self.send_alert(
                                title=f"Azure VM Service Down: {service}",
                                severity="critical",
                                details=f"{service} service is not active!\n\nManual intervention required.",
                                metrics=health_text
                            )

            # Check sync status
            sync_status = self.check_sync_status()

            # Alert if sync hasn't run recently (only if not currently running)
            if not sync_status["sync_running"] and sync_status["last_sync_age_minutes"]:
                if sync_status["last_sync_age_minutes"] > self.thresholds["sync_age_warning"]:
                    if self.should_alert("sync_stale"):
                        self.send_alert(
                            title=f"Backup Sync Overdue",
                            severity="warning",
                            details=f"Last sync was {sync_status['last_sync_age_minutes']} minutes ago.\n\nExpected to run every 30 minutes.",
                            metrics=json.dumps(sync_status, indent=2)
                        )

            # Alert if gap is too large
            if sync_status["total_gap"] > self.thresholds["gap_critical"]:
                if self.should_alert("gap_critical"):
                    self.send_alert(
                        title=f"Backup Gap Critical: {sync_status['total_gap']:,} records",
                        severity="warning",
                        details=f"Database backup gap is {sync_status['total_gap']:,} records.\n\nSeptember: {sync_status['gap_september']:,}\nOctober: {sync_status['gap_october']:,}",
                        metrics=json.dumps(sync_status, indent=2)
                    )

            # Alert on sync errors
            if sync_status["last_error"]:
                if self.should_alert("sync_error"):
                    self.send_alert(
                        title="Backup Sync Error Detected",
                        severity="warning",
                        details=f"Error found in sync logs:\n\n{sync_status['last_error']}",
                        metrics=json.dumps(sync_status, indent=2)
                    )

            # Log successful check
            sync_info = f"Gap: {sync_status['total_gap']:,}, Synced today: {sync_status['records_synced_today']:,}"
            if health_text:
                logger.info(f"Monitor cycle - Azure VM: Disk {data['disk_percent']}%, Memory {data['memory_percent']}%, Services {len([s for s in data['services'].values() if s])}/{len(data['services'])} | Sync: {sync_info}")
            else:
                logger.info(f"Monitor cycle - Sync: {sync_info}")

        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")

    def send_daily_report(self):
        """Send daily health + sync report"""
        try:
            logger.info("Generating daily health + sync report...")

            # Get Azure VM report
            vm_report = "Azure VM Status: Unable to fetch"
            response = self.call_mcp("monitor", "tools/call", {
                "name": "full_report",
                "arguments": {}
            })

            if response and "content" in response:
                vm_report = response["content"][0]["text"]

            # Get sync status
            sync_status = self.check_sync_status()

            # Format sync report
            sync_report = f"""
BACKUP SYNC STATUS:
------------------
Last Sync: {sync_status['last_sync_time'] or 'Never'}
Sync Age: {sync_status['last_sync_age_minutes'] or 'N/A'} minutes
Currently Running: {'YES' if sync_status['sync_running'] else 'NO'}

Database Gaps:
- September 2025: {sync_status['gap_september']:,} records
- October 2025: {sync_status['gap_october']:,} records
- TOTAL GAP: {sync_status['total_gap']:,} records

Progress Today:
- Records Synced: {sync_status['records_synced_today']:,}

Status: {'ERROR - ' + sync_status['last_error'] if sync_status['last_error'] else 'OK'}
"""

            # Combine reports
            full_report = f"{vm_report}\n\n{'='*70}\n{sync_report}"

            # Send combined report
            self.call_mcp("alert", "tools/call", {
                "name": "send_health_report",
                "arguments": {"report_data": full_report}
            })

            logger.info("Daily report sent")
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")

    def run(self):
        """Main agent loop"""
        logger.info("="*70)
        logger.info("Azure VM Autonomous Agent - Enhanced (with Sync Monitoring)")
        logger.info("Mode: READ-ONLY monitoring + Backup Sync Tracking")
        logger.info("Target: Azure VM 172.208.66.188 + iac1 Sync Status")
        logger.info("Check interval: 5 minutes")
        logger.info("="*70)

        last_daily_report = datetime.now().date()

        while True:
            try:
                # Run health check and alerts
                self.check_and_alert()

                # Send daily report at 8 AM
                now = datetime.now()
                if now.date() > last_daily_report and now.hour >= 8:
                    self.send_daily_report()
                    last_daily_report = now.date()

                # Sleep until next check
                logger.info(f"Sleeping for {self.check_interval} seconds...")
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                logger.info("Agent stopped by user")
                break
            except Exception as e:
                logger.error(f"Unexpected error in main loop: {e}")
                time.sleep(60)  # Wait 1 min before retrying

if __name__ == "__main__":
    agent = AzureAgentEnhanced()
    agent.run()
