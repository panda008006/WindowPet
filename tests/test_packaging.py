from pathlib import Path
import json
import runpy

from PySide6.QtGui import QImageReader

from window_pet_app.assets import detect_asset
from window_pet_app.overlay import MOUSE_TRIGGER_ACTIONS


def test_pyinstaller_spec_includes_assets_bundle():
    spec = Path("WindowPet.spec").read_text(encoding="utf-8")

    assert '(str(ROOT / "assets"), "assets")' in spec
    assert '(str(ROOT / "AI角色制作"), "AI角色制作")' in spec
    assert '(str(ROOT / "AGENTS.md"), ".")' in spec
    assert '(str(ROOT / "CLAUDE.md"), ".")' in spec
    assert '(str(ROOT / "update_config.json"), ".")' in spec
    assert 'copy2(ROOT / "update_config.json", EXTERNAL_ROOT / "update_config.json")' in spec
    assert 'copytree(ROOT / "AI角色制作", EXTERNAL_ROOT / "AI角色制作"' in spec


def test_master_sheet_authoring_tools_are_in_the_packaged_guide():
    guide = Path("AI角色制作")

    assert (guide / "START_HERE.md").is_file()
    assert (guide / "master_sheet_prompt.md").is_file()
    assert (guide / "master_sheet_schema.json").is_file()
    assert (guide / "build_character_from_sheet.py").is_file()
    assert "Pillow" in (guide / "requirements.txt").read_text(encoding="utf-8")


def test_requested_builtin_pets_exist_in_assets_bundle():
    for folder in (
        "LuluCapybaraPet",
        "XiaobaPet",
        "UsagiPet",
        "JiyiPet",
        "NuonuoPet",
        "PenguinSisterPet",
        "MianmianPet",
        "XiaochaiPet",
        "SalaryCatPet",
    ):
        assert (Path("assets") / folder).is_dir()


def test_pyinstaller_spec_includes_tool_assets():
    assert (Path("assets") / "ToolAssets").is_dir()
    assert (Path("assets") / "UiAssets" / "doubao-avatar.png").is_file()
    assert (Path("assets") / "UiAssets" / "doubao-local-computer-guide.png").is_file()


def test_reference_image_authoring_contract_is_bundled():
    guide = Path("AI角色制作") / "reference_image_mode.md"
    action_guide = Path("AI角色制作") / "action_design_mode.md"
    quality = json.loads((Path("AI角色制作") / "质量标准.json").read_text(encoding="utf-8"))

    assert guide.is_file()
    assert action_guide.is_file()
    assert "Do not redraw, redesign" in guide.read_text(encoding="utf-8")
    action_text = action_guide.read_text(encoding="utf-8")
    assert "Moving, scaling, rotating, fading, or shaking" in action_text
    assert "Do not paste glasses, wands, stars" in action_text
    assert quality["reference_image_policy"]["mode"] == "reference_first"
    assert quality["reference_image_policy"]["attach_reference_to_every_action_job"] is True


def test_reference_image_contract_requires_action_motion_policy():
    quality = json.loads((Path("AI角色制作") / "质量标准.json").read_text(encoding="utf-8"))

    assert quality["action_motion_policy"]["forbid_whole_image_scaling_only"] is True
    assert quality["action_motion_policy"]["require_all_basic_actions"] is True
    assert quality["action_motion_policy"]["require_idle_independent_frames"] is True
    assert quality["action_motion_policy"]["require_frame_level_pose_changes"] is True
    assert quality["action_motion_policy"]["image_generation_provider"] == "user_configured_api_or_account"
    assert quality["action_motion_policy"]["forbid_overlay_icons"] is True


def test_character_validator_rejects_shared_required_action_folders(tmp_path):
    validator = runpy.run_path(str(Path("AI角色制作") / "validate_character.py"))
    actions = ("idle", "click", "drag")
    metadata = {
        "type": "frame_animation",
        "preview": "missing.png",
        "animations": {
            name: {"folder": "shared", "fps": 10, "loop": name in {"idle", "drag"}}
            for name in actions
        },
    }
    (tmp_path / "asset.json").write_text(json.dumps(metadata), encoding="utf-8")

    errors, _warnings = validator["validate"](tmp_path)

    assert any("three independent frame folders" in error for error in errors)


def test_character_validator_accepts_head_track_special_mode():
    validator = runpy.run_path(str(Path("AI角色制作") / "validate_character.py"))

    errors, warnings = validator["validate"](Path("assets") / "XiaobaTurnPet")

    assert errors == []
    assert warnings == []


def test_every_packaged_pet_supports_all_fixed_interaction_actions():
    required_actions = {"idle", *MOUSE_TRIGGER_ACTIONS.values()}
    assert len(required_actions) == 3

    missing_by_pet = {}
    for asset_json in sorted(Path("assets").glob("*/asset.json")):
        metadata = json.loads(asset_json.read_text(encoding="utf-8-sig"))
        if metadata.get("interaction_mode") == "head_track":
            assert "idle" in metadata.get("animations", {})
            continue
        animations = metadata.get("animations", {})
        available = set(animations)
        missing = sorted(required_actions - available)
        if missing:
            missing_by_pet[asset_json.parent.name] = missing
            continue

        for action_name in required_actions:
            definition = animations[action_name]
            if metadata.get("type") == "spritesheet":
                assert definition.get("frames"), f"{asset_json.parent.name}:{action_name} has no frames"
                continue
            folder = asset_json.parent / str(definition.get("folder") or ".")
            assert next(folder.glob("*.png"), None), f"{asset_json.parent.name}:{action_name} has no PNG frames"

    assert missing_by_pet == {}


def test_every_packaged_pet_manifest_loads_through_the_real_runtime_parser():
    required_actions = {"idle", *MOUSE_TRIGGER_ACTIONS.values()}

    for asset_json in sorted(Path("assets").glob("*/asset.json")):
        asset = detect_asset(asset_json.parent)
        if (asset.metadata or {}).get("interaction_mode") == "head_track":
            assert "idle" in (asset.metadata or {}).get("animations", {})
            continue
        animations = (asset.metadata or {}).get("animations", {})

        assert required_actions.issubset(animations), asset_json.parent.name


def test_legacy_right_double_click_alias_is_never_a_mouse_trigger():
    assert "right-double-click" not in MOUSE_TRIGGER_ACTIONS.values()


def assert_finished_pets_have_animation(animation_name: str):
    for folder in (
        "LuluCapybaraPet",
        "XiaobaPet",
        "UsagiPet",
        "JiyiPet",
        "PandaPet",
        "PenguinSisterPet",
        "NuonuoPet",
        "HuhuPet",
        "Huhu2Pet",
        "MianmianPet",
        "XiaochaiPet",
    ):
        asset_dir = Path("assets") / folder
        metadata = json.loads((asset_dir / "asset.json").read_text(encoding="utf-8-sig"))
        animation = metadata["animations"].get(animation_name)

        assert animation == {"folder": animation_name, "fps": 12, "loop": False}

        frame_dir = asset_dir / animation_name
        frames = sorted(frame_dir.glob("*.png"))
        assert len(frames) == 8
        for frame in frames:
            size = QImageReader(str(frame)).size()
            assert size.width() == 192
            assert size.height() == 208


def test_finished_pets_have_feather_tickle_animation():
    assert_finished_pets_have_animation("feather-tickle")


def test_finished_pets_have_whip_hit_animation():
    assert_finished_pets_have_animation("whip-hit")


def test_codex_spritesheet_pets_have_windowpet_interactions():
    required = {
        "idle": 6,
        "running-right": 8,
        "running-left": 8,
        "waving": 4,
        "jumping": 5,
        "failed": 8,
        "waiting": 6,
        "running": 6,
        "review": 6,
        "hover": 6,
        "click": 5,
        "drag": 6,
        "reward": 4,
        "whip-hit": 8,
        "feather-tickle": 6,
    }

    for folder in ("BearPet", "BubuPet", "BuyaPet", "KunLikePet", "NezukoPet"):
        asset_dir = Path("assets") / folder
        metadata = json.loads((asset_dir / "asset.json").read_text(encoding="utf-8-sig"))

        assert metadata["type"] == "spritesheet"
        assert metadata["image"] == "spritesheet.webp"
        assert (asset_dir / "spritesheet.webp").is_file()

        animations = metadata["animations"]
        for animation_name, frame_count in required.items():
            animation = animations.get(animation_name)
            assert animation is not None
            assert len(animation["frames"]) == frame_count

        assert animations["click"]["source_animation"] == "jumping"
        assert animations["drag"]["source_animation"] == "running"
