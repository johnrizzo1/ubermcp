#!/usr/bin/env python3
"""Add Uber MCP Server to Claude Desktop configuration."""

import json
import os
import sys

# Path to Claude Desktop config
config_path = os.path.expanduser(
    "~/Library/Application Support/Claude/claude_desktop_config.json"
)

# Read current config
try:
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"Error: Claude Desktop config not found at {config_path}")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON in config file: {e}")
    sys.exit(1)

# Add our server using stdio bridge (since HTTP is being rejected)
if "mcpServer" not in config:
    config["mcpServer"] = {}

# Add the uber-mcp-server using the stdio bridge
config["mcpServer"]["uber-mcp-server"] = {
    "command": "/Users/jrizzo/Projects/ai/agents/ubermcp/run_mcp_bridge.sh"
}

# Alternative: Try adding with full path
# config["mcpServer"]["uber-mcp-server"] = {
#     "command": "bash",
#     "args": [
#         "-c",
#         "cd /Users/jrizzo/Projects/ai/agents/ubermcp && ./run_mcp_bridge.sh"
#     ]
# }

# Write updated config
try:
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    print("✅ Successfully added uber-mcp-server to Claude Desktop config")
    print(
        "📝 Using stdio bridge at: /Users/jrizzo/Projects/ai/agents/ubermcp/run_mcp_bridge.sh"
    )
    print("🔄 Please restart Claude Desktop completely (Cmd+Q and reopen)")
    print("\n⚠️  Make sure the FastAPI server is running first: nix run")
except Exception as e:
    print(f"Error writing config: {e}")
    sys.exit(1)
