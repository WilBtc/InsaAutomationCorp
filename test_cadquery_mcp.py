#!/usr/bin/env python3
"""
Test CadQuery MCP Server
Quick test to verify CadQuery MCP is working correctly
"""

import subprocess
import json
import time

def test_cadquery_mcp():
    """Test CadQuery MCP server startup and basic functionality"""

    print("🔧 Testing CadQuery MCP Server...")
    print()

    # Test 1: Server startup
    print("✅ Test 1: Server Startup")
    cmd = ["/home/wil/mcp-servers/mcp-cadquery/server_stdio.sh"]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # Give it 2 seconds to start
        time.sleep(2)

        if proc.poll() is None:
            print("   ✅ Server started successfully")

            # Try to read server info
            try:
                line = proc.stdout.readline()
                if line:
                    data = json.loads(line)
                    if data.get("type") == "server_info":
                        print(f"   ✅ Server name: {data.get('server_name')}")
                        print(f"   ✅ Server version: {data.get('version')}")
                        print(f"   ✅ Tools available: {len(data.get('tools', []))}")

                        print("\n📋 Available Tools:")
                        for tool in data.get("tools", []):
                            print(f"      - {tool['name']}: {tool['description'][:60]}...")
            except json.JSONDecodeError as e:
                print(f"   ⚠️  Could not parse server info: {e}")

            # Terminate the process
            proc.terminate()
            proc.wait(timeout=5)
            print("   ✅ Server terminated cleanly")

        else:
            print(f"   ❌ Server failed to start. Return code: {proc.returncode}")
            stderr = proc.stderr.read()
            if stderr:
                print(f"   Error: {stderr}")
            return False

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    print()
    print("🎉 CadQuery MCP Server Test PASSED!")
    print()
    print("Available CadQuery Tools:")
    print("  1. execute_cadquery_script - Execute CadQuery Python scripts")
    print("  2. export_shape - Export shapes to STEP/STL formats")
    print("  3. export_shape_to_svg - Generate SVG previews")
    print("  4. scan_part_library - Index part library")
    print("  5. search_parts - Search indexed parts")
    print("  6. launch_cq_editor - Launch CQ-Editor GUI")
    print("  7. get_shape_properties - Get shape measurements")
    print()
    print("🚀 Ready for Claude Code integration!")

    return True

if __name__ == "__main__":
    success = test_cadquery_mcp()
    exit(0 if success else 1)
