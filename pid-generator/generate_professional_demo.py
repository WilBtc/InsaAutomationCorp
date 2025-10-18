#!/usr/bin/env python3
"""
Generate Professional P&ID Demo
Creates modern, client-ready P&ID with all professional features
"""

from pid_generator_professional import PIDGeneratorProfessional
from datetime import datetime

# Sample BOM data - Enhanced industrial control system
professional_bom = [
    {
        "part_name": "Siemens S7-1500 PLC Advanced Controller",
        "part_ipn": "6ES7515-2AM02-0AB0",
        "quantity": 1,
        "reference": "PLC1",
        "description": "Main process controller - CPU 1515-2 PN"
    },
    {
        "part_name": "Siemens HMI Comfort Panel 15-inch",
        "part_ipn": "6AV2124-0MC01-0AX0",
        "quantity": 1,
        "reference": "HMI1",
        "description": "Operator interface - 15\" TFT touchscreen"
    },
    {
        "part_name": "Rosemount 3144P Temperature Transmitter PT100",
        "part_ipn": "3144P-RTD-4-20MA",
        "quantity": 3,
        "reference": "TT-101",
        "description": "Process temperature - Reactor inlet"
    },
    {
        "part_name": "Rosemount 3144P Temperature Transmitter PT100",
        "part_ipn": "3144P-RTD-4-20MA",
        "quantity": 1,
        "reference": "TT-102",
        "description": "Process temperature - Reactor outlet"
    },
    {
        "part_name": "Rosemount 3051 Pressure Transmitter 0-10 Bar",
        "part_ipn": "3051CD-10BAR-4-20MA",
        "quantity": 2,
        "reference": "PT-101",
        "description": "Line pressure - Main process line"
    },
    {
        "part_name": "Rosemount 3051 Pressure Transmitter 0-10 Bar",
        "part_ipn": "3051CD-10BAR-4-20MA",
        "quantity": 1,
        "reference": "PT-102",
        "description": "Line pressure - Return line"
    },
    {
        "part_name": "Endress+Hauser Promag 53 Electromagnetic Flow Meter DN50",
        "part_ipn": "53P50-DN50-4-20MA",
        "quantity": 1,
        "reference": "FT-101",
        "description": "Main flow measurement - Process inlet"
    },
    {
        "part_name": "Endress+Hauser Promag 53 Electromagnetic Flow Meter DN40",
        "part_ipn": "53P40-DN40-4-20MA",
        "quantity": 1,
        "reference": "FT-102",
        "description": "Flow measurement - Return line"
    },
    {
        "part_name": "Fisher Control Valve DN50 PN16 + 3582i Positioner",
        "part_ipn": "FISHER-ED-DN50-PN16",
        "quantity": 1,
        "reference": "CV-101",
        "description": "Flow control valve - Process flow regulation"
    },
    {
        "part_name": "Fisher Control Valve DN40 PN16 + 3582i Positioner",
        "part_ipn": "FISHER-ED-DN40-PN16",
        "quantity": 1,
        "reference": "CV-102",
        "description": "Flow control valve - Return flow"
    },
    {
        "part_name": "ASCO Solenoid Valve 24VDC 2-Way DN25 PN16",
        "part_ipn": "ASCO-8210G094-24VDC",
        "quantity": 1,
        "reference": "SV-101",
        "description": "Emergency shutoff valve - Process isolation"
    },
    {
        "part_name": "Grundfos CR 10-3 Centrifugal Pump 3HP 1450 RPM",
        "part_ipn": "GRUNDFOS-CR10-3-3HP",
        "quantity": 1,
        "reference": "P-101",
        "description": "Main circulation pump - SS316L construction"
    }
]

def main():
    print("=" * 80)
    print("PROFESSIONAL P&ID GENERATION - CLIENT PRESENTATION EDITION")
    print("=" * 80)
    print()
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print()

    # Create professional P&ID generator
    pid = PIDGeneratorProfessional(
        project_name="Industrial Process Control System - Phase 1",
        customer="ABC Manufacturing Inc.",
        drawing_number="PID-2025-001",
        project_number="INSA-2025-042"
    )

    # Set professional metadata
    pid.revision = "A"
    pid.drawn_by = "INSA Engineering"
    pid.checked_by = ""  # Will show signature line
    pid.approved_by = ""  # Will show signature line

    print(f"Project: {pid.project_name}")
    print(f"Customer: {pid.customer}")
    print(f"Drawing No: {pid.drawing_number}")
    print(f"Project No: {pid.project_number}")
    print(f"Revision: {pid.revision}")
    print()

    # Load BOM
    print(f"Loading {len(professional_bom)} components from BOM...")
    pid.load_from_bom(professional_bom)

    # Create intelligent connections
    print("\nCreating intelligent process connections...")

    # All transmitters → PLC (signal lines)
    pid.add_connection("TT-101", "PLC1", "signal")
    pid.add_connection("TT-102", "PLC1", "signal")
    pid.add_connection("PT-101", "PLC1", "signal")
    pid.add_connection("PT-102", "PLC1", "signal")
    pid.add_connection("FT-101", "PLC1", "signal")
    pid.add_connection("FT-102", "PLC1", "signal")

    # PLC → Control valves (signal lines)
    pid.add_connection("PLC1", "CV-101", "signal")
    pid.add_connection("PLC1", "CV-102", "signal")
    pid.add_connection("PLC1", "SV-101", "signal")

    # PLC → HMI (electric)
    pid.add_connection("PLC1", "HMI1", "electric")

    # Pump → Valves (process lines)
    pid.add_connection("P-101", "CV-101", "process")
    pid.add_connection("P-101", "SV-101", "process")

    print(f"✓ Created {len(pid.connections)} connections")

    # Generate outputs
    print("\n" + "=" * 80)
    print("GENERATING PROFESSIONAL OUTPUTS")
    print("=" * 80)

    print("\n1. Generating professional SVG diagram...")
    svg_file = pid.generate_svg()

    print("2. Exporting enhanced component list...")
    json_file = pid.export_component_list()

    # Show results
    print("\n" + "=" * 80)
    print("✓ PROFESSIONAL P&ID GENERATION COMPLETE!")
    print("=" * 80)

    import os

    print(f"\nOutput Files:")
    print(f"  • Professional SVG: {svg_file}")
    print(f"                      Size: {os.path.getsize(svg_file) / 1024:.1f} KB")
    print(f"  • Component Data:   {json_file}")
    print(f"                      Size: {os.path.getsize(json_file) / 1024:.1f} KB")

    print("\n" + "=" * 80)
    print("PROFESSIONAL FEATURES INCLUDED:")
    print("=" * 80)
    print("\n✅ Enhanced Title Block:")
    print("   • Company branding (INSA Automation Corp)")
    print("   • Project and drawing numbers")
    print("   • Approval signature lines (Drawn/Checked/Approved)")
    print("   • ISA-5.1-2024 standard reference")
    print()
    print("✅ Comprehensive Legend:")
    print("   • All line types with descriptions")
    print("   • ISA-5.1 instrument symbols")
    print("   • Color-coded connections")
    print("   • Standard compliance notes")
    print()
    print("✅ Grid System:")
    print("   • Alphanumeric grid (A-Z, 1-20)")
    print("   • Easy equipment location")
    print("   • Professional appearance")
    print()
    print("✅ Revision Block:")
    print("   • Complete revision history")
    print("   • Change tracking capability")
    print("   • Professional documentation")
    print()
    print("✅ Component Summary:")
    print(f"   • Total Components: {len(pid.components)}")
    print(f"   • Total Connections: {len(pid.connections)}")
    print()

    print("=" * 80)
    print("READY FOR CLIENT PRESENTATION")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
