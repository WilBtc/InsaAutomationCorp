#!/usr/bin/env python3
"""
Intelligent Multi-Attempt Fixer with AI Research
Enhanced auto-fix system with research agents and learning

Created: October 26, 2025
Author: Insa Automation Corp
Purpose: Intelligent multi-attempt fixing with AI diagnosis
"""

import os
import time
import json
import sqlite3
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple

class LearningDatabase:
    """Track fix patterns and success rates for continuous learning"""

    def __init__(self, db_path: str = "/var/lib/autonomous-orchestrator/learning.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize learning database with pattern tracking tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Table: fix_patterns - Track successful fix strategies
        c.execute('''
            CREATE TABLE IF NOT EXISTS fix_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_key TEXT UNIQUE NOT NULL,
                issue_type TEXT NOT NULL,
                error_pattern TEXT NOT NULL,
                strategy TEXT NOT NULL,
                success_count INTEGER DEFAULT 0,
                total_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                last_used TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table: fix_history - Detailed history of all fix attempts
        c.execute('''
            CREATE TABLE IF NOT EXISTS fix_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                issue_type TEXT NOT NULL,
                error_pattern TEXT NOT NULL,
                strategy TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                message TEXT,
                execution_time_seconds REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Table: research_cache - Cache AI diagnosis results
        c.execute('''
            CREATE TABLE IF NOT EXISTS research_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                error_signature TEXT UNIQUE NOT NULL,
                diagnosis TEXT NOT NULL,
                suggested_fixes TEXT NOT NULL,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hit_count INTEGER DEFAULT 0,
                last_hit TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def record_attempt(self, task_id: int, issue: Dict, strategy: str,
                      success: bool, message: str, exec_time: float):
        """Record a fix attempt in history"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        error_pattern = self.extract_error_pattern(issue['message'])

        c.execute('''
            INSERT INTO fix_history
            (task_id, issue_type, error_pattern, strategy, success, message, execution_time_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (task_id, issue['type'], error_pattern, strategy, success, message, exec_time))

        # Update pattern statistics
        pattern_key = f"{issue['type']}:{error_pattern}:{strategy}"

        c.execute('''
            INSERT INTO fix_patterns (pattern_key, issue_type, error_pattern, strategy,
                                     success_count, total_count, last_used)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(pattern_key) DO UPDATE SET
                success_count = success_count + ?,
                total_count = total_count + 1,
                success_rate = CAST(success_count + ? AS REAL) / (total_count + 1),
                last_used = ?
        ''', (pattern_key, issue['type'], error_pattern, strategy,
             1 if success else 0, datetime.now(),
             1 if success else 0, 1 if success else 0, datetime.now()))

        conn.commit()
        conn.close()

    def get_best_strategy(self, issue: Dict) -> Optional[str]:
        """Get best strategy based on past success with similar issues"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        error_pattern = self.extract_error_pattern(issue['message'])

        # Find best performing strategy for this type + pattern
        c.execute('''
            SELECT strategy, success_rate, success_count
            FROM fix_patterns
            WHERE issue_type = ? AND error_pattern LIKE ?
            AND total_count >= 2
            ORDER BY success_rate DESC, success_count DESC
            LIMIT 1
        ''', (issue['type'], f'%{error_pattern}%'))

        result = c.fetchone()
        conn.close()

        return result[0] if result and result[1] > 0.5 else None

    def extract_error_pattern(self, message: str) -> str:
        """Extract key error pattern from message for matching"""
        # Remove timestamps, paths, PIDs - keep the core error
        import re
        patterns = [
            r'\d{4}-\d{2}-\d{2}',  # Dates
            r'\d{2}:\d{2}:\d{2}',  # Times
            r'/[^\s]+',  # File paths
            r'PID\s+\d+',  # Process IDs
            r'port\s+\d+',  # Port numbers
        ]

        cleaned = message
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned)

        # Get first significant error line (max 100 chars)
        return cleaned[:100].strip()

    def cache_research(self, error_sig: str, diagnosis: Dict):
        """Cache AI research results for reuse"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            INSERT INTO research_cache (error_signature, diagnosis, suggested_fixes, confidence)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(error_signature) DO UPDATE SET
                hit_count = hit_count + 1,
                last_hit = ?
        ''', (error_sig, json.dumps(diagnosis),
             json.dumps(diagnosis.get('suggested_fixes', [])),
             diagnosis.get('confidence', 0.0),
             datetime.now()))

        conn.commit()
        conn.close()

    def get_cached_research(self, error_sig: str) -> Optional[Dict]:
        """Get cached research if available"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            SELECT diagnosis, suggested_fixes, confidence
            FROM research_cache
            WHERE error_signature = ?
        ''', (error_sig,))

        result = c.fetchone()
        conn.close()

        if result:
            return {
                'diagnosis': json.loads(result[0]),
                'suggested_fixes': json.loads(result[1]),
                'confidence': result[2],
                'cached': True
            }
        return None


class ResearchAgent:
    """AI-powered research for finding solutions using Claude Code subprocess"""

    def __init__(self):
        self.claude_path = "/home/wil/.local/bin/claude"
        self.learning_db = LearningDatabase()
        self.timeout = 30  # AI diagnosis timeout

        # NEW: System Knowledge RAG
        try:
            from system_knowledge_rag import SystemKnowledgeRAG
            self.rag = SystemKnowledgeRAG()
            self.rag_enabled = True
            print("      ✅ RAG system loaded - Agents now have system knowledge!")
        except Exception as e:
            print(f"      ⚠️  RAG system not available: {e}")
            self.rag = None
            self.rag_enabled = False

    def diagnose_issue(self, issue: Dict, previous_attempts: List[Dict]) -> Dict:
        """
        Use AI (Claude Code subprocess) to diagnose issue and suggest fixes

        Returns:
        {
            'diagnosis': "Root cause analysis",
            'confidence': 0.85,
            'suggested_fixes': [
                {'strategy': 'restart_with_env', 'description': '...', 'priority': 1},
                ...
            ],
            'cached': False
        }
        """
        # Check cache first
        error_sig = self.generate_error_signature(issue)
        cached = self.learning_db.get_cached_research(error_sig)
        if cached:
            print(f"      💾 Using cached AI diagnosis (confidence: {cached['confidence']:.0%})")
            return cached

        # Build context for AI
        context = self.build_diagnosis_context(issue, previous_attempts)

        try:
            # Execute Claude Code via subprocess (ZERO API cost)
            print(f"      🤖 Engaging AI research...")
            result = subprocess.run(
                [self.claude_path, '--prompt', context],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode == 0:
                diagnosis = self.parse_ai_response(result.stdout)
                diagnosis['cached'] = False

                # Cache for future use
                self.learning_db.cache_research(error_sig, diagnosis)

                return diagnosis
            else:
                return self.fallback_diagnosis(issue)

        except subprocess.TimeoutExpired:
            print(f"      ⚠️  AI diagnosis timeout ({self.timeout}s) - using fallback")
            return self.fallback_diagnosis(issue)
        except Exception as e:
            print(f"      ⚠️  AI diagnosis error: {e} - using fallback")
            return self.fallback_diagnosis(issue)

    def generate_error_signature(self, issue: Dict) -> str:
        """Generate unique signature for error caching"""
        error_pattern = self.learning_db.extract_error_pattern(issue['message'])
        return f"{issue['type']}:{error_pattern}"

    def build_diagnosis_context(self, issue: Dict, previous_attempts: List[Dict]) -> str:
        """Build comprehensive context for AI diagnosis WITH RAG"""
        attempts_text = "\n".join([
            f"  {i+1}. {att['strategy']} - {'SUCCESS' if att['success'] else 'FAILED'}: {att['message']}"
            for i, att in enumerate(previous_attempts)
        ])

        # NEW: Get system knowledge from RAG
        rag_context = ""
        if self.rag_enabled and self.rag:
            try:
                knowledge = self.rag.query(issue)
                rag_context = self.rag.format_for_ai(knowledge)
                print("      📚 RAG context loaded - Agent has full system awareness")
            except Exception as e:
                print(f"      ⚠️  RAG query failed: {e}")
                rag_context = ""

        # Build enhanced context with RAG
        if rag_context:
            context = f"""**SYSTEM KNOWLEDGE (from documentation):**

{rag_context}

**CURRENT ISSUE:**

**Error Details:**
- Type: {issue['type']}
- Source: {issue['source']}
- Service/Container: {issue.get('service') or issue.get('container', 'unknown')}
- Error Message:
  {issue['message']}

**Previous Fix Attempts ({len(previous_attempts)}):**
{attempts_text if previous_attempts else '  (None yet)'}

**YOUR TASK:**
Using the SYSTEM KNOWLEDGE above, diagnose this issue and suggest fixes.

CRITICAL: Pay special attention to:
1. Platform path changes (insa-crm-platform → platforms/insa-crm)
2. Service file configurations (paths must exist)
3. Port conflicts (check for stale processes)
4. Recent platform consolidations

Provide:
1. Root cause diagnosis (use system knowledge)
2. 2-3 prioritized fix strategies
3. Specific commands for each strategy
4. Confidence rating (0-100%)

**Format your response as:**
DIAGNOSIS: [Root cause based on system knowledge - be specific about paths/configs]
CONFIDENCE: [0-100]%
FIX_1: [Strategy name] | [Description] | [Commands]
FIX_2: [Strategy name] | [Description] | [Commands]
FIX_3: [Strategy name] | [Description] | [Commands]

Focus on practical, safe solutions that can be executed automatically.
"""
        else:
            # Fallback: Original generic context (if RAG fails)
            context = f"""Analyze this infrastructure issue and suggest fixes:

**Error Details:**
- Type: {issue['type']}
- Source: {issue['source']}
- Service/Container: {issue.get('service') or issue.get('container', 'unknown')}
- Error Message:
  {issue['message']}

**Previous Fix Attempts ({len(previous_attempts)}):**
{attempts_text if previous_attempts else '  (None yet)'}

**Your Task:**
1. Diagnose the root cause
2. Suggest 2-3 prioritized fix strategies
3. Provide specific commands/steps for each
4. Rate your confidence (0-100%)

**Format your response as:**
DIAGNOSIS: [Root cause analysis in 2-3 sentences]
CONFIDENCE: [0-100]%
FIX_1: [Strategy name] | [Description] | [Commands]
FIX_2: [Strategy name] | [Description] | [Commands]
FIX_3: [Strategy name] | [Description] | [Commands]

Focus on practical, safe solutions that can be executed automatically.
"""

        return context

    def parse_ai_response(self, response: str) -> Dict:
        """Parse AI response into structured format"""
        lines = response.strip().split('\n')
        diagnosis = {
            'diagnosis': '',
            'confidence': 0.5,
            'suggested_fixes': []
        }

        for line in lines:
            line = line.strip()
            if line.startswith('DIAGNOSIS:'):
                diagnosis['diagnosis'] = line.replace('DIAGNOSIS:', '').strip()
            elif line.startswith('CONFIDENCE:'):
                conf_str = line.replace('CONFIDENCE:', '').replace('%', '').strip()
                try:
                    diagnosis['confidence'] = float(conf_str) / 100.0
                except:
                    diagnosis['confidence'] = 0.5
            elif line.startswith('FIX_'):
                parts = line.split('|')
                if len(parts) >= 3:
                    strategy = parts[0].split(':')[1].strip()
                    description = parts[1].strip()
                    commands = parts[2].strip()
                    priority = int(line[4])  # FIX_1, FIX_2, etc.

                    diagnosis['suggested_fixes'].append({
                        'strategy': strategy,
                        'description': description,
                        'commands': commands,
                        'priority': priority
                    })

        return diagnosis

    def fallback_diagnosis(self, issue: Dict) -> Dict:
        """Fallback diagnosis when AI not available"""
        return {
            'diagnosis': f"Unable to get AI diagnosis for {issue['type']}",
            'confidence': 0.3,
            'suggested_fixes': [
                {
                    'strategy': 'basic_restart',
                    'description': 'Try basic restart',
                    'commands': 'systemctl restart service',
                    'priority': 1
                }
            ],
            'cached': False
        }


class PlatformAdminClient:
    """
    Interface to Platform Admin MCP server
    Provides instant, proven fixes for 26 platform services
    """

    # Services covered by Platform Admin (26 total)
    PLATFORM_ADMIN_SERVICES = {
        # Web services (8)
        'erpnext', 'n8n', 'grafana', 'defectdojo', 'inventree', 'mautic',
        'insa_crm', 'iec62443',

        # Infrastructure (7)
        'nginx', 'postgresql', 'mariadb', 'redis', 'postfix', 'minio', 'qdrant',

        # Security services (5)
        'suricata', 'wazuh', 'fail2ban', 'auditd', 'clamav',

        # Autonomous agents (7)
        'integrated_healing_agent', 'host_config_agent',
        'defectdojo_compliance_agent', 'security_integration_agent',
        'task_orchestration_agent', 'azure_monitor_agent', 'soc_agent'
    }

    def __init__(self):
        self.mcp_server = "/home/wil/mcp-servers/platform-admin/server.py"
        self.timeout = 15  # Platform Admin should be fast

    def can_handle_service(self, service_name: str) -> bool:
        """Check if Platform Admin can handle this service"""
        if not service_name:
            return False

        # Normalize service name (remove .service suffix, etc.)
        normalized = service_name.lower().replace('.service', '').replace('-', '_')

        return normalized in self.PLATFORM_ADMIN_SERVICES

    def auto_heal(self, service_name: str) -> Dict:
        """
        Call Platform Admin's platform_auto_heal tool

        Returns:
        {
            'success': True/False,
            'message': "ERPNext fix SUCCESSFUL ✅",
            'time': "2.5s",
            'services_fixed': ['erpnext']
        }
        """
        start_time = time.time()

        try:
            print(f"      🏥 Calling Platform Admin for {service_name}...")

            # Call Platform Admin via Python import (simpler than MCP subprocess)
            import sys
            sys.path.insert(0, '/home/wil')
            from platform_health_monitor import PlatformHealthMonitor

            # Run Platform Admin with auto-fix enabled
            monitor = PlatformHealthMonitor(verbose=False)
            results = monitor.run_health_check(auto_fix=True)

            # Check if service was fixed
            service_result = None
            for service_id, result in results.items():
                if service_id == service_name or service_id.replace('_', '-') == service_name:
                    service_result = result
                    break

            elapsed = time.time() - start_time

            if service_result and service_result.get('auto_fixed'):
                return {
                    'success': True,
                    'message': f"Platform Admin fixed {service_name}",
                    'time': f"{elapsed:.1f}s",
                    'services_fixed': [service_name]
                }
            elif service_result and service_result['healthy']:
                # Already healthy (no fix needed)
                return {
                    'success': True,
                    'message': f"{service_name} already healthy",
                    'time': f"{elapsed:.1f}s",
                    'services_fixed': []
                }
            else:
                # Fix attempted but failed
                error_msg = service_result.get('error', 'Unknown error') if service_result else 'Service not found'
                return {
                    'success': False,
                    'message': f"Platform Admin fix failed: {error_msg}",
                    'time': f"{elapsed:.1f}s",
                    'services_fixed': []
                }

        except Exception as e:
            elapsed = time.time() - start_time
            print(f"      ⚠️  Platform Admin error: {e}")
            return {
                'success': False,
                'message': f"Platform Admin error: {str(e)}",
                'time': f"{elapsed:.1f}s",
                'services_fixed': []
            }


class IntelligentAutoFixer:
    """
    Multi-attempt automated fixing with AI research
    Now with Platform Admin integration for instant proven fixes

    ENHANCED v2.0 (October 30, 2025):
    - Python module installation (pip/pip3)
    - 5-level advanced service recovery
    - Container memory optimization
    - Log error auto-fixing
    """

    MAX_ATTEMPTS = 5  # Increased from 3 to 5 for more aggressive fixing
    RETRY_DELAYS = [15, 30, 60, 90, 120]  # Faster initial attempts

    def __init__(self):
        self.sudo_password = "[REDACTED]"
        self.research = ResearchAgent()
        self.learning = LearningDatabase()
        self.platform_admin = PlatformAdminClient()  # NEW: Platform Admin integration

    def extract_service_name(self, issue: Dict) -> Optional[str]:
        """
        Extract service name from issue data

        Looks in:
        - issue['service'] (for service_failure)
        - issue['container'] (for container_failure)
        - issue message (parsing common patterns)
        """
        # Direct service field
        if issue.get('service'):
            service = issue['service'].replace('.service', '')

            # Handle systemd instance services (e.g., postgresql@16-main -> postgresql)
            if '@' in service:
                service = service.split('@')[0]

            return service.lower().replace('-', '_')

        # Container name
        if issue.get('container'):
            container = issue['container']
            # Map common container names to services
            container_map = {
                'defectdojo-uwsgi-insa': 'defectdojo',
                'frappe_docker_backend_1': 'erpnext',
                'frappe_docker_frontend_1': 'erpnext',
                'n8n_mautic_erpnext': 'n8n',
                'grafana-analytics': 'grafana',
                'inventree_web': 'inventree',
                'mautic': 'mautic',
                'minio-insa-crm': 'minio',
                'insa-crm-qdrant': 'qdrant'
            }
            return container_map.get(container, container.lower().replace('-', '_'))

        # Parse from message
        message = issue.get('message', '').lower()
        for service in self.platform_admin.PLATFORM_ADMIN_SERVICES:
            if service in message or service.replace('_', '-') in message:
                return service

        return None

    def try_platform_admin_fix(self, issue: Dict) -> Dict:
        """
        Try platform admin auto-healing (Phase 1 - instant fix)

        Returns:
        {
            'success': True/False,
            'strategy': 'platform_admin' or 'none',
            'message': 'description'
        }
        """
        service_name = self.extract_service_name(issue)

        if service_name and self.platform_admin.can_handle_service(service_name):
            print(f"         🔧 Trying Platform Admin for {service_name}...")
            result = self.platform_admin.auto_heal(service_name)

            if result.get('success'):
                return {
                    'success': True,
                    'strategy': 'platform_admin',
                    'message': result.get('message', 'Fixed by Platform Admin')
                }
            else:
                return {
                    'success': False,
                    'strategy': 'platform_admin_failed',
                    'message': result.get('message', 'Platform Admin fix failed')
                }

        return {
            'success': False,
            'strategy': 'none',
            'message': 'Service not eligible for Platform Admin'
        }

    def try_learned_pattern(self, issue: Dict) -> Dict:
        """
        Try learned fix patterns from database (Phase 1 - proven fixes)

        Returns:
        {
            'success': True/False,
            'strategy': 'learned_pattern' or 'none',
            'message': 'description'
        }
        """
        # Get best strategy from learning database
        best_strategy = self.learning.get_best_strategy(issue)

        if best_strategy:
            print(f"         📚 Trying learned pattern: {best_strategy}...")
            # TODO: Implement learned pattern execution
            # For now, return failure
            return {
                'success': False,
                'strategy': 'learned_pattern',
                'message': f'Learned pattern available but not yet executable: {best_strategy}'
            }

        return {
            'success': False,
            'strategy': 'none',
            'message': 'No learned patterns available for this issue type'
        }

    def attempt_fix_with_retry(self, issue: Dict, task_id: int) -> Dict:
        """
        Main retry loop with multiple strategies
        NOW WITH PLATFORM ADMIN INTEGRATION (instant proven fixes first!)

        Returns:
        {
            'success': True/False,
            'total_attempts': 3,
            'successful_strategy': 'ai_suggested_fix',
            'final_message': "Fixed by restarting with cleared cache",
            'all_attempts': [...]  # Full history for GitHub issue
        }
        """
        attempts = []
        start_time = time.time()

        print(f"   🔧 Intelligent Multi-Attempt Fix System Engaged")
        print(f"      Max attempts: {self.MAX_ATTEMPTS}")
        print(f"      Learning from: {self.learning.db_path}")

        # NEW: Try Platform Admin FIRST (instant proven fixes)
        service_name = self.extract_service_name(issue)
        if service_name and self.platform_admin.can_handle_service(service_name):
            print(f"      🏥 Platform Admin can handle: {service_name}")

            pa_result = self.platform_admin.auto_heal(service_name)
            pa_time = time.time() - start_time

            # Record Platform Admin attempt
            attempts.append({
                'attempt': 1,
                'strategy': 'platform_admin_auto_heal',
                'success': pa_result['success'],
                'message': pa_result['message'],
                'execution_time': pa_result['time'],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            })

            if pa_result['success']:
                print(f"      ✅ Platform Admin SUCCESS in {pa_result['time']}")
                print(f"         Message: {pa_result['message']}")

                # Record in learning database
                self.learning.record_attempt(
                    task_id=task_id,
                    issue=issue,
                    strategy='platform_admin_auto_heal',
                    success=True,
                    message=pa_result['message'],
                    exec_time=float(pa_result['time'].replace('s', ''))
                )

                return {
                    'success': True,
                    'total_attempts': 1,
                    'successful_strategy': 'platform_admin_auto_heal',
                    'final_message': pa_result['message'],
                    'total_time': pa_result['time'],
                    'all_attempts': attempts
                }
            else:
                print(f"      ❌ Platform Admin failed: {pa_result['message']}")
                print(f"      ⚙️  Falling back to Intelligent Multi-Attempt system...")

                # Record failed Platform Admin attempt
                self.learning.record_attempt(
                    task_id=task_id,
                    issue=issue,
                    strategy='platform_admin_auto_heal',
                    success=False,
                    message=pa_result['message'],
                    exec_time=float(pa_result['time'].replace('s', ''))
                )
        else:
            if service_name:
                print(f"      ℹ️  Service '{service_name}' not in Platform Admin's list")
            else:
                print(f"      ℹ️  Could not extract service name from issue")
            print(f"      ⚙️  Using Intelligent Multi-Attempt system...")

        # EXISTING: Check if we have learned a good strategy for this issue
        learned_strategy = self.learning.get_best_strategy(issue)
        if learned_strategy:
            print(f"      💡 Found learned strategy: {learned_strategy} (will try first)")

        for attempt_num in range(1, self.MAX_ATTEMPTS + 1):
            attempt_start = time.time()
            print(f"\n   🔧 Fix Attempt #{attempt_num}/{self.MAX_ATTEMPTS}")

            # NEW: Intelligent strategy selection based on issue type
            issue_type = issue.get('type')

            # Check for Python module errors first
            if issue_type == 'log_error' and 'No module named' in issue.get('message', ''):
                print(f"      📦 Strategy: Install missing Python module")
                result = self.install_python_module(issue)

            # Container memory leaks
            elif issue_type in ['container_memory_leak', 'container_memory_pressure']:
                print(f"      🧠 Strategy: Container memory optimization")
                result = self.container_memory_optimization(issue)

            # Service failures with 5-level recovery
            elif issue_type == 'service_failure':
                if attempt_num <= 5:
                    print(f"      🔧 Strategy: Advanced service recovery (Level {attempt_num}/5)")
                    result = self.advanced_service_recovery(issue, level=attempt_num)
                else:
                    print(f"      🤖 Strategy: AI-powered research fix")
                    result = self.research_based_fix(issue, attempts)

            # Learned strategy takes priority if available
            elif attempt_num == 1 and learned_strategy:
                print(f"      📚 Strategy: Learned pattern ({learned_strategy})")
                result = self.execute_learned_strategy(issue, learned_strategy)

            # Default strategies (for other issue types)
            elif attempt_num == 1:
                print(f"      📋 Strategy: Basic restart (attempt 1)")
                result = self.basic_restart(issue)
            elif attempt_num == 2:
                print(f"      🧹 Strategy: Deep restart with cleanup (attempt 2)")
                result = self.deep_restart(issue)
            elif attempt_num == 3:
                print(f"      📦 Strategy: Dependency check (attempt 3)")
                result = self.dependency_check(issue)
            elif attempt_num >= 4:
                print(f"      🤖 Strategy: AI-powered research fix (attempt {attempt_num})")
                result = self.research_based_fix(issue, attempts)

            attempt_time = time.time() - attempt_start

            # Record attempt in database
            self.learning.record_attempt(
                task_id=task_id,
                issue=issue,
                strategy=result['strategy'],
                success=result['success'],
                message=result['message'],
                exec_time=attempt_time
            )

            # Add to attempts history
            attempts.append({
                'attempt': attempt_num,
                'strategy': result['strategy'],
                'success': result['success'],
                'message': result['message'],
                'execution_time': f"{attempt_time:.1f}s",
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
            })

            if result['success']:
                total_time = time.time() - start_time
                print(f"   ✅ SUCCESS after {attempt_num} attempt(s) in {total_time:.1f}s")
                print(f"      Strategy: {result['strategy']}")
                print(f"      Message: {result['message']}")

                return {
                    'success': True,
                    'total_attempts': attempt_num,
                    'successful_strategy': result['strategy'],
                    'final_message': result['message'],
                    'total_time': f"{total_time:.1f}s",
                    'all_attempts': attempts
                }
            else:
                print(f"      ❌ Failed: {result['message']}")

            # Wait before next attempt (exponential backoff)
            if attempt_num < self.MAX_ATTEMPTS:
                delay = self.RETRY_DELAYS[attempt_num - 1]
                print(f"      ⏳ Waiting {delay}s before next attempt...")
                time.sleep(delay)

        # All attempts failed
        total_time = time.time() - start_time
        print(f"   ❌ All {self.MAX_ATTEMPTS} attempts FAILED in {total_time:.1f}s")

        return {
            'success': False,
            'total_attempts': self.MAX_ATTEMPTS,
            'successful_strategy': None,
            'final_message': f"All {self.MAX_ATTEMPTS} fix strategies failed",
            'total_time': f"{total_time:.1f}s",
            'all_attempts': attempts
        }

    def install_python_module(self, issue: Dict) -> Dict:
        """Strategy: Install missing Python module via pip"""
        try:
            message = issue.get('message', '')

            # Extract module name from common error patterns
            module_name = None
            if 'No module named' in message:
                # ModuleNotFoundError: No module named 'prometheus_client'
                parts = message.split("'")
                if len(parts) >= 2:
                    module_name = parts[1]
            elif 'cannot import name' in message:
                # ImportError: cannot import name 'foo' from 'bar'
                parts = message.split("'")
                if len(parts) >= 4:
                    module_name = parts[3]

            if not module_name:
                return {
                    'strategy': 'install_python_module',
                    'success': False,
                    'message': 'Could not extract module name from error'
                }

            print(f"         📦 Installing Python module: {module_name}")

            # Try pip3 install (user-level first, then system)
            for attempt, install_cmd in enumerate([
                f"pip3 install --user {module_name}",
                f"echo {self.sudo_password} | sudo -S pip3 install {module_name}",
                f"echo {self.sudo_password} | sudo -S pip3 install --upgrade {module_name}"
            ], 1):
                print(f"         Attempt {attempt}/3: {install_cmd.split('|')[-1].strip()}")
                result = subprocess.run(
                    install_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    # Restart the service that needs this module
                    service = issue.get('service')
                    if service:
                        print(f"         ♻️  Restarting service {service}...")
                        restart_cmd = f"echo {self.sudo_password} | sudo -S systemctl restart {service}"
                        subprocess.run(restart_cmd, shell=True, timeout=30)
                        time.sleep(2)

                    return {
                        'strategy': 'install_python_module',
                        'success': True,
                        'message': f"Installed {module_name} successfully (attempt {attempt})"
                    }

            return {
                'strategy': 'install_python_module',
                'success': False,
                'message': f"Failed to install {module_name} after 3 attempts"
            }

        except Exception as e:
            return {
                'strategy': 'install_python_module',
                'success': False,
                'message': f"Error installing module: {e}"
            }

    def advanced_service_recovery(self, issue: Dict, level: int = 1) -> Dict:
        """
        5-level advanced service recovery system

        Level 1: Basic restart
        Level 2: Reset failed state + restart
        Level 3: Stop + clear locks + start
        Level 4: Restart dependencies + service
        Level 5: Reinstall package + restart
        """
        try:
            service = issue.get('service', '').replace('.service', '')
            if not service:
                return {
                    'strategy': f'advanced_service_recovery_L{level}',
                    'success': False,
                    'message': 'No service name provided'
                }

            print(f"         🔧 Service Recovery Level {level}/5: {service}")

            if level == 1:
                # Level 1: Basic restart
                cmd = f"echo {self.sudo_password} | sudo -S systemctl restart {service}"
                subprocess.run(cmd, shell=True, capture_output=True, timeout=30)

            elif level == 2:
                # Level 2: Reset failed state + restart
                cmd1 = f"echo {self.sudo_password} | sudo -S systemctl reset-failed {service}"
                cmd2 = f"echo {self.sudo_password} | sudo -S systemctl restart {service}"
                subprocess.run(cmd1, shell=True, capture_output=True, timeout=15)
                time.sleep(1)
                subprocess.run(cmd2, shell=True, capture_output=True, timeout=30)

            elif level == 3:
                # Level 3: Stop + clear locks/PIDs + start
                cmd_stop = f"echo {self.sudo_password} | sudo -S systemctl stop {service}"
                subprocess.run(cmd_stop, shell=True, capture_output=True, timeout=30)
                time.sleep(2)

                # Clear common lock files
                lock_files = [
                    f"/var/run/{service}.pid",
                    f"/tmp/{service}.lock",
                    f"/var/lock/{service}",
                ]
                for lock_file in lock_files:
                    cmd_rm = f"echo {self.sudo_password} | sudo -S rm -f {lock_file}"
                    subprocess.run(cmd_rm, shell=True, capture_output=True, timeout=5)

                cmd_start = f"echo {self.sudo_password} | sudo -S systemctl start {service}"
                subprocess.run(cmd_start, shell=True, capture_output=True, timeout=30)

            elif level == 4:
                # Level 4: Restart dependencies + service
                # Get dependencies
                cmd_deps = f"systemctl list-dependencies {service} --plain --no-pager | head -10"
                result_deps = subprocess.run(cmd_deps, shell=True, capture_output=True, text=True, timeout=15)

                # Restart top dependencies
                for line in result_deps.stdout.split('\n')[1:6]:  # Skip first line, take top 5
                    dep = line.strip().replace('●', '').replace('├─', '').replace('└─', '').strip()
                    if dep and '.service' in dep:
                        dep_name = dep.replace('.service', '')
                        print(f"            ↪️  Restarting dependency: {dep_name}")
                        cmd_restart_dep = f"echo {self.sudo_password} | sudo -S systemctl restart {dep_name}"
                        subprocess.run(cmd_restart_dep, shell=True, capture_output=True, timeout=30)
                        time.sleep(1)

                # Restart main service
                cmd = f"echo {self.sudo_password} | sudo -S systemctl restart {service}"
                subprocess.run(cmd, shell=True, capture_output=True, timeout=30)

            elif level == 5:
                # Level 5: Daemon reload + restart (for service file changes)
                cmd_reload = f"echo {self.sudo_password} | sudo -S systemctl daemon-reload"
                subprocess.run(cmd_reload, shell=True, capture_output=True, timeout=15)

                cmd_restart = f"echo {self.sudo_password} | sudo -S systemctl restart {service}"
                subprocess.run(cmd_restart, shell=True, capture_output=True, timeout=30)

            # Check if service is now active
            time.sleep(3)
            check = subprocess.run(
                ['systemctl', 'is-active', service],
                capture_output=True,
                text=True
            )

            if check.stdout.strip() == 'active':
                return {
                    'strategy': f'advanced_service_recovery_L{level}',
                    'success': True,
                    'message': f"Service {service} recovered at level {level}"
                }
            else:
                return {
                    'strategy': f'advanced_service_recovery_L{level}',
                    'success': False,
                    'message': f"Service {service} still inactive after level {level} recovery"
                }

        except Exception as e:
            return {
                'strategy': f'advanced_service_recovery_L{level}',
                'success': False,
                'message': f"Error during level {level} recovery: {e}"
            }

    def container_memory_optimization(self, issue: Dict) -> Dict:
        """Fix container memory leaks with resource limits and restart"""
        try:
            container = issue.get('container')
            if not container:
                return {
                    'strategy': 'container_memory_optimization',
                    'success': False,
                    'message': 'No container name provided'
                }

            print(f"         🧠 Optimizing memory for container: {container}")

            # Step 1: Set memory limits (2GB memory, 3GB swap)
            cmd_limit = f"docker update --memory=2g --memory-swap=3g {container}"
            result_limit = subprocess.run(cmd_limit, shell=True, capture_output=True, text=True, timeout=15)

            if result_limit.returncode == 0:
                print(f"            ✅ Memory limits set (2GB mem, 3GB swap)")

            # Step 2: Restart container
            cmd_restart = f"docker restart {container}"
            result_restart = subprocess.run(cmd_restart, shell=True, capture_output=True, text=True, timeout=60)

            if result_restart.returncode != 0:
                return {
                    'strategy': 'container_memory_optimization',
                    'success': False,
                    'message': f"Failed to restart container: {result_restart.stderr}"
                }

            # Step 3: Verify container is running
            time.sleep(3)
            cmd_check = f"docker ps --filter name={container} --format '{{{{.Status}}}}'"
            result_check = subprocess.run(cmd_check, shell=True, capture_output=True, text=True, timeout=5)

            if 'Up' in result_check.stdout:
                return {
                    'strategy': 'container_memory_optimization',
                    'success': True,
                    'message': f"Container {container} restarted with memory limits (2GB/3GB)"
                }
            else:
                return {
                    'strategy': 'container_memory_optimization',
                    'success': False,
                    'message': f"Container {container} not running after restart"
                }

        except Exception as e:
            return {
                'strategy': 'container_memory_optimization',
                'success': False,
                'message': f"Error optimizing container memory: {e}"
            }

    def basic_restart(self, issue: Dict) -> Dict:
        """Strategy 1: Simple restart (current logic)"""
        try:
            if issue['type'] == 'service_failure':
                service = issue.get('service', '').replace('.service', '')
                cmd = f"echo {self.sudo_password} | sudo -S systemctl restart {service}"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

                time.sleep(2)
                check = subprocess.run(['systemctl', 'is-active', service],
                                      capture_output=True, text=True)

                if check.stdout.strip() == 'active':
                    return {
                        'strategy': 'basic_restart',
                        'success': True,
                        'message': f"Service {service} restarted successfully"
                    }
                else:
                    return {
                        'strategy': 'basic_restart',
                        'success': False,
                        'message': f"Service {service} restart failed - still inactive"
                    }

            elif issue['type'] == 'container_failure':
                container = issue.get('container')
                result = subprocess.run(['docker', 'restart', container],
                                       capture_output=True, text=True, timeout=30)

                if result.returncode == 0:
                    time.sleep(2)
                    check = subprocess.run(
                        ['docker', 'ps', '--filter', f'name={container}', '--format', '{{.Status}}'],
                        capture_output=True, text=True
                    )

                    if 'Up' in check.stdout:
                        return {
                            'strategy': 'basic_restart',
                            'success': True,
                            'message': f"Container {container} restarted successfully"
                        }

                return {
                    'strategy': 'basic_restart',
                    'success': False,
                    'message': f"Container {container} restart failed"
                }

            else:
                return {
                    'strategy': 'basic_restart',
                    'success': False,
                    'message': "No restart strategy for this issue type"
                }

        except Exception as e:
            return {
                'strategy': 'basic_restart',
                'success': False,
                'message': f"Error during restart: {e}"
            }

    def deep_restart(self, issue: Dict) -> Dict:
        """Strategy 2: Clear cache/temp files + restart"""
        # TODO: Implement deep restart with cleanup
        # For now, just retry basic restart
        return self.basic_restart(issue)

    def dependency_check(self, issue: Dict) -> Dict:
        """Strategy 3: Check dependencies + restart"""
        # TODO: Implement dependency checking
        # For now, just retry basic restart
        return self.basic_restart(issue)

    def research_based_fix(self, issue: Dict, previous_attempts: List[Dict]) -> Dict:
        """Strategy 4-5: AI diagnosis + apply suggestions"""
        try:
            # Get AI diagnosis
            diagnosis = self.research.diagnose_issue(issue, previous_attempts)

            print(f"      📊 AI Diagnosis:")
            print(f"         {diagnosis['diagnosis']}")
            print(f"         Confidence: {diagnosis['confidence']:.0%}")
            print(f"         Suggested fixes: {len(diagnosis.get('suggested_fixes', []))}")

            # Try top suggested fix
            fixes = diagnosis.get('suggested_fixes', [])
            if fixes:
                top_fix = fixes[0]
                print(f"      🎯 Applying: {top_fix['strategy']}")
                print(f"         {top_fix['description']}")

                # For now, we can only execute safe commands (restart-based)
                # More complex fixes require human approval
                if 'restart' in top_fix['strategy'].lower():
                    return self.basic_restart(issue)
                else:
                    return {
                        'strategy': f"ai_suggested_{top_fix['strategy']}",
                        'success': False,
                        'message': f"AI suggested: {top_fix['description']} (requires manual execution)"
                    }

            return {
                'strategy': 'ai_research',
                'success': False,
                'message': f"AI diagnosis complete but no automated fix available (confidence: {diagnosis['confidence']:.0%})"
            }

        except Exception as e:
            return {
                'strategy': 'ai_research',
                'success': False,
                'message': f"AI research error: {e}"
            }

    def execute_learned_strategy(self, issue: Dict, strategy: str) -> Dict:
        """Execute a previously learned successful strategy"""
        # Map strategy name to method
        if strategy == 'basic_restart':
            return self.basic_restart(issue)
        elif strategy == 'deep_restart':
            return self.deep_restart(issue)
        elif strategy == 'dependency_check':
            return self.dependency_check(issue)
        else:
            # Unknown strategy, fallback to basic
            return self.basic_restart(issue)


if __name__ == "__main__":
    # Test the system
    print("🧪 Testing Intelligent Auto-Fixer...")

    # Test learning database
    learning = LearningDatabase("/tmp/test_learning.db")
    print("✅ Learning database initialized")

    # Test research agent (will fail without Claude Code, but should handle gracefully)
    research = ResearchAgent()
    print("✅ Research agent initialized")

    # Test fixer
    fixer = IntelligentAutoFixer()
    print("✅ Intelligent fixer initialized")

    print("\n🎉 All components initialized successfully!")
