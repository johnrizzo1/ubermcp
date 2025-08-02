#!/usr/bin/env python3
"""Update Claude config to use the direct bridge runner."""

import json
import os

config_path = os.path.expanduser(
    "~/Library/Application Support/Claude/claude_desktop_config.json"
)

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

# Update the command
config["mcpServer"]["uber-mcp-server"][
    "command"
] = "/Users/jrizzo/Projects/ai/agents/ubermcp/run_mcp_bridge_direct.sh"

with open(config_path, "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)

print("✅ Updated Claude config to use direct bridge runner")
