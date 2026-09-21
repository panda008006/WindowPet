import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from window_pet_app import assets as assets_module
from window_pet_app import control_panel as control_panel_module
from window_pet_app import state
from window_pet_app.control_panel import ControlPanel, LIBRARY_ACTION_ROLE


@pytest.fixture
def panel(monkeypatch, tmp_path):
    app = QApplication.instance() or QApplication([])
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(assets_module, "CONFIG_PATH", config_path)
    monkeypatch.setattr(assets_module, "SETTINGS_PATH", config_path)
    monkeypatch.setattr(control_panel_module, "CONFIG_PATH", config_path)
    monkeypatch.setattr(state, "ASSETS_DIR", Path("assets").resolve())
    monkeypatch.setattr(state, "PET_UNLOCKS", None, raising=False)
    monkeypatch.setattr(state, "WINDOWS", [])
    panel = ControlPanel()
    try:
        yield panel
    finally:
        panel.close()
        panel.deleteLater()
        app.processEvents()


def test_redeem_is_only_exposed_as_the_library_action_card(panel):
    assert not hasattr(panel, "activity_tab_index")
    assert not hasattr(panel, "redeem_input")
    assert "兑换" not in [button.toolTip() for button in panel.tabs.buttons]

    redeem_cards = [
        panel.library_list.item(index)
        for index in range(panel.library_list.count())
        if panel.library_list.item(index).data(LIBRARY_ACTION_ROLE) == "redeem"
    ]
    assert len(redeem_cards) == 1
    assert redeem_cards[0].text() == "兑换角色"
