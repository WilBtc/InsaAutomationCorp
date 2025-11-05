#!/usr/bin/env python3
"""
System Knowledge RAG - Documentation & Context Retrieval
Provides system awareness to autonomous agents

Created: November 1, 2025
Author: Insa Automation Corp
Purpose: Give agents access to CLAUDE.md, README files, git history, service configs
"""

import os
import re
import subprocess
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json


class SystemKnowledgeRAG:
    """Query system documentation and configuration for agent context"""

    def __init__(self):
        self.docs_paths = {
            'claude_md': '/home/wil/.claude/CLAUDE.md',
            'main_readme': '/home/wil/README.md',
            'automation_readme': '/home/wil/automation/README.md',
            'insa_crm_readme': '/home/wil/platforms/insa-crm/README.md',
            'orchestrator_docs': '/home/wil/automation/agents/orchestrator/*.md'
        }

        self.system_paths = {
            'platform_root': '/home/wil/platforms/',
            'automation_root': '/home/wil/automation/',
            'services_root': '/etc/systemd/system/',
            'old_platform': '/home/wil/insa-crm-platform/',  # Deprecated
        }

        # Cache for frequently accessed docs
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes

    def query(self, issue: Dict) -> Dict[str, str]:
        """
        Query relevant documentation based on issue type

        Args:
            issue: {
                'type': 'service_failure',
                'source': 'systemd',
                'service': 'insa-crm.service',
                'message': 'Service failed...'
            }

        Returns:
            {
                'system_overview': 'Platform structure...',
                'service_config': 'Service patterns...',
                'recent_changes': 'Git history...',
                'known_patterns': 'Similar issues...',
                'platform_paths': 'Directory structure...'
            }
        """
        context = {}

        # 1. System overview from CLAUDE.md
        context['system_overview'] = self.get_system_overview(issue)

        # 2. Service configuration patterns
        if issue['type'] in ['service_failure', 'port_conflict']:
            context['service_config'] = self.get_service_patterns(issue)
        else:
            context['service_config'] = ''

        # 3. Recent platform changes from git
        context['recent_changes'] = self.get_recent_changes(issue)

        # 4. Platform path structure
        context['platform_paths'] = self.get_platform_structure()

        # 5. Known patterns (from docs and patterns)
        context['known_patterns'] = self.get_known_patterns(issue)

        return context

    def get_system_overview(self, issue: Dict) -> str:
        """Extract relevant sections from CLAUDE.md"""
        claude_md = self._read_cached(self.docs_paths['claude_md'])

        if not claude_md:
            return "System documentation not available"

        # Extract key sections
        sections = []

        # Server info
        server_section = self._extract_section(claude_md, r'# iac1 Server.*?(?=##)', flags=re.DOTALL)
        if server_section:
            sections.append("SERVER INFO:\n" + server_section[:500])

        # Active systems
        active_section = self._extract_section(claude_md, r'## ⚡ ACTIVE SYSTEMS.*?(?=##)', flags=re.DOTALL)
        if active_section:
            sections.append("\nACTIVE SERVICES:\n" + active_section[:800])

        # Quick access paths
        paths_section = self._extract_section(claude_md, r'## 🔑 QUICK ACCESS.*?(?=##)', flags=re.DOTALL)
        if paths_section:
            sections.append("\nKEY PATHS:\n" + paths_section[:400])

        return '\n'.join(sections)

    def get_service_patterns(self, issue: Dict) -> str:
        """Get service configuration patterns and common issues"""
        service_name = issue.get('service', '')

        patterns = []

        # Check if service file exists
        service_file = f"/etc/systemd/system/{service_name}"
        if os.path.exists(service_file):
            with open(service_file, 'r') as f:
                config = f.read()

            # Extract key configs
            working_dir = self._extract_config(config, 'WorkingDirectory')
            exec_start = self._extract_config(config, 'ExecStart')

            patterns.append(f"SERVICE CONFIG ({service_name}):")
            if working_dir:
                # Check if path exists
                exists = "✅ EXISTS" if os.path.exists(working_dir) else "❌ MISSING"
                patterns.append(f"  WorkingDirectory: {working_dir} ({exists})")
            if exec_start:
                exec_path = exec_start.split()[0] if exec_start else ''
                exists = "✅ EXISTS" if os.path.exists(exec_path) else "❌ MISSING"
                patterns.append(f"  ExecStart: {exec_start[:80]}... ({exists})")

        # Add known platform paths
        patterns.append("\nKNOWN PLATFORM PATHS:")
        patterns.append(f"  Current: {self.system_paths['platform_root']}")
        patterns.append(f"  Old (DEPRECATED): {self.system_paths['old_platform']}")
        patterns.append("  Migration: insa-crm-platform → platforms/insa-crm (Oct 2025)")

        return '\n'.join(patterns)

    def get_recent_changes(self, issue: Dict) -> str:
        """Query git for recent platform changes"""
        try:
            # Get recent commits related to platform structure
            result = subprocess.run(
                ['git', 'log', '--since=14 days', '--oneline', '--all',
                 '--grep=platform\\|consolidat\\|path\\|service', '-i'],
                cwd='/home/wil',
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0 and result.stdout:
                commits = result.stdout.strip().split('\n')[:5]  # Last 5 relevant commits

                changes = ["RECENT PLATFORM CHANGES (Last 14 days):"]
                for commit in commits:
                    changes.append(f"  • {commit}")

                return '\n'.join(changes)

        except Exception as e:
            pass

        return "No recent platform changes detected"

    def get_platform_structure(self) -> str:
        """Document current platform directory structure"""
        structure = ["PLATFORM DIRECTORY STRUCTURE:"]

        # Check key directories
        dirs_to_check = [
            ('/home/wil/platforms/insa-crm', 'Current INSA CRM platform'),
            ('/home/wil/platforms/insa-crm/core', 'Core backend services'),
            ('/home/wil/automation/agents', 'Autonomous agents'),
            ('/home/wil/insa-crm-platform', 'OLD LOCATION (deprecated)'),
        ]

        for path, description in dirs_to_check:
            exists = "✅" if os.path.exists(path) else "❌"
            structure.append(f"  {exists} {path}")
            structure.append(f"     ({description})")

        return '\n'.join(structure)

    def get_known_patterns(self, issue: Dict) -> str:
        """Return known error patterns and solutions"""
        patterns = []

        issue_type = issue.get('type', '')
        message = issue.get('message', '').lower()

        # Path-related issues
        if 'no such file' in message or 'not found' in message or 'exit.*203' in message:
            patterns.append("PATTERN: Missing File/Path (exit code 203)")
            patterns.append("  Common causes:")
            patterns.append("    1. Platform consolidation (insa-crm-platform → platforms/insa-crm)")
            patterns.append("    2. Service file points to old paths")
            patterns.append("    3. Symlinks broken after directory moves")
            patterns.append("  Solution:")
            patterns.append("    - Update service WorkingDirectory and ExecStart paths")
            patterns.append("    - Check /etc/systemd/system/<service>.service")
            patterns.append("    - Replace old paths with new platform structure")

        # Port conflicts
        if 'address already in use' in message or 'bind' in message:
            patterns.append("PATTERN: Port Conflict (EADDRINUSE)")
            patterns.append("  Common causes:")
            patterns.append("    1. Stale process holding port")
            patterns.append("    2. Service restart without killing old process")
            patterns.append("    3. Multiple services configured for same port")
            patterns.append("  Solution:")
            patterns.append("    - Find process: lsof -i :<port> or ss -tlnp | grep <port>")
            patterns.append("    - Kill stale process: kill <PID>")
            patterns.append("    - Verify port free before restart")

        # Service failures
        if issue_type == 'service_failure':
            patterns.append("PATTERN: Service Failure Checklist")
            patterns.append("  1. Check service file paths exist")
            patterns.append("  2. Verify dependencies (After= clauses)")
            patterns.append("  3. Check for port conflicts")
            patterns.append("  4. Review recent platform changes")
            patterns.append("  5. Validate Python/binary executables exist")

        if patterns:
            return '\n'.join(patterns)

        return "No specific patterns matched"

    def _read_cached(self, path: str) -> Optional[str]:
        """Read file with caching"""
        cache_key = f"file:{path}"

        # Check cache
        if cache_key in self._cache:
            cached_time, cached_content = self._cache[cache_key]
            if (datetime.now() - cached_time).seconds < self._cache_ttl:
                return cached_content

        # Read file
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    content = f.read()

                # Cache it
                self._cache[cache_key] = (datetime.now(), content)
                return content
        except Exception as e:
            pass

        return None

    def _extract_section(self, text: str, pattern: str, flags=0) -> Optional[str]:
        """Extract section from text using regex"""
        match = re.search(pattern, text, flags)
        if match:
            return match.group(0).strip()
        return None

    def _extract_config(self, service_config: str, key: str) -> Optional[str]:
        """Extract configuration value from service file"""
        pattern = f'^{key}=(.+)$'
        match = re.search(pattern, service_config, re.MULTILINE)
        if match:
            return match.group(1).strip()
        return None

    def format_for_ai(self, knowledge: Dict[str, str]) -> str:
        """Format knowledge dictionary for AI prompt"""
        sections = []

        if knowledge.get('system_overview'):
            sections.append("=== SYSTEM ARCHITECTURE ===")
            sections.append(knowledge['system_overview'])
            sections.append("")

        if knowledge.get('platform_paths'):
            sections.append("=== PLATFORM STRUCTURE ===")
            sections.append(knowledge['platform_paths'])
            sections.append("")

        if knowledge.get('service_config'):
            sections.append("=== SERVICE CONFIGURATION ===")
            sections.append(knowledge['service_config'])
            sections.append("")

        if knowledge.get('recent_changes'):
            sections.append("=== RECENT CHANGES ===")
            sections.append(knowledge['recent_changes'])
            sections.append("")

        if knowledge.get('known_patterns'):
            sections.append("=== KNOWN PATTERNS & SOLUTIONS ===")
            sections.append(knowledge['known_patterns'])
            sections.append("")

        return '\n'.join(sections)


# Test function
if __name__ == "__main__":
    print("Testing SystemKnowledgeRAG...")

    rag = SystemKnowledgeRAG()

    # Test with service failure issue
    test_issue = {
        'type': 'service_failure',
        'source': 'systemd',
        'service': 'integrated-healing-agent.service',
        'message': 'Main process exited, code=exited, status=203/EXEC'
    }

    knowledge = rag.query(test_issue)
    formatted = rag.format_for_ai(knowledge)

    print("\n" + "="*80)
    print("RAG QUERY RESULT:")
    print("="*80)
    print(formatted)
    print("="*80)
