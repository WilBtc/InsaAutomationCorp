#!/usr/bin/env python3
"""
InvenTree P&ID Integration Script
Automatically generates P&ID diagrams from InvenTree BOM data
Version: 1.0.0
"""

import requests
import argparse
import sys
from typing import List, Dict, Tuple
from pid_generator import PIDGenerator

# InvenTree configuration
INVENTREE_URL = "http://100.100.101.1:9600"
INVENTREE_API = f"{INVENTREE_URL}/api"
INVENTREE_USER = "admin"
INVENTREE_PASS = "insaadmin2025"


class InvenTreePIDIntegration:
    """Integration between InvenTree and P&ID Generator"""

    def __init__(self):
        self.session = requests.Session()
        self.session.auth = (INVENTREE_USER, INVENTREE_PASS)
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

    def get_part_details(self, part_id: int) -> Dict:
        """Get part details from InvenTree"""
        try:
            response = self.session.get(f"{INVENTREE_API}/part/{part_id}/")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching part {part_id}: {e}")
            return {}

    def get_bom(self, assembly_part_id: int) -> List[Dict]:
        """Get BOM (Bill of Materials) from InvenTree"""
        try:
            response = self.session.get(
                f"{INVENTREE_API}/bom/",
                params={"part": assembly_part_id}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching BOM for part {assembly_part_id}: {e}")
            return []

    def convert_bom_to_pid_format(self, bom_raw: List[Dict]) -> List[Dict]:
        """
        Convert InvenTree BOM format to P&ID generator format

        Args:
            bom_raw: Raw BOM data from InvenTree API

        Returns:
            List of components in P&ID format
        """
        pid_bom = []

        for idx, item in enumerate(bom_raw):
            # Extract sub-part details
            sub_part = item.get("sub_part_detail", {})

            # Get part name and details
            part_name = sub_part.get("name", "Unknown Part")
            part_ipn = sub_part.get("IPN", "")
            quantity = item.get("quantity", 1)
            reference = item.get("reference", f"COMP-{idx + 1}")
            note = item.get("note", "")

            # Build description from available data
            description = note if note else sub_part.get("description", "")

            pid_bom.append({
                "part_name": part_name,
                "part_ipn": part_ipn,
                "quantity": quantity,
                "reference": reference,
                "description": description
            })

        return pid_bom

    def generate_pid_from_assembly(self, assembly_part_id: int,
                                   project_name: str = None,
                                   customer: str = "") -> Tuple[str, str, str]:
        """
        Generate P&ID diagrams from InvenTree assembly part

        Args:
            assembly_part_id: InvenTree assembly part ID
            project_name: Project name (defaults to part name)
            customer: Customer name

        Returns:
            Tuple of (svg_file, dxf_file, json_file)
        """
        # Get assembly part details
        part_details = self.get_part_details(assembly_part_id)

        if not part_details:
            raise ValueError(f"Could not fetch details for part ID {assembly_part_id}")

        # Use part name as project name if not provided
        if not project_name:
            project_name = part_details.get("name", f"Assembly {assembly_part_id}")

        print(f"Generating P&ID for: {project_name}")

        # Get BOM
        bom_raw = self.get_bom(assembly_part_id)

        if not bom_raw:
            print(f"Warning: No BOM found for assembly part {assembly_part_id}")
            print("Creating empty P&ID...")

        # Convert BOM to P&ID format
        pid_bom = self.convert_bom_to_pid_format(bom_raw)

        print(f"Found {len(pid_bom)} components in BOM")

        # Create P&ID generator
        pid = PIDGenerator(project_name, customer)

        # Load BOM
        pid.load_from_bom(pid_bom)

        # Add automatic connections based on component types
        self._auto_connect_components(pid)

        # Generate output files
        print("Generating SVG diagram...")
        svg_file = pid.generate_svg()

        print("Generating DXF diagram...")
        dxf_file = pid.generate_dxf()

        print("Exporting component list...")
        json_file = pid.export_component_list()

        return svg_file, dxf_file, json_file

    def _auto_connect_components(self, pid: PIDGenerator) -> None:
        """
        Automatically create connections based on component types

        Args:
            pid: PIDGenerator instance
        """
        # Group components by type
        plcs = []
        hmis = []
        transmitters = []
        valves = []
        pumps = []

        for comp in pid.components:
            tag = comp["tag"]
            comp_type = comp["type"].lower()

            if "plc" in comp_type:
                plcs.append(tag)
            elif "hmi" in comp_type:
                hmis.append(tag)
            elif "transmitter" in comp_type or tag.startswith(("TT", "PT", "FT", "LT")):
                transmitters.append(tag)
            elif "valve" in comp_type or tag.startswith(("CV", "SV")):
                valves.append(tag)
            elif "pump" in comp_type:
                pumps.append(tag)

        # Auto-connect logic:
        # 1. All transmitters → PLC (signal lines)
        # 2. PLC → Valves (signal lines)
        # 3. PLC → HMI (electric lines)
        # 4. Pumps → Valves (process lines)

        if plcs:
            main_plc = plcs[0]  # Use first PLC as main controller

            # Connect transmitters to PLC
            for transmitter in transmitters:
                pid.add_connection(transmitter, main_plc, "signal")

            # Connect PLC to valves
            for valve in valves:
                pid.add_connection(main_plc, valve, "signal")

            # Connect PLC to HMIs
            for hmi in hmis:
                pid.add_connection(main_plc, hmi, "electric")

        # Connect pumps to valves (process flow)
        for pump in pumps:
            for valve in valves:
                pid.add_connection(pump, valve, "process")

        connections_count = len(transmitters) + len(valves) + len(hmis) + len(pumps)
        if connections_count > 0:
            print(f"Auto-generated {connections_count} connections")


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description="Generate P&ID diagrams from InvenTree BOM data"
    )
    parser.add_argument(
        "assembly_id",
        type=int,
        help="InvenTree assembly part ID"
    )
    parser.add_argument(
        "-p", "--project",
        type=str,
        help="Project name (defaults to part name)"
    )
    parser.add_argument(
        "-c", "--customer",
        type=str,
        default="",
        help="Customer name"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Output directory (default: current directory)"
    )

    args = parser.parse_args()

    try:
        # Create integration instance
        integration = InvenTreePIDIntegration()

        # Generate P&ID
        svg_file, dxf_file, json_file = integration.generate_pid_from_assembly(
            assembly_part_id=args.assembly_id,
            project_name=args.project,
            customer=args.customer
        )

        # Print results
        print("\n" + "="*60)
        print("✓ P&ID Generation Complete!")
        print("="*60)
        print(f"SVG Diagram:      {svg_file}")
        print(f"DXF CAD File:     {dxf_file}")
        print(f"Component List:   {json_file}")
        print("="*60)

        # Show file sizes
        import os
        svg_size = os.path.getsize(svg_file) / 1024
        dxf_size = os.path.getsize(dxf_file) / 1024
        json_size = os.path.getsize(json_file) / 1024

        print(f"\nFile Sizes:")
        print(f"  SVG:  {svg_size:.1f} KB")
        print(f"  DXF:  {dxf_size:.1f} KB")
        print(f"  JSON: {json_size:.1f} KB")

        return 0

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
