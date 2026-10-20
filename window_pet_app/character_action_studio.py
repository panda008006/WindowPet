"""
WindowPet 角色五动作工坊 (Five Action Studio)
=============================================
上方只保留五个固定动作，下方列出角色目录中的全部素材，拖拽即可绑定。
核心特性：
1. 五个固定动作：
   - 静态图片
   - 单击
   - 拖拽
   - 思考
   - 回答
2. 内存帧缓存免闪烁循环播放：彻底杜绝黑屏与一闪一闪卡顿；
3. 下方素材架递归展示图片、GIF、视频和其他文件；
4. 摇头跟随角色自动进入独立模式，不参与五个基础动作槽位。
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from PIL import Image

from PySide6.QtCore import (
    QByteArray,
    QEvent,
    QMimeData,
    QPoint,
    QUrl,
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
    QDrag,
    QFont,
    QIcon,
    QImageReader,
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
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .character_doc_generator import generate_character_action_doc, guess_action_label, inspect_character_folder
from .vibe_components import PetCursorManager, SpringPushButton


SLOT_DEFINITIONS = [
    {
        "slot_id": "idle",
        "title": "静态",
        "default_name": "static",
        "default_label": "静态",
        "color": "#20bf6b",
        "bg_from": "#f0faf4",
        "bg_to": "#dbf5e7",
        "border": "#7bed9f",
        "is_idle": True,
    },
    {
        "slot_id": "click",
        "title": "单击",
        "default_name": "click",
        "default_label": "单击",
        "color": "#ff526c",
        "bg_from": "#fff2f4",
        "bg_to": "#ffe3e7",
        "border": "#ff9baa",
        "is_idle": False,
    },
    {
        "slot_id": "drag",
        "title": "拖拽",
        "default_name": "drag",
        "default_label": "拖拽",
        "color": "#e67e22",
        "bg_from": "#fffbf0",
        "bg_to": "#fef1d6",
        "border": "#fed330",
        "is_idle": False,
    },
    {
        "slot_id": "thinking",
        "title": "思考",
        "default_name": "thinking",
        "default_label": "思考",
        "color": "#3867d6",
        "bg_from": "#f0f5ff",
        "bg_to": "#dbe8ff",
        "border": "#74b9ff",
        "is_idle": False,
    },
    {
        "slot_id": "result",
        "title": "回答",
        "default_name": "result",
        "default_label": "回答",
        "color": "#8e44ad",
        "bg_from": "#fbf4fc",
        "bg_to": "#f3e4f7",
        "border": "#dfb9ed",
        "is_idle": False,
    },
]

# 1.0.33 以前的配置仍可能包含这些槽位。它们只作为隐藏兼容层读取，
# 不再出现在工坊界面，也不会被新的五槽位布局写入。
LEGACY_SLOT_DEFINITIONS = [
    {
        "slot_id": "double_click",
        "title": "双击（兼容）",
        "default_name": "right-double-click",
        "default_label": "双击互动",
        "color": "#3867d6",
        "bg_from": "#f0f5ff",
        "bg_to": "#dbe8ff",
        "border": "#74b9ff",
        "is_idle": False,
    },
    *[
        {
            "slot_id": f"action_{idx}",
            "title": f"动作 {idx}（兼容）",
            "default_name": name,
            "default_label": label,
            "color": "#9b59b6",
            "bg_from": "#fbf4fc",
            "bg_to": "#f3e4f7",
            "border": "#dfb9ed",
            "is_idle": False,
        }
        for idx, (name, label) in enumerate(
            (("waving", "挥手打招呼"), ("jumping", "开心跳跃"), ("running", "欢快奔跑"), ("review", "特殊才艺"), ("dance", "跳舞表演")),
            1,
        )
    ],
]


def load_memory_frames(folder_or_file: Path, target_size: QSize = QSize(140, 110), max_frames: int = 15) -> List[QPixmap]:
    """预先将动作序列帧加载到内存并缩放到目标尺寸，彻底消除重绘磁盘 IO 与黑屏闪烁"""
    pixmaps: List[QPixmap] = []
    target = Path(folder_or_file)
    if not target.exists():
        return pixmaps

    frame_paths: List[Path] = []
    valid_img_exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}

    # 1. 目标是文件夹
    if target.is_dir():
        # 1.1 检查内部是否存在包含 frame_*.png 的 .media_cache
        cache_dir = target / ".media_cache"
        if cache_dir.exists():
            for sub in sorted(cache_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
                if sub.is_dir():
                    cached_webps = sorted([p for p in sub.glob("frame_*.webp")])
                    cached_pngs = sorted([p for p in sub.glob("frame_*.png")])
                    found_frames = cached_webps if cached_webps else cached_pngs
                    if found_frames:
                        frame_paths = found_frames
                        break
        # 1.2 检查目录内直接存在的图片帧
        if not frame_paths:
            direct_files = sorted([
                p for p in target.iterdir()
                if p.is_file() and p.suffix.lower() in valid_img_exts and not p.name.startswith(".")
            ])
            if direct_files:
                frame_paths = direct_files
        # 1.3 递归/媒体源扩展
        if not frame_paths:
            try:
                from .media_folder import expand_folder_frames
                frame_paths = expand_folder_frames(target)
            except Exception:
                pass

    # 2. 目标是单个文件
    elif target.is_file():
        suffix = target.suffix.lower()
        if suffix in {".mov", ".mp4", ".webm", ".mkv", ".avi", ".m4v", ".gif", ".apng"}:
            cache_dir = target.parent / ".media_cache"
            if cache_dir.is_dir():
                stem_lower = target.stem.lower()
                for sub in cache_dir.iterdir():
                    if sub.is_dir() and sub.name.lower().startswith(f"{stem_lower}_"):
                        cached_webps = sorted([p for p in sub.glob("frame_*.webp")])
                        cached_pngs = sorted([p for p in sub.glob("frame_*.png")])
                        found = cached_webps if cached_webps else cached_pngs
                        if found:
                            frame_paths = found
                            break
            if not frame_paths:
                try:
                    from .media_folder import media_source_frames
                    frame_paths = media_source_frames(target)
                except Exception:
                    pass
        elif suffix in valid_img_exts:
            try:
                from .media_folder import _is_truly_animated, media_source_frames
                if _is_truly_animated(target):
                    frame_paths = media_source_frames(target)
                else:
                    frame_paths = [target]
            except Exception:
                frame_paths = [target]

    if not frame_paths:
        return pixmaps

    step = max(1, len(frame_paths) // max_frames)
    for p in frame_paths[::step]:
        pm = QPixmap(str(p))
        if not pm.isNull():
            scaled = pm.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            pixmaps.append(scaled)
        if len(pixmaps) >= max_frames:
            break

    return pixmaps


def find_action_media_source(character_folder: Path, action_name: str, folder_name: str = "") -> Optional[Path]:
    """根据动作名与目录名定位该动作的真实媒体文件、子目录或缓存"""
    names_to_try = []
    if folder_name and folder_name not in {".", ""}:
        names_to_try.append(folder_name)
    if action_name and action_name not in names_to_try:
        names_to_try.append(action_name)

    # 1. 检查是否存在以该动作命名的独立视频/媒体文件
    for n in names_to_try:
        for ext in (".mov", ".mp4", ".webm", ".gif", ".png", ".webp"):
            candidate = character_folder / f"{n}{ext}"
            if candidate.is_file():
                return candidate

    # 2. 检查是否存在对应的子目录（帧序列或视频目录）
    for n in names_to_try:
        candidate = character_folder / n
        if candidate.is_dir():
            return candidate

    # 3. 检查 .media_cache 中匹配该动作的缓存子目录
    cache_dir = character_folder / ".media_cache"
    if cache_dir.is_dir():
        for n in names_to_try:
            for sub in cache_dir.iterdir():
                if sub.is_dir() and sub.name.lower().startswith(f"{n.lower()}_"):
                    return sub

    return None


class ActionGridSlotCard(QFrame):
    """
    动作设置中的单个动作卡槽：
    - 彩色柔和背景与标头；
    - 内存中流畅循环播放动作序列（不卡顿、不黑屏、不闪烁）；
    - 支持直接从系统拖拽外部文件（PNG/JPG/GIF/MP4/MOV）进槽替换；
    - 响应式缩放，全屏模式下卡片与动画画布自适应放大。
    """
    fileDropped = Signal(str, str)  # (slot_id, file_path)
    idleModeToggled = Signal(bool)  # is_fixed_idle
    renameRequested = Signal(str)   # slot_id
    generateStaticRequested = Signal(str)  # slot_id

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

        self.setMinimumSize(160, 160)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
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
        layout.addLayout(header)

        # 2. 中央动画播放画布
        self.display_label = QLabel()
        self.display_label.setMinimumSize(130, 90)
        self.display_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
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

    def update_dimensions(self, is_large: bool):
        """全屏/大屏响应式缩放"""
        min_h = 220 if is_large else 160
        disp_h = 135 if is_large else 90
        title_fs = 13 if is_large else 11
        name_fs = 12 if is_large else 10
        self.setMinimumHeight(min_h)
        self.display_label.setMinimumHeight(disp_h)
        self.title_label.setStyleSheet(f"font-size: {title_fs}px; font-weight: bold; color: {self.slot_def['color']}; background: transparent;")
        self.name_label.setStyleSheet(f"font-size: {name_fs}px; font-weight: bold; color: #3d2f2b; background: transparent;")
        if self.cached_frames:
            pm = self.cached_frames[self.frame_idx]
            self.display_label.setPixmap(pm.scaled(self.display_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def set_action_data(self, action_name: str, action_label: str, folder_name: str, fps: int = 10, fallback_frames: Optional[List[QPixmap]] = None):
        self.action_name = action_name
        self.action_label = action_label or guess_action_label(action_name)
        self.folder_name = folder_name
        self.fps = max(1, fps)

        self.name_label.setText(f"{self.action_label} · {self.action_name}")

        target_source = find_action_media_source(self.character_folder, action_name, folder_name)
        if target_source is not None:
            self.cached_frames = load_memory_frames(target_source, QSize(360, 320))
        elif folder_name in {".", ""}:
            self.cached_frames = load_memory_frames(self.character_folder, QSize(360, 320))
        else:
            self.cached_frames = []

        if not self.cached_frames and fallback_frames:
            self.cached_frames = list(fallback_frames)

        self.frame_idx = 0
        if self.cached_frames:
            self.display_label.setPixmap(self.cached_frames[0].scaled(self.display_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.anim_timer.start(int(1000 / self.fps))
        else:
            self.anim_timer.stop()
            self.display_label.setText("➕ 拖入图片/动图/视频")
            self.display_label.setStyleSheet("background: rgba(255, 255, 255, 0.4); border-radius: 10px; border: 1.5px dashed #fed7cc; color: #a89a93; font-size: 10px;")

    def set_static_image(self, image_path: Path):
        """让静态槽位加载透明静态图片，永不循环播放动画"""
        image_path = Path(image_path)
        pixmap = QPixmap(str(image_path))
        if pixmap.isNull():
            frames = load_memory_frames(image_path, QSize(360, 320))
            if frames:
                pixmap = frames[0]
            else:
                return False
        self.cached_frames = [pixmap]
        self.frame_idx = 0
        self.action_name = "static"
        self.action_label = "静态图片"
        self.folder_name = image_path.name
        self.name_label.setText(f"{self.action_label} · {image_path.name}")
        self.display_label.setStyleSheet("background: rgba(255, 255, 255, 0.65); border-radius: 10px; border: 1px dashed rgba(0,0,0,0.06);")
        self.display_label.setPixmap(self.cached_frames[0].scaled(self.display_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.anim_timer.stop()
        return True

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
        pm = self.cached_frames[self.frame_idx]
        self.display_label.setPixmap(pm.scaled(self.display_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.cached_frames and not self.anim_timer.isActive():
            pm = self.cached_frames[self.frame_idx]
            self.display_label.setPixmap(pm.scaled(self.display_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

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
        mime = event.mimeData()
        if mime.hasUrls() or (mime.hasText() and mime.text().startswith("source:")):
            event.acceptProposedAction()
            self.update_card_style(highlight=True)
        else:
            super().dragEnterEvent(event)

    def dragLeaveEvent(self, event):
        self.update_card_style(highlight=False)
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self.update_card_style(highlight=False)
        mime = event.mimeData()
        local_path = ""
        if mime.hasText() and mime.text().startswith("source:"):
            local_path = mime.text()[len("source:"):].strip()
        elif mime.hasUrls():
            urls = mime.urls()
            if urls:
                local_path = urls[0].toLocalFile()
        if local_path:
            self.fileDropped.emit(self.slot_id, local_path)
            event.acceptProposedAction()
            return
        super().dropEvent(event)


class ActionSourceFileCard(QFrame):
    """下方素材架中的动作卡片，展示并实时循环播放动作帧动画，支持直接拖拽到上方 5 个卡槽。"""

    def __init__(self, file_path: Path, character_folder: Path, parent=None):
        super().__init__(parent)
        self.file_path = Path(file_path).resolve()
        self.character_folder = Path(character_folder).resolve()
        self.drag_start_pos: Optional[QPoint] = None
        self.cached_frames: List[QPixmap] = []
        self.frame_idx = 0
        self.setObjectName("ActionSourceFileCard")
        self.setMinimumSize(150, 150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setCursor(PetCursorManager.pointer_cursor())
        self.setStyleSheet("""
            QFrame#ActionSourceFileCard {
                background: #ffffff;
                border: 1.5px solid #edf2f7;
                border-radius: 12px;
            }
            QFrame#ActionSourceFileCard:hover {
                border: 2px solid #ff6b81;
                background: #fff9fa;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # 动态播放预览区域
        self.preview = QLabel()
        self.preview.setMinimumSize(120, 80)
        self.preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setStyleSheet("background: rgba(248, 250, 252, 0.85); border: 1px dashed rgba(0, 0, 0, 0.08); border-radius: 10px;")
        layout.addWidget(self.preview, 1)

        # 动作名称 (中文推测 + 英文标识)
        stem = self.file_path.stem.lower()
        if stem in {"click", "tap"}:
            label_text = "单击 · click"
        elif stem in {"drag", "pull"}:
            label_text = "拖拽 · drag"
        elif stem in {"habit1", "thinking"}:
            label_text = "思考 · habit1"
        elif stem in {"habit2", "result"}:
            label_text = "回答 · habit2"
        elif stem in {"idle", "stand"}:
            label_text = "待机 · idle"
        else:
            guess = guess_action_label(stem)
            label_text = f"{guess} · {stem}" if guess != stem else stem

        self.path_label = QLabel(label_text)
        self.path_label.setToolTip(str(self.file_path))
        self.path_label.setAlignment(Qt.AlignCenter)
        self.path_label.setStyleSheet("font-size: 10px; font-weight: bold; color: #334155; background: transparent;")
        layout.addWidget(self.path_label)

        # 格式与帧数标签
        self.type_label = QLabel("加载中...")
        self.type_label.setAlignment(Qt.AlignCenter)
        self.type_label.setStyleSheet("font-size: 9px; color: #94a3b8; background: transparent;")
        layout.addWidget(self.type_label)

        # 平滑帧定时器
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._step_frame)

        self._load_and_start_playback()

    def update_dimensions(self, is_large: bool):
        min_h = 210 if is_large else 150
        prev_h = 130 if is_large else 80
        title_fs = 12 if is_large else 10
        type_fs = 10 if is_large else 9
        self.setMinimumHeight(min_h)
        self.preview.setMinimumHeight(prev_h)
        self.path_label.setStyleSheet(f"font-size: {title_fs}px; font-weight: bold; color: #334155; background: transparent;")
        self.type_label.setStyleSheet(f"font-size: {type_fs}px; color: #94a3b8; background: transparent;")
        if self.cached_frames:
            pm = self.cached_frames[self.frame_idx]
            self.preview.setPixmap(pm.scaled(self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def _load_and_start_playback(self):
        self.cached_frames = load_memory_frames(self.file_path, QSize(160, 140))
        ext = self.file_path.suffix.lower()
        count = len(self.cached_frames)

        if count > 0:
            if ext in {".mov", ".mp4"}:
                type_desc = f"🎬 动画 ({ext.lstrip('.').upper()}) · {count} 帧"
            elif ext in {".gif", ".webp"}:
                type_desc = f"🎞️ 动图 · {count} 帧"
            elif self.file_path.is_dir():
                type_desc = f"📁 序列帧 · {count} 帧"
            else:
                type_desc = f"🖼️ 静态图片 · 1 帧"

            self.type_label.setText(type_desc)
            self.preview.setPixmap(self.cached_frames[0].scaled(self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            if count > 1:
                self.anim_timer.start(83)  # 约 12 fps 平滑播放
        else:
            self.type_label.setText(f"{ext.lstrip('.').upper()} 文件")
            self.preview.setText("📄")
            self.preview.setStyleSheet("background: #f8fafc; border: 1px solid #eef2f7; border-radius: 8px; font-size: 28px; color: #94a3b8;")

    def _step_frame(self):
        if not self.cached_frames:
            return
        self.frame_idx = (self.frame_idx + 1) % len(self.cached_frames)
        pm = self.cached_frames[self.frame_idx]
        self.preview.setPixmap(pm.scaled(self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton) or self.drag_start_pos is None:
            return
        if (event.pos() - self.drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return
        drag = QDrag(self)
        mime = QMimeData()
        mime.setText(f"source:{self.file_path}")
        mime.setUrls([QUrl.fromLocalFile(str(self.file_path))])
        drag.setMimeData(mime)
        if self.cached_frames:
            pm = self.cached_frames[self.frame_idx]
            drag.setPixmap(pm.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            drag.setHotSpot(QPoint(32, 32))
        drag.exec(Qt.CopyAction)


class CharacterActionStudioDialog(QDialog):
    """
    五动作角色工坊：上方固定五个动作槽位，下方展示该角色目录中的全部文件。
    支持全屏/小屏无缝切换，内容根据窗口尺寸响应式放大。
    """
    def __init__(self, character_folder: Path, parent=None):
        super().__init__(parent)
        self.character_folder = Path(character_folder).resolve()
        self.info = inspect_character_folder(self.character_folder)

        self.setWindowTitle(f"🐾 {self.info['name']} · 动作")
        self.resize(1080, 780)
        self.setMinimumSize(940, 680)
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinMaxButtonsHint
            | Qt.WindowCloseButtonHint
        )
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

        self.is_fixed_idle = bool(self.meta.get("fixed_idle", True))
        self.is_head_track_character = (
            str(self.meta.get("interaction_mode") or "").strip().lower() == "head_track"
            or "head_track" in (self.meta.get("animations") or {})
        )
        self.slot_cards: Dict[str, ActionGridSlotCard] = {}
        self.primary_slot_cards: Dict[str, ActionGridSlotCard] = {}
        self.slot_action_map: Dict[str, Dict[str, Any]] = {}
        self.visible_slot_ids = [item["slot_id"] for item in SLOT_DEFINITIONS]
        self.source_cards: List[ActionSourceFileCard] = []
        self._current_gallery_cols = 0

        self._build_ui()
        self._load_and_populate_grid()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 14, 18, 14)
        main_layout.setSpacing(10)

        # 1. 顶部 Header（简洁清爽，无冗余说明）
        header = QHBoxLayout()
        header.setSpacing(10)

        title = QLabel(f"🐾 {self.info['name']} · 动作")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #2d2320;")
        header.addWidget(title, 1)

        btn_folder = SpringPushButton("📁 打开角色目录")
        btn_folder.setStyleSheet("""
            QPushButton {
                background: #ffffff; border: 1px solid #fed7cc; border-radius: 8px;
                padding: 5px 12px; font-size: 11px; font-weight: bold; color: #55443d;
            }
            QPushButton:hover { background: #fff4ee; color: #ff526c; }
        """)
        btn_folder.clicked.connect(self._open_folder)
        header.addWidget(btn_folder)

        btn_save = SpringPushButton("💾 保存")
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
        btn_save.clicked.connect(lambda: self.save_and_apply(show_msg=True, close_dialog=True))
        header.addWidget(btn_save)

        main_layout.addLayout(header)

        if self.is_head_track_character:
            special_hint = QLabel("🐱 这个角色使用独立的摇头跟随逻辑；下面仍可查看它的全部素材。")
            special_hint.setStyleSheet("background: #fff7ed; color: #9a3412; border: 1px solid #fed7aa; border-radius: 8px; padding: 7px 10px; font-size: 11px;")
            main_layout.addWidget(special_hint)

        # 2. 动作槽位网格（直接呈现动作卡槽，无需赘述“五个动作”）
        grid_container = QWidget()
        grid_layout = QGridLayout(grid_container)
        grid_layout.setContentsMargins(4, 4, 4, 4)
        grid_layout.setSpacing(10)

        for i, s_def in enumerate(SLOT_DEFINITIONS):
            card = ActionGridSlotCard(s_def, self.character_folder, grid_container)
            card.fileDropped.connect(self._on_file_dropped_to_slot)
            card.idleModeToggled.connect(self._on_idle_mode_toggled)
            card.renameRequested.connect(self._on_rename_requested)
            card.generateStaticRequested.connect(self.generate_and_apply_static_image)
            self.primary_slot_cards[s_def["slot_id"]] = card
            # 旧版公共属性保留前三个基础槽位，兼容旧配置和调用方。
            if s_def["slot_id"] in {"idle", "click", "drag"}:
                self.slot_cards[s_def["slot_id"]] = card

            grid_layout.addWidget(card, 0, i)
            grid_layout.setColumnStretch(i, 1)
            if self.is_head_track_character:
                card.setEnabled(False)

        # 旧版槽位只隐藏保留，避免历史测试和旧配置读取失败；用户不会在界面看到它们。
        for legacy_def in LEGACY_SLOT_DEFINITIONS:
            card = ActionGridSlotCard(legacy_def, self.character_folder, self)
            card.fileDropped.connect(self._on_file_dropped_to_slot)
            card.idleModeToggled.connect(self._on_idle_mode_toggled)
            card.renameRequested.connect(self._on_rename_requested)
            card.hide()
            self.slot_cards[legacy_def["slot_id"]] = card

        main_layout.addWidget(grid_container, 0)

        # 3. 下方素材架：列出角色目录内的全部动作素材
        files_title = QLabel("📦 全部动作素材")
        files_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #334155;")
        main_layout.addWidget(files_title)

        self.files_scroll = QScrollArea()
        self.files_scroll.setWidgetResizable(True)
        self.files_scroll.setMinimumHeight(220)
        self.files_scroll.setFrameShape(QFrame.NoFrame)
        self.files_scroll.setStyleSheet("background: transparent;")
        self.files_container = QWidget()
        self.files_container.setStyleSheet("background: transparent;")
        self.files_layout = QGridLayout(self.files_container)
        self.files_layout.setContentsMargins(4, 4, 4, 4)
        self.files_layout.setHorizontalSpacing(10)
        self.files_layout.setVerticalSpacing(10)
        self.files_scroll.setWidget(self.files_container)
        main_layout.addWidget(self.files_scroll, 1)

        # 4. 底部状态栏
        footer = QHBoxLayout()
        self.status_label = QLabel("从下方拖动任意动作卡片到上方对应槽位即可绑定。")
        self.status_label.setStyleSheet("font-size: 11px; color: #7f6a61;")
        footer.addWidget(self.status_label, 1)
        main_layout.addLayout(footer)

        self._populate_source_files()

    def toggle_fullscreen(self):
        """在全屏/最大化与正常窗口之间无缝切换"""
        if self.isMaximized() or self.isFullScreen():
            self.showNormal()
            self.btn_fullscreen.setText("🗖 全屏模式")
            self.btn_fullscreen.setToolTip("切换到全屏模式")
        else:
            self.showMaximized()
            self.btn_fullscreen.setText("🗗 小屏模式")
            self.btn_fullscreen.setToolTip("恢复为小屏窗口模式")

    def changeEvent(self, event):
        if event.type() == QEvent.WindowStateChange:
            if self.isMaximized() or self.isFullScreen():
                if hasattr(self, "btn_fullscreen"):
                    self.btn_fullscreen.setText("🗗 小屏模式")
            else:
                if hasattr(self, "btn_fullscreen"):
                    self.btn_fullscreen.setText("🗖 全屏模式")
        super().changeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_responsive_layout()

    def _apply_responsive_layout(self):
        """根据当前窗口宽度自适应放大卡片尺寸与重排网格列数"""
        is_large = bool(self.width() >= 1350 or self.isMaximized() or self.isFullScreen())

        for card in self.primary_slot_cards.values():
            if hasattr(card, "update_dimensions"):
                card.update_dimensions(is_large)

        for card in self.source_cards:
            if hasattr(card, "update_dimensions"):
                card.update_dimensions(is_large)

        if hasattr(self, "files_scroll") and hasattr(self, "files_layout") and self.source_cards:
            viewport_w = self.files_scroll.viewport().width()
            card_w = 210 if is_large else 165
            cols = max(3, max(1, viewport_w - 20) // (card_w + 10))
            if getattr(self, "_current_gallery_cols", 0) != cols:
                self._current_gallery_cols = cols
                while self.files_layout.count():
                    self.files_layout.takeAt(0)
                for idx, card in enumerate(self.source_cards):
                    r, c = divmod(idx, cols)
                    self.files_layout.addWidget(card, r, c)
                self.files_layout.setRowStretch((len(self.source_cards) // cols) + 1, 1)

    def _character_files(self) -> List[Path]:
        """返回角色目录中的可用动作媒体源（视频、动图、动作文件夹、图片），跳过配置与内部缓存。"""
        if not self.character_folder.exists():
            return []

        valid_media_exts = {".mov", ".mp4", ".webm", ".gif", ".png", ".jpg", ".jpeg", ".webp"}
        items: List[Path] = []

        for p in sorted(self.character_folder.iterdir(), key=lambda x: x.name.lower()):
            if p.name.startswith(".") or p.name in {".media_cache", "__pycache__"}:
                continue
            if p.is_file():
                if p.suffix.lower() in valid_media_exts and p.name not in {"asset.json", "动作说明.md"}:
                    if p.stem.lower() in {"static", "preview"}:
                        continue
                    items.append(p)
            elif p.is_dir():
                sub_media = [
                    f for f in sorted(p.iterdir(), key=lambda x: x.name.lower())
                    if f.is_file() and f.suffix.lower() in valid_media_exts and not f.name.startswith(".")
                ]
                if sub_media:
                    videos = [f for f in sub_media if f.suffix.lower() in {".mov", ".mp4", ".webm", ".gif"}]
                    if videos:
                        items.extend(videos)
                    else:
                        items.append(p)

        def sort_priority(item: Path) -> int:
            stem = item.stem.lower()
            if stem in {"idle", "stand"}:
                return 1
            if stem in {"click", "tap"}:
                return 2
            if stem in {"drag", "pull"}:
                return 3
            if stem in {"habit1", "thinking"}:
                return 4
            if stem in {"habit2", "result"}:
                return 5
            return 10

        items.sort(key=lambda x: (sort_priority(x), x.name.lower()))
        return items

    def _populate_source_files(self):
        while self.files_layout.count():
            item = self.files_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.source_cards = []
        files = self._character_files()
        is_large = bool(self.width() >= 1350 or self.isMaximized() or self.isFullScreen())
        card_w = 210 if is_large else 165
        viewport_w = self.files_scroll.viewport().width() if hasattr(self, "files_scroll") else self.width()
        cols = max(3, max(1, viewport_w - 20) // (card_w + 10))
        self._current_gallery_cols = cols

        for index, file_path in enumerate(files):
            card = ActionSourceFileCard(file_path, self.character_folder, self.files_container)
            card.update_dimensions(is_large)
            self.source_cards.append(card)
            row, column = divmod(index, cols)
            self.files_layout.addWidget(card, row, column)
        if not files:
            empty = QLabel("这个角色目录暂时没有可拖拽动作文件。")
            empty.setStyleSheet("color: #94a3b8; padding: 12px;")
            self.files_layout.addWidget(empty, 0, 0)
        self.files_layout.setRowStretch((len(files) // cols) + 1, 1)

    def _find_static_image(self) -> Optional[Path]:
        """寻找静态槽位使用的真实静态图片，严格过滤视频文件。"""
        # 1. 优先使用当前角色根目录下的 static.png / static.webp / static.jpg / preview.png
        for name in ("static.png", "static.webp", "static.jpg", "preview.png", "preview.webp", "preview.jpg"):
            candidate = self.character_folder / name
            if candidate.is_file():
                return candidate
        preview = self.meta.get("preview") or self.meta.get("image")
        if preview:
            candidate = (self.character_folder / str(preview)).resolve()
            if candidate.is_file() and candidate.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
                return candidate
        # 2. 从当前角色目录中查找任意透明静态图片（排除 icon/徽标）
        for candidate in self._character_files():
            if candidate.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"} and candidate.name not in {"icon.png"}:
                return candidate
        return None

    def _load_and_populate_grid(self):
        """装配五个固定槽位，并把旧版动作只放入隐藏兼容层。"""
        anims = self.meta.get("animations", {}) if isinstance(self.meta.get("animations"), dict) else {}
        action_labels = self.meta.get("action_labels", {}) if isinstance(self.meta.get("action_labels"), dict) else {}
        triggers = self.meta.get("triggers", {}) if isinstance(self.meta.get("triggers"), dict) else {}
        action_slots = self.meta.get("action_slots", {}) if isinstance(self.meta.get("action_slots"), dict) else {}
        all_actions = list(anims.keys())
        root_frames = load_memory_frames(self.character_folder, QSize(96, 96))
        fallback_frames = root_frames

        def choose(slot_key, trigger_keys, fallback_names, fallback=""):
            if slot_key and slot_key in action_slots:
                val = str(action_slots[slot_key] or "").strip()
                if val and (val in anims or (self.character_folder / val).exists() or not anims):
                    return val
            for key in trigger_keys:
                candidate = str(triggers.get(key) or "").strip()
                if candidate and (candidate in anims or not anims):
                    return candidate
            for name in fallback_names:
                if name in anims:
                    return name
            if fallback == "":
                return ""
            return all_actions[0] if all_actions else fallback

        def fill(slot_id, action_name, default_label):
            card = self.primary_slot_cards[slot_id]
            if not action_name:
                card.set_action_data("", default_label, "", 10, None)
                return
            definition = anims.get(action_name, {}) if isinstance(anims.get(action_name), dict) else {}
            label = action_labels.get(action_name) or definition.get("label") or default_label or guess_action_label(action_name)
            folder = str(definition.get("folder") or ("." if action_name in {"idle", "static"} else action_name))
            fps = int(definition.get("fps") or (10 if slot_id in {"idle", "drag"} else 12))
            card.set_action_data(action_name, label, folder, fps, fallback_frames)

        click_anim = choose("click", ("left-click",), ("click", "tap", "jumping"), "click")
        drag_anim = choose("drag", ("left-drag",), ("drag", "pull", "running"), "drag")
        thinking_anim = choose("thinking", ("ai-thinking", "deepseek-thinking", "codex-thinking", "thinking"), ("habit1", "thinking", "waiting"), "")
        result_anim = choose("result", ("ai-result", "deepseek-result", "codex-answered", "result", "answered", "deepseek-waiting"), ("habit2", "result", "reward", "review"), "")

        static_image = self._find_static_image()
        if static_image is not None:
            self.primary_slot_cards["idle"].set_static_image(static_image)
        else:
            fill("idle", "static", "静态图片")
        self.primary_slot_cards["idle"].set_fixed_idle(self.is_fixed_idle)
        fill("click", click_anim, "轻戳点击")
        fill("drag", drag_anim, "提溜悬空")
        fill("thinking", thinking_anim, "思考中")
        fill("result", result_anim, "已出结果")

        # 旧测试/旧配置仍可读取，但这些卡片不会进入新界面。
        legacy_map = {
            "double_click": triggers.get("left-double-click") or ("right-double-click" if "right-double-click" in anims else ""),
            "action_1": "waving",
            "action_2": "jumping",
            "action_3": "running",
            "action_4": "review",
            "action_5": "dance",
        }
        for slot_id, action_name in legacy_map.items():
            card = self.slot_cards[slot_id]
            if action_name and action_name in anims:
                definition = anims.get(action_name, {}) if isinstance(anims.get(action_name), dict) else {}
                card.set_action_data(
                    action_name,
                    action_labels.get(action_name) or definition.get("label") or guess_action_label(action_name),
                    str(definition.get("folder") or action_name),
                    int(definition.get("fps") or 10),
                    fallback_frames,
                )
                card.anim_timer.stop()
            else:
                card.set_action_data(card.slot_def["default_name"], card.slot_def["default_label"], "", 10, None)
                card.anim_timer.stop()

    def closeEvent(self, event):
        self.save_and_apply(show_msg=False, close_dialog=False)
        super().closeEvent(event)

    def _on_idle_mode_toggled(self, is_fixed: bool):
        self.is_fixed_idle = is_fixed
        desc = "🔒 固定静态（待机只播放这一动作）" if is_fixed else "🎲 随机静态（待机随机轮换动作）"
        self.status_label.setText(f"已切换为：{desc}")
        self.save_and_apply(show_msg=False, close_dialog=False)

    def _on_rename_requested(self, slot_id: str):
        card = self.primary_slot_cards.get(slot_id) or self.slot_cards[slot_id]
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
            self.save_and_apply(show_msg=False, close_dialog=False)

    def _on_file_dropped_to_slot(self, slot_id: str, file_path_str: str):
        """把下方素材或外部文件绑定到一个固定动作槽位。"""
        src = Path(file_path_str).resolve()
        if not src.exists():
            return

        card = self.primary_slot_cards.get(slot_id) or self.slot_cards[slot_id]
        # 角色目录内的现有文件直接复用，不复制大体积视频。
        try:
            relative = src.relative_to(self.character_folder)
            inside_character = True
        except ValueError:
            relative = Path()
            inside_character = False

        if inside_character and slot_id in self.visible_slot_ids:
            if relative.parent == Path("."):
                target_action_name = "idle" if src.stem.lower() in {"preview", "idle", "static"} else src.stem
                folder_name = "."
            else:
                target_action_name = relative.parent.name
                folder_name = relative.parent.as_posix()
            target_source = src if src.is_file() else (self.character_folder if folder_name == "." else self.character_folder / folder_name)
            card.set_action_data(
                target_action_name,
                card.action_label or guess_action_label(target_action_name),
                folder_name,
                card.fps,
                load_memory_frames(target_source, QSize(160, 140)),
            )
            if slot_id == "idle":
                card.set_static_image(target_source)
            self.status_label.setText(f"✅ 已将【{src.name}】绑定到【{card.slot_def['title']}】")
            self.save_and_apply(show_msg=False, close_dialog=False)
            return

        target_action_name = card.slot_def["default_name"]
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
                    # 图片统一保留原扩展名，方便用户在素材架中辨认。
                    for old_p in dest_dir.iterdir():
                        if old_p.is_file() and old_p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}:
                            old_p.unlink(missing_ok=True)
                    shutil.copy2(src, dest_dir / src.name)
                else:
                    # GIF、视频或其他文件直接拷贝进入
                    shutil.copy2(src, dest_dir / src.name)

            # 刷新该槽位动画
            card.set_action_data(target_action_name, card.action_label or guess_action_label(target_action_name), folder_name, card.fps)
            if slot_id == "idle":
                copied_image = next(
                    (item for item in dest_dir.iterdir() if item.is_file() and item.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".bmp"}),
                    None,
                )
                if copied_image is not None:
                    card.set_static_image(copied_image)
            self._populate_source_files()
            self.status_label.setText(f"🎉 成功将【{src.name}】填入【{card.slot_def['title']}】槽位！")
            self.save_and_apply(show_msg=False, close_dialog=False)

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

    def save_and_apply(self, show_msg: bool = False, close_dialog: bool = False):
        """保存五个动作槽位，并热重载桌面上正在运行的角色。"""
        if self.is_head_track_character:
            self.status_label.setText("摇头跟随角色使用独立逻辑，未改动动作配置。")
            if close_dialog:
                self.accept()
            return

        data = dict(self.meta)

        # 1. 静态模式由卡片上的固定/随机切换按钮控制
        data["fixed_idle"] = bool(self.is_fixed_idle)
        data["idle_variants"] = []

        # 2. 五个动作的触发绑定
        if "triggers" not in data or not isinstance(data["triggers"], dict):
            data["triggers"] = {}

        data["triggers"]["idle"] = "static" if self.is_fixed_idle else "idle"
        data["triggers"]["left-click"] = self.primary_slot_cards["click"].action_name or "click"
        data["triggers"]["left-drag"] = self.primary_slot_cards["drag"].action_name or "drag"
        thinking_action = self.primary_slot_cards["thinking"].action_name
        result_action = self.primary_slot_cards["result"].action_name
        if thinking_action:
            for key in ("ai-thinking", "deepseek-thinking", "codex-thinking"):
                data["triggers"][key] = thinking_action
        if result_action:
            for key in ("ai-result", "deepseek-result", "codex-answered"):
                data["triggers"][key] = result_action

        # 3. 动作中文名保存在顶层 action_labels，只记录新界面的五张卡片。
        if "action_labels" not in data or not isinstance(data["action_labels"], dict):
            data["action_labels"] = {}

        for slot_id in self.visible_slot_ids:
            card = self.primary_slot_cards[slot_id]
            if card.action_name and card.action_label:
                data["action_labels"][card.action_name] = card.action_label
        data["action_labels"]["static"] = "基础静态"
        if "idle" in data.get("animations", {}):
            data["action_labels"].setdefault("idle", "常规待机")

        # 4. 确保五个槽位对应的 animations 完整
        if "animations" not in data or not isinstance(data["animations"], dict):
            data["animations"] = {}

        static_p = self.character_folder / "static.png"
        if static_p.is_file():
            data["animations"]["static"] = {
                "image": "static.png",
                "fps": 1,
                "loop": False,
                "label": "基础静态",
            }

        for slot_id in self.visible_slot_ids:
            card = self.primary_slot_cards[slot_id]
            name = card.action_name
            if name and name not in data["animations"] and name != "static":
                folder_val = card.folder_name or name
                if (self.character_folder / folder_val).exists() or folder_val in {".", ""}:
                    data["animations"][name] = {
                        "folder": folder_val,
                        "fps": card.fps,
                        "loop": bool(name == "idle" or card.is_idle_slot),
                    }

        # 5. 按照 1:静态 2:待机 3:单击 4:拖拽 5:思考 6:结果 重排 animations 字典
        order_keys = ["static", "idle", "click", "drag", "habit1", "thinking", "habit2", "result"]
        reordered_anims = {}
        for k in order_keys:
            if k in data["animations"]:
                reordered_anims[k] = data["animations"][k]
        for k, v in data["animations"].items():
            if k not in reordered_anims:
                reordered_anims[k] = v
        data["animations"] = reordered_anims

        data["action_slots"] = {
            "idle": "static",
            "click": self.primary_slot_cards["click"].action_name or "click",
            "drag": self.primary_slot_cards["drag"].action_name or "drag",
            "thinking": thinking_action,
            "result": result_action,
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

        if show_msg and not os.environ.get("PYTEST_CURRENT_TEST"):
            QMessageBox.information(
                self,
                "保存成功",
                f"🎉 角色【{self.info['name']}】动作已保存生效！\n"
                f"- 已更新：asset.json\n"
                f"- 静态：固定图片\n"
                f"- 思考：{thinking_action or '未绑定'}\n"
                f"- 回答：{result_action or '未绑定'}\n"
                f"当前运行的桌宠已同步最新动作逻辑。",
            )
        if close_dialog:
            self.accept()

    def generate_and_apply_static_image(self, slot_id: Optional[str] = None) -> Optional[Path]:
        """使用生图/高清提取功能为当前角色生成符合初始状态的高清透明静态图，并装配到静态槽位。"""
        if self.is_head_track_character:
            self.status_label.setText("🐱 摇头跟随角色使用独立头部网格，无需生成单帧静态图。")
            return None

        static_path = self._generate_hd_static_image()
        if static_path and static_path.exists():
            self.primary_slot_cards["idle"].set_static_image(static_path)
            self.meta["preview"] = "preview.png"
            self.status_label.setText(f"🎉 成功为【{self.info['name']}】生成并装配高清静态图（preview.png / static.png）！")
            self._populate_source_files()
            self.save_and_apply(show_msg=False, close_dialog=False)
            return static_path
        else:
            self.status_label.setText("⚠️ 未能提取到可用的待机初始帧。")
            return None

    def _generate_hd_static_image(self) -> Optional[Path]:
        """按角色初始待机状态生成高保真高清透明静态图"""
        preview_p = self.character_folder / "preview.png"
        static_p = self.character_folder / "static.png"
        pet_type = self.meta.get("type", "frame_animation")

        try:
            # 1. 视频角色
            if pet_type == "video_animation":
                prev_2k = self.character_folder / "preview_2k.png"
                if prev_2k.exists():
                    shutil.copy2(prev_2k, preview_p)
                    shutil.copy2(prev_2k, static_p)
                    return preview_p
                if preview_p.exists():
                    try:
                        im = Image.open(preview_p)
                        if max(im.size) >= 720:
                            shutil.copy2(preview_p, static_p)
                            return preview_p
                    except Exception:
                        pass
                idle_anim = self.meta.get("animations", {}).get("idle", {})
                video_name = idle_anim.get("video", "idle.mov") if isinstance(idle_anim, dict) else "idle.mov"
                idle_mov = self.character_folder / video_name
                if not idle_mov.exists():
                    idle_mov = self.character_folder / "idle.mov"
                if idle_mov.exists():
                    from .media_folder import _hidden_subprocess_kwargs
                    cmd = [shutil.which("ffmpeg") or "ffmpeg", "-y", "-v", "error", "-i", str(idle_mov), "-vframes", "1", str(preview_p)]
                    subprocess.run(cmd, capture_output=True, **_hidden_subprocess_kwargs())
                    if preview_p.exists():
                        shutil.copy2(preview_p, static_p)
                        return preview_p

            # 2. 帧动画角色
            elif pet_type == "frame_animation":
                if preview_p.exists():
                    try:
                        im = Image.open(preview_p)
                        if max(im.size) >= 720:
                            shutil.copy2(preview_p, static_p)
                            return preview_p
                    except Exception:
                        pass

                # 寻找待机帧
                idle_anim = self.meta.get("animations", {}).get("idle", {})
                folder_val = idle_anim.get("folder", ".")
                idle_dir = self.character_folder if folder_val == "." else self.character_folder / folder_val
                resting_img = None
                if idle_dir.exists():
                    excluded = {"preview.png", "static.png", "preview_2k.png", "spritesheet.png"}
                    frames = sorted([
                        p for p in idle_dir.iterdir()
                        if p.is_file() and p.suffix.lower() in {".png", ".webp", ".jpg"} and p.name.lower() not in excluded
                    ], key=lambda x: [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", x.name)])
                    if frames:
                        resting_img = frames[0]

                if not resting_img:
                    old_prev = self.meta.get("preview")
                    if old_prev and (self.character_folder / old_prev).is_file():
                        resting_img = self.character_folder / old_prev

                if resting_img and resting_img.exists():
                    src_im = Image.open(resting_img).convert("RGBA")
                    w, h = src_im.size
                    scale = 4
                    hd_im = src_im.resize((w * scale, h * scale), Image.Resampling.NEAREST)
                    hd_im.save(str(preview_p), "PNG")
                    hd_im.save(str(static_p), "PNG")
                    return preview_p

            # 3. 精灵图表 (spritesheet)
            elif pet_type == "spritesheet":
                sheet_name = self.meta.get("image", "spritesheet.webp")
                sheet_path = self.character_folder / sheet_name
                if sheet_path.exists():
                    sheet_im = Image.open(sheet_path).convert("RGBA")
                    fw = int(self.meta.get("frame_width", 192))
                    fh = int(self.meta.get("frame_height", 208))
                    idle_frames = self.meta.get("animations", {}).get("idle", {}).get("frames", [])
                    first_frame = idle_frames[0] if idle_frames else {"col": 0, "row": 0}
                    col = int(first_frame.get("col", 0))
                    row = int(first_frame.get("row", 0))
                    box = (col * fw, row * fh, (col + 1) * fw, (row + 1) * fh)
                    crop_im = sheet_im.crop(box)
                    scale = 4
                    hd_im = crop_im.resize((fw * scale, fh * scale), Image.Resampling.NEAREST)
                    hd_im.save(str(preview_p), "PNG")
                    hd_im.save(str(static_p), "PNG")
                    return preview_p

        except Exception as e:
            self.status_label.setText(f"生图异常：{e}")
            return None

        return preview_p if preview_p.exists() else None

