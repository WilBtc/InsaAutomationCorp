#!/usr/bin/env python3
"""
Email Sender - P&ID Separador Trifásico de Petróleo
Envía el P&ID completo con todos los archivos adjuntos

Destinatario: j.casas@insaing.com
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime

def send_pid_email():
    """
    Envía email con P&ID del separador trifásico
    """

    # Configuración SMTP (self-hosted Postfix)
    smtp_server = "localhost"
    smtp_port = 25

    # Remitente y destinatario
    from_email = "w.aroca@insaing.com"
    to_email = "j.casas@insaing.com"

    # Crear mensaje
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = "P&ID Separador Trifásico de Petróleo - Control Electrónico"

    # Cuerpo del email en HTML
    html_body = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                      color: white; padding: 30px; text-align: center; border-radius: 10px; }
            .content { padding: 20px; background: #f9f9f9; border-radius: 10px; margin: 20px 0; }
            .section { background: white; padding: 20px; margin: 15px 0; border-radius: 8px;
                       border-left: 4px solid #667eea; }
            .highlight { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 10px 0; }
            .stats { display: inline-block; background: #4CAF50; color: white;
                     padding: 10px 20px; margin: 5px; border-radius: 5px; }
            .footer { text-align: center; color: #666; padding: 20px; font-size: 0.9em; }
            table { width: 100%; border-collapse: collapse; margin: 15px 0; }
            th { background: #667eea; color: white; padding: 12px; text-align: left; }
            td { padding: 10px; border-bottom: 1px solid #ddd; }
            tr:hover { background: #f5f5f5; }
            .checkmark { color: #4CAF50; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛢️ P&ID Separador Trifásico de Petróleo</h1>
            <h2>Control Electrónico Avanzado</h2>
            <p>Diseño Profesional ISA-5.1-2024 | API RP 12J | API RP 14C</p>
        </div>

        <div class="content">
            <div class="section">
                <h2>📊 Resumen Ejecutivo</h2>
                <p>Se adjunta el <strong>P&ID completo</strong> de un separador trifásico de petróleo
                con control electrónico automatizado, cumpliendo al 100% con los estándares internacionales
                de la industria petrolera.</p>

                <div class="highlight">
                    <h3>🎯 Sistema Diseñado</h3>
                    <ul>
                        <li><strong>Separación Trifásica:</strong> Gas + Petróleo + Agua</li>
                        <li><strong>Capacidad:</strong> 1000 bbl (Vessel horizontal)</li>
                        <li><strong>Presión de Diseño:</strong> 1440 psi (ANSI 600)</li>
                        <li><strong>Control:</strong> PLC Siemens S7-1500 (redundante)</li>
                        <li><strong>Interfaz:</strong> HMI SCADA 15" touchscreen</li>
                    </ul>
                </div>
            </div>

            <div class="section">
                <h2>📁 Archivos Adjuntos (3 formatos)</h2>
                <table>
                    <tr>
                        <th>Archivo</th>
                        <th>Tipo</th>
                        <th>Tamaño</th>
                        <th>Uso</th>
                    </tr>
                    <tr>
                        <td>Separador_Trifasico_Petroleo_PID.svg</td>
                        <td>SVG Vector</td>
                        <td>22 KB</td>
                        <td>Visualización / Presentaciones</td>
                    </tr>
                    <tr>
                        <td>Separador_Trifasico_Petroleo_PID.dxf</td>
                        <td>DXF CAD</td>
                        <td>27 KB</td>
                        <td>Edición en AutoCAD/QCAD</td>
                    </tr>
                    <tr>
                        <td>Separador_Trifasico_Petroleo_Components.json</td>
                        <td>JSON</td>
                        <td>11 KB</td>
                        <td>Lista de componentes (BOM)</td>
                    </tr>
                    <tr>
                        <td>SEPARADOR_TRIFASICO_VALIDATION.md</td>
                        <td>Markdown</td>
                        <td>~50 KB</td>
                        <td>Reporte de validación completo</td>
                    </tr>
                </table>
            </div>

            <div class="section">
                <h2>🔧 Componentes del Sistema</h2>

                <div style="text-align: center; margin: 20px 0;">
                    <span class="stats">28 Componentes</span>
                    <span class="stats">37 Conexiones</span>
                    <span class="stats">4 Lazos PID</span>
                    <span class="stats">100% ISA-5.1</span>
                </div>

                <h3>Instrumentación Principal:</h3>
                <ul>
                    <li><strong>4 Transmisores de Flujo:</strong> Coriolis (entrada), Vortex (gas),
                        Turbine (petróleo), Magnético (agua)</li>
                    <li><strong>2 Transmisores de Presión:</strong> Entrada + Separador (4-20mA)</li>
                    <li><strong>2 Transmisores de Temperatura:</strong> RTD Pt100 (0-200°C)</li>
                    <li><strong>4 Transmisores de Nivel:</strong> Radar + Displacer + 2 Alarmas</li>
                    <li><strong>4 Controladores PID:</strong> Presión, Temperatura, 2x Nivel</li>
                </ul>

                <h3>Válvulas de Control:</h3>
                <ul>
                    <li><strong>PCV-100:</strong> Control de presión (salida gas) - Neumática</li>
                    <li><strong>LCV-101:</strong> Control de nivel (salida petróleo) - Eléctrica</li>
                    <li><strong>LCV-102:</strong> Control de interfase (salida agua) - Eléctrica</li>
                    <li><strong>SDV-001 + SDV-100:</strong> Shutdown fail-close 24VDC</li>
                    <li><strong>PSV-100:</strong> Válvula de seguridad @ 400 psi</li>
                </ul>

                <h3>Equipos:</h3>
                <ul>
                    <li><strong>V-100:</strong> Separador horizontal 1000 bbl, A516 Gr.70 Carbon Steel</li>
                    <li><strong>P-101:</strong> Bomba centrífuga petróleo 10 HP, SS316</li>
                    <li><strong>P-102:</strong> Bomba centrífuga agua 7.5 HP, Duplex SS</li>
                    <li><strong>PLC-001:</strong> Siemens S7-1500, 128 AI/AO, Hot standby</li>
                    <li><strong>HMI-001:</strong> SCADA 15" touchscreen, WinCC</li>
                </ul>
            </div>

            <div class="section">
                <h2>✅ Cumplimiento de Estándares (100%)</h2>

                <table>
                    <tr>
                        <th>Estándar</th>
                        <th>Requisitos</th>
                        <th>Cumplidos</th>
                        <th>Estado</th>
                    </tr>
                    <tr>
                        <td><strong>ISA-5.1-2024</strong><br>Símbolos e Identificación</td>
                        <td>16</td>
                        <td>16</td>
                        <td><span class="checkmark">✅ 100%</span></td>
                    </tr>
                    <tr>
                        <td><strong>API RP 12J</strong><br>Separadores de Producción</td>
                        <td>9</td>
                        <td>9</td>
                        <td><span class="checkmark">✅ 100%</span></td>
                    </tr>
                    <tr>
                        <td><strong>API RP 14C</strong><br>Control y Seguridad</td>
                        <td>7</td>
                        <td>7</td>
                        <td><span class="checkmark">✅ 100%</span></td>
                    </tr>
                    <tr style="background: #e8f5e9; font-weight: bold;">
                        <td><strong>TOTAL</strong></td>
                        <td>32</td>
                        <td>32</td>
                        <td><span class="checkmark">✅ 100%</span></td>
                    </tr>
                </table>
            </div>

            <div class="section">
                <h2>🎯 Filosofía de Control</h2>

                <div class="highlight">
                    <h3>Loop de Control de Presión (Gas)</h3>
                    <p><code>PT-100 → PLC-001 → PIC-100 → PCV-100</code></p>
                    <p><strong>Setpoint:</strong> 250 psi | <strong>Tipo:</strong> PID</p>
                </div>

                <div class="highlight">
                    <h3>Loop de Control de Nivel de Petróleo</h3>
                    <p><code>LT-101 (Radar) → PLC-001 → LIC-101 → LCV-101</code></p>
                    <p><strong>Setpoint:</strong> 50% | <strong>Tipo:</strong> PID</p>
                </div>

                <div class="highlight">
                    <h3>Loop de Control de Interfase Oil/Water</h3>
                    <p><code>LT-102 (Displacer) → PLC-001 → LIC-102 → LCV-102</code></p>
                    <p><strong>Setpoint:</strong> 30% | <strong>Tipo:</strong> PID</p>
                </div>

                <div class="highlight">
                    <h3>Loop de Control de Temperatura</h3>
                    <p><code>TT-100 (RTD) → PLC-001 → TIC-100 → Calentamiento</code></p>
                    <p><strong>Setpoint:</strong> 60°C | <strong>Tipo:</strong> PID</p>
                </div>
            </div>

            <div class="section">
                <h2>🚨 Sistema de Seguridad</h2>
                <ul>
                    <li><strong>PSV-100:</strong> Alivio de presión @ 400 psi (Spring-loaded)</li>
                    <li><strong>SDV-001:</strong> Shutdown entrada (Fail-close)</li>
                    <li><strong>SDV-100:</strong> Shutdown gas (Fail-close)</li>
                    <li><strong>LAH-100:</strong> Alarma nivel alto @ 85%</li>
                    <li><strong>LAL-100:</strong> Alarma nivel bajo @ 15%</li>
                    <li><strong>Shutdown automático:</strong> PT-100 > 400 psi → Cierre SDVs</li>
                </ul>
            </div>

            <div class="section">
                <h2>📐 Especificaciones Técnicas</h2>

                <h3>Vessel V-100:</h3>
                <ul>
                    <li><strong>Tipo:</strong> Horizontal 3-Phase Separator</li>
                    <li><strong>Capacidad:</strong> 1000 bbl</li>
                    <li><strong>Presión de Diseño:</strong> 1440 psi (ASME Sec VIII Div 1)</li>
                    <li><strong>Temperatura de Diseño:</strong> 250°F (121°C)</li>
                    <li><strong>Material:</strong> A516 Gr.70 Carbon Steel</li>
                </ul>

                <h3>Rangos de Instrumentación:</h3>
                <ul>
                    <li><strong>FT-001:</strong> 0-500 bbl/day (Coriolis, ±0.1%)</li>
                    <li><strong>FT-100:</strong> 0-10 MMSCFD (Vortex, ±1%)</li>
                    <li><strong>FT-101:</strong> 0-300 bbl/day (Turbine, ±0.5%)</li>
                    <li><strong>FT-102:</strong> 0-200 bbl/day (Magnético, ±0.5%)</li>
                    <li><strong>PT-001:</strong> 0-1000 psi (±0.25%)</li>
                    <li><strong>PT-100:</strong> 0-500 psi (±0.25%)</li>
                    <li><strong>TT-001/100:</strong> 0-200°C (RTD Pt100, ±0.1°C)</li>
                    <li><strong>LT-101:</strong> 0-100% (Radar, ±2mm)</li>
                    <li><strong>LT-102:</strong> 0-100% (Displacer, ±5mm)</li>
                </ul>
            </div>

            <div class="section">
                <h2>🎓 Aplicaciones</h2>
                <p>Este P&ID es adecuado para:</p>
                <ul>
                    <li>✅ Facilidades de producción de petróleo</li>
                    <li>✅ Estaciones de recolección (gathering stations)</li>
                    <li>✅ Plantas de procesamiento de crudo</li>
                    <li>✅ Sistemas de tratamiento de agua de producción</li>
                    <li>✅ Operaciones offshore (con adaptaciones)</li>
                    <li>✅ Producción de gas asociado</li>
                </ul>
            </div>

            <div class="section">
                <h2>📚 Referencias</h2>
                <ol>
                    <li><strong>ANSI/ISA-5.1-2024</strong> - Instrumentation Symbols and Identification</li>
                    <li><strong>API RP 12J</strong> - Specification for Oil and Gas Separators (8th Edition)</li>
                    <li><strong>API RP 14C</strong> - Control and Safety Systems for Offshore Production</li>
                    <li><strong>ASME Sec VIII Div 1</strong> - Pressure Vessel Design Code</li>
                </ol>
            </div>
        </div>

        <div class="footer">
            <p><strong>🛢️ P&ID Separador Trifásico de Petróleo</strong></p>
            <p>Generado el: """ + datetime.now().strftime("%d de %B, %Y a las %H:%M UTC") + """</p>
            <p><strong>INSA Automation Corp - Oil & Gas Division</strong></p>
            <p>📧 <a href="mailto:w.aroca@insaing.com">w.aroca@insaing.com</a></p>
            <p>🤖 Diseñado con Claude Code - Sistema de Generación Automatizada de P&IDs</p>
            <hr>
            <p style="font-size: 0.8em; color: #999;">
                Este documento y sus adjuntos son confidenciales y están destinados únicamente
                para uso de INSA Automation Corp y sus clientes autorizados.
            </p>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, 'html'))

    # Lista de archivos a adjuntar
    attachments = [
        'Separador_Trifasico_Petroleo_PID.svg',
        'Separador_Trifasico_Petroleo_PID.dxf',
        'Separador_Trifasico_Petroleo_Components.json',
        'SEPARADOR_TRIFASICO_VALIDATION.md'
    ]

    # Adjuntar archivos
    for filename in attachments:
        filepath = f'/home/wil/pid-generator/{filename}'

        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
                msg.attach(part)
                print(f"✅ Archivo adjuntado: {filename}")
        else:
            print(f"⚠️  Archivo no encontrado: {filename}")

    # Enviar email
    try:
        print("\n📧 Enviando email...")
        print(f"   De: {from_email}")
        print(f"   Para: {to_email}")
        print(f"   Asunto: P&ID Separador Trifásico de Petróleo")

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.send_message(msg)
        server.quit()

        print("\n✅ ¡Email enviado exitosamente!")
        print(f"\n📬 Destinatario: {to_email}")
        print(f"   Adjuntos: {len(attachments)} archivos")

        return True

    except Exception as e:
        print(f"\n❌ Error al enviar email: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("📧 ENVÍO DE P&ID - SEPARADOR TRIFÁSICO DE PETRÓLEO")
    print("=" * 70)
    print("\nDestinatario: j.casas@insaing.com")
    print("Remitente: w.aroca@insaing.com")
    print()

    success = send_pid_email()

    if success:
        print("\n" + "=" * 70)
        print("✅ PROCESO COMPLETADO")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ ERROR EN EL ENVÍO")
        print("=" * 70)
