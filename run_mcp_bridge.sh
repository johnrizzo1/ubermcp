#!/usr/bin/env bash
# Script to run the MCP stdio bridge

# Ensure we're in the project directory
cd "$(dirname "$0")"

# Suppress the shellHook banner by redirecting stdout during nix develop initialization
# Then restore stdout for the actual Python script
exec 3>&1  # Save stdout to fd 3
exec 1>/dev/null  # Redirect stdout to /dev/null
nix develop --quiet --command bash -c 'exec 1>&3 3>&-; exec python src/mcp_stdio_bridge.py'