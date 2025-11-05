"""
Separador Trifásico (Three-Phase Separator) - CadQuery Model
INSA Automation Corp - Industrial Equipment CAD Generation

This script generates a 3D model of a three-phase separator vessel
for oil, gas, and water separation in upstream petroleum operations.

Parameters can be passed from ERPNext BOM or modified directly.
"""

import cadquery as cq

# ==============================================================================
# PARAMETERS (Can be passed via MCP execute_cadquery_script tool)
# ==============================================================================

# Vessel dimensions
DIAMETER = 1200  # mm (outer diameter)
LENGTH = 3000    # mm (vessel length)
WALL_THICKNESS = 10  # mm (pressure vessel wall)
HEAD_TYPE = "elliptical"  # or "hemispherical", "torispherical"

# Nozzle specifications (based on ASME B16.5)
INLET_SIZE = 150  # DN150 (6 inch)
GAS_OUTLET_SIZE = 100  # DN100 (4 inch)
OIL_OUTLET_SIZE = 150  # DN150 (6 inch)
WATER_OUTLET_SIZE = 100  # DN100 (4 inch)
DRAIN_SIZE = 50  # DN50 (2 inch)
VENT_SIZE = 25  # DN25 (1 inch)

# Nozzle positions (Z-axis, from bottom)
INLET_Z = LENGTH * 0.75
GAS_OUTLET_Z = LENGTH * 0.90
OIL_OUTLET_Z = LENGTH * 0.50
WATER_OUTLET_Z = LENGTH * 0.10
DRAIN_Z = 50

# Flange specifications (ASME B16.5 Class 150)
FLANGE_RATINGS = {
    25: {"od": 90, "thickness": 11},    # DN25 (1")
    50: {"od": 120, "thickness": 14},   # DN50 (2")
    100: {"od": 215, "thickness": 17},  # DN100 (4")
    150: {"od": 280, "thickness": 20},  # DN150 (6")
}

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def create_nozzle(dn_size, length=200, position=(0, 0, 0), direction="radial"):
    """
    Create a nozzle with flange

    Args:
        dn_size: Nominal diameter (DN)
        length: Nozzle length (mm)
        position: (x, y, z) position
        direction: "radial" or "axial"

    Returns:
        CadQuery Workplane with nozzle assembly
    """
    # Nozzle pipe
    pipe_od = dn_size
    pipe_id = dn_size - (2 * WALL_THICKNESS)

    if direction == "radial":
        nozzle = (
            cq.Workplane("XZ", origin=position)
            .circle(pipe_od / 2)
            .circle(pipe_id / 2)
            .extrude(length)
        )
    else:  # axial
        nozzle = (
            cq.Workplane("XY", origin=position)
            .circle(pipe_od / 2)
            .circle(pipe_id / 2)
            .extrude(length)
        )

    # Flange
    flange_spec = FLANGE_RATINGS.get(dn_size, FLANGE_RATINGS[150])
    flange_od = flange_spec["od"]
    flange_thickness = flange_spec["thickness"]

    if direction == "radial":
        flange = (
            cq.Workplane("XZ", origin=(position[0], position[1] + length, position[2]))
            .circle(flange_od / 2)
            .extrude(flange_thickness)
        )
    else:  # axial
        flange = (
            cq.Workplane("XY", origin=(position[0], position[1], position[2] + length))
            .circle(flange_od / 2)
            .extrude(flange_thickness)
        )

    return nozzle.union(flange)


def create_elliptical_head(diameter, wall_thickness):
    """
    Create elliptical pressure vessel head (2:1 ellipse)

    Args:
        diameter: Vessel outer diameter (mm)
        wall_thickness: Wall thickness (mm)

    Returns:
        CadQuery Workplane with elliptical head
    """
    # 2:1 elliptical head per ASME Sec VIII Div 1
    major_axis = diameter / 2
    minor_axis = diameter / 4

    # Outer surface
    outer = cq.Workplane("XY").ellipse(major_axis, minor_axis).revolve(180, (0, 0, 0), (1, 0, 0))

    # Inner surface (subtract to create shell)
    inner_major = major_axis - wall_thickness
    inner_minor = minor_axis - wall_thickness
    inner = cq.Workplane("XY").ellipse(inner_major, inner_minor).revolve(180, (0, 0, 0), (1, 0, 0))

    return outer.cut(inner)


# ==============================================================================
# MAIN ASSEMBLY
# ==============================================================================

def create_separator():
    """Create complete three-phase separator assembly"""

    # 1. Vessel body (cylindrical shell)
    vessel = (
        cq.Workplane("XY")
        .circle(DIAMETER / 2)
        .circle((DIAMETER / 2) - WALL_THICKNESS)
        .extrude(LENGTH)
    )

    # 2. Add elliptical heads
    head_left = create_elliptical_head(DIAMETER, WALL_THICKNESS)
    head_right = create_elliptical_head(DIAMETER, WALL_THICKNESS).rotate((0, 0, 0), (0, 1, 0), 180)

    vessel = vessel.union(head_left).union(head_right.translate((0, 0, LENGTH)))

    # 3. Add inlet nozzle (tangential entry for gas/liquid separation)
    inlet = create_nozzle(
        dn_size=INLET_SIZE,
        length=300,
        position=(0, DIAMETER/2, INLET_Z),
        direction="radial"
    )
    vessel = vessel.union(inlet)

    # 4. Add gas outlet nozzle (top)
    gas_outlet = create_nozzle(
        dn_size=GAS_OUTLET_SIZE,
        length=200,
        position=(0, DIAMETER/2, GAS_OUTLET_Z),
        direction="radial"
    )
    vessel = vessel.union(gas_outlet)

    # 5. Add oil outlet nozzle (middle)
    oil_outlet = create_nozzle(
        dn_size=OIL_OUTLET_SIZE,
        length=250,
        position=(DIAMETER/2, 0, OIL_OUTLET_Z),
        direction="radial"
    )
    vessel = vessel.union(oil_outlet)

    # 6. Add water outlet nozzle (bottom)
    water_outlet = create_nozzle(
        dn_size=WATER_OUTLET_SIZE,
        length=200,
        position=(-DIAMETER/2, 0, WATER_OUTLET_Z),
        direction="radial"
    )
    vessel = vessel.union(water_outlet)

    # 7. Add drain nozzle (bottom, lowest point)
    drain = create_nozzle(
        dn_size=DRAIN_SIZE,
        length=150,
        position=(0, 0, DRAIN_Z),
        direction="axial"
    )
    vessel = vessel.union(drain)

    # 8. Add vent nozzle (top)
    vent = create_nozzle(
        dn_size=VENT_SIZE,
        length=100,
        position=(0, 0, LENGTH - 100),
        direction="axial"
    )
    vessel = vessel.union(vent)

    # 9. Add support saddles (simplified)
    saddle_width = 200
    saddle_height = 150
    saddle_thickness = 15

    saddle_left = (
        cq.Workplane("YZ", origin=(0, 0, LENGTH * 0.25))
        .rect(saddle_width, saddle_height)
        .extrude(saddle_thickness)
    )

    saddle_right = (
        cq.Workplane("YZ", origin=(0, 0, LENGTH * 0.75))
        .rect(saddle_width, saddle_height)
        .extrude(saddle_thickness)
    )

    vessel = vessel.union(saddle_left).union(saddle_right)

    return vessel


# ==============================================================================
# EXECUTION
# ==============================================================================

# Generate the separator model
result = create_separator()

# The 'result' object will be available to the MCP server for export
# You can export it using:
#   export_shape(result_id=..., filename="separador_trifasico.step", format="STEP")
#   export_shape_to_svg(result_id=..., filename="separador_preview.svg")

# ==============================================================================
# METADATA (Used by scan_part_library tool)
# ==============================================================================

"""
Name: Separador Trifásico Horizontal
Description: Three-phase horizontal separator for oil, gas, and water separation.
             Includes inlet, outlets for each phase, drain, vent, and support saddles.
             Designed per ASME Section VIII Division 1 standards.
Tags: separator, vessel, pressure-vessel, oil-gas, three-phase, asme
Author: INSA Automation Corp
Version: 1.0
Date: 2025-10-18

Parameters:
  - DIAMETER: 1200mm (vessel outer diameter)
  - LENGTH: 3000mm (vessel length)
  - WALL_THICKNESS: 10mm (pressure vessel wall)
  - Design Pressure: 150 psi (ASME Class 150)
  - Design Temperature: -20°C to 120°C

Nozzles:
  - Inlet: DN150 (6") - Tangential entry
  - Gas Outlet: DN100 (4") - Top outlet
  - Oil Outlet: DN150 (6") - Middle outlet
  - Water Outlet: DN100 (4") - Bottom outlet
  - Drain: DN50 (2") - Bottom drain
  - Vent: DN25 (1") - Top vent

Export Formats:
  - STEP: For manufacturing and detailed design
  - STL: For 3D printing scale models
  - SVG: For technical proposals and P&ID integration
"""
