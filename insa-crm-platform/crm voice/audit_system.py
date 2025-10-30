#!/usr/bin/env python3
"""
INSA CRM Platform - System Audit Tool
Comprehensive audit of code quality, workflows, and system health
"""
import os
import sys
import json
import sqlite3
import subprocess
import psutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Setup logging
logger = logging.getLogger(__name__)

class SystemAuditor:
    """Comprehensive system auditor"""

    def __init__(self):
        self.base_path = Path("/home/wil/insa-crm-platform/crm voice")
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'phase': 'Phase 11 Complete',
            'version': '1.0.0',
            'sections': {}
        }

    def audit_processes(self) -> Dict[str, Any]:
        """Audit running processes"""
        logger.info("Auditing Running Processes...")

        processes = {
            'workers': [],
            'backends': [],
            'other': []
        }

        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'memory_info', 'cpu_percent']):
            try:
                cmdline = proc.info['cmdline']
                if not cmdline:
                    continue

                cmdline_str = ' '.join(cmdline)

                # Workers
                if 'sizing_agent_worker.py' in cmdline_str:
                    processes['workers'].append({
                        'name': 'Sizing Agent Worker',
                        'pid': proc.info['pid'],
                        'uptime': int(datetime.now().timestamp() - proc.info['create_time']),
                        'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                        'cpu_percent': proc.info['cpu_percent'],
                        'status': 'running'
                    })
                elif 'crm_agent_worker.py' in cmdline_str:
                    processes['workers'].append({
                        'name': 'CRM Agent Worker',
                        'pid': proc.info['pid'],
                        'uptime': int(datetime.now().timestamp() - proc.info['create_time']),
                        'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                        'cpu_percent': proc.info['cpu_percent'],
                        'status': 'running'
                    })

                # Backends
                elif 'crm-backend.py' in cmdline_str:
                    processes['backends'].append({
                        'name': 'CRM Backend (Voice)',
                        'pid': proc.info['pid'],
                        'uptime': int(datetime.now().timestamp() - proc.info['create_time']),
                        'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                        'cpu_percent': proc.info['cpu_percent'],
                        'port': 5000,
                        'status': 'running'
                    })
                elif 'main.py' in cmdline_str and 'core/api' in cmdline_str:
                    processes['backends'].append({
                        'name': 'INSA CRM Core API',
                        'pid': proc.info['pid'],
                        'uptime': int(datetime.now().timestamp() - proc.info['create_time']),
                        'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                        'cpu_percent': proc.info['cpu_percent'],
                        'port': 8003,
                        'status': 'running'
                    })

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return {
            'workers': processes['workers'],
            'backends': processes['backends'],
            'total_workers': len(processes['workers']),
            'total_backends': len(processes['backends']),
            'expected_workers': 2,
            'workers_health': 'healthy' if len(processes['workers']) == 2 else 'degraded'
        }

    def audit_databases(self) -> Dict[str, Any]:
        """Audit database files"""
        logger.info("Auditing Databases...")

        dbs = {
            'message_bus': '/var/lib/insa-crm/agent_messages.db',
            'learning': '/var/lib/insa-crm/learning.db',
            'host_config': '/var/lib/host-config-agent/host_config.db'
        }

        results = {}

        for name, path in dbs.items():
            if os.path.exists(path):
                try:
                    conn = sqlite3.connect(path)
                    cursor = conn.cursor()

                    # Get table count
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = [row[0] for row in cursor.fetchall()]

                    # Get row counts
                    row_counts = {}
                    for table in tables:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        row_counts[table] = cursor.fetchone()[0]

                    # Get file size
                    size_mb = os.path.getsize(path) / 1024 / 1024

                    conn.close()

                    results[name] = {
                        'status': 'ok',
                        'path': path,
                        'size_mb': round(size_mb, 2),
                        'tables': len(tables),
                        'table_names': tables,
                        'row_counts': row_counts,
                        'total_rows': sum(row_counts.values())
                    }
                except Exception as e:
                    results[name] = {
                        'status': 'error',
                        'error': str(e)
                    }
            else:
                results[name] = {
                    'status': 'missing',
                    'path': path
                }

        return results

    def audit_code_structure(self) -> Dict[str, Any]:
        """Audit code files and structure"""
        logger.info("Auditing Code Structure...")

        code_files = {
            'week1': [
                'agent_message_bus.py',
                'orchestrator_agent.py'
            ],
            'week2': [
                'agent_handoff.py',
                'agent_worker.py',
                'sizing_agent_worker.py',
                'crm_agent_worker.py'
            ],
            'week3': [
                'orchestrator_cache.py',
                'orchestrator_agent_optimized.py',
                'agent_status_api.py'
            ],
            'integration': [
                'insa_agents.py',
                'crm-backend.py'
            ],
            'tests': [
                'test_workers.py',
                'test_e2e.py'
            ]
        }

        results = {}
        total_lines = 0

        for category, files in code_files.items():
            category_data = {
                'files': [],
                'total_lines': 0,
                'total_size_kb': 0
            }

            for filename in files:
                filepath = self.base_path / filename
                if filepath.exists():
                    with open(filepath, 'r') as f:
                        lines = len(f.readlines())

                    size_kb = filepath.stat().st_size / 1024

                    category_data['files'].append({
                        'name': filename,
                        'lines': lines,
                        'size_kb': round(size_kb, 2),
                        'status': 'ok'
                    })
                    category_data['total_lines'] += lines
                    category_data['total_size_kb'] += size_kb
                    total_lines += lines
                else:
                    category_data['files'].append({
                        'name': filename,
                        'status': 'missing'
                    })

            category_data['total_size_kb'] = round(category_data['total_size_kb'], 2)
            results[category] = category_data

        return {
            'categories': results,
            'total_lines': total_lines,
            'total_files': sum(len(cat['files']) for cat in results.values())
        }

    def audit_documentation(self) -> Dict[str, Any]:
        """Audit documentation files"""
        logger.info("Auditing Documentation...")

        doc_files = [
            '/home/wil/PHASE11_WEEK1_COMPLETE_OCT28_2025.md',
            '/home/wil/PHASE11_WEEK2_COMPLETE_OCT28_2025.md',
            '/home/wil/PHASE11_WEEK3_COMPLETE_OCT28_2025.md',
            '/home/wil/PHASE11_WEEK2_PROGRESS_OCT28_2025.md'
        ]

        results = []
        total_lines = 0

        for filepath in doc_files:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    lines = len(f.readlines())

                size_kb = os.path.getsize(filepath) / 1024

                results.append({
                    'name': os.path.basename(filepath),
                    'path': filepath,
                    'lines': lines,
                    'size_kb': round(size_kb, 2),
                    'status': 'ok'
                })
                total_lines += lines
            else:
                results.append({
                    'name': os.path.basename(filepath),
                    'status': 'missing'
                })

        return {
            'files': results,
            'total_files': len([f for f in results if f.get('status') == 'ok']),
            'total_lines': total_lines,
            'total_size_kb': sum(f.get('size_kb', 0) for f in results)
        }

    def audit_performance(self) -> Dict[str, Any]:
        """Audit system performance metrics"""
        logger.info("Auditing Performance...")

        # Test orchestrator cache
        try:
            from orchestrator_cache import get_cache
            cache = get_cache()
            cache_stats = cache.stats()

            # Test pattern matching speed
            import time
            test_query = "Necesito cotización para separador trifásico"
            start = time.time()
            result = cache.match_pattern(test_query)
            elapsed_ms = (time.time() - start) * 1000

            cache_performance = {
                'status': 'ok',
                'patterns': cache_stats['patterns'],
                'pattern_match_time_ms': round(elapsed_ms, 2),
                'cache_hit': result is not None
            }
        except Exception as e:
            cache_performance = {
                'status': 'error',
                'error': str(e)
            }

        # System resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            'cache': cache_performance,
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': round(memory.available / 1024 / 1024 / 1024, 2),
                'disk_percent': disk.percent,
                'disk_free_gb': round(disk.free / 1024 / 1024 / 1024, 2)
            }
        }

    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on audit"""
        logger.info("Generating Recommendations...")

        recommendations = []

        # Check process health
        proc_audit = self.results['sections']['processes']
        if proc_audit['workers_health'] != 'healthy':
            recommendations.append({
                'priority': 'high',
                'category': 'processes',
                'issue': f"Only {proc_audit['total_workers']}/2 workers running",
                'action': "Run start_workers.sh to start missing workers"
            })

        # Check database health
        db_audit = self.results['sections']['databases']
        for db_name, db_info in db_audit.items():
            if db_info.get('status') == 'missing':
                recommendations.append({
                    'priority': 'medium',
                    'category': 'database',
                    'issue': f"{db_name} database missing",
                    'action': f"Initialize {db_name} database"
                })

        # Performance recommendations
        perf_audit = self.results['sections']['performance']
        if perf_audit['system']['memory_percent'] > 80:
            recommendations.append({
                'priority': 'medium',
                'category': 'performance',
                'issue': f"High memory usage ({perf_audit['system']['memory_percent']}%)",
                'action': "Review memory-intensive processes"
            })

        if perf_audit['system']['disk_percent'] > 80:
            recommendations.append({
                'priority': 'medium',
                'category': 'performance',
                'issue': f"High disk usage ({perf_audit['system']['disk_percent']}%)",
                'action': "Clean up old logs and temporary files"
            })

        # Always recommend next steps
        recommendations.append({
            'priority': 'low',
            'category': 'enhancement',
            'issue': "Phase 11 complete, ready for next phase",
            'action': "Consider Phase 12: Knowledge Base Integration or Production Optimization"
        })

        return recommendations

    def run_audit(self) -> Dict[str, Any]:
        """Run complete audit"""
        print("=" * 80)
        print("🔍 INSA CRM PLATFORM - SYSTEM AUDIT")
        print("=" * 80)
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"Phase: {self.results['phase']}")
        print("=" * 80)
        print()

        # Run all audits
        self.results['sections']['processes'] = self.audit_processes()
        self.results['sections']['databases'] = self.audit_databases()
        self.results['sections']['code_structure'] = self.audit_code_structure()
        self.results['sections']['documentation'] = self.audit_documentation()
        self.results['sections']['performance'] = self.audit_performance()

        # Generate recommendations
        self.results['recommendations'] = self.generate_recommendations()

        # Calculate overall health
        health_score = self._calculate_health_score()
        self.results['overall_health'] = health_score

        return self.results

    def _calculate_health_score(self) -> Dict[str, Any]:
        """Calculate overall system health score"""
        score = 100
        issues = []

        # Process health (30 points)
        if self.results['sections']['processes']['workers_health'] != 'healthy':
            score -= 30
            issues.append('Workers not running')

        # Database health (20 points)
        db_missing = sum(1 for db in self.results['sections']['databases'].values()
                        if db.get('status') == 'missing')
        if db_missing > 0:
            score -= (db_missing * 10)
            issues.append(f'{db_missing} databases missing')

        # Performance (20 points)
        perf = self.results['sections']['performance']['system']
        if perf['memory_percent'] > 80:
            score -= 10
            issues.append('High memory usage')
        if perf['disk_percent'] > 80:
            score -= 10
            issues.append('High disk usage')

        # Code completeness (15 points)
        code = self.results['sections']['code_structure']
        missing_files = sum(1 for cat in code['categories'].values()
                          for f in cat['files'] if f.get('status') == 'missing')
        if missing_files > 0:
            score -= (missing_files * 3)
            issues.append(f'{missing_files} code files missing')

        # Documentation (15 points)
        doc = self.results['sections']['documentation']
        missing_docs = sum(1 for f in doc['files'] if f.get('status') == 'missing')
        if missing_docs > 0:
            score -= (missing_docs * 5)
            issues.append(f'{missing_docs} documentation files missing')

        # Determine status
        if score >= 90:
            status = 'excellent'
        elif score >= 75:
            status = 'good'
        elif score >= 60:
            status = 'fair'
        else:
            status = 'poor'

        return {
            'score': max(0, score),
            'status': status,
            'issues': issues
        }

    def print_summary(self):
        """Print audit summary"""
        print("\n" + "=" * 80)
        print("📊 AUDIT SUMMARY")
        print("=" * 80)

        # Overall Health
        health = self.results['overall_health']
        print(f"\n🏥 Overall Health: {health['score']}/100 ({health['status'].upper()})")
        if health['issues']:
            print("   Issues:")
            for issue in health['issues']:
                print(f"   - {issue}")

        # Processes
        print(f"\n🔄 Processes:")
        proc = self.results['sections']['processes']
        print(f"   Workers: {proc['total_workers']}/{proc['expected_workers']} ({proc['workers_health']})")
        for worker in proc['workers']:
            print(f"   - {worker['name']}: PID {worker['pid']}, {worker['memory_mb']:.1f} MB")

        # Databases
        print(f"\n💾 Databases:")
        for name, db in self.results['sections']['databases'].items():
            if db['status'] == 'ok':
                print(f"   - {name}: {db['total_rows']} rows, {db['size_mb']} MB")
            else:
                print(f"   - {name}: {db['status'].upper()}")

        # Code
        print(f"\n📝 Code:")
        code = self.results['sections']['code_structure']
        print(f"   Total Lines: {code['total_lines']:,}")
        print(f"   Total Files: {code['total_files']}")
        for cat_name, cat_data in code['categories'].items():
            print(f"   - {cat_name}: {cat_data['total_lines']:,} lines ({len(cat_data['files'])} files)")

        # Documentation
        print(f"\n📚 Documentation:")
        doc = self.results['sections']['documentation']
        print(f"   Total Files: {doc['total_files']}")
        print(f"   Total Lines: {doc['total_lines']:,}")

        # Performance
        print(f"\n⚡ Performance:")
        perf = self.results['sections']['performance']
        if perf['cache']['status'] == 'ok':
            print(f"   Cache: {perf['cache']['patterns']} patterns, {perf['cache']['pattern_match_time_ms']:.2f}ms")
        sys_perf = perf['system']
        print(f"   CPU: {sys_perf['cpu_percent']}%")
        print(f"   Memory: {sys_perf['memory_percent']}% ({sys_perf['memory_available_gb']} GB free)")
        print(f"   Disk: {sys_perf['disk_percent']}% ({sys_perf['disk_free_gb']} GB free)")

        # Recommendations
        print(f"\n💡 Recommendations ({len(self.results['recommendations'])}):")
        for rec in self.results['recommendations']:
            priority_icon = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(rec['priority'], '⚪')
            print(f"   {priority_icon} [{rec['priority'].upper()}] {rec['issue']}")
            print(f"      → {rec['action']}")

        print("\n" + "=" * 80)
        print("✅ Audit Complete")
        print("=" * 80)

    def save_report(self, filepath: str = None):
        """Save audit report to JSON file"""
        if filepath is None:
            filepath = f"/home/wil/SYSTEM_AUDIT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        logger.info(f"Report saved: {filepath}")
        return filepath


if __name__ == '__main__':
    auditor = SystemAuditor()
    results = auditor.run_audit()
    auditor.print_summary()
    report_path = auditor.save_report()

    print(f"\n📄 Full report: {report_path}")
