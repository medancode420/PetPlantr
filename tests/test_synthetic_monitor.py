import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ["ENABLE_SYNTHETIC_MONITOR"] = "true"


@pytest.mark.sprint_c
def test_synthetic_live_enabled_returns_status():
	# Ensure repository root is importable
	repo_root = Path(__file__).resolve().parents[1]
	if str(repo_root) not in sys.path:
		sys.path.insert(0, str(repo_root))

	from api_server import app

	with TestClient(app) as client:
		resp = client.get("/api/v1/ops/synthetic/live")
		assert resp.status_code == 200
		data = resp.json()
		assert data.get("enabled") is True
		assert isinstance(data.get("ok"), bool)
		assert "latency_s" in data
		assert "running" in data
