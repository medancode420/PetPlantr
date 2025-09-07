import importlib
from fastapi.testclient import TestClient

def test_health_ok():
    mod = importlib.import_module("api_server_minimal")
    app = getattr(mod, "app")
    client = TestClient(app)
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json().get("ok") is True