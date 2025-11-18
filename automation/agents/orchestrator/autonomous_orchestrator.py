#!/usr/bin/env python3
"""
Autonomous Task Orchestrator
Closed-loop system: Bug Detection → GitHub Issue → Auto-Fix → Update Issue → Close Issue

UPGRADED: Parallel execution with ThreadPoolExecutor (October 29, 2025)
- Multi-threaded task processing (4 workers)
- 4x faster cycle execution
- Thread-safe database operations
- Per-task timeout handling (5 minutes)
- Isolated error handling

Created: October 26, 2025
Author: Insa Automation Corp
Purpose: Self-healing infrastructure with automated task tracking
"""

import os
import sys
import json
import time
import sqlite3
import subprocess
import requests
import smtplib
import threading
import concurrent.futures
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# Add parent directory to path
sys.path.insert(0, '/home/wil/mcp-servers/bug-hunter')
sys.path.insert(0, '/home/wil/mcp-servers/github-agent')
sys.path.insert(0, '/home/wil/autonomous-task-orchestrator')

# Import intelligent fixer module
from intelligent_fixer import IntelligentAutoFixer, LearningDatabase, ResearchAgent

# Import new multi-agent system
from agent_coordinator import AgentCoordinator

class GitHubIntegration:
    """GitHub API integration for issue management"""

    def __init__(self, config_path: str = "/home/wil/mcp-servers/active/github-agent/config.json"):
        with open(config_path, 'r') as f:
            config = json.load(f)

        self.token = config['github_token']
        self.owner = config['github_owner']
        self.repo = config['github_repo']
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "INSA-Autonomous-Orchestrator"
        }

    def create_issue(self, title: str, body: str, labels: List[str] = None) -> Optional[Dict]:
        """Create GitHub issue"""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues"
        data = {
            "title": title,
            "body": body,
            "labels": labels or ["automation", "bug-hunter"]
        }

        try:
            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code == 201:
                return response.json()
            else:
                print(f"❌ Failed to create issue: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating issue: {e}")
            return None

    def update_issue(self, issue_number: int, comment: str) -> bool:
        """Add comment to existing issue"""
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues/{issue_number}/comments"
        data = {"body": comment}

        try:
            response = requests.post(url, headers=self.headers, json=data)
            return response.status_code == 201
        except Exception as e:
            print(f"❌ Error updating issue: {e}")
            return False

    def close_issue(self, issue_number: int, comment: str = None) -> bool:
        """Close GitHub issue"""
        if comment:
            self.update_issue(issue_number, comment)

        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues/{issue_number}"
        data = {"state": "closed"}

        try:
            response = requests.patch(url, headers=self.headers, json=data)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Error closing issue: {e}")
            return False

class EmailNotifier:
    """Email notification system for escalations - Updated Nov 15, 2025 for centralized alerts"""

    def __init__(self, to_email: str = "w.aroca@insaing.com", smtp_host: str = "localhost", smtp_port: int = 25):
        self.to_email = to_email
        self.from_email = "autonomous-orchestrator@iac1.local"
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

        # Try to use centralized alert system
        try:
            import sys
            sys.path.insert(0, '/home/wil/automation/agents/shared')
            from centralized_alert_queue import send_alert
            self.send_alert = send_alert
            self.use_centralized = True
            print("✅ Using centralized alert system")
        except ImportError as e:
            self.use_centralized = False
            print(f"⚠️  Centralized alerts not available, using direct email: {e}")

    def send_escalation_email(self, task_id: int, issue_type: str, issue_message: str,
                             github_issue_number: int, github_url: str, fix_attempted: bool) -> bool:
        """Send email notification when issue is escalated to GitHub"""
        try:
            # Use centralized alert system if available
            if self.use_centralized:
                subject = f"Autonomous Orchestrator Alert: Task #{task_id} Escalated"
                message = f"""Autonomous Task Orchestrator Alert - Human Intervention Required

Task ID: #{task_id}
Type: {issue_type}
Auto-fix Attempted: {'Yes ❌ (Failed)' if fix_attempted else 'No (Not fixable automatically)'}
GitHub Issue: #{github_issue_number}

Error Message:
{issue_message[:500]}

Action Required:
This issue requires manual investigation and resolution.

GitHub Issue: {github_url}

---
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
Database: /var/lib/autonomous-orchestrator/tasks.db
Server: iac1 (100.100.101.1)
"""

                self.send_alert(
                    category="service",
                    priority="HIGH",
                    subject=subject,
                    message=message,
                    source="autonomous-orchestrator"
                )

                print(f"✅ Escalation alert queued for Task #{task_id}")
                return True

            # Fallback to direct email (legacy)
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🚨 Autonomous Orchestrator Alert: Task #{task_id} Escalated"
            msg['From'] = self.from_email
            msg['To'] = self.to_email

            # Email body (HTML)
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .header {{ background: #d32f2f; color: white; padding: 20px; border-radius: 5px; }}
                    .content {{ padding: 20px; background: #f5f5f5; margin-top: 10px; border-radius: 5px; }}
                    .info {{ background: white; padding: 15px; margin: 10px 0; border-left: 4px solid #2196F3; }}
                    .github-link {{ display: inline-block; padding: 10px 20px; background: #2196F3;
                                   color: white; text-decoration: none; border-radius: 5px; margin-top: 10px; }}
                    .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd;
                              color: #777; font-size: 12px; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>🚨 Autonomous Task Orchestrator Alert</h2>
                    <p>Human intervention required for Task #{task_id}</p>
                </div>

                <div class="content">
                    <h3>Issue Details</h3>
                    <div class="info">
                        <p><strong>Task ID:</strong> #{task_id}</p>
                        <p><strong>Type:</strong> {issue_type}</p>
                        <p><strong>Auto-fix Attempted:</strong> {'Yes ❌ (Failed)' if fix_attempted else 'No (Not fixable automatically)'}</p>
                        <p><strong>GitHub Issue:</strong> #{github_issue_number}</p>
                    </div>

                    <h3>Error Message</h3>
                    <div class="info">
                        <pre style="white-space: pre-wrap; word-wrap: break-word;">{issue_message[:500]}</pre>
                    </div>

                    <h3>Action Required</h3>
                    <p>This issue requires manual investigation and resolution. Please review the GitHub issue for full details.</p>

                    <a href="{github_url}" class="github-link">View GitHub Issue #{github_issue_number}</a>
                </div>

                <div class="footer">
                    <p>This email was sent by the Autonomous Task Orchestrator running on iac1 (100.100.101.1)</p>
                    <p>Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    <p>Database: /var/lib/autonomous-orchestrator/tasks.db</p>
                </div>
            </body>
            </html>
            """

            # Attach HTML body
            msg.attach(MIMEText(html_body, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.send_message(msg)

            print(f"✅ Email notification sent to {self.to_email}")
            return True

        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False

class BugScanner:
    """Multi-source bug detection"""

    def __init__(self):
        self.error_patterns = [
            'ERROR:', 'CRITICAL:', 'Exception:', 'Traceback',
            'fatal:', 'panic:', 'Failed to', 'Connection refused'
        ]

    def scan_logs(self, hours: int = 1) -> List[Dict]:
        """Scan log files for errors"""
        errors = []
        log_files = [
            '/var/log/syslog',
            '/tmp/crm-backend.log',
            '/tmp/insa-crm.log',
            '/var/log/defectdojo_remediation_agent.log'
        ]

        for log_file in log_files:
            if not os.path.exists(log_file):
                continue

            try:
                # Get recent lines
                cmd = f"tail -1000 {log_file} | grep -i 'error\\|fail\\|critical\\|exception' | tail -10"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)

                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        # CRITICAL FIX (Nov 18, 2025): Filter out benign Docker DNS errors
                        # These DNS resolver errors are transient and don't require AI escalation
                        # Root cause of 771/913 escalations causing OOM (42GB Claude subprocess)
                        if '[resolver] failed to query external DNS server' in line:
                            continue
                        if 'dockerd' in line and 'DNS server' in line:
                            continue

                        if any(pattern.lower() in line.lower() for pattern in self.error_patterns):
                            errors.append({
                                'source': log_file,
                                'message': line[:200],
                                'timestamp': datetime.now().isoformat(),
                                'type': 'log_error'
                            })
            except Exception as e:
                print(f"⚠️  Could not scan {log_file}: {e}")

        return errors

    def check_failed_services(self) -> List[Dict]:
        """
        Check for failed AND inactive systemd services

        FIX (Nov 14, 2025): Added detection of 'inactive' services that should be running
        Previously only detected 'failed' services, missing services like host-config-agent
        that are enabled but not running.
        """
        failures = []

        try:
            # Check for failed services
            result = subprocess.run(
                ['systemctl', 'list-units', '--state=failed', '--no-pager'],
                capture_output=True, text=True, timeout=10
            )

            for line in result.stdout.split('\n'):
                if '●' in line and '.service' in line:
                    service_name = line.split()[1] if len(line.split()) > 1 else 'unknown'
                    failures.append({
                        'source': 'systemd',
                        'message': f'Service {service_name} has failed',
                        'timestamp': datetime.now().isoformat(),
                        'type': 'service_failure',
                        'service': service_name
                    })

            # NEW: Check for enabled but inactive services (should be running but aren't)
            result_enabled = subprocess.run(
                ['systemctl', 'list-unit-files', '--state=enabled', '--type=service', '--no-pager'],
                capture_output=True, text=True, timeout=10
            )

            enabled_services = []
            for line in result_enabled.stdout.split('\n'):
                if '.service' in line and 'enabled' in line:
                    parts = line.split()
                    if len(parts) >= 1:
                        enabled_services.append(parts[0])

            # For each enabled service, check if it's actually running
            for service in enabled_services:
                try:
                    status_result = subprocess.run(
                        ['systemctl', 'is-active', service],
                        capture_output=True, text=True, timeout=5
                    )

                    status = status_result.stdout.strip()

                    # If enabled service is inactive (not running), report it
                    if status == 'inactive':
                        # IGNORE LIST: Services that are SUPPOSED to be inactive (Nov 15, 2025)
                        # These are one-time services, non-daemons, or optional services
                        ignore_services = [
                            'dmesg.service',           # One-time boot service
                            'open-vm-tools.service',   # VMware tools (not running on bare metal)
                            'mcp-tailscale.service',   # Optional MCP server
                            'mcp-docker-local.service',# Optional MCP server
                            'mcp-local.service',       # Optional MCP server
                            'tailscale-devops-mcp.service', # Optional MCP server
                        ]

                        if service in ignore_services:
                            # Skip - this service is intentionally inactive
                            continue

                        # Skip one-shot services and timers (they're supposed to be inactive)
                        type_result = subprocess.run(
                            ['systemctl', 'show', '-p', 'Type', service],
                            capture_output=True, text=True, timeout=5
                        )

                        service_type = type_result.stdout.strip()

                        # Only report if it's a regular service (not oneshot)
                        if 'oneshot' not in service_type:
                            failures.append({
                                'source': 'systemd',
                                'message': f'Service {service} is enabled but inactive (should be running)',
                                'timestamp': datetime.now().isoformat(),
                                'type': 'service_failure',
                                'service': service,
                                'subtype': 'inactive_enabled'
                            })
                except Exception:
                    # Skip services we can't check
                    pass

        except Exception as e:
            print(f"⚠️  Could not check services: {e}")

        return failures

    def check_failed_containers(self) -> List[Dict]:
        """Check for exited Docker containers"""
        failures = []

        try:
            result = subprocess.run(
                ['docker', 'ps', '-a', '--filter', 'status=exited', '--format', '{{.Names}}:{{.Status}}'],
                capture_output=True, text=True, timeout=10
            )

            for line in result.stdout.strip().split('\n'):
                if line and ':' in line:
                    container, status = line.split(':', 1)
                    # Only report recent exits (last 24 hours)
                    if 'hours ago' in status or 'minutes ago' in status or 'seconds ago' in status:
                        failures.append({
                            'source': 'docker',
                            'message': f'Container {container} exited: {status}',
                            'timestamp': datetime.now().isoformat(),
                            'type': 'container_failure',
                            'container': container
                        })
        except Exception as e:
            print(f"⚠️  Could not check containers: {e}")

        return failures

    def check_crash_loops(self) -> List[Dict]:
        """
        Check for containers in crash-loop state (restarting repeatedly)

        ADDED: November 17, 2025
        PURPOSE: Detect crash-looping containers (like anh-grafana, code-server)
        DETECTION: Containers with "Restarting" status
        """
        failures = []

        try:
            # Method 1: Check for "Restarting" status
            result = subprocess.run(
                ['docker', 'ps', '-a', '--filter', 'status=restarting',
                 '--format', '{{.Names}}:{{.Status}}'],
                capture_output=True, text=True, timeout=10
            )

            for line in result.stdout.strip().split('\n'):
                if line and ':' in line:
                    container, status = line.split(':', 1)
                    failures.append({
                        'source': 'docker',
                        'message': f'🔄 CRASH LOOP: Container {container} is restarting repeatedly: {status}',
                        'timestamp': datetime.now().isoformat(),
                        'type': 'container_crash_loop',
                        'container': container,
                        'severity': 'HIGH',
                        'action': 'investigate_logs_and_config'
                    })
                    print(f"   🔄 CRASH LOOP DETECTED: {container} - {status}")

        except Exception as e:
            print(f"⚠️  Could not check for crash loops: {e}")

        return failures

    def check_excessive_restarts(self) -> List[Dict]:
        """
        Check for containers with high restart counts

        ADDED: November 17, 2025
        PURPOSE: Catch containers that restart frequently but may not be in "Restarting" state
        THRESHOLD: >5 restarts = warning, >10 restarts = critical
        """
        failures = []

        try:
            # Get all running containers
            containers_result = subprocess.run(
                ['docker', 'ps', '--format', '{{.Names}}'],
                capture_output=True, text=True, timeout=10
            )

            for container in containers_result.stdout.strip().split('\n'):
                if not container:
                    continue

                try:
                    # Get restart count for this container
                    restart_result = subprocess.run(
                        ['docker', 'inspect', container, '--format', '{{.RestartCount}}'],
                        capture_output=True, text=True, timeout=5
                    )

                    restart_count = restart_result.stdout.strip()

                    try:
                        count = int(restart_count)
                    except ValueError:
                        continue

                    # Alert if restart count is high
                    if count > 10:
                        failures.append({
                            'source': 'docker',
                            'message': f'⚠️  CRITICAL: Container {container} has restarted {count} times',
                            'timestamp': datetime.now().isoformat(),
                            'type': 'excessive_restarts',
                            'container': container,
                            'restart_count': count,
                            'severity': 'CRITICAL',
                            'action': 'investigate_root_cause'
                        })
                        print(f"   ⚠️  CRITICAL RESTARTS: {container} - {count} restarts")

                    elif count > 5:
                        failures.append({
                            'source': 'docker',
                            'message': f'⚠️  WARNING: Container {container} has restarted {count} times',
                            'timestamp': datetime.now().isoformat(),
                            'type': 'excessive_restarts',
                            'container': container,
                            'restart_count': count,
                            'severity': 'MEDIUM',
                            'action': 'monitor_closely'
                        })
                        print(f"   ⚠️  FREQUENT RESTARTS: {container} - {count} restarts")

                except Exception:
                    # Skip containers we can't inspect
                    continue

        except Exception as e:
            print(f"⚠️  Could not check restart counts: {e}")

        return failures

    def check_unhealthy_containers(self) -> List[Dict]:
        """
        Check for containers with failing health checks

        ADDED: November 17, 2025
        PURPOSE: Detect containers that are running but unhealthy (like anh-backend, insa-iot-api)
        DETECTION: Docker health check status = unhealthy
        """
        failures = []

        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'health=unhealthy',
                 '--format', '{{.Names}}:{{.Status}}'],
                capture_output=True, text=True, timeout=10
            )

            for line in result.stdout.strip().split('\n'):
                if line and ':' in line:
                    container, status = line.split(':', 1)
                    failures.append({
                        'source': 'docker',
                        'message': f'💔 UNHEALTHY: Container {container} failing health checks: {status}',
                        'timestamp': datetime.now().isoformat(),
                        'type': 'container_unhealthy',
                        'container': container,
                        'severity': 'MEDIUM',
                        'action': 'check_health_endpoint'
                    })
                    print(f"   💔 UNHEALTHY CONTAINER: {container} - {status}")

        except Exception as e:
            print(f"⚠️  Could not check unhealthy containers: {e}")

        return failures

    def check_http_services(self) -> List[Dict]:
        """
        Check HTTP service availability for critical services

        FIX (Nov 14, 2025): Added Tailscale HTTPS endpoint monitoring
        Previously missing, causing 502 errors to go undetected
        """
        failures = []

        # Critical HTTP services to monitor
        http_services = [
            # Tailscale HTTPS endpoint (NEW - Nov 14, 2025)
            {'name': 'Tailscale HTTPS', 'url': 'https://iac1.tailc58ea3.ts.net', 'timeout': 10},
            # Local HTTP services
            {'name': 'INSA CRM', 'url': 'http://localhost:8003', 'timeout': 5},
            {'name': 'DefectDojo SOC', 'url': 'http://localhost:8082', 'timeout': 5},
            {'name': 'ERPNext CRM', 'url': 'http://localhost:9000', 'timeout': 10},
            {'name': 'InvenTree', 'url': 'http://localhost:9600', 'timeout': 5},
            {'name': 'Mautic', 'url': 'http://localhost:9700', 'timeout': 5},
            {'name': 'n8n Workflows', 'url': 'http://localhost:5678', 'timeout': 5},
            {'name': 'Grafana', 'url': 'http://localhost:3002', 'timeout': 5},
        ]

        try:
            for service in http_services:
                result = subprocess.run(
                    ['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
                     '--connect-timeout', str(service['timeout']), service['url']],
                    capture_output=True, text=True, timeout=service['timeout'] + 2
                )

                http_code = result.stdout.strip()

                # HTTP 000 means connection failed, 200-399 are success codes
                if http_code == '000' or (http_code and int(http_code) >= 400):
                    failures.append({
                        'source': 'http_check',
                        'message': f"Service {service['name']} unavailable (HTTP {http_code})",
                        'timestamp': datetime.now().isoformat(),
                        'type': 'http_failure',
                        'service': service['name'],
                        'url': service['url'],
                        'http_code': http_code
                    })
        except Exception as e:
            print(f"⚠️  Could not check HTTP services: {e}")

        return failures

    def check_container_memory(self) -> List[Dict]:
        """Monitor container memory usage and detect potential OOM risks"""
        issues = []

        # Memory thresholds
        WARNING_THRESHOLD = 70  # Alert at 70% memory usage
        CRITICAL_THRESHOLD = 85  # Critical at 85% memory usage
        LEAK_DETECTION_FILE = "/var/lib/autonomous-orchestrator/memory_history.json"

        try:
            # Get container stats
            result = subprocess.run(
                ['docker', 'stats', '--no-stream', '--format',
                 '{{.Name}}|{{.MemUsage}}|{{.MemPerc}}|{{.Container}}'],
                capture_output=True, text=True, timeout=15
            )

            current_readings = {}

            for line in result.stdout.strip().split('\n'):
                if not line or '|' not in line:
                    continue

                parts = line.split('|')
                if len(parts) < 4:
                    continue

                name = parts[0]
                mem_usage = parts[1]  # e.g., "649MiB / 4GiB"
                mem_perc = parts[2]   # e.g., "15.84%"
                container_id = parts[3]

                # Parse memory percentage
                try:
                    mem_percent = float(mem_perc.strip().replace('%', ''))
                except (ValueError, AttributeError):
                    continue

                # Parse memory usage (current / limit)
                try:
                    if '/' in mem_usage:
                        current, limit = mem_usage.split('/')
                        current_mb = self._parse_memory_mb(current.strip())
                        limit_mb = self._parse_memory_mb(limit.strip())
                    else:
                        continue
                except Exception:
                    continue

                # Store current reading for leak detection
                current_readings[name] = {
                    'timestamp': datetime.now().isoformat(),
                    'mem_percent': mem_percent,
                    'mem_current_mb': current_mb,
                    'mem_limit_mb': limit_mb
                }

                # Check thresholds
                severity = None
                if mem_percent >= CRITICAL_THRESHOLD:
                    severity = 'critical'
                elif mem_percent >= WARNING_THRESHOLD:
                    severity = 'warning'

                if severity:
                    issues.append({
                        'source': 'container_memory',
                        'message': f'Container {name} using {mem_percent:.1f}% memory ({mem_usage}) - {severity.upper()} threshold exceeded',
                        'timestamp': datetime.now().isoformat(),
                        'type': 'container_memory_pressure',
                        'container': name,
                        'container_id': container_id,
                        'mem_percent': mem_percent,
                        'mem_usage': mem_usage,
                        'severity': severity
                    })

            # Memory leak detection (compare with historical data)
            leak_issues = self._detect_memory_leaks(current_readings, LEAK_DETECTION_FILE)
            issues.extend(leak_issues)

            # Save current readings for next cycle
            self._save_memory_history(current_readings, LEAK_DETECTION_FILE)

        except Exception as e:
            print(f"⚠️  Could not check container memory: {e}")

        return issues

    def _parse_memory_mb(self, mem_str: str) -> float:
        """Parse memory string to MB (e.g., '649MiB', '4GiB', '2.5GB')"""
        mem_str = mem_str.strip().upper()

        if 'GIB' in mem_str or 'GB' in mem_str:
            value = float(mem_str.replace('GIB', '').replace('GB', '').strip())
            return value * 1024
        elif 'MIB' in mem_str or 'MB' in mem_str:
            return float(mem_str.replace('MIB', '').replace('MB', '').strip())
        elif 'KIB' in mem_str or 'KB' in mem_str:
            value = float(mem_str.replace('KIB', '').replace('KB', '').strip())
            return value / 1024
        else:
            return 0.0

    def _detect_memory_leaks(self, current: Dict, history_file: str) -> List[Dict]:
        """Detect memory leaks by comparing current vs historical readings"""
        leaks = []

        # Load historical data (last 6 readings = 30 minutes of data at 5-min intervals)
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history = json.load(f)
            else:
                history = {}
        except Exception:
            return leaks

        # Check each container for increasing memory trend
        for container, current_data in current.items():
            if container not in history or len(history[container]) < 3:
                # Need at least 3 data points (15 minutes) to detect leak
                continue

            recent_readings = history[container][-5:]  # Last 5 readings (25 minutes)

            # Calculate memory growth rate
            memory_values = [r['mem_current_mb'] for r in recent_readings]
            memory_values.append(current_data['mem_current_mb'])

            # Check if memory is consistently increasing
            increasing_count = 0
            for i in range(1, len(memory_values)):
                if memory_values[i] > memory_values[i-1]:
                    increasing_count += 1

            # Memory leak if 80%+ readings show increase and total growth > 20%
            leak_threshold = 0.8 * (len(memory_values) - 1)
            growth_rate = (memory_values[-1] - memory_values[0]) / memory_values[0] * 100

            if increasing_count >= leak_threshold and growth_rate > 20:
                leaks.append({
                    'source': 'memory_leak_detector',
                    'message': f'Potential memory leak in container {container}: {growth_rate:.1f}% growth over {len(memory_values)*5} minutes ({"→".join([f"{v:.0f}MB" for v in memory_values])})',
                    'timestamp': datetime.now().isoformat(),
                    'type': 'container_memory_leak',
                    'container': container,
                    'growth_rate': growth_rate,
                    'duration_minutes': len(memory_values) * 5,
                    'severity': 'critical' if growth_rate > 50 else 'warning'
                })

        return leaks

    def _save_memory_history(self, current: Dict, history_file: str):
        """Save current memory readings to history file"""
        try:
            # Load existing history
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    history = json.load(f)
            else:
                history = {}

            # Append current readings
            for container, data in current.items():
                if container not in history:
                    history[container] = []

                history[container].append(data)

                # Keep only last 12 readings (1 hour at 5-min intervals)
                if len(history[container]) > 12:
                    history[container] = history[container][-12:]

            # Save updated history
            os.makedirs(os.path.dirname(history_file), exist_ok=True)
            with open(history_file, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save memory history: {e}")

    def check_ml_models(self) -> List[Dict]:
        """Monitor ML model health for predictive maintenance system"""
        issues = []

        # Add path for ML model manager
        sys.path.insert(0, '/home/wil/iot-portal')

        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            # Database connection
            conn = psycopg2.connect(
                host='localhost',
                database='insa_iiot',
                user='iiot_user',
                password='iiot_secure_2025',
                port=5432
            )

            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Check 1: Models older than 7 days (need retraining)
            cursor.execute("""
                SELECT id, device_id, metric_name, trained_at,
                       EXTRACT(DAY FROM NOW() - trained_at) as age_days
                FROM ml_models
                WHERE status = 'active'
                    AND trained_at < NOW() - INTERVAL '7 days'
            """)

            stale_models = cursor.fetchall()
            for model in stale_models:
                issues.append({
                    'source': 'ml_health_monitor',
                    'message': f"ML model for {model['device_id']}/{model['metric_name']} is {int(model['age_days'])} days old and needs retraining (threshold: 7 days)",
                    'timestamp': datetime.now().isoformat(),
                    'type': 'ml_model_stale',
                    'model_id': str(model['id']),
                    'device_id': model['device_id'],
                    'metric_name': model['metric_name'],
                    'age_days': int(model['age_days']),
                    'severity': 'warning' if model['age_days'] < 14 else 'critical'
                })

            # Check 2: Inactive models (not used in last 24 hours)
            cursor.execute("""
                SELECT id, device_id, metric_name, last_used_at,
                       EXTRACT(HOUR FROM NOW() - COALESCE(last_used_at, trained_at)) as hours_inactive
                FROM ml_models
                WHERE status = 'active'
                    AND (last_used_at IS NULL OR last_used_at < NOW() - INTERVAL '24 hours')
            """)

            inactive_models = cursor.fetchall()
            for model in inactive_models:
                hours_inactive = int(model['hours_inactive']) if model['hours_inactive'] else 999
                issues.append({
                    'source': 'ml_health_monitor',
                    'message': f"ML model for {model['device_id']}/{model['metric_name']} has not been used in {hours_inactive} hours - possible inactive device or dead model",
                    'timestamp': datetime.now().isoformat(),
                    'type': 'ml_model_inactive',
                    'model_id': str(model['id']),
                    'device_id': model['device_id'],
                    'metric_name': model['metric_name'],
                    'hours_inactive': hours_inactive,
                    'severity': 'warning'
                })

            # Check 3: Too many inactive models per device (cleanup needed)
            cursor.execute("""
                SELECT device_id, metric_name, COUNT(*) as inactive_count
                FROM ml_models
                WHERE status = 'inactive'
                GROUP BY device_id, metric_name
                HAVING COUNT(*) > 5
            """)

            cleanup_needed = cursor.fetchall()
            for entry in cleanup_needed:
                issues.append({
                    'source': 'ml_health_monitor',
                    'message': f"Device {entry['device_id']}/{entry['metric_name']} has {entry['inactive_count']} inactive models - cleanup recommended to save storage",
                    'timestamp': datetime.now().isoformat(),
                    'type': 'ml_model_cleanup_needed',
                    'device_id': entry['device_id'],
                    'metric_name': entry['metric_name'],
                    'inactive_count': entry['inactive_count'],
                    'severity': 'warning'
                })

            # Check 4: Model storage disk space
            model_storage_dir = '/var/lib/insa-iiot/ml_models'
            if os.path.exists(model_storage_dir):
                result = subprocess.run(
                    ['du', '-sm', model_storage_dir],
                    capture_output=True, text=True, timeout=10
                )

                if result.returncode == 0:
                    storage_mb = int(result.stdout.split()[0])
                    # Warn if storage > 500MB
                    if storage_mb > 500:
                        issues.append({
                            'source': 'ml_health_monitor',
                            'message': f"ML model storage using {storage_mb}MB - consider cleanup or archival (threshold: 500MB)",
                            'timestamp': datetime.now().isoformat(),
                            'type': 'ml_storage_high',
                            'storage_mb': storage_mb,
                            'severity': 'warning' if storage_mb < 1000 else 'critical'
                        })

            cursor.close()
            conn.close()

        except Exception as e:
            # Only report if ML database is expected to exist
            if 'does not exist' not in str(e) and 'relation' not in str(e):
                print(f"⚠️  Could not check ML models: {e}")

        return issues

    def check_port_conflicts(self) -> List[Dict]:
        """NEW: Detect port binding conflicts in service logs"""
        conflicts = []

        try:
            # Scan recent service logs for port binding errors
            result = subprocess.run(
                ['journalctl', '--since', '10 minutes ago', '--priority=err',
                 '--grep', 'address already in use|bind.*failed', '--no-pager'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'address already in use' in line.lower() or 'bind' in line.lower():
                        # Extract service name and port
                        service_match = re.search(r'(\S+\.service)', line)
                        port_match = re.search(r':(\d+)', line)

                        service_name = service_match.group(1) if service_match else 'unknown'
                        port = port_match.group(1) if port_match else 'unknown'

                        conflicts.append({
                            'type': 'port_conflict',
                            'source': 'systemd',
                            'service': service_name,
                            'port': port,
                            'message': f"Service {service_name} cannot bind to port {port} - address already in use"
                        })

        except Exception as e:
            print(f"⚠️  Could not scan for port conflicts: {e}")

        return conflicts

    def check_service_path_validity(self) -> List[Dict]:
        """NEW: Proactive validation of service file paths"""
        invalid_paths = []

        try:
            import glob

            # Scan all active service files
            for service_file in glob.glob('/etc/systemd/system/*.service'):
                if not os.path.exists(service_file):
                    continue

                try:
                    with open(service_file, 'r') as f:
                        config = f.read()

                    service_name = os.path.basename(service_file)

                    # Check WorkingDirectory
                    working_dir_match = re.search(r'^WorkingDirectory=(.+)$', config, re.MULTILINE)
                    if working_dir_match:
                        working_dir = working_dir_match.group(1).strip()
                        if not os.path.exists(working_dir):
                            invalid_paths.append({
                                'type': 'invalid_service_path',
                                'source': 'systemd',
                                'service': service_name,
                                'path': working_dir,
                                'config_line': 'WorkingDirectory',
                                'message': f"Service {service_name} WorkingDirectory does not exist: {working_dir}"
                            })

                    # Check ExecStart path
                    exec_start_match = re.search(r'^ExecStart=(.+)$', config, re.MULTILINE)
                    if exec_start_match:
                        exec_start = exec_start_match.group(1).strip()
                        exec_path = exec_start.split()[0] if exec_start else ''
                        if exec_path and not os.path.exists(exec_path):
                            invalid_paths.append({
                                'type': 'invalid_service_path',
                                'source': 'systemd',
                                'service': service_name,
                                'path': exec_path,
                                'config_line': 'ExecStart',
                                'message': f"Service {service_name} ExecStart binary does not exist: {exec_path}"
                            })

                except Exception as e:
                    pass  # Skip problematic service files

        except Exception as e:
            print(f"⚠️  Could not validate service paths: {e}")

        return invalid_paths

    def scan_all(self) -> List[Dict]:
        """Comprehensive scan of all sources"""
        all_issues = []

        print("🔍 Scanning logs...")
        all_issues.extend(self.scan_logs())

        print("🔍 Checking services...")
        all_issues.extend(self.check_failed_services())

        print("🔍 Checking containers...")
        all_issues.extend(self.check_failed_containers())

        print("🔄 Checking for crash loops...")
        all_issues.extend(self.check_crash_loops())

        print("🔄 Checking restart counts...")
        all_issues.extend(self.check_excessive_restarts())

        print("💔 Checking unhealthy containers...")
        all_issues.extend(self.check_unhealthy_containers())

        print("🔍 Checking HTTP services...")
        all_issues.extend(self.check_http_services())

        print("🔍 Monitoring container memory...")
        all_issues.extend(self.check_container_memory())

        print("🔍 Checking ML model health...")
        all_issues.extend(self.check_ml_models())

        print("🔍 Checking for port conflicts...")
        all_issues.extend(self.check_port_conflicts())

        print("🔍 Validating service paths...")
        all_issues.extend(self.check_service_path_validity())

        return all_issues

class AutoFixer:
    """Automated fixing capabilities"""

    def __init__(self):
        self.sudo_password = "110811081108"  # For service restarts

    def fix_service(self, service_name: str) -> Tuple[bool, str]:
        """Attempt to restart failed service"""
        try:
            # Restart service
            cmd = f"echo {self.sudo_password} | sudo -S systemctl restart {service_name}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

            # Check if successful
            time.sleep(2)
            check = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True, text=True
            )

            if check.stdout.strip() == 'active':
                return True, f"Service {service_name} restarted successfully"
            else:
                return False, f"Service {service_name} restart failed - still inactive"

        except Exception as e:
            return False, f"Error restarting service: {e}"

    def fix_container(self, container_name: str) -> Tuple[bool, str]:
        """Attempt to restart failed container"""
        try:
            # Restart container
            result = subprocess.run(
                ['docker', 'restart', container_name],
                capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                # Check if running
                time.sleep(2)
                check = subprocess.run(
                    ['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Status}}'],
                    capture_output=True, text=True
                )

                if 'Up' in check.stdout:
                    return True, f"Container {container_name} restarted successfully"
                else:
                    return False, f"Container {container_name} restart failed - not running"
            else:
                return False, f"Docker restart command failed"

        except Exception as e:
            return False, f"Error restarting container: {e}"

    def attempt_fix(self, issue: Dict) -> Tuple[bool, str]:
        """Attempt automated fix based on issue type"""
        issue_type = issue.get('type')

        if issue_type == 'service_failure':
            service = issue.get('service', '').replace('.service', '')
            return self.fix_service(service)

        elif issue_type == 'container_failure':
            container = issue.get('container')
            return self.fix_container(container)

        else:
            return False, "No automated fix available for this issue type"

class TaskOrchestrator:
    """Main orchestration logic with parallel execution support"""

    def __init__(self, db_path: str = "/var/lib/autonomous-orchestrator/tasks.db", max_workers: int = 4):
        self.db_path = db_path
        self.max_workers = max_workers
        self.db_lock = threading.Lock()  # Thread-safe database operations

        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.github = GitHubIntegration()
        self.scanner = BugScanner()
        self.fixer = IntelligentAutoFixer()  # Legacy - kept for compatibility
        self.email = EmailNotifier()

        # NEW: Multi-agent coordinator (4-phase graduated intelligence)
        self.coordinator = AgentCoordinator()

        self.init_database()

        print(f"🚀 Parallel Execution Enabled: {self.max_workers} worker threads")
        print(f"🎓 Multi-Agent System Enabled: 4-phase graduated intelligence")

    def init_database(self):
        """Initialize task tracking database"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        c = conn.cursor()

        c.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                issue_hash TEXT UNIQUE NOT NULL,
                github_issue_number INTEGER,
                issue_type TEXT NOT NULL,
                issue_source TEXT NOT NULL,
                issue_message TEXT NOT NULL,
                status TEXT DEFAULT 'detected',
                fix_attempted BOOLEAN DEFAULT 0,
                fix_successful BOOLEAN DEFAULT 0,
                fix_message TEXT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                github_created_at TIMESTAMP,
                fixed_at TIMESTAMP,
                closed_at TIMESTAMP
            )
        ''')

        c.execute('''
            CREATE TABLE IF NOT EXISTS task_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        ''')

        conn.commit()
        conn.close()

    def generate_issue_hash(self, issue: Dict) -> str:
        """Generate unique hash for issue deduplication"""
        key = f"{issue['type']}:{issue['source']}:{issue.get('service', issue.get('container', 'unknown'))}"
        return key

    def task_exists(self, issue_hash: str) -> Optional[int]:
        """Check if task already exists and is not closed"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            c = conn.cursor()
            c.execute(
                "SELECT id FROM tasks WHERE issue_hash = ? AND status != 'closed' ORDER BY id DESC LIMIT 1",
                (issue_hash,)
            )
            result = c.fetchone()
            conn.close()
            return result[0] if result else None

    def get_task_status(self, task_id: int) -> Optional[Dict]:
        """Get full task details including status"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            c = conn.cursor()
            c.execute(
                """SELECT id, status, fix_attempted, fix_successful, fix_message,
                          detected_at, github_issue_number
                   FROM tasks WHERE id = ?""",
                (task_id,)
            )
            result = c.fetchone()
            conn.close()

            if result:
                return {
                    'id': result[0],
                    'status': result[1],
                    'fix_attempted': bool(result[2]),
                    'fix_successful': bool(result[3]),
                    'fix_message': result[4],
                    'detected_at': result[5],
                    'github_issue_number': result[6]
                }
            return None

    def create_task(self, issue: Dict) -> int:
        """Create new task in database"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            c = conn.cursor()

            issue_hash = self.generate_issue_hash(issue)

            # Try to insert, but if it already exists, get the existing task_id
            c.execute('''
                INSERT OR IGNORE INTO tasks (issue_hash, issue_type, issue_source, issue_message)
                VALUES (?, ?, ?, ?)
            ''', (issue_hash, issue['type'], issue['source'], issue['message']))

            if c.lastrowid > 0:
                # New task created
                task_id = c.lastrowid
                c.execute('''
                    INSERT INTO task_history (task_id, action, details)
                    VALUES (?, ?, ?)
                ''', (task_id, 'detected', f"Issue detected: {issue['message'][:100]}"))
            else:
                # Task already exists, get its ID
                c.execute(
                    "SELECT id FROM tasks WHERE issue_hash = ? ORDER BY id DESC LIMIT 1",
                    (issue_hash,)
                )
                result = c.fetchone()
                task_id = result[0] if result else None

            conn.commit()
            conn.close()

            return task_id

    def update_task_github(self, task_id: int, issue_number: int):
        """Update task with GitHub issue number"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            c = conn.cursor()
            c.execute('''
                UPDATE tasks
                SET github_issue_number = ?, github_created_at = ?, status = 'escalated'
                WHERE id = ?
            ''', (issue_number, datetime.now(), task_id))

            c.execute('''
                INSERT INTO task_history (task_id, action, details)
                VALUES (?, ?, ?)
            ''', (task_id, 'github_created', f"GitHub issue #{issue_number} created"))

            conn.commit()
            conn.close()

    def update_task_fix_attempt(self, task_id: int, success: bool, message: str):
        """Update task with fix attempt result"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            c = conn.cursor()

            status = 'fixed' if success else 'fix_failed'
            fixed_at = datetime.now() if success else None

            c.execute('''
                UPDATE tasks
                SET fix_attempted = 1, fix_successful = ?, fix_message = ?, status = ?, fixed_at = ?
                WHERE id = ?
            ''', (success, message, status, fixed_at, task_id))

            c.execute('''
                INSERT INTO task_history (task_id, action, details)
                VALUES (?, ?, ?)
            ''', (task_id, 'fix_attempted', f"Fix {'successful' if success else 'failed'}: {message}"))

            conn.commit()
            conn.close()

    def close_task(self, task_id: int):
        """Mark task as closed"""
        with self.db_lock:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            c = conn.cursor()
            c.execute('''
                UPDATE tasks
                SET status = 'closed', closed_at = ?
                WHERE id = ?
            ''', (datetime.now(), task_id))

            c.execute('''
                INSERT INTO task_history (task_id, action, details)
                VALUES (?, ?, ?)
            ''', (task_id, 'closed', 'Task completed and closed'))

            conn.commit()
            conn.close()

    def process_issue(self, issue: Dict) -> Dict:
        """Process single issue through full workflow"""
        result = {
            'issue': issue,
            'task_created': False,
            'github_created': False,
            'fix_attempted': False,
            'fix_successful': False,
            'closed': False
        }

        # Check for duplicate
        issue_hash = self.generate_issue_hash(issue)
        existing_task_id = self.task_exists(issue_hash)

        # Handle existing task with retry logic
        if existing_task_id:
            task_status = self.get_task_status(existing_task_id)

            if task_status and task_status['status'] == 'closed':
                # Task already closed, skip
                print(f"   ⏭️  Issue already resolved (Task #{existing_task_id})")
                result['closed'] = True
                return result

            # Task exists but not closed - retry fixing
            print(f"   🔄 Retrying existing Task #{existing_task_id} (Status: {task_status['status']})")
            task_id = existing_task_id
            result['task_created'] = False  # Using existing task
        else:
            # Create new task
            task_id = self.create_task(issue)
            result['task_created'] = True
            print(f"   ✅ Created Task #{task_id}")

        # NEW: Use 4-phase intelligent coordinator system
        print(f"   🤖 Starting 4-Phase Intelligent Agent System...")
        coord_result = self.coordinator.process_issue_intelligent(issue, task_id)

        result['fix_attempted'] = True
        result['fix_successful'] = coord_result.get('success', False)
        result['phase'] = coord_result.get('phase', 0)
        result['escalated'] = coord_result.get('escalated', False)

        # Handle different phases
        if coord_result['success']:
            # Fixed in Phase 1, 2, or 3
            phase = coord_result['phase']
            strategy = coord_result.get('strategy', 'unknown')

            fix_message = f"Phase {phase} success: {strategy}"
            self.update_task_fix_attempt(task_id, True, fix_message)

            print(f"   ✅ FIXED IN PHASE {phase}")
            print(f"      Strategy: {strategy}")

            # Close task immediately if fixed
            self.close_task(task_id)
            result['closed'] = True
            print(f"   ✅ Task #{task_id} closed (auto-fixed)")

            return result

        elif coord_result['escalated']:
            # Phase 4: Local escalation (no GitHub)
            escalation_id = coord_result['escalation_id']

            fix_message = f"Escalated locally (Escalation #{escalation_id})"
            self.update_task_fix_attempt(task_id, False, fix_message)

            print(f"   📋 LOCALLY ESCALATED (Escalation #{escalation_id})")
            print(f"   🌐 View at: http://localhost:8888/escalation/{escalation_id}")
            print(f"   📧 Email sent to w.aroca@insaing.com")
            print(f"   ⚠️  NO GITHUB ISSUE CREATED (local only)")

            result['local_escalation'] = True
            result['escalation_id'] = escalation_id

            return result

        return result

    def generate_github_title(self, issue: Dict) -> str:
        """Generate GitHub issue title"""
        issue_type = issue['type'].replace('_', ' ').title()
        source = issue.get('service') or issue.get('container') or issue['source']
        return f"🤖 {issue_type}: {source}"

    def generate_github_body(self, issue: Dict, task_id: int, fix_message: str, attempts: List[Dict] = None) -> str:
        """Generate enhanced GitHub issue body with full fix attempt history"""

        # Build attempt history section
        attempt_history = ""
        if attempts:
            attempt_history = "\n### Fix Attempt History\n\n"
            for att in attempts:
                status_icon = "✅" if att['success'] else "❌"
                attempt_history += f"""**Attempt {att['attempt']}: {att['strategy'].replace('_', ' ').title()}** {status_icon}
- **Time:** {att['execution_time']}
- **Timestamp:** {att['timestamp']}
- **Result:** {att['message']}

"""

        return f"""## Automated Issue Detection

**Detected by:** Autonomous Task Orchestrator with Intelligent Multi-Attempt System
**Task ID:** #{task_id}
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
**Fix Attempts:** {len(attempts) if attempts else 0}

### Issue Details

**Type:** {issue['type'].replace('_', ' ').title()}
**Source:** {issue['source']}
**Service/Container:** {issue.get('service') or issue.get('container', 'N/A')}
**Message:**
```
{issue['message']}
```
{attempt_history}
### Final Status

**Status:** ❌ All automated fix attempts failed
**Summary:** {fix_message}

### AI Research Results

The intelligent fixer system attempted multiple strategies including:
- Basic restart (simple service/container restart)
- Deep restart (with cache clearing and cleanup)
- Dependency checking (verify required services)
- AI-powered research and diagnosis

**All attempts exhausted.** Manual intervention required.

### Required Action

This issue requires manual investigation and resolution.

**Recommended steps:**
1. Review the fix attempt history above
2. Check service logs: `journalctl -u {issue.get('service', 'SERVICE_NAME')} -n 100`
3. Verify dependencies: `systemctl list-dependencies {issue.get('service', 'SERVICE_NAME')}`
4. Check resource usage: `systemctl status {issue.get('service', 'SERVICE_NAME')}`
5. Apply manual fix
6. Comment on this issue with resolution
7. The orchestrator will detect the fix automatically

**Possible causes:**
- Missing dependencies (requires installation)
- Configuration error (requires manual edit)
- Resource constraints (requires system adjustment)
- Code bug (requires code fix)
- External service failure (requires external resolution)

---

🤖 Generated by Autonomous Task Orchestrator with Intelligent Multi-Attempt System + AI Research
Co-Authored-By: Claude <noreply@anthropic.com>
"""

    def generate_github_labels(self, issue: Dict) -> List[str]:
        """Generate appropriate labels for GitHub issue"""
        labels = ['automation', 'bug-hunter']

        if issue['type'] == 'service_failure':
            labels.append('service')
        elif issue['type'] == 'container_failure':
            labels.append('docker')
        elif issue['type'] == 'log_error':
            labels.append('error')
        elif issue['type'] == 'container_memory_pressure':
            labels.append('docker')
            labels.append('memory')
            labels.append('oom-risk')
        elif issue['type'] == 'container_memory_leak':
            labels.append('docker')
            labels.append('memory')
            labels.append('memory-leak')
        elif issue['type'] == 'ml_model_stale':
            labels.append('ml')
            labels.append('ml-retraining')
            labels.append('predictive-maintenance')
        elif issue['type'] == 'ml_model_inactive':
            labels.append('ml')
            labels.append('ml-monitoring')
        elif issue['type'] == 'ml_model_cleanup_needed':
            labels.append('ml')
            labels.append('ml-cleanup')
            labels.append('storage')
        elif issue['type'] == 'ml_storage_high':
            labels.append('ml')
            labels.append('storage')

        # Add priority based on severity or message
        severity = issue.get('severity', '').lower()
        if severity == 'critical' or 'critical' in issue['message'].lower():
            labels.append('priority:critical')
        elif severity == 'warning' or 'high' in issue['message'].lower():
            labels.append('priority:high')
        else:
            labels.append('priority:medium')

        return labels

    def run_cycle(self) -> Dict:
        """Run one complete orchestration cycle with parallel execution"""
        print("\n" + "="*70)
        print("🤖 AUTONOMOUS TASK ORCHESTRATOR - Cycle Starting")
        print("="*70)
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        cycle_start_time = time.time()

        # Scan for issues
        print("\n📊 Phase 1: Multi-Source Scanning")
        issues = self.scanner.scan_all()

        print(f"\n📋 Found {len(issues)} issues")

        if not issues:
            print("   ✅ No issues detected - system healthy")
            return {'issues_found': 0, 'tasks_created': 0, 'fixes_successful': 0, 'github_issues_created': 0, 'execution_time': 0}

        # Process issues in parallel
        print(f"\n📊 Phase 2: Processing {len(issues)} Issues in Parallel")
        print(f"   🚀 Using {min(self.max_workers, len(issues))} worker threads")

        stats = {
            'issues_found': len(issues),
            'tasks_created': 0,
            'fixes_successful': 0,
            'github_issues_created': 0,
            'execution_time': 0,
            'parallel_execution': True,
            'max_workers': self.max_workers
        }

        # Use ThreadPoolExecutor for parallel processing
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks to the executor
            future_to_issue = {
                executor.submit(self._process_issue_with_timeout, issue, i, len(issues)): issue
                for i, issue in enumerate(issues, 1)
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_issue):
                issue = future_to_issue[future]
                try:
                    result = future.result(timeout=300)  # 5 minute timeout per task

                    # Update statistics
                    if result['task_created']:
                        stats['tasks_created'] += 1
                    if result['fix_successful']:
                        stats['fixes_successful'] += 1
                    if result['github_created']:
                        stats['github_issues_created'] += 1

                except concurrent.futures.TimeoutError:
                    print(f"\n⚠️  TIMEOUT: Task for issue {issue['type']} exceeded 5 minutes")
                    print(f"   Source: {issue['source']}")
                    print(f"   Skipping to prevent blocking...")

                except Exception as exc:
                    print(f"\n❌ ERROR: Task for issue {issue['type']} generated exception:")
                    print(f"   Exception: {exc}")
                    print(f"   Source: {issue['source']}")
                    print(f"   Continuing with other tasks...")

        # Calculate total execution time
        cycle_end_time = time.time()
        stats['execution_time'] = round(cycle_end_time - cycle_start_time, 2)

        # Summary
        print("\n" + "="*70)
        print("📊 CYCLE COMPLETE - Summary")
        print("="*70)
        print(f"   Issues Detected: {stats['issues_found']}")
        print(f"   Tasks Created: {stats['tasks_created']}")
        print(f"   Fixes Successful: {stats['fixes_successful']}")
        print(f"   GitHub Issues Created: {stats['github_issues_created']}")
        print(f"   Auto-Fix Success Rate: {stats['fixes_successful']}/{stats['tasks_created']} ({100*stats['fixes_successful']/max(stats['tasks_created'],1):.0f}%)")
        print(f"   ⚡ Execution Time: {stats['execution_time']}s (parallel with {self.max_workers} workers)")
        print("="*70)

        return stats

    def _process_issue_with_timeout(self, issue: Dict, issue_num: int, total_issues: int) -> Dict:
        """Wrapper for process_issue with proper logging for parallel execution"""
        thread_id = threading.current_thread().name
        print(f"\n📌 [Worker {thread_id}] Issue {issue_num}/{total_issues}: {issue['type']}")
        print(f"   Source: {issue['source']}")
        print(f"   Message: {issue['message'][:80]}...")

        try:
            result = self.process_issue(issue)
            print(f"✅ [Worker {thread_id}] Completed issue {issue_num}")
            return result
        except Exception as e:
            print(f"❌ [Worker {thread_id}] Failed to process issue {issue_num}: {e}")
            raise

def main():
    """Main entry point"""
    orchestrator = TaskOrchestrator()

    # Run single cycle
    stats = orchestrator.run_cycle()

    return 0 if stats['issues_found'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
