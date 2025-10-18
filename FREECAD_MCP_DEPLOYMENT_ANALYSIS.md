# FreeCAD MCP Deployment Analysis - HEADLESS SERVER LIMITATION

**Date:** October 18, 2025
**Server:** iac1 (100.100.101.1)
**Status:** ⚠️ DEPLOYMENT BLOCKED - Requires GUI

---

## 🚨 Critical Discovery: FreeCAD MCP Requires GUI

### Architecture Limitation

Both production FreeCAD MCP servers require a **running FreeCAD GUI instance** with XML-RPC server:

**contextform/freecad-mcp:**
- Requires FreeCAD 1.0+ GUI application running
- MCP server connects via XML-RPC to localhost:9875
- "AICopilot" workbench addon must be installed in FreeCAD GUI
- Cannot operate in headless/server mode

**neka-nat/freecad-mcp:**
- Same architecture - requires FreeCAD GUI
- "MCP Addon" workbench must be manually started
- "Start RPC Server" command in toolbar launches XML-RPC server
- No standalone headless mode

### Why This Blocks iac1 Deployment

```yaml
iac1 Server Constraints:
  - Headless Ubuntu Server 24.04 (no X11, no GUI)
  - SSH-only access (no display server)
  - Production monitoring server (not a workstation)
  - Cannot run FreeCAD GUI application
  - QT_QPA_PLATFORM=offscreen only works for CLI, not MCP server
```

**Conclusion:** FreeCAD MCP **CANNOT be deployed on iac1** as currently architected.

---

## ✅ What Was Successfully Installed

### FreeCAD 0.21.2 (Headless-Compatible)
```bash
Package: freecad
Version: 2:0.21.2+dfsg1~202407140123~ubuntu24.04.1
Location: /usr/bin/freecad
Python Module: /usr/lib/freecad-python3/lib
Size: 1.2GB (193 packages)
```

**FreeCAD Python API Works:**
```python
import sys
sys.path.append('/usr/lib/freecad-python3/lib')
import FreeCAD
print(FreeCAD.Version())  # Works!
# Output: ['0', '21', '2', '33771 (Git)', ...]
```

### FreeCAD MCP Python Package
```bash
Location: ~/mcp-servers/freecad-mcp/
Virtual Environment: venv (Python 3.12)
Package: freecad-mcp 0.1.13
Status: ✅ Installed successfully

Dependencies:
  - mcp 1.18.0 (Model Context Protocol)
  - FastMCP (MCP server framework)
  - httpx, pydantic, starlette, uvicorn
  - Total: 32 packages
```

### MCP Configuration
```json
File: ~/.mcp.json
Status: ✅ Configured (but won't work without GUI)

"freecad-mcp": {
  "transport": "stdio",
  "command": "/home/wil/mcp-servers/freecad-mcp/venv/bin/python",
  "args": ["-m", "freecad_mcp"],
  "env": {
    "QT_QPA_PLATFORM": "offscreen",
    "FREECAD_PATH": "/usr/bin/freecad"
  }
}
```

**Problem:** Server expects FreeCAD GUI on port 9875, will fail with connection error.

---

## 🔍 Research Findings: CAD OSS for Headless Servers

### Original Requirements
1. ✅ Open-source CAD software
2. ✅ Programmable API (Python)
3. ✅ MCP server for Claude Code integration
4. ❌ **Headless server deployment** (NOT met by FreeCAD MCP)

### Comprehensive CAD OSS Research

**Document:** `~/CAD_OSS_MCP_RESEARCH_2025.md` (500+ lines)

**Options Evaluated:**

| CAD Software | MCP Servers | Headless Mode | Server Deployment | Recommendation |
|--------------|-------------|---------------|-------------------|----------------|
| **FreeCAD** | 2 (contextform, neka-nat) | ❌ GUI Required | ❌ Blocked | Not suitable for iac1 |
| **CadQuery** | 1 (rishigundakaram) | ✅ Pure Python | ✅ Works | **BEST for iac1** |
| **OpenSCAD** | 2 (quellant, jhacksman) | ✅ CLI mode | ✅ Works | Alternative option |

---

## 🎯 Recommended Solution: CadQuery MCP

### Why CadQuery for iac1?

**CadQuery is a Python-based parametric CAD library:**
```python
import cadquery as cq

# Pure Python - no GUI required!
result = (cq.Workplane("XY")
    .box(60, 60, 10)
    .faces(">Z")
    .hole(5))

# Export STEP, STL, DXF, SVG
cq.exporters.export(result, "output.step")
```

**Advantages for Headless Server:**
1. ✅ **Pure Python library** - no GUI dependencies
2. ✅ **Headless operation** - perfect for iac1
3. ✅ **MCP server available** - rishigundakaram/cadquery-mcp-server
4. ✅ **OCCT kernel** - same as FreeCAD (industry-standard)
5. ✅ **STEP/IGES export** - manufacturing-ready files
6. ✅ **Scriptable** - code-based CAD (perfect for AI)
7. ✅ **Lightweight** - ~500MB vs FreeCAD's 1.2GB

**MCP Server:**
```bash
GitHub: rishigundakaram/cadquery-mcp-server
Status: Active (2024-2025)
Features: Full CAD operations via Claude Code
```

### Alternative: OpenSCAD

**OpenSCAD is also headless-compatible:**
```bash
# CLI-only CAD generation
openscad -o output.stl input.scad
```

**Trade-offs:**
- ✅ Headless CLI mode works
- ✅ 2 MCP servers available
- ⚠️ Own scripting language (not Python)
- ⚠️ Less flexible than CadQuery for parametric design

---

## 📊 Installation Comparison

### Current State (FreeCAD)
```yaml
Disk Space: 1.2GB
Packages: 193 (Qt5, PySide2, OCCT, etc.)
Dependencies: GUI libraries, X11 support
Python API: ✅ Works headless
MCP Server: ❌ Requires GUI
```

### Recommended (CadQuery)
```yaml
Disk Space: ~500MB (estimated)
Packages: Python only (cadquery, OCCT bindings)
Dependencies: No GUI required
Python API: ✅ Pure Python library
MCP Server: ✅ Fully headless
```

---

## 🚀 Next Steps: CadQuery Deployment Plan

### 1. Install CadQuery
```bash
# Create virtual environment
cd ~/mcp-servers
mkdir cadquery-mcp
cd cadquery-mcp
python3 -m venv venv
source venv/bin/activate

# Install CadQuery
pip install cadquery
pip install cadquery-server  # If using server mode

# Verify
python -c "import cadquery as cq; print('CadQuery version:', cq.__version__)"
```

### 2. Install CadQuery MCP Server
```bash
# Clone MCP server
git clone https://github.com/rishigundakaram/cadquery-mcp-server.git
cd cadquery-mcp-server

# Install dependencies
pip install -r requirements.txt

# Test
python server.py --help
```

### 3. Configure ~/.mcp.json
```json
{
  "cadquery-mcp": {
    "transport": "stdio",
    "command": "/home/wil/mcp-servers/cadquery-mcp/venv/bin/python",
    "args": ["/home/wil/mcp-servers/cadquery-mcp-server/server.py"],
    "env": {
      "PYTHONDONTWRITEBYTECODE": "1",
      "PYTHONUNBUFFERED": "1"
    },
    "_description": "CadQuery CAD automation for INSA - Pure Python parametric 3D CAD, STEP/IGES export, headless operation"
  }
}
```

### 4. Integration with ERPNext/InvenTree
```python
#!/usr/bin/env python3
"""Generate 3D CAD from InvenTree BOM using CadQuery"""

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

def generate_cad_from_bom(bom_data):
    """Generate 3D assembly from BOM data"""
    assembly = cq.Assembly()

    for item in bom_data:
        # Create part based on BOM specifications
        part_name = item.get("sub_part_detail", {}).get("name", "")

        # Example: Create enclosure for PLC
        if "PLC" in part_name:
            plc = (cq.Workplane("XY")
                .box(120, 80, 60)
                .faces(">Z")
                .hole(10))
            assembly.add(plc, name="PLC")

        # Add more part logic here...

    # Export STEP file
    assembly.save("output_assembly.step")
    return "output_assembly.step"

# Usage
bom = get_bom_from_inventree(200)
cad_file = generate_cad_from_bom(bom)
print(f"✓ Generated: {cad_file}")
```

---

## 📝 FreeCAD Deployment Options (For Reference)

### Option A: Deploy on Workstation (LU1)
```yaml
Workstation: 100.81.103.99 (LU1)
OS: Likely has GUI support
Strategy: Install FreeCAD + MCP addon on workstation
Access: Via Tailscale network from iac1
Trade-off: Requires workstation to be always on
```

### Option B: Docker with VNC
```dockerfile
FROM ubuntu:24.04

# Install FreeCAD + VNC
RUN apt-get update && \
    apt-get install -y freecad tightvncserver xfce4

# Start VNC server + FreeCAD
CMD vncserver && freecad
```
**Trade-off:** High overhead, complex, not ideal for automation

### Option C: Wait for Headless FreeCAD MCP
```yaml
Status: No headless fork exists (as of Oct 2025)
Likelihood: Low (architecture requires GUI)
Recommendation: Use CadQuery instead
```

---

## 💰 Business Impact Analysis

### Current P&ID Generator
```yaml
Location: ~/pid-generator/
Status: ✅ OPERATIONAL
Capabilities:
  - ISA-5.1-2024 compliant P&ID diagrams
  - SVG + DXF export
  - InvenTree BOM integration
  - Professional output (A3 landscape)
Limitation: 2D diagrams only (no 3D CAD models)
```

### Adding 3D CAD Capabilities (CadQuery)
```yaml
Value Proposition:
  - Generate 3D models from BOMs
  - STEP files for manufacturing
  - Technical drawings (2D projections)
  - Assembly visualizations
  - Enclosure design automation

Use Cases:
  1. Quote Generation: Auto-generate 3D previews for proposals
  2. Engineering Docs: STEP files for manufacturing partners
  3. Project Management: Visual assembly guides
  4. Training Materials: 3D exploded views

Time Savings: 50-65% (per research document)
Cost Savings: $4,500-9,000/year (20 projects/year)
```

---

## 🎯 Final Recommendation

### Immediate Action: Deploy CadQuery MCP

**Rationale:**
1. ✅ **Headless compatible** - works on iac1 server
2. ✅ **Pure Python** - integrates with existing Python MCP servers
3. ✅ **MCP server available** - proven Claude Code integration
4. ✅ **Industry-standard exports** - STEP, IGES, DXF, STL
5. ✅ **Lightweight** - half the disk space of FreeCAD
6. ✅ **Code-based CAD** - perfect for AI agent automation

**FreeCAD Status:**
- Keep installed (Python API still useful)
- Remove from ~/.mcp.json (won't work in headless mode)
- Document for future workstation deployment (if needed)

**Next Steps:**
1. Install CadQuery + MCP server
2. Test CAD generation from InvenTree BOMs
3. Integrate with ERPNext quotation workflow
4. Document CAD agent capabilities
5. Commit to git with full documentation

---

## 📚 Documentation Files

**Research:**
- `~/CAD_OSS_MCP_RESEARCH_2025.md` - Full comparison (500+ lines)

**This File:**
- `~/FREECAD_MCP_DEPLOYMENT_ANALYSIS.md` - Deployment blockers + solution

**MCP Config:**
- `~/.mcp.json` - FreeCAD configured (won't work), CadQuery pending

**Installation Logs:**
- FreeCAD 0.21.2: Successfully installed (1.2GB)
- freecad-mcp: Successfully installed (Python package)
- Status: GUI blocker discovered, CadQuery recommended

---

## 🤖 Integration Architecture (Proposed)

```
┌─────────────────────────────────────────────────────────────┐
│ Claude Code (AI Agent)                                      │
│ - Natural language CAD requests                             │
│ - ERPNext project integration                               │
│ - InvenTree BOM processing                                  │
└────────────┬────────────────────────────────────────────────┘
             │ MCP Protocol
             ▼
┌─────────────────────────────────────────────────────────────┐
│ CadQuery MCP Server (Headless on iac1)                     │
│ - Pure Python parametric CAD                                │
│ - STEP/IGES/DXF/STL export                                 │
│ - Assembly generation                                        │
└────────────┬────────────────────────────────────────────────┘
             │
             ├──────────────┐
             │              │
             ▼              ▼
┌──────────────────┐  ┌─────────────────────┐
│ InvenTree BOM    │  │ ERPNext Projects    │
│ - Part library   │  │ - Quotations        │
│ - BOMs           │  │ - Sales orders      │
│ - Specifications │  │ - Documentation     │
└──────────────────┘  └─────────────────────┘
             │              │
             ▼              ▼
┌─────────────────────────────────────────────────────────────┐
│ Output: 3D CAD Models                                       │
│ - STEP files (manufacturing)                                │
│ - Technical drawings (DXF)                                  │
│ - STL files (3D printing)                                   │
│ - Assembly visualizations (SVG)                             │
└─────────────────────────────────────────────────────────────┘
```

---

**Version:** 1.0
**Status:** ⚠️ FreeCAD MCP blocked, CadQuery recommended
**Last Updated:** October 18, 2025 01:45 UTC

🤖 Generated with [Claude Code](https://claude.com/claude-code)

**Made with ❤️ by INSA Automation Corp for Industrial DevSecOps**
