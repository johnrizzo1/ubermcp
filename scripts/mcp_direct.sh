#!/usr/bin/env bash
# Direct MCP bridge using nix run without shell

cd "$(dirname "$0")"
exec nix run --quiet .#mcp-bridge -- "$@" 2>/tmp/mcp_bridge.log