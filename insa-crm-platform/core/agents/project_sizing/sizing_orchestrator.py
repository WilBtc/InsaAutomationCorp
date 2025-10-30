"""
Sizing Orchestrator - Master coordinator for project dimensioning
Orchestrates classification, estimation, and document prediction
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from project_classifier import ProjectClassifier
from discipline_estimator import DisciplineEstimator
from document_predictor import DocumentPredictor
from config import SIZING_RESULTS_DIR, CONFIDENCE_THRESHOLDS


class SizingOrchestrator:
    """
    Master orchestrator for INSA Project Sizing Agent

    Coordinates all sizing components:
    1. Project Classification (type, complexity, disciplines)
    2. Discipline Estimation (hours, cost, personnel)
    3. Document Prediction (deliverables list)
    4. RAG Knowledge Base (similar projects)
    5. ERPNext Integration (project creation)

    Provides complete project sizing in <2 seconds
    """

    def __init__(self):
        self.classifier = ProjectClassifier()
        self.estimator = DisciplineEstimator()
        self.predictor = DocumentPredictor()

    def size_project(
        self,
        project_description: str,
        customer_name: Optional[str] = None,
        country: str = "colombia",
        project_parameters: Optional[Dict] = None,
        customer_requirements: Optional[List[str]] = None,
        save_results: bool = True
    ) -> Dict:
        """
        Complete project sizing from description to detailed estimate

        Args:
            project_description: Natural language project description
            customer_name: Customer name (for repeat project detection)
            country: Project country (colombia/ecuador/usa)
            project_parameters: Optional parameters (io_count, tank_count, etc)
            customer_requirements: Custom document requirements
            save_results: Save results to disk (default True)

        Returns:
            Complete sizing with classification, estimation, documents
        """

        start_time = datetime.now()

        # ====================================================================
        # STEP 1: CLASSIFY PROJECT
        # ====================================================================
        print("🔍 Step 1/5: Classifying project...")

        classification = self.classifier.classify(
            project_description=project_description,
            customer_name=customer_name,
            country=country,
            additional_context=project_parameters
        )

        print(f"   ✓ Type: {classification['project_type']}")
        print(f"   ✓ Complexity: {classification['complexity']}")
        print(f"   ✓ Disciplines: {len(classification['required_disciplines'])}")
        print(f"   ✓ Confidence: {classification['overall_confidence']:.1%}")

        # ====================================================================
        # STEP 2: FIND SIMILAR PROJECTS (RAG)
        # ====================================================================
        print("\n📚 Step 2/5: Searching for similar projects (RAG)...")

        similar_projects = self._find_similar_projects(
            classification,
            customer_name
        )

        if similar_projects:
            print(f"   ✓ Found {len(similar_projects)} similar project(s)")
        else:
            print("   ℹ No similar projects found - using reference baseline")

        # ====================================================================
        # STEP 3: ESTIMATE PROJECT
        # ====================================================================
        print("\n💼 Step 3/5: Estimating effort across all disciplines...")

        estimation = self.estimator.estimate_project(
            project_classification=classification,
            project_parameters=project_parameters,
            similar_projects=similar_projects
        )

        print(f"   ✓ Total Hours: {estimation['total_hours']:.1f}")
        print(f"   ✓ Total Cost: ${estimation['total_cost']:,.2f}")
        print(f"   ✓ Duration: {estimation['project_duration_weeks']} weeks")
        print(f"   ✓ Confidence: {estimation['overall_confidence']:.1%}")

        # ====================================================================
        # STEP 4: PREDICT DOCUMENTS
        # ====================================================================
        print("\n📄 Step 4/5: Predicting required documents...")

        document_prediction = self.predictor.predict_documents(
            project_classification=classification,
            discipline_estimation=estimation,
            country=country,
            customer_requirements=customer_requirements
        )

        print(f"   ✓ Total Documents: {document_prediction['total_documents']}")
        print(f"   ✓ Templates Available: {len(document_prediction['templates_available'])}")

        # ====================================================================
        # STEP 5: ASSEMBLE COMPLETE SIZING
        # ====================================================================
        print("\n🎯 Step 5/5: Assembling complete project sizing...")

        end_time = datetime.now()
        duration_seconds = (end_time - start_time).total_seconds()

        sizing_result = {
            "sizing_id": self._generate_sizing_id(),
            "timestamp": start_time.isoformat(),
            "generation_time_seconds": round(duration_seconds, 2),

            # Input data
            "input": {
                "project_description": project_description,
                "customer_name": customer_name,
                "country": country,
                "project_parameters": project_parameters or {},
                "customer_requirements": customer_requirements or []
            },

            # Classification results
            "classification": classification,

            # Estimation results
            "estimation": estimation,

            # Document prediction
            "documents": document_prediction,

            # Similar projects used
            "similar_projects_used": len(similar_projects) if similar_projects else 0,

            # Overall assessment
            "assessment": self._assess_sizing(
                classification,
                estimation,
                document_prediction
            ),

            # Next steps recommendation
            "recommended_actions": self._recommend_actions(
                classification,
                estimation,
                document_prediction
            )
        }

        print(f"\n✅ Project sizing completed in {duration_seconds:.2f} seconds!")

        # ====================================================================
        # SAVE RESULTS
        # ====================================================================
        if save_results:
            saved_path = self._save_sizing_result(sizing_result)
            sizing_result["saved_to"] = saved_path
            print(f"   💾 Results saved to: {saved_path}")

        return sizing_result

    def _find_similar_projects(
        self,
        classification: Dict,
        customer_name: Optional[str]
    ) -> Optional[List[Dict]]:
        """
        Find similar projects from RAG knowledge base

        Future: Query ChromaDB for vector similarity
        Currently: Returns reference project if applicable
        """

        project_type = classification.get("project_type")

        # For now, return reference project if it matches type
        if project_type == "separator":
            # Return INSAGTEC-6598 reference data
            from config import REFERENCE_PROJECT_HOURS
            return [REFERENCE_PROJECT_HOURS]

        # Future: Query RAG database
        # similar = self.rag_kb.query(
        #     project_type=project_type,
        #     complexity=classification['complexity'],
        #     customer=customer_name,
        #     top_k=3
        # )

        return None

    def _assess_sizing(
        self,
        classification: Dict,
        estimation: Dict,
        documents: Dict
    ) -> Dict:
        """
        Assess overall quality and confidence of sizing
        """

        # Calculate weighted confidence
        classification_conf = classification.get("overall_confidence", 0.7)
        estimation_conf = estimation.get("overall_confidence", 0.7)

        # Weighted average (estimation is more critical)
        overall_confidence = (classification_conf * 0.4) + (estimation_conf * 0.6)

        # Determine confidence level
        if overall_confidence >= CONFIDENCE_THRESHOLDS["high"]:
            confidence_level = "HIGH"
            confidence_desc = "High confidence - sizing ready for quotation"
        elif overall_confidence >= CONFIDENCE_THRESHOLDS["medium"]:
            confidence_level = "MEDIUM"
            confidence_desc = "Medium confidence - recommend review by senior engineer"
        else:
            confidence_level = "LOW"
            confidence_desc = "Low confidence - requires detailed project scoping"

        # Risk assessment
        risks = []

        if estimation["total_hours"] > 1000:
            risks.append("Large project scope - resource availability critical")

        if estimation["project_duration_weeks"] > 24:
            risks.append("Long duration - schedule risk and resource leveling required")

        if estimation["personnel_required"].get("specialist", 0) > 1:
            risks.append("Specialist expertise required - early allocation needed")

        if classification.get("classification_method") == "hybrid_low_confidence":
            risks.append("Ambiguous project description - clarify requirements")

        # Opportunities
        opportunities = []

        if "repeat_project" in classification.get("complexity_factors", []):
            opportunities.append("Repeat project - efficiency gains possible")

        if classification.get("project_type") == "separator":
            opportunities.append("Reference project available (INSAGTEC-6598) - high accuracy")

        if estimation["total_hours"] < 300:
            opportunities.append("Small project - fast turnaround possible")

        return {
            "overall_confidence": overall_confidence,
            "confidence_level": confidence_level,
            "confidence_description": confidence_desc,
            "risks": risks,
            "opportunities": opportunities,
            "ready_for_quotation": overall_confidence >= CONFIDENCE_THRESHOLDS["medium"]
        }

    def _recommend_actions(
        self,
        classification: Dict,
        estimation: Dict,
        documents: Dict
    ) -> List[str]:
        """
        Recommend next actions based on sizing results
        """

        actions = []

        overall_conf = (classification.get("overall_confidence", 0.7) * 0.4 +
                       estimation.get("overall_confidence", 0.7) * 0.6)

        # Confidence-based actions
        if overall_conf >= CONFIDENCE_THRESHOLDS["high"]:
            actions.append("✅ PROCEED: Generate detailed quotation using Quote Generation Agent")
            actions.append("📋 NEXT: Create project in ERPNext with estimated hours/cost")
        elif overall_conf >= CONFIDENCE_THRESHOLDS["medium"]:
            actions.append("⚠️ REVIEW: Have senior engineer review sizing estimate")
            actions.append("📞 CLARIFY: Schedule customer call to confirm requirements")
        else:
            actions.append("🔍 INVESTIGATE: Conduct detailed project scoping session")
            actions.append("📄 REQUEST: Ask customer for technical specifications/drawings")

        # Project-specific actions
        if estimation["total_cost"] > 100000:
            actions.append("💰 ESCALATE: High-value project - require management approval")

        if "cybersecurity" in classification.get("required_disciplines", []):
            actions.append("🔒 ASSIGN: Allocate cybersecurity specialist early (IEC 62443)")

        if "scada_integration" in classification.get("complexity_factors", []):
            actions.append("🖥️ CONFIRM: Verify SCADA platform compatibility with customer")

        # Resource actions
        specialists_needed = estimation["personnel_required"].get("specialist", 0)
        if specialists_needed > 0:
            actions.append(f"👨‍🎓 RESOURCE: Identify and allocate {specialists_needed:.1f} FTE specialist(s)")

        # Document actions
        if documents["total_documents"] > 50:
            actions.append("📚 TEMPLATE: Set up document management system and templates")

        return actions

    def _generate_sizing_id(self) -> str:
        """
        Generate unique sizing ID

        Format: SZ-YYYYMMDDHHMMSS
        Example: SZ-20251019164530
        """

        return f"SZ-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def _save_sizing_result(self, sizing_result: Dict) -> str:
        """
        Save sizing result to disk
        """

        sizing_id = sizing_result["sizing_id"]
        filename = f"{sizing_id}_project_sizing.json"
        filepath = SIZING_RESULTS_DIR / filename

        # Ensure directory exists
        SIZING_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

        # Save JSON
        with open(filepath, "w") as f:
            json.dump(sizing_result, f, indent=2)

        # Also save human-readable summary
        summary_path = SIZING_RESULTS_DIR / f"{sizing_id}_summary.txt"
        with open(summary_path, "w") as f:
            f.write(self._generate_summary_report(sizing_result))

        return str(filepath)

    def _generate_summary_report(self, sizing: Dict) -> str:
        """
        Generate human-readable summary report
        """

        classification = sizing["classification"]
        estimation = sizing["estimation"]
        documents = sizing["documents"]
        assessment = sizing["assessment"]

        report = f"""
================================================================================
INSA PROJECT SIZING SUMMARY
================================================================================

Sizing ID: {sizing['sizing_id']}
Generated: {sizing['timestamp']}
Generation Time: {sizing['generation_time_seconds']} seconds

================================================================================
PROJECT OVERVIEW
================================================================================

Customer: {sizing['input']['customer_name'] or 'Unknown'}
Country: {sizing['input']['country'].upper()}

Project Description:
{sizing['input']['project_description']}

================================================================================
CLASSIFICATION
================================================================================

Project Type: {classification['project_type'].upper()}
Variant: {classification.get('variant', 'Standard')}
Complexity: {classification['complexity'].upper()}

Required Disciplines ({len(classification['required_disciplines'])}):
"""

        for disc in classification['required_disciplines']:
            from config import INSA_DISCIPLINES
            disc_name = INSA_DISCIPLINES.get(disc, {}).get("name", disc)
            report += f"  • {disc_name}\n"

        if classification.get('complexity_factors'):
            report += f"\nComplexity Factors ({len(classification['complexity_factors'])}):\n"
            for factor in classification['complexity_factors']:
                from config import COMPLEXITY_FACTORS
                desc = COMPLEXITY_FACTORS[factor]["description"]
                mult = COMPLEXITY_FACTORS[factor]["multiplier"]
                report += f"  • {desc} (×{mult})\n"

        report += f"""
Classification Confidence: {classification['overall_confidence']:.1%}

================================================================================
EFFORT ESTIMATION
================================================================================

Total Hours: {estimation['total_hours']:.1f} hours
Total Cost: ${estimation['total_cost']:,.2f} USD
Project Duration: {estimation['project_duration_weeks']} weeks

Personnel Required:
"""

        for level, fte in estimation['personnel_required'].items():
            report += f"  • {level.replace('_', ' ').title()}: {fte:.2f} FTE\n"

        report += "\nEffort by Discipline:\n"
        for disc, details in estimation['disciplines'].items():
            report += f"  • {details['discipline_name']}: {details['total_hours']:.1f}h | ${details['total_cost']:,.2f}\n"

        report += "\nEffort by Phase:\n"
        for phase, details in estimation['phases'].items():
            report += f"  • {details['phase_name']}: {details['total_hours']:.1f}h | ${details['total_cost']:,.2f}\n"

        report += f"""
Estimation Confidence: {estimation['overall_confidence']:.1%}

================================================================================
DOCUMENTS & DELIVERABLES
================================================================================

Total Documents: {documents['total_documents']}
Templates Available: {len(documents['templates_available'])}

Documents by Phase:
"""

        for phase, details in documents['documents_by_phase'].items():
            report += f"  • {details['phase_name']}: {details['document_count']} documents\n"

        report += f"""
================================================================================
ASSESSMENT
================================================================================

Overall Confidence: {assessment['overall_confidence']:.1%}
Confidence Level: {assessment['confidence_level']}
Ready for Quotation: {'YES' if assessment['ready_for_quotation'] else 'NO'}

{assessment['confidence_description']}

"""

        if assessment['risks']:
            report += "⚠️  RISKS:\n"
            for risk in assessment['risks']:
                report += f"  • {risk}\n"
            report += "\n"

        if assessment['opportunities']:
            report += "✨ OPPORTUNITIES:\n"
            for opp in assessment['opportunities']:
                report += f"  • {opp}\n"
            report += "\n"

        report += f"""
================================================================================
RECOMMENDED ACTIONS
================================================================================

"""

        for action in sizing['recommended_actions']:
            report += f"{action}\n"

        report += f"""
================================================================================
END OF REPORT
================================================================================

Generated by INSA AI Project Sizing Agent (Phase 11)
© 2025 INSA Automation Corp - Made with Claude Code
"""

        return report

    def list_saved_sizings(self, limit: int = 10) -> List[Dict]:
        """
        List recently saved project sizings
        """

        sizing_files = sorted(
            SIZING_RESULTS_DIR.glob("SZ-*_project_sizing.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:limit]

        sizings = []

        for filepath in sizing_files:
            with open(filepath, "r") as f:
                sizing = json.load(f)
                sizings.append({
                    "sizing_id": sizing["sizing_id"],
                    "timestamp": sizing["timestamp"],
                    "project_type": sizing["classification"]["project_type"],
                    "customer": sizing["input"]["customer_name"],
                    "total_hours": sizing["estimation"]["total_hours"],
                    "total_cost": sizing["estimation"]["total_cost"],
                    "confidence": sizing["assessment"]["overall_confidence"],
                    "filepath": str(filepath)
                })

        return sizings

    def load_sizing(self, sizing_id: str) -> Optional[Dict]:
        """
        Load a previously saved sizing by ID
        """

        filepath = SIZING_RESULTS_DIR / f"{sizing_id}_project_sizing.json"

        if filepath.exists():
            with open(filepath, "r") as f:
                return json.load(f)

        return None


# ============================================================================
# CLI Testing
# ============================================================================

if __name__ == "__main__":
    import sys

    print("=" * 70)
    print("INSA AI PROJECT SIZING AGENT - PRODUCTION TEST")
    print("=" * 70)
    print()

    # Initialize orchestrator
    orchestrator = SizingOrchestrator()

    # Test project
    test_description = """
    Three-phase test separator automation project for PAD-3 location at Genesis oil field.

    Requirements:
    - Allen-Bradley CompactLogix PLC with 64 I/O points (48 DI/AI, 16 DO/AO)
    - Weintek HMI with 15 SCADA screens for operator interface
    - Complete instrumentation package: 20 instruments total
      * 6 level sensors (radar, displacer, switches)
      * 8 pressure instruments (transmitters, switches, gauges)
      * 4 temperature sensors (RTDs, thermocouples)
      * 2 flow meters (differential pressure)
    - 2 electrical control panels (PLC panel + low voltage distribution)
    - Cable routing approximately 2.5 km total
    - Separator vessels: 3 vessels (oil, water, gas phases)

    Project located in Colombia - must comply with RETIE electrical standards.
    Timeline is urgent - customer needs completion within 4 months.
    This is a new customer for INSA (Deilim Colombia).

    Similar to previous INSAGTEC-6598 project but slightly larger scope.
    """

    # Project parameters
    parameters = {
        "io_count": 64,
        "instrument_count": 20,
        "panel_count": 2,
        "cable_length_km": 2.5,
        "scada_screens": 15,
        "tank_count": 3,
        "equipment_count": 6
    }

    # Custom requirements
    custom_reqs = [
        "Monthly Progress Reports",
        "Safety Data Sheets (SDS)",
        "RETIE Compliance Certificate"
    ]

    # Size the project
    print("\n🚀 Starting project sizing...\n")

    sizing = orchestrator.size_project(
        project_description=test_description,
        customer_name="Deilim Colombia",
        country="colombia",
        project_parameters=parameters,
        customer_requirements=custom_reqs,
        save_results=True
    )

    # Display key results
    print("\n" + "=" * 70)
    print("KEY RESULTS")
    print("=" * 70)
    print(f"\nSizing ID: {sizing['sizing_id']}")
    print(f"Confidence: {sizing['assessment']['confidence_level']} ({sizing['assessment']['overall_confidence']:.1%})")
    print(f"\nTotal Hours: {sizing['estimation']['total_hours']:.1f}")
    print(f"Total Cost: ${sizing['estimation']['total_cost']:,.2f}")
    print(f"Duration: {sizing['estimation']['project_duration_weeks']} weeks")
    print(f"Documents: {sizing['documents']['total_documents']}")
    print(f"\nGeneration Time: {sizing['generation_time_seconds']:.2f} seconds ⚡")

    print("\n" + "=" * 70)
    print("✅ TEST COMPLETED SUCCESSFULLY")
    print("=" * 70)
