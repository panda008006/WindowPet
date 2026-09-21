"""
WindowPet 角色包规范与动作说明自生成工具
==========================================
让民间创作者和开源社区轻松管理角色、看清每一个角色的动作组成。
支持自动分析角色文件夹内的帧序列、动作子目录、触发方式，并输出清晰的《动作说明.md》。
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


KNOWN_ACTION_LABELS: Dict[str, str] = {
    "idle": "基础待机",
    "click": "轻戳点击",
    "drag": "提溜拖拽",
    "hover": "好奇注视",
    "waiting": "乖乖等待",
    "waving": "挥手打招呼",
    "jumping": "开心跳跃",
    "running": "欢快奔跑",
    "running-left": "向左奔跑",
    "running-right": "向右奔跑",
    "failed": "受挫委屈",
    "review": "特殊才艺",
    "reward": "奖励动作",
    "feather-tickle": "羽毛挠痒",
    "whip-hit": "抽鞭督促",
    "gesture-dance": "手势舞",
    "happy-dance": "欢庆跳舞",
    "reverse-warning": "倒车请注意",
    "right-double-click": "双击互动",
    "fall": "空中下落",
    "land": "着地缓冲",
    "sleep": "困倦打盹",
}

DEFAULT_TRIGGER_NAMES: Dict[str, str] = {
    "left-click": "🔴 单击触发 (Click)",
    "left-double-click": "🔵 双击触发 (Double Click)",
    "idle": "🟢 默认待机 (Default Idle)",
    "left-drag": "🟡 拖拽互动 (Drag)",
    "menu": "🟣 右键菜单点播 (Action Menu)",
    "idle_variant": "⚪ 待机随机变体 (Idle Variant)",
}


def guess_action_label(action_name: str, existing_label: Optional[str] = None) -> str:
    if existing_label and str(existing_label).strip():
        return str(existing_label).strip()
    clean_name = action_name.strip().lower()
    if clean_name in KNOWN_ACTION_LABELS:
        return KNOWN_ACTION_LABELS[clean_name]
    return clean_name.replace("-", " ").replace("_", " ").title()


def count_folder_frames(folder: Path) -> int:
    if not folder.exists() or not folder.is_dir():
        return 0
    valid_exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    return sum(1 for p in folder.iterdir() if p.is_file() and p.suffix.lower() in valid_exts)


def inspect_character_folder(folder_path: Path) -> Dict[str, Any]:
    """深度分析角色文件夹，提取所有动作、帧数、配置和触发方式"""
    folder = Path(folder_path).resolve()
    asset_json_path = folder / "asset.json"

    meta: Dict[str, Any] = {}
    if asset_json_path.exists():
        try:
            content = asset_json_path.read_text(encoding="utf-8-sig")
            meta = json.loads(content)
        except Exception:
            try:
                meta = json.loads(asset_json_path.read_text(encoding="gbk"))
            except Exception:
                meta = {}

    character_name = meta.get("name") or folder.name
    character_id = meta.get("character_id") or folder.name
    base_fps = int(meta.get("fps") or 10)
    preview_file = meta.get("preview") or ""
    if not preview_file:
        for p in folder.glob("*.png"):
            preview_file = p.name
            break

    triggers = meta.get("triggers", {}) if isinstance(meta.get("triggers"), dict) else {}
    idle_variants = set(meta.get("idle_variants", []) if isinstance(meta.get("idle_variants"), list) else [])
    menu_actions = set(meta.get("menu_actions", []) if isinstance(meta.get("menu_actions"), list) else [])

    raw_anims = meta.get("animations", {}) if isinstance(meta.get("animations"), dict) else {}
    action_items: List[Dict[str, Any]] = []

    # 1. 扫描 asset.json 中列出的动作
    seen_folders = set()
    for anim_name, anim_conf in raw_anims.items():
        if not isinstance(anim_conf, dict):
            anim_conf = {}
        sub_folder_name = anim_conf.get("folder", anim_name)
        seen_folders.add(sub_folder_name)
        sub_dir = folder if sub_folder_name in {".", ""} else folder / sub_folder_name
        frame_count = count_folder_frames(sub_dir)
        if sub_folder_name in {".", ""} and frame_count == 0:
            frame_count = sum(1 for p in folder.glob("*.png") if p.is_file())

        label = guess_action_label(anim_name, anim_conf.get("label"))
        fps = int(anim_conf.get("fps") or base_fps)
        loop = bool(anim_conf.get("loop", anim_name == "idle"))

        # 推断当前绑定的触发方式
        trigger_tags = []
        if triggers.get("left-click") == anim_name or (not triggers and anim_name == "click"):
            trigger_tags.append("🔴 单击触发")
        if triggers.get("left-double-click") == anim_name or (not triggers and anim_name == "right-double-click"):
            trigger_tags.append("🔵 双击触发")
        if anim_name == "idle":
            trigger_tags.append("🟢 默认待机")
        if triggers.get("left-drag") == anim_name or (not triggers and anim_name == "drag"):
            trigger_tags.append("🟡 拖拽动作")
        if anim_name in idle_variants:
            trigger_tags.append("⚪ 待机变体")
        if anim_name in menu_actions or (not menu_actions and anim_name not in {"idle", "click", "drag", "head_track"}):
            trigger_tags.append("🟣 菜单动作")

        action_items.append({
            "name": anim_name,
            "label": label,
            "folder": sub_folder_name,
            "fps": fps,
            "loop": loop,
            "frame_count": frame_count,
            "trigger_tags": trigger_tags,
            "description": anim_conf.get("description", ""),
        })

    # 2. 扫描文件夹中未在 asset.json 中声明的子目录
    for sub in sorted(folder.iterdir()):
        if sub.is_dir() and sub.name not in seen_folders and not sub.name.startswith((".", "_")):
            frames = count_folder_frames(sub)
            if frames > 0:
                name = sub.name
                action_items.append({
                    "name": name,
                    "label": guess_action_label(name),
                    "folder": name,
                    "fps": base_fps,
                    "loop": False,
                    "frame_count": frames,
                    "trigger_tags": ["🟣 候选动作"],
                    "description": "本地子目录素材",
                })

    return {
        "folder_path": str(folder),
        "folder_name": folder.name,
        "name": character_name,
        "character_id": character_id,
        "fps": base_fps,
        "preview": preview_file,
        "has_music": bool(meta.get("has_music")),
        "music_file": meta.get("music_file", ""),
        "triggers": triggers,
        "idle_variants": list(idle_variants),
        "menu_actions": list(menu_actions),
        "actions": action_items,
        "total_actions": len(action_items),
    }


def generate_character_action_doc(folder_path: Path) -> str:
    """为角色生成标准规范的《动作说明.md》"""
    info = inspect_character_folder(folder_path)
    lines = []
    lines.append(f"# 🐾 {info['name']} ({info['folder_name']}) · 角色动作说明书\n")
    lines.append("> 本文档由 WindowPet 角色工坊自动生成与同步，供民间创作者与开源社区查阅和管理角色动作。\n")

    lines.append("## 📌 基础信息\n")
    lines.append(f"- **角色名称**：{info['name']}")
    lines.append(f"- **内部标识**：`{info['character_id']}`")
    lines.append(f"- **基准帧率**：`{info['fps']} FPS`")
    if info['preview']:
        lines.append(f"- **角色预览图**：`{info['preview']}`")
    if info['has_music']:
        lines.append(f"- **专属伴奏**：`{info['music_file']}` (支持下班欢庆演奏)")
    lines.append(f"- **包含动作总数**：`{info['total_actions']}` 个动作\n")

    lines.append("## 🎭 动作清单与交互响应全览\n")
    lines.append("| 动作标识 (ID) | 中文名称 | 子目录 | 帧数 | 帧率 | 循环 | 当前触发交互 | 动作说明 |")
    lines.append("| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |")

    for a in info["actions"]:
        loop_str = "是" if a["loop"] else "否"
        triggers_str = "、".join(a["trigger_tags"]) if a["trigger_tags"] else "未绑定"
        folder_display = f"`{a['folder']}`" if a["folder"] != "." else "根目录"
        desc = a["description"] or "-"
        lines.append(
            f"| `{a['name']}` | **{a['label']}** | {folder_display} | {a['frame_count']} 帧 | {a['fps']} fps | {loop_str} | {triggers_str} | {desc} |"
        )
    lines.append("")

    lines.append("## 🌈 触发交互类型指南\n")
    lines.append("在 WindowPet 角色动作工坊中，可通过拖拽彩色阴影/光晕为动作绑定不同的触发方式：")
    lines.append("- 🔴 **单击触发 (Left Click)**：鼠标左键轻点桌宠时立即播放此动作并自动恢复待机。")
    lines.append("- 🔵 **双击触发 (Double Click)**：鼠标左键连续双击桌宠时播放此动作。")
    lines.append("- 🟢 **默认待机 (Default Idle)**：桌宠在屏幕上停留时默认循环播放的姿态。")
    lines.append("- 🟡 **拖拽动作 (Left Drag)**：按住鼠标左键提溜拖动桌宠时播放的悬空动作。")
    lines.append("- 🟣 **右键菜单点播 (Action Menu)**：收录在桌面右键「🎭 动作列表」子菜单中供用户随时点播。")
    lines.append("- ⚪ **待机随机变体 (Idle Variant)**：桌宠待机时，会随机间歇性表演此动作增加灵动感。\n")

    lines.append("## 🛠️ 民间创作者扩展与制作指南\n")
    lines.append("欢迎民间创作者为本角色制作新动作或设计新角色，只需遵循以下极简规范：\n")
    lines.append("1. **新建动作文件夹**：在角色目录下新建一个文件夹（例如 `my-dance/`）；")
    lines.append("2. **放入序列帧**：将制作好的透明背景 PNG 帧图片放入该目录（命名建议为 `01.png`, `02.png` ...，尺寸推荐 192×208，通常 6~24 帧）；")
    lines.append("3. **在软件中一键配置**：打开 WindowPet 控制台主页，**右键本角色卡片 -> 🎨 角色动作工坊**，即可在下方托盘看到新动作，拖动彩色阴影即可完成绑定并实时预览！")
    lines.append("4. **保存即更新**：点击保存后，软件会自动更新 `asset.json` 并重新生成此文档。\n")

    return "\n".join(lines)


def sync_character_folder(folder_path: Path, write_doc: bool = True) -> Dict[str, Any]:
    """
    同步角色文件夹：
    安全生成/覆盖写入《动作说明.md》，供开源创作者和用户查看。
    """
    folder = Path(folder_path).resolve()
    doc_content = generate_character_action_doc(folder)
    if write_doc:
        doc_path = folder / "动作说明.md"
        doc_path.write_text(doc_content, encoding="utf-8")

    asset_json_path = folder / "asset.json"
    if asset_json_path.exists():
        try:
            return json.loads(asset_json_path.read_text(encoding="utf-8-sig"))
        except Exception:
            try:
                return json.loads(asset_json_path.read_text(encoding="gbk"))
            except Exception:
                return {}
    return {}


def batch_sync_all_characters(assets_root: Path) -> int:
    """批量为 assets 下所有角色生成《动作说明.md》，不破坏原始 asset.json 结构"""
    root = Path(assets_root).resolve()
    count = 0
    for sub in sorted(root.iterdir()):
        if sub.is_dir() and (sub / "asset.json").exists():
            try:
                sync_character_folder(sub, write_doc=True)
                count += 1
            except Exception as e:
                print(f"Failed to generate doc for {sub.name}: {e}")
    return count
