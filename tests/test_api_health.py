"""Unit tests for FastAPI application health and root endpoints."""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint() -> None:
    """Test the root metadata endpoint returns operational status."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "UrbanTwin"
    assert data["status"] == "operational"


def test_basic_health_endpoint() -> None:
    """Test liveness probe endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
