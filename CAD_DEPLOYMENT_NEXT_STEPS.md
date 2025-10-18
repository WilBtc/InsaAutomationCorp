# CAD Deployment Next Steps - CadQuery Recommended

**Date:** October 18, 2025
**Server:** iac1 (100.100.101.1)
**Current Status:** FreeCAD MCP blocked, CadQuery recommended for headless deployment

---

## 📋 Executive Summary

**FreeCAD MCP deployment BLOCKED** due to GUI requirement on headless server iac1.

**Recommended Alternative:** **CadQuery MCP** - Pure Python parametric CAD with full headless support.

**Files Created:**
1. `~/CAD_OSS_MCP_RESEARCH_2025.md` - Comprehensive CAD research (500+ lines)
2. `~/FREECAD_MCP_DEPLOYMENT_ANALYSIS.md` - Deployment blocker analysis + solution
3. `~/CAD_DEPLOYMENT_NEXT_STEPS.md` - This file (action plan)

---

## 🚨 Why FreeCAD MCP Failed

### Architecture Discovery

Both production FreeCAD MCP servers (contextform, neka-nat) require:
- ✅ FreeCAD GUI application running
- ✅ XML-RPC server on localhost:9875
- ✅ Workbench addon installed in FreeCAD
- ❌ **Cannot operate in headless mode**

**Root Cause:**
```python
# From freecad-mcp server.py:
class FreeCADConnection:
    def __init__(self, host: str = "localhost", port: int = 9875):
        self.server = xmlrpc.client.ServerProxy(
            f"http://{host}:{port}",
            allow_none=True
        )
```

**iac1 Server Constraints:**
- Headless Ubuntu Server 24.04 (no X11, no display server)
- SSH-only access
- Cannot run FreeCAD GUI application
- QT_QPA_PLATFORM=offscreen only works for FreeCAD CLI, not MCP server

**Conclusion:** FreeCAD MCP is **incompatible** with headless server deployment.

---

## ✅ What Was Installed Successfully

### 1. FreeCAD 0.21.2 (Headless-Compatible CLI)
```bash
Location: /usr/bin/freecad
Size: 1.2GB (193 packages)
Python API: WORKS in headless mode
Status: ✅ KEPT (Python API still useful)

# Python API works:
import sys
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD
FreeCAD.Version()  # SUCCESS
```

### 2. freecad-mcp Python Package
```bash
Location: ~/mcp-servers/freecad-mcp/venv
Package: freecad-mcp 0.1.13 + 32 dependencies
Status: ✅ Installed (but won't work without GUI)
```

### 3. MCP Configuration
```bash
File: ~/.mcp.json
Status: ✅ FreeCAD removed (GUI blocker)
Backup: Available if needed for future workstation deployment
```

---

## 🎯 Recommended Solution: CadQuery MCP

### Why CadQuery is Perfect for iac1

**CadQuery** is a Python-based parametric CAD library (like FreeCAD's Python API, but standalone):

```python
import cadquery as cq

# Pure Python - no GUI required!
result = (cq.Workplane("XY")
    .box(60, 60, 10)
    .faces(">Z")
    .hole(5))

# Export STEP, STL, DXF, SVG
cq.exporters.export(result, "part.step")
```

**Advantages:**
1. ✅ **Pure Python** - no GUI dependencies
2. ✅ **Headless operation** - perfect for servers
3. ✅ **MCP server available** - rishigundakaram/cadquery-mcp-server
4. ✅ **Same OCCT kernel** - industry-standard (like FreeCAD)
5. ✅ **STEP/IGES export** - manufacturing-ready
6. ✅ **Lightweight** - ~500MB vs FreeCAD's 1.2GB
7. ✅ **Code-based CAD** - ideal for AI agent automation

---

## 🚀 CadQuery Deployment Plan

### Step 1: Install CadQuery
```bash
# Create virtualenv
cd ~/mcp-servers
mkdir cadquery-mcp
cd cadquery-mcp
python3 -m venv venv
source venv/bin/activate

# Install CadQuery
pip install cadquery

# Verify installation
python -c "import cadquery as cq; print('CadQuery version:', cq.__version__)"
```

**Expected Output:**
```
CadQuery version: 2.4.0
```

**Disk Space:** ~500MB (half of FreeCAD)

### Step 2: Install CadQuery MCP Server
```bash
# Clone MCP server
cd ~/mcp-servers/cadquery-mcp
git clone https://github.com/rishigundakaram/cadquery-mcp-server.git server

# Install dependencies
cd server
pip install -r requirements.txt

# Test server
python server.py --help
```

**MCP Server Features:**
- CAD object creation (boxes, cylinders, spheres, etc.)
- Boolean operations (union, subtract, intersect)
- Extrusion, revolution, loft
- Assembly management
- STEP/IGES/STL/DXF export

### Step 3: Configure ~/.mcp.json
```bash
# Backup current config
cp ~/.mcp.json ~/.mcp.json.backup-$(date +%Y%m%d_%H%M%S)

# Add CadQuery MCP server
```

```json
{
  "mcpServers": {
    "cadquery-mcp": {
      "transport": "stdio",
      "command": "/home/wil/mcp-servers/cadquery-mcp/venv/bin/python",
      "args": ["/home/wil/mcp-servers/cadquery-mcp/server/server.py"],
      "env": {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1"
      },
      "_description": "CadQuery CAD automation for INSA - Pure Python parametric 3D CAD, STEP/IGES/DXF export, headless operation, BOM-driven CAD generation"
    }
  }
}
```

### Step 4: Test CadQuery MCP
```bash
# Test server startup
cd ~/mcp-servers/cadquery-mcp
timeout 5 ./venv/bin/python server/server.py

# Expected: Server starts without errors, listens for MCP protocol
```

### Step 5: Integration Testing
```python
#!/usr/bin/env python3
"""Test CadQuery headless CAD generation"""

import cadquery as cq

# Test 1: Basic shape creation
box = cq.Workplane("XY").box(100, 50, 30)
cq.exporters.export(box, "/tmp/test_box.step")
print("✓ Test 1: Box STEP export successful")

# Test 2: Complex part
bracket = (cq.Workplane("XY")
    .box(80, 60, 10)
    .faces(">Z")
    .workplane()
    .hole(10)
    .faces(">Z")
    .workplane()
    .rect(50, 40, forConstruction=True)
    .vertices()
    .hole(5))
cq.exporters.export(bracket, "/tmp/test_bracket.step")
print("✓ Test 2: Bracket STEP export successful")

# Test 3: Assembly
assembly = cq.Assembly()
assembly.add(box, name="base")
assembly.add(bracket, name="bracket", loc=cq.Location((0, 0, 15)))
assembly.save("/tmp/test_assembly.step")
print("✓ Test 3: Assembly STEP export successful")
```

**Expected Output:**
```
✓ Test 1: Box STEP export successful
✓ Test 2: Bracket STEP export successful
✓ Test 3: Assembly STEP export successful

Files created:
- /tmp/test_box.step (3D model)
- /tmp/test_bracket.step (3D model with features)
- /tmp/test_assembly.step (multi-part assembly)
```

---

## 🔗 ERPNext/InvenTree Integration

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Claude Code AI Agent                                        │
│ - Natural language: "Create 3D model for PLC enclosure"    │
└────────────┬────────────────────────────────────────────────┘
             │ MCP Protocol
             ▼
┌─────────────────────────────────────────────────────────────┐
│ CadQuery MCP Server (iac1 headless)                        │
│ - Parse requirements                                         │
│ - Generate Python CAD code                                  │
│ - Execute CadQuery scripts                                  │
│ - Export STEP/IGES/DXF files                               │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──────────────┬──────────────┐
             ▼              ▼              ▼
┌───────────────┐  ┌────────────┐  ┌──────────────────┐
│ InvenTree BOM │  │ ERPNext    │  │ P&ID Generator   │
│ - Dimensions  │  │ Projects   │  │ - 2D diagrams    │
│ - Materials   │  │ - Quotes   │  │ - Symbols        │
│ - Assembly    │  │ - Orders   │  │ - DXF export     │
└───────────────┘  └────────────┘  └──────────────────┘
             │              │              │
             └──────────────┴──────────────┘
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ Output: Complete Technical Documentation                    │
│ - 3D CAD models (STEP/IGES) - Manufacturing                │
│ - 2D drawings (DXF) - Fabrication                          │
│ - P&ID diagrams (SVG/DXF) - Installation                   │
│ - Assembly instructions (PDF) - Field service              │
└─────────────────────────────────────────────────────────────┘
```

### Example: BOM → 3D CAD Automation

```python
#!/usr/bin/env python3
"""Auto-generate 3D CAD models from InvenTree BOMs"""

import cadquery as cq
import requests

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

def generate_plc_enclosure(width, height, depth):
    """Generate industrial PLC enclosure"""
    enclosure = (cq.Workplane("XY")
        # Base box
        .box(width, depth, height)
        # Front panel cutout
        .faces(">X").workplane()
        .rect(width * 0.8, height * 0.8).cutThruAll()
        # Mounting holes (4 corners)
        .faces(">Z").workplane()
        .rect(width - 20, depth - 20, forConstruction=True)
        .vertices().hole(5)
        # Cable glands (bottom)
        .faces("<Z").workplane()
        .rarray(width / 3, 1, 3, 1)
        .circle(10).cutThruAll()
        # DIN rail mounting slots
        .faces("<X").workplane()
        .rarray(1, height / 4, 1, 3)
        .slot2D(30, 5).cutBlind(-5)
    )
    return enclosure

def generate_cad_from_bom(assembly_part_id, project_name):
    """Main function: BOM → 3D CAD model"""
    # Get BOM from InvenTree
    bom_data = get_bom_from_inventree(assembly_part_id)

    # Create assembly
    assembly = cq.Assembly()

    for idx, item in enumerate(bom_data):
        part_name = item.get("sub_part_detail", {}).get("name", "")
        quantity = item.get("quantity", 1)
        reference = item.get("reference", f"COMP-{idx+1}")

        # Generate part based on type
        if "PLC" in part_name.upper():
            plc_enclosure = generate_plc_enclosure(120, 200, 80)
            assembly.add(plc_enclosure, name=f"PLC_{reference}")

        elif "HMI" in part_name.upper():
            hmi = (cq.Workplane("XY")
                .box(180, 10, 120)
                .faces(">Y")
                .workplane()
                .rect(160, 100).cutBlind(-5)
            )
            assembly.add(hmi, name=f"HMI_{reference}")

        # Add more part types...

    # Export assembly
    output_file = f"/tmp/{project_name}_assembly.step"
    assembly.save(output_file)

    print(f"✓ 3D CAD model generated: {output_file}")
    print(f"  - Parts: {len(bom_data)}")
    print(f"  - Format: STEP (ISO 10303)")
    print(f"  - Size: {os.path.getsize(output_file) / 1024:.1f} KB")

    return output_file

# Usage
cad_file = generate_cad_from_bom(
    assembly_part_id=200,
    project_name="Industrial_Automation_Panel_XYZ"
)
```

### ERPNext Quotation Integration

```python
#!/usr/bin/env python3
"""Generate 3D CAD preview for ERPNext quotations"""

import cadquery as cq
import base64

def generate_quotation_preview(quotation_items):
    """
    Create 3D preview of quoted system
    Input: ERPNext quotation line items
    Output: STEP file + PNG preview
    """
    assembly = cq.Assembly()

    for item in quotation_items:
        item_name = item["item_name"]
        qty = item["qty"]

        # Create visual representation
        if "Cabinet" in item_name:
            cabinet = cq.Workplane("XY").box(800, 600, 2000)
            assembly.add(cabinet, name="Cabinet")

        # ... add more items

    # Export STEP for engineering
    assembly.save("/tmp/quotation_preview.step")

    # Export PNG for sales (requires OCP to PNG conversion)
    # This would be handled by CadQuery's visualization tools

    return {
        "step_file": "/tmp/quotation_preview.step",
        "preview_image": "/tmp/quotation_preview.png"
    }

# Attach to ERPNext quotation
# (via MCP tool: erpnext_create_quotation with file attachment)
```

---

## 💰 Business Value

### Use Cases Enabled by CadQuery

1. **Automated Quote Generation**
   - Input: ERPNext quotation items
   - Output: 3D preview STEP file
   - Benefit: Visual proposals increase close rate

2. **Engineering Documentation**
   - Input: InvenTree BOM
   - Output: STEP files for manufacturing
   - Benefit: Faster project handoff

3. **Project Visualization**
   - Input: Project milestones
   - Output: Assembly progress views
   - Benefit: Customer transparency

4. **Training Materials**
   - Input: Equipment list
   - Output: Exploded assembly views
   - Benefit: Field service support

### ROI Estimate

**From research document (~/CAD_OSS_MCP_RESEARCH_2025.md):**

| Metric | Manual Process | CadQuery Automated | Savings |
|--------|----------------|-------------------|---------|
| CAD model creation | 4-6 hours | 20-30 min | 80-90% |
| Technical drawings | 2-3 hours | 10-15 min | 90-95% |
| BOM-to-CAD | 6-8 hours | 30-45 min | 85-90% |
| Quotation previews | 1-2 hours | 5-10 min | 85-95% |

**Annual Savings (20 projects/year):**
- Time saved: 50-65% reduction
- Cost savings: $4,500 - $9,000
- Customer satisfaction: Higher due to visual proposals
- Engineering efficiency: Faster project delivery

---

## 📊 Comparison: FreeCAD vs CadQuery

| Feature | FreeCAD + MCP | CadQuery + MCP | Winner |
|---------|---------------|----------------|--------|
| Headless Operation | ❌ GUI Required | ✅ Pure Python | **CadQuery** |
| iac1 Deployment | ❌ Blocked | ✅ Compatible | **CadQuery** |
| Disk Space | 1.2GB | ~500MB | **CadQuery** |
| Python API | ✅ Available | ✅ Native | Tie |
| STEP/IGES Export | ✅ Full | ✅ Full | Tie |
| MCP Integration | ⚠️ 2 servers (GUI) | ✅ 1 server (headless) | **CadQuery** |
| AI Automation | ⚠️ Limited (GUI) | ✅ Excellent (code) | **CadQuery** |
| Learning Curve | Moderate | Easy (Python) | **CadQuery** |
| Industrial Use | ✅ Mature | ✅ Production-ready | Tie |

**Verdict:** CadQuery is the **clear winner** for iac1 headless server deployment.

---

## 🔄 FreeCAD Future Options

### Keep FreeCAD Installed (Python API)

FreeCAD's Python API still works headless and can be used for:
```python
import sys
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD

# Can use FreeCAD Python API for STEP import/analysis
doc = FreeCAD.open("/tmp/model.step")
# ... process STEP file
```

**Use Cases:**
- STEP file import/validation
- CAD file conversion
- Geometry analysis
- Fallback option

**Disk Space:** Already installed (1.2GB) - keep it

### Workstation Deployment (Future)

If GUI-based FreeCAD MCP is needed later:
```yaml
Deploy on: Workstation (LU1 - 100.81.103.99)
OS: Likely has GUI support
Access: Via Tailscale from iac1
MCP: Full FreeCAD GUI + MCP addon
Trade-off: Workstation must be always on
```

**When to Consider:**
- Need advanced FreeCAD-specific features
- Require FreeCAD GUI for complex operations
- Have dedicated workstation for CAD work

---

## ✅ Action Items

### Immediate (Today)
- [x] Document FreeCAD MCP deployment blocker
- [x] Create CadQuery deployment plan
- [x] Remove FreeCAD MCP from ~/.mcp.json
- [ ] Install CadQuery + MCP server
- [ ] Test headless CAD generation
- [ ] Commit documentation to git

### Short-Term (This Week)
- [ ] Integrate CadQuery with InvenTree BOM API
- [ ] Create ERPNext quotation preview generator
- [ ] Test STEP export quality
- [ ] Document CAD agent capabilities

### Long-Term (This Month)
- [ ] Build CAD template library (common enclosures, panels, etc.)
- [ ] Create automated assembly generation from BOMs
- [ ] Integrate with P&ID generator (2D + 3D combo)
- [ ] Train AI agent on CadQuery syntax

---

## 📚 Documentation Files

**Created:**
1. `~/CAD_OSS_MCP_RESEARCH_2025.md` (500+ lines)
   - Comprehensive CAD OSS comparison
   - MCP server analysis
   - Business value calculations

2. `~/FREECAD_MCP_DEPLOYMENT_ANALYSIS.md` (400+ lines)
   - FreeCAD GUI blocker analysis
   - CadQuery technical details
   - Integration architecture

3. `~/CAD_DEPLOYMENT_NEXT_STEPS.md` (This file - 350+ lines)
   - Step-by-step CadQuery deployment
   - Integration examples
   - Business use cases

**Existing:**
- `~/pid-generator/` - Professional P&ID generator (ISA-5.1-2024)
- `~/PHASE3_ERPNEXT_PROJECTS_COMPLETE.md` - ERPNext project management

**Configuration:**
- `~/.mcp.json` - FreeCAD removed, CadQuery pending

---

## 🎯 Summary

**Problem:** FreeCAD MCP requires GUI, cannot run on headless iac1 server

**Solution:** Deploy CadQuery MCP for pure Python headless CAD automation

**Status:**
- ✅ FreeCAD research complete
- ✅ Deployment blocker documented
- ✅ CadQuery recommended as alternative
- ⏳ CadQuery installation pending user approval
- ⏳ Integration with ERPNext/InvenTree pending

**Next Step:** Install CadQuery + MCP server (awaiting user confirmation)

---

**Version:** 1.0
**Status:** Ready for CadQuery deployment
**Last Updated:** October 18, 2025 01:50 UTC

🤖 Generated with [Claude Code](https://claude.com/claude-code)

**Made with ❤️ by INSA Automation Corp for Industrial DevSecOps**
