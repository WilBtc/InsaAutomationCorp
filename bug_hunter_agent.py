#!/usr/bin/env python3
"""
Bug Hunter Autonomous Agent
Purpose: Continuous bug detection, diagnosis, and automated fixing
Created: October 31, 2025
"""

import sys
import time
import json
import sqlite3
from datetime import datetime
from pathlib import Path

# Add Bug Hunter to path
sys.path.insert(0, '/home/wil/mcp-servers/active/bug-hunter')
from server import BugDatabase, ErrorDetector, BugFixer


class BugHunterAgent:
    """Autonomous agent for continuous bug hunting and fixing"""

    def __init__(self):
        self.db = BugDatabase()
        self.detector = ErrorDetector()
        self.fixer = BugFixer(self.db)
        self.scan_interval = 300  # 5 minutes
        self.max_fix_attempts = 3

    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}", flush=True)

    def scan_for_new_bugs(self) -> dict:
        """Scan logs and services for new bugs"""
        self.log("🔍 Scanning for bugs...")

        log_files = [
            '/var/log/syslog',
            '/tmp/crm-backend.log',
            '/tmp/insa-crm.log',
            '/var/log/defectdojo_remediation_agent.log',
            '/tmp/insa-crm-auth-api.log'
        ]

        all_errors = []

        # Scan logs (last 5 minutes)
        log_errors = self.detector.scan_logs(log_files, hours=0.1)
        all_errors.extend(log_errors)

        # Check services
        service_errors = self.detector.check_services()
        all_errors.extend(service_errors)

        # Check containers
        container_errors = self.detector.check_docker_containers()
        all_errors.extend(container_errors)

        # Store new bugs
        new_bugs = 0
        for error in all_errors:
            bug_hash = f"{error.get('error_type')}:{error.get('message', '')[:50]}"
            try:
                bug_id = self.db.add_bug({
                    'bug_hash': bug_hash,
                    'title': f"{error.get('error_type', 'Error')}: {error.get('message', '')[:100]}",
                    'description': error.get('context', ''),
                    'error_type': error.get('error_type'),
                    'stack_trace': error.get('context'),
                    'source_file': error.get('source_file'),
                    'line_number': error.get('line_number'),
                    'service': error.get('service'),
                    'severity': error.get('severity', 'medium')
                })
                if bug_id:
                    new_bugs += 1
            except:
                pass  # Bug already exists

        self.log(f"   Found {len(all_errors)} errors, {new_bugs} new bugs")
        return {
            'total_errors': len(all_errors),
            'new_bugs': new_bugs,
            'errors_by_type': self._count_by_type(all_errors)
        }

    def _count_by_type(self, errors):
        """Count errors by type"""
        counts = {}
        for error in errors:
            error_type = error.get('error_type', 'unknown')
            counts[error_type] = counts.get(error_type, 0) + 1
        return counts

    def get_fixable_bugs(self) -> list:
        """Get bugs that can be fixed automatically"""
        conn = sqlite3.connect(self.db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get bugs that:
        # 1. Haven't been fixed yet
        # 2. Have fewer than max attempts
        # 3. Have a service name (fixable)
        # 4. Are high or critical severity
        cursor.execute("""
            SELECT * FROM bugs
            WHERE status IN ('detected', 'attempted')
            AND fix_attempts < ?
            AND service IS NOT NULL
            AND service != ''
            AND severity IN ('high', 'critical', 'medium')
            ORDER BY severity DESC, detected_at DESC
            LIMIT 20
        """, (self.max_fix_attempts,))

        bugs = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return bugs

    def attempt_fix(self, bug_data: dict) -> dict:
        """Attempt to fix a bug"""
        bug_id = bug_data['id']

        self.log(f"   🔧 Attempting fix for Bug #{bug_id}: {bug_data['title'][:60]}...")

        # Diagnose first
        diagnosis = self.fixer.diagnose_bug(bug_data)
        confidence = diagnosis.get('confidence', 0)

        self.log(f"      Diagnosis: {diagnosis.get('diagnosis')}")
        self.log(f"      Fix type: {diagnosis.get('fix_type')}, Confidence: {confidence:.0%}")

        # Safety check
        if confidence < 0.6:
            self.log(f"      ⏭️  Confidence too low ({confidence:.0%}), skipping", "WARN")
            return {
                'success': False,
                'reason': 'low_confidence',
                'confidence': confidence
            }

        # Attempt fix
        fix_success = False
        fix_message = "No fix attempted"

        if diagnosis.get('fix_type') == 'service_restart':
            service = bug_data.get('service') or diagnosis.get('service')
            if service and service != '●':  # Skip malformed service names
                fix_success = self.fixer._restart_service(service)
                fix_message = f"Restarted service: {service}" if fix_success else f"Failed to restart {service}"

        elif diagnosis.get('fix_type') == 'container_restart':
            container = bug_data.get('service') or diagnosis.get('service')
            if container and container != '●':
                fix_success = self.fixer._restart_container(container)
                fix_message = f"Restarted container: {container}" if fix_success else f"Failed to restart {container}"

        elif diagnosis.get('fix_type') == 'learned_pattern':
            fix_message = "Learned pattern identified but execution not implemented"

        # Record fix attempt
        self.db.add_fix({
            'bug_id': bug_id,
            'fix_type': diagnosis.get('fix_type', 'unknown'),
            'fix_description': fix_message,
            'fix_code': diagnosis.get('fix_template', ''),
            'success': fix_success,
            'verification_result': 'Success' if fix_success else 'Failed'
        })

        if fix_success:
            self.log(f"      ✅ Fix successful: {fix_message}", "SUCCESS")
        else:
            self.log(f"      ❌ Fix failed: {fix_message}", "ERROR")

        return {
            'success': fix_success,
            'fix_type': diagnosis.get('fix_type'),
            'message': fix_message
        }

    def run_cycle(self):
        """Run one bug hunting cycle"""
        self.log("=" * 60)
        self.log("🤖 BUG HUNTER AGENT - Cycle Starting")
        self.log("=" * 60)

        start_time = time.time()

        # Phase 1: Scan for new bugs
        scan_results = self.scan_for_new_bugs()

        # Phase 2: Get fixable bugs
        self.log("📋 Checking fixable bugs...")
        fixable_bugs = self.get_fixable_bugs()
        self.log(f"   Found {len(fixable_bugs)} fixable bugs")

        # Phase 3: Attempt fixes
        if fixable_bugs:
            self.log("🔧 Attempting fixes...")
            fixes_attempted = 0
            fixes_successful = 0

            for bug in fixable_bugs:
                result = self.attempt_fix(bug)
                fixes_attempted += 1
                if result['success']:
                    fixes_successful += 1

            success_rate = (fixes_successful / fixes_attempted * 100) if fixes_attempted > 0 else 0
            self.log(f"   Fixes: {fixes_successful}/{fixes_attempted} successful ({success_rate:.1f}%)")
        else:
            self.log("   No fixable bugs at this time")

        # Phase 4: Summary
        elapsed = time.time() - start_time
        self.log("=" * 60)
        self.log(f"✅ Cycle complete in {elapsed:.1f}s")
        self.log("=" * 60)

    def run(self):
        """Main agent loop"""
        self.log("🚀 Bug Hunter Agent Starting")
        self.log(f"   Database: {self.db.db_path}")
        self.log(f"   Scan interval: {self.scan_interval}s ({self.scan_interval // 60} minutes)")
        self.log(f"   Max fix attempts: {self.max_fix_attempts}")

        cycle_count = 0

        try:
            while True:
                cycle_count += 1
                self.log(f"\n📊 Cycle #{cycle_count}")

                self.run_cycle()

                # Sleep until next cycle
                self.log(f"💤 Sleeping for {self.scan_interval}s...")
                time.sleep(self.scan_interval)

        except KeyboardInterrupt:
            self.log("🛑 Agent stopped by user", "INFO")
        except Exception as e:
            self.log(f"❌ Agent crashed: {e}", "ERROR")
            raise


if __name__ == "__main__":
    agent = BugHunterAgent()
    agent.run()
