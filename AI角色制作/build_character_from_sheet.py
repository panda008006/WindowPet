from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import statistics
import tempfile
from pathlib import Path

from PIL import Image, ImageChops


SHEET_COLUMNS = 6
ACTION_ROWS = (
    "idle",
    "click",
    "drag",
)
CANVAS_SIZE = (192, 208)
HORIZONTAL_MARGIN = 12
TOP_MARGIN = 12
BOTTOM_MARGIN = 12
BACKGROUND_TOLERANCE = 42
CHARACTER_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


class CharacterBuildError(RuntimeError):
    pass


def _normalise_character_folder(character_id: str) -> str:
    value = str(character_id or "").strip()
    if not CHARACTER_ID_PATTERN.fullmatch(value):
        raise CharacterBuildError(
            "character-id 只能使用英文字母、数字、下划线和连字符，并且必须以英文字母开头。"
        )
    return value if value.lower().endswith("pet") else f"{value}Pet"


def _parse_background(background: str) -> str | tuple[int, int, int]:
    value = str(background or "auto").strip()
    lowered = value.lower()
    if lowered in {"auto", "transparent"}:
        return lowered
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        raise CharacterBuildError(
            "background 必须是 auto、transparent 或 #RRGGBB 纯色。"
        )
    return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))


def _estimate_background(cell: Image.Image) -> tuple[int, int, int]:
    rgb = cell.convert("RGB")
    width, height = rgb.size
    sample_radius = max(1, min(width, height) // 100)
    samples: list[tuple[int, int, int]] = []
    for x, y in (
        (0, 0),
        (width - sample_radius, 0),
        (0, height - sample_radius),
        (width - sample_radius, height - sample_radius),
    ):
        crop = rgb.crop(
            (
                x,
                y,
                min(width, x + sample_radius),
                min(height, y + sample_radius),
            )
        )
        samples.extend(crop.get_flattened_data())
    return tuple(int(statistics.median(channel)) for channel in zip(*samples))


def _remove_plain_background(
    cell: Image.Image,
    background: str | tuple[int, int, int],
) -> Image.Image:
    rgba = cell.convert("RGBA")
    if background == "transparent":
        return rgba
    if background == "auto":
        alpha = rgba.getchannel("A")
        corners = (
            alpha.getpixel((0, 0)),
            alpha.getpixel((rgba.width - 1, 0)),
            alpha.getpixel((0, rgba.height - 1)),
            alpha.getpixel((rgba.width - 1, rgba.height - 1)),
        )
        if sum(value <= 8 for value in corners) >= 3:
            return rgba

    background_rgb = _estimate_background(rgba) if background == "auto" else background
    rgb = rgba.convert("RGB")
    solid = Image.new("RGB", rgb.size, background_rgb)
    difference = ImageChops.difference(rgb, solid)
    red, green, blue = difference.split()
    maximum_difference = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    keep_mask = maximum_difference.point(
        lambda value: 0 if value <= BACKGROUND_TOLERANCE else 255
    )
    original_alpha = rgba.getchannel("A")
    rgba.putalpha(ImageChops.darker(original_alpha, keep_mask))
    return rgba


def _normalise_frames(cells: list[Image.Image], background) -> list[Image.Image]:
    foregrounds = [_remove_plain_background(cell, background) for cell in cells]
    boxes = [foreground.getchannel("A").getbbox() for foreground in foregrounds]
    if any(bbox is None for bbox in boxes):
        raise CharacterBuildError(
            f"检测到空白格：{len(cells)} 个格子都必须包含一个完整角色主帧。"
        )
    left = min(bbox[0] for bbox in boxes)
    top = min(bbox[1] for bbox in boxes)
    right = max(bbox[2] for bbox in boxes)
    bottom = max(bbox[3] for bbox in boxes)
    common_width = right - left
    common_height = bottom - top
    max_width = CANVAS_SIZE[0] - HORIZONTAL_MARGIN * 2
    max_height = CANVAS_SIZE[1] - TOP_MARGIN - BOTTOM_MARGIN
    scale = min(max_width / common_width, max_height / common_height)
    target_size = (
        max(1, round(common_width * scale)),
        max(1, round(common_height * scale)),
    )
    frames = []
    for foreground in foregrounds:
        shared_crop = foreground.crop((left, top, right, bottom))
        shared_crop = shared_crop.resize(target_size, Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", CANVAS_SIZE, (0, 0, 0, 0))
        x = (CANVAS_SIZE[0] - shared_crop.width) // 2
        y = CANVAS_SIZE[1] - BOTTOM_MARGIN - shared_crop.height
        canvas.alpha_composite(shared_crop, (x, y))
        frames.append(canvas)
    return frames


def _metadata(display_name: str, character_folder: str) -> dict:
    animations = {}
    for action in ACTION_ROWS:
        animations[action] = {
            "folder": "." if action == "idle" else action,
            "fps": 8 if action == "idle" else 10,
            "loop": action in {"idle", "drag"},
        }
    return {
        "format_version": 2,
        "type": "frame_animation",
        "name": display_name,
        "character_id": character_folder,
        "fps": 10,
        "preview": f"{character_folder}_01.png",
        "idle_variants": [],
        "animations": animations,
    }


def _load_validator():
    validator_path = Path(__file__).with_name("validate_character.py")
    spec = importlib.util.spec_from_file_location(
        "windowpet_character_validator", validator_path
    )
    if spec is None or spec.loader is None:
        raise CharacterBuildError("无法加载 WindowPet 内置角色校验器。")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate


def _validate_staged_character(character_dir: Path) -> None:
    errors, _warnings = _load_validator()(character_dir)
    if errors:
        raise CharacterBuildError("角色未通过内置质检：\n" + "\n".join(errors))


def build_character_from_sheet(
    *,
    sheet,
    display_name,
    character_id,
    assets_root,
    background="auto",
) -> Path:
    sheet_path = Path(sheet).expanduser().resolve()
    assets_root = Path(assets_root).expanduser().resolve()
    display_name = str(display_name or "").strip()
    if not display_name:
        raise CharacterBuildError("display-name 不能为空。")
    if not sheet_path.is_file():
        raise CharacterBuildError(f"找不到主精灵图：{sheet_path}")

    character_folder = _normalise_character_folder(character_id)
    target = assets_root / character_folder
    if target.exists():
        raise CharacterBuildError(
            f"角色“{character_folder}”已经存在，本次没有覆盖或修改原角色。"
        )
    parsed_background = _parse_background(background)

    try:
        source = Image.open(sheet_path)
        source.load()
    except (OSError, Image.UnidentifiedImageError) as exc:
        raise CharacterBuildError(f"无法读取主精灵图：{exc}") from exc
    if source.width % SHEET_COLUMNS or source.height % len(ACTION_ROWS):
        raise CharacterBuildError(
            "主精灵图尺寸必须能被 6 列和 3 行整除，不能带网格外边框或额外留白。"
        )

    assets_root.mkdir(parents=True, exist_ok=True)
    staging_root = Path(
        tempfile.mkdtemp(prefix=".windowpet-build-", dir=assets_root.parent)
    )
    staged_character = staging_root / character_folder
    staged_character.mkdir()
    try:
        cell_width = source.width // SHEET_COLUMNS
        cell_height = source.height // len(ACTION_ROWS)
        cells = []
        for row in range(len(ACTION_ROWS)):
            for column in range(SHEET_COLUMNS):
                cells.append(
                    source.crop(
                        (
                            column * cell_width,
                            row * cell_height,
                            (column + 1) * cell_width,
                            (row + 1) * cell_height,
                        )
                    )
                )
        frames = _normalise_frames(cells, parsed_background)
        for row, action in enumerate(ACTION_ROWS):
            output_dir = (
                staged_character
                if action == "idle"
                else staged_character / action
            )
            output_dir.mkdir(exist_ok=True)
            for column in range(SHEET_COLUMNS):
                frame = frames[row * SHEET_COLUMNS + column]
                filename = (
                    f"{character_folder}_{column + 1:02d}.png"
                    if action == "idle"
                    else f"{column:02d}.png"
                )
                frame.save(output_dir / filename, format="PNG", optimize=True)

        (staged_character / "asset.json").write_text(
            json.dumps(
                _metadata(display_name, character_folder),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        _validate_staged_character(staged_character)
        if target.exists():
            raise CharacterBuildError(
                f"角色“{character_folder}”刚刚被其他任务创建，本次没有覆盖它。"
            )
        os.rename(staged_character, target)
        return target
    finally:
        source.close()
        shutil.rmtree(staging_root, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="把一张固定 6×3 WindowPet 主精灵图自动拆帧、去背景并安装为角色"
    )
    parser.add_argument("--sheet", required=True, type=Path, help="主精灵图路径")
    parser.add_argument("--display-name", required=True, help="角色在软件中显示的名称")
    parser.add_argument(
        "--character-id",
        required=True,
        help="英文角色目录名；不以 Pet 结尾时会自动补上",
    )
    parser.add_argument("--assets-root", required=True, type=Path, help="角色库根目录")
    parser.add_argument(
        "--background",
        default="auto",
        help="auto、transparent 或 #RRGGBB；默认自动读取四角纯色",
    )
    args = parser.parse_args()
    try:
        target = build_character_from_sheet(
            sheet=args.sheet,
            display_name=args.display_name,
            character_id=args.character_id,
            assets_root=args.assets_root,
            background=args.background,
        )
    except CharacterBuildError as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"OK: 已安装角色到 {target}")
    print(f"PNG: {sum(1 for path in target.rglob('*.png') if path.is_file())} 张")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
