#!/usr/bin/env python3
"""Wrapper for MCP bridge that ensures clean stdio communication."""

import asyncio
import os
import sys

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Set Python path
sys.path.insert(0, "src")

# Import and run the bridge
from mcp_stdio_bridge import main  # pylint: disable=wrong-import-position

if __name__ == "__main__":
    asyncio.run(main())
