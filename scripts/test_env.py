#!/usr/bin/env python
import sys

print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")
print(f"Path: {sys.path}")

try:
    import fastapi  # noqa: F401  # pylint: disable=unused-import

    print("✓ FastAPI imported successfully")
except ImportError as e:
    print(f"✗ FastAPI import failed: {e}")

try:
    from src.main import create_app  # noqa: F401  # pylint: disable=unused-import

    print("✓ src.main.create_app imported successfully")
except ImportError as e:
    print(f"✗ src.main.create_app import failed: {e}")
