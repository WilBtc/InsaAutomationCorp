"""
Email Service for INSA CRM
Uses localhost Postfix for sending emails
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
from pathlib import Path
from typing import Optional, List

logger = logging.getLogger(__name__)

SMTP_HOST = "localhost"
SMTP_PORT = 25
FROM_EMAIL = "noreply@insaing.com"
FROM_NAME = "INSA Automation Corp"


def send_email(
    to: str,
    subject: str,
    html_body: str,
    text_body: Optional[str] = None,
    attachments: Optional[List[Path]] = None
) -> bool:
    """
    Send email using localhost Postfix

    Args:
        to: Recipient email address
        subject: Email subject
        html_body: HTML email body
        text_body: Plain text fallback (optional)
        attachments: List of file paths to attach (optional)

    Returns:
        True if sent successfully, False otherwise
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg['To'] = to
        msg['Subject'] = subject

        # Add plain text part (fallback)
        if text_body:
            msg.attach(MIMEText(text_body, 'plain'))

        # Add HTML part
        msg.attach(MIMEText(html_body, 'html'))

        # Add attachments if provided
        if attachments:
            for file_path in attachments:
                if file_path.exists():
                    with open(file_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename={file_path.name}'
                        )
                        msg.attach(part)

        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.send_message(msg)

        logger.info(f"Email sent successfully to {to}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to}: {e}")
        return False


def send_password_reset_email(email: str, full_name: str, reset_token: str, base_url: str) -> bool:
    """
    Send password reset email

    Args:
        email: User's email address
        full_name: User's full name
        reset_token: Password reset token
        base_url: Base URL for reset link (e.g., https://iac1.tailc58ea3.ts.net)
    """
    reset_link = f"{base_url}/command-center/reset-password.html?token={reset_token}"

    subject = "INSA CRM - Password Reset Request"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #0891b2 0%, #7c3aed 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background: #f8fafc;
                padding: 30px;
                border: 1px solid #e2e8f0;
                border-radius: 0 0 10px 10px;
            }}
            .button {{
                display: inline-block;
                background: linear-gradient(135deg, #0891b2 0%, #7c3aed 100%);
                color: white;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .footer {{
                margin-top: 30px;
                text-align: center;
                color: #64748b;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔐 Password Reset Request</h1>
        </div>
        <div class="content">
            <p>Hola {full_name},</p>

            <p>Recibimos una solicitud para restablecer la contraseña de tu cuenta de <strong>INSA Command Center</strong>.</p>

            <p>Haz clic en el siguiente botón para crear una nueva contraseña:</p>

            <p style="text-align: center;">
                <a href="{reset_link}" class="button">Restablecer Contraseña</a>
            </p>

            <p>O copia este enlace en tu navegador:</p>
            <p style="background: #e2e8f0; padding: 10px; border-radius: 5px; word-break: break-all;">
                {reset_link}
            </p>

            <p><strong>⚠️ Este enlace expira en 1 hora.</strong></p>

            <p>Si no solicitaste este cambio, puedes ignorar este correo de forma segura.</p>

            <p>Saludos,<br>
            <strong>INSA Automation Corp</strong><br>
            Industrial Automation & Control Systems</p>
        </div>
        <div class="footer">
            <p>Este es un correo automático, por favor no respondas.</p>
            <p>&copy; 2025 INSA Automation Corp. Todos los derechos reservados.</p>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    INSA CRM - Password Reset Request

    Hola {full_name},

    Recibimos una solicitud para restablecer la contraseña de tu cuenta de INSA Command Center.

    Visita el siguiente enlace para crear una nueva contraseña:
    {reset_link}

    Este enlace expira en 1 hora.

    Si no solicitaste este cambio, puedes ignorar este correo.

    Saludos,
    INSA Automation Corp
    """

    return send_email(email, subject, html_body, text_body)


def send_invitation_email(
    email: str,
    role: str,
    invited_by_name: str,
    invitation_token: str,
    base_url: str
) -> bool:
    """
    Send user invitation email

    Args:
        email: New user's email address
        role: User's role (admin, user, etc.)
        invited_by_name: Name of the person who sent the invitation
        invitation_token: Invitation token
        base_url: Base URL for invitation link
    """
    invitation_link = f"{base_url}/command-center/accept-invitation.html?token={invitation_token}"

    role_spanish = {
        "admin": "Administrador",
        "sales_manager": "Gerente de Ventas",
        "sales_rep": "Representante de Ventas",
        "engineer": "Ingeniero",
        "user": "Usuario"
    }.get(role, role)

    subject = f"INSA CRM - Invitación a INSA Command Center"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #0891b2 0%, #7c3aed 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background: #f8fafc;
                padding: 30px;
                border: 1px solid #e2e8f0;
                border-radius: 0 0 10px 10px;
            }}
            .button {{
                display: inline-block;
                background: linear-gradient(135deg, #0891b2 0%, #7c3aed 100%);
                color: white;
                padding: 12px 30px;
                text-decoration: none;
                border-radius: 5px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .features {{
                background: white;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .features h3 {{
                color: #0891b2;
                margin-top: 0;
            }}
            .features ul {{
                list-style: none;
                padding: 0;
            }}
            .features li {{
                padding: 5px 0;
                padding-left: 25px;
                position: relative;
            }}
            .features li:before {{
                content: "✓";
                position: absolute;
                left: 0;
                color: #10b981;
                font-weight: bold;
            }}
            .footer {{
                margin-top: 30px;
                text-align: center;
                color: #64748b;
                font-size: 12px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 ¡Bienvenido a INSA Command Center!</h1>
        </div>
        <div class="content">
            <p>Hola,</p>

            <p><strong>{invited_by_name}</strong> te invitó a unirte a <strong>INSA Command Center</strong> como <strong>{role_spanish}</strong>.</p>

            <div class="features">
                <h3>🤖 Plataforma de Automatización con IA</h3>
                <ul>
                    <li>8 agentes de IA especializados para Oil & Gas</li>
                    <li>Dimensionamiento automático de proyectos</li>
                    <li>CRM industrial con 33 herramientas integradas</li>
                    <li>Cumplimiento IEC 62443 automatizado</li>
                    <li>Auto-sanación de sistemas 24/7</li>
                    <li>Generación de P&IDs y modelos 3D CAD</li>
                    <li>Gestión completa de plataforma</li>
                    <li>Investigación RAG con 900+ documentos</li>
                </ul>
            </div>

            <p>Haz clic en el siguiente botón para crear tu cuenta:</p>

            <p style="text-align: center;">
                <a href="{invitation_link}" class="button">Aceptar Invitación</a>
            </p>

            <p>O copia este enlace en tu navegador:</p>
            <p style="background: #e2e8f0; padding: 10px; border-radius: 5px; word-break: break-all;">
                {invitation_link}
            </p>

            <p><strong>⚠️ Esta invitación expira en 7 días.</strong></p>

            <p>Saludos,<br>
            <strong>INSA Automation Corp</strong><br>
            Industrial Automation & Control Systems</p>
        </div>
        <div class="footer">
            <p>Este es un correo automático, por favor no respondas.</p>
            <p>&copy; 2025 INSA Automation Corp. Todos los derechos reservados.</p>
        </div>
    </body>
    </html>
    """

    text_body = f"""
    INSA CRM - Invitación a INSA Command Center

    Hola,

    {invited_by_name} te invitó a unirte a INSA Command Center como {role_spanish}.

    Visita el siguiente enlace para crear tu cuenta:
    {invitation_link}

    Esta invitación expira en 7 días.

    Saludos,
    INSA Automation Corp
    """

    return send_email(email, subject, html_body, text_body)
