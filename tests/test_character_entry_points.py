import os
import re
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPushButton

from window_pet_app import assets as assets_module
from window_pet_app import control_panel as control_panel_module
from window_pet_app import state
from window_pet_app.control_panel import ControlPanel, DoubaoGuideDialog, LIBRARY_ACTION_ROLE


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


def test_library_ends_with_doubao_and_redeem_cards(panel):
    actions = [
        panel.library_list.item(index).data(LIBRARY_ACTION_ROLE)
        for index in range(panel.library_list.count())
    ]

    assert actions[-2:] == ["doubao", "redeem"]
    assert panel.library_list.item(panel.library_list.count() - 2).text() == "豆包生成"
    assert panel.library_list.item(panel.library_list.count() - 1).text() == "兑换角色"


def test_character_cards_hide_internal_package_numbers(panel):
    visible_pet_names = [
        panel.library_list.item(index).text()
        for index in range(panel.library_list.count())
        if panel.library_list.item(index).data(Qt.UserRole)
    ]

    assert visible_pet_names
    assert all(not re.match(r"^\d{4}\s*·", name) for name in visible_pet_names)


def test_clicking_action_card_dispatches_without_treating_it_as_a_pet(panel, monkeypatch):
    opened = []
    monkeypatch.setattr(panel, "open_doubao_guide", lambda: opened.append("doubao"))
    item = panel.library_list.item(panel.library_list.count() - 2)

    panel.switch_library_asset_to_desktop(item)

    assert opened == ["doubao"]


def test_doubao_dialog_shows_direct_package_path_without_zip_detour(panel, tmp_path, monkeypatch):
    assets_root = tmp_path / "assets"
    dialog = DoubaoGuideDialog("direct prompt", assets_root, lambda _path: None, panel)
    try:
        assert not dialog.doubao_mode_guide_label.pixmap().isNull()
        assert dialog.package_path_label.text() == str(assets_root / "{角色英文名}Pet")
        assert dialog.character_description_input.placeholderText()
        assert dialog.prompt_view.toPlainText().splitlines()[0] == "我创建这个角色是XXX。"
        dialog.character_description_input.setText("会弹吉他的橘猫")
        assert dialog.prompt_view.toPlainText().splitlines()[0] == "我创建这个角色是会弹吉他的橘猫。"
        assert dialog.prompt.splitlines()[0] == "我创建这个角色是会弹吉他的橘猫。"
        monkeypatch.setattr(control_panel_module.QMessageBox, "information", lambda *args: None)
        dialog.copy_prompt()
        assert QApplication.clipboard().text() == dialog.prompt
        monkeypatch.setattr(control_panel_module.QDesktopServices, "openUrl", lambda _url: True)
        dialog.open_doubao()
        assert QApplication.clipboard().text() == dialog.prompt
        assert "导入角色 ZIP" not in [button.text() for button in dialog.findChildren(QPushButton)]
    finally:
        dialog.close()


def test_doubao_dialog_supports_simple_image_mode_switch(panel, tmp_path):
    assets_root = tmp_path / "assets"
    dialog = DoubaoGuideDialog("direct prompt", assets_root, lambda _path: None, panel)
    try:
        dialog.character_description_input.setText("会弹吉他的橘猫")
        dialog.mode_simple_btn.click()
        assert dialog.current_mode == "simple"
        assert "会弹吉他的橘猫" in dialog.prompt_view.toPlainText()
        assert "纯白背景" in dialog.prompt_view.toPlainText()
        assert dialog.doubao_mode_guide_label.isHidden()
        assert dialog.package_path_label.isHidden()

        dialog.mode_auto_btn.click()
        assert dialog.current_mode == "auto"
        assert dialog.prompt_view.toPlainText().splitlines()[0] == "我创建这个角色是会弹吉他的橘猫。"
        assert not dialog.doubao_mode_guide_label.isHidden()
        assert not dialog.package_path_label.isHidden()
    finally:
        dialog.close()


def test_redeem_requires_login_and_stops_when_login_is_cancelled(panel, monkeypatch):
    monkeypatch.setattr(control_panel_module, "logged_in_account", lambda _state: {})
    login_attempts = []
    monkeypatch.setattr(panel, "open_account_dialog", lambda: login_attempts.append(True) and False)
    monkeypatch.setattr(
        control_panel_module,
        "RedeemCharacterDialog",
        lambda *args, **kwargs: pytest.fail("取消登录后不应打开兑换窗口"),
    )

    panel.open_redeem_character()

    assert login_attempts == [True]


def test_redeem_opens_after_successful_login(panel, monkeypatch):
    accounts = iter(({}, {"token": "token-123", "email": "user@example.com"}))
    monkeypatch.setattr(control_panel_module, "logged_in_account", lambda _state: next(accounts))
    monkeypatch.setattr(panel, "open_account_dialog", lambda: True)
    opened = []

    class FakeDialog:
        def __init__(self, token, assets_root, on_installed, parent=None):
            opened.append((token, Path(assets_root), on_installed, parent))

        def exec(self):
            return 0

    monkeypatch.setattr(control_panel_module, "RedeemCharacterDialog", FakeDialog)

    panel.open_redeem_character()

    assert opened[0][0] == "token-123"
    assert opened[0][1] == state.ASSETS_DIR
    assert opened[0][3] is panel
