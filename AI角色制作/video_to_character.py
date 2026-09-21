"""视频导入角色工具：把去掉背景的动态视频变成 WindowPet 可运行的动作。

三种输入都支持：
  1. 透明视频（webm/mov，带 alpha 通道）
  2. 绿幕/洋红幕视频（mp4/webm，纯色背景）—— 自动抠像
  3. 动图（gif / apng / 动图 webp）—— 直接逐帧拆

两种用法：
  A. 新建角色：--character-id XxxPet --display-name 名称
     视频帧会同时装入三个基础动作（后续可用方式 B 逐个替换或添加命名动作）。
  B. 给现有角色添加/替换动作：--character-id XxxPet --action click
     帧序列覆盖写入该动作（idle 写到角色根目录）。

示例：
  python video_to_character.py --video dance.webm --character-id PopoPet ^
      --display-name 坡坡popo --assets-root ..\\assets
  python video_to_character.py --video wave.webm --character-id PopoPet --action click
  python video_to_character.py --video dance.webm --character-id PopoPet --action dance

写帧后自动调用 validate_character.py 质检。不修改既有角色的其他动作。
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ACTIONS = ("idle", "click", "drag")
CANVAS_W, CANVAS_H = 192, 208
MARGIN = 6
CHARACTER_ID_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
ACTION_NAME_PATTERN = CHARACTER_ID_PATTERN
VIDEO_SUFFIXES = {".webm", ".mp4", ".mov", ".mkv", ".avi", ".m4v"}
ANIMATED_IMAGE_SUFFIXES = {".gif", ".apng", ".webp", ".png"}


class VideoImportError(RuntimeError):
    pass


def _normalise_character_folder(character_id: str) -> str:
    value = str(character_id or "").strip()
    if not CHARACTER_ID_PATTERN.fullmatch(value):
        raise VideoImportError("character-id 只能使用英文字母、数字、下划线和连字符，并以字母开头。")
    return value if value.lower().endswith("pet") else f"{value}Pet"


def _normalise_action_name(action: str) -> str:
    value = str(action or "").strip()
    if not ACTION_NAME_PATTERN.fullmatch(value):
        raise VideoImportError(
            "action 只能使用英文字母、数字、下划线和连字符，并以英文字母开头。"
        )
    return value


def _require_ffmpeg() -> tuple[str, str]:
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise VideoImportError("找不到 ffmpeg/ffprobe，请先安装并加入 PATH。")
    return ffmpeg, ffprobe


def _probe(video: Path, ffprobe: str) -> dict:
    result = subprocess.run(
        [ffprobe, "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,nb_frames,pix_fmt,avg_frame_rate",
         "-of", "json", str(video)],
        capture_output=True, text=True, check=True,
    )
    streams = json.loads(result.stdout).get("streams") or []
    if not streams:
        raise VideoImportError(f"视频里没有画面流：{video}")
    return streams[0]


def _first_frame_has_alpha(video: Path, ffmpeg: str, out_dir: Path) -> bool:
    """抽第一帧实际检查透明度——比 ffprobe 的 pix_fmt 报告更可靠。"""
    probe_png = out_dir / "probe_%05d.png"
    subprocess.run(
        [ffmpeg, "-y", "-v", "error", "-i", str(video), "-frames:v", "1", str(probe_png)],
        capture_output=True, text=True, check=True,
    )
    probes = sorted(out_dir.glob("probe_*.png"))
    if not probes:
        return False
    with Image.open(probes[0]) as im:
        if "A" not in im.getbands():
            return False
        low, _high = im.getchannel("A").getextrema()
        return low < 250


def _extract_with_ffmpeg(video: Path, out_dir: Path, background: str, max_frames: int,
                         ffmpeg: str, ffprobe: str) -> list[Path]:
    info = _probe(video, ffprobe)
    has_alpha = _first_frame_has_alpha(video, ffmpeg, out_dir)

    if background in {"transparent", "auto"} and not has_alpha:
        raise VideoImportError(
            "视频没有可用的透明通道。请改用 --background #00FF00（绿幕）"
            "或 #FF00FF（洋红幕）抠像；透明视频推荐 qtrle/png 编码的 mov 或带 alpha 的 webm。"
        )

    out_pattern = out_dir / "raw_%05d.png"
    cmd = [ffmpeg, "-y", "-v", "error", "-i", str(video)]
    if has_alpha and background in {"transparent", "auto"}:
        pass  # 直接保留 alpha
    elif background.startswith("#"):
        color = background[1:]
        cmd += ["-vf", f"colorkey=0x{color}:0.30:0.10"]
    cmd += ["-frames:v", str(max_frames * 3), str(out_pattern)]
    subprocess.run(cmd, capture_output=True, text=True, check=True)

    frames = sorted(out_dir.glob("raw_*.png"))
    if not frames:
        raise VideoImportError("抽帧结果为空，请检查视频是否可解码。")
    return _thin_frames(frames, max_frames)


def _extract_animated_image(video: Path, out_dir: Path, max_frames: int) -> list[Path]:
    with Image.open(video) as im:
        index = 0
        try:
            while True:
                im.seek(index)
                frame = im.convert("RGBA")
                frame.save(out_dir / f"raw_{index:05d}.png")
                index += 1
        except EOFError:
            pass
    frames = sorted(out_dir.glob("raw_*.png"))
    if not frames:
        raise VideoImportError("动图没有可读的帧。")
    return _thin_frames(frames, max_frames)


def _thin_frames(frames: list[Path], max_frames: int) -> list[Path]:
    if len(frames) <= max_frames:
        return frames
    step = len(frames) / max_frames
    picked = [frames[min(len(frames) - 1, round(i * step))] for i in range(max_frames)]
    for frame in frames:
        if frame not in picked:
            frame.unlink()
    return picked


def _normalise_frames(frames: list[Path]) -> list[Image.Image]:
    """统一所有帧画布：共享 bbox、按比例缩放到 192x208 内、底边对齐。"""
    images = []
    boxes = []
    for frame in frames:
        rgba = Image.open(frame).convert("RGBA")
        bbox = rgba.getchannel("A").getbbox()
        if bbox is None:
            continue
        images.append(rgba)
        boxes.append(bbox)
    if not images:
        raise VideoImportError("所有帧都是空白（alpha 全透明），无法导入。")

    left = min(b[0] for b in boxes)
    top = min(b[1] for b in boxes)
    right = max(b[2] for b in boxes)
    bottom = max(b[3] for b in boxes)
    scale = min(
        (CANVAS_W - MARGIN * 2) / max(1, right - left),
        (CANVAS_H - MARGIN * 2) / max(1, bottom - top),
    )
    target = (max(1, round((right - left) * scale)), max(1, round((bottom - top) * scale)))

    normalised = []
    for rgba in images:
        cropped = rgba.crop((left, top, right, bottom)).resize(target, Image.Resampling.LANCZOS)
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        canvas.alpha_composite(cropped, ((CANVAS_W - target[0]) // 2, CANVAS_H - MARGIN - target[1]))
        normalised.append(canvas)
    return normalised


def _default_metadata(
    display_name: str,
    character_folder: str,
    frame_count: int,
    video_sources: dict[str, str] | None = None,
) -> dict:
    def entry(folder, loop=False):
        return {"folder": folder, "fps": 10, "loop": loop}

    animations = {
        action: entry("." if action == "idle" else action, action in {"idle", "drag"})
        for action in ACTIONS
    }
    metadata = {
        "format_version": 2,
        "type": "frame_animation",
        "name": display_name,
        "character_id": character_folder,
        "fps": 10,
        "preview": f"{character_folder}_01.png",
        "idle_variants": [],
        "animations": animations,
        "source": {"method": "video_import", "actions": {a: frame_count for a in ACTIONS}},
    }
    if video_sources:
        metadata["video_sources"] = dict(video_sources)
    return metadata


def _write_action_frames(character_dir: Path, character_folder: str, action: str,
                         frames: list[Image.Image]) -> None:
    if action == "idle":
        for old in character_dir.glob(f"{character_folder}_*.png"):
            old.unlink()
        for index, frame in enumerate(frames, start=1):
            frame.save(character_dir / f"{character_folder}_{index:02d}.png")
        return
    action_dir = character_dir / action
    if action_dir.exists():
        shutil.rmtree(action_dir)
    action_dir.mkdir(parents=True)
    for index, frame in enumerate(frames):
        frame.save(action_dir / f"{index:02d}.png")


def _store_video_source(character_dir: Path, source: Path, action: str) -> str:
    """保留原始视频，返回写入 asset.json 的角色包内相对路径。"""
    target_dir = character_dir / "video_sources"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{action}_{source.stem}{source.suffix.lower()}"
    if source.resolve() != target.resolve():
        shutil.copy2(source, target)
    return target.relative_to(character_dir).as_posix()


def _update_metadata_action(
    character_dir: Path,
    action: str,
    frame_count: int,
    video_source: str | None = None,
) -> None:
    metadata_path = character_dir / "asset.json"
    metadata = {}
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    animations = metadata.setdefault("animations", {})
    entry = animations.get(action) if isinstance(animations.get(action), dict) else {}
    entry["folder"] = "." if action == "idle" else action
    entry.setdefault("fps", 8 if action == "idle" else 10)
    entry["loop"] = True if action in {"idle", "drag"} else bool(entry.get("loop", False))
    animations[action] = entry
    source = metadata.setdefault("source", {"method": "video_import"})
    if not isinstance(source, dict):
        source = {"method": "video_import"}
        metadata["source"] = source
    actions_source = source.setdefault("actions", {})
    if not isinstance(actions_source, dict):
        actions_source = {}
        source["actions"] = actions_source
    actions_source[action] = frame_count
    if video_source:
        video_sources = metadata.setdefault("video_sources", {})
        if not isinstance(video_sources, dict):
            video_sources = {}
            metadata["video_sources"] = video_sources
        video_sources[action] = video_source
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_validator():
    import importlib.util
    validator_path = Path(__file__).with_name("validate_character.py")
    spec = importlib.util.spec_from_file_location("windowpet_character_validator", validator_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.validate


def main():
    parser = argparse.ArgumentParser(description="把动态视频导入为 WindowPet 角色动作。")
    parser.add_argument("--video", type=Path, required=True, help="视频或动图路径")
    parser.add_argument("--character-id", required=True, help="英文角色 ID（自动补 Pet 后缀）")
    parser.add_argument("--display-name", default="", help="新建角色时的显示名")
    parser.add_argument("--assets-root", type=Path, required=True, help="assets 目录绝对路径")
    parser.add_argument("--action", help="添加/替换到指定动作名（缺省=新建角色；可使用 dance 等自定义名称）")
    parser.add_argument("--background", default="auto",
                        help="transparent/auto（视频需带 alpha）或 #RRGGBB 抠像色")
    parser.add_argument("--max-frames", type=int, default=96, help="最多保留帧数（默认 96）")
    parser.add_argument("--fps", type=int, help="覆盖该动作的播放帧率")
    args = parser.parse_args()

    if not (4 <= args.max_frames <= 240):
        raise VideoImportError("max-frames 需在 4-240 之间。")
    character_folder = _normalise_character_folder(args.character_id)
    character_dir = args.assets_root / character_folder
    action_name = None if args.action is None else _normalise_action_name(args.action)
    creating = action_name is None

    if creating:
        if not args.display_name.strip():
            raise VideoImportError("新建角色必须提供 --display-name。")
        if character_dir.exists():
            raise VideoImportError(f"角色 {character_folder} 已存在，本次不覆盖。请用 --action 添加动作。")
    elif not character_dir.exists():
        raise VideoImportError(f"角色 {character_folder} 不存在，无法添加动作。请先新建角色。")

    video = args.video
    if not video.is_file():
        raise VideoImportError(f"找不到视频：{video}")

    background = str(args.background).strip()
    if background not in {"auto", "transparent"} and not re.fullmatch(r"#[0-9A-Fa-f]{6}", background):
        raise VideoImportError("background 必须是 auto/transparent 或 #RRGGBB。")

    with tempfile.TemporaryDirectory(prefix="windowpet_video_import_") as temp:
        out_dir = Path(temp)
        if video.suffix.lower() in VIDEO_SUFFIXES:
            ffmpeg, ffprobe = _require_ffmpeg()
            frames = _extract_with_ffmpeg(video, out_dir, background, args.max_frames, ffmpeg, ffprobe)
        elif video.suffix.lower() in ANIMATED_IMAGE_SUFFIXES:
            frames = _extract_animated_image(video, out_dir, args.max_frames)
        else:
            raise VideoImportError(f"不支持的文件类型：{video.suffix}（支持 {sorted(VIDEO_SUFFIXES | ANIMATED_IMAGE_SUFFIXES)}）")

        normalised = _normalise_frames(frames)
        if len(normalised) < 4:
            raise VideoImportError(f"有效帧只有 {len(normalised)} 帧，至少需要 4 帧。")

        if creating:
            character_dir.mkdir(parents=True)
        video_source = None
        if video.suffix.lower() in VIDEO_SUFFIXES:
            video_source = _store_video_source(
                character_dir,
                video.resolve(),
                "source" if creating else action_name,
            )

        if creating:
            for action in ACTIONS:
                _write_action_frames(character_dir, character_folder, action, normalised)
            if video_source:
                video_sources = {action: video_source for action in ACTIONS}
            else:
                video_sources = None
            metadata = _default_metadata(
                args.display_name.strip(),
                character_folder,
                len(normalised),
                video_sources,
            )
            (character_dir / "asset.json").write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"OK: 新建角色 {character_folder}（三种基础动作各 {len(normalised)} 帧）")
        else:
            _write_action_frames(character_dir, character_folder, action_name, normalised)
            _update_metadata_action(character_dir, action_name, len(normalised), video_source)
            if args.fps:
                metadata_path = character_dir / "asset.json"
                metadata = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
                metadata["animations"][action_name]["fps"] = int(args.fps)
                metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"OK: 已把 {len(normalised)} 帧写入 {character_folder}/{action_name}")

    errors, warnings = _load_validator()(character_dir)
    for item in errors:
        print("ERROR:", item)
    for item in warnings:
        print("WARNING:", item)
    if errors:
        raise SystemExit(1)
    print("校验通过。")


if __name__ == "__main__":
    try:
        main()
    except VideoImportError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(1)
