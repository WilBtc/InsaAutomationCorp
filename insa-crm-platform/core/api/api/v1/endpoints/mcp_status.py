"""
MCP Server Status Endpoints
"""

from fastapi import APIRouter
import structlog

from api.core.mcp_manager import mcp_manager

logger = structlog.get_logger()
router = APIRouter()


@router.get("/status")
async def mcp_server_status():
    """Get status of all MCP servers"""
    status = mcp_manager.get_server_status()

    return {
        "mcp_manager_initialized": status["initialized"],
        "total_servers": status["total_servers"],
        "active_servers": status["active_servers"],
        "servers": status["servers"]
    }


@router.get("/servers/{server_name}/tools")
async def list_server_tools(server_name: str):
    """List available tools for a specific MCP server"""
    tools = mcp_manager.get_available_tools(server_name)

    if not tools:
        return {
            "server": server_name,
            "status": "not_found_or_no_tools",
            "tools": []
        }

    return {
        "server": server_name,
        "tool_count": len(tools),
        "tools": tools
    }
