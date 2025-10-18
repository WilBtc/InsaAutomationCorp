"""
Agent Execution Tracking Model
Stores audit trail of all AI agent executions
"""

from sqlalchemy import Column, String, Integer, DateTime, JSON, Text, Enum
from sqlalchemy.sql import func
import enum

from ..core.database import Base


class AgentStatus(str, enum.Enum):
    """Agent execution status"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class AgentType(str, enum.Enum):
    """Types of AI agents"""
    LEAD_QUALIFICATION = "lead_qualification"
    QUOTE_GENERATION = "quote_generation"
    SECURITY_ASSESSMENT = "security_assessment"
    PROPOSAL_WRITING = "proposal_writing"
    TECHNICAL_DESIGN = "technical_design"
    COMPLIANCE_TRACKING = "compliance_tracking"


class AgentExecution(Base):
    """Agent execution audit log"""

    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Agent info
    agent_type = Column(Enum(AgentType), nullable=False, index=True)
    agent_model = Column(String(100), nullable=False)  # claude-sonnet, haiku, etc.

    # Execution tracking
    status = Column(Enum(AgentStatus), nullable=False, default=AgentStatus.QUEUED, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Input/Output
    input_data = Column(JSON, nullable=False)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # Cost tracking
    tokens_used = Column(Integer, default=0)
    estimated_cost_usd = Column(Integer, default=0)  # Store as cents

    # Related entities
    customer_id = Column(String(100), nullable=True, index=True)
    lead_id = Column(String(100), nullable=True, index=True)
    opportunity_id = Column(String(100), nullable=True, index=True)
    project_id = Column(String(100), nullable=True, index=True)

    # User context
    triggered_by = Column(String(100), nullable=True)  # User ID or 'system'

    # Metadata
    mcp_tools_used = Column(JSON, nullable=True)  # List of MCP tools called
    execution_duration_ms = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<AgentExecution(id={self.id}, type={self.agent_type}, status={self.status})>"
