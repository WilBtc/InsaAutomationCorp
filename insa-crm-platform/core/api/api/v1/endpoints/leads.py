"""
Lead Management Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import structlog

from api.core.database import get_db
import sys
from pathlib import Path
# Add project root to path to import agents
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
from agents.lead_qualification_agent import lead_qualification_agent

logger = structlog.get_logger()
router = APIRouter()


@router.post("/qualify/{lead_id}")
async def qualify_lead(
    lead_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger AI qualification for a lead

    This endpoint:
    1. Fetches lead from ERPNext (via MCP)
    2. Spawns Lead Qualification Agent
    3. Returns immediately (processing in background)
    4. Agent saves results to PostgreSQL
    """
    logger.info("lead_qualification_requested", lead_id=lead_id)

    # In production, fetch from ERPNext via MCP
    # For now, use sample data
    lead_data = {
        "name": lead_id,
        "lead_name": "John Smith",
        "company_name": "Acme Manufacturing",
        "designation": "Engineering Manager",
        "email_id": "jsmith@acme.com",
        "industry": "Manufacturing",
        "source": "Website",
        "notes": """We need help with IEC 62443 compliance for our production facility.

        Current environment:
        - 15 Allen-Bradley PLCs
        - Wonderware SCADA system
        - Unpatched Windows 7 HMIs
        - No network segmentation

        Timeline: 4-6 months
        Budget: To be discussed but approved for $150K""",
        "custom_project_type": "Industrial Cybersecurity",
        "custom_services": "IEC 62443 Compliance, Network Segmentation, SCADA Security"
    }

    # Queue agent execution in background
    background_tasks.add_task(
        _execute_qualification,
        lead_id,
        lead_data,
        db
    )

    return {
        "status": "processing",
        "lead_id": lead_id,
        "message": "Lead qualification in progress"
    }


async def _execute_qualification(lead_id: str, lead_data: dict, db: AsyncSession):
    """Background task for lead qualification"""
    try:
        # Run qualification agent
        result = await lead_qualification_agent.qualify_lead(lead_data)

        # Save to database
        await lead_qualification_agent.save_qualification_to_db(
            lead_id=lead_id,
            qualification=result,
            db_session=db
        )

        logger.info(
            "lead_qualification_completed",
            lead_id=lead_id,
            score=result["qualification_score"]
        )

    except Exception as e:
        logger.error(
            "lead_qualification_failed",
            lead_id=lead_id,
            error=str(e)
        )


@router.get("/scores")
async def list_lead_scores(
    limit: int = 50,
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all lead scores with optional filtering

    Query parameters:
    - limit: Max results (default 50)
    - priority: Filter by priority (IMMEDIATE, HIGH, MEDIUM, LOW)
    """
    from api.models.lead_score import LeadScore, LeadPriority
    from sqlalchemy import select

    query = select(LeadScore).order_by(LeadScore.scored_at.desc()).limit(limit)

    if priority:
        try:
            priority_enum = LeadPriority(priority.lower())
            query = query.where(LeadScore.priority == priority_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid priority: {priority}")

    result = await db.execute(query)
    scores = result.scalars().all()

    return {
        "total": len(scores),
        "scores": [
            {
                "lead_id": s.lead_id,
                "lead_name": s.lead_name,
                "score": s.qualification_score,
                "priority": s.priority.value,
                "recommended_action": s.recommended_action.value,
                "reasoning": s.reasoning,
                "confidence": s.confidence_level,
                "scored_at": s.scored_at.isoformat()
            }
            for s in scores
        ]
    }


@router.get("/scores/{lead_id}")
async def get_lead_score(
    lead_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get qualification score for a specific lead"""
    from api.models.lead_score import LeadScore
    from sqlalchemy import select

    result = await db.execute(
        select(LeadScore).where(LeadScore.lead_id == lead_id)
    )
    score = result.scalar_one_or_none()

    if not score:
        raise HTTPException(status_code=404, detail="Lead score not found")

    return {
        "lead_id": score.lead_id,
        "lead_name": score.lead_name,
        "qualification_score": score.qualification_score,
        "priority": score.priority.value,
        "recommended_action": score.recommended_action.value,
        "reasoning": score.reasoning,
        "confidence_level": score.confidence_level,
        "factor_scores": {
            "budget": score.budget_score,
            "timeline": score.timeline_score,
            "technical_complexity": score.technical_complexity_score,
            "decision_authority": score.decision_authority_score,
            "fit": score.fit_score
        },
        "scored_at": score.scored_at.isoformat(),
        "human_override": {
            "score": score.human_override_score,
            "reason": score.override_reason,
            "by": score.overridden_by,
            "at": score.overridden_at.isoformat() if score.overridden_at else None
        } if score.human_override_score else None
    }
