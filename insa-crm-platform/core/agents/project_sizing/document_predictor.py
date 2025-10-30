"""
Document Predictor - Predicts required documents/deliverables for projects
Based on INSA's 4-phase project lifecycle and discipline requirements
"""

import json
from typing import Dict, List, Optional, Set
from pathlib import Path

from config import (
    INSA_DISCIPLINES,
    PROJECT_PHASES,
    STANDARDS_BY_COUNTRY
)


class DocumentPredictor:
    """
    Predicts complete document deliverables list for INSA projects

    Based on:
    - Project type and complexity
    - Required disciplines
    - Country-specific standards
    - Customer requirements
    - Phase-by-phase deliverables

    Reference: INSAGTEC-6598 project structure (63 documents)
    """

    def __init__(self):
        self.disciplines = INSA_DISCIPLINES
        self.phases = PROJECT_PHASES
        self.standards = STANDARDS_BY_COUNTRY

        # Document templates by discipline and phase
        self.document_templates = self._initialize_document_templates()

    def predict_documents(
        self,
        project_classification: Dict,
        discipline_estimation: Dict,
        country: str = "colombia",
        customer_requirements: Optional[List[str]] = None
    ) -> Dict:
        """
        Predict complete document list for project

        Args:
            project_classification: Classification from ProjectClassifier
            discipline_estimation: Estimation from DisciplineEstimator
            country: Project country (for standards compliance)
            customer_requirements: Additional customer-specific requirements

        Returns:
            Complete document prediction with templates and counts
        """

        project_type = project_classification.get("project_type", "unknown")
        complexity = project_classification.get("complexity", "standard")
        required_disciplines = project_classification.get("required_disciplines", [])
        project_code = f"[PROJECT_CODE]"  # Placeholder

        # Initialize result structure
        prediction = {
            "project_type": project_type,
            "complexity": complexity,
            "country": country,
            "total_documents": 0,
            "documents_by_phase": {},
            "documents_by_discipline": {},
            "document_list": [],
            "templates_available": [],
            "standards_compliance": self.standards.get(country, {}),
            "naming_convention": self._get_naming_convention()
        }

        # Step 1: Generate phase-based documents
        for phase_key in ["phase_0", "phase_1", "phase_2", "phase_3", "phase_4"]:
            phase_docs = self._predict_phase_documents(
                phase_key,
                required_disciplines,
                complexity,
                project_code,
                country
            )

            prediction["documents_by_phase"][phase_key] = phase_docs
            prediction["document_list"].extend(phase_docs["documents"])
            prediction["total_documents"] += len(phase_docs["documents"])

        # Step 2: Generate discipline-specific documents
        for discipline in required_disciplines:
            disc_docs = self._predict_discipline_documents(
                discipline,
                project_type,
                complexity,
                project_code,
                country
            )

            prediction["documents_by_discipline"][discipline] = disc_docs

        # Step 3: Add customer-specific requirements
        if customer_requirements:
            custom_docs = self._add_custom_requirements(
                customer_requirements,
                project_code
            )
            prediction["document_list"].extend(custom_docs)
            prediction["total_documents"] += len(custom_docs)

        # Step 4: Identify available templates
        prediction["templates_available"] = self._identify_templates(
            project_type,
            required_disciplines
        )

        # Step 5: Generate document matrix
        prediction["document_matrix"] = self._generate_document_matrix(
            prediction["document_list"]
        )

        return prediction

    def _initialize_document_templates(self) -> Dict:
        """
        Initialize document templates based on INSAGTEC-6598 reference project
        """

        templates = {
            # ================================================================
            # PHASE 0: KICK-OFF & QUALITY
            # ================================================================
            "phase_0": {
                "quality": [
                    {
                        "code": "DC01",
                        "name": "Plan_de_calidad",
                        "description": "Quality Plan - QA/QC procedures, document control",
                        "discipline": "QUA",
                        "mandatory": True
                    },
                    {
                        "code": "LT01",
                        "name": "Dossier_ingeniería",
                        "description": "Engineering Dossier - Complete document index",
                        "discipline": "GRL",
                        "mandatory": True
                    }
                ],
                "hse": [
                    {
                        "code": "HS01",
                        "name": "HSE_Plan",
                        "description": "Health, Safety & Environment Plan",
                        "discipline": "HSE",
                        "mandatory": True
                    }
                ],
                "general": [
                    {
                        "code": "PM01",
                        "name": "Project_Plan_WBS",
                        "description": "Project Plan with Work Breakdown Structure",
                        "discipline": "GRL",
                        "mandatory": True
                    }
                ]
            },

            # ================================================================
            # PHASE 1: ENGINEERING DESIGN
            # ================================================================
            "phase_1": {
                "instrumentation": [
                    {
                        "code": "DC02",
                        "name": "Control_Philosophy",
                        "description": "Control Philosophy - control strategies, interlocks",
                        "discipline": "INS",
                        "mandatory": True
                    },
                    {
                        "code": "DC03",
                        "name": "Requisición_del_PLC",
                        "description": "PLC Specification - model, I/O count, protocols",
                        "discipline": "INS",
                        "mandatory": True
                    },
                    {
                        "code": "DC04",
                        "name": "Panel_Specification_Procedure",
                        "description": "Panel specification methodology",
                        "discipline": "INS",
                        "mandatory": True
                    },
                    {
                        "code": "DC05",
                        "name": "PLC_Control_Panel_Datasheet",
                        "description": "PLC panel detailed specification",
                        "discipline": "INS",
                        "mandatory": True
                    },
                    {
                        "code": "DC06",
                        "name": "TBT_Distribution_Datasheet",
                        "description": "Low voltage distribution panel datasheet",
                        "discipline": "INS",
                        "mandatory": True
                    },
                    # Instrument datasheets (varies by project)
                    {
                        "code": "DC07",
                        "name": "Level_Switch_Datasheet",
                        "description": "Level switch specifications",
                        "discipline": "INS",
                        "mandatory": False
                    },
                    {
                        "code": "DC08",
                        "name": "Pressure_Switch_Datasheet",
                        "description": "Pressure switch specifications",
                        "discipline": "INS",
                        "mandatory": False
                    },
                    {
                        "code": "DC09",
                        "name": "Level_Transmitter_Datasheet",
                        "description": "Level transmitter specifications",
                        "discipline": "INS",
                        "mandatory": False
                    },
                    {
                        "code": "DC10",
                        "name": "Pressure_Transmitter_Datasheet",
                        "description": "Pressure transmitter specifications",
                        "discipline": "INS",
                        "mandatory": False
                    },
                    # Lists
                    {
                        "code": "LT02",
                        "name": "Material_List",
                        "description": "Complete instrumentation material list",
                        "discipline": "INS",
                        "mandatory": True
                    },
                    {
                        "code": "LT03",
                        "name": "Instrument_Index",
                        "description": "Master instrument index",
                        "discipline": "INS",
                        "mandatory": True
                    },
                    {
                        "code": "LT04",
                        "name": "Cause_Effect_Matrix",
                        "description": "Cause & effect matrix - interlocks and shutdowns",
                        "discipline": "INS",
                        "mandatory": True
                    },
                    {
                        "code": "LT05",
                        "name": "IO_Allocation",
                        "description": "I/O allocation to PLC modules",
                        "discipline": "INS",
                        "mandatory": True
                    },
                    # Drawings
                    {
                        "code": "DW01",
                        "name": "PID_Diagram",
                        "description": "Piping & Instrumentation Diagram",
                        "discipline": "INS",
                        "mandatory": True
                    },
                    {
                        "code": "DW02",
                        "name": "Control_Architecture",
                        "description": "Control system architecture diagram",
                        "discipline": "INS",
                        "mandatory": True
                    },
                    {
                        "code": "DW03",
                        "name": "PLC_Wiring_Diagram",
                        "description": "PLC module wiring diagrams",
                        "discipline": "INS",
                        "mandatory": True
                    }
                ],

                "automation": [
                    {
                        "code": "DC15",
                        "name": "SCADA_Specification",
                        "description": "SCADA/HMI system specification",
                        "discipline": "AUT",
                        "mandatory": False  # Only if SCADA required
                    },
                    {
                        "code": "LT10",
                        "name": "Logic_Narrative",
                        "description": "PLC logic narrative descriptions",
                        "discipline": "AUT",
                        "mandatory": True
                    }
                ],

                "electrical": [
                    {
                        "code": "DC20",
                        "name": "Electrical_Panel_Specification",
                        "description": "Electrical panel design specification",
                        "discipline": "ELE",
                        "mandatory": True
                    },
                    {
                        "code": "DW10",
                        "name": "Single_Line_Diagram",
                        "description": "Electrical single-line diagram",
                        "discipline": "ELE",
                        "mandatory": True
                    },
                    {
                        "code": "LT20",
                        "name": "Load_Calculation",
                        "description": "Electrical load calculations",
                        "discipline": "ELE",
                        "mandatory": True
                    },
                    {
                        "code": "LT21",
                        "name": "Cable_Schedule",
                        "description": "Cable schedule with routing",
                        "discipline": "ELE",
                        "mandatory": True
                    }
                ],

                "mechanical": [
                    {
                        "code": "DW20",
                        "name": "Isometric_Drawings",
                        "description": "Piping isometric drawings",
                        "discipline": "MEC",
                        "mandatory": True
                    },
                    {
                        "code": "DW21",
                        "name": "Equipment_Layout",
                        "description": "Equipment layout and location plan",
                        "discipline": "MEC",
                        "mandatory": True
                    },
                    {
                        "code": "DC30",
                        "name": "Valve_Specification",
                        "description": "Valve datasheets and specifications",
                        "discipline": "MEC",
                        "mandatory": False
                    }
                ],

                "process": [
                    {
                        "code": "DC40",
                        "name": "Process_Criteria",
                        "description": "Process design criteria and basis",
                        "discipline": "PRO",
                        "mandatory": True
                    },
                    {
                        "code": "LT30",
                        "name": "Line_List",
                        "description": "Process line list",
                        "discipline": "PRO",
                        "mandatory": True
                    }
                ],

                "cybersecurity": [
                    {
                        "code": "DC50",
                        "name": "Cybersecurity_Architecture_IEC62443",
                        "description": "IEC 62443 zones & conduits model",
                        "discipline": "CYB",
                        "mandatory": False  # Only if cybersecurity required
                    }
                ]
            },

            # ================================================================
            # PHASE 2: PROCUREMENT
            # ================================================================
            "phase_2": {
                "procurement": [
                    {
                        "code": "RFQ01",
                        "name": "RFQ_Package",
                        "description": "Request for Quotation package",
                        "discipline": "PRC",
                        "mandatory": True
                    },
                    {
                        "code": "TBE01",
                        "name": "Technical_Bid_Evaluation",
                        "description": "Technical-economic bid evaluation",
                        "discipline": "PRC",
                        "mandatory": True
                    }
                ]
            },

            # ================================================================
            # PHASE 3: CONSTRUCTION
            # ================================================================
            "phase_3": {
                "construction": [
                    {
                        "code": "ITP01",
                        "name": "Inspection_Test_Plan",
                        "description": "Inspection and test plan",
                        "discipline": "CON",
                        "mandatory": True
                    },
                    {
                        "code": "PL01",
                        "name": "Punch_List",
                        "description": "Construction punch list",
                        "discipline": "CON",
                        "mandatory": True
                    }
                ],
                "quality": [
                    {
                        "code": "AB01",
                        "name": "As_Built_Documentation",
                        "description": "As-built drawings and documents",
                        "discipline": "QUA",
                        "mandatory": True
                    }
                ]
            },

            # ================================================================
            # PHASE 4: COMMISSIONING
            # ================================================================
            "phase_4": {
                "commissioning": [
                    {
                        "code": "FAT01",
                        "name": "Factory_Acceptance_Test_Protocol",
                        "description": "FAT test procedures and results",
                        "discipline": "COM",
                        "mandatory": True
                    },
                    {
                        "code": "SAT01",
                        "name": "Site_Acceptance_Test_Protocol",
                        "description": "SAT test procedures and results",
                        "discipline": "COM",
                        "mandatory": True
                    },
                    {
                        "code": "LC01",
                        "name": "Loop_Check_Sheets",
                        "description": "Instrument loop check documentation",
                        "discipline": "COM",
                        "mandatory": True
                    },
                    {
                        "code": "CAL01",
                        "name": "Calibration_Certificates",
                        "description": "Instrument calibration certificates",
                        "discipline": "COM",
                        "mandatory": True
                    }
                ],
                "operations": [
                    {
                        "code": "OM01",
                        "name": "Operation_Maintenance_Manual",
                        "description": "Complete O&M manual",
                        "discipline": "OPE",
                        "mandatory": True
                    },
                    {
                        "code": "TR01",
                        "name": "Training_Materials",
                        "description": "Operator and maintenance training materials",
                        "discipline": "OPE",
                        "mandatory": True
                    }
                ],
                "automation": [
                    {
                        "code": "PB01",
                        "name": "PLC_Program_Backup",
                        "description": "PLC program backup (.ACD/.L5X)",
                        "discipline": "AUT",
                        "mandatory": True
                    },
                    {
                        "code": "HB01",
                        "name": "HMI_Program_Backup",
                        "description": "HMI project backup",
                        "discipline": "AUT",
                        "mandatory": True
                    }
                ]
            }
        }

        return templates

    def _predict_phase_documents(
        self,
        phase_key: str,
        required_disciplines: List[str],
        complexity: str,
        project_code: str,
        country: str
    ) -> Dict:
        """
        Predict documents for a specific project phase
        """

        phase_templates = self.document_templates.get(phase_key, {})
        phase_name = self.phases[phase_key]["name"]

        documents = []

        # Iterate through disciplines in this phase
        for discipline in required_disciplines:
            # Get templates for this discipline in this phase
            discipline_templates = phase_templates.get(discipline, [])

            for template in discipline_templates:
                # Generate document name
                doc_name = self._format_document_name(
                    project_code,
                    template["discipline"],
                    template["code"],
                    template["name"]
                )

                doc_info = {
                    "document_name": doc_name,
                    "code": template["code"],
                    "description": template["description"],
                    "discipline": template["discipline"],
                    "phase": phase_key,
                    "mandatory": template["mandatory"],
                    "template_available": True
                }

                documents.append(doc_info)

        # Add always-required documents (like quality, general)
        for discipline_key in ["quality", "general", "hse"]:
            if discipline_key in phase_templates:
                for template in phase_templates[discipline_key]:
                    doc_name = self._format_document_name(
                        project_code,
                        template["discipline"],
                        template["code"],
                        template["name"]
                    )

                    doc_info = {
                        "document_name": doc_name,
                        "code": template["code"],
                        "description": template["description"],
                        "discipline": template["discipline"],
                        "phase": phase_key,
                        "mandatory": template["mandatory"],
                        "template_available": True
                    }

                    documents.append(doc_info)

        return {
            "phase_name": phase_name,
            "gate": self.phases[phase_key]["gate"],
            "document_count": len(documents),
            "documents": documents
        }

    def _predict_discipline_documents(
        self,
        discipline: str,
        project_type: str,
        complexity: str,
        project_code: str,
        country: str
    ) -> Dict:
        """
        Predict all documents for a specific discipline across all phases
        """

        discipline_code = self.disciplines[discipline]["code"]
        discipline_name = self.disciplines[discipline]["name"]

        documents = []

        # Collect documents from all phases
        for phase_key, phase_templates in self.document_templates.items():
            if discipline in phase_templates:
                for template in phase_templates[discipline]:
                    doc_name = self._format_document_name(
                        project_code,
                        template["discipline"],
                        template["code"],
                        template["name"]
                    )

                    documents.append({
                        "document_name": doc_name,
                        "code": template["code"],
                        "description": template["description"],
                        "phase": phase_key,
                        "mandatory": template["mandatory"]
                    })

        return {
            "discipline_name": discipline_name,
            "discipline_code": discipline_code,
            "document_count": len(documents),
            "documents": documents
        }

    def _format_document_name(
        self,
        project_code: str,
        discipline: str,
        doc_code: str,
        doc_name: str
    ) -> str:
        """
        Format document name according to INSA naming convention

        Format: [PROJECT_CODE]-[DISCIPLINE]-[DOC_CODE]_[Description].pdf
        Example: INSAGTEC-6598-INS-DC02_Control_Philosophy.pdf
        """

        return f"{project_code}-{discipline}-{doc_code}_{doc_name}.pdf"

    def _add_custom_requirements(
        self,
        requirements: List[str],
        project_code: str
    ) -> List[Dict]:
        """
        Add customer-specific document requirements
        """

        custom_docs = []

        for i, req in enumerate(requirements):
            custom_docs.append({
                "document_name": f"{project_code}-CUS-CR{i+1:02d}_{req.replace(' ', '_')}.pdf",
                "code": f"CR{i+1:02d}",
                "description": req,
                "discipline": "CUS",
                "phase": "custom",
                "mandatory": True,
                "template_available": False
            })

        return custom_docs

    def _identify_templates(
        self,
        project_type: str,
        required_disciplines: List[str]
    ) -> List[str]:
        """
        Identify which templates are available for this project
        """

        # Currently all templates are available from reference project
        # Future: match templates to project type

        available = [
            "Quality Plan (DC01)",
            "Engineering Dossier (LT01)",
            "Control Philosophy (DC02)",
            "PLC Specification (DC03)",
            "P&ID Template (DW01)",
            "Instrument Index (LT03)",
            "I/O Allocation (LT05)",
            "FAT Protocol (FAT01)",
            "SAT Protocol (SAT01)"
        ]

        return available

    def _generate_document_matrix(self, document_list: List[Dict]) -> str:
        """
        Generate a document matrix/checklist in markdown format
        """

        matrix = "# INSA Project Document Matrix\n\n"
        matrix += "| # | Document Name | Code | Discipline | Phase | Mandatory | Status |\n"
        matrix += "|---|---------------|------|------------|-------|-----------|--------|\n"

        for i, doc in enumerate(document_list, 1):
            mandatory = "✓" if doc["mandatory"] else "-"
            matrix += f"| {i} | {doc['description']} | {doc['code']} | {doc['discipline']} | "
            matrix += f"{doc['phase']} | {mandatory} | ☐ |\n"

        return matrix

    def _get_naming_convention(self) -> Dict:
        """
        Return INSA document naming convention
        """

        return {
            "format": "[PROJECT_CODE]-[DISCIPLINE]-[DOC_TYPE][NUMBER]_[Description].[ext]",
            "example": "INSAGTEC-6598-INS-DC02_Control_Philosophy.pdf",
            "components": {
                "project_code": "Unique project identifier (e.g., INSAGTEC-6598)",
                "discipline": "3-letter discipline code (INS, ELE, MEC, etc)",
                "doc_type": "DC=Document, LT=List, DW=Drawing, etc",
                "number": "Sequential number (01, 02, 03...)",
                "description": "Descriptive name with underscores",
                "extension": "pdf, dwg, xlsx, etc"
            }
        }


# ============================================================================
# CLI Testing
# ============================================================================

if __name__ == "__main__":
    from project_classifier import ProjectClassifier
    from discipline_estimator import DisciplineEstimator

    print("Testing Document Predictor...\n")

    # Classify and estimate project
    classifier = ProjectClassifier()
    estimator = DisciplineEstimator()

    test_description = """
    Three-phase test separator with PLC, HMI, instrumentation.
    Located in Colombia.
    """

    classification = classifier.classify(test_description, country="colombia")
    estimation = estimator.estimate_project(classification)

    # Predict documents
    predictor = DocumentPredictor()

    prediction = predictor.predict_documents(
        project_classification=classification,
        discipline_estimation=estimation,
        country="colombia",
        customer_requirements=["Monthly Progress Reports", "Safety Data Sheets"]
    )

    print("=" * 70)
    print("DOCUMENT PREDICTION RESULTS")
    print("=" * 70)
    print(f"Total Documents: {prediction['total_documents']}")
    print(f"Project Type: {prediction['project_type']}")
    print(f"Complexity: {prediction['complexity']}")

    print("\n" + "-" * 70)
    print("DOCUMENTS BY PHASE")
    print("-" * 70)
    for phase_key, phase_data in prediction['documents_by_phase'].items():
        print(f"\n{phase_data['phase_name']} (Gate {phase_data['gate']}): {phase_data['document_count']} documents")
        for doc in phase_data['documents'][:3]:  # Show first 3
            print(f"  - {doc['code']}: {doc['description']}")
        if phase_data['document_count'] > 3:
            print(f"  ... and {phase_data['document_count'] - 3} more")

    print("\n" + "-" * 70)
    print("AVAILABLE TEMPLATES")
    print("-" * 70)
    for template in prediction['templates_available']:
        print(f"  ✓ {template}")

    print("\n" + "=" * 70)
    print("Document matrix saved to: /var/lib/insa-crm/project_sizing/document_matrix.md")
    print("=" * 70)

    # Save document matrix
    import os
    os.makedirs("/var/lib/insa-crm/project_sizing", exist_ok=True)
    with open("/var/lib/insa-crm/project_sizing/document_matrix.md", "w") as f:
        f.write(prediction["document_matrix"])

    with open("/var/lib/insa-crm/project_sizing/document_prediction.json", "w") as f:
        json.dump(prediction, f, indent=2)
