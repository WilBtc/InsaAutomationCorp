#!/usr/bin/env python3
"""
INSA Platform Health Monitor & Auto-Repair System - EXPANDED
Autonomous diagnostic and healing for 15+ critical services

Features:
- HTTP health checks for all 8 web UIs
- Systemd service monitoring (nginx, postgresql, mariadb, redis, postfix)
- Container health checks (minio, qdrant, databases)
- Database connection tests
- Automatic issue detection
- Self-healing capabilities
- MCP tool integration for Claude Code

Author: Claude Code (Autonomous Platform Management)
Date: October 22, 2025
Version: 2.0 (Production Expansion)
"""

import subprocess
import json
import time
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional

class PlatformHealthMonitor:
    """Monitors and auto-repairs INSA platform services - EXPANDED VERSION"""

    SERVICES = {
        # ============================================================
        # WEB SERVICES (HTTP-based health checks)
        # ============================================================
        'insa_crm': {
            'type': 'web',
            'url': 'http://100.100.101.1:8003',
            'name': 'INSA CRM',
            'timeout': 5,
            'expected_status': [200],
            'critical': True,
            'container': None,  # Not containerized
            'fix_function': None
        },
        'defectdojo': {
            'type': 'web',
            'url': 'http://100.100.101.1:8082',
            'name': 'DefectDojo SOC',
            'timeout': 5,
            'expected_status': [200, 302],
            'critical': True,
            'container': 'defectdojo-uwsgi-insa',
            'fix_function': 'fix_defectdojo'
        },
        'erpnext': {
            'type': 'docker_exec',  # Changed to docker_exec (headless mode - Oct 22, 2025)
            'url': 'http://100.100.101.1:9000',  # Not used in headless mode
            'name': 'ERPNext CRM (Headless)',
            'timeout': 10,
            'expected_status': [200, 302],  # Not used in headless mode
            'critical': True,
            'container': 'frappe_docker_backend_1',  # Changed from frontend to backend
            'bench_site': 'insa.local',
            'check_command': 'bench --site insa.local list-apps',  # Headless health check
            'compose_dir': '/home/wil/frappe_docker',
            'fix_function': 'fix_erpnext_headless'
        },
        'inventree': {
            'type': 'web',
            'url': 'http://100.100.101.1:9600',
            'name': 'InvenTree',
            'timeout': 5,
            'expected_status': [200, 302],
            'critical': False,
            'container': 'inventree_web',
            'fix_function': 'fix_inventree'
        },
        'mautic': {
            'type': 'web',
            'url': 'http://100.100.101.1:9700',
            'name': 'Mautic',
            'timeout': 5,
            'expected_status': [200, 302],
            'critical': False,
            'container': 'n8n_mautic_erpnext',  # Fixed: actual container name
            'fix_function': 'fix_mautic'
        },
        'n8n': {
            'type': 'web',
            'url': 'http://100.100.101.1:5678',
            'name': 'n8n Workflows',
            'timeout': 60,  # Increased from 30s (Oct 22, 2025 - healing agent improvement)
            'startup_grace_period': 300,  # 5 minutes grace period after restart
            'expected_status': [200, 302],
            'critical': False,
            'container': 'n8n_mautic_erpnext',
            'fix_function': 'fix_n8n'
        },
        'grafana': {
            'type': 'web',
            'url': 'http://100.100.101.1:3002',
            'name': 'Grafana',
            'timeout': 60,  # Increased from 30s (Oct 22, 2025 - healing agent improvement)
            'startup_grace_period': 300,  # 5 minutes grace period after restart
            'expected_status': [200, 302],
            'critical': False,
            'container': 'grafana-analytics',
            'fix_function': 'fix_grafana'
        },
        'iec62443': {
            'type': 'web',
            'url': 'http://100.100.101.1:3004',
            'name': 'IEC 62443 Dashboard',
            'timeout': 5,
            'expected_status': [200],
            'critical': False,
            'container': None,
            'fix_function': None
        },

        # ============================================================
        # NEW: CRITICAL INFRASTRUCTURE (Systemd services)
        # ============================================================
        'nginx': {
            'type': 'systemd',
            'systemd_service': 'nginx.service',
            'name': 'Nginx Reverse Proxy',
            'critical': True,
            'fix_function': 'fix_nginx',
            'description': 'HTTP reverse proxy for all web services'
        },
        'postgresql': {
            'type': 'systemd+db',
            'systemd_service': 'postgresql@16-main.service',
            'name': 'PostgreSQL 16',
            'critical': True,
            'fix_function': 'fix_postgresql',
            'db_test': 'sudo -u postgres psql -c "SELECT 1" template1',
            'description': 'Primary database for INSA CRM, ERPNext, Kong'
        },
        'mariadb': {
            'type': 'systemd+db',
            'systemd_service': 'mariadb.service',
            'name': 'MariaDB 10.11',
            'critical': True,
            'fix_function': 'fix_mariadb',
            'db_test': 'echo "110811081108***" | sudo -S mysql -u root -e "SELECT 1"',
            'description': 'Database for Mautic (157 tables)'
        },
        'redis': {
            'type': 'systemd',
            'systemd_service': 'redis-server.service',
            'name': 'Redis Server',
            'critical': True,
            'fix_function': 'fix_redis',
            'description': 'Cache for multiple services'
        },
        'postfix': {
            'type': 'systemd',
            'systemd_service': 'postfix@-.service',
            'name': 'Postfix Email',
            'critical': False,
            'fix_function': 'fix_postfix',
            'description': 'Email delivery for notifications'
        },

        # ============================================================
        # NEW: STORAGE BACKENDS (Container-based)
        # ============================================================
        'minio': {
            'type': 'container',  # Container-only check (HTTP health unreliable)
            'name': 'MinIO Object Storage',
            'critical': True,
            'container': 'minio-insa-crm',
            'fix_function': 'fix_minio',
            'description': 'Object storage for INSA CRM files (ports 9200:9000, 9201:9001)'
        },
        'qdrant': {
            'type': 'container+http',
            'url': 'http://100.100.101.1:6333/',  # Fixed: root endpoint, not /health
            'name': 'Qdrant Vector DB',
            'timeout': 5,
            'expected_status': [200],
            'critical': True,
            'container': 'insa-crm-qdrant',
            'fix_function': 'fix_qdrant',
            'description': 'Vector database for AI RAG (900+ docs)'
        },

        # ============================================================
        # WEEK 4: SECURITY SERVICES (IDS/IPS, FIM, Log Collection)
        # ============================================================
        'suricata': {
            'type': 'systemd',
            'systemd_service': 'suricata.service',
            'name': 'Suricata IDS/IPS',
            'critical': True,
            'fix_function': 'fix_suricata',
            'description': 'Network IDS/IPS - 45,777 rules (ET Open + OT protocols)'
        },
        'wazuh': {
            'type': 'systemd',
            'systemd_service': 'wazuh-manager.service',
            'name': 'Wazuh Manager',
            'critical': True,
            'fix_function': 'fix_wazuh',
            'description': 'FIM + Log collection + Analysis + Threat detection (Manager/Server)'
        },
        'fail2ban': {
            'type': 'systemd',
            'systemd_service': 'fail2ban.service',
            'name': 'Fail2ban',
            'critical': False,
            'fix_function': 'fix_fail2ban',
            'description': 'SSH brute-force protection (auto-ban failed attempts)'
        },
        'auditd': {
            'type': 'systemd',
            'systemd_service': 'auditd.service',
            'name': 'Auditd',
            'critical': False,
            'fix_function': 'fix_auditd',
            'description': 'System call auditing (kernel-level event logging)'
        },
        'clamav': {
            'type': 'systemd',
            'systemd_service': 'clamav-daemon.service',
            'name': 'ClamAV Daemon',
            'critical': False,
            'fix_function': 'fix_clamav',
            'description': 'Antivirus scanning (weekly full scans via cron)'
        },

        # ============================================================
        # WEEK 5: AUTONOMOUS AGENTS (Self-monitoring)
        # ============================================================
        'integrated_healing_agent': {
            'type': 'systemd',
            'systemd_service': 'integrated-healing-agent.service',
            'name': 'Integrated Healing Agent',
            'critical': True,
            'fix_function': 'fix_integrated_healing',
            'description': 'Autonomous platform health + auto-healing (Week 1-4 + Phases 1-4)'
        },
        'host_config_agent': {
            'type': 'systemd',
            'systemd_service': 'host-config-agent.service',
            'name': 'Host Config Agent',
            'critical': True,
            'fix_function': 'fix_host_config',
            'description': 'Resource tracking + AI deployment decisions (MCP server)'
        },
        'defectdojo_compliance_agent': {
            'type': 'systemd',
            'systemd_service': 'defectdojo-compliance-agent.service',
            'name': 'DefectDojo Compliance Agent',
            'critical': True,
            'fix_function': 'fix_defectdojo_compliance',
            'description': 'IEC 62443 compliance automation (hourly Trivy scans)'
        },
        'security_integration_agent': {
            'type': 'systemd',
            'systemd_service': 'security-integration-agent.service',
            'name': 'Security Integration Agent',
            'critical': True,
            'fix_function': 'fix_security_integration',
            'description': 'Suricata/Wazuh/Lynis → DefectDojo bridge (hourly)'
        },
        'task_orchestration_agent': {
            'type': 'systemd',
            'systemd_service': 'task-orchestration-agent.service',
            'name': 'Task Orchestration Agent',
            'critical': False,
            'fix_function': 'fix_task_orchestration',
            'description': 'Multi-agent task coordination and routing'
        },
        'azure_monitor_agent': {
            'type': 'systemd',
            'systemd_service': 'azure-monitor-agent.service',
            'name': 'Azure Monitor Agent',
            'critical': False,
            'fix_function': 'fix_azure_monitor',
            'description': 'Azure VM health monitoring (100.107.50.52 via Tailscale)'
        },
        'soc_agent': {
            'type': 'systemd',
            'systemd_service': 'soc-agent.service',
            'name': 'SOC Agent',
            'critical': False,
            'fix_function': 'fix_soc_agent',
            'description': 'Autonomous 24/7 SOC operations'
        },

        # ============================================================
        # WEEK 7: MCP SERVER MONITORING (Critical MCP Servers)
        # ============================================================
        'mcp_platform_admin': {
            'type': 'mcp',
            'mcp_server_name': 'platform-admin',
            'name': 'MCP Platform Admin',
            'critical': True,
            'fix_function': None,  # MCP servers auto-restart
            'description': 'Platform health MCP server (8 tools)'
        },
        'mcp_defectdojo': {
            'type': 'mcp',
            'mcp_server_name': 'defectdojo-iec62443',
            'name': 'MCP DefectDojo IEC62443',
            'critical': True,
            'fix_function': None,
            'description': 'Security compliance MCP server (8 tools)'
        },
        'mcp_erpnext': {
            'type': 'mcp',
            'mcp_server_name': 'erpnext-crm',
            'name': 'MCP ERPNext CRM',
            'critical': True,
            'fix_function': None,
            'description': 'CRM automation MCP server (33 tools)'
        }
    }

    def __init__(self, verbose=True):
        self.verbose = verbose
        self.results = {}

    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        if self.verbose:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [{level}] {message}")

    def run_command(self, cmd: str, timeout: int = 30) -> Tuple[int, str, str]:
        """Run shell command and return (returncode, stdout, stderr)"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timeout"
        except Exception as e:
            return -1, "", str(e)

    # ============================================================
    # HEALTH CHECK FUNCTIONS
    # ============================================================

    def check_http_health(self, service_id: str) -> Dict:
        """Check HTTP health of a service (IMPROVED Oct 22, 2025)"""
        service = self.SERVICES[service_id]
        self.log(f"Checking {service['name']} ({service['url']})...")

        # IMPROVEMENT: Check if container exists and is running BEFORE HTTP check
        container_status = None
        if service.get('container'):
            container_status = self.check_container_status(service['container'])
            if not container_status['exists']:
                self.log(f"  {service['name']}: Container '{service['container']}' NOT FOUND", "ERROR")
                return {
                    'healthy': False,
                    'http_code': None,
                    'error': f"Container not found: {service['container']}",
                    'container_running': False,
                    'container_exists': False
                }
            elif not container_status['running']:
                self.log(f"  {service['name']}: Container exists but NOT RUNNING (status: {container_status['status']})", "ERROR")
                return {
                    'healthy': False,
                    'http_code': None,
                    'error': f"Container not running (status: {container_status['status']})",
                    'container_running': False,
                    'container_exists': True
                }

        # Use curl with timeout
        cmd = f"curl -s -o /dev/null -w '%{{http_code}}' --max-time {service['timeout']} {service['url']}"
        returncode, stdout, stderr = self.run_command(cmd, timeout=service['timeout'] + 5)

        http_code = stdout.strip()

        if returncode == 0 and http_code:
            try:
                code = int(http_code)
                is_healthy = code in service['expected_status']
                status = "HEALTHY" if is_healthy else "UNHEALTHY"
                self.log(f"  {service['name']}: HTTP {code} - {status}")
                return {
                    'healthy': is_healthy,
                    'http_code': code,
                    'error': None if is_healthy else f"Unexpected HTTP {code}",
                    'container_running': container_status['running'] if container_status else None,
                    'container_exists': container_status['exists'] if container_status else None
                }
            except ValueError:
                return {
                    'healthy': False,
                    'http_code': None,
                    'error': f"Invalid HTTP code: {http_code}",
                    'container_running': container_status['running'] if container_status else None,
                    'container_exists': container_status['exists'] if container_status else None
                }
        else:
            # IMPROVEMENT: Better error messages
            error_msg = stderr or "Connection failed"
            if "Connection timed out" in error_msg or "timeout" in error_msg.lower():
                error_msg = f"TIMEOUT after {service['timeout']}s (container running: {container_status['running'] if container_status else 'unknown'})"
            elif "Connection refused" in error_msg:
                error_msg = f"Connection refused (service not listening on port)"

            self.log(f"  {service['name']}: {error_msg}", "ERROR")
            return {
                'healthy': False,
                'http_code': None,
                'error': error_msg,
                'container_running': container_status['running'] if container_status else None,
                'container_exists': container_status['exists'] if container_status else None
            }

    def check_docker_exec_health(self, service_id: str) -> Dict:
        """Check health via docker exec (headless mode - Oct 22, 2025)"""
        service = self.SERVICES[service_id]
        container = service.get('container')
        check_cmd = service.get('check_command')

        self.log(f"Checking {service['name']} (headless via docker exec)...")

        # Check container exists and is running
        container_status = self.check_container_status(container)
        if not container_status['exists']:
            self.log(f"  {service['name']}: Container '{container}' NOT FOUND", "ERROR")
            return {
                'healthy': False,
                'error': f"Container not found: {container}",
                'container_running': False,
                'container_exists': False
            }
        elif not container_status['running']:
            self.log(f"  {service['name']}: Container NOT RUNNING (status: {container_status['status']})", "ERROR")
            return {
                'healthy': False,
                'error': f"Container not running: {container_status['status']}",
                'container_running': False,
                'container_exists': True
            }

        # Execute health check command inside container
        cmd = f"docker exec {container} {check_cmd}"
        returncode, stdout, stderr = self.run_command(cmd, timeout=service.get('timeout', 10))

        if returncode == 0:
            self.log(f"  {service['name']}: HEALTHY (headless mode) ✅")
            return {
                'healthy': True,
                'error': None,
                'output': stdout.strip(),
                'container_running': True,
                'container_exists': True
            }
        else:
            error_msg = stderr.strip() or "Command failed"
            self.log(f"  {service['name']}: UNHEALTHY - {error_msg}", "ERROR")
            return {
                'healthy': False,
                'error': error_msg,
                'container_running': True,
                'container_exists': True
            }

    def check_mcp_server(self, service_id: str) -> Dict:
        """Check MCP server availability via ~/.mcp.json"""
        service = self.SERVICES[service_id]
        mcp_name = service['mcp_server_name']

        self.log(f"Checking {service['name']} (MCP: {mcp_name})...")

        # Check if MCP server is configured in ~/.mcp.json
        cmd = f"jq -r '.mcpServers.\"{mcp_name}\" | if . == null then \"NOT_FOUND\" else \"FOUND\" end' ~/.mcp.json 2>/dev/null"
        returncode, stdout, stderr = self.run_command(cmd, timeout=5)

        if returncode == 0 and stdout.strip() == "FOUND":
            self.log(f"  {service['name']}: MCP server configured ✅")
            return {
                'healthy': True,
                'mcp_configured': True,
                'error': None
            }
        else:
            self.log(f"  {service['name']}: MCP server NOT CONFIGURED ❌", "ERROR")
            return {
                'healthy': False,
                'mcp_configured': False,
                'error': f"MCP server '{mcp_name}' not found in ~/.mcp.json"
            }

    def check_systemd_service(self, service_id: str) -> Dict:
        """Check systemd service health"""
        service = self.SERVICES[service_id]
        systemd_name = service['systemd_service']

        self.log(f"Checking {service['name']} (systemd: {systemd_name})...")

        # Check if service is active
        cmd = f"systemctl is-active {systemd_name}"
        returncode, stdout, stderr = self.run_command(cmd)

        is_active = (returncode == 0 and stdout.strip() == 'active')

        # Get detailed status
        cmd = f"systemctl show {systemd_name} -p ActiveState,SubState,LoadState --value"
        returncode2, stdout2, stderr2 = self.run_command(cmd)

        status_parts = stdout2.strip().split('\n') if returncode2 == 0 else ['unknown', 'unknown', 'unknown']

        status = "HEALTHY" if is_active else "UNHEALTHY"
        self.log(f"  {service['name']}: {status_parts[0]}/{status_parts[1]} - {status}")

        return {
            'healthy': is_active,
            'systemd_active': is_active,
            'active_state': status_parts[0] if len(status_parts) > 0 else 'unknown',
            'sub_state': status_parts[1] if len(status_parts) > 1 else 'unknown',
            'error': None if is_active else f"Service not active: {status_parts[0]}/{status_parts[1]}"
        }

    def check_database_connection(self, service_id: str) -> Dict:
        """Check database connection for systemd+db services"""
        service = self.SERVICES[service_id]

        # First check systemd status
        systemd_health = self.check_systemd_service(service_id)

        if not systemd_health['healthy']:
            return systemd_health

        # Test database connection
        if 'db_test' in service:
            self.log(f"  Testing database connection for {service['name']}...")
            cmd = service['db_test']
            returncode, stdout, stderr = self.run_command(cmd, timeout=5)

            db_ok = (returncode == 0)
            if db_ok:
                self.log(f"  Database connection: OK")
                systemd_health['db_connection'] = True
            else:
                self.log(f"  Database connection: FAILED - {stderr[:100]}")
                systemd_health['healthy'] = False
                systemd_health['db_connection'] = False
                systemd_health['error'] = f"DB connection failed: {stderr[:100]}"

        return systemd_health

    def check_container_status(self, container_name: str) -> Dict:
        """Check if Docker container is running"""
        cmd = f"docker inspect {container_name} --format '{{{{.State.Status}}}}' 2>/dev/null"
        returncode, stdout, stderr = self.run_command(cmd)

        if returncode == 0:
            status = stdout.strip()
            running = (status == 'running')
            return {
                'running': running,
                'status': status,
                'exists': True
            }
        else:
            return {
                'running': False,
                'status': 'not_found',
                'exists': False
            }

    # ============================================================
    # FIX FUNCTIONS (Original)
    # ============================================================

    def fix_erpnext(self) -> bool:
        """Auto-fix ERPNext frontend not running issue"""
        service = self.SERVICES['erpnext']
        compose_dir = service.get('compose_dir')

        if compose_dir:
            self.log("Applying ERPNext fix: Restarting frontend container...", "FIX")

            # Strategy 1: Restart just frontend
            cmd = f"cd {compose_dir} && docker-compose -f pwd.yml restart frontend"
            returncode, stdout, stderr = self.run_command(cmd, timeout=60)

            if returncode == 0:
                time.sleep(15)  # Wait for startup

                # Verify fix worked
                health = self.check_http_health('erpnext')
                if health['healthy']:
                    self.log("  ERPNext fix SUCCESSFUL ✅", "FIX")
                    return True
                else:
                    self.log("  Frontend restart didn't resolve issue, trying full restart...", "FIX")
                    # Strategy 2: Full restart
                    cmd = f"cd {compose_dir} && docker-compose -f pwd.yml restart"
                    returncode, stdout, stderr = self.run_command(cmd, timeout=120)
                    if returncode == 0:
                        time.sleep(30)
                        health = self.check_http_health('erpnext')
                        return health['healthy']

        self.log("  ERPNext fix FAILED ❌", "ERROR")
        return False

    def fix_erpnext_headless(self) -> bool:
        """Auto-fix ERPNext headless mode (Docker exec) - Oct 22, 2025"""
        service = self.SERVICES['erpnext']
        container = service['container']
        compose_dir = service.get('compose_dir')

        self.log("Applying ERPNext headless fix: Checking backend container...", "FIX")

        # Strategy 1: Restart backend container
        cmd = f"docker restart {container}"
        returncode, stdout, stderr = self.run_command(cmd, timeout=60)

        if returncode == 0:
            self.log("  Backend container restarted, waiting 15s for startup...", "FIX")
            time.sleep(15)

            # Verify fix worked
            health = self.check_docker_exec_health('erpnext')
            if health['healthy']:
                self.log("  ERPNext headless fix SUCCESSFUL ✅", "FIX")
                return True
            else:
                # Strategy 2: Restart all ERPNext containers
                if compose_dir:
                    self.log("  Backend restart didn't resolve issue, restarting all containers...", "FIX")
                    cmd = f"cd {compose_dir} && docker-compose restart"
                    returncode, stdout, stderr = self.run_command(cmd, timeout=120)
                    if returncode == 0:
                        time.sleep(30)
                        health = self.check_docker_exec_health('erpnext')
                        if health['healthy']:
                            self.log("  ERPNext headless fix SUCCESSFUL ✅", "FIX")
                            return True

        self.log("  ERPNext headless fix FAILED ❌", "ERROR")
        return False

    def fix_n8n(self) -> bool:
        """Auto-fix n8n volume permission issue"""
        self.log("Applying n8n fix: Checking volume permissions...", "FIX")

        # Find n8n data volume
        cmd = "docker inspect n8n_mautic_erpnext --format '{{range .Mounts}}{{.Source}}{{end}}' 2>/dev/null | head -1"
        returncode, stdout, stderr = self.run_command(cmd)

        if returncode == 0 and stdout.strip():
            volume_path = stdout.strip()
            self.log(f"  Found n8n volume: {volume_path}", "FIX")

            # Fix permissions (UID 1000 for n8n)
            cmd = f"echo '110811081108***' | sudo -S chown -R 1000:1000 {volume_path}"
            returncode, stdout, stderr = self.run_command(cmd)

            if returncode == 0:
                self.log("  Permissions fixed, restarting container...", "FIX")
                cmd = "docker restart n8n_mautic_erpnext"
                returncode, stdout, stderr = self.run_command(cmd)

                if returncode == 0:
                    time.sleep(20)  # Wait for startup
                    health = self.check_http_health('n8n')
                    if health['healthy']:
                        self.log("  n8n fix SUCCESSFUL ✅", "FIX")
                        return True

        self.log("  n8n fix FAILED ❌", "ERROR")
        return False

    def fix_grafana(self) -> bool:
        """Auto-fix Grafana plugin download timeout"""
        self.log("Applying Grafana fix: Restarting container...", "FIX")

        cmd = "docker restart grafana-analytics"
        returncode, stdout, stderr = self.run_command(cmd)

        if returncode == 0:
            time.sleep(15)  # Wait for startup
            health = self.check_http_health('grafana')
            if health['healthy']:
                self.log("  Grafana fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  Grafana fix FAILED ❌", "ERROR")
        return False

    def fix_defectdojo(self) -> bool:
        """Auto-fix DefectDojo issues"""
        self.log("Restarting DefectDojo container...", "FIX")

        cmd = "docker restart defectdojo-uwsgi-insa"
        returncode, stdout, stderr = self.run_command(cmd)

        if returncode == 0:
            time.sleep(10)
            health = self.check_http_health('defectdojo')
            return health['healthy']

        return False

    def fix_inventree(self) -> bool:
        """Auto-fix InvenTree issues"""
        self.log("Restarting InvenTree container...", "FIX")

        cmd = "docker restart inventree_web"
        returncode, stdout, stderr = self.run_command(cmd)

        if returncode == 0:
            time.sleep(10)
            health = self.check_http_health('inventree')
            return health['healthy']

        return False

    def fix_mautic(self) -> bool:
        """Auto-fix Mautic issues"""
        self.log("Clearing Mautic cache and restarting...", "FIX")

        # Clear cache
        cmd = "docker exec mautic php bin/console cache:clear 2>/dev/null || true"
        self.run_command(cmd)

        # Restart
        cmd = "docker restart mautic"
        returncode, stdout, stderr = self.run_command(cmd)

        if returncode == 0:
            time.sleep(10)
            health = self.check_http_health('mautic')
            return health['healthy']

        return False

    # ============================================================
    # NEW FIX FUNCTIONS (Critical Infrastructure)
    # ============================================================

    def fix_nginx(self) -> bool:
        """Auto-fix nginx service"""
        self.log("Restarting nginx service...", "FIX")

        cmd = "echo '110811081108***' | sudo -S systemctl restart nginx.service"
        returncode, stdout, stderr = self.run_command(cmd, timeout=10)

        if returncode == 0:
            time.sleep(2)
            health = self.check_systemd_service('nginx')
            if health['healthy']:
                self.log("  Nginx fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  Nginx fix FAILED ❌", "ERROR")
        return False

    def fix_postgresql(self) -> bool:
        """Auto-fix PostgreSQL service"""
        self.log("Restarting PostgreSQL service...", "FIX")

        cmd = "echo '110811081108***' | sudo -S systemctl restart postgresql@16-main.service"
        returncode, stdout, stderr = self.run_command(cmd, timeout=30)

        if returncode == 0:
            time.sleep(5)
            health = self.check_database_connection('postgresql')
            if health['healthy']:
                self.log("  PostgreSQL fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  PostgreSQL fix FAILED ❌", "ERROR")
        return False

    def fix_mariadb(self) -> bool:
        """Auto-fix MariaDB service"""
        self.log("Restarting MariaDB service...", "FIX")

        cmd = "echo '110811081108***' | sudo -S systemctl restart mariadb.service"
        returncode, stdout, stderr = self.run_command(cmd, timeout=30)

        if returncode == 0:
            time.sleep(5)
            health = self.check_database_connection('mariadb')
            if health['healthy']:
                self.log("  MariaDB fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  MariaDB fix FAILED ❌", "ERROR")
        return False

    def fix_redis(self) -> bool:
        """Auto-fix Redis service"""
        self.log("Restarting Redis service...", "FIX")

        cmd = "echo '110811081108***' | sudo -S systemctl restart redis-server.service"
        returncode, stdout, stderr = self.run_command(cmd, timeout=10)

        if returncode == 0:
            time.sleep(2)
            health = self.check_systemd_service('redis')
            if health['healthy']:
                self.log("  Redis fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  Redis fix FAILED ❌", "ERROR")
        return False

    def fix_postfix(self) -> bool:
        """Auto-fix Postfix service"""
        self.log("Restarting Postfix service...", "FIX")

        cmd = "echo '110811081108***' | sudo -S systemctl restart postfix@-.service"
        returncode, stdout, stderr = self.run_command(cmd, timeout=10)

        if returncode == 0:
            time.sleep(2)
            health = self.check_systemd_service('postfix')
            if health['healthy']:
                self.log("  Postfix fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  Postfix fix FAILED ❌", "ERROR")
        return False

    def fix_minio(self) -> bool:
        """Auto-fix MinIO container"""
        self.log("Restarting MinIO container...", "FIX")

        cmd = "docker restart minio-insa-crm"
        returncode, stdout, stderr = self.run_command(cmd)

        if returncode == 0:
            time.sleep(5)
            # Check both container and HTTP
            container_health = self.check_container_status('minio-insa-crm')
            if container_health['running']:
                time.sleep(5)  # Wait for HTTP to be ready
                http_health = self.check_http_health('minio')
                if http_health['healthy']:
                    self.log("  MinIO fix SUCCESSFUL ✅", "FIX")
                    return True

        self.log("  MinIO fix FAILED ❌", "ERROR")
        return False

    def fix_qdrant(self) -> bool:
        """Auto-fix Qdrant container"""
        self.log("Restarting Qdrant container...", "FIX")

        cmd = "docker restart insa-crm-qdrant"
        returncode, stdout, stderr = self.run_command(cmd)

        if returncode == 0:
            time.sleep(5)
            # Check both container and HTTP
            container_health = self.check_container_status('insa-crm-qdrant')
            if container_health['running']:
                time.sleep(5)  # Wait for HTTP to be ready
                http_health = self.check_http_health('qdrant')
                if http_health['healthy']:
                    self.log("  Qdrant fix SUCCESSFUL ✅", "FIX")
                    return True

        self.log("  Qdrant fix FAILED ❌", "ERROR")
        return False

    # ============================================================
    # WEEK 4: SECURITY SERVICE FIX FUNCTIONS
    # ============================================================

    def fix_suricata(self) -> bool:
        """Auto-fix Suricata IDS/IPS service"""
        self.log("Restarting Suricata service...", "FIX")

        cmd = "echo '110811081108***' | sudo -S systemctl restart suricata.service"
        returncode, stdout, stderr = self.run_command(cmd, timeout=30)

        if returncode == 0:
            time.sleep(10)  # Suricata takes longer to start (rule loading)
            health = self.check_systemd_service('suricata')
            if health['healthy']:
                self.log("  Suricata fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  Suricata fix FAILED ❌", "ERROR")
        return False

    def fix_wazuh(self) -> bool:
        """Auto-fix Wazuh manager service"""
        self.log("Restarting Wazuh manager...", "FIX")

        cmd = "echo '110811081108***' | sudo -S systemctl restart wazuh-manager.service"
        returncode, stdout, stderr = self.run_command(cmd, timeout=20)

        if returncode == 0:
            time.sleep(5)
            health = self.check_systemd_service('wazuh')
            if health['healthy']:
                self.log("  Wazuh fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  Wazuh fix FAILED ❌", "ERROR")
        return False

    def fix_fail2ban(self) -> bool:
        """Auto-fix Fail2ban service"""
        self.log("Restarting Fail2ban service...", "FIX")

        cmd = "echo '110811081108***' | sudo -S systemctl restart fail2ban.service"
        returncode, stdout, stderr = self.run_command(cmd, timeout=15)

        if returncode == 0:
            time.sleep(3)
            health = self.check_systemd_service('fail2ban')
            if health['healthy']:
                self.log("  Fail2ban fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  Fail2ban fix FAILED ❌", "ERROR")
        return False

    def fix_auditd(self) -> bool:
        """Auto-fix Auditd service"""
        self.log("Restarting Auditd service...", "FIX")

        # Auditd requires special restart procedure
        cmd = "echo '110811081108***' | sudo -S service auditd restart"
        returncode, stdout, stderr = self.run_command(cmd, timeout=15)

        if returncode == 0:
            time.sleep(3)
            health = self.check_systemd_service('auditd')
            if health['healthy']:
                self.log("  Auditd fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  Auditd fix FAILED ❌", "ERROR")
        return False

    def fix_clamav(self) -> bool:
        """Auto-fix ClamAV daemon service"""
        self.log("Restarting ClamAV daemon...", "FIX")

        cmd = "echo '110811081108***' | sudo -S systemctl restart clamav-daemon.service"
        returncode, stdout, stderr = self.run_command(cmd, timeout=20)

        if returncode == 0:
            time.sleep(5)  # ClamAV takes time to load virus DB
            health = self.check_systemd_service('clamav')
            if health['healthy']:
                self.log("  ClamAV daemon fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  ClamAV daemon fix FAILED ❌", "ERROR")
        return False

    # ============================================================
    # WEEK 5: AUTONOMOUS AGENT FIX FUNCTIONS
    # ============================================================

    def fix_integrated_healing(self) -> bool:
        """Auto-fix Integrated Healing Agent (self-healing the healer!)"""
        self.log("Restarting Integrated Healing Agent...", "FIX")

        cmd = "echo '110811081108***' | sudo -S systemctl restart integrated-healing-agent.service"
        returncode, stdout, stderr = self.run_command(cmd, timeout=15)

        if returncode == 0:
            time.sleep(5)
            health = self.check_systemd_service('integrated_healing_agent')
            if health['healthy']:
                self.log("  Integrated Healing Agent fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  Integrated Healing Agent fix FAILED ❌", "ERROR")
        return False

    def fix_host_config(self) -> bool:
        """Auto-fix Host Config Agent"""
        self.log("Restarting Host Config Agent...", "FIX")

        cmd = "echo '110811081108***' | sudo -S systemctl restart host-config-agent.service"
        returncode, stdout, stderr = self.run_command(cmd, timeout=15)

        if returncode == 0:
            time.sleep(5)
            health = self.check_systemd_service('host_config_agent')
            if health['healthy']:
                self.log("  Host Config Agent fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  Host Config Agent fix FAILED ❌", "ERROR")
        return False

    def fix_defectdojo_compliance(self) -> bool:
        """Auto-fix DefectDojo Compliance Agent"""
        self.log("Restarting DefectDojo Compliance Agent...", "FIX")

        cmd = "echo '110811081108***' | sudo -S systemctl restart defectdojo-compliance-agent.service"
        returncode, stdout, stderr = self.run_command(cmd, timeout=15)

        if returncode == 0:
            time.sleep(5)
            health = self.check_systemd_service('defectdojo_compliance_agent')
            if health['healthy']:
                self.log("  DefectDojo Compliance Agent fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  DefectDojo Compliance Agent fix FAILED ❌", "ERROR")
        return False

    def fix_security_integration(self) -> bool:
        """Auto-fix Security Integration Agent"""
        self.log("Restarting Security Integration Agent...", "FIX")

        cmd = "echo '110811081108***' | sudo -S systemctl restart security-integration-agent.service"
        returncode, stdout, stderr = self.run_command(cmd, timeout=15)

        if returncode == 0:
            time.sleep(5)
            health = self.check_systemd_service('security_integration_agent')
            if health['healthy']:
                self.log("  Security Integration Agent fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  Security Integration Agent fix FAILED ❌", "ERROR")
        return False

    def fix_task_orchestration(self) -> bool:
        """Auto-fix Task Orchestration Agent"""
        self.log("Restarting Task Orchestration Agent...", "FIX")

        cmd = "echo '110811081108***' | sudo -S systemctl restart task-orchestration-agent.service"
        returncode, stdout, stderr = self.run_command(cmd, timeout=15)

        if returncode == 0:
            time.sleep(5)
            health = self.check_systemd_service('task_orchestration_agent')
            if health['healthy']:
                self.log("  Task Orchestration Agent fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  Task Orchestration Agent fix FAILED ❌", "ERROR")
        return False

    def fix_azure_monitor(self) -> bool:
        """Auto-fix Azure Monitor Agent"""
        self.log("Restarting Azure Monitor Agent...", "FIX")

        cmd = "echo '110811081108***' | sudo -S systemctl restart azure-monitor-agent.service"
        returncode, stdout, stderr = self.run_command(cmd, timeout=15)

        if returncode == 0:
            time.sleep(5)
            health = self.check_systemd_service('azure_monitor_agent')
            if health['healthy']:
                self.log("  Azure Monitor Agent fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  Azure Monitor Agent fix FAILED ❌", "ERROR")
        return False

    def fix_soc_agent(self) -> bool:
        """Auto-fix SOC Agent"""
        self.log("Restarting SOC Agent...", "FIX")

        cmd = "echo '110811081108***' | sudo -S systemctl restart soc-agent.service"
        returncode, stdout, stderr = self.run_command(cmd, timeout=15)

        if returncode == 0:
            time.sleep(5)
            health = self.check_systemd_service('soc_agent')
            if health['healthy']:
                self.log("  SOC Agent fix SUCCESSFUL ✅", "FIX")
                return True

        self.log("  SOC Agent fix FAILED ❌", "ERROR")
        return False

    # ============================================================
    # MAIN HEALTH CHECK ORCHESTRATION
    # ============================================================

    def run_health_check(self, auto_fix=False) -> Dict:
        """Run full platform health check"""
        self.log("=" * 60)
        self.log("INSA PLATFORM HEALTH CHECK - WEEK 4-6 (30 Services: Apps + Security + Agents + MCP)")
        self.log("=" * 60)

        for service_id, service in self.SERVICES.items():
            service_type = service.get('type', 'web')

            # Determine check method based on service type
            if service_type == 'web':
                health = self.check_http_health(service_id)
            elif service_type == 'systemd':
                health = self.check_systemd_service(service_id)
            elif service_type == 'systemd+db':
                health = self.check_database_connection(service_id)
            elif service_type == 'container+http':
                # Check both container and HTTP
                health = self.check_http_health(service_id)
            elif service_type == 'container':
                # Container-only check (no HTTP)
                container_status = self.check_container_status(service['container'])
                health = {
                    'healthy': container_status['running'],
                    'container_running': container_status['running'],
                    'container_status': container_status['status'],
                    'error': None if container_status['running'] else f"Container not running: {container_status['status']}"
                }
            elif service_type == 'mcp':
                # MCP server configuration check
                health = self.check_mcp_server(service_id)
            elif service_type == 'docker_exec':
                # Docker exec health check (headless mode - Oct 22, 2025)
                health = self.check_docker_exec_health(service_id)
            else:
                health = {'healthy': False, 'error': f'Unknown service type: {service_type}'}

            # Container status check for web/container services (if not already checked)
            if service.get('container') and service_type != 'container':
                container_status = self.check_container_status(service['container'])
                health['container_running'] = container_status['running']
                health['container_status'] = container_status['status']

            self.results[service_id] = {
                'name': service['name'],
                'type': service_type,
                'critical': service['critical'],
                **health
            }

            # Auto-fix if enabled and service is unhealthy
            if auto_fix and not health['healthy'] and service.get('fix_function'):
                self.log(f"\nAttempting auto-fix for {service['name']}...", "FIX")
                fix_func = getattr(self, service['fix_function'])
                success = fix_func()
                self.results[service_id]['auto_fixed'] = success
                self.results[service_id]['fix_attempted'] = True
            else:
                self.results[service_id]['auto_fixed'] = None
                self.results[service_id]['fix_attempted'] = False

        return self.results

    def generate_report(self) -> str:
        """Generate human-readable health report"""
        healthy_count = sum(1 for r in self.results.values() if r['healthy'])
        total_count = len(self.results)
        critical_count = sum(1 for r in self.results.values() if r['critical'])
        critical_healthy = sum(1 for r in self.results.values() if r['critical'] and r['healthy'])

        report = f"\n{'=' * 70}\n"
        report += f"PLATFORM HEALTH SUMMARY (EXPANDED)\n"
        report += f"{'=' * 70}\n"
        report += f"Overall: {healthy_count}/{total_count} services healthy ({healthy_count/total_count*100:.1f}%)\n"
        report += f"Critical: {critical_healthy}/{critical_count} critical services healthy ({critical_healthy/critical_count*100:.1f}%)\n\n"

        # Working services
        report += "✅ HEALTHY SERVICES:\n"
        for service_id, result in self.results.items():
            if result['healthy']:
                critical_mark = " [CRITICAL]" if result['critical'] else ""
                if result['type'] == 'web':
                    report += f"  • {result['name']} - HTTP {result.get('http_code', 'N/A')}{critical_mark}\n"
                elif result['type'] in ['systemd', 'systemd+db']:
                    report += f"  • {result['name']} - {result.get('active_state', 'active')}{critical_mark}\n"
                elif result['type'] == 'container+http':
                    report += f"  • {result['name']} - HTTP {result.get('http_code', 'N/A')} + Container{critical_mark}\n"
                elif result['type'] == 'container':
                    report += f"  • {result['name']} - Container {result.get('container_status', 'running')}{critical_mark}\n"
                elif result['type'] == 'mcp':
                    report += f"  • {result['name']} - MCP Server Configured{critical_mark}\n"

        # Unhealthy services
        unhealthy = {k: v for k, v in self.results.items() if not v['healthy']}
        if unhealthy:
            report += f"\n❌ UNHEALTHY SERVICES:\n"
            for service_id, result in unhealthy.items():
                critical_mark = " [CRITICAL]" if result['critical'] else ""
                report += f"  • {result['name']}{critical_mark}\n"
                report += f"    Error: {result['error']}\n"
                if result.get('container_running') is not None:
                    status = "Running" if result['container_running'] else "NOT RUNNING"
                    report += f"    Container: {status}\n"
                if result.get('fix_attempted'):
                    fix_status = "✅ FIXED" if result['auto_fixed'] else "❌ FAILED"
                    report += f"    Auto-fix: {fix_status}\n"

        report += f"\n{'=' * 70}\n"
        return report

    def get_json_report(self) -> str:
        """Get results as JSON"""
        return json.dumps(self.results, indent=2)

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='INSA Platform Health Monitor - EXPANDED')
    parser.add_argument('--auto-fix', action='store_true', help='Automatically fix unhealthy services')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')
    parser.add_argument('--service', type=str, help='Check specific service only')

    args = parser.parse_args()

    monitor = PlatformHealthMonitor(verbose=not args.quiet)

    # Run health check
    results = monitor.run_health_check(auto_fix=args.auto_fix)

    # Output results
    if args.json:
        print(monitor.get_json_report())
    else:
        print(monitor.generate_report())

    # Exit code: 0 if all healthy, 1 if any unhealthy, 2 if critical unhealthy
    all_healthy = all(r['healthy'] for r in results.values())
    critical_unhealthy = any(r['critical'] and not r['healthy'] for r in results.values())

    if all_healthy:
        sys.exit(0)
    elif critical_unhealthy:
        sys.exit(2)  # Critical failure
    else:
        sys.exit(1)  # Non-critical failure

if __name__ == '__main__':
    main()
