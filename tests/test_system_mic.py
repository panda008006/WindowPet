import os
import pytest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication

from window_pet_app import assets as assets_module
from window_pet_app import state
from window_pet_app.assets import detect_asset
from window_pet_app.overlay import OverlayWindow
from window_pet_app.system_mic import (
    get_microphone_muted,
    set_microphone_muted,
    toggle_microphone_muted,
    is_system_mic_available,
)


@pytest.fixture
def mock_pet_dir(tmp_path):
    pet_dir = tmp_path / "MicTestPet"
    pet_dir.mkdir()

    app = QApplication.instance() or QApplication([])
    from PySide6.QtGui import QColor, QImage
    img = QImage(32, 32, QImage.Format_ARGB32)
    img.fill(QColor(100, 200, 120))
    img.save(str(pet_dir / "frame_01.png"))

    import json
    meta = {
        "type": "frame_animation",
        "name": "麦克风测试宠",
        "fps": 10,
        "preview": "frame_01.png",
        "animations": {
            "idle": {"folder": ".", "fps": 10, "loop": True}
        }
    }
    (pet_dir / "asset.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    return pet_dir


def test_system_mic_manager_get_set_toggle():
    # 保证初始为开麦状态 (False)
    set_microphone_muted(False)
    assert get_microphone_muted() is False

    # 闭麦
    res = set_microphone_muted(True)
    assert res is True
    assert get_microphone_muted() is True

    # 再次开麦
    set_microphone_muted(False)
    assert get_microphone_muted() is False

    # 一键切换闭麦
    new_state = toggle_microphone_muted()
    assert new_state is True
    assert get_microphone_muted() is True

    # 再次切换开麦
    new_state = toggle_microphone_muted()
    assert new_state is False
    assert get_microphone_muted() is False


def test_overlay_mic_badge_and_toggle(mock_pet_dir, monkeypatch, tmp_path):
    app = QApplication.instance() or QApplication([])
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(assets_module, "CONFIG_PATH", config_path)
    monkeypatch.setattr(assets_module, "SETTINGS_PATH", config_path)
    monkeypatch.setattr(state, "WINDOWS", [])

    set_microphone_muted(False)

    asset = detect_asset(mock_pet_dir)
    assert asset is not None
    window = OverlayWindow(asset, {"physics_enabled": False})
    state.WINDOWS.append(window)
    window.show()

    # 1. 验证存在悬浮麦克风小徽标
    assert hasattr(window, "mic_badge")
    assert window.mic_badge.text() == "🎙️"

    # 2. 调用 toggle_microphone_mute
    window.toggle_microphone_mute()
    assert get_microphone_muted() is True
    assert window.mic_badge.text() == "🔇"
    assert "闭麦" in window._transient_speech

    # 3. 再次调用，恢复开麦
    window.toggle_microphone_mute()
    assert get_microphone_muted() is False
    assert window.mic_badge.text() == "🎙️"
    assert "开麦" in window._transient_speech

    # 4. 测试直接鼠标单击悬浮麦克风按钮
    QTest.mouseClick(window.mic_badge, Qt.LeftButton)
    assert get_microphone_muted() is True
    assert window.mic_badge.text() == "🔇"

    # 5. 右键显现徽标
    window.mic_badge.reveal()
    assert window.mic_badge.isVisible()

    window.close()
    window.deleteLater()
    app.processEvents()


def test_character_default_sound_muted_and_toggle(mock_pet_dir, monkeypatch, tmp_path):
    """测试所有角色在刚下载时默认静音，并支持一键开启/静音角色声音"""
    app = QApplication.instance() or QApplication([])
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(assets_module, "CONFIG_PATH", config_path)
    monkeypatch.setattr(assets_module, "SETTINGS_PATH", config_path)
    monkeypatch.setattr(state, "WINDOWS", [])

    asset = detect_asset(mock_pet_dir)
    assert asset is not None
    # 刚下载/初始创建，配置中没有 sound_muted
    window = OverlayWindow(asset, {"physics_enabled": False})
    state.WINDOWS.append(window)

    # 1. 验证刚下载时所有角色默认静音 (sound_muted is True)
    assert window.sound_muted is True
    assert window.to_config()["sound_muted"] is True

    # 2. 一键切换开启声音
    window.toggle_sound_muted()
    assert window.sound_muted is False
    assert "声音已开启" in window._transient_speech
    assert window.to_config()["sound_muted"] is False

    # 3. 再次切换恢复静音
    window.toggle_sound_muted()
    assert window.sound_muted is True
    assert "已静音" in window._transient_speech
    assert window.to_config()["sound_muted"] is True

    window.close()
    window.deleteLater()
    app.processEvents()

