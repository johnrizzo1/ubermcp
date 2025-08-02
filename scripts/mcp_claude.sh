#!/usr/bin/env bash
# Ultra-simple MCP bridge for Claude - no banners, no noise

cd "$(dirname "$0")"

# Get the Python path from nix, but suppress ALL output except stdout from our script
PYTHON_BIN=$(nix develop --quiet --command which python 2>/dev/null)

# If that fails, try to find it in the result
if [ -z "$PYTHON_BIN" ]; then
    PYTHON_BIN=$(find /nix/store -name python3.13 -type f -executable 2>/dev/null | grep python3-3.13.3-env | head -1)
fi

# Run our bridge with clean output
export PYTHONPATH="./src:$PYTHONPATH"
exec "$PYTHON_BIN" mcp_bridge_wrapper.py 2>/tmp/mcp_bridge.log