"""文件夹即素材：单张图片 / GIF / 视频 / 混合内容都能展开为可播放帧序列。"""
import os
import shutil
import subprocess
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PIL import Image

from window_pet_app.assets import detect_asset
from window_pet_app.media_folder import expand_folder_frames

FFMPEG = shutil.which("ffmpeg")


def _make_frame(path: Path, color, size=(64, 72)):
    Image.new("RGBA", size, color).save(path)


@pytest.fixture()
def media_root(tmp_path):
    root = tmp_path / "MediaAssets"
    root.mkdir()
    return root


def _animated_gif(path: Path, frames=6, color_a=(255, 0, 0, 255), color_b=(0, 0, 255, 255)):
    images = [Image.new("RGBA", (60, 70), color_a if i % 2 else color_b) for i in range(frames)]
    images[0].save(path, save_all=True, append_images=images[1:], duration=100, loop=0, disposal=2)


def _video(path: Path, frames=8):
    if not FFMPEG:
        pytest.skip("ffmpeg not available")
    tmp = path.parent / f"_src_{path.stem}"
    tmp.mkdir(exist_ok=True)
    for i in range(frames):
        _make_frame(tmp / f"f_{i:02d}.png", (i * 20 % 255, 120, 90, 255))
    subprocess.run([
        FFMPEG, "-y", "-v", "error", "-framerate", "8", "-i", str(tmp / "f_%02d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
    ], check=True)
    shutil.rmtree(tmp)


def test_single_static_image_folder_becomes_playable(media_root):
    folder = media_root / "SingleImagePet"
    folder.mkdir()
    _make_frame(folder / "shot.png", (10, 200, 10, 255))

    frames = expand_folder_frames(folder)
    assert len(frames) == 1
    asset = detect_asset(folder)
    assert asset is not None and asset.type == "frame_animation"


def test_plain_frame_sequence_unchanged(media_root):
    folder = media_root / "SeqPet"
    folder.mkdir()
    for i in range(5):
        _make_frame(folder / f"{i:02d}.png", (i * 40, 0, 0, 255))

    frames = expand_folder_frames(folder)
    assert [f.name for f in frames] == ["00.png", "01.png", "02.png", "03.png", "04.png"]


def test_gif_expands_to_frames(media_root):
    folder = media_root / "GifPet"
    folder.mkdir()
    _animated_gif(folder / "move.gif", frames=6)

    frames = expand_folder_frames(folder)
    assert len(frames) == 6
    assert all(f.suffix == ".png" for f in frames)
    # 二次调用命中缓存，结果一致
    again = expand_folder_frames(folder)
    assert [f.name for f in again] == [f.name for f in frames]


def test_static_png_not_treated_as_animation(media_root):
    folder = media_root / "StaticPet"
    folder.mkdir()
    _make_frame(folder / "a.png", (1, 2, 3, 255))

    frames = expand_folder_frames(folder)
    assert [f.name for f in frames] == ["a.png"]


def test_video_expands_to_frames(media_root):
    folder = media_root / "VideoPet"
    folder.mkdir()
    _video(folder / "dance.mp4", frames=8)

    frames = expand_folder_frames(folder)
    assert len(frames) >= 4
    assert all(f.suffix == ".png" for f in frames)
    # 缓存命中：第二次调用不再依赖 ffmpeg 也能返回同样数量
    again = expand_folder_frames(folder)
    assert len(again) == len(frames)


def test_video_cache_invalidates_on_change(media_root):
    folder = media_root / "VideoCachePet"
    folder.mkdir()
    video = folder / "clip.mp4"
    _video(video, frames=6)
    first = len(expand_folder_frames(folder))

    # 重新生成不同帧数的视频（mtime/size 变化）
    import time
    time.sleep(0.05)
    _video(video, frames=10)
    second = len(expand_folder_frames(folder))
    assert second > first


def test_mixed_gif_and_plain_frames(media_root):
    folder = media_root / "MixedPet"
    folder.mkdir()
    _make_frame(folder / "idle.png", (9, 9, 9, 255))
    _animated_gif(folder / "extra.gif", frames=4)

    frames = expand_folder_frames(folder)
    names = [f.name for f in frames]
    # 静态帧在前，gif 展开帧在后
    assert names[0] == "idle.png"
    assert len(frames) == 5


def test_folder_without_media_returns_empty(media_root):
    folder = media_root / "EmptyPet"
    folder.mkdir()
    (folder / "asset.json").write_text("{}", encoding="utf-8")
    assert expand_folder_frames(folder) == []
    assert detect_asset(folder) is None


def test_media_cache_directory_is_ignored(media_root):
    folder = media_root / "CacheIgnorePet"
    folder.mkdir()
    cache = folder / ".media_cache"
    cache.mkdir()
    _make_frame(cache / "frame_0000.png", (5, 5, 5, 255))
    _make_frame(folder / "real.png", (6, 6, 6, 255))

    frames = expand_folder_frames(folder)
    assert [f.name for f in frames] == ["real.png"]
