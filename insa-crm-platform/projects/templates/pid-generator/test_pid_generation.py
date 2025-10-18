#!/usr/bin/env python3
"""
Test P&ID Generation with Sample BOM Data
Demonstrates automated P&ID generation without requiring InvenTree
"""

from pid_generator import PIDGenerator

# Sample BOM data for industrial control system
sample_bom = [
    {
        "part_name": "Siemens S7-1200 PLC",
        "part_ipn": "6ES7214-1AG40-0XB0",
        "quantity": 1,
        "reference": "PLC1",
        "description": "Main controller - CPU 1214C DC/DC/DC"
    },
    {
        "part_name": "Weintek HMI 7-inch Touchscreen",
        "part_ipn": "MT6071iP",
        "quantity": 1,
        "reference": "HMI1",
        "description": "Operator interface panel"
    },
    {
        "part_name": "Temperature Transmitter PT100 4-20mA",
        "part_ipn": "TT-4100-PT100",
        "quantity": 2,
        "reference": "TT-101",
        "description": "Process temperature measurement"
    },
    {
        "part_name": "Temperature Transmitter PT100 4-20mA",
        "part_ipn": "TT-4100-PT100",
        "quantity": 1,
        "reference": "TT-102",
        "description": "Return temperature measurement"
    },
    {
        "part_name": "Pressure Transmitter 0-10 Bar 4-20mA",
        "part_ipn": "PT-1000-10B",
        "quantity": 2,
        "reference": "PT-101",
        "description": "Line pressure monitoring"
    },
    {
        "part_name": "Flow Transmitter Electromagnetic DN50",
        "part_ipn": "FT-EM-DN50",
        "quantity": 1,
        "reference": "FT-101",
        "description": "Main flow measurement"
    },
    {
        "part_name": "Control Valve DN50 PN16 with Actuator",
        "part_ipn": "CV-DN50-PN16-24V",
        "quantity": 2,
        "reference": "CV-101",
        "description": "Flow control valve - pneumatic actuated"
    },
    {
        "part_name": "Control Valve DN40 PN16 with Actuator",
        "part_ipn": "CV-DN40-PN16-24V",
        "quantity": 1,
        "reference": "CV-102",
        "description": "Return flow control"
    },
    {
        "part_name": "Solenoid Valve 24VDC 2-Way DN25",
        "part_ipn": "SV-24V-2W-DN25",
        "quantity": 1,
        "reference": "SV-101",
        "description": "Emergency shutoff valve"
    },
    {
        "part_name": "Centrifugal Pump 3HP 1450 RPM",
        "part_ipn": "PUMP-3HP-1450",
        "quantity": 1,
        "reference": "P-101",
        "description": "Main circulation pump"
    }
]

def main():
    print("=" * 70)
    print("P&ID Generation Test - Industrial Control System")
    print("=" * 70)
    print()

    # Create P&ID generator
    pid = PIDGenerator(
        project_name="Industrial Process Control System",
        customer="ABC Manufacturing"
    )

    # Load BOM data
    print(f"Loading {len(sample_bom)} components from BOM...")
    pid.load_from_bom(sample_bom)

    # Add manual connections for better control
    print("\nCreating intelligent connections...")

    # All transmitters → PLC (signal lines)
    pid.add_connection("TT-101", "PLC1", "signal")
    pid.add_connection("TT-102", "PLC1", "signal")
    pid.add_connection("PT-101", "PLC1", "signal")
    pid.add_connection("FT-101", "PLC1", "signal")

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
    print("\n" + "=" * 70)
    print("Generating Output Files...")
    print("=" * 70)

    print("\n1. Generating SVG diagram (web/print)...")
    svg_file = pid.generate_svg()

    print("2. Generating DXF diagram (CAD software)...")
    dxf_file = pid.generate_dxf()

    print("3. Exporting component list (JSON)...")
    json_file = pid.export_component_list()

    # Show results
    print("\n" + "=" * 70)
    print("✓ P&ID Generation Complete!")
    print("=" * 70)

    import os

    print(f"\nOutput Files:")
    print(f"  • SVG Diagram:    {svg_file}")
    print(f"                    Size: {os.path.getsize(svg_file) / 1024:.1f} KB")
    print(f"  • DXF CAD File:   {dxf_file}")
    print(f"                    Size: {os.path.getsize(dxf_file) / 1024:.1f} KB")
    print(f"  • Component List: {json_file}")
    print(f"                    Size: {os.path.getsize(json_file) / 1024:.1f} KB")

    print("\n" + "=" * 70)
    print("Usage:")
    print("=" * 70)
    print(f"\n  View SVG in browser:")
    print(f"    firefox {svg_file}")
    print(f"\n  Open DXF in CAD software:")
    print(f"    - AutoCAD, QCAD, LibreCAD, FreeCAD")
    print(f"\n  View component list:")
    print(f"    cat {json_file} | jq")

    print("\n" + "=" * 70)
    print("Component Summary:")
    print("=" * 70)
    print(f"\n  Total Components: {len(pid.components)}")
    print(f"  Total Connections: {len(pid.connections)}")
    print(f"\n  Components by Type:")

    from collections import Counter
    comp_types = Counter([c['type'] for c in pid.components])
    for comp_type, count in sorted(comp_types.items()):
        print(f"    • {comp_type}: {count}")

    print("\n  Connection Types:")
    conn_types = Counter([c['type'] for c in pid.connections])
    for conn_type, count in sorted(conn_types.items()):
        print(f"    • {conn_type}: {count}")

    print("\n" + "=" * 70)

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
