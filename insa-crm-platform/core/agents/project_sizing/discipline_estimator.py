"""
Discipline Estimator - Multi-discipline project effort estimation
Estimates hours, personnel, and costs for each of 13 INSA disciplines
"""

import json
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

from config import (
    INSA_DISCIPLINES,
    PROJECT_PHASES,
    COMPLEXITY_FACTORS,
    REFERENCE_PROJECT_HOURS,
    CONFIDENCE_THRESHOLDS
)


class DisciplineEstimator:
    """
    AI-powered multi-discipline effort estimation

    For each discipline, estimates:
    - Total hours required
    - Hours breakdown by project phase
    - Personnel requirements (Junior/Senior/Specialist)
    - Cost estimation
    - Document count prediction
    - Confidence scores
    """

    def __init__(self):
        self.disciplines = INSA_DISCIPLINES
        self.phases = PROJECT_PHASES
        self.reference_hours = REFERENCE_PROJECT_HOURS

    def estimate_project(
        self,
        project_classification: Dict,
        project_parameters: Optional[Dict] = None,
        similar_projects: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Estimate complete project across all required disciplines

        Args:
            project_classification: Result from ProjectClassifier
            project_parameters: Additional params (tank count, I/O count, etc)
            similar_projects: Historical similar projects from RAG

        Returns:
            Complete project estimation with all disciplines
        """

        required_disciplines = project_classification.get("required_disciplines", [])
        complexity = project_classification.get("complexity", "standard")
        complexity_factors = project_classification.get("complexity_factors", [])
        project_type = project_classification.get("project_type", "unknown")

        # Initialize results
        estimation = {
            "project_type": project_type,
            "complexity": complexity,
            "timestamp": datetime.now().isoformat(),
            "disciplines": {},
            "total_hours": 0,
            "total_cost": 0,
            "project_duration_weeks": 0,
            "personnel_required": {},
            "overall_confidence": 0.0
        }

        # Estimate each required discipline
        discipline_confidences = []

        for discipline in required_disciplines:
            disc_estimate = self._estimate_discipline(
                discipline=discipline,
                project_type=project_type,
                complexity=complexity,
                complexity_factors=complexity_factors,
                project_parameters=project_parameters,
                similar_projects=similar_projects
            )

            estimation["disciplines"][discipline] = disc_estimate
            estimation["total_hours"] += disc_estimate["total_hours"]
            estimation["total_cost"] += disc_estimate["total_cost"]
            discipline_confidences.append(disc_estimate["confidence"])

            # Aggregate personnel
            for level, count in disc_estimate["personnel"].items():
                estimation["personnel_required"][level] = \
                    estimation["personnel_required"].get(level, 0) + count

        # Calculate project duration (critical path)
        estimation["project_duration_weeks"] = self._calculate_duration(
            estimation["disciplines"],
            complexity_factors
        )

        # Calculate overall confidence
        if discipline_confidences:
            estimation["overall_confidence"] = sum(discipline_confidences) / len(discipline_confidences)
        else:
            estimation["overall_confidence"] = 0.5

        # Add phase breakdown
        estimation["phases"] = self._aggregate_phases(estimation["disciplines"])

        # Add recommendations
        estimation["recommendations"] = self._generate_recommendations(estimation)

        return estimation

    def _estimate_discipline(
        self,
        discipline: str,
        project_type: str,
        complexity: str,
        complexity_factors: List[str],
        project_parameters: Optional[Dict],
        similar_projects: Optional[List[Dict]]
    ) -> Dict:
        """
        Estimate effort for a single discipline
        """

        # Step 1: Get base hours from reference project or parametric model
        base_hours = self._get_base_hours(discipline, project_type, similar_projects)

        # Step 2: Apply complexity multiplier
        complexity_mult = self.disciplines[discipline]["complexity_multipliers"].get(
            complexity, 1.0
        )
        adjusted_hours = base_hours * complexity_mult

        # Step 3: Apply complexity factors
        for factor in complexity_factors:
            factor_config = COMPLEXITY_FACTORS.get(factor, {})
            factor_mult = factor_config.get("multiplier", 1.0)
            affects = factor_config.get("affects", [])

            # Check if this factor affects this discipline
            if "all" in affects or discipline in affects:
                adjusted_hours *= factor_mult

        # Step 4: Apply parametric adjustments (if parameters provided)
        if project_parameters:
            adjusted_hours = self._apply_parametric_adjustments(
                adjusted_hours,
                discipline,
                project_parameters
            )

        # Step 5: Breakdown by project phase
        phase_breakdown = self._breakdown_by_phase(adjusted_hours, discipline)

        # Step 6: Determine personnel requirements
        personnel = self._determine_personnel(adjusted_hours, discipline, complexity)

        # Step 7: Calculate cost
        hourly_rate = self.disciplines[discipline]["typical_hourly_rate"]
        total_cost = adjusted_hours * hourly_rate

        # Step 8: Estimate document count
        document_count = self._estimate_documents(discipline, project_type, complexity)

        # Step 9: Calculate confidence
        confidence = self._calculate_discipline_confidence(
            discipline,
            project_type,
            similar_projects
        )

        return {
            "discipline_name": self.disciplines[discipline]["name"],
            "discipline_code": self.disciplines[discipline]["code"],
            "total_hours": round(adjusted_hours, 1),
            "base_hours": round(base_hours, 1),
            "complexity_multiplier": complexity_mult,
            "phase_breakdown": phase_breakdown,
            "personnel": personnel,
            "hourly_rate": hourly_rate,
            "total_cost": round(total_cost, 2),
            "estimated_documents": document_count,
            "confidence": confidence,
            "estimation_method": "parametric" if similar_projects else "reference"
        }

    def _get_base_hours(
        self,
        discipline: str,
        project_type: str,
        similar_projects: Optional[List[Dict]]
    ) -> float:
        """
        Get base hours for discipline using reference project or similar projects
        """

        # If we have similar projects from RAG, use their average
        if similar_projects:
            discipline_hours = []
            for project in similar_projects:
                hours = project.get("hours_by_discipline", {}).get(discipline)
                if hours:
                    discipline_hours.append(hours)

            if discipline_hours:
                # Weighted average (more recent projects weighted higher)
                avg_hours = sum(discipline_hours) / len(discipline_hours)
                return avg_hours

        # Fallback to reference project
        ref_hours = self.reference_hours.get("hours_by_discipline", {}).get(discipline)

        if ref_hours:
            return ref_hours

        # Final fallback: estimate based on typical percentage
        # These are industry-standard percentages for Oil & Gas automation
        discipline_percentages = {
            "process": 0.08,           # 8% of total
            "instrumentation": 0.25,   # 25% of total (largest)
            "automation": 0.20,        # 20% of total
            "electrical": 0.13,        # 13% of total
            "mechanical": 0.12,        # 12% of total
            "digitalization": 0.08,    # 8% of total
            "cybersecurity": 0.05,     # 5% of total
            "procurement": 0.07,       # 7% of total
            "construction": 0.10,      # 10% of total
            "commissioning": 0.09,     # 9% of total
            "operations": 0.05,        # 5% of total
            "hse": 0.04,               # 4% of total
            "quality": 0.06            # 6% of total
        }

        base_total = self.reference_hours.get("total_hours", 464)
        percentage = discipline_percentages.get(discipline, 0.05)

        return base_total * percentage

    def _apply_parametric_adjustments(
        self,
        base_hours: float,
        discipline: str,
        parameters: Dict
    ) -> float:
        """
        Apply parametric adjustments based on project-specific parameters

        Parameters can include:
        - io_count: Number of I/O points
        - tank_count: Number of tanks
        - instrument_count: Number of instruments
        - panel_count: Number of panels
        - cable_length_km: Total cable length
        - scada_screens: Number of SCADA screens
        """

        adjusted_hours = base_hours

        # Instrumentation: Scale by I/O count or instrument count
        if discipline == "instrumentation":
            io_count = parameters.get("io_count")
            if io_count:
                # Reference: 44 I/O points = 120 hours
                # Linear scaling with diminishing returns
                ref_io = 44
                scale_factor = math.sqrt(io_count / ref_io)
                adjusted_hours *= scale_factor

            instrument_count = parameters.get("instrument_count")
            if instrument_count:
                # Reference: ~15 instruments = 120 hours
                ref_instruments = 15
                scale_factor = math.sqrt(instrument_count / ref_instruments)
                adjusted_hours *= scale_factor

        # Automation: Scale by I/O count and SCADA screens
        elif discipline == "automation":
            io_count = parameters.get("io_count")
            if io_count:
                # PLC programming effort scales with I/O
                ref_io = 44
                scale_factor = (io_count / ref_io) ** 0.8  # Sublinear scaling
                adjusted_hours *= scale_factor

            scada_screens = parameters.get("scada_screens")
            if scada_screens:
                # Each SCADA screen adds effort
                ref_screens = 10
                screen_factor = 1 + (scada_screens - ref_screens) * 0.05
                adjusted_hours *= max(0.5, screen_factor)

        # Electrical: Scale by panel count and cable length
        elif discipline == "electrical":
            panel_count = parameters.get("panel_count", 1)
            if panel_count > 1:
                # Each additional panel adds 70% of base effort
                panel_factor = 1 + (panel_count - 1) * 0.7
                adjusted_hours *= panel_factor

            cable_length_km = parameters.get("cable_length_km")
            if cable_length_km:
                # Cable design effort scales with length
                ref_length = 1.0  # 1 km reference
                length_factor = math.sqrt(cable_length_km / ref_length)
                adjusted_hours *= length_factor

        # Mechanical: Scale by equipment count
        elif discipline == "mechanical":
            equipment_count = parameters.get("equipment_count")
            if equipment_count:
                # Isometrics and supports scale with equipment
                ref_equipment = 5
                equip_factor = (equipment_count / ref_equipment) ** 0.7
                adjusted_hours *= equip_factor

        # Process: Scale by tank/vessel count
        elif discipline == "process":
            tank_count = parameters.get("tank_count")
            if tank_count:
                # P&ID complexity scales with vessel count
                ref_tanks = 3  # Three-phase separator = 3 vessels
                tank_factor = (tank_count / ref_tanks) ** 0.6
                adjusted_hours *= tank_factor

        return adjusted_hours

    def _breakdown_by_phase(self, total_hours: float, discipline: str) -> Dict:
        """
        Breakdown discipline hours by project phase
        """

        # Phase distribution varies by discipline
        phase_distributions = {
            # Engineering-heavy disciplines
            "process": {"phase_0": 0.05, "phase_1": 0.70, "phase_2": 0.10, "phase_3": 0.05, "phase_4": 0.10},
            "instrumentation": {"phase_0": 0.05, "phase_1": 0.60, "phase_2": 0.10, "phase_3": 0.15, "phase_4": 0.10},
            "automation": {"phase_0": 0.05, "phase_1": 0.50, "phase_2": 0.10, "phase_3": 0.15, "phase_4": 0.20},
            "electrical": {"phase_0": 0.05, "phase_1": 0.65, "phase_2": 0.10, "phase_3": 0.15, "phase_4": 0.05},
            "mechanical": {"phase_0": 0.05, "phase_1": 0.65, "phase_2": 0.10, "phase_3": 0.15, "phase_4": 0.05},
            "digitalization": {"phase_0": 0.10, "phase_1": 0.50, "phase_2": 0.10, "phase_3": 0.10, "phase_4": 0.20},

            # Execution-heavy disciplines
            "construction": {"phase_0": 0.05, "phase_1": 0.10, "phase_2": 0.05, "phase_3": 0.70, "phase_4": 0.10},
            "commissioning": {"phase_0": 0.05, "phase_1": 0.10, "phase_2": 0.10, "phase_3": 0.25, "phase_4": 0.50},

            # Support disciplines (distributed throughout)
            "cybersecurity": {"phase_0": 0.10, "phase_1": 0.40, "phase_2": 0.10, "phase_3": 0.20, "phase_4": 0.20},
            "procurement": {"phase_0": 0.05, "phase_1": 0.15, "phase_2": 0.70, "phase_3": 0.05, "phase_4": 0.05},
            "quality": {"phase_0": 0.15, "phase_1": 0.25, "phase_2": 0.15, "phase_3": 0.25, "phase_4": 0.20},
            "hse": {"phase_0": 0.20, "phase_1": 0.20, "phase_2": 0.10, "phase_3": 0.30, "phase_4": 0.20},
            "operations": {"phase_0": 0.05, "phase_1": 0.20, "phase_2": 0.10, "phase_3": 0.15, "phase_4": 0.50},
        }

        distribution = phase_distributions.get(
            discipline,
            {"phase_0": 0.05, "phase_1": 0.40, "phase_2": 0.15, "phase_3": 0.20, "phase_4": 0.20}  # Default
        )

        breakdown = {}
        for phase, percentage in distribution.items():
            phase_name = self.phases[phase]["name"]
            breakdown[phase] = {
                "phase_name": phase_name,
                "hours": round(total_hours * percentage, 1),
                "percentage": percentage * 100
            }

        return breakdown

    def _determine_personnel(
        self,
        total_hours: float,
        discipline: str,
        complexity: str
    ) -> Dict:
        """
        Determine personnel requirements (Junior/Senior/Specialist mix)
        """

        # Personnel mix varies by discipline and complexity
        # Format: {level: percentage}

        if complexity in ["basic", "standard"]:
            # Standard projects: 30% Senior, 60% Mid, 10% Junior
            mix = {"senior": 0.30, "mid_level": 0.60, "junior": 0.10}
        elif complexity == "advanced":
            # Advanced projects: 50% Senior, 40% Mid, 10% Specialist
            mix = {"senior": 0.50, "mid_level": 0.40, "specialist": 0.10}
        else:  # custom
            # Custom projects: 40% Senior, 30% Specialist, 30% Mid
            mix = {"senior": 0.40, "specialist": 0.30, "mid_level": 0.30}

        # Adjust for discipline expertise requirements
        if discipline in ["cybersecurity", "digitalization", "automation"]:
            # Tech disciplines need more senior/specialist
            mix["senior"] = mix.get("senior", 0) + 0.10
            mix["specialist"] = mix.get("specialist", 0) + 0.10
            mix["mid_level"] = mix.get("mid_level", 0) - 0.15
            mix["junior"] = mix.get("junior", 0) - 0.05

        # Calculate FTE (Full Time Equivalent) assuming 40-hour work week
        # and project phases spread over calendar time
        typical_project_weeks = 16
        available_hours_per_person = typical_project_weeks * 40

        total_fte = total_hours / available_hours_per_person

        personnel = {}
        for level, percentage in mix.items():
            if percentage > 0:
                fte = total_fte * percentage
                personnel[level] = round(fte, 2)

        return personnel

    def _estimate_documents(
        self,
        discipline: str,
        project_type: str,
        complexity: str
    ) -> int:
        """
        Estimate number of documents/deliverables for discipline
        """

        # Base document counts from reference project (INSAGTEC-6598)
        base_documents = {
            "quality": 2,
            "instrumentation": 37,
            "electrical": 4,
            "mechanical": 21,
            "automation": 5,  # Estimated (control philosophy, PLC spec, etc)
            "process": 3,     # Estimated (P&ID, process criteria, line list)
            "digitalization": 4,
            "cybersecurity": 3,
            "procurement": 5,
            "construction": 8,
            "commissioning": 6,
            "operations": 4,
            "hse": 5
        }

        base_count = base_documents.get(discipline, 5)

        # Complexity multipliers
        complexity_mult = {
            "basic": 0.6,
            "standard": 1.0,
            "advanced": 1.4,
            "custom": 1.8
        }.get(complexity, 1.0)

        estimated_count = int(base_count * complexity_mult)

        return max(1, estimated_count)  # At least 1 document

    def _calculate_discipline_confidence(
        self,
        discipline: str,
        project_type: str,
        similar_projects: Optional[List[Dict]]
    ) -> float:
        """
        Calculate confidence score for discipline estimation
        """

        confidence = 0.70  # Base confidence

        # Boost if we have similar projects
        if similar_projects and len(similar_projects) > 0:
            confidence += 0.15

        # Boost if discipline is common in this project type
        # (based on reference project data)
        common_disciplines = {
            "separator": ["instrumentation", "automation", "electrical", "mechanical"],
            "compressor": ["mechanical", "instrumentation", "automation"],
            "tank_farm": ["instrumentation", "electrical", "hse"],
            "metering": ["instrumentation", "automation", "quality"],
        }

        if discipline in common_disciplines.get(project_type, []):
            confidence += 0.10

        return min(confidence, 0.95)  # Cap at 95%

    def _calculate_duration(
        self,
        disciplines: Dict,
        complexity_factors: List[str]
    ) -> int:
        """
        Calculate project duration based on critical path

        Uses phase-based calculation with parallel execution
        """

        # Get max hours per phase across all disciplines
        phase_max_hours = {f"phase_{i}": 0 for i in range(5)}

        for discipline, estimate in disciplines.items():
            for phase, phase_data in estimate["phase_breakdown"].items():
                phase_max_hours[phase] = max(
                    phase_max_hours[phase],
                    phase_data["hours"]
                )

        # Calculate weeks per phase (assuming 40-hour work week, some parallel work)
        # Parallelization factor: 0.6 (disciplines can work somewhat in parallel)
        parallelization = 0.6
        total_weeks = 0

        for phase, max_hours in phase_max_hours.items():
            # Convert hours to weeks with parallelization
            phase_weeks = (max_hours * parallelization) / 40

            # Add minimum phase duration (admin overhead)
            phase_min_weeks = self.phases[phase]["typical_duration_weeks"] * 0.3
            phase_weeks = max(phase_weeks, phase_min_weeks)

            total_weeks += phase_weeks

        # Apply complexity factor adjustments
        if "fast_track" in complexity_factors:
            total_weeks *= 0.7  # Compressed schedule

        if "offshore" in complexity_factors:
            total_weeks *= 1.3  # Logistics overhead

        return int(math.ceil(total_weeks))

    def _aggregate_phases(self, disciplines: Dict) -> Dict:
        """
        Aggregate all disciplines by project phase
        """

        phases = {}

        for phase_key in ["phase_0", "phase_1", "phase_2", "phase_3", "phase_4"]:
            phase_name = self.phases[phase_key]["name"]
            phase_hours = 0
            phase_cost = 0

            for discipline, estimate in disciplines.items():
                phase_data = estimate["phase_breakdown"][phase_key]
                phase_hours += phase_data["hours"]
                phase_cost += phase_data["hours"] * estimate["hourly_rate"]

            phases[phase_key] = {
                "phase_name": phase_name,
                "gate": self.phases[phase_key]["gate"],
                "total_hours": round(phase_hours, 1),
                "total_cost": round(phase_cost, 2),
                "typical_duration_weeks": self.phases[phase_key]["typical_duration_weeks"]
            }

        return phases

    def _generate_recommendations(self, estimation: Dict) -> List[str]:
        """
        Generate recommendations based on estimation results
        """

        recommendations = []

        # Check confidence
        if estimation["overall_confidence"] < CONFIDENCE_THRESHOLDS["low"]:
            recommendations.append(
                "⚠️ Low confidence estimation - recommend gathering more project details"
            )

        # Check if project is large
        if estimation["total_hours"] > 1000:
            recommendations.append(
                "📊 Large project (>1000 hours) - recommend phased approach with gates"
            )

        # Check if duration is long
        if estimation["project_duration_weeks"] > 24:
            recommendations.append(
                "⏰ Long duration project (>24 weeks) - consider resource leveling"
            )

        # Check personnel requirements
        total_personnel = sum(estimation["personnel_required"].values())
        if total_personnel > 10:
            recommendations.append(
                f"👥 High personnel requirement ({total_personnel:.1f} FTE) - verify resource availability"
            )

        # Check for specialists
        if estimation["personnel_required"].get("specialist", 0) > 1:
            recommendations.append(
                "🎓 Specialist expertise required - identify and allocate early"
            )

        # Budget threshold check
        if estimation["total_cost"] > 100000:
            recommendations.append(
                f"💰 High-value project (${estimation['total_cost']:,.0f}) - recommend detailed quote review"
            )

        return recommendations


# ============================================================================
# CLI Testing Interface
# ============================================================================

if __name__ == "__main__":
    import sys
    from project_classifier import ProjectClassifier

    print("Testing Discipline Estimator...\n")

    # Step 1: Classify project
    classifier = ProjectClassifier()

    test_description = """
    Three-phase test separator for PAD-3 location.
    Requirements include PLC control system (Allen-Bradley CompactLogix, 64 I/O points),
    HMI/SCADA integration with 15 screens, instrumentation (20 instruments total:
    level, pressure, temperature sensors), electrical panel design (2 panels),
    cable routing (2.5 km total). Project located in Colombia, must comply with RETIE.
    Timeline is urgent - need completion in 4 months. This is a new customer.
    """

    classification = classifier.classify(
        project_description=test_description,
        customer_name="Deilim Colombia",
        country="colombia"
    )

    print("=" * 70)
    print("PROJECT CLASSIFICATION")
    print("=" * 70)
    print(classifier.get_classification_summary(classification))

    # Step 2: Estimate project
    estimator = DisciplineEstimator()

    # Provide parametric details
    parameters = {
        "io_count": 64,
        "instrument_count": 20,
        "panel_count": 2,
        "cable_length_km": 2.5,
        "scada_screens": 15,
        "tank_count": 3
    }

    estimation = estimator.estimate_project(
        project_classification=classification,
        project_parameters=parameters,
        similar_projects=None  # No historical projects yet
    )

    # Step 3: Display results
    print("\n" + "=" * 70)
    print("PROJECT ESTIMATION RESULTS")
    print("=" * 70)
    print(f"Project Type: {estimation['project_type']}")
    print(f"Complexity: {estimation['complexity'].upper()}")
    print(f"Total Hours: {estimation['total_hours']:.1f}")
    print(f"Total Cost: ${estimation['total_cost']:,.2f}")
    print(f"Duration: {estimation['project_duration_weeks']} weeks")
    print(f"Overall Confidence: {estimation['overall_confidence']:.1%}")

    print("\n" + "-" * 70)
    print("PERSONNEL REQUIREMENTS")
    print("-" * 70)
    for level, fte in estimation['personnel_required'].items():
        print(f"  {level.replace('_', ' ').title()}: {fte:.2f} FTE")

    print("\n" + "-" * 70)
    print("DISCIPLINE BREAKDOWN")
    print("-" * 70)
    for disc, details in estimation['disciplines'].items():
        print(f"\n{details['discipline_name']} ({details['discipline_code']}):")
        print(f"  Hours: {details['total_hours']:.1f} | Cost: ${details['total_cost']:,.2f} | Confidence: {details['confidence']:.1%}")
        print(f"  Documents: {details['estimated_documents']} | Personnel: {sum(details['personnel'].values()):.2f} FTE")

    print("\n" + "-" * 70)
    print("PHASE BREAKDOWN")
    print("-" * 70)
    for phase, details in estimation['phases'].items():
        print(f"{details['phase_name']} ({details['gate']}): {details['total_hours']:.1f}h | ${details['total_cost']:,.2f}")

    print("\n" + "-" * 70)
    print("RECOMMENDATIONS")
    print("-" * 70)
    for rec in estimation['recommendations']:
        print(f"  {rec}")

    print("\n" + "=" * 70)
    print(f"Full estimation saved to: /var/lib/insa-crm/project_sizing/test_estimation.json")
    print("=" * 70)

    # Save to file
    import os
    os.makedirs("/var/lib/insa-crm/project_sizing", exist_ok=True)
    with open("/var/lib/insa-crm/project_sizing/test_estimation.json", "w") as f:
        json.dump(estimation, f, indent=2)
