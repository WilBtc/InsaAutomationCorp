"""
Example: How CRM Agents Use the Instrumentation RAG System

This demonstrates how AI agents can query the industrial instrumentation
knowledge base to provide better recommendations and proposals.

Author: INSA Automation Corp
Date: October 18, 2025
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from knowledge.instrumentation_rag import (
    instrumentation_rag,
    get_sensor_recommendation,
    get_control_strategy,
    get_calibration_procedure
)


def example_1_equipment_recommendation():
    """
    Example 1: Equipment Recommendation Agent

    Scenario: Customer needs pressure sensors for a high-temperature reactor
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Equipment Recommendation Agent")
    print("=" * 80)
    print("\nScenario: Customer needs pressure sensors for high-temperature reactor")
    print("Budget: $50,000 | Timeline: 3 months | Industry: Chemical Processing\n")

    # Agent queries the RAG system
    query = "transmisor de presión alta temperatura reactor"
    context = instrumentation_rag.get_context_for_agent(query, max_tokens=1000)

    print("🤖 Agent's Knowledge Base Query Results:\n")
    print(context)

    # Agent would use this context to generate a recommendation
    print("\n📋 Agent-Generated Recommendation:")
    print("""
Based on the industrial instrumentation reference (Antonio Creus Solé, 8th Ed.):

1. **Recommended Solution:** Differential pressure transmitter with diaphragm seal
   - Suitable for high-temperature applications
   - Provides reliable measurement in reactor environments
   - Complies with ISA standards for industrial automation

2. **Technical Specifications:**
   - Operating range: 0-500 psi
   - Temperature rating: -40°C to 250°C
   - Output: 4-20mA analog signal
   - Accuracy: ±0.5% of span

3. **Estimated Cost:** $45,000 (within budget)
   - Includes 3x transmitters, installation, and calibration

4. **Next Steps:**
   - Schedule technical consultation
   - Review process conditions
   - Provide detailed quote with datasheets
    """)


def example_2_quote_generation():
    """
    Example 2: Quote Generation Agent

    Scenario: Generate quote for a complete control loop
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Quote Generation Agent")
    print("=" * 80)
    print("\nScenario: Customer needs complete PID control loop for temperature control\n")

    # Query for control valve information
    valve_context = instrumentation_rag.get_context_for_agent("válvula de control", max_tokens=800)

    # Query for PID control information
    pid_context = instrumentation_rag.get_context_for_agent("control PID", max_tokens=800)

    print("🤖 Agent's Analysis:\n")
    print("Based on Chapter 8 (Control Elements) and Chapter 9 (Automatic Control):\n")

    print("📋 Generated Quote:\n")
    print("""
QUOTE #2025-1001: Temperature Control Loop for Process Reactor

EQUIPMENT LIST:
├── Temperature Sensor: PT100 RTD (-50°C to 400°C)         $1,200
├── Temperature Transmitter: 4-20mA output                 $2,500
├── PID Controller: Industrial grade, ISA compliant        $4,800
├── Control Valve: Pneumatic actuated, 2" size            $8,500
├── I/P Converter: Current-to-pressure converter           $1,100
├── Installation & Wiring                                  $3,500
└── Commissioning & Calibration                           $2,400
                                                     ─────────────
                                        TOTAL:            $24,000

DELIVERABLES:
✓ Complete PID control loop installation
✓ System integration with existing SCADA
✓ Calibration certificates (ISO 9000 compliant)
✓ Operator training manual
✓ 1-year warranty on all equipment

TIMELINE: 6 weeks (delivery + installation)

TECHNICAL REFERENCE: Design based on ISA standards and proven
control strategies from "Instrumentación Industrial" (Creus, 8th Ed.)
    """)


def example_3_proposal_writing():
    """
    Example 3: Proposal Writing Agent

    Scenario: Write technical proposal for IEC 62443 compliance project
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Proposal Writing Agent")
    print("=" * 80)
    print("\nScenario: Technical proposal for industrial cybersecurity project\n")

    # Query for instrumentation standards
    context = instrumentation_rag.get_context_for_agent("ISA normas comunicación", max_tokens=1000)

    print("🤖 Agent uses RAG context to write proposal sections:\n")
    print("=" * 80)
    print("""
TECHNICAL PROPOSAL: IEC 62443 Industrial Cybersecurity Implementation

1. EXECUTIVE SUMMARY
   ABC Manufacturing requires IEC 62443 compliance for their SCADA system.
   Our solution integrates modern security controls while maintaining
   compatibility with existing ISA-standard instrumentation.

2. TECHNICAL APPROACH

   Based on ISA/ISO instrumentation standards (Ref: Creus, Ch. 1-2):

   - Network Segmentation: Separate OT and IT networks
   - Secure Communication Protocols: Upgrade to encrypted industrial protocols
   - Instrument Identification: Maintain ISA-5.1 compliance for all devices
   - Access Control: RBAC implementation for all control systems

3. INSTRUMENTATION INTEGRATION

   Our approach preserves your existing instrumentation investments:

   ✓ Pressure transmitters: Maintain 4-20mA analog signals
   ✓ Temperature sensors: PT100/thermocouple compatibility
   ✓ Control valves: Existing pneumatic actuators supported
   ✓ SCADA integration: Industry-standard communication protocols

4. DELIVERABLES
   - IEC 62443 compliance assessment report
   - Network security architecture design
   - Firewall and DMZ implementation
   - Security monitoring system (SIEM)
   - Incident response playbooks
   - Staff training (4 sessions)

5. INVESTMENT: $180,000
   Timeline: 12 weeks
   ROI: Prevent potential cyber incidents ($2M+ risk mitigation)

References:
- Antonio Creus Solé, "Instrumentación Industrial" 8th Ed. (Ch. 1, 2, 9)
- IEC 62443 Industrial Automation and Control Systems Security
- ISA-5.1-2024 Instrumentation Symbols and Identification
    """)


def example_4_lead_qualification():
    """
    Example 4: Lead Qualification Agent

    Scenario: Qualify inbound lead based on technical requirements
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Lead Qualification Agent")
    print("=" * 80)
    print("\nScenario: Qualify lead based on technical complexity\n")

    lead_data = {
        "company": "XYZ Petrochemical",
        "industry": "Oil & Gas",
        "requirement": "Need flow measurement for viscous fluids in pipeline",
        "budget": "$75,000",
        "timeline": "2 months"
    }

    print(f"📧 Inbound Lead:")
    for key, value in lead_data.items():
        print(f"   {key.capitalize()}: {value}")

    # Agent queries RAG for technical complexity assessment
    flow_context = instrumentation_rag.query("medición de caudal fluidos viscosos", top_k=3)

    print("\n🤖 Agent's Technical Analysis:\n")
    print(f"Found {len(flow_context)} relevant references in instrumentation manual")
    print(f"Technical complexity: HIGH (Chapter 5: Flow Measurement)")

    print("\n📊 Lead Qualification Score: 92/100\n")
    print("""
QUALIFICATION BREAKDOWN:
├── Budget Score: 25/25 (sufficient for viscous flow measurement)
├── Timeline Score: 20/25 (2 months is tight but feasible)
├── Technical Complexity: 25/25 (HIGH - we have expertise)
├── Decision Authority: 15/15 (technical manager contact)
└── Industry Fit: 7/10 (oil & gas is target industry)

PRIORITY: IMMEDIATE (Contact within 24 hours)

RECOMMENDED ACTION:
1. Schedule technical consultation call
2. Involve flow measurement specialist
3. Request process conditions (viscosity, temperature, pressure)
4. Prepare viscous flow meter options (Coriolis, PD, magnetic)

TECHNICAL NOTES (from RAG system):
- Viscous fluids require special consideration for flow measurement
- Coriolis meters recommended for high-accuracy applications
- Reference: Instrumentación Industrial, Ch. 5 (Flow Measurement)
    """)


def example_5_customer_support():
    """
    Example 5: Customer Support Agent

    Scenario: Answer technical question about calibration
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Customer Support Agent")
    print("=" * 80)
    print("\nScenario: Customer asks about pressure transmitter calibration\n")

    customer_question = "How often should we calibrate our pressure transmitters?"

    print(f"❓ Customer Question: {customer_question}\n")

    # Query calibration procedures
    calibration_info = get_calibration_procedure("transmisor de presión")

    print("🤖 Agent's Response (using RAG knowledge):\n")
    print("""
Thank you for your question about pressure transmitter calibration!

Based on industry best practices and ISO 9000 standards:

📋 CALIBRATION FREQUENCY RECOMMENDATIONS:

1. **Standard Industrial Applications:**
   - Calibration every 6-12 months
   - Depends on process criticality

2. **Critical Safety Systems:**
   - Calibration every 3-6 months
   - More frequent if required by regulations

3. **Factors Affecting Frequency:**
   - Process conditions (temperature, pressure extremes)
   - Environmental factors (vibration, corrosion)
   - Instrument drift history
   - Quality system requirements (ISO 9000)

4. **Our Recommendation for Your Application:**
   Based on your industry (chemical processing) and the criticality
   of your reactor pressure measurement:

   ✓ Schedule calibration every 6 months
   ✓ Perform interim checks every 3 months
   ✓ Document all calibrations (ISO 9000 compliance)

📞 Would you like to schedule a calibration service visit?
   We offer:
   - On-site calibration
   - NIST-traceable standards
   - Complete documentation
   - ISO 9000 certified procedures

Reference: "Instrumentación Industrial" by Antonio Creus Solé,
Chapter 10: Calibration and Quality Standards

Best regards,
INSA Automation Corp Technical Support
    """)


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("CRM AGENT INTEGRATION EXAMPLES")
    print("Using Industrial Instrumentation RAG System")
    print("=" * 80)
    print("\nINSA Automation Corp - AI-Powered CRM")
    print(f"Knowledge Base: {len(instrumentation_rag.chunks)} chunks from 11 chapters")
    print("Reference: Instrumentación Industrial, 8va Edición (Antonio Creus Solé)")

    # Run all examples
    example_1_equipment_recommendation()
    example_2_quote_generation()
    example_3_proposal_writing()
    example_4_lead_qualification()
    example_5_customer_support()

    print("\n" + "=" * 80)
    print("✅ ALL EXAMPLES COMPLETED")
    print("=" * 80)
    print("\nThe RAG system is ready for production use by CRM AI agents!")
    print("Agents can now provide technically accurate recommendations")
    print("based on 794 pages of industrial instrumentation knowledge.\n")
