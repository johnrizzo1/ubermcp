#!/usr/bin/env bash
set -e

echo "Starting Uber MCP Server..."
echo "Current directory: $(pwd)"
echo "DEVENV_ROOT: $DEVENV_ROOT"
echo "PYTHONPATH: $PYTHONPATH"

# Change to project root
cd "$DEVENV_ROOT" || exit 1

# Set Python path
export PYTHONPATH="$DEVENV_ROOT/src:$PYTHONPATH"

# Run the server
exec uvicorn src.main:create_app --factory --host 0.0.0.0 --port 8080 --reload