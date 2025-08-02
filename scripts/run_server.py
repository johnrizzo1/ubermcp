#!/usr/bin/env python
"""Simple wrapper to start the server with proper imports."""
import os
import sys

# Add src to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import uvicorn  # pylint: disable=wrong-import-position

if __name__ == "__main__":
    uvicorn.run(
        "src.main:create_app",
        factory=True,
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info",
    )
