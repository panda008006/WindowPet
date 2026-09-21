import os
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import (
    QEvent,
    QMimeData,
    QPoint,
    QPropertyAnimation,
    QEasingCurve,
    QRect,
    QRectF,
    QSize,
    Qt,
    Signal,
)
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QCursor,
    QDrag,
    QFont,
    QIcon,
    QKeySequence,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .notchnotes_store import NotchNotesStore
from .constants import resource_path
from .vibe_components import EmptyStateWidget, PopconfirmBubble, SpringPushButton


# --- WindowPet Macaron Pastel Palette ---
COLOR_BG_PAGE = QColor("#fffdfa")
COLOR_BG_PANEL = QColor("#fdf7f2")
COLOR_BG_CARD = QColor("#ffffff")
COLOR_BG_INPUT = QColor("#ffffff")
COLOR_LINE = QColor(226, 209, 196, 180)
COLOR_LINE_HOVER = QColor(255, 138, 158, 140)
COLOR_TEXT_MAIN = QColor("#2d2320")
COLOR_TEXT_MUTED = QColor(124, 109, 102, 220)
COLOR_TEXT_QUIET = QColor(168, 155, 148, 180)

# WindowPet Pastel Accents
COLOR_BLUE = QColor("#70a1ff")
COLOR_MINT = QColor("#52c79b")
COLOR_PINK = QColor("#ff8aa3")
COLOR_CORAL = QColor("#ff6b81")


class NotchHandleWidget(QWidget):
    """
    Compact notch handle (the folded state pill).
    Sits above the desktop pet or at screen top center.
    Clicking or hovering over it unfolds the full NotchNotes window.
    """
    clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 26)
        self.setCursor(Qt.PointingHandCursor)
        self.badge_text = "NotchNotes"
        self._hovered = False

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)

        path = QPainterPath()
        path.addRoundedRect(rect, 12, 12)

        bg = QLinearGradient(rect.topLeft(), rect.bottomLeft())
        if self._hovered:
            bg.setColorAt(0.0, QColor("#ffffff"))
            bg.setColorAt(1.0, QColor("#fff0eb"))
            border_color = QColor("#ff8a9e")
        else:
            bg.setColorAt(0.0, QColor("#ffffff"))
            bg.setColorAt(1.0, QColor("#fff6f2"))
            border_color = QColor("#fed7cc")

        painter.setBrush(QBrush(bg))
        painter.setPen(QPen(border_color, 1.2))
        painter.drawPath(path)

        # Draw mini glow dot
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(COLOR_MINT))
        painter.drawEllipse(QPoint(int(rect.left() + 14), int(rect.center().y())), 3, 3)

        # Text
        font = QFont("Microsoft YaHei UI", 8)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(COLOR_TEXT_MAIN if self._hovered else COLOR_TEXT_MUTED)
        painter.drawText(
            QRectF(rect.left() + 24, rect.top(), rect.width() - 32, rect.height()).toRect(),
            Qt.AlignVCenter | Qt.AlignLeft,
            self.badge_text,
        )



class TodoCheckButton(QPushButton):
    """Clean custom checkbox button that draws rounded box and checkmark."""
    toggled_state = Signal(bool)

    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.checked = checked
        self.setFixedSize(20, 20)
        self.setCursor(Qt.PointingHandCursor)
        self.clicked.connect(self._toggle)

    def setChecked(self, checked: bool):
        self.checked = checked
        self.update()

    def isChecked(self) -> bool:
        return self.checked

    def _toggle(self):
        self.checked = not self.checked
        self.update()
        self.toggled_state.emit(self.checked)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        rect = QRectF(2, 2, 16, 16)

        if self.checked:
            # Checked: filled cheerful mint green with crisp white checkmark
            painter.setBrush(QBrush(QColor("#52c79b")))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect, 4.5, 4.5)

            # Draw white checkmark
            pen = QPen(QColor("#ffffff"), 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            path = QPainterPath()
            path.moveTo(rect.left() + 4.0, rect.top() + 8.2)
            path.lineTo(rect.left() + 6.8, rect.top() + 11.2)
            path.lineTo(rect.left() + 12.2, rect.top() + 5.0)
            painter.drawPath(path)
        else:
            # Unchecked: clean white box with pastel coral border
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.setPen(QPen(QColor("#fed7cc"), 1.5))
            painter.drawRoundedRect(rect, 4.5, 4.5)


class PinButton(QPushButton):
    """Clean vector-drawn Pin toggle button."""
    def __init__(self, checked=False, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setFixedSize(26, 26)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("保持置顶")
        self._hovered = False

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)
        rect = self.rect()

        if self.isChecked():
            painter.setBrush(QBrush(QColor(255, 107, 129, 30)))
            painter.setPen(QPen(QColor("#ff6b81"), 1.2))
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 5, 5)
            pin_color = QColor("#ff526c")
        elif self._hovered:
            painter.setBrush(QBrush(QColor(254, 215, 204, 80)))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 5, 5)
            pin_color = QColor("#2d2320")
        else:
            pin_color = QColor("#a89c96")

        # Draw diagonal pushpin (tilted 45 degrees)
        painter.save()
        painter.translate(13, 13)
        painter.rotate(45)
        # Pin head
        painter.setPen(QPen(pin_color, 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(-4, -6, 4, -6)
        # Pin body taper
        painter.drawLine(-2, -6, -2, -1)
        painter.drawLine(2, -6, 2, -1)
        # Base ridge
        painter.drawLine(-4, -1, 4, -1)
        # Needle
        painter.setPen(QPen(pin_color, 1.4, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(0, -1, 0, 7)
        painter.restore()


class TodoItemWidget(QFrame):
    """
    Interactive Todo checklist row with clickable custom checkbox,
    strikethrough on completed text, and hover delete button.
    """
    toggled = Signal(int)
    deleted = Signal(int)

    def __init__(self, index: int, text: str, checked: bool, parent=None):
        super().__init__(parent)
        self.index = index
        self.text = text
        self.checked = checked
        self._hovered = False

        self.setObjectName("TodoItemWidget")
        self.setFixedHeight(38)
        self.setStyleSheet("""
            QFrame#TodoItemWidget {
                background-color: #ffffff;
                border: 1px solid #ebdcd2;
                border-radius: 9px;
            }
            QFrame#TodoItemWidget:hover {
                background-color: #fffaf7;
                border-color: #ffccd3;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(10)

        # Custom check button
        self.check_box = TodoCheckButton(checked=checked, parent=self)
        self.check_box.toggled_state.connect(self._on_toggled)
        layout.addWidget(self.check_box)

        # Label
        self.label = QLabel(text)
        self._apply_text_style()
        layout.addWidget(self.label, 1)

        # Delete Button (hidden until hover)
        self.del_btn = QPushButton("×")
        self.del_btn.setFixedSize(20, 20)
        self.del_btn.setCursor(Qt.PointingHandCursor)
        self.del_btn.setToolTip("删除此任务")
        self.del_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #a89c96;
                border: none;
                font-size: 14px;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255, 107, 129, 0.15);
                color: #ff526c;
            }
        """)
        self.del_btn.clicked.connect(lambda: self.deleted.emit(self.index))
        layout.addWidget(self.del_btn)

    def _apply_text_style(self):
        font = QFont("Microsoft YaHei UI", 9)
        font.setStrikeOut(self.checked)
        self.label.setFont(font)
        color = "#a89c96" if self.checked else "#2d2320"
        self.label.setStyleSheet(f"color: {color}; background: transparent; border: 0;")

    def _on_toggled(self, is_checked: bool):
        self.checked = is_checked
        self._apply_text_style()
        self.toggled.emit(self.index)



class FileShelfChip(QFrame):
    """
    Draggable file item in the bottom shelf.
    Can be clicked to open, or dragged out to Explorer/browser.
    """
    removed = Signal(int)

    def __init__(self, index: int, file_info: dict, parent=None):
        super().__init__(parent)
        self.index = index
        self.file_info = file_info
        self.file_path = file_info.get("path", "")
        self.file_name = file_info.get("name", "File")
        self.file_size = file_info.get("size", "")
        self._drag_start_pos = None

        self.setFixedHeight(30)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(f"{self.file_path}\n(双击直接打开，支持向外拖拽分享)")
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #ebdcd2;
                border-radius: 6px;
            }
            QFrame:hover {
                background-color: #fff4f2;
                border-color: #ff8a9e;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(7, 2, 7, 2)
        layout.setSpacing(6)

        # File icon
        ext = file_info.get("ext", "").lower()
        icon_text = "📄"
        if ext in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"):
            icon_text = "🖼️"
        elif ext in (".mp3", ".wav", ".flac", ".ogg"):
            icon_text = "🎵"
        elif ext in (".mp4", ".mkv", ".mov"):
            icon_text = "🎬"
        elif ext in (".zip", ".rar", ".7z", ".tar", ".gz"):
            icon_text = "📦"
        elif ext in (".py", ".js", ".ts", ".html", ".css", ".json", ".md"):
            icon_text = "💻"
        elif file_info.get("is_dir"):
            icon_text = "📁"

        icon_label = QLabel(icon_text)
        icon_label.setStyleSheet("background: transparent; border: 0;")
        layout.addWidget(icon_label)

        # Name label
        name_label = QLabel(self.file_name)
        font = QFont("Microsoft YaHei UI", 8)
        name_label.setFont(font)
        name_label.setStyleSheet("color: #2d2320; background: transparent; border: 0;")
        name_label.setMaximumWidth(120)
        layout.addWidget(name_label)

        # Size
        if self.file_size:
            size_label = QLabel(self.file_size)
            size_label.setFont(QFont("Microsoft YaHei UI", 7))
            size_label.setStyleSheet("color: #8c7e77; background: transparent; border: 0;")
            layout.addWidget(size_label)

        # Remove btn
        del_btn = QPushButton("×")
        del_btn.setFixedSize(14, 14)
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #a89c96;
                border: 0;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ff526c;
            }
        """)
        del_btn.clicked.connect(lambda: self.removed.emit(self.index))
        layout.addWidget(del_btn)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton and os.path.exists(self.file_path):
            try:
                os.startfile(self.file_path)
            except Exception as e:
                print(f"Failed to open file: {e}")
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.LeftButton) or not self._drag_start_pos:
            return
        if (event.pos() - self._drag_start_pos).manhattanLength() < QApplication.startDragDistance():
            return

        drag = QDrag(self)
        mime = QMimeData()
        p = Path(self.file_path).resolve()
        if p.exists():
            from PySide6.QtCore import QUrl
            mime.setUrls([QUrl.fromLocalFile(str(p))])
            drag.setMimeData(mime)
            drag.exec(Qt.CopyAction)
        super().mouseMoveEvent(event)


class FileShelfWidget(QFrame):
    """
    Bottom drop shelf matching NotchNotes signature file stash area.
    """
    files_changed = Signal()

    def __init__(self, store: NotchNotesStore, parent=None):
        super().__init__(parent)
        self.store = store
        self.setAcceptDrops(True)
        self._drag_over = False

        self.setObjectName("FileShelfWidget")
        self.setStyleSheet("""
            QFrame#FileShelfWidget {
                background-color: #fdf7f2;
                border-top: 1px solid #fed7cc;
                border-bottom-left-radius: 18px;
                border-bottom-right-radius: 18px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 10)
        layout.setSpacing(6)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        shelf_title = QLabel("文件暂存架 · File Shelf")
        font = QFont("Microsoft YaHei UI", 8)
        font.setBold(True)
        shelf_title.setFont(font)
        shelf_title.setStyleSheet("color: #55443d; background: transparent;")
        header_row.addWidget(shelf_title)

        self.count_badge = QLabel("0")
        self.count_badge.setStyleSheet("""
            color: #ff526c;
            background-color: #ffeff0;
            border: 1px solid #ffccd3;
            border-radius: 8px;
            padding: 1px 6px;
            font-size: 10px;
            font-weight: bold;
        """)
        header_row.addWidget(self.count_badge)
        header_row.addStretch(1)

        hint = QLabel("拖入文件即可暂存")
        hint.setStyleSheet("color: #a89c96; font-size: 10px; background: transparent;")
        header_row.addWidget(hint)

        self.clear_btn = SpringPushButton("清空")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #a89c96;
                border: 0;
                font-size: 10px;
            }
            QPushButton:hover {
                color: #ff526c;
            }
        """)
        self.clear_btn.clicked.connect(self._prompt_clear_shelf)
        header_row.addWidget(self.clear_btn)
        layout.addLayout(header_row)

    def _prompt_clear_shelf(self):
        if not self.store.file_shelf:
            return
        pop = PopconfirmBubble(
            target_widget=self.clear_btn,
            message="确定清空暂存架上的所有文件吗？",
            confirm_text="确定清空",
            cancel_text="取消",
            dark_mode=False,
            parent=self.window(),
        )
        pop.confirmed.connect(self._clear_shelf)
        pop.show_above_target()
        self._shelf_popconfirm = pop

        # Chips scroll area
        self.scroll = QScrollArea()
        self.scroll.setFixedHeight(44)
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: 0; }
            QScrollBar:horizontal {
                height: 4px;
                background: transparent;
            }
            QScrollBar::handle:horizontal {
                background: #e2d2c8;
                border-radius: 2px;
            }
        """)

        self.chips_container = QWidget()
        self.chips_container.setStyleSheet("background: transparent;")
        self.chips_layout = QHBoxLayout(self.chips_container)
        self.chips_layout.setContentsMargins(0, 0, 0, 0)
        self.chips_layout.setSpacing(8)
        self.chips_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.scroll.setWidget(self.chips_container)
        layout.addWidget(self.scroll)

        self.refresh()

    def refresh(self):
        while self.chips_layout.count() > 0:
            child = self.chips_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        items = self.store.file_shelf
        self.count_badge.setText(str(len(items)))
        if not items:
            empty_hint = QLabel("暂无暂存文件，从桌面或文件夹拖入文件即可随时取用")
            empty_hint.setStyleSheet("color: #a89c96; font-size: 11px; padding-left: 4px;")
            self.chips_layout.addWidget(empty_hint)
        else:
            for idx, file_info in enumerate(items):
                chip = FileShelfChip(idx, file_info, self)
                chip.removed.connect(self._remove_item)
                self.chips_layout.addWidget(chip)

    def _remove_item(self, idx: int):
        self.store.remove_file_shelf_item(idx)
        self.refresh()
        self.files_changed.emit()

    def _clear_shelf(self):
        self.store.clear_file_shelf()
        self.refresh()
        self.files_changed.emit()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self._drag_over = True
            event.acceptProposedAction()
            self.update()

    def dragLeaveEvent(self, event):
        self._drag_over = False
        self.update()

    def dropEvent(self, event):
        self._drag_over = False
        urls = event.mimeData().urls()
        added_any = False
        for url in urls:
            path = url.toLocalFile()
            if path and os.path.exists(path):
                if self.store.add_file_shelf_item(path):
                    added_any = True
        if added_any:
            self.refresh()
            self.files_changed.emit()
        event.acceptProposedAction()
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._drag_over:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
            painter.setPen(QPen(COLOR_PINK, 1.5, Qt.DashLine))
            painter.setBrush(QBrush(QColor(255, 138, 163, 25)))
            painter.drawRoundedRect(rect, 14, 14)



class NotchNotesWindow(QWidget):
    """
    Main NotchNotes floating / unfoldable window.
    """
    folded = Signal()
    unfolded = Signal()
    all_tasks_completed = Signal()

    def __init__(self, store: Optional[NotchNotesStore] = None, parent=None):
        super().__init__(parent)
        self.store = store or NotchNotesStore.get_instance()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._is_unfolded = True
        self._full_width = 390
        self._full_height = 520
        self._folded_height = 66
        self._drag_pos = None

        self.resize(self._full_width, self._full_height)
        self.setMinimumSize(320, 66)

        self._build_ui()
        self._load_current_scene()

        # Keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+N"), self, self._new_note_or_task)
        QShortcut(QKeySequence("Ctrl+W"), self, self.toggle_unfold)
        QShortcut(QKeySequence("Escape"), self, self.toggle_unfold)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        # Outer Glass Container
        self.container = QFrame(self)
        self.container.setObjectName("NotchNotesContainer")
        self.container.setStyleSheet("""
            QFrame#NotchNotesContainer {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #fffefc,
                    stop: 0.15 #fffaf5,
                    stop: 0.70 #fff5ee,
                    stop: 1 #fdf2e9
                );
                border: 1px solid #fed7cc;
                border-radius: 18px;
            }
        """)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # 1. Header Toolbar
        header_bar = QFrame()
        header_bar.setFixedHeight(46)
        header_bar.setStyleSheet("""
            background: rgba(255, 255, 255, 0.65);
            border-bottom: 1px solid #fed7cc;
            border-top-left-radius: 18px;
            border-top-right-radius: 18px;
        """)
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(14, 0, 12, 0)
        header_layout.setSpacing(8)

        # Notch Dot & Title
        title_box = QHBoxLayout()
        title_box.setSpacing(7)
        self.notch_dot = QLabel()
        self.notch_dot.setFixedSize(8, 8)
        self.notch_dot.setStyleSheet("background-color: #52c79b; border-radius: 4px;")
        title_box.addWidget(self.notch_dot)

        brand_title = QLabel("NotchNotes")
        b_font = QFont("Microsoft YaHei UI", 9)
        b_font.setBold(True)
        brand_title.setFont(b_font)
        brand_title.setStyleSheet("color: #2d2320; background: transparent;")
        title_box.addWidget(brand_title)
        header_layout.addLayout(title_box)

        header_layout.addSpacing(6)

        # Scene Switcher Pill
        self.scene_buttons = {}
        scene_row = QHBoxLayout()
        scene_row.setSpacing(4)
        for sc_id, sc_name in (("todo", "Todo"), ("notes", "Notes"), ("ideas", "Ideas")):
            btn = QPushButton(sc_name)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #7c6d66;
                    border: 0;
                    padding: 4px 10px;
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    color: #ff526c;
                    background: #ffeff0;
                }
                QPushButton:checked {
                    color: #ffffff;
                    background-color: #ff6b81;
                }
            """)
            btn.clicked.connect(lambda _checked=False, s=sc_id: self._switch_scene(s))
            self.scene_buttons[sc_id] = btn
            scene_row.addWidget(btn)
        header_layout.addLayout(scene_row)

        header_layout.addStretch(1)

        # Right actions: Pin, Fold
        self.pin_btn = PinButton(checked=self.store.pin_top)
        self.pin_btn.clicked.connect(self._toggle_pin)
        header_layout.addWidget(self.pin_btn)

        self.fold_btn = QPushButton("—")
        self.fold_btn.setFixedSize(26, 26)
        self.fold_btn.setCursor(Qt.PointingHandCursor)
        self.fold_btn.setToolTip("折叠便签 (Esc)")
        self.fold_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #7c6d66;
                border: 0;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background: #ffeff0;
                color: #ff526c;
            }
        """)
        self.fold_btn.clicked.connect(self.toggle_unfold)
        header_layout.addWidget(self.fold_btn)

        container_layout.addWidget(header_bar)

        # 2. Main Stacked Content Pages
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent; border: 0;")

        # Page 0: Todo Checklist
        self.todo_page = self._build_todo_page()
        self.stack.addWidget(self.todo_page)

        # Page 1: Notes Editor
        self.notes_page = self._build_notes_page("notes")
        self.stack.addWidget(self.notes_page)

        # Page 2: Ideas Editor
        self.ideas_page = self._build_notes_page("ideas")
        self.stack.addWidget(self.ideas_page)

        container_layout.addWidget(self.stack, 1)

        # 3. Bottom File Shelf
        self.file_shelf_widget = FileShelfWidget(self.store, self)
        container_layout.addWidget(self.file_shelf_widget)

        main_layout.addWidget(self.container)

    def _build_todo_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 12, 14, 8)
        layout.setSpacing(10)

        # Top Task Input Bar
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.todo_input = QLineEdit()
        self.todo_input.setPlaceholderText("+ 添加任务并回车...")
        self.todo_input.setStyleSheet("""
            QLineEdit {
                color: #2d2320;
                background-color: #ffffff;
                border: 1px solid #ebdcd2;
                border-radius: 8px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #ff8a9e;
                background-color: #ffffff;
            }
        """)
        self.todo_input.returnPressed.connect(self._add_todo_item)
        input_row.addWidget(self.todo_input, 1)

        # Stats Badge
        self.todo_stats_badge = QLabel("0/0")
        self.todo_stats_badge.setStyleSheet("""
            color: #ff526c;
            background-color: #ffeff0;
            border: 1px solid #ffccd3;
            border-radius: 8px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: bold;
        """)
        input_row.addWidget(self.todo_stats_badge)
        layout.addLayout(input_row)

        # Checklist Scroll Area
        self.todo_scroll = QScrollArea()
        self.todo_scroll.setWidgetResizable(True)
        self.todo_scroll.setFrameShape(QFrame.NoFrame)
        self.todo_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.todo_scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: 0; }
            QScrollBar:vertical {
                width: 5px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #e2d2c8;
                border-radius: 2.5px;
            }
        """)

        self.todo_list_container = QWidget()
        self.todo_list_container.setStyleSheet("background: transparent;")
        self.todo_list_layout = QVBoxLayout(self.todo_list_container)
        self.todo_list_layout.setContentsMargins(0, 0, 0, 0)
        self.todo_list_layout.setSpacing(6)
        self.todo_list_layout.setAlignment(Qt.AlignTop)
        self.todo_scroll.setWidget(self.todo_list_container)

        layout.addWidget(self.todo_scroll, 1)
        return page

    def _build_notes_page(self, scene_id: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(14, 10, 14, 8)
        layout.setSpacing(8)

        # Markdown Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(4)
        for tag, insert_str in (
            ("H1", "# "),
            ("H2", "## "),
            ("Bold", "**粗体**"),
            ("Italic", "*斜体*"),
            ("Code", "`代码`"),
            ("List", "- "),
            ("Task", "- [ ] "),
        ):
            b = QPushButton(tag)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet("""
                QPushButton {
                    background: #ffffff;
                    color: #55443d;
                    border: 1px solid #ebdcd2;
                    border-radius: 5px;
                    padding: 3px 7px;
                    font-size: 10px;
                    font-weight: 600;
                }
                QPushButton:hover {
                    background: #ffeff0;
                    color: #ff526c;
                    border-color: #ff8a9e;
                }
            """)
            b.clicked.connect(lambda _c=False, s=scene_id, ins=insert_str: self._insert_markdown(s, ins))
            toolbar.addWidget(b)
        toolbar.addStretch(1)

        # Export button
        export_btn = QPushButton("导出.md")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #ff526c;
                border: 0;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #d6304a;
            }
        """)
        export_btn.clicked.connect(lambda: self._export_markdown(scene_id))
        toolbar.addWidget(export_btn)
        layout.addLayout(toolbar)

        # Editor
        editor = QTextEdit()
        editor.setPlaceholderText("用 Markdown 随手记录灵感与备忘...")
        editor.setStyleSheet("""
            QTextEdit {
                color: #2d2320;
                background-color: #ffffff;
                border: 1px solid #ebdcd2;
                border-radius: 10px;
                padding: 10px 12px;
                font-family: "Microsoft YaHei UI", "Cascadia Code", Consolas, sans-serif;
                font-size: 12px;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border-color: #ff8a9e;
            }
            QScrollBar:vertical {
                width: 5px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #e2d2c8;
                border-radius: 2.5px;
            }
        """)
        editor.textChanged.connect(lambda: self._on_editor_text_changed(scene_id, editor))
        layout.addWidget(editor, 1)

        setattr(self, f"{scene_id}_editor", editor)
        return page

    # --- Scene Switching & Content Sync ---

    def _switch_scene(self, scene_id: str):
        self.store.current_scene_id = scene_id
        for sc, btn in self.scene_buttons.items():
            btn.setChecked(sc == scene_id)

        idx_map = {"todo": 0, "notes": 1, "ideas": 2}
        self.stack.setCurrentIndex(idx_map.get(scene_id, 0))

        dot_colors = {"todo": "#52c79b", "notes": "#70a1ff", "ideas": "#ff8aa3"}
        self.notch_dot.setStyleSheet(f"background-color: {dot_colors.get(scene_id, '#52c79b')}; border-radius: 4px;")

        if scene_id == "todo":
            self.refresh_todo_list()

    def _load_current_scene(self):
        cur = self.store.current_scene_id
        for sc in ("notes", "ideas"):
            editor = getattr(self, f"{sc}_editor", None)
            if editor:
                editor.blockSignals(True)
                editor.setPlainText(self.store.get_content(sc))
                editor.blockSignals(False)

        self._switch_scene(cur)

    # --- Todo Checklist Logic ---

    def refresh_todo_list(self):
        while self.todo_list_layout.count() > 0:
            child = self.todo_list_layout.takeAt(0)
            if child.widget():
                w = child.widget()
                w.setParent(None)
                w.deleteLater()

        items = self.store.parse_todo_items()
        done, total = self.store.get_todo_stats()
        self.todo_stats_badge.setText(f"{done}/{total}")

        if not items:
            empty = EmptyStateWidget(
                title="所有待办均已达成",
                subtitle="在上方输入框写下新计划，按回车开始记录~",
                dark_mode=False,
                parent=self,
            )
            self.todo_list_layout.addWidget(empty)
        else:
            for idx, item in enumerate(items):
                row = TodoItemWidget(idx, item["text"], item["checked"], self)
                row.toggled.connect(self._on_todo_item_toggled)
                row.deleted.connect(self._on_todo_item_deleted)
                self.todo_list_layout.addWidget(row)


    def _add_todo_item(self):
        text = self.todo_input.text().strip()
        if text:
            self.store.add_todo_item(text)
            self.todo_input.clear()
            self.refresh_todo_list()

    def _on_todo_item_toggled(self, idx: int):
        self.store.toggle_todo_item(idx)
        done, total = self.store.get_todo_stats()
        self.todo_stats_badge.setText(f"{done}/{total}")
        if total > 0 and done == total:
            self.all_tasks_completed.emit()

    def _on_todo_item_deleted(self, idx: int):
        self.store.remove_todo_item(idx)
        self.refresh_todo_list()

    # --- Markdown Editor Logic ---

    def _on_editor_text_changed(self, scene_id: str, editor: QTextEdit):
        self.store.set_content(scene_id, editor.toPlainText())

    def _insert_markdown(self, scene_id: str, tag: str):
        editor = getattr(self, f"{scene_id}_editor", None)
        if editor:
            cursor = editor.textCursor()
            cursor.insertText(tag)
            editor.setFocus()

    def _export_markdown(self, scene_id: str):
        content = self.store.get_content(scene_id)
        path, _ = QFileDialog.getSaveFileName(
            self,
            f"导出 {scene_id}.md",
            str(Path.home() / f"{scene_id}.md"),
            "Markdown Files (*.md);;Text Files (*.txt)",
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                print(f"Export error: {e}")

    def _new_note_or_task(self):
        if self.store.current_scene_id == "todo":
            self.todo_input.setFocus()
        else:
            editor = getattr(self, f"{self.store.current_scene_id}_editor", None)
            if editor:
                editor.append("\n\n")
                editor.setFocus()

    def _toggle_pin(self):
        pinned = self.pin_btn.isChecked()
        self.store.pin_top = pinned
        self.setWindowFlag(Qt.WindowStaysOnTopHint, pinned)
        self.show()

    # --- Unfold Animation & Dragging ---

    def toggle_unfold(self):
        if self._is_unfolded:
            self.fold_window()
        else:
            self.unfold_window()

    def fold_window(self):
        self._is_unfolded = False
        self.stack.hide()
        self.file_shelf_widget.hide()
        self.fold_btn.setText("+")
        self.fold_btn.setToolTip("展开便签")
        self.resize(self.width(), self._folded_height)
        self.folded.emit()

    def unfold_window(self):
        self._is_unfolded = True
        self.fold_btn.setText("—")
        self.fold_btn.setToolTip("折叠便签 (Esc)")
        self.resize(self.width(), self._full_height)
        self.stack.show()
        self.file_shelf_widget.show()
        self.unfolded.emit()

    # Window Dragging
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        super().mouseReleaseEvent(event)
