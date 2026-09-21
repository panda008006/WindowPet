import base64
import json
import zipfile
from pathlib import Path

import pytest

from window_pet_app import cloud_api
from window_pet_app.character_acquisition import (
    CharacterAcquisitionError,
    build_doubao_image_prompt,
    build_doubao_prompt,
    install_character_archive,
)


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
)


def test_doubao_prompt_requires_direct_install_to_explicit_character_package_path(tmp_path):
    app_root = tmp_path / "WindowPet"
    assets_root = app_root / "assets"
    target = assets_root / "{角色英文名}Pet"

    prompt = build_doubao_prompt(app_root, assets_root)

    assert prompt.splitlines()[0] == "我创建这个角色是XXX。"
    assert str(app_root / "AI角色制作" / "AI先读我.md") in prompt
    assert str(app_root / "AI角色制作" / "质量标准.json") in prompt
    assert str(assets_root) in prompt
    assert str(target) in prompt
    assert "角色包最终地址" in prompt
    assert "直接创建" in prompt
    assert "不要只返回教程、提示词、预览图或压缩包" in prompt
    assert "每个动作默认 6 帧" in prompt
    assert "validate_character.py" in prompt
    assert "ZIP" not in prompt


def test_doubao_prompt_uses_the_users_character_description(tmp_path):
    app_root = tmp_path / "another-users-windowpet"
    assets_root = tmp_path / "another-users-library"

    prompt = build_doubao_prompt(app_root, assets_root, "一只戴红围巾、会弹吉他的白色小猫")

    assert prompt.splitlines()[0] == "我创建这个角色是一只戴红围巾、会弹吉他的白色小猫。"
    assert str(assets_root.resolve()) in prompt


def test_doubao_prompt_forces_reference_image_first_frame_workflow(tmp_path):
    app_root = tmp_path / "WindowPet"
    prompt = build_doubao_prompt(app_root, tmp_path / "assets")

    assert "REFERENCE IMAGE MODE (MANDATORY)" in prompt
    assert "authoritative source of truth" in prompt
    assert "Do not redraw, redesign, reinterpret" in prompt
    assert "every animation frame" in prompt
    assert "If the reference image cannot be accessed, stop and ask" in prompt
    assert str((app_root / "AI角色制作" / "reference_image_mode.md").resolve()) in prompt


def test_doubao_prompt_requires_real_action_design_for_all_triggers(tmp_path):
    prompt = build_doubao_prompt(tmp_path / "WindowPet", tmp_path / "assets")

    assert "ACTION DESIGN MODE (MANDATORY)" in prompt
    assert "Do not fake animation with only scale, zoom, translation, opacity, or whole-image wobble" in prompt
    assert "research 3-5 recognizable" in prompt
    assert "idle, click for left_click, and drag for left_drag" in prompt
    assert "anticipation, action, and settle" in prompt
    assert "meaningful pose, limb, expression, or prop change" in prompt
    assert "one image per frame" in prompt
    assert str((tmp_path / "WindowPet" / "AI角色制作" / "action_design_mode.md").resolve()) in prompt


def test_doubao_prompt_requires_configured_full_frame_generation_not_overlay_compositing(tmp_path):
    prompt = build_doubao_prompt(tmp_path / "WindowPet", tmp_path / "assets")

    assert "image-generation or image-editing API/account configured" in prompt
    assert "one complete full-frame character image per frame" in prompt
    assert "Do not overlay icons, stickers, props, badges, or separate PNGs" in prompt
    assert "Compose/package frames only after the full images are generated" in prompt
    assert "If the configured provider cannot use the reference image, stop" in prompt


def test_doubao_prompt_drives_one_master_sheet_then_local_automatic_install(tmp_path):
    app_root = tmp_path / "WindowPet"
    assets_root = app_root / "assets"

    prompt = build_doubao_prompt(app_root, assets_root, "一只白色小猫")

    assert str(app_root / "AI角色制作" / "START_HERE.md") in prompt
    assert str(app_root / "AI角色制作" / "master_sheet_prompt.md") in prompt
    assert str(app_root / "AI角色制作" / "build_character_from_sheet.py") in prompt
    assert "6 列 × 3 行" in prompt
    assert "18 格" in prompt
    assert "一张主精灵图" in prompt
    assert "不要让我手动裁剪、拆帧、配置或导入" in prompt
    assert "--sheet" in prompt
    assert "--display-name" in prompt
    assert "--character-id" in prompt
    assert "--assets-root" in prompt
    assert "原子安装" in prompt


def test_character_archive_rejects_path_traversal(tmp_path):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("../outside.png", PNG_1X1)

    with pytest.raises(CharacterAcquisitionError, match="不安全"):
        install_character_archive(archive, tmp_path / "assets")

    assert not (tmp_path / "outside.png").exists()


def test_valid_character_archive_installs_as_one_complete_folder(tmp_path):
    archive = tmp_path / "MomoPet.zip"
    metadata = {
        "type": "frame_animation",
        "name": "桃桃",
        "fps": 12,
        "preview": "frame_01.png",
        "animations": {"idle": {"folder": ".", "fps": 12, "loop": True}},
    }
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("MomoPet/asset.json", json.dumps(metadata, ensure_ascii=False))
        bundle.writestr("MomoPet/frame_01.png", PNG_1X1)
        bundle.writestr("MomoPet/frame_02.png", PNG_1X1)

    installed = install_character_archive(archive, tmp_path / "assets")

    assert installed == tmp_path / "assets" / "MomoPet"
    assert json.loads((installed / "asset.json").read_text(encoding="utf-8"))["name"] == "桃桃"
    assert (installed / "frame_01.png").read_bytes() == PNG_1X1


def test_character_archive_does_not_overwrite_existing_role(tmp_path):
    assets_root = tmp_path / "assets"
    existing = assets_root / "MomoPet"
    existing.mkdir(parents=True)
    marker = existing / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    archive = tmp_path / "MomoPet.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("MomoPet/asset.json", '{"type":"frame_animation","name":"桃桃"}')
        bundle.writestr("MomoPet/frame_01.png", PNG_1X1)
        bundle.writestr("MomoPet/frame_02.png", PNG_1X1)

    with pytest.raises(CharacterAcquisitionError, match="已经存在"):
        install_character_archive(archive, assets_root)

    assert marker.read_text(encoding="utf-8") == "keep"


def test_redeem_404_is_reported_as_not_open_without_fake_success(monkeypatch):
    def missing_endpoint(*args, **kwargs):
        raise cloud_api.CloudApiError("Not found")

    monkeypatch.setattr(cloud_api, "request_json", missing_endpoint)

    with pytest.raises(cloud_api.CloudApiError, match="尚未开放"):
        cloud_api.redeem_character("WP-TEST-1", "token")


def test_build_doubao_image_prompt_returns_clear_chinese_art_guidelines():
    prompt = build_doubao_image_prompt("一只会发光的赛博小熊")
    assert "一只会发光的赛博小熊" in prompt
    assert "纯白背景" in prompt
    assert "九宫格动作工坊" in prompt
    assert "idle" in prompt
    assert "click" in prompt
    assert "drag" in prompt
