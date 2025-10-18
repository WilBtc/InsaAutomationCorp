# CAD Open Source Software + MCP Server Research for Claude Code Integration
**Research Date:** October 18, 2025
**Purpose:** Identify best OSS CAD solution with MCP server for INSA Automation Corp
**Goal:** AI-powered CAD engineering via Claude Code on iac1

---

## 🎯 Executive Summary

Based on comprehensive research, **3 primary CAD solutions** have existing MCP servers for Claude Code integration:

| CAD Software | MCP Server | Maturity | Best For | Recommendation |
|--------------|------------|----------|----------|----------------|
| **FreeCAD** | ✅ 2 servers | Production | Industrial automation, mechanical parts | ⭐⭐⭐⭐⭐ **BEST** |
| **CadQuery** | ✅ 1 server | Stable | Parametric scripting, automation | ⭐⭐⭐⭐ **EXCELLENT** |
| **OpenSCAD** | ✅ 2 servers | Active | Code-first modeling, 3D printing | ⭐⭐⭐ **GOOD** |

**Winner: FreeCAD** - Most mature ecosystem, dual MCP servers, industrial automation focus, headless operation.

---

## 🔬 Detailed Analysis

### 1. FreeCAD + MCP (RECOMMENDED ⭐⭐⭐⭐⭐)

**Overview:**
- Open-source parametric 3D CAD modeler
- Powerful Python-based scripting environment
- Widely used for product design, mechanical engineering, architecture
- **2 production-ready MCP servers available**

**MCP Servers Available:**

#### A. contextform/freecad-mcp (Most User-Friendly)
**GitHub:** https://github.com/contextform/freecad-mcp
**PyPI:** https://pypi.org/project/freecad-mcp/
**Status:** ✅ Production-ready, actively maintained

**Installation:**
```bash
# Option 1: NPM setup (easiest)
npm install -g freecad-mcp-setup@latest
npx freecad-mcp-setup setup

# Option 2: Manual Python
python -m pip install --user mcp
pip install freecad-mcp
```

**Capabilities:**
- **PartDesign (13 operations):** Pad, Revolution, Fillet, Chamfer, Holes, Patterns
- **Part (18 operations):** Primitives (Box, Cylinder, Sphere), Booleans (Union, Cut, Intersection), Transforms (Mirror, Scale, Rotate), Advanced shapes
- **Conversational AI:** Create 3D models using natural language with Claude Code
- **Workflow automation:** Automate CAD workflows through AI

**Example Usage:**
```
Claude Code: "Create a mechanical bracket with mounting holes"
→ FreeCAD MCP executes Python script
→ Generates 3D model with 4 M6 mounting holes
→ Exports to STEP/STL
```

#### B. neka-nat/freecad-mcp (Python-Native)
**GitHub:** https://github.com/neka-nat/freecad-mcp
**Status:** ✅ Actively maintained

**Installation:**
```bash
# Add to Claude Code MCP config
claude mcp add-json "freecad" '{"command":"uvx","args":["freecad-mcp"]}'
```

**Features:**
- Execute Python scripts directly in FreeCAD
- Create and edit objects programmatically
- Access FreeCAD parts library
- Control FreeCAD from Claude Desktop/Code
- Automation and integration of design tasks

**Technical Stack:**
- FreeCAD Python API (direct integration)
- FastMCP (MCP server framework)
- Python Socket Module (network communication)

**Headless Support:**
```bash
# Run FreeCAD headless (no GUI)
export QT_QPA_PLATFORM=offscreen
freecad --console script.py
```

**Why FreeCAD is Best for Industrial Automation:**
✅ Industry-standard for mechanical engineering
✅ STEP/IGES/STL export for manufacturing
✅ Assembly design capabilities
✅ Technical drawing generation
✅ Parametric modeling (design intent preservation)
✅ Python API access to all features
✅ Free, open-source, no licensing costs
✅ Large community, extensive documentation

**Use Cases for INSA:**
- Design custom control panels and enclosures
- Create mounting brackets for sensors/instruments
- Generate technical drawings for fabrication
- Model assemblies for installation planning
- Export CAD files for CNC machining
- Produce 3D visualizations for customer proposals

---

### 2. CadQuery + MCP (EXCELLENT ⭐⭐⭐⭐)

**Overview:**
- Python parametric CAD scripting framework
- Based on OCCT (Open CASCADE Technology)
- Code-first approach (no GUI required)
- Perfect for automation and server integration

**MCP Server:**

**GitHub:** https://github.com/rishigundakaram/cadquery-mcp-server
**LobeHub:** https://lobehub.com/mcp/rishigundakaram-cadquery-mcp-server
**Status:** ✅ Production-ready

**Installation:**
```bash
pip install cadquery
# Add to Claude Code config
# Point to server.py from repository
```

**Key Features:**
- Full CadQuery support for parametric 3D modeling
- Direct export to STL/STEP formats
- SVG generation for model inspection
- Natural language → CadQuery code via Claude
- ~85% executable success rate (2025 research)

**Technical Advantages:**
- **OCCT kernel** (more powerful than OpenSCAD's CGAL)
- NURBS, splines, surface sewing
- STL repair, STEP import/export
- Complex operations support
- Server-friendly (no GUI dependency)

**Example CadQuery Script:**
```python
import cadquery as cq

# Create mounting bracket
result = (cq.Workplane("XY")
    .box(50, 30, 5)  # Base plate
    .faces(">Z").workplane()
    .rect(40, 20, forConstruction=True)
    .vertices()
    .hole(5)  # M5 mounting holes
)

# Export
result.exportStep("bracket.step")
result.exportStl("bracket.stl")
```

**Integration with Claude Code:**
```
User: "Design a sensor mounting bracket for DIN rail"
Claude Code: Uses cadquery-mcp-server
→ Generates CadQuery Python code
→ Executes code, creates 3D model
→ Exports STEP file for manufacturing
```

**Recent Research (2025):**
- Commercial LLMs (Claude, Gemini) can translate natural language → CadQuery code
- Enhanced feedback loops boost success to ~85%
- Text-to-CadQuery paradigm emerging for CAD generation

**Why CadQuery for Automation:**
✅ Pure Python (easy scripting)
✅ No GUI required (perfect for servers)
✅ Version control friendly (code as CAD)
✅ Parametric by design
✅ Integration into CI/CD pipelines
✅ Scientific/engineering script use cases
✅ Reproducible designs

**Use Cases for INSA:**
- Automated generation of standard parts
- Parametric designs from specifications
- Integration into quotation system
- Generate CAD from BOM data
- Version-controlled engineering designs
- Batch production of similar parts

---

### 3. OpenSCAD + MCP (GOOD ⭐⭐⭐)

**Overview:**
- Script-only CAD program
- Code-based 3D modeling
- Popular for 3D printing
- Uses own scripting language (not Python natively)

**MCP Servers Available:**

#### A. quellant/openscad-mcp (Production-Ready)
**GitHub:** https://github.com/quellant/openscad-mcp
**Status:** ✅ Production-ready, scalable

**Features:**
- Headless OpenSCAD rendering (no GUI)
- Execute OpenSCAD code → generate PNG images
- Flexible camera control
- Cross-platform support
- Built with FastMCP
- Run directly from GitHub (no installation)

#### B. jhacksman/OpenSCAD-MCP-Server (AI-Powered)
**GitHub:** https://github.com/jhacksman/OpenSCAD-MCP-Server
**Status:** ✅ Active development

**Features:**
- AI image generation from text descriptions
- Multi-view image generation
- 3D reconstruction using CUDA Multi-View Stereo
- Remote processing capabilities
- OpenSCAD integration for parametric models
- Built with Python MCP SDK

**Python Integration:**

**PythonSCAD** (Merged into OpenSCAD core - February 2025)
- Core devs merged PythonSCAD into OpenSCAD
- Python functionality now available to wider audience

**AnchorScad + PythonOpenScad**
- Python libraries for 3D printing models
- GNU LGPL license
- Richer API than pure OpenSCAD

**Example OpenSCAD Script:**
```openscad
// Sensor mounting bracket
difference() {
    cube([50, 30, 5]);  // Base
    translate([10, 10, -1]) cylinder(h=7, r=2.5);  // Hole 1
    translate([40, 10, -1]) cylinder(h=7, r=2.5);  // Hole 2
    translate([10, 20, -1]) cylinder(h=7, r=2.5);  // Hole 3
    translate([40, 20, -1]) cylinder(h=7, r=2.5);  // Hole 4
}
```

**Why OpenSCAD:**
✅ Code-first approach (version control friendly)
✅ Popular for 3D printing
✅ Parametric designs
✅ Fast iteration
⚠️ Own language (not Python)
⚠️ Less suitable for complex industrial CAD

**Use Cases for INSA:**
- Rapid prototyping for 3D printing
- Simple brackets and fixtures
- Teaching/training materials
- Quick design iterations

---

## 📊 Comparison Matrix

| Feature | FreeCAD | CadQuery | OpenSCAD |
|---------|---------|----------|----------|
| **MCP Servers** | 2 (mature) | 1 (stable) | 2 (active) |
| **Python Native** | ✅ Full API | ✅ Pure Python | ⚠️ Wrapper needed |
| **GUI Available** | ✅ Yes | ❌ Code-only | ✅ Yes |
| **Headless Mode** | ✅ Yes | ✅ Native | ✅ Yes |
| **Industrial CAD** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ |
| **Parametric** | ✅ Yes | ✅ Yes | ✅ Yes |
| **STEP/IGES Export** | ✅ Yes | ✅ Yes | ❌ No |
| **Assembly Design** | ✅ Yes | ⚠️ Limited | ❌ No |
| **Technical Drawings** | ✅ Yes | ⚠️ Limited | ❌ No |
| **Learning Curve** | Medium | Low (if Python) | Low |
| **Community Size** | Large | Medium | Large |
| **Manufacturing Ready** | ✅ Yes | ✅ Yes | ⚠️ 3D print focus |
| **Server Integration** | ✅ Excellent | ✅ Excellent | ✅ Good |
| **Automation** | ✅ Excellent | ✅ Excellent | ✅ Good |

---

## 🏗️ Integration Architecture for INSA

### Recommended: FreeCAD + MCP on iac1

```yaml
Stack:
  CAD Engine: FreeCAD 0.21+ (headless)
  MCP Server: contextform/freecad-mcp
  Integration: Claude Code on iac1
  Storage: ~/freecad-projects/
  Export: STEP, IGES, STL, PDF (drawings)

Workflow:
  1. User request via Claude Code
     "Design a control panel enclosure for PLC"

  2. Claude Code → FreeCAD MCP
     - Generates Python script
     - Executes in FreeCAD headless
     - Creates 3D model

  3. Export outputs
     - STEP file for CAD editing
     - STL file for 3D printing
     - PDF technical drawing
     - PNG preview image

  4. Integration with existing systems
     - Link to ERPNext project (erpnext_create_project)
     - Attach to quotation (erpnext_create_quotation)
     - Add to InvenTree BOM (inventree_create_bom)
     - Include in P&ID diagrams (existing generator)

MCP Tools Created:
  - freecad_create_model(description, parameters)
  - freecad_export_step(model_id, output_path)
  - freecad_export_stl(model_id, output_path)
  - freecad_generate_drawing(model_id, views)
  - freecad_modify_model(model_id, changes)
  - freecad_create_assembly(parts_list)
```

### Alternative: CadQuery for Pure Automation

```yaml
Stack:
  CAD Engine: CadQuery (pure Python)
  MCP Server: rishigundakaram/cadquery-mcp-server
  Integration: Claude Code on iac1
  Storage: ~/cadquery-designs/
  Export: STEP, STL, SVG

Best For:
  - Automated part generation
  - Parametric designs from specifications
  - Version-controlled CAD (Git-friendly)
  - CI/CD integration
  - Batch production of parts
```

---

## 🚀 Installation Guide for iac1

### Option 1: FreeCAD + MCP (Recommended)

```bash
# 1. Install FreeCAD
sudo add-apt-repository ppa:freecad-maintainers/freecad-stable
sudo apt update
sudo apt install freecad freecad-python3

# 2. Install MCP server
cd ~/mcp-servers
mkdir freecad-mcp
cd freecad-mcp
python3 -m venv venv
source venv/bin/activate
pip install freecad-mcp

# 3. Configure Claude Code MCP
# Add to ~/.mcp.json:
{
  "freecad-mcp": {
    "transport": "stdio",
    "command": "/home/wil/mcp-servers/freecad-mcp/venv/bin/python",
    "args": ["-m", "freecad_mcp"],
    "env": {
      "FREECAD_PATH": "/usr/bin/freecad",
      "QT_QPA_PLATFORM": "offscreen"
    },
    "_description": "FreeCAD MCP for AI-powered 3D CAD design and automation"
  }
}

# 4. Test installation
freecad --version
python -c "import freecad_mcp; print('MCP installed')"
```

### Option 2: CadQuery + MCP (Alternative)

```bash
# 1. Install CadQuery
cd ~/mcp-servers
mkdir cadquery-mcp
cd cadquery-mcp
python3 -m venv venv
source venv/bin/activate
pip install cadquery

# 2. Clone MCP server
git clone https://github.com/rishigundakaram/cadquery-mcp-server.git
cd cadquery-mcp-server
pip install -r requirements.txt

# 3. Configure Claude Code MCP
# Add to ~/.mcp.json:
{
  "cadquery-mcp": {
    "transport": "stdio",
    "command": "/home/wil/mcp-servers/cadquery-mcp/venv/bin/python",
    "args": ["/home/wil/mcp-servers/cadquery-mcp/cadquery-mcp-server/server.py"],
    "env": {
      "PYTHONUNBUFFERED": "1"
    },
    "_description": "CadQuery MCP for parametric CAD scripting and automation"
  }
}

# 4. Test installation
python -c "import cadquery as cq; print(f'CadQuery {cq.__version__} installed')"
```

---

## 💼 Business Value for INSA Automation

### Use Cases

**1. Quotation Support**
- Auto-generate 3D CAD models for proposals
- Create technical drawings for customer review
- Export CAD files for customer engineering review
- Integrate with ERPNext quotation system

**2. Engineering Documentation**
- Produce manufacturing drawings
- Generate assembly instructions
- Create installation guides
- Document as-built configurations

**3. Product Development**
- Design custom control panels
- Create sensor mounting solutions
- Develop specialized fixtures
- Model complete installations

**4. Manufacturing Support**
- Export STEP files for CNC machining
- Generate STL files for 3D printing
- Produce DXF files for laser cutting
- Create technical specifications

**5. Customer Collaboration**
- Share 3D models for approval
- Provide editable CAD files
- Generate photorealistic renderings
- Create interactive 3D PDFs

### ROI Calculation

**Current Process:**
- Manual CAD design: 4-8 hours per project
- Engineer cost: $75/hour
- Cost per design: $300-600

**With AI CAD (FreeCAD + MCP):**
- AI-assisted design: 1-2 hours per project
- Engineer review: 0.5-1 hour
- Cost per design: $112-225
- **Savings: 50-65% time reduction**

**Annual Impact (20 projects/year):**
- Time saved: 60-120 hours
- Cost saved: $4,500-9,000
- Additional value: Faster quotes, better customer experience

---

## 🎯 Recommendation

### Primary: FreeCAD + contextform/freecad-mcp

**Rationale:**
1. ✅ Most mature MCP server ecosystem (2 production servers)
2. ✅ Industry-standard CAD capabilities
3. ✅ Full parametric modeling support
4. ✅ STEP/IGES export for manufacturing
5. ✅ Technical drawing generation
6. ✅ Assembly design capabilities
7. ✅ Headless operation for server deployment
8. ✅ Large community and extensive documentation
9. ✅ Perfect for industrial automation focus
10. ✅ Free, open-source, no licensing costs

**Implementation Plan:**
- Phase 1: Install FreeCAD + MCP server on iac1
- Phase 2: Integrate with ERPNext project system
- Phase 3: Connect to InvenTree for BOM-driven CAD
- Phase 4: Automate CAD generation for quotations
- Phase 5: Train team on AI-assisted CAD workflows

### Secondary: CadQuery (for specific automation)

**When to Use:**
- Pure automation tasks (no GUI needed)
- Parametric part generation
- Integration into CI/CD pipelines
- Version-controlled designs
- Batch production of similar parts

---

## 📚 References

**FreeCAD MCP Servers:**
- https://github.com/contextform/freecad-mcp
- https://github.com/neka-nat/freecad-mcp
- https://lobehub.com/mcp/contextform-freecad-mcp
- https://mcpmarket.com/server/freecad

**CadQuery MCP Server:**
- https://github.com/rishigundakaram/cadquery-mcp-server
- https://lobehub.com/mcp/rishigundakaram-cadquery-mcp-server
- https://github.com/CadQuery/cadquery

**OpenSCAD MCP Servers:**
- https://github.com/quellant/openscad-mcp
- https://github.com/jhacksman/OpenSCAD-MCP-Server

**General MCP CAD Resources:**
- https://snyk.io/articles/9-mcp-servers-for-computer-aided-drafting-cad-with-ai/
- https://www.datacamp.com/blog/top-mcp-servers-and-clients

**Research Papers:**
- Text-to-CadQuery: https://arxiv.org/html/2505.06507v1

---

**Prepared by:** Claude Code (INSA Automation DevSecOps)
**Date:** October 18, 2025
**Status:** ✅ RESEARCH COMPLETE
**Next Step:** Install FreeCAD + MCP on iac1

🤖 Generated with [Claude Code](https://claude.com/claude-code)

**Version:** 1.0
**Classification:** Internal Research - INSA Automation Corp
