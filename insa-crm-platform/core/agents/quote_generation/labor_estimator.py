"""
Labor Estimator Agent
Estimates engineering, installation, and commissioning labor hours
Uses historical data and complexity scoring
"""

from typing import Dict, Any, List
import structlog
from datetime import datetime
import statistics

from .config import config

logger = structlog.get_logger()


class LaborEstimatorAgent:
    """
    Estimates labor hours for industrial automation projects
    Based on historical data and complexity analysis
    """

    # Standard labor hour estimates (pessimistic for safety)
    LABOR_ESTIMATES = {
        "engineering": {
            "plc_programming": {
                "simple": {"hours_per_io": 0.5, "base_hours": 40},
                "moderate": {"hours_per_io": 1.0, "base_hours": 80},
                "complex": {"hours_per_io": 2.0, "base_hours": 160},
            },
            "hmi_development": {
                "per_screen": {"simple": 4, "moderate": 8, "complex": 16},
                "base_hours": 40
            },
            "pid_drawings": {
                "per_drawing": 16,
                "base_hours": 24
            },
            "electrical_design": {
                "per_panel": 40,
                "base_hours": 24
            },
            "documentation": {
                "percentage_of_total": 0.15  # 15% of total engineering hours
            }
        },
        "installation": {
            "panel_installation": {"hours_per_panel": 24},
            "instrument_installation": {"hours_per_instrument": 4},
            "cable_pulling": {"hours_per_100m": 8},
            "termination": {"hours_per_io_point": 0.5},
        },
        "commissioning": {
            "plc_commissioning": {"hours_per_io": 0.3, "base_hours": 40},
            "instrument_calibration": {"hours_per_instrument": 2},
            "fat": {"base_hours": 40},  # Factory Acceptance Test
            "sat": {"base_hours": 80},  # Site Acceptance Test
        },
        "training": {
            "operator_training": {"hours_per_session": 8, "min_sessions": 2},
            "maintenance_training": {"hours_per_session": 16, "min_sessions": 1},
        }
    }

    def __init__(self):
        """Initialize labor estimator"""
        self.engineering_rate = config.engineering_rate_per_hour
        self.labor_rate = config.labor_rate_per_hour

    def estimate_labor(
        self,
        requirements: Dict[str, Any],
        bom: Dict[str, Any],
        similar_projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Estimate total labor hours and cost

        Args:
            requirements: Extracted requirements
            bom: Generated BOM
            similar_projects: Historical projects for reference

        Returns:
            Labor estimate dictionary
        """
        try:
            logger.info("Estimating labor hours and costs")

            complexity = requirements.get('complexity_score', 50)

            # Determine complexity level
            if complexity >= 80:
                complexity_level = "complex"
            elif complexity >= 60:
                complexity_level = "moderate"
            else:
                complexity_level = "simple"

            # Calculate each phase
            engineering_hours, engineering_breakdown = self._estimate_engineering(
                requirements, complexity_level
            )

            installation_hours, installation_breakdown = self._estimate_installation(
                requirements, bom
            )

            commissioning_hours, commissioning_breakdown = self._estimate_commissioning(
                requirements
            )

            training_hours, training_breakdown = self._estimate_training(
                requirements
            )

            # Total hours
            total_hours = (
                engineering_hours +
                installation_hours +
                commissioning_hours +
                training_hours
            )

            # Calculate costs (engineering at higher rate)
            engineering_cost = engineering_hours * self.engineering_rate
            installation_cost = installation_hours * self.labor_rate
            commissioning_cost = commissioning_hours * self.labor_rate
            training_cost = training_hours * self.labor_rate

            total_cost = engineering_cost + installation_cost + commissioning_cost + training_cost

            # Apply historical adjustment if available
            adjustment_factor = self._calculate_historical_adjustment(
                similar_projects,
                requirements,
                total_hours
            )

            adjusted_hours = total_hours * adjustment_factor
            adjusted_cost = total_cost * adjustment_factor

            estimate = {
                "total_hours": round(total_hours, 1),
                "adjusted_hours": round(adjusted_hours, 1),
                "adjustment_factor": round(adjustment_factor, 2),
                "total_cost": round(total_cost, 2),
                "adjusted_cost": round(adjusted_cost, 2),
                "currency": "USD",
                "breakdown": {
                    "engineering": {
                        "hours": round(engineering_hours, 1),
                        "cost": round(engineering_cost, 2),
                        "rate_per_hour": self.engineering_rate,
                        "details": engineering_breakdown
                    },
                    "installation": {
                        "hours": round(installation_hours, 1),
                        "cost": round(installation_cost, 2),
                        "rate_per_hour": self.labor_rate,
                        "details": installation_breakdown
                    },
                    "commissioning": {
                        "hours": round(commissioning_hours, 1),
                        "cost": round(commissioning_cost, 2),
                        "rate_per_hour": self.labor_rate,
                        "details": commissioning_breakdown
                    },
                    "training": {
                        "hours": round(training_hours, 1),
                        "cost": round(training_cost, 2),
                        "rate_per_hour": self.labor_rate,
                        "details": training_breakdown
                    }
                },
                "complexity_level": complexity_level,
                "confidence": self._calculate_confidence(requirements, similar_projects),
                "estimated_date": datetime.utcnow().isoformat(),
                "notes": self._generate_notes(requirements, similar_projects)
            }

            logger.info("Labor estimate completed",
                       total_hours=adjusted_hours,
                       total_cost=adjusted_cost,
                       complexity=complexity_level)

            return estimate

        except Exception as e:
            logger.error("Failed to estimate labor", error=str(e))
            raise

    def _estimate_engineering(
        self,
        requirements: Dict[str, Any],
        complexity_level: str
    ) -> tuple[float, Dict]:
        """Estimate engineering hours"""
        total_hours = 0.0
        breakdown = {}

        tech_req = requirements.get('technical_requirements', {})

        # PLC Programming
        plc_req = tech_req.get('plc', {})
        io_count = plc_req.get('io_count', {})
        total_io = sum([
            io_count.get('di', 0),
            io_count.get('do', 0),
            io_count.get('ai', 0),
            io_count.get('ao', 0)
        ])

        plc_params = self.LABOR_ESTIMATES['engineering']['plc_programming'][complexity_level]
        plc_hours = plc_params['base_hours'] + (total_io * plc_params['hours_per_io'])
        breakdown['plc_programming'] = round(plc_hours, 1)
        total_hours += plc_hours

        # HMI Development
        hmi_req = tech_req.get('hmi_scada', {})
        screens = hmi_req.get('screens', 10)
        screen_params = self.LABOR_ESTIMATES['engineering']['hmi_development']
        hmi_hours = screen_params['base_hours'] + (screens * screen_params['per_screen'][complexity_level])
        breakdown['hmi_development'] = round(hmi_hours, 1)
        total_hours += hmi_hours

        # P&ID Drawings (estimate 3-5 drawings based on complexity)
        drawing_count = 3 if complexity_level == "simple" else 5 if complexity_level == "moderate" else 8
        pid_hours = self.LABOR_ESTIMATES['engineering']['pid_drawings']['base_hours'] + \
                    (drawing_count * self.LABOR_ESTIMATES['engineering']['pid_drawings']['per_drawing'])
        breakdown['pid_drawings'] = round(pid_hours, 1)
        total_hours += pid_hours

        # Electrical Design
        panel_count = 1 if total_io < 100 else 2
        elec_hours = self.LABOR_ESTIMATES['engineering']['electrical_design']['base_hours'] + \
                     (panel_count * self.LABOR_ESTIMATES['engineering']['electrical_design']['per_panel'])
        breakdown['electrical_design'] = round(elec_hours, 1)
        total_hours += elec_hours

        # Documentation (15% of total engineering)
        doc_hours = total_hours * self.LABOR_ESTIMATES['engineering']['documentation']['percentage_of_total']
        breakdown['documentation'] = round(doc_hours, 1)
        total_hours += doc_hours

        return total_hours, breakdown

    def _estimate_installation(
        self,
        requirements: Dict[str, Any],
        bom: Dict[str, Any]
    ) -> tuple[float, Dict]:
        """Estimate installation hours"""
        total_hours = 0.0
        breakdown = {}

        # Count panels from BOM
        panel_count = 0
        for item in bom.get('items', []):
            if 'panel' in item.get('description', '').lower():
                panel_count += item.get('quantity', 0)

        if panel_count > 0:
            panel_hours = panel_count * self.LABOR_ESTIMATES['installation']['panel_installation']['hours_per_panel']
            breakdown['panel_installation'] = round(panel_hours, 1)
            total_hours += panel_hours

        # Count instruments
        inst_count = sum(requirements.get('technical_requirements', {}).get('instrumentation', {}).values())
        if inst_count > 0:
            inst_hours = inst_count * self.LABOR_ESTIMATES['installation']['instrument_installation']['hours_per_instrument']
            breakdown['instrument_installation'] = round(inst_hours, 1)
            total_hours += inst_hours

        # Cable pulling (from BOM)
        total_cable_length = 0
        for item in bom.get('items', []):
            if item.get('category') == 'Cables & Wiring':
                total_cable_length += item.get('quantity', 0)

        if total_cable_length > 0:
            cable_hours = (total_cable_length / 100) * self.LABOR_ESTIMATES['installation']['cable_pulling']['hours_per_100m']
            breakdown['cable_pulling'] = round(cable_hours, 1)
            total_hours += cable_hours

        # Termination
        tech_req = requirements.get('technical_requirements', {})
        io_count = tech_req.get('plc', {}).get('io_count', {})
        total_io = sum(io_count.values())

        if total_io > 0:
            term_hours = total_io * self.LABOR_ESTIMATES['installation']['termination']['hours_per_io_point']
            breakdown['termination'] = round(term_hours, 1)
            total_hours += term_hours

        return total_hours, breakdown

    def _estimate_commissioning(self, requirements: Dict[str, Any]) -> tuple[float, Dict]:
        """Estimate commissioning hours"""
        total_hours = 0.0
        breakdown = {}

        tech_req = requirements.get('technical_requirements', {})

        # PLC Commissioning
        io_count = tech_req.get('plc', {}).get('io_count', {})
        total_io = sum(io_count.values())

        comm_params = self.LABOR_ESTIMATES['commissioning']['plc_commissioning']
        plc_comm_hours = comm_params['base_hours'] + (total_io * comm_params['hours_per_io'])
        breakdown['plc_commissioning'] = round(plc_comm_hours, 1)
        total_hours += plc_comm_hours

        # Instrument Calibration
        inst_count = sum(tech_req.get('instrumentation', {}).values())
        if inst_count > 0:
            cal_hours = inst_count * self.LABOR_ESTIMATES['commissioning']['instrument_calibration']['hours_per_instrument']
            breakdown['instrument_calibration'] = round(cal_hours, 1)
            total_hours += cal_hours

        # FAT & SAT
        fat_hours = self.LABOR_ESTIMATES['commissioning']['fat']['base_hours']
        sat_hours = self.LABOR_ESTIMATES['commissioning']['sat']['base_hours']
        breakdown['factory_acceptance_test'] = fat_hours
        breakdown['site_acceptance_test'] = sat_hours
        total_hours += fat_hours + sat_hours

        return total_hours, breakdown

    def _estimate_training(self, requirements: Dict[str, Any]) -> tuple[float, Dict]:
        """Estimate training hours"""
        total_hours = 0.0
        breakdown = {}

        # Operator Training (2 sessions minimum)
        operator_params = self.LABOR_ESTIMATES['training']['operator_training']
        operator_hours = operator_params['hours_per_session'] * operator_params['min_sessions']
        breakdown['operator_training'] = operator_hours
        total_hours += operator_hours

        # Maintenance Training (1 session minimum)
        maint_params = self.LABOR_ESTIMATES['training']['maintenance_training']
        maint_hours = maint_params['hours_per_session'] * maint_params['min_sessions']
        breakdown['maintenance_training'] = maint_hours
        total_hours += maint_hours

        return total_hours, breakdown

    def _calculate_historical_adjustment(
        self,
        similar_projects: List[Dict[str, Any]],
        requirements: Dict[str, Any],
        estimated_hours: float
    ) -> float:
        """
        Calculate adjustment factor based on historical project data

        Returns:
            Adjustment factor (e.g., 1.2 = 20% more hours than estimate)
        """
        if not similar_projects or len(similar_projects) == 0:
            # No historical data, use conservative 1.2x (20% buffer)
            return 1.2

        # Extract actual vs estimated hours from similar projects (if available)
        # For now, use a fixed adjustment based on complexity
        complexity = requirements.get('complexity_score', 50)

        if complexity >= 80:
            return 1.3  # Complex projects tend to overrun by 30%
        elif complexity >= 60:
            return 1.2  # Moderate projects by 20%
        else:
            return 1.1  # Simple projects by 10%

    def _calculate_confidence(
        self,
        requirements: Dict[str, Any],
        similar_projects: List[Dict[str, Any]]
    ) -> float:
        """Calculate confidence in labor estimate"""
        confidence = 0.6  # Base confidence

        # Increase if requirements are detailed
        req_confidence = requirements.get('confidence_score', 0.5)
        confidence += req_confidence * 0.2

        # Increase if we have similar projects
        if similar_projects and len(similar_projects) > 0:
            confidence += 0.2

        return min(confidence, 1.0)

    def _generate_notes(
        self,
        requirements: Dict[str, Any],
        similar_projects: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate notes about labor estimate"""
        notes = [
            "Labor hours estimated based on industry standard rates",
            "Engineering hours assume experienced personnel",
            "Installation hours assume normal site conditions",
            "20% contingency applied based on project complexity",
        ]

        if not similar_projects or len(similar_projects) == 0:
            notes.append("No similar historical projects found - conservative estimate applied")

        missing_info = requirements.get('missing_information', [])
        if missing_info:
            notes.append("Some requirements unclear - may require revision")

        return notes
