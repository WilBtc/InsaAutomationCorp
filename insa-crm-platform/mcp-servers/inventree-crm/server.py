#!/usr/bin/env python3
"""
InvenTree MCP Server for INSA Automation
Provides inventory management and BOM tracking for industrial automation projects

Author: INSA Automation Corp
Created: October 17, 2025
License: MIT
"""

import asyncio
import json
import logging
import os
import requests
from typing import Any, Optional, Dict
from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import Field

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("inventree-crm-mcp")

class InvenTreeServer:
    """InvenTree MCP Server for inventory and BOM management"""

    def __init__(self):
        self.server = Server("inventree-crm")
        self.base_url = os.getenv("INVENTREE_URL", "http://100.100.101.1:9600")
        self.username = os.getenv("INVENTREE_USERNAME", "admin")
        self.password = os.getenv("INVENTREE_PASSWORD", "insaadmin2025")
        self.api_token = None
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json"
        })

        self.setup_handlers()
        logger.info(f"InvenTree MCP Server initialized - Base URL: {self.base_url}")

    def authenticate(self):
        """Authenticate with InvenTree API and get token"""
        if self.api_token:
            return

        logger.info("Authenticating with InvenTree API...")

        # InvenTree uses session-based authentication
        # First, get CSRF token
        response = self.session.get(f"{self.base_url}/api/")
        if response.status_code != 200:
            raise Exception(f"Failed to connect to InvenTree: {response.status_code}")

        # Login via web form to get session cookie
        login_url = f"{self.base_url}/accounts/login/"
        response = self.session.get(login_url)

        # Extract CSRF token from cookies
        csrf_token = self.session.cookies.get('csrftoken')
        if csrf_token:
            self.session.headers.update({'X-CSRFToken': csrf_token})

        # Post login credentials
        login_data = {
            'username': self.username,
            'password': self.password,
            'csrfmiddlewaretoken': csrf_token
        }
        response = self.session.post(login_url, data=login_data, headers={'Referer': login_url})

        if response.status_code == 200 and 'sessionid' in self.session.cookies:
            logger.info("Successfully authenticated with InvenTree")
            self.api_token = "session_auth"  # Mark as authenticated
        else:
            logger.error(f"Authentication failed: {response.status_code}")
            raise Exception("InvenTree authentication failed")

    def api_call(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
        """Make authenticated API call to InvenTree"""
        self.authenticate()

        url = f"{self.base_url}{endpoint}"

        try:
            if method == "GET":
                response = self.session.get(url, params=data)
            elif method == "POST":
                response = self.session.post(url, json=data)
            elif method == "PUT":
                response = self.session.put(url, json=data)
            elif method == "DELETE":
                response = self.session.delete(url)
            else:
                return {"error": f"Unsupported method: {method}"}

            if response.status_code in [200, 201]:
                return response.json()
            else:
                logger.error(f"API call failed: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}: {response.text[:200]}"}

        except Exception as e:
            logger.error(f"API call exception: {e}")
            return {"error": str(e)}

    # Tool: List Parts
    async def list_parts(self, filters: Optional[Dict] = None, limit: int = 50) -> str:
        """List parts inventory with optional filters"""
        params = {"limit": limit}

        if filters:
            # Common filters: category, active, IPN (Internal Part Number), assembly, purchaseable
            for key, value in filters.items():
                params[key] = value

        result = self.api_call("/api/part/", "GET", params)

        if "error" in result:
            return f"Error listing parts: {result['error']}"

        if "results" in result:
            parts = result["results"]
            parts_summary = []

            for part in parts:
                part_type = "📦 Assembly" if part.get('assembly') else "🔧 Component"
                status = "✅ Active" if part.get('active') else "❌ Inactive"
                stock = part.get('total_in_stock', 0)

                parts_summary.append(
                    f"• {part.get('name', 'N/A')} (IPN: {part.get('IPN', 'N/A')})\n"
                    f"  Type: {part_type} | Status: {status}\n"
                    f"  Category: {part.get('category_name', 'Uncategorized')}\n"
                    f"  Stock: {stock} {part.get('units', 'pcs')}\n"
                    f"  Description: {part.get('description', 'N/A')[:80]}...\n"
                )

            return f"Found {len(parts)} parts (total: {result.get('count', len(parts))}):\n\n" + "\n".join(parts_summary)
        else:
            return "No parts found"

    # Tool: Get Part Details
    async def get_part_details(self, part_id: int) -> str:
        """Get detailed part specifications, stock levels, and pricing"""
        result = self.api_call(f"/api/part/{part_id}/", "GET")

        if "error" in result:
            return f"Error getting part details: {result['error']}"

        part = result

        # Format part details
        part_info = (
            f"Part Details:\n"
            f"Name: {part.get('name', 'N/A')}\n"
            f"IPN: {part.get('IPN', 'N/A')}\n"
            f"Description: {part.get('description', 'N/A')}\n"
            f"Category: {part.get('category_name', 'Uncategorized')}\n"
            f"Units: {part.get('units', 'pcs')}\n"
            f"\nStock Information:\n"
            f"Total in Stock: {part.get('total_in_stock', 0)} {part.get('units', 'pcs')}\n"
            f"Minimum Stock: {part.get('minimum_stock', 0)} {part.get('units', 'pcs')}\n"
            f"Allocated: {part.get('allocated_to_build_orders', 0)} {part.get('units', 'pcs')}\n"
            f"Available: {part.get('unallocated_stock', 0)} {part.get('units', 'pcs')}\n"
            f"\nAttributes:\n"
            f"Assembly: {'Yes' if part.get('assembly') else 'No'}\n"
            f"Component: {'Yes' if part.get('component') else 'No'}\n"
            f"Purchaseable: {'Yes' if part.get('purchaseable') else 'No'}\n"
            f"Salable: {'Yes' if part.get('salable') else 'No'}\n"
            f"Active: {'Yes' if part.get('active') else 'No'}\n"
            f"Virtual: {'Yes' if part.get('virtual') else 'No'}\n"
        )

        # Get pricing if available
        pricing_result = self.api_call(f"/api/part/{part_id}/pricing/", "GET")
        if "error" not in pricing_result and pricing_result:
            part_info += f"\nPricing:\n"
            if 'purchase_cost_min' in pricing_result:
                part_info += f"Purchase Cost: ${pricing_result.get('purchase_cost_min', 0):.2f} - ${pricing_result.get('purchase_cost_max', 0):.2f}\n"
            if 'sale_price_min' in pricing_result:
                part_info += f"Sale Price: ${pricing_result.get('sale_price_min', 0):.2f} - ${pricing_result.get('sale_price_max', 0):.2f}\n"

        return part_info

    # Tool: Create BOM
    async def create_bom(self, assembly_part_id: int, bom_items: list) -> str:
        """Create Bill of Materials for an assembly part"""
        if not isinstance(bom_items, list) or len(bom_items) == 0:
            return "Error: bom_items must be a non-empty list"

        created_items = []
        errors = []

        for item in bom_items:
            bom_data = {
                "part": assembly_part_id,
                "sub_part": item.get("sub_part_id"),
                "quantity": item.get("quantity", 1),
                "reference": item.get("reference", ""),
                "note": item.get("note", "")
            }

            result = self.api_call("/api/bom/", "POST", bom_data)

            if "error" in result:
                errors.append(f"Failed to add {item.get('sub_part_id')}: {result['error']}")
            else:
                created_items.append(f"✓ Added part {item.get('sub_part_id')} (Qty: {item.get('quantity', 1)})")

        summary = f"BOM Creation Summary for Part {assembly_part_id}:\n\n"
        summary += f"Successfully added: {len(created_items)}\n"
        summary += "\n".join(created_items)

        if errors:
            summary += f"\n\nErrors: {len(errors)}\n"
            summary += "\n".join(errors)

        return summary

    # Tool: Get Pricing
    async def get_pricing(self, parts_list: list) -> str:
        """Calculate total cost for a list of parts with quantities"""
        if not isinstance(parts_list, list) or len(parts_list) == 0:
            return "Error: parts_list must be a non-empty list with format [{'part_id': 1, 'quantity': 5}, ...]"

        total_cost = 0.0
        pricing_details = []
        errors = []

        for item in parts_list:
            part_id = item.get("part_id")
            quantity = item.get("quantity", 1)

            if not part_id:
                errors.append("Missing part_id in item")
                continue

            # Get part details for pricing
            pricing_result = self.api_call(f"/api/part/{part_id}/pricing/", "GET")

            if "error" in pricing_result:
                errors.append(f"Part {part_id}: {pricing_result['error']}")
                continue

            # Use average purchase cost
            purchase_cost_min = pricing_result.get('purchase_cost_min', 0)
            purchase_cost_max = pricing_result.get('purchase_cost_max', 0)
            avg_cost = (purchase_cost_min + purchase_cost_max) / 2 if purchase_cost_max > 0 else purchase_cost_min

            item_total = avg_cost * quantity
            total_cost += item_total

            # Get part name
            part_result = self.api_call(f"/api/part/{part_id}/", "GET")
            part_name = part_result.get('name', f'Part {part_id}') if "error" not in part_result else f'Part {part_id}'

            pricing_details.append(
                f"• {part_name}\n"
                f"  Qty: {quantity} x ${avg_cost:.2f} = ${item_total:.2f}"
            )

        summary = "Pricing Calculation:\n\n"
        summary += "\n".join(pricing_details)
        summary += f"\n\n{'='*40}\n"
        summary += f"Total Cost: ${total_cost:,.2f}"

        if errors:
            summary += f"\n\nErrors:\n"
            summary += "\n".join(errors)

        return summary

    # Tool: Track Customer Equipment
    async def track_customer_equipment(self, customer_name: str) -> str:
        """List all equipment/parts installed at a customer location"""
        # Search for stock items assigned to customer
        params = {
            "customer": customer_name,
            "limit": 100
        }

        result = self.api_call("/api/stock/", "GET", params)

        if "error" in result:
            return f"Error tracking customer equipment: {result['error']}"

        if "results" in result and len(result["results"]) > 0:
            items = result["results"]
            equipment_list = []

            for item in items:
                part_id = item.get('part')

                # Get part details
                part_result = self.api_call(f"/api/part/{part_id}/", "GET")
                part_name = part_result.get('name', 'Unknown') if "error" not in part_result else 'Unknown'

                equipment_list.append(
                    f"• {part_name}\n"
                    f"  Serial Number: {item.get('serial', 'N/A')}\n"
                    f"  Quantity: {item.get('quantity', 0)} {item.get('units', 'pcs')}\n"
                    f"  Location: {item.get('location_name', 'Unknown')}\n"
                    f"  Status: {item.get('status_text', 'Unknown')}\n"
                    f"  Notes: {item.get('notes', 'N/A')[:80]}...\n"
                )

            return f"Equipment installed at {customer_name} ({len(items)} items):\n\n" + "\n".join(equipment_list)
        else:
            return f"No equipment found for customer: {customer_name}"

    def setup_handlers(self):
        """Setup MCP server handlers"""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="inventree_list_parts",
                    description="List parts from inventory with optional filters (category, active, IPN, assembly, purchaseable)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "filters": {
                                "type": "object",
                                "description": "Filters like {'category': 1, 'active': True, 'assembly': False}",
                            },
                            "limit": {
                                "type": "number",
                                "description": "Maximum number of parts to return",
                                "default": 50
                            }
                        }
                    }
                ),
                Tool(
                    name="inventree_get_part_details",
                    description="Get detailed part specifications, stock levels, and pricing information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "part_id": {
                                "type": "number",
                                "description": "Part ID"
                            }
                        },
                        "required": ["part_id"]
                    }
                ),
                Tool(
                    name="inventree_create_bom",
                    description="Create Bill of Materials for an assembly part by adding sub-components",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "assembly_part_id": {
                                "type": "number",
                                "description": "ID of the assembly part that contains sub-components"
                            },
                            "bom_items": {
                                "type": "array",
                                "description": "List of sub-components to add to BOM",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "sub_part_id": {
                                            "type": "number",
                                            "description": "ID of the sub-component part"
                                        },
                                        "quantity": {
                                            "type": "number",
                                            "description": "Quantity required",
                                            "default": 1
                                        },
                                        "reference": {
                                            "type": "string",
                                            "description": "Reference designator (e.g., 'R1', 'C2')"
                                        },
                                        "note": {
                                            "type": "string",
                                            "description": "Additional notes"
                                        }
                                    }
                                }
                            }
                        },
                        "required": ["assembly_part_id", "bom_items"]
                    }
                ),
                Tool(
                    name="inventree_get_pricing",
                    description="Calculate total cost for a list of parts with quantities",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "parts_list": {
                                "type": "array",
                                "description": "List of parts with quantities",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "part_id": {
                                            "type": "number",
                                            "description": "Part ID"
                                        },
                                        "quantity": {
                                            "type": "number",
                                            "description": "Quantity needed",
                                            "default": 1
                                        }
                                    }
                                }
                            }
                        },
                        "required": ["parts_list"]
                    }
                ),
                Tool(
                    name="inventree_track_customer_equipment",
                    description="List all equipment/parts installed at a specific customer location",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "customer_name": {
                                "type": "string",
                                "description": "Customer name to search for"
                            }
                        },
                        "required": ["customer_name"]
                    }
                ),
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            try:
                if name == "inventree_list_parts":
                    result = await self.list_parts(
                        filters=arguments.get("filters"),
                        limit=arguments.get("limit", 50)
                    )
                elif name == "inventree_get_part_details":
                    result = await self.get_part_details(arguments["part_id"])
                elif name == "inventree_create_bom":
                    result = await self.create_bom(
                        assembly_part_id=arguments["assembly_part_id"],
                        bom_items=arguments["bom_items"]
                    )
                elif name == "inventree_get_pricing":
                    result = await self.get_pricing(arguments["parts_list"])
                elif name == "inventree_track_customer_equipment":
                    result = await self.track_customer_equipment(arguments["customer_name"])
                else:
                    result = f"Unknown tool: {name}"

                return [TextContent(type="text", text=result)]

            except Exception as e:
                logger.error(f"Tool execution error: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

async def main():
    """Main entry point for InvenTree MCP server"""
    server = InvenTreeServer()

    # Run the server using stdin/stdout streams
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        logger.info("InvenTree MCP Server starting...")
        await server.server.run(
            read_stream,
            write_stream,
            server.server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
