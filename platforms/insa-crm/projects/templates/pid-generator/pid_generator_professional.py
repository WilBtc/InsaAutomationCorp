#!/usr/bin/env python3
"""
Professional P&ID Generator - Enhanced Version
Includes modern professional features for client presentations
Version: 2.0.0 - Client Presentation Edition
"""

import svgwrite
import ezdxf
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pid_symbols import PIDSymbols


class PIDGeneratorProfessional:
    """Enhanced P&ID generator with professional client presentation features"""

    def __init__(self, project_name: str, customer: str = "",
                 drawing_number: str = "PID-001", project_number: str = ""):
        self.project_name = project_name
        self.customer = customer
        self.drawing_number = drawing_number
        self.project_number = project_number or datetime.now().strftime("%Y-%m")
        self.components = []
        self.connections = []

        # Enhanced drawing dimensions (A3 landscape: 420mm x 297mm)
        self.width = 1587
        self.height = 1122
        self.margin = 20

        # Grid system
        self.grid_size = 50
        self.show_grid = True

        # Revision information
        self.revision = "A"
        self.drawn_by = "INSA Engineering"
        self.checked_by = ""
        self.approved_by = ""

        # Initialize SVG drawing
        self.dwg = svgwrite.Drawing(
            filename=f"{project_name.replace(' ', '_')}_PID_Professional.svg",
            size=(f"{self.width}px", f"{self.height}px"),
            profile='full'
        )

        self.symbols = PIDSymbols(self.dwg, scale=1.0)

    def add_component(self, component_type: str, tag: str, description: str = "",
                     quantity: int = 1, specifications: Dict = None) -> None:
        """Add a component to the P&ID"""
        self.components.append({
            "type": component_type,
            "tag": tag,
            "description": description,
            "quantity": quantity,
            "specifications": specifications or {}
        })

    def add_connection(self, from_tag: str, to_tag: str,
                      connection_type: str = "process") -> None:
        """Add a connection between components"""
        self.connections.append({
            "from": from_tag,
            "to": to_tag,
            "type": connection_type
        })

    def load_from_bom(self, bom_data: List[Dict]) -> None:
        """Load components from BOM data"""
        for idx, item in enumerate(bom_data):
            part_name = item.get("part_name", "")
            reference = item.get("reference", f"COMP-{idx + 1}")
            quantity = item.get("quantity", 1)
            description = item.get("description", "")

            comp_type = self._infer_component_type(part_name, reference)

            self.add_component(
                component_type=comp_type,
                tag=reference,
                description=description,
                quantity=quantity
            )

    def _infer_component_type(self, part_name: str, reference: str) -> str:
        """Infer component type from part name and reference"""
        part_lower = part_name.lower()
        ref_upper = reference.upper()

        # Check reference designator first
        if ref_upper.startswith("PLC"):
            return "PLC"
        elif ref_upper.startswith("HMI"):
            return "HMI"
        elif ref_upper.startswith("TT-"):
            return "Temperature Transmitter"
        elif ref_upper.startswith("PT-"):
            return "Pressure Transmitter"
        elif ref_upper.startswith("FT-"):
            return "Flow Transmitter"
        elif ref_upper.startswith("LT-"):
            return "Level Transmitter"
        elif ref_upper.startswith("CV-"):
            return "Control Valve"
        elif ref_upper.startswith("SV-"):
            return "Solenoid Valve"
        elif ref_upper.startswith("P-"):
            return "Pump"
        elif ref_upper.startswith("V-"):
            return "Tank"

        # Check part name keywords
        if "plc" in part_lower or "controller" in part_lower:
            return "PLC"
        elif "hmi" in part_lower or "screen" in part_lower or "display" in part_lower:
            return "HMI"
        elif "temperature" in part_lower or "thermocouple" in part_lower:
            return "Temperature Transmitter"
        elif "pressure" in part_lower:
            return "Pressure Transmitter"
        elif "flow" in part_lower:
            return "Flow Transmitter"
        elif "level" in part_lower:
            return "Level Transmitter"
        elif "valve" in part_lower:
            if "solenoid" in part_lower:
                return "Solenoid Valve"
            elif "control" in part_lower:
                return "Control Valve"
            else:
                return "Manual Valve"
        elif "pump" in part_lower:
            return "Pump"
        elif "tank" in part_lower or "vessel" in part_lower:
            return "Tank"

        return "Generic Component"

    def _draw_grid(self) -> None:
        """Draw grid system with alphanumeric labels"""
        if not self.show_grid:
            return

        grid_group = self.dwg.g(id="grid_system")

        # Vertical grid lines (columns 1-20)
        for i in range(1, 21):
            x = self.margin + i * self.grid_size
            if x < self.width - self.margin:
                grid_group.add(self.dwg.line(
                    start=(x, self.margin),
                    end=(x, self.height - self.margin),
                    stroke="#e0e0e0",
                    stroke_width=0.5
                ))
                # Column number at top
                grid_group.add(self.dwg.text(
                    str(i),
                    insert=(x, self.margin + 15),
                    text_anchor="middle",
                    font_size=10,
                    font_family="Arial",
                    fill="#999"
                ))

        # Horizontal grid lines (rows A-Z)
        letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for i, letter in enumerate(letters[:20]):
            y = self.margin + (i + 1) * self.grid_size
            if y < self.height - self.margin:
                grid_group.add(self.dwg.line(
                    start=(self.margin, y),
                    end=(self.width - self.margin, y),
                    stroke="#e0e0e0",
                    stroke_width=0.5
                ))
                # Row letter on left
                grid_group.add(self.dwg.text(
                    letter,
                    insert=(self.margin + 10, y + 5),
                    text_anchor="start",
                    font_size=10,
                    font_family="Arial",
                    fill="#999"
                ))

        self.dwg.add(grid_group)

    def _draw_professional_title_block(self) -> None:
        """Draw enhanced professional title block"""
        # Title block dimensions
        tb_width = 450
        tb_height = 180
        tb_x = self.width - self.margin - tb_width
        tb_y = self.height - self.margin - tb_height

        title_group = self.dwg.g(id="professional_title_block")

        # Main border
        title_group.add(self.dwg.rect(
            insert=(tb_x, tb_y),
            size=(tb_width, tb_height),
            fill="white",
            stroke="black",
            stroke_width=2
        ))

        # Company header section (top 40px)
        title_group.add(self.dwg.rect(
            insert=(tb_x, tb_y),
            size=(tb_width, 40),
            fill="#2c3e50",
            stroke="none"
        ))

        title_group.add(self.dwg.text(
            "INSA AUTOMATION CORP",
            insert=(tb_x + 10, tb_y + 20),
            font_family="Arial",
            font_size=16,
            font_weight="bold",
            fill="white"
        ))

        title_group.add(self.dwg.text(
            "Industrial Automation Solutions",
            insert=(tb_x + 10, tb_y + 35),
            font_family="Arial",
            font_size=10,
            fill="white"
        ))

        # Project number (top right)
        title_group.add(self.dwg.text(
            f"PROJECT NO: {self.project_number}",
            insert=(tb_x + tb_width - 10, tb_y + 25),
            text_anchor="end",
            font_family="Arial",
            font_size=10,
            font_weight="bold",
            fill="white"
        ))

        # Horizontal dividers
        y_offset = tb_y + 40
        title_group.add(self.dwg.line(
            start=(tb_x, y_offset),
            end=(tb_x + tb_width, y_offset),
            stroke="black",
            stroke_width=1
        ))

        # Project name section
        y_offset += 10
        title_group.add(self.dwg.text(
            "PROJECT:",
            insert=(tb_x + 10, y_offset),
            font_family="Arial",
            font_size=10,
            font_weight="bold"
        ))

        title_group.add(self.dwg.text(
            self.project_name,
            insert=(tb_x + 80, y_offset),
            font_family="Arial",
            font_size=12,
            font_weight="bold",
            fill="#2c3e50"
        ))

        y_offset += 20
        title_group.add(self.dwg.text(
            "CUSTOMER:",
            insert=(tb_x + 10, y_offset),
            font_family="Arial",
            font_size=10,
            font_weight="bold"
        ))

        title_group.add(self.dwg.text(
            self.customer,
            insert=(tb_x + 80, y_offset),
            font_family="Arial",
            font_size=11
        ))

        # Divider line
        y_offset += 10
        title_group.add(self.dwg.line(
            start=(tb_x, y_offset),
            end=(tb_x + tb_width, y_offset),
            stroke="black",
            stroke_width=1
        ))

        # Drawing information grid
        y_offset += 15

        # Left column
        title_group.add(self.dwg.text(
            "DRAWING TYPE:",
            insert=(tb_x + 10, y_offset),
            font_family="Arial",
            font_size=9,
            font_weight="bold"
        ))

        title_group.add(self.dwg.text(
            "P&ID",
            insert=(tb_x + 120, y_offset),
            font_family="Arial",
            font_size=9
        ))

        # Right column
        title_group.add(self.dwg.text(
            "DRAWING NO:",
            insert=(tb_x + 240, y_offset),
            font_family="Arial",
            font_size=9,
            font_weight="bold"
        ))

        title_group.add(self.dwg.text(
            self.drawing_number,
            insert=(tb_x + 330, y_offset),
            font_family="Arial",
            font_size=9
        ))

        y_offset += 18

        # Sheet and revision
        title_group.add(self.dwg.text(
            "SHEET:",
            insert=(tb_x + 10, y_offset),
            font_family="Arial",
            font_size=9,
            font_weight="bold"
        ))

        title_group.add(self.dwg.text(
            "1 of 1",
            insert=(tb_x + 120, y_offset),
            font_family="Arial",
            font_size=9
        ))

        title_group.add(self.dwg.text(
            "REVISION:",
            insert=(tb_x + 240, y_offset),
            font_family="Arial",
            font_size=9,
            font_weight="bold"
        ))

        title_group.add(self.dwg.text(
            self.revision,
            insert=(tb_x + 330, y_offset),
            font_family="Arial",
            font_size=9,
            font_weight="bold",
            fill="#e74c3c"
        ))

        # Divider line
        y_offset += 10
        title_group.add(self.dwg.line(
            start=(tb_x, y_offset),
            end=(tb_x + tb_width, y_offset),
            stroke="black",
            stroke_width=1
        ))

        # Signatures section
        y_offset += 15

        title_group.add(self.dwg.text(
            "DRAWN BY:",
            insert=(tb_x + 10, y_offset),
            font_family="Arial",
            font_size=9,
            font_weight="bold"
        ))

        title_group.add(self.dwg.text(
            self.drawn_by,
            insert=(tb_x + 80, y_offset),
            font_family="Arial",
            font_size=9
        ))

        title_group.add(self.dwg.text(
            "DATE:",
            insert=(tb_x + 240, y_offset),
            font_family="Arial",
            font_size=9,
            font_weight="bold"
        ))

        title_group.add(self.dwg.text(
            datetime.now().strftime("%Y-%m-%d"),
            insert=(tb_x + 330, y_offset),
            font_family="Arial",
            font_size=9
        ))

        y_offset += 18

        title_group.add(self.dwg.text(
            "CHECKED BY:",
            insert=(tb_x + 10, y_offset),
            font_family="Arial",
            font_size=9,
            font_weight="bold"
        ))

        title_group.add(self.dwg.text(
            self.checked_by or "_" * 15,
            insert=(tb_x + 80, y_offset),
            font_family="Arial",
            font_size=9
        ))

        title_group.add(self.dwg.text(
            "DATE:",
            insert=(tb_x + 240, y_offset),
            font_family="Arial",
            font_size=9,
            font_weight="bold"
        ))

        title_group.add(self.dwg.text(
            "_" * 12,
            insert=(tb_x + 330, y_offset),
            font_family="Arial",
            font_size=9
        ))

        y_offset += 18

        title_group.add(self.dwg.text(
            "APPROVED BY:",
            insert=(tb_x + 10, y_offset),
            font_family="Arial",
            font_size=9,
            font_weight="bold"
        ))

        title_group.add(self.dwg.text(
            self.approved_by or "_" * 15,
            insert=(tb_x + 80, y_offset),
            font_family="Arial",
            font_size=9
        ))

        title_group.add(self.dwg.text(
            "DATE:",
            insert=(tb_x + 240, y_offset),
            font_family="Arial",
            font_size=9,
            font_weight="bold"
        ))

        title_group.add(self.dwg.text(
            "_" * 12,
            insert=(tb_x + 330, y_offset),
            font_family="Arial",
            font_size=9
        ))

        # Bottom section
        y_offset += 15
        title_group.add(self.dwg.line(
            start=(tb_x, y_offset),
            end=(tb_x + tb_width, y_offset),
            stroke="black",
            stroke_width=1
        ))

        y_offset += 15

        title_group.add(self.dwg.text(
            "SCALE: NTS",
            insert=(tb_x + 10, y_offset),
            font_family="Arial",
            font_size=9
        ))

        title_group.add(self.dwg.text(
            "SIZE: A3",
            insert=(tb_x + 120, y_offset),
            font_family="Arial",
            font_size=9
        ))

        title_group.add(self.dwg.text(
            "STANDARD: ISA-5.1-2024",
            insert=(tb_x + 240, y_offset),
            font_family="Arial",
            font_size=9,
            fill="#27ae60",
            font_weight="bold"
        ))

        self.dwg.add(title_group)

    def _draw_comprehensive_legend(self) -> None:
        """Draw comprehensive legend with all symbols and line types"""
        legend_width = 350
        legend_height = 220
        legend_x = 60
        legend_y = self.height - self.margin - legend_height - 200

        legend_group = self.dwg.g(id="comprehensive_legend")

        # Legend border
        legend_group.add(self.dwg.rect(
            insert=(legend_x, legend_y),
            size=(legend_width, legend_height),
            fill="white",
            stroke="black",
            stroke_width=2
        ))

        # Legend header
        legend_group.add(self.dwg.rect(
            insert=(legend_x, legend_y),
            size=(legend_width, 30),
            fill="#3498db",
            stroke="none"
        ))

        legend_group.add(self.dwg.text(
            "LEGEND - ISA-5.1-2024 SYMBOLS",
            insert=(legend_x + legend_width/2, legend_y + 20),
            text_anchor="middle",
            font_family="Arial",
            font_size=12,
            font_weight="bold",
            fill="white"
        ))

        y_pos = legend_y + 50

        # Line types section
        legend_group.add(self.dwg.text(
            "LINE TYPES:",
            insert=(legend_x + 10, y_pos),
            font_family="Arial",
            font_size=10,
            font_weight="bold",
            fill="#2c3e50"
        ))

        y_pos += 18

        # Process line
        legend_group.add(self.dwg.line(
            start=(legend_x + 15, y_pos),
            end=(legend_x + 75, y_pos),
            stroke="black",
            stroke_width=2
        ))
        legend_group.add(self.dwg.text(
            "Process Line (Piping)",
            insert=(legend_x + 85, y_pos + 5),
            font_family="Arial",
            font_size=9
        ))

        y_pos += 18

        # Signal line
        legend_group.add(self.dwg.line(
            start=(legend_x + 15, y_pos),
            end=(legend_x + 75, y_pos),
            stroke="blue",
            stroke_width=1.5,
            stroke_dasharray="5,5"
        ))
        legend_group.add(self.dwg.text(
            "Signal Line (4-20mA)",
            insert=(legend_x + 85, y_pos + 5),
            font_family="Arial",
            font_size=9
        ))

        y_pos += 18

        # Pneumatic line
        legend_group.add(self.dwg.line(
            start=(legend_x + 15, y_pos),
            end=(legend_x + 75, y_pos),
            stroke="red",
            stroke_width=1.5
        ))
        legend_group.add(self.dwg.text(
            "Pneumatic Line",
            insert=(legend_x + 85, y_pos + 5),
            font_family="Arial",
            font_size=9
        ))

        y_pos += 18

        # Electric line
        legend_group.add(self.dwg.line(
            start=(legend_x + 15, y_pos),
            end=(legend_x + 75, y_pos),
            stroke="green",
            stroke_width=1.5,
            stroke_dasharray="2,2"
        ))
        legend_group.add(self.dwg.text(
            "Electric Line",
            insert=(legend_x + 85, y_pos + 5),
            font_family="Arial",
            font_size=9
        ))

        # Instrument symbols section
        y_pos = legend_y + 50
        x_offset = legend_x + 200

        legend_group.add(self.dwg.text(
            "INSTRUMENT SYMBOLS:",
            insert=(x_offset, y_pos),
            font_family="Arial",
            font_size=10,
            font_weight="bold",
            fill="#2c3e50"
        ))

        y_pos += 18

        # Transmitter circle
        legend_group.add(self.dwg.circle(
            center=(x_offset + 15, y_pos),
            r=10,
            fill="lightblue",
            stroke="black",
            stroke_width=1
        ))
        legend_group.add(self.dwg.text(
            "XX",
            insert=(x_offset + 15, y_pos + 4),
            text_anchor="middle",
            font_family="Arial",
            font_size=8,
            font_weight="bold"
        ))
        legend_group.add(self.dwg.text(
            "Transmitter",
            insert=(x_offset + 35, y_pos + 5),
            font_family="Arial",
            font_size=9
        ))

        y_pos += 22

        # Control valve
        points = [
            (x_offset + 15, y_pos - 8),
            (x_offset + 23, y_pos),
            (x_offset + 15, y_pos + 8),
            (x_offset + 7, y_pos)
        ]
        legend_group.add(self.dwg.polygon(
            points=points,
            fill="white",
            stroke="black",
            stroke_width=1
        ))
        # Actuator triangle
        act_points = [
            (x_offset + 10, y_pos - 8),
            (x_offset + 20, y_pos - 8),
            (x_offset + 15, y_pos - 14)
        ]
        legend_group.add(self.dwg.polygon(
            points=act_points,
            fill="lightgray",
            stroke="black",
            stroke_width=1
        ))
        legend_group.add(self.dwg.text(
            "Control Valve",
            insert=(x_offset + 35, y_pos + 5),
            font_family="Arial",
            font_size=9
        ))

        y_pos += 22

        # PLC
        legend_group.add(self.dwg.rect(
            insert=(x_offset + 5, y_pos - 8),
            size=(20, 12),
            fill="lightblue",
            stroke="black",
            stroke_width=1
        ))
        legend_group.add(self.dwg.text(
            "PLC",
            insert=(x_offset + 15, y_pos - 1),
            text_anchor="middle",
            font_family="Arial",
            font_size=7,
            font_weight="bold"
        ))
        legend_group.add(self.dwg.text(
            "PLC/Controller",
            insert=(x_offset + 35, y_pos + 5),
            font_family="Arial",
            font_size=9
        ))

        y_pos += 22

        # Pump
        legend_group.add(self.dwg.circle(
            center=(x_offset + 15, y_pos),
            r=8,
            fill="white",
            stroke="black",
            stroke_width=1
        ))
        legend_group.add(self.dwg.circle(
            center=(x_offset + 15, y_pos),
            r=3,
            fill="black"
        ))
        legend_group.add(self.dwg.text(
            "Pump",
            insert=(x_offset + 35, y_pos + 5),
            font_family="Arial",
            font_size=9
        ))

        # Notes section at bottom
        y_pos = legend_y + legend_height - 30

        legend_group.add(self.dwg.text(
            "NOTE: All symbols comply with ANSI/ISA-5.1-2024 standard",
            insert=(legend_x + 10, y_pos),
            font_family="Arial",
            font_size=8,
            fill="#7f8c8d",
            font_style="italic"
        ))

        self.dwg.add(legend_group)

    def _draw_revision_block(self) -> None:
        """Draw revision history block"""
        rev_width = 300
        rev_height = 80
        rev_x = self.width - self.margin - rev_width
        rev_y = self.height - self.margin - 400

        rev_group = self.dwg.g(id="revision_block")

        # Border
        rev_group.add(self.dwg.rect(
            insert=(rev_x, rev_y),
            size=(rev_width, rev_height),
            fill="white",
            stroke="black",
            stroke_width=1.5
        ))

        # Header
        rev_group.add(self.dwg.rect(
            insert=(rev_x, rev_y),
            size=(rev_width, 25),
            fill="#34495e",
            stroke="none"
        ))

        rev_group.add(self.dwg.text(
            "REVISION HISTORY",
            insert=(rev_x + rev_width/2, rev_y + 17),
            text_anchor="middle",
            font_family="Arial",
            font_size=11,
            font_weight="bold",
            fill="white"
        ))

        # Column headers
        y_pos = rev_y + 40
        col_widths = [40, 150, 70, 40]
        x_positions = [rev_x]
        for w in col_widths[:-1]:
            x_positions.append(x_positions[-1] + w)

        headers = ["REV", "DESCRIPTION", "DATE", "BY"]
        for i, header in enumerate(headers):
            rev_group.add(self.dwg.text(
                header,
                insert=(x_positions[i] + 5, y_pos),
                font_family="Arial",
                font_size=9,
                font_weight="bold"
            ))

        # Vertical dividers
        for x_pos in x_positions[1:]:
            rev_group.add(self.dwg.line(
                start=(x_pos, rev_y + 25),
                end=(x_pos, rev_y + rev_height),
                stroke="black",
                stroke_width=0.5
            ))

        # Horizontal divider
        y_pos += 5
        rev_group.add(self.dwg.line(
            start=(rev_x, y_pos),
            end=(rev_x + rev_width, y_pos),
            stroke="black",
            stroke_width=0.5
        ))

        # First revision entry
        y_pos += 15
        rev_group.add(self.dwg.text(
            self.revision,
            insert=(x_positions[0] + 5, y_pos),
            font_family="Arial",
            font_size=9
        ))

        rev_group.add(self.dwg.text(
            "Initial Release",
            insert=(x_positions[1] + 5, y_pos),
            font_family="Arial",
            font_size=9
        ))

        rev_group.add(self.dwg.text(
            datetime.now().strftime("%Y-%m-%d"),
            insert=(x_positions[2] + 5, y_pos),
            font_family="Arial",
            font_size=9
        ))

        rev_group.add(self.dwg.text(
            "ENG",
            insert=(x_positions[3] + 5, y_pos),
            font_family="Arial",
            font_size=9
        ))

        self.dwg.add(rev_group)

    def _auto_layout_components(self) -> Dict[str, Tuple[float, float]]:
        """Calculate positions for all components with better spacing"""
        positions = {}

        # Group components by type
        plcs = [c for c in self.components if c["type"] == "PLC"]
        hmis = [c for c in self.components if c["type"] == "HMI"]
        transmitters = [c for c in self.components if "Transmitter" in c["type"]]
        valves = [c for c in self.components if "Valve" in c["type"]]
        pumps = [c for c in self.components if c["type"] == "Pump"]
        tanks = [c for c in self.components if c["type"] == "Tank"]

        # Layout parameters
        start_x = 350
        start_y = 150
        spacing_x = 250
        spacing_y = 150

        # Place PLCs at top center
        for i, plc in enumerate(plcs):
            positions[plc["tag"]] = (start_x + i * spacing_x, start_y)

        # Place HMIs below PLCs
        for i, hmi in enumerate(hmis):
            positions[hmi["tag"]] = (start_x + i * spacing_x, start_y + spacing_y)

        # Place transmitters in middle rows
        cols = 3
        for i, trans in enumerate(transmitters):
            row = i // cols
            col = i % cols
            positions[trans["tag"]] = (start_x + col * spacing_x, start_y + (row + 3) * spacing_y)

        # Place valves in bottom rows
        for i, valve in enumerate(valves):
            row = i // cols
            col = i % cols
            positions[valve["tag"]] = (start_x + col * spacing_x, start_y + (row + 6) * spacing_y)

        # Place pumps at bottom
        for i, pump in enumerate(pumps):
            positions[pump["tag"]] = (start_x + i * spacing_x, start_y + 9 * spacing_y)

        # Place tanks
        for i, tank in enumerate(tanks):
            positions[tank["tag"]] = (start_x + i * spacing_x + 400, start_y + 5 * spacing_y)

        return positions

    def generate_svg(self, output_file: Optional[str] = None) -> str:
        """Generate professional SVG P&ID diagram"""
        if output_file is None:
            output_file = f"{self.project_name.replace(' ', '_')}_PID_Professional.svg"

        # Draw grid first (background)
        self._draw_grid()

        # Draw outer border
        self.dwg.add(self.dwg.rect(
            insert=(self.margin, self.margin),
            size=(self.width - 2 * self.margin, self.height - 2 * self.margin),
            fill="none",
            stroke="black",
            stroke_width=3
        ))

        # Draw inner border
        self.dwg.add(self.dwg.rect(
            insert=(self.margin + 20, self.margin + 20),
            size=(self.width - 2 * self.margin - 40, self.height - 2 * self.margin - 40),
            fill="none",
            stroke="black",
            stroke_width=1
        ))

        # Calculate component positions
        positions = self._auto_layout_components()

        # Draw components
        for component in self.components:
            tag = component["tag"]
            comp_type = component["type"]
            pos = positions.get(tag, (400, 400))

            if comp_type == "PLC":
                symbol = self.symbols.controller_plc(pos, tag)
            elif comp_type == "HMI":
                symbol = self.symbols.hmi_display(pos, tag)
            elif comp_type == "Temperature Transmitter":
                symbol = self.symbols.temperature_transmitter(pos, tag)
            elif comp_type == "Pressure Transmitter":
                symbol = self.symbols.pressure_transmitter(pos, tag)
            elif comp_type == "Flow Transmitter":
                symbol = self.symbols.flow_transmitter(pos, tag)
            elif comp_type == "Level Transmitter":
                symbol = self.symbols.level_transmitter(pos, tag)
            elif comp_type == "Control Valve":
                symbol = self.symbols.valve_control(pos, tag)
            elif comp_type == "Solenoid Valve":
                symbol = self.symbols.valve_solenoid(pos, tag)
            elif comp_type == "Manual Valve":
                symbol = self.symbols.valve_manual(pos, tag)
            elif comp_type == "Pump":
                symbol = self.symbols.pump_centrifugal(pos, tag)
            elif comp_type == "Tank":
                symbol = self.symbols.tank_vertical(pos, tag)
            else:
                symbol = self.symbols.sensor_generic(pos, tag, comp_type)

            self.dwg.add(symbol)

        # Draw connections
        for conn in self.connections:
            from_tag = conn["from"]
            to_tag = conn["to"]
            conn_type = conn["type"]

            from_pos = positions.get(from_tag)
            to_pos = positions.get(to_tag)

            if from_pos and to_pos:
                line = self.symbols.process_line(from_pos, to_pos, conn_type)
                self.dwg.add(line)

        # Draw professional elements
        self._draw_professional_title_block()
        self._draw_comprehensive_legend()
        self._draw_revision_block()

        # Save
        self.dwg.saveas(output_file)
        return output_file

    def export_component_list(self, output_file: str = "component_list_professional.json") -> str:
        """Export component list to JSON"""
        data = {
            "project": self.project_name,
            "customer": self.customer,
            "drawing_number": self.drawing_number,
            "project_number": self.project_number,
            "revision": self.revision,
            "components": self.components,
            "connections": self.connections,
            "generated_at": datetime.now().isoformat(),
            "standard": "ANSI/ISA-5.1-2024"
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        return output_file
