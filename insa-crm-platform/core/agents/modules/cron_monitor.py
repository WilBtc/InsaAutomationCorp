#!/usr/bin/env python3
"""
Cron Job Monitor - Safe Detection Module
Created: October 20, 2025
Purpose: Detect cron job chaos without modifications
Safety: 100% READ-ONLY - No crontab modifications
"""

import re
import time
import psutil
import logging
from glob import glob
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CronJobMonitor:
    """
    Safe cron job analysis - READ ONLY
    Detects duplicates, overlaps, and runaway processes
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def detect_cron_chaos(self) -> Dict:
        """
        Comprehensive cron job analysis across all sources
        Returns risk assessment and recommendations
        """
        self.logger.info("Starting cron chaos detection...")

        sources = {
            'syslog_crons': self._scan_syslog_crons(),
            'cron_d_files': self._scan_cron_d(),
            'etc_crontab': self._scan_etc_crontab(),
        }

        # Analyze for problems
        total_jobs = sum(len(s) for s in sources.values())
        duplicates = self._find_duplicates(sources)
        overlaps = self._find_time_overlaps(sources)
        runaway = self.detect_runaway_processes()

        risk_level = self._calculate_risk(total_jobs, duplicates, overlaps, runaway)

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_jobs': total_jobs,
            'sources': {k: len(v) for k, v in sources.items()},
            'duplicates': len(duplicates),
            'duplicate_details': duplicates,
            'time_overlaps': overlaps,
            'runaway_processes': runaway,
            'risk_level': risk_level,
            'recommendation': self._generate_recommendation(risk_level, duplicates, runaway)
        }

    def _scan_syslog_crons(self) -> List[Dict]:
        """
        Parse /var/log/syslog for CRON executions (last 24h)
        This infers user crontabs without needing sudo
        """
        crons = []
        syslog_path = '/var/log/syslog'

        try:
            with open(syslog_path, 'r') as f:
                for line in f:
                    if 'CRON' in line and 'CMD' in line:
                        parsed = self._parse_cron_log(line)
                        if parsed:
                            crons.append(parsed)

        except PermissionError:
            self.logger.warning(f"Cannot read {syslog_path}")
        except FileNotFoundError:
            self.logger.warning(f"{syslog_path} not found")

        # Deduplicate (same command seen multiple times = scheduled job)
        unique_crons = {}
        for cron in crons:
            key = (cron['user'], cron['command'])
            if key not in unique_crons:
                unique_crons[key] = cron
            else:
                unique_crons[key]['execution_count'] = unique_crons[key].get('execution_count', 1) + 1

        return list(unique_crons.values())

    def _parse_cron_log(self, log_line: str) -> Optional[Dict]:
        """
        Parse syslog cron line:
        Oct 20 19:15:01 iac1 CRON[2495420]: (www-data) CMD (timeout 300 systemd-run ...)
        """
        match = re.search(
            r'(\w{3}\s+\d+\s+\d+:\d+:\d+).*CRON\[(\d+)\]:\s*\((\w+)\)\s+CMD\s*\((.*)\)',
            log_line
        )
        if match:
            timestamp, pid, user, command = match.groups()
            return {
                'timestamp': timestamp,
                'pid': int(pid),
                'user': user,
                'command': command.strip(),
                'source': 'syslog',
                'execution_count': 1
            }
        return None

    def _scan_cron_d(self) -> List[Dict]:
        """Scan /etc/cron.d/ files (world-readable)"""
        jobs = []
        for file_path in glob('/etc/cron.d/*'):
            try:
                with open(file_path, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        parsed = self._parse_crontab_line(line, source=file_path, line_num=line_num)
                        if parsed:
                            jobs.append(parsed)
            except PermissionError:
                self.logger.warning(f"Cannot read {file_path}")

        return jobs

    def _scan_etc_crontab(self) -> List[Dict]:
        """Scan /etc/crontab (world-readable)"""
        jobs = []
        try:
            with open('/etc/crontab', 'r') as f:
                for line_num, line in enumerate(f, 1):
                    parsed = self._parse_crontab_line(line, source='/etc/crontab', line_num=line_num)
                    if parsed:
                        jobs.append(parsed)
        except FileNotFoundError:
            pass

        return jobs

    def _parse_crontab_line(self, line: str, source: str, line_num: int) -> Optional[Dict]:
        """
        Parse crontab line:
        */5 * * * * user command
        """
        line = line.strip()

        # Skip comments and empty lines
        if not line or line.startswith('#'):
            return None

        # Skip variable assignments (SHELL=/bin/bash, etc)
        if '=' in line and not line.startswith('*'):
            return None

        # Parse cron schedule + user + command
        parts = line.split(None, 6)  # Split on whitespace, max 7 parts
        if len(parts) < 6:
            return None

        schedule = ' '.join(parts[0:5])
        user = parts[5]
        command = parts[6] if len(parts) > 6 else ''

        return {
            'schedule': schedule,
            'user': user,
            'command': command,
            'source': source,
            'line_num': line_num
        }

    def _find_duplicates(self, sources: Dict[str, List[Dict]]) -> List[Dict]:
        """Find duplicate commands across all sources"""
        command_map = defaultdict(list)

        for source_name, jobs in sources.items():
            for job in jobs:
                # Normalize command (remove env variables, timeouts)
                normalized = self._normalize_command(job['command'])
                command_map[normalized].append({
                    'source': source_name,
                    'user': job.get('user', 'unknown'),
                    'full_command': job['command']
                })

        # Filter to only duplicates (same command, multiple sources)
        duplicates = []
        for command, instances in command_map.items():
            if len(instances) > 1:
                duplicates.append({
                    'command': command,
                    'instances': instances,
                    'count': len(instances)
                })

        return duplicates

    def _normalize_command(self, command: str) -> str:
        """Normalize command for duplicate detection"""
        # Remove timeout, nice, ionice wrappers
        normalized = re.sub(r'timeout\s+\d+\s+', '', command)
        normalized = re.sub(r'nice\s+-n\s+\d+\s+', '', normalized)
        normalized = re.sub(r'ionice\s+-c\d+\s+-n\d+\s+', '', normalized)
        normalized = re.sub(r'systemd-run\s+[^\s]+\s+', '', normalized)

        # Extract core command (php /path/to/script args)
        match = re.search(r'php\s+\S+\s+\S+', normalized)
        if match:
            return match.group(0)

        return normalized.strip()

    def _find_time_overlaps(self, sources: Dict[str, List[Dict]]) -> Dict:
        """Find times when multiple jobs run simultaneously"""
        time_slots = defaultdict(list)

        for source_name, jobs in sources.items():
            for job in jobs:
                schedule = job.get('schedule', '')
                if schedule:
                    # Parse */5 * * * * → every 5 minutes
                    slots = self._expand_schedule(schedule)
                    for slot in slots:
                        time_slots[slot].append({
                            'command': self._normalize_command(job['command']),
                            'user': job.get('user', 'unknown')
                        })

        # Filter to only overlaps (>3 jobs at same time)
        overlaps = {}
        for time_slot, jobs in time_slots.items():
            if len(jobs) > 3:
                overlaps[time_slot] = {
                    'job_count': len(jobs),
                    'jobs': jobs
                }

        return overlaps

    def _expand_schedule(self, schedule: str) -> List[str]:
        """
        Expand cron schedule to time slots
        */5 * * * * → ['00', '05', '10', '15', ...]
        """
        parts = schedule.split()
        if len(parts) < 2:
            return []

        minute = parts[0]
        hour = parts[1]

        # Simple expansion (minute only)
        if minute.startswith('*/'):
            interval = int(minute[2:])
            return [f"{h:02d}:{m:02d}" for h in range(24) for m in range(0, 60, interval)]
        elif minute.isdigit():
            if hour.isdigit():
                return [f"{int(hour):02d}:{int(minute):02d}"]
            else:
                return [f"{h:02d}:{int(minute):02d}" for h in range(24)]

        return []

    def detect_runaway_processes(self) -> List[Dict]:
        """Find processes running too long (likely from cron)"""
        runaway = []

        # Exclude long-running services (not cron jobs)
        excluded_patterns = [
            'php-fpm:',           # PHP-FPM is a service
            'grafana server',     # Grafana is a service
            'minio server',       # MinIO is a service
            'python3 -m http',    # HTTP servers
            'uwsgi',              # uWSGI is a service
            'nginx:',             # Nginx is a service
        ]

        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'create_time', 'username']):
            try:
                info = proc.info
                cmdline = ' '.join(info['cmdline'] or [])
                runtime = time.time() - info['create_time']

                # Skip long-running services
                if any(pattern in cmdline for pattern in excluded_patterns):
                    continue

                # Cron job indicators
                if any(x in cmdline for x in ['php', 'mautic:', 'console', 'bin/console']):
                    if runtime > 1800:  # 30 minutes
                        runaway.append({
                            'pid': info['pid'],
                            'user': info['username'],
                            'command': cmdline,
                            'cpu_percent': info['cpu_percent'] or 0,
                            'runtime_minutes': round(runtime / 60, 1)
                        })

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return runaway

    def _calculate_risk(self, total_jobs: int, duplicates: List, overlaps: Dict, runaway: List) -> str:
        """Calculate risk level based on detected issues"""
        score = 0

        # Scoring
        if total_jobs > 20:
            score += 1
        if len(duplicates) > 5:
            score += 2
        if len(overlaps) > 3:
            score += 2
        if len(runaway) > 0:
            score += 3

        # Risk levels
        if score >= 5:
            return 'CRITICAL'
        elif score >= 3:
            return 'HIGH'
        elif score >= 1:
            return 'MEDIUM'
        else:
            return 'LOW'

    def _generate_recommendation(self, risk_level: str, duplicates: List, runaway: List) -> str:
        """Generate human-readable recommendation"""
        if risk_level == 'CRITICAL':
            return (
                f"CRITICAL: {len(duplicates)} duplicate cron jobs and {len(runaway)} runaway processes detected. "
                "Immediate action required: Consolidate cron jobs to /etc/cron.d/ with resource limits."
            )
        elif risk_level == 'HIGH':
            return (
                f"HIGH: {len(duplicates)} duplicate cron jobs detected. "
                "Recommend consolidating to /etc/cron.d/ with systemd resource limits."
            )
        elif risk_level == 'MEDIUM':
            return "MEDIUM: Some cron job overlap detected. Monitor for CPU spikes."
        else:
            return "LOW: Cron jobs appear normal."


if __name__ == '__main__':
    # Test the monitor
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    monitor = CronJobMonitor()
    result = monitor.detect_cron_chaos()

    print("\n=== Cron Chaos Detection Report ===")
    print(f"Timestamp: {result['timestamp']}")
    print(f"Total Jobs: {result['total_jobs']}")
    print(f"Risk Level: {result['risk_level']}")
    print(f"\nSources: {result['sources']}")
    print(f"\nDuplicates: {result['duplicates']}")
    if result['duplicate_details']:
        print("\nDuplicate Details:")
        for dup in result['duplicate_details'][:5]:  # Show first 5
            print(f"  - {dup['command']} ({dup['count']} instances)")

    print(f"\nTime Overlaps: {len(result['time_overlaps'])}")
    if result['time_overlaps']:
        print("\nOverlap Details:")
        for time_slot, details in list(result['time_overlaps'].items())[:5]:
            print(f"  - {time_slot}: {details['job_count']} jobs")

    print(f"\nRunaway Processes: {len(result['runaway_processes'])}")
    if result['runaway_processes']:
        print("\nRunaway Details:")
        for proc in result['runaway_processes']:
            print(f"  - PID {proc['pid']}: {proc['command'][:60]}... ({proc['runtime_minutes']}min)")

    print(f"\n{result['recommendation']}")
