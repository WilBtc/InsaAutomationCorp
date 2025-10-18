"""
BOM (Bill of Materials) Generator Agent
Automatically generates BOMs from requirements using InvenTree integration
"""

import requests
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime

from .config import config

logger = structlog.get_logger()


class BOMGeneratorAgent:
    """
    Generates Bill of Materials from extracted requirements
    Integrates with InvenTree for part lookup and pricing
    """

    # Standard component mappings for industrial automation
    COMPONENT_CATEGORIES = {
        "plc": {
            "allen-bradley": {
                "compactlogix": {"base_cost": 2500, "per_io": 50},
                "controllogix": {"base_cost": 5000, "per_io": 75},
            },
            "siemens": {
                "s7-1200": {"base_cost": 1500, "per_io": 40},
                "s7-1500": {"base_cost": 4000, "per_io": 60},
            }
        },
        "hmi": {
            "rockwell": {"base_cost": 3000, "per_screen": 200},
            "siemens": {"base_cost": 2500, "per_screen": 150},
            "wonderware": {"base_cost": 5000, "per_screen": 300},
            "weintek": {"base_cost": 1000, "per_screen": 50},
        },
        "instrumentation": {
            "level_sensor": {"radar": 2000, "ultrasonic": 1200, "displacer": 800},
            "pressure_sensor": {"transmitter": 500, "switch": 150, "gauge": 50},
            "temperature_sensor": {"rtd": 200, "thermocouple": 100},
            "flow_meter": {"magnetic": 3000, "vortex": 2500, "turbine": 1500},
            "control_valve": {"pneumatic": 1500, "motorized": 2500},
        },
        "panels": {
            "control_panel": {"small": 2000, "medium": 4000, "large": 8000},
            "junction_box": {"standard": 500, "hazloc": 1200},
        },
        "cables": {
            "power_cable": {"per_meter": 5},
            "control_cable": {"per_meter": 3},
            "instrument_cable": {"per_meter": 4},
            "ethernet_cable": {"per_meter": 2},
        }
    }

    def __init__(self):
        """Initialize BOM generator"""
        self.inventree_api = config.inventree_api_url
        self.inventree_token = config.inventree_token

    def generate_bom(
        self,
        requirements: Dict[str, Any],
        similar_projects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Generate BOM from requirements

        Args:
            requirements: Extracted requirements dictionary
            similar_projects: List of similar past projects for reference

        Returns:
            BOM dictionary with parts, quantities, and costs
        """
        try:
            logger.info("Generating BOM from requirements",
                       plc_vendor=requirements.get('technical_requirements', {}).get('plc', {}).get('vendor', 'Unknown'))

            bom_items = []
            total_material_cost = 0.0

            # 1. PLC System
            plc_items, plc_cost = self._generate_plc_items(requirements)
            bom_items.extend(plc_items)
            total_material_cost += plc_cost

            # 2. HMI/SCADA
            hmi_items, hmi_cost = self._generate_hmi_items(requirements)
            bom_items.extend(hmi_items)
            total_material_cost += hmi_cost

            # 3. Instrumentation
            inst_items, inst_cost = self._generate_instrumentation_items(requirements)
            bom_items.extend(inst_items)
            total_material_cost += inst_cost

            # 4. Panels & Enclosures
            panel_items, panel_cost = self._generate_panel_items(requirements)
            bom_items.extend(panel_items)
            total_material_cost += panel_cost

            # 5. Cables & Wiring
            cable_items, cable_cost = self._generate_cable_items(requirements)
            bom_items.extend(cable_items)
            total_material_cost += cable_cost

            # 6. Miscellaneous (10% of total)
            misc_cost = total_material_cost * 0.10
            bom_items.append({
                "category": "Miscellaneous",
                "description": "Terminals, wire, labels, consumables",
                "quantity": 1,
                "unit": "lot",
                "unit_cost": misc_cost,
                "total_cost": misc_cost,
                "source": "estimated"
            })
            total_material_cost += misc_cost

            # Build final BOM
            bom = {
                "items": bom_items,
                "summary": {
                    "total_items": len(bom_items),
                    "total_material_cost": round(total_material_cost, 2),
                    "currency": "USD",
                    "generated_date": datetime.utcnow().isoformat(),
                },
                "category_breakdown": self._calculate_category_breakdown(bom_items),
                "confidence": self._calculate_bom_confidence(requirements, similar_projects),
                "notes": self._generate_bom_notes(requirements)
            }

            logger.info("BOM generated successfully",
                       total_items=len(bom_items),
                       total_cost=total_material_cost,
                       confidence=bom['confidence'])

            return bom

        except Exception as e:
            logger.error("Failed to generate BOM", error=str(e))
            raise

    def _generate_plc_items(self, requirements: Dict[str, Any]) -> tuple[List[Dict], float]:
        """Generate PLC-related BOM items"""
        items = []
        total_cost = 0.0

        plc_req = requirements.get('technical_requirements', {}).get('plc', {})
        vendor = plc_req.get('vendor', '').lower()
        model = plc_req.get('model', '').lower()
        io_count = plc_req.get('io_count', {})

        # Calculate total I/O
        total_io = sum([
            io_count.get('di', 0),
            io_count.get('do', 0),
            io_count.get('ai', 0),
            io_count.get('ao', 0)
        ])

        # Lookup pricing
        if vendor in self.COMPONENT_CATEGORIES['plc']:
            vendor_plcs = self.COMPONENT_CATEGORIES['plc'][vendor]

            # Match model
            plc_family = None
            for family_name in vendor_plcs.keys():
                if family_name in model:
                    plc_family = family_name
                    break

            if not plc_family:
                plc_family = list(vendor_plcs.keys())[0]  # Default to first

            pricing = vendor_plcs[plc_family]
            plc_cost = pricing['base_cost'] + (total_io * pricing['per_io'])

            items.append({
                "category": "Control System",
                "description": f"{vendor.title()} {plc_family.upper()} PLC with {total_io} I/O points",
                "quantity": 1,
                "unit": "system",
                "unit_cost": plc_cost,
                "total_cost": plc_cost,
                "source": "estimated",
                "details": {
                    "vendor": vendor,
                    "model": plc_family,
                    "io_breakdown": io_count
                }
            })
            total_cost += plc_cost

        else:
            # Generic PLC estimate
            plc_cost = 3000 + (total_io * 50)
            items.append({
                "category": "Control System",
                "description": f"PLC System ({vendor}) with {total_io} I/O points",
                "quantity": 1,
                "unit": "system",
                "unit_cost": plc_cost,
                "total_cost": plc_cost,
                "source": "estimated",
                "note": "Generic pricing - specific model TBD"
            })
            total_cost += plc_cost

        return items, total_cost

    def _generate_hmi_items(self, requirements: Dict[str, Any]) -> tuple[List[Dict], float]:
        """Generate HMI/SCADA BOM items"""
        items = []
        total_cost = 0.0

        hmi_req = requirements.get('technical_requirements', {}).get('hmi_scada', {})
        vendor = hmi_req.get('vendor', '').lower()
        screens = hmi_req.get('screens', 10)

        # Lookup pricing
        if vendor in self.COMPONENT_CATEGORIES['hmi']:
            pricing = self.COMPONENT_CATEGORIES['hmi'][vendor]
            hmi_cost = pricing['base_cost'] + (screens * pricing['per_screen'])
        else:
            # Generic estimate
            hmi_cost = 2000 + (screens * 150)

        items.append({
            "category": "HMI/SCADA",
            "description": f"HMI/SCADA System ({vendor.title()}) - {screens} screens",
            "quantity": 1,
            "unit": "system",
            "unit_cost": hmi_cost,
            "total_cost": hmi_cost,
            "source": "estimated"
        })
        total_cost += hmi_cost

        return items, total_cost

    def _generate_instrumentation_items(self, requirements: Dict[str, Any]) -> tuple[List[Dict], float]:
        """Generate instrumentation BOM items"""
        items = []
        total_cost = 0.0

        inst_req = requirements.get('technical_requirements', {}).get('instrumentation', {})

        # Process each instrument type
        instrument_mapping = {
            'level_sensors': ('Level Transmitter', 'radar', 2000),
            'pressure_sensors': ('Pressure Transmitter', 'transmitter', 500),
            'temperature_sensors': ('Temperature Sensor', 'rtd', 200),
            'flow_meters': ('Flow Meter', 'magnetic', 3000),
            'control_valves': ('Control Valve', 'pneumatic', 1500),
        }

        for req_key, (desc, default_type, default_cost) in instrument_mapping.items():
            quantity = inst_req.get(req_key, 0)

            if quantity > 0:
                unit_cost = default_cost
                item_cost = quantity * unit_cost

                items.append({
                    "category": "Instrumentation",
                    "description": desc,
                    "quantity": quantity,
                    "unit": "ea",
                    "unit_cost": unit_cost,
                    "total_cost": item_cost,
                    "source": "estimated"
                })
                total_cost += item_cost

        return items, total_cost

    def _generate_panel_items(self, requirements: Dict[str, Any]) -> tuple[List[Dict], float]:
        """Generate panel & enclosure BOM items"""
        items = []
        total_cost = 0.0

        # Estimate panel size based on I/O count
        plc_req = requirements.get('technical_requirements', {}).get('plc', {})
        io_count = plc_req.get('io_count', {})
        total_io = sum([
            io_count.get('di', 0),
            io_count.get('do', 0),
            io_count.get('ai', 0),
            io_count.get('ao', 0)
        ])

        # Determine panel size
        if total_io < 50:
            panel_size = "small"
            panel_cost = 2000
        elif total_io < 150:
            panel_size = "medium"
            panel_cost = 4000
        else:
            panel_size = "large"
            panel_cost = 8000

        items.append({
            "category": "Panels & Enclosures",
            "description": f"Control Panel ({panel_size.upper()}) with breakers, terminals, DIN rail",
            "quantity": 1,
            "unit": "ea",
            "unit_cost": panel_cost,
            "total_cost": panel_cost,
            "source": "estimated"
        })
        total_cost += panel_cost

        # Junction boxes (estimate based on instrumentation)
        inst_count = sum(requirements.get('technical_requirements', {}).get('instrumentation', {}).values())
        if inst_count > 10:
            junction_boxes = max(2, inst_count // 10)
            jb_cost = 500 * junction_boxes

            items.append({
                "category": "Panels & Enclosures",
                "description": "Field Junction Boxes",
                "quantity": junction_boxes,
                "unit": "ea",
                "unit_cost": 500,
                "total_cost": jb_cost,
                "source": "estimated"
            })
            total_cost += jb_cost

        return items, total_cost

    def _generate_cable_items(self, requirements: Dict[str, Any]) -> tuple[List[Dict], float]:
        """Generate cable & wiring BOM items"""
        items = []
        total_cost = 0.0

        # Estimate cable lengths based on instrumentation count
        inst_count = sum(requirements.get('technical_requirements', {}).get('instrumentation', {}).values())

        # Assume average 50m per instrument
        cable_length = inst_count * 50

        cable_types = [
            ("Power Cable", 5, 0.3),  # 30% of total length
            ("Control Cable", 3, 0.4),  # 40% of total length
            ("Instrument Cable", 4, 0.3),  # 30% of total length
        ]

        for cable_desc, cost_per_meter, percentage in cable_types:
            length = int(cable_length * percentage)
            cable_cost = length * cost_per_meter

            items.append({
                "category": "Cables & Wiring",
                "description": cable_desc,
                "quantity": length,
                "unit": "m",
                "unit_cost": cost_per_meter,
                "total_cost": cable_cost,
                "source": "estimated"
            })
            total_cost += cable_cost

        return items, total_cost

    def _calculate_category_breakdown(self, items: List[Dict]) -> Dict[str, float]:
        """Calculate cost breakdown by category"""
        breakdown = {}
        for item in items:
            category = item['category']
            cost = item['total_cost']
            breakdown[category] = breakdown.get(category, 0) + cost
        return breakdown

    def _calculate_bom_confidence(
        self,
        requirements: Dict[str, Any],
        similar_projects: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate confidence score for BOM accuracy

        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = 0.5  # Base confidence

        # Increase if requirements are detailed
        req_confidence = requirements.get('confidence_score', 0.5)
        confidence += req_confidence * 0.3

        # Increase if we have similar projects
        if similar_projects and len(similar_projects) > 0:
            confidence += 0.2

        return min(confidence, 1.0)

    def _generate_bom_notes(self, requirements: Dict[str, Any]) -> List[str]:
        """Generate notes about BOM assumptions"""
        notes = [
            "All costs are estimated based on standard industry pricing",
            "Actual costs may vary based on vendor selection and quantities",
            "Cable lengths estimated at 50m average per instrument",
            "Miscellaneous items include terminals, wire, labels, and consumables",
        ]

        missing_info = requirements.get('missing_information', [])
        if missing_info:
            notes.append(f"Missing information: {'; '.join(missing_info[:3])}")

        return notes
