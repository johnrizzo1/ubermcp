#!/usr/bin/env python3
"""Test the MCP bridge to ensure it's working correctly."""

import json
import subprocess
import sys

# Test message
test_message = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}

# Run the bridge
with subprocess.Popen(
    ["./run_mcp_bridge.sh"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.DEVNULL,
    text=True,
) as process:
    # Send test message
    if process.stdin is None:
        print("Error: stdin is not available")
        sys.exit(1)

    process.stdin.write(json.dumps(test_message) + "\n")
    process.stdin.flush()

    # Read response
    if process.stdout is None:
        print("Error: stdout is not available")
        sys.exit(1)

    response_line = process.stdout.readline()

    # Parse and display
    try:
        response = json.loads(response_line)
        print("✅ Bridge is working!")
        print(f"📊 Found {len(response['result']['tools'])} tools")
        print("\n🔧 Available tools:")
        for tool in response["result"]["tools"]:
            print(f"  - {tool['name']}: {tool['description']}")
    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Response was: {response_line}")
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Response was: {response_line}")

    # Cleanup
    process.terminate()
