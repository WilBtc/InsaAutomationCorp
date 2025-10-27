"""
Email Notification System for INSA Advanced IIoT Platform v2.0
Phase 2 - Feature 4

Handles email notifications for rule engine alerts with SMTP configuration
and template-based emails.

Author: INSA Automation Corp
Date: October 27, 2025
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Dict, List, Optional
import psycopg2
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Email notification service with SMTP support"""

    def __init__(self, smtp_config: Dict):
        """
        Initialize email notifier

        Args:
            smtp_config: SMTP configuration
                {
                    'host': 'smtp.gmail.com',
                    'port': 587,
                    'username': 'alerts@insa.com',
                    'password': 'app_password',
                    'from_email': 'INSA IIoT Platform <alerts@insa.com>',
                    'use_tls': True
                }
        """
        self.smtp_config = smtp_config
        self.host = smtp_config.get('host', 'localhost')
        self.port = smtp_config.get('port', 587)
        self.username = smtp_config.get('username')
        self.password = smtp_config.get('password')
        self.from_email = smtp_config.get('from_email', 'noreply@insa.com')
        self.use_tls = smtp_config.get('use_tls', True)

        logger.info(f"Email notifier initialized - SMTP: {self.host}:{self.port}")

    def send_alert_email(
        self,
        to_emails: List[str],
        device_id: str,
        rule_name: str,
        severity: str,
        message: str,
        context: Dict
    ) -> bool:
        """
        Send alert email notification

        Args:
            to_emails: List of recipient email addresses
            device_id: Device ID that triggered the alert
            rule_name: Name of the rule that triggered
            severity: Alert severity (info, warning, critical)
            message: Alert message
            context: Additional context data

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Format subject based on severity
            severity_emoji = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'critical': '🚨'
            }
            emoji = severity_emoji.get(severity.lower(), '📢')

            subject = f"{emoji} [{severity.upper()}] {rule_name}"

            # Create HTML email body
            html_body = self._generate_alert_html(
                device_id=device_id,
                rule_name=rule_name,
                severity=severity,
                message=message,
                context=context
            )

            # Create plain text fallback
            text_body = self._generate_alert_text(
                device_id=device_id,
                rule_name=rule_name,
                severity=severity,
                message=message,
                context=context
            )

            # Send email
            success = self._send_email(
                to_emails=to_emails,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )

            if success:
                logger.info(f"Alert email sent to {', '.join(to_emails)}: {subject}")
            else:
                logger.error(f"Failed to send alert email to {', '.join(to_emails)}")

            return success

        except Exception as e:
            logger.error(f"Error sending alert email: {e}")
            return False

    def _generate_alert_html(
        self,
        device_id: str,
        rule_name: str,
        severity: str,
        message: str,
        context: Dict
    ) -> str:
        """Generate HTML email body for alert"""

        severity_colors = {
            'info': '#3498db',
            'warning': '#f39c12',
            'critical': '#e74c3c'
        }
        color = severity_colors.get(severity.lower(), '#95a5a6')

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: {color};
                    color: white;
                    padding: 20px;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-top: none;
                }}
                .detail-row {{
                    margin: 10px 0;
                    padding: 10px;
                    background-color: white;
                    border-left: 3px solid {color};
                }}
                .label {{
                    font-weight: bold;
                    color: #555;
                }}
                .footer {{
                    margin-top: 20px;
                    padding: 15px;
                    background-color: #34495e;
                    color: white;
                    text-align: center;
                    border-radius: 0 0 5px 5px;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🏭 INSA IIoT Platform Alert</h2>
                    <p style="margin: 0;">Severity: {severity.upper()}</p>
                </div>
                <div class="content">
                    <div class="detail-row">
                        <span class="label">Rule:</span> {rule_name}
                    </div>
                    <div class="detail-row">
                        <span class="label">Device ID:</span> {device_id}
                    </div>
                    <div class="detail-row">
                        <span class="label">Message:</span><br>
                        {message}
                    </div>
                    <div class="detail-row">
                        <span class="label">Timestamp:</span> {timestamp}
                    </div>
        """

        # Add context details if available
        if context:
            html += """
                    <div class="detail-row">
                        <span class="label">Details:</span><br>
            """
            for key, value in context.items():
                if key != 'rule_id':  # Skip rule_id (internal)
                    html += f"                        • {key}: {value}<br>\n"
            html += "                    </div>\n"

        html += """
                </div>
                <div class="footer">
                    INSA Advanced IIoT Platform v2.0<br>
                    <em>This is an automated alert - do not reply</em>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def _generate_alert_text(
        self,
        device_id: str,
        rule_name: str,
        severity: str,
        message: str,
        context: Dict
    ) -> str:
        """Generate plain text email body for alert"""

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')

        text = f"""
INSA IIoT Platform Alert
{'='*60}

Severity: {severity.upper()}
Rule: {rule_name}
Device ID: {device_id}

Message:
{message}

Timestamp: {timestamp}

"""

        # Add context details if available
        if context:
            text += "Details:\n"
            for key, value in context.items():
                if key != 'rule_id':
                    text += f"  • {key}: {value}\n"

        text += f"""
{'='*60}
INSA Advanced IIoT Platform v2.0
This is an automated alert - do not reply
"""

        return text

    def _send_email(
        self,
        to_emails: List[str],
        subject: str,
        html_body: str,
        text_body: str
    ) -> bool:
        """
        Send email via SMTP

        Args:
            to_emails: List of recipient emails
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text email body

        Returns:
            bool: True if sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject

            # Attach parts (text first, then html)
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')
            msg.attach(part1)
            msg.attach(part2)

            # Connect to SMTP server
            if self.use_tls:
                server = smtplib.SMTP(self.host, self.port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.host, self.port)

            # Login if credentials provided
            if self.username and self.password:
                server.login(self.username, self.password)

            # Send email
            server.sendmail(self.from_email, to_emails, msg.as_string())
            server.quit()

            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def test_email_connection(self) -> bool:
        """
        Test SMTP connection

        Returns:
            bool: True if connection successful
        """
        try:
            if self.use_tls:
                server = smtplib.SMTP(self.host, self.port, timeout=10)
                server.starttls()
            else:
                server = smtplib.SMTP(self.host, self.port, timeout=10)

            if self.username and self.password:
                server.login(self.username, self.password)

            server.quit()
            logger.info("SMTP connection test successful")
            return True

        except Exception as e:
            logger.error(f"SMTP connection test failed: {e}")
            return False


# Module-level singleton instance
_email_notifier = None


def init_email_notifier(smtp_config: Dict) -> EmailNotifier:
    """
    Initialize the email notifier singleton

    Args:
        smtp_config: SMTP configuration dict

    Returns:
        EmailNotifier: Initialized email notifier instance
    """
    global _email_notifier
    _email_notifier = EmailNotifier(smtp_config)
    return _email_notifier


def get_email_notifier() -> Optional[EmailNotifier]:
    """
    Get the email notifier singleton instance

    Returns:
        EmailNotifier or None: Email notifier instance if initialized
    """
    return _email_notifier
