import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Fixture qui fournit un client de test avec déclenchement du cycle de vie (lifespan)."""
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    """Vérifie que l'API est en ligne."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_inspect_valid_payload(client):
    """Vérifie qu'une requête valide d'inspection renvoie un code 200 et la structure attendue."""
    payload = {"payload": "' OR '1'='1' --"}
    response = client.post("/api/v1/inspect", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "is_malicious" in data
    assert "action" in data
    assert "confidence" in data
    assert data["action"] in ["ALLOW", "BLOCK"]


def test_inspect_empty_payload(client):
    """Vérifie qu'un payload vide renvoie une erreur 400."""
    payload = {"payload": "   "}
    response = client.post("/api/v1/inspect", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Le payload ne peut pas être vide."
def test_inspect_sql_injection_should_block(client):
    """Vérifie qu'une injection SQL est bien bloquée (BLOCK)."""
    payload = {"payload": "' OR '1'='1' --"}
    response = client.post("/api/v1/inspect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_malicious"] is True
    assert data["action"] == "BLOCK"


def test_inspect_legitimate_request_should_allow(client):
    """Vérifie qu'une requête saine est autorisée (ALLOW)."""
    payload = {"payload": "username=john_doe&page=profile&lang=fr"}
    response = client.post("/api/v1/inspect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_malicious"] is False
    assert data["action"] == "ALLOW"


def test_inspect_missing_payload_field(client):
    """Vérifie le rejet automatique par Pydantic si la clé 'payload' est absente (422)."""
    response = client.post("/api/v1/inspect", json={})
    assert response.status_code == 422