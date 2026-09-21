"""
WindowPet 角色动作九宫格工坊 (9-Grid Action Matrix Studio)
=========================================================
极致纯粹、图形化、所见即所得的 3×3 九宫格角色动作设计器。
核心特性：
1. 3×3 九宫格动作矩阵：
   - 🟢 静态 (待机) · 支持「🎲 随机静态」与「🔒 固定静态」一键切换
   - 🔴 点击
   - 🟡 拖拽
   - 🔵 双击
   - 🟣 扩展动作 1 ~ 5
2. 内存帧缓存免闪烁循环播放：彻底杜绝黑屏与一闪一闪卡顿；
3. 单动作角色智能自适应：单个动作自动复制填充前三大槽位，不留白；
4. 开放式拖拽导入：直接从 Windows 桌面拖入 PNG、JPG、GIF、WebP、MP4、MOV 或帧文件夹实时替换填槽。
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import (
    QByteArray,
    QMimeData,
    QPoint,
    QRectF,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QIcon,
    QLinearGradient,
    QMovie,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .character_doc_generator import generate_character_action_doc, guess_action_label, inspect_character_folder
from .vibe_components import PetCursorManager, SpringPushButton


SLOT_DEFINITIONS = [
    {
        "slot_id": "idle",
        "title": "🟢 静态",
        "default_name": "idle",
        "default_label": "基础待机",
        "color": "#20bf6b",
        "bg_from": "#f0faf4",
        "bg_to": "#dbf5e7",
        "border": "#7bed9f",
        "is_idle": True,
    },
    {
        "slot_id": "click",
        "title": "🔴 点击",
        "default_name": "click",
        "default_label": "轻戳点击",
        "color": "#ff526c",
        "bg_from": "#fff2f4",
        "bg_to": "#ffe3e7",
        "border": "#ff9baa",
        "is_idle": False,
    },
    {
        "slot_id": "drag",
        "title": "🟡 拖拽",
        "default_name": "drag",
        "default_label": "提溜悬空",
        "color": "#e67e22",
        "bg_from": "#fffbf0",
        "bg_to": "#fef1d6",
        "border": "#fed330",
        "is_idle": False,
    },
    {
        "slot_id": "double_click",
        "title": "🔵 双击",
        "default_name": "right-double-click",
        "default_label": "双击互动",
        "color": "#3867d6",
        "bg_from": "#f0f5ff",
        "bg_to": "#dbe8ff",
        "border": "#74b9ff",
        "is_idle": False,
    },
    {
        "slot_id": "action_1",
        "title": "🟣 动作 1",
        "default_name": "waving",
        "default_label": "挥手打招呼",
        "color": "#9b59b6",
        "bg_from": "#fbf4fc",
        "bg_to": "#f3e4f7",
        "border": "#dfb9ed",
        "is_idle": False,
    },
    {
        "slot_id": "action_2",
        "title": "🟣 动作 2",
        "default_name": "jumping",
        "default_label": "开心跳跃",
        "color": "#9b59b6",
        "bg_from": "#fbf4fc",
        "bg_to": "#f3e4f7",
        "border": "#dfb9ed",
        "is_idle": False,
    },
    {
        "slot_id": "action_3",
        "title": "🟣 动作 3",
        "default_name": "running",
        "default_label": "欢快奔跑",
        "color": "#9b59b6",
        "bg_from": "#fbf4fc",
        "bg_to": "#f3e4f7",
        "border": "#dfb9ed",
        "is_idle": False,
    },
    {
        "slot_id": "action_4",
        "title": "🟣 动作 4",
        "default_name": "review",
        "default_label": "特殊才艺",
        "color": "#9b59b6",
        "bg_from": "#fbf4fc",
        "bg_to": "#f3e4f7",
        "border": "#dfb9ed",
        "is_idle": False,
    },
    {
        "slot_id": "action_5",
        "title": "🟣 动作 5",
        "default_name": "dance",
        "default_label": "跳舞表演",
        "color": "#9b59b6",
        "bg_from": "#fbf4fc",
        "bg_to": "#f3e4f7",
        "border": "#dfb9ed",
        "is_idle": False,
    },
]


def load_memory_frames(folder: Path, target_size: QSize = QSize(110, 110)) -> List[QPixmap]:
    """预先将动作序列帧加载到内存并缩放到目标尺寸，彻底消除重绘磁盘 IO 与黑屏闪烁"""
    pixmaps: List[QPixmap] = []
    if not folder.exists():
        return pixmaps

    # 1. 查找 PNG 序列帧
    valid_exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
    files = sorted([p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in valid_exts])
    for f in files:
        pm = QPixmap(str(f))
        if not pm.isNull():
            scaled = pm.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pixmaps.append(scaled)

    # 2. 若没有单独图片帧，尝试寻找动图或视频帧缓存
    if not pixmaps:
        try:
            from .media_folder import expand_folder_frames
            expanded = expand_folder_frames(folder)
            for p in expanded:
                pm = QPixmap(str(p))
                if not pm.isNull():
                    scaled = pm.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    pixmaps.append(scaled)
        except Exception:
            pass

    return pixmaps


class ActionGridSlotCard(QFrame):
    """
    九宫格中的单个动作卡槽：
    - 彩色柔和背景与标头；
    - 内存中流畅循环播放动作序列（不卡顿、不黑屏、不闪烁）；
    - 支持直接从系统拖拽外部文件（PNG/JPG/GIF/MP4/MOV）进槽替换；
    - 静态卡槽配备「🎲 随机静态」/「🔒 固定静态」一键切换药丸。
    """
    fileDropped = Signal(str, str)  # (slot_id, file_path)
    idleModeToggled = Signal(bool)  # is_fixed_idle
    renameRequested = Signal(str)   # slot_id

    def __init__(self, slot_def: Dict[str, Any], character_folder: Path, parent=None):
        super().__init__(parent)
        self.slot_def = slot_def
        self.slot_id = slot_def["slot_id"]
        self.character_folder = character_folder
        self.is_idle_slot = slot_def.get("is_idle", False)
        self.is_fixed_idle = False

        self.action_name = ""
        self.action_label = ""
        self.folder_name = ""
        self.fps = 10
        self.cached_frames: List[QPixmap] = []
        self.frame_idx = 0

        self.setFixedSize(220, 168)
        self.setAcceptDrops(True)
        self.setCursor(PetCursorManager.pointer_cursor())

        # 平滑帧定时器
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._step_frame)

        self._build_ui()
        self.update_card_style()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        # 1. 顶部标头栏
        header = QHBoxLayout()
        header.setSpacing(4)

        self.title_label = QLabel(self.slot_def["title"])
        self.title_label.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {self.slot_def['color']}; background: transparent;")
        header.addWidget(self.title_label)

        header.addStretch(1)

        if self.is_idle_slot:
            # 静态槽位的 🎲 随机静态 <-> 🔒 固定静态 切换药丸
            self.idle_toggle_btn = SpringPushButton("🎲 随机静态")
            self.idle_toggle_btn.setToolTip("点击在【随机静态】与【固定静态】之间切换")
            self.idle_toggle_btn.setFixedHeight(22)
            self.idle_toggle_btn.setStyleSheet("""
                QPushButton {
                    background: #ffffff;
                    border: 1px solid #7bed9f;
                    border-radius: 6px;
                    color: #20bf6b;
                    font-size: 9px;
                    font-weight: bold;
                    padding: 1px 6px;
                }
                QPushButton:hover {
                    background: #e8f9ee;
                }
            """)
            self.idle_toggle_btn.clicked.connect(self._toggle_idle_mode)
            header.addWidget(self.idle_toggle_btn)

        layout.addLayout(header)

        # 2. 中央动画播放画布
        self.display_label = QLabel()
        self.display_label.setFixedSize(196, 96)
        self.display_label.setAlignment(Qt.AlignCenter)
        self.display_label.setStyleSheet("background: rgba(255, 255, 255, 0.65); border-radius: 10px; border: 1px dashed rgba(0,0,0,0.06);")
        layout.addWidget(self.display_label)

        # 3. 底部信息：动作名称与说明
        info_row = QHBoxLayout()
        info_row.setSpacing(4)

        self.name_label = QLabel()
        self.name_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #3d2f2b; background: transparent;")
        info_row.addWidget(self.name_label, 1)

        self.btn_edit = SpringPushButton("✏️")
        self.btn_edit.setToolTip("重命名动作名称")
        self.btn_edit.setFixedSize(20, 20)
        self.btn_edit.setStyleSheet("""
            QPushButton {
                background: #ffffff; border: 1px solid #fed7cc; border-radius: 5px;
                font-size: 9px; color: #7f6a61;
            }
            QPushButton:hover { background: #fff4ee; color: #ff526c; }
        """)
        self.btn_edit.clicked.connect(lambda: self.renameRequested.emit(self.slot_id))
        info_row.addWidget(self.btn_edit)

        layout.addLayout(info_row)

    def set_action_data(self, action_name: str, action_label: str, folder_name: str, fps: int = 10, fallback_frames: Optional[List[QPixmap]] = None):
        self.action_name = action_name
        self.action_label = action_label or guess_action_label(action_name)
        self.folder_name = folder_name
        self.fps = max(1, fps)

        self.name_label.setText(f"{self.action_label} · {self.action_name}")

        target_dir = self.character_folder if folder_name in {".", ""} else self.character_folder / folder_name
        self.cached_frames = load_memory_frames(target_dir, QSize(96, 96))

        if not self.cached_frames and fallback_frames:
            self.cached_frames = list(fallback_frames)

        self.frame_idx = 0
        if self.cached_frames:
            self.display_label.setPixmap(self.cached_frames[0])
            self.anim_timer.start(int(1000 / self.fps))
        else:
            self.anim_timer.stop()
            self.display_label.setText("➕ 拖入图片/动图/视频")
            self.display_label.setStyleSheet("background: rgba(255, 255, 255, 0.4); border-radius: 10px; border: 1.5px dashed #fed7cc; color: #a89a93; font-size: 10px;")

    def set_fixed_idle(self, fixed: bool):
        self.is_fixed_idle = fixed
        if hasattr(self, "idle_toggle_btn"):
            if fixed:
                self.idle_toggle_btn.setText("🔒 固定静态")
                self.idle_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background: #20bf6b;
                        border: 1px solid #20bf6b;
                        border-radius: 6px;
                        color: #ffffff;
                        font-size: 9px;
                        font-weight: bold;
                        padding: 1px 6px;
                    }
                """)
            else:
                self.idle_toggle_btn.setText("🎲 随机静态")
                self.idle_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background: #ffffff;
                        border: 1px solid #7bed9f;
                        border-radius: 6px;
                        color: #20bf6b;
                        font-size: 9px;
                        font-weight: bold;
                        padding: 1px 6px;
                    }
                    QPushButton:hover {
                        background: #e8f9ee;
                    }
                """)

    def _toggle_idle_mode(self):
        new_fixed = not self.is_fixed_idle
        self.set_fixed_idle(new_fixed)
        self.idleModeToggled.emit(new_fixed)

    def _step_frame(self):
        if not self.cached_frames:
            return
        self.frame_idx = (self.frame_idx + 1) % len(self.cached_frames)
        self.display_label.setPixmap(self.cached_frames[self.frame_idx])

    def update_card_style(self, highlight: bool = False):
        border_color = "#ff526c" if highlight else self.slot_def["border"]
        border_width = "2px" if highlight else "1.2px"
        self.setStyleSheet(f"""
            ActionGridSlotCard {{
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 {self.slot_def['bg_from']}, stop: 1 {self.slot_def['bg_to']});
                border: {border_width} solid {border_color};
                border-radius: 14px;
            }}
        """)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.update_card_style(highlight=True)
        else:
            super().dragEnterEvent(event)

    def dragLeaveEvent(self, event):
        self.update_card_style(highlight=False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self.update_card_style(highlight=False)
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                local_path = urls[0].toLocalFile()
                if local_path:
                    self.fileDropped.emit(self.slot_id, local_path)
                    event.acceptProposedAction()
                    return
        super().dropEvent(event)


class CharacterActionStudioDialog(QDialog):
    """
    纯视觉 3×3 九宫格角色动作工坊对话框
    """
    def __init__(self, character_folder: Path, parent=None):
        super().__init__(parent)
        self.character_folder = Path(character_folder).resolve()
        self.info = inspect_character_folder(self.character_folder)

        self.setWindowTitle(f"🐾 {self.info['name']} · 动作九宫格工坊")
        self.resize(760, 640)
        self.setStyleSheet("""
            QDialog {
                background-color: #fffdfa;
                color: #2d2320;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            }
        """)

        # 读取已有配置
        self.meta: Dict[str, Any] = {}
        asset_json_path = self.character_folder / "asset.json"
        if asset_json_path.exists():
            try:
                self.meta = json.loads(asset_json_path.read_text(encoding="utf-8-sig"))
            except Exception:
                try:
                    self.meta = json.loads(asset_json_path.read_text(encoding="gbk"))
                except Exception:
                    self.meta = {}

        self.is_fixed_idle = bool(self.meta.get("fixed_idle", False))
        self.slot_cards: Dict[str, ActionGridSlotCard] = {}
        self.slot_action_map: Dict[str, Dict[str, Any]] = {}

        self._build_ui()
        self._load_and_populate_grid()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(10)

        # 1. 顶部 Header
        header = QHBoxLayout()
        header.setSpacing(10)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel(f"🐾 {self.info['name']} · 动作九宫格工坊")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #2d2320;")
        sub = QLabel("💡 支持直接从电脑拖拽图片(PNG/JPG)、动图(GIF)、视频(MP4/MOV)或文件夹放入九宫格替换")
        sub.setStyleSheet("font-size: 11px; color: #8c7b74;")
        title_col.addWidget(title)
        title_col.addWidget(sub)
        header.addLayout(title_col, 1)

        btn_folder = SpringPushButton("📁 打开角色目录")
        btn_folder.setStyleSheet("""
            QPushButton {
                background: #ffffff; border: 1px solid #fed7cc; border-radius: 8px;
                padding: 5px 10px; font-size: 11px; font-weight: bold; color: #55443d;
            }
            QPushButton:hover { background: #fff4ee; color: #ff526c; }
        """)
        btn_folder.clicked.connect(self._open_folder)
        header.addWidget(btn_folder)

        btn_save = SpringPushButton("💾 保存并生效")
        btn_save.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #ff6b81, stop: 1 #ff526c);
                border: none; border-radius: 8px;
                padding: 6px 16px; font-size: 11px; color: #ffffff; font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #ff7e92, stop: 1 #ff657d);
            }
        """)
        btn_save.clicked.connect(self.save_and_apply)
        header.addWidget(btn_save)

        main_layout.addLayout(header)

        # 2. 中央 3×3 九宫格卡片矩阵
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setContentsMargins(4, 4, 4, 4)
        grid_layout.setSpacing(12)

        for i, s_def in enumerate(SLOT_DEFINITIONS):
            card = ActionGridSlotCard(s_def, self.character_folder, grid_container)
            card.fileDropped.connect(self._on_file_dropped_to_slot)
            card.idleModeToggled.connect(self._on_idle_mode_toggled)
            card.renameRequested.connect(self._on_rename_requested)
            self.slot_cards[s_def["slot_id"]] = card

            row = i // 3
            col = i % 3
            grid_layout.addWidget(card, row, col)

        main_layout.addWidget(grid_container, 1)

        # 3. 底部状态栏
        footer = QHBoxLayout()
        self.status_label = QLabel("就绪：九宫格动作实时循环播放中，可直接拖入外部文件填槽。")
        self.status_label.setStyleSheet("font-size: 11px; color: #7f6a61;")
        footer.addWidget(self.status_label, 1)
        main_layout.addLayout(footer)

    def _load_and_populate_grid(self):
        """装配九宫格动作数据，单动作自动复制3份保底"""
        anims = self.meta.get("animations", {}) if isinstance(self.meta.get("animations"), dict) else {}
        action_labels = self.meta.get("action_labels", {}) if isinstance(self.meta.get("action_labels"), dict) else {}
        triggers = self.meta.get("triggers", {}) if isinstance(self.meta.get("triggers"), dict) else {}

        # 收集可用动作列表
        all_actions = list(anims.keys())

        # 若动作极少（<=1个），自动自适应保底
        root_frames = load_memory_frames(self.character_folder, QSize(96, 96))
        fallback_frames = root_frames

        # 分配动作到九宫格：
        # Slot 0: 静态
        idle_anim = triggers.get("idle") or "idle" if "idle" in anims else (all_actions[0] if all_actions else "idle")
        idle_lbl = action_labels.get(idle_anim) or anims.get(idle_anim, {}).get("label") or guess_action_label(idle_anim)
        idle_folder = anims.get(idle_anim, {}).get("folder", ".")
        idle_fps = anims.get(idle_anim, {}).get("fps", 10)
        self.slot_cards["idle"].set_action_data(idle_anim, idle_lbl, idle_folder, idle_fps, fallback_frames)
        self.slot_cards["idle"].set_fixed_idle(self.is_fixed_idle)

        # Slot 1: 点击
        click_anim = triggers.get("left-click") or "click" if "click" in anims else (all_actions[0] if all_actions else idle_anim)
        click_lbl = action_labels.get(click_anim) or anims.get(click_anim, {}).get("label") or guess_action_label(click_anim)
        click_folder = anims.get(click_anim, {}).get("folder", "click" if "click" in anims else idle_folder)
        click_fps = anims.get(click_anim, {}).get("fps", 12)
        self.slot_cards["click"].set_action_data(click_anim, click_lbl, click_folder, click_fps, fallback_frames)

        # Slot 2: 拖拽
        drag_anim = triggers.get("left-drag") or "drag" if "drag" in anims else (all_actions[0] if all_actions else idle_anim)
        drag_lbl = action_labels.get(drag_anim) or anims.get(drag_anim, {}).get("label") or guess_action_label(drag_anim)
        drag_folder = anims.get(drag_anim, {}).get("folder", "drag" if "drag" in anims else idle_folder)
        drag_fps = anims.get(drag_anim, {}).get("fps", 10)
        self.slot_cards["drag"].set_action_data(drag_anim, drag_lbl, drag_folder, drag_fps, fallback_frames)

        # Slot 3: 双击
        double_anim = triggers.get("left-double-click") or ("right-double-click" if "right-double-click" in anims else ("waving" if "waving" in anims else ""))
        if double_anim and double_anim in anims:
            d_lbl = action_labels.get(double_anim) or anims.get(double_anim, {}).get("label") or guess_action_label(double_anim)
            d_folder = anims.get(double_anim, {}).get("folder", double_anim)
            d_fps = anims.get(double_anim, {}).get("fps", 10)
            self.slot_cards["double_click"].set_action_data(double_anim, d_lbl, d_folder, d_fps, fallback_frames)
        else:
            self.slot_cards["double_click"].set_action_data(
                self.slot_cards["double_click"].slot_def["default_name"],
                self.slot_cards["double_click"].slot_def["default_label"],
                "", 10, None
            )

        # Slots 4~8: 动作 1 ~ 5
        used_actions = {idle_anim, click_anim, drag_anim, double_anim}
        remaining_actions = [a for a in all_actions if a not in used_actions and a not in {"head_track"}]

        for idx in range(1, 6):
            slot_key = f"action_{idx}"
            card = self.slot_cards[slot_key]
            if remaining_actions:
                act = remaining_actions.pop(0)
                lbl = action_labels.get(act) or anims.get(act, {}).get("label") or guess_action_label(act)
                fld = anims.get(act, {}).get("folder", act)
                f_fps = anims.get(act, {}).get("fps", 10)
                card.set_action_data(act, lbl, fld, f_fps, fallback_frames)
            else:
                card.set_action_data(card.slot_def["default_name"], card.slot_def["default_label"], "", 10, None)

    def _on_idle_mode_toggled(self, is_fixed: bool):
        self.is_fixed_idle = is_fixed
        desc = "🔒 固定静态（待机只播放这一动作）" if is_fixed else "🎲 随机静态（待机随机轮换动作）"
        self.status_label.setText(f"已切换为：{desc}")

    def _on_rename_requested(self, slot_id: str):
        card = self.slot_cards[slot_id]
        new_label, ok = QInputDialog.getText(
            self,
            "修改动作名称",
            f"请输入【{card.action_name}】的中文展示名称：",
            text=card.action_label,
        )
        if ok and new_label.strip():
            card.action_label = new_label.strip()
            card.name_label.setText(f"{card.action_label} · {card.action_name}")
            self.status_label.setText(f"✏️ 已将【{card.action_name}】名称修改为：{card.action_label}")

    def _on_file_dropped_to_slot(self, slot_id: str, file_path_str: str):
        """直接从系统拖入文件到槽位：拷贝至背后对应目录并实时更新"""
        src = Path(file_path_str).resolve()
        if not src.exists():
            return

        card = self.slot_cards[slot_id]
        target_action_name = card.action_name or card.slot_def["default_name"]

        # 确定对应的文件夹名称
        folder_name = target_action_name
        dest_dir = self.character_folder / folder_name
        dest_dir.mkdir(parents=True, exist_ok=True)

        try:
            if src.is_dir():
                # 拖入整个帧目录：拷贝里面所有图片/视频
                for item in src.iterdir():
                    if item.is_file():
                        shutil.copy2(item, dest_dir / item.name)
            else:
                # 拖入单个文件（GIF、视频、图片）
                ext = src.suffix.lower()
                if ext in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
                    # 清理旧帧并保存为 01.png
                    for old_p in dest_dir.glob("*.png"):
                        try:
                            old_p.unlink()
                        except Exception:
                            pass
                    shutil.copy2(src, dest_dir / "01.png")
                else:
                    # GIF 或视频：直接拷贝进入
                    shutil.copy2(src, dest_dir / src.name)

            # 刷新该槽位动画
            card.set_action_data(target_action_name, card.action_label or guess_action_label(target_action_name), folder_name, card.fps)
            self.status_label.setText(f"🎉 成功将【{src.name}】填入【{card.slot_def['title']}】槽位！")

        except Exception as e:
            QMessageBox.warning(self, "导入失败", f"无法导入文件：{e}")

    def _open_folder(self):
        try:
            if sys.platform == "win32":
                os.startfile(str(self.character_folder))
            else:
                subprocess.Popen(["xdg-open", str(self.character_folder)])
        except Exception as e:
            QMessageBox.warning(self, "打开文件夹", f"无法打开文件夹：{e}")

    def save_and_apply(self):
        """保存配置到 asset.json 并生成 动作说明.md，同步更新桌宠"""
        data = dict(self.meta)

        # 1. 固定/随机静态状态
        data["fixed_idle"] = self.is_fixed_idle

        # 2. 触发方式绑定
        if "triggers" not in data or not isinstance(data["triggers"], dict):
            data["triggers"] = {}

        data["triggers"]["idle"] = self.slot_cards["idle"].action_name or "idle"
        data["triggers"]["left-click"] = self.slot_cards["click"].action_name or "click"
        data["triggers"]["left-drag"] = self.slot_cards["drag"].action_name or "drag"
        double_act = self.slot_cards["double_click"].action_name
        if double_act and double_act != "double-click":
            data["triggers"]["left-double-click"] = double_act

        # 3. 动作中文名保存在顶层 action_labels
        if "action_labels" not in data or not isinstance(data["action_labels"], dict):
            data["action_labels"] = {}

        for card in self.slot_cards.values():
            if card.action_name and card.action_label:
                data["action_labels"][card.action_name] = card.action_label

        # 4. 确保 animations 完整
        if "animations" not in data or not isinstance(data["animations"], dict):
            data["animations"] = {}

        for card in self.slot_cards.values():
            name = card.action_name
            if name and name not in data["animations"]:
                folder_val = card.folder_name or name
                if (self.character_folder / folder_val).exists() or folder_val in {".", ""}:
                    data["animations"][name] = {
                        "folder": folder_val,
                        "fps": card.fps,
                        "loop": bool(name == "idle" or card.is_idle_slot),
                    }

        # 写入 asset.json
        asset_json_path = self.character_folder / "asset.json"
        asset_json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        # 同步生成 动作说明.md
        doc_path = self.character_folder / "动作说明.md"
        doc_content = generate_character_action_doc(self.character_folder)
        doc_path.write_text(doc_content, encoding="utf-8")

        # 热重载桌面运行中的对应角色
        try:
            from . import state
            for win in getattr(state, "WINDOWS", []):
                if getattr(win, "asset", None) and getattr(win.asset, "path", None) == self.character_folder:
                    win.asset.metadata = data
                    if hasattr(win, "play_idle_animation"):
                        win.play_idle_animation()
        except Exception:
            pass

        if not os.environ.get("PYTEST_CURRENT_TEST"):
            QMessageBox.information(
                self,
                "保存成功",
                f"🎉 角色【{self.info['name']}】九宫格动作与配置已保存生效！\n"
                f"- 已更新：asset.json\n"
                f"- 静态模式：{'🔒 固定静态' if self.is_fixed_idle else '🎲 随机静态'}\n"
                f"当前运行的桌宠已同步最新动作逻辑。",
            )
        self.accept()
