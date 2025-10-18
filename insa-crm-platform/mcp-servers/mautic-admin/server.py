#!/usr/bin/env python3
"""
Mautic Admin MCP Server - Complete Administrative Control
Provides 25+ tools for full Mautic management via Claude Code

Author: INSA Automation Corp
Date: October 18, 2025
Version: 1.0.0
"""

import asyncio
import subprocess
import json
import os
from typing import Any, Dict, List, Optional
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource

# Configuration
MAUTIC_PATH = "/var/www/mautic"
MAUTIC_URL = os.getenv("MAUTIC_URL", "http://100.100.101.1:9700")
MAUTIC_USERNAME = os.getenv("MAUTIC_USERNAME", "admin")
MAUTIC_PASSWORD = os.getenv("MAUTIC_PASSWORD", "mautic_admin_2025")
PHP_BIN = "/usr/bin/php"
CONSOLE_PATH = f"{MAUTIC_PATH}/bin/console"

# MCP Server instance
app = Server("mautic-admin")

class MauticAdmin:
    """Mautic administrative operations handler"""

    def __init__(self):
        self.base_url = MAUTIC_URL
        self.auth = (MAUTIC_USERNAME, MAUTIC_PASSWORD)
        self.api_url = f"{self.base_url}/api"

    async def run_console_command(self, command: str, args: List[str] = None) -> str:
        """Execute Mautic console command"""
        cmd = ["sudo", "-u", "www-data", PHP_BIN, CONSOLE_PATH, command]
        if args:
            cmd.extend(args)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=MAUTIC_PATH
            )

            output = result.stdout + result.stderr
            return output if output else "Command executed successfully (no output)"

        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after 300 seconds"
        except Exception as e:
            return f"Error executing command: {str(e)}"

    async def api_request(self, method: str, endpoint: str, data: Dict = None) -> Dict:
        """Make authenticated API request to Mautic"""
        url = f"{self.api_url}/{endpoint}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if method == "GET":
                    response = await client.get(url, auth=self.auth)
                elif method == "POST":
                    response = await client.post(url, auth=self.auth, json=data)
                elif method == "PATCH":
                    response = await client.patch(url, auth=self.auth, json=data)
                elif method == "DELETE":
                    response = await client.delete(url, auth=self.auth)
                else:
                    return {"error": f"Unsupported method: {method}"}

                return response.json()

            except Exception as e:
                return {"error": str(e)}

# Initialize admin handler
admin = MauticAdmin()

# ============================================================================
# INSTALLATION & SETUP TOOLS (5 tools)
# ============================================================================

@app.call_tool()
async def mautic_install_database(
    admin_firstname: str = "INSA",
    admin_lastname: str = "Admin",
    admin_username: str = "admin",
    admin_email: str = "w.aroca@insaing.com",
    admin_password: str = "mautic_admin_2025"
) -> list[TextContent]:
    """
    Install Mautic database schema and create admin user via CLI

    This is the programmatic equivalent of the web installation wizard.
    Creates all database tables, fixtures, and admin user.
    """

    # Step 1: Install database schema
    result1 = await admin.run_console_command("mautic:install:data", ["--force"])

    # Step 2: Create admin user
    result2 = await admin.run_console_command(
        "mautic:user:create",
        [
            f"--username={admin_username}",
            f"--email={admin_email}",
            f"--password={admin_password}",
            f"--firstname={admin_firstname}",
            f"--lastname={admin_lastname}",
            "--admin"
        ]
    )

    output = f"""✅ Mautic Installation Complete

Database Schema Installation:
{result1}

Admin User Creation:
{result2}

Admin Credentials:
  Username: {admin_username}
  Email: {admin_email}
  Password: {admin_password}
  Role: Administrator

Access Mautic: {MAUTIC_URL}
"""

    return [TextContent(type="text", text=output)]

@app.call_tool()
async def mautic_check_system() -> list[TextContent]:
    """
    Check Mautic system requirements and configuration status

    Verifies PHP extensions, file permissions, database connection, etc.
    """

    result = await admin.run_console_command("mautic:install:check")

    return [TextContent(
        type="text",
        text=f"🔍 Mautic System Check\n\n{result}"
    )]

@app.call_tool()
async def mautic_clear_cache() -> list[TextContent]:
    """Clear Mautic application cache (Symfony cache clear)"""

    result = await admin.run_console_command("cache:clear", ["--env=prod"])

    return [TextContent(
        type="text",
        text=f"✅ Cache Cleared\n\n{result}"
    )]

@app.call_tool()
async def mautic_update_schema() -> list[TextContent]:
    """Update database schema (run after Mautic updates)"""

    result = await admin.run_console_command("doctrine:schema:update", ["--force"])

    return [TextContent(
        type="text",
        text=f"✅ Database Schema Updated\n\n{result}"
    )]

@app.call_tool()
async def mautic_get_config() -> list[TextContent]:
    """Get current Mautic configuration parameters"""

    result = await admin.run_console_command("mautic:config:get")

    return [TextContent(
        type="text",
        text=f"📋 Mautic Configuration\n\n{result}"
    )]

# ============================================================================
# CONTACT MANAGEMENT TOOLS (5 tools)
# ============================================================================

@app.call_tool()
async def mautic_create_contact(
    email: str,
    firstname: str = "",
    lastname: str = "",
    company: str = "",
    phone: str = "",
    tags: str = ""
) -> list[TextContent]:
    """
    Create a new contact in Mautic

    Args:
        email: Contact email (required)
        firstname: First name
        lastname: Last name
        company: Company name
        phone: Phone number
        tags: Comma-separated tags
    """

    data = {
        "email": email,
        "firstname": firstname,
        "lastname": lastname,
        "company": company,
        "phone": phone
    }

    # Remove empty fields
    data = {k: v for k, v in data.items() if v}

    result = await admin.api_request("POST", "contacts/new", data)

    if "contact" in result:
        contact = result["contact"]
        output = f"""✅ Contact Created

ID: {contact.get('id')}
Email: {contact.get('fields', {}).get('core', {}).get('email', {}).get('value')}
Name: {contact.get('fields', {}).get('core', {}).get('firstname', {}).get('value', '')} {contact.get('fields', {}).get('core', {}).get('lastname', {}).get('value', '')}
Company: {contact.get('fields', {}).get('core', {}).get('company', {}).get('value', 'N/A')}
"""
    else:
        output = f"❌ Error creating contact: {result.get('error', 'Unknown error')}"

    return [TextContent(type="text", text=output)]

@app.call_tool()
async def mautic_get_contacts(
    search: str = "",
    limit: int = 20,
    orderBy: str = "id",
    orderByDir: str = "DESC"
) -> list[TextContent]:
    """
    Get list of contacts from Mautic

    Args:
        search: Search query (email, name, company)
        limit: Number of contacts to return (default: 20)
        orderBy: Field to sort by (id, email, firstname, etc.)
        orderByDir: Sort direction (ASC or DESC)
    """

    params = f"?limit={limit}&orderBy={orderBy}&orderByDir={orderByDir}"
    if search:
        params += f"&search={search}"

    result = await admin.api_request("GET", f"contacts{params}")

    if "contacts" in result:
        contacts = result["contacts"]
        total = result.get("total", len(contacts))

        output = f"📇 Mautic Contacts (Total: {total})\n\n"

        for contact_id, contact in list(contacts.items())[:limit]:
            fields = contact.get("fields", {}).get("core", {})
            email = fields.get("email", {}).get("value", "N/A")
            firstname = fields.get("firstname", {}).get("value", "")
            lastname = fields.get("lastname", {}).get("value", "")
            company = fields.get("company", {}).get("value", "")
            points = contact.get("points", 0)

            output += f"""ID: {contact_id}
  Email: {email}
  Name: {firstname} {lastname}
  Company: {company}
  Points: {points}
  Last Active: {contact.get('lastActive', 'Never')}

"""
    else:
        output = f"❌ Error fetching contacts: {result.get('error', 'Unknown error')}"

    return [TextContent(type="text", text=output)]

@app.call_tool()
async def mautic_update_contact(
    contact_id: int,
    email: str = "",
    firstname: str = "",
    lastname: str = "",
    company: str = "",
    points: int = None
) -> list[TextContent]:
    """Update an existing contact"""

    data = {}
    if email:
        data["email"] = email
    if firstname:
        data["firstname"] = firstname
    if lastname:
        data["lastname"] = lastname
    if company:
        data["company"] = company
    if points is not None:
        data["points"] = points

    result = await admin.api_request("PATCH", f"contacts/{contact_id}/edit", data)

    if "contact" in result:
        output = f"✅ Contact {contact_id} updated successfully"
    else:
        output = f"❌ Error updating contact: {result.get('error', 'Unknown error')}"

    return [TextContent(type="text", text=output)]

@app.call_tool()
async def mautic_delete_contact(contact_id: int) -> list[TextContent]:
    """Delete a contact from Mautic"""

    result = await admin.api_request("DELETE", f"contacts/{contact_id}/delete")

    if "contact" in result:
        output = f"✅ Contact {contact_id} deleted successfully"
    else:
        output = f"❌ Error deleting contact: {result.get('error', 'Unknown error')}"

    return [TextContent(type="text", text=output)]

@app.call_tool()
async def mautic_add_contact_to_segment(contact_id: int, segment_id: int) -> list[TextContent]:
    """Add contact to a specific segment"""

    result = await admin.api_request("POST", f"segments/{segment_id}/contact/{contact_id}/add")

    if "success" in result:
        output = f"✅ Contact {contact_id} added to segment {segment_id}"
    else:
        output = f"❌ Error: {result.get('error', 'Unknown error')}"

    return [TextContent(type="text", text=output)]

# ============================================================================
# SEGMENT MANAGEMENT TOOLS (3 tools)
# ============================================================================

@app.call_tool()
async def mautic_create_segment(
    name: str,
    description: str = "",
    is_global: bool = True
) -> list[TextContent]:
    """
    Create a new contact segment

    Args:
        name: Segment name
        description: Segment description
        is_global: Make segment global (visible to all users)
    """

    data = {
        "name": name,
        "description": description,
        "isGlobal": is_global,
        "isPublished": True
    }

    result = await admin.api_request("POST", "segments/new", data)

    if "list" in result:
        segment = result["list"]
        output = f"""✅ Segment Created

ID: {segment.get('id')}
Name: {segment.get('name')}
Description: {segment.get('description', 'N/A')}
Global: {segment.get('isGlobal')}
"""
    else:
        output = f"❌ Error creating segment: {result.get('error', 'Unknown error')}"

    return [TextContent(type="text", text=output)]

@app.call_tool()
async def mautic_get_segments(limit: int = 20) -> list[TextContent]:
    """Get list of contact segments"""

    result = await admin.api_request("GET", f"segments?limit={limit}")

    if "lists" in result:
        segments = result["lists"]
        total = result.get("total", len(segments))

        output = f"📊 Mautic Segments (Total: {total})\n\n"

        for seg_id, segment in segments.items():
            output += f"""ID: {seg_id}
  Name: {segment.get('name')}
  Description: {segment.get('description', 'N/A')}
  Contacts: {segment.get('contactCount', 0)}
  Global: {segment.get('isGlobal')}

"""
    else:
        output = f"❌ Error fetching segments: {result.get('error', 'Unknown error')}"

    return [TextContent(type="text", text=output)]

@app.call_tool()
async def mautic_update_segments() -> list[TextContent]:
    """Update all segments (recalculate membership based on filters)"""

    result = await admin.run_console_command("mautic:segments:update")

    return [TextContent(
        type="text",
        text=f"✅ Segments Updated\n\n{result}"
    )]

# ============================================================================
# CAMPAIGN MANAGEMENT TOOLS (5 tools)
# ============================================================================

@app.call_tool()
async def mautic_create_campaign(
    name: str,
    description: str = "",
    is_published: bool = True
) -> list[TextContent]:
    """Create a new email campaign"""

    data = {
        "name": name,
        "description": description,
        "isPublished": is_published
    }

    result = await admin.api_request("POST", "campaigns/new", data)

    if "campaign" in result:
        campaign = result["campaign"]
        output = f"""✅ Campaign Created

ID: {campaign.get('id')}
Name: {campaign.get('name')}
Description: {campaign.get('description', 'N/A')}
Published: {campaign.get('isPublished')}
"""
    else:
        output = f"❌ Error creating campaign: {result.get('error', 'Unknown error')}"

    return [TextContent(type="text", text=output)]

@app.call_tool()
async def mautic_get_campaigns(limit: int = 20) -> list[TextContent]:
    """Get list of campaigns"""

    result = await admin.api_request("GET", f"campaigns?limit={limit}")

    if "campaigns" in result:
        campaigns = result["campaigns"]
        total = result.get("total", len(campaigns))

        output = f"📧 Mautic Campaigns (Total: {total})\n\n"

        for camp_id, campaign in campaigns.items():
            output += f"""ID: {camp_id}
  Name: {campaign.get('name')}
  Description: {campaign.get('description', 'N/A')}
  Published: {campaign.get('isPublished')}
  Contacts: {campaign.get('contactCount', 0)}

"""
    else:
        output = f"❌ Error fetching campaigns: {result.get('error', 'Unknown error')}"

    return [TextContent(type="text", text=output)]

@app.call_tool()
async def mautic_trigger_campaigns() -> list[TextContent]:
    """Trigger campaign actions (process scheduled campaign events)"""

    result = await admin.run_console_command("mautic:campaigns:trigger")

    return [TextContent(
        type="text",
        text=f"✅ Campaigns Triggered\n\n{result}"
    )]

@app.call_tool()
async def mautic_rebuild_campaigns() -> list[TextContent]:
    """Rebuild campaign membership (update which contacts are in campaigns)"""

    result = await admin.run_console_command("mautic:campaigns:rebuild")

    return [TextContent(
        type="text",
        text=f"✅ Campaigns Rebuilt\n\n{result}"
    )]

@app.call_tool()
async def mautic_add_contact_to_campaign(contact_id: int, campaign_id: int) -> list[TextContent]:
    """Add contact to a specific campaign"""

    result = await admin.api_request("POST", f"campaigns/{campaign_id}/contact/{contact_id}/add")

    if "success" in result:
        output = f"✅ Contact {contact_id} added to campaign {campaign_id}"
    else:
        output = f"❌ Error: {result.get('error', 'Unknown error')}"

    return [TextContent(type="text", text=output)]

# ============================================================================
# EMAIL MANAGEMENT TOOLS (4 tools)
# ============================================================================

@app.call_tool()
async def mautic_send_email_queue() -> list[TextContent]:
    """Process email queue and send pending emails"""

    result = await admin.run_console_command("mautic:emails:send")

    return [TextContent(
        type="text",
        text=f"✅ Email Queue Processed\n\n{result}"
    )]

@app.call_tool()
async def mautic_send_broadcast(broadcast_id: int) -> list[TextContent]:
    """Send a broadcast email to segment"""

    result = await admin.run_console_command("mautic:broadcasts:send", [f"--id={broadcast_id}"])

    return [TextContent(
        type="text",
        text=f"✅ Broadcast {broadcast_id} Sent\n\n{result}"
    )]

@app.call_tool()
async def mautic_get_emails(limit: int = 20) -> list[TextContent]:
    """Get list of email templates"""

    result = await admin.api_request("GET", f"emails?limit={limit}")

    if "emails" in result:
        emails = result["emails"]
        total = result.get("total", len(emails))

        output = f"📨 Mautic Emails (Total: {total})\n\n"

        for email_id, email in emails.items():
            output += f"""ID: {email_id}
  Name: {email.get('name')}
  Subject: {email.get('subject', 'N/A')}
  Type: {email.get('emailType', 'N/A')}
  Published: {email.get('isPublished')}
  Sent Count: {email.get('sentCount', 0)}
  Read Count: {email.get('readCount', 0)}

"""
    else:
        output = f"❌ Error fetching emails: {result.get('error', 'Unknown error')}"

    return [TextContent(type="text", text=output)]

@app.call_tool()
async def mautic_send_email_to_contact(email_id: int, contact_id: int) -> list[TextContent]:
    """Send specific email to a contact"""

    result = await admin.api_request("POST", f"emails/{email_id}/contact/{contact_id}/send")

    if "success" in result or result.get("success") == 1:
        output = f"✅ Email {email_id} sent to contact {contact_id}"
    else:
        output = f"❌ Error: {result.get('error', 'Unknown error')}"

    return [TextContent(type="text", text=output)]

# ============================================================================
# MAINTENANCE & MONITORING TOOLS (4 tools)
# ============================================================================

@app.call_tool()
async def mautic_cleanup_old_data(days_old: int = 30) -> list[TextContent]:
    """
    Clean up old data (visitors, logs, stats)

    Args:
        days_old: Delete data older than this many days (default: 30)
    """

    result = await admin.run_console_command("mautic:maintenance:cleanup", [f"--days-old={days_old}"])

    return [TextContent(
        type="text",
        text=f"✅ Cleanup Complete (data older than {days_old} days)\n\n{result}"
    )]

@app.call_tool()
async def mautic_update_ip_database() -> list[TextContent]:
    """Update IP lookup database (for geolocation)"""

    result = await admin.run_console_command("mautic:iplookup:download")

    return [TextContent(
        type="text",
        text=f"✅ IP Database Updated\n\n{result}"
    )]

@app.call_tool()
async def mautic_process_webhooks() -> list[TextContent]:
    """Process queued webhook events"""

    result = await admin.run_console_command("mautic:webhooks:process")

    return [TextContent(
        type="text",
        text=f"✅ Webhooks Processed\n\n{result}"
    )]

@app.call_tool()
async def mautic_get_stats() -> list[TextContent]:
    """Get Mautic statistics and metrics"""

    # Get various metrics via API
    contacts_result = await admin.api_request("GET", "contacts?limit=1")
    campaigns_result = await admin.api_request("GET", "campaigns?limit=1")
    segments_result = await admin.api_request("GET", "segments?limit=1")
    emails_result = await admin.api_request("GET", "emails?limit=1")

    output = f"""📊 Mautic Statistics

Total Contacts: {contacts_result.get('total', 'N/A')}
Total Campaigns: {campaigns_result.get('total', 'N/A')}
Total Segments: {segments_result.get('total', 'N/A')}
Total Emails: {emails_result.get('total', 'N/A')}

Server: {MAUTIC_URL}
"""

    return [TextContent(type="text", text=output)]

# ============================================================================
# IMPORT/EXPORT TOOLS (2 tools)
# ============================================================================

@app.call_tool()
async def mautic_import_contacts(file_path: str) -> list[TextContent]:
    """
    Import contacts from CSV file

    Args:
        file_path: Path to CSV file with contacts
    """

    result = await admin.run_console_command("mautic:import", [file_path])

    return [TextContent(
        type="text",
        text=f"✅ Import Started\n\n{result}"
    )]

@app.call_tool()
async def mautic_process_import_queue() -> list[TextContent]:
    """Process queued import jobs"""

    result = await admin.run_console_command("mautic:import")

    return [TextContent(
        type="text",
        text=f"✅ Import Queue Processed\n\n{result}"
    )]

# ============================================================================
# List all tools
# ============================================================================

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available Mautic admin tools"""

    return [
        # Installation & Setup (5 tools)
        Tool(
            name="mautic_install_database",
            description="Install Mautic database schema and create admin user via CLI (programmatic installation)",
            inputSchema={
                "type": "object",
                "properties": {
                    "admin_firstname": {"type": "string", "default": "INSA"},
                    "admin_lastname": {"type": "string", "default": "Admin"},
                    "admin_username": {"type": "string", "default": "admin"},
                    "admin_email": {"type": "string", "default": "w.aroca@insaing.com"},
                    "admin_password": {"type": "string", "default": "mautic_admin_2025"}
                }
            }
        ),
        Tool(
            name="mautic_check_system",
            description="Check Mautic system requirements and configuration status",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="mautic_clear_cache",
            description="Clear Mautic application cache",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="mautic_update_schema",
            description="Update database schema after Mautic updates",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="mautic_get_config",
            description="Get current Mautic configuration parameters",
            inputSchema={"type": "object", "properties": {}}
        ),

        # Contact Management (5 tools)
        Tool(
            name="mautic_create_contact",
            description="Create a new contact in Mautic",
            inputSchema={
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "firstname": {"type": "string"},
                    "lastname": {"type": "string"},
                    "company": {"type": "string"},
                    "phone": {"type": "string"},
                    "tags": {"type": "string"}
                },
                "required": ["email"]
            }
        ),
        Tool(
            name="mautic_get_contacts",
            description="Get list of contacts from Mautic with optional search and filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "search": {"type": "string"},
                    "limit": {"type": "integer", "default": 20},
                    "orderBy": {"type": "string", "default": "id"},
                    "orderByDir": {"type": "string", "default": "DESC"}
                }
            }
        ),
        Tool(
            name="mautic_update_contact",
            description="Update an existing contact",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer"},
                    "email": {"type": "string"},
                    "firstname": {"type": "string"},
                    "lastname": {"type": "string"},
                    "company": {"type": "string"},
                    "points": {"type": "integer"}
                },
                "required": ["contact_id"]
            }
        ),
        Tool(
            name="mautic_delete_contact",
            description="Delete a contact from Mautic",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer"}
                },
                "required": ["contact_id"]
            }
        ),
        Tool(
            name="mautic_add_contact_to_segment",
            description="Add contact to a specific segment",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer"},
                    "segment_id": {"type": "integer"}
                },
                "required": ["contact_id", "segment_id"]
            }
        ),

        # Segment Management (3 tools)
        Tool(
            name="mautic_create_segment",
            description="Create a new contact segment",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "is_global": {"type": "boolean", "default": True}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="mautic_get_segments",
            description="Get list of contact segments",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20}
                }
            }
        ),
        Tool(
            name="mautic_update_segments",
            description="Update all segments (recalculate membership based on filters)",
            inputSchema={"type": "object", "properties": {}}
        ),

        # Campaign Management (5 tools)
        Tool(
            name="mautic_create_campaign",
            description="Create a new email campaign",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "is_published": {"type": "boolean", "default": True}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="mautic_get_campaigns",
            description="Get list of campaigns",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20}
                }
            }
        ),
        Tool(
            name="mautic_trigger_campaigns",
            description="Trigger campaign actions (process scheduled campaign events)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="mautic_rebuild_campaigns",
            description="Rebuild campaign membership (update which contacts are in campaigns)",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="mautic_add_contact_to_campaign",
            description="Add contact to a specific campaign",
            inputSchema={
                "type": "object",
                "properties": {
                    "contact_id": {"type": "integer"},
                    "campaign_id": {"type": "integer"}
                },
                "required": ["contact_id", "campaign_id"]
            }
        ),

        # Email Management (4 tools)
        Tool(
            name="mautic_send_email_queue",
            description="Process email queue and send pending emails",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="mautic_send_broadcast",
            description="Send a broadcast email to segment",
            inputSchema={
                "type": "object",
                "properties": {
                    "broadcast_id": {"type": "integer"}
                },
                "required": ["broadcast_id"]
            }
        ),
        Tool(
            name="mautic_get_emails",
            description="Get list of email templates",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 20}
                }
            }
        ),
        Tool(
            name="mautic_send_email_to_contact",
            description="Send specific email to a contact",
            inputSchema={
                "type": "object",
                "properties": {
                    "email_id": {"type": "integer"},
                    "contact_id": {"type": "integer"}
                },
                "required": ["email_id", "contact_id"]
            }
        ),

        # Maintenance & Monitoring (4 tools)
        Tool(
            name="mautic_cleanup_old_data",
            description="Clean up old data (visitors, logs, stats older than specified days)",
            inputSchema={
                "type": "object",
                "properties": {
                    "days_old": {"type": "integer", "default": 30}
                }
            }
        ),
        Tool(
            name="mautic_update_ip_database",
            description="Update IP lookup database for geolocation",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="mautic_process_webhooks",
            description="Process queued webhook events",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="mautic_get_stats",
            description="Get Mautic statistics and metrics (contacts, campaigns, segments, emails)",
            inputSchema={"type": "object", "properties": {}}
        ),

        # Import/Export (2 tools)
        Tool(
            name="mautic_import_contacts",
            description="Import contacts from CSV file",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"}
                },
                "required": ["file_path"]
            }
        ),
        Tool(
            name="mautic_process_import_queue",
            description="Process queued import jobs",
            inputSchema={"type": "object", "properties": {}}
        ),
    ]

# ============================================================================
# Main entry point
# ============================================================================

async def main():
    """Run the Mautic Admin MCP server"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
