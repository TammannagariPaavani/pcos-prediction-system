"""API smoke tests."""

from fastapi.testclient import TestClient

from app.main import app


def test_health_check_returns_ok():
    """Health endpoint should return a basic readiness response."""

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
