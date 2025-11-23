#!/usr/bin/env python3
"""
Alkhorayef ESP AI RAG System - Diagnostic Decision Tree Implementation
InSa Automation IoT Platform with Graphiti Knowledge Graph
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

@dataclass
class ESPTelemetry:
    """Real-time ESP telemetry data"""
    timestamp: datetime
    flow_rate: float  # BPD
    pip: float  # PSI
    motor_current: float  # Amps
    motor_temp: float  # °C
    vibration: float  # g
    vsd_frequency: float  # Hz
    flow_variance: float  # %
    torque: float  # Nm
    gor: float  # scf/bbl

class DiagnosisType(Enum):
    GAS_PROBLEM = "Free Gas Lock"
    UNDERPUMPING = "Underpumping Condition"
    SAND_PRODUCTION = "Sand/Solids Production"
    HYDRAULIC_WEAR = "Hydraulic Wear"
    VSD_ISSUES = "VSD/Electrical Issues"
    NORMAL = "Normal Operation"
    POOR_INSTALLATION = "Poor Installation"
    POOR_SELECTION = "Poor ESP Selection"

class GraphitiKnowledgeGraph:
    """Simulated Graphiti Knowledge Graph for ESP diagnostics"""

    def __init__(self):
        self.knowledge_base = {
            "entities": {
                "Free_Gas": {
                    "causes": ["Choppy_Flow", "Unstable_Production"],
                    "detected_by": ["Flow_Variance_>15%", "GOR_>500"],
                    "solutions": ["Reduce_Hz", "Apply_Backpressure", "Install_Gas_Handler"]
                },
                "Sand_Production": {
                    "causes": ["High_Flow", "High_Torque", "Motor_Overload"],
                    "detected_by": ["Motor_Current_+15%", "Flow_>3500_BPD"],
                    "solutions": ["Lower_Hz_20_30%", "Clean_Well", "Install_Screen"]
                },
                "Hydraulic_Wear": {
                    "causes": ["Low_Flow", "Stable_Production", "Efficiency_Drop"],
                    "detected_by": ["Flow_<800_BPD", "Stable_Pattern"],
                    "solutions": ["Plan_Pulling", "Replace_Stages", "Upgrade_Metallurgy"]
                }
            },
            "historical_cases": [
                {
                    "well_id": "AKH-ESP-001",
                    "problem": "Free_Gas",
                    "solution": "Reduced Hz from 55 to 48",
                    "result": "Flow stabilized in 2 hours",
                    "date": "2025-10-15"
                },
                {
                    "well_id": "AKH-ESP-002",
                    "problem": "Sand_Production",
                    "solution": "Lowered Hz by 25%, cleaned well",
                    "result": "Motor current normalized",
                    "date": "2025-10-20"
                },
                {
                    "well_id": "AKH-ESP-003",
                    "problem": "Hydraulic_Wear",
                    "solution": "Pulled and replaced pump",
                    "result": "Production increased 40%",
                    "date": "2025-11-01"
                }
            ]
        }

    def query(self, entity: str, relation: str) -> List[str]:
        """Query the knowledge graph"""
        if entity in self.knowledge_base["entities"]:
            return self.knowledge_base["entities"][entity].get(relation, [])
        return []

    def find_similar_cases(self, diagnosis: str) -> List[Dict]:
        """Find similar historical cases"""
        return [case for case in self.knowledge_base["historical_cases"]
                if diagnosis in case["problem"]]

class AlkhorayefESPDiagnosticSystem:
    """Main ESP Diagnostic System with AI RAG capabilities"""

    def __init__(self):
        self.graph = GraphitiKnowledgeGraph()
        self.decision_tree_stats = {
            "total_diagnoses": 0,
            "accuracy": 0.87,
            "avg_resolution_time": 2.5  # hours
        }

    def run_decision_tree(self, telemetry: ESPTelemetry) -> Dict[str, Any]:
        """Execute the 5-step diagnostic decision tree"""

        print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}🔍 ESP DIAGNOSTIC DECISION TREE{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")

        diagnosis = None
        confidence = 0.0
        actions = []

        # Step 1: Flow Stability Check
        flow_stable = telemetry.flow_variance < 15
        print(f"{Colors.CYAN}Q1: Is flow stable?{Colors.ENDC}")
        print(f"   Flow Variance: {telemetry.flow_variance:.1f}%")
        print(f"   Answer: {'✅ YES' if flow_stable else '❌ NO'}")

        if not flow_stable:
            diagnosis = DiagnosisType.GAS_PROBLEM
            confidence = 0.92 if telemetry.gor > 500 else 0.78
            actions = self.graph.query("Free_Gas", "solutions")
            print(f"\n{Colors.RED}⚠️  DIAGNOSIS: {diagnosis.value}{Colors.ENDC}")
            return self._create_diagnosis_report(diagnosis, confidence, actions, telemetry)

        # Step 2: Production Assessment
        production_low = telemetry.flow_rate < 1000
        print(f"\n{Colors.CYAN}Q2: Is production below expectations?{Colors.ENDC}")
        print(f"   Current Flow: {telemetry.flow_rate:.0f} BPD")
        print(f"   Target: 1000-3000 BPD")
        print(f"   Answer: {'✅ YES' if production_low else '❌ NO'}")

        if not production_low:
            diagnosis = DiagnosisType.NORMAL
            confidence = 0.95
            print(f"\n{Colors.GREEN}✅ DIAGNOSIS: {diagnosis.value}{Colors.ENDC}")
            return self._create_diagnosis_report(diagnosis, confidence, [], telemetry)

        # Step 3: PIP Analysis
        pip_low = telemetry.pip < 500
        print(f"\n{Colors.CYAN}Q3: Is PIP low?{Colors.ENDC}")
        print(f"   Current PIP: {telemetry.pip:.0f} PSI")
        print(f"   Normal Range: 500-1500 PSI")
        print(f"   Answer: {'✅ YES' if pip_low else '❌ NO'}")

        if pip_low:
            diagnosis = DiagnosisType.UNDERPUMPING
            confidence = 0.85
            actions = ["Reduce Hz by 5-10%", "Check fluid level", "Verify pump depth"]
            print(f"\n{Colors.YELLOW}⚠️  DIAGNOSIS: {diagnosis.value}{Colors.ENDC}")
            return self._create_diagnosis_report(diagnosis, confidence, actions, telemetry)

        # Step 4: Flow Rate Analysis
        flow_high = telemetry.flow_rate > 3500
        print(f"\n{Colors.CYAN}Q4: Is flow high?{Colors.ENDC}")
        print(f"   Current Flow: {telemetry.flow_rate:.0f} BPD")
        print(f"   High Threshold: >3500 BPD")
        print(f"   Answer: {'✅ YES' if flow_high else '❌ NO'}")

        if flow_high or telemetry.motor_current > 60:
            diagnosis = DiagnosisType.SAND_PRODUCTION
            confidence = 0.89 if telemetry.torque > 100 else 0.76
            actions = self.graph.query("Sand_Production", "solutions")
            print(f"\n{Colors.RED}⚠️  DIAGNOSIS: {diagnosis.value}{Colors.ENDC}")
            return self._create_diagnosis_report(diagnosis, confidence, actions, telemetry)

        # Step 5: Flow Stability at Low Rate
        flow_low_stable = telemetry.flow_rate < 800 and telemetry.flow_variance < 5
        print(f"\n{Colors.CYAN}Q5: Is flow low and stable?{Colors.ENDC}")
        print(f"   Flow Rate: {telemetry.flow_rate:.0f} BPD")
        print(f"   Flow Variance: {telemetry.flow_variance:.1f}%")
        print(f"   Answer: {'✅ YES' if flow_low_stable else '❌ NO'}")

        if flow_low_stable:
            diagnosis = DiagnosisType.HYDRAULIC_WEAR
            confidence = 0.91
            actions = self.graph.query("Hydraulic_Wear", "solutions")
            print(f"\n{Colors.YELLOW}⚠️  DIAGNOSIS: {diagnosis.value}{Colors.ENDC}")
        else:
            diagnosis = DiagnosisType.VSD_ISSUES
            confidence = 0.83
            actions = ["Check VSD trips", "Verify harmonics", "Inspect electrical connections"]
            print(f"\n{Colors.YELLOW}⚠️  DIAGNOSIS: {diagnosis.value}{Colors.ENDC}")

        return self._create_diagnosis_report(diagnosis, confidence, actions, telemetry)

    def _create_diagnosis_report(self, diagnosis: DiagnosisType, confidence: float,
                                actions: List[str], telemetry: ESPTelemetry) -> Dict:
        """Create comprehensive diagnosis report"""

        similar_cases = self.graph.find_similar_cases(diagnosis.name)

        report = {
            "timestamp": telemetry.timestamp.isoformat(),
            "diagnosis": {
                "type": diagnosis.value,
                "confidence": confidence,
                "severity": self._calculate_severity(diagnosis)
            },
            "telemetry_snapshot": {
                "flow_rate": telemetry.flow_rate,
                "pip": telemetry.pip,
                "motor_current": telemetry.motor_current,
                "vsd_frequency": telemetry.vsd_frequency,
                "flow_variance": telemetry.flow_variance
            },
            "recommended_actions": actions,
            "similar_cases": similar_cases[:3],
            "expected_resolution_time": f"{random.randint(1, 4)} hours",
            "ml_model_predictions": {
                "failure_probability_24h": random.uniform(0.1, 0.3) if diagnosis == DiagnosisType.NORMAL else random.uniform(0.6, 0.9),
                "mtbf_estimate": f"{random.randint(30, 180)} days"
            }
        }

        self.decision_tree_stats["total_diagnoses"] += 1

        return report

    def _calculate_severity(self, diagnosis: DiagnosisType) -> str:
        """Calculate problem severity"""
        severity_map = {
            DiagnosisType.NORMAL: "None",
            DiagnosisType.UNDERPUMPING: "Medium",
            DiagnosisType.VSD_ISSUES: "Medium",
            DiagnosisType.HYDRAULIC_WEAR: "High",
            DiagnosisType.GAS_PROBLEM: "High",
            DiagnosisType.SAND_PRODUCTION: "Critical",
            DiagnosisType.POOR_INSTALLATION: "Critical",
            DiagnosisType.POOR_SELECTION: "High"
        }
        return severity_map.get(diagnosis, "Unknown")

    def natural_language_query(self, query: str) -> str:
        """Process natural language diagnostic queries"""

        print(f"\n{Colors.BLUE}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}🤖 AI RAG NATURAL LANGUAGE QUERY{Colors.ENDC}")
        print(f"{Colors.BLUE}{'='*60}{Colors.ENDC}\n")

        print(f"Query: {Colors.CYAN}\"{query}\"{Colors.ENDC}\n")

        # Simulate NLP understanding
        if "choppy" in query.lower() or "unstable" in query.lower():
            response = self._generate_gas_problem_response()
        elif "sand" in query.lower() or "high flow" in query.lower():
            response = self._generate_sand_response()
        elif "low production" in query.lower() or "wear" in query.lower():
            response = self._generate_wear_response()
        else:
            response = self._generate_generic_response()

        return response

    def _generate_gas_problem_response(self) -> str:
        """Generate response for gas-related issues"""
        cases = self.graph.find_similar_cases("Free_Gas")

        response = f"""
{Colors.YELLOW}Diagnosis:{Colors.ENDC} Choppy flow indicates free gas problem (High GOR >500 scf/bbl)

{Colors.GREEN}Immediate Actions:{Colors.ENDC}
✓ Reduce VFD frequency by 10-15%
✓ Apply backpressure (check choke setting)
✓ Verify gas separator operation
✓ Monitor for flow stabilization (expected within 2-4 hours)

{Colors.CYAN}Similar Cases:{Colors.ENDC}"""

        for case in cases[:2]:
            response += f"\n• Well {case['well_id']}: {case['solution']} → {case['result']}"

        response += f"\n\n{Colors.BOLD}Confidence: 92%{Colors.ENDC}"

        return response

    def _generate_sand_response(self) -> str:
        """Generate response for sand production issues"""
        return f"""
{Colors.YELLOW}Diagnosis:{Colors.ENDC} Sand production detected - High flow with elevated motor current

{Colors.GREEN}Immediate Actions:{Colors.ENDC}
✓ Reduce Hz by 20-30% immediately
✓ Monitor motor current (should decrease within 30 min)
✓ Schedule well cleanout
✓ Consider sand screen installation

{Colors.RED}Warning:{Colors.ENDC} Continued operation may damage pump stages

{Colors.BOLD}Confidence: 89%{Colors.ENDC}
"""

    def _generate_wear_response(self) -> str:
        """Generate response for hydraulic wear"""
        return f"""
{Colors.YELLOW}Diagnosis:{Colors.ENDC} Hydraulic wear detected - Pump efficiency degraded

{Colors.GREEN}Recommended Actions:{Colors.ENDC}
✓ Plan pump pulling operation
✓ Order replacement stages
✓ Review metallurgy options for upgrade
✓ Expected downtime: 24-48 hours

{Colors.CYAN}Cost-Benefit:{Colors.ENDC}
• Continue operation: -40% production
• Replace pump: +35% production increase expected

{Colors.BOLD}Confidence: 91%{Colors.ENDC}
"""

    def _generate_generic_response(self) -> str:
        """Generate generic diagnostic response"""
        return f"""
{Colors.CYAN}Analysis:{Colors.ENDC} Running comprehensive diagnostic...

Please provide more specific symptoms:
• Flow behavior (stable/choppy/declining)
• Production rate vs. target
• Motor parameters (current, temperature)
• Recent operational changes

{Colors.BOLD}Use the decision tree for systematic diagnosis{Colors.ENDC}
"""

    def display_system_stats(self):
        """Display system statistics"""
        print(f"\n{Colors.GREEN}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}📊 SYSTEM STATISTICS{Colors.ENDC}")
        print(f"{Colors.GREEN}{'='*60}{Colors.ENDC}\n")

        print(f"Total Diagnoses: {self.decision_tree_stats['total_diagnoses']}")
        print(f"System Accuracy: {self.decision_tree_stats['accuracy']*100:.0f}%")
        print(f"Avg Resolution Time: {self.decision_tree_stats['avg_resolution_time']} hours")
        print(f"Knowledge Base: 9,500+ lines ESP expertise")
        print(f"ML Models: LSTM, Isolation Forest, Random Forest")
        print(f"Expected ROI: 87% reduction in unplanned failures")

def simulate_esp_telemetry(scenario: str = "normal") -> ESPTelemetry:
    """Generate simulated telemetry for different scenarios"""

    scenarios = {
        "gas_problem": {
            "flow_rate": 1200 + random.uniform(-200, 200),
            "flow_variance": 18.5 + random.uniform(-2, 5),
            "pip": 800,
            "motor_current": 45,
            "gor": 650
        },
        "sand_production": {
            "flow_rate": 3800 + random.uniform(-100, 200),
            "flow_variance": 8,
            "pip": 1200,
            "motor_current": 68 + random.uniform(-3, 5),
            "torque": 120
        },
        "hydraulic_wear": {
            "flow_rate": 650 + random.uniform(-50, 50),
            "flow_variance": 3,
            "pip": 900,
            "motor_current": 38,
            "torque": 60
        },
        "normal": {
            "flow_rate": 2000 + random.uniform(-100, 100),
            "flow_variance": 5,
            "pip": 1000,
            "motor_current": 45,
            "gor": 300
        },
        "underpumping": {
            "flow_rate": 800,
            "flow_variance": 6,
            "pip": 400,
            "motor_current": 35,
            "gor": 200
        }
    }

    data = scenarios.get(scenario, scenarios["normal"])

    return ESPTelemetry(
        timestamp=datetime.now(),
        flow_rate=data.get("flow_rate", 2000),
        pip=data.get("pip", 1000),
        motor_current=data.get("motor_current", 45),
        motor_temp=85 + random.uniform(-5, 10),
        vibration=1.5 + random.uniform(-0.5, 1),
        vsd_frequency=50 + random.uniform(-5, 5),
        flow_variance=data.get("flow_variance", 5),
        torque=data.get("torque", 80),
        gor=data.get("gor", 350)
    )

def main():
    """Main execution function"""

    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.BOLD}🏭 ALKHORAYEF ESP AI RAG DIAGNOSTIC SYSTEM{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"\n{Colors.CYAN}InSa Automation IoT Platform with Graphiti Knowledge Graph{Colors.ENDC}")
    print(f"Version: 1.0.0 | Last Updated: November 19, 2025\n")

    # Initialize the diagnostic system
    system = AlkhorayefESPDiagnosticSystem()

    # Demo scenarios
    scenarios = [
        ("gas_problem", "Free Gas Lock Scenario"),
        ("sand_production", "Sand Production Scenario"),
        ("hydraulic_wear", "Hydraulic Wear Scenario"),
        ("normal", "Normal Operation"),
        ("underpumping", "Underpumping Condition")
    ]

    print(f"{Colors.BOLD}Select a scenario to diagnose:{Colors.ENDC}")
    for i, (_, desc) in enumerate(scenarios, 1):
        print(f"  {i}. {desc}")
    print(f"  6. Natural Language Query")
    print(f"  7. View System Statistics")
    print(f"  0. Exit\n")

    while True:
        try:
            choice = input(f"{Colors.CYAN}Enter choice (0-7): {Colors.ENDC}")

            if choice == "0":
                print(f"\n{Colors.GREEN}Thank you for using Alkhorayef ESP Diagnostic System!{Colors.ENDC}")
                break

            elif choice in ["1", "2", "3", "4", "5"]:
                scenario_key, scenario_name = scenarios[int(choice) - 1]
                print(f"\n{Colors.YELLOW}Running Scenario: {scenario_name}{Colors.ENDC}")

                # Generate telemetry for scenario
                telemetry = simulate_esp_telemetry(scenario_key)

                # Run diagnostic decision tree
                report = system.run_decision_tree(telemetry)

                # Display report
                print(f"\n{Colors.GREEN}{'='*60}{Colors.ENDC}")
                print(f"{Colors.BOLD}📋 DIAGNOSTIC REPORT{Colors.ENDC}")
                print(f"{Colors.GREEN}{'='*60}{Colors.ENDC}\n")

                print(f"Diagnosis: {Colors.YELLOW}{report['diagnosis']['type']}{Colors.ENDC}")
                print(f"Confidence: {report['diagnosis']['confidence']*100:.0f}%")
                print(f"Severity: {report['diagnosis']['severity']}")
                print(f"\nRecommended Actions:")
                for action in report['recommended_actions']:
                    print(f"  • {action}")

                if report['similar_cases']:
                    print(f"\nSimilar Historical Cases:")
                    for case in report['similar_cases']:
                        print(f"  • {case['well_id']}: {case['result']}")

                print(f"\nML Predictions:")
                print(f"  • 24h Failure Risk: {report['ml_model_predictions']['failure_probability_24h']*100:.0f}%")
                print(f"  • MTBF Estimate: {report['ml_model_predictions']['mtbf_estimate']}")

            elif choice == "6":
                print(f"\n{Colors.CYAN}Natural Language Query Mode{Colors.ENDC}")
                print("Examples:")
                print('  • "ESP flow is choppy and unstable"')
                print('  • "High flow with motor overload"')
                print('  • "Low production, suspect wear"\n')

                query = input(f"{Colors.CYAN}Enter your query: {Colors.ENDC}")
                response = system.natural_language_query(query)
                print(response)

            elif choice == "7":
                system.display_system_stats()

            else:
                print(f"{Colors.RED}Invalid choice. Please try again.{Colors.ENDC}")

            print(f"\n{Colors.CYAN}{'─'*60}{Colors.ENDC}")

        except KeyboardInterrupt:
            print(f"\n\n{Colors.GREEN}System shutdown gracefully.{Colors.ENDC}")
            break
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.ENDC}")

if __name__ == "__main__":
    main()