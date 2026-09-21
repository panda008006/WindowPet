import random
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QCursor,
    QFont,
    QFontMetrics,
    QImageReader,
    QLinearGradient,
    QMovie,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QInputDialog,
    QMenu,
    QMessageBox,
    QPushButton,
    QSystemTrayIcon,
    QWidget,
    QWidgetAction,
)

from .system_mic import (
    get_microphone_muted,
    set_microphone_muted,
    toggle_microphone_muted,
)
from .assets import (
    AssetType,
    assets_for_pack,
    detect_asset,
    frame_paths_for_folder,
    import_asset_to_assets,
    save_config,
    stored_path,
)
from .asset_validation import validate_asset_metadata
from .constants import APP_DISPLAY_NAME, BASE_DIR
from .behavior_packs import SCREEN_SAVER_ENTER, SCREEN_SAVER_EXIT, STARTUP, resolve_behavior_action
from .frame_animation_player import FrameAnimationPlayer
from .media_folder import media_source_frames, video_sources_for_folder
from .video_audio_player import VideoAudioPlayer, VideoMediaPlayer
from .focus import (
    FOCUS_MODE_BREAK,
    FOCUS_MODE_CUSTOM,
    FOCUS_MODE_FOCUS,
    completion_message,
    normalize_focus_mode,
    should_count_focus_session,
    timer_done_text,
    timer_prefix,
)
from .metadata_renderers import (
    CompositeUIRenderer,
    SpriteAnimationPlayer,
    load_sprite_strip_frames,
    load_spritesheet_frames,
)
from . import state
from .logging_utils import log_info, log_warning
from .physics import OverlayPhysics
from .startup import set_startup_enabled, startup_enabled
from .style_utils import style_menu, style_message_box
from .updater import check_for_updates, open_official_site
from .feather_tool import show_feather_tool
from .whip_tool import show_whip_tool
from .interactions import infer_character_id_from_path
from .vibe_components import VibeVerticalSizeControl


EDGE_CRAWL_ANIMATIONS = {
    "edge-crawl-bottom",
    "edge-crawl-top",
    "edge-crawl-left",
    "edge-crawl-right",
}
BASIC_ACTION_NAMES = (
    "idle",
    "click",
    "drag",
)
MANUAL_ACTION_EXCLUDED_NAMES = frozenset({"head_track", "right-double-click"})
MANUAL_ACTION_EXCLUDED_PREFIXES = ("edge-crawl-", "trio-")
DEFAULT_MANUAL_ACTION_LABELS = {
    "hover": "看看你",
    "jumping": "跳一跳",
    "review": "特别表演",
    "waving": "挥挥手",
    "waiting": "等等",
    "running": "跑一跑",
    "running-left": "向左跑",
    "running-right": "向右跑",
    "failed": "失败反应",
    "reward": "奖励动作",
    "feather-tickle": "羽毛挠痒",
    "whip-hit": "抽鞭子",
    "fall": "下落",
    "land": "落地",
}
MOUSE_TRIGGER_ORDER = (
    "left-click",
    "left-drag",
)
MOUSE_TRIGGER_ACTIONS = {
    "left-click": "click",
    "left-drag": "drag",
}

_TASKBAR_CACHE_SECONDS = 0.5
_TASKBAR_CACHE_AT = 0.0
_TASKBAR_CACHE_RECTS = []


def _windows_taskbar_rects():
    global _TASKBAR_CACHE_AT, _TASKBAR_CACHE_RECTS

    if sys.platform != "win32":
        return []

    now = time.monotonic()
    if now - _TASKBAR_CACHE_AT < _TASKBAR_CACHE_SECONDS:
        return list(_TASKBAR_CACHE_RECTS)

    rects = []
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32

        class Rect(ctypes.Structure):
            _fields_ = [
                ("left", wintypes.LONG),
                ("top", wintypes.LONG),
                ("right", wintypes.LONG),
                ("bottom", wintypes.LONG),
            ]

        def append_rect(hwnd):
            if not hwnd or not user32.IsWindowVisible(hwnd):
                return
            rect = Rect()
            if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return
            width = rect.right - rect.left
            height = rect.bottom - rect.top
            if width > 0 and height > 0:
                rects.append(QRect(rect.left, rect.top, width, height))

        append_rect(user32.FindWindowW("Shell_TrayWnd", None))
        hwnd = 0
        while True:
            hwnd = user32.FindWindowExW(None, hwnd, "Shell_SecondaryTrayWnd", None)
            if not hwnd:
                break
            append_rect(hwnd)
    except Exception:
        rects = []

    _TASKBAR_CACHE_AT = now
    _TASKBAR_CACHE_RECTS = rects
    return list(rects)


def _geometry_excluding_taskbars(screen_geometry, available_geometry, taskbar_rects):
    result = QRect(available_geometry)
    if not screen_geometry.isValid() or not result.isValid():
        return result

    edge_slop = 2
    for taskbar in taskbar_rects:
        if not isinstance(taskbar, QRect) or not taskbar.isValid():
            continue
        intersection = taskbar.intersected(screen_geometry)
        if not intersection.isValid():
            continue

        spans_width = intersection.width() >= max(1, round(screen_geometry.width() * 0.5))
        spans_height = intersection.height() >= max(1, round(screen_geometry.height() * 0.5))
        if spans_width and abs(intersection.bottom() - screen_geometry.bottom()) <= edge_slop:
            result.setBottom(min(result.bottom(), intersection.top() - 1))
        elif spans_width and abs(intersection.top() - screen_geometry.top()) <= edge_slop:
            result.setTop(max(result.top(), intersection.bottom() + 1))
        elif spans_height and abs(intersection.right() - screen_geometry.right()) <= edge_slop:
            result.setRight(min(result.right(), intersection.left() - 1))
        elif spans_height and abs(intersection.left() - screen_geometry.left()) <= edge_slop:
            result.setLeft(max(result.left(), intersection.right() + 1))

    return result if result.isValid() else QRect(available_geometry)


def work_area_for_screen(screen):
    available = screen.availableGeometry()
    if sys.platform != "win32":
        return available
    return _geometry_excluding_taskbars(screen.geometry(), available, _windows_taskbar_rects())


def remove_native_border(window):
    if sys.platform != "win32":
        return

    try:
        import ctypes

        hwnd = int(window.winId())
        color_none = ctypes.c_uint(0xFFFFFFFE)
        corner_none = ctypes.c_int(1)

        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 34, ctypes.byref(color_none), ctypes.sizeof(color_none)
        )
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 33, ctypes.byref(corner_none), ctypes.sizeof(corner_none)
        )
    except Exception:
        pass


def refresh_control_panel():
    if state.CONTROL_PANEL is not None:
        state.CONTROL_PANEL.refresh_active()


def exit_app():
    state.EXITING = True
    log_info("%s exit requested", APP_DISPLAY_NAME)
    save_config()
    QApplication.instance().quit()


def confirm_exit_or_tray(parent=None):
    dialog = style_message_box(QMessageBox(parent))
    dialog.setWindowTitle(f"退出 {APP_DISPLAY_NAME}")
    dialog.setText("你想直接退出程序，还是最小化到系统托盘？")

    minimize_button = dialog.addButton("最小化到托盘", QMessageBox.ActionRole)
    exit_button = dialog.addButton("退出", QMessageBox.DestructiveRole)
    cancel_button = dialog.addButton("取消", QMessageBox.RejectRole)
    dialog.setDefaultButton(minimize_button)
    dialog.exec()

    clicked = dialog.clickedButton()
    if clicked == minimize_button:
        if state.CONTROL_PANEL is not None:
            state.CONTROL_PANEL.hide()
        return "tray"

    if clicked == exit_button:
        exit_app()
        return "exit"

    if clicked == cancel_button:
        return "cancel"

    return "cancel"


def add_window(asset_path, config=None, save=True):
    path = Path(asset_path).resolve()
    asset = detect_asset(path)
    if asset is None and path.is_file():
        imported_path = import_asset_to_assets(path)
        asset = detect_asset(imported_path) if imported_path is not None else None

    if asset is None:
        log_warning("Unsupported or missing asset skipped: %s", asset_path)
        return None

    try:
        window = OverlayWindow(asset, config or {})
    except ValueError as exc:
        log_warning("%s", exc)
        return None
    state.WINDOWS.append(window)
    window.show()
    remove_native_border(window)
    log_info("Overlay created: %s", window.asset_path)
    if save:
        save_config()
    refresh_control_panel()
    return window


class SpeechBubbleWindow(QWidget):
    """悬浮在宠物头顶上方的软萌云朵气泡。

    独立的无边框、鼠标完全穿透窗口，因此不会遮住宠物脸部的交互；
    云朵轮廓由温润圆角主体、蓬松有机云朵弧线和自然下垂的微弯漫画尾巴经 QPainterPath.united
    合成单一轮廓后一次性填充和描边，内部不出现穿线；
    四边预留充足内边距与阴影缓冲，杜绝任何顶缘、底缘、尾巴或文字被系统窗口截断的现象；
    文字前缀均配备高质感 3D 拟态贴纸徽章图标（计时闹钟、达成金星、待办清单、睡眠月亮、萌宠心语等）。
    """

    OWNER_GAP = 8
    LINE_HEIGHT = 32
    MARGIN_LEFT = 14.0
    MARGIN_RIGHT = 14.0
    MARGIN_TOP = 16.0
    MARGIN_BOTTOM = 24.0
    PADDING_INNER_X = 14.0
    ICON_SIZE = 22.0
    ICON_TEXT_GAP = 10.0
    MIN_WIDTH = 170
    MAX_WIDTH = 480

    def __init__(self, owner):
        super().__init__(None)
        self.owner = owner
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.Tool
            | Qt.WindowTransparentForInput
            | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self._lines = []
        self._tail_x = None
        self._tail_inverted = False

    def bubble_font(self):
        font = QFont("Microsoft YaHei UI", 9)
        font.setBold(True)
        return font

    def set_lines(self, lines):
        lines = [tuple(line) for line in (lines or [])]
        if lines == self._lines:
            return
        self._lines = lines
        self._relayout()

    def _relayout(self):
        metrics = QFontMetrics(self.bubble_font())
        max_text_w = 0
        for text, _kind in self._lines:
            max_text_w = max(max_text_w, metrics.horizontalAdvance(text))

        needed_w = (
            self.MARGIN_LEFT
            + self.PADDING_INNER_X
            + self.ICON_SIZE
            + self.ICON_TEXT_GAP
            + max_text_w
            + self.PADDING_INNER_X
            + self.MARGIN_RIGHT
            + 16.0
        )
        width = max(self.MIN_WIDTH, min(int(needed_w), self.MAX_WIDTH))

        top_margin = self.MARGIN_BOTTOM if self._tail_inverted else self.MARGIN_TOP
        bottom_margin = self.MARGIN_TOP if self._tail_inverted else self.MARGIN_BOTTOM
        height = int(top_margin + bottom_margin + max(1, len(self._lines)) * self.LINE_HEIGHT)

        self.setFixedSize(width, height)
        self.update()

    def body_rect(self):
        top_y = self.MARGIN_BOTTOM if self._tail_inverted else self.MARGIN_TOP
        return QRectF(
            self.MARGIN_LEFT,
            top_y,
            self.width() - self.MARGIN_LEFT - self.MARGIN_RIGHT,
            max(32.0, float(len(self._lines)) * self.LINE_HEIGHT),
        )

    def cloud_path(self):
        rect = self.body_rect()
        path = QPainterPath()
        radius = min(18.0, rect.height() / 2.0)
        path.addRoundedRect(rect, radius, radius)

        # Controlled fixed-height top cloud puffs (strictly bounded within MARGIN_TOP)
        puff_h = min(8.5, rect.height() * 0.28)
        lobes_def = [
            (rect.left() + rect.width() * 0.18, rect.top(), 22.0, puff_h),
            (rect.left() + rect.width() * 0.40, rect.top(), 28.0, puff_h * 1.22),
            (rect.left() + rect.width() * 0.65, rect.top(), 26.0, puff_h * 1.15),
            (rect.left() + rect.width() * 0.84, rect.top(), 20.0, puff_h * 0.95),
        ]
        for cx, cy, rx, ry in lobes_def:
            lobe = QPainterPath()
            lobe.addEllipse(QRectF(cx - rx, cy - ry, rx * 2.0, ry * 2.0))
            path = path.united(lobe)

        # Dynamic curved speech tail pointing towards the pet
        tail_x = self._tail_x if self._tail_x is not None else (rect.center().x() - 10.0)
        tail_x = max(rect.left() + 24.0, min(rect.right() - 24.0, tail_x))

        tail = QPainterPath()
        if not self._tail_inverted:
            tail_bottom = rect.bottom() + 11.0
            tail.moveTo(tail_x - 9.0, rect.bottom() - 2.0)
            tail.cubicTo(tail_x - 7.0, rect.bottom() + 4.0, tail_x - 4.0, tail_bottom - 2.0, tail_x - 5.0, tail_bottom)
            tail.cubicTo(tail_x - 2.0, tail_bottom - 2.0, tail_x + 5.0, rect.bottom() + 4.0, tail_x + 9.0, rect.bottom() - 2.0)
            tail.closeSubpath()
            path = path.united(tail)

            droplet = QPainterPath()
            droplet.addEllipse(QRectF(tail_x - 10.0, tail_bottom - 1.0, 4.0, 4.0))
            path = path.united(droplet)
        else:
            tail_top = rect.top() - 11.0
            tail.moveTo(tail_x - 9.0, rect.top() + 2.0)
            tail.cubicTo(tail_x - 7.0, rect.top() - 4.0, tail_x - 4.0, tail_top + 2.0, tail_x - 5.0, tail_top)
            tail.cubicTo(tail_x - 2.0, tail_top + 2.0, tail_x + 5.0, rect.top() - 4.0, tail_x + 9.0, rect.top() + 2.0)
            tail.closeSubpath()
            path = path.united(tail)

            droplet = QPainterPath()
            droplet.addEllipse(QRectF(tail_x - 10.0, tail_top - 3.0, 4.0, 4.0))
            path = path.united(droplet)

        return path

    def draw_line_icon(self, painter, rect, kind):
        painter.save()
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        cx = rect.center().x()
        cy = rect.center().y()
        size = min(rect.width(), rect.height())
        badge_rect = QRectF(cx - size / 2.0, cy - size / 2.0, size, size)

        if kind == "timer":
            bg_color = QColor("#fff4ec")
            border_color = QColor("#ffd8bf")
            accent_color = QColor("#fa541c")

            painter.setPen(QPen(border_color, 1.2))
            painter.setBrush(QBrush(bg_color))
            painter.drawEllipse(badge_rect)

            face_r = size * 0.35
            face_rect = QRectF(cx - face_r, cy - face_r + 1.2, face_r * 2.0, face_r * 2.0)
            painter.setPen(QPen(accent_color, 1.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(face_rect)

            # Alarm bells
            painter.setPen(QPen(accent_color, 1.4, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(cx - face_r * 0.7, cy - face_r * 0.7 + 1.2), QPointF(cx - face_r * 0.95, cy - face_r * 0.95))
            painter.drawLine(QPointF(cx + face_r * 0.7, cy - face_r * 0.7 + 1.2), QPointF(cx + face_r * 0.95, cy - face_r * 0.95))

            # Hands
            painter.setPen(QPen(accent_color, 1.5, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(cx, cy + 1.2), QPointF(cx, cy - face_r * 0.55 + 1.2))
            painter.drawLine(QPointF(cx, cy + 1.2), QPointF(cx + face_r * 0.5, cy + 1.2))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(accent_color))
            painter.drawEllipse(QPointF(cx, cy + 1.2), 1.2, 1.2)

        elif kind == "timer_done":
            bg_color = QColor("#fffbe6")
            border_color = QColor("#ffe58f")
            accent_color = QColor("#faad14")

            painter.setPen(QPen(border_color, 1.2))
            painter.setBrush(QBrush(bg_color))
            painter.drawEllipse(badge_rect)

            star = QPainterPath()
            sr = size * 0.38
            star.moveTo(cx, cy - sr)
            star.cubicTo(cx + sr * 0.2, cy - sr * 0.2, cx + sr * 0.2, cy - sr * 0.2, cx + sr, cy)
            star.cubicTo(cx + sr * 0.2, cy + sr * 0.2, cx + sr * 0.2, cy + sr * 0.2, cx, cy + sr)
            star.cubicTo(cx - sr * 0.2, cy + sr * 0.2, cx - sr * 0.2, cy + sr * 0.2, cx - sr, cy)
            star.cubicTo(cx - sr * 0.2, cy - sr * 0.2, cx - sr * 0.2, cy - sr * 0.2, cx, cy - sr)

            painter.setPen(QPen(QColor("#d48806"), 1.2))
            painter.setBrush(QBrush(accent_color))
            painter.drawPath(star)

        elif kind == "memo":
            checked = getattr(self.owner, "memo_checked", False)
            if checked:
                bg_color = QColor("#f6ffed")
                border_color = QColor("#b7eb8f")
                accent_color = QColor("#52c41a")
            else:
                bg_color = QColor("#f0fdf4")
                border_color = QColor("#bbf7d0")
                accent_color = QColor("#16a34a")

            painter.setPen(QPen(border_color, 1.2))
            painter.setBrush(QBrush(bg_color))
            painter.drawRoundedRect(badge_rect, 6.0, 6.0)

            box_r = size * 0.32
            box_rect = QRectF(cx - box_r, cy - box_r, box_r * 2.0, box_r * 2.0)
            painter.setPen(QPen(accent_color, 1.4))
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawRoundedRect(box_rect, 3.5, 3.5)

            if checked:
                chk = QPainterPath()
                chk.moveTo(cx - box_r * 0.6, cy)
                chk.lineTo(cx - box_r * 0.1, cy + box_r * 0.5)
                chk.lineTo(cx + box_r * 0.7, cy - box_r * 0.45)
                painter.setPen(QPen(accent_color, 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                painter.setBrush(Qt.NoBrush)
                painter.drawPath(chk)
            else:
                painter.setPen(QPen(accent_color, 1.4, Qt.SolidLine, Qt.RoundCap))
                painter.drawLine(QPointF(cx - box_r * 0.5, cy - box_r * 0.3), QPointF(cx + box_r * 0.5, cy - box_r * 0.3))
                painter.drawLine(QPointF(cx - box_r * 0.5, cy + box_r * 0.3), QPointF(cx + box_r * 0.2, cy + box_r * 0.3))

        elif kind == "power":
            bg_color = QColor("#f9f0ff")
            border_color = QColor("#d3adf7")
            accent_color = QColor("#722ed1")

            painter.setPen(QPen(border_color, 1.2))
            painter.setBrush(QBrush(bg_color))
            painter.drawEllipse(badge_rect)

            pr = size * 0.30
            p_rect = QRectF(cx - pr, cy - pr + 1.0, pr * 2.0, pr * 2.0)
            painter.setPen(QPen(accent_color, 1.6, Qt.SolidLine, Qt.RoundCap))
            painter.setBrush(Qt.NoBrush)
            painter.drawArc(p_rect.toRect(), 50 * 16, 260 * 16)
            painter.drawLine(QPointF(cx, cy - pr + 1.0), QPointF(cx, cy + 1.0))

        elif kind in ("party", "offwork"):
            bg_color = QColor("#fff7e6")
            border_color = QColor("#ffd591")
            accent_color = QColor("#fa8c16")

            painter.setPen(QPen(border_color, 1.2))
            painter.setBrush(QBrush(bg_color))
            painter.drawEllipse(badge_rect)

            pr = size * 0.35
            painter.setPen(QPen(QColor("#faad14"), 1.6, Qt.SolidLine, Qt.RoundCap))
            painter.drawLine(QPointF(cx - pr * 0.6, cy + pr * 0.6), QPointF(cx + pr * 0.6, cy - pr * 0.6))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#ff4d4f")))
            painter.drawEllipse(QPointF(cx + pr * 0.5, cy - pr * 0.5), 2.2, 2.2)
            painter.setBrush(QBrush(QColor("#fa8c16")))
            painter.drawEllipse(QPointF(cx - pr * 0.3, cy - pr * 0.4), 1.8, 1.8)
            painter.setBrush(QBrush(QColor("#52c41a")))
            painter.drawEllipse(QPointF(cx + pr * 0.4, cy + pr * 0.2), 1.8, 1.8)

        else:
            bg_color = QColor("#fff0f6")
            border_color = QColor("#ffadd2")
            accent_color = QColor("#eb2f96")

            painter.setPen(QPen(border_color, 1.2))
            painter.setBrush(QBrush(bg_color))
            painter.drawEllipse(badge_rect)

            hr = size * 0.30
            heart = QPainterPath()
            heart.moveTo(cx, cy + hr * 0.75)
            heart.cubicTo(cx - hr * 1.1, cy, cx - hr * 1.1, cy - hr * 0.9, cx, cy - hr * 0.35)
            heart.cubicTo(cx + hr * 1.1, cy - hr * 0.9, cx + hr * 1.1, cy, cx, cy + hr * 0.75)
            painter.setPen(QPen(QColor("#c41d7f"), 1.0))
            painter.setBrush(QBrush(accent_color))
            painter.drawPath(heart)

        painter.restore()

    def line_color(self, kind):
        if kind == "timer":
            return QColor("#d4380d")
        if kind == "timer_done":
            return QColor("#d46b08")
        if kind in ("party", "offwork"):
            return QColor("#d4380d")
        if kind == "memo":
            return QColor("#1f2937")
        if kind == "power":
            return QColor("#531dab")
        return QColor("#c41d7f")

    def paintEvent(self, event):
        if not self._lines:
            return
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)
        path = self.cloud_path()

        # Multi-tier Soft Drop Shadows
        shadow_tiers = [
            (0.0, 5.0, QColor(26, 38, 64, 18)),
            (0.0, 2.5, QColor(26, 38, 64, 28)),
            (0.0, 1.0, QColor(255, 117, 140, 26)),
        ]
        for sx, sy, scolor in shadow_tiers:
            s_path = QPainterPath(path)
            s_path.translate(sx, sy)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(scolor))
            painter.drawPath(s_path)

        # Milky Porcelain Fill with subtle warm gradient
        grad = QLinearGradient(0.0, 0.0, 0.0, float(self.height()))
        grad.setColorAt(0.0, QColor(255, 255, 255, 254))
        grad.setColorAt(0.75, QColor(255, 253, 252, 252))
        grad.setColorAt(1.0, QColor(255, 247, 247, 250))

        # Delicate Warm Pastel Border
        border_pen = QPen(QColor("#ffd6d6"), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(border_pen)
        painter.setBrush(QBrush(grad))
        painter.drawPath(path)

        # Top Soft Inner Highlight
        painter.save()
        painter.setClipPath(path)
        top_y = float(self.MARGIN_TOP - 2) if not self._tail_inverted else float(self.MARGIN_BOTTOM)
        highlight_grad = QLinearGradient(0.0, top_y, 0.0, top_y + 20.0)
        highlight_grad.setColorAt(0.0, QColor(255, 255, 255, 210))
        highlight_grad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(highlight_grad))
        painter.drawRect(QRectF(0.0, 0.0, float(self.width()), top_y + 20.0))
        painter.restore()

        # Content Lines
        body = self.body_rect()
        font = self.bubble_font()
        painter.setFont(font)
        metrics = QFontMetrics(font)
        available_text_w = body.width() - self.PADDING_INNER_X * 2.0 - self.ICON_SIZE - self.ICON_TEXT_GAP

        for index, (text, kind) in enumerate(self._lines):
            line_y = body.top() + float(index) * self.LINE_HEIGHT
            icon_x = body.left() + self.PADDING_INNER_X
            icon_y = line_y + (self.LINE_HEIGHT - self.ICON_SIZE) / 2.0
            icon_rect = QRectF(icon_x, icon_y, self.ICON_SIZE, self.ICON_SIZE)
            self.draw_line_icon(painter, icon_rect, kind)

            text_x = icon_x + self.ICON_SIZE + self.ICON_TEXT_GAP
            text_rect = QRectF(text_x, line_y, available_text_w, self.LINE_HEIGHT)

            display_text = metrics.elidedText(text, Qt.ElideRight, int(available_text_w))
            if kind in ("timer", "timer_done"):
                text_w = metrics.horizontalAdvance(display_text)
                card_w = min(available_text_w, text_w + 14)
                card_rect = QRectF(text_x - 2, line_y + 4, card_w, self.LINE_HEIGHT - 8)
                c_bg = QColor("#fff4ec") if kind == "timer" else QColor("#fffbe6")
                c_border = QColor("#ffd8bf") if kind == "timer" else QColor("#ffe58f")
                painter.setPen(QPen(c_border, 1.2))
                painter.setBrush(QBrush(c_bg))
                painter.drawRoundedRect(card_rect, 6.0, 6.0)

                mono_font = QFont("Consolas", 10, QFont.Bold)
                mono_font.setStyleHint(QFont.Monospace)
                painter.setFont(mono_font)
                painter.setPen(self.line_color(kind))
                painter.drawText(card_rect, Qt.AlignCenter, display_text)
                painter.setFont(font)
            else:
                painter.setPen(self.line_color(kind))
                painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, display_text)

    def reposition(self):
        owner_geometry = self.owner.geometry()
        x = owner_geometry.center().x() - self.width() // 2
        y = owner_geometry.top() - self.height() - self.OWNER_GAP
        screen = self.owner.screen() or QApplication.primaryScreen()
        prev_inverted = self._tail_inverted
        if screen is not None:
            available = screen.availableGeometry()
            if y < available.top() + 2:
                y = owner_geometry.bottom() + self.OWNER_GAP + 2
                self._tail_inverted = True
            else:
                self._tail_inverted = False
            x = max(available.left() + 2, min(x, available.right() - self.width() - 2))
        else:
            self._tail_inverted = False

        if self._tail_inverted != prev_inverted:
            self._relayout()

        self._tail_x = float(owner_geometry.center().x() - x)
        self.move(x, y)
        self.update()


class MicFloatingBadge(QPushButton):
    """悬浮在桌宠身上的麦克风状态图标与闭麦控制按钮。
    - 右键点击桌宠后显现，或处于闭麦(静音)状态时常驻提示；
    - 单击图标即可一键完成闭麦/开麦；
    - 提供温润灵动的微拟态视觉反馈与气泡联动。
    """

    def __init__(self, overlay: "OverlayWindow"):
        super().__init__(overlay)
        self.overlay = overlay
        self.setFixedSize(30, 30)
        self.setCursor(Qt.PointingHandCursor)
        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self._on_auto_hide)
        self.clicked.connect(self._on_clicked)
        self.update_state()

    def update_state(self):
        is_muted = get_microphone_muted()
        if is_muted:
            self._auto_hide_timer.stop()
            self.setText("🔇")
            self.setToolTip("当前麦克风已闭麦 · 点击重新开麦")
            self.setStyleSheet("""
                QPushButton {
                    background: #ffebee;
                    border: 2px solid #ff526c;
                    border-radius: 15px;
                    font-size: 14px;
                    color: #ff526c;
                    padding: 0px;
                }
                QPushButton:hover {
                    background: #ffd6dc;
                    border-color: #ff3355;
                }
            """)
            self.show()
            self.raise_()
        else:
            self.setText("🎙️")
            self.setToolTip("点击闭麦 (静音系统麦克风)")
            self.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.95);
                    border: 1.5px solid #20bf6b;
                    border-radius: 15px;
                    font-size: 14px;
                    padding: 0px;
                }
                QPushButton:hover {
                    background: #e8f9ee;
                    border-color: #10ac58;
                }
            """)
            if self.isVisible():
                self._auto_hide_timer.start(8000)

    def reveal(self):
        """右键触发时显现麦克风图标"""
        self.update_state()
        self.show()
        self.raise_()
        if not get_microphone_muted():
            self._auto_hide_timer.start(8000)

    def _on_auto_hide(self):
        if not get_microphone_muted():
            self.hide()

    def _on_clicked(self):
        if self.overlay is not None:
            self.overlay.toggle_microphone_mute()


class OverlayWindow(QWidget):
    def __init__(self, asset, config=None):
        super().__init__()
        config = config or {}

        self.asset = asset
        self.asset_path = Path(asset.path).resolve()
        self.asset_type = asset.type
        self.character_id = str(config.get("character_id") or infer_character_id_from_path(self.asset_path))
        self.pet_serial = str(config.get("pet_serial") or "")
        self.pet_display_name = str(config.get("pet_display_name") or asset.name or self.asset_path.name)
        self.gif_path = self.asset_path
        self.locked = bool(config.get("locked", False))
        self.always_on_top = bool(config.get("always_on_top", True))
        self.click_through = bool(config.get("click_through", False))
        self.scale = self.config_int(config, "scale", 50)
        self.opacity = self.config_int(config, "opacity", 100)
        self.speed = self.config_int(config, "speed", 100)
        self.drag_offset = QPoint()
        self.base_size = QSize()
        self._speech_bubble = None
        self.press_global_pos = QPoint()
        self.is_dragging_asset = False
        self.drag_button = None
        self.drag_start_dock_mode = "none"
        self.drag_released_at_top_edge = False
        self.screen_saver_active = False
        self.initializing_position = True
        # Edge docking was removed from the user-facing interaction model.
        # Old config files may still contain dock_mode; always normalise it away.
        self.dock_mode = "none"
        self.physics_enabled = bool(config.get("physics_enabled", False))
        self.temporary_fall_enabled = False
        self.top_drop_timer = QTimer(self)
        self.top_drop_timer.setInterval(33)
        self.top_drop_timer.timeout.connect(self.step_top_drop)
        self.top_drop_target_y = 0
        self.top_drop_last_tick = None
        self.timer_visible = bool(config.get("timer_visible", False))
        self.timer_seconds = self.config_int(config, "timer_seconds", 300)
        self.timer_seconds = min(24 * 3600, max(60, self.timer_seconds))
        self.focus_mode = normalize_focus_mode(config.get("focus_mode"))
        self.focus_sessions_completed = max(0, self.config_int(config, "focus_sessions_completed", 0))
        self.timer_running = False
        self.timer_done = False
        self.countdown_timer = QTimer(self)
        self.countdown_timer.setInterval(1000)
        self.countdown_timer.timeout.connect(self.tick_countdown)
        self.idle_variant_timer = QTimer(self)
        self.idle_variant_timer.setSingleShot(True)
        self.idle_variant_timer.timeout.connect(self.play_random_idle_variant)
        self.animation_duration_timer = QTimer(self)
        self.animation_duration_timer.setSingleShot(True)
        self.animation_duration_timer.timeout.connect(self.finish_timed_frame_animation)
        self.memo_visible = bool(config.get("memo_visible", False))
        self.memo_text = str(config.get("memo_text") or "")
        self.memo_checked = bool(config.get("memo_checked", False))
        self.notchnotes_window = None
        self.power_action_type = str(config.get("power_action_type") or "")
        self.power_action_due_at = str(config.get("power_action_due_at") or "")
        self.power_timer = QTimer(self)
        self.power_timer.setInterval(1000)
        self.power_timer.timeout.connect(self.check_power_schedule)
        self.power_timer.start()
        self.head_track_enabled = bool(config.get("head_track_enabled", True))
        self.head_track_frames = []
        self.head_track_index = -1
        self.head_track_timer = QTimer(self)
        self.head_track_timer.setInterval(40)
        self.head_track_timer.timeout.connect(self.tick_head_track)
        self.whip_hit_cooldown_until = 0.0
        enabled_accessories = config.get("enabled_accessories")
        self.enabled_accessories = list(enabled_accessories) if isinstance(enabled_accessories, list) else []
        self.accessory_cache = {}
        self.current_frame_animation = "idle"
        self.return_to_idle_after_animation = False
        self.movie = None
        self.static_pixmap = QPixmap()
        self.current_pixmap = QPixmap()
        self.current_pixmap_content_cache_key = None
        self.frame_player = None
        self.mic_badge = MicFloatingBadge(self)
        if not get_microphone_muted():
            self.mic_badge.hide()
        # 角色自身声音静音状态 (刚下载时所有角色默认静音，静心陪伴)
        self.sound_muted = bool(config.get("sound_muted", True))
        self.sprite_player = None
        self.video_player = None
        self.video_audio_player = None
        self.video_action_player = None
        self.composite_renderer = None
        layer_values = config.get("layer_values")
        self.layer_values = dict(layer_values) if isinstance(layer_values, dict) else {}
        current_animation = config.get("current_animation")
        self.current_animation = current_animation if isinstance(current_animation, str) else None

        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)
        self.setContentsMargins(0, 0, 0, 0)
        self.setMouseTracking(True)
        self.setStyleSheet("background: transparent; border: 0; margin: 0; padding: 0;")

        if not self.load_asset_content():
            raise ValueError(f"Unable to load asset: {self.asset_path}")

        self.apply_window_flags()
        self.apply_click_through()
        self.setWindowOpacity(self.opacity / 100)

        x = self.config_int(config, "x", 100)
        y = self.config_int(config, "y", 100)
        self.move(self.restored_position(QPoint(x, y)))
        self.initializing_position = False
        self.physics = OverlayPhysics(self, enabled=self.physics_enabled)

        self.start_playback()
        medal_store = getattr(state, "MEDAL_STORE", None)
        if medal_store is not None:
            metadata = self.asset.metadata or {}
            medal_store.record_pet(
                self.character_id,
                custom=bool(metadata.get("custom_character") or metadata.get("custom_delivery")),
            )
        self.physics.start()
        self.setup_head_track()

    def load_asset_content(self):
        errors = validate_asset_metadata(self.asset)
        if errors:
            for error in errors:
                log_warning("%s: %s", self.asset.path, error)
            return False

        if self.asset_type == AssetType.GIF:
            self.movie = QMovie(str(self.asset_path))
            self.movie.setCacheMode(QMovie.CacheAll)
            self.movie.setSpeed(self.speed)

            size = QImageReader(str(self.asset_path)).size()
            if not size.isValid():
                size = self.movie.frameRect().size()
            if size.isValid():
                self.base_size = size
                self.apply_scale()

            self.movie.frameChanged.connect(self.update_from_movie)
            return True

        if self.asset_type == AssetType.STATIC_IMAGE:
            self.static_pixmap = QPixmap(str(self.asset_path))
            if self.static_pixmap.isNull():
                log_warning("Unreadable image skipped: %s", self.asset_path)
                return False
            self.current_pixmap = self.static_pixmap
            self.base_size = self.static_pixmap.size()
            self.apply_scale()
            return True

        if self.asset_type == AssetType.VIDEO:
            if not self.asset_path.is_file():
                log_warning("Unreadable video skipped: %s", self.asset_path)
                return False
            self.video_player = VideoMediaPlayer(self)
            self.video_player.frame_changed.connect(self.update_from_video_player)
            self.video_player.finished.connect(self.frame_animation_finished)
            first_frame = media_source_frames(self.asset_path)
            if first_frame:
                self.current_pixmap = QPixmap(str(first_frame[0]))
                if self.current_pixmap.isNull():
                    self.current_pixmap = QPixmap()
                else:
                    self.base_size = self.current_pixmap.size()
                    self.apply_scale()
                    self.video_player.set_display_size(self.base_size)
            return True

        if self.asset_type == AssetType.FRAME_ANIMATION:
            frame_paths, fps, _loop = self.frame_animation_definition("idle")
            if not frame_paths and self.animation_video_source("idle") is not None:
                self.video_action_player = VideoMediaPlayer(self)
                self.video_action_player.frame_changed.connect(self.update_from_video_player)
                self.video_action_player.finished.connect(self.frame_animation_finished)
                first_frame = media_source_frames(self.animation_video_source("idle"))
                if first_frame:
                    self.current_pixmap = QPixmap(str(first_frame[0]))
                    if not self.current_pixmap.isNull():
                        self.base_size = self.current_pixmap.size()
                        self.apply_scale()
                        self.video_action_player.set_display_size(self.base_size)
                return True
            self.frame_player = FrameAnimationPlayer(
                frame_paths,
                fps=fps,
                parent=self,
                loop=True,
            )
            self.frame_player.set_speed(self.speed)
            self.frame_player.pixmap_changed.connect(self.update_from_frame_player)
            self.frame_player.finished.connect(self.frame_animation_finished)
            if not self.frame_player.frames:
                log_warning("No readable frames in asset skipped: %s", self.asset_path)
                return False
            self.current_pixmap = self.frame_player.frames[0]
            self.base_size = self.current_pixmap.size()
            self.apply_scale()
            return True

        if self.asset_type == AssetType.SPRITE_STRIP:
            metadata = self.asset.metadata or {}
            frames = load_sprite_strip_frames(self.asset_path, metadata)
            if not frames:
                log_warning("No readable sprite strip frames in asset skipped: %s", self.asset_path)
                return False
            fps = metadata.get("fps", self.asset.fps or 8)
            loop = bool(metadata.get("loop", True))
            self.sprite_player = SpriteAnimationPlayer(frames, fps=fps, loop=loop, parent=self)
            self.sprite_player.set_speed(self.speed)
            self.sprite_player.pixmap_changed.connect(self.update_from_sprite_player)
            self.current_pixmap = frames[0]
            self.base_size = self.current_pixmap.size()
            self.apply_scale()
            return True

        if self.asset_type == AssetType.SPRITESHEET:
            metadata = self.asset.metadata or {}
            frames, fps, loop, selected_name = load_spritesheet_frames(self.asset_path, metadata, self.current_animation)
            if not frames:
                log_warning("No readable spritesheet frames in asset skipped: %s", self.asset_path)
                return False
            self.current_animation = selected_name
            self.sprite_player = SpriteAnimationPlayer(frames, fps=fps, loop=loop, parent=self)
            self.sprite_player.set_speed(self.speed)
            self.sprite_player.pixmap_changed.connect(self.update_from_sprite_player)
            self.current_pixmap = frames[0]
            self.base_size = self.current_pixmap.size()
            self.apply_scale()
            return True

        if self.asset_type == AssetType.COMPOSITE_UI:
            metadata = self._composite_metadata_with_runtime_values()
            self.composite_renderer = CompositeUIRenderer(self.asset_path, metadata)
            if not self.composite_renderer.layers:
                log_warning("No readable composite_ui layers in asset skipped: %s", self.asset_path)
                return False
            self.current_pixmap = self.composite_renderer.render()
            self.base_size = self.current_pixmap.size()
            self.apply_scale()
            return True

        return False

    def start_playback(self):
        if self.movie is not None:
            self.movie.start()
            self.update_from_movie()
            if self.prefers_calm_static_idle():
                self.movie.stop()
        if self.frame_player is not None:
            calm_idle = self.prefers_calm_static_idle() and self.animation_video_source("idle") is None
            self.frame_player.start()
            if self.current_frame_animation == "idle" and calm_idle:
                self.frame_player.stop()
            self.play_animation_audio(
                self.current_frame_animation or "idle",
                not calm_idle,
            )
        video_action_player = getattr(self, "video_action_player", None)
        if video_action_player is not None:
            source = self.animation_video_source(self.current_frame_animation or "idle")
            if source is not None:
                video_action_player.play(source, loop=True, speed=self.speed)
        if self.sprite_player is not None:
            self.sprite_player.start()
            if self.current_frame_animation == "idle" and self.prefers_calm_static_idle():
                self.sprite_player.stop()
        video_player = getattr(self, "video_player", None)
        if video_player is not None:
            video_player.play(self.asset_path, loop=True, speed=self.speed)

    def idle_variant_names(self):
        asset = getattr(self, "asset", None)
        meta = getattr(asset, "metadata", {}) or {}
        if meta.get("fixed_idle") is False:
            variants = meta.get("idle_variants")
            if isinstance(variants, list) and variants:
                return [v for v in variants if v in self.available_animations()]
        return []

    def schedule_next_idle_variant(self):
        if self.head_track_enabled and len(self.head_track_frames) == 25:
            self.idle_variant_timer.stop()
            return
        if self.prefers_calm_static_idle():
            self.idle_variant_timer.stop()
            return
        variants = self.idle_variant_names()
        if not variants:
            self.idle_variant_timer.stop()
            return
        self.idle_variant_timer.start(random.randint(6500, 14000))

    def play_random_idle_variant(self):
        if self.head_track_enabled and len(self.head_track_frames) == 25:
            self.schedule_next_idle_variant()
            return
        variants = self.idle_variant_names()
        if (
            not variants
            or self.is_dragging_asset
            or self.screen_saver_active
            or self.current_frame_animation != "idle"
            or not self.isVisible()
        ):
            self.schedule_next_idle_variant()
            return
        self.play_frame_animation(random.choice(variants), loop=False, return_to_idle=True)

    def behavior_action(self, event_name):
        if self.asset_type not in {AssetType.FRAME_ANIMATION, AssetType.SPRITESHEET}:
            return None
        return resolve_behavior_action(self.asset.metadata or {}, event_name, self.available_animations())

    def play_behavior_event(self, event_name):
        # Behavior-pack actions are now manual entries in the Action menu.
        # Screen saver and startup state changes must not trigger a pet action.
        return False

    def play_startup_behavior(self):
        return False

    def enter_screen_saver_sleep(self):
        if self.asset_type not in {AssetType.FRAME_ANIMATION, AssetType.SPRITESHEET}:
            return False
        self.screen_saver_active = True
        self.play_idle_animation()
        return False

    def exit_screen_saver_sleep(self):
        was_active = self.screen_saver_active
        self.screen_saver_active = False
        if was_active:
            self.play_idle_animation()
        return False

    def apply_window_flags(self):
        was_visible = self.isVisible()
        pos = self.pos()
        flags = Qt.FramelessWindowHint | Qt.Tool | Qt.NoDropShadowWindowHint
        if self.always_on_top:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.move(self.clamped_position(pos))
        self.apply_click_through()
        if was_visible:
            self.show()
            self.raise_()
        remove_native_border(self)

    def apply_click_through(self):
        self.setAttribute(Qt.WA_TransparentForMouseEvents, self.click_through)
        self.update()

    def physics_time_seconds(self):
        return time.monotonic()

    def available_geometry(self):
        screen = QApplication.primaryScreen()
        return work_area_for_screen(screen) if screen else None

    def visible_screen_geometry(self):
        screens = QApplication.screens()
        if not screens:
            return None

        geometry = QRect()
        for screen in screens:
            work_area = work_area_for_screen(screen)
            geometry = geometry.united(work_area) if geometry.isValid() else work_area
        return geometry

    def centered_on_primary_screen(self):
        geometry = self.available_geometry()
        if geometry is None:
            return QPoint(100, 100)

        return QPoint(
            geometry.left() + max(0, (geometry.width() - max(1, self.width())) // 2),
            geometry.top() + max(0, (geometry.height() - max(1, self.height())) // 2),
        )

    def restored_position(self, pos):
        visible_geometry = self.visible_screen_geometry()
        if visible_geometry is None:
            return pos

        window_rect = QRect(pos, self.size())
        if not window_rect.intersects(visible_geometry):
            return self.clamped_position(self.centered_on_primary_screen())

        return self.clamped_position(pos)

    def clamped_position(self, pos):
        geometry = self.visible_screen_geometry()
        if geometry is None:
            return pos

        max_x = max(geometry.left(), geometry.right() - max(1, self.width()) + 1)
        max_y = max(geometry.top(), geometry.bottom() - max(1, self.height()) + 1)
        x = min(max(pos.x(), geometry.left()), max_x)
        y = min(max(pos.y(), geometry.top()), max_y)
        return QPoint(x, y)

    def screen_geometry_for_window(self):
        window_rect = QRect(self.pos(), self.size())
        for screen_item in QApplication.screens():
            if window_rect.intersects(screen_item.geometry()):
                return work_area_for_screen(screen_item)
        center = self.pos() + QPoint(max(1, self.width()) // 2, max(1, self.height()) // 2)
        screen = QApplication.screenAt(center)
        if screen is None and QApplication.primaryScreen() is not None:
            screen = QApplication.primaryScreen()
        if screen is not None:
            return work_area_for_screen(screen)
        return self.visible_screen_geometry()

    def base_visible_head_size(self):
        if self.character_id in {"logoguineapigpet", "logo-guinea-pig"}:
            return min(72, max(58, round(min(max(1, self.width()), max(1, self.height())) * 0.34)))
        return min(170, max(82, round(min(max(1, self.width()), max(1, self.height())) * 0.42)))

    def current_content_rect(self):
        pixmap = self.current_pixmap
        if pixmap.isNull():
            return None

        cache_key = (pixmap.cacheKey(), pixmap.width(), pixmap.height())
        if cache_key == self.current_pixmap_content_cache_key:
            return self.current_pixmap_content_rect

        image = pixmap.toImage()
        width = image.width()
        height = image.height()
        left = width
        top = height
        right = -1
        bottom = -1

        for y in range(height):
            for x in range(width):
                if image.pixelColor(x, y).alpha() > 8:
                    left = min(left, x)
                    top = min(top, y)
                    right = max(right, x)
                    bottom = max(bottom, y)

        self.current_pixmap_content_cache_key = cache_key
        if right < left or bottom < top:
            self.current_pixmap_content_rect = None
        else:
            self.current_pixmap_content_rect = QRect(left, top, right - left + 1, bottom - top + 1)
        return self.current_pixmap_content_rect

    def whip_hit_rect(self):
        rect = self.current_content_rect()
        pixmap = self.current_pixmap
        if rect is None or pixmap.isNull():
            return QRect(self.pos(), self.size()).adjusted(-10, -10, 10, 10)

        scale_x = self.width() / max(1, pixmap.width())
        scale_y = self.height() / max(1, pixmap.height())
        hit_rect = QRect(
            self.x() + round(rect.x() * scale_x),
            self.y() + round(rect.y() * scale_y),
            max(1, round(rect.width() * scale_x)),
            max(1, round(rect.height() * scale_y)),
        )
        return hit_rect.adjusted(-10, -10, 10, 10)

    def feather_touch_rect(self):
        return self.whip_hit_rect()

    def handle_whip_hit(self):
        now = time.monotonic()
        if now < self.whip_hit_cooldown_until:
            return False
        self.whip_hit_cooldown_until = now + 0.9
        return False

    def handle_feather_touch(self):
        return False

    def visible_edge_size(self, mode=None):
        mode = mode or self.dock_mode or "bottom"
        desired_visible_content = self.base_visible_head_size()
        rect = self.current_content_rect()
        pixmap = self.current_pixmap
        if rect is None or pixmap.isNull():
            return desired_visible_content

        width = max(1, self.width())
        height = max(1, self.height())
        pixmap_width = max(1, pixmap.width())
        pixmap_height = max(1, pixmap.height())
        scale_x = width / pixmap_width
        scale_y = height / pixmap_height

        if mode == "bottom":
            transparent_padding = round(rect.top() * scale_y)
            axis_size = height
            if self.current_frame_animation in EDGE_CRAWL_ANIMATIONS:
                desired_visible_content = round(rect.height() * scale_y)
        elif mode == "top":
            transparent_padding = round((pixmap_height - rect.bottom() - 1) * scale_y)
            axis_size = height
            if self.current_frame_animation in EDGE_CRAWL_ANIMATIONS:
                desired_visible_content = round(rect.height() * scale_y)
        elif mode == "right":
            transparent_padding = round(rect.left() * scale_x)
            axis_size = width
            if self.current_frame_animation in EDGE_CRAWL_ANIMATIONS:
                desired_visible_content = round(rect.width() * scale_x)
        elif mode == "left":
            transparent_padding = round((pixmap_width - rect.right() - 1) * scale_x)
            axis_size = width
            if self.current_frame_animation in EDGE_CRAWL_ANIMATIONS:
                desired_visible_content = round(rect.width() * scale_x)
        else:
            transparent_padding = 0
            axis_size = min(width, height)

        return min(axis_size, max(1, transparent_padding + desired_visible_content))

    def visible_head_size(self):
        return self.visible_edge_size(self.dock_mode or "bottom")

    def prefers_calm_static_idle(self):
        asset = getattr(self, "asset", None)
        meta = getattr(asset, "metadata", {}) or {}
        if meta.get("fixed_idle") is False:
            return False
        return True

    def edge_crawl_animation_name(self):
        if self.dock_mode in {"top", "bottom", "left", "right"}:
            return f"edge-crawl-{self.dock_mode}"
        return ""

    def docked_position(self, pos, mode):
        geometry = self.screen_geometry_for_window()
        if geometry is None:
            return self.clamped_position(pos)
        visible = self.visible_edge_size(mode)
        if mode == "bottom":
            x = min(max(pos.x(), geometry.left()), max(geometry.left(), geometry.right() - self.width() + 1))
            return QPoint(x, geometry.bottom() - visible + 1)
        if mode == "top":
            x = min(max(pos.x(), geometry.left()), max(geometry.left(), geometry.right() - self.width() + 1))
            return QPoint(x, geometry.top() - self.height() + visible)
        if mode == "left":
            y = min(max(pos.y(), geometry.top()), max(geometry.top(), geometry.bottom() - self.height() + 1))
            return QPoint(geometry.left() - self.width() + visible, y)
        if mode == "right":
            y = min(max(pos.y(), geometry.top()), max(geometry.top(), geometry.bottom() - self.height() + 1))
            return QPoint(geometry.right() - visible + 1, y)
        return self.clamped_position(pos)

    def snap_position_if_near_edge(self, pos):
        """Legacy compatibility helper; edge docking is intentionally disabled."""
        self.drag_released_at_top_edge = False
        self.dock_mode = "none"
        return self.clamped_position(pos)

    def play_edge_crawl_animation(self):
        animation_name = self.edge_crawl_animation_name()
        if not animation_name:
            return False
        if self.play_frame_animation(animation_name, loop=False, return_to_idle=False):
            self.move(self.docked_position(self.pos(), self.dock_mode))
            return True
        self.play_docked_idle_fallback()
        self.move(self.docked_position(self.pos(), self.dock_mode))
        return False

    def play_docked_idle_fallback(self):
        if self.asset_type not in {AssetType.FRAME_ANIMATION, AssetType.SPRITESHEET}:
            return False
        played = self.play_frame_animation("idle", loop=True, return_to_idle=False)
        self.idle_variant_timer.stop()
        return played

    def is_near_top_edge(self):
        return False

    def begin_temporary_fall_from_top(self):
        geometry = self.screen_geometry_for_window()
        if geometry is None:
            return False
        x = min(max(self.pos().x(), geometry.left()), max(geometry.left(), geometry.right() - self.width() + 1))
        self.move(QPoint(x, geometry.top()))
        self.dock_mode = "none"
        self.temporary_fall_enabled = True
        self.top_drop_target_y = max(geometry.top(), geometry.bottom() - self.height() + 1)
        self.top_drop_last_tick = None
        self.physics.set_enabled(False)
        self.play_idle_animation()
        self.top_drop_timer.start()
        return True

    def step_top_drop(self):
        if not self.temporary_fall_enabled:
            self.top_drop_timer.stop()
            return
        geometry = self.screen_geometry_for_window()
        if geometry is not None:
            self.top_drop_target_y = max(geometry.top(), geometry.bottom() - self.height() + 1)
        now = self.physics_time_seconds()
        if self.top_drop_last_tick is None:
            self.top_drop_last_tick = now
            return
        elapsed = min(0.08, max(0.0, now - self.top_drop_last_tick))
        self.top_drop_last_tick = now
        next_y = min(self.top_drop_target_y, round(self.pos().y() + 210.0 * elapsed))
        if next_y != self.pos().y():
            self.move(QPoint(self.pos().x(), next_y))
        if next_y >= self.top_drop_target_y:
            self.finish_top_drop()

    def finish_top_drop(self):
        self.top_drop_timer.stop()
        self.temporary_fall_enabled = False
        self.top_drop_last_tick = None
        if self.physics_enabled:
            self.physics.set_enabled(True)
        self.play_idle_animation()
        save_config()

    def undock_for_drag(self):
        self.dock_mode = "none"
        self.move(self.clamped_position(self.pos()))
        save_config()

    def config_int(self, config, key, default):
        try:
            return int(config.get(key, default))
        except (TypeError, ValueError):
            return default

    def format_timer(self):
        seconds = max(0, int(self.timer_seconds))
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    def set_timer_seconds(self, seconds):
        self.timer_seconds = min(24 * 3600, max(60, int(seconds)))
        self.timer_done = False
        self.update()
        save_config()

    def adjust_timer_minutes(self, minutes):
        self.timer_visible = True
        self.focus_mode = FOCUS_MODE_CUSTOM
        self.set_timer_seconds(self.timer_seconds + int(minutes) * 60)

    def toggle_timer_visible(self):
        self.timer_visible = not self.timer_visible
        self.update()
        save_config()

    def start_or_pause_timer(self):
        self.timer_visible = True
        self.timer_done = False
        self.timer_running = not self.timer_running
        if self.timer_running:
            self.countdown_timer.start()
        else:
            self.countdown_timer.stop()
        self.update()
        save_config()

    def reset_timer(self):
        self.timer_running = False
        self.timer_done = False
        self.focus_mode = FOCUS_MODE_CUSTOM
        self.countdown_timer.stop()
        self.set_timer_seconds(5 * 60)

    def tick_countdown(self):
        if not self.timer_running:
            return
        self.timer_seconds = max(0, self.timer_seconds - 1)
        if self.timer_seconds <= 0:
            self.complete_countdown()
        self.update()
        save_config()

    def start_preset_timer(self, seconds, focus_mode):
        self.timer_visible = True
        self.timer_seconds = min(24 * 3600, max(60, int(seconds)))
        self.focus_mode = normalize_focus_mode(focus_mode)
        self.timer_done = False
        self.timer_running = True
        self.countdown_timer.start()
        self.update()
        save_config()

    def start_focus_session(self):
        self.start_preset_timer(25 * 60, FOCUS_MODE_FOCUS)
        self.show_focus_message("专注开始", "25 分钟专注开始")

    def start_break_session(self):
        self.start_preset_timer(5 * 60, FOCUS_MODE_BREAK)
        self.show_focus_message("休息开始", "5 分钟休息开始")

    def complete_countdown(self):
        if self.timer_done:
            return
        self.timer_running = False
        self.timer_done = True
        self.countdown_timer.stop()
        if should_count_focus_session(self.focus_mode):
            self.focus_sessions_completed += 1
        self.trigger_reward("timer")
        self.show_focus_message("计时完成", completion_message(self.focus_mode, self.focus_sessions_completed))

    def complete_current_task(self):
        if not self.memo_text:
            self.edit_memo()
            if not self.memo_text:
                return
        self.memo_visible = True
        self.memo_checked = True
        self.timer_done = True
        self.update()
        save_config()
        self.trigger_reward("task")
        self.show_focus_message("任务完成", self.memo_text[:80] or "当前任务已完成")

    def trigger_reward(self, reason):
        return []

    def show_focus_message(self, title, message):
        tray = state.TRAY_ICON
        if tray is None:
            return
        try:
            icon = getattr(QSystemTrayIcon, "Information", QSystemTrayIcon.MessageIcon.Information)
            tray.showMessage(str(title), str(message), icon, 4000)
        except Exception as exc:
            log_warning("Focus tray notification failed: %s", exc)

    def parse_power_due_at(self):
        if not self.power_action_due_at:
            return None
        try:
            return datetime.fromisoformat(self.power_action_due_at)
        except ValueError:
            return None

    def format_power_due_at(self):
        due = self.parse_power_due_at()
        if due is None:
            return ""
        now = datetime.now()
        label = "今天" if due.date() == now.date() else "明天" if due.date() == (now + timedelta(days=1)).date() else due.strftime("%m-%d")
        return f"{label} {due:%H:%M}"

    def power_action_label(self):
        return "关机" if self.power_action_type == "shutdown" else "待机" if self.power_action_type == "sleep" else ""

    def set_power_schedule(self, action_type, due_at):
        self.power_action_type = str(action_type)
        self.power_action_due_at = due_at.isoformat(timespec="seconds")
        self.update()
        save_config()

    def confirm_power_schedule(self, action_type, due_at):
        label = "关机" if action_type == "shutdown" else "待机"
        result = QMessageBox.question(
            self,
            "电源计划",
            f"确定设置为 {due_at:%Y-%m-%d %H:%M} 自动{label}吗？\n到时间后会直接执行，请先保存正在编辑的文件。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result == QMessageBox.Yes:
            self.set_power_schedule(action_type, due_at)

    def choose_power_action(self):
        action, ok = QInputDialog.getItem(self, "电源计划", "选择要执行的动作：", ["待机", "关机"], 0, False)
        if not ok:
            return None
        return "shutdown" if action == "关机" else "sleep"

    def schedule_power_after_minutes(self):
        action_type = self.choose_power_action()
        if action_type is None:
            return
        minutes, ok = QInputDialog.getInt(self, "多久之后执行", "多少分钟之后执行：", 30, 1, 24 * 60, 1)
        if ok:
            self.confirm_power_schedule(action_type, datetime.now() + timedelta(minutes=minutes))

    def schedule_power_at_time(self):
        action_type = self.choose_power_action()
        if action_type is None:
            return
        text, ok = QInputDialog.getText(self, "具体时间执行", "输入时间，例如 23:30：", text=datetime.now().strftime("%H:%M"))
        if not ok:
            return
        try:
            hour_text, minute_text = text.strip().split(":", 1)
            hour = int(hour_text)
            minute = int(minute_text)
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "电源计划", "时间格式不对，请输入类似 23:30 的格式。")
            return
        now = datetime.now()
        due_at = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if due_at <= now:
            due_at += timedelta(days=1)
        self.confirm_power_schedule(action_type, due_at)

    def cancel_power_schedule(self):
        self.power_action_type = ""
        self.power_action_due_at = ""
        self.update()
        save_config()

    def check_power_schedule(self):
        due_at = self.parse_power_due_at()
        if not self.power_action_type or due_at is None:
            return
        if datetime.now() < due_at:
            self.update()
            return
        action_type = self.power_action_type
        self.cancel_power_schedule()
        self.execute_power_action(action_type)

    def execute_power_action(self, action_type):
        if sys.platform != "win32":
            QMessageBox.warning(self, "电源计划", "当前只实现了 Windows 待机/关机命令。")
            return
        try:
            if action_type == "shutdown":
                subprocess.Popen(["shutdown", "/s", "/t", "0"], creationflags=subprocess.CREATE_NO_WINDOW)
                return
            if action_type == "sleep":
                command = (
                    "Add-Type -AssemblyName System.Windows.Forms; "
                    "[System.Windows.Forms.Application]::SetSuspendState('Suspend',$false,$false)"
                )
                subprocess.Popen(
                    ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", command],
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )
        except Exception as exc:
            log_warning("Power action failed: %s", exc)
            QMessageBox.warning(self, "电源计划", f"执行失败：{exc}")

    def accessory_definitions(self):
        accessories = (self.asset.metadata or {}).get("accessories")
        return accessories if isinstance(accessories, dict) else {}

    def accessory_display_name(self, key, definition):
        return str(definition.get("name") or key)

    def toggle_accessory(self, key):
        key = str(key)
        if key in self.enabled_accessories:
            self.enabled_accessories = [item for item in self.enabled_accessories if item != key]
        else:
            self.enabled_accessories.append(key)
        self.update()
        save_config()

    def accessory_pixmap(self, key, definition):
        if key in self.accessory_cache:
            return self.accessory_cache[key]
        image = definition.get("image") if isinstance(definition, dict) else None
        if not image:
            return QPixmap()
        pixmap = QPixmap(str(self.asset_path / str(image)))
        self.accessory_cache[key] = pixmap
        return pixmap

    def accessory_offset(self, definition):
        offsets = definition.get("animation_offsets") if isinstance(definition, dict) else None
        if not isinstance(offsets, dict):
            return 0, 0
        offset = offsets.get(self.current_frame_animation) or offsets.get("idle") or {}
        if not isinstance(offset, dict):
            return 0, 0
        return int(offset.get("x", 0)), int(offset.get("y", 0))

    def get_notchnotes_window(self):
        if self.notchnotes_window is None:
            from .notchnotes_window import NotchNotesWindow
            from .notchnotes_store import NotchNotesStore
            self.notchnotes_window = NotchNotesWindow(store=NotchNotesStore.get_instance())
            self.notchnotes_window.all_tasks_completed.connect(self._on_notchnotes_all_completed)
        return self.notchnotes_window

    def toggle_notchnotes(self):
        w = self.get_notchnotes_window()
        if w.isVisible():
            if w._is_unfolded:
                w.toggle_unfold()
            else:
                w.show()
                w.raise_()
                w.activateWindow()
        else:
            pet_pos = self.mapToGlobal(QPoint(0, 0))
            screen = QApplication.primaryScreen()
            screen_geom = screen.availableGeometry() if screen else QRect(0, 0, 1920, 1080)
            target_x = pet_pos.x() + self.width() + 15
            target_y = pet_pos.y() - 30
            if target_x + w.width() > screen_geom.right():
                target_x = max(screen_geom.left() + 10, pet_pos.x() - w.width() - 15)
            if target_y + w.height() > screen_geom.bottom():
                target_y = max(screen_geom.top() + 20, screen_geom.bottom() - w.height() - 20)
            if target_y < screen_geom.top():
                target_y = screen_geom.top() + 20

            w.move(target_x, target_y)
            w.show()
            w.raise_()
            w.activateWindow()

    def _on_notchnotes_all_completed(self):
        self.trigger_reward("task")
        for act in ("dance", "wave", "cheer", "happy", "reward"):
            if self.play_named_action(act):
                break
        self.show_focus_message("🎉 任务全部达成！", "NotchNotes 中的所有待办事项均已勾选完成，太棒了！")

    def quick_add_todo_task(self):
        text, ok = QInputDialog.getText(self, "添加待办任务", "输入待办事项内容：")
        if ok and text.strip():
            from .notchnotes_store import NotchNotesStore
            store = NotchNotesStore.get_instance()
            store.add_todo_item(text.strip())
            self.memo_visible = True
            if self.notchnotes_window and self.notchnotes_window.isVisible():
                self.notchnotes_window.refresh_todo_list()
            self.update()
            save_config()
            self.show_focus_message("待办已记录", f"已添加待办：{text.strip()}")

    def toggle_memo_visible(self):
        self.memo_visible = not self.memo_visible
        self.update()
        save_config()

    def edit_memo(self):
        text, ok = QInputDialog.getMultiLineText(self, "备忘便签", "写下便签内容：", self.memo_text)
        if not ok:
            return
        self.memo_text = text.strip()[:220]
        self.memo_visible = bool(self.memo_text)
        if not self.memo_text:
            self.memo_checked = False
        self.update()
        save_config()

    def toggle_memo_checked(self):
        if not self.memo_text:
            return
        self.memo_checked = not self.memo_checked
        self.memo_visible = True
        self.update()
        save_config()

    def clear_memo(self):
        self.memo_text = ""
        self.memo_visible = False
        self.memo_checked = False
        try:
            from .notchnotes_store import NotchNotesStore
            store = NotchNotesStore.get_instance()
            store.set_content("todo", "# 待办清单\n\n")
            if self.notchnotes_window and self.notchnotes_window.isVisible():
                self.notchnotes_window.refresh_todo_list()
        except Exception:
            pass
        self.update()
        save_config()

    def update_from_movie(self):
        pixmap = self.movie.currentPixmap()
        self.set_current_pixmap(pixmap)

    def update_from_frame_player(self, pixmap):
        self.set_current_pixmap(pixmap)

    def update_from_sprite_player(self, pixmap):
        self.set_current_pixmap(pixmap)

    def update_from_video_player(self, pixmap):
        self.set_current_pixmap(pixmap)

    def keep_docked_position_after_frame_change(self):
        if self.initializing_position or self.dock_mode == "none":
            return
        self.move(self.docked_position(self.pos(), self.dock_mode))

    def frame_animation_definition(self, name):
        metadata = self.asset.metadata or {}
        animations = metadata.get("animations")
        if name != "idle" and (not isinstance(animations, dict) or name not in animations):
            return [], self.asset.fps or 12, False
        definition = animations.get(name, {}) if isinstance(animations, dict) else {}
        if not isinstance(definition, dict):
            definition = {}

        folder_name = str(definition.get("folder") or ".")
        folder = self.asset_path if folder_name in {"", "."} else self.asset_path / folder_name
        frame_paths = frame_paths_for_folder(folder)
        if not frame_paths and name != "idle":
            return [], self.asset.fps or 12, False
        if not frame_paths:
            frame_paths = frame_paths_for_folder(self.asset_path)

        fps = self.config_int(definition, "fps", self.asset.fps or 12)
        loop = bool(definition.get("loop", name == "idle"))
        return frame_paths, fps, loop

    def animation_video_source(self, name):
        """Resolve the optional original video that supplies an action's sound."""
        if self.asset_type != AssetType.FRAME_ANIMATION:
            return None
        metadata = self.asset.metadata or {}
        animations = metadata.get("animations")
        definition = animations.get(name, {}) if isinstance(animations, dict) else {}
        if not isinstance(definition, dict):
            definition = {}

        source_value = definition.get("video") or definition.get("video_source")
        video_sources = metadata.get("video_sources")
        if not source_value and isinstance(video_sources, dict):
            source_value = video_sources.get(name)
        candidates = []
        if isinstance(source_value, str) and source_value.strip():
            source_path = Path(source_value.strip())
            candidates.extend(
                [source_path]
                if source_path.is_absolute()
                else [self.asset_path / source_path, self.asset_path.parent / source_path]
            )

        folder_name = str(definition.get("folder") or ".")
        folder = self.asset_path if folder_name in {"", "."} else self.asset_path / folder_name
        candidates.extend(video_sources_for_folder(folder))
        for candidate in candidates:
            candidate = Path(candidate).resolve()
            if candidate.is_file():
                return candidate
        return None

    def play_animation_audio(self, name, loop):
        source = self.animation_video_source(name)
        if source is None:
            if self.video_audio_player is not None:
                self.video_audio_player.stop()
            return False
        if self.video_audio_player is None:
            self.video_audio_player = VideoAudioPlayer(self, muted=self.sound_muted)
        else:
            self.video_audio_player.set_muted(self.sound_muted)
        return self.video_audio_player.play(source, loop=loop, speed=self.speed)

    def play_frame_animation(self, name, *, loop=None, return_to_idle=True):
        if self.asset_type == AssetType.SPRITESHEET:
            return self.play_spritesheet_animation(name, loop=loop, return_to_idle=return_to_idle)
        if self.asset_type == AssetType.VIDEO:
            if self.video_player is None:
                return False
            self.animation_duration_timer.stop()
            self.current_frame_animation = str(name)
            self.current_animation = str(name)
            playback_loop = True if loop is None else bool(loop)
            self.return_to_idle_after_animation = bool(return_to_idle)
            return self.video_player.play(self.asset_path, loop=playback_loop, speed=self.speed)
        if self.asset_type != AssetType.FRAME_ANIMATION:
            return False

        frame_paths, fps, default_loop = self.frame_animation_definition(name)
        video_source = self.animation_video_source(name)
        if not frame_paths:
            if video_source is None:
                return False
            if self.frame_player is not None:
                self.frame_player.stop()
            if self.video_action_player is None:
                self.video_action_player = VideoMediaPlayer(self)
                self.video_action_player.frame_changed.connect(self.update_from_video_player)
                self.video_action_player.finished.connect(self.frame_animation_finished)
            self.animation_duration_timer.stop()
            self.current_frame_animation = str(name)
            self.current_animation = str(name)
            if name != "idle":
                self.idle_variant_timer.stop()
            duration_seconds = self.frame_animation_duration_seconds(name)
            timed_action = duration_seconds > 0 and name != "idle"
            self.return_to_idle_after_animation = bool(return_to_idle)
            playback_loop = True if timed_action else (default_loop if loop is None else loop)
            self.video_action_player.play(video_source, loop=playback_loop, speed=self.speed)
            if timed_action:
                self.animation_duration_timer.start(round(duration_seconds * 1000))
            return True

        if self.frame_player is None:
            return False
        if self.video_action_player is not None:
            self.video_action_player.stop()

        self.animation_duration_timer.stop()
        self.current_frame_animation = name
        self.current_animation = str(name)
        if name != "idle":
            self.idle_variant_timer.stop()
        duration_seconds = self.frame_animation_duration_seconds(name)
        timed_action = duration_seconds > 0 and name != "idle"
        self.return_to_idle_after_animation = bool(return_to_idle)
        playback_loop = True if timed_action else (default_loop if loop is None else loop)
        self.frame_player.set_frames(frame_paths, fps=fps, loop=playback_loop)
        self.frame_player.set_speed(self.speed)
        self.frame_player.start()
        if name == "idle" and self.prefers_calm_static_idle() and video_source is None:
            self.frame_player.stop()
        calm_idle = self.prefers_calm_static_idle() and video_source is None
        self.play_animation_audio(name, playback_loop and not calm_idle)
        if timed_action:
            self.animation_duration_timer.start(round(duration_seconds * 1000))
        return True

    def spritesheet_animation_definition(self, name):
        metadata = self.asset.metadata or {}
        animations = metadata.get("animations")
        definition = animations.get(name, {}) if isinstance(animations, dict) else {}
        return definition if isinstance(definition, dict) else {}

    def play_spritesheet_animation(self, name, *, loop=None, return_to_idle=True):
        if self.asset_type != AssetType.SPRITESHEET:
            return False

        frames, fps, default_loop, selected_name = load_spritesheet_frames(
            self.asset_path,
            self.asset.metadata or {},
            name,
        )
        if not frames:
            return False

        if self.sprite_player is not None:
            self.sprite_player.stop()
            self.sprite_player.deleteLater()

        self.animation_duration_timer.stop()
        self.current_frame_animation = selected_name or str(name)
        self.current_animation = self.current_frame_animation
        if self.current_frame_animation != "idle":
            self.idle_variant_timer.stop()

        duration_seconds = self.frame_animation_duration_seconds(self.current_frame_animation)
        timed_action = duration_seconds > 0 and self.current_frame_animation != "idle"
        self.return_to_idle_after_animation = bool(return_to_idle)
        playback_loop = True if timed_action else (default_loop if loop is None else loop)

        self.sprite_player = SpriteAnimationPlayer(frames, fps=fps, loop=playback_loop, parent=self)
        self.sprite_player.set_speed(self.speed)
        self.sprite_player.pixmap_changed.connect(self.update_from_sprite_player)
        self.sprite_player.finished.connect(self.frame_animation_finished)
        self.current_pixmap = frames[0]
        self.base_size = self.current_pixmap.size()
        self.apply_scale()
        self.sprite_player.start()
        if self.current_frame_animation == "idle" and self.prefers_calm_static_idle():
            self.sprite_player.stop()
        if self.video_audio_player is not None:
            self.video_audio_player.stop()
        if self.video_action_player is not None:
            self.video_action_player.stop()
        if timed_action:
            self.animation_duration_timer.start(round(duration_seconds * 1000))
        return True

    def frame_animation_duration_seconds(self, name):
        metadata = self.asset.metadata or {}
        animations = metadata.get("animations")
        definition = animations.get(name, {}) if isinstance(animations, dict) else {}
        if not isinstance(definition, dict):
            return 0.0
        try:
            duration_seconds = max(0.0, float(definition.get("duration_seconds", 0) or 0))
        except (TypeError, ValueError):
            return 0.0
        return duration_seconds * self.frame_animation_repeat_count(name)

    def frame_animation_repeat_count(self, name):
        metadata = self.asset.metadata or {}
        animations = metadata.get("animations")
        definition = animations.get(name, {}) if isinstance(animations, dict) else {}
        if not isinstance(definition, dict):
            return 1
        try:
            return max(1, int(definition.get("repeat_count", 1) or 1))
        except (TypeError, ValueError):
            return 1

    def play_idle_animation(self):
        # Head-track roles allow idle playback; tick_head_track manages static/active switching.
        if self.asset_type == AssetType.FRAME_ANIMATION:
            self.animation_duration_timer.stop()
            calm_idle = self.prefers_calm_static_idle() and self.animation_video_source("idle") is None
            self.play_frame_animation("idle", loop=not calm_idle, return_to_idle=False)
            self.schedule_next_idle_variant()
        elif self.asset_type == AssetType.SPRITESHEET:
            self.animation_duration_timer.stop()
            self.play_spritesheet_animation("idle", loop=False, return_to_idle=False)
            self.schedule_next_idle_variant()
        elif self.asset_type == AssetType.VIDEO:
            self.current_frame_animation = "idle"
            self.current_animation = "idle"
            if self.video_player is not None:
                self.video_player.play(self.asset_path, loop=True, speed=self.speed)

    def finish_timed_frame_animation(self):
        if self.return_to_idle_after_animation:
            self.play_idle_animation()

    def frame_animation_finished(self):
        if self.return_to_idle_after_animation:
            self.play_idle_animation()
        elif self.current_frame_animation == "idle":
            self.schedule_next_idle_variant()

    def setup_head_track(self):
        # Load the 5x5 parameter grid frames for pointer-driven head tracking.
        frame_paths, _fps, _loop = self.frame_animation_definition("head_track")
        frames = []
        for path in frame_paths:
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                frames.append(pixmap)
        self.head_track_frames = frames
        self._head_last_cursor = None
        self._head_last_move_time = time.monotonic()
        self._head_neutral_index = 12  # grid_r2_c2 = center/front-facing pose
        if self.head_track_enabled and len(self.head_track_frames) == 25:
            # No idle animation for head-track-only pets; start at the neutral (center) frame.
            if self.frame_player is not None:
                self.frame_player.stop()
            self.current_frame_animation = "idle"
            self.head_track_index = self._head_neutral_index
            self.current_pixmap = self.head_track_frames[self._head_neutral_index]
            self.current_pixmap_content_cache_key = None
            self.head_track_timer.start()
            log_info("Head tracking enabled for %s (%d frames)", self.character_id, len(frames))

    def is_head_tracking_active(self):
        return (
            self.head_track_enabled
            and len(self.head_track_frames) == 25
            and self.current_frame_animation == "idle"
            and not self.is_dragging_asset
            and not self.screen_saver_active
        )

    def tick_head_track(self):
        if not self.is_head_tracking_active():
            return
        center = self.frameGeometry().center()
        cursor = QCursor.pos()
        dx = cursor.x() - center.x()
        dy = cursor.y() - center.y()
        radius = max(120.0, min(self.width(), self.height()) * 2.2)
        dxn = max(-1.0, min(1.0, dx / radius))
        dyn = max(-1.0, min(1.0, dy / radius))
        col = max(0, min(4, int(round((dxn + 1) * 2))))
        row = max(0, min(4, int(round((dyn + 1) * 2))))
        index = row * 5 + col
        # Static head-track-only pet: no idle; neutral frame shown when cursor near center.
        if index != self.head_track_index:
            self.head_track_index = index
            self.current_pixmap = self.head_track_frames[index]
            self.current_pixmap_content_cache_key = None
            self.update()

    def clipped_layer_values(self):
        if self.asset_type != AssetType.COMPOSITE_UI:
            return {}
        values = {}
        for layer in (self.asset.metadata or {}).get("layers", []):
            if not isinstance(layer, dict):
                continue
            if str(layer.get("clip") or "").lower() not in {"horizontal", "vertical"}:
                continue
            name = str(layer.get("name") or layer.get("image") or "layer")
            values[name] = float(self.layer_values.get(name, layer.get("value", 1.0)))
        return values

    def available_animations(self):
        animations = (self.asset.metadata or {}).get("animations")
        if self.asset_type in {AssetType.FRAME_ANIMATION, AssetType.SPRITESHEET} and isinstance(animations, dict):
            return list(animations.keys())
        return []

    def animation_display_name(self, animation_name, fallback_label=""):
        animations = (self.asset.metadata or {}).get("animations")
        definition = animations.get(animation_name) if isinstance(animations, dict) else None
        if isinstance(definition, dict):
            for field in ("label", "display_name", "title"):
                value = definition.get(field)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        action_labels = (self.asset.metadata or {}).get("action_labels")
        if isinstance(action_labels, dict):
            value = action_labels.get(animation_name)
            if isinstance(value, str) and value.strip():
                return value.strip()
        if isinstance(fallback_label, str) and fallback_label.strip():
            return fallback_label.strip()
        legacy_label = DEFAULT_MANUAL_ACTION_LABELS.get(str(animation_name))
        if legacy_label:
            return legacy_label
        return str(animation_name).replace("-", " ").replace("_", " ").strip() or str(animation_name)

    def named_action_items(self):
        """Return extra animations that can be selected from the right-click menu."""
        if self.asset_type not in {AssetType.FRAME_ANIMATION, AssetType.SPRITESHEET}:
            return []

        binding_labels = {}
        bindings = (self.asset.metadata or {}).get("interaction_bindings")
        if isinstance(bindings, dict):
            for binding in bindings.values():
                if not isinstance(binding, dict):
                    continue
                items = binding.get("items")
                if not isinstance(items, list):
                    continue
                for item in items:
                    if not isinstance(item, dict):
                        continue
                    action_name = str(item.get("action") or item.get("id") or "").strip()
                    label = item.get("label")
                    if action_name and isinstance(label, str) and label.strip():
                        binding_labels.setdefault(action_name, label.strip())

        explicit_menu_actions = (self.asset.metadata or {}).get("menu_actions")
        if isinstance(explicit_menu_actions, list) and explicit_menu_actions:
            items = []
            for animation_name in explicit_menu_actions:
                name = str(animation_name)
                if name in self.available_animations():
                    items.append((name, self.animation_display_name(name, binding_labels.get(name, ""))))
            if items:
                return items

        items = []
        for animation_name in self.available_animations():
            name = str(animation_name)
            if (
                name in BASIC_ACTION_NAMES
                or name in MANUAL_ACTION_EXCLUDED_NAMES
                or name.startswith(MANUAL_ACTION_EXCLUDED_PREFIXES)
            ):
                continue
            items.append((name, self.animation_display_name(name, binding_labels.get(name, ""))))
        return items

    def play_named_action(self, animation_name):
        """Play one named extra action once, then return the pet to idle."""
        if self.click_through or self.screen_saver_active:
            return False
        name = str(animation_name or "").strip()
        if name not in {action_name for action_name, _label in self.named_action_items()}:
            return False
        return self.play_frame_animation(name, loop=False, return_to_idle=True)

    def set_layer_value(self, layer_name, value):
        if self.asset_type != AssetType.COMPOSITE_UI:
            return
        value = min(1.0, max(0.0, float(value)))
        self.layer_values[str(layer_name)] = value
        if self.composite_renderer is not None:
            self.current_pixmap = self.composite_renderer.set_layer_value(str(layer_name), value)
            self.update()
        save_config()

    def set_animation(self, animation_name):
        animations = (self.asset.metadata or {}).get("animations")
        if not isinstance(animations, dict) or animation_name not in animations:
            return False
        if self.asset_type == AssetType.FRAME_ANIMATION:
            frame_paths, _fps, default_loop = self.frame_animation_definition(animation_name)
            if not frame_paths:
                return False
            self.current_animation = str(animation_name)
            return self.play_frame_animation(animation_name, loop=default_loop, return_to_idle=not default_loop)
        if self.asset_type == AssetType.SPRITESHEET:
            definition = self.spritesheet_animation_definition(animation_name)
            default_loop = bool(definition.get("loop", animation_name == "idle"))
            return self.play_spritesheet_animation(animation_name, loop=default_loop, return_to_idle=not default_loop)
        return False

    def _reset_head_track_runtime(self):
        # 旧角色的转头帧和定时器不能跨角色存活，否则切换后仍会把画面覆盖回旧帧。
        self.head_track_timer.stop()
        self.head_track_frames = []
        self.head_track_index = -1

    def reload_asset_definition(self, new_asset_definition=None):
        old_state = {
            "asset": self.asset,
            "asset_path": self.asset_path,
            "asset_type": self.asset_type,
            "base_size": self.base_size,
            "current_pixmap": self.current_pixmap,
            "movie": self.movie,
            "frame_player": self.frame_player,
            "sprite_player": self.sprite_player,
            "video_player": getattr(self, "video_player", None),
            "video_audio_player": getattr(self, "video_audio_player", None),
            "video_action_player": getattr(self, "video_action_player", None),
            "composite_renderer": self.composite_renderer,
        }
        self.stop_playback()
        self._reset_head_track_runtime()
        if new_asset_definition is None:
            new_asset_definition = detect_asset(self.asset_path)
        if new_asset_definition is None:
            self._restore_renderer_state(old_state)
            self.setup_head_track()
            return False

        self.asset = new_asset_definition
        self.asset_path = Path(new_asset_definition.path).resolve()
        self.asset_type = new_asset_definition.type
        self.movie = None
        self.frame_player = None
        self.sprite_player = None
        self.video_player = None
        self.video_audio_player = None
        self.video_action_player = None
        self.composite_renderer = None
        self.current_pixmap = QPixmap()
        if not self.load_asset_content():
            self._restore_renderer_state(old_state)
            self.setup_head_track()
            log_warning("Overlay reload failed: %s", self.asset_path)
            return False
        self.start_playback()
        self.setup_head_track()
        self.update()
        log_info("Overlay reloaded: %s", self.asset_path)
        return True

    def stop_playback(self):
        if self.movie is not None:
            self.movie.stop()
        if self.frame_player is not None:
            self.frame_player.stop()
        if self.sprite_player is not None:
            self.sprite_player.stop()
        if self.video_player is not None:
            self.video_player.stop()
        if self.video_audio_player is not None:
            self.video_audio_player.stop()
        if self.video_action_player is not None:
            self.video_action_player.stop()

    def _restore_renderer_state(self, state_data):
        self.asset = state_data["asset"]
        self.asset_path = state_data["asset_path"]
        self.asset_type = state_data["asset_type"]
        self.base_size = state_data["base_size"]
        self.current_pixmap = state_data["current_pixmap"]
        self.movie = state_data["movie"]
        self.frame_player = state_data["frame_player"]
        self.sprite_player = state_data["sprite_player"]
        self.video_player = state_data.get("video_player")
        self.video_audio_player = state_data.get("video_audio_player")
        self.video_action_player = state_data.get("video_action_player")
        self.composite_renderer = state_data["composite_renderer"]
        self.start_playback()

    def _composite_metadata_with_runtime_values(self):
        metadata = dict(self.asset.metadata or {})
        layers = []
        for layer in metadata.get("layers", []):
            if not isinstance(layer, dict):
                continue
            layer_copy = dict(layer)
            name = str(layer_copy.get("name") or layer_copy.get("image") or "layer")
            if name in self.layer_values:
                layer_copy["value"] = self.layer_values[name]
            layers.append(layer_copy)
        metadata["layers"] = layers
        return metadata

    def set_current_pixmap(self, pixmap):
        size = pixmap.size()
        if size.isValid() and self.base_size != size:
            self.base_size = size
            self.apply_scale()
        self.current_pixmap = pixmap
        self.keep_docked_position_after_frame_change()
        self.update()

    def paintEvent(self, event):
        pixmap = self.current_pixmap
        if not pixmap.isNull():
            painter = QPainter(self)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.fillRect(self.rect(), Qt.transparent)
            painter.drawPixmap(self.rect(), pixmap)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            painter.setRenderHint(QPainter.Antialiasing, True)
            self.draw_accessories(painter)
            self.draw_status_overlays(painter)

    def draw_accessories(self, painter):
        if not self.enabled_accessories or not self.base_size.isValid():
            return
        sx = self.width() / max(1, self.base_size.width())
        sy = self.height() / max(1, self.base_size.height())
        for key in self.enabled_accessories:
            definition = self.accessory_definitions().get(str(key))
            if not isinstance(definition, dict):
                continue
            pixmap = self.accessory_pixmap(str(key), definition)
            if pixmap.isNull():
                continue
            dx, dy = self.accessory_offset(definition)
            scale = float(definition.get("scale", 1.0) or 1.0)
            x = (float(definition.get("x", 0)) + dx) * sx
            y = (float(definition.get("y", 0)) + dy) * sy
            pivot_x = float(definition.get("pivot_x", pixmap.width() / 2)) * sx * scale
            pivot_y = float(definition.get("pivot_y", pixmap.height() / 2)) * sy * scale
            width = max(1, round(pixmap.width() * sx * scale))
            height = max(1, round(pixmap.height() * sy * scale))
            painter.drawPixmap(round(x - pivot_x), round(y - pivot_y), width, height, pixmap)

    def draw_status_overlays(self, painter):
        self._sync_speech_bubble()

    def _speech_lines(self):
        lines = []
        if getattr(self, "_transient_speech", None):
            lines.append((self._transient_speech, getattr(self, "_transient_kind", "chat")))
        if self.power_action_type and self.power_action_due_at:
            lines.append((f"{self.power_action_label()} {self.format_power_due_at()}", "power"))
        if self.timer_visible:
            if self.timer_done:
                text = timer_done_text(self.focus_mode, self.focus_sessions_completed)
                lines.append((text, "timer_done"))
            else:
                text = f"{timer_prefix(self.focus_mode)} {self.format_timer()}"
                lines.append((text, "timer"))
        if self.memo_visible:
            display_text = ""
            try:
                from .notchnotes_store import NotchNotesStore
                store = NotchNotesStore.get_instance()
                top_task = store.get_top_pending_task()
                if top_task:
                    display_text = f"待办: {top_task}"
            except Exception:
                pass
            if not display_text and self.memo_text:
                display_text = self.memo_text
            if display_text:
                text = display_text.replace("\r", " ").replace("\n", " ").strip()
                if len(text) > 34:
                    text = text[:34] + "..."
                if text:
                    lines.append((text, "memo"))
        return lines

    def say(self, text, duration_ms=4500, kind="chat"):
        """Show an expressive speech bubble message over the pet's head."""
        self._transient_speech = str(text or "").strip()
        self._transient_kind = str(kind or "chat")
        self._sync_speech_bubble()
        if not hasattr(self, "_transient_speech_timer"):
            self._transient_speech_timer = QTimer(self)
            self._transient_speech_timer.setSingleShot(True)
            self._transient_speech_timer.timeout.connect(self._clear_transient_speech)
        self._transient_speech_timer.start(max(1000, duration_ms))

    def _clear_transient_speech(self):
        self._transient_speech = ""
        self._sync_speech_bubble()

    def _sync_speech_bubble(self):
        lines = self._speech_lines()
        if not lines:
            if self._speech_bubble is not None:
                self._speech_bubble.hide()
            return
        if self._speech_bubble is None:
            self._speech_bubble = SpeechBubbleWindow(self)
        if not self.isVisible():
            return
        self._speech_bubble.set_lines(lines)
        self._speech_bubble.reposition()
        if not self._speech_bubble.isVisible():
            self._speech_bubble.show()

    def apply_scale(self):
        if not self.base_size.isValid():
            return
        width = max(1, round(self.base_size.width() * self.scale / 100))
        height = max(1, round(self.base_size.height() * self.scale / 100))
        self.setFixedSize(width, height)
        if hasattr(self, "mic_badge"):
            self.mic_badge.move(max(0, self.width() - 34), 4)
        if self.initializing_position:
            return
        self.move(self.clamped_position(self.pos()))

    def trigger_animation_candidates(self, trigger_name):
        """Return the one fixed animation for each supported mouse operation."""
        trigger_name = str(trigger_name or "")
        custom_triggers = (getattr(self.asset, "metadata", {}) or {}).get("triggers")
        if isinstance(custom_triggers, dict) and trigger_name in custom_triggers:
            custom_action = custom_triggers.get(trigger_name)
            if custom_action and custom_action in self.available_animations():
                return [(custom_action, 1.0)]
        fallback = MOUSE_TRIGGER_ACTIONS.get(trigger_name)
        return [(fallback, 1.0)] if fallback else []

    def select_trigger_animation(self, trigger_name):
        candidates = self.trigger_animation_candidates(trigger_name)
        if not candidates:
            return None
        names, weights = zip(*candidates)
        return random.choices(names, weights=weights, k=1)[0]

    def bound_animation_names(self, trigger_name):
        return [name for name, _weight in self.trigger_animation_candidates(trigger_name) if name]

    def play_mouse_trigger_action(self, trigger_name, *, loop=False, return_to_idle=True):
        if self.click_through or self.screen_saver_active:
            return False
        animation_name = self.select_trigger_animation(trigger_name)
        if not animation_name:
            return False
        played = self.play_frame_animation(animation_name, loop=loop, return_to_idle=return_to_idle)
        if played:
            medal_store = getattr(state, "MEDAL_STORE", None)
            if medal_store is not None:
                changed = medal_store.record_trigger(str(trigger_name))
                character_id = str(getattr(self, "character_id", "") or "").strip()
                if character_id:
                    changed = medal_store.record_pet(character_id) or changed
                panel = getattr(state, "CONTROL_PANEL", None)
                if changed and panel is not None and hasattr(panel, "refresh_medals_page"):
                    panel.refresh_medals_page()
        return played

    def start_hover_reaction(self):
        return False

    def stop_hover_reaction(self, restore=True):
        return

    def enterEvent(self, event):
        super().enterEvent(event)

    def leaveEvent(self, event):
        super().leaveEvent(event)

    def trigger_offwork_celebration(self, target_scale=150, duration_seconds=300):
        """下班到点/右键触发欢庆仪式：支持桌面任意角色，平滑变大、随机执行专属动作、播放音乐(若有)、头顶冒出气泡字【下班了~】，点击缩回"""
        if getattr(self, "is_celebrating_offwork", False):
            return
        self.is_celebrating_offwork = True
        self._pre_celebration_scale = getattr(self, "scale", 50)
        self._pre_celebration_pos = self.pos()

        # 1. 头顶气泡弹出大字：下班了~ 🥳🎉 打工人解放啦！
        self.say("下班了~ 🥳🎉 打工人解放啦！", duration_ms=duration_seconds * 1000, kind="party")

        # 2. 动作触发：不限于特定角色，从该角色可用动作中随机抽取一个活跃动作进行表演
        metadata = getattr(self.asset, "metadata", {}) or {}
        animations = metadata.get("animations", {}) if isinstance(metadata.get("animations"), dict) else {}
        passive_keys = {"idle", "hover", "click", "drag", "fall", "land", "whip-hit", "feather-tickle", "feather-touch", "sleep"}
        celebration_candidates = [k for k in animations.keys() if k not in passive_keys]
        if not celebration_candidates:
            celebration_candidates = [k for k in animations.keys() if k != "idle"]

        chosen_anim = None
        if celebration_candidates:
            chosen_anim = random.choice(celebration_candidates)
            self.play_frame_animation(chosen_anim, loop=True, return_to_idle=False)
        else:
            self.play_idle_animation()

        # 3. 伴奏音乐播放（若素材包含音乐如水豚嘟嘟，或动作带有音频，自动循环播放）
        self._play_celebration_music(chosen_anim)

        # 4. 平滑放大插值动画 (从原始 scale 平滑变大到 target_scale)
        start_scale = self._pre_celebration_scale
        end_scale = max(target_scale, start_scale + 40)
        self._animate_scale(start_scale, end_scale, steps=12, interval_ms=25)

        # 5. 安全长时超时保护：默认保持放大跳舞，直到用户主动点击；若长时间无人点击，超时后自动安全缩回
        if not hasattr(self, "_offwork_auto_dismiss_timer"):
            self._offwork_auto_dismiss_timer = QTimer(self)
            self._offwork_auto_dismiss_timer.setSingleShot(True)
            self._offwork_auto_dismiss_timer.timeout.connect(self.dismiss_offwork_celebration)
        self._offwork_auto_dismiss_timer.start(duration_seconds * 1000)

    def _play_celebration_music(self, chosen_anim=None):
        """为欢庆仪式解析并播放专属 BGM 或动作音轨"""
        music_candidates = []
        if hasattr(self, "asset_path") and self.asset_path:
            p = Path(self.asset_path)
            if p.is_dir():
                for ext in ("*.wav", "*.mp3", "*.ogg", "*.m4a"):
                    music_candidates.extend(list(p.glob(ext)))

        metadata = getattr(self.asset, "metadata", {}) or {}
        declared_music = metadata.get("music_file") or metadata.get("audio") or metadata.get("sound")
        if declared_music and hasattr(self, "asset_path"):
            cand = Path(self.asset_path) / str(declared_music)
            if cand.is_file():
                music_candidates.insert(0, cand)

        if chosen_anim:
            action_source = self.animation_video_source(chosen_anim)
            if action_source is not None:
                music_candidates.append(action_source)

        for audio_file in music_candidates:
            if audio_file.is_file():
                if self.video_audio_player is None:
                    self.video_audio_player = VideoAudioPlayer(self, muted=self.sound_muted)
                else:
                    self.video_audio_player.set_muted(self.sound_muted)
                if self.video_audio_player.play(audio_file, loop=True, speed=self.speed):
                    return True
        return False

    def dismiss_offwork_celebration(self):
        """点击缩回：停止音乐、平滑缩回原尺寸，更新温情祝福并恢复日常待机"""
        if not getattr(self, "is_celebrating_offwork", False):
            return
        self.is_celebrating_offwork = False
        if hasattr(self, "_offwork_auto_dismiss_timer"):
            self._offwork_auto_dismiss_timer.stop()

        # 停止伴奏音乐
        if self.video_audio_player is not None:
            self.video_audio_player.stop()

        target_scale = getattr(self, "_pre_celebration_scale", 50)
        current_scale = getattr(self, "scale", 150)

        # 气泡更换为下班愉快
        self.say("下班了~ 祝今晚开心！👋🍻", duration_ms=4500, kind="party")

        # 平滑缩回动画
        self._animate_scale(
            current_scale,
            target_scale,
            steps=12,
            interval_ms=25,
            on_finished=self.play_idle_animation,
        )

    def _animate_scale(self, from_scale, to_scale, steps=12, interval_ms=25, on_finished=None):
        if not hasattr(self, "_scale_anim_timer"):
            self._scale_anim_timer = QTimer(self)
        else:
            self._scale_anim_timer.stop()
            try:
                self._scale_anim_timer.timeout.disconnect()
            except Exception:
                pass

        step_idx = 0
        diff = to_scale - from_scale
        center = self.geometry().center()

        def do_step():
            nonlocal step_idx
            step_idx += 1
            progress = min(1.0, step_idx / max(1, steps))
            # cubic ease out: 1 - (1 - t)^3
            ease = 1.0 - (1.0 - progress) ** 3
            current = int(round(from_scale + diff * ease))
            self.scale = current
            self.apply_scale()
            new_geom = self.geometry()
            new_geom.moveCenter(center)
            self.move(self.clamped_position(new_geom.topLeft()))

            if step_idx >= steps:
                self._scale_anim_timer.stop()
                self.scale = to_scale
                self.apply_scale()
                new_geom = self.geometry()
                new_geom.moveCenter(center)
                self.move(self.clamped_position(new_geom.topLeft()))
                save_config()
                if callable(on_finished):
                    on_finished()

        self._scale_anim_timer.timeout.connect(do_step)
        self._scale_anim_timer.start(interval_ms)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            if getattr(self, "is_celebrating_offwork", False):
                self.dismiss_offwork_celebration()
                event.accept()
                return
            custom_triggers = (getattr(self.asset, "metadata", {}) or {}).get("triggers")
            if isinstance(custom_triggers, dict) and custom_triggers.get("left-double-click"):
                self.play_mouse_trigger_action("left-double-click", loop=False, return_to_idle=True)
            if state.CONTROL_PANEL is not None:
                state.CONTROL_PANEL.select_window(self)
            event.accept()
            return
        if event.button() == Qt.RightButton:
            event.accept()
            return
        if event.button() == Qt.MiddleButton:
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event):
        if getattr(self, "is_celebrating_offwork", False) and event.button() == Qt.LeftButton:
            self.dismiss_offwork_celebration()
            event.accept()
            return

        if self.screen_saver_active and event.button() in {Qt.LeftButton, Qt.MiddleButton, Qt.RightButton}:
            self.screen_saver_active = False

        if event.button() == Qt.MiddleButton:
            event.accept()
            return

        if event.button() == Qt.LeftButton:
            self.drag_start_dock_mode = self.dock_mode
            self.drag_button = event.button()
            self.physics.pause_for_drag()
            self.press_global_pos = event.globalPosition().toPoint()
            self.is_dragging_asset = False
            self.drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return

        if event.button() == Qt.RightButton:
            self.open_menu(event.globalPosition().toPoint())
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.screen_saver_active:
            event.accept()
            return

        active_drag_button = self.drag_button
        if active_drag_button == Qt.LeftButton and event.buttons() & active_drag_button and not self.locked:
            if not self.is_dragging_asset:
                delta = event.globalPosition().toPoint() - self.press_global_pos
                drag_threshold = 6
                if delta.manhattanLength() < drag_threshold:
                    event.accept()
                    return
                self.is_dragging_asset = True
                self.play_mouse_trigger_action("left-drag", loop=True, return_to_idle=False)
            self.move(self.clamped_position(event.globalPosition().toPoint() - self.drag_offset))
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            event.accept()
            return

        if event.button() == Qt.LeftButton:
            if getattr(self, "is_celebrating_offwork", False):
                self.dismiss_offwork_celebration()
                event.accept()
                return

            released_drag_button = self.drag_button
            if self.is_dragging_asset:
                self.is_dragging_asset = False
                self.move(self.clamped_position(self.pos()))
                self.play_idle_animation()
                self.physics.resume_after_drag(force_landing_animation=False)
            else:
                if released_drag_button == event.button():
                    self.play_mouse_trigger_action("left-click", loop=False, return_to_idle=True)
                self.move(self.clamped_position(self.pos()))
                self.physics.start()
            self.drag_start_dock_mode = "none"
            self.drag_button = None
            save_config()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event):
        # Allow mouse wheel to zoom the pet directly if Ctrl is held
        modifiers_fn = getattr(event, "modifiers", None)
        if callable(modifiers_fn) and (modifiers_fn() & Qt.ControlModifier):
            delta_fn = getattr(event, "angleDelta", None)
            delta = delta_fn().y() if callable(delta_fn) else 0
            if delta > 0:
                self.set_scale(min(200, self.scale + 5))
            elif delta < 0:
                self.set_scale(max(20, self.scale - 5))
            event.accept()
            return
        event.accept()


    def contextMenuEvent(self, event):
        event.accept()

    def open_control_panel(self):
        if state.CONTROL_PANEL is not None:
            state.CONTROL_PANEL.show()
            state.CONTROL_PANEL.raise_()
            state.CONTROL_PANEL.activateWindow()

    def toggle_microphone_mute(self):
        new_muted = toggle_microphone_muted()
        if hasattr(self, "mic_badge"):
            self.mic_badge.update_state()
            self.mic_badge.show()
            self.mic_badge.raise_()
        for win in getattr(state, "WINDOWS", []):
            if win != self and hasattr(win, "mic_badge"):
                win.mic_badge.update_state()
        msg = "🤫 麦克风已闭麦" if new_muted else "🎙️ 麦克风已开麦"
        self.say(msg, duration_ms=2500)

    def toggle_sound_muted(self):
        """切换角色自身的声音静音状态 (刚下载时所有角色默认静音)"""
        self.sound_muted = not self.sound_muted
        if self.video_audio_player is not None:
            self.video_audio_player.set_muted(self.sound_muted)
        msg = "🔈 角色已静音" if self.sound_muted else "🔊 角色声音已开启"
        self.say(msg, duration_ms=2500)
        save_config()

    def open_menu(self, pos):
        if hasattr(self, "mic_badge"):
            self.mic_badge.reveal()

        menu = style_menu(QMenu(self))

        # 1. 软件控制台主页
        open_control_panel_action = QAction("🏠 打开 WindowPet 控制台", self)
        open_control_panel_action.triggered.connect(self.open_control_panel)
        menu.addAction(open_control_panel_action)

        # 麦克风闭麦 / 开麦一键控制
        is_muted = get_microphone_muted()
        mic_text = "🔇 麦克风已闭麦 (点击开麦)" if is_muted else "🎙️ 闭麦 (静音麦克风)"
        mic_action = QAction(mic_text, self)
        mic_action.triggered.connect(self.toggle_microphone_mute)
        menu.addAction(mic_action)

        # 角色自身声音静音/开启控制 (刚下载时所有角色默认静音)
        sound_text = "🔈 角色已静音 (点击开启声音)" if self.sound_muted else "🔊 角色声音已开启 (点击静音)"
        sound_action = QAction(sound_text, self)
        sound_action.triggered.connect(self.toggle_sound_muted)
        menu.addAction(sound_action)

        menu.addSeparator()

        # 2. 核心互动与动作类
        celebrate_action = QAction("🎉 欢庆时刻 (变大起舞)", self)
        celebrate_action.triggered.connect(lambda: self.trigger_offwork_celebration())
        menu.addAction(celebrate_action)

        whip_action = QAction("🪄 抽鞭子", self)
        whip_action.triggered.connect(lambda: show_whip_tool(self))
        menu.addAction(whip_action)

        feather_action = QAction("🪶 小羽毛", self)
        feather_action.triggered.connect(lambda: show_feather_tool(self))
        menu.addAction(feather_action)

        actions = self.named_action_items()
        if actions:
            animation_menu = menu.addMenu("🎭 动作列表")
            for animation_name, display_name in actions:
                animation_action = QAction(str(display_name), self)
                if str(display_name) != str(animation_name):
                    animation_action.setToolTip(str(animation_name))
                animation_action.triggered.connect(
                    lambda checked=False, name=animation_name: self.play_named_action(name)
                )
                animation_menu.addAction(animation_action)

        accessories = self.accessory_definitions()
        if accessories:
            accessory_menu = menu.addMenu("🎀 配件")
            for key, definition in accessories.items():
                accessory_action = QAction(self.accessory_display_name(key, definition), self)
                accessory_action.setCheckable(True)
                accessory_action.setChecked(str(key) in self.enabled_accessories)
                accessory_action.triggered.connect(lambda checked=False, value=str(key): self.toggle_accessory(value))
                accessory_menu.addAction(accessory_action)

        menu.addSeparator()

        # 3. 实用轻量工具：计时器 & 便签
        timer_menu = menu.addMenu("⏰ 计时与专注")
        timer_visible_action = QAction("隐藏计时器" if self.timer_visible else "显示计时器", self)
        timer_visible_action.triggered.connect(self.toggle_timer_visible)
        timer_menu.addAction(timer_visible_action)
        timer_start_action = QAction("暂停计时" if self.timer_running else "开始计时", self)
        timer_start_action.triggered.connect(self.start_or_pause_timer)
        timer_menu.addAction(timer_start_action)
        timer_reset_action = QAction("重置为 5 分钟", self)
        timer_reset_action.triggered.connect(self.reset_timer)
        timer_menu.addAction(timer_reset_action)
        timer_menu.addSeparator()
        focus_action = QAction("开始 25 分钟专注", self)
        focus_action.triggered.connect(self.start_focus_session)
        timer_menu.addAction(focus_action)
        break_action = QAction("开始 5 分钟休息", self)
        break_action.triggered.connect(self.start_break_session)
        timer_menu.addAction(break_action)
        complete_task_action = QAction("完成当前任务并庆祝", self)
        complete_task_action.triggered.connect(self.complete_current_task)
        timer_menu.addAction(complete_task_action)
        timer_menu.addSeparator()
        for label, minutes in (("加 1 分钟", 1), ("减 1 分钟", -1), ("加 5 分钟", 5), ("减 5 分钟", -5)):
            adjust_action = QAction(label, self)
            adjust_action.triggered.connect(lambda checked=False, value=minutes: self.adjust_timer_minutes(value))
            timer_menu.addAction(adjust_action)

        power_menu = menu.addMenu("🌙 定时休眠与关机")
        due_at = self.parse_power_due_at()
        if self.power_action_type and due_at is not None:
            lbl = self.power_action_label()
            status_action = QAction(f"⏳ 已预约 {lbl} ({due_at:%H:%M})", self)
            status_action.setEnabled(False)
            power_menu.addAction(status_action)
            cancel_action = QAction("❌ 取消定时计划", self)
            cancel_action.triggered.connect(self.cancel_power_schedule)
            power_menu.addAction(cancel_action)
            power_menu.addSeparator()

        after_action = QAction("⏱️ 倒计时自动休眠/关机...", self)
        after_action.triggered.connect(self.schedule_power_after_minutes)
        power_menu.addAction(after_action)

        exact_action = QAction("⏰ 指定时刻自动休眠/关机...", self)
        exact_action.triggered.connect(self.schedule_power_at_time)
        power_menu.addAction(exact_action)

        memo_menu = menu.addMenu("📝 NotchNotes 便签")
        notchnotes_open_action = QAction("展开/收起 NotchNotes 便签", self)
        notchnotes_open_action.triggered.connect(self.toggle_notchnotes)
        memo_menu.addAction(notchnotes_open_action)
        memo_menu.addSeparator()
        memo_show_action = QAction("隐藏桌宠头顶气泡" if self.memo_visible else "在桌宠头顶显示待办气泡", self)
        memo_show_action.triggered.connect(self.toggle_memo_visible)
        memo_menu.addAction(memo_show_action)
        quick_task_action = QAction("快速添加待办任务...", self)
        quick_task_action.triggered.connect(self.quick_add_todo_task)
        memo_menu.addAction(quick_task_action)
        memo_edit_action = QAction("编辑简易便签文本...", self)
        memo_edit_action.triggered.connect(self.edit_memo)
        memo_menu.addAction(memo_edit_action)
        memo_clear_action = QAction("清空所有待办与便签", self)
        memo_clear_action.triggered.connect(self.clear_memo)
        memo_menu.addAction(memo_clear_action)

        menu.addSeparator()

        # 4. 全新竖向大小滚轮滑块 (Vertical Wheel / Slider Control)
        size_widget = VibeVerticalSizeControl(current_scale=self.scale, on_scale_changed=self.set_scale, parent=menu)
        size_action = QWidgetAction(menu)
        size_action.setDefaultWidget(size_widget)
        menu.addAction(size_action)

        menu.addSeparator()

        # 5. 关闭与退出
        close_action = QAction("✕ 关闭此桌宠", self)
        close_action.triggered.connect(self.close)
        menu.addAction(close_action)

        exit_action = QAction("🚪 退出 WindowPet", self)
        exit_action.triggered.connect(lambda: confirm_exit_or_tray(self))
        menu.addAction(exit_action)

        style_menu(menu).exec(pos)


    def open_gallery_site(self):
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices

        url = "http://127.0.0.1:5173/pet/#/gallery"
        try:
            import urllib.request
            urllib.request.urlopen("http://127.0.0.1:5173/pet/", timeout=0.5)
        except Exception:
            url = "https://windowpet.cn/pet/#/gallery"
        QDesktopServices.openUrl(QUrl(url))

    def add_quick_switch_menu(self, menu):
        try:
            assets = assets_for_pack(state.ASSETS_DIR)
        except OSError as exc:
            log_warning("Unable to list assets for quick switch: %s", exc)
            return

        if not assets:
            return

        switch_menu = menu.addMenu("切换当前宠物")
        current_path = self.asset_path.resolve()
        for asset in assets:
            asset_path = Path(asset.path).resolve()
            action = QAction(str(asset.name or asset_path.name), self)
            is_current = asset_path == current_path
            action.setCheckable(True)
            action.setChecked(is_current)
            action.setEnabled(not is_current)
            action.triggered.connect(lambda checked=False, path=str(asset_path): self.switch_to_asset(path))
            switch_menu.addAction(action)

    def switch_to_asset(self, asset_path):
        new_asset = detect_asset(Path(asset_path).resolve())
        if new_asset is None:
            QMessageBox.warning(self, "切换宠物", "这个宠物素材暂时无法加载。")
            return False

        if Path(new_asset.path).resolve() == self.asset_path:
            return True

        runtime_state = {
            "enabled_accessories": self.enabled_accessories,
            "accessory_cache": self.accessory_cache,
            "layer_values": self.layer_values,
            "current_animation": self.current_animation,
            "current_frame_animation": self.current_frame_animation,
            "pet_serial": self.pet_serial,
            "character_id": self.character_id,
            "pet_display_name": self.pet_display_name,
        }
        self.physics.pause_for_drag()
        self.enabled_accessories = []
        self.accessory_cache = {}
        self.layer_values = {}
        self.current_animation = "idle"
        self.current_frame_animation = "idle"

        if not self.reload_asset_definition(new_asset):
            self.enabled_accessories = runtime_state["enabled_accessories"]
            self.accessory_cache = runtime_state["accessory_cache"]
            self.layer_values = runtime_state["layer_values"]
            self.current_animation = runtime_state["current_animation"]
            self.current_frame_animation = runtime_state["current_frame_animation"]
            self.pet_serial = runtime_state["pet_serial"]
            self.character_id = runtime_state["character_id"]
            self.pet_display_name = runtime_state["pet_display_name"]
            QMessageBox.warning(self, "切换宠物", "切换失败，已保留当前宠物。")
            return False

        metadata = new_asset.metadata or {}
        self.pet_serial = ""
        self.character_id = str(metadata.get("character_id") or infer_character_id_from_path(self.asset_path))
        self.pet_display_name = str(new_asset.name or self.asset_path.name)
        self.current_animation = "idle"
        self.current_frame_animation = "idle"
        self.dock_mode = "none"
        self.move(self.clamped_position(self.pos()))
        self.schedule_next_idle_variant()
        self.physics.start()
        save_config()
        refresh_control_panel()
        return True

    def toggle_startup_enabled(self, checked):
        set_startup_enabled(bool(checked))
        if state.CONTROL_PANEL is not None and hasattr(state.CONTROL_PANEL, "startup_check"):
            state.CONTROL_PANEL.startup_check.blockSignals(True)
            state.CONTROL_PANEL.startup_check.setChecked(startup_enabled())
            state.CONTROL_PANEL.startup_check.blockSignals(False)

    def add_asset(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "导入素材",
            str(BASE_DIR),
            "可视素材 (*.gif *.mp4 *.webm *.mov *.mkv *.avi *.m4v *.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if path:
            add_window(path)
            if state.CONTROL_PANEL is not None:
                state.CONTROL_PANEL.refresh_packs()

    def toggle_lock(self):
        self.locked = not self.locked
        save_config()
        refresh_control_panel()

    def toggle_always_on_top(self):
        self.always_on_top = not self.always_on_top
        self.apply_window_flags()
        save_config()
        refresh_control_panel()

    def showEvent(self, event):
        remove_native_border(self)
        super().showEvent(event)
        self._sync_speech_bubble()

    def moveEvent(self, event):
        super().moveEvent(event)
        if self._speech_bubble is not None and self._speech_bubble.isVisible():
            self._speech_bubble.reposition()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "mic_badge"):
            self.mic_badge.move(max(0, self.width() - 34), 4)
        if self._speech_bubble is not None and self._speech_bubble.isVisible():
            self._speech_bubble.reposition()

    def hideEvent(self, event):
        super().hideEvent(event)
        if self._speech_bubble is not None:
            self._speech_bubble.hide()

    def toggle_click_through(self):
        self.click_through = not self.click_through
        self.apply_click_through()
        save_config()
        refresh_control_panel()

    def toggle_physics_enabled(self, checked):
        self.physics_enabled = bool(checked)
        self.physics.set_enabled(self.physics_enabled)
        save_config()
        refresh_control_panel()

    def set_selected(self, selected):
        self.update()

    def set_scale(self, value):
        self.scale = int(value)
        self.apply_scale()
        save_config()

    def set_opacity_percent(self, value):
        self.opacity = int(value)
        self.setWindowOpacity(self.opacity / 100)
        save_config()

    def set_speed(self, value):
        self.speed = int(value)
        if self.movie is not None:
            self.movie.setSpeed(self.speed)
        if self.frame_player is not None:
            self.frame_player.set_speed(self.speed)
        if self.sprite_player is not None:
            self.sprite_player.set_speed(self.speed)
        if self.video_player is not None:
            self.video_player.set_speed(self.speed)
        if self.video_audio_player is not None:
            self.video_audio_player.set_speed(self.speed)
        if self.video_action_player is not None:
            self.video_action_player.set_speed(self.speed)
        save_config()

    def to_config(self):
        pos = self.pos()
        data = {
            "path": stored_path(self.asset_path),
            "asset_id": self.asset.id,
            "asset_type": self.asset_type,
            "x": pos.x(),
            "y": pos.y(),
            "locked": self.locked,
            "always_on_top": self.always_on_top,
            "click_through": self.click_through,
            "scale": self.scale,
            "opacity": self.opacity,
            "speed": self.speed,
            "dock_mode": "none",
            "physics_enabled": self.physics_enabled,
            "timer_visible": self.timer_visible,
            "timer_seconds": self.timer_seconds,
            "focus_mode": self.focus_mode,
            "focus_sessions_completed": self.focus_sessions_completed,
            "memo_visible": self.memo_visible,
            "memo_text": self.memo_text,
            "memo_checked": self.memo_checked,
            "power_action_type": self.power_action_type,
            "power_action_due_at": self.power_action_due_at,
            "enabled_accessories": self.enabled_accessories,
            "pet_serial": self.pet_serial,
            "character_id": self.character_id,
            "pet_display_name": self.pet_display_name,
            "sound_muted": self.sound_muted,
        }
        if self.layer_values:
            data["layer_values"] = self.layer_values
        if self.current_animation:
            data["current_animation"] = self.current_animation
        return data

    def closeEvent(self, event):
        self.physics.stop()
        self.stop_playback()
        if self._speech_bubble is not None:
            self._speech_bubble.close()
            self._speech_bubble = None

        if state.EXITING:
            save_config()
            super().closeEvent(event)
            return

        save_config()
        if self in state.WINDOWS:
            state.WINDOWS.remove(self)
        log_info("Overlay removed: %s", self.asset_path)
        save_config()
        refresh_control_panel()
        super().closeEvent(event)
