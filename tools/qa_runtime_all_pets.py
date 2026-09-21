import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication

from window_pet_app import assets as assets_module
from window_pet_app import state
from window_pet_app.assets import AssetType, SUPPORTED_VIDEO_EXTENSIONS, detect_asset
from window_pet_app.overlay import MOUSE_TRIGGER_ACTIONS, MOUSE_TRIGGER_ORDER, OverlayWindow


REQUIRED_BASIC_ANIMATIONS = (
    "idle",
    "click",
    "drag",
)


def natural_key(path):
    import re

    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", Path(path).name)]


def player_is_stopped(window):
    if window.asset_type == AssetType.FRAME_ANIMATION:
        return window.frame_player is not None and not window.frame_player.timer.isActive()
    if window.asset_type == AssetType.SPRITESHEET:
        return window.sprite_player is not None and not window.sprite_player.timer.isActive()
    return window.asset_type not in {AssetType.VIDEO}


def video_source_is_selected(player, source):
    return player is not None and getattr(player, "current_source", None) == source.resolve()


def verify_idle_playback(window, check):
    """Verify the expected idle mode without treating video playback as a failure."""
    if window.asset_type == AssetType.VIDEO:
        player = getattr(window, "video_player", None)
        check(
            "video idle player",
            video_source_is_selected(player, window.asset_path),
            "video player did not select the asset source",
        )
        check("video idle pixmap", not window.current_pixmap.isNull(), "video idle rendered a null pixmap")
        return

    video_source = None
    if window.asset_type == AssetType.FRAME_ANIMATION:
        video_source = window.animation_video_source("idle")
    if video_source is not None:
        check(
            "video idle audio source",
            video_source_is_selected(getattr(window, "video_audio_player", None), video_source),
            "video audio player did not select the idle source",
        )
        frame_player = getattr(window, "frame_player", None)
        video_player = getattr(window, "video_action_player", None)
        visual_running = bool(frame_player and frame_player.timer.isActive()) or video_source_is_selected(
            video_player, video_source
        )
        check("video idle visual playback", visual_running, "video-backed idle is not playing")
        return

    check("idle stopped", player_is_stopped(window), "idle playback timer is active")


def verify_pet(asset_path, app):
    checks = []
    errors = []
    window = None

    def check(name, condition, detail=""):
        checks.append({"name": name, "passed": bool(condition), "detail": "" if condition else str(detail)})
        if not condition:
            errors.append(f"{name}: {detail}" if detail else name)

    try:
        asset = detect_asset(asset_path)
        check("runtime parser", asset is not None, "detect_asset returned None")
        if asset is None:
            return {"folder": asset_path.name, "passed": False, "checks": checks, "errors": errors}

        window = OverlayWindow(
            asset,
            {
                "physics_enabled": False,
                "always_on_top": False,
                "x": 40,
                "y": 40,
                "scale": 50,
            },
        )
        window.show()
        app.processEvents()

        check("window created", window.isVisible(), "offscreen window did not become visible")
        check("static idle policy", window.prefers_calm_static_idle(), "calm static idle is disabled")
        check("idle selected", window.current_frame_animation == "idle", window.current_frame_animation)
        verify_idle_playback(window, check)
        check("idle pixmap", not window.current_pixmap.isNull(), "idle rendered a null pixmap")

        metadata = asset.metadata or {}
        head_track_mode = metadata.get("interaction_mode") == "head_track"
        available = tuple(window.available_animations())
        video_mode = asset.type == AssetType.VIDEO
        if head_track_mode:
            check("head-track grid", len(window.head_track_frames) == 25, len(window.head_track_frames))
        elif video_mode:
            check("video asset mode", window.video_player is not None, "video player was not created")
        else:
            missing_basics = sorted(set(REQUIRED_BASIC_ANIMATIONS) - set(available))
            check("three basic animations", not missing_basics, repr(missing_basics))
        manual_actions = window.named_action_items()
        check(
            "named manual actions",
            all(name and label for name, label in manual_actions),
            repr(manual_actions),
        )

        if not head_track_mode:
            for trigger_name in MOUSE_TRIGGER_ORDER:
                expected_animation = MOUSE_TRIGGER_ACTIONS[trigger_name]
                played = window.play_mouse_trigger_action(
                    trigger_name,
                    loop=trigger_name == "left-drag",
                    return_to_idle=trigger_name != "left-drag",
                )
                app.processEvents()
                check(f"trigger {trigger_name}", played, f"could not play {expected_animation}")
                check(
                    f"selected {trigger_name}",
                    window.current_frame_animation == expected_animation,
                    f"expected {expected_animation}, got {window.current_frame_animation}",
                )
                check(f"pixmap {trigger_name}", not window.current_pixmap.isNull(), "rendered a null pixmap")

        window.play_idle_animation()
        app.processEvents()
        check("returned to idle", window.current_frame_animation == "idle", window.current_frame_animation)
        if window.asset_type == AssetType.VIDEO or window.animation_video_source("idle") is not None:
            verify_idle_playback(window, check)
        else:
            check("returned idle stopped", player_is_stopped(window), "idle playback timer is active")

        return {
            "folder": asset_path.name,
            "name": asset.name,
            "character_id": window.character_id,
            "asset_type": asset.type,
            "passed": not errors,
            "checks": checks,
            "errors": errors,
        }
    except Exception as exc:
        errors.append(f"exception: {type(exc).__name__}: {exc}")
        return {"folder": asset_path.name, "passed": False, "checks": checks, "errors": errors}
    finally:
        if window is not None:
            window.stop_playback()
            window.close()
            window.deleteLater()
            app.processEvents()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--assets", type=Path, default=Path("assets"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    app = QApplication.instance() or QApplication([])
    state.WINDOWS = []
    state.MEDAL_STORE = None

    with tempfile.TemporaryDirectory(prefix="windowpet-runtime-qa-") as temp_dir:
        assets_module.CONFIG_PATH = Path(temp_dir) / "config.json"
        pet_dirs = sorted(
            (
                path
                for path in args.assets.iterdir()
                if path.is_dir() and (path / "asset.json").exists()
            ),
            key=natural_key,
        )
        direct_videos = sorted(
            (
                path
                for path in args.assets.iterdir()
                if path.is_file() and path.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS
            ),
            key=natural_key,
        )
        pets = [verify_pet(asset_path.resolve(), app) for asset_path in [*pet_dirs, *direct_videos]]

    report = {
        "pet_count": len(pets),
        "required_basic_animations": list(REQUIRED_BASIC_ANIMATIONS),
        "trigger_mapping": dict(MOUSE_TRIGGER_ACTIONS),
        "passed": bool(pets) and all(pet["passed"] for pet in pets),
        "pets": pets,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "pet_count": report["pet_count"],
                "passed": report["passed"],
                "failed": [pet["folder"] for pet in pets if not pet["passed"]],
            },
            ensure_ascii=False,
        )
    )
    app.quit()
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
