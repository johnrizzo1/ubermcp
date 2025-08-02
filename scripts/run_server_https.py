#!/usr/bin/env python3
"""Run the FastAPI server with HTTPS support."""
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    import uvicorn

    # Check if certificates exist
    cert_path = Path("certs/server.crt")
    key_path = Path("certs/server.key")

    if not cert_path.exists() or not key_path.exists():
        print("SSL certificates not found. Please run ./generate_certs.sh first")
        sys.exit(1)

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=9543,  # Custom HTTPS port to avoid conflicts
        ssl_keyfile=str(key_path),
        ssl_certfile=str(cert_path),
        reload=True,
        log_level="info",
    )
