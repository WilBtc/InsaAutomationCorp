# P&ID Diagram Generator for Industrial Automation

**Version:** 1.0.0
**Author:** INSA Automation Corp
**Date:** October 17, 2025

Automated P&ID (Piping and Instrumentation Diagram) generation from BOM (Bill of Materials) data for industrial automation projects.

---

## 🎯 Features

- **Automated diagram generation** from InvenTree BOM data
- **ISA-5.1 compliant symbols** for industrial instrumentation
- **Multiple output formats**: SVG (web/print), DXF (CAD software), JSON (data export)
- **Smart component detection** from part names and reference designators
- **Professional title blocks** with project info, date, revision
- **Auto-layout algorithm** for component positioning
- **Connection routing** for process lines, signals, pneumatic, and electric

---

## 📦 Installation

### Prerequisites

- Python 3.8+
- Virtual environment (included)

### Setup

```bash
cd ~/pid-generator
source venv/bin/activate

# Libraries already installed:
# - svgwrite 1.4.3 (SVG generation)
# - ezdxf 1.4.2 (DXF/CAD generation)
# - numpy 2.3.4 (numerical operations)
```

---

## 🚀 Quick Start

### Example 1: Manual Component Entry

```python
from pid_generator import PIDGenerator

# Create generator
pid = PIDGenerator(
    project_name="Industrial Control System",
    customer="ABC Manufacturing"
)

# Add components
pid.add_component("PLC", "PLC1", "Siemens S7-1200")
pid.add_component("HMI", "HMI1", "7-inch Touchscreen")
pid.add_component("Temperature Transmitter", "TT-101", "Process Temp")
pid.add_component("Control Valve", "CV-101", "Flow Control")

# Add connections
pid.add_connection("TT-101", "PLC1", "signal")
pid.add_connection("PLC1", "CV-101", "signal")
pid.add_connection("PLC1", "HMI1", "electric")

# Generate diagrams
svg_file = pid.generate_svg()
dxf_file = pid.generate_dxf()

print(f"✓ SVG: {svg_file}")
print(f"✓ DXF: {dxf_file}")
```

### Example 2: From InvenTree BOM

```python
from pid_generator import PIDGenerator

# BOM data from InvenTree (via inventree_create_bom MCP tool)
bom_data = [
    {
        "part_name": "Siemens S7-1200 PLC",
        "quantity": 1,
        "reference": "PLC1",
        "description": "Main controller"
    },
    {
        "part_name": "7-inch HMI Touchscreen",
        "quantity": 1,
        "reference": "HMI1",
        "description": "Operator interface"
    },
    {
        "part_name": "Temperature Sensor PT100",
        "quantity": 3,
        "reference": "TT-101",
        "description": "Process temperature"
    },
    {
        "part_name": "Pressure Transmitter 4-20mA",
        "quantity": 2,
        "reference": "PT-101",
        "description": "Line pressure"
    },
    {
        "part_name": "Control Valve DN50 PN16",
        "quantity": 2,
        "reference": "CV-101",
        "description": "Flow control"
    }
]

# Create and generate
pid = PIDGenerator("Water Treatment System", "City Utilities")
pid.load_from_bom(bom_data)
pid.generate_svg()
pid.generate_dxf()
```

---

## 📊 Supported Components

### Instruments
- **PLC** - Programmable Logic Controller
- **HMI** - Human Machine Interface
- **PID Controller** - Process controller
- **Temperature Transmitter (TT)** - Thermocouples, RTDs
- **Pressure Transmitter (PT)** - Pressure sensors
- **Flow Transmitter (FT)** - Flow meters
- **Level Transmitter (LT)** - Level sensors
- **Generic Sensors** - Any sensor type

### Actuators & Valves
- **Manual Valve** - Hand-operated
- **Control Valve (CV)** - Pneumatic/electric actuated
- **Solenoid Valve (SV)** - Electrically actuated
- **Pump** - Centrifugal pump

### Vessels & Equipment
- **Tank/Vessel** - Vertical tanks
- **HMI Display** - Operator screens

---

## 🎨 Output Formats

### SVG (Scalable Vector Graphics)
- **Use**: Web display, presentations, print
- **Size**: ~7-10 KB
- **Viewable in**: Web browsers, Inkscape, Adobe Illustrator
- **Scalable**: Infinite resolution

### DXF (Drawing Exchange Format)
- **Use**: CAD software import
- **Size**: ~15-20 KB
- **Editable in**: AutoCAD, QCAD, LibreCAD, FreeCAD
- **Layers**: INSTRUMENTS, SYMBOLS, PROCESS, SIGNALS, PNEUMATIC, ELECTRIC

### JSON (Component List)
- **Use**: Documentation, inventory, data processing
- **Size**: ~1-2 KB
- **Contains**: Full component specifications, connections, metadata

---

## 🔧 Connection Types

| Type | Color | Style | Usage |
|------|-------|-------|-------|
| **process** | Black | Solid line | Piping, material flow |
| **signal** | Blue | Dashed (5,5) | Instrument signals 4-20mA |
| **pneumatic** | Red | Solid line | Pneumatic tubing |
| **electric** | Green | Dotted (2,2) | Electrical wiring |

---

## 📐 Drawing Standards

### Compliance
- **ISA-5.1** - Instrumentation Symbols and Identification
- **ISO 14617** - Graphical symbols for diagrams
- **A3 Size** - 420mm x 297mm (1587 x 1122 pixels @96 DPI)

### Title Block
- Project name
- Customer name
- Drawing type (P&ID)
- Date (auto-generated)
- Drawn by (INSA Automation)
- Sheet number
- Revision
- Scale (NTS - Not To Scale)

---

## 🔄 Integration with ERPNext/InvenTree

### Workflow

```
1. ERPNext: Sales Order created (erpnext_create_sales_order)
2. ERPNext: Project created (erpnext_create_project)
3. InvenTree: BOM created (inventree_create_bom)
4. InvenTree: Get BOM data (inventree_get_part_details)
5. P&ID Generator: Load BOM → Generate diagrams
6. Output: SVG (web), DXF (engineering), JSON (docs)
```

### Example Integration Script

```python
#!/usr/bin/env python3
"""Generate P&ID from InvenTree BOM"""

import requests
from pid_generator import PIDGenerator

# InvenTree API configuration
INVENTREE_URL = "http://100.100.101.1:9600/api"
INVENTREE_USER = "admin"
INVENTREE_PASS = "insaadmin2025"

def get_bom_from_inventree(assembly_part_id):
    """Fetch BOM from InvenTree API"""
    response = requests.get(
        f"{INVENTREE_URL}/bom/",
        params={"part": assembly_part_id},
        auth=(INVENTREE_USER, INVENTREE_PASS)
    )
    return response.json()

def generate_pid_from_inventree(assembly_part_id, project_name, customer):
    """Generate P&ID from InvenTree BOM"""
    # Fetch BOM
    bom_raw = get_bom_from_inventree(assembly_part_id)

    # Convert to P&ID format
    bom_data = []
    for idx, item in enumerate(bom_raw):
        bom_data.append({
            "part_name": item.get("sub_part_detail", {}).get("name", ""),
            "quantity": item.get("quantity", 1),
            "reference": item.get("reference", f"COMP-{idx + 1}"),
            "description": item.get("note", "")
        })

    # Generate P&ID
    pid = PIDGenerator(project_name, customer)
    pid.load_from_bom(bom_data)

    # Output
    svg_file = pid.generate_svg()
    dxf_file = pid.generate_dxf()
    json_file = pid.export_component_list()

    return svg_file, dxf_file, json_file

# Usage
svg, dxf, json_data = generate_pid_from_inventree(
    assembly_part_id=200,
    project_name="Industrial Control Panel XYZ",
    customer="ABC Manufacturing"
)

print(f"✓ Generated: {svg}, {dxf}, {json_data}")
```

---

## 📝 API Reference

### PIDGenerator Class

#### Constructor
```python
PIDGenerator(project_name: str, customer: str = "")
```

#### Methods

**add_component(component_type, tag, description, quantity, specifications)**
- Add a component to the diagram

**add_connection(from_tag, to_tag, connection_type)**
- Add a connection between components

**load_from_bom(bom_data: List[Dict])**
- Load components from BOM data

**generate_svg(output_file: Optional[str]) -> str**
- Generate SVG diagram (returns file path)

**generate_dxf(output_file: Optional[str]) -> str**
- Generate DXF CAD file (returns file path)

**export_component_list(output_file: str) -> str**
- Export component list to JSON (returns file path)

---

## 📁 File Structure

```
~/pid-generator/
├── venv/                   # Python virtual environment
├── pid_symbols.py          # Symbol library (ISA-5.1 compliant)
├── pid_generator.py        # Main generator class
├── README.md               # This file
├── examples/               # Example scripts (to be created)
└── output/                 # Generated diagrams (to be created)
```

---

## 🎯 Use Cases

### Use Case 1: Quotation Support
Generate P&ID diagrams automatically when creating quotations to show customers the proposed system architecture.

### Use Case 2: Engineering Documentation
Create professional P&ID diagrams for project documentation and as-built drawings.

### Use Case 3: CAD Integration
Export to DXF for further editing in AutoCAD or other CAD tools.

### Use Case 4: Training Materials
Generate clear, standardized diagrams for operator training manuals.

---

## 🔍 Component Detection Logic

The generator automatically infers component types from:

1. **Reference Designator Prefix**
   - `PLC*` → PLC
   - `HMI*` → HMI
   - `TT-*` → Temperature Transmitter
   - `PT-*` → Pressure Transmitter
   - `FT-*` → Flow Transmitter
   - `LT-*` → Level Transmitter
   - `CV-*` → Control Valve
   - `SV-*` → Solenoid Valve

2. **Part Name Keywords**
   - "plc", "controller" → PLC
   - "hmi", "screen", "display" → HMI
   - "temperature", "thermocouple" → Temperature Transmitter
   - "pressure" → Pressure Transmitter
   - "flow" → Flow Transmitter
   - "valve" → Valve (type determined by other keywords)
   - "pump" → Pump
   - "tank", "vessel" → Tank

---

## ⚡ Performance

- **Generation Time**: <1 second for typical systems (10-50 components)
- **File Sizes**:
  - SVG: 5-15 KB
  - DXF: 10-30 KB
  - JSON: 1-5 KB
- **Memory Usage**: ~50 MB (virtual environment)

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'svgwrite'"

**Solution:**
```bash
cd ~/pid-generator
source venv/bin/activate
pip install svgwrite ezdxf
```

### Issue: "Permission denied"

**Solution:**
```bash
chmod +x pid_generator.py
```

### Issue: Component not rendering correctly

**Solution:** Check that the component type is recognized. Add custom handling in `_infer_component_type()` method.

---

## 📚 References

- **ISA-5.1-2009**: Instrumentation Symbols and Identification
- **ISO 14617**: Graphical symbols for diagrams
- **ISA-5.4-1991**: Instrument Loop Diagrams
- **SVGWrite Documentation**: https://svgwrite.readthedocs.io/
- **ezdxf Documentation**: https://ezdxf.readthedocs.io/

---

## 🚀 Future Enhancements

- [ ] Advanced auto-routing for connections
- [ ] 3D isometric view generation
- [ ] PDF export with embedded metadata
- [ ] Interactive HTML diagrams
- [ ] Import from Excel/CSV BOM templates
- [ ] Multi-sheet support for large systems
- [ ] Animated sequences for training
- [ ] Alarm and interlock diagrams

---

## 📞 Support

**Organization:** INSA Automation Corp
**Email:** w.aroca@insaing.com
**Documentation:** ~/pid-generator/README.md
**Server:** iac1 (100.100.101.1)

---

**Generated with:** Claude Code (INSA Automation DevSecOps)
**License:** Proprietary - INSA Automation Corp
**Version:** 1.0.0
