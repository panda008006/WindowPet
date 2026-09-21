import math
from typing import List, Optional, Tuple

from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QPoint,
    QPointF,
    QRect,
    QRectF,
    QSize,
    Qt,
    QTimer,
    Property,
    QPropertyAnimation,
    Signal,
)
from PySide6.QtGui import (
    QBrush,
    QColor,
    QCursor,
    QFont,
    QFontMetrics,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QPolygonF,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class PetCursorManager:
    """
    WindowPet Custom Cursor System:
    Provides themed cursors:
      - default_cursor: cute pastel arrow with mini pink paw print
      - pointer_cursor: 3D chibi cat paw pointing upward with pink beans
      - grab_cursor: open paw for sliders/draggable controls
      - grabbing_cursor: clutching paw while dragging
    """
    _default_cursor = None
    _pointer_cursor = None
    _grab_cursor = None
    _grabbing_cursor = None

    @classmethod
    def _find_asset(cls, filename: str) -> Optional[Path]:
        p1 = Path(__file__).resolve().parent.parent / "assets" / "UiAssets" / filename
        if p1.exists():
            return p1
        try:
            from window_pet_app.assets import resource_path
            p2 = resource_path(f"assets/UiAssets/{filename}")
            if p2.exists():
                return p2
        except Exception:
            pass
        return None

    @classmethod
    def default_cursor(cls) -> QCursor:
        if cls._default_cursor is None:
            p = cls._find_asset("cursor-default.png")
            if p and p.exists():
                cls._default_cursor = QCursor(QPixmap(str(p)), 9, 4)
            else:
                cls._default_cursor = QCursor(Qt.ArrowCursor)
        return cls._default_cursor

    @classmethod
    def pointer_cursor(cls) -> QCursor:
        if cls._pointer_cursor is None:
            p = cls._find_asset("cursor-pointer.png")
            if p and p.exists():
                cls._pointer_cursor = QCursor(QPixmap(str(p)), 9, 4)
            else:
                cls._pointer_cursor = QCursor(Qt.PointingHandCursor)
        return cls._pointer_cursor

    @classmethod
    def grab_cursor(cls) -> QCursor:
        if cls._grab_cursor is None:
            p = cls._find_asset("cursor-grab.png")
            if p and p.exists():
                cls._grab_cursor = QCursor(QPixmap(str(p)), 22, 22)
            else:
                cls._grab_cursor = QCursor(Qt.OpenHandCursor)
        return cls._grab_cursor

    @classmethod
    def grabbing_cursor(cls) -> QCursor:
        if cls._grabbing_cursor is None:
            p = cls._find_asset("cursor-grabbing.png")
            if p and p.exists():
                cls._grabbing_cursor = QCursor(QPixmap(str(p)), 22, 22)
            else:
                cls._grabbing_cursor = QCursor(Qt.ClosedHandCursor)
        return cls._grabbing_cursor

    @classmethod
    def apply_to_window(cls, widget: QWidget):
        if widget is not None:
            widget.setCursor(cls.default_cursor())


class SpringPushButton(QPushButton):
    """
    VibeHub Spring & Active Button:
    Subtle tactile physics spring feedback upon click.
    Shrinks to 0.95 on press, bounces back on release.
    """

    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self._scale: float = 1.0
        self.setCursor(PetCursorManager.pointer_cursor())

        self._anim = QPropertyAnimation(self, b"scaleFactor", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QEasingCurve.OutBack)

    def get_scale_factor(self) -> float:
        return self._scale

    def set_scale_factor(self, s: float):
        self._scale = s
        self.update()

    scaleFactor = Property(float, get_scale_factor, set_scale_factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._anim.stop()
            self._anim.setDuration(90)
            self._anim.setEasingCurve(QEasingCurve.OutQuad)
            self._anim.setStartValue(self._scale)
            self._anim.setEndValue(0.95)
            self._anim.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._anim.stop()
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutBack)
        self._anim.setStartValue(self._scale)
        self._anim.setEndValue(1.0)
        self._anim.start()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        if abs(self._scale - 1.0) < 0.001:
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        center = QPointF(self.width() / 2.0, self.height() / 2.0)
        painter.translate(center)
        painter.scale(self._scale, self._scale)
        painter.translate(-center)
        super().paintEvent(event)


class SegmentedControl(QWidget):
    """
    VibeHub Segmented Control:
    A capsule rail with a smoothly sliding active pill indicator,
    supporting light macaron or dark obsidian themes.
    """
    currentIndexChanged = Signal(int)
    currentKeyChanged = Signal(str)

    def __init__(
        self,
        items: List[Tuple[str, str]],  # List of (key, label)
        default_index: int = 0,
        dark_mode: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        normalized_items = []
        for it in (items or []):
            if isinstance(it, (tuple, list)) and len(it) >= 2:
                normalized_items.append((str(it[0]), str(it[1])))
            else:
                normalized_items.append((str(it), str(it)))
        self.items = normalized_items
        self._current_index = max(0, min(default_index, len(self.items) - 1)) if self.items else 0
        self.dark_mode = dark_mode
        self._indicator_x: float = 0.0
        self._target_indicator_x: float = 0.0
        self._hovered_index: int = -1

        self.setFixedHeight(38)
        self.setMinimumWidth(max(180, len(items) * 85))
        self.setCursor(PetCursorManager.pointer_cursor())

        self._slide_anim = QPropertyAnimation(self, b"indicatorX", self)
        self._slide_anim.setDuration(220)
        self._slide_anim.setEasingCurve(QEasingCurve.OutCubic)

        QTimer.singleShot(0, self._sync_initial_pos)

    def _sync_initial_pos(self):
        if self.items:
            w = (self.width() - 8) / len(self.items)
            self._indicator_x = 4 + self._current_index * w
            self.update()

    def get_indicator_x(self) -> float:
        return self._indicator_x

    def set_indicator_x(self, x: float):
        self._indicator_x = x
        self.update()

    indicatorX = Property(float, get_indicator_x, set_indicator_x)

    def currentIndex(self) -> int:
        return self._current_index

    def currentKey(self) -> str:
        if 0 <= self._current_index < len(self.items):
            return self.items[self._current_index][0]
        return ""

    def setCurrentIndex(self, index: int, emit: bool = True):
        if not (0 <= index < len(self.items)) or index == self._current_index:
            return
        self._current_index = index
        w = (self.width() - 8) / len(self.items)
        target = 4 + self._current_index * w

        self._slide_anim.stop()
        self._slide_anim.setStartValue(self._indicator_x)
        self._slide_anim.setEndValue(target)
        self._slide_anim.start()

        if emit:
            self.currentIndexChanged.emit(self._current_index)
            self.currentKeyChanged.emit(self.items[self._current_index][0])

    def set_current_key(self, key: str, emit: bool = False):
        for idx, item in enumerate(self.items):
            if item[0] == key:
                self.setCurrentIndex(idx, emit=emit)
                break

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.items:
            w = (self.width() - 8) / len(self.items)
            self._indicator_x = 4 + self._current_index * w

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.items:
            w = (self.width() - 8) / len(self.items)
            idx = int((event.position().x() - 4) // w)
            if 0 <= idx < len(self.items):
                self.setCurrentIndex(idx)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.items:
            w = (self.width() - 8) / len(self.items)
            idx = int((event.position().x() - 4) // w)
            if 0 <= idx < len(self.items) and idx != self._hovered_index:
                self._hovered_index = idx
                self.update()
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self._hovered_index = -1
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)

        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        r = rect.height() / 2.0

        # 1. Background Track
        if self.dark_mode:
            track_bg = QColor("#0d0f16")
            track_border = QColor(255, 255, 255, 22)
        else:
            track_bg = QColor("#edeaf5")
            track_border = QColor(215, 210, 230, 160)

        path = QPainterPath()
        path.addRoundedRect(rect, r, r)
        painter.fillPath(path, QBrush(track_bg))
        painter.setPen(QPen(track_border, 1.0))
        painter.drawPath(path)

        if not self.items:
            return

        item_w = (rect.width() - 6) / len(self.items)
        pill_h = rect.height() - 6
        pill_y = rect.top() + 3
        pill_r = pill_h / 2.0

        # 2. Sliding Active Pill
        pill_rect = QRectF(self._indicator_x, pill_y, item_w, pill_h)
        pill_path = QPainterPath()
        pill_path.addRoundedRect(pill_rect, pill_r, pill_r)

        if self.dark_mode:
            pill_bg = QLinearGradient(pill_rect.topLeft(), pill_rect.bottomLeft())
            pill_bg.setColorAt(0.0, QColor("#2a2d3c"))
            pill_bg.setColorAt(1.0, QColor("#1c1e29"))
            pill_border = QColor(255, 255, 255, 55)
        else:
            pill_bg = QLinearGradient(pill_rect.topLeft(), pill_rect.bottomLeft())
            pill_bg.setColorAt(0.0, QColor("#ffffff"))
            pill_bg.setColorAt(1.0, QColor("#f4f3fb"))
            pill_border = QColor(255, 255, 255, 255)

        painter.fillPath(pill_path, QBrush(pill_bg))
        painter.setPen(QPen(pill_border, 1.2))
        painter.drawPath(pill_path)

        # 3. Text Labels
        font = QFont("Microsoft YaHei UI", 9)
        font.setBold(True)
        painter.setFont(font)

        for i, (_k, label) in enumerate(self.items):
            item_rect = QRectF(rect.left() + 3 + i * item_w, pill_y, item_w, pill_h)
            is_active = (i == self._current_index)
            is_hover = (i == self._hovered_index and not is_active)

            if self.dark_mode:
                if is_active:
                    text_color = QColor("#b0eccf")
                elif is_hover:
                    text_color = QColor("#f5f5f6")
                else:
                    text_color = QColor(245, 245, 246, 130)
            else:
                if is_active:
                    text_color = QColor("#3559d8")
                elif is_hover:
                    text_color = QColor("#1a1c24")
                else:
                    text_color = QColor("#686f82")

            painter.setPen(text_color)
            painter.drawText(item_rect, Qt.AlignCenter, label)


class EmptyStateWidget(QFrame):
    """
    VibeHub Empty State:
    Friendly vector-drawn pet doodle, encouraging title,
    subtitle, and optional action call-to-action button.
    """

    def __init__(
        self,
        title: str = "暂无待办事项",
        subtitle: str = "在上方输入框写下第一个任务，回车开始记录吧~",
        action_text: Optional[str] = None,
        dark_mode: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.title_text = title
        self.subtitle_text = subtitle
        self.dark_mode = dark_mode
        self.action_clicked = Signal()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignCenter)

        # Custom Doodle canvas
        self.doodle = _EmptyPetDoodle(dark_mode=dark_mode, parent=self)
        layout.addWidget(self.doodle, 0, Qt.AlignCenter)

        self.title_label = QLabel(title)
        t_font = QFont("Microsoft YaHei UI", 10)
        t_font.setBold(True)
        self.title_label.setFont(t_font)
        self.title_label.setAlignment(Qt.AlignCenter)

        self.sub_label = QLabel(subtitle)
        self.sub_label.setFont(QFont("Microsoft YaHei UI", 8))
        self.sub_label.setAlignment(Qt.AlignCenter)
        self.sub_label.setWordWrap(True)

        if dark_mode:
            self.title_label.setStyleSheet("color: rgba(245, 245, 246, 0.85); background: transparent;")
            self.sub_label.setStyleSheet("color: rgba(245, 245, 246, 0.45); background: transparent;")
        else:
            self.title_label.setStyleSheet("color: #4b5260; background: transparent;")
            self.sub_label.setStyleSheet("color: #8c93a4; background: transparent;")

        layout.addWidget(self.title_label)
        layout.addWidget(self.sub_label)

        if action_text:
            self.btn = SpringPushButton(action_text)
            self.btn.setFixedHeight(28)
            if dark_mode:
                self.btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(176, 236, 207, 0.15);
                        color: #b0eccf;
                        border: 1px solid rgba(176, 236, 207, 0.35);
                        border-radius: 6px;
                        padding: 3px 12px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: rgba(176, 236, 207, 0.25);
                    }
                """)
            else:
                self.btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(53, 89, 216, 0.1);
                        color: #3559d8;
                        border: 1px solid rgba(53, 89, 216, 0.25);
                        border-radius: 6px;
                        padding: 3px 12px;
                        font-size: 11px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background: rgba(53, 89, 216, 0.2);
                    }
                """)
            layout.addWidget(self.btn, 0, Qt.AlignCenter)
        else:
            self.btn = None


class _EmptyPetDoodle(QWidget):
    """Clean vector drawing of a cute sleeping/waiting mascot."""

    def __init__(self, dark_mode: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.setFixedSize(72, 60)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing)

        color_body = QColor(255, 255, 255, 210) if self.dark_mode else QColor("#ffffff")
        color_line = QColor("#9bb8ff") if self.dark_mode else QColor("#7a8ebd")
        color_blush = QColor("#ffa7cc")

        pen = QPen(color_line, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(QBrush(color_body))

        # Pet head & body blob
        body_path = QPainterPath()
        body_path.addRoundedRect(QRectF(12, 16, 48, 38), 20, 20)
        painter.drawPath(body_path)

        # Ears
        ear_l = QPainterPath()
        ear_l.moveTo(18, 18)
        ear_l.quadTo(15, 6, 25, 12)
        ear_l.closeSubpath()
        painter.drawPath(ear_l)

        ear_r = QPainterPath()
        ear_r.moveTo(54, 18)
        ear_r.quadTo(57, 6, 47, 12)
        ear_r.closeSubpath()
        painter.drawPath(ear_r)

        # Sleeping eye curves: ^ ^
        painter.drawLine(24, 30, 28, 27)
        painter.drawLine(28, 27, 32, 30)

        painter.drawLine(40, 30, 44, 27)
        painter.drawLine(44, 27, 48, 30)

        # Tiny nose
        painter.setBrush(QBrush(color_line))
        painter.drawEllipse(QPointF(36, 33), 1.5, 1.5)

        # Cheerful blush dots
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(color_blush))
        painter.drawEllipse(QPointF(22, 35), 3, 2)
        painter.drawEllipse(QPointF(50, 35), 3, 2)

        # Floating 'z Z' sleep marks
        painter.setPen(QPen(color_blush, 1.3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(52, 12, 57, 12)
        painter.drawLine(57, 12, 52, 17)
        painter.drawLine(52, 17, 57, 17)


class PopconfirmBubble(QWidget):
    """
    VibeHub Popconfirm & Popover:
    A lightweight, non-modal confirmation bubble that anchors right above
    or below a target button, preventing destructive accidents gracefully.
    """
    confirmed = Signal()
    cancelled = Signal()

    def __init__(
        self,
        target_widget: QWidget,
        message: str = "确定执行此操作吗？",
        confirm_text: str = "确定",
        cancel_text: str = "取消",
        dark_mode: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.target_widget = target_widget
        self.message = message
        self.dark_mode = dark_mode

        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

        self._build_ui(confirm_text, cancel_text)

    def _build_ui(self, confirm_text: str, cancel_text: str):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(6, 6, 6, 6)
        outer_layout.setSpacing(0)

        # Card container
        self.card = QFrame()
        self.card.setObjectName("PopconfirmCard")
        if self.dark_mode:
            self.card.setStyleSheet("""
                QFrame#PopconfirmCard {
                    background-color: #151722;
                    border: 1px solid rgba(255, 255, 255, 0.18);
                    border-radius: 12px;
                }
            """)
        else:
            self.card.setStyleSheet("""
                QFrame#PopconfirmCard {
                    background-color: #ffffff;
                    border: 1px solid rgba(100, 110, 140, 0.22);
                    border-radius: 12px;
                }
            """)

        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(14, 12, 14, 12)
        card_layout.setSpacing(10)

        # Message row with warning dot
        msg_row = QHBoxLayout()
        msg_row.setSpacing(8)
        dot = QLabel("●")
        dot.setStyleSheet("color: #ff526c; font-size: 11px; background: transparent;")
        msg_row.addWidget(dot)

        lbl = QLabel(self.message)
        lbl.setFont(QFont("Microsoft YaHei UI", 9))
        if self.dark_mode:
            lbl.setStyleSheet("color: #f5f5f6; background: transparent;")
        else:
            lbl.setStyleSheet("color: #1c1e28; background: transparent;")
        msg_row.addWidget(lbl)
        card_layout.addLayout(msg_row)

        # Button row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_row.addStretch(1)

        cancel_btn = SpringPushButton(cancel_text)
        cancel_btn.setFixedHeight(24)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: rgba(120, 125, 140, 0.9);
                border: 1px solid rgba(120, 125, 140, 0.25);
                border-radius: 5px;
                padding: 2px 10px;
                font-size: 10px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: rgba(120, 125, 140, 0.12);
            }
        """)
        cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(cancel_btn)

        confirm_btn = SpringPushButton(confirm_text)
        confirm_btn.setFixedHeight(24)
        confirm_btn.setStyleSheet("""
            QPushButton {
                background: #ff526c;
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 2px 10px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #ff6b81;
            }
        """)
        confirm_btn.clicked.connect(self._on_confirm)
        btn_row.addWidget(confirm_btn)

        card_layout.addLayout(btn_row)
        outer_layout.addWidget(self.card)

    def show_above_target(self):
        self.adjustSize()
        target_pt = self.target_widget.mapToGlobal(QPoint(0, 0))
        # Center horizontally above target
        target_center_x = target_pt.x() + self.target_widget.width() / 2
        pop_x = int(target_center_x - self.width() / 2)
        pop_y = int(target_pt.y() - self.height() - 4)

        # Boundary adjustments
        screen = QApplication.primaryScreen()
        if screen:
            geom = screen.availableGeometry()
            if pop_x < geom.left() + 10:
                pop_x = geom.left() + 10
            elif pop_x + self.width() > geom.right() - 10:
                pop_x = geom.right() - self.width() - 10
            if pop_y < geom.top() + 10:
                # If cannot show above, show below
                pop_y = int(target_pt.y() + self.target_widget.height() + 4)

        self.move(pop_x, pop_y)
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_confirm(self):
        self.confirmed.emit()
        self.close()

    def _on_cancel(self):
        self.cancelled.emit()
        self.close()


class VibeButton(SpringPushButton):
    """
    VibeHub 标志性多态微物理弹性按钮：
    支持 primary / secondary / danger / ghost 四种美学变体，
    内置 3D 黏土柔光倒角、前缀图标支持与触觉微弹性回弹。
    """

    def __init__(
        self,
        text: str = "",
        variant: str = "primary",
        icon_path: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(text, parent)
        self.variant = variant
        self._hovered = False
        self._icon_pixmap: Optional[QPixmap] = None
        if icon_path:
            p = QPixmap(str(icon_path))
            if not p.isNull():
                self._icon_pixmap = p

        self.setMinimumHeight(38)
        self.setFont(QFont("Microsoft YaHei UI", 10, QFont.Bold))
        self.setAttribute(Qt.WA_Hover, True)

    def set_icon_path(self, icon_path: str):
        p = QPixmap(str(icon_path))
        if not p.isNull():
            self._icon_pixmap = p
            self.update()

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
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)

        # Apply Spring Scale
        if abs(self._scale - 1.0) > 0.001:
            center = QPointF(self.width() / 2.0, self.height() / 2.0)
            painter.translate(center)
            painter.scale(self._scale, self._scale)
            painter.translate(-center)

        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        r = 14.0  # 胶囊/圆角气质

        # Colors by variant
        if self.variant == "primary":
            grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            if self.isDown():
                grad.setColorAt(0.0, QColor("#eb5968"))
                grad.setColorAt(1.0, QColor("#d93f4e"))
            elif self._hovered:
                grad.setColorAt(0.0, QColor("#ff8f96"))
                grad.setColorAt(1.0, QColor("#ff6372"))
            else:
                grad.setColorAt(0.0, QColor("#ff7f87"))
                grad.setColorAt(1.0, QColor("#ff5866"))
            pen = QPen(QColor(255, 255, 255, 120), 1.2)
            text_color = QColor("#ffffff")
        elif self.variant == "danger":
            grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            if self.isDown():
                grad.setColorAt(0.0, QColor("#d92534"))
                grad.setColorAt(1.0, QColor("#b81422"))
            elif self._hovered:
                grad.setColorAt(0.0, QColor("#ff5765"))
                grad.setColorAt(1.0, QColor("#eb3141"))
            else:
                grad.setColorAt(0.0, QColor("#ff4757"))
                grad.setColorAt(1.0, QColor("#e02839"))
            pen = QPen(QColor(255, 255, 255, 100), 1.2)
            text_color = QColor("#ffffff")
        elif self.variant == "secondary":
            grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
            if self.isDown():
                grad.setColorAt(0.0, QColor("#f4ece6"))
                grad.setColorAt(1.0, QColor("#e8ded6"))
            elif self._hovered:
                grad.setColorAt(0.0, QColor("#ffffff"))
                grad.setColorAt(1.0, QColor("#fdf3ed"))
            else:
                grad.setColorAt(0.0, QColor("#ffffff"))
                grad.setColorAt(1.0, QColor("#fbf7f4"))
            pen = QPen(QColor("#e2d3cb" if not self._hovered else "#ff9aa2"), 1.4)
            text_color = QColor("#2d3748")
        else:  # ghost
            bg_col = QColor(0, 0, 0, 16 if self._hovered else 0)
            grad = QBrush(bg_col)
            pen = Qt.NoPen
            text_color = QColor("#ff7f87" if self._hovered else "#718096")

        # Background Fill
        painter.setPen(pen)
        painter.setBrush(grad)
        painter.drawRoundedRect(rect, r, r)

        # Inner Top Bevel for Claymorphic Touch (primary/secondary)
        if self.variant in ("primary", "secondary") and not self.isDown():
            bevel = QPainterPath()
            bevel.addRoundedRect(rect.adjusted(1, 1, -1, -rect.height() / 2), r - 1, r - 1)
            b_grad = QLinearGradient(rect.topLeft(), QPointF(rect.left(), rect.center().y()))
            b_grad.setColorAt(0.0, QColor(255, 255, 255, 80 if self.variant == "primary" else 160))
            b_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(b_grad)
            painter.drawPath(bevel)

        # Content: Icon + Text
        text = self.text()
        metrics = painter.fontMetrics()
        text_w = metrics.horizontalAdvance(text)
        has_icon = self._icon_pixmap is not None and not self._icon_pixmap.isNull()
        icon_size = 20
        gap = 8 if has_icon and text else 0

        total_w = text_w + (icon_size + gap if has_icon else 0)
        start_x = rect.center().x() - total_w / 2.0

        if has_icon:
            icon_rect = QRectF(start_x, rect.center().y() - icon_size / 2.0, icon_size, icon_size)
            scaled = self._icon_pixmap.scaled(
                icon_size * 2, icon_size * 2, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            painter.drawPixmap(icon_rect.toRect(), scaled)
            start_x += icon_size + gap

        if text:
            painter.setPen(text_color)
            painter.setFont(self.font())
            text_rect = QRectF(start_x, rect.top(), text_w + 4, rect.height())
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, text)


class VibeInput(QFrame):
    """
    VibeHub 前端发光前缀输入框：
    支持左侧 3D 萌系前缀小图标（邮箱/密码/验证码/搜索）、
    聚焦时柔和外发光光晕（Focus Ambient Glow）、
    一键清空按钮以及圆润粘土边框。
    """

    textChanged = Signal(str)
    returnPressed = Signal()

    def __init__(
        self,
        placeholder: str = "",
        icon_path: Optional[str] = None,
        is_password: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._glow_alpha: float = 0.0
        self._focused: bool = False

        self.setObjectName("VibeInputField")
        self.setFixedHeight(44)
        self.setCursor(Qt.IBeamCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        # Prefix Icon
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(26, 26)
        self.icon_label.setAlignment(Qt.AlignCenter)
        if icon_path:
            self.set_icon(icon_path)
        else:
            self.icon_label.hide()
        layout.addWidget(self.icon_label)

        # Line Edit
        from PySide6.QtWidgets import QLineEdit
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText(placeholder)
        if is_password:
            self.line_edit.setEchoMode(QLineEdit.Password)
        self.line_edit.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: #26334a;
                font-family: 'Microsoft YaHei UI';
                font-size: 13px;
                font-weight: 500;
                selection-background-color: #ffccd2;
                selection-color: #26334a;
            }
        """)
        self.line_edit.textChanged.connect(self._on_text_changed)
        self.line_edit.returnPressed.connect(self.returnPressed)
        self.line_edit.installEventFilter(self)
        layout.addWidget(self.line_edit, 1)

        # Clear Button
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setFixedSize(20, 20)
        self.clear_btn.setCursor(PetCursorManager.pointer_cursor())
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background: rgba(180, 190, 205, 0.25);
                color: #718096;
                border: none;
                border-radius: 10px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 90, 105, 0.85);
                color: #ffffff;
            }
        """)
        self.clear_btn.clicked.connect(self.clear)
        self.clear_btn.hide()
        layout.addWidget(self.clear_btn)

        # Glow Animation
        self._glow_anim = QPropertyAnimation(self, b"glowAlpha", self)
        self._glow_anim.setDuration(180)
        self._glow_anim.setEasingCurve(QEasingCurve.OutCubic)

    def get_glow_alpha(self) -> float:
        return self._glow_alpha

    def set_glow_alpha(self, v: float):
        self._glow_alpha = v
        self.update()

    glowAlpha = Property(float, get_glow_alpha, set_glow_alpha)

    def set_icon(self, icon_path: str):
        pm = QPixmap(str(icon_path))
        if not pm.isNull():
            self.icon_label.setPixmap(
                pm.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            self.icon_label.show()
        else:
            self.icon_label.hide()

    def text(self) -> str:
        return self.line_edit.text()

    def setText(self, val: str):
        self.line_edit.setText(val)

    def clear(self):
        self.line_edit.clear()

    def setPlaceholderText(self, text: str):
        self.line_edit.setPlaceholderText(text)

    def setEchoMode(self, mode):
        self.line_edit.setEchoMode(mode)

    def eventFilter(self, obj, event):
        if obj == self.line_edit:
            t = event.type()
            if t in (QEvent.FocusIn, getattr(QEvent.Type, "FocusIn", None)):
                self._focused = True
                self._glow_anim.stop()
                self._glow_anim.setStartValue(self._glow_alpha)
                self._glow_anim.setEndValue(1.0)
                self._glow_anim.start()
            elif t in (QEvent.FocusOut, getattr(QEvent.Type, "FocusOut", None)):
                self._focused = False
                self._glow_anim.stop()
                self._glow_anim.setStartValue(self._glow_alpha)
                self._glow_anim.setEndValue(0.0)
                self._glow_anim.start()
        return super().eventFilter(obj, event)

    def _on_text_changed(self, text: str):
        self.clear_btn.setVisible(bool(text))
        self.textChanged.emit(text)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        rect = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        r = 13.0

        # Background Fill
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#ffffff"))
        painter.drawRoundedRect(rect, r, r)

        # Glow Ring on Focus
        if self._glow_alpha > 0.001:
            glow_color = QColor(255, 127, 135, int(110 * self._glow_alpha))
            glow_pen = QPen(glow_color, 2.4)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect.adjusted(-0.5, -0.5, 0.5, 0.5), r, r)

        # Base Border
        border_col = QColor("#ff99a2" if self._focused else "#ddd4cc")
        painter.setPen(QPen(border_col, 1.4 if self._focused else 1.1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, r, r)


class VibeSwitch(QWidget):
    """
    VibeHub iOS 拟态双色药丸微弹性拨钮开关：
    50x28 紧凑跑道，切换时带微弹性质感拉伸。
    """

    toggled = Signal(bool)

    def __init__(self, checked: bool = False, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._checked: bool = checked
        self._knob_pos: float = 1.0 if checked else 0.0
        self.setFixedSize(50, 28)
        self.setCursor(PetCursorManager.pointer_cursor())

        self._anim = QPropertyAnimation(self, b"knobPos", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutBack)

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, val: bool):
        if self._checked != val:
            self._checked = val
            self._anim.stop()
            self._anim.setStartValue(self._knob_pos)
            self._anim.setEndValue(1.0 if val else 0.0)
            self._anim.start()
            self.toggled.emit(val)

    def get_knob_pos(self) -> float:
        return self._knob_pos

    def set_knob_pos(self, v: float):
        self._knob_pos = v
        self.update()

    knobPos = Property(float, get_knob_pos, set_knob_pos)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        r = rect.height() / 2.0

        # Background track color interpolates between #dbe0ea and #ff7f87
        off_col = QColor("#dbe0ea")
        on_col = QColor("#ff7f87")
        t = max(0.0, min(1.0, self._knob_pos))
        cur_r = int(off_col.red() + (on_col.red() - off_col.red()) * t)
        cur_g = int(off_col.green() + (on_col.green() - off_col.green()) * t)
        cur_b = int(off_col.blue() + (on_col.blue() - off_col.blue()) * t)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(cur_r, cur_g, cur_b))
        painter.drawRoundedRect(rect, r, r)

        # Sliding Knob
        knob_d = rect.height() - 4
        travel = rect.width() - 4 - knob_d
        knob_x = rect.left() + 2 + travel * self._knob_pos
        knob_rect = QRectF(knob_x, rect.top() + 2, knob_d, knob_d)

        # Knob shadow
        painter.setBrush(QColor(0, 0, 0, 30))
        painter.drawEllipse(knob_rect.adjusted(0, 1.5, 0, 1.5))

        # Knob circle
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(knob_rect)


class VibeLink(QLabel):
    """
    VibeHub 前端交互链接：
    支持悬停平滑展开下划线与柔粉微光变色。
    """

    clicked = Signal()

    def __init__(self, text: str = "", parent: Optional[QWidget] = None):
        super().__init__(text, parent)
        self._hover_progress: float = 0.0
        self.setCursor(PetCursorManager.pointer_cursor())
        self.setFont(QFont("Microsoft YaHei UI", 9, QFont.Medium))
        self.setStyleSheet("background: transparent; padding: 2px 4px;")

        self._anim = QPropertyAnimation(self, b"hoverProgress", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def get_hover_progress(self) -> float:
        return self._hover_progress

    def set_hover_progress(self, v: float):
        self._hover_progress = v
        self.update()

    hoverProgress = Property(float, get_hover_progress, set_hover_progress)

    def enterEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._hover_progress)
        self._anim.setEndValue(1.0)
        self._anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._anim.stop()
        self._anim.setStartValue(self._hover_progress)
        self._anim.setEndValue(0.0)
        self._anim.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._hover_progress > 0.01:
            painter = QPainter(self)
            painter.setRenderHints(QPainter.Antialiasing)
            metrics = self.fontMetrics()
            text_w = metrics.horizontalAdvance(self.text())
            cur_w = text_w * self._hover_progress
            y = self.height() - 2
            x = 4 + (text_w - cur_w) / 2.0
            painter.setPen(QPen(QColor(255, 127, 135, int(220 * self._hover_progress)), 2, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(x, y), QPointF(x + cur_w, y))


class VibeToast(QWidget):
    """
    VibeHub 轻量非阻塞浮动提示 Toast：
    在窗口顶部优雅滑入，显示温馨反馈文案，2.2秒后平滑淡出，替代阻塞式弹窗。
    """

    def __init__(self, message: str, parent: QWidget, icon_type: str = "success"):
        super().__init__(parent)
        self.setWindowFlags(Qt.SubWindow | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)

        self._opacity: float = 0.0
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(10)

        # Icon
        icon_str = "✓" if icon_type == "success" else "ℹ"
        icon_lbl = QLabel(icon_str)
        icon_lbl.setFont(QFont("Microsoft YaHei UI", 11, QFont.Bold))
        icon_lbl.setStyleSheet(
            "color: #10b981;" if icon_type == "success" else "color: #ff7f87;"
        )
        layout.addWidget(icon_lbl)

        # Message
        msg_lbl = QLabel(message)
        msg_lbl.setFont(QFont("Microsoft YaHei UI", 10, QFont.Bold))
        msg_lbl.setStyleSheet("color: #1f2937;")
        layout.addWidget(msg_lbl)

        self.adjustSize()
        self._anim = QPropertyAnimation(self, b"toastOpacity", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

        # Reposition to top center of parent
        self._reposition()

        # Timer to auto-hide
        QTimer.singleShot(2400, self._fade_out)

    def _reposition(self):
        parent = self.parentWidget()
        if parent:
            px = int((parent.width() - self.width()) / 2.0)
            py = 28
            self.move(px, py)

    def get_toast_opacity(self) -> float:
        return self._opacity

    def set_toast_opacity(self, v: float):
        self._opacity = v
        self.setWindowOpacity(v)
        self.update()

    toastOpacity = Property(float, get_toast_opacity, set_toast_opacity)

    def show_toast(self):
        self.show()
        self.raise_()
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()

    def _fade_out(self):
        self._anim.stop()
        self._anim.setStartValue(self._opacity)
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(self.close)
        self._anim.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        r = rect.height() / 2.0

        # Clay shadow & pill fill
        painter.setPen(QPen(QColor("#f0e6e0"), 1.2))
        painter.setBrush(QColor(255, 255, 255, 245))
        painter.drawRoundedRect(rect, r, r)


class VibeSlider(QSlider):
    """
    VibeHub Dynamic Micro-Interactive Slider:
    - Smooth pastel gradient active track
    - Spring-animated expanding thumb upon hover
    - Ripple/halo glow when dragging
    - Live floating value pill tooltip above thumb
    - Tactile click-to-jump with spring feedback
    - Custom grab/grabbing pet cursors
    """
    def __init__(
        self,
        orientation=Qt.Horizontal,
        parent=None,
        unit: str = "%",
        color_variant: str = "coral", # "coral" or "mint"
    ):
        super().__init__(orientation, parent)
        self.unit = unit
        self.color_variant = color_variant
        self.setFixedHeight(46)
        self.setCursor(PetCursorManager.grab_cursor())

        self._thumb_radius: float = 9.5
        self._bubble_opacity: float = 0.0
        self._dragging: bool = False
        self._hovered: bool = False

        # Animations
        self._thumb_anim = QPropertyAnimation(self, b"thumbRadius", self)
        self._thumb_anim.setDuration(180)
        self._thumb_anim.setEasingCurve(QEasingCurve.OutBack)

        self._bubble_anim = QPropertyAnimation(self, b"bubbleOpacity", self)
        self._bubble_anim.setDuration(160)
        self._bubble_anim.setEasingCurve(QEasingCurve.OutCubic)

    def get_thumb_radius(self) -> float:
        return self._thumb_radius

    def set_thumb_radius(self, r: float):
        self._thumb_radius = r
        self.update()

    thumbRadius = Property(float, get_thumb_radius, set_thumb_radius)

    def get_bubble_opacity(self) -> float:
        return self._bubble_opacity

    def set_bubble_opacity(self, o: float):
        self._bubble_opacity = o
        self.update()

    bubbleOpacity = Property(float, get_bubble_opacity, set_bubble_opacity)

    def enterEvent(self, event):
        self._hovered = True
        self.setCursor(PetCursorManager.grab_cursor())
        self._thumb_anim.stop()
        self._thumb_anim.setStartValue(self._thumb_radius)
        self._thumb_anim.setEndValue(13.5)
        self._thumb_anim.start()

        self._bubble_anim.stop()
        self._bubble_anim.setStartValue(self._bubble_opacity)
        self._bubble_anim.setEndValue(1.0)
        self._bubble_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        if not self._dragging:
            self._thumb_anim.stop()
            self._thumb_anim.setStartValue(self._thumb_radius)
            self._thumb_anim.setEndValue(9.5)
            self._thumb_anim.start()

            self._bubble_anim.stop()
            self._bubble_anim.setStartValue(self._bubble_opacity)
            self._bubble_anim.setEndValue(0.0)
            self._bubble_anim.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = True
            self.setCursor(PetCursorManager.grabbing_cursor())
            self._update_val_from_mouse(event.pos().x())
            self._bubble_anim.stop()
            self._bubble_anim.setStartValue(self._bubble_opacity)
            self._bubble_anim.setEndValue(1.0)
            self._bubble_anim.start()
            self.update()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._update_val_from_mouse(event.pos().x())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._dragging = False
            self.setCursor(PetCursorManager.grab_cursor() if self._hovered else PetCursorManager.default_cursor())
            if not self._hovered:
                self._thumb_anim.stop()
                self._thumb_anim.setStartValue(self._thumb_radius)
                self._thumb_anim.setEndValue(9.5)
                self._thumb_anim.start()

                self._bubble_anim.stop()
                self._bubble_anim.setStartValue(self._bubble_opacity)
                self._bubble_anim.setEndValue(0.0)
                self._bubble_anim.start()
            self.update()
        super().mouseReleaseEvent(event)

    def _update_val_from_mouse(self, mouse_x: int):
        pad = 20
        available_w = max(1, self.width() - pad * 2)
        ratio = max(0.0, min(1.0, (mouse_x - pad) / available_w))
        val = int(round(self.minimum() + ratio * (self.maximum() - self.minimum())))
        step = self.singleStep() or 1
        val = round(val / step) * step
        self.setValue(val)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)

        pad = 20
        track_h = 7.0
        cy = float(self.height() - 15.0) # track in lower portion, leaving top for bubble
        track_rect = QRectF(pad, cy - track_h / 2.0, self.width() - pad * 2, track_h)

        # Track background (inactive)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#e8edf2"))
        painter.drawRoundedRect(track_rect, track_h / 2.0, track_h / 2.0)

        # Value progress
        val_range = max(1, self.maximum() - self.minimum())
        ratio = max(0.0, min(1.0, (self.value() - self.minimum()) / val_range))
        thumb_x = pad + ratio * track_rect.width()

        active_rect = QRectF(track_rect.left(), track_rect.top(), thumb_x - track_rect.left(), track_h)
        if active_rect.width() > 0:
            grad = QLinearGradient(active_rect.left(), 0, active_rect.right(), 0)
            if self.color_variant == "mint":
                grad.setColorAt(0.0, QColor("#63e6be"))
                grad.setColorAt(1.0, QColor("#20c997"))
            else:
                grad.setColorAt(0.0, QColor("#ffa8ba"))
                grad.setColorAt(1.0, QColor("#ff6b81"))
            painter.setBrush(QBrush(grad))
            painter.drawRoundedRect(active_rect, track_h / 2.0, track_h / 2.0)

        # Dragging Glow Halo
        if self._dragging:
            halo_r = self._thumb_radius + 6.0
            painter.setPen(Qt.NoPen)
            halo_color = QColor(255, 107, 129, 65) if self.color_variant != "mint" else QColor(32, 201, 151, 65)
            painter.setBrush(halo_color)
            painter.drawEllipse(QPointF(thumb_x, cy), halo_r, halo_r)

        # Thumb Soft Shadow
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(60, 30, 40, 40))
        painter.drawEllipse(QPointF(thumb_x, cy + 2.0), self._thumb_radius, self._thumb_radius)

        # Thumb Body (Ceramic white with gradient border)
        t_grad = QLinearGradient(thumb_x - self._thumb_radius, cy - self._thumb_radius, thumb_x + self._thumb_radius, cy + self._thumb_radius)
        t_grad.setColorAt(0.0, QColor("#ffffff"))
        t_grad.setColorAt(1.0, QColor("#fff9f8"))
        painter.setBrush(QBrush(t_grad))

        border_color = QColor("#ff6b81") if self.color_variant != "mint" else QColor("#20c997")
        painter.setPen(QPen(border_color, 2.4))
        painter.drawEllipse(QPointF(thumb_x, cy), self._thumb_radius, self._thumb_radius)

        # Cute Inner Core
        core_r = max(2.5, self._thumb_radius - 6.5)
        painter.setPen(Qt.NoPen)
        painter.setBrush(border_color)
        painter.drawEllipse(QPointF(thumb_x, cy), core_r, core_r)

        # Floating Value Bubble (Tooltip)
        if self._bubble_opacity > 0.02:
            alpha = int(240 * self._bubble_opacity)
            bubble_w = 46.0
            bubble_h = 18.0
            bx = max(4.0, min(float(self.width() - bubble_w - 4.0), thumb_x - bubble_w / 2.0))
            by = max(2.0, cy - self._thumb_radius - bubble_h - 2.5)

            # Bubble background pill
            b_rect = QRectF(bx, by, bubble_w, bubble_h)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(45, 55, 72, alpha))
            painter.drawRoundedRect(b_rect, 5.0, 5.0)

            # Little triangle pointer below pill
            tri = QPainterPath()
            tri.moveTo(thumb_x - 3.5, by + bubble_h)
            tri.lineTo(thumb_x + 3.5, by + bubble_h)
            tri.lineTo(thumb_x, by + bubble_h + 2.5)
            tri.closeSubpath()
            painter.drawPath(tri)

            # Bubble text
            painter.setPen(QColor(255, 255, 255, alpha))
            font = painter.font()
            font.setFamily("Microsoft YaHei UI")
            font.setBold(True)
            font.setPointSize(8)
            painter.setFont(font)
            val_text = f"{self.value()}{self.unit}"
            painter.drawText(b_rect, Qt.AlignCenter, val_text)


class TimeDigitSlot(QWidget):
    """
    Interactive digit slot for hours or minutes in VibeTimePicker:
    - Displays 2-digit formatted number (e.g. 05, 30)
    - Hoverable with soft pastel background & coral border
    - Clickable top-half (increment) and bottom-half (decrement) with visual chevrons
    - Mouse wheel support (scroll up to increment, scroll down to decrement)
    """
    valueChanged = Signal(int)

    def __init__(self, value: int = 0, min_val: int = 0, max_val: int = 59, step: int = 1, parent=None):
        super().__init__(parent)
        self._value = value
        self._min_val = min_val
        self._max_val = max_val
        self._step = step
        self._hovered = False
        self._active_half = 0  # 1 = top (up), -1 = bottom (down), 0 = none
        self.setFixedSize(54, 52)
        self.setCursor(PetCursorManager.pointer_cursor())
        self.setFocusPolicy(Qt.StrongFocus)

    def value(self) -> int:
        return self._value

    def setValue(self, val: int):
        clamped = max(self._min_val, min(self._max_val, val))
        if clamped != self._value:
            self._value = clamped
            self.update()
            self.valueChanged.emit(self._value)

    def step_up(self):
        new_val = self._value + self._step
        if new_val > self._max_val:
            new_val = self._min_val
        self.setValue(new_val)

    def step_down(self):
        new_val = self._value - self._step
        if new_val < self._min_val:
            new_val = self._max_val
        self.setValue(new_val)

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._active_half = 0
        self.update()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        half = 1 if event.pos().y() < self.height() / 2 else -1
        if half != self._active_half:
            self._active_half = half
            self.update()
        super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.step_up()
        elif delta < 0:
            self.step_down()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if event.pos().y() < self.height() / 2:
                self.step_up()
            else:
                self.step_down()
            event.accept()
        else:
            super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Up, Qt.Key_Right):
            self.step_up()
            event.accept()
        elif event.key() in (Qt.Key_Down, Qt.Key_Left):
            self.step_down()
            event.accept()
        else:
            super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        rect = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)

        # Background ceramic capsule
        bg_color = QColor("#fff8f6") if self._hovered else QColor("#ffffff")
        border_color = QColor("#ff94a4") if self._hovered else QColor("#ffd2d8")
        
        painter.setPen(QPen(border_color, 1.6))
        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect, 12, 12)

        # Draw micro stepper indicator arrows
        cx = rect.center().x()
        
        # Up chevron
        uy = rect.top() + 8
        up_color = QColor("#ff526c") if (self._hovered and self._active_half == 1) else (QColor("#ff94a4") if self._hovered else QColor("#cbd5e1"))
        painter.setPen(QPen(up_color, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(cx - 4.5, uy + 2.5), QPointF(cx, uy))
        painter.drawLine(QPointF(cx, uy), QPointF(cx + 4.5, uy + 2.5))

        # Down chevron
        dy = rect.bottom() - 8
        down_color = QColor("#ff526c") if (self._hovered and self._active_half == -1) else (QColor("#ff94a4") if self._hovered else QColor("#cbd5e1"))
        painter.setPen(QPen(down_color, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawLine(QPointF(cx - 4.5, dy - 2.5), QPointF(cx, dy))
        painter.drawLine(QPointF(cx, dy), QPointF(cx + 4.5, dy - 2.5))

        # Draw 2-digit number
        painter.setPen(QPen(QColor("#1e293b")))
        font = QFont("Segoe UI", 16, QFont.Bold)
        painter.setFont(font)
        digit_rect = QRectF(rect.left(), rect.top() + 4, rect.width(), rect.height() - 8)
        painter.drawText(digit_rect, Qt.AlignCenter, f"{self._value:02d}")


class VibeTimePicker(QWidget):
    """
    VibeHub Modern Tactile Time Picker:
    - Dual interactive slots for Hours & Minutes
    - Breathing separator pill ':'
    - Quick Preset Duration Chips (e.g. 15m, 30m, 45m, 1h, 2h)
    - Full QSpinBox compatible API: value(), setValue(), setRange(), valueChanged, setSingleStep, setSuffix, setKeyboardTracking
    """
    valueChanged = Signal(int)

    def __init__(self, default_minutes: int = 30, presets: Optional[List[int]] = None, parent=None):
        super().__init__(parent)
        self._min_minutes = 1
        self._max_minutes = 24 * 60
        self._presets = presets if presets is not None else [15, 30, 45, 60, 90, 120]
        
        default_minutes = max(self._min_minutes, min(self._max_minutes, default_minutes))
        h = default_minutes // 60
        m = default_minutes % 60

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # Trigger / Slot Row
        trigger_row = QHBoxLayout()
        trigger_row.setSpacing(8)
        trigger_row.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # Hours slot
        self.hour_slot = TimeDigitSlot(value=h, min_val=0, max_val=23, step=1)
        self.hour_slot.valueChanged.connect(self._on_slot_changed)
        trigger_row.addWidget(self.hour_slot)

        hour_lbl = QLabel("时")
        hour_lbl.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 600;")
        trigger_row.addWidget(hour_lbl)

        # Colon / Breathing Separator
        sep_lbl = QLabel(":")
        sep_lbl.setStyleSheet("color: #ff758c; font-size: 18px; font-weight: 800; padding: 0 2px;")
        trigger_row.addWidget(sep_lbl)

        # Minutes slot
        self.min_slot = TimeDigitSlot(value=m, min_val=0, max_val=59, step=5)
        self.min_slot.valueChanged.connect(self._on_slot_changed)
        trigger_row.addWidget(self.min_slot)

        min_lbl = QLabel("分")
        min_lbl.setStyleSheet("color: #64748b; font-size: 13px; font-weight: 600;")
        trigger_row.addWidget(min_lbl)

        trigger_row.addStretch(1)
        main_layout.addLayout(trigger_row)

        # Presets Chips Row
        if self._presets:
            chips_layout = QHBoxLayout()
            chips_layout.setSpacing(6)
            chips_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self._preset_buttons = []
            for p in self._presets:
                if p < 60:
                    lbl = f"{p}分钟"
                elif p % 60 == 0:
                    lbl = f"{p//60}小时"
                else:
                    lbl = f"{p/60:.1f}小时"
                btn = QPushButton(lbl)
                btn.setObjectName("VibePresetChip")
                btn.setCursor(PetCursorManager.pointer_cursor())
                btn.setFixedHeight(28)
                btn.setCheckable(True)
                btn.clicked.connect(lambda checked=False, minutes=p: self.setValue(minutes))
                chips_layout.addWidget(btn)
                self._preset_buttons.append((p, btn))
                
            chips_layout.addStretch(1)
            main_layout.addLayout(chips_layout)
            self._apply_chip_styles()
            self._update_chip_selection()
        else:
            self._preset_buttons = []

    def _apply_chip_styles(self):
        for _, btn in self._preset_buttons:
            btn.setStyleSheet("""
                QPushButton#VibePresetChip {
                    background: #fff4f6;
                    border: 1px solid #ffd2d8;
                    border-radius: 14px;
                    color: #e11d48;
                    font-size: 12px;
                    font-weight: 600;
                    padding: 0 12px;
                }
                QPushButton#VibePresetChip:hover {
                    background: #ffe4e9;
                    border-color: #ff94a4;
                    color: #be123c;
                }
                QPushButton#VibePresetChip:checked {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ff758c, stop:1 #ff7eb3);
                    border: 1px solid #ff5a79;
                    color: #ffffff;
                    font-weight: 700;
                }
            """)

    def _on_slot_changed(self):
        total = self.hour_slot.value() * 60 + self.min_slot.value()
        total = max(self._min_minutes, min(self._max_minutes, total))
        self._update_chip_selection()
        self.valueChanged.emit(total)

    def _update_chip_selection(self):
        current = self.value()
        for p, btn in self._preset_buttons:
            btn.blockSignals(True)
            btn.setChecked(p == current)
            btn.blockSignals(False)

    def value(self) -> int:
        return self.hour_slot.value() * 60 + self.min_slot.value()

    def setValue(self, minutes: int):
        minutes = max(self._min_minutes, min(self._max_minutes, int(minutes)))
        h = minutes // 60
        m = minutes % 60
        self.hour_slot.blockSignals(True)
        self.min_slot.blockSignals(True)
        self.hour_slot.setValue(h)
        self.min_slot.setValue(m)
        self.hour_slot.blockSignals(False)
        self.min_slot.blockSignals(False)
        self._update_chip_selection()
        self.valueChanged.emit(minutes)

    def setRange(self, min_val: int, max_val: int):
        self._min_minutes = max(0, min_val)
        self._max_minutes = max_val
        self.hour_slot._max_val = max(0, max_val // 60)

    def setSingleStep(self, step: int):
        self.min_slot._step = max(1, step)

    def setSuffix(self, suffix: str):
        pass

    def setKeyboardTracking(self, tracking: bool):
        pass


class VibeVerticalSizeControl(QWidget):
    """
    Vertical Slider & Wheel Size Control for Pet Context Menu:
    - Displays current scale percentage (e.g. "100%") with a warm pastel badge
    - Features a vertical slider track (range: 20% to 200%)
    - Responsive to mouse wheel: scrolling over widget smoothly adjusts scale by +/- 5%
    - Stepper buttons: [+] (+10%), [重置] (100%), [-] (-10%)
    - Emits scaleChanged(int) whenever value changes
    """
    scaleChanged = Signal(int)

    def __init__(self, current_scale: int = 100, on_scale_changed=None, parent=None):
        super().__init__(parent)
        self._scale = max(20, min(200, int(current_scale or 100)))
        if on_scale_changed:
            self.scaleChanged.connect(on_scale_changed)

        self.setFixedSize(168, 190)
        self.setStyleSheet("""
            QWidget#VibeVerticalSizeControl {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #fffcf9, stop: 1 #fff6f0);
                border: 1px solid #fed7cc;
                border-radius: 14px;
            }
        """)
        self.setObjectName("VibeVerticalSizeControl")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Header: Icon, Label, and Pill Badge
        header = QHBoxLayout()
        header.setSpacing(6)

        lbl = QLabel("📏 缩放大小")
        lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #2d2320; background: transparent;")
        header.addWidget(lbl)

        header.addStretch(1)

        self.badge = QLabel(f"{self._scale}%")
        self.badge.setStyleSheet("""
            QLabel {
                background-color: #ffeff0;
                color: #ff526c;
                font-weight: bold;
                font-size: 11px;
                padding: 2px 7px;
                border: 1px solid #ffccd3;
                border-radius: 8px;
            }
        """)
        header.addWidget(self.badge)
        layout.addLayout(header)

        # Center area: Vertical Slider with guide ticks & steppers
        center_row = QHBoxLayout()
        center_row.setSpacing(10)
        center_row.setAlignment(Qt.AlignCenter)

        # Quick guide labels on the left (200%, 100%, 20%)
        ticks_col = QVBoxLayout()
        ticks_col.setContentsMargins(0, 4, 0, 4)
        t_max = QLabel("200%")
        t_mid = QLabel("100%")
        t_min = QLabel("20%")
        for t in (t_max, t_mid, t_min):
            t.setStyleSheet("font-size: 9px; color: #a89c96; background: transparent;")
        ticks_col.addWidget(t_max, 0, Qt.AlignRight)
        ticks_col.addStretch(1)
        ticks_col.addWidget(t_mid, 0, Qt.AlignRight)
        ticks_col.addStretch(1)
        ticks_col.addWidget(t_min, 0, Qt.AlignRight)
        center_row.addLayout(ticks_col)

        # Vertical Slider
        self.slider = QSlider(Qt.Vertical)
        self.slider.setRange(20, 200)
        self.slider.setValue(self._scale)
        self.slider.setSingleStep(5)
        self.slider.setPageStep(20)
        self.slider.setFixedHeight(110)
        self.slider.setCursor(PetCursorManager.grab_cursor())
        self.slider.setStyleSheet("""
            QSlider::groove:vertical {
                background: #f0e4dc;
                width: 6px;
                border-radius: 3px;
            }
            QSlider::sub-page:vertical {
                background: #f0e4dc;
                border-radius: 3px;
            }
            QSlider::add-page:vertical {
                background: qlineargradient(x1: 0, y1: 1, x2: 0, y2: 0, stop: 0 #ff8a9e, stop: 1 #ff526c);
                border-radius: 3px;
            }
            QSlider::handle:vertical {
                background: #ffffff;
                border: 2px solid #ff526c;
                height: 16px;
                width: 16px;
                margin: 0 -5px;
                border-radius: 8px;
            }
            QSlider::handle:vertical:hover {
                background: #ff526c;
                border: 2px solid #ffffff;
            }
        """)
        self.slider.valueChanged.connect(self._on_slider_changed)
        center_row.addWidget(self.slider)

        # Quick preset buttons on the right
        btn_col = QVBoxLayout()
        btn_col.setContentsMargins(0, 0, 0, 0)
        btn_col.setSpacing(4)
        btn_style = """
            QPushButton {
                background: #ffffff;
                border: 1px solid #fed7cc;
                border-radius: 7px;
                color: #4a3b34;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                font-size: 11px;
                font-weight: 500;
                min-width: 40px;
                min-height: 22px;
                padding: 1px 4px;
            }
            QPushButton:hover {
                background: #ffeff0;
                border-color: #ff8a9e;
                color: #ff526c;
            }
            QPushButton:pressed {
                background: #ffd6dc;
            }
        """
        b_plus = SpringPushButton("+")
        b_plus.setToolTip("放大 +10%")
        b_plus.setStyleSheet(btn_style)
        b_plus.clicked.connect(lambda: self.adjust_scale(10))

        b_reset = SpringPushButton("重置")
        b_reset.setToolTip("重置为 100%")
        b_reset.setStyleSheet(btn_style)
        b_reset.clicked.connect(lambda: self.set_scale(100))

        b_minus = SpringPushButton("-")
        b_minus.setToolTip("缩小 -10%")
        b_minus.setStyleSheet(btn_style)
        b_minus.clicked.connect(lambda: self.adjust_scale(-10))

        btn_col.addWidget(b_plus)
        btn_col.addWidget(b_reset)
        btn_col.addWidget(b_minus)
        center_row.addLayout(btn_col)

        layout.addLayout(center_row)

    def _on_slider_changed(self, value: int):
        self._scale = value
        self.badge.setText(f"{value}%")
        self.scaleChanged.emit(value)

    def set_scale(self, value: int):
        clamped = max(20, min(200, int(value)))
        self.slider.setValue(clamped)

    def adjust_scale(self, delta: int):
        self.set_scale(self._scale + delta)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.adjust_scale(5)
        elif delta < 0:
            self.adjust_scale(-5)
        event.accept()
