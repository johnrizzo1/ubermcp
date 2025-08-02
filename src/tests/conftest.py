import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.main import create_app

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def api_client():
    return TestClient(create_app())
