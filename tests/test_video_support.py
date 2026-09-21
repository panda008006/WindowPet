import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PIL import Image, ImageDraw
from PySide6.QtWidgets import QApplication

from window_pet_app.asset_analyzer import AssetAnalyzer
from window_pet_app.assets import AssetType, detect_asset, make_thumbnail
from window_pet_app.media_folder import video_sources_for_folder, expand_folder_frames
from window_pet_app.overlay import OverlayWindow
from window_pet_app.video_audio_player import VideoAudioPlayer, VideoMediaPlayer


ROOT = Path(__file__).resolve().parents[1]
FFMPEG = shutil.which("ffmpeg")


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def _make_video(path: Path, frames=8):
    if not FFMPEG:
        pytest.skip("ffmpeg not available")
    source_dir = path.parent / f"_{path.stem}_frames"
    source_dir.mkdir()
    for index in range(frames):
        image = Image.new("RGB", (64, 72), (0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.rectangle((10 + index, 16, 42 + index, 58), fill=(80, 220, 120))
        image.save(source_dir / f"frame_{index:02d}.png")
    subprocess.run(
        [
            FFMPEG,
            "-y",
            "-v",
            "error",
            "-framerate",
            "8",
            "-i",
            str(source_dir / "frame_%02d.png"),
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=880:duration=1",
            "-shortest",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            str(path),
        ],
        check=True,
    )
    shutil.rmtree(source_dir)


def test_independent_video_is_detected_and_has_thumbnail(tmp_path, qapp):
    video = tmp_path / "talk.mp4"
    _make_video(video)

    asset = detect_asset(video)

    assert asset is not None
    assert asset.type == AssetType.VIDEO
    assert asset.fps == 8
    assert not make_thumbnail(asset).isNull()
    guess = AssetAnalyzer().analyze_file(video)
    assert guess and guess[0].guessed_type == AssetType.VIDEO


def test_action_folder_keeps_video_source_and_expands_frames(tmp_path):
    folder = tmp_path / "ActionPet" / "click"
    folder.mkdir(parents=True)
    video = folder / "click.mp4"
    _make_video(video, frames=8)

    assert video_sources_for_folder(folder) == [video]
    frames = expand_folder_frames(folder)
    assert len(frames) == 8
    assert all(frame.suffix == ".png" for frame in frames)


def test_video_audio_player_stops_and_switches_sources(tmp_path, qapp):
    first = tmp_path / "first.mp4"
    second = tmp_path / "second.mp4"
    _make_video(first)
    _make_video(second)
    player = VideoAudioPlayer()

    try:
        assert player.play(first, loop=False, speed=125)
        assert player.current_source == first.resolve()
        assert player.player.loops() == 1
        assert player.player.playbackRate() == pytest.approx(1.25)

        assert player.play(second, loop=True)
        assert player.current_source == second.resolve()
        assert player.player.loops() == -1
        player.stop()
        assert player.current_source is None
    finally:
        player.close()


def test_frame_animation_duration_uses_optional_repeat_count():
    class FakeAsset:
        def __init__(self, definition):
            self.metadata = {"animations": {"dance": definition}}

    class FakeWindow:
        frame_animation_repeat_count = OverlayWindow.frame_animation_repeat_count

    window = FakeWindow()
    window.asset = FakeAsset({"duration_seconds": 2.5, "repeat_count": 3})

    assert OverlayWindow.frame_animation_repeat_count(window, "dance") == 3
    assert OverlayWindow.frame_animation_duration_seconds(window, "dance") == pytest.approx(7.5)


@pytest.mark.parametrize("repeat_count", [None, 0, -2, "invalid", "3.5"])
def test_frame_animation_repeat_count_falls_back_to_one(repeat_count):
    class FakeAsset:
        metadata = {"animations": {"dance": {"duration_seconds": 2, "repeat_count": repeat_count}}}

    class FakeWindow:
        frame_animation_repeat_count = OverlayWindow.frame_animation_repeat_count

    window = FakeWindow()
    window.asset = FakeAsset()

    assert OverlayWindow.frame_animation_repeat_count(window, "dance") == 1
    assert OverlayWindow.frame_animation_duration_seconds(window, "dance") == pytest.approx(2)


def test_popo_dance_actions_repeat_three_times():
    metadata = json.loads((ROOT / "assets" / "PopoPet" / "asset.json").read_text(encoding="utf-8"))

    animations = metadata["animations"]
    assert animations["gesture-dance"]["repeat_count"] == 3
    assert animations["happy-dance"]["repeat_count"] == 3
    assert "repeat_count" not in animations["reverse-warning"]


def test_video_media_player_signal_can_connect(tmp_path, qapp):
    video = tmp_path / "visual.mp4"
    _make_video(video)
    player = VideoMediaPlayer()
    received = []

    try:
        player.frame_changed.connect(received.append)
        assert player.play(video, loop=True)
        assert player.current_source == video.resolve()
    finally:
        player.close()


def test_video_import_preserves_original_source_and_maps_all_basic_actions(tmp_path):
    video = tmp_path / "source.mp4"
    _make_video(video)
    assets_root = tmp_path / "assets"
    script = ROOT / "AI角色制作" / "video_to_character.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--video",
            str(video),
            "--character-id",
            "AudioPet",
            "--display-name",
            "带声音角色",
            "--assets-root",
            str(assets_root),
            "--background",
            "#000000",
            "--max-frames",
            "8",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    character = assets_root / "AudioPet"
    metadata = json.loads((character / "asset.json").read_text(encoding="utf-8"))
    sources = metadata["video_sources"]
    assert set(sources) == {"idle", "click", "drag"}
    assert len(set(sources.values())) == 1
    stored_source = character / Path(sources["idle"])
    assert stored_source.is_file()
    assert stored_source.read_bytes() == video.read_bytes()
