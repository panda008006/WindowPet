import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .constants import BASE_DIR


NOTCHNOTES_PATH = BASE_DIR / "notchnotes.json"

DEFAULT_DATA = {
    "current_scene": "todo",
    "anchor_mode": "pet",  # "pet" (attached above pet) | "notch" (screen top center) | "float" (freely positioned)
    "opacity": 0.95,
    "pin_top": True,
    "scenes": {
        "todo": {
            "title": "待办清单",
            "content": (
                "# 今日待办\n"
                "- [ ] 体验 WindowPet 3D 黏土拟态新界面\n"
                "- [ ] 使用 NotchNotes 便签记录任务灵感\n"
                "- [ ] 尝试把文件拖入底部暂存架快速暂存\n"
            ),
        },
        "notes": {
            "title": "工作笔记",
            "content": (
                "# 工作与学习笔记\n\n"
                "## 快捷提示\n"
                "- 灵感来源于 **oil-oil/NotchNotes** 暗黑美学便签\n"
                "- 点击便签顶部药丸按钮可在 **Todo / Notes / Ideas** 之间流畅切换\n"
                "- 支持 Markdown 语法与底部文件随手暂存架\n"
            ),
        },
        "ideas": {
            "title": "灵感草稿",
            "content": (
                "# 脑洞与碎碎念\n\n"
                "- [Idea] 给桌宠增加更多微互动动作\n"
                "- [Idea] 定时提醒与番茄钟完成联动播报\n"
            ),
        },
    },
    "file_shelf": [],
}


class NotchNotesStore:
    _instance: Optional["NotchNotesStore"] = None

    def __init__(self, path: Optional[Path] = None):
        self.path = path or NOTCHNOTES_PATH
        self.data: dict = {}
        self.load()

    @classmethod
    def get_instance(cls) -> "NotchNotesStore":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self.data = DEFAULT_DATA.copy()
                self.data.update(loaded)
                # Ensure structure
                if "scenes" not in self.data:
                    self.data["scenes"] = DEFAULT_DATA["scenes"].copy()
                for sc_key, sc_val in DEFAULT_DATA["scenes"].items():
                    if sc_key not in self.data["scenes"]:
                        self.data["scenes"][sc_key] = sc_val.copy()
                if "file_shelf" not in self.data:
                    self.data["file_shelf"] = []
                return
            except Exception:
                pass
        self.data = json.loads(json.dumps(DEFAULT_DATA))
        self.save()

    def save(self):
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self.path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.path)
        except Exception as e:
            print(f"Failed to save notchnotes: {e}")

    # --- Scene & Content ---

    @property
    def current_scene_id(self) -> str:
        return self.data.get("current_scene", "todo")

    @current_scene_id.setter
    def current_scene_id(self, scene_id: str):
        if scene_id in self.data.get("scenes", {}):
            self.data["current_scene"] = scene_id
            self.save()

    def get_scene(self, scene_id: str) -> dict:
        return self.data.get("scenes", {}).get(scene_id, {})

    def get_content(self, scene_id: Optional[str] = None) -> str:
        scene_id = scene_id or self.current_scene_id
        return self.get_scene(scene_id).get("content", "")

    def set_content(self, scene_id: str, content: str):
        if scene_id in self.data.get("scenes", {}):
            self.data["scenes"][scene_id]["content"] = content
            self.save()

    # --- Todo Checklist Parsing & Manipulation ---

    def parse_todo_items(self) -> List[dict]:
        """
        Parses all lines matching `- [ ]` or `- [x]` or `- [X]` from the todo scene.
        Returns a list of dicts: {'line_index': int, 'checked': bool, 'text': str, 'raw': str}
        """
        content = self.get_content("todo")
        lines = content.splitlines()
        items = []
        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(("- [ ]", "- [x]", "- [X]", "* [ ]", "* [x]", "* [X]")):
                is_checked = stripped[3:4].lower() == "x"
                text = stripped[5:].strip()
                items.append({
                    "line_index": idx,
                    "checked": is_checked,
                    "text": text,
                    "raw": line,
                })
        return items

    def toggle_todo_item(self, item_index: int) -> bool:
        """Toggles the check state of the i-th todo item."""
        items = self.parse_todo_items()
        if not (0 <= item_index < len(items)):
            return False
        target_item = items[item_index]
        line_idx = target_item["line_index"]
        content = self.get_content("todo")
        lines = content.splitlines()

        old_line = lines[line_idx]
        if target_item["checked"]:
            # uncheck
            new_line = old_line.replace("- [x]", "- [ ]").replace("- [X]", "- [ ]").replace("* [x]", "* [ ]").replace("* [X]", "* [ ]")
        else:
            # check
            new_line = old_line.replace("- [ ]", "- [x]").replace("* [ ]", "* [x]")

        lines[line_idx] = new_line
        self.set_content("todo", "\n".join(lines))
        return not target_item["checked"]

    def add_todo_item(self, text: str):
        """Appends a new unchecked task to the todo scene."""
        clean = text.strip()
        if not clean:
            return
        content = self.get_content("todo")
        line = f"- [ ] {clean}"
        if content.strip():
            new_content = content.rstrip() + "\n" + line
        else:
            new_content = "# 今日待办\n" + line
        self.set_content("todo", new_content)

    def remove_todo_item(self, item_index: int) -> bool:
        """Removes the i-th todo item from the content."""
        items = self.parse_todo_items()
        if not (0 <= item_index < len(items)):
            return False
        line_idx = items[item_index]["line_index"]
        content = self.get_content("todo")
        lines = content.splitlines()
        del lines[line_idx]
        self.set_content("todo", "\n".join(lines))
        return True

    def get_todo_stats(self) -> Tuple[int, int]:
        """Returns (completed_count, total_count)."""
        items = self.parse_todo_items()
        if not items:
            return 0, 0
        completed = sum(1 for it in items if it["checked"])
        return completed, len(items)

    def get_top_pending_task(self) -> Optional[str]:
        """Returns the first uncompleted task text (for companion dialogue)."""
        items = self.parse_todo_items()
        for it in items:
            if not it["checked"]:
                return it["text"]
        return None

    # --- File Shelf (暂存架) ---

    @property
    def file_shelf(self) -> List[dict]:
        return self.data.get("file_shelf", [])

    def add_file_shelf_item(self, file_path: str) -> bool:
        p = Path(file_path).resolve()
        if not p.exists():
            return False
        shelf = self.data.setdefault("file_shelf", [])
        # Avoid duplicate paths
        for item in shelf:
            if item.get("path") == str(p):
                return False
        try:
            size_bytes = p.stat().st_size
            if size_bytes < 1024:
                size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
        except Exception:
            size_str = ""

        shelf.append({
            "path": str(p),
            "name": p.name,
            "ext": p.suffix.lower(),
            "size": size_str,
            "is_dir": p.is_dir(),
        })
        self.save()
        return True

    def remove_file_shelf_item(self, index: int) -> bool:
        shelf = self.data.get("file_shelf", [])
        if 0 <= index < len(shelf):
            del shelf[index]
            self.save()
            return True
        return False

    def clear_file_shelf(self):
        self.data["file_shelf"] = []
        self.save()

    # --- Preferences ---

    @property
    def anchor_mode(self) -> str:
        return self.data.get("anchor_mode", "pet")

    @anchor_mode.setter
    def anchor_mode(self, mode: str):
        if mode in ("pet", "notch", "float"):
            self.data["anchor_mode"] = mode
            self.save()

    @property
    def opacity(self) -> float:
        return float(self.data.get("opacity", 0.95))

    @opacity.setter
    def opacity(self, val: float):
        self.data["opacity"] = max(0.4, min(1.0, float(val)))
        self.save()

    @property
    def pin_top(self) -> bool:
        return bool(self.data.get("pin_top", True))

    @pin_top.setter
    def pin_top(self, val: bool):
        self.data["pin_top"] = bool(val)
        self.save()
