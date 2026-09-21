import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtCore import QEvent, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from window_pet_app import assets as assets_module
from window_pet_app import state
from window_pet_app.assets import detect_asset
from window_pet_app.assets import AssetType
from window_pet_app.overlay import MOUSE_TRIGGER_ACTIONS, MOUSE_TRIGGER_ORDER, OverlayWindow


class FakeTimer:
    def stop(self):
        pass


class FakeMovie:
    def __init__(self):
        self.calls = []

    def start(self):
        self.calls.append("start")

    def stop(self):
        self.calls.append("stop")


class FakeAsset:
    fps = 12

    def __init__(self, animations):
        if isinstance(animations, dict):
            definitions = animations
        else:
            definitions = {name: {} for name in animations}
        self.metadata = {"animations": definitions}


class FakeOverlay:
    play_mouse_trigger_action = OverlayWindow.play_mouse_trigger_action
    available_animations = OverlayWindow.available_animations
    animation_display_name = OverlayWindow.animation_display_name
    named_action_items = OverlayWindow.named_action_items
    play_named_action = OverlayWindow.play_named_action
    trigger_animation_candidates = OverlayWindow.trigger_animation_candidates
    select_trigger_animation = OverlayWindow.select_trigger_animation
    bound_animation_names = OverlayWindow.bound_animation_names

    def __init__(self, animations):
        self.click_through = False
        self.screen_saver_active = False
        self.asset_type = AssetType.FRAME_ANIMATION
        self.asset = FakeAsset(animations)
        self.played = []

    def prefers_calm_static_idle(self):
        return True

    def play_frame_animation(self, name, *, loop=None, return_to_idle=True):
        if name not in self.asset.metadata["animations"]:
            return False
        self.played.append((name, loop, return_to_idle))
        return True


class FakeWheelEvent:
    def __init__(self, delta_y=120):
        self.delta_y = delta_y
        self.accepted = False

    def angleDelta(self):
        return type("Delta", (), {"y": lambda _self: self.delta_y})()

    def accept(self):
        self.accepted = True


class FakeWheelOverlay(FakeOverlay):
    wheelEvent = OverlayWindow.wheelEvent

    def __init__(self, animations):
        super().__init__(animations)
        self.timer_visible = True
        self.timer_adjustments = []

    def adjust_timer_minutes(self, minutes):
        self.timer_adjustments.append(minutes)


@pytest.fixture
def real_overlay(monkeypatch, tmp_path):
    app = QApplication.instance() or QApplication([])
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(assets_module, "CONFIG_PATH", config_path)
    monkeypatch.setattr(assets_module, "SETTINGS_PATH", config_path)
    monkeypatch.setattr(state, "WINDOWS", [])

    asset = detect_asset(Path("assets/XiaobaPet").resolve())
    window = OverlayWindow(asset, {"physics_enabled": False})
    window.show()
    app.processEvents()

    try:
        yield window
    finally:
        window.close()
        window.deleteLater()
        app.processEvents()


def test_mouse_trigger_count_matches_requested_surface():
    assert MOUSE_TRIGGER_ORDER == (
        "left-click",
        "left-drag",
    )


def test_only_click_and_drag_play_fixed_basic_actions():
    window = FakeOverlay(
        [
            "idle",
            "click",
            "drag",
            "hover",
            "jumping",
            "review",
        ]
    )

    assert window.play_mouse_trigger_action("left-click") is True
    assert window.play_mouse_trigger_action("left-drag", loop=True, return_to_idle=False) is True
    assert window.play_mouse_trigger_action("pointer-pass") is False
    assert window.play_mouse_trigger_action("left-double-click") is False
    assert window.play_mouse_trigger_action("right-menu") is False

    assert window.played == [
        ("click", False, True),
        ("drag", True, False),
    ]

    assert MOUSE_TRIGGER_ACTIONS.get("hover") is None
    assert MOUSE_TRIGGER_ACTIONS.get("leave") is None
    assert MOUSE_TRIGGER_ACTIONS.get("wheel-long-press") is None


def test_left_click_does_not_fall_back_when_its_fixed_action_is_missing():
    window = FakeOverlay(["idle", "hover"])

    assert window.play_mouse_trigger_action("left-click") is False
    assert window.played == []


def test_pointer_enter_and_leave_do_not_play_actions(real_overlay, monkeypatch):
    calls = []
    monkeypatch.setattr(
        real_overlay,
        "play_mouse_trigger_action",
        lambda name, **_kwargs: calls.append(name) or True,
    )

    real_overlay.start_hover_reaction()
    real_overlay.leaveEvent(QEvent(QEvent.Leave))

    assert calls == []


def test_single_click_plays_immediately(real_overlay, monkeypatch):
    calls = []
    monkeypatch.setattr(
        real_overlay,
        "play_mouse_trigger_action",
        lambda name, **_kwargs: calls.append(name) or True,
    )

    QTest.mouseClick(real_overlay, Qt.LeftButton)
    assert calls == ["left-click"]


def test_double_click_does_not_have_its_own_action(real_overlay, monkeypatch):
    calls = []
    monkeypatch.setattr(
        real_overlay,
        "play_mouse_trigger_action",
        lambda name, **_kwargs: calls.append(name) or True,
    )

    QTest.mouseClick(real_overlay, Qt.LeftButton)
    QTest.mouseDClick(real_overlay, Qt.LeftButton)

    assert "left-double-click" not in calls
    assert set(calls) <= {"left-click"}


def test_right_single_click_opens_menu_without_playing_an_action(real_overlay, monkeypatch):
    calls = []
    menus = []
    monkeypatch.setattr(
        real_overlay,
        "play_mouse_trigger_action",
        lambda name, **_kwargs: calls.append(name) or True,
    )
    monkeypatch.setattr(real_overlay, "open_menu", lambda pos: menus.append(pos))

    QTest.mouseClick(real_overlay, Qt.RightButton)
    assert calls == []
    assert len(menus) == 1


def test_right_double_click_has_no_character_action(real_overlay, monkeypatch):
    calls = []
    menus = []
    monkeypatch.setattr(
        real_overlay,
        "play_mouse_trigger_action",
        lambda name, **_kwargs: calls.append(name) or True,
    )
    monkeypatch.setattr(real_overlay, "open_menu", lambda pos: menus.append(pos))

    QTest.mouseClick(real_overlay, Qt.RightButton)
    QTest.mouseDClick(real_overlay, Qt.RightButton)

    assert calls == []
    assert menus


def test_wheel_scroll_has_no_character_action():
    window = FakeWheelOverlay(["feather-tickle"])
    event = FakeWheelEvent()

    window.wheelEvent(event)

    assert window.played == []
    assert window.timer_adjustments == []
    assert event.accepted is True


def test_middle_click_has_no_character_action(real_overlay, monkeypatch):
    calls = []
    monkeypatch.setattr(
        real_overlay,
        "play_mouse_trigger_action",
        lambda name, **_kwargs: calls.append(name) or True,
    )

    QTest.mouseClick(real_overlay, Qt.MiddleButton)
    assert calls == []

    calls.clear()
    QTest.mousePress(real_overlay, Qt.MiddleButton)
    QTest.qWait(650)
    QTest.mouseRelease(real_overlay, Qt.MiddleButton)
    assert calls == []


def test_sleeping_middle_press_only_wakes(real_overlay, monkeypatch):
    calls = []
    real_overlay.screen_saver_active = True
    monkeypatch.setattr(
        real_overlay,
        "play_mouse_trigger_action",
        lambda name, **_kwargs: calls.append(name) or True,
    )

    QTest.mouseClick(real_overlay, Qt.MiddleButton)

    assert real_overlay.screen_saver_active is False
    assert calls == []


def test_default_gif_playback_stops_on_the_first_frame():
    movie = FakeMovie()
    window = type(
        "FakeGifOverlay",
        (),
        {
            "movie": movie,
            "frame_player": None,
            "sprite_player": None,
            "prefers_calm_static_idle": lambda _self: True,
            "update_from_movie": lambda _self: movie.calls.append("update"),
        },
    )()

    OverlayWindow.start_playback(window)

    assert movie.calls == ["start", "update", "stop"]


def test_action_menu_lists_named_extras_and_hides_internal_actions():
    window = FakeOverlay(
        {
            "idle": {},
            "click": {},
            "drag": {},
            "hover": {},
            "jumping": {"label": "跳一跳"},
            "waving": {"display_name": "挥挥手"},
            "dance": {},
            "head_track": {},
            "right-double-click": {},
            "edge-crawl-bottom": {},
            "trio-bottom-fig1": {},
        }
    )

    assert window.named_action_items() == [
        ("hover", "看看你"),
        ("jumping", "跳一跳"),
        ("waving", "挥挥手"),
        ("dance", "dance"),
    ]


def test_named_action_plays_once_then_returns_to_idle():
    window = FakeOverlay(["idle", "click", "drag", "dance"])

    assert window.play_named_action("dance") is True
    assert window.played == [("dance", False, True)]
    assert window.play_named_action("idle") is False
