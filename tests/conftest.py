import os

os.environ["ENV"] = "test"
os.environ["DEBUG"] = "false"
os.environ["CORS_ORIGINS"] = "*"
os.environ["AI_PROVIDER"] = "mock"
os.environ["AI_ENABLED"] = "true"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
