#!/usr/bin/env python3
"""
Send Demo P&ID Diagram via Email with PNG Image
Sends PNG embedded + SVG/DXF as attachments to w.aroca@insaing.com
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime
import base64

# Email configuration
FROM_EMAIL = "noreply@iac1"
TO_EMAIL = "w.aroca@insaing.com"
SMTP_SERVER = "localhost"
SMTP_PORT = 25

# File paths
PNG_FILE = "/home/wil/pid-generator/Industrial_Process_Control_System_PID.png"
SVG_FILE = "/home/wil/pid-generator/Industrial_Process_Control_System_PID.svg"
DXF_FILE = "/home/wil/pid-generator/Industrial_Process_Control_System_PID.dxf"
JSON_FILE = "/home/wil/pid-generator/component_list.json"

def create_email():
    """Create email with embedded PNG and attachments"""

    # Create message
    msg = MIMEMultipart('related')
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL
    msg['Subject'] = "Demo P&ID Diagram - Industrial Process Control System (Updated)"

    # Create alternative part for HTML
    msg_alternative = MIMEMultipart('alternative')
    msg.attach(msg_alternative)

    # Read PNG and encode as base64 for embedding
    with open(PNG_FILE, 'rb') as f:
        png_data = base64.b64encode(f.read()).decode()

    # Email body with embedded PNG
    body = f"""
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .content {{
            padding: 20px;
            background-color: #f4f4f4;
        }}
        .section {{
            background-color: white;
            margin: 20px 0;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .diagram {{
            text-align: center;
            margin: 20px 0;
            padding: 20px;
            background-color: white;
            border: 2px solid #3498db;
            border-radius: 5px;
        }}
        .diagram img {{
            max-width: 100%;
            height: auto;
            border: 1px solid #ccc;
        }}
        .component-list {{
            background-color: #ecf0f1;
            padding: 15px;
            border-left: 4px solid #3498db;
            margin: 10px 0;
        }}
        .footer {{
            background-color: #34495e;
            color: white;
            padding: 20px;
            text-align: center;
            margin-top: 20px;
        }}
        h1 {{ color: white; margin: 0; }}
        h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h3 {{ color: #34495e; }}
        ul {{ list-style-type: none; padding-left: 0; }}
        li {{ padding: 5px 0; }}
        li:before {{ content: "✓ "; color: #27ae60; font-weight: bold; }}
        .highlight {{ color: #e74c3c; font-weight: bold; }}
        .info {{ color: #3498db; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏭 Demo P&ID Diagram</h1>
        <p>Industrial Process Control System - Phase 3</p>
        <p style="font-size: 14px; margin-top: 10px;">✅ Updated: PNG Image Included</p>
    </div>

    <div class="content">
        <div class="section">
            <h2>📊 P&ID Diagram Preview</h2>
            <p>Below is the generated P&ID (Piping and Instrumentation Diagram) for the demo industrial control system:</p>
        </div>

        <div class="diagram">
            <h3>Industrial Process Control System</h3>
            <img src="data:image/png;base64,{png_data}" alt="P&ID Diagram" />
            <p style="margin-top: 15px; color: #7f8c8d; font-size: 12px;">
                Click image to view full size • High-resolution PNG (159 KB)
            </p>
        </div>

        <div class="section">
            <h2>📎 Attached Files</h2>
            <p>This email includes 4 file attachments for different use cases:</p>
            <ul>
                <li><strong class="highlight">Industrial_Process_Control_System_PID.png</strong> (159 KB)<br>
                    → High-resolution PNG image (2400px height)<br>
                    → Universal format for viewing and printing</li>

                <li><strong class="highlight">Industrial_Process_Control_System_PID.svg</strong> (9.1 KB)<br>
                    → SVG vector format (scalable, no quality loss)<br>
                    → Open with: Firefox, Chrome, Inkscape, Adobe Illustrator</li>

                <li><strong class="highlight">Industrial_Process_Control_System_PID.dxf</strong> (18.8 KB)<br>
                    → DXF CAD format for engineering software<br>
                    → Open with: AutoCAD, QCAD, LibreCAD, FreeCAD</li>

                <li><strong class="highlight">component_list.json</strong> (2.6 KB)<br>
                    → Component data in JSON format<br>
                    → Complete specifications and connections</li>
            </ul>
        </div>

        <div class="section">
            <h2>🎯 System Components</h2>
            <div class="component-list">
                <h3>Control System (2 components)</h3>
                <ul>
                    <li><strong>PLC1:</strong> Siemens S7-1200 PLC - Main controller CPU 1214C DC/DC/DC</li>
                    <li><strong>HMI1:</strong> Weintek HMI 7-inch Touchscreen - Operator interface panel</li>
                </ul>

                <h3>Transmitters (4 components)</h3>
                <ul>
                    <li><strong>TT-101:</strong> Temperature Transmitter PT100 4-20mA - Process temperature</li>
                    <li><strong>TT-102:</strong> Temperature Transmitter PT100 4-20mA - Return temperature</li>
                    <li><strong>PT-101:</strong> Pressure Transmitter 0-10 Bar 4-20mA - Line pressure</li>
                    <li><strong>FT-101:</strong> Flow Transmitter Electromagnetic DN50 - Main flow measurement</li>
                </ul>

                <h3>Valves (3 components)</h3>
                <ul>
                    <li><strong>CV-101:</strong> Control Valve DN50 PN16 - Flow control (pneumatic actuated)</li>
                    <li><strong>CV-102:</strong> Control Valve DN40 PN16 - Return flow control</li>
                    <li><strong>SV-101:</strong> Solenoid Valve 24VDC 2-Way DN25 - Emergency shutoff</li>
                </ul>

                <h3>Equipment (1 component)</h3>
                <ul>
                    <li><strong>P-101:</strong> Centrifugal Pump 3HP 1450 RPM - Main circulation pump</li>
                </ul>
            </div>
        </div>

        <div class="section">
            <h2>🔌 Connections</h2>
            <p><strong>Total Connections:</strong> 10</p>

            <h3>Signal Lines (Blue Dashed - 7 connections):</h3>
            <div class="component-list">
                <p>4-20mA analog signals for instrumentation:</p>
                <ul>
                    <li>TT-101 → PLC1 (Temperature input)</li>
                    <li>TT-102 → PLC1 (Temperature input)</li>
                    <li>PT-101 → PLC1 (Pressure input)</li>
                    <li>FT-101 → PLC1 (Flow input)</li>
                    <li>PLC1 → CV-101 (Control output)</li>
                    <li>PLC1 → CV-102 (Control output)</li>
                    <li>PLC1 → SV-101 (Control output)</li>
                </ul>
            </div>

            <h3>Electric Lines (Green Dotted - 1 connection):</h3>
            <div class="component-list">
                <p>Communication and power:</p>
                <ul>
                    <li>PLC1 → HMI1 (Ethernet/Serial communication)</li>
                </ul>
            </div>

            <h3>Process Lines (Black Solid - 2 connections):</h3>
            <div class="component-list">
                <p>Material flow through piping:</p>
                <ul>
                    <li>P-101 → CV-101 (Main flow path)</li>
                    <li>P-101 → SV-101 (Emergency shutoff path)</li>
                </ul>
            </div>
        </div>

        <div class="section">
            <h2>✨ Features</h2>
            <ul>
                <li><strong>ISA-5.1 Compliant:</strong> Industry-standard symbols and conventions</li>
                <li><strong>Professional Quality:</strong> A3 size, title blocks, legends</li>
                <li><strong>Multiple Formats:</strong> PNG (universal), SVG (scalable), DXF (CAD), JSON (data)</li>
                <li><strong>Intelligent Automation:</strong> Auto-component detection, auto-connections</li>
                <li><strong>InvenTree Integration:</strong> Direct BOM import from inventory system</li>
            </ul>
        </div>

        <div class="section">
            <h2>🚀 How to Use the Attached Files</h2>

            <h3>View/Print the Diagram:</h3>
            <ol>
                <li>The PNG image is embedded above and attached to this email</li>
                <li>Download the PNG attachment for high-resolution viewing</li>
                <li>Print directly from email or open PNG in image viewer</li>
            </ol>

            <h3>Edit in CAD Software:</h3>
            <ol>
                <li>Download the DXF attachment</li>
                <li>Open in AutoCAD, QCAD, LibreCAD, or FreeCAD</li>
                <li>Edit on proper layers (INSTRUMENTS, SIGNALS, PROCESS, etc.)</li>
                <li>Export to production drawings</li>
            </ol>

            <h3>Scalable Vector Graphics:</h3>
            <ol>
                <li>Download the SVG attachment</li>
                <li>Open in web browser or vector graphics software</li>
                <li>Zoom infinitely without quality loss</li>
            </ol>
        </div>

        <div class="section">
            <h2>📚 Documentation</h2>
            <p>Complete documentation available on server iac1 (100.100.101.1):</p>
            <ul>
                <li><strong>User Guide:</strong> ~/pid-generator/README.md</li>
                <li><strong>Implementation Report:</strong> ~/PID_GENERATOR_COMPLETE.md</li>
                <li><strong>Phase 3 Summary:</strong> ~/PHASE3_COMPLETE.md</li>
            </ul>
        </div>
    </div>

    <div class="footer">
        <p><strong>INSA Automation Corp</strong><br>
        Industrial Automation Solutions</p>
        <p>Server: iac1 (100.100.101.1)<br>
        Contact: w.aroca@insaing.com</p>
        <p style="font-size: 12px; margin-top: 15px;">
        🤖 Generated with Claude Code (INSA Automation DevSecOps)<br>
        Phase 3 - P&ID Diagram Generator - October 17, 2025
        </p>
    </div>
</body>
</html>
"""

    msg_alternative.attach(MIMEText(body, 'html'))

    # Attach PNG file
    with open(PNG_FILE, 'rb') as f:
        png_part = MIMEImage(f.read(), name="Industrial_Process_Control_System_PID.png")
        png_part.add_header('Content-Disposition', 'attachment', filename="Industrial_Process_Control_System_PID.png")
        msg.attach(png_part)

    # Attach SVG file
    with open(SVG_FILE, 'rb') as f:
        svg_part = MIMEBase('image', 'svg+xml')
        svg_part.set_payload(f.read())
        encoders.encode_base64(svg_part)
        svg_part.add_header('Content-Disposition', 'attachment', filename="Industrial_Process_Control_System_PID.svg")
        msg.attach(svg_part)

    # Attach DXF file
    with open(DXF_FILE, 'rb') as f:
        dxf_part = MIMEBase('application', 'octet-stream')
        dxf_part.set_payload(f.read())
        encoders.encode_base64(dxf_part)
        dxf_part.add_header('Content-Disposition', 'attachment', filename="Industrial_Process_Control_System_PID.dxf")
        msg.attach(dxf_part)

    # Attach JSON file
    with open(JSON_FILE, 'rb') as f:
        json_part = MIMEBase('application', 'json')
        json_part.set_payload(f.read())
        encoders.encode_base64(json_part)
        json_part.add_header('Content-Disposition', 'attachment', filename="component_list.json")
        msg.attach(json_part)

    return msg

def send_email():
    """Send email via local SMTP server"""

    print("=" * 70)
    print("Sending Demo P&ID via Email (PNG + Attachments)")
    print("=" * 70)
    print()

    # Create email
    print("Creating email with embedded PNG and attachments...")
    msg = create_email()

    # Send email
    print(f"Connecting to SMTP server {SMTP_SERVER}:{SMTP_PORT}...")

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        print(f"Sending email to {TO_EMAIL}...")
        server.send_message(msg)
        server.quit()

        print()
        print("=" * 70)
        print("✓ Email Sent Successfully!")
        print("=" * 70)
        print()
        print(f"To: {TO_EMAIL}")
        print(f"Subject: Demo P&ID Diagram - Industrial Process Control System (Updated)")
        print()
        print("Embedded Image:")
        print(f"  • PNG diagram embedded in email body")
        print()
        print("Attachments:")
        print(f"  1. Industrial_Process_Control_System_PID.png ({os.path.getsize(PNG_FILE) / 1024:.1f} KB)")
        print(f"  2. Industrial_Process_Control_System_PID.svg ({os.path.getsize(SVG_FILE) / 1024:.1f} KB)")
        print(f"  3. Industrial_Process_Control_System_PID.dxf ({os.path.getsize(DXF_FILE) / 1024:.1f} KB)")
        print(f"  4. component_list.json ({os.path.getsize(JSON_FILE) / 1024:.1f} KB)")
        print()
        print("=" * 70)

        return 0

    except Exception as e:
        print()
        print("=" * 70)
        print("❌ Error sending email!")
        print("=" * 70)
        print(f"Error: {e}")
        print()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(send_email())
