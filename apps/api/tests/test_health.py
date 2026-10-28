from fastapi.testclient import TestClient
from apps.api.src.main import app

def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "AttendX AI" in data["name"]
    assert "ZEAL College" in data["institution"]


def test_health_check_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["services"]["database"]["status"] == "healthy"
    assert data["services"]["qr_crypto_validator"]["status"] == "operational"
    assert data["services"]["geofence_engine"]["status"] == "operational"
    assert data["services"]["biometric_verifier"]["status"] == "operational"

