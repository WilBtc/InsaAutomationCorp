"""
Agent Status and Control Endpoints
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import structlog

from api.core.database import get_db
from api.models.agent_execution import AgentExecution, AgentType, AgentStatus

logger = structlog.get_logger()
router = APIRouter()


@router.get("/executions")
async def list_agent_executions(
    limit: int = 50,
    agent_type: str = None,
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    """List recent agent executions"""
    query = select(AgentExecution).order_by(AgentExecution.started_at.desc()).limit(limit)

    if agent_type:
        query = query.where(AgentExecution.agent_type == agent_type)

    if status:
        query = query.where(AgentExecution.status == status)

    result = await db.execute(query)
    executions = result.scalars().all()

    return {
        "total": len(executions),
        "executions": [
            {
                "id": e.id,
                "agent_type": e.agent_type.value,
                "status": e.status.value,
                "started_at": e.started_at.isoformat(),
                "completed_at": e.completed_at.isoformat() if e.completed_at else None,
                "duration_ms": e.execution_duration_ms,
                "tokens_used": e.tokens_used,
                "cost_usd": e.estimated_cost_usd / 100 if e.estimated_cost_usd else 0,
                "customer_id": e.customer_id,
                "lead_id": e.lead_id
            }
            for e in executions
        ]
    }


@router.get("/stats")
async def agent_statistics(db: AsyncSession = Depends(get_db)):
    """Get agent execution statistics"""

    # Total executions
    total_result = await db.execute(select(func.count(AgentExecution.id)))
    total_executions = total_result.scalar()

    # By status
    status_result = await db.execute(
        select(AgentExecution.status, func.count(AgentExecution.id))
        .group_by(AgentExecution.status)
    )
    by_status = {row[0].value: row[1] for row in status_result}

    # By agent type
    type_result = await db.execute(
        select(AgentExecution.agent_type, func.count(AgentExecution.id))
        .group_by(AgentExecution.agent_type)
    )
    by_type = {row[0].value: row[1] for row in type_result}

    # Total tokens
    tokens_result = await db.execute(
        select(func.sum(AgentExecution.tokens_used))
    )
    total_tokens = tokens_result.scalar() or 0

    # Total cost
    cost_result = await db.execute(
        select(func.sum(AgentExecution.estimated_cost_usd))
    )
    total_cost_cents = cost_result.scalar() or 0

    return {
        "total_executions": total_executions,
        "by_status": by_status,
        "by_type": by_type,
        "total_tokens_used": total_tokens,
        "total_cost_usd": total_cost_cents / 100,
        "average_cost_per_execution": (total_cost_cents / 100 / total_executions) if total_executions > 0 else 0
    }
