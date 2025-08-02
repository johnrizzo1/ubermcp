#!/usr/bin/env bash
# Development shell wrapper to bypass bashrc issues

echo "Starting development shell (bypassing bashrc)..."
exec nix develop --command bash --norc