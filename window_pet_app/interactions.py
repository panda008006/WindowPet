import math
import random
from datetime import datetime
from pathlib import Path
from time import monotonic

from PySide6.QtCore import QObject, QTimer

from . import state
from .logging_utils import log_info


CHARACTER_BY_FOLDER = {
    "xiaobapet": "xiaoba",
    "jiyipet": "jiyi",
    "usagipet": "usagi",
    "nuonuopet": "nuonuo",
    "mianmianpet": "mianmian",
}


TRIO_CONCERT_RULE = {
    "id": "concert-trio",
    "characters": ("xiaoba", "jiyi", "usagi"),
    "max_distance": 720,
    "actions": {
        "xiaoba": ("concert-piano", "review"),
        "jiyi": ("concert-hum", "waving"),
        "usagi": ("concert-fireworks", "waving"),
    },
}

BOTTOM_DOCK_CLUSTER_RULE = {
    "id": "bottom-dock-cluster",
    "characters": ("xiaoba", "jiyi", "usagi"),
    "dock_mode": "bottom",
    "max_distance": 620,
    "cooldown_seconds": 45,
    "ready_animations": ("idle", "edge-crawl-bottom"),
    "variants": (
        {
            "id": "bottom-dock-figure-1",
            "actions": {
                "xiaoba": ("trio-bottom-fig1",),
                "jiyi": ("trio-bottom-fig1",),
                "usagi": ("trio-bottom-fig1",),
            },
        },
        {
            "id": "bottom-dock-figure-3",
            "actions": {
                "xiaoba": ("trio-bottom-fig3",),
                "jiyi": ("trio-bottom-fig3",),
                "usagi": ("trio-bottom-fig3",),
            },
        },
    ),
}

RIGHT_DOCK_STACK_RULE = {
    "id": "right-dock-stack",
    "characters": ("xiaoba", "jiyi", "usagi"),
    "dock_mode": "right",
    "max_distance": 620,
    "cooldown_seconds": 45,
    "ready_animations": ("idle", "edge-crawl-right"),
    "actions": {
        "xiaoba": ("trio-right-fig2",),
        "jiyi": ("trio-right-fig2",),
        "usagi": ("trio-right-fig2",),
    },
}

TIME_OF_DAY_TRIO_RULES = (
    {
        "id": "trio-time-0900",
        "hour": 9,
        "minute": 0,
        "characters": ("xiaoba", "jiyi", "usagi"),
        "actions": {
            "xiaoba": ("trio-time-0900-fig6",),
            "jiyi": ("trio-time-0900-fig6",),
            "usagi": ("trio-time-0900-fig6",),
        },
    },
    {
        "id": "trio-time-1500",
        "hour": 15,
        "minute": 0,
        "characters": ("xiaoba", "jiyi", "usagi"),
        "actions": {
            "xiaoba": ("trio-time-1500-fig4",),
            "jiyi": ("trio-time-1500-fig4",),
            "usagi": ("trio-time-1500-fig4",),
        },
    },
    {
        "id": "trio-time-2100",
        "hour": 21,
        "minute": 0,
        "characters": ("xiaoba", "jiyi", "usagi"),
        "actions": {
            "xiaoba": ("trio-time-2100-fig5",),
            "jiyi": ("trio-time-2100-fig5",),
            "usagi": ("trio-time-2100-fig5",),
        },
    },
)


def infer_character_id_from_path(path) -> str:
    folder = Path(path).name.lower()
    return CHARACTER_BY_FOLDER.get(folder, folder)


def center_point(window) -> tuple[float, float]:
    return (
        float(window.x()) + float(max(1, window.width())) / 2,
        float(window.y()) + float(max(1, window.height())) / 2,
    )


def max_center_distance(windows) -> float:
    centers = [center_point(window) for window in windows]
    if len(centers) < 2:
        return 0.0
    distance = 0.0
    for index, first in enumerate(centers):
        for second in centers[index + 1 :]:
            distance = max(distance, math.dist(first, second))
    return distance


class PetInteractionController(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.tick)
        self.bottom_dock_cluster_next_allowed = 0.0
        self.right_dock_stack_next_allowed = 0.0
        self.time_rule_triggered_dates = {}

    def start(self):
        self.timer.start()

    def tick(self):
        # Extra named actions are intentionally manual-only. Keep the
        # controller alive for compatibility with existing app state, but do
        # not start choreography from time, proximity, or docking events.
        return

    def visible_windows(self):
        return [window for window in list(state.WINDOWS) if window.isVisible()]

    def windows_by_character(self):
        grouped = {}
        for window in self.visible_windows():
            character_id = getattr(window, "character_id", "") or infer_character_id_from_path(
                getattr(window, "asset_path", "")
            )
            if not character_id:
                continue
            grouped.setdefault(character_id, []).append(window)
        return grouped

    def ready_for_group_action(self, window) -> bool:
        if getattr(window, "is_dragging_asset", False):
            return False
        if getattr(window, "screen_saver_active", False):
            return False
        if getattr(window, "asset_type", "") != "frame_animation":
            return False
        current = getattr(window, "current_frame_animation", "idle")
        return current == "idle"

    def current_datetime(self):
        return datetime.now()

    def ready_for_bottom_dock_cluster(self, window) -> bool:
        if getattr(window, "is_dragging_asset", False):
            return False
        if getattr(window, "screen_saver_active", False):
            return False
        if getattr(window, "asset_type", "") != "frame_animation":
            return False
        if getattr(window, "dock_mode", "none") != BOTTOM_DOCK_CLUSTER_RULE["dock_mode"]:
            return False
        current = getattr(window, "current_frame_animation", "idle")
        return current in BOTTOM_DOCK_CLUSTER_RULE["ready_animations"]

    def supports_any_action(self, window, action_names) -> bool:
        available_animations = getattr(window, "available_animations", None)
        if callable(available_animations):
            if any(name in set(available_animations()) for name in action_names):
                return True

        frame_animation_definition = getattr(window, "frame_animation_definition", None)
        if callable(frame_animation_definition):
            for name in action_names:
                frame_paths, _fps, _loop = frame_animation_definition(name)
                if frame_paths:
                    return True
        return False

    def playable_bottom_dock_variants(self, selected):
        rule = BOTTOM_DOCK_CLUSTER_RULE
        windows_by_character = dict(zip(rule["characters"], selected, strict=True))
        playable = []
        for variant in rule["variants"]:
            actions = variant["actions"]
            if all(
                self.supports_any_action(windows_by_character[character_id], actions.get(character_id, ()))
                for character_id in rule["characters"]
            ):
                playable.append(variant)
        return playable

    def try_bottom_dock_cluster_pose(self):
        rule = BOTTOM_DOCK_CLUSTER_RULE
        grouped = self.windows_by_character()
        selected = []
        for character_id in rule["characters"]:
            candidates = grouped.get(character_id, [])
            if not candidates:
                return False
            selected.append(candidates[0])

        if any(getattr(window, "dock_mode", "none") != rule["dock_mode"] for window in selected):
            return False
        if max_center_distance(selected) > rule["max_distance"]:
            return False

        # This bottom-edge scene owns the trio so the ordinary concert rule cannot steal it.
        if any(not self.ready_for_bottom_dock_cluster(window) for window in selected):
            return True

        now = monotonic()
        if now < getattr(self, "bottom_dock_cluster_next_allowed", 0.0):
            return True

        playable_variants = self.playable_bottom_dock_variants(selected)
        if not playable_variants:
            return True

        variant = random.choice(playable_variants)
        played = []
        for character_id, window in zip(rule["characters"], selected, strict=True):
            action_names = variant["actions"].get(character_id, ())
            for action_name in action_names:
                if window.play_frame_animation(action_name, loop=False, return_to_idle=True):
                    played.append(f"{character_id}:{action_name}")
                    break

        self.bottom_dock_cluster_next_allowed = now + rule["cooldown_seconds"]
        if played:
            log_info("Interaction triggered %s/%s: %s", rule["id"], variant["id"], ", ".join(played))
        return True

    def ready_for_right_dock_stack(self, window) -> bool:
        if getattr(window, "is_dragging_asset", False):
            return False
        if getattr(window, "screen_saver_active", False):
            return False
        if getattr(window, "asset_type", "") != "frame_animation":
            return False
        if getattr(window, "dock_mode", "none") != RIGHT_DOCK_STACK_RULE["dock_mode"]:
            return False
        current = getattr(window, "current_frame_animation", "idle")
        return current in RIGHT_DOCK_STACK_RULE["ready_animations"]

    def try_right_dock_stack_pose(self):
        rule = RIGHT_DOCK_STACK_RULE
        grouped = self.windows_by_character()
        selected = []
        for character_id in rule["characters"]:
            candidates = grouped.get(character_id, [])
            if not candidates:
                return False
            selected.append(candidates[0])

        if any(getattr(window, "dock_mode", "none") != rule["dock_mode"] for window in selected):
            return False
        if max_center_distance(selected) > rule["max_distance"]:
            return False

        # This right-edge stack owns the trio so the ordinary concert rule cannot steal it.
        if any(not self.ready_for_right_dock_stack(window) for window in selected):
            return True

        now = monotonic()
        if now < getattr(self, "right_dock_stack_next_allowed", 0.0):
            return True

        if not all(
            self.supports_any_action(window, rule["actions"].get(character_id, ()))
            for character_id, window in zip(rule["characters"], selected, strict=True)
        ):
            return True

        played = []
        for character_id, window in zip(rule["characters"], selected, strict=True):
            for action_name in rule["actions"].get(character_id, ()):
                if window.play_frame_animation(action_name, loop=False, return_to_idle=True):
                    played.append(f"{character_id}:{action_name}")
                    break

        self.right_dock_stack_next_allowed = now + rule["cooldown_seconds"]
        if played:
            log_info("Interaction triggered %s: %s", rule["id"], ", ".join(played))
        return True

    def selected_windows_for_characters(self, characters):
        grouped = self.windows_by_character()
        selected = []
        for character_id in characters:
            candidates = grouped.get(character_id, [])
            if not candidates:
                return []
            selected.append(candidates[0])
        return selected

    def try_time_of_day_trio_pose(self):
        now = self.current_datetime()
        today_key = now.date().isoformat()
        for rule in TIME_OF_DAY_TRIO_RULES:
            if now.hour != rule["hour"] or now.minute != rule["minute"]:
                continue
            if self.time_rule_triggered_dates.get(rule["id"]) == today_key:
                return True

            selected = self.selected_windows_for_characters(rule["characters"])
            if not selected:
                return False
            if any(not self.ready_for_group_action(window) for window in selected):
                return True
            if not all(
                self.supports_any_action(window, rule["actions"].get(character_id, ()))
                for character_id, window in zip(rule["characters"], selected, strict=True)
            ):
                return True

            played = []
            for character_id, window in zip(rule["characters"], selected, strict=True):
                for action_name in rule["actions"].get(character_id, ()):
                    if window.play_frame_animation(action_name, loop=False, return_to_idle=True):
                        played.append(f"{character_id}:{action_name}")
                        break

            self.time_rule_triggered_dates[rule["id"]] = today_key
            if played:
                log_info("Interaction triggered %s at %02d:%02d: %s", rule["id"], rule["hour"], rule["minute"], ", ".join(played))
            return True
        return False

    def ready_for_reward_action(self, window) -> bool:
        return self.ready_for_group_action(window)

    def reward_candidates(self):
        return [
            window
            for window in self.visible_windows()
            if self.ready_for_reward_action(window)
        ]

    def play_reward(self, reason=""):
        played = []
        for window in self.reward_candidates():
            character_id = getattr(window, "character_id", "") or infer_character_id_from_path(
                getattr(window, "asset_path", "")
            )
            for action_name in ("reward", "review", "waving"):
                if window.play_frame_animation(action_name, loop=False, return_to_idle=True):
                    played.append(f"{character_id}:{action_name}")
                    break

        if played:
            label = f" {reason}" if reason else ""
            log_info("Reward interaction triggered%s: %s", label, ", ".join(played))
        return played

    def try_trio_concert(self):
        rule = TRIO_CONCERT_RULE
        grouped = self.windows_by_character()
        selected = []
        for character_id in rule["characters"]:
            candidates = grouped.get(character_id, [])
            if not candidates:
                return
            selected.append(candidates[0])

        if any(not self.ready_for_group_action(window) for window in selected):
            return
        if max_center_distance(selected) > rule["max_distance"]:
            return

        played = []
        for character_id, window in zip(rule["characters"], selected, strict=True):
            action_names = rule["actions"].get(character_id, ())
            for action_name in action_names:
                if window.play_frame_animation(action_name, loop=False, return_to_idle=True):
                    played.append(f"{character_id}:{action_name}")
                    break

        if played:
            log_info("Interaction triggered %s: %s", rule["id"], ", ".join(played))
