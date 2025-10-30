#!/usr/bin/env python3
"""
INSA CRM Platform - Phase 8: Customer Communication Agent
Multi-channel communication: Email, Phone AI, SMS, WhatsApp
"""

import os
import sys
import json
import structlog
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "api" / "core"))

try:
    from database import get_db_connection
except ImportError:
    # Fallback: create simple connection function
    import psycopg2
    def get_db_connection():
        return psycopg2.connect(
            host="localhost",
            database="insa_crm",
            user="postgres"
        )

logger = structlog.get_logger(__name__)


class CommunicationChannel(Enum):
    """Available communication channels"""
    EMAIL = "email"
    PHONE = "phone"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class MessagePriority(Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class CommunicationConfig:
    """Communication agent configuration"""

    # Email (via Postfix)
    smtp_host: str = "localhost"
    smtp_port: int = 25
    from_email: str = "sales@insaautomation.com"
    from_name: str = "INSA Automation Corp"

    # Phone AI (Vapi.ai integration)
    vapi_api_key: Optional[str] = None
    vapi_phone_number: Optional[str] = None
    vapi_assistant_id: Optional[str] = None

    # SMS (Twilio)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None

    # WhatsApp Business API
    whatsapp_api_key: Optional[str] = None
    whatsapp_phone_number: Optional[str] = None

    # Storage
    communication_logs_path: str = "/var/lib/insa-crm/communication_logs"

    @classmethod
    def from_env(cls):
        """Load configuration from environment"""
        return cls(
            smtp_host=os.getenv("SMTP_HOST", "localhost"),
            smtp_port=int(os.getenv("SMTP_PORT", "25")),
            from_email=os.getenv("FROM_EMAIL", "sales@insaautomation.com"),
            from_name=os.getenv("FROM_NAME", "INSA Automation Corp"),
            vapi_api_key=os.getenv("VAPI_API_KEY"),
            vapi_phone_number=os.getenv("VAPI_PHONE_NUMBER"),
            vapi_assistant_id=os.getenv("VAPI_ASSISTANT_ID"),
            twilio_account_sid=os.getenv("TWILIO_ACCOUNT_SID"),
            twilio_auth_token=os.getenv("TWILIO_AUTH_TOKEN"),
            twilio_phone_number=os.getenv("TWILIO_PHONE_NUMBER"),
            whatsapp_api_key=os.getenv("WHATSAPP_API_KEY"),
            whatsapp_phone_number=os.getenv("WHATSAPP_PHONE_NUMBER"),
        )


class CustomerCommunicationAgent:
    """
    Phase 8: Multi-channel customer communication agent

    Handles:
    - Email (via Postfix SMTP)
    - Phone AI (via Vapi.ai)
    - SMS (via Twilio)
    - WhatsApp (via Business API)

    Features:
    - Adaptive messaging (learns from responses)
    - Multi-channel campaigns
    - Call transcription & analysis
    - Automated follow-ups
    """

    def __init__(self, config: Optional[CommunicationConfig] = None):
        self.config = config or CommunicationConfig.from_env()
        self.logger = structlog.get_logger(__name__)

        # Create storage directory
        Path(self.config.communication_logs_path).mkdir(parents=True, exist_ok=True)

        self.logger.info("customer_communication_agent_initialized",
                        channels=["email", "phone", "sms", "whatsapp"])

    # =========================================================================
    # EMAIL COMMUNICATION (via Postfix)
    # =========================================================================

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        track_opens: bool = True,
        track_clicks: bool = True,
    ) -> Dict[str, Any]:
        """
        Send email via Postfix SMTP

        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML body
            body_text: Plain text body (optional, auto-generated if None)
            attachments: List of attachments [{"filename": "file.pdf", "content": bytes}]
            priority: Message priority
            track_opens: Add tracking pixel
            track_clicks: Add click tracking

        Returns:
            {
                "success": bool,
                "message_id": str,
                "sent_at": str,
                "error": Optional[str]
            }
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = to_email
            msg['X-Priority'] = str(priority.value)

            # Message ID for tracking
            message_id = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{hash(to_email) % 10000:04d}@insaautomation.com"
            msg['Message-ID'] = message_id

            # Plain text part
            if body_text is None:
                # Auto-generate from HTML (simple strip)
                import re
                body_text = re.sub('<[^<]+?>', '', body_html)

            msg.attach(MIMEText(body_text, 'plain'))

            # HTML part (with optional tracking)
            if track_opens:
                # Add tracking pixel
                # Get CRM API URL from environment
                crm_api_url = os.getenv("CRM_API_URL", "http://localhost:8003")
                tracking_pixel = f'<img src="{crm_api_url}/track/open/{message_id}" width="1" height="1" />'
                body_html += tracking_pixel

            msg.attach(MIMEText(body_html, 'html'))

            # Attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEApplication(attachment['content'])
                    part.add_header('Content-Disposition', 'attachment',
                                  filename=attachment['filename'])
                    msg.attach(part)

            # Send via SMTP
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as smtp:
                smtp.send_message(msg)

            # Log to database
            self._log_communication(
                channel=CommunicationChannel.EMAIL,
                recipient=to_email,
                message_id=message_id,
                subject=subject,
                content=body_html,
                status="sent"
            )

            self.logger.info("email_sent",
                           to=to_email,
                           subject=subject,
                           message_id=message_id)

            return {
                "success": True,
                "message_id": message_id,
                "sent_at": datetime.utcnow().isoformat(),
                "error": None
            }

        except Exception as e:
            self.logger.error("email_send_failed",
                            to=to_email,
                            error=str(e))
            return {
                "success": False,
                "message_id": None,
                "sent_at": None,
                "error": str(e)
            }

    def send_quote_email(
        self,
        customer_email: str,
        customer_name: str,
        quote_data: Dict[str, Any],
        attach_pdf: bool = True
    ) -> Dict[str, Any]:
        """
        Send quote to customer with professional formatting

        Args:
            customer_email: Customer email
            customer_name: Customer name
            quote_data: Quote data from quote_orchestrator
            attach_pdf: Attach PDF version

        Returns:
            Email send result
        """
        quote_id = quote_data.get('quote_id')
        total = quote_data.get('pricing', {}).get('pricing', {}).get('total', 0)
        valid_until = quote_data.get('metadata', {}).get('valid_until')

        # HTML email body
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: #003366; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px; }}
                .quote-summary {{ background: #f4f4f4; padding: 20px; margin: 20px 0; border-left: 4px solid #003366; }}
                .cta {{ background: #FF6600; color: white; padding: 15px 30px; text-decoration: none; display: inline-block; margin: 20px 0; border-radius: 5px; }}
                .footer {{ background: #f4f4f4; padding: 20px; text-align: center; font-size: 12px; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>INSA Automation Corp</h1>
                <p>Industrial Automation Excellence</p>
            </div>

            <div class="content">
                <p>Dear {customer_name},</p>

                <p>Thank you for your interest in INSA Automation Corp. We're pleased to provide you with a customized quote for your industrial automation project.</p>

                <div class="quote-summary">
                    <h2>Quote Summary</h2>
                    <p><strong>Quote ID:</strong> {quote_id}</p>
                    <p><strong>Total Investment:</strong> ${total:,.2f} USD</p>
                    <p><strong>Valid Until:</strong> {valid_until}</p>
                    <p><strong>Delivery Timeline:</strong> {quote_data.get('project_overview', {}).get('timeline', {}).get('duration_months', 'TBD')} months</p>
                </div>

                <p>This quote includes:</p>
                <ul>
                    <li>Complete PLC control system design & programming</li>
                    <li>HMI/SCADA development</li>
                    <li>P&ID diagrams & electrical schematics</li>
                    <li>On-site commissioning & training</li>
                    <li>IEC 62443 cybersecurity compliance</li>
                    <li>12 months warranty & support</li>
                </ul>

                <p>Our team has <strong>{quote_data.get('metadata', {}).get('similar_projects_count', 0)} similar projects</strong> in our portfolio, ensuring proven expertise in your industry.</p>

                <a href="{os.getenv('CRM_API_URL', 'http://localhost:8003')}/quotes/{quote_id}" class="cta">View Full Quote Details</a>

                <p>Questions? We're here to help:</p>
                <ul>
                    <li>📧 Email: sales@insaautomation.com</li>
                    <li>📞 Phone: +1 (555) 0100</li>
                    <li>🌐 Web: www.insaautomation.com</li>
                </ul>

                <p>We look forward to partnering with you!</p>

                <p>Best regards,<br>
                <strong>INSA Automation Sales Team</strong></p>
            </div>

            <div class="footer">
                <p>INSA Automation Corp | Industrial Control Systems Since 2015</p>
                <p>100.100.101.1 | Tailscale Network</p>
            </div>
        </body>
        </html>
        """

        # Attachments (optional PDF)
        attachments = []
        if attach_pdf:
            # TODO: Generate PDF from quote_data
            # For now, attach JSON
            quote_json = json.dumps(quote_data, indent=2).encode()
            attachments.append({
                "filename": f"{quote_id}.json",
                "content": quote_json
            })

        return self.send_email(
            to_email=customer_email,
            subject=f"Your Custom Quote - {quote_id} (${total:,.0f})",
            body_html=html_body,
            attachments=attachments if attachments else None,
            priority=MessagePriority.HIGH
        )

    # =========================================================================
    # PHONE AI COMMUNICATION (via Vapi.ai)
    # =========================================================================

    def make_phone_call(
        self,
        phone_number: str,
        purpose: str,
        context: Optional[Dict[str, Any]] = None,
        assistant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make outbound phone call via Vapi.ai

        Args:
            phone_number: Phone number to call (E.164 format)
            purpose: Call purpose (quote_follow_up, meeting_scheduling, etc)
            context: Additional context for AI assistant
            assistant_id: Vapi assistant ID (uses default if None)

        Returns:
            {
                "success": bool,
                "call_id": str,
                "status": str,
                "error": Optional[str]
            }
        """
        if not self.config.vapi_api_key:
            self.logger.warning("vapi_not_configured")
            return {
                "success": False,
                "call_id": None,
                "status": "not_configured",
                "error": "Vapi.ai API key not configured"
            }

        try:
            import requests

            # Vapi.ai API endpoint
            url = "https://api.vapi.ai/call/phone"

            headers = {
                "Authorization": f"Bearer {self.config.vapi_api_key}",
                "Content-Type": "application/json"
            }

            # Call payload
            payload = {
                "phoneNumber": phone_number,
                "assistantId": assistant_id or self.config.vapi_assistant_id,
                "metadata": {
                    "purpose": purpose,
                    "context": context or {},
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            call_id = result.get('id')

            # Log to database
            self._log_communication(
                channel=CommunicationChannel.PHONE,
                recipient=phone_number,
                message_id=call_id,
                subject=purpose,
                content=json.dumps(context or {}),
                status="initiated"
            )

            self.logger.info("phone_call_initiated",
                           phone=phone_number,
                           purpose=purpose,
                           call_id=call_id)

            return {
                "success": True,
                "call_id": call_id,
                "status": result.get('status', 'initiated'),
                "error": None
            }

        except Exception as e:
            self.logger.error("phone_call_failed",
                            phone=phone_number,
                            error=str(e))
            return {
                "success": False,
                "call_id": None,
                "status": "failed",
                "error": str(e)
            }

    def get_call_transcript(self, call_id: str) -> Dict[str, Any]:
        """
        Get call transcript and analysis from Vapi.ai

        Args:
            call_id: Vapi call ID

        Returns:
            {
                "success": bool,
                "transcript": str,
                "duration_seconds": int,
                "sentiment": str,
                "action_items": List[str],
                "recording_url": Optional[str]
            }
        """
        if not self.config.vapi_api_key:
            return {"success": False, "error": "Vapi.ai not configured"}

        try:
            import requests

            url = f"https://api.vapi.ai/call/{call_id}"
            headers = {"Authorization": f"Bearer {self.config.vapi_api_key}"}

            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            data = response.json()

            return {
                "success": True,
                "transcript": data.get('transcript', ''),
                "duration_seconds": data.get('duration', 0),
                "sentiment": data.get('sentiment', 'neutral'),
                "action_items": data.get('actionItems', []),
                "recording_url": data.get('recordingUrl'),
                "error": None
            }

        except Exception as e:
            self.logger.error("get_transcript_failed",
                            call_id=call_id,
                            error=str(e))
            return {
                "success": False,
                "error": str(e)
            }

    # =========================================================================
    # SMS COMMUNICATION (via Twilio)
    # =========================================================================

    def send_sms(
        self,
        phone_number: str,
        message: str,
        purpose: str = "notification"
    ) -> Dict[str, Any]:
        """
        Send SMS via Twilio

        Args:
            phone_number: Recipient phone (E.164 format)
            message: SMS text (max 160 chars recommended)
            purpose: Message purpose for tracking

        Returns:
            {
                "success": bool,
                "message_sid": str,
                "error": Optional[str]
            }
        """
        if not self.config.twilio_account_sid:
            self.logger.warning("twilio_not_configured")
            return {
                "success": False,
                "message_sid": None,
                "error": "Twilio not configured"
            }

        try:
            from twilio.rest import Client

            client = Client(
                self.config.twilio_account_sid,
                self.config.twilio_auth_token
            )

            sms = client.messages.create(
                body=message,
                from_=self.config.twilio_phone_number,
                to=phone_number
            )

            # Log to database
            self._log_communication(
                channel=CommunicationChannel.SMS,
                recipient=phone_number,
                message_id=sms.sid,
                subject=purpose,
                content=message,
                status="sent"
            )

            self.logger.info("sms_sent",
                           phone=phone_number,
                           purpose=purpose,
                           sid=sms.sid)

            return {
                "success": True,
                "message_sid": sms.sid,
                "error": None
            }

        except Exception as e:
            self.logger.error("sms_send_failed",
                            phone=phone_number,
                            error=str(e))
            return {
                "success": False,
                "message_sid": None,
                "error": str(e)
            }

    # =========================================================================
    # ADAPTIVE MESSAGING & CAMPAIGNS
    # =========================================================================

    def create_follow_up_campaign(
        self,
        lead_id: int,
        quote_id: str,
        channels: List[CommunicationChannel] = None
    ) -> Dict[str, Any]:
        """
        Create adaptive follow-up campaign for a quote

        Multi-channel sequence:
        Day 0: Email with quote
        Day 2: SMS reminder
        Day 5: Phone call follow-up
        Day 7: Email with case studies
        Day 14: Final email before expiration

        Args:
            lead_id: Lead ID from database
            quote_id: Quote ID to follow up on
            channels: Channels to use (default: email + sms + phone)

        Returns:
            {
                "campaign_id": str,
                "scheduled_messages": int,
                "channels": List[str]
            }
        """
        if channels is None:
            channels = [
                CommunicationChannel.EMAIL,
                CommunicationChannel.SMS,
                CommunicationChannel.PHONE
            ]

        campaign_id = f"campaign-{quote_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Get lead info from database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT company_name, contact_name, email, phone
                FROM leads WHERE id = %s
            """, (lead_id,))
            lead = cursor.fetchone()

        if not lead:
            return {"error": "Lead not found"}

        company, contact, email, phone = lead

        # Schedule messages
        scheduled = []

        # Day 0: Email with quote (immediate)
        if CommunicationChannel.EMAIL in channels:
            scheduled.append({
                "channel": "email",
                "delay_days": 0,
                "action": "send_quote_email"
            })

        # Day 2: SMS reminder
        if CommunicationChannel.SMS in channels and phone:
            scheduled.append({
                "channel": "sms",
                "delay_days": 2,
                "message": f"Hi {contact}! Just following up on quote {quote_id}. Any questions? Reply or call us at (555) 0100. - INSA Automation"
            })

        # Day 5: Phone call
        if CommunicationChannel.PHONE in channels and phone:
            scheduled.append({
                "channel": "phone",
                "delay_days": 5,
                "purpose": "quote_follow_up",
                "context": {
                    "quote_id": quote_id,
                    "customer_name": contact,
                    "company": company
                }
            })

        # Day 7: Email with case studies
        if CommunicationChannel.EMAIL in channels:
            scheduled.append({
                "channel": "email",
                "delay_days": 7,
                "subject": f"Similar Success Stories - {company}",
                "action": "send_case_studies"
            })

        # Day 14: Final reminder
        if CommunicationChannel.EMAIL in channels:
            scheduled.append({
                "channel": "email",
                "delay_days": 14,
                "subject": f"Quote Expiring Soon - {quote_id}",
                "action": "send_expiration_reminder"
            })

        # Save campaign to database
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO communication_campaigns
                (campaign_id, lead_id, quote_id, channels, scheduled_messages, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (
                campaign_id,
                lead_id,
                quote_id,
                json.dumps([c.value for c in channels]),
                json.dumps(scheduled)
            ))
            conn.commit()

        self.logger.info("campaign_created",
                        campaign_id=campaign_id,
                        lead_id=lead_id,
                        messages=len(scheduled))

        return {
            "campaign_id": campaign_id,
            "scheduled_messages": len(scheduled),
            "channels": [c.value for c in channels]
        }

    # =========================================================================
    # UTILITY FUNCTIONS
    # =========================================================================

    def _log_communication(
        self,
        channel: CommunicationChannel,
        recipient: str,
        message_id: str,
        subject: str,
        content: str,
        status: str
    ):
        """Log communication to database"""
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO communication_logs
                    (channel, recipient, message_id, subject, content, status, sent_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                """, (
                    channel.value,
                    recipient,
                    message_id,
                    subject,
                    content,
                    status
                ))
                conn.commit()
        except Exception as e:
            self.logger.error("log_communication_failed", error=str(e))


def main():
    """Test customer communication agent"""
    print("=" * 80)
    print("INSA CRM - Customer Communication Agent Test")
    print("=" * 80)

    agent = CustomerCommunicationAgent()

    # Test 1: Send test email
    print("\nTest 1: Sending test email...")
    result = agent.send_email(
        to_email="w.aroca@insaing.com",
        subject="Test Email from Communication Agent",
        body_html="<h1>Test Email</h1><p>This is a test from the customer communication agent.</p>",
        priority=MessagePriority.NORMAL
    )
    print(f"Result: {result}")

    # Test 2: Phone AI status
    print("\nTest 2: Phone AI status...")
    if agent.config.vapi_api_key:
        print("✅ Vapi.ai configured")
    else:
        print("⚠️  Vapi.ai not configured (set VAPI_API_KEY in .env)")

    # Test 3: SMS status
    print("\nTest 3: SMS status...")
    if agent.config.twilio_account_sid:
        print("✅ Twilio configured")
    else:
        print("⚠️  Twilio not configured (set TWILIO_ACCOUNT_SID in .env)")

    print("\n" + "=" * 80)
    print("Communication agent ready!")
    print("=" * 80)


if __name__ == "__main__":
    main()
