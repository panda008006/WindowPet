import pytest
from window_pet_app import assets, control_panel


@pytest.fixture(autouse=True)
def isolate_test_config(tmp_path, monkeypatch, request):
    if request.node.name == "test_source_mode_paths_are_repo_local":
        return
    test_config = tmp_path / "config.json"
    monkeypatch.setattr(assets, "CONFIG_PATH", test_config)
    monkeypatch.setattr(control_panel, "CONFIG_PATH", test_config)
