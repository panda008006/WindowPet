from pathlib import Path

from PySide6.QtGui import QPixmap

from .assets import AssetType
from .media_folder import VIDEO_EXTENSIONS


def validate_asset_metadata(asset_definition) -> list[str]:
    asset_type = getattr(asset_definition, "type", None)
    folder = Path(getattr(asset_definition, "path", ""))
    metadata = getattr(asset_definition, "metadata", None) or {}

    if asset_type == AssetType.SPRITE_STRIP:
        return _validate_sprite_strip(folder, metadata)
    if asset_type == AssetType.SPRITESHEET:
        return _validate_spritesheet(folder, metadata)
    if asset_type == AssetType.COMPOSITE_UI:
        return _validate_composite_ui(folder, metadata)
    if asset_type == AssetType.FRAME_ANIMATION:
        return _validate_frame_animation_video_sources(folder, metadata)
    return []


def _validate_frame_animation_video_sources(folder: Path, metadata: dict) -> list[str]:
    errors = []
    values = {}
    video_sources = metadata.get("video_sources")
    if isinstance(video_sources, dict):
        values.update(video_sources)
    animations = metadata.get("animations")
    if isinstance(animations, dict):
        for name, definition in animations.items():
            if isinstance(definition, dict):
                value = definition.get("video") or definition.get("video_source")
                if value:
                    values.setdefault(name, value)

    for name, value in values.items():
        if not isinstance(value, str) or not value.strip():
            errors.append(f"动作 {name} 的视频来源路径无效。")
            continue
        source = Path(value)
        if source.is_absolute() or any(part in {"", ".", ".."} for part in source.parts):
            errors.append(f"动作 {name} 的视频来源路径不安全：{value}")
            continue
        resolved = (folder / source).resolve()
        try:
            resolved.relative_to(folder.resolve())
        except ValueError:
            errors.append(f"动作 {name} 的视频来源路径不安全：{value}")
            continue
        if resolved.suffix.lower() not in VIDEO_EXTENSIONS:
            errors.append(f"动作 {name} 的视频来源格式不支持：{value}")
        elif not resolved.is_file():
            errors.append(f"动作 {name} 的视频来源文件不存在：{value}")
    return errors


def _validate_sprite_strip(folder: Path, metadata: dict) -> list[str]:
    errors = []
    image_path = _image_path(folder, metadata)
    pixmap = _pixmap(image_path)
    if image_path is None or not image_path.exists():
        errors.append("序列图图片文件缺失。")
        return errors
    if pixmap.isNull():
        errors.append("序列图图片文件无法读取。")
        return errors

    frames = _int(metadata.get("frames"), 0)
    if frames <= 0:
        errors.append("序列图帧数必须大于 0。")
        return errors

    direction = str(metadata.get("direction") or "horizontal").lower()
    if direction not in {"horizontal", "vertical"}:
        errors.append("序列图方向必须是横向或纵向。")
        return errors

    frame_width = _int(metadata.get("frame_width"), 0)
    frame_height = _int(metadata.get("frame_height"), 0)
    if frame_width > 0 or frame_height > 0:
        if frame_width <= 0 or frame_height <= 0:
            errors.append("如果填写单帧宽度/高度，两者都必须大于 0。")
            return errors
        required_width = frame_width * frames if direction == "horizontal" else frame_width
        required_height = frame_height if direction == "horizontal" else frame_height * frames
        if required_width > pixmap.width() or required_height > pixmap.height():
            errors.append("单帧尺寸和帧数超出了图片范围。")
        _validate_sprite_strip_crop(metadata, frame_width, frame_height, errors)
        return errors

    dimension = pixmap.width() if direction == "horizontal" else pixmap.height()
    if dimension % frames != 0:
        errors.append(f"序列图在 {direction} 方向的尺寸 {dimension}px 不能被 {frames} 帧整除，并且没有手动指定单帧尺寸。")
        return errors

    frame_width = pixmap.width() if direction == "vertical" else pixmap.width() // frames
    frame_height = pixmap.height() if direction == "horizontal" else pixmap.height() // frames
    _validate_sprite_strip_crop(metadata, frame_width, frame_height, errors)
    return errors


def _validate_sprite_strip_crop(metadata: dict, frame_width: int, frame_height: int, errors: list[str]):
    crop_left = _int(metadata.get("crop_left"), 0)
    crop_top = _int(metadata.get("crop_top"), 0)
    crop_right = _int(metadata.get("crop_right"), 0)
    crop_bottom = _int(metadata.get("crop_bottom"), 0)
    crops = {
        "crop_left": crop_left,
        "crop_top": crop_top,
        "crop_right": crop_right,
        "crop_bottom": crop_bottom,
    }
    for name, value in crops.items():
        if value < 0:
            errors.append(f"序列图裁剪参数 {name} 必须大于等于 0。")
    if crop_left + crop_right >= frame_width:
        errors.append("左侧裁剪 + 右侧裁剪必须小于单帧宽度。")
    if crop_top + crop_bottom >= frame_height:
        errors.append("顶部裁剪 + 底部裁剪必须小于单帧高度。")


def _validate_spritesheet(folder: Path, metadata: dict) -> list[str]:
    errors = []
    image_path = _image_path(folder, metadata)
    pixmap = _pixmap(image_path)
    if image_path is None or not image_path.exists():
        errors.append("精灵表图片文件缺失。")
        return errors
    if pixmap.isNull():
        errors.append("精灵表图片文件无法读取。")
        return errors

    frame_width = _int(metadata.get("frame_width"), 0)
    frame_height = _int(metadata.get("frame_height"), 0)
    if frame_width <= 0 or frame_height <= 0:
        errors.append("精灵表的单帧宽度和高度必须大于 0。")

    animations = metadata.get("animations")
    if not isinstance(animations, dict) or not animations:
        errors.append("精灵表至少需要定义一个动画。")
        return errors

    for name, animation in animations.items():
        frames = animation.get("frames") if isinstance(animation, dict) else None
        if not isinstance(frames, list) or not frames:
            errors.append(f"精灵表动画 '{name}' 至少需要定义一个帧。")
            continue
        for index, frame in enumerate(frames):
            if not isinstance(frame, dict) or not (("col" in frame and "row" in frame) or ("x" in frame and "y" in frame)):
                errors.append(f"精灵表动画 '{name}' 的第 {index + 1} 帧需要 col/row 或 x/y。")
    return errors


def _validate_composite_ui(folder: Path, metadata: dict) -> list[str]:
    errors = []
    layers = metadata.get("layers")
    if not isinstance(layers, list) or not layers:
        return ["组合界面/HUD 素材至少需要一个图层。"]

    readable = 0
    for index, layer in enumerate(layers):
        if not isinstance(layer, dict):
            errors.append(f"组合界面/HUD 第 {index + 1} 个图层无效。")
            continue
        image = layer.get("image")
        if not image:
            errors.append(f"组合界面/HUD 第 {index + 1} 个图层缺少图片。")
            continue
        image_path = folder / str(image)
        if not image_path.exists():
            errors.append(f"组合界面/HUD 图层图片缺失：{image}")
            continue
        if _pixmap(image_path).isNull():
            errors.append(f"组合界面/HUD 图层图片无法读取：{image}")
            continue
        readable += 1

    if readable == 0:
        errors.append("组合界面/HUD 素材至少需要一个可读取图层。")
    return errors


def _image_path(folder: Path, metadata: dict) -> Path | None:
    image = metadata.get("image")
    if not image:
        return None
    if folder.is_file():
        return folder if folder.name == str(image) else folder.parent / str(image)
    return folder / str(image)


def _pixmap(path: Path | None) -> QPixmap:
    return QPixmap(str(path)) if path is not None else QPixmap()


def _int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default
