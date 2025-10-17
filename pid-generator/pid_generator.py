#!/usr/bin/env python3
"""
P&ID Diagram Generator for Industrial Automation Projects
Automatically generates P&ID diagrams from BOM (Bill of Materials) data
Version: 1.0.0
"""

import svgwrite
import ezdxf
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import json
from pid_symbols import PIDSymbols


class PIDGenerator:
    """Automated P&ID diagram generator from BOM data"""

    def __init__(self, project_name: str, customer: str = ""):
        """
        Initialize P&ID generator

        Args:
            project_name: Project name for the diagram
            customer: Customer name
        """
        self.project_name = project_name
        self.customer = customer
        self.components = []
        self.connections = []

        # Drawing dimensions (A3 landscape: 420mm x 297mm = 1587 x 1122 pixels @96 DPI)
        self.width = 1587
        self.height = 1122
        self.margin = 100

        # Initialize SVG drawing
        self.dwg = svgwrite.Drawing(
            filename=f"{project_name.replace(' ', '_')}_PID.svg",
            size=(f"{self.width}px", f"{self.height}px"),
            profile='full'
        )

        # Initialize symbol library
        self.symbols = PIDSymbols(self.dwg, scale=1.0)

        # Component positions (auto-layout)
        self.positions = {}
        self.current_row = 0
        self.current_col = 0

    def add_component(self, component_type: str, tag: str, description: str = "",
                     quantity: int = 1, specifications: Dict = None) -> None:
        """
        Add a component to the P&ID

        Args:
            component_type: Type (PLC, Sensor, Valve, Pump, Tank, HMI, etc)
            tag: Component tag/ID
            description: Component description
            quantity: Quantity of this component
            specifications: Technical specifications
        """
        self.components.append({
            "type": component_type,
            "tag": tag,
            "description": description,
            "quantity": quantity,
            "specifications": specifications or {}
        })

    def add_connection(self, from_tag: str, to_tag: str,
                      connection_type: str = "process") -> None:
        """
        Add a connection between components

        Args:
            from_tag: Source component tag
            to_tag: Destination component tag
            connection_type: "process", "signal", "pneumatic", "electric"
        """
        self.connections.append({
            "from": from_tag,
            "to": to_tag,
            "type": connection_type
        })

    def _calculate_positions(self) -> None:
        """Calculate automatic layout positions for components"""
        # Layout parameters
        cols = 5  # Components per row
        col_spacing = (self.width - 2 * self.margin) / (cols + 1)
        row_spacing = 150

        # Group components by type for better organization
        component_groups = {}
        for comp in self.components:
            comp_type = comp["type"]
            if comp_type not in component_groups:
                component_groups[comp_type] = []
            component_groups[comp_type].append(comp)

        # Position components
        row = 0
        col = 0

        for group_name, group_components in component_groups.items():
            for comp in group_components:
                tag = comp["tag"]
                x = self.margin + (col + 1) * col_spacing
                y = self.margin + row * row_spacing + 100

                self.positions[tag] = (x, y)

                col += 1
                if col >= cols:
                    col = 0
                    row += 1

            # Start new row for next component type
            if col > 0:
                col = 0
                row += 1

    def _draw_title_block(self) -> None:
        """Draw standard title block (bottom right corner)"""
        block_width = 400
        block_height = 150
        x = self.width - block_width - 20
        y = self.height - block_height - 20

        # Border
        title_group = self.dwg.g(id="title_block")
        title_group.add(self.dwg.rect(
            insert=(x, y),
            size=(block_width, block_height),
            fill="white",
            stroke="black",
            stroke_width=2
        ))

        # Horizontal dividers
        title_group.add(self.dwg.line(
            start=(x, y + 40),
            end=(x + block_width, y + 40),
            stroke="black",
            stroke_width=1
        ))
        title_group.add(self.dwg.line(
            start=(x, y + 80),
            end=(x + block_width, y + 80),
            stroke="black",
            stroke_width=1
        ))
        title_group.add(self.dwg.line(
            start=(x, y + 110),
            end=(x + block_width, y + 110),
            stroke="black",
            stroke_width=1
        ))

        # Vertical dividers
        title_group.add(self.dwg.line(
            start=(x + 120, y + 40),
            end=(x + 120, y + block_height),
            stroke="black",
            stroke_width=1
        ))
        title_group.add(self.dwg.line(
            start=(x + 240, y + 80),
            end=(x + 240, y + block_height),
            stroke="black",
            stroke_width=1
        ))

        # Title
        title_group.add(self.dwg.text(
            self.project_name,
            insert=(x + 10, y + 25),
            font_size=18,
            font_family="Arial",
            font_weight="bold"
        ))

        # Customer
        if self.customer:
            title_group.add(self.dwg.text(
                f"Customer: {self.customer}",
                insert=(x + 10, y + 65),
                font_size=14,
                font_family="Arial"
            ))

        # Labels
        labels = [
            ("Drawing Type:", "P&ID", x + 10, y + 95),
            ("Date:", datetime.now().strftime("%Y-%m-%d"), x + 10, y + 130),
            ("Drawn By:", "INSA Automation", x + 130, y + 95),
            ("Sheet:", "1 of 1", x + 130, y + 130),
            ("Rev:", "A", x + 250, y + 95),
            ("Scale:", "NTS", x + 250, y + 130)
        ]

        for label, value, lx, ly in labels:
            title_group.add(self.dwg.text(
                label,
                insert=(lx, ly),
                font_size=10,
                font_family="Arial",
                font_weight="bold"
            ))
            title_group.add(self.dwg.text(
                value,
                insert=(lx + 70, ly),
                font_size=10,
                font_family="Arial"
            ))

        self.dwg.add(title_group)

    def _draw_border(self) -> None:
        """Draw A3 drawing border"""
        # Outer border
        self.dwg.add(self.dwg.rect(
            insert=(20, 20),
            size=(self.width - 40, self.height - 40),
            fill="none",
            stroke="black",
            stroke_width=2
        ))

        # Inner border (margin)
        self.dwg.add(self.dwg.rect(
            insert=(40, 40),
            size=(self.width - 80, self.height - 80),
            fill="none",
            stroke="black",
            stroke_width=1
        ))

    def _draw_component(self, component: Dict) -> None:
        """Draw a component symbol based on its type"""
        tag = component["tag"]
        comp_type = component["type"].lower()
        pos = self.positions.get(tag)

        if not pos:
            return

        # Map component types to symbol methods
        if "plc" in comp_type or "controller" in comp_type:
            symbol = self.symbols.controller_plc(pos, tag)
        elif "hmi" in comp_type or "display" in comp_type or "screen" in comp_type:
            symbol = self.symbols.hmi_display(pos, tag)
        elif "temperature" in comp_type or comp_type.startswith("tt"):
            symbol = self.symbols.temperature_transmitter(pos, tag)
        elif "pressure" in comp_type or comp_type.startswith("pt"):
            symbol = self.symbols.pressure_transmitter(pos, tag)
        elif "flow" in comp_type or comp_type.startswith("ft"):
            symbol = self.symbols.flow_transmitter(pos, tag)
        elif "level" in comp_type or comp_type.startswith("lt"):
            symbol = self.symbols.level_transmitter(pos, tag)
        elif "valve" in comp_type and ("control" in comp_type or "cv" in comp_type):
            symbol = self.symbols.valve_control(pos, tag)
        elif "valve" in comp_type and ("solenoid" in comp_type or "sv" in comp_type):
            symbol = self.symbols.valve_solenoid(pos, tag)
        elif "valve" in comp_type:
            symbol = self.symbols.valve_manual(pos, tag)
        elif "pump" in comp_type:
            symbol = self.symbols.pump_centrifugal(pos, tag)
        elif "tank" in comp_type or "vessel" in comp_type:
            symbol = self.symbols.tank_vertical(pos, tag)
        elif "sensor" in comp_type:
            symbol = self.symbols.sensor_generic(pos, tag, component.get("description", "Sensor"))
        elif "pid" in comp_type:
            symbol = self.symbols.controller_pid(pos, tag)
        else:
            # Default: generic instrument circle
            symbol = self.symbols.instrument_circle(pos, tag, component.get("description", ""))

        self.dwg.add(symbol)

    def _draw_connections(self) -> None:
        """Draw connections between components"""
        for conn in self.connections:
            from_tag = conn["from"]
            to_tag = conn["to"]
            conn_type = conn["type"]

            from_pos = self.positions.get(from_tag)
            to_pos = self.positions.get(to_tag)

            if from_pos and to_pos:
                line = self.symbols.process_line(from_pos, to_pos, conn_type)
                self.dwg.add(line)

    def _generate_legend(self) -> None:
        """Generate symbol legend"""
        legend_x = 60
        legend_y = self.height - 180
        legend_width = 300
        legend_height = 140

        # Legend box
        legend_group = self.dwg.g(id="legend")
        legend_group.add(self.dwg.rect(
            insert=(legend_x, legend_y),
            size=(legend_width, legend_height),
            fill="white",
            stroke="black",
            stroke_width=1
        ))

        # Title
        legend_group.add(self.dwg.text(
            "LEGEND",
            insert=(legend_x + 10, legend_y + 20),
            font_size=14,
            font_family="Arial",
            font_weight="bold"
        ))

        # Legend items
        items = [
            ("─────", "Process Line", "black"),
            ("─ ─ ─", "Signal Line", "blue"),
            ("─────", "Pneumatic", "red"),
            ("· · · ·", "Electric", "green")
        ]

        y_offset = legend_y + 45
        for symbol, label, color in items:
            legend_group.add(self.dwg.text(
                symbol,
                insert=(legend_x + 15, y_offset),
                font_size=12,
                font_family="Arial",
                fill=color
            ))
            legend_group.add(self.dwg.text(
                label,
                insert=(legend_x + 80, y_offset),
                font_size=11,
                font_family="Arial"
            ))
            y_offset += 25

        self.dwg.add(legend_group)

    def generate_svg(self, output_file: Optional[str] = None) -> str:
        """
        Generate SVG P&ID diagram

        Args:
            output_file: Output file path (optional)

        Returns:
            Output file path
        """
        if not output_file:
            output_file = f"{self.project_name.replace(' ', '_')}_PID.svg"

        # Calculate component positions
        self._calculate_positions()

        # Draw border and title block
        self._draw_border()
        self._draw_title_block()

        # Draw all components
        for component in self.components:
            self._draw_component(component)

        # Draw connections
        self._draw_connections()

        # Draw legend
        self._generate_legend()

        # Save SVG
        self.dwg.filename = output_file
        self.dwg.save()

        return output_file

    def generate_dxf(self, output_file: Optional[str] = None) -> str:
        """
        Generate DXF CAD file for AutoCAD/industrial design tools

        Args:
            output_file: Output file path (optional)

        Returns:
            Output file path
        """
        if not output_file:
            output_file = f"{self.project_name.replace(' ', '_')}_PID.dxf"

        # Create DXF document
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()

        # Calculate positions
        self._calculate_positions()

        # Add components as blocks/text
        for component in self.components:
            tag = component["tag"]
            pos = self.positions.get(tag)
            if pos:
                x, y = pos
                # Add text label
                msp.add_text(
                    tag,
                    dxfattribs={
                        'insert': (x / 10, y / 10),  # Scale to reasonable units
                        'height': 2.5,
                        'layer': 'INSTRUMENTS'
                    }
                )

                # Add circle for instrument
                msp.add_circle(
                    center=(x / 10, y / 10),
                    radius=4,
                    dxfattribs={'layer': 'SYMBOLS'}
                )

        # Add connections as lines
        for conn in self.connections:
            from_pos = self.positions.get(conn["from"])
            to_pos = self.positions.get(conn["to"])

            if from_pos and to_pos:
                layer = {
                    "process": "PROCESS",
                    "signal": "SIGNALS",
                    "pneumatic": "PNEUMATIC",
                    "electric": "ELECTRIC"
                }.get(conn["type"], "PROCESS")

                msp.add_line(
                    (from_pos[0] / 10, from_pos[1] / 10),
                    (to_pos[0] / 10, to_pos[1] / 10),
                    dxfattribs={'layer': layer}
                )

        # Save DXF
        doc.saveas(output_file)

        return output_file

    def load_from_bom(self, bom_data: List[Dict]) -> None:
        """
        Load components from BOM (Bill of Materials) data

        Args:
            bom_data: List of BOM items with fields:
                - part_name: Component name
                - quantity: Quantity
                - reference: Reference designator (e.g., "PLC1", "TT-101")
                - description: Description
        """
        for idx, item in enumerate(bom_data):
            part_name = item.get("part_name", "")
            reference = item.get("reference", f"COMP-{idx + 1}")
            quantity = item.get("quantity", 1)
            description = item.get("description", "")

            # Determine component type from part name
            comp_type = self._infer_component_type(part_name, reference)

            self.add_component(
                component_type=comp_type,
                tag=reference,
                description=description,
                quantity=quantity
            )

    def _infer_component_type(self, part_name: str, reference: str) -> str:
        """Infer component type from part name and reference"""
        name_lower = part_name.lower()
        ref_lower = reference.lower()

        # Check reference designator first
        if ref_lower.startswith("tt"):
            return "Temperature Transmitter"
        elif ref_lower.startswith("pt"):
            return "Pressure Transmitter"
        elif ref_lower.startswith("ft"):
            return "Flow Transmitter"
        elif ref_lower.startswith("lt"):
            return "Level Transmitter"
        elif ref_lower.startswith("plc") or "plc" in ref_lower:
            return "PLC"
        elif ref_lower.startswith("hmi") or "hmi" in ref_lower:
            return "HMI"

        # Check part name
        if "plc" in name_lower or "controller" in name_lower:
            return "PLC"
        elif "hmi" in name_lower or "screen" in name_lower or "display" in name_lower:
            return "HMI"
        elif "temperature" in name_lower or "thermocouple" in name_lower:
            return "Temperature Transmitter"
        elif "pressure" in name_lower:
            return "Pressure Transmitter"
        elif "flow" in name_lower:
            return "Flow Transmitter"
        elif "level" in name_lower:
            return "Level Transmitter"
        elif "valve" in name_lower:
            if "control" in name_lower:
                return "Control Valve"
            elif "solenoid" in name_lower:
                return "Solenoid Valve"
            else:
                return "Manual Valve"
        elif "pump" in name_lower:
            return "Pump"
        elif "tank" in name_lower or "vessel" in name_lower:
            return "Tank"
        elif "sensor" in name_lower:
            return "Sensor"
        else:
            return "Generic Instrument"

    def export_component_list(self, output_file: str = "component_list.json") -> str:
        """
        Export component list to JSON

        Args:
            output_file: Output file path

        Returns:
            Output file path
        """
        with open(output_file, 'w') as f:
            json.dump({
                "project": self.project_name,
                "customer": self.customer,
                "components": self.components,
                "connections": self.connections,
                "generated_at": datetime.now().isoformat()
            }, f, indent=2)

        return output_file


# Example usage
if __name__ == "__main__":
    # Create P&ID generator
    pid = PIDGenerator(
        project_name="Industrial Control Panel XYZ",
        customer="ABC Manufacturing"
    )

    # Add components manually
    pid.add_component("PLC", "PLC1", "Siemens S7-1200")
    pid.add_component("HMI", "HMI1", "7-inch Touchscreen")
    pid.add_component("Temperature Transmitter", "TT-101", "Process Temperature")
    pid.add_component("Pressure Transmitter", "PT-101", "Line Pressure")
    pid.add_component("Flow Transmitter", "FT-101", "Flow Rate")
    pid.add_component("Control Valve", "CV-101", "Flow Control")
    pid.add_component("Pump", "P-101", "Centrifugal Pump")

    # Add connections
    pid.add_connection("TT-101", "PLC1", "signal")
    pid.add_connection("PT-101", "PLC1", "signal")
    pid.add_connection("FT-101", "PLC1", "signal")
    pid.add_connection("PLC1", "CV-101", "signal")
    pid.add_connection("PLC1", "HMI1", "electric")
    pid.add_connection("P-101", "CV-101", "process")

    # Generate diagrams
    svg_file = pid.generate_svg()
    dxf_file = pid.generate_dxf()
    json_file = pid.export_component_list()

    print(f"✓ SVG diagram generated: {svg_file}")
    print(f"✓ DXF diagram generated: {dxf_file}")
    print(f"✓ Component list exported: {json_file}")
