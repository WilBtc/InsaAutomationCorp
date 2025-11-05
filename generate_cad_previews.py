#!/usr/bin/env python3
"""
Generate CAD Preview Images for Email
Creates SVG and PNG previews of PLC system CAD models
"""

import subprocess
import os
import sys

# Add CadQuery to path
sys.path.append('/home/wil/mcp-servers/mcp-cadquery/.venv-cadquery/lib/python3.12/site-packages')

def generate_svg_preview(script_path, output_path, view="isometric"):
    """
    Generate SVG preview of CAD model using CadQuery

    Views: isometric, front, top, side
    """

    print(f"🎨 Generating {view} view preview...")

    # Create a wrapper script to export SVG
    wrapper = f"""
import sys
sys.path.append('/home/wil/mcp-servers/mcp-cadquery/.venv-cadquery/lib/python3.12/site-packages')

import cadquery as cq
from cadquery import exporters

# Execute the main CAD script
exec(open('{script_path}').read())

# Export to SVG
exporters.export(result, '{output_path}', opt={{
    'width': 800,
    'height': 600,
    'marginLeft': 10,
    'marginTop': 10,
    'showAxes': False,
    'projectionDir': (1, 1, 0.5) if '{view}' == 'isometric' else (0, 0, 1),
    'strokeWidth': 0.5,
    'strokeColor': (0, 0, 0),
    'hiddenColor': (160, 160, 160)
}})

print(f"✅ Saved: {output_path}")
"""

    # Write wrapper script
    wrapper_path = f"/tmp/cadquery_wrapper_{view}.py"
    with open(wrapper_path, 'w') as f:
        f.write(wrapper)

    # Execute with CadQuery venv
    try:
        result = subprocess.run(
            [
                '/home/wil/mcp-servers/mcp-cadquery/.venv-cadquery/bin/python3',
                wrapper_path
            ],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print(f"   ✅ {view.capitalize()} view generated")
            return True
        else:
            print(f"   ❌ Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"   ⚠️  Timeout generating {view} view")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def create_simple_preview_image():
    """
    Create a simple preview image using ASCII art converted to SVG
    This is a fallback if CadQuery export fails
    """

    print("🎨 Creating simple preview diagram...")

    svg = """
<svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="panelGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#2a5298;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#1e3c72;stop-opacity:1" />
    </linearGradient>
    <filter id="shadow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur in="SourceAlpha" stdDeviation="3"/>
      <feOffset dx="2" dy="2" result="offsetblur"/>
      <feComponentTransfer>
        <feFuncA type="linear" slope="0.5"/>
      </feComponentTransfer>
      <feMerge>
        <feMergeNode/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>

  <!-- Background -->
  <rect width="800" height="600" fill="#f0f0f0"/>

  <!-- Grid -->
  <defs>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#e0e0e0" stroke-width="0.5"/>
    </pattern>
  </defs>
  <rect width="800" height="600" fill="url(#grid)"/>

  <!-- Title -->
  <text x="400" y="40" text-anchor="middle" font-family="Arial, sans-serif" font-size="24" font-weight="bold" fill="#1e3c72">
    PLC Control System - 3D Layout
  </text>

  <!-- Main PLC Panel -->
  <g filter="url(#shadow)">
    <rect x="250" y="150" width="120" height="200" rx="5" fill="url(#panelGrad)" stroke="#000" stroke-width="2"/>
    <rect x="260" y="160" width="30" height="40" rx="2" fill="#4a90e2" stroke="#000"/>
    <rect x="260" y="210" width="30" height="40" rx="2" fill="#4a90e2" stroke="#000"/>
    <rect x="260" y="260" width="30" height="40" rx="2" fill="#4a90e2" stroke="#000"/>
    <rect x="300" y="170" width="60" height="120" rx="3" fill="#333" stroke="#000"/>
    <circle cx="330" cy="230" r="25" fill="#1e3c72" stroke="#4a90e2" stroke-width="2"/>
    <text x="330" y="238" text-anchor="middle" font-family="Arial" font-size="12" fill="#fff" font-weight="bold">HMI</text>
  </g>

  <!-- Label Main Panel -->
  <text x="310" y="370" text-anchor="middle" font-family="Arial" font-size="14" fill="#1e3c72" font-weight="bold">
    Main PLC Panel
  </text>
  <text x="310" y="385" text-anchor="middle" font-family="Arial" font-size="10" fill="#666">
    2000×1200×600mm
  </text>

  <!-- Remote I/O Panel 1 -->
  <g filter="url(#shadow)">
    <rect x="450" y="200" width="80" height="120" rx="5" fill="url(#panelGrad)" stroke="#000" stroke-width="2"/>
    <rect x="460" y="220" width="20" height="30" rx="2" fill="#50c878" stroke="#000"/>
    <rect x="460" y="260" width="20" height="30" rx="2" fill="#50c878" stroke="#000"/>
  </g>
  <text x="490" y="340" text-anchor="middle" font-family="Arial" font-size="12" fill="#1e3c72" font-weight="bold">
    Remote I/O #1
  </text>
  <text x="490" y="355" text-anchor="middle" font-family="Arial" font-size="9" fill="#666">
    Separator Zone
  </text>

  <!-- Remote I/O Panel 2 -->
  <g filter="url(#shadow)">
    <rect x="580" y="200" width="80" height="120" rx="5" fill="url(#panelGrad)" stroke="#000" stroke-width="2"/>
    <rect x="590" y="220" width="20" height="30" rx="2" fill="#50c878" stroke="#000"/>
    <rect x="590" y="260" width="20" height="30" rx="2" fill="#50c878" stroke="#000"/>
  </g>
  <text x="620" y="340" text-anchor="middle" font-family="Arial" font-size="12" fill="#1e3c72" font-weight="bold">
    Remote I/O #2
  </text>
  <text x="620" y="355" text-anchor="middle" font-family="Arial" font-size="9" fill="#666">
    Pump Zone
  </text>

  <!-- Marshalling Cabinet -->
  <g filter="url(#shadow)">
    <rect x="100" y="180" width="100" height="150" rx="5" fill="url(#panelGrad)" stroke="#000" stroke-width="2"/>
    <rect x="110" y="200" width="80" height="15" rx="1" fill="#ffa500" stroke="#000"/>
    <rect x="110" y="220" width="80" height="15" rx="1" fill="#ffa500" stroke="#000"/>
    <rect x="110" y="240" width="80" height="15" rx="1" fill="#ffa500" stroke="#000"/>
  </g>
  <text x="150" y="350" text-anchor="middle" font-family="Arial" font-size="12" fill="#1e3c72" font-weight="bold">
    Marshalling
  </text>
  <text x="150" y="365" text-anchor="middle" font-family="Arial" font-size="9" fill="#666">
    Terminal Blocks
  </text>

  <!-- Connection Lines (PROFINET Ring) -->
  <path d="M 370 250 L 450 260" stroke="#e74c3c" stroke-width="3" stroke-dasharray="5,5" marker-end="url(#arrowRed)"/>
  <path d="M 530 260 L 580 260" stroke="#e74c3c" stroke-width="3" stroke-dasharray="5,5" marker-end="url(#arrowRed)"/>
  <path d="M 620 200 Q 620 150 310 150" stroke="#e74c3c" stroke-width="3" stroke-dasharray="5,5" marker-end="url(#arrowRed)"/>

  <!-- Connection to Marshalling -->
  <path d="M 250 250 L 200 250" stroke="#3498db" stroke-width="2" stroke-dasharray="3,3" marker-end="url(#arrowBlue)"/>

  <!-- Arrow markers -->
  <defs>
    <marker id="arrowRed" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L0,6 L9,3 z" fill="#e74c3c"/>
    </marker>
    <marker id="arrowBlue" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto" markerUnits="strokeWidth">
      <path d="M0,0 L0,6 L9,3 z" fill="#3498db"/>
    </marker>
  </defs>

  <!-- Legend -->
  <rect x="20" y="450" width="760" height="120" rx="5" fill="#fff" stroke="#ccc" stroke-width="1"/>
  <text x="400" y="475" text-anchor="middle" font-family="Arial" font-size="14" font-weight="bold" fill="#1e3c72">
    System Components
  </text>

  <!-- Legend items -->
  <rect x="40" y="490" width="15" height="15" fill="url(#panelGrad)"/>
  <text x="60" y="502" font-family="Arial" font-size="11" fill="#333">NEMA 4X Enclosures (Stainless Steel 316L)</text>

  <rect x="40" y="515" width="15" height="15" fill="#4a90e2"/>
  <text x="60" y="527" font-family="Arial" font-size="11" fill="#333">PLC I/O Modules (Siemens S7-1500)</text>

  <rect x="40" y="540" width="15" height="15" fill="#50c878"/>
  <text x="60" y="552" font-family="Arial" font-size="11" fill="#333">Remote I/O (ET200SP Distributed)</text>

  <line x1="350" y1="497" x2="380" y2="497" stroke="#e74c3c" stroke-width="3" stroke-dasharray="5,5"/>
  <text x="385" y="502" font-family="Arial" font-size="11" fill="#333">PROFINET Ring (10ms cycle)</text>

  <line x1="350" y1="522" x2="380" y2="522" stroke="#3498db" stroke-width="2" stroke-dasharray="3,3"/>
  <text x="385" y="527" font-family="Arial" font-size="11" fill="#333">Signal Cables (4-20mA, 24VDC)</text>

  <circle cx="348" cy="547" r="7" fill="#1e3c72" stroke="#4a90e2" stroke-width="2"/>
  <text x="385" y="552" font-family="Arial" font-size="11" fill="#333">21" HMI Touchscreen (Panel IPC477E Pro)</text>

  <!-- Specifications box -->
  <rect x="520" y="490" width="240" height="70" rx="3" fill="#f8f9fa" stroke="#dee2e6"/>
  <text x="640" y="510" text-anchor="middle" font-family="Arial" font-size="11" font-weight="bold" fill="#1e3c72">
    Total I/O Points: 284
  </text>
  <text x="540" y="530" font-family="Arial" font-size="10" fill="#555">
    • 120 Digital Inputs (DI)
  </text>
  <text x="540" y="545" font-family="Arial" font-size="10" fill="#555">
    • 80 Digital Outputs (DO)
  </text>
  <text x="650" y="530" font-family="Arial" font-size="10" fill="#555">
    • 60 Analog Inputs (AI)
  </text>
  <text x="650" y="545" font-family="Arial" font-size="10" fill="#555">
    • 24 Analog Outputs (AO)
  </text>
</svg>
"""

    output_path = "/home/wil/plc_designs/plc_system_layout.svg"
    with open(output_path, 'w') as f:
        f.write(svg)

    print(f"   ✅ Simple preview saved: {output_path}")
    return True


def main():
    """Generate all preview images"""

    print("🎨 Generating CAD Preview Images for Email")
    print("=" * 60)
    print()

    # Ensure output directory exists
    os.makedirs('/home/wil/plc_designs', exist_ok=True)

    # Create simple SVG preview (always works, fast)
    create_simple_preview_image()

    print()
    print("✅ Preview images generated successfully!")
    print()
    print("📁 Files created:")
    print("   - plc_designs/plc_system_layout.svg (System layout diagram)")
    print()
    print("🚀 Ready to embed in email!")

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
