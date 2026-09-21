import json
import os
import re
import shutil
import tempfile
import zlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QImageReader, QMovie, QPixmap

from .constants import BASE_DIR, BUNDLED_ASSETS_DIR, CONFIG_PATH, DEFAULT_ASSETS_DIR, THUMBNAIL_SIZE
from . import state
from .logging_utils import log_warning
from .media_folder import (
    VIDEO_EXTENSIONS,
    expand_folder_frames,
    first_frame_for_media_source,
    video_fps_for_source,
)
from .package_registry import package_code_for_folder, package_code_for_id


class AssetType:
    GIF = "gif"
    VIDEO = "video"
    STATIC_IMAGE = "static_image"
    FRAME_ANIMATION = "frame_animation"
    SPRITE_STRIP = "sprite_strip"
    SPRITESHEET = "spritesheet"
    COMPOSITE_UI = "composite_ui"
    UNKNOWN = "unknown"


SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
SUPPORTED_VIDEO_EXTENSIONS = set(VIDEO_EXTENSIONS)
SUPPORTED_ASSET_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | {".gif"} | SUPPORTED_VIDEO_EXTENSIONS
DEFAULT_FRAME_FPS = 12
METADATA_ASSET_TYPES = {
    AssetType.FRAME_ANIMATION,
    AssetType.SPRITE_STRIP,
    AssetType.SPRITESHEET,
    AssetType.COMPOSITE_UI,
}
TOOL_ONLY_ASSET_FOLDERS = {"ToolAssets", "UiAssets"}
CONFIG_SCHEMA_VERSION = 1
WINDOW_CONFIG_KEYS = {
    "path",
    "gif_path",
    "asset_path",
    "asset_id",
    "asset_type",
    "x",
    "y",
    "locked",
    "always_on_top",
    "click_through",
    "scale",
    "opacity",
    "speed",
    "layer_values",
    "current_animation",
    "dock_mode",
    "physics_enabled",
    "timer_visible",
    "timer_seconds",
    "focus_mode",
    "focus_sessions_completed",
    "memo_visible",
    "memo_text",
    "memo_checked",
    "power_action_type",
    "power_action_due_at",
    "enabled_accessories",
    "pet_serial",
    "character_id",
    "pet_display_name",
}


@dataclass
class AssetDefinition:
    id: str
    name: str
    type: str
    path: Path
    pack: str | None = None
    metadata: dict | None = None
    preview_path: Path | None = None
    fps: int | None = None


def ensure_assets_dir():
    state.ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def copy_missing_assets(source_root, target_root):
    source_root = Path(source_root)
    target_root = Path(target_root)
    target_root.mkdir(parents=True, exist_ok=True)
    for source_path in source_root.rglob("*"):
        relative_path = source_path.relative_to(source_root)
        target_path = target_root / relative_path
        if source_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
        elif source_path.is_file() and not target_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temp_name = tempfile.mkstemp(
                prefix=f".{target_path.name}.seed-",
                suffix=".tmp",
                dir=target_path.parent,
            )
            os.close(descriptor)
            temp_path = Path(temp_name)
            try:
                shutil.copy2(source_path, temp_path)
                try:
                    os.rename(temp_path, target_path)
                except FileExistsError:
                    pass
            finally:
                temp_path.unlink(missing_ok=True)


def seed_default_assets_dir():
    if state.ASSETS_DIR != DEFAULT_ASSETS_DIR:
        return
    if BUNDLED_ASSETS_DIR.resolve() == DEFAULT_ASSETS_DIR.resolve():
        return
    if not BUNDLED_ASSETS_DIR.exists():
        return
    try:
        copy_missing_assets(BUNDLED_ASSETS_DIR, DEFAULT_ASSETS_DIR)
    except OSError as exc:
        log_warning("Could not seed bundled assets into runtime assets folder: %s", exc)


def stored_path(path):
    path = Path(path).resolve()
    try:
        return path.relative_to(BASE_DIR).as_posix()
    except ValueError:
        return str(path)


def resolved_path(path):
    path = Path(path)
    return path if path.is_absolute() else BASE_DIR / path


def config_warning(message):
    log_warning(message)


def is_inside_assets(path):
    try:
        Path(path).resolve().relative_to(state.ASSETS_DIR.resolve())
        return True
    except ValueError:
        return False


def unique_asset_path(target_dir, filename):
    target_dir.mkdir(parents=True, exist_ok=True)
    base = Path(filename).stem
    suffix = Path(filename).suffix or ".gif"
    candidate = target_dir / f"{base}{suffix}"
    index = 1

    while candidate.exists():
        candidate = target_dir / f"{base}_{index}{suffix}"
        index += 1

    return candidate


def unique_folder_path(target_dir, folder_name):
    target_dir.mkdir(parents=True, exist_ok=True)
    base = Path(folder_name).name
    candidate = target_dir / base
    index = 1

    while candidate.exists():
        candidate = target_dir / f"{base}_{index}"
        index += 1

    return candidate


def natural_key(path):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", Path(path).name)]


def is_supported_asset_file(path):
    return Path(path).suffix.lower() in SUPPORTED_ASSET_EXTENSIONS


def is_supported_frame_file(path):
    return Path(path).suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS


def load_metadata(folder):
    metadata_path = Path(folder) / "asset.json"
    if not metadata_path.exists():
        return {}

    try:
        data = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        log_warning("Invalid asset metadata %s: %s", metadata_path, exc)
        return {}

    return data if isinstance(data, dict) else {}


def frame_paths_for_folder(folder):
    """文件夹即素材：帧图片、GIF/APNG/动图 webp、视频统一展开为可播放帧序列。"""
    return expand_folder_frames(Path(folder))


def pack_name_for(path):
    try:
        relative = Path(path).resolve().relative_to(state.ASSETS_DIR.resolve())
    except ValueError:
        return None
    return relative.parts[0] if len(relative.parts) > 1 else None


def is_tool_only_asset_folder(path):
    return Path(path).name in TOOL_ONLY_ASSET_FOLDERS


def _metadata_preview(folder, metadata):
    preview = metadata.get("preview") if isinstance(metadata, dict) else None
    image = metadata.get("image") if isinstance(metadata, dict) else None
    preview_path_value = preview or image
    if not preview_path_value and isinstance(metadata, dict):
        layers = metadata.get("layers")
        if isinstance(layers, list):
            for layer in layers:
                if isinstance(layer, dict) and layer.get("image"):
                    preview_path_value = layer.get("image")
                    break
    if not preview_path_value:
        return None
    preview_path = (Path(folder) / str(preview_path_value)).resolve()
    return preview_path if preview_path.exists() else None


def _metadata_int(metadata, key, default):
    try:
        return max(1, int(metadata.get(key, default)))
    except (AttributeError, TypeError, ValueError):
        return default


def detect_asset(path):
    path = Path(path).resolve()
    if path.is_file():
        suffix = path.suffix.lower()
        if suffix == ".gif":
            asset_type = AssetType.GIF
        elif suffix in SUPPORTED_VIDEO_EXTENSIONS:
            asset_type = AssetType.VIDEO
        elif suffix in SUPPORTED_IMAGE_EXTENSIONS:
            asset_type = AssetType.STATIC_IMAGE
        else:
            return None

        return AssetDefinition(
            id=stored_path(path),
            name=path.stem,
            type=asset_type,
            path=path,
            pack=pack_name_for(path),
            metadata={},
            preview_path=path,
            fps=video_fps_for_source(path) if asset_type == AssetType.VIDEO else None,
        )

    if path.is_dir():
        metadata = load_metadata(path)
        metadata = dict(metadata or {})
        package_code = package_code_for_folder(path.name) or package_code_for_id(metadata.get("character_id"))
        if package_code:
            metadata["package_code"] = package_code
        metadata_type = str(metadata.get("type") or "").strip().lower() if metadata else ""
        if metadata_type in METADATA_ASSET_TYPES and metadata_type != AssetType.FRAME_ANIMATION:
            return AssetDefinition(
                id=stored_path(path),
                name=str(metadata.get("name") or path.name),
                type=metadata_type,
                path=path,
                pack=pack_name_for(path),
                metadata=metadata,
                preview_path=_metadata_preview(path, metadata),
                fps=_metadata_int(metadata, "fps", DEFAULT_FRAME_FPS),
            )

        frames = frame_paths_for_folder(path)
        if not frames:
            return None

        fps = _metadata_int(metadata, "fps", DEFAULT_FRAME_FPS)

        return AssetDefinition(
            id=stored_path(path),
            name=str(metadata.get("name") or path.name),
            type=metadata_type if metadata_type == AssetType.FRAME_ANIMATION else AssetType.FRAME_ANIMATION,
            path=path,
            pack=pack_name_for(path),
            metadata=metadata,
            preview_path=_metadata_preview(path, metadata) or frames[0],
            fps=fps,
        )

    return None


def scan_assets(root_dir):
    root = Path(root_dir)
    if not root.exists():
        return []

    assets = []
    seen = set()

    def visit(folder):
        for path in sorted(folder.iterdir(), key=lambda item: item.name.lower()):
            if path.name == "asset.json":
                continue
            if path.is_file() and is_supported_asset_file(path):
                asset = detect_asset(path)
                if asset is not None and asset.id not in seen:
                    assets.append(asset)
                    seen.add(asset.id)
            elif path.is_dir():
                if is_tool_only_asset_folder(path):
                    continue
                asset = detect_asset(path)
                if asset is not None:
                    if asset.id not in seen:
                        assets.append(asset)
                        seen.add(asset.id)
                    continue
                visit(path)

    visit(root)

    return assets


def assets_for_pack(pack_dir):
    ensure_assets_dir()
    pack_dir = Path(pack_dir).resolve()
    if is_tool_only_asset_folder(pack_dir):
        return []

    assets = []
    seen = set()

    for path in sorted(pack_dir.iterdir(), key=lambda item: item.name.lower()):
        if path.is_file() and is_supported_asset_file(path):
            asset = detect_asset(path)
            if asset is not None and asset.id not in seen:
                assets.append(asset)
                seen.add(asset.id)
        elif path.is_dir():
            if is_tool_only_asset_folder(path):
                continue
            asset = detect_asset(path)
            if asset is not None and asset.id not in seen:
                assets.append(asset)
                seen.add(asset.id)
                continue

            for nested in scan_assets(path):
                if nested.id not in seen:
                    assets.append(nested)
                    seen.add(nested.id)

    return assets


def import_asset_to_assets(source, pack_dir=None, reuse_existing=False):
    source = Path(source).resolve()
    if not source.exists() or not source.is_file() or not is_supported_asset_file(source):
        log_warning("Unsupported asset import skipped: %s", source)
        return None

    ensure_assets_dir()
    if is_inside_assets(source):
        return source

    target_dir = Path(pack_dir).resolve() if pack_dir else state.ASSETS_DIR
    existing_target = target_dir / source.name
    if reuse_existing and existing_target.exists():
        return existing_target

    target = unique_asset_path(target_dir, source.name)
    shutil.copy2(source, target)
    return target


def import_folder_to_assets(source, pack_dir=None, reuse_existing=False):
    source = Path(source).resolve()
    if not source.exists() or not source.is_dir() or detect_asset(source) is None:
        log_warning("Unsupported asset folder import skipped: %s", source)
        return None

    ensure_assets_dir()
    if is_inside_assets(source):
        return source

    target_dir = Path(pack_dir).resolve() if pack_dir else state.ASSETS_DIR
    existing_target = target_dir / source.name
    if reuse_existing and existing_target.exists():
        return existing_target

    target = unique_folder_path(target_dir, source.name)
    shutil.copytree(source, target)
    return target


def import_gif_to_assets(source, pack_dir=None, reuse_existing=False):
    source = Path(source).resolve()
    if source.suffix.lower() != ".gif":
        return None
    return import_asset_to_assets(source, pack_dir, reuse_existing)


def asset_packs():
    ensure_assets_dir()
    packs = [("根目录素材", state.ASSETS_DIR)]
    packs.extend(
        (path.name, path)
        for path in sorted(state.ASSETS_DIR.iterdir())
        if path.is_dir() and not is_tool_only_asset_folder(path)
    )
    return packs


def gifs_for_pack(pack_dir):
    pack_dir = Path(pack_dir)
    if pack_dir == state.ASSETS_DIR:
        return sorted(path for path in state.ASSETS_DIR.glob("*.gif") if path.is_file())
    return sorted(path for path in pack_dir.glob("*.gif") if path.is_file())


def make_thumbnail(asset_or_path):
    path = asset_or_path.preview_path if isinstance(asset_or_path, AssetDefinition) else asset_or_path
    if Path(path).suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS:
        first_frame = first_frame_for_media_source(path)
        if first_frame is not None:
            path = first_frame
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    image = reader.read()

    if image.isNull():
        movie = QMovie(str(path))
        movie.start()
        pixmap = movie.currentPixmap()
        movie.stop()
    else:
        pixmap = QPixmap.fromImage(image)

    if pixmap.isNull():
        pixmap = QPixmap(THUMBNAIL_SIZE)
        pixmap.fill(Qt.transparent)

    return QIcon(pixmap.scaled(THUMBNAIL_SIZE, Qt.KeepAspectRatio, Qt.SmoothTransformation))


def default_config():
    return {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "asset_root": stored_path(DEFAULT_ASSETS_DIR),
        "windows": [],
    }


def corrupt_config_backup_path(config_path):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return config_path.with_name(f"{config_path.stem}.corrupt.{timestamp}{config_path.suffix}")


def backup_corrupt_config(config_path):
    backup_path = corrupt_config_backup_path(config_path)
    try:
        shutil.copy2(config_path, backup_path)
        config_warning(f"Invalid config backed up to {backup_path}")
    except OSError as exc:
        config_warning(f"Invalid config could not be backed up: {exc}")
    return backup_path


def normalize_window_config(item):
    if isinstance(item, str):
        return {"path": item} if item else None

    if not isinstance(item, dict):
        config_warning("Skipped saved overlay with invalid entry type.")
        return None

    path_value = item.get("path") or item.get("gif_path") or item.get("asset_path")
    if not isinstance(path_value, str) or not path_value.strip():
        config_warning("Skipped saved overlay without a valid asset path.")
        return None

    normalized = {key: value for key, value in item.items() if key in WINDOW_CONFIG_KEYS}
    normalized["path"] = path_value
    return normalized


def normalize_config_data(data):
    if isinstance(data, list):
        raw_windows = data
        asset_root = None
    elif isinstance(data, dict):
        schema_version = data.get("schema_version", 0)
        if schema_version not in (0, CONFIG_SCHEMA_VERSION):
            config_warning(f"Config schema version {schema_version} is newer than supported; attempting safe load.")

        asset_root = data.get("asset_root")
        raw_windows = data.get("windows", [])
        if not isinstance(raw_windows, list):
            config_warning("Config windows field was invalid; starting with no saved overlays.")
            raw_windows = []
    else:
        config_warning("Config root was invalid; starting with safe defaults.")
        asset_root = None
        raw_windows = []

    if isinstance(asset_root, str) and asset_root.strip():
        resolved_root = resolved_path(asset_root).expanduser().resolve()
        state.ASSETS_DIR = resolved_root if resolved_root.exists() else DEFAULT_ASSETS_DIR
    else:
        state.ASSETS_DIR = DEFAULT_ASSETS_DIR

    windows = []
    for item in raw_windows:
        normalized = normalize_window_config(item)
        if normalized is not None:
            windows.append(normalized)

    return {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "asset_root": stored_path(state.ASSETS_DIR),
        "windows": windows,
    }


def load_config_data(config_path=CONFIG_PATH):
    config_path = Path(config_path)
    if not config_path.exists():
        state.ASSETS_DIR = DEFAULT_ASSETS_DIR
        return default_config()

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        backup_corrupt_config(config_path)
        state.ASSETS_DIR = DEFAULT_ASSETS_DIR
        return default_config()
    except OSError as exc:
        config_warning(f"Could not read config: {exc}")
        state.ASSETS_DIR = DEFAULT_ASSETS_DIR
        return default_config()

    return normalize_config_data(data)


def atomic_write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f".{path.name}.tmp")
    content = json.dumps(data, indent=2)

    with temp_path.open("w", encoding="utf-8") as file:
        file.write(content)
        file.write("\n")
        file.flush()
        os.fsync(file.fileno())

    os.replace(temp_path, path)


def load_config():
    return load_config_data(CONFIG_PATH)["windows"]


def save_config(windows=None):
    windows = state.WINDOWS if windows is None else windows
    data = {
        "schema_version": CONFIG_SCHEMA_VERSION,
        "asset_root": stored_path(state.ASSETS_DIR),
        "windows": [window.to_config() for window in windows],
    }
    _save_settings(data)
    try:
        atomic_write_json(CONFIG_PATH, data)
    except OSError as exc:
        config_warning(f"Could not save config: {exc}")


# ---------------------------------------------------------------------------
# Login / Pet unlock / Wallpaper schedule / Auto-update
# Stored inside config.json under a "_settings" key.
# ---------------------------------------------------------------------------

UNLOCK_RULE_VERSION = 2
DEFAULT_UNLOCKED_PET_COUNT = 0
LOGIN_GRANT_COUNT = 0
INVITE_EGG_CHANCES = 0
CHECKIN_EGG_CHANCES = 0
SIGNIN_CHANCE_LIMIT = 0
SUPPORTED_WALLPAPER_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

_AUTO_UPDATE_KEY = "auto_update_check"
_WALLPAPER_KEY = "wallpaper_schedule"
_UNLOCKS_KEY = "pet_unlocks"
_ACCOUNT_KEY = "account"

SETTINGS_PATH = CONFIG_PATH


def _load_settings():
    if not SETTINGS_PATH.exists():
        return {}
    try:
        raw = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    settings = raw.get("_settings")
    return settings if isinstance(settings, dict) else {}


def invite_code_for_identity(identity):
    seed = str(identity or "").strip().lower()
    if not seed:
        return None
    checksum = f"{zlib.crc32(seed.encode('utf-8')) & 0xFFFFFFFF:08X}"
    return f"WP-{checksum[:4]}-{checksum[4:]}"


def _save_settings(data):
    settings = {}
    if SETTINGS_PATH.exists():
        try:
            existing = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            existing_settings = existing.get("_settings", {})
            if isinstance(existing_settings, dict):
                settings = existing_settings
        except (json.JSONDecodeError, OSError):
            pass
    raw_activity_state = getattr(state, "PET_UNLOCKS", None)
    if isinstance(raw_activity_state, dict):
        activity_state = normalize_pet_unlocks(raw_activity_state)
        settings["activity_state"] = activity_state
        settings[_UNLOCKS_KEY] = activity_state.get("unlocks", {})
        if activity_state.get("email"):
            invite_code = activity_state.get("invite_code") or invite_code_for_identity(
                activity_state.get("identity") or activity_state.get("email") or activity_state.get("phone")
            )
            settings[_ACCOUNT_KEY] = {
                "email": activity_state.get("email"),
                "identity": activity_state.get("identity") or activity_state.get("email"),
                "phone": activity_state.get("phone"),
                "token": activity_state.get("token"),
                "user_id": activity_state.get("user_id"),
                "user_number": activity_state.get("user_number"),
                "name": activity_state.get("name"),
                "provider": activity_state.get("provider", "local"),
                "auth_mode": activity_state.get("auth_mode"),
                "local_account_id": activity_state.get("local_account_id"),
                "logged_in_at": activity_state.get("logged_in_at"),
                "invite_code": invite_code,
            }
            settings["invite_code"] = invite_code
    data["_settings"] = settings


def _write_settings(settings):
    if SETTINGS_PATH.exists():
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    else:
        data = {}
    if not isinstance(data, dict):
        data = {}
    data["_settings"] = settings
    atomic_write_json(SETTINGS_PATH, data)


def auto_update_check_enabled():
    settings = _load_settings()
    return bool(settings.get(_AUTO_UPDATE_KEY, True))


def set_auto_update_check_enabled(enabled):
    settings = _load_settings()
    settings[_AUTO_UPDATE_KEY] = bool(enabled)
    _write_settings(settings)


def wallpaper_schedule_settings():
    settings = _load_settings()
    schedule = settings.get(_WALLPAPER_KEY, {})
    if not isinstance(schedule, dict):
        schedule = {}
    schedule.setdefault("enabled", False)
    schedule.setdefault("slots", [])
    schedule.setdefault("shuffle", False)
    return schedule


def set_wallpaper_schedule_enabled(enabled):
    settings = _load_settings()
    schedule = settings.get(_WALLPAPER_KEY, {})
    if not isinstance(schedule, dict):
        schedule = {}
    schedule["enabled"] = bool(enabled)
    settings[_WALLPAPER_KEY] = schedule
    _write_settings(settings)


def set_wallpaper_slot_path(slot_index, path_str):
    settings = _load_settings()
    schedule = settings.get(_WALLPAPER_KEY, {})
    if not isinstance(schedule, dict):
        schedule = {"enabled": False, "slots": [], "shuffle": False}
    slots = schedule.get("slots", [])
    if not isinstance(slots, list):
        slots = []
    while len(slots) <= slot_index:
        slots.append({"path": ""})
    slots[slot_index] = {"path": str(path_str or "")}
    schedule["slots"] = slots
    settings[_WALLPAPER_KEY] = schedule
    _write_settings(settings)


def normalize_pet_unlocks(raw_state):
    if not isinstance(raw_state, dict):
        raw_state = {}
    account = raw_state.get("account") if isinstance(raw_state.get("account"), dict) else {}
    identity = str(raw_state.get("identity") or account.get("identity") or raw_state.get("email") or account.get("email") or "").strip()
    phone = str(raw_state.get("phone") or account.get("phone") or "").strip()
    email = str(raw_state.get("email") or account.get("email") or identity or phone or "").strip() or None
    token = str(raw_state.get("token") or account.get("token") or "").strip() or None
    claimed_codes = raw_state.get("claimed_invite_codes") or raw_state.get("claimed_codes") or []
    if not isinstance(claimed_codes, list):
        claimed_codes = []
    checkin_dates = raw_state.get("checkin_dates") or []
    if not isinstance(checkin_dates, list):
        checkin_dates = []
    history = raw_state.get("history") or raw_state.get("activity_history") or []
    if not isinstance(history, list):
        history = []
    unlocks = {str(k): bool(v) for k, v in (raw_state.get("unlocks") or {}).items()}
    unlocked_asset_ids = [str(v) for v in (raw_state.get("unlocked_asset_ids") or []) if v]
    return {
        "unlock_rule_version": max(0, int(raw_state.get("unlock_rule_version", 0) or 0)),
        "initialized": bool(raw_state.get("initialized", False)),
        "all_unlocked": bool(raw_state.get("all_unlocked", False)),
        "unlocks": unlocks,
        "unlocked_asset_ids": unlocked_asset_ids,
        "email": email,
        "identity": identity or email,
        "phone": phone,
        "token": token,
        "user_id": raw_state.get("user_id") or account.get("user_id"),
        "user_number": raw_state.get("user_number") or account.get("user_number"),
        "name": raw_state.get("name") or account.get("name"),
        "provider": raw_state.get("provider") or account.get("provider", "local"),
        "auth_mode": raw_state.get("auth_mode") or account.get("auth_mode"),
        "local_account_id": raw_state.get("local_account_id") or account.get("local_account_id"),
        "logged_in_at": raw_state.get("logged_in_at") or account.get("logged_in_at"),
        "egg_chances": max(0, int(raw_state.get("egg_chances", raw_state.get("chances", 0)) or 0)),
        "claimed_invite_codes": [str(code).strip().upper() for code in claimed_codes if str(code).strip()],
        "invite_count": max(0, int(raw_state.get("invite_count", 0) or 0)),
        "invite_goal": max(2, int(raw_state.get("invite_goal", 2) or 2)),
        "checkin_dates": [str(date) for date in checkin_dates if str(date).strip()],
        "last_checkin_date": str(raw_state.get("last_checkin_date") or "").strip() or None,
        "checkin_streak": max(0, int(raw_state.get("checkin_streak", 0) or 0)),
        "next_day_checkin_done": bool(raw_state.get("next_day_checkin_done", False)),
        "mission_completed": bool(raw_state.get("mission_completed", False)),
        "login_free_open_recorded": bool(raw_state.get("login_free_open_recorded", False)),
        "history": [str(item) for item in history[:12]],
        "feedback": list(raw_state.get("feedback") or [])[:30],
        "invite_code": str(raw_state.get("invite_code") or account.get("invite_code") or "").strip()
        or invite_code_for_identity(identity or email or phone),
    }


def _asset_character_id(asset):
    metadata = getattr(asset, "metadata", None) or {}
    return str(metadata.get("character_id") or asset.name or asset.id)


def ensure_pet_unlock_state(assets, grant_login_pets=False):
    asset_ids = []
    character_id_by_asset_id = {}
    for asset in (assets or []):
        asset_id = str(getattr(asset, "id", "") or "")
        if not asset_id:
            continue
        asset_ids.append(asset_id)
        character_id_by_asset_id[asset_id] = _asset_character_id(asset)

    settings = _load_settings()
    account = settings.get(_ACCOUNT_KEY, {})
    if not isinstance(account, dict):
        account = {}
    saved_activity = normalize_pet_unlocks(settings.get("activity_state", {}))
    pending_raw = getattr(state, "PET_UNLOCKS", None)
    has_pending_state = isinstance(pending_raw, dict) and any(
        pending_raw.get(key)
        for key in (
            "account",
            "email",
            "identity",
            "phone",
            "claimed_invite_codes",
            "invite_count",
            "checkin_dates",
            "last_checkin_date",
            "initialized",
            "unlock_rule_version",
            "all_unlocked",
            "unlocks",
            "unlocked_asset_ids",
            "egg_chances",
            "login_free_open_recorded",
            "next_day_checkin_done",
            "mission_completed",
            "user_number",
            "history",
            "feedback",
        )
    )
    if has_pending_state:
        pending_activity = normalize_pet_unlocks(pending_raw)
        saved_activity.update(pending_activity)

    unlocked_asset_ids = list(asset_ids)
    unlocks = {
        character_id_by_asset_id[asset_id]: True
        for asset_id in asset_ids
        if character_id_by_asset_id.get(asset_id)
    }

    unlock_state = {
        **saved_activity,
        "unlock_rule_version": UNLOCK_RULE_VERSION,
        "initialized": True,
        "all_unlocked": True,
        "unlocks": unlocks,
        "unlocked_asset_ids": unlocked_asset_ids,
        "egg_chances": 0,
        "email": str(
            account.get("email")
            or account.get("identity")
            or account.get("phone")
            or saved_activity.get("email")
            or saved_activity.get("identity")
            or saved_activity.get("phone")
            or ""
        ).strip() or None,
        "identity": str(
            account.get("identity")
            or account.get("email")
            or account.get("phone")
            or saved_activity.get("identity")
            or saved_activity.get("email")
            or ""
        ).strip() or None,
        "phone": str(account.get("phone") or saved_activity.get("phone") or "").strip() or None,
        "token": str(account.get("token") or saved_activity.get("token") or "").strip() or None,
        "user_id": account.get("user_id") or saved_activity.get("user_id"),
        "user_number": account.get("user_number") or saved_activity.get("user_number"),
        "name": account.get("name") or saved_activity.get("name"),
        "provider": account.get("provider") or saved_activity.get("provider", "local"),
        "auth_mode": account.get("auth_mode") or saved_activity.get("auth_mode"),
        "local_account_id": account.get("local_account_id") or saved_activity.get("local_account_id"),
        "logged_in_at": account.get("logged_in_at") or saved_activity.get("logged_in_at"),
        "invite_code": str(
            settings.get("invite_code")
            or account.get("invite_code")
            or saved_activity.get("invite_code")
            or ""
        ).strip()
        or invite_code_for_identity(
            account.get("identity")
            or account.get("email")
            or account.get("phone")
            or saved_activity.get("identity")
            or saved_activity.get("email")
            or saved_activity.get("phone")
        ),
    }

    return unlock_state


def is_asset_unlocked(asset, assets=None):
    return True


def logged_in_account(unlock_state=None):
    if unlock_state and isinstance(unlock_state, dict) and unlock_state.get("email"):
        return {
            "email": unlock_state["email"],
            "token": unlock_state.get("token"),
            "user_id": unlock_state.get("user_id"),
            "user_number": unlock_state.get("user_number"),
            "identity": unlock_state.get("identity") or unlock_state["email"],
            "name": unlock_state.get("name", unlock_state["email"].split("@")[0]),
            "provider": unlock_state.get("provider", "local"),
            "logged_in_at": unlock_state.get("logged_in_at"),
            "invite_code": unlock_state.get("invite_code") or invite_code_for_identity(unlock_state.get("identity") or unlock_state["email"]),
        }
    settings = _load_settings()
    account = settings.get(_ACCOUNT_KEY, {})
    identity = str((account or {}).get("email") or (account or {}).get("identity") or (account or {}).get("phone") or "").strip()
    if not isinstance(account, dict) or not identity:
        return None
    return {
        "email": identity,
        "token": account.get("token"),
        "user_id": account.get("user_id"),
        "user_number": account.get("user_number"),
        "identity": account.get("identity") or identity,
        "name": account.get("name", identity.split("@")[0]),
        "provider": account.get("provider", "local"),
        "logged_in_at": account.get("logged_in_at"),
        "invite_code": account.get("invite_code") or invite_code_for_identity(account.get("identity") or identity),
    }
