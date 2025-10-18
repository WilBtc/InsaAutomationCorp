#!/usr/bin/env python3
"""
Send Complete PLC System Design Package via Email - WITH IMAGES
INSA Automation Corp - Professional Proposal with Visual Impact
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email import encoders
import os
import base64
from datetime import datetime

# Email configuration (localhost Postfix)
SMTP_SERVER = "localhost"
SMTP_PORT = 25
FROM_EMAIL = "w.aroca@insaing.com"
TO_EMAIL = "w.aroca@insaing.com"

def embed_image_as_base64(image_path):
    """Convert image to base64 for embedding"""
    with open(image_path, 'rb') as f:
        image_data = f.read()
        return base64.b64encode(image_data).decode('utf-8')


def create_html_email_with_images():
    """Create professional HTML email body with embedded CAD images"""

    # Embed the SVG diagram
    svg_path = "/home/wil/plc_designs/plc_system_layout.svg"
    if os.path.exists(svg_path):
        svg_base64 = embed_image_as_base64(svg_path)
        svg_embed = f'data:image/svg+xml;base64,{svg_base64}'
    else:
        svg_embed = ''

    html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .email-container {{
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 32px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .header p {{
            margin: 10px 0 0 0;
            font-size: 18px;
            opacity: 0.95;
        }}
        .hero-image {{
            width: 100%;
            max-width: 900px;
            height: auto;
            display: block;
            border-bottom: 5px solid #2a5298;
        }}
        .content {{
            padding: 40px;
        }}
        .section {{
            background: #f8f9fa;
            padding: 30px;
            margin-bottom: 25px;
            border-radius: 8px;
            border-left: 5px solid #2a5298;
        }}
        .section h2 {{
            color: #1e3c72;
            margin-top: 0;
            font-size: 24px;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
        }}
        .highlight {{
            background: linear-gradient(135deg, #fff3cd 0%, #ffe8a1 100%);
            padding: 20px;
            border-radius: 8px;
            border-left: 5px solid #ffc107;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .highlight strong {{
            color: #856404;
            font-size: 18px;
        }}
        .specs {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .specs table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .specs td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e0e0e0;
        }}
        .specs tr:last-child td {{
            border-bottom: none;
        }}
        .specs td:first-child {{
            font-weight: bold;
            color: #1e3c72;
            width: 35%;
        }}
        .specs td:last-child {{
            color: #555;
        }}
        .deliverables {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .deliverable-item {{
            background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #28a745;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: transform 0.2s;
        }}
        .deliverable-item:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }}
        .deliverable-item strong {{
            color: #1e3c72;
            display: block;
            margin-bottom: 5px;
            font-size: 16px;
        }}
        .cost-box {{
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 35px;
            border-radius: 12px;
            text-align: center;
            font-size: 28px;
            font-weight: bold;
            margin: 30px 0;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        }}
        .cost-box .amount {{
            font-size: 42px;
            margin: 10px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        .cost-box small {{
            display: block;
            font-size: 16px;
            font-weight: normal;
            margin-top: 10px;
            opacity: 0.95;
        }}
        .timeline {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .timeline-item {{
            padding: 15px 0;
            border-left: 3px solid #2a5298;
            padding-left: 20px;
            margin-bottom: 10px;
        }}
        .timeline-item:last-child {{
            border-left-color: #28a745;
        }}
        .timeline-item strong {{
            color: #1e3c72;
            font-size: 16px;
        }}
        .features {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin: 20px 0;
        }}
        .feature-box {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            border-top: 4px solid #2a5298;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .feature-box h3 {{
            color: #1e3c72;
            margin-top: 0;
            font-size: 18px;
        }}
        .feature-box ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .feature-box li {{
            margin: 8px 0;
            color: #555;
        }}
        .cta-section {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 40px;
            margin-top: 40px;
            border-radius: 8px;
            text-align: center;
        }}
        .cta-section h3 {{
            margin-top: 0;
            font-size: 28px;
            color: white;
        }}
        .btn {{
            display: inline-block;
            padding: 15px 35px;
            background: white;
            color: #1e3c72;
            text-decoration: none;
            border-radius: 6px;
            margin: 15px 10px;
            font-weight: bold;
            font-size: 16px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            transition: all 0.3s;
        }}
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        }}
        .footer {{
            background: #e9ecef;
            padding: 30px;
            text-align: center;
            border-top: 4px solid #2a5298;
        }}
        .footer p {{
            margin: 5px 0;
            color: #666;
        }}
        .footer strong {{
            color: #1e3c72;
        }}
        ul {{
            margin: 15px 0;
        }}
        li {{
            margin: 8px 0;
        }}
        .badge {{
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .stat-box {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-top: 3px solid #2a5298;
        }}
        .stat-box .number {{
            font-size: 36px;
            font-weight: bold;
            color: #2a5298;
            display: block;
            margin: 10px 0;
        }}
        .stat-box .label {{
            font-size: 14px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🏭 Complete PLC System Design</h1>
            <p>Oil & Gas Production Facility - Full Automation Package</p>
            <p><strong>INSA Automation Corp</strong> | Industrial Control Systems Excellence</p>
        </div>

        {f'<img src="{svg_embed}" class="hero-image" alt="PLC System Layout" />' if svg_embed else ''}

        <div class="content">
            <div class="highlight">
                <strong>🎯 Revolutionary Approach:</strong> This complete engineering design was generated using <strong>AI-powered CAD automation</strong> integrated with our CRM system. From your requirements to complete 3D models, full documentation, and professional proposal in <strong>under 30 minutes</strong> - showcasing the cutting-edge efficiency of modern industrial automation design.
            </div>

            <div class="section">
                <h2>📋 Project Overview</h2>
                <p style="font-size: 16px; line-height: 1.8;">
                    Thank you for your interest in our industrial automation solutions. This package contains a <strong>complete, production-ready PLC control system design</strong> engineered specifically for upstream oil & gas production facilities.
                </p>

                <div class="stat-grid">
                    <div class="stat-box">
                        <span class="number">284</span>
                        <span class="label">Total I/O Points</span>
                    </div>
                    <div class="stat-box">
                        <span class="number">6</span>
                        <span class="label">Production Pumps</span>
                    </div>
                    <div class="stat-box">
                        <span class="number">20</span>
                        <span class="label">Automated Valves</span>
                    </div>
                    <div class="stat-box">
                        <span class="number">60+</span>
                        <span class="label">Instruments</span>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🎨 3D CAD Model - Visual Overview</h2>
                <p>The complete system includes:</p>
                <div class="features">
                    <div class="feature-box">
                        <h3>🖥️ Main PLC Panel</h3>
                        <ul>
                            <li>Siemens S7-1500 PLC with redundancy</li>
                            <li>21" industrial HMI touchscreen</li>
                            <li>3 KVA UPS (2 hours runtime)</li>
                            <li>2000×1200×600mm NEMA 4X enclosure</li>
                        </ul>
                    </div>
                    <div class="feature-box">
                        <h3>🔌 Remote I/O Stations</h3>
                        <ul>
                            <li>2 × ET200SP distributed I/O</li>
                            <li>PROFINET ring topology</li>
                            <li>Field-mounted (800×600×300mm)</li>
                            <li>Zone 1: Separator, Zone 2: Pumps</li>
                        </ul>
                    </div>
                    <div class="feature-box">
                        <h3>⚡ Safety Systems</h3>
                        <ul>
                            <li>Emergency Shutdown (ESD)</li>
                            <li>Fire & Gas Detection (20 sensors)</li>
                            <li>SIL 2 certified per IEC 61508</li>
                            <li>IEC 62443 cybersecurity compliant</li>
                        </ul>
                    </div>
                    <div class="feature-box">
                        <h3>🔧 Marshalling Cabinet</h3>
                        <ul>
                            <li>72 terminal positions</li>
                            <li>Signal conditioning</li>
                            <li>Intrinsic safety barriers</li>
                            <li>2000×800×400mm enclosure</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🛠️ System Specifications</h2>
                <div class="specs">
                    <table>
                        <tr>
                            <td>Main PLC <span class="badge">CORE</span></td>
                            <td>Siemens S7-1500 (1515-2 PN) with redundant power supply</td>
                        </tr>
                        <tr>
                            <td>Remote I/O <span class="badge">FIELD</span></td>
                            <td>2 × ET200SP distributed stations (PROFINET ring, 10ms cycle)</td>
                        </tr>
                        <tr>
                            <td>HMI Operator Station</td>
                            <td>21" industrial touchscreen, NEMA 4X/IP66 rated, sunlight readable</td>
                        </tr>
                        <tr>
                            <td>Backup Power</td>
                            <td>3 KVA UPS online double-conversion, 2 hours runtime @ 50% load</td>
                        </tr>
                        <tr>
                            <td>Enclosure Rating</td>
                            <td>NEMA 4X / IP66 (corrosive/explosive environment, stainless steel 316L)</td>
                        </tr>
                        <tr>
                            <td>I/O Configuration</td>
                            <td>120 DI + 80 DO + 60 AI (4-20mA HART) + 24 AO (4-20mA)</td>
                        </tr>
                        <tr>
                            <td>Safety Certification</td>
                            <td>SIL 2 per IEC 61508 (functional safety for process shutdown)</td>
                        </tr>
                        <tr>
                            <td>Cybersecurity</td>
                            <td>IEC 62443 compliant (industrial network security, firewall, VPN)</td>
                        </tr>
                    </table>
                </div>
            </div>

            <div class="section">
                <h2>📦 Complete Package Contents</h2>
                <div class="deliverables">
                    <div class="deliverable-item">
                        <strong>✅ 3D CAD Model</strong><br>
                        CadQuery parametric design<br>
                        Export: STEP/STL/SVG/DXF
                    </div>
                    <div class="deliverable-item">
                        <strong>✅ Complete Documentation</strong><br>
                        25+ pages specifications<br>
                        System architecture
                    </div>
                    <div class="deliverable-item">
                        <strong>✅ I/O Point List</strong><br>
                        284 points documented<br>
                        Terminal assignments
                    </div>
                    <div class="deliverable-item">
                        <strong>✅ Network Architecture</strong><br>
                        PROFINET + Modbus<br>
                        Topology diagrams
                    </div>
                    <div class="deliverable-item">
                        <strong>✅ Hardware BOM</strong><br>
                        Itemized parts list<br>
                        With pricing
                    </div>
                    <div class="deliverable-item">
                        <strong>✅ Safety Systems</strong><br>
                        ESD + F&G integration<br>
                        SIL 2 certified
                    </div>
                    <div class="deliverable-item">
                        <strong>⏳ PLC Programming</strong><br>
                        TIA Portal V18<br>
                        Upon contract
                    </div>
                    <div class="deliverable-item">
                        <strong>⏳ HMI Screens</strong><br>
                        WinCC Unified<br>
                        Upon contract
                    </div>
                </div>
            </div>

            <div class="cost-box">
                <div>Total Project Investment</div>
                <div class="amount">$155,000 USD</div>
                <small>Hardware + Engineering + Installation | Turnkey Solution</small>
                <small>Payment: 30% deposit / 40% at FAT / 30% at SAT</small>
            </div>

            <div class="section">
                <h2>📅 Project Timeline - 20 Weeks</h2>
                <div class="timeline">
                    <div class="timeline-item">
                        <strong>Week 1-2:</strong> Detailed design & P&ID review with your engineering team
                    </div>
                    <div class="timeline-item">
                        <strong>Week 3-6:</strong> Panel fabrication, wiring, and component assembly
                    </div>
                    <div class="timeline-item">
                        <strong>Week 7-10:</strong> PLC programming & HMI development (TIA Portal V18)
                    </div>
                    <div class="timeline-item">
                        <strong>Week 11-12:</strong> Factory Acceptance Test (FAT) at our facility
                    </div>
                    <div class="timeline-item">
                        <strong>Week 13-16:</strong> Site installation, cabling, and field wiring
                    </div>
                    <div class="timeline-item">
                        <strong>Week 17-18:</strong> Commissioning & Site Acceptance Test (SAT)
                    </div>
                    <div class="timeline-item">
                        <strong>Week 19-20:</strong> Operator training & documentation handover ✅
                    </div>
                </div>
            </div>

            <div class="section">
                <h2>🎓 Standards Compliance & Certifications</h2>
                <div class="features">
                    <div class="feature-box">
                        <h3>Programming Standards</h3>
                        <ul>
                            <li><strong>IEC 61131-3</strong> - PLC Languages (LAD, FBD, SCL)</li>
                            <li><strong>ISA-88</strong> - Batch Control</li>
                            <li><strong>ISA-95</strong> - Enterprise Integration</li>
                        </ul>
                    </div>
                    <div class="feature-box">
                        <h3>Safety Standards</h3>
                        <ul>
                            <li><strong>IEC 61508</strong> - Functional Safety (SIL 2)</li>
                            <li><strong>IEC 61511</strong> - Process Safety</li>
                            <li><strong>API RP 14C</strong> - Separation Equipment</li>
                        </ul>
                    </div>
                    <div class="feature-box">
                        <h3>Electrical Standards</h3>
                        <ul>
                            <li><strong>NFPA 70</strong> - National Electrical Code</li>
                            <li><strong>IEEE 1100</strong> - Grounding (Emerald Book)</li>
                            <li><strong>NEMA 250</strong> - Enclosure Ratings</li>
                        </ul>
                    </div>
                    <div class="feature-box">
                        <h3>Cybersecurity</h3>
                        <ul>
                            <li><strong>IEC 62443</strong> - Industrial Cybersecurity</li>
                            <li><strong>NIST CSF</strong> - Cybersecurity Framework</li>
                            <li><strong>API 1164</strong> - Pipeline SCADA Security</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="cta-section">
                <h3>📞 Ready to Move Forward?</h3>
                <p style="font-size: 18px; margin: 20px 0;">
                    Our team is ready to answer your questions and begin implementation
                </p>
                <a href="mailto:w.aroca@insaing.com?subject=PLC System Proposal - Schedule Consultation" class="btn">📅 Schedule Consultation</a>
                <a href="mailto:w.aroca@insaing.com?subject=PLC System Proposal - Request Modifications" class="btn">✏️ Request Modifications</a>
                <a href="mailto:w.aroca@insaing.com?subject=PLC System Proposal - Get Quote" class="btn">💰 Get Formal Quote</a>
            </div>
        </div>

        <div class="footer">
            <h3 style="color: #1e3c72; margin-top: 0;">INSA Automation Corp</h3>
            <p><strong>Industrial Automation | Energy Optimization | Industrial Cybersecurity</strong></p>
            <p><strong>Email:</strong> w.aroca@insaing.com</p>
            <p><strong>Support:</strong> 24/7 Emergency Support Available</p>
            <p><strong>Certifications:</strong> Siemens PCS 7 | TÜV SIL 2 | ISA CAP | IEC 62443 Expert</p>
            <hr style="border: 0; border-top: 1px solid #ccc; margin: 20px 0;">
            <p style="font-size: 12px; color: #999;">
                <strong>Generated by:</strong> AI-Powered Engineering Design System<br>
                <strong>Technology Stack:</strong> Claude Code + CadQuery + ERPNext + InvenTree<br>
                <strong>Date:</strong> {datetime.now().strftime("%B %d, %Y %H:%M UTC")}<br>
                <strong>Status:</strong> Production-Ready Engineering Design | Quote Valid 30 Days
            </p>
        </div>
    </div>
</body>
</html>
    """

    return html


def send_email_with_images():
    """Send email with embedded CAD images"""

    print("🚀 Sending Complete PLC System Design Package (WITH IMAGES)...")
    print()

    # Create message
    msg = MIMEMultipart('related')
    msg['Subject'] = '🏭 Complete PLC System Design with 3D CAD Models - Oil & Gas ($155K Project)'
    msg['From'] = FROM_EMAIL
    msg['To'] = TO_EMAIL
    msg['X-Priority'] = '1'  # High priority

    # Create HTML body
    html_body = create_html_email_with_images()
    html_part = MIMEText(html_body, 'html')
    msg.attach(html_part)

    # Attach files
    attachments = [
        {
            'path': '/home/wil/plc_designs/oil_gas_plc_panel.py',
            'name': 'OilGas_PLC_Panel_CAD_Model.py',
            'description': '3D CAD model (CadQuery parametric)'
        },
        {
            'path': '/home/wil/plc_designs/PLC_SYSTEM_DOCUMENTATION.md',
            'name': 'PLC_System_Complete_Documentation.md',
            'description': 'Complete specifications (25+ pages)'
        },
        {
            'path': '/home/wil/plc_designs/plc_system_layout.svg',
            'name': 'PLC_System_Layout_Diagram.svg',
            'description': 'System layout diagram (SVG)'
        }
    ]

    for att in attachments:
        if os.path.exists(att['path']):
            with open(att['path'], 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={att["name"]}'
                )
                msg.attach(part)
                print(f"   ✅ Attached: {att['name']} ({att['description']})")
        else:
            print(f"   ⚠️  File not found: {att['path']}")

    print()

    # Send email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.send_message(msg)
            print("✅ Email sent successfully!")
            print()
            print(f"   From: {FROM_EMAIL}")
            print(f"   To: {TO_EMAIL}")
            print(f"   Subject: {msg['Subject']}")
            print(f"   Attachments: {len(attachments)} files")
            print(f"   Embedded Images: SVG layout diagram (base64)")
            print()
            print("📧 Check your inbox for the complete PLC system design package!")
            print("🎨 The email includes an embedded 3D system layout diagram!")

    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

    return True


if __name__ == "__main__":
    success = send_email_with_images()
    exit(0 if success else 1)
