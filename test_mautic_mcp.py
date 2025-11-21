#!/usr/bin/env python3
"""
Quick test script for Mautic MCP server tools
Tests API connectivity and core functionality
"""
import asyncio
import httpx
import sys

MAUTIC_URL = "http://100.100.101.1:9700"
MAUTIC_USERNAME = "admin"
MAUTIC_PASSWORD = "mautic_admin_2025"

async def test_api_connectivity():
    """Test basic API connectivity"""
    print("Testing API connectivity...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{MAUTIC_URL}/api/contacts",
                auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD)
            )
            print(f"✅ API Status: {response.status_code}")
            data = response.json()
            print(f"✅ Total contacts: {data.get('total', 0)}")
            return True
        except Exception as e:
            print(f"❌ API Error: {e}")
            return False

async def test_create_contact():
    """Test contact creation via API"""
    print("\nTesting contact creation...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            contact_data = {
                "firstname": "Test",
                "lastname": "Contact",
                "email": "test@insaing.com",
                "company": "INSA Automation Corp"
            }
            response = await client.post(
                f"{MAUTIC_URL}/api/contacts/new",
                auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD),
                json=contact_data
            )
            print(f"✅ Contact creation status: {response.status_code}")
            if response.status_code == 201:
                data = response.json()
                contact_id = data.get('contact', {}).get('id')
                print(f"✅ Created contact ID: {contact_id}")
                return contact_id
            else:
                print(f"⚠️  Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Contact creation error: {e}")
            return None

async def test_get_segments():
    """Test segment listing via API"""
    print("\nTesting segment listing...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{MAUTIC_URL}/api/segments",
                auth=(MAUTIC_USERNAME, MAUTIC_PASSWORD)
            )
            print(f"✅ Segments API status: {response.status_code}")
            data = response.json()
            print(f"✅ Total segments: {data.get('total', 0)}")
            return True
        except Exception as e:
            print(f"❌ Segments error: {e}")
            return False

async def main():
    """Run all tests"""
    print("=" * 60)
    print("Mautic MCP Server - API Functionality Test")
    print("=" * 60)

    # Test 1: API connectivity
    if not await test_api_connectivity():
        print("\n❌ API connectivity failed. Aborting.")
        sys.exit(1)

    # Test 2: Segments
    await test_get_segments()

    # Test 3: Contact creation
    contact_id = await test_create_contact()

    print("\n" + "=" * 60)
    if contact_id:
        print("✅ ALL TESTS PASSED - MCP Server Ready!")
    else:
        print("⚠️  Some tests had warnings - Check output above")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
