#!/usr/bin/env bash
# Wrapper script to run MCP bridge without the nix banner

# Change to project directory
cd "$(dirname "$0")"

# Run nix develop and filter out the banner
# The banner ends with a line containing "Server:", so we skip everything until after that
exec nix develop --command python src/mcp_stdio_bridge.py 2>&1 | awk '
BEGIN { skip=1 }
/Server:/ { skip=0; next }
!skip { print }
'