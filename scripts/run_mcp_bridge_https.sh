#!/usr/bin/env bash
# Script to run the MCP stdio bridge with HTTPS support

# Ensure we're in the project directory
cd "$(dirname "$0")"

# Run the HTTPS bridge using nix to ensure all dependencies are available
# Suppress the banner by redirecting stderr for nix develop
exec nix develop --command python src/mcp_stdio_bridge_https.py 2>/dev/null