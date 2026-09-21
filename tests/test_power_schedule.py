import os
from datetime import datetime, timedelta
from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from window_pet_app import state
from window_pet_app.assets import detect_asset
from window_pet_app.control_panel import ControlPanel
from window_pet_app.overlay import OverlayWindow


def test_overlay_power_schedule_settings(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    asset_dir = tmp_path / "assets" / "TestPet"
    asset_dir.mkdir(parents=True)

    img = QImage(32, 32, QImage.Format_ARGB32)
    img.fill(QColor(100, 200, 120))
    img.save(str(asset_dir / "frame_01.png"))

    (asset_dir / "asset.json").write_text(
        '{"name": "测试桌宠", "type": "frame_animation", "preview": "frame_01.png", "animations": {"idle": {"folder": ".", "fps": 10}}}',
        encoding="utf-8"
    )

    monkeypatch.setattr(state, "ASSETS_DIR", tmp_path / "assets")
    from window_pet_app import assets, control_panel
    monkeypatch.setattr(assets, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(control_panel, "CONFIG_PATH", tmp_path / "config.json")

    asset = detect_asset(asset_dir)
    overlay = OverlayWindow(asset)
    try:
        assert overlay.power_action_label() == ""
        assert overlay.parse_power_due_at() is None

        target = datetime.now() + timedelta(minutes=30)
        overlay.set_power_schedule("sleep", target)
        assert overlay.power_action_type == "sleep"
        assert overlay.power_action_label() == "待机"
        assert overlay.parse_power_due_at() is not None

        overlay.cancel_power_schedule()
        assert overlay.power_action_type == ""
        assert overlay.power_action_label() == ""
        assert overlay.parse_power_due_at() is None
    finally:
        overlay.close()


def test_control_panel_power_schedule_handlers(tmp_path, monkeypatch):
    from window_pet_app import assets, control_panel
    monkeypatch.setattr(assets, "CONFIG_PATH", tmp_path / "config.json")
    monkeypatch.setattr(control_panel, "CONFIG_PATH", tmp_path / "config.json")
    app = QApplication.instance() or QApplication([])
    panel = ControlPanel()
    try:
        assert hasattr(panel, "schedule_power_after_minutes_from_panel")
        assert hasattr(panel, "schedule_power_at_time_from_panel")
        assert hasattr(panel, "cancel_power_schedule_from_panel")
    finally:
        panel.close()
