#!/usr/bin/env python3
"""
Azure VM Autonomous Monitoring Agent
24/7 READ-ONLY monitoring from iac1
"""

import json
import subprocess
import time
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/home/wil/azure_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AzureAgent:
    def __init__(self):
        self.monitor_path = "/home/wil/mcp-servers/azure-vm-monitor"
        self.alert_path = "/home/wil/mcp-servers/azure-alert"
        
        # Alert thresholds
        self.thresholds = {
            "disk_warning": 85,     # % disk usage
            "disk_critical": 90,
            "memory_warning": 85,   # % memory usage
            "backup_age_warning": 36  # hours since last backup
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
                    # Extract: /dev/root  124G  58G  66G  47% /
                    parts = line.split()
                    for part in parts:
                        if "%" in part:
                            data["disk_percent"] = int(part.replace("%", ""))
                            break
                
                elif "Memory:" in line and "Gi" in line:
                    # Extract: Mem: 15Gi 8.3Gi ...
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
        """Main monitoring logic - READ ONLY"""
        try:
            # Get health data (READ-ONLY SSH check)
            health_text = self.check_health()
            if not health_text:
                return
            
            data = self.parse_health_data(health_text)
            
            # Check disk usage
            disk = data["disk_percent"]
            if disk >= self.thresholds["disk_critical"]:
                if self.should_alert("disk_critical"):
                    self.send_alert(
                        title=f"Disk Usage Critical: {disk}%",
                        severity="critical",
                        details=f"Disk usage is at {disk}%, exceeding critical threshold of {self.thresholds['disk_critical']}%\n\nImmediate action required!",
                        metrics=health_text
                    )
            elif disk >= self.thresholds["disk_warning"]:
                if self.should_alert("disk_warning"):
                    self.send_alert(
                        title=f"Disk Usage Warning: {disk}%",
                        severity="warning",
                        details=f"Disk usage is at {disk}%, exceeding warning threshold of {self.thresholds['disk_warning']}%",
                        metrics=health_text
                    )
            
            # Check services
            for service, status in data["services"].items():
                if not status:
                    alert_key = f"service_down_{service}"
                    if self.should_alert(alert_key):
                        self.send_alert(
                            title=f"Service Down: {service}",
                            severity="critical",
                            details=f"{service} service is not active!\n\nThis is a READ-ONLY monitor - manual intervention required.",
                            metrics=health_text
                        )
            
            # Log successful check
            logger.info(f"Monitor cycle complete - Disk: {disk}%, Memory: {data['memory_percent']}%, Services: {len([s for s in data['services'].values() if s])}/{len(data['services'])} active")
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")
    
    def send_daily_report(self):
        """Send daily health report"""
        try:
            logger.info("Generating daily health report...")
            
            # Get full report (READ-ONLY)
            response = self.call_mcp("monitor", "tools/call", {
                "name": "full_report",
                "arguments": {}
            })
            
            if response and "content" in response:
                report_text = response["content"][0]["text"]
                
                # Send report
                self.call_mcp("alert", "tools/call", {
                    "name": "send_health_report",
                    "arguments": {"report_data": report_text}
                })
                
                logger.info("Daily report sent")
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
    
    def run(self):
        """Main agent loop"""
        logger.info("="*70)
        logger.info("Azure VM Autonomous Agent Starting")
        logger.info("Mode: READ-ONLY monitoring from iac1")
        logger.info("Target: Azure VM (100.107.50.52 - azure-vm-thingsboard via Tailscale)")
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
    agent = AzureAgent()
    agent.run()
