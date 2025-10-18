"""
API v1 Router
"""

from fastapi import APIRouter
from .endpoints import leads, agents, mcp_status

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(mcp_status.router, prefix="/mcp", tags=["mcp"])
