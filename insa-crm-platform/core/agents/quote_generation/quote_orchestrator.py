"""
Quote Generation Orchestrator
Main agent that coordinates all quote generation components
"""

import json
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import structlog

from .config import config
from .rag_knowledge_base import RAGKnowledgeBase
from .requirement_extractor import RequirementExtractor
from .bom_generator import BOMGeneratorAgent
from .labor_estimator import LaborEstimatorAgent
from .pricing_strategy import PricingStrategyAgent

logger = structlog.get_logger()


class QuoteOrchestrator:
    """
    Main orchestrator for AI quote generation
    Coordinates all sub-agents to produce complete quotes in <5 minutes
    """

    def __init__(self):
        """Initialize orchestrator and all sub-agents"""
        logger.info("Initializing Quote Orchestrator")

        # Initialize all agents
        self.rag = RAGKnowledgeBase()
        self.req_extractor = RequirementExtractor()
        self.bom_generator = BOMGeneratorAgent()
        self.labor_estimator = LaborEstimatorAgent()
        self.pricing_agent = PricingStrategyAgent()

        # Ensure storage directories exist
        os.makedirs(config.quotes_storage_path, exist_ok=True)

        logger.info("Quote Orchestrator initialized successfully")

    def generate_quote(
        self,
        requirement_source: str,
        customer_name: str,
        customer_email: str,
        source_type: str = "text",
        customer_context: Optional[Dict[str, Any]] = None,
        auto_approve_threshold: float = 0.85
    ) -> Dict[str, Any]:
        """
        Generate a complete quote from requirements

        Args:
            requirement_source: Requirements text or file path
            customer_name: Customer name
            customer_email: Customer email
            source_type: "text", "pdf", "docx", or "auto"
            customer_context: Optional customer history/context
            auto_approve_threshold: Confidence threshold for auto-approval

        Returns:
            Complete quote dictionary
        """
        try:
            quote_id = self._generate_quote_id()
            start_time = datetime.utcnow()

            logger.info("Starting quote generation",
                       quote_id=quote_id,
                       customer=customer_name,
                       source_type=source_type)

            # STEP 1: Extract requirements
            logger.info("Step 1/6: Extracting requirements", quote_id=quote_id)
            requirements = self._extract_requirements(requirement_source, source_type)

            # STEP 2: Find similar projects (RAG)
            logger.info("Step 2/6: Finding similar projects", quote_id=quote_id)
            similar_projects = self._find_similar_projects(requirements)

            # STEP 3: Generate BOM
            logger.info("Step 3/6: Generating BOM", quote_id=quote_id)
            bom = self.bom_generator.generate_bom(requirements, similar_projects)

            # STEP 4: Estimate labor
            logger.info("Step 4/6: Estimating labor", quote_id=quote_id)
            labor_estimate = self.labor_estimator.estimate_labor(
                requirements,
                bom,
                similar_projects
            )

            # STEP 5: Calculate pricing
            logger.info("Step 5/6: Calculating pricing", quote_id=quote_id)
            pricing = self.pricing_agent.calculate_pricing(
                bom,
                labor_estimate,
                requirements,
                similar_projects,
                customer_context
            )

            # STEP 6: Build final quote
            logger.info("Step 6/6: Building final quote", quote_id=quote_id)
            quote = self._build_quote(
                quote_id,
                customer_name,
                customer_email,
                requirements,
                similar_projects,
                bom,
                labor_estimate,
                pricing,
                start_time
            )

            # Determine if auto-approval
            overall_confidence = self._calculate_overall_confidence(
                requirements,
                bom,
                labor_estimate,
                pricing
            )

            quote['approval'] = {
                "overall_confidence": round(overall_confidence, 2),
                "auto_approve_threshold": auto_approve_threshold,
                "requires_review": overall_confidence < auto_approve_threshold,
                "recommended_action": self._get_recommended_action(overall_confidence, pricing)
            }

            # Save quote
            self._save_quote(quote)

            end_time = datetime.utcnow()
            generation_time = (end_time - start_time).total_seconds()

            quote['metadata']['generation_time_seconds'] = round(generation_time, 1)

            logger.info("Quote generation complete",
                       quote_id=quote_id,
                       total_price=pricing['pricing']['total'],
                       confidence=overall_confidence,
                       generation_time=generation_time,
                       requires_review=quote['approval']['requires_review'])

            return quote

        except Exception as e:
            logger.error("Quote generation failed", error=str(e))
            raise

    def _extract_requirements(self, source: str, source_type: str) -> Dict[str, Any]:
        """Extract requirements from source"""
        if source_type == "text":
            return self.req_extractor.extract_from_text(source)
        elif source_type == "pdf":
            return self.req_extractor.extract_from_pdf(source)
        elif source_type == "docx":
            return self.req_extractor.extract_from_docx(source)
        elif source_type == "auto":
            return self.req_extractor.extract_from_file(source)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

    def _find_similar_projects(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar historical projects using RAG"""
        # Build search text from requirements
        search_text = self._build_search_text(requirements)

        # Query RAG database
        similar = self.rag.find_similar_projects(
            requirement_text=search_text,
            n_results=5,
            filters={"industry": requirements.get('industry')} if requirements.get('industry') != "Unknown" else None
        )

        return similar

    def _build_search_text(self, requirements: Dict[str, Any]) -> str:
        """Build search text from requirements for RAG lookup"""
        parts = []

        # Project scope
        scope = requirements.get('project_scope', {})
        parts.append(scope.get('summary', ''))

        # Technical requirements
        tech_req = requirements.get('technical_requirements', {})
        if 'plc' in tech_req:
            parts.append(f"PLC: {tech_req['plc'].get('vendor', '')}")
        if 'hmi_scada' in tech_req:
            parts.append(f"HMI: {tech_req['hmi_scada'].get('type', '')}")

        # Standards
        standards = requirements.get('compliance_standards', [])
        if standards:
            parts.append(f"Standards: {', '.join(standards)}")

        # Industry
        parts.append(f"Industry: {requirements.get('industry', '')}")

        return " ".join(parts)

    def _build_quote(
        self,
        quote_id: str,
        customer_name: str,
        customer_email: str,
        requirements: Dict[str, Any],
        similar_projects: List[Dict[str, Any]],
        bom: Dict[str, Any],
        labor_estimate: Dict[str, Any],
        pricing: Dict[str, Any],
        start_time: datetime
    ) -> Dict[str, Any]:
        """Build final quote structure"""

        return {
            "quote_id": quote_id,
            "version": "1.0",
            "customer": {
                "name": customer_name,
                "email": customer_email
            },
            "metadata": {
                "generated_date": start_time.isoformat(),
                "generated_by": "INSA AI Quote Generation Agent",
                "valid_until": pricing['validity']['expiration_date'],
                "similar_projects_count": len(similar_projects),
                "status": "draft"
            },
            "project_overview": {
                "scope": requirements.get('project_scope', {}),
                "industry": requirements.get('industry', 'Unknown'),
                "compliance_standards": requirements.get('compliance_standards', []),
                "timeline": requirements.get('project_timeline', {}),
                "complexity_score": requirements.get('complexity_score', 0),
                "deliverables": requirements.get('deliverables', [])
            },
            "technical_solution": {
                "requirements": requirements.get('technical_requirements', {}),
                "site_information": requirements.get('site_information', {}),
            },
            "bill_of_materials": bom,
            "labor_estimate": labor_estimate,
            "pricing": pricing,
            "similar_projects": [
                {
                    "project_code": p['project_code'],
                    "similarity_score": p['similarity_score'],
                    "customer": p['metadata'].get('customer', 'Unknown')
                }
                for p in similar_projects[:3]  # Top 3 only
            ],
            "notes": {
                "requirements_notes": requirements.get('missing_information', []),
                "bom_notes": bom.get('notes', []),
                "labor_notes": labor_estimate.get('notes', []),
                "pricing_notes": pricing.get('pricing_notes', [])
            }
        }

    def _calculate_overall_confidence(
        self,
        requirements: Dict[str, Any],
        bom: Dict[str, Any],
        labor_estimate: Dict[str, Any],
        pricing: Dict[str, Any]
    ) -> float:
        """Calculate overall quote confidence score"""

        # Weighted average of component confidences
        req_conf = requirements.get('confidence_score', 0.5)
        bom_conf = bom.get('confidence', 0.5)
        labor_conf = labor_estimate.get('confidence', 0.5)
        pricing_conf = pricing.get('confidence', 0.5)

        # Requirements are most important (40%), then labor (30%), pricing (20%), BOM (10%)
        overall = (
            req_conf * 0.40 +
            labor_conf * 0.30 +
            pricing_conf * 0.20 +
            bom_conf * 0.10
        )

        return overall

    def _get_recommended_action(self, confidence: float, pricing: Dict[str, Any]) -> str:
        """Get recommended action based on confidence and pricing"""

        win_prob = pricing.get('win_probability', 0.3)

        if confidence >= 0.85 and win_prob >= 0.50:
            return "SEND_IMMEDIATELY"
        elif confidence >= 0.70 and win_prob >= 0.40:
            return "REVIEW_AND_SEND"
        elif confidence >= 0.60:
            return "REFINE_REQUIREMENTS"
        else:
            return "SCHEDULE_DISCOVERY_CALL"

    def _generate_quote_id(self) -> str:
        """Generate unique quote ID"""
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        return f"Q-{timestamp}"

    def _save_quote(self, quote: Dict[str, Any]) -> str:
        """Save quote to storage"""
        quote_id = quote['quote_id']
        filepath = Path(config.quotes_storage_path) / f"{quote_id}.json"

        with open(filepath, 'w') as f:
            json.dump(quote, f, indent=2)

        logger.info("Quote saved", quote_id=quote_id, path=str(filepath))
        return str(filepath)

    def index_reference_projects(self) -> int:
        """Index all reference projects into RAG database"""
        logger.info("Indexing reference projects")
        count = self.rag.index_all_reference_projects()
        logger.info("Reference projects indexed", count=count)
        return count

    def get_quote(self, quote_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve saved quote"""
        filepath = Path(config.quotes_storage_path) / f"{quote_id}.json"

        if not filepath.exists():
            return None

        with open(filepath, 'r') as f:
            return json.load(f)

    def list_quotes(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent quotes"""
        quotes_dir = Path(config.quotes_storage_path)

        if not quotes_dir.exists():
            return []

        quote_files = sorted(
            quotes_dir.glob("Q-*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]

        quotes = []
        for filepath in quote_files:
            try:
                with open(filepath, 'r') as f:
                    quote = json.load(f)
                    quotes.append({
                        "quote_id": quote['quote_id'],
                        "customer": quote['customer']['name'],
                        "generated_date": quote['metadata']['generated_date'],
                        "total_price": quote['pricing']['pricing']['total'],
                        "status": quote['metadata']['status'],
                        "requires_review": quote.get('approval', {}).get('requires_review', True)
                    })
            except Exception as e:
                logger.error("Failed to load quote", file=str(filepath), error=str(e))

        return quotes
