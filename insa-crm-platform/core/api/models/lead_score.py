"""
Lead Scoring Model
AI-generated lead qualification scores
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Enum, Float
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class LeadPriority(str, enum.Enum):
    """Lead priority classification"""
    IMMEDIATE = "immediate"  # Score 80-100
    HIGH = "high"  # Score 60-79
    MEDIUM = "medium"  # Score 40-59
    LOW = "low"  # Score 0-39


class RecommendedAction(str, enum.Enum):
    """Recommended next action"""
    IMMEDIATE_CONTACT = "immediate_contact"
    SCHEDULE_DEMO = "schedule_demo"
    SEND_PROPOSAL = "send_proposal"
    NURTURE = "nurture"
    DISQUALIFY = "disqualify"


class LeadScore(Base):
    """AI-generated lead qualification score"""

    __tablename__ = "lead_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ERPNext Lead reference
    lead_id = Column(String(100), unique=True, nullable=False, index=True)
    lead_name = Column(String(200), nullable=False)

    # Scoring
    qualification_score = Column(Integer, nullable=False)  # 0-100
    priority = Column(Enum(LeadPriority), nullable=False, index=True)
    recommended_action = Column(Enum(RecommendedAction), nullable=False)

    # AI reasoning
    reasoning = Column(Text, nullable=False)  # Claude's explanation
    confidence_level = Column(Float, nullable=False)  # 0.0-1.0

    # Scoring factors
    budget_score = Column(Integer, nullable=True)  # 0-100
    timeline_score = Column(Integer, nullable=True)
    technical_complexity_score = Column(Integer, nullable=True)
    decision_authority_score = Column(Integer, nullable=True)
    fit_score = Column(Integer, nullable=True)

    # Agent execution reference
    agent_execution_id = Column(Integer, nullable=True, index=True)

    # Timestamps
    scored_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Human override
    human_override_score = Column(Integer, nullable=True)
    override_reason = Column(Text, nullable=True)
    overridden_by = Column(String(100), nullable=True)
    overridden_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<LeadScore(lead_id={self.lead_id}, score={self.qualification_score}, priority={self.priority})>"
