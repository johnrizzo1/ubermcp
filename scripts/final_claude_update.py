#!/usr/bin/env python3
"""Final update to Claude config with clean bridge."""

import json
import os

config_path = os.path.expanduser(
    "~/Library/Application Support/Claude/claude_desktop_config.json"
)

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

# Update to the final clean runner
config["mcpServer"]["uber-mcp-server"][
    "command"
] = "/Users/jrizzo/Projects/ai/agents/ubermcp/run_mcp_final.sh"

with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)

print("✅ Updated Claude config to use final clean bridge")
print("🔄 Please restart Claude Desktop completely")
print("📝 The bridge will log errors to /tmp/mcp_bridge_errors.log if any occur")
