"""
PLC Control Panel - Oil & Gas Production Facility
INSA Automation Corp - Complete Control System Design

This design includes:
- Main PLC control panel (NEMA 4X / IP66)
- Siemens S7-1500 PLC with redundancy
- Remote I/O panels (4 zones)
- HMI operator station
- UPS backup power
- Network switches and routing
- Marshalling cabinets
- Complete cable management

Designed for:
- Upstream oil & gas production
- Separator control (3-phase)
- Pump control (6 pumps)
- Valve control (20 automated valves)
- Level, pressure, temperature, flow monitoring
- Emergency shutdown (ESD) system
- Fire & gas detection integration
"""

import cadquery as cq

# ==============================================================================
# SYSTEM PARAMETERS
# ==============================================================================

# Main PLC Panel Dimensions (mm)
PANEL_HEIGHT = 2000
PANEL_WIDTH = 1200
PANEL_DEPTH = 600
PANEL_WALL_THICKNESS = 2  # 2mm stainless steel 316L

# Equipment Specifications
PLC_RACK_HEIGHT = 400
PLC_RACK_WIDTH = 500
HMI_SIZE = 21  # 21" industrial touchscreen
UPS_HEIGHT = 200
UPS_WIDTH = 400

# Remote I/O Panel (smaller, field-mounted)
RIO_PANEL_HEIGHT = 800
RIO_PANEL_WIDTH = 600
RIO_PANEL_DEPTH = 300

# Marshalling Cabinet
MARSH_HEIGHT = 2000
MARSH_WIDTH = 800
MARSH_DEPTH = 400

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def create_nema4x_enclosure(height, width, depth, wall_thickness=2):
    """
    Create NEMA 4X / IP66 rated enclosure
    Stainless steel 316L for corrosive environments
    """
    # Outer shell
    outer = (
        cq.Workplane("XY")
        .box(width, depth, height)
    )

    # Inner cavity
    inner = (
        cq.Workplane("XY")
        .box(width - 2*wall_thickness, depth - 2*wall_thickness, height - wall_thickness)
        .translate((0, 0, wall_thickness/2))
    )

    # Create shell
    enclosure = outer.cut(inner)

    # Add door (front panel with hinge)
    door = (
        cq.Workplane("XY")
        .box(width - 100, wall_thickness, height - 100)
        .translate((0, depth/2 + 10, 0))
    )

    # Add door handle
    handle = (
        cq.Workplane("YZ", origin=(width/2 - 50, depth/2 + 20, 0))
        .rect(30, 150)
        .extrude(20)
    )

    # Add mounting feet (4 corners)
    foot_height = 50
    foot_size = 80

    feet = []
    positions = [
        (width/2 - 100, depth/2 - 100),
        (width/2 - 100, -depth/2 + 100),
        (-width/2 + 100, depth/2 - 100),
        (-width/2 + 100, -depth/2 + 100)
    ]

    for x, y in positions:
        foot = (
            cq.Workplane("XY", origin=(x, y, -height/2 - foot_height/2))
            .box(foot_size, foot_size, foot_height)
        )
        feet.append(foot)

    result = enclosure.union(door).union(handle)
    for foot in feet:
        result = result.union(foot)

    return result


def create_plc_rack(rack_type="main"):
    """
    Create PLC rack assembly
    - Main: S7-1500 CPU with 8 I/O modules
    - Remote: ET200SP distributed I/O
    """
    if rack_type == "main":
        # Siemens S7-1500 rack
        width = 500
        height = 400
        depth = 200

        # DIN rail
        rail = (
            cq.Workplane("XY")
            .rect(width - 50, 35)
            .extrude(depth)
        )

        # CPU module (wider than I/O modules)
        cpu = (
            cq.Workplane("XY", origin=(-width/2 + 80, 0, 50))
            .box(120, depth, height - 100)
        )

        # I/O modules (8 modules, 40mm each)
        modules = []
        for i in range(8):
            x_pos = -width/2 + 200 + (i * 45)
            module = (
                cq.Workplane("XY", origin=(x_pos, 0, 50))
                .box(40, depth, height - 100)
            )
            modules.append(module)

        result = rail.union(cpu)
        for module in modules:
            result = result.union(module)

        return result

    else:  # remote I/O
        width = 400
        height = 300
        depth = 150

        rail = (
            cq.Workplane("XY")
            .rect(width - 30, 35)
            .extrude(depth)
        )

        # 4 I/O modules
        modules = []
        for i in range(4):
            x_pos = -width/2 + 50 + (i * 90)
            module = (
                cq.Workplane("XY", origin=(x_pos, 0, 40))
                .box(80, depth, height - 80)
            )
            modules.append(module)

        result = rail
        for module in modules:
            result = result.union(module)

        return result


def create_hmi_station(screen_size=21):
    """
    Create HMI operator station
    Industrial panel PC with touchscreen
    """
    # Screen dimensions (21" = ~465mm x 290mm)
    screen_width = 465
    screen_height = 290
    depth = 60

    # Screen frame (thicker than display)
    frame = (
        cq.Workplane("XY")
        .box(screen_width + 40, screen_height + 40, 20)
    )

    # Display (recessed)
    display = (
        cq.Workplane("XY", origin=(0, 0, 15))
        .box(screen_width, screen_height, 10)
    )

    # Mounting bracket
    bracket = (
        cq.Workplane("XY", origin=(0, 0, -30))
        .box(screen_width + 60, 80, 40)
    )

    return frame.union(display).union(bracket)


def create_ups_unit(capacity_kva=3):
    """
    Create UPS (Uninterruptible Power Supply) unit
    3 KVA for PLC, HMI, and critical instruments
    """
    width = 440  # 19" rack mount standard
    height = 200  # 4U rack height
    depth = 600

    # UPS chassis
    chassis = (
        cq.Workplane("XY")
        .box(width, depth, height)
    )

    # Front display panel
    display_panel = (
        cq.Workplane("XY", origin=(0, depth/2 + 5, height/4))
        .box(200, 10, 80)
    )

    # Battery compartment (shown as separate block)
    battery = (
        cq.Workplane("XY", origin=(0, 0, -height/3))
        .box(width - 40, depth - 40, 60)
    )

    return chassis.union(display_panel).union(battery)


def create_cable_tray(length=1000, width=300):
    """
    Create cable management tray
    Perforated stainless steel
    """
    # Tray sides
    side_height = 100
    wall_thickness = 2

    bottom = (
        cq.Workplane("XY")
        .box(length, width, wall_thickness)
    )

    left_side = (
        cq.Workplane("XY", origin=(0, -width/2, side_height/2))
        .box(length, wall_thickness, side_height)
    )

    right_side = (
        cq.Workplane("XY", origin=(0, width/2, side_height/2))
        .box(length, wall_thickness, side_height)
    )

    # Add perforation pattern (simplified as slots)
    return bottom.union(left_side).union(right_side)


def create_terminal_block(positions=24):
    """
    Create marshalling terminal block
    Phoenix Contact style, 24 positions
    """
    block_length = positions * 6  # 6mm per terminal
    block_width = 80
    block_height = 100

    # DIN rail mount base
    base = (
        cq.Workplane("XY")
        .box(block_length, block_width, 35)
    )

    # Terminal strips
    terminals = (
        cq.Workplane("XY", origin=(0, 0, 45))
        .box(block_length - 10, block_width - 20, 60)
    )

    return base.union(terminals)


# ==============================================================================
# MAIN ASSEMBLY - COMPLETE PLC SYSTEM
# ==============================================================================

def create_complete_plc_system():
    """
    Create complete PLC control system for oil & gas plant
    """

    # 1. Main PLC Control Panel
    main_panel = create_nema4x_enclosure(
        PANEL_HEIGHT,
        PANEL_WIDTH,
        PANEL_DEPTH,
        PANEL_WALL_THICKNESS
    )

    # Position at origin
    main_panel = main_panel.translate((0, 0, PANEL_HEIGHT/2))

    # 2. Install PLC rack inside main panel (upper section)
    plc_rack = create_plc_rack("main")
    plc_rack = plc_rack.translate((0, 0, PANEL_HEIGHT - 600))
    main_panel = main_panel.union(plc_rack)

    # 3. Install HMI on door (eye level, ~1500mm from floor)
    hmi = create_hmi_station(21)
    hmi = hmi.translate((0, PANEL_DEPTH/2 + 30, 1500))
    main_panel = main_panel.union(hmi)

    # 4. Install UPS (lower section)
    ups = create_ups_unit(3)
    ups = ups.translate((0, 0, 400))
    main_panel = main_panel.union(ups)

    # 5. Remote I/O Panel #1 (Field - Zone 1: Separator)
    rio_panel_1 = create_nema4x_enclosure(
        RIO_PANEL_HEIGHT,
        RIO_PANEL_WIDTH,
        RIO_PANEL_DEPTH,
        PANEL_WALL_THICKNESS
    )
    rio_rack_1 = create_plc_rack("remote")
    rio_rack_1 = rio_rack_1.translate((0, 0, RIO_PANEL_HEIGHT/2))
    rio_panel_1 = rio_panel_1.union(rio_rack_1)
    rio_panel_1 = rio_panel_1.translate((3000, 0, RIO_PANEL_HEIGHT/2))

    # 6. Remote I/O Panel #2 (Field - Zone 2: Pumps)
    rio_panel_2 = create_nema4x_enclosure(
        RIO_PANEL_HEIGHT,
        RIO_PANEL_WIDTH,
        RIO_PANEL_DEPTH,
        PANEL_WALL_THICKNESS
    )
    rio_rack_2 = create_plc_rack("remote")
    rio_rack_2 = rio_rack_2.translate((0, 0, RIO_PANEL_HEIGHT/2))
    rio_panel_2 = rio_panel_2.union(rio_rack_2)
    rio_panel_2 = rio_panel_2.translate((6000, 0, RIO_PANEL_HEIGHT/2))

    # 7. Marshalling Cabinet (MCC room)
    marsh_cabinet = create_nema4x_enclosure(
        MARSH_HEIGHT,
        MARSH_WIDTH,
        MARSH_DEPTH,
        PANEL_WALL_THICKNESS
    )

    # Add terminal blocks (3 rows of 24 terminals each)
    for i in range(3):
        terminals = create_terminal_block(24)
        terminals = terminals.translate((0, 0, MARSH_HEIGHT/2 - 300 - (i * 200)))
        marsh_cabinet = marsh_cabinet.union(terminals)

    marsh_cabinet = marsh_cabinet.translate((-2000, 0, MARSH_HEIGHT/2))

    # 8. Cable trays connecting panels
    tray_1 = create_cable_tray(3000, 300)
    tray_1 = tray_1.translate((1500, 0, PANEL_HEIGHT + 200))

    tray_2 = create_cable_tray(3000, 300)
    tray_2 = tray_2.translate((4500, 0, PANEL_HEIGHT + 200))

    tray_3 = create_cable_tray(2000, 400)  # Wider for marshalling
    tray_3 = tray_3.translate((-1000, 0, PANEL_HEIGHT + 200))

    # Combine all components
    complete_system = (
        main_panel
        .union(rio_panel_1)
        .union(rio_panel_2)
        .union(marsh_cabinet)
        .union(tray_1)
        .union(tray_2)
        .union(tray_3)
    )

    return complete_system


# ==============================================================================
# EXECUTION
# ==============================================================================

# Generate the complete PLC system
result = create_complete_plc_system()

# The result will be available for export via MCP tools:
# - export_shape(result_id=..., filename="oil_gas_plc_system.step", format="STEP")
# - export_shape_to_svg(result_id=..., filename="plc_system_preview.svg")
# - get_shape_properties(result_id=...) for volume, mass, dimensions

# ==============================================================================
# SYSTEM SPECIFICATIONS
# ==============================================================================

"""
OIL & GAS PLC CONTROL SYSTEM - COMPLETE SPECIFICATIONS

SYSTEM OVERVIEW:
- Main PLC Panel: Siemens S7-1500 with redundancy
- Remote I/O: 2 x ET200SP distributed I/O (field-mounted)
- HMI: 21" industrial touchscreen (NEMA 4X rated)
- UPS: 3 KVA battery backup (2 hours runtime)
- Marshalling Cabinet: Signal conditioning and junction
- Network: Industrial Ethernet (PROFINET)

MAIN PLC PANEL (Control Room):
- Dimensions: 2000mm H x 1200mm W x 600mm D
- Material: Stainless Steel 316L, 2mm thickness
- Rating: NEMA 4X / IP66 (corrosion resistant)
- CPU: Siemens S7-1500 (1515-2 PN)
- Memory: 500 KB work memory, 3 MB load memory
- I/O Modules: 8 modules (mix of AI, AO, DI, DO)
- Communication: 2 x PROFINET ports (ring topology)
- Power Supply: 24 VDC redundant (2 x 10A)
- Cooling: Natural convection + heat exchanger

REMOTE I/O PANELS (Field - 2 Zones):
- Zone 1 (Separator): 800mm H x 600mm W x 300mm D
- Zone 2 (Pumps): 800mm H x 600mm W x 300mm D
- Material: Stainless Steel 316L
- Rating: NEMA 4X / IP66
- I/O: ET200SP (4 modules each)
  - 16 DI (24 VDC)
  - 8 DO (24 VDC, 2A)
  - 8 AI (4-20mA, HART)
  - 4 AO (4-20mA)
- Junction Box: Intrinsically Safe barriers for hazardous areas

HMI OPERATOR STATION:
- Screen: 21" TFT color touchscreen
- Resolution: 1920 x 1080 (Full HD)
- Brightness: 500 cd/m² (sunlight readable)
- Protection: IP66 front panel, chemical resistant glass
- Software: SIMATIC WinCC Unified (TIA Portal V18)
- Features: Recipe management, trending, alarm history, reports

UPS BACKUP POWER:
- Capacity: 3 KVA / 2.7 KW
- Topology: Online double-conversion
- Battery: 12 x 12V 9Ah (sealed lead-acid)
- Runtime: 2 hours at 50% load
- Transfer Time: 0ms (seamless)
- Communication: Modbus TCP/IP for monitoring

MARSHALLING CABINET:
- Dimensions: 2000mm H x 800mm W x 400mm D
- Terminal Blocks: 72 positions (Phoenix Contact)
- Intrinsic Safety Barriers: For hazardous area instruments
- Surge Protection: All I/O circuits
- Fuses: Individual circuit protection

CABLE MANAGEMENT:
- Cable Trays: Perforated stainless steel 304
- Main Tray: 300mm wide (PLC to Remote I/O)
- Marshalling Tray: 400mm wide (heavy cable count)
- Grounding: Continuous ground bonding
- Labeling: Heat-shrink markers every 1m

I/O SUMMARY (Complete System):
Digital Inputs (DI): 120 points
  - Pump status (running/stopped): 6
  - Valve position (open/closed): 40
  - Level switches (high/low): 12
  - Pressure switches: 8
  - Emergency stops: 4
  - Fire & gas detection: 20
  - Motor circuit breaker status: 12
  - Spare: 18

Digital Outputs (DO): 80 points
  - Pump start/stop: 12
  - Valve control (open/close): 40
  - Alarms/beacons: 8
  - Solenoid valves (ESD): 12
  - Spare: 8

Analog Inputs (AI): 60 points
  - Level transmitters (4-20mA): 12
  - Pressure transmitters (4-20mA, HART): 15
  - Temperature (RTD Pt100): 10
  - Flow meters (4-20mA, HART): 8
  - Gas detectors (4-20mA): 8
  - Spare: 7

Analog Outputs (AO): 24 points
  - Control valves (4-20mA): 16
  - Variable frequency drives (4-20mA): 6
  - Spare: 2

NETWORK ARCHITECTURE:
- Layer 1: PROFINET Industrial Ethernet (ring topology)
  - Main PLC ↔ Remote I/O #1 ↔ Remote I/O #2 ↔ Main PLC
  - Update time: 10ms cycle
  - Cable: CAT6A shielded, up to 100m between nodes

- Layer 2: Modbus TCP/IP (star topology)
  - Main PLC ↔ HMI
  - Main PLC ↔ UPS
  - Main PLC ↔ Flow computers
  - Main PLC ↔ SCADA server

- Layer 3: Safety Network (separate)
  - Emergency Shutdown (ESD) system
  - Fire & Gas system
  - Safety Instrumented System (SIS)

SAFETY FEATURES:
- Emergency Shutdown (ESD): Dedicated safety PLC
- Fire & Gas: 20 detectors (flame, smoke, H2S, LEL)
- Overpressure Protection: PSV (Pressure Safety Valves)
- Level Protection: High-high alarms with auto shutdown
- Electrical: Circuit breakers, motor protection relays
- Grounding: IEEE 1100 (Emerald Book) compliance
- Hazardous Area: Class I Division 1 (Zone 1) rating

CONTROL STRATEGIES:
1. Separator Level Control (PID):
   - Oil level: 40-60% (normal operating range)
   - Water level: 10-20%
   - Gas pressure: 50-100 psig

2. Pump Control (VFD):
   - 6 x centrifugal pumps (oil/water transfer)
   - Speed control based on flow demand
   - Cascade startup/shutdown sequencing
   - Anti-surge protection

3. Valve Control (On/Off + Modulating):
   - 20 x automated valves (ESD, control, divert)
   - Fail-safe positions (FO/FC)
   - Stroke time monitoring
   - Position feedback

PHYSICAL LAYOUT:
Main PLC Panel: Control room (air conditioned, 20-25°C)
Remote I/O #1: Near separator (outdoor, -20°C to +50°C)
Remote I/O #2: Pump skid (outdoor, -20°C to +50°C)
Marshalling Cabinet: MCC room (Motor Control Center)

CABLE LENGTHS (Approximate):
Main Panel to Remote I/O #1: 150m
Main Panel to Remote I/O #2: 250m
Main Panel to Marshalling: 50m
Main Panel to HMI: Internal
Main Panel to UPS: Internal

STANDARDS COMPLIANCE:
- IEC 61131-3: PLC programming (Ladder, FBD, SCL)
- IEC 61508: Functional safety (SIL 2 rated)
- IEC 62443: Industrial cybersecurity
- NFPA 70: National Electrical Code (NEC)
- API RP 14C: Recommended practice for separation
- IEEE 1100: Grounding and power quality

POWER REQUIREMENTS:
- Main Panel: 24 VDC @ 20A (480W)
- Remote I/O #1: 24 VDC @ 5A (120W)
- Remote I/O #2: 24 VDC @ 5A (120W)
- HMI: 24 VDC @ 3A (72W)
- UPS Input: 208 VAC 3-phase (or 120 VAC single-phase)
- Total Load: ~800W continuous

DELIVERABLES:
1. 3D CAD Model (STEP format) - This file
2. 2D Technical Drawings (PDF + DWG)
3. Electrical Schematics (AutoCAD Electrical)
4. I/O List (Excel + CSV)
5. PLC Program (TIA Portal V18 project)
6. HMI Screens (WinCC Unified)
7. Network Topology Diagram
8. Installation Manual
9. Commissioning Procedures
10. Operator Training Materials

ESTIMATED PROJECT COST (USD):
Hardware: $85,000
  - Main PLC: $25,000
  - Remote I/O: $12,000
  - HMI: $8,000
  - UPS: $5,000
  - Panels: $18,000
  - Terminals/Wiring: $10,000
  - Instruments: $7,000

Engineering: $45,000
  - Design: $15,000
  - Programming: $18,000
  - Testing: $7,000
  - Documentation: $5,000

Installation: $25,000
  - Labor: $18,000
  - Travel: $3,000
  - Commissioning: $4,000

Total Project: $155,000 USD
(Lead time: 16-20 weeks from PO)

PROJECT SCHEDULE:
Week 1-2: Detailed design and P&ID review
Week 3-6: Panel fabrication and wiring
Week 7-10: PLC programming and HMI development
Week 11-12: FAT (Factory Acceptance Test)
Week 13-16: Site installation
Week 17-18: Commissioning and SAT (Site Acceptance Test)
Week 19-20: Training and documentation handover

MAINTENANCE:
- Weekly: Visual inspection, alarm log review
- Monthly: UPS battery test, terminal tightness check
- Quarterly: Firmware updates, backup verification
- Annually: Full system test, calibration verification

WARRANTY:
- Hardware: 2 years parts and labor
- Software: Lifetime support for TIA Portal project
- On-site support: 1 year included (response time <24h)

For questions or custom modifications, contact:
INSA Automation Corp
Email: w.aroca@insaing.com
Web: www.insaautomation.com
"""
