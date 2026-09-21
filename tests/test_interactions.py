from datetime import datetime
from pathlib import Path

from window_pet_app.interactions import (
    BOTTOM_DOCK_CLUSTER_RULE,
    TRIO_CONCERT_RULE,
    PetInteractionController,
    infer_character_id_from_path,
    max_center_distance,
)


class FakeWindow:
    def __init__(self, x, y, width=100, height=100):
        self._x = x
        self._y = y
        self._width = width
        self._height = height

    def x(self):
        return self._x

    def y(self):
        return self._y

    def width(self):
        return self._width

    def height(self):
        return self._height


class FakeRewardWindow:
    character_id = "fake"
    asset_path = Path("assets") / "FakePet"

    def __init__(self):
        self.calls = []

    def play_frame_animation(self, name, *, loop=None, return_to_idle=True):
        self.calls.append((name, loop, return_to_idle))
        return name == "review"


class FakeRewardController:
    def __init__(self, windows):
        self.windows = windows

    def reward_candidates(self):
        return self.windows


class FakeTrioWindow:
    asset_type = "frame_animation"
    is_dragging_asset = False
    screen_saver_active = False
    current_frame_animation = "edge-crawl-bottom"

    def __init__(self, character_id, x, y, dock_mode="bottom", animations=None):
        self.character_id = character_id
        self.asset_path = Path("assets") / f"{character_id}Pet"
        self.dock_mode = dock_mode
        self._x = x
        self._y = y
        self._animations = set(animations or ())
        self.calls = []

    def isVisible(self):
        return True

    def x(self):
        return self._x

    def y(self):
        return self._y

    def width(self):
        return 100

    def height(self):
        return 100

    def available_animations(self):
        return sorted(self._animations)

    def play_frame_animation(self, name, *, loop=None, return_to_idle=True):
        self.calls.append((name, loop, return_to_idle))
        return name in self._animations


class FakeTrioController:
    def __init__(self, windows):
        self.windows = windows
        self.bottom_dock_cluster_next_allowed = 0.0
        self.right_dock_stack_next_allowed = 0.0
        self.time_rule_triggered_dates = {}

    def visible_windows(self):
        return self.windows

    def windows_by_character(self):
        return PetInteractionController.windows_by_character(self)

    def ready_for_group_action(self, window):
        return PetInteractionController.ready_for_group_action(self, window)

    def ready_for_bottom_dock_cluster(self, window):
        return PetInteractionController.ready_for_bottom_dock_cluster(self, window)

    def ready_for_right_dock_stack(self, window):
        return PetInteractionController.ready_for_right_dock_stack(self, window)

    def supports_any_action(self, window, action_names):
        return PetInteractionController.supports_any_action(self, window, action_names)

    def playable_bottom_dock_variants(self, selected):
        return PetInteractionController.playable_bottom_dock_variants(self, selected)

    def selected_windows_for_characters(self, characters):
        return PetInteractionController.selected_windows_for_characters(self, characters)


def test_known_pet_folder_maps_to_character_id():
    assert infer_character_id_from_path(Path("assets") / "XiaobaPet") == "xiaoba"
    assert infer_character_id_from_path(Path("assets") / "JiyiPet") == "jiyi"
    assert infer_character_id_from_path(Path("assets") / "UsagiPet") == "usagi"


def test_max_center_distance_uses_window_centers():
    windows = [FakeWindow(0, 0), FakeWindow(300, 0), FakeWindow(0, 400)]

    assert round(max_center_distance(windows)) == 500


def test_trio_concert_requires_close_group_without_cooldown():
    assert TRIO_CONCERT_RULE["max_distance"] == 720
    assert "cooldown_seconds" not in TRIO_CONCERT_RULE


def test_bottom_dock_cluster_owns_bottom_scene(monkeypatch):
    windows = [
        FakeTrioWindow("xiaoba", 0, 900, animations={"trio-bottom-fig1", "concert-piano"}),
        FakeTrioWindow("jiyi", 150, 900, animations={"trio-bottom-fig1", "concert-hum"}),
        FakeTrioWindow("usagi", 300, 900, animations={"trio-bottom-fig1", "concert-fireworks"}),
    ]
    controller = FakeTrioController(windows)

    monkeypatch.setattr("window_pet_app.interactions.random.choice", lambda variants: variants[0])
    handled = PetInteractionController.try_bottom_dock_cluster_pose(controller)

    assert handled is True
    assert [window.calls[0][0] for window in windows] == ["trio-bottom-fig1"] * 3


def test_bottom_dock_cluster_random_pool_requires_all_three_to_support_variant(monkeypatch):
    windows = [
        FakeTrioWindow("xiaoba", 0, 900, animations={"trio-bottom-fig1", "trio-bottom-fig3"}),
        FakeTrioWindow("jiyi", 150, 900, animations={"trio-bottom-fig1", "trio-bottom-fig3"}),
        FakeTrioWindow("usagi", 300, 900, animations={"trio-bottom-fig1"}),
    ]
    controller = FakeTrioController(windows)
    chosen = []

    def choose(variants):
        chosen.extend(variant["id"] for variant in variants)
        return variants[-1]

    monkeypatch.setattr("window_pet_app.interactions.random.choice", choose)

    assert PetInteractionController.try_bottom_dock_cluster_pose(controller) is True
    assert chosen == ["bottom-dock-figure-1"]
    assert [window.calls[0][0] for window in windows] == ["trio-bottom-fig1"] * 3


def test_right_dock_stack_triggers_right_pose():
    windows = [
        FakeTrioWindow("xiaoba", 900, 0, dock_mode="right", animations={"trio-right-fig2", "concert-piano"}),
        FakeTrioWindow("jiyi", 900, 150, dock_mode="right", animations={"trio-right-fig2", "concert-hum"}),
        FakeTrioWindow("usagi", 900, 300, dock_mode="right", animations={"trio-right-fig2", "concert-fireworks"}),
    ]
    for window in windows:
        window.current_frame_animation = "edge-crawl-right"
    controller = FakeTrioController(windows)

    assert PetInteractionController.try_right_dock_stack_pose(controller) is True
    assert [window.calls[0][0] for window in windows] == ["trio-right-fig2"] * 3


def test_time_of_day_trio_triggers_once_per_day():
    windows = [
        FakeTrioWindow("xiaoba", 0, 0, dock_mode="none", animations={"trio-time-1500-fig4"}),
        FakeTrioWindow("jiyi", 150, 0, dock_mode="none", animations={"trio-time-1500-fig4"}),
        FakeTrioWindow("usagi", 300, 0, dock_mode="none", animations={"trio-time-1500-fig4"}),
    ]
    for window in windows:
        window.current_frame_animation = "idle"
    controller = FakeTrioController(windows)
    controller.time_rule_triggered_dates = {}
    controller.current_datetime = lambda: datetime(2026, 5, 10, 15, 0, 12)

    assert PetInteractionController.try_time_of_day_trio_pose(controller) is True
    assert [window.calls[0][0] for window in windows] == ["trio-time-1500-fig4"] * 3

    assert PetInteractionController.try_time_of_day_trio_pose(controller) is True
    assert [len(window.calls) for window in windows] == [1, 1, 1]


def test_reward_action_falls_back_when_reward_animation_is_missing():
    window = FakeRewardWindow()
    controller = FakeRewardController([window])

    played = PetInteractionController.play_reward(controller, "test")

    assert played == ["fake:review"]
    assert [call[0] for call in window.calls] == ["reward", "review"]
