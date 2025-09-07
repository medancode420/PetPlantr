import os
import pytest

@pytest.mark.sprint_c
def test_graceful_degradation_toggle_enables_fallback(monkeypatch):
    # Feature flag off -> no degradation
    monkeypatch.setenv("FEATURE_MESH_GOVERNOR", "false")
    from src.core.settings import Settings as S1
    s1 = S1()
    assert s1.feature_mesh_governor is False

    # Feature flag on -> degradation enabled
    monkeypatch.setenv("FEATURE_MESH_GOVERNOR", "true")
    from importlib import reload
    import src.core.settings as settings_mod
    reload(settings_mod)
    assert settings_mod.settings.feature_mesh_governor is True 