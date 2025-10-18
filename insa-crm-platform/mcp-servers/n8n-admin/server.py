#!/usr/bin/env python3
"""
n8n MCP Server - Full Administrative Control
============================================

Provides Claude Code with complete autonomous control over n8n workflow automation platform.

**Organization:** INSA Automation Corp
**Server:** iac1 (100.100.101.1)
**Purpose:** Workflow automation management for ERPNext ↔ Mautic integration
**Created:** October 18, 2025

## Features
- 23 comprehensive tools for full n8n control
- Workflow CRUD operations (create, read, update, delete, activate)
- Execution management (trigger, monitor, retry, cancel)
- Credential management (add, update, list, delete)
- Analytics and monitoring (success rates, performance metrics)
- Error handling and debugging support

## Tools Organized by Category

### Workflow Management (7 tools)
1. n8n_list_workflows - List all workflows with filters
2. n8n_get_workflow - Get detailed workflow JSON
3. n8n_create_workflow - Create new workflow from JSON
4. n8n_update_workflow - Update existing workflow
5. n8n_delete_workflow - Delete workflow by ID
6. n8n_activate_workflow - Activate/deactivate workflow
7. n8n_duplicate_workflow - Clone existing workflow

### Execution Control (6 tools)
8. n8n_list_executions - List workflow executions with filters
9. n8n_get_execution - Get detailed execution data
10. n8n_trigger_workflow - Manually trigger workflow execution
11. n8n_retry_execution - Retry failed execution
12. n8n_cancel_execution - Cancel running execution
13. n8n_delete_execution - Delete execution record

### Credential Management (4 tools)
14. n8n_list_credentials - List all credentials
15. n8n_get_credential - Get credential details (without sensitive data)
16. n8n_create_credential - Add new API credential
17. n8n_delete_credential - Delete credential

### Monitoring & Analytics (4 tools)
18. n8n_get_stats - Get n8n statistics and metrics
19. n8n_get_workflow_stats - Get workflow-specific performance
20. n8n_get_execution_summary - Get execution summary by date range
21. n8n_health_check - Check n8n health status

### Administration (2 tools)
22. n8n_get_settings - Get n8n configuration
23. n8n_export_workflows - Export all workflows as backup

## API Authentication
n8n supports multiple authentication methods:
- API Key (recommended for production)
- HTTP Basic Auth (username/password)

## Environment Variables
- N8N_API_URL: n8n API base URL (default: http://100.100.101.1:5678)
- N8N_API_KEY: API key for authentication (if available)
- N8N_USERNAME: Username for basic auth (fallback)
- N8N_PASSWORD: Password for basic auth (fallback)
"""

import os
import sys
import json
import asyncio
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent

# Load environment variables
load_dotenv()

# Configuration
N8N_API_URL = os.getenv("N8N_API_URL", "http://100.100.101.1:5678")
N8N_API_KEY = os.getenv("N8N_API_KEY", "")
N8N_USERNAME = os.getenv("N8N_USERNAME", "admin")
N8N_PASSWORD = os.getenv("N8N_PASSWORD", "n8n_admin_2025")

# Global session with authentication
session = requests.Session()
if N8N_API_KEY:
    session.headers.update({"X-N8N-API-KEY": N8N_API_KEY})
else:
    session.auth = (N8N_USERNAME, N8N_PASSWORD)

session.headers.update({
    "Content-Type": "application/json",
    "Accept": "application/json"
})


class N8NMCPServer:
    """n8n MCP Server for workflow automation management"""

    def __init__(self):
        self.server = Server("n8n-admin")
        self.setup_handlers()

    def setup_handlers(self):
        """Register MCP handlers"""
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                # ===== WORKFLOW MANAGEMENT (7 tools) =====
                Tool(
                    name="n8n_list_workflows",
                    description="List all n8n workflows with optional filters (active, name, tags)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "active": {
                                "type": "boolean",
                                "description": "Filter by active status"
                            },
                            "tags": {
                                "type": "string",
                                "description": "Filter by tags (comma-separated)"
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum workflows to return (default: 50)",
                                "default": 50
                            }
                        }
                    }
                ),
                Tool(
                    name="n8n_get_workflow",
                    description="Get detailed workflow information including full JSON definition",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "string",
                                "description": "Workflow ID (numeric or string)"
                            }
                        },
                        "required": ["workflow_id"]
                    }
                ),
                Tool(
                    name="n8n_create_workflow",
                    description="Create new workflow from JSON definition",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Workflow name"
                            },
                            "nodes": {
                                "type": "array",
                                "description": "Array of workflow nodes (JSON)"
                            },
                            "connections": {
                                "type": "object",
                                "description": "Node connections (JSON)"
                            },
                            "settings": {
                                "type": "object",
                                "description": "Workflow settings (optional)"
                            },
                            "tags": {
                                "type": "array",
                                "description": "Workflow tags (optional)",
                                "items": {"type": "string"}
                            },
                            "active": {
                                "type": "boolean",
                                "description": "Activate workflow immediately (default: false)",
                                "default": False
                            }
                        },
                        "required": ["name", "nodes", "connections"]
                    }
                ),
                Tool(
                    name="n8n_update_workflow",
                    description="Update existing workflow (name, nodes, connections, settings, active status)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "string",
                                "description": "Workflow ID to update"
                            },
                            "name": {
                                "type": "string",
                                "description": "New workflow name (optional)"
                            },
                            "nodes": {
                                "type": "array",
                                "description": "Updated nodes (optional)"
                            },
                            "connections": {
                                "type": "object",
                                "description": "Updated connections (optional)"
                            },
                            "settings": {
                                "type": "object",
                                "description": "Updated settings (optional)"
                            },
                            "active": {
                                "type": "boolean",
                                "description": "Active status (optional)"
                            },
                            "tags": {
                                "type": "array",
                                "description": "Updated tags (optional)",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["workflow_id"]
                    }
                ),
                Tool(
                    name="n8n_delete_workflow",
                    description="Delete workflow by ID (permanent, cannot be undone)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "string",
                                "description": "Workflow ID to delete"
                            }
                        },
                        "required": ["workflow_id"]
                    }
                ),
                Tool(
                    name="n8n_activate_workflow",
                    description="Activate or deactivate workflow (enables/disables execution)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "string",
                                "description": "Workflow ID"
                            },
                            "active": {
                                "type": "boolean",
                                "description": "True to activate, False to deactivate"
                            }
                        },
                        "required": ["workflow_id", "active"]
                    }
                ),
                Tool(
                    name="n8n_duplicate_workflow",
                    description="Clone existing workflow with new name",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "string",
                                "description": "Source workflow ID"
                            },
                            "new_name": {
                                "type": "string",
                                "description": "Name for duplicated workflow"
                            }
                        },
                        "required": ["workflow_id", "new_name"]
                    }
                ),

                # ===== EXECUTION CONTROL (6 tools) =====
                Tool(
                    name="n8n_list_executions",
                    description="List workflow executions with filters (status, date range, workflow)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "string",
                                "description": "Filter by workflow ID (optional)"
                            },
                            "status": {
                                "type": "string",
                                "description": "Filter by status: success, error, running, waiting (optional)",
                                "enum": ["success", "error", "running", "waiting", "canceled"]
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum executions to return (default: 20)",
                                "default": 20
                            }
                        }
                    }
                ),
                Tool(
                    name="n8n_get_execution",
                    description="Get detailed execution data including input/output for all nodes",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "execution_id": {
                                "type": "string",
                                "description": "Execution ID"
                            }
                        },
                        "required": ["execution_id"]
                    }
                ),
                Tool(
                    name="n8n_trigger_workflow",
                    description="Manually trigger workflow execution with optional input data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "string",
                                "description": "Workflow ID to trigger"
                            },
                            "input_data": {
                                "type": "object",
                                "description": "Input data for workflow (optional)"
                            }
                        },
                        "required": ["workflow_id"]
                    }
                ),
                Tool(
                    name="n8n_retry_execution",
                    description="Retry failed execution from last failed node",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "execution_id": {
                                "type": "string",
                                "description": "Failed execution ID to retry"
                            }
                        },
                        "required": ["execution_id"]
                    }
                ),
                Tool(
                    name="n8n_cancel_execution",
                    description="Cancel currently running execution",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "execution_id": {
                                "type": "string",
                                "description": "Running execution ID to cancel"
                            }
                        },
                        "required": ["execution_id"]
                    }
                ),
                Tool(
                    name="n8n_delete_execution",
                    description="Delete execution record (cleanup old executions)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "execution_id": {
                                "type": "string",
                                "description": "Execution ID to delete"
                            }
                        },
                        "required": ["execution_id"]
                    }
                ),

                # ===== CREDENTIAL MANAGEMENT (4 tools) =====
                Tool(
                    name="n8n_list_credentials",
                    description="List all credentials (API keys, auth tokens, etc.) without sensitive data",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "description": "Filter by credential type (e.g., 'httpBasicAuth', 'httpHeaderAuth')"
                            }
                        }
                    }
                ),
                Tool(
                    name="n8n_get_credential",
                    description="Get credential details (name, type, but NOT sensitive values)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "credential_id": {
                                "type": "string",
                                "description": "Credential ID"
                            }
                        },
                        "required": ["credential_id"]
                    }
                ),
                Tool(
                    name="n8n_create_credential",
                    description="Create new credential for API authentication",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "Credential name (e.g., 'ERPNext API')"
                            },
                            "type": {
                                "type": "string",
                                "description": "Credential type (e.g., 'httpBasicAuth', 'httpHeaderAuth', 'apiKey')"
                            },
                            "data": {
                                "type": "object",
                                "description": "Credential data (keys depend on type)"
                            }
                        },
                        "required": ["name", "type", "data"]
                    }
                ),
                Tool(
                    name="n8n_delete_credential",
                    description="Delete credential by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "credential_id": {
                                "type": "string",
                                "description": "Credential ID to delete"
                            }
                        },
                        "required": ["credential_id"]
                    }
                ),

                # ===== MONITORING & ANALYTICS (4 tools) =====
                Tool(
                    name="n8n_get_stats",
                    description="Get n8n statistics (total workflows, executions, success rate)",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="n8n_get_workflow_stats",
                    description="Get workflow-specific performance metrics (execution count, success rate, avg duration)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "workflow_id": {
                                "type": "string",
                                "description": "Workflow ID"
                            },
                            "days": {
                                "type": "number",
                                "description": "Days to look back (default: 7)",
                                "default": 7
                            }
                        },
                        "required": ["workflow_id"]
                    }
                ),
                Tool(
                    name="n8n_get_execution_summary",
                    description="Get execution summary by date range (success/error counts, trends)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD)"
                            }
                        },
                        "required": ["start_date", "end_date"]
                    }
                ),
                Tool(
                    name="n8n_health_check",
                    description="Check n8n health status and connectivity",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),

                # ===== ADMINISTRATION (2 tools) =====
                Tool(
                    name="n8n_get_settings",
                    description="Get n8n configuration and settings",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="n8n_export_workflows",
                    description="Export all workflows as JSON backup",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "output_path": {
                                "type": "string",
                                "description": "Path to save backup (default: /tmp/n8n-backup.json)",
                                "default": "/tmp/n8n-backup.json"
                            }
                        }
                    }
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            try:
                # Route tool calls to appropriate methods
                if name == "n8n_list_workflows":
                    result = await self.list_workflows(arguments)
                elif name == "n8n_get_workflow":
                    result = await self.get_workflow(arguments["workflow_id"])
                elif name == "n8n_create_workflow":
                    result = await self.create_workflow(arguments)
                elif name == "n8n_update_workflow":
                    result = await self.update_workflow(arguments)
                elif name == "n8n_delete_workflow":
                    result = await self.delete_workflow(arguments["workflow_id"])
                elif name == "n8n_activate_workflow":
                    result = await self.activate_workflow(arguments["workflow_id"], arguments["active"])
                elif name == "n8n_duplicate_workflow":
                    result = await self.duplicate_workflow(arguments["workflow_id"], arguments["new_name"])

                elif name == "n8n_list_executions":
                    result = await self.list_executions(arguments)
                elif name == "n8n_get_execution":
                    result = await self.get_execution(arguments["execution_id"])
                elif name == "n8n_trigger_workflow":
                    result = await self.trigger_workflow(arguments["workflow_id"], arguments.get("input_data"))
                elif name == "n8n_retry_execution":
                    result = await self.retry_execution(arguments["execution_id"])
                elif name == "n8n_cancel_execution":
                    result = await self.cancel_execution(arguments["execution_id"])
                elif name == "n8n_delete_execution":
                    result = await self.delete_execution(arguments["execution_id"])

                elif name == "n8n_list_credentials":
                    result = await self.list_credentials(arguments.get("type"))
                elif name == "n8n_get_credential":
                    result = await self.get_credential(arguments["credential_id"])
                elif name == "n8n_create_credential":
                    result = await self.create_credential(arguments)
                elif name == "n8n_delete_credential":
                    result = await self.delete_credential(arguments["credential_id"])

                elif name == "n8n_get_stats":
                    result = await self.get_stats()
                elif name == "n8n_get_workflow_stats":
                    result = await self.get_workflow_stats(arguments["workflow_id"], arguments.get("days", 7))
                elif name == "n8n_get_execution_summary":
                    result = await self.get_execution_summary(arguments["start_date"], arguments["end_date"])
                elif name == "n8n_health_check":
                    result = await self.health_check()

                elif name == "n8n_get_settings":
                    result = await self.get_settings()
                elif name == "n8n_export_workflows":
                    result = await self.export_workflows(arguments.get("output_path", "/tmp/n8n-backup.json"))
                else:
                    result = f"❌ Unknown tool: {name}"

                return [TextContent(type="text", text=result)]

            except Exception as e:
                error_msg = f"❌ Error executing {name}: {str(e)}"
                return [TextContent(type="text", text=error_msg)]

    # ===== HELPER METHODS =====

    def _api_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make API request to n8n"""
        url = urljoin(N8N_API_URL, endpoint)

        try:
            response = session.request(method, url, **kwargs)
            response.raise_for_status()

            # Handle empty responses
            if response.status_code == 204 or not response.content:
                return {"success": True}

            return response.json()

        except requests.exceptions.HTTPError as e:
            error_data = {}
            try:
                error_data = e.response.json()
            except:
                error_data = {"message": e.response.text}

            raise Exception(f"HTTP {e.response.status_code}: {error_data.get('message', str(e))}")

        except Exception as e:
            raise Exception(f"API request failed: {str(e)}")

    # ===== WORKFLOW MANAGEMENT =====

    async def list_workflows(self, filters: Dict) -> str:
        """List all workflows with optional filters"""
        try:
            # Build query parameters
            params = {}
            if "active" in filters:
                params["active"] = str(filters["active"]).lower()
            if "tags" in filters:
                params["tags"] = filters["tags"]

            # Get workflows
            data = self._api_request("GET", "/api/v1/workflows", params=params)
            workflows = data.get("data", [])

            # Apply limit
            limit = filters.get("limit", 50)
            workflows = workflows[:limit]

            if not workflows:
                return "No workflows found."

            # Format output
            output = [f"Found {len(workflows)} workflows:\n"]

            for wf in workflows:
                status = "🟢 ACTIVE" if wf.get("active") else "⚪ INACTIVE"
                name = wf.get("name", "Unnamed")
                wf_id = wf.get("id", "N/A")
                nodes = len(wf.get("nodes", []))
                tags = ", ".join([t.get("name", "") for t in wf.get("tags", [])])

                output.append(f"\n{status} {name} (ID: {wf_id})")
                output.append(f"   Nodes: {nodes}")
                if tags:
                    output.append(f"   Tags: {tags}")

                # Show last update
                updated = wf.get("updatedAt", "")
                if updated:
                    output.append(f"   Updated: {updated[:10]}")

            return "".join(output)

        except Exception as e:
            return f"❌ Failed to list workflows: {str(e)}"

    async def get_workflow(self, workflow_id: str) -> str:
        """Get detailed workflow information"""
        try:
            data = self._api_request("GET", f"/api/v1/workflows/{workflow_id}")

            # Format output
            wf = data.get("data", data)
            output = [f"📊 Workflow Details: {wf.get('name', 'Unnamed')}\n"]
            output.append(f"ID: {wf.get('id')}")
            output.append(f"Status: {'🟢 ACTIVE' if wf.get('active') else '⚪ INACTIVE'}")
            output.append(f"Nodes: {len(wf.get('nodes', []))}")
            output.append(f"Created: {wf.get('createdAt', 'N/A')[:10]}")
            output.append(f"Updated: {wf.get('updatedAt', 'N/A')[:10]}")

            # Tags
            tags = [t.get("name", "") for t in wf.get("tags", [])]
            if tags:
                output.append(f"Tags: {', '.join(tags)}")

            # Node summary
            nodes = wf.get("nodes", [])
            if nodes:
                output.append(f"\nNodes ({len(nodes)}):")
                for node in nodes:
                    node_type = node.get("type", "Unknown")
                    node_name = node.get("name", "Unnamed")
                    output.append(f"  - {node_name} ({node_type})")

            # Include full JSON for advanced users
            output.append(f"\n\n--- Full Workflow JSON ---")
            output.append(json.dumps(wf, indent=2))

            return "\n".join(output)

        except Exception as e:
            return f"❌ Failed to get workflow: {str(e)}"

    async def create_workflow(self, workflow_data: Dict) -> str:
        """Create new workflow"""
        try:
            # Build workflow object
            workflow = {
                "name": workflow_data["name"],
                "nodes": workflow_data["nodes"],
                "connections": workflow_data["connections"],
                "active": workflow_data.get("active", False),
                "settings": workflow_data.get("settings", {}),
            }

            # Add tags if provided
            if "tags" in workflow_data:
                workflow["tags"] = [{"name": tag} for tag in workflow_data["tags"]]

            # Create workflow
            data = self._api_request("POST", "/api/v1/workflows", json=workflow)
            result = data.get("data", data)

            return f"✅ Workflow created successfully!\n\nID: {result.get('id')}\nName: {result.get('name')}\nStatus: {'🟢 ACTIVE' if result.get('active') else '⚪ INACTIVE'}"

        except Exception as e:
            return f"❌ Failed to create workflow: {str(e)}"

    async def update_workflow(self, updates: Dict) -> str:
        """Update existing workflow"""
        try:
            workflow_id = updates.pop("workflow_id")

            # Get current workflow first
            current = self._api_request("GET", f"/api/v1/workflows/{workflow_id}")
            workflow = current.get("data", current)

            # Apply updates
            for key, value in updates.items():
                if key == "tags" and value:
                    workflow["tags"] = [{"name": tag} for tag in value]
                else:
                    workflow[key] = value

            # Update workflow
            data = self._api_request("PUT", f"/api/v1/workflows/{workflow_id}", json=workflow)
            result = data.get("data", data)

            return f"✅ Workflow updated successfully!\n\nID: {result.get('id')}\nName: {result.get('name')}\nStatus: {'🟢 ACTIVE' if result.get('active') else '⚪ INACTIVE'}"

        except Exception as e:
            return f"❌ Failed to update workflow: {str(e)}"

    async def delete_workflow(self, workflow_id: str) -> str:
        """Delete workflow"""
        try:
            self._api_request("DELETE", f"/api/v1/workflows/{workflow_id}")
            return f"✅ Workflow {workflow_id} deleted successfully."

        except Exception as e:
            return f"❌ Failed to delete workflow: {str(e)}"

    async def activate_workflow(self, workflow_id: str, active: bool) -> str:
        """Activate or deactivate workflow"""
        try:
            # Get current workflow
            current = self._api_request("GET", f"/api/v1/workflows/{workflow_id}")
            workflow = current.get("data", current)

            # Update active status
            workflow["active"] = active

            # Save
            self._api_request("PUT", f"/api/v1/workflows/{workflow_id}", json=workflow)

            status = "activated" if active else "deactivated"
            return f"✅ Workflow {workflow_id} {status} successfully."

        except Exception as e:
            return f"❌ Failed to activate/deactivate workflow: {str(e)}"

    async def duplicate_workflow(self, workflow_id: str, new_name: str) -> str:
        """Duplicate workflow with new name"""
        try:
            # Get source workflow
            current = self._api_request("GET", f"/api/v1/workflows/{workflow_id}")
            workflow = current.get("data", current)

            # Modify for duplication
            workflow["name"] = new_name
            workflow["active"] = False  # Duplicates start inactive
            workflow.pop("id", None)  # Remove ID
            workflow.pop("createdAt", None)
            workflow.pop("updatedAt", None)

            # Create new workflow
            data = self._api_request("POST", "/api/v1/workflows", json=workflow)
            result = data.get("data", data)

            return f"✅ Workflow duplicated successfully!\n\nNew ID: {result.get('id')}\nName: {result.get('name')}\nStatus: ⚪ INACTIVE (activate manually)"

        except Exception as e:
            return f"❌ Failed to duplicate workflow: {str(e)}"

    # ===== EXECUTION CONTROL =====

    async def list_executions(self, filters: Dict) -> str:
        """List workflow executions"""
        try:
            # Build query parameters
            params = {}
            if "workflow_id" in filters:
                params["workflowId"] = filters["workflow_id"]
            if "status" in filters:
                params["status"] = filters["status"]

            limit = filters.get("limit", 20)
            params["limit"] = limit

            # Get executions
            data = self._api_request("GET", "/api/v1/executions", params=params)
            executions = data.get("data", [])

            if not executions:
                return "No executions found."

            # Format output
            output = [f"Found {len(executions)} executions:\n"]

            for ex in executions:
                status_icon = {
                    "success": "✅",
                    "error": "❌",
                    "running": "🔄",
                    "waiting": "⏳",
                    "canceled": "⛔"
                }.get(ex.get("status", "unknown"), "❓")

                ex_id = ex.get("id", "N/A")
                workflow_name = ex.get("workflowData", {}).get("name", "Unknown")
                status = ex.get("status", "unknown").upper()
                started = ex.get("startedAt", "")[:19]

                output.append(f"\n{status_icon} Execution {ex_id}")
                output.append(f"   Workflow: {workflow_name}")
                output.append(f"   Status: {status}")
                output.append(f"   Started: {started}")

                # Show duration if finished
                if ex.get("stoppedAt"):
                    stopped = ex.get("stoppedAt", "")[:19]
                    output.append(f"   Finished: {stopped}")

            return "".join(output)

        except Exception as e:
            return f"❌ Failed to list executions: {str(e)}"

    async def get_execution(self, execution_id: str) -> str:
        """Get detailed execution data"""
        try:
            data = self._api_request("GET", f"/api/v1/executions/{execution_id}")
            ex = data.get("data", data)

            # Format output
            status_icon = {
                "success": "✅",
                "error": "❌",
                "running": "🔄",
                "waiting": "⏳",
                "canceled": "⛔"
            }.get(ex.get("status", "unknown"), "❓")

            output = [f"{status_icon} Execution Details: {ex.get('id')}\n"]
            output.append(f"Workflow: {ex.get('workflowData', {}).get('name', 'Unknown')}")
            output.append(f"Status: {ex.get('status', 'unknown').upper()}")
            output.append(f"Started: {ex.get('startedAt', 'N/A')[:19]}")

            if ex.get("stoppedAt"):
                output.append(f"Stopped: {ex.get('stoppedAt')[:19]}")

            # Node execution data
            exec_data = ex.get("data", {})
            if exec_data:
                output.append(f"\nNode Execution Results:")
                result_data = exec_data.get("resultData", {})
                runs = result_data.get("runData", {})

                for node_name, node_runs in runs.items():
                    if node_runs:
                        node_status = "✅ SUCCESS" if not node_runs[0].get("error") else "❌ ERROR"
                        output.append(f"\n  {node_name}: {node_status}")

                        # Show error if present
                        if node_runs[0].get("error"):
                            error_msg = node_runs[0].get("error", {}).get("message", "Unknown error")
                            output.append(f"    Error: {error_msg}")

            # Include full JSON
            output.append(f"\n\n--- Full Execution JSON ---")
            output.append(json.dumps(ex, indent=2))

            return "\n".join(output)

        except Exception as e:
            return f"❌ Failed to get execution: {str(e)}"

    async def trigger_workflow(self, workflow_id: str, input_data: Optional[Dict]) -> str:
        """Manually trigger workflow"""
        try:
            # Prepare request
            payload = {}
            if input_data:
                payload["data"] = input_data

            # Trigger workflow
            data = self._api_request("POST", f"/api/v1/workflows/{workflow_id}/execute", json=payload)
            result = data.get("data", data)

            return f"✅ Workflow triggered successfully!\n\nExecution ID: {result.get('id')}\nStatus: {result.get('status', 'running').upper()}"

        except Exception as e:
            return f"❌ Failed to trigger workflow: {str(e)}"

    async def retry_execution(self, execution_id: str) -> str:
        """Retry failed execution"""
        try:
            data = self._api_request("POST", f"/api/v1/executions/{execution_id}/retry")
            result = data.get("data", data)

            return f"✅ Execution retry initiated!\n\nNew Execution ID: {result.get('id')}"

        except Exception as e:
            return f"❌ Failed to retry execution: {str(e)}"

    async def cancel_execution(self, execution_id: str) -> str:
        """Cancel running execution"""
        try:
            self._api_request("POST", f"/api/v1/executions/{execution_id}/stop")
            return f"✅ Execution {execution_id} canceled successfully."

        except Exception as e:
            return f"❌ Failed to cancel execution: {str(e)}"

    async def delete_execution(self, execution_id: str) -> str:
        """Delete execution record"""
        try:
            self._api_request("DELETE", f"/api/v1/executions/{execution_id}")
            return f"✅ Execution {execution_id} deleted successfully."

        except Exception as e:
            return f"❌ Failed to delete execution: {str(e)}"

    # ===== CREDENTIAL MANAGEMENT =====

    async def list_credentials(self, cred_type: Optional[str]) -> str:
        """List all credentials"""
        try:
            params = {}
            if cred_type:
                params["type"] = cred_type

            data = self._api_request("GET", "/api/v1/credentials", params=params)
            credentials = data.get("data", [])

            if not credentials:
                return "No credentials found."

            # Format output (exclude sensitive data)
            output = [f"Found {len(credentials)} credentials:\n"]

            for cred in credentials:
                cred_id = cred.get("id", "N/A")
                name = cred.get("name", "Unnamed")
                cred_type = cred.get("type", "Unknown")

                output.append(f"\n🔑 {name} (ID: {cred_id})")
                output.append(f"   Type: {cred_type}")
                output.append(f"   Updated: {cred.get('updatedAt', 'N/A')[:10]}")

            return "".join(output)

        except Exception as e:
            return f"❌ Failed to list credentials: {str(e)}"

    async def get_credential(self, credential_id: str) -> str:
        """Get credential details (without sensitive data)"""
        try:
            data = self._api_request("GET", f"/api/v1/credentials/{credential_id}")
            cred = data.get("data", data)

            output = [f"🔑 Credential Details: {cred.get('name', 'Unnamed')}\n"]
            output.append(f"ID: {cred.get('id')}")
            output.append(f"Type: {cred.get('type')}")
            output.append(f"Created: {cred.get('createdAt', 'N/A')[:10]}")
            output.append(f"Updated: {cred.get('updatedAt', 'N/A')[:10]}")
            output.append(f"\nNote: Sensitive credential data is not displayed for security.")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Failed to get credential: {str(e)}"

    async def create_credential(self, cred_data: Dict) -> str:
        """Create new credential"""
        try:
            credential = {
                "name": cred_data["name"],
                "type": cred_data["type"],
                "data": cred_data["data"]
            }

            data = self._api_request("POST", "/api/v1/credentials", json=credential)
            result = data.get("data", data)

            return f"✅ Credential created successfully!\n\nID: {result.get('id')}\nName: {result.get('name')}\nType: {result.get('type')}"

        except Exception as e:
            return f"❌ Failed to create credential: {str(e)}"

    async def delete_credential(self, credential_id: str) -> str:
        """Delete credential"""
        try:
            self._api_request("DELETE", f"/api/v1/credentials/{credential_id}")
            return f"✅ Credential {credential_id} deleted successfully."

        except Exception as e:
            return f"❌ Failed to delete credential: {str(e)}"

    # ===== MONITORING & ANALYTICS =====

    async def get_stats(self) -> str:
        """Get n8n statistics"""
        try:
            # Get workflows
            workflows_data = self._api_request("GET", "/api/v1/workflows")
            workflows = workflows_data.get("data", [])
            active_workflows = sum(1 for wf in workflows if wf.get("active"))

            # Get executions (last 100)
            executions_data = self._api_request("GET", "/api/v1/executions", params={"limit": 100})
            executions = executions_data.get("data", [])

            # Count by status
            success = sum(1 for ex in executions if ex.get("status") == "success")
            error = sum(1 for ex in executions if ex.get("status") == "error")
            running = sum(1 for ex in executions if ex.get("status") == "running")

            success_rate = (success / len(executions) * 100) if executions else 0

            # Get credentials
            creds_data = self._api_request("GET", "/api/v1/credentials")
            credentials = creds_data.get("data", [])

            # Format output
            output = ["📊 n8n Statistics\n"]
            output.append(f"Total Workflows: {len(workflows)}")
            output.append(f"Active Workflows: {active_workflows}")
            output.append(f"Inactive Workflows: {len(workflows) - active_workflows}")
            output.append(f"\nRecent Executions (last 100):")
            output.append(f"  ✅ Success: {success}")
            output.append(f"  ❌ Error: {error}")
            output.append(f"  🔄 Running: {running}")
            output.append(f"  Success Rate: {success_rate:.1f}%")
            output.append(f"\nCredentials: {len(credentials)}")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Failed to get stats: {str(e)}"

    async def get_workflow_stats(self, workflow_id: str, days: int) -> str:
        """Get workflow-specific performance metrics"""
        try:
            # Get workflow details
            workflow_data = self._api_request("GET", f"/api/v1/workflows/{workflow_id}")
            workflow = workflow_data.get("data", workflow_data)

            # Get executions for this workflow
            executions_data = self._api_request("GET", "/api/v1/executions",
                                               params={"workflowId": workflow_id, "limit": 100})
            executions = executions_data.get("data", [])

            # Filter by date range
            cutoff = datetime.now() - timedelta(days=days)
            recent_executions = [
                ex for ex in executions
                if ex.get("startedAt") and datetime.fromisoformat(ex["startedAt"].replace("Z", "+00:00")) > cutoff
            ]

            # Calculate stats
            total = len(recent_executions)
            success = sum(1 for ex in recent_executions if ex.get("status") == "success")
            error = sum(1 for ex in recent_executions if ex.get("status") == "error")

            success_rate = (success / total * 100) if total else 0

            # Calculate average duration
            durations = []
            for ex in recent_executions:
                if ex.get("startedAt") and ex.get("stoppedAt"):
                    start = datetime.fromisoformat(ex["startedAt"].replace("Z", "+00:00"))
                    stop = datetime.fromisoformat(ex["stoppedAt"].replace("Z", "+00:00"))
                    duration = (stop - start).total_seconds()
                    durations.append(duration)

            avg_duration = sum(durations) / len(durations) if durations else 0

            # Format output
            output = [f"📈 Workflow Performance: {workflow.get('name', 'Unknown')}\n"]
            output.append(f"Period: Last {days} days")
            output.append(f"\nExecution Count: {total}")
            output.append(f"  ✅ Success: {success}")
            output.append(f"  ❌ Error: {error}")
            output.append(f"  Success Rate: {success_rate:.1f}%")
            output.append(f"\nAverage Duration: {avg_duration:.1f} seconds")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Failed to get workflow stats: {str(e)}"

    async def get_execution_summary(self, start_date: str, end_date: str) -> str:
        """Get execution summary by date range"""
        try:
            # Get all executions (limited to 500 for performance)
            executions_data = self._api_request("GET", "/api/v1/executions", params={"limit": 500})
            executions = executions_data.get("data", [])

            # Parse dates
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)

            # Filter by date range
            filtered = []
            for ex in executions:
                if ex.get("startedAt"):
                    ex_date = datetime.fromisoformat(ex["startedAt"].replace("Z", "+00:00"))
                    if start <= ex_date < end:
                        filtered.append(ex)

            # Calculate stats
            total = len(filtered)
            success = sum(1 for ex in filtered if ex.get("status") == "success")
            error = sum(1 for ex in filtered if ex.get("status") == "error")
            running = sum(1 for ex in filtered if ex.get("status") == "running")

            success_rate = (success / total * 100) if total else 0

            # Group by workflow
            by_workflow = {}
            for ex in filtered:
                wf_name = ex.get("workflowData", {}).get("name", "Unknown")
                if wf_name not in by_workflow:
                    by_workflow[wf_name] = {"total": 0, "success": 0, "error": 0}

                by_workflow[wf_name]["total"] += 1
                if ex.get("status") == "success":
                    by_workflow[wf_name]["success"] += 1
                elif ex.get("status") == "error":
                    by_workflow[wf_name]["error"] += 1

            # Format output
            output = [f"📊 Execution Summary: {start_date} to {end_date}\n"]
            output.append(f"Total Executions: {total}")
            output.append(f"  ✅ Success: {success}")
            output.append(f"  ❌ Error: {error}")
            output.append(f"  🔄 Running: {running}")
            output.append(f"  Success Rate: {success_rate:.1f}%")

            output.append(f"\n\nBy Workflow:")
            for wf_name, stats in sorted(by_workflow.items(), key=lambda x: x[1]["total"], reverse=True):
                wf_success_rate = (stats["success"] / stats["total"] * 100) if stats["total"] else 0
                output.append(f"\n  {wf_name}")
                output.append(f"    Executions: {stats['total']}")
                output.append(f"    Success Rate: {wf_success_rate:.1f}%")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Failed to get execution summary: {str(e)}"

    async def health_check(self) -> str:
        """Check n8n health status"""
        try:
            # Try to access the API
            response = session.get(urljoin(N8N_API_URL, "/healthz"), timeout=5)

            if response.status_code == 200:
                return f"✅ n8n is healthy and responding.\n\nAPI URL: {N8N_API_URL}\nStatus Code: {response.status_code}"
            else:
                return f"⚠️ n8n responded but status is not OK.\n\nStatus Code: {response.status_code}"

        except Exception as e:
            return f"❌ n8n health check failed: {str(e)}\n\nAPI URL: {N8N_API_URL}"

    # ===== ADMINISTRATION =====

    async def get_settings(self) -> str:
        """Get n8n configuration"""
        try:
            # Note: n8n may not have a public settings endpoint
            # This is a placeholder - adjust based on actual API

            output = ["⚙️ n8n Configuration\n"]
            output.append(f"API URL: {N8N_API_URL}")
            output.append(f"Authentication: {'API Key' if N8N_API_KEY else 'Basic Auth'}")
            output.append(f"\nNote: Full settings may not be accessible via API for security reasons.")

            return "\n".join(output)

        except Exception as e:
            return f"❌ Failed to get settings: {str(e)}"

    async def export_workflows(self, output_path: str) -> str:
        """Export all workflows as JSON backup"""
        try:
            # Get all workflows
            workflows_data = self._api_request("GET", "/api/v1/workflows")
            workflows = workflows_data.get("data", [])

            if not workflows:
                return "No workflows to export."

            # Create backup
            backup = {
                "timestamp": datetime.now().isoformat(),
                "n8n_url": N8N_API_URL,
                "workflow_count": len(workflows),
                "workflows": workflows
            }

            # Save to file
            with open(output_path, "w") as f:
                json.dump(backup, f, indent=2)

            # Calculate file size
            file_size = os.path.getsize(output_path)
            size_kb = file_size / 1024

            return f"✅ Workflows exported successfully!\n\nFile: {output_path}\nWorkflows: {len(workflows)}\nSize: {size_kb:.1f} KB"

        except Exception as e:
            return f"❌ Failed to export workflows: {str(e)}"

    async def run(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


# ===== MAIN =====

def main():
    """Main entry point"""
    server = N8NMCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()
