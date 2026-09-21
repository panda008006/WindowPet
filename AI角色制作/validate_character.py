from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path


REQUIRED_ACTIONS = {"idle", "click", "drag"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v"}


def load_quality_profile() -> dict:
    path = Path(__file__).with_name("质量标准.json")
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}


def natural_key(path: Path) -> list[object]:
    import re

    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]


def png_info(path: Path) -> tuple[int, int, int] | None:
    try:
        with path.open("rb") as handle:
            header = handle.read(29)
        if len(header) < 29 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
            return None
        width, height = struct.unpack(">II", header[16:24])
        colour_type = header[25]
        return width, height, colour_type
    except OSError:
        return None


def validate(character_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    metadata_path = character_dir / "asset.json"
    if not metadata_path.is_file():
        return [f"缺少 {metadata_path}"], warnings

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"asset.json 无法读取：{exc}"], warnings

    quality = load_quality_profile()
    action_profile = quality.get("required_actions", {})
    special_mode = str(metadata.get("interaction_mode") or "").strip().lower()
    is_head_track = special_mode == "head_track"
    required_actions = {"idle", "head_track"} if special_mode == "head_track" else (set(action_profile) or REQUIRED_ACTIONS)
    if metadata.get("type") != "frame_animation":
        errors.append("type 必须为 frame_animation")
    animations = metadata.get("animations")
    if not isinstance(animations, dict):
        return errors + ["animations 必须是对象"], warnings

    _validate_video_sources(character_dir, metadata, animations, errors)

    missing = sorted(required_actions - set(animations))
    if missing:
        errors.append("缺少当前版本所需基础动作：" + ", ".join(missing))

    required_folders: dict[str, str] = {}
    for action_name in sorted(required_actions):
        definition = animations.get(action_name)
        if not isinstance(definition, dict):
            continue
        folder_value = definition.get("folder")
        if not isinstance(folder_value, str) or not folder_value:
            continue
        previous_action = required_folders.get(folder_value)
        if previous_action is not None:
            errors.append(
                f"required actions must use three independent frame folders: "
                f"{previous_action} and {action_name} both use {folder_value}"
            )
        else:
            required_folders[folder_value] = action_name

    canvas_sizes: set[tuple[int, int]] = set()
    for name, definition in animations.items():
        if not isinstance(definition, dict):
            errors.append(f"动作 {name} 的配置不是对象")
            continue
        folder_value = definition.get("folder")
        if not isinstance(folder_value, str) or not folder_value:
            errors.append(f"动作 {name} 缺少 folder")
            continue
        folder = character_dir if folder_value == "." else character_dir / folder_value
        if not folder.is_dir():
            errors.append(f"动作 {name} 的文件夹不存在：{folder_value}")
            continue
        excluded = {"preview.png", "spritesheet.png"}
        frames = sorted(
            (
                path
                for path in folder.iterdir()
                if path.is_file()
                and path.suffix.lower() == ".png"
                and (folder_value != "." or path.name.lower() not in excluded)
            ),
            key=natural_key,
        )
        if not frames:
            videos = [
                path
                for path in folder.iterdir()
                if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
            ]
            if videos:
                warnings.append(f"动作 {name} 使用视频源，将保留原视频声音")
                continue
            errors.append(f"动作 {name} 没有 PNG 帧或视频源")
            continue
        if not is_head_track:
            limits = action_profile.get(name, {})
            minimum = int(limits.get("min_frames", 0))
            if minimum and len(frames) < minimum:
                warnings.append(f"动作 {name} 有 {len(frames)} 帧，默认建议至少 {minimum} 帧")
            elif len(frames) < 4:
                warnings.append(f"动作 {name} 只有 {len(frames)} 帧，可能显得生硬")
            expected_loop = limits.get("loop")
            if expected_loop is not None and bool(definition.get("loop")) != bool(expected_loop):
                errors.append(f"动作 {name} 的 loop 应为 {str(expected_loop).lower()}")
        if is_head_track and name == "head_track" and len(frames) != 25:
            errors.append(f"head_track 必须正好有 25 帧，当前为 {len(frames)} 帧")
        action_sizes: set[tuple[int, int]] = set()
        for frame in frames:
            info = png_info(frame)
            if info is None:
                errors.append(f"不是有效 PNG：{frame.relative_to(character_dir)}")
                continue
            width, height, colour_type = info
            action_sizes.add((width, height))
            canvas_sizes.add((width, height))
            if colour_type not in {4, 6}:
                warnings.append(f"{frame.relative_to(character_dir)} 可能没有透明通道")
        if len(action_sizes) > 1:
            errors.append(f"动作 {name} 内存在不同画布尺寸：{sorted(action_sizes)}")

    if len(canvas_sizes) > 1:
        errors.append(f"角色不同动作的画布尺寸不一致：{sorted(canvas_sizes)}")
    elif canvas_sizes and next(iter(canvas_sizes)) != (192, 208) and not is_head_track:
        warnings.append(f"当前画布为 {next(iter(canvas_sizes))}，推荐使用 (192, 208)")

    preview = metadata.get("preview")
    if not isinstance(preview, str) or not (character_dir / preview).is_file():
        errors.append("preview 指向的图片不存在")

    if special_mode == "head_track":
        return errors, warnings

    return errors, warnings


def _validate_video_sources(character_dir: Path, metadata: dict, animations: dict, errors: list[str]) -> None:
    """校验音频来源只能是角色包内部的受支持视频文件。"""
    values = {}
    video_sources = metadata.get("video_sources")
    if isinstance(video_sources, dict):
        values.update(video_sources)
    for action_name, definition in animations.items():
        if isinstance(definition, dict):
            value = definition.get("video") or definition.get("video_source")
            if value:
                values.setdefault(action_name, value)

    for action_name, value in values.items():
        if not isinstance(value, str) or not value.strip():
            errors.append(f"动作 {action_name} 的视频来源路径无效")
            continue
        source = Path(value)
        if source.is_absolute() or any(part in {"", ".", ".."} for part in source.parts):
            errors.append(f"动作 {action_name} 的视频来源路径不安全：{value}")
            continue
        resolved = (character_dir / source).resolve()
        try:
            resolved.relative_to(character_dir.resolve())
        except ValueError:
            errors.append(f"动作 {action_name} 的视频来源路径不安全：{value}")
            continue
        if resolved.suffix.lower() not in VIDEO_EXTENSIONS:
            errors.append(f"动作 {action_name} 的视频来源格式不支持：{value}")
        elif not resolved.is_file():
            errors.append(f"动作 {action_name} 的视频来源文件不存在：{value}")


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 WindowPet 角色文件夹")
    parser.add_argument("character_dir", type=Path)
    args = parser.parse_args()
    character_dir = args.character_dir.resolve()
    errors, warnings = validate(character_dir)
    print(f"角色：{character_dir}")
    profile = load_quality_profile()
    png_count = sum(1 for path in character_dir.rglob("*.png") if path.is_file())
    role_bytes = sum(path.stat().st_size for path in character_dir.rglob("*") if path.is_file())
    print(
        f"质控档：{profile.get('profile', 'built-in')}；PNG：{png_count} 张；"
        f"目录体积：{role_bytes / 1024 / 1024:.2f} MB"
    )
    for message in errors:
        print(f"ERROR   {message}")
    for message in warnings:
        print(f"WARNING {message}")
    if not errors and not warnings:
        print("OK      未发现结构问题")
    else:
        print(f"结果：{len(errors)} 个错误，{len(warnings)} 个警告")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
