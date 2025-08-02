#!/usr/bin/env bash
# Wrapper script to run pytest-watch in the correct nix environment

echo "Starting test watcher in nix environment..."
exec nix run .#test-watch