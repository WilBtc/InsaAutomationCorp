"""
Configuration for INSA Project Sizing Agent
Defines disciplines, project types, estimation parameters
"""

import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
STORAGE_DIR = Path("/var/lib/insa-crm/project_sizing")
KNOWLEDGE_BASE_DIR = STORAGE_DIR / "knowledge_base"
SIZING_RESULTS_DIR = STORAGE_DIR / "sizing_results"

# Ensure directories exist
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
KNOWLEDGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
SIZING_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# INSA DISCIPLINES (13 disciplines)
# ============================================================================

INSA_DISCIPLINES = {
    "process": {
        "code": "PRO",
        "name": "Process Engineering",
        "description": "P&ID design, process criteria, line lists",
        "typical_hourly_rate": 95,  # USD/hour
        "complexity_multipliers": {"basic": 0.7, "standard": 1.0, "advanced": 1.3, "custom": 1.6}
    },
    "instrumentation": {
        "code": "INS",
        "name": "Instrumentation & Control",
        "description": "Instrument index, I/O lists, loop diagrams, datasheets",
        "typical_hourly_rate": 100,
        "complexity_multipliers": {"basic": 0.8, "standard": 1.0, "advanced": 1.4, "custom": 1.8}
    },
    "automation": {
        "code": "AUT",
        "name": "Automation & PLC Programming",
        "description": "Control philosophy, PLC programming, SCADA, cause & effect",
        "typical_hourly_rate": 120,
        "complexity_multipliers": {"basic": 0.8, "standard": 1.0, "advanced": 1.5, "custom": 2.0}
    },
    "electrical": {
        "code": "ELE",
        "name": "Electrical Engineering",
        "description": "Single-line diagrams, load calc, grounding, conduit design",
        "typical_hourly_rate": 90,
        "complexity_multipliers": {"basic": 0.7, "standard": 1.0, "advanced": 1.3, "custom": 1.6}
    },
    "mechanical": {
        "code": "MEC",
        "name": "Mechanical Engineering",
        "description": "Isometrics, supports, valve specs, hydro test plans",
        "typical_hourly_rate": 85,
        "complexity_multipliers": {"basic": 0.7, "standard": 1.0, "advanced": 1.2, "custom": 1.5}
    },
    "digitalization": {
        "code": "DIG",
        "name": "Digitalization & SCADA",
        "description": "OT/IT architecture, OPC UA, PI System, MES integration",
        "typical_hourly_rate": 110,
        "complexity_multipliers": {"basic": 0.9, "standard": 1.0, "advanced": 1.4, "custom": 1.8}
    },
    "cybersecurity": {
        "code": "CYB",
        "name": "OT Cybersecurity",
        "description": "IEC 62443 zones & conduits, MFA, hardening, incident response",
        "typical_hourly_rate": 130,
        "complexity_multipliers": {"basic": 1.0, "standard": 1.2, "advanced": 1.5, "custom": 2.0}
    },
    "procurement": {
        "code": "PRC",
        "name": "Procurement & Supply Chain",
        "description": "RFQ generation, vendor evaluation, FAT coordination",
        "typical_hourly_rate": 70,
        "complexity_multipliers": {"basic": 0.8, "standard": 1.0, "advanced": 1.2, "custom": 1.4}
    },
    "construction": {
        "code": "CON",
        "name": "Construction & Installation",
        "description": "Installation supervision, QA/QC, punch lists",
        "typical_hourly_rate": 75,
        "complexity_multipliers": {"basic": 0.8, "standard": 1.0, "advanced": 1.2, "custom": 1.5}
    },
    "commissioning": {
        "code": "COM",
        "name": "Commissioning & Startup",
        "description": "FAT, SAT, loop checks, calibration, startup support",
        "typical_hourly_rate": 95,
        "complexity_multipliers": {"basic": 0.8, "standard": 1.0, "advanced": 1.3, "custom": 1.6}
    },
    "operations": {
        "code": "OPE",
        "name": "Operations & Maintenance",
        "description": "O&M manuals, training, spare parts lists",
        "typical_hourly_rate": 80,
        "complexity_multipliers": {"basic": 0.7, "standard": 1.0, "advanced": 1.2, "custom": 1.4}
    },
    "hse": {
        "code": "HSE",
        "name": "Health, Safety & Environment",
        "description": "HSE plans, permits, risk assessments, HAZOP",
        "typical_hourly_rate": 85,
        "complexity_multipliers": {"basic": 0.8, "standard": 1.0, "advanced": 1.3, "custom": 1.5}
    },
    "quality": {
        "code": "QUA",
        "name": "Quality Assurance",
        "description": "Quality plans, document control, audits, dossiers",
        "typical_hourly_rate": 75,
        "complexity_multipliers": {"basic": 0.7, "standard": 1.0, "advanced": 1.2, "custom": 1.4}
    }
}

# ============================================================================
# PROJECT TYPES (expandable taxonomy)
# ============================================================================

PROJECT_TYPES = {
    "separator": {
        "name": "Oil & Gas Separator",
        "variants": ["two_phase", "three_phase", "test_separator", "production_separator"],
        "typical_disciplines": ["process", "instrumentation", "automation", "electrical", "mechanical"],
        "base_complexity": "standard",
        "reference_projects": ["INSAGTEC-6598"]  # PAD-2 Test Separator
    },
    "compressor": {
        "name": "Compressor Station",
        "variants": ["gas_compressor", "air_compressor", "reciprocating", "centrifugal"],
        "typical_disciplines": ["process", "instrumentation", "automation", "electrical", "mechanical", "vibration"],
        "base_complexity": "advanced"
    },
    "tank_farm": {
        "name": "Tank Farm / Storage",
        "variants": ["crude_oil", "refined_products", "water", "chemical"],
        "typical_disciplines": ["process", "instrumentation", "automation", "electrical", "mechanical", "hse"],
        "base_complexity": "standard"
    },
    "metering": {
        "name": "Custody Transfer / Metering",
        "variants": ["fiscal_metering", "allocation_metering", "proving_system"],
        "typical_disciplines": ["instrumentation", "automation", "electrical", "quality"],
        "base_complexity": "advanced"
    },
    "pipeline": {
        "name": "Pipeline Automation",
        "variants": ["oil_pipeline", "gas_pipeline", "water_injection"],
        "typical_disciplines": ["instrumentation", "automation", "electrical", "mechanical", "cybersecurity"],
        "base_complexity": "advanced"
    },
    "wellhead": {
        "name": "Wellhead Automation",
        "variants": ["production_well", "injection_well", "artificial_lift"],
        "typical_disciplines": ["instrumentation", "automation", "electrical"],
        "base_complexity": "standard"
    },
    "scada": {
        "name": "SCADA System",
        "variants": ["greenfield", "brownfield_upgrade", "migration"],
        "typical_disciplines": ["digitalization", "automation", "cybersecurity", "operations"],
        "base_complexity": "advanced"
    },
    "panel": {
        "name": "Control Panel / MCC",
        "variants": ["plc_panel", "mcc", "junction_box", "field_enclosure"],
        "typical_disciplines": ["electrical", "instrumentation", "automation"],
        "base_complexity": "basic"
    }
}

# ============================================================================
# PROJECT PHASES (INSA 5-phase lifecycle)
# ============================================================================

PROJECT_PHASES = {
    "phase_0": {
        "name": "Kick-off",
        "gate": "G0",
        "typical_duration_weeks": 2,
        "key_activities": [
            "Project plan (PDT/WBS)",
            "Document matrix",
            "Quality plan (SIG)",
            "HSE plan and permits"
        ],
        "effort_percentage": 5  # % of total project effort
    },
    "phase_1": {
        "name": "Engineering Design",
        "gate": "G1",
        "typical_duration_weeks": 8,
        "key_activities": [
            "Detailed engineering all disciplines",
            "Client approval package",
            "Vendor specifications",
            "Construction drawings"
        ],
        "effort_percentage": 40
    },
    "phase_2": {
        "name": "Procurement",
        "gate": "G2",
        "typical_duration_weeks": 12,
        "key_activities": [
            "RFQ generation",
            "Vendor evaluation",
            "Purchase orders",
            "FAT coordination"
        ],
        "effort_percentage": 15
    },
    "phase_3": {
        "name": "Construction & Installation",
        "gate": "G3",
        "typical_duration_weeks": 8,
        "key_activities": [
            "Installation supervision",
            "QA/QC inspections",
            "As-built documentation",
            "Punch list management"
        ],
        "effort_percentage": 20
    },
    "phase_4": {
        "name": "Commissioning & Startup",
        "gate": "G4",
        "typical_duration_weeks": 4,
        "key_activities": [
            "FAT/SAT execution",
            "Loop checks and calibration",
            "Startup support",
            "Training delivery",
            "Final documentation"
        ],
        "effort_percentage": 20
    }
}

# ============================================================================
# COMPLEXITY FACTORS (adjustment multipliers)
# ============================================================================

COMPLEXITY_FACTORS = {
    "hazardous_area": {
        "description": "ATEX/IECEx Zone 1 or Division 1",
        "multiplier": 1.2,
        "affects": ["instrumentation", "electrical", "mechanical"]
    },
    "cybersecurity_required": {
        "description": "IEC 62443 compliance mandatory",
        "multiplier": 1.15,
        "affects": ["automation", "digitalization", "cybersecurity"]
    },
    "scada_integration": {
        "description": "SCADA/DCS integration required",
        "multiplier": 1.3,
        "affects": ["automation", "digitalization"]
    },
    "sil_rated": {
        "description": "SIL 2 or SIL 3 safety systems",
        "multiplier": 1.4,
        "affects": ["instrumentation", "automation", "quality"]
    },
    "offshore": {
        "description": "Offshore platform installation",
        "multiplier": 1.5,
        "affects": ["all"]
    },
    "fast_track": {
        "description": "Accelerated schedule (<50% normal duration)",
        "multiplier": 1.3,
        "affects": ["all"]
    },
    "new_customer": {
        "description": "First-time customer (learning curve)",
        "multiplier": 1.1,
        "affects": ["all"]
    },
    "repeat_project": {
        "description": "Repeat/similar project (efficiency gain)",
        "multiplier": 0.85,
        "affects": ["all"]
    }
}

# ============================================================================
# STANDARDS BY COUNTRY (compliance requirements)
# ============================================================================

STANDARDS_BY_COUNTRY = {
    "colombia": {
        "electrical": ["RETIE", "NTC 2050"],
        "instrumentation": ["ISA-5.1", "API RP"],
        "cybersecurity": ["IEC 62443"],
        "documentation_language": "Spanish"
    },
    "ecuador": {
        "electrical": ["INEN", "NEC"],
        "instrumentation": ["ISA-5.1", "API RP"],
        "cybersecurity": ["IEC 62443"],
        "documentation_language": "Spanish"
    },
    "usa": {
        "electrical": ["NEC", "NFPA 70"],
        "instrumentation": ["ISA-5.1", "API RP"],
        "cybersecurity": ["NERC CIP", "IEC 62443"],
        "documentation_language": "English"
    }
}

# ============================================================================
# ESTIMATION PARAMETERS
# ============================================================================

# Base hours for reference project (INSAGTEC-6598 - Three-phase separator)
REFERENCE_PROJECT_HOURS = {
    "project_code": "INSAGTEC-6598",
    "project_type": "separator",
    "variant": "three_phase",
    "complexity": "standard",
    "total_hours": 464,  # From Phase 7 quote generation
    "hours_by_discipline": {
        "process": 40,
        "instrumentation": 120,
        "automation": 100,
        "electrical": 60,
        "mechanical": 60,
        "quality": 40,
        "commissioning": 44
    },
    "documents_generated": 63,
    "project_duration_weeks": 16
}

# Confidence thresholds
CONFIDENCE_THRESHOLDS = {
    "high": 0.85,      # >85% = High confidence
    "medium": 0.70,    # 70-85% = Medium confidence
    "low": 0.70        # <70% = Low confidence, requires review
}

# AI Model settings
AI_MODEL = "claude-code-subprocess"  # Zero-cost local Claude Code
AI_TIMEOUT_SECONDS = 30
AI_MAX_RETRIES = 3
