"""动作文件夹媒体展开层。

让"文件夹即素材"成立：动作文件夹里无论放入
  - 单张静态图片（png/jpg/jpeg/bmp）
  - 动图（gif / apng / 动图 webp）
  - 视频（mp4 / webm / mov / mkv / avi / m4v）
  - 或以上混合 + 常规 PNG 帧序列
`expand_folder_frames` 都返回一个可直接播放的 PNG 帧路径列表。

视频与动图抽帧结果缓存在文件夹内的 `.media_cache/<源名>_<指纹>\\`，
指纹取源文件 mtime+size，源文件更新后自动重抽。
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Callable

from PIL import Image
from PySide6.QtCore import QObject, QRunnable, QThreadPool, Qt, Signal

from .logging_utils import log_warning

STATIC_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v"}
CACHE_DIR_NAME = ".media_cache"
MAX_FRAMES_PER_SOURCE = 1000
MAX_FRAME_HEIGHT = 1440
_ACTIVE_MEDIA_TASKS: set["_MediaFrameTask"] = set()
_CACHE_LOCKS: dict[str, threading.Lock] = {}
_CACHE_LOCKS_GUARD = threading.Lock()


def _cache_lock(cache_dir: Path) -> threading.Lock:
    key = str(cache_dir.resolve()).lower()
    with _CACHE_LOCKS_GUARD:
        return _CACHE_LOCKS.setdefault(key, threading.Lock())


class _MediaFrameSignals(QObject):
    finished = Signal(object, object)


class _MediaFrameTask(QRunnable):
    def __init__(self, source: Path, cache_folder: Path | None):
        super().__init__()
        # The QObject carrying the result signal must outlive ``run``.  Qt's
        # default QRunnable auto-delete can destroy it before the queued
        # signal is emitted on slower ffmpeg jobs.
        self.setAutoDelete(False)
        self.source = source
        self.cache_folder = cache_folder
        self.signals = _MediaFrameSignals()

    def run(self):
        try:
            frames = media_source_frames(self.source, self.cache_folder)
            try:
                self.signals.finished.emit(frames, None)
            except RuntimeError:
                pass
        except Exception as exc:  # pragma: no cover - defensive worker guard
            try:
                self.signals.finished.emit([], exc)
            except RuntimeError:
                pass


def media_source_frames_async(
    source,
    cache_folder=None,
    callback: Callable[[list[Path], Exception | None], None] | None = None,
):
    """Expand a media source without blocking the Qt GUI thread.

    The returned QRunnable is owned by Qt's global pool.  ``callback`` is
    delivered through a queued Qt signal, so callers may safely create or
    replace QPixmaps in the GUI thread.
    """
    task = _MediaFrameTask(Path(source), Path(cache_folder) if cache_folder is not None else None)
    _ACTIVE_MEDIA_TASKS.add(task)
    if callback is not None:
        # PySide does not reliably retain a local Python callable connected to
        # a short-lived QRunnable signal.  Keep it on the task until the
        # worker has emitted its queued result.
        def deliver(frame_paths, error):
            try:
                callback(frame_paths, error)
            finally:
                _ACTIVE_MEDIA_TASKS.discard(task)

        task._callback = deliver
        task.signals.finished.connect(deliver, Qt.ConnectionType.QueuedConnection)
    else:
        task.signals.finished.connect(lambda *_: _ACTIVE_MEDIA_TASKS.discard(task), Qt.ConnectionType.QueuedConnection)
    QThreadPool.globalInstance().start(task)
    return task


def _hidden_subprocess_kwargs() -> dict:
    """Return Windows flags that keep ffmpeg/ffprobe out of the user's desktop.

    These helpers run from the Qt GUI thread while importing a dropped video.  A
    normal ``subprocess.run`` inherits the console window on Windows, which
    makes the app flash a black command prompt (and can look like a code/input
    dialog).  CREATE_NO_WINDOW is ignored on other platforms.
    """
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        return {"creationflags": subprocess.CREATE_NO_WINDOW}
    return {}

_NATURAL_SPLIT = re.compile(r"(\d+)")


def natural_sort_key(path: Path):
    return [
        int(part) if part.isdigit() else part.lower()
        for part in _NATURAL_SPLIT.split(path.name)
    ]


def _fingerprint(source: Path) -> str:
    stat = source.stat()
    raw = f"{stat.st_mtime_ns}:{stat.st_size}".encode()
    return hashlib.sha1(raw).hexdigest()[:8]


def _cache_root(folder: Path) -> Path:
    return Path(folder) / CACHE_DIR_NAME


def _scaled_frames(cache_dir: Path) -> list[Path]:
    all_frames = sorted(
        [*cache_dir.glob("frame_*.png"), *cache_dir.glob("frame_*.webp")],
        key=natural_sort_key,
    )
    by_stem = {}
    for p in all_frames:
        stem = p.stem
        if stem not in by_stem or p.suffix.lower() == ".webp":
            by_stem[stem] = p
    frames = [by_stem[k] for k in sorted(by_stem.keys(), key=lambda s: natural_sort_key(Path(s)))]
    if not frames:
        return []
    try:
        with Image.open(frames[0]) as sample:
            if sample.height <= MAX_FRAME_HEIGHT:
                return frames
    except (OSError, Image.UnidentifiedImageError):
        # A cancelled ffmpeg/Pillow conversion may leave a truncated PNG in
        # the cache.  Treat it as a cache miss and rebuild instead of letting
        # an image decoding exception abort the desktop click handler.
        for frame in frames:
            frame.unlink(missing_ok=True)
        return []
    # 缓存帧过大：整体缩一档并回写
    scale = MAX_FRAME_HEIGHT / sample.height
    valid_frames = []
    for frame in frames:
        try:
            with Image.open(frame) as im:
                size = (max(1, round(im.width * scale)), MAX_FRAME_HEIGHT)
                im.convert("RGBA").resize(size, Image.Resampling.LANCZOS).save(frame)
                valid_frames.append(frame)
        except (OSError, Image.UnidentifiedImageError):
            frame.unlink(missing_ok=True)
    return valid_frames


def _extract_animated_source(source: Path, folder: Path) -> list[Path]:
    cache_dir = _cache_root(folder) / f"{source.stem}_{_fingerprint(source)}"
    frames = _scaled_frames(cache_dir)
    if frames:
        return frames

    cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(source) as im:
            index = 0
            while True:
                im.seek(index)
                frame = im.convert("RGBA")
                if frame.height > MAX_FRAME_HEIGHT:
                    scale = MAX_FRAME_HEIGHT / frame.height
                    frame = frame.resize(
                        (max(1, round(frame.width * scale)), MAX_FRAME_HEIGHT),
                        Image.Resampling.LANCZOS,
                    )
                frame.save(cache_dir / f"frame_{index:04d}.png")
                index += 1
                if index >= MAX_FRAMES_PER_SOURCE:
                    break
    except (EOFError, OSError):
        pass
    except Exception as exc:
        log_warning("Unable to decode animated media %s: %s", source, exc)
        return []
    return _scaled_frames(cache_dir)


def _thin_evenly(frames: list[Path], cache_dir: Path) -> list[Path]:
    """把 ffmpeg 抽出的原始帧均匀抽稀到上限内，重命名为 frame_*。"""
    step = len(frames) / MAX_FRAMES_PER_SOURCE
    picked = [frames[min(len(frames) - 1, round(i * step))] for i in range(MAX_FRAMES_PER_SOURCE)]
    for index, frame in enumerate(picked):
        target = cache_dir / f"frame_{index:04d}.png"
        target.unlink(missing_ok=True)
        shutil.move(str(frame), target)
    for frame in frames:
        frame.unlink(missing_ok=True)
    return _scaled_frames(cache_dir)


def _extract_video_source(source: Path, folder: Path) -> list[Path]:
    cache_dir = _cache_root(folder) / f"{source.stem}_{_fingerprint(source)}"
    with _cache_lock(cache_dir):
        return _extract_video_source_unlocked(source, folder)


def _extract_video_source_unlocked(source: Path, folder: Path) -> list[Path]:
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        log_warning("ffmpeg not found on PATH; skipping video asset %s", source.name)
        return []

    cache_dir = _cache_root(folder) / f"{source.stem}_{_fingerprint(source)}"
    frames = _scaled_frames(cache_dir)
    if frames:
        return frames

    cache_dir.mkdir(parents=True, exist_ok=True)
    # A killed ffmpeg process can leave raw frames behind.  Clear those
    # partial outputs before retrying so a later move never fails with
    # Windows ERROR_FILE_EXISTS (183).
    for stale in cache_dir.glob("raw_*.png"):
        stale.unlink(missing_ok=True)
    for stale in cache_dir.glob("frame_*.png"):
        stale.unlink(missing_ok=True)
    raw_pattern = cache_dir / "raw_%05d.png"
    cmd = [
        ffmpeg, "-y", "-v", "error", "-i", str(source),
        # The player caps every source at MAX_FRAMES_PER_SOURCE anyway.  Do
        # not decode three times that many frames only to discard them; the
        # old 360-frame burst was a major source of first-click stutter.
        "-frames:v", str(MAX_FRAMES_PER_SOURCE), str(raw_pattern),
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True, **_hidden_subprocess_kwargs())
    except (subprocess.CalledProcessError, OSError) as exc:
        log_warning("ffmpeg failed for %s: %s", source, exc)
        return []

    raw_frames = sorted(cache_dir.glob("raw_*.png"))
    if not raw_frames:
        log_warning("ffmpeg produced no frames for %s", source)
        return []
    if len(raw_frames) > MAX_FRAMES_PER_SOURCE:
        return _thin_evenly(raw_frames, cache_dir)
    for index, frame in enumerate(raw_frames):
        target = cache_dir / f"frame_{index:04d}.png"
        target.unlink(missing_ok=True)
        shutil.move(str(frame), target)
    return _scaled_frames(cache_dir)


def video_sources_for_folder(folder) -> list[Path]:
    """返回动作文件夹中的视频源，供运行时同步播放其声音。"""
    folder = Path(folder)
    if not folder.is_dir():
        return []
    return sorted(
        (
            path
            for path in folder.iterdir()
            if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
        ),
        key=natural_sort_key,
    )


def cached_frames_for_source(source, cache_folder=None) -> list[Path]:
    """Return previously extracted frames even when the original video is absent.

    Release packages keep the small, transparent frame cache for built-in video
    characters and omit the multi-gigabyte production videos.  The cache name
    starts with the source stem and includes the original fingerprint, so a
    package can still play the exact frames that were prepared during authoring.
    """
    source = Path(source)
    folder = Path(cache_folder) if cache_folder is not None else source.parent
    cache_root = _cache_root(folder)
    if not cache_root.is_dir():
        return []

    prefix = f"{source.stem}_"
    candidates = [
        path
        for path in cache_root.iterdir()
        if path.is_dir() and path.name.startswith(prefix)
    ]
    # Prefer the most recently prepared cache when an author has kept several
    # generations of the same source.
    candidates.sort(key=lambda path: path.stat().st_mtime_ns, reverse=True)
    for candidate in candidates:
        frames = _scaled_frames(candidate)
        if frames:
            return frames
    return []


def media_source_frames(source, cache_folder=None) -> list[Path]:
    """展开一个独立媒体源；视频/GIF 的缓存仍放在指定文件夹的缓存目录内。"""
    source = Path(source)
    if not source.is_file():
        return []
    folder = Path(cache_folder) if cache_folder is not None else source.parent
    suffix = source.suffix.lower()
    if suffix in VIDEO_EXTENSIONS:
        return _extract_video_source(source, folder)
    if suffix in {".gif", ".apng", ".webp", ".png"}:
        if suffix == ".gif" or _is_truly_animated(source):
            return _extract_animated_source(source, folder)
    if suffix in STATIC_IMAGE_EXTENSIONS:
        return [source]
    return []


def first_frame_for_media_source(source, cache_folder=None) -> Path | None:
    frames = media_source_frames(source, cache_folder)
    return frames[0] if frames else None


def video_fps_for_source(source, fallback=12) -> int:
    """读取视频原始帧率，读取失败时返回稳定的桌宠默认值。"""
    source = Path(source)
    ffprobe = shutil.which("ffprobe")
    if not source.is_file() or source.suffix.lower() not in VIDEO_EXTENSIONS or not ffprobe:
        return max(1, int(fallback or 12))
    try:
        result = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=avg_frame_rate",
                "-of",
                "json",
                str(source),
            ],
            capture_output=True,
            text=True,
            check=True,
            **_hidden_subprocess_kwargs(),
        )
        streams = json.loads(result.stdout).get("streams") or []
        rate = str(streams[0].get("avg_frame_rate") or "") if streams else ""
        numerator, denominator = rate.split("/", 1)
        fps = float(numerator) / float(denominator)
        if fps > 0:
            return max(1, round(fps))
    except (OSError, ValueError, TypeError, ZeroDivisionError, json.JSONDecodeError, IndexError):
        pass
    return max(1, int(fallback or 12))


def _is_truly_static(source: Path) -> bool:
    try:
        with Image.open(source) as im:
            return not getattr(im, "is_animated", False)
    except OSError:
        return False


def expand_folder_frames(folder) -> list[Path]:
    """把文件夹里的所有媒体展开成统一 PNG 帧路径列表（按来源顺序、帧内自然序）。"""
    folder = Path(folder)
    if not folder.is_dir():
        return []

    plain_frames: list[Path] = []
    animated_sources: list[Path] = []

    for path in sorted(folder.iterdir(), key=natural_sort_key):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.stem.lower() in {"preview", "static", "thumbnail", "cover", "icon"}:
            continue
        suffix = path.suffix.lower()
        if suffix in VIDEO_EXTENSIONS or suffix == ".gif":
            animated_sources.append(path)
        elif suffix in STATIC_IMAGE_EXTENSIONS:
            if _is_truly_animated(path):
                animated_sources.append(path)
            else:
                plain_frames.append(path)
        # 其他扩展名（asset.json、说明文件等）忽略

    expanded: list[Path] = list(plain_frames)
    for source in animated_sources:
        expanded.extend(media_source_frames(source, folder))
    return expanded


def _is_truly_animated(source: Path) -> bool:
    try:
        with Image.open(source) as im:
            return bool(getattr(im, "is_animated", False))
    except OSError:
        return False
