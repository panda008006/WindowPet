import json
from datetime import date
from pathlib import Path

from .constants import BASE_DIR


MEDAL_STATE_PATH = BASE_DIR / "medals.json"
REQUIRED_MEDAL_TRIGGERS = {
    "static-idle",
    "left-click",
    "left-drag",
}
INTERACTIVE_MEDAL_TRIGGERS = REQUIRED_MEDAL_TRIGGERS - {"static-idle"}

MEDAL_DEFINITIONS = (
    {
        "id": "first-response",
        "icon": "✦",
        "title": {"zh": "第一次回应", "en": "First Response"},
        "detail": {"zh": "第一次让角色回应你的互动", "en": "Let a pet respond to you for the first time"},
        "unlock": lambda state: bool(set(state["triggers"]) & INTERACTIVE_MEDAL_TRIGGERS),
    },
    {
        "id": "three-days",
        "icon": "☼",
        "title": {"zh": "熟悉的身影", "en": "A Familiar Face"},
        "detail": {"zh": "自然使用 Window Pet 3 天", "en": "Use Window Pet naturally on 3 days"},
        "unlock": lambda state: len(state["active_days"]) >= 3,
    },
    {
        "id": "three-responses",
        "icon": "✧",
        "title": {"zh": "三种回应", "en": "Three Responses"},
        "detail": {"zh": "体验待机、单击和拖拽三种基础状态", "en": "Experience idle, click, and drag"},
        "unlock": lambda state: REQUIRED_MEDAL_TRIGGERS.issubset(state["triggers"]),
    },
    {
        "id": "pet-collector",
        "icon": "♢",
        "title": {"zh": "角色收藏家", "en": "Pet Collector"},
        "detail": {"zh": "和 3 位桌面伙伴相处过", "en": "Spend time with 3 desktop companions"},
        "unlock": lambda state: len(state["pets"]) >= 3,
    },
    {
        "id": "one-week",
        "icon": "◌",
        "title": {"zh": "一周陪伴", "en": "A Week Together"},
        "detail": {"zh": "自然使用 Window Pet 7 天", "en": "Use Window Pet naturally on 7 days"},
        "unlock": lambda state: len(state["active_days"]) >= 7,
    },
    {
        "id": "custom-companion",
        "icon": "♡",
        "title": {"zh": "专属伙伴", "en": "Custom Companion"},
        "detail": {"zh": "拥有一只定制角色后解锁", "en": "Unlock after receiving a custom pet"},
        "unlock": lambda state: bool(state["custom_pet"]),
    },
    {
        "id": "quiet-company",
        "icon": "⌁",
        "title": {"zh": "安静陪伴", "en": "Quiet Company"},
        "detail": {"zh": "让角色保持静态陪伴", "en": "Keep a pet in calm static idle"},
        "unlock": lambda state: "static-idle" in state["triggers"],
    },
    {
        "id": "action-explorer",
        "icon": "✺",
        "title": {"zh": "动作体验家", "en": "Interaction Explorer"},
        "detail": {"zh": "按自己的节奏体验两种基础互动", "en": "Try both basic interactions at your own pace"},
        "unlock": lambda state: INTERACTIVE_MEDAL_TRIGGERS.issubset(state["triggers"]),
    },
    {
        "id": "seasonal-letter",
        "icon": "❋",
        "title": {"zh": "季节来信", "en": "Seasonal Letter"},
        "detail": {"zh": "季节活动开放后可获得", "en": "Available during a future seasonal event"},
        "unlock": lambda _state: False,
        "seasonal": True,
    },
)


def _blank_state():
    return {
        "schema_version": 1,
        "active_days": [],
        "triggers": [],
        "pets": [],
        "custom_pet": False,
        "hidden": False,
    }


class MedalStore:
    def __init__(self, path: Path | str = MEDAL_STATE_PATH, *, today: date | None = None):
        self.path = Path(path)
        self.today = today or date.today()
        self.data = self._load()

    @property
    def hidden(self):
        return bool(self.data["hidden"])

    def _load(self):
        default = _blank_state()
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError, TypeError):
            return default
        if not isinstance(loaded, dict):
            return default
        for key in ("active_days", "triggers", "pets"):
            values = loaded.get(key)
            if isinstance(values, list):
                default[key] = sorted({str(value) for value in values if str(value).strip()})
        default["custom_pet"] = bool(loaded.get("custom_pet", False))
        default["hidden"] = bool(loaded.get("hidden", False))
        return default

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temp_path.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(self.path)

    def _add(self, key, value):
        values = set(self.data[key])
        if value in values:
            return False
        values.add(value)
        self.data[key] = sorted(values)
        self._save()
        return True

    def record_launch(self):
        changed = self._add("active_days", self.today.isoformat())
        trigger_changed = self.record_trigger("static-idle")
        return changed or trigger_changed

    def record_trigger(self, trigger_name):
        trigger_name = str(trigger_name or "").strip()
        if trigger_name not in REQUIRED_MEDAL_TRIGGERS:
            return False
        return self._add("triggers", trigger_name)

    def record_pet(self, character_id, *, custom=False):
        character_id = str(character_id or "").strip().lower()
        changed = self._add("pets", character_id) if character_id else False
        if custom and not self.data["custom_pet"]:
            self.data["custom_pet"] = True
            self._save()
            changed = True
        return changed

    def set_hidden(self, hidden):
        hidden = bool(hidden)
        if self.data["hidden"] == hidden:
            return False
        self.data["hidden"] = hidden
        self._save()
        return True

    def snapshot(self, language="zh"):
        language = "en" if language == "en" else "zh"
        result = []
        for definition in MEDAL_DEFINITIONS:
            unlocked = bool(definition["unlock"](self.data))
            if unlocked:
                status = "Unlocked" if language == "en" else "已解锁"
            elif definition.get("seasonal"):
                status = "Future event" if language == "en" else "活动未开放"
            else:
                status = "Unlock naturally" if language == "en" else "自然解锁"
            result.append(
                {
                    "id": definition["id"],
                    "icon": definition["icon"],
                    "title": definition["title"][language],
                    "detail": definition["detail"][language],
                    "status": status,
                    "unlocked": unlocked,
                }
            )
        return result

    def unlocked_count(self):
        return sum(1 for medal in self.snapshot() if medal["unlocked"])
