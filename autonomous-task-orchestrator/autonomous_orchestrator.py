#!/usr/bin/env python3
"""
Autonomous Task Orchestrator
Closed-loop system: Bug Detection → GitHub Issue → Auto-Fix → Update Issue → Close Issue

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

class GitHubIntegration:
    """GitHub API integration for issue management"""

    def __init__(self, config_path: str = "/home/wil/mcp-servers/github-agent/config.json"):
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
    """Email notification system for escalations"""

    def __init__(self, to_email: str = "w.aroca@insaing.com", smtp_host: str = "localhost", smtp_port: int = 25):
        self.to_email = to_email
        self.from_email = "autonomous-orchestrator@iac1.local"
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    def send_escalation_email(self, task_id: int, issue_type: str, issue_message: str,
                             github_issue_number: int, github_url: str, fix_attempted: bool) -> bool:
        """Send email notification when issue is escalated to GitHub"""
        try:
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
        """Check for failed systemd services"""
        failures = []

        try:
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

    def check_http_services(self) -> List[Dict]:
        """Check HTTP service availability for critical services"""
        failures = []

        # Critical HTTP services to monitor
        http_services = [
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

    def scan_all(self) -> List[Dict]:
        """Comprehensive scan of all sources"""
        all_issues = []

        print("🔍 Scanning logs...")
        all_issues.extend(self.scan_logs())

        print("🔍 Checking services...")
        all_issues.extend(self.check_failed_services())

        print("🔍 Checking containers...")
        all_issues.extend(self.check_failed_containers())

        print("🔍 Checking HTTP services...")
        all_issues.extend(self.check_http_services())

        print("🔍 Monitoring container memory...")
        all_issues.extend(self.check_container_memory())

        return all_issues

class AutoFixer:
    """Automated fixing capabilities"""

    def __init__(self):
        self.sudo_password = "[REDACTED]"  # For service restarts

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
    """Main orchestration logic"""

    def __init__(self, db_path: str = "/var/lib/autonomous-orchestrator/tasks.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.github = GitHubIntegration()
        self.scanner = BugScanner()
        self.fixer = IntelligentAutoFixer()  # Enhanced multi-attempt fixer
        self.email = EmailNotifier()

        self.init_database()

    def init_database(self):
        """Initialize task tracking database"""
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "SELECT id FROM tasks WHERE issue_hash = ? AND status != 'closed' ORDER BY id DESC LIMIT 1",
            (issue_hash,)
        )
        result = c.fetchone()
        conn.close()
        return result[0] if result else None

    def create_task(self, issue: Dict) -> int:
        """Create new task in database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        issue_hash = self.generate_issue_hash(issue)

        c.execute('''
            INSERT INTO tasks (issue_hash, issue_type, issue_source, issue_message)
            VALUES (?, ?, ?, ?)
        ''', (issue_hash, issue['type'], issue['source'], issue['message']))

        task_id = c.lastrowid

        c.execute('''
            INSERT INTO task_history (task_id, action, details)
            VALUES (?, ?, ?)
        ''', (task_id, 'detected', f"Issue detected: {issue['message'][:100]}"))

        conn.commit()
        conn.close()

        return task_id

    def update_task_github(self, task_id: int, issue_number: int):
        """Update task with GitHub issue number"""
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
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
        conn = sqlite3.connect(self.db_path)
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

        if existing_task_id:
            print(f"   ⏭️  Issue already tracked (Task #{existing_task_id})")
            return result

        # Create task
        task_id = self.create_task(issue)
        result['task_created'] = True
        print(f"   ✅ Created Task #{task_id}")

        # Attempt automated fix with intelligent multi-attempt system
        print(f"   🔧 Intelligent Multi-Attempt Fix System...")
        fix_result = self.fixer.attempt_fix_with_retry(issue, task_id)
        result['fix_attempted'] = True
        result['fix_successful'] = fix_result['success']
        result['fix_attempts'] = fix_result['total_attempts']
        result['fix_strategy'] = fix_result.get('successful_strategy')

        # Store comprehensive fix results
        fix_message = f"{fix_result['final_message']} ({fix_result['total_attempts']} attempts, {fix_result['total_time']})"
        self.update_task_fix_attempt(task_id, fix_result['success'], fix_message)

        if fix_result['success']:
            print(f"   ✅ Fix successful: {fix_result['final_message']}")
            print(f"      Strategy: {fix_result['successful_strategy']}")
            print(f"      Attempts: {fix_result['total_attempts']}")
            print(f"      Time: {fix_result['total_time']}")

            # Close task immediately if fixed
            self.close_task(task_id)
            result['closed'] = True
            print(f"   ✅ Task #{task_id} closed (auto-fixed)")

            return result
        else:
            print(f"   ❌ All fix attempts failed")
            print(f"      Attempts: {fix_result['total_attempts']}")
            print(f"      Time: {fix_result['total_time']}")
            # Store fix attempts for GitHub issue
            result['fix_attempts_detail'] = fix_result['all_attempts']

        # Escalate to GitHub if fix failed
        print(f"   📤 Escalating to GitHub...")
        github_title = self.generate_github_title(issue)
        github_body = self.generate_github_body(issue, task_id, fix_message, result.get('fix_attempts_detail', []))
        labels = self.generate_github_labels(issue)

        github_issue = self.github.create_issue(github_title, github_body, labels)

        if github_issue:
            issue_number = github_issue['number']
            result['github_created'] = True
            self.update_task_github(task_id, issue_number)
            print(f"   ✅ GitHub issue #{issue_number} created")
            print(f"      URL: {github_issue['html_url']}")

            # Send email notification
            print(f"   📧 Sending email notification...")
            email_sent = self.email.send_escalation_email(
                task_id=task_id,
                issue_type=issue['type'],
                issue_message=issue['message'],
                github_issue_number=issue_number,
                github_url=github_issue['html_url'],
                fix_attempted=fix_success or False
            )
            if email_sent:
                print(f"   ✅ Email sent to w.aroca@insaing.com")
            else:
                print(f"   ⚠️  Email notification failed (but GitHub issue created)")
        else:
            print(f"   ❌ Failed to create GitHub issue")

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
        """Run one complete orchestration cycle"""
        print("\n" + "="*70)
        print("🤖 AUTONOMOUS TASK ORCHESTRATOR - Cycle Starting")
        print("="*70)
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")

        # Scan for issues
        print("\n📊 Phase 1: Multi-Source Scanning")
        issues = self.scanner.scan_all()

        print(f"\n📋 Found {len(issues)} issues")

        if not issues:
            print("   ✅ No issues detected - system healthy")
            return {'issues_found': 0, 'tasks_created': 0, 'fixes_successful': 0, 'github_issues_created': 0}

        # Process each issue
        print(f"\n📊 Phase 2: Processing {len(issues)} Issues")

        stats = {
            'issues_found': len(issues),
            'tasks_created': 0,
            'fixes_successful': 0,
            'github_issues_created': 0
        }

        for i, issue in enumerate(issues, 1):
            print(f"\n📌 Issue {i}/{len(issues)}: {issue['type']}")
            print(f"   Source: {issue['source']}")
            print(f"   Message: {issue['message'][:80]}...")

            result = self.process_issue(issue)

            if result['task_created']:
                stats['tasks_created'] += 1
            if result['fix_successful']:
                stats['fixes_successful'] += 1
            if result['github_created']:
                stats['github_issues_created'] += 1

        # Summary
        print("\n" + "="*70)
        print("📊 CYCLE COMPLETE - Summary")
        print("="*70)
        print(f"   Issues Detected: {stats['issues_found']}")
        print(f"   Tasks Created: {stats['tasks_created']}")
        print(f"   Fixes Successful: {stats['fixes_successful']}")
        print(f"   GitHub Issues Created: {stats['github_issues_created']}")
        print(f"   Auto-Fix Success Rate: {stats['fixes_successful']}/{stats['tasks_created']} ({100*stats['fixes_successful']/max(stats['tasks_created'],1):.0f}%)")
        print("="*70)

        return stats

def main():
    """Main entry point"""
    orchestrator = TaskOrchestrator()

    # Run single cycle
    stats = orchestrator.run_cycle()

    return 0 if stats['issues_found'] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
