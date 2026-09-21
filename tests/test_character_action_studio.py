import json
import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from window_pet_app import assets as assets_module
from window_pet_app import state
from window_pet_app.assets import detect_asset, AssetType
from window_pet_app.character_doc_generator import (
    generate_character_action_doc,
    inspect_character_folder,
    sync_character_folder,
)
from window_pet_app.character_action_studio import CharacterActionStudioDialog
from window_pet_app.overlay import OverlayWindow


@pytest.fixture
def test_character_dir(tmp_path):
    pet_dir = tmp_path / "TestPet"
    pet_dir.mkdir()

    app = QApplication.instance() or QApplication([])
    from PySide6.QtGui import QColor, QImage
    img = QImage(32, 32, QImage.Format_ARGB32)
    img.fill(QColor(255, 120, 140))

    # Create root frames for idle
    for i in range(1, 4):
        img.save(str(pet_dir / f"frame_{i:02d}.png"))

    # Create click subfolder
    click_dir = pet_dir / "click"
    click_dir.mkdir()
    for i in range(1, 4):
        img.save(str(click_dir / f"c_{i:02d}.png"))

    # Create dance subfolder
    dance_dir = pet_dir / "dance"
    dance_dir.mkdir()
    for i in range(1, 5):
        img.save(str(dance_dir / f"d_{i:02d}.png"))

    asset_json = {
        "type": "frame_animation",
        "name": "测试小萌宠",
        "fps": 12,
        "preview": "frame_01.png",
        "character_id": "test-pet",
        "animations": {
            "idle": {"folder": ".", "fps": 10, "loop": True, "label": "常规待机"},
            "click": {"folder": "click", "fps": 12, "loop": False, "label": "轻点一下"},
            "dance": {"folder": "dance", "fps": 14, "loop": False, "label": "欢快起舞"},
        },
        "triggers": {
            "left-click": "click",
            "left-double-click": "dance",
        },
        "menu_actions": ["dance"],
    }
    (pet_dir / "asset.json").write_text(json.dumps(asset_json, ensure_ascii=False), encoding="utf-8")
    return pet_dir


def test_inspect_character_folder(test_character_dir):
    info = inspect_character_folder(test_character_dir)
    assert info["name"] == "测试小萌宠"
    assert info["character_id"] == "test-pet"
    assert info["fps"] == 12
    assert info["total_actions"] == 3
    action_names = [a["name"] for a in info["actions"]]
    assert "idle" in action_names
    assert "click" in action_names
    assert "dance" in action_names


def test_generate_character_action_doc(test_character_dir):
    doc = generate_character_action_doc(test_character_dir)
    assert "# 🐾 测试小萌宠" in doc
    assert "| `idle` |" in doc
    assert "| `click` |" in doc
    assert "| `dance` |" in doc
    assert "民间创作者扩展与制作指南" in doc


def test_custom_triggers_in_overlay(test_character_dir, monkeypatch, tmp_path):
    app = QApplication.instance() or QApplication([])
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(assets_module, "CONFIG_PATH", config_path)
    monkeypatch.setattr(assets_module, "SETTINGS_PATH", config_path)
    monkeypatch.setattr(state, "WINDOWS", [])

    asset = detect_asset(test_character_dir)
    assert asset is not None
    window = OverlayWindow(asset, {"physics_enabled": False})

    # Test custom trigger resolution
    candidates = window.trigger_animation_candidates("left-click")
    assert candidates == [("click", 1.0)]

    candidates_double = window.trigger_animation_candidates("left-double-click")
    assert candidates_double == [("dance", 1.0)]

    # Test menu_actions filtering
    named_items = [name for name, _ in window.named_action_items()]
    assert named_items == ["dance"]

    window.close()
    window.deleteLater()
    app.processEvents()


def test_character_action_studio_dialog(test_character_dir):
    app = QApplication.instance() or QApplication([])
    dialog = CharacterActionStudioDialog(test_character_dir)

    # 1. 验证九宫格 9 个槽位全部生成
    assert len(dialog.slot_cards) == 9
    expected_slots = ["idle", "click", "drag", "double_click", "action_1", "action_2", "action_3", "action_4", "action_5"]
    for slot_id in expected_slots:
        assert slot_id in dialog.slot_cards

    # 2. 验证初始动作绑定
    assert dialog.slot_cards["idle"].action_name == "idle"
    assert dialog.slot_cards["click"].action_name == "click"
    assert dialog.slot_cards["double_click"].action_name == "dance"
    assert dialog.is_fixed_idle is False

    # 3. 测试静态模式切换：随机静态 <-> 固定静态
    dialog._on_idle_mode_toggled(True)
    assert dialog.is_fixed_idle is True
    dialog.slot_cards["idle"].set_fixed_idle(True)
    assert "固定静态" in dialog.slot_cards["idle"].idle_toggle_btn.text()

    # 4. 测试修改动作中文名称
    dialog.slot_cards["click"].action_label = "开心戳戳"

    # 5. 测试拖拽外部文件填槽
    from PySide6.QtGui import QColor, QImage
    test_img = QImage(32, 32, QImage.Format_ARGB32)
    test_img.fill(QColor(80, 160, 240))
    imported_file = test_character_dir / "imported_action.png"
    test_img.save(str(imported_file))

    dialog._on_file_dropped_to_slot("action_1", str(imported_file))
    assert (test_character_dir / "waving").exists()

    # 6. 保存并生效
    dialog.save_and_apply()

    # 7. 验证 asset.json 状态
    saved_meta = json.loads((test_character_dir / "asset.json").read_text(encoding="utf-8"))
    assert saved_meta["fixed_idle"] is True
    assert saved_meta["action_labels"]["click"] == "开心戳戳"
    assert saved_meta["triggers"]["left-click"] == "click"
    assert saved_meta["triggers"]["left-double-click"] == "dance"

    # 8. 验证 动作说明.md 生成
    doc_file = test_character_dir / "动作说明.md"
    assert doc_file.exists()
    assert "测试小萌宠" in doc_file.read_text(encoding="utf-8")

    dialog.close()
    dialog.deleteLater()
    app.processEvents()


def test_single_action_character_fallback(tmp_path):
    """测试单动作角色自适应保底：自动填充静态、点击、拖拽槽位"""
    pet_dir = tmp_path / "SinglePet"
    pet_dir.mkdir()

    app = QApplication.instance() or QApplication([])
    from PySide6.QtGui import QColor, QImage
    img = QImage(32, 32, QImage.Format_ARGB32)
    img.fill(QColor(200, 220, 240))
    img.save(str(pet_dir / "frame_01.png"))

    asset_json = {
        "type": "frame_animation",
        "name": "独苗小宠",
        "fps": 8,
        "preview": "frame_01.png",
        "animations": {
            "idle": {"folder": ".", "fps": 8, "loop": True},
        },
    }
    (pet_dir / "asset.json").write_text(json.dumps(asset_json, ensure_ascii=False), encoding="utf-8")

    dialog = CharacterActionStudioDialog(pet_dir)
    assert dialog.slot_cards["idle"].action_name == "idle"
    assert dialog.slot_cards["click"].action_name == "idle"
    assert dialog.slot_cards["drag"].action_name == "idle"
    assert len(dialog.slot_cards["idle"].cached_frames) >= 1
    assert len(dialog.slot_cards["click"].cached_frames) >= 1
    assert len(dialog.slot_cards["drag"].cached_frames) >= 1

    dialog.close()
    dialog.deleteLater()
    app.processEvents()

