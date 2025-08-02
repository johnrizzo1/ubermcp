#!/usr/bin/env bash
# Final MCP bridge runner using nix develop python directly

cd "$(dirname "$0")"

# Use nix develop to get the python with all dependencies, but suppress all output
exec nix develop --quiet --command python mcp_bridge_wrapper.py 2>/tmp/mcp_bridge_errors.log