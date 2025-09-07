"""
Detect-file endpoint test with stubbed predict() to avoid heavy ML deps.
"""
import importlib
import base64
import types
import sys
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def make_app():
    breed = importlib.import_module("src.api.routes.breed")
    app = FastAPI()
    app.include_router(breed.router, prefix="/api/v1")
    return app


def create_png_bytes():
    # 1x1 PNG pixel (transparent)
    b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/6XGdbYAAAAASUVORK5CYII="
    return base64.b64decode(b64)


@pytest.mark.sprint_c
def test_detect_file_success(monkeypatch):
    monkeypatch.setenv("ENABLE_BREED_API", "true")
    # Stub model loaded info and predict
    svc = importlib.import_module("src.services.breed_detection")
    monkeypatch.setattr(svc, "get_model_info", lambda: {"loaded": True, "model_version": "test", "device": "cpu", "num_breeds": 5})

    async def fake_predict(image, confidence_threshold: float = 0.8, top_k: int = 5):
        return {
            "predicted_breed": "labrador",
            "confidence": 0.91,
            "top_predictions": [{"labrador": 0.91}, {"poodle": 0.05}],
            "is_high_confidence": True,
            "model_version": "test",
        }

    monkeypatch.setattr(svc, "predict", fake_predict)

    app = make_app()
    client = TestClient(app)

    # Provide a minimal PIL.Image stub so the route can import and call .open
    class _FakeImage:
        def __init__(self):
            self.mode = "RGB"
            self.size = (1, 1)

        def convert(self, mode: str):
            return self

    def _fake_open(_):
        return _FakeImage()

    pil_module = types.ModuleType("PIL")
    image_module = types.ModuleType("PIL.Image")
    setattr(image_module, "open", _fake_open)
    setattr(pil_module, "Image", image_module)
    sys.modules["PIL"] = pil_module
    sys.modules["PIL.Image"] = image_module

    content = create_png_bytes()
    files = {"file": ("dog.png", content, "image/png")}
    r = client.post("/api/v1/breed/detect-file", files=files)
    assert r.status_code == 200
    data = r.json()
    assert data["predicted_breed"] == "labrador"
    assert data["confidence"] >= 0.9
    assert data["model_version"] == "test"


@pytest.mark.sprint_c
def test_detect_file_rejects_non_image(monkeypatch):
    monkeypatch.setenv("ENABLE_BREED_API", "true")
    svc = importlib.import_module("src.services.breed_detection")
    monkeypatch.setattr(svc, "get_model_info", lambda: {"loaded": True})

    app = make_app()
    client = TestClient(app)

    files = {"file": ("not-image.txt", b"hello", "text/plain")}
    r = client.post("/api/v1/breed/detect-file", files=files)
    assert r.status_code == 400
