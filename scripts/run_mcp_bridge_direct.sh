#!/usr/bin/env bash
# Direct MCP bridge runner without nix develop banner

cd "$(dirname "$0")"

# Run directly with the nix python environment
exec nix run .#mcp-bridge