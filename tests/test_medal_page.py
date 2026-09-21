import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication, QFrame, QLabel

from window_pet_app import assets as assets_module
from window_pet_app import control_panel as control_panel_module
from window_pet_app import state
from window_pet_app.control_panel import ControlPanel
from window_pet_app.medals import MedalStore


@pytest.fixture
def panel(monkeypatch, tmp_path):
    app = QApplication.instance() or QApplication([])
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    medal_store = MedalStore(tmp_path / "medals.json")
    medal_store.record_launch()
    monkeypatch.setattr(assets_module, "CONFIG_PATH", config_path)
    monkeypatch.setattr(assets_module, "SETTINGS_PATH", config_path)
    monkeypatch.setattr(control_panel_module, "CONFIG_PATH", config_path)
    monkeypatch.setattr(state, "ASSETS_DIR", Path("assets").resolve())
    monkeypatch.setattr(state, "PET_UNLOCKS", None, raising=False)
    monkeypatch.setattr(state, "MEDAL_STORE", medal_store)
    monkeypatch.setattr(state, "WINDOWS", [])
    panel = ControlPanel()

    try:
        yield panel, medal_store
    finally:
        panel.close()
        panel.deleteLater()
        app.processEvents()


def test_medal_page_is_a_real_cockpit_page_with_nine_optional_medals(panel):
    panel, _store = panel
    page = panel.page_stack.widget(panel.medals_tab_index)
    cards = [frame for frame in page.findChildren(QFrame) if frame.objectName() == "MedalCard"]
    titles = [label.text() for label in page.findChildren(QLabel) if label.objectName() == "MedalCardTitle"]

    assert panel.tabs.buttons[panel.medals_tab_index].toolTip() == "勋章"
    assert len(cards) == 9
    assert titles[:3] == ["第一次回应", "熟悉的身影", "三种回应"]
    assert panel.medals_note_label.text() == "勋章只用于收藏和装扮，不会锁住角色功能。"


def test_medal_page_can_be_hidden_and_restored_without_popup(panel):
    panel, store = panel

    panel.set_medals_hidden(True)
    assert store.hidden is True
    assert panel.medal_grid_widget.isHidden() is True
    assert panel.medals_hidden_card.isHidden() is False

    panel.set_medals_hidden(False)
    assert store.hidden is False
    assert panel.medal_grid_widget.isHidden() is False
    assert panel.medals_hidden_card.isHidden() is True


def test_medal_page_refreshes_after_natural_interaction_progress(panel):
    panel, store = panel
    store.record_trigger("left-click")

    panel.refresh_medals_page()

    assert panel.medal_cards[0]["status"].text() == "已解锁"
    assert "2 / 9" in panel.medals_summary_label.text()
