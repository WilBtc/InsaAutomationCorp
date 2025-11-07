#!/usr/bin/env python3
"""
P&ID Symbol Library for Industrial Automation
Provides standard ISA-5.1 compliant symbols for P&ID diagram generation
Version: 1.0.0
"""

import svgwrite
from typing import Tuple, Optional

class PIDSymbols:
    """Library of standard P&ID symbols for industrial automation"""

    def __init__(self, dwg: svgwrite.Drawing, scale: float = 1.0):
        """
        Initialize P&ID symbol library

        Args:
            dwg: SVG drawing object
            scale: Scale factor for symbols (default: 1.0)
        """
        self.dwg = dwg
        self.scale = scale
        self.symbol_size = 40 * scale  # Base symbol size

    def _create_group(self, name: str) -> svgwrite.container.Group:
        """Create a named SVG group for a symbol"""
        return self.dwg.g(id=name, class_=name)

    # ==================== INSTRUMENTS ====================

    def instrument_circle(self, pos: Tuple[float, float], tag: str,
                         desc: str = "", fill: str = "white") -> svgwrite.container.Group:
        """
        Create standard instrument circle (ISA-5.1)

        Args:
            pos: (x, y) position
            tag: Instrument tag (e.g., "TT-101")
            desc: Description text
            fill: Circle fill color

        Returns:
            SVG group containing the instrument symbol
        """
        group = self._create_group(f"instrument_{tag}")
        x, y = pos
        radius = self.symbol_size / 2

        # Circle
        group.add(self.dwg.circle(
            center=(x, y),
            r=radius,
            fill=fill,
            stroke="black",
            stroke_width=2 * self.scale
        ))

        # Tag text
        group.add(self.dwg.text(
            tag,
            insert=(x, y + 5),
            text_anchor="middle",
            font_size=12 * self.scale,
            font_family="Arial",
            font_weight="bold"
        ))

        # Description text (below circle)
        if desc:
            group.add(self.dwg.text(
                desc,
                insert=(x, y + radius + 15),
                text_anchor="middle",
                font_size=10 * self.scale,
                font_family="Arial"
            ))

        return group

    def temperature_transmitter(self, pos: Tuple[float, float], tag: str) -> svgwrite.container.Group:
        """Temperature transmitter (TT)"""
        return self.instrument_circle(pos, tag, "Temperature", fill="lightblue")

    def pressure_transmitter(self, pos: Tuple[float, float], tag: str) -> svgwrite.container.Group:
        """Pressure transmitter (PT)"""
        return self.instrument_circle(pos, tag, "Pressure", fill="lightgreen")

    def flow_transmitter(self, pos: Tuple[float, float], tag: str) -> svgwrite.container.Group:
        """Flow transmitter (FT)"""
        return self.instrument_circle(pos, tag, "Flow", fill="lightyellow")

    def level_transmitter(self, pos: Tuple[float, float], tag: str) -> svgwrite.container.Group:
        """Level transmitter (LT)"""
        return self.instrument_circle(pos, tag, "Level", fill="lightcyan")

    # ==================== VALVES ====================

    def valve_manual(self, pos: Tuple[float, float], tag: str = "") -> svgwrite.container.Group:
        """Manual valve symbol"""
        group = self._create_group(f"valve_manual_{tag}")
        x, y = pos
        size = self.symbol_size / 2

        # Diamond shape for valve body
        points = [
            (x, y - size),      # top
            (x + size, y),      # right
            (x, y + size),      # bottom
            (x - size, y)       # left
        ]
        group.add(self.dwg.polygon(
            points=points,
            fill="white",
            stroke="black",
            stroke_width=2 * self.scale
        ))

        # Stem (actuator indicator)
        group.add(self.dwg.line(
            start=(x, y - size),
            end=(x, y - size - 15 * self.scale),
            stroke="black",
            stroke_width=2 * self.scale
        ))

        # Tag
        if tag:
            group.add(self.dwg.text(
                tag,
                insert=(x, y + size + 15),
                text_anchor="middle",
                font_size=10 * self.scale,
                font_family="Arial"
            ))

        return group

    def valve_control(self, pos: Tuple[float, float], tag: str = "") -> svgwrite.container.Group:
        """Control valve with actuator"""
        group = self._create_group(f"valve_control_{tag}")
        x, y = pos
        size = self.symbol_size / 2

        # Diamond shape for valve body
        points = [
            (x, y - size),
            (x + size, y),
            (x, y + size),
            (x - size, y)
        ]
        group.add(self.dwg.polygon(
            points=points,
            fill="white",
            stroke="black",
            stroke_width=2 * self.scale
        ))

        # Pneumatic actuator (triangle)
        actuator_points = [
            (x - size * 0.6, y - size),
            (x + size * 0.6, y - size),
            (x, y - size - size * 0.8)
        ]
        group.add(self.dwg.polygon(
            points=actuator_points,
            fill="lightgray",
            stroke="black",
            stroke_width=2 * self.scale
        ))

        # Tag
        if tag:
            group.add(self.dwg.text(
                tag,
                insert=(x, y + size + 15),
                text_anchor="middle",
                font_size=10 * self.scale,
                font_family="Arial",
                font_weight="bold"
            ))

        return group

    def valve_solenoid(self, pos: Tuple[float, float], tag: str = "") -> svgwrite.container.Group:
        """Solenoid valve"""
        group = self._create_group(f"valve_solenoid_{tag}")
        x, y = pos
        size = self.symbol_size / 2

        # Diamond shape
        points = [
            (x, y - size),
            (x + size, y),
            (x, y + size),
            (x - size, y)
        ]
        group.add(self.dwg.polygon(
            points=points,
            fill="white",
            stroke="black",
            stroke_width=2 * self.scale
        ))

        # Solenoid coil (rectangle)
        group.add(self.dwg.rect(
            insert=(x - size * 0.4, y - size - size * 0.8),
            size=(size * 0.8, size * 0.6),
            fill="yellow",
            stroke="black",
            stroke_width=1.5 * self.scale
        ))

        # Tag
        if tag:
            group.add(self.dwg.text(
                tag,
                insert=(x, y + size + 15),
                text_anchor="middle",
                font_size=10 * self.scale,
                font_family="Arial"
            ))

        return group

    # ==================== PUMPS ====================

    def pump_centrifugal(self, pos: Tuple[float, float], tag: str = "") -> svgwrite.container.Group:
        """Centrifugal pump symbol"""
        group = self._create_group(f"pump_{tag}")
        x, y = pos
        radius = self.symbol_size / 2

        # Outer circle
        group.add(self.dwg.circle(
            center=(x, y),
            r=radius,
            fill="white",
            stroke="black",
            stroke_width=2 * self.scale
        ))

        # Inner impeller (smaller circle)
        group.add(self.dwg.circle(
            center=(x, y),
            r=radius * 0.3,
            fill="black"
        ))

        # Motor connection (small square)
        motor_size = radius * 0.5
        group.add(self.dwg.rect(
            insert=(x + radius, y - motor_size / 2),
            size=(motor_size, motor_size),
            fill="lightgray",
            stroke="black",
            stroke_width=1.5 * self.scale
        ))

        # Tag
        if tag:
            group.add(self.dwg.text(
                tag,
                insert=(x, y + radius + 15),
                text_anchor="middle",
                font_size=10 * self.scale,
                font_family="Arial",
                font_weight="bold"
            ))

        return group

    # ==================== TANKS/VESSELS ====================

    def tank_vertical(self, pos: Tuple[float, float], tag: str = "",
                     width: float = None, height: float = None) -> svgwrite.container.Group:
        """Vertical tank/vessel"""
        group = self._create_group(f"tank_{tag}")
        x, y = pos
        w = width or self.symbol_size * 1.2
        h = height or self.symbol_size * 2

        # Tank body (rectangle)
        group.add(self.dwg.rect(
            insert=(x - w/2, y - h/2),
            size=(w, h),
            fill="white",
            stroke="black",
            stroke_width=2 * self.scale
        ))

        # Bottom (ellipse for 3D effect)
        group.add(self.dwg.ellipse(
            center=(x, y + h/2),
            r=(w/2, h * 0.1),
            fill="lightgray",
            stroke="black",
            stroke_width=2 * self.scale
        ))

        # Tag
        if tag:
            group.add(self.dwg.text(
                tag,
                insert=(x, y + h/2 + 25),
                text_anchor="middle",
                font_size=12 * self.scale,
                font_family="Arial",
                font_weight="bold"
            ))

        return group

    # ==================== CONTROLLERS/PLCs ====================

    def controller_plc(self, pos: Tuple[float, float], tag: str = "") -> svgwrite.container.Group:
        """PLC (Programmable Logic Controller) symbol"""
        group = self._create_group(f"plc_{tag}")
        x, y = pos
        width = self.symbol_size * 1.5
        height = self.symbol_size

        # Main box
        group.add(self.dwg.rect(
            insert=(x - width/2, y - height/2),
            size=(width, height),
            fill="lightblue",
            stroke="black",
            stroke_width=2 * self.scale
        ))

        # PLC label
        group.add(self.dwg.text(
            "PLC",
            insert=(x, y + 5),
            text_anchor="middle",
            font_size=14 * self.scale,
            font_family="Arial",
            font_weight="bold"
        ))

        # Tag
        if tag:
            group.add(self.dwg.text(
                tag,
                insert=(x, y + height/2 + 15),
                text_anchor="middle",
                font_size=10 * self.scale,
                font_family="Arial"
            ))

        # I/O indicators (small rectangles)
        io_width = 5 * self.scale
        io_height = 3 * self.scale
        for i in range(4):
            y_offset = y - height/2 + 10 + i * 8
            group.add(self.dwg.rect(
                insert=(x - width/2 - io_width, y_offset),
                size=(io_width, io_height),
                fill="green"
            ))
            group.add(self.dwg.rect(
                insert=(x + width/2, y_offset),
                size=(io_width, io_height),
                fill="orange"
            ))

        return group

    def controller_pid(self, pos: Tuple[float, float], tag: str = "") -> svgwrite.container.Group:
        """PID Controller symbol"""
        group = self._create_group(f"pid_controller_{tag}")
        x, y = pos
        size = self.symbol_size

        # Hexagon
        points = []
        for i in range(6):
            angle = i * 60 - 30  # Start from 30 degrees
            import math
            px = x + size/2 * math.cos(math.radians(angle))
            py = y + size/2 * math.sin(math.radians(angle))
            points.append((px, py))

        group.add(self.dwg.polygon(
            points=points,
            fill="lightyellow",
            stroke="black",
            stroke_width=2 * self.scale
        ))

        # PID label
        group.add(self.dwg.text(
            "PID",
            insert=(x, y + 5),
            text_anchor="middle",
            font_size=12 * self.scale,
            font_family="Arial",
            font_weight="bold"
        ))

        # Tag
        if tag:
            group.add(self.dwg.text(
                tag,
                insert=(x, y + size/2 + 15),
                text_anchor="middle",
                font_size=10 * self.scale,
                font_family="Arial"
            ))

        return group

    # ==================== PROCESS LINES ====================

    def process_line(self, start: Tuple[float, float], end: Tuple[float, float],
                    line_type: str = "process") -> svgwrite.shapes.Line:
        """
        Create a process line

        Args:
            start: (x, y) start point
            end: (x, y) end point
            line_type: "process", "signal", "pneumatic", "electric"
        """
        styles = {
            "process": {"stroke": "black", "stroke_width": 2 * self.scale},
            "signal": {"stroke": "blue", "stroke_width": 1.5 * self.scale, "stroke_dasharray": "5,5"},
            "pneumatic": {"stroke": "red", "stroke_width": 1.5 * self.scale},
            "electric": {"stroke": "green", "stroke_width": 1.5 * self.scale, "stroke_dasharray": "2,2"}
        }

        style = styles.get(line_type, styles["process"])
        return self.dwg.line(start=start, end=end, **style)

    # ==================== SENSORS ====================

    def sensor_generic(self, pos: Tuple[float, float], tag: str = "",
                      sensor_type: str = "Generic") -> svgwrite.container.Group:
        """Generic sensor symbol"""
        group = self._create_group(f"sensor_{tag}")
        x, y = pos
        size = self.symbol_size * 0.4

        # Triangle pointing down
        points = [
            (x, y + size),       # bottom point
            (x - size, y - size),  # top left
            (x + size, y - size)   # top right
        ]
        group.add(self.dwg.polygon(
            points=points,
            fill="lightgreen",
            stroke="black",
            stroke_width=1.5 * self.scale
        ))

        # Sensor type label
        group.add(self.dwg.text(
            sensor_type[:1],  # First letter
            insert=(x, y),
            text_anchor="middle",
            font_size=10 * self.scale,
            font_family="Arial",
            font_weight="bold"
        ))

        # Tag
        if tag:
            group.add(self.dwg.text(
                tag,
                insert=(x, y + size + 15),
                text_anchor="middle",
                font_size=9 * self.scale,
                font_family="Arial"
            ))

        return group

    # ==================== HMI/DISPLAY ====================

    def hmi_display(self, pos: Tuple[float, float], tag: str = "") -> svgwrite.container.Group:
        """HMI/Display screen symbol"""
        group = self._create_group(f"hmi_{tag}")
        x, y = pos
        width = self.symbol_size * 1.8
        height = self.symbol_size * 1.2

        # Screen
        group.add(self.dwg.rect(
            insert=(x - width/2, y - height/2),
            size=(width, height),
            fill="black",
            stroke="darkgray",
            stroke_width=3 * self.scale,
            rx=5,
            ry=5
        ))

        # Inner screen (lighter)
        group.add(self.dwg.rect(
            insert=(x - width/2 + 5, y - height/2 + 5),
            size=(width - 10, height - 10),
            fill="lightblue",
            stroke="none"
        ))

        # HMI label
        group.add(self.dwg.text(
            "HMI",
            insert=(x, y + 5),
            text_anchor="middle",
            font_size=16 * self.scale,
            font_family="Arial",
            font_weight="bold",
            fill="darkblue"
        ))

        # Tag
        if tag:
            group.add(self.dwg.text(
                tag,
                insert=(x, y + height/2 + 18),
                text_anchor="middle",
                font_size=11 * self.scale,
                font_family="Arial",
                font_weight="bold"
            ))

        return group
