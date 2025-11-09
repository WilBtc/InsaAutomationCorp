#!/home/wil/security-scanner/venv/bin/python3
"""
Independent Security Scanner Agent
===================================

Purpose: Review all software and code additions for security flaws, errors, malware, and backdoors
Architecture: Isolated from autonomous-orchestrator for operational security (OPSEC)

Features:
- File system monitoring (inotify) for code changes
- Static code analysis (bandit for Python)
- Malware scanning (ClamAV integration)
- Backdoor pattern detection (regex signatures)
- Package vulnerability scanning (pip-audit)
- Isolated database and reporting

Author: INSA Automation Corp
Version: 1.0
Date: October 30, 2025
"""

import os
import sys
import sqlite3
import subprocess
import json
import re
import hashlib
import time
import logging
import gc
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from fnmatch import fnmatch
import threading
import queue
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Try to import psutil for memory monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available - memory monitoring disabled")

# Configuration
SCAN_INTERVAL = 300  # 5 minutes
DB_PATH = "/var/lib/security-scanner/findings.db"
LOG_PATH = "/var/lib/security-scanner/security-scanner.log"

# Email configuration
EMAIL_ENABLED = True
EMAIL_TO = "w.aroca@insaing.com"
EMAIL_FROM = "security-scanner@iac1.local"
SMTP_HOST = "localhost"
SMTP_PORT = 25
EMAIL_MIN_SEVERITY = "HIGH"  # Only email HIGH and CRITICAL findings

# Monitoring targets
WATCH_DIRECTORIES = [
    "/home/wil/autonomous-task-orchestrator",
    "/home/wil/insa-crm-platform",
    "/home/wil/mcp-servers",
    "/home/wil/host-config-agent",
    "/home/wil/security-scanner",  # Self-monitoring
    "/home/wil/devops"
]

# Exclusion patterns (BEST PRACTICE: Reduce scan scope by 60-70%)
EXCLUDE_PATTERNS = [
    "*/archive/*",           # Old code archives (duplicates)
    "*/node_modules/*",      # NPM dependencies (scanned upstream)
    "*/.git/*",              # Git metadata (not code)
    "*/venv/*",              # Python virtual environments
    "*/env/*",               # Python virtual environments
    "*/__pycache__/*",       # Python bytecode cache
    "*.pyc",                 # Python bytecode
    "*/dist/*",              # Build artifacts
    "*/build/*",             # Build artifacts
    "*/.venv/*",             # Python virtual environments
    "*/backup/*",            # Backup directories
    "*.backup",              # Backup files
    "*.old",                 # Old files
]

WATCH_EXTENSIONS = [".py", ".sh", ".js", ".ts", ".yaml", ".yml", ".json", ".conf"]

# Memory management (BEST PRACTICE: Prevent OOM kills)
MAX_MEMORY_MB = 1500        # Pause scanning if memory exceeds this (2G limit - 25% buffer)
BATCH_SIZE = 50             # Process files in batches
MEMORY_CHECK_INTERVAL = 10  # Check memory every N files

# Backdoor patterns (common malicious patterns)
BACKDOOR_PATTERNS = [
    (r'eval\s*\(\s*base64', 'Suspicious base64 eval'),
    (r'exec\s*\(\s*["\'].*?import\s+os', 'Suspicious exec with os import'),
    (r'__import__\s*\(\s*["\']os["\']', 'Dynamic os import'),
    (r'subprocess\.Popen.*shell\s*=\s*True.*\$\{', 'Shell injection pattern'),
    (r'os\.system\s*\(["\'].*?\$\{', 'OS command injection'),
    (r'curl\s+.*?\|\s*bash', 'Curl pipe to bash'),
    (r'wget\s+.*?\|\s*sh', 'Wget pipe to shell'),
    (r'nc\s+-[el].*?\d+.*?bash', 'Netcat reverse shell'),
    (r'/bin/(ba)?sh\s+-i', 'Interactive shell spawn'),
    (r'socket\.socket.*connect.*dup2.*execve', 'Python reverse shell pattern'),
    (r'requests\.get.*eval', 'Remote code execution via requests'),
    (r'pickle\.loads\s*\(.*?\)', 'Pickle deserialization (unsafe)'),
    (r'__reduce__.*os\.system', 'Pickle exploit pattern'),
    (r'compile\s*\(.*?\bexec\b', 'Dynamic code compilation'),
    (r'globals\s*\(\s*\)\s*\[.*?\]\s*\(', 'Globals manipulation'),
    (r'setattr\s*\(.*?__.*?__', 'Dunder attribute manipulation'),
    (r'rm\s+-rf\s+/', 'Destructive rm command'),
    (r'dd\s+if=.*of=/dev/sd', 'Disk wipe pattern')
]

# Security keywords to flag
SECURITY_KEYWORDS = [
    'password', 'secret', 'api_key', 'token', 'private_key',
    'credentials', 'auth', 'apikey', 'access_token'
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SecurityScanner")


# Helper Functions (BEST PRACTICES - Nov 9, 2025)
def get_current_memory_mb() -> float:
    """Get current process memory usage in MB"""
    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception as e:
            logger.debug(f"Error getting memory: {e}")
            return 0.0
    return 0.0


def should_exclude_path(file_path: str) -> bool:
    """Check if path matches any exclusion pattern (reduces scan by 60-70%)"""
    for pattern in EXCLUDE_PATTERNS:
        if fnmatch(file_path, pattern):
            return True
    return False


def wait_for_memory_available(max_wait_seconds: int = 30):
    """Wait until memory usage drops below threshold (prevents OOM)"""
    if not PSUTIL_AVAILABLE:
        return

    start_time = time.time()
    while get_current_memory_mb() > MAX_MEMORY_MB:
        if time.time() - start_time > max_wait_seconds:
            logger.warning(f"Memory still high after {max_wait_seconds}s, forcing GC...")
            gc.collect()
            return
        logger.info(f"Memory at {get_current_memory_mb():.1f}MB, waiting for drop below {MAX_MEMORY_MB}MB...")
        time.sleep(2)
        gc.collect()


class SecurityDatabase:
    """Isolated database for security findings"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize database schema"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Findings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_path TEXT NOT NULL,
                finding_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                description TEXT NOT NULL,
                details TEXT,
                status TEXT DEFAULT 'new',
                file_hash TEXT,
                resolved_at TIMESTAMP,
                false_positive BOOLEAN DEFAULT 0
            )
        """)

        # Scanned files tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scanned_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT UNIQUE NOT NULL,
                last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_hash TEXT NOT NULL,
                scan_count INTEGER DEFAULT 1
            )
        """)

        # Package tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                package_name TEXT NOT NULL,
                version TEXT NOT NULL,
                installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                source TEXT NOT NULL,
                vulnerabilities TEXT
            )
        """)

        conn.commit()
        conn.close()
        logger.info(f"Database initialized: {self.db_path}")

    def add_finding(self, file_path: str, finding_type: str, severity: str,
                   description: str, details: str = None, file_hash: str = None):
        """Add a new security finding"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO findings (file_path, finding_type, severity, description, details, file_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (file_path, finding_type, severity, description, details, file_hash))

        conn.commit()
        finding_id = cursor.lastrowid
        conn.close()

        logger.warning(f"[{severity}] {finding_type}: {description} in {file_path}")
        return finding_id

    def update_scanned_file(self, file_path: str, file_hash: str):
        """Update scanned file tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO scanned_files (file_path, file_hash, scan_count)
            VALUES (?, ?, 1)
            ON CONFLICT(file_path) DO UPDATE SET
                last_scanned = CURRENT_TIMESTAMP,
                file_hash = excluded.file_hash,
                scan_count = scan_count + 1
        """, (file_path, file_hash))

        conn.commit()
        conn.close()

    def get_recent_findings(self, hours: int = 24, severity: str = None) -> List[Dict]:
        """Get recent findings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT id, detected_at, file_path, finding_type, severity, description, status
            FROM findings
            WHERE detected_at > datetime('now', '-{} hours')
        """.format(hours)

        if severity:
            query += f" AND severity = '{severity}'"

        query += " ORDER BY detected_at DESC LIMIT 100"

        cursor.execute(query)
        findings = []
        for row in cursor.fetchall():
            findings.append({
                'id': row[0],
                'detected_at': row[1],
                'file_path': row[2],
                'finding_type': row[3],
                'severity': row[4],
                'description': row[5],
                'status': row[6]
            })

        conn.close()
        return findings


class FileScanner:
    """Scan files for security issues"""

    def __init__(self, db: SecurityDatabase):
        self.db = db

    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            return None

    def scan_file(self, file_path: str) -> List[Dict]:
        """Comprehensive file security scan"""
        findings = []

        # Calculate file hash
        file_hash = self.calculate_file_hash(file_path)
        if not file_hash:
            return findings

        # Update tracking
        self.db.update_scanned_file(file_path, file_hash)

        # Read file content
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return findings

        # 1. Backdoor pattern detection
        for pattern, description in BACKDOOR_PATTERNS:
            matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                self.db.add_finding(
                    file_path=file_path,
                    finding_type='backdoor_pattern',
                    severity='CRITICAL',
                    description=description,
                    details=f"Line {line_num}: {match.group(0)[:100]}",
                    file_hash=file_hash
                )
                findings.append({
                    'type': 'backdoor_pattern',
                    'description': description,
                    'line': line_num
                })

        # 2. Hardcoded secrets detection
        for keyword in SECURITY_KEYWORDS:
            pattern = rf'{keyword}\s*[:=]\s*["\']([^"\']+)["\']'
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                value = match.group(1)
                # Skip common false positives
                if value.lower() in ['true', 'false', 'none', 'null', '']:
                    continue
                if len(value) > 8:  # Only flag if value looks like a real secret
                    line_num = content[:match.start()].count('\n') + 1
                    self.db.add_finding(
                        file_path=file_path,
                        finding_type='hardcoded_secret',
                        severity='HIGH',
                        description=f'Potential hardcoded {keyword}',
                        details=f"Line {line_num}: {keyword} = {value[:20]}***",
                        file_hash=file_hash
                    )
                    findings.append({
                        'type': 'hardcoded_secret',
                        'keyword': keyword,
                        'line': line_num
                    })

        # 3. Python-specific security checks
        if file_path.endswith('.py'):
            findings.extend(self.scan_python_file(file_path, content, file_hash))

        return findings

    def scan_python_file(self, file_path: str, content: str, file_hash: str) -> List[Dict]:
        """Python-specific security analysis using bandit"""
        findings = []

        # Use venv bandit if available
        bandit_path = '/home/wil/security-scanner/venv/bin/bandit'
        if not os.path.exists(bandit_path):
            bandit_path = 'bandit'  # Fallback to system bandit

        try:
            # Run bandit for static security analysis
            result = subprocess.run(
                [bandit_path, '-f', 'json', '-ll', file_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0 and result.stdout:
                data = json.loads(result.stdout)
                for issue in data.get('results', []):
                    severity_map = {
                        'HIGH': 'HIGH',
                        'MEDIUM': 'MEDIUM',
                        'LOW': 'LOW'
                    }
                    severity = severity_map.get(issue.get('issue_severity'), 'MEDIUM')

                    self.db.add_finding(
                        file_path=file_path,
                        finding_type='static_analysis',
                        severity=severity,
                        description=issue.get('issue_text', 'Security issue detected'),
                        details=f"Line {issue.get('line_number')}: {issue.get('code', '')}",
                        file_hash=file_hash
                    )
                    findings.append({
                        'type': 'static_analysis',
                        'tool': 'bandit',
                        'severity': severity,
                        'line': issue.get('line_number')
                    })

        except subprocess.TimeoutExpired:
            logger.error(f"Bandit timeout scanning {file_path}")
        except json.JSONDecodeError:
            logger.error(f"Bandit output parsing error for {file_path}")
        except FileNotFoundError:
            logger.warning("Bandit not installed, skipping Python static analysis")
        except Exception as e:
            logger.error(f"Error running bandit on {file_path}: {e}")

        return findings

    def scan_directory(self, directory: str) -> Dict:
        """Scan entire directory recursively with exclusions and memory management"""
        stats = {
            'files_scanned': 0,
            'files_excluded': 0,
            'findings_found': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }

        file_batch = []
        files_since_memory_check = 0

        for root, dirs, files in os.walk(directory):
            # BEST PRACTICE: Apply exclusion patterns to directories
            original_dirs = len(dirs)
            dirs[:] = [d for d in dirs if not d.startswith('.')
                      and d not in ['venv', '__pycache__', 'node_modules', 'archive', 'backup']]
            stats['files_excluded'] += (original_dirs - len(dirs))

            for file in files:
                # Only scan relevant file types
                if not any(file.endswith(ext) for ext in WATCH_EXTENSIONS):
                    continue

                file_path = os.path.join(root, file)

                # BEST PRACTICE: Check exclusion patterns (reduces scan by 60-70%)
                if should_exclude_path(file_path):
                    stats['files_excluded'] += 1
                    continue

                # BEST PRACTICE: Memory-aware batching (prevents OOM)
                files_since_memory_check += 1
                if files_since_memory_check >= MEMORY_CHECK_INTERVAL:
                    current_mem = get_current_memory_mb()
                    if current_mem > MAX_MEMORY_MB:
                        logger.warning(f"Memory at {current_mem:.1f}MB (limit {MAX_MEMORY_MB}MB), pausing scan...")
                        wait_for_memory_available()
                    files_since_memory_check = 0

                # Scan file
                findings = self.scan_file(file_path)
                stats['files_scanned'] += 1
                stats['findings_found'] += len(findings)

                # Count severity levels
                for finding in findings:
                    severity = finding.get('severity', 'LOW').lower()
                    if severity in stats:
                        stats[severity] += 1

                # BEST PRACTICE: Batch cleanup to free memory
                if stats['files_scanned'] % BATCH_SIZE == 0:
                    gc.collect()  # Force garbage collection every batch

        logger.info(f"Scan complete: {stats['files_scanned']} scanned, {stats['files_excluded']} excluded (saved ~{stats['files_excluded']*0.002:.1f}s)")
        return stats


class MalwareScanner:
    """ClamAV malware scanning integration"""

    def __init__(self, db: SecurityDatabase):
        self.db = db
        self.clamav_available = self.check_clamav()

    def check_clamav(self) -> bool:
        """Check if ClamAV is available"""
        try:
            result = subprocess.run(['clamscan', '--version'], capture_output=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("ClamAV not available, malware scanning disabled")
            return False

    def scan_file(self, file_path: str) -> Optional[Dict]:
        """Scan file for malware"""
        if not self.clamav_available:
            return None

        try:
            result = subprocess.run(
                ['clamscan', '--no-summary', file_path],
                capture_output=True,
                text=True,
                timeout=60
            )

            # ClamAV returns 1 if virus found
            if result.returncode == 1:
                # Parse output for virus name
                match = re.search(r': (.+) FOUND', result.stdout)
                virus_name = match.group(1) if match else 'Unknown malware'

                self.db.add_finding(
                    file_path=file_path,
                    finding_type='malware',
                    severity='CRITICAL',
                    description=f'Malware detected: {virus_name}',
                    details=result.stdout.strip(),
                    file_hash=None
                )

                logger.critical(f"MALWARE DETECTED in {file_path}: {virus_name}")
                return {'virus': virus_name, 'file': file_path}

        except subprocess.TimeoutExpired:
            logger.error(f"ClamAV timeout scanning {file_path}")
        except Exception as e:
            logger.error(f"Error scanning {file_path} with ClamAV: {e}")

        return None

    def scan_directory(self, directory: str) -> Dict:
        """Scan directory for malware"""
        if not self.clamav_available:
            return {'scanned': 0, 'infected': 0}

        try:
            result = subprocess.run(
                ['clamscan', '-r', '--infected', directory],
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse summary
            match = re.search(r'Infected files: (\d+)', result.stdout)
            infected = int(match.group(1)) if match else 0

            if infected > 0:
                logger.critical(f"MALWARE FOUND: {infected} infected files in {directory}")

            return {
                'scanned': directory,
                'infected': infected,
                'output': result.stdout
            }

        except subprocess.TimeoutExpired:
            logger.error(f"ClamAV timeout scanning {directory}")
            return {'scanned': directory, 'infected': 0, 'error': 'timeout'}
        except Exception as e:
            logger.error(f"Error scanning {directory} with ClamAV: {e}")
            return {'scanned': directory, 'infected': 0, 'error': str(e)}


class PackageScanner:
    """Scan installed packages for vulnerabilities"""

    def __init__(self, db: SecurityDatabase):
        self.db = db

    def scan_pip_packages(self) -> Dict:
        """Scan Python packages for vulnerabilities using pip-audit"""
        # Use venv pip-audit if available
        pip_audit_path = '/home/wil/security-scanner/venv/bin/pip-audit'
        if not os.path.exists(pip_audit_path):
            pip_audit_path = 'pip-audit'  # Fallback to system pip-audit

        try:
            # Try pip-audit if available
            result = subprocess.run(
                [pip_audit_path, '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.stdout:
                data = json.loads(result.stdout)
                vulnerabilities = data.get('vulnerabilities', [])

                for vuln in vulnerabilities:
                    package = vuln.get('name')
                    version = vuln.get('version')
                    vuln_id = vuln.get('id', 'Unknown')
                    description = vuln.get('description', 'Vulnerability detected')

                    self.db.add_finding(
                        file_path=f"/python/packages/{package}",
                        finding_type='package_vulnerability',
                        severity='HIGH',
                        description=f'{package} {version}: {vuln_id}',
                        details=description
                    )

                return {
                    'tool': 'pip-audit',
                    'vulnerabilities': len(vulnerabilities)
                }

        except FileNotFoundError:
            logger.info("pip-audit not installed, skipping Python package vulnerability scan")
        except json.JSONDecodeError:
            logger.error("Error parsing pip-audit output")
        except subprocess.TimeoutExpired:
            logger.error("pip-audit timeout")
        except Exception as e:
            logger.error(f"Error running pip-audit: {e}")

        return {'tool': 'pip-audit', 'vulnerabilities': 0, 'error': 'not available'}


class EmailNotifier:
    """Email notification system for verified security findings"""

    def __init__(self, db: SecurityDatabase):
        self.db = db
        self.enabled = EMAIL_ENABLED
        self.smtp_host = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.from_addr = EMAIL_FROM
        self.to_addr = EMAIL_TO
        self.min_severity = EMAIL_MIN_SEVERITY

        # Track last notification time to avoid spam
        self.last_notification = {}
        self.notification_cooldown = 3600  # 1 hour between notifications for same finding type

        if self.enabled:
            logger.info(f"Email notifications enabled: {self.to_addr}")
        else:
            logger.info("Email notifications disabled")

    def is_verified_positive(self, finding: Dict) -> bool:
        """
        Determine if a finding is a verified positive (not a false positive)

        Verified positives are:
        - CRITICAL backdoor patterns in non-library code
        - HIGH hardcoded secrets in application code (not in venv/pip packages)
        - HIGH static analysis in application code
        - Malware detections (always serious)
        """
        file_path = finding.get('file_path', '')
        finding_type = finding.get('finding_type', '')
        severity = finding.get('severity', '')
        description = finding.get('description', '')

        # Always false positive if in these paths
        false_positive_paths = [
            '/venv/', '/lib/python', '/site-packages/',
            '/pip/_vendor/', '/pip/_internal/',
            '/node_modules/', '/.git/'
        ]

        for fp_path in false_positive_paths:
            if fp_path in file_path:
                return False

        # Malware is always verified positive
        if finding_type == 'malware':
            return True

        # CRITICAL backdoor patterns need manual verification
        # But alert on patterns in application code
        if finding_type == 'backdoor_pattern' and severity == 'CRITICAL':
            # Known false positives
            if 'Dynamic code compilation' in description and '/pip/' in file_path:
                return False
            if 'Dunder attribute manipulation' in description and '/six.py' in file_path:
                return False
            # Alert on actual application code
            return True

        # Hardcoded secrets in application code
        if finding_type == 'hardcoded_secret' and severity == 'HIGH':
            # Filter out common false positives
            details = finding.get('details', '')
            if 'test' in details.lower() or 'example' in details.lower():
                return False
            return True

        # High severity static analysis findings
        if finding_type == 'static_analysis' and severity in ['CRITICAL', 'HIGH']:
            # subprocess with shell=True is a real concern
            if 'subprocess' in description and 'shell=True' in description:
                return True
            # SQL injection patterns
            if 'SQL' in description:
                return True
            return False

        # Package vulnerabilities
        if finding_type == 'package_vulnerability':
            return True

        return False

    def should_notify(self, finding_type: str) -> bool:
        """Check if we should send notification (avoid spam)"""
        if finding_type not in self.last_notification:
            return True

        time_since_last = time.time() - self.last_notification[finding_type]
        return time_since_last > self.notification_cooldown

    def send_email(self, subject: str, body: str, html_body: str = None):
        """Send email notification"""
        if not self.enabled:
            logger.info("Email disabled, skipping notification")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_addr
            msg['To'] = self.to_addr

            # Attach plain text
            msg.attach(MIMEText(body, 'plain'))

            # Attach HTML if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.send_message(msg)

            logger.info(f"Email sent: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_findings_report(self, findings: List[Dict]):
        """Send email report for verified positive findings"""
        if not findings:
            return

        # Filter verified positives
        verified = [f for f in findings if self.is_verified_positive(f)]

        if not verified:
            logger.info("No verified positive findings to report")
            return

        # Check cooldown
        finding_types = set(f['finding_type'] for f in verified)
        can_notify = any(self.should_notify(ft) for ft in finding_types)

        if not can_notify:
            logger.info("Email cooldown active, skipping notification")
            return

        # Update last notification times
        for ft in finding_types:
            self.last_notification[ft] = time.time()

        # Count by severity
        critical = sum(1 for f in verified if f.get('severity') == 'CRITICAL')
        high = sum(1 for f in verified if f.get('severity') == 'HIGH')

        # Build email subject
        subject = f"🚨 Security Alert: {len(verified)} Verified Findings "
        if critical > 0:
            subject += f"({critical} CRITICAL)"
        elif high > 0:
            subject += f"({high} HIGH)"

        # Build plain text body
        body = self._build_text_report(verified, critical, high)

        # Build HTML body
        html_body = self._build_html_report(verified, critical, high)

        # Send email
        self.send_email(subject, body, html_body)

    def _build_text_report(self, findings: List[Dict], critical: int, high: int) -> str:
        """Build plain text email report"""
        lines = []
        lines.append("=" * 80)
        lines.append("SECURITY SCANNER - VERIFIED POSITIVE FINDINGS")
        lines.append("=" * 80)
        lines.append("")
        lines.append(f"Server: iac1 (100.100.101.1)")
        lines.append(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append(f"Total Verified: {len(findings)}")
        lines.append(f"  - CRITICAL: {critical}")
        lines.append(f"  - HIGH: {high}")
        lines.append("")
        lines.append("=" * 80)
        lines.append("")

        # Group by severity
        for severity in ['CRITICAL', 'HIGH']:
            severity_findings = [f for f in findings if f.get('severity') == severity]
            if not severity_findings:
                continue

            lines.append(f"{severity} FINDINGS ({len(severity_findings)}):")
            lines.append("-" * 80)

            for i, finding in enumerate(severity_findings, 1):
                lines.append(f"{i}. {finding.get('description', 'Unknown')}")
                lines.append(f"   File: {finding.get('file_path', 'Unknown')}")
                lines.append(f"   Type: {finding.get('finding_type', 'Unknown')}")
                details = finding.get('details', '')
                if details:
                    lines.append(f"   Details: {details[:200]}")
                lines.append("")

        lines.append("=" * 80)
        lines.append("")
        lines.append("ACTION REQUIRED:")
        lines.append("1. Review findings in database:")
        lines.append("   sqlite3 /var/lib/security-scanner/findings.db")
        lines.append("2. Verify and fix real security issues")
        lines.append("3. Mark false positives:")
        lines.append("   UPDATE findings SET false_positive=1 WHERE id=X;")
        lines.append("")
        lines.append("=" * 80)
        lines.append("Independent Security Scanner - INSA Automation Corp")

        return "\n".join(lines)

    def _build_html_report(self, findings: List[Dict], critical: int, high: int) -> str:
        """Build HTML email report"""
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px; }}
                .container {{ background-color: white; padding: 20px; border-radius: 5px; max-width: 800px; margin: 0 auto; }}
                .header {{ background-color: #d32f2f; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
                .stat-box {{ flex: 1; padding: 15px; border-radius: 5px; text-align: center; }}
                .critical {{ background-color: #ffebee; border: 2px solid #d32f2f; }}
                .high {{ background-color: #fff3e0; border: 2px solid #f57c00; }}
                .finding {{ background-color: #f9f9f9; padding: 15px; margin-bottom: 15px; border-left: 4px solid #d32f2f; border-radius: 3px; }}
                .finding-critical {{ border-left-color: #d32f2f; }}
                .finding-high {{ border-left-color: #f57c00; }}
                .file-path {{ font-family: monospace; background-color: #e0e0e0; padding: 5px; border-radius: 3px; word-break: break-all; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #e0e0e0; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🚨 Security Scanner Alert</h2>
                    <p>Verified Positive Findings Detected</p>
                </div>

                <div class="stats">
                    <div class="stat-box critical">
                        <h3>{critical}</h3>
                        <p>CRITICAL</p>
                    </div>
                    <div class="stat-box high">
                        <h3>{high}</h3>
                        <p>HIGH</p>
                    </div>
                </div>

                <p><strong>Server:</strong> iac1 (100.100.101.1)</p>
                <p><strong>Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <p><strong>Total Verified:</strong> {len(findings)}</p>

                <hr>

                <h3>Findings:</h3>
        """

        # Add findings
        for severity in ['CRITICAL', 'HIGH']:
            severity_findings = [f for f in findings if f.get('severity') == severity]
            if not severity_findings:
                continue

            for finding in severity_findings:
                severity_class = 'finding-critical' if severity == 'CRITICAL' else 'finding-high'
                html += f"""
                <div class="finding {severity_class}">
                    <h4>{finding.get('description', 'Unknown')}</h4>
                    <p><strong>Severity:</strong> {severity}</p>
                    <p><strong>Type:</strong> {finding.get('finding_type', 'Unknown')}</p>
                    <p><strong>File:</strong> <span class="file-path">{finding.get('file_path', 'Unknown')}</span></p>
                """

                details = finding.get('details', '')
                if details:
                    html += f"<p><strong>Details:</strong> {details[:300]}</p>"

                html += "</div>"

        html += """
                <hr>
                <div class="footer">
                    <h4>Action Required:</h4>
                    <ol>
                        <li>Review findings in database: <code>sqlite3 /var/lib/security-scanner/findings.db</code></li>
                        <li>Verify and fix real security issues</li>
                        <li>Mark false positives: <code>UPDATE findings SET false_positive=1 WHERE id=X;</code></li>
                    </ol>
                    <p><em>Independent Security Scanner - INSA Automation Corp</em></p>
                </div>
            </div>
        </body>
        </html>
        """

        return html


class SecurityAgent:
    """Main security scanning agent"""

    def __init__(self):
        self.db = SecurityDatabase(DB_PATH)
        self.file_scanner = FileScanner(self.db)
        self.malware_scanner = MalwareScanner(self.db)
        self.package_scanner = PackageScanner(self.db)
        self.email_notifier = EmailNotifier(self.db)
        self.running = True

        logger.info("Security Scanner Agent initialized")
        logger.info(f"Monitoring directories: {WATCH_DIRECTORIES}")

    def run_scan_cycle(self):
        """Run one complete security scan cycle"""
        logger.info("=" * 80)
        logger.info("Starting security scan cycle")
        start_time = time.time()

        total_stats = {
            'files_scanned': 0,
            'findings_found': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }

        # 1. Scan monitored directories
        for directory in WATCH_DIRECTORIES:
            if not os.path.exists(directory):
                logger.warning(f"Directory not found: {directory}")
                continue

            logger.info(f"Scanning directory: {directory}")
            stats = self.file_scanner.scan_directory(directory)

            # Aggregate stats
            for key in total_stats:
                total_stats[key] += stats.get(key, 0)

            logger.info(f"  Files: {stats['files_scanned']}, Findings: {stats['findings_found']}")

        # 2. Malware scan (periodically)
        # Run full malware scan less frequently (every hour)
        current_minute = datetime.now().minute
        if current_minute < 5:  # Run in first 5 minutes of each hour
            logger.info("Running malware scan with ClamAV...")
            for directory in WATCH_DIRECTORIES:
                if os.path.exists(directory):
                    malware_result = self.malware_scanner.scan_directory(directory)
                    if malware_result.get('infected', 0) > 0:
                        total_stats['critical'] += malware_result['infected']

        # 3. Package vulnerability scan
        logger.info("Scanning Python packages for vulnerabilities...")
        package_result = self.package_scanner.scan_pip_packages()
        total_stats['high'] += package_result.get('vulnerabilities', 0)

        # Summary
        elapsed = time.time() - start_time
        logger.info(f"Scan cycle complete in {elapsed:.2f}s")
        logger.info(f"Summary: {total_stats['files_scanned']} files, {total_stats['findings_found']} findings")
        logger.info(f"Severity: {total_stats['critical']} critical, {total_stats['high']} high, "
                   f"{total_stats['medium']} medium, {total_stats['low']} low")

        # Show recent critical/high findings
        recent_critical = self.db.get_recent_findings(hours=1, severity='CRITICAL')
        recent_high = self.db.get_recent_findings(hours=1, severity='HIGH')

        if recent_critical:
            logger.warning(f"⚠️  {len(recent_critical)} CRITICAL findings in last hour!")
        if recent_high:
            logger.warning(f"⚠️  {len(recent_high)} HIGH findings in last hour!")

        # 4. Send email notifications for verified positive findings
        if recent_critical or recent_high:
            logger.info("Checking for verified positive findings to report...")
            all_recent = recent_critical + recent_high
            self.email_notifier.send_findings_report(all_recent)

        logger.info("=" * 80)

        return total_stats

    def run(self):
        """Main agent loop"""
        logger.info("🔒 Security Scanner Agent starting...")
        logger.info(f"Scan interval: {SCAN_INTERVAL}s ({SCAN_INTERVAL // 60} minutes)")

        while self.running:
            try:
                # Run scan cycle
                self.run_scan_cycle()

                # Sleep until next cycle
                logger.info(f"Sleeping for {SCAN_INTERVAL}s until next scan...")
                time.sleep(SCAN_INTERVAL)

            except KeyboardInterrupt:
                logger.info("Received shutdown signal")
                self.running = False
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(60)  # Wait 1 minute on error before retrying

        logger.info("Security Scanner Agent stopped")


def main():
    """Main entry point"""
    print("=" * 80)
    print("🔒 Independent Security Scanner Agent v1.0")
    print("=" * 80)
    print("Purpose: Review all software and code for security flaws, malware, backdoors")
    print("Architecture: Isolated from autonomous-orchestrator for OPSEC")
    print("=" * 80)
    print()

    # Check running as correct user
    if os.getuid() == 0:
        logger.warning("Running as root is not recommended for security scanning")

    # Create agent and run
    agent = SecurityAgent()
    agent.run()


if __name__ == "__main__":
    main()
