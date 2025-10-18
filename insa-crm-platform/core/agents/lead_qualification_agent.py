"""
Lead Qualification Agent - MVP
AI-powered lead scoring for industrial automation projects

Analyzes leads based on:
- Budget indicators
- Project timeline urgency
- Technical complexity (IEC 62443, PLC programming, etc.)
- Decision authority
- Industry fit

Uses Claude Code via MCP tools (no API key needed)
"""

import json
import structlog
from typing import Dict, Any
from datetime import datetime
import asyncio

logger = structlog.get_logger()


class LeadQualificationAgent:
    """
    AI agent for qualifying industrial automation leads
    """

    # System prompt for Claude
    SYSTEM_PROMPT = """You are a lead qualification specialist for INSA Automation Corp, an industrial automation engineering company.

We provide three core services:
1. **Industrial Automation**: PLC programming (Siemens, Allen-Bradley), SCADA systems, HMI development, DCS configuration
2. **Energy Optimization**: Energy audits, monitoring systems, efficiency retrofits, renewable integration
3. **Industrial Cybersecurity**: IEC 62443 compliance, ICS security audits, OT network segmentation

## Qualification Criteria:

### Budget Score (0-25 points)
- $100K+ project value: 25 points
- $50K-$100K: 20 points
- $25K-$50K: 15 points
- $10K-$25K: 10 points
- Under $10K: 5 points
- Unknown budget: Infer from project scope

### Timeline Score (0-25 points)
- Urgent (< 3 months): 25 points
- Soon (3-6 months): 20 points
- Mid-term (6-12 months): 15 points
- Long-term (> 12 months): 10 points
- No timeline: 5 points

### Technical Complexity Score (0-25 points)
- IEC 62443 compliance required: 25 points (high value, complex)
- Multi-site project: 20 points
- SCADA/DCS integration: 18 points
- PLC programming only: 15 points
- Energy audit: 12 points
- Simple equipment: 8 points

### Decision Authority Score (0-15 points)
- C-level (CEO, CTO, COO): 15 points
- VP/Director: 12 points
- Manager: 9 points
- Engineer/Technician: 5 points
- Unknown: 3 points

### Industry Fit Score (0-10 points)
- Manufacturing/Process: 10 points (perfect fit)
- Utilities/Energy: 10 points
- Oil & Gas: 10 points
- Water/Wastewater: 9 points
- Food & Beverage: 8 points
- Other industrial: 6 points
- Non-industrial: 2 points

## Recommended Actions:
- **80-100 points**: IMMEDIATE_CONTACT (high-value, urgent)
- **60-79 points**: SCHEDULE_DEMO (strong fit)
- **40-59 points**: SEND_PROPOSAL (moderate fit, needs nurturing)
- **20-39 points**: NURTURE (low urgency or budget)
- **0-19 points**: DISQUALIFY (poor fit)

## Response Format:
Provide a JSON response with:
{
  "qualification_score": 85,
  "budget_score": 25,
  "timeline_score": 25,
  "technical_complexity_score": 20,
  "decision_authority_score": 12,
  "fit_score": 10,
  "priority": "IMMEDIATE",
  "recommended_action": "IMMEDIATE_CONTACT",
  "reasoning": "Detailed explanation of scoring...",
  "confidence_level": 0.9,
  "key_factors": ["High budget", "IEC 62443 compliance", "C-level contact"],
  "risk_factors": ["Tight timeline may require additional resources"],
  "next_steps": ["Contact within 24 hours", "Prepare IEC 62443 compliance overview"]
}

Be thorough but concise. Justify your scoring."""

    def __init__(self):
        self.agent_type = "lead_qualification"
        self.model = "claude-sonnet-4-5-20250929"  # Use Sonnet for quality

    async def qualify_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Qualify a lead using Claude Code

        Args:
            lead_data: Dictionary containing lead information from ERPNext
                - lead_name: str
                - company_name: str
                - email: str
                - phone: str
                - source: str
                - industry: str
                - status: str
                - notes: str (project description)
                - custom fields...

        Returns:
            Qualification results with score, priority, recommended action
        """
        logger.info("qualifying_lead", lead_id=lead_data.get("name"))

        try:
            # Format lead data for analysis
            lead_context = self._format_lead_context(lead_data)

            # In a real implementation, this would use Claude Code SDK
            # For now, we'll simulate the response structure
            qualification_result = await self._analyze_with_claude(lead_context)

            logger.info(
                "lead_qualified",
                lead_id=lead_data.get("name"),
                score=qualification_result["qualification_score"],
                priority=qualification_result["priority"]
            )

            return qualification_result

        except Exception as e:
            logger.error("lead_qualification_failed", lead_id=lead_data.get("name"), error=str(e))
            raise

    def _format_lead_context(self, lead_data: Dict[str, Any]) -> str:
        """Format lead data into a context string for Claude"""
        context = f"""# Lead Information

**Lead ID**: {lead_data.get('name', 'Unknown')}
**Company**: {lead_data.get('company_name', 'Unknown')}
**Contact**: {lead_data.get('lead_name', 'Unknown')}
**Title**: {lead_data.get('designation', 'Unknown')}
**Email**: {lead_data.get('email_id', 'Not provided')}
**Phone**: {lead_data.get('phone', 'Not provided')}
**Industry**: {lead_data.get('industry', 'Unknown')}
**Source**: {lead_data.get('source', 'Unknown')}
**Status**: {lead_data.get('status', 'New')}

## Project Description:
{lead_data.get('notes', 'No description provided')}

## Requirements (if provided):
- Budget: {lead_data.get('custom_budget', 'Not specified')}
- Timeline: {lead_data.get('custom_timeline', 'Not specified')}
- Project Type: {lead_data.get('custom_project_type', 'Not specified')}
- Services Needed: {lead_data.get('custom_services', 'Not specified')}

Please analyze this lead and provide a comprehensive qualification score."""

        return context

    async def _analyze_with_claude(self, lead_context: str) -> Dict[str, Any]:
        """
        Call Claude for analysis

        NOTE: In production, this would use the Claude Code SDK:

        from claude_code_sdk import ClaudeAgent

        agent = ClaudeAgent(
            system_prompt=self.SYSTEM_PROMPT,
            model=self.model,
            allowed_tools=["mcp__erpnext__update_lead"]
        )

        response = await agent.query(lead_context)
        return json.loads(response.content)
        """

        # For now, return a simulated response structure
        # This demonstrates what the agent would return
        logger.info("simulating_claude_analysis")

        # Simulate processing time
        await asyncio.sleep(0.5)

        # Example response structure
        return {
            "qualification_score": 85,
            "budget_score": 25,
            "timeline_score": 20,
            "technical_complexity_score": 25,
            "decision_authority_score": 12,
            "fit_score": 10,
            "priority": "IMMEDIATE",
            "recommended_action": "IMMEDIATE_CONTACT",
            "reasoning": """This is a high-value opportunity for INSA Automation Corp:

1. **Strong Budget Indicators** (25/25): Project scope suggests $100K+ value based on IEC 62443 compliance requirements and multi-system integration.

2. **Good Timeline** (20/25): 4-month timeline is achievable and shows serious intent.

3. **High Technical Complexity** (25/25): IEC 62443 compliance is one of our specialties and commands premium pricing. This aligns perfectly with our cybersecurity service line.

4. **Decision Authority** (12/15): Contact is Engineering Manager - likely has budget authority or direct access to decision-makers.

5. **Perfect Industry Fit** (10/10): Manufacturing sector is our core market.

**Total: 92/100 - IMMEDIATE PRIORITY**""",
            "confidence_level": 0.92,
            "key_factors": [
                "IEC 62443 compliance required (high-value service)",
                "Manufacturing industry (perfect fit)",
                "Clear technical scope",
                "Reasonable timeline"
            ],
            "risk_factors": [
                "Need to confirm exact budget availability",
                "May require specialized IEC 62443 resources"
            ],
            "next_steps": [
                "Contact within 24 hours",
                "Prepare IEC 62443 compliance overview presentation",
                "Schedule on-site assessment if possible",
                "Involve cybersecurity team lead in discovery call"
            ],
            "analyzed_at": datetime.utcnow().isoformat()
        }

    async def save_qualification_to_db(
        self,
        lead_id: str,
        qualification: Dict[str, Any],
        db_session
    ):
        """Save qualification results to PostgreSQL"""
        from api.models.lead_score import LeadScore, LeadPriority, RecommendedAction

        # Map string values to enums
        priority_map = {
            "IMMEDIATE": LeadPriority.IMMEDIATE,
            "HIGH": LeadPriority.HIGH,
            "MEDIUM": LeadPriority.MEDIUM,
            "LOW": LeadPriority.LOW
        }

        action_map = {
            "IMMEDIATE_CONTACT": RecommendedAction.IMMEDIATE_CONTACT,
            "SCHEDULE_DEMO": RecommendedAction.SCHEDULE_DEMO,
            "SEND_PROPOSAL": RecommendedAction.SEND_PROPOSAL,
            "NURTURE": RecommendedAction.NURTURE,
            "DISQUALIFY": RecommendedAction.DISQUALIFY
        }

        lead_score = LeadScore(
            lead_id=lead_id,
            lead_name=qualification.get("lead_name", "Unknown"),
            qualification_score=qualification["qualification_score"],
            priority=priority_map.get(qualification["priority"], LeadPriority.MEDIUM),
            recommended_action=action_map.get(
                qualification["recommended_action"],
                RecommendedAction.NURTURE
            ),
            reasoning=qualification["reasoning"],
            confidence_level=qualification["confidence_level"],
            budget_score=qualification.get("budget_score"),
            timeline_score=qualification.get("timeline_score"),
            technical_complexity_score=qualification.get("technical_complexity_score"),
            decision_authority_score=qualification.get("decision_authority_score"),
            fit_score=qualification.get("fit_score")
        )

        db_session.add(lead_score)
        await db_session.commit()
        await db_session.refresh(lead_score)

        logger.info("lead_score_saved", lead_id=lead_id, score_id=lead_score.id)
        return lead_score


# Global agent instance
lead_qualification_agent = LeadQualificationAgent()
