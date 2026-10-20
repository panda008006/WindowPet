"""
WindowPet 角色核心动作直观配置器 (Character Action Config Dialog)
================================================================
直观、极简、面向核心互动体验的角色动作分配器：
1. 上层展架：展示该角色拥有的全部动作序列（带流畅动态帧预览与中英文释义，支持鼠标拖拽，支持快捷点击一键配置）；
2. 下层三大核心模式槽位：
   - 👆 单击触发 (Click)：拖入单个动作，点击桌宠时立即触发；
   - ✋ 拖拽触发 (Drag)：拖入单个动作，拖动桌宠时持续触发；
   - 🎲 静态随机动作池 (Idle Pool)：可拖入多个动作，静止挂机时随机轮播；
3. 智能默认适配：导入新角色时自动推导最佳动作配置，不再点击无反应；
4. 实时热生效：保存即刻写入 asset.json 并同步刷新桌面端运行中的桌宠。
"""

import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from PySide6.QtCore import (
    QMimeData,
    QPoint,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QDrag,
    QIcon,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from . import state
from .character_action_studio import load_memory_frames
from .character_doc_generator import guess_action_label, inspect_character_folder
from .vibe_components import PetCursorManager, SpringPushButton


def infer_recommended_triggers(actions: List[Dict[str, Any]]) -> Dict[str, str]:
    """智能推断角色的最佳默认触发动作"""
    names = [a["name"] for a in actions]
    rec = {"left-click": "", "left-drag": ""}

    # 1. 单击推荐优先级
    click_prio = ["click", "tap", "jumping", "jump", "waving", "wave", "bounce", "review", "failed"]
    for pref in click_prio:
        for n in names:
            if pref in n.lower():
                rec["left-click"] = n
                break
        if rec["left-click"]:
            break
    if not rec["left-click"]:
        # 回退：除 idle 外的第一个动作
        non_idle = [n for n in names if n != "idle"]
        rec["left-click"] = non_idle[0] if non_idle else "idle"

    # 2. 拖拽推荐优先级
    drag_prio = ["drag", "pull", "running", "run", "running-right", "running-left", "walk", "moving"]
    for pref in drag_prio:
        for n in names:
            if pref in n.lower():
                rec["left-drag"] = n
                break
        if rec["left-drag"]:
            break
    if not rec["left-drag"]:
        non_idle = [n for n in names if n != "idle" and n != rec["left-click"]]
        rec["left-drag"] = non_idle[0] if non_idle else (names[0] if names else "idle")

    return rec


class ActionPreviewWidget(QLabel):
    """内存帧免闪烁循环播放微型预览部件"""
    def __init__(self, size: QSize = QSize(96, 96), parent=None):
        super().__init__(parent)
        self.setFixedSize(size)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            background: #f7f9fc;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
        """)
        self.frames: List[QPixmap] = []
        self.frame_idx = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._next_frame)

    def set_frames(self, frames: List[QPixmap], fps: int = 10):
        self.frames = frames
        self.frame_idx = 0
        self.timer.stop()
        if self.frames:
            self.setPixmap(self.frames[0])
            interval = max(30, int(1000 / max(1, fps)))
            self.timer.start(interval)
        else:
            self.clear()
            self.setText("暂无预览")

    def _next_frame(self):
        if not self.frames:
            return
        self.frame_idx = (self.frame_idx + 1) % len(self.frames)
        self.setPixmap(self.frames[self.frame_idx])


class ActionSourceCard(QFrame):
    """
    顶部展架中的单动作卡片：
    - 展示动作动画预览、中文与英文名；
    - 支持鼠标拖拽（Drag）；
    - 提供 3 个快捷分配微按钮（👆单击、✋拖拽、🎲随机）。
    """
    assignClicked = Signal(str, str)  # (action_name, target_slot_type: 'click'|'drag'|'idle')

    def __init__(self, action_data: Dict[str, Any], character_folder: Path, parent=None):
        super().__init__(parent)
        self.action_data = action_data
        self.action_name = action_data["name"]
        self.action_label = action_data.get("label") or guess_action_label(self.action_name)
        self.character_folder = character_folder
        self.drag_start_pos: Optional[QPoint] = None

        self.setFixedSize(146, 196)
        self.setCursor(PetCursorManager.pointer_cursor())
        self.setObjectName("ActionSourceCard")
        self.setStyleSheet("""
            QFrame#ActionSourceCard {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
            QFrame#ActionSourceCard:hover {
                border: 1.5px solid #ff7a92;
                background: #fffbfa;
            }
        """)

        self._build_ui()
        self._load_animation()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # 1. 动图预览
        self.preview = ActionPreviewWidget(QSize(96, 96), self)
        layout.addWidget(self.preview, 0, Qt.AlignHCenter)

        # 2. 动作标签与英文名
        self.label_widget = QLabel(self.action_label)
        self.label_widget.setAlignment(Qt.AlignCenter)
        self.label_widget.setStyleSheet("font-size: 12px; font-weight: bold; color: #2d3748;")
        layout.addWidget(self.label_widget)

        self.sub_name_widget = QLabel(self.action_name)
        self.sub_name_widget.setAlignment(Qt.AlignCenter)
        self.sub_name_widget.setStyleSheet("font-size: 10px; color: #a0aec0;")
        layout.addWidget(self.sub_name_widget)

        # 3. 快捷微按钮条（免拖拽直达）
        btn_row = QHBoxLayout()
        btn_row.setSpacing(3)
        btn_row.setContentsMargins(0, 2, 0, 0)

        self.btn_click = QPushButton("👆单击")
        self.btn_click.setToolTip("设为【单击触发】动作")
        self.btn_click.setFixedHeight(20)
        self.btn_click.setStyleSheet("""
            QPushButton {
                background: #fff1f2;
                color: #e11d48;
                border: 1px solid #fecdd3;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 500;
                padding: 0 4px;
            }
            QPushButton:hover {
                background: #ffe4e6;
                border-color: #fb7185;
            }
        """)
        self.btn_click.clicked.connect(lambda: self.assignClicked.emit(self.action_name, "click"))

        self.btn_drag = QPushButton("✋拖拽")
        self.btn_drag.setToolTip("设为【拖拽触发】动作")
        self.btn_drag.setFixedHeight(20)
        self.btn_drag.setStyleSheet("""
            QPushButton {
                background: #fffbeb;
                color: #d97706;
                border: 1px solid #fde68a;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 500;
                padding: 0 4px;
            }
            QPushButton:hover {
                background: #fef3c7;
                border-color: #f59e0b;
            }
        """)
        self.btn_drag.clicked.connect(lambda: self.assignClicked.emit(self.action_name, "drag"))

        self.btn_idle = QPushButton("🎲随机")
        self.btn_idle.setToolTip("加入【静态随机动作池】")
        self.btn_idle.setFixedHeight(20)
        self.btn_idle.setStyleSheet("""
            QPushButton {
                background: #f0fdf4;
                color: #16a34a;
                border: 1px solid #bbf7d0;
                border-radius: 4px;
                font-size: 10px;
                font-weight: 500;
                padding: 0 4px;
            }
            QPushButton:hover {
                background: #dcfce7;
                border-color: #4ade80;
            }
        """)
        self.btn_idle.clicked.connect(lambda: self.assignClicked.emit(self.action_name, "idle"))

        btn_row.addWidget(self.btn_click)
        btn_row.addWidget(self.btn_drag)
        btn_row.addWidget(self.btn_idle)
        layout.addLayout(btn_row)

    def _load_animation(self):
        folder_name = self.action_data.get("folder", self.action_name)
        target_dir = self.character_folder if folder_name in {".", ""} else self.character_folder / folder_name
        frames = load_memory_frames(target_dir, QSize(96, 96))
        fps = int(self.action_data.get("fps") or 10)
        self.preview.set_frames(frames, fps)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton):
            return
        if self.drag_start_pos is None:
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(f"action:{self.action_name}")
        drag.setMimeData(mime_data)

        # 制作半透明缩略图
        if self.preview.frames:
            pixmap = self.preview.frames[0]
            scaled = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            drag.setPixmap(scaled)
            drag.setHotSpot(QPoint(32, 32))

        drag.exec(Qt.CopyAction)


class SingleActionSlotCard(QFrame):
    """
    单选触发动作卡槽（用于【👆 单击触发】或【✋ 拖拽触发】）：
    - 接收上方卡片拖入（Drop）；
    - 支持点击清除与恢复推荐；
    - 动态展示当前绑定动作的动画与名称。
    """
    actionChanged = Signal(str, str)  # (slot_type, action_name)

    def __init__(self, slot_type: str, title: str, subtitle: str, color_theme: str, parent=None):
        super().__init__(parent)
        self.slot_type = slot_type  # 'click' or 'drag'
        self.title_text = title
        self.subtitle_text = subtitle
        self.color_theme = color_theme  # e.g. '#e11d48' or '#d97706'
        self.current_action = ""
        self.current_label = ""
        self.character_folder: Optional[Path] = None
        self.actions_dict: Dict[str, Dict[str, Any]] = {}

        self.setAcceptDrops(True)
        self.setMinimumHeight(150)
        self.setObjectName("SingleActionSlotCard")
        self.update_style(is_hover=False)

        self._build_ui()

    def update_style(self, is_hover: bool = False):
        border_color = self.color_theme if is_hover else "#cbd5e1"
        bg_color = "#fff7f8" if self.slot_type == "click" and is_hover else ("#fffdf5" if is_hover else "#ffffff")
        self.setStyleSheet(f"""
            QFrame#SingleActionSlotCard {{
                background: {bg_color};
                border: 2px dashed {border_color};
                border-radius: 12px;
            }}
        """)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(6)

        # 1. 标题行
        header = QHBoxLayout()
        title_lbl = QLabel(self.title_text)
        title_lbl.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {self.color_theme};")
        header.addWidget(title_lbl)

        header.addStretch()

        self.clear_btn = QPushButton("重置")
        self.clear_btn.setFixedSize(50, 22)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                color: #64748b;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                font-size: 11px;
                padding: 0;
            }
            QPushButton:hover {
                background: #e2e8f0;
                color: #334155;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_action)
        header.addWidget(self.clear_btn)
        layout.addLayout(header)

        # 2. 中间内容区（动图预览 + 动作名称）
        content_row = QHBoxLayout()
        content_row.setSpacing(10)

        self.preview = ActionPreviewWidget(QSize(76, 76), self)
        content_row.addWidget(self.preview)

        name_layout = QVBoxLayout()
        name_layout.setSpacing(2)
        name_layout.addStretch()

        self.action_title_label = QLabel("未配置动作")
        self.action_title_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #1e293b;")
        name_layout.addWidget(self.action_title_label)

        self.action_code_label = QLabel("拖入上方动作，或点击【👆单击】设置")
        self.action_code_label.setStyleSheet("font-size: 11px; color: #64748b;")
        self.action_code_label.setWordWrap(True)
        name_layout.addWidget(self.action_code_label)

        name_layout.addStretch()
        content_row.addLayout(name_layout, 1)

        layout.addLayout(content_row)

        # 3. 底部说明
        tip_lbl = QLabel(self.subtitle_text)
        tip_lbl.setStyleSheet("font-size: 10px; color: #94a3b8;")
        layout.addWidget(tip_lbl)

    def set_character_context(self, folder: Path, actions_dict: Dict[str, Dict[str, Any]]):
        self.character_folder = folder
        self.actions_dict = actions_dict

    def set_action(self, action_name: str):
        self.current_action = action_name
        if not action_name:
            self.action_title_label.setText("未配置动作")
            self.action_code_label.setText("拖入上方动作卡片，或点击快捷分配按钮")
            self.preview.set_frames([])
            self.actionChanged.emit(self.slot_type, "")
            return

        act_data = self.actions_dict.get(action_name, {})
        label = act_data.get("label") or guess_action_label(action_name)
        self.current_label = label
        self.action_title_label.setText(f"{label} · {action_name}")
        self.action_code_label.setText(f"已就绪：{self.title_text.split()[0]}触发此动作")

        if self.character_folder:
            fld = act_data.get("folder", action_name)
            sub_dir = self.character_folder if fld in {".", ""} else self.character_folder / fld
            frames = load_memory_frames(sub_dir, QSize(76, 76))
            fps = int(act_data.get("fps") or 10)
            self.preview.set_frames(frames, fps)

        self.actionChanged.emit(self.slot_type, action_name)

    def clear_action(self):
        self.set_action("")

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("action:"):
            event.acceptProposedAction()
            self.update_style(is_hover=True)

    def dragLeaveEvent(self, event):
        self.update_style(is_hover=False)

    def dropEvent(self, event):
        self.update_style(is_hover=False)
        text = event.mimeData().text()
        if text.startswith("action:"):
            action_name = text[len("action:"):]
            self.set_action(action_name)
            event.acceptProposedAction()


class IdlePoolSlotCard(QFrame):
    """
    静态随机待机动作池（多选槽位）：
    - 支持多次拖入动作加入池中；
    - 展示已加入动作的小药丸胶囊，可单项 ❌ 移除；
    - 提供【一键全选导入】与【一键清空】。
    """
    poolChanged = Signal(list)  # List[str]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.character_folder: Optional[Path] = None
        self.actions_dict: Dict[str, Dict[str, Any]] = {}
        self.selected_actions: List[str] = []

        self.setAcceptDrops(True)
        self.setMinimumHeight(130)
        self.setObjectName("IdlePoolSlotCard")
        self.update_style(is_hover=False)

        self._build_ui()

    def update_style(self, is_hover: bool = False):
        border_color = "#16a34a" if is_hover else "#cbd5e1"
        bg_color = "#f0fdf4" if is_hover else "#ffffff"
        self.setStyleSheet(f"""
            QFrame#IdlePoolSlotCard {{
                background: {bg_color};
                border: 2px dashed {border_color};
                border-radius: 12px;
            }}
        """)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(8)

        # 1. 顶部操作栏
        header = QHBoxLayout()
        title_lbl = QLabel("🎲 静态随机动作池 (Idle Pool)")
        title_lbl.setStyleSheet("font-size: 13px; font-weight: bold; color: #16a34a;")
        header.addWidget(title_lbl)

        self.count_badge = QLabel("（已选 0 个）")
        self.count_badge.setStyleSheet("font-size: 11px; color: #64748b;")
        header.addWidget(self.count_badge)

        header.addStretch()

        self.btn_select_all = QPushButton("✨ 一键全选导入")
        self.btn_select_all.setFixedHeight(22)
        self.btn_select_all.setStyleSheet("""
            QPushButton {
                background: #f0fdf4;
                color: #16a34a;
                border: 1px solid #86efac;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
                padding: 0 8px;
            }
            QPushButton:hover {
                background: #dcfce7;
            }
        """)
        self.btn_select_all.clicked.connect(self.select_all_actions)
        header.addWidget(self.btn_select_all)

        self.btn_clear_all = QPushButton("清空")
        self.btn_clear_all.setFixedHeight(22)
        self.btn_clear_all.setStyleSheet("""
            QPushButton {
                background: #f8fafc;
                color: #64748b;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                font-size: 11px;
                padding: 0 8px;
            }
            QPushButton:hover {
                background: #e2e8f0;
                color: #334155;
            }
        """)
        self.btn_clear_all.clicked.connect(self.clear_pool)
        header.addWidget(self.btn_clear_all)

        layout.addLayout(header)

        # 2. 标签胶囊平铺展示区
        self.scroll = QScrollArea(self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.pills_container = QWidget()
        self.pills_container.setStyleSheet("background: transparent;")
        self.pills_layout = QHBoxLayout(self.pills_container)
        self.pills_layout.setContentsMargins(0, 4, 0, 4)
        self.pills_layout.setSpacing(6)
        self.pills_layout.addStretch()

        self.scroll.setWidget(self.pills_container)
        layout.addWidget(self.scroll, 1)

        # 3. 底部提示
        tip_lbl = QLabel("挂机静止时，桌宠会每隔 6~14 秒从上面动作池中随机挑选一个表演。可将上方动作卡片拖拽入内，或点击卡片上的【🎲随机】。")
        tip_lbl.setStyleSheet("font-size: 10px; color: #94a3b8;")
        layout.addWidget(tip_lbl)

    def set_character_context(self, folder: Path, actions_dict: Dict[str, Dict[str, Any]]):
        self.character_folder = folder
        self.actions_dict = actions_dict

    def add_action(self, action_name: str):
        if not action_name:
            return
        if action_name in self.selected_actions:
            return
        self.selected_actions.append(action_name)
        self._refresh_pills()
        self.poolChanged.emit(self.selected_actions)

    def remove_action(self, action_name: str):
        if action_name in self.selected_actions:
            self.selected_actions.remove(action_name)
            self._refresh_pills()
            self.poolChanged.emit(self.selected_actions)

    def set_actions(self, action_names: List[str]):
        # 去重且保持有效
        self.selected_actions = []
        for n in action_names:
            if n and n not in self.selected_actions:
                self.selected_actions.append(n)
        self._refresh_pills()
        self.poolChanged.emit(self.selected_actions)

    def select_all_actions(self):
        # 导入全部除 idle 本身外的动作（或全部动作）
        all_names = list(self.actions_dict.keys())
        # 优先过滤纯移动动作或者直接全量放入
        self.set_actions(all_names)

    def clear_pool(self):
        self.set_actions([])

    def _refresh_pills(self):
        # 清理旧子项
        while self.pills_layout.count() > 0:
            item = self.pills_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

        self.count_badge.setText(f"（已选 {len(self.selected_actions)} 个动作）")

        if not self.selected_actions:
            empty_lbl = QLabel("暂未添加随机动作（静止时将固定播放基础待机）")
            empty_lbl.setStyleSheet("font-size: 11px; color: #94a3b8; font-style: italic;")
            self.pills_layout.addWidget(empty_lbl)
            self.pills_layout.addStretch()
            return

        for name in self.selected_actions:
            act_info = self.actions_dict.get(name, {})
            label = act_info.get("label") or guess_action_label(name)

            pill = QFrame()
            pill.setStyleSheet("""
                QFrame {
                    background: #f0fdf4;
                    border: 1px solid #86efac;
                    border-radius: 12px;
                    padding: 2px 6px;
                }
            """)
            pill_layout = QHBoxLayout(pill)
            pill_layout.setContentsMargins(4, 2, 4, 2)
            pill_layout.setSpacing(4)

            text_lbl = QLabel(f"{label} ({name})")
            text_lbl.setStyleSheet("font-size: 11px; color: #166534; font-weight: 500;")
            pill_layout.addWidget(text_lbl)

            del_btn = QPushButton("×")
            del_btn.setFixedSize(16, 16)
            del_btn.setCursor(PetCursorManager.pointer_cursor())
            del_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #991b1b;
                    font-size: 13px;
                    font-weight: bold;
                    border: none;
                }
                QPushButton:hover {
                    color: #ef4444;
                }
            """)
            del_btn.clicked.connect(lambda _=False, n=name: self.remove_action(n))
            pill_layout.addWidget(del_btn)

            self.pills_layout.addWidget(pill)

        self.pills_layout.addStretch()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText() and event.mimeData().text().startswith("action:"):
            event.acceptProposedAction()
            self.update_style(is_hover=True)

    def dragLeaveEvent(self, event):
        self.update_style(is_hover=False)

    def dropEvent(self, event):
        self.update_style(is_hover=False)
        text = event.mimeData().text()
        if text.startswith("action:"):
            action_name = text[len("action:"):]
            self.add_action(action_name)
            event.acceptProposedAction()


class CharacterActionConfigDialog(QDialog):
    """
    全新设计的【角色核心动作直观配置器】
    ======================================
    - 上部：动作展架（Action Rack），横向滑轨展示所有可用动作，支持拖拽与一键快捷分配；
    - 下部：3 大核心模式槽位（👆 单击触发、✋ 拖拽触发、🎲 静态随机动作池）；
    - 底部：保存即刻热重载，桌面桌宠当场生效！
    """
    def __init__(self, character_folder: Path, parent=None):
        super().__init__(parent)
        self.character_folder = Path(character_folder).resolve()
        self.meta: Dict[str, Any] = {}
        self.actions_list: List[Dict[str, Any]] = []
        self.actions_dict: Dict[str, Dict[str, Any]] = {}

        self.setWindowTitle("⚙️ 配置该主宠动作")
        self.resize(880, 620)
        self.setMinimumSize(780, 560)
        self.setStyleSheet("""
            QDialog {
                background: #f8fafc;
                font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
            }
        """)

        self._load_character_data()
        self._build_ui()
        self._populate_current_config()

    def _load_character_data(self):
        info = inspect_character_folder(self.character_folder)
        self.actions_list = info.get("actions", [])
        self.actions_dict = {a["name"]: a for a in self.actions_list}

        asset_json_path = self.character_folder / "asset.json"
        if asset_json_path.exists():
            try:
                self.meta = json.loads(asset_json_path.read_text(encoding="utf-8-sig"))
            except Exception:
                try:
                    self.meta = json.loads(asset_json_path.read_text(encoding="gbk"))
                except Exception:
                    self.meta = {}
        else:
            self.meta = {}

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(12)

        # 1. 顶部标头行
        header_row = QHBoxLayout()
        pet_name = self.meta.get("name") or self.character_folder.name
        title = QLabel(f"🎨 {pet_name} · 动作分配中心")
        title.setStyleSheet("font-size: 17px; font-weight: bold; color: #0f172a;")
        header_row.addWidget(title)

        header_row.addStretch()

        help_tip = QLabel("💡 拖动上方动作卡片到下方槽位，或点击卡片上的【👆单击/✋拖拽/🎲随机】快捷分配")
        help_tip.setStyleSheet("font-size: 11px; color: #64748b; background: #f1f5f9; padding: 4px 10px; border-radius: 6px;")
        header_row.addWidget(help_tip)
        main_layout.addLayout(header_row)

        # 2. 上部动作展架（Action Rack）
        rack_label_row = QHBoxLayout()
        rack_title = QLabel(f"📦 角色拥有的全部动作（共 {len(self.actions_list)} 个动作）")
        rack_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #334155;")
        rack_label_row.addWidget(rack_title)
        rack_label_row.addStretch()
        main_layout.addLayout(rack_label_row)

        self.rack_scroll = QScrollArea()
        self.rack_scroll.setFixedHeight(215)
        self.rack_scroll.setWidgetResizable(True)
        self.rack_scroll.setFrameShape(QFrame.NoFrame)
        self.rack_scroll.setStyleSheet("background: transparent;")
        self.rack_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.rack_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        rack_container = QWidget()
        rack_container.setStyleSheet("background: transparent;")
        self.rack_layout = QHBoxLayout(rack_container)
        self.rack_layout.setContentsMargins(4, 4, 4, 4)
        self.rack_layout.setSpacing(10)

        for act in self.actions_list:
            card = ActionSourceCard(act, self.character_folder, self)
            card.assignClicked.connect(self._on_source_card_assign)
            self.rack_layout.addWidget(card)

        self.rack_layout.addStretch()
        self.rack_scroll.setWidget(rack_container)
        main_layout.addWidget(self.rack_scroll)

        # 3. 分割线
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #e2e8f0; background: #e2e8f0; max-height: 1px;")
        main_layout.addWidget(sep)

        # 4. 下部核心三大槽位
        slots_title = QLabel("🎯 核心触发模式配属")
        slots_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #334155;")
        main_layout.addWidget(slots_title)

        # 上两单选槽位并排
        slots_row = QHBoxLayout()
        slots_row.setSpacing(12)

        self.slot_click = SingleActionSlotCard(
            slot_type="click",
            title="👆 单击触发 (Click)",
            subtitle="鼠标左键轻点一下桌宠时，立即触发表演该动作",
            color_theme="#e11d48",
            parent=self,
        )
        self.slot_click.set_character_context(self.character_folder, self.actions_dict)

        self.slot_drag = SingleActionSlotCard(
            slot_type="drag",
            title="✋ 拖拽触发 (Drag)",
            subtitle="按住鼠标拖动桌宠跑动/悬空时，持续播放该动作",
            color_theme="#d97706",
            parent=self,
        )
        self.slot_drag.set_character_context(self.character_folder, self.actions_dict)

        slots_row.addWidget(self.slot_click)
        slots_row.addWidget(self.slot_drag)
        main_layout.addLayout(slots_row)

        # 下一宽幅多选槽位：静态随机待机动作池
        self.slot_idle_pool = IdlePoolSlotCard(parent=self)
        self.slot_idle_pool.set_character_context(self.character_folder, self.actions_dict)
        main_layout.addWidget(self.slot_idle_pool)

        # 5. 底部按钮控制栏
        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 6, 0, 0)

        self.btn_auto_adapt = QPushButton("🪄 智能推荐配属")
        self.btn_auto_adapt.setToolTip("按最优交互习惯，一键自动匹配单击跳跃、拖拽奔跑与随机待机")
        self.btn_auto_adapt.setFixedHeight(34)
        self.btn_auto_adapt.setStyleSheet("""
            QPushButton {
                background: #f1f5f9;
                color: #475569;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 500;
                padding: 0 14px;
            }
            QPushButton:hover {
                background: #e2e8f0;
                color: #1e293b;
            }
        """)
        self.btn_auto_adapt.clicked.connect(self.apply_smart_adaptation)
        bottom_bar.addWidget(self.btn_auto_adapt)

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("font-size: 12px; color: #16a34a; font-weight: 500;")
        bottom_bar.addWidget(self.status_lbl)

        bottom_bar.addStretch()

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.setFixedHeight(34)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                color: #64748b;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                font-size: 12px;
                padding: 0 16px;
            }
            QPushButton:hover {
                background: #f8fafc;
                color: #334155;
            }
        """)
        self.btn_cancel.clicked.connect(self.reject)
        bottom_bar.addWidget(self.btn_cancel)

        self.btn_save = SpringPushButton("💾 保存并立即生效")
        self.btn_save.setFixedHeight(34)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff6b81, stop:1 #ff8da1);
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff526c, stop:1 #ff7a92);
            }
        """)
        self.btn_save.clicked.connect(self.save_and_apply)
        bottom_bar.addWidget(self.btn_save)

        main_layout.addLayout(bottom_bar)

    def _populate_current_config(self):
        """加载当前角色已有的配置，若未配置则执行智能推荐"""
        triggers = self.meta.get("triggers", {}) if isinstance(self.meta.get("triggers"), dict) else {}
        idle_variants = self.meta.get("idle_variants", []) if isinstance(self.meta.get("idle_variants"), list) else []

        # 1. 单击动作
        click_act = triggers.get("left-click") or ""
        if click_act and click_act in self.actions_dict:
            self.slot_click.set_action(click_act)
        else:
            # 智能推荐
            rec = infer_recommended_triggers(self.actions_list)
            self.slot_click.set_action(rec["left-click"])

        # 2. 拖拽动作
        drag_act = triggers.get("left-drag") or ""
        if drag_act and drag_act in self.actions_dict:
            self.slot_drag.set_action(drag_act)
        else:
            rec = infer_recommended_triggers(self.actions_list)
            self.slot_drag.set_action(rec["left-drag"])

        # 3. 静态随机动作池
        if idle_variants:
            valid_variants = [v for v in idle_variants if v in self.actions_dict]
            self.slot_idle_pool.set_actions(valid_variants)
        else:
            # 默认全量导入所有动作（用户原话：“至少在静态随机触发那里，都是默认全部导入的”）
            self.slot_idle_pool.select_all_actions()

    def _on_source_card_assign(self, action_name: str, target_slot_type: str):
        if target_slot_type == "click":
            self.slot_click.set_action(action_name)
            self.status_lbl.setText(f"✅ 已将【{action_name}】设为单击动作")
        elif target_slot_type == "drag":
            self.slot_drag.set_action(action_name)
            self.status_lbl.setText(f"✅ 已将【{action_name}】设为拖拽动作")
        elif target_slot_type == "idle":
            self.slot_idle_pool.add_action(action_name)
            self.status_lbl.setText(f"✅ 已将【{action_name}】加入静态随机动作池")

    def apply_smart_adaptation(self):
        """一键智能恢复/推荐配置"""
        rec = infer_recommended_triggers(self.actions_list)
        self.slot_click.set_action(rec["left-click"])
        self.slot_drag.set_action(rec["left-drag"])
        self.slot_idle_pool.select_all_actions()
        self.status_lbl.setText("✨ 已应用智能推荐适配方案！")

    def save_and_apply(self):
        """保存至 asset.json 并实时刷新桌面当前活跃窗口"""
        data = dict(self.meta)

        if "triggers" not in data or not isinstance(data["triggers"], dict):
            data["triggers"] = {}

        click_action = self.slot_click.current_action.strip()
        drag_action = self.slot_drag.current_action.strip()
        idle_variants = list(self.slot_idle_pool.selected_actions)

        if click_action:
            data["triggers"]["left-click"] = click_action
        elif "left-click" in data["triggers"]:
            del data["triggers"]["left-click"]

        if drag_action:
            data["triggers"]["left-drag"] = drag_action
        elif "left-drag" in data["triggers"]:
            del data["triggers"]["left-drag"]

        data["idle_variants"] = idle_variants
        # 若随机池非空则激活随机待机，否则固定单动作待机
        data["fixed_idle"] = False if idle_variants else True

        # 写入 asset.json
        asset_json_path = self.character_folder / "asset.json"
        try:
            asset_json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"无法写入配置文件：{e}")
            return

        # 实时热重载桌面上正在运行的该角色窗口
        refreshed_count = self._hot_reload_active_pet_windows(data)

        self.status_lbl.setText(f"🎉 保存成功！桌面 {refreshed_count} 个桌宠已即时生效！")
        QMessageBox.information(
            self,
            "配置已生效",
            f"主宠动作配置已成功保存！\n\n"
            f"• 👆 单击触发：{click_action or '默认'}\n"
            f"• ✋ 拖拽触发：{drag_action or '默认'}\n"
            f"• 🎲 静态随机：共 {len(idle_variants)} 个轮播动作\n\n"
            f"桌面桌宠已即时热重载生效，无需重启软件。",
        )
        self.accept()

    def _hot_reload_active_pet_windows(self, new_meta: Dict[str, Any]) -> int:
        """遍历 state.ACTIVE_WINDOWS，若角色匹配则就地热刷新"""
        refreshed = 0
        active_windows = getattr(state, "ACTIVE_WINDOWS", []) or []
        for w in active_windows:
            try:
                asset = getattr(w, "asset", None)
                if asset is not None:
                    # 通过路径或 ID 匹配
                    w_path = getattr(asset, "path", None)
                    if w_path and Path(w_path).resolve() == self.character_folder:
                        asset.metadata = dict(new_meta)
                        if hasattr(w, "reload_asset_metadata"):
                            w.reload_asset_metadata()
                        else:
                            # 直接更新定时器
                            if hasattr(w, "schedule_next_idle_variant"):
                                w.schedule_next_idle_variant()
                        refreshed += 1
            except Exception:
                pass
        return refreshed
