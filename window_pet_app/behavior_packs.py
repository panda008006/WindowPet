import json
from dataclasses import dataclass

from .constants import BASE_DIR
from .logging_utils import log_warning


BEHAVIOR_PACK_ROOT = BASE_DIR / "behavior_packs"

SCREEN_SAVER_ENTER = "screen_saver_enter"
SCREEN_SAVER_EXIT = "screen_saver_exit"
STARTUP = "startup"

DEFAULT_EVENT_PACKS = {
    SCREEN_SAVER_ENTER: "screensaver-sleep",
    SCREEN_SAVER_EXIT: "wake-stretch",
    STARTUP: "wake-stretch",
}


@dataclass(frozen=True)
class BehaviorAction:
    event_name: str
    pack_id: str
    animation_name: str
    loop: bool
    return_to_idle: bool


BUILTIN_PACKS = {
    "screensaver-sleep": {
        "id": "screensaver-sleep",
        "events": {
            SCREEN_SAVER_ENTER: {
                "animation_candidates": [
                    "sleep",
                    "sleeping",
                    "lying-sleep",
                    "nap",
                    "idle_sleep",
                    "idle_sleepy",
                    "waiting",
                    "idle",
                ],
                "loop": True,
                "return_to_idle": False,
            }
        },
    },
    "wake-stretch": {
        "id": "wake-stretch",
        "events": {
            STARTUP: {
                "animation_candidates": [
                    "stretch",
                    "wake-stretch",
                    "waking-up",
                    "wake",
                    "waving",
                    "jumping",
                    "idle",
                ],
                "loop": False,
                "return_to_idle": True,
            },
            SCREEN_SAVER_EXIT: {
                "animation_candidates": [
                    "stretch",
                    "wake-stretch",
                    "waking-up",
                    "wake",
                    "waving",
                    "jumping",
                    "idle",
                ],
                "loop": False,
                "return_to_idle": True,
            },
        },
    },
}


def behavior_pack_mapping(metadata):
    mapping = dict(DEFAULT_EVENT_PACKS)
    configured = metadata.get("behavior_packs") if isinstance(metadata, dict) else None
    if not isinstance(configured, dict):
        return mapping

    for event_name, pack_id in configured.items():
        event_key = str(event_name).strip()
        if not event_key:
            continue
        if pack_id in (False, None, ""):
            mapping.pop(event_key, None)
        else:
            mapping[event_key] = str(pack_id).strip()
    return mapping


def load_behavior_pack(pack_id):
    pack_id = str(pack_id or "").strip()
    if not pack_id:
        return None

    pack_path = BEHAVIOR_PACK_ROOT / pack_id / "behavior_pack.json"
    if pack_path.exists():
        try:
            data = json.loads(pack_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            log_warning("Invalid behavior pack %s: %s", pack_path, exc)
            return None
        return data if isinstance(data, dict) else None

    return BUILTIN_PACKS.get(pack_id)


def resolve_behavior_action(metadata, event_name, available_animations):
    if not isinstance(metadata, dict):
        metadata = {}

    event_key = str(event_name or "").strip()
    pack_id = behavior_pack_mapping(metadata).get(event_key)
    if not pack_id:
        return None

    pack = load_behavior_pack(pack_id)
    if not isinstance(pack, dict):
        return None

    events = pack.get("events")
    definition = events.get(event_key) if isinstance(events, dict) else None
    if not isinstance(definition, dict):
        return None

    available = {str(name) for name in available_animations}
    candidates = definition.get("animation_candidates")
    if not isinstance(candidates, list):
        candidates = []

    animation_name = ""
    for candidate in candidates:
        candidate_name = str(candidate)
        if candidate_name in available:
            animation_name = candidate_name
            break

    if not animation_name and bool(definition.get("allow_idle_fallback", True)) and "idle" in available:
        animation_name = "idle"
    if not animation_name:
        return None

    loop = bool(definition.get("loop", False))
    default_return = not loop
    return BehaviorAction(
        event_name=event_key,
        pack_id=str(pack.get("id") or pack_id),
        animation_name=animation_name,
        loop=loop,
        return_to_idle=bool(definition.get("return_to_idle", default_return)),
    )
