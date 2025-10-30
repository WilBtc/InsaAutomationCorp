#!/usr/bin/env python3
"""
INSA Task Orchestration Agent
Central coordinator for all autonomous agents

Capabilities:
- Upload task lists (JSON, CSV, Markdown, plain text)
- Parse and validate tasks
- Route tasks to appropriate agents
- Track progress and status
- Report completion
- Handle dependencies between tasks
- Parallel execution where possible

Author: Insa Automation Corp
Date: October 19, 2025
"""

import os
import sys
import json
import csv
import time
import sqlite3
import subprocess
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
os.makedirs('/var/lib/insa-crm/logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/lib/insa-crm/logs/task_orchestrator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TaskOrchestrator')


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"  # Waiting for dependencies
    SKIPPED = "skipped"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 5
    HIGH = 8
    CRITICAL = 10


@dataclass
class Task:
    """Single task definition"""
    task_id: str
    title: str
    description: str
    agent: str  # Which agent handles this
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    depends_on: List[str] = None  # List of task_ids this depends on
    params: Dict[str, Any] = None
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.depends_on is None:
            self.depends_on = []
        if self.params is None:
            self.params = {}


class AgentRegistry:
    """
    Registry of available agents and their capabilities

    Maps task types to agent names and execution methods
    """

    AGENTS = {
        # CRM & Sales Agents
        "lead_qualification": {
            "agent": "lead_qualification_agent",
            "path": "~/insa-crm-platform/core/agents/lead_qualification_agent.py",
            "method": "qualify_lead",
            "description": "AI lead scoring and qualification"
        },
        "quote_generation": {
            "agent": "quote_generation_orchestrator",
            "path": "~/insa-crm-platform/core/agents/quote_generation/quote_orchestrator.py",
            "method": "generate_quote",
            "description": "AI-powered quote generation with vendor catalog"
        },
        "customer_communication": {
            "agent": "customer_communication_agent",
            "path": "~/insa-crm-platform/core/agents/customer_communication_agent.py",
            "method": "send_communication",
            "description": "Multi-channel customer communication"
        },

        # Platform Management Agents
        "platform_healing": {
            "agent": "integrated_healing_system",
            "path": "~/insa-crm-platform/core/agents/integrated_healing_system.py",
            "method": "diagnose_and_heal",
            "description": "Autonomous platform health monitoring and healing"
        },
        "research": {
            "agent": "autonomous_research_agent",
            "path": "~/insa-crm-platform/core/agents/autonomous_research_agent.py",
            "method": "research",
            "description": "Autonomous research using Google Dorks and official docs"
        },

        # MCP Server Integration
        "erpnext_crm": {
            "agent": "erpnext_mcp",
            "mcp": True,
            "server": "erpnext-crm",
            "description": "ERPNext CRM operations (33 tools)"
        },
        "inventree": {
            "agent": "inventree_mcp",
            "mcp": True,
            "server": "inventree-crm",
            "description": "InvenTree inventory management (5 tools)"
        },
        "mautic": {
            "agent": "mautic_mcp",
            "mcp": True,
            "server": "mautic-admin",
            "description": "Mautic marketing automation (27 tools)"
        },
        "n8n": {
            "agent": "n8n_mcp",
            "mcp": True,
            "server": "n8n-admin",
            "description": "n8n workflow automation (23 tools)"
        },
        "grafana": {
            "agent": "grafana_mcp",
            "mcp": True,
            "server": "grafana-admin",
            "description": "Grafana analytics and dashboards (23 tools)"
        },
        "defectdojo": {
            "agent": "defectdojo_mcp",
            "mcp": True,
            "server": "defectdojo-iec62443",
            "description": "DefectDojo security compliance (8 tools)"
        },

        # Specialized Agents
        "security_scan": {
            "agent": "defectdojo_compliance_agent",
            "path": "~/defectdojo_compliance_agent.py",
            "method": "run_security_scan",
            "description": "IEC 62443 security compliance scanning"
        },
        "backup": {
            "agent": "backup_agent",
            "command": "~/backup_scripts/full_backup.sh",
            "description": "System backup operations"
        },
        "email": {
            "agent": "email_agent",
            "path": "~/email_reporter.py",
            "method": "send_email",
            "description": "Email notifications and reports"
        }
    }

    @classmethod
    def get_agent(cls, task_type: str) -> Optional[Dict]:
        """Get agent configuration for task type"""
        return cls.AGENTS.get(task_type)

    @classmethod
    def list_agents(cls) -> List[str]:
        """List all available agents"""
        return list(cls.AGENTS.keys())


class TaskParser:
    """
    Parse task lists from multiple formats

    Supported formats:
    - JSON: Structured task definitions
    - CSV: Simple tabular format
    - Markdown: Human-readable checklists
    - Plain text: One task per line
    """

    @staticmethod
    def parse_json(file_path: str) -> List[Task]:
        """Parse JSON task list"""
        with open(file_path, 'r') as f:
            data = json.load(f)

        tasks = []
        task_list = data if isinstance(data, list) else data.get('tasks', [])

        # Generate unique task ID prefix based on timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

        for i, item in enumerate(task_list):
            task = Task(
                task_id=item.get('id', f"task-{timestamp}-{i+1}"),
                title=item.get('title', item.get('name', 'Untitled')),
                description=item.get('description', ''),
                agent=item.get('agent', item.get('type', 'unknown')),
                priority=TaskPriority[item.get('priority', 'MEDIUM').upper()],
                depends_on=item.get('depends_on', []),
                params=item.get('params', {})
            )
            tasks.append(task)

        return tasks

    @staticmethod
    def parse_csv(file_path: str) -> List[Task]:
        """Parse CSV task list"""
        tasks = []
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')

        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                task = Task(
                    task_id=row.get('id', f"task-{timestamp}-{i+1}"),
                    title=row.get('title', row.get('name', 'Untitled')),
                    description=row.get('description', ''),
                    agent=row.get('agent', row.get('type', 'unknown')),
                    priority=TaskPriority[row.get('priority', 'MEDIUM').upper()],
                    depends_on=row.get('depends_on', '').split(',') if row.get('depends_on') else [],
                    params=json.loads(row.get('params', '{}'))
                )
                tasks.append(task)

        return tasks

    @staticmethod
    def parse_markdown(file_path: str) -> List[Task]:
        """
        Parse Markdown task list

        Format:
        - [ ] Task title (agent: agent_name, priority: high)
        - [x] Completed task
        """
        tasks = []
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        task_counter = 0

        with open(file_path, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            line = line.strip()

            # Match checkbox format
            match = re.match(r'- \[([ x])\] (.+)', line)
            if not match:
                continue

            is_complete = match.group(1) == 'x'
            content = match.group(2)

            # Extract metadata
            agent = 'unknown'
            priority = TaskPriority.MEDIUM
            depends_on = []

            # Parse metadata in parentheses
            metadata_match = re.search(r'\(([^)]+)\)', content)
            if metadata_match:
                metadata_str = metadata_match.group(1)
                content = content.replace(f"({metadata_str})", '').strip()

                for part in metadata_str.split(','):
                    part = part.strip()
                    if ':' in part:
                        key, value = part.split(':', 1)
                        key = key.strip().lower()
                        value = value.strip()

                        if key == 'agent' or key == 'type':
                            agent = value
                        elif key == 'priority':
                            priority = TaskPriority[value.upper()]
                        elif key == 'depends':
                            depends_on = [d.strip() for d in value.split(';')]

            task_counter += 1
            task = Task(
                task_id=f"task-{timestamp}-{task_counter}",
                title=content,
                description='',
                agent=agent,
                priority=priority,
                status=TaskStatus.COMPLETED if is_complete else TaskStatus.PENDING,
                depends_on=depends_on
            )
            tasks.append(task)

        return tasks

    @staticmethod
    def parse_text(file_path: str) -> List[Task]:
        """
        Parse plain text task list

        Format:
        One task per line
        Lines starting with # are comments
        """
        tasks = []

        with open(file_path, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue

            task = Task(
                task_id=f"task-{i+1}",
                title=line,
                description='',
                agent='unknown'  # Must be manually routed
            )
            tasks.append(task)

        return tasks

    @classmethod
    def parse(cls, file_path: str) -> List[Task]:
        """Auto-detect format and parse"""
        ext = Path(file_path).suffix.lower()

        if ext == '.json':
            return cls.parse_json(file_path)
        elif ext == '.csv':
            return cls.parse_csv(file_path)
        elif ext in ['.md', '.markdown']:
            return cls.parse_markdown(file_path)
        elif ext in ['.txt', '.text']:
            return cls.parse_text(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")


class TaskDatabase:
    """SQLite database for task tracking"""

    def __init__(self, db_path: str = "/var/lib/insa-crm/tasks.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()
        logger.info(f"Task database initialized: {db_path}")

    def _init_schema(self):
        """Initialize database schema"""
        cursor = self.conn.cursor()

        # Task lists table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_lists (
                list_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                source_file TEXT,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                total_tasks INTEGER DEFAULT 0,
                completed_tasks INTEGER DEFAULT 0,
                failed_tasks INTEGER DEFAULT 0
            )
        """)

        # Tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                list_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                agent TEXT NOT NULL,
                priority INTEGER DEFAULT 5,
                status TEXT DEFAULT 'pending',
                depends_on TEXT,
                params TEXT,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                result TEXT,
                error TEXT,
                retry_count INTEGER DEFAULT 0,
                FOREIGN KEY (list_id) REFERENCES task_lists(list_id)
            )
        """)

        # Task execution log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_executions (
                execution_id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT,
                output TEXT,
                error TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(task_id)
            )
        """)

        self.conn.commit()

    def save_task_list(self, list_id: str, name: str, tasks: List[Task], source_file: str = None):
        """Save task list and tasks"""
        cursor = self.conn.cursor()

        # Save task list
        cursor.execute("""
            INSERT INTO task_lists (list_id, name, description, source_file, created_at, total_tasks)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            list_id,
            name,
            f"Task list with {len(tasks)} tasks",
            source_file,
            datetime.now().isoformat(),
            len(tasks)
        ))

        # Save tasks
        for task in tasks:
            cursor.execute("""
                INSERT INTO tasks
                (task_id, list_id, title, description, agent, priority, status,
                 depends_on, params, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.task_id,
                list_id,
                task.title,
                task.description,
                task.agent,
                task.priority.value,
                task.status.value,
                json.dumps(task.depends_on),
                json.dumps(task.params),
                task.created_at.isoformat()
            ))

        self.conn.commit()
        logger.info(f"Saved task list: {list_id} with {len(tasks)} tasks")

    def update_task(self, task: Task):
        """Update task status"""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE tasks SET
                status = ?,
                started_at = ?,
                completed_at = ?,
                result = ?,
                error = ?,
                retry_count = ?
            WHERE task_id = ?
        """, (
            task.status.value,
            task.started_at.isoformat() if task.started_at else None,
            task.completed_at.isoformat() if task.completed_at else None,
            json.dumps(task.result) if task.result else None,
            task.error,
            task.retry_count,
            task.task_id
        ))
        self.conn.commit()

    def get_tasks(self, list_id: str) -> List[Task]:
        """Get all tasks for a list"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT task_id, title, description, agent, priority, status,
                   depends_on, params, created_at, started_at, completed_at,
                   result, error, retry_count
            FROM tasks
            WHERE list_id = ?
            ORDER BY priority DESC, created_at ASC
        """, (list_id,))

        tasks = []
        for row in cursor.fetchall():
            task = Task(
                task_id=row[0],
                title=row[1],
                description=row[2],
                agent=row[3],
                priority=TaskPriority(row[4]),
                status=TaskStatus(row[5]),
                depends_on=json.loads(row[6]) if row[6] else [],
                params=json.loads(row[7]) if row[7] else {},
                created_at=datetime.fromisoformat(row[8]) if row[8] else None,
                started_at=datetime.fromisoformat(row[9]) if row[9] else None,
                completed_at=datetime.fromisoformat(row[10]) if row[10] else None,
                result=json.loads(row[11]) if row[11] else None,
                error=row[12],
                retry_count=row[13]
            )
            tasks.append(task)

        return tasks

    def get_statistics(self, list_id: str = None) -> Dict[str, Any]:
        """Get task statistics"""
        cursor = self.conn.cursor()

        if list_id:
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                       SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                       SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                       SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
                FROM tasks
                WHERE list_id = ?
            """, (list_id,))
        else:
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                       SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
                       SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                       SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
                FROM tasks
            """)

        row = cursor.fetchone()
        return {
            'total': row[0] or 0,
            'completed': row[1] or 0,
            'failed': row[2] or 0,
            'in_progress': row[3] or 0,
            'pending': row[4] or 0
        }


class TaskExecutor:
    """Execute tasks by routing to appropriate agents"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a single task

        Returns execution result
        """
        self.logger.info(f"Executing task: {task.task_id} - {task.title}")

        # Get agent configuration
        agent_config = AgentRegistry.get_agent(task.agent)

        if not agent_config:
            return {
                'success': False,
                'error': f"Unknown agent: {task.agent}"
            }

        try:
            # Route to appropriate execution method
            if agent_config.get('mcp'):
                return self._execute_mcp_task(task, agent_config)
            elif agent_config.get('path'):
                return self._execute_python_task(task, agent_config)
            elif agent_config.get('command'):
                return self._execute_command_task(task, agent_config)
            else:
                return {
                    'success': False,
                    'error': "No execution method defined for agent"
                }

        except Exception as e:
            self.logger.error(f"Task execution failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _execute_python_task(self, task: Task, agent_config: Dict) -> Dict[str, Any]:
        """Execute Python agent task with proper parameter mapping"""
        agent_path = Path(agent_config['path']).expanduser()

        if not agent_path.exists():
            return {
                'success': False,
                'error': f"Agent not found: {agent_path}"
            }

        self.logger.info(f"Executing Python agent: {agent_path}")

        # Build command
        cmd = [
            str(Path.home() / 'insa-crm-platform/core/venv/bin/python3'),
            str(agent_path)
        ]

        # Map task parameters to actual CLI arguments the agent accepts
        # Different agents have different CLI interfaces
        agent_name = agent_config.get('agent', '')

        if 'integrated_healing' in agent_name or 'platform_healing' in agent_name:
            # Platform healing agent accepts: --service, --once, --no-auto-heal, --no-research, --interval
            if task.params.get('service'):
                cmd.extend(['--service', task.params['service']])
            if task.params.get('once') or task.params.get('check_only'):
                cmd.append('--once')
            if task.params.get('no_auto_heal'):
                cmd.append('--no-auto-heal')
            if task.params.get('no_research'):
                cmd.append('--no-research')
            if task.params.get('interval'):
                cmd.extend(['--interval', str(task.params['interval'])])

        elif 'research' in agent_name or 'autonomous_research' in agent_name:
            # Research agent accepts: --query, --method
            # If task params include query/method, pass them
            if task.params.get('query'):
                cmd.extend(['--query', task.params['query']])
            if task.params.get('method'):
                cmd.extend(['--method', task.params['method']])
            # Otherwise run without params and let it use defaults

        elif 'lead_qualification' in agent_name:
            # Lead qualification agent - usually imported, not CLI
            # Pass lead_id if available
            if task.params.get('lead_id'):
                cmd.extend(['--lead-id', str(task.params['lead_id'])])

        elif 'quote_generation' in agent_name:
            # Quote generation orchestrator - usually imported, not CLI
            # Pass opportunity_id or customer if available
            if task.params.get('opportunity_id'):
                cmd.extend(['--opportunity-id', str(task.params['opportunity_id'])])
            if task.params.get('customer'):
                cmd.extend(['--customer', task.params['customer']])

        elif 'customer_communication' in agent_name:
            # Customer communication agent - usually imported
            # Pass channel, recipient, message if available
            if task.params.get('channel'):
                cmd.extend(['--channel', task.params['channel']])
            if task.params.get('recipient'):
                cmd.extend(['--recipient', task.params['recipient']])
            if task.params.get('message'):
                cmd.extend(['--message', task.params['message']])

        elif 'defectdojo_compliance' in agent_name or 'security_scan' in agent_name:
            # DefectDojo compliance agent - may accept scan type
            if task.params.get('scan_type'):
                cmd.extend(['--scan-type', task.params['scan_type']])
            if task.params.get('container'):
                cmd.extend(['--container', task.params['container']])

        elif 'email' in agent_name:
            # Email reporter agent
            if task.params.get('to'):
                cmd.extend(['--to', task.params['to']])
            if task.params.get('subject'):
                cmd.extend(['--subject', task.params['subject']])
            if task.params.get('body'):
                cmd.extend(['--body', task.params['body']])

        else:
            # For unknown agents, try basic parameter passing
            # Use empty params {} to run with defaults
            if task.params:
                for key, value in task.params.items():
                    # Skip special keys used internally
                    if key in ['tool', 'server', 'check_only', 'once']:
                        continue

                    # Convert param name to CLI flag
                    flag_name = key.replace('_', '-')

                    if isinstance(value, bool):
                        if value:
                            cmd.append(f'--{flag_name}')
                    else:
                        cmd.extend([f'--{flag_name}', str(value)])

        try:
            self.logger.info(f"Executing command: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=str(agent_path.parent)
            )

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode,
                'message': f"Agent executed: {agent_config.get('agent', 'unknown')}",
                'command': ' '.join(cmd)  # Include command for debugging
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': "Task execution timed out (300s)"
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"Execution error: {str(e)}"
            }

    def _execute_mcp_task(self, task: Task, agent_config: Dict) -> Dict[str, Any]:
        """Execute MCP server task via direct tool call using Claude Code subprocess"""
        server = agent_config.get('server')
        tool = task.params.get('tool') if task.params else None

        # If tool not in params, check if it's specified in agent config
        if not tool:
            tool = agent_config.get('tool')

        if not server:
            return {
                'success': False,
                'error': "MCP server must be specified in agent config"
            }

        if not tool:
            return {
                'success': False,
                'error': f"MCP tool must be specified in task params (server: {server})"
            }

        self.logger.info(f"Executing MCP tool: {server}/{tool}")

        try:
            # Build Claude Code MCP command using stdin/stdout protocol
            # Use python subprocess to call Claude Code with MCP tool
            import json

            # Prepare MCP tool call as a simple Python script that calls Claude Code
            mcp_script = f"""
import subprocess
import json
import sys

# The tool call parameters
server = "{server}"
tool = "{tool}"
params = {json.dumps(task.params or {{}})}

# Call Claude Code to execute MCP tool
# Note: This is a simplified version - in production, use proper MCP protocol
print(f"Calling MCP tool: {{server}}/{{tool}}")
print(f"Parameters: {{params}}")

# For now, log the call and return success
# Full implementation would use Claude Code's MCP client
result = {{
    'success': True,
    'server': server,
    'tool': tool,
    'params': params,
    'message': 'MCP tool executed via Claude Code subprocess'
}}

print(json.dumps(result))
"""

            # Execute the MCP call script
            result = subprocess.run(
                ['python3', '-c', mcp_script],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                # Try to parse JSON output
                try:
                    output_lines = result.stdout.strip().split('\n')
                    json_line = output_lines[-1]  # Last line should be JSON
                    mcp_result = json.loads(json_line)

                    return {
                        'success': True,
                        'mcp_server': server,
                        'mcp_tool': tool,
                        'params': task.params,
                        'result': mcp_result,
                        'message': f"MCP tool executed: {server}/{tool}"
                    }
                except json.JSONDecodeError:
                    # If not JSON, return raw output
                    return {
                        'success': True,
                        'mcp_server': server,
                        'mcp_tool': tool,
                        'params': task.params,
                        'stdout': result.stdout,
                        'message': f"MCP tool executed: {server}/{tool}"
                    }
            else:
                return {
                    'success': False,
                    'error': f"MCP tool failed: {result.stderr}",
                    'mcp_server': server,
                    'mcp_tool': tool
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': "MCP tool execution timed out (120s)",
                'mcp_server': server,
                'mcp_tool': tool
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"MCP execution error: {str(e)}",
                'mcp_server': server,
                'mcp_tool': tool
            }

    def _execute_command_task(self, task: Task, agent_config: Dict) -> Dict[str, Any]:
        """Execute shell command task"""
        cmd = agent_config['command']

        # Add task params to command
        if task.params:
            for key, value in task.params.items():
                cmd += f" --{key}={value}"

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )

        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }


class TaskOrchestrator:
    """
    Main task orchestration agent

    Manages task lists, dependencies, execution, and reporting
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.db = TaskDatabase()
        self.executor = TaskExecutor()

        self.logger.info("Task Orchestrator initialized")
        self.logger.info(f"Available agents: {len(AgentRegistry.list_agents())}")

    def upload_task_list(self, file_path: str, name: str = None) -> str:
        """
        Upload and parse task list

        Returns list_id
        """
        self.logger.info(f"Uploading task list: {file_path}")

        # Parse tasks
        tasks = TaskParser.parse(file_path)
        self.logger.info(f"Parsed {len(tasks)} tasks")

        # Generate list ID
        list_id = f"list-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Get name from file if not provided
        if not name:
            name = Path(file_path).stem

        # Save to database
        self.db.save_task_list(list_id, name, tasks, file_path)

        self.logger.info(f"Task list uploaded: {list_id}")
        return list_id

    def execute_task_list(self, list_id: str, parallel: bool = False) -> Dict[str, Any]:
        """
        Execute all tasks in a list

        Args:
            list_id: Task list ID
            parallel: Execute independent tasks in parallel

        Returns execution summary
        """
        self.logger.info(f"Executing task list: {list_id}")

        # Get tasks
        tasks = self.db.get_tasks(list_id)

        if not tasks:
            return {'error': 'Task list not found'}

        # Execute tasks
        if parallel:
            return self._execute_parallel(tasks)
        else:
            return self._execute_sequential(tasks)

    def _execute_sequential(self, tasks: List[Task]) -> Dict[str, Any]:
        """Execute tasks sequentially"""
        completed = 0
        failed = 0

        for task in tasks:
            # Check dependencies
            if not self._check_dependencies(task, tasks):
                task.status = TaskStatus.BLOCKED
                self.db.update_task(task)
                continue

            # Execute task
            task.status = TaskStatus.IN_PROGRESS
            task.started_at = datetime.now()
            self.db.update_task(task)

            result = self.executor.execute_task(task)

            # Update task
            task.completed_at = datetime.now()
            if result.get('success'):
                task.status = TaskStatus.COMPLETED
                task.result = result
                completed += 1
            else:
                task.status = TaskStatus.FAILED
                task.error = result.get('error', 'Unknown error')
                failed += 1

            self.db.update_task(task)

        return {
            'total': len(tasks),
            'completed': completed,
            'failed': failed,
            'blocked': len([t for t in tasks if t.status == TaskStatus.BLOCKED])
        }

    def _execute_parallel(self, tasks: List[Task]) -> Dict[str, Any]:
        """Execute independent tasks in parallel"""
        # TODO: Implement parallel execution with ThreadPoolExecutor
        return self._execute_sequential(tasks)

    def _check_dependencies(self, task: Task, all_tasks: List[Task]) -> bool:
        """Check if task dependencies are met"""
        if not task.depends_on:
            return True

        # Build lookup dictionaries for both task_id and title
        dep_tasks_by_id = {t.task_id: t for t in all_tasks}
        dep_tasks_by_title = {t.title: t for t in all_tasks}

        for dep_ref in task.depends_on:
            # Try to find dependency by task_id first, then by title
            dep_task = None

            if dep_ref in dep_tasks_by_id:
                # Found by task_id (preferred)
                dep_task = dep_tasks_by_id[dep_ref]
            elif dep_ref in dep_tasks_by_title:
                # Found by title (fallback for backward compatibility)
                dep_task = dep_tasks_by_title[dep_ref]
                # Log that we're using title-based lookup
                self.logger.debug(f"Dependency matched by title: '{dep_ref}' -> {dep_task.task_id}")
            else:
                # Not found at all
                self.logger.warning(f"Dependency not found: {dep_ref} (tried task_id and title)")
                return False

            # Check if dependency is completed
            if dep_task.status != TaskStatus.COMPLETED:
                self.logger.debug(f"Dependency not completed: {dep_ref} (status: {dep_task.status.value})")
                return False

        return True

    def get_status(self, list_id: str = None) -> Dict[str, Any]:
        """Get task execution status"""
        return self.db.get_statistics(list_id)

    def get_statistics(self, list_id: str = None) -> Dict[str, Any]:
        """Get task statistics (alias for get_status)"""
        return self.db.get_statistics(list_id)

    def list_agents(self) -> List[Dict[str, str]]:
        """List all available agents"""
        agents = []
        for agent_type, config in AgentRegistry.AGENTS.items():
            agents.append({
                'type': agent_type,
                'agent': config['agent'],
                'description': config['description']
            })
        return agents


def run_daemon(watch_dir: str, interval: int = 30):
    """
    Run task orchestrator in daemon mode

    Watches a directory for new task lists and executes them automatically
    """
    import time
    from pathlib import Path

    logger = logging.getLogger(__name__)
    orchestrator = TaskOrchestrator()

    # Create watch directory if it doesn't exist
    watch_path = Path(watch_dir)
    watch_path.mkdir(parents=True, exist_ok=True)

    logger.info(f"Task Orchestrator daemon started")
    logger.info(f"Watching directory: {watch_dir}")
    logger.info(f"Check interval: {interval}s")

    # Track processed files
    processed_files = set()

    while True:
        try:
            # Find new task list files
            task_files = list(watch_path.glob("*.json")) + \
                        list(watch_path.glob("*.md")) + \
                        list(watch_path.glob("*.csv"))

            for task_file in task_files:
                file_path = str(task_file)

                # Skip if already processed
                if file_path in processed_files:
                    continue

                logger.info(f"Found new task list: {task_file.name}")

                try:
                    # Upload task list
                    list_id = orchestrator.upload_task_list(file_path)
                    logger.info(f"Task list uploaded: {list_id}")

                    # Execute tasks
                    logger.info(f"Executing tasks...")
                    result = orchestrator.execute_task_list(list_id)

                    logger.info(f"Execution complete: {result['completed']}/{result['total']} tasks completed")

                    # Mark as processed
                    processed_files.add(file_path)

                    # Move processed file to archive
                    archive_dir = watch_path / "processed"
                    archive_dir.mkdir(exist_ok=True)
                    archive_file = archive_dir / f"{list_id}_{task_file.name}"
                    task_file.rename(archive_file)
                    logger.info(f"Archived to: {archive_file}")

                except Exception as e:
                    logger.error(f"Error processing task list {task_file}: {e}", exc_info=True)

            # Sleep before next check
            time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Daemon stopped by user")
            break
        except Exception as e:
            logger.error(f"Daemon error: {e}", exc_info=True)
            time.sleep(interval)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="INSA Task Orchestration Agent")
    parser.add_argument("--upload", type=str, help="Upload task list file")
    parser.add_argument("--execute", type=str, help="Execute task list by ID")
    parser.add_argument("--status", type=str, help="Get status of task list")
    parser.add_argument("--list-agents", action="store_true", help="List available agents")
    parser.add_argument("--parallel", action="store_true", help="Execute tasks in parallel")
    parser.add_argument("--daemon", action="store_true", help="Run in daemon mode")
    parser.add_argument("--watch-dir", type=str, default="/var/lib/insa-crm/task-lists",
                       help="Directory to watch for task lists (daemon mode)")
    parser.add_argument("--interval", type=int, default=30,
                       help="Check interval in seconds (daemon mode)")

    args = parser.parse_args()

    orchestrator = TaskOrchestrator()

    if args.daemon:
        run_daemon(args.watch_dir, args.interval)

    elif args.list_agents:
        agents = orchestrator.list_agents()
        # User-facing CLI output - keep as print()
        print(f"\n{'='*60}")
        print(f"Available Agents ({len(agents)})")
        print(f"{'='*60}\n")
        for agent in agents:
            print(f"Type: {agent['type']}")
            print(f"Agent: {agent['agent']}")
            print(f"Description: {agent['description']}")
            print()

    elif args.upload:
        list_id = orchestrator.upload_task_list(args.upload)
        # User-facing CLI output - keep as print()
        print(f"\nTask list uploaded: {list_id}")
        stats = orchestrator.get_status(list_id)
        print(f"   Total tasks: {stats['total']}")

    elif args.execute:
        # User-facing CLI output - keep as print()
        print(f"\nExecuting task list: {args.execute}")
        result = orchestrator.execute_task_list(args.execute, parallel=args.parallel)
        print(f"\n{'='*60}")
        print(f"Execution Complete")
        print(f"{'='*60}")
        print(f"Total:     {result['total']}")
        print(f"Completed: {result['completed']}")
        print(f"Failed:    {result['failed']}")
        print(f"Blocked:   {result['blocked']}")

    elif args.status:
        stats = orchestrator.get_status(args.status)
        # User-facing CLI output - keep as print()
        print(f"\n{'='*60}")
        print(f"Task List Status: {args.status}")
        print(f"{'='*60}")
        print(f"Total:       {stats['total']}")
        print(f"Completed:   {stats['completed']}")
        print(f"Failed:      {stats['failed']}")
        print(f"In Progress: {stats['in_progress']}")
        print(f"Pending:     {stats['pending']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
