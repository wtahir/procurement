from fastapi.testclient import TestClient

from apps.api.main import app as api_app


def api_client() -> TestClient:
    return TestClient(api_app)
