"""
Concurrency busy-path test: simulate semaphore timeout returning 503.
We stub predict() to raise the same HTTPException the service emits on timeout.
"""
import importlib
import base64
import types
import sys

import pytest
from fastapi import FastAPI, HTTPException
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
def test_detect_file_busy_returns_503(monkeypatch):
    monkeypatch.setenv("ENABLE_BREED_API", "true")
    svc = importlib.import_module("src.services.breed_detection")

    # Model is reported as loaded
    monkeypatch.setattr(
        svc,
        "get_model_info",
        lambda: {"loaded": True, "model_version": "test", "device": "cpu", "num_breeds": 5},
    )

    # Simulate busy/timeout behavior from service layer
    async def busy_predict(*_, **__):
        raise HTTPException(status_code=503, detail="Breed detection busy, please retry")

    monkeypatch.setattr(svc, "predict", busy_predict)

    # Stub a minimal PIL.Image.open so route can parse the upload
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

    app = make_app()
    client = TestClient(app)

    content = create_png_bytes()
    files = {"file": ("dog.png", content, "image/png")}
    r = client.post("/api/v1/breed/detect-file", files=files)
    assert r.status_code == 503
    body = r.json()
    # FastAPI wraps detail into {"detail": "..."}
    assert "busy" in (body.get("detail") or "").lower()
