import os
import sys
import importlib
import pytest
from fastapi.testclient import TestClient
from api_server_minimal import app  # Adjust import if needed

# Ensure repository root is importable for grok_client module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@pytest.fixture
def client(monkeypatch):
    # Ensure constructor doesn't fail due to missing env
    monkeypatch.setenv("GROK_API_KEY", "test-key")
    return TestClient(app)


def test_grok_query_success(client, monkeypatch):
    def mock_query(self, prompt, model="grok-beta", max_tokens=512, temperature=0.3):
        return f"MOCK RESPONSE for: {prompt}"

    mod = importlib.import_module("grok_client")
    monkeypatch.setattr(getattr(mod, "GrokClient"), "query", mock_query)

    response = client.post("/api/v1/grok/query", json={"prompt": "Test prompt"})
    assert response.status_code == 200
    assert response.json() == {"response": "MOCK RESPONSE for: Test prompt"}


def test_grok_query_error(client, monkeypatch):
    def mock_query(self, prompt, model="grok-beta", max_tokens=512, temperature=0.3):
        raise ValueError("Mock error")

    mod = importlib.import_module("grok_client")
    monkeypatch.setattr(getattr(mod, "GrokClient"), "query", mock_query)

    response = client.post("/api/v1/grok/query", json={"prompt": "Test prompt"})
    # Endpoint raises HTTPException(502, detail=...) on failure
    assert response.status_code == 502
    body = response.json()
    assert isinstance(body, dict)
    assert "detail" in body
    assert "Grok query failed" in body.get("detail", "")
