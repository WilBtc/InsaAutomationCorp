"""
MCP Server Manager
Coordinates multiple MCP servers for the CRM system
"""

import structlog
from typing import Dict, Any
from contextlib import asynccontextmanager

logger = structlog.get_logger()


class MCPServerManager:
    """
    Manages MCP server connections
    Coordinates between ERPNext, PostgreSQL, Security Tools, etc.
    """

    def __init__(self):
        self.servers: Dict[str, Any] = {}
        self.initialized = False

    async def initialize(self):
        """Initialize all MCP servers"""
        if self.initialized:
            logger.warning("mcp_manager_already_initialized")
            return

        logger.info("initializing_mcp_servers")

        # Note: In production, these would connect to actual MCP servers
        # For now, we'll register them for reference
        self.servers = {
            "erpnext": {
                "type": "erpnext-crm",
                "status": "configured",
                "description": "ERPNext CRM integration (existing MCP server)"
            },
            "postgres": {
                "type": "postgresql",
                "status": "pending",
                "description": "PostgreSQL direct access for agent execution logs"
            },
            "security": {
                "type": "security-tools",
                "status": "pending",
                "description": "Security assessment tools (Nmap, IEC 62443 checks)"
            },
            "inventree": {
                "type": "inventree",
                "status": "not_installed",
                "description": "InvenTree BOM and parts management"
            },
            "qdrant": {
                "type": "qdrant",
                "status": "not_configured",
                "description": "Qdrant vector database for RAG"
            },
            "freecad": {
                "type": "freecad-automation",
                "status": "future",
                "description": "FreeCAD P&ID diagram generation"
            }
        }

        self.initialized = True
        logger.info("mcp_servers_registered", count=len(self.servers))

    async def shutdown(self):
        """Shutdown all MCP servers"""
        logger.info("shutting_down_mcp_servers")
        # Close connections here
        self.initialized = False

    def get_available_tools(self, server_name: str) -> list:
        """Get available tools from a specific MCP server"""
        if server_name not in self.servers:
            return []

        # Map server names to their tools
        tool_map = {
            "erpnext": [
                "erpnext_list_leads",
                "erpnext_create_lead",
                "erpnext_get_lead",
                "erpnext_update_lead",
                "erpnext_create_opportunity",
                "erpnext_create_customer",
                "erpnext_get_crm_analytics"
            ],
            "postgres": [
                "save_agent_execution",
                "get_customer_history",
                "query_lead_scores"
            ],
            "security": [
                "scan_ot_network",
                "check_iec62443_compliance",
                "analyze_vulnerabilities"
            ]
        }

        return tool_map.get(server_name, [])

    def get_server_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers"""
        return {
            "initialized": self.initialized,
            "servers": self.servers,
            "total_servers": len(self.servers),
            "active_servers": sum(1 for s in self.servers.values() if s["status"] == "configured")
        }


# Global MCP manager instance
mcp_manager = MCPServerManager()
