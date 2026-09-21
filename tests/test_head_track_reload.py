import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from window_pet_app import overlay as overlay_module
from window_pet_app.overlay import OverlayWindow


class FakeTimer:
    def __init__(self):
        self.stopped = False

    def stop(self):
        self.stopped = True


class FakeAssetDefinition:
    def __init__(self, path):
        self.path = Path(path)
        self.type = "frame_animation"


class FakeOverlay:
    """只挂载 reload 相关的真实方法，其余依赖用桩替代。"""

    reload_asset_definition = OverlayWindow.reload_asset_definition
    _reset_head_track_runtime = OverlayWindow._reset_head_track_runtime

    def __init__(self):
        self.asset = object()
        self.asset_path = Path("assets/XiaobaTurnPet")
        self.asset_type = "frame_animation"
        self.base_size = None
        self.current_pixmap = None
        self.movie = None
        self.frame_player = None
        self.sprite_player = None
        self.composite_renderer = None
        self.head_track_timer = FakeTimer()
        self.head_track_frames = ["frame"] * 25
        self.head_track_index = 7
        self.stop_playback_calls = 0
        self.setup_head_track_calls = 0
        self.restored = False

    def stop_playback(self):
        self.stop_playback_calls += 1

    def start_playback(self):
        pass

    def setup_head_track(self):
        self.setup_head_track_calls += 1

    def load_asset_content(self):
        return self._load_ok

    def _restore_renderer_state(self, state_data):
        self.restored = True

    def update(self):
        pass


@pytest.fixture(scope="module")
def qapp():
    return QApplication.instance() or QApplication([])


def test_reload_clears_stale_head_track_runtime(qapp, monkeypatch):
    overlay = FakeOverlay()
    overlay._load_ok = True
    new_asset = FakeAssetDefinition("assets/PandaPet")
    monkeypatch.setattr(overlay_module, "detect_asset", lambda path: new_asset)

    assert overlay.reload_asset_definition(new_asset) is True
    # 旧角色的转头定时器与帧缓存必须被清理，否则切换后仍会覆盖回旧帧
    assert overlay.stop_playback_calls == 1
    assert overlay.head_track_timer.stopped is True
    assert overlay.head_track_frames == []
    assert overlay.head_track_index == -1
    # 新角色加载后重新探测 head_track（是转头角色则重新启用）
    assert overlay.setup_head_track_calls == 1


def test_reload_failure_reinstalls_head_track_for_restored_asset(qapp, monkeypatch):
    overlay = FakeOverlay()
    overlay._load_ok = False
    new_asset = FakeAssetDefinition("assets/PandaPet")
    monkeypatch.setattr(overlay_module, "detect_asset", lambda path: new_asset)

    assert overlay.reload_asset_definition(new_asset) is False
    assert overlay.restored is True
    # 加载失败回到原角色时，也要恢复原角色的转头状态
    assert overlay.setup_head_track_calls == 1
