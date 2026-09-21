import json
import math
import random
import re
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QPointF,
    QRect,
    QRectF,
    QSize,
    Qt,
    QTime,
    QTimer,
    QUrl,
    Property,
    QPropertyAnimation,
)
from PySide6.QtGui import QAction, QBrush, QColor, QDesktopServices, QFont, QIcon, QImageReader, QLinearGradient, QMovie, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCalendarWidget,
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QStackedWidget,
    QStyle,
    QStyledItemDelegate,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from . import state
from .asset_analyzer import (
    AssetAnalyzer,
    AssetGuess,
    create_asset_folder_from_guess,
)
from .asset_setup_dialog import AssetSetupDialog
from .asset_validation import validate_asset_metadata
from .character_acquisition import (
    CharacterAcquisitionError,
    build_doubao_image_prompt,
    build_doubao_prompt,
    download_and_install_character,
    ensure_ai_authoring_guide,
)
from .assets import (
    AssetType,
    assets_for_pack,
    asset_packs,
    auto_update_check_enabled,
    detect_asset,
    ensure_pet_unlock_state,
    import_asset_to_assets,
    is_asset_unlocked,
    logged_in_account,
    load_metadata,
    make_thumbnail,
    normalize_pet_unlocks,
    save_config,
    SUPPORTED_WALLPAPER_EXTENSIONS,
    set_auto_update_check_enabled,
    set_wallpaper_schedule_enabled,
    set_wallpaper_slot_path,
    wallpaper_schedule_settings,
)
from .constants import APP_DISPLAY_NAME, BASE_DIR, CONFIG_PATH, LOG_DIR, LOG_PATH, THUMBNAIL_SIZE, resource_path
from .cloud_api import (
    CloudApiError,
    login as cloud_login,
    redeem_character as cloud_redeem_character,
    register as cloud_register,
    send_register_code,
)
from .logging_utils import log_info, log_warning, recent_warnings_and_errors
from .medals import MedalStore
from .local_search import (
    format_modified,
    format_size,
    open_parent,
    open_path,
    search_local,
)
from .overlay import add_window, exit_app, frame_paths_for_folder
from .metadata_renderers import load_spritesheet_frames
from . import recovery
from .startup import set_startup_enabled, startup_enabled
from .style_utils import style_menu
from .focus import FOCUS_MODE_BREAK, FOCUS_MODE_CUSTOM, FOCUS_MODE_FOCUS
from .uninstaller import can_self_uninstall, start_self_uninstall, uninstall_target_dir
from .updater import (
    check_for_updates,
    fetch_json,
    is_newer_version,
    official_site_url,
    open_official_site,
    update_manifest_url,
)
from .version import __version__
from .whip_tool import show_whip_tool
from .vibe_components import (
    SegmentedControl,
    SpringPushButton,
    PopconfirmBubble,
    EmptyStateWidget,
    VibeButton,
    VibeInput,
    VibeSwitch,
    VibeLink,
    VibeToast,
    PetCursorManager,
    VibeSlider,
    VibeTimePicker,
)


LIBRARY_LOCKED_ROLE = int(Qt.UserRole) + 1
LIBRARY_LOCK_IMAGE_ROLE = int(Qt.UserRole) + 2
LIBRARY_ASSET_ID_ROLE = int(Qt.UserRole) + 3
LIBRARY_PACKAGE_CODE_ROLE = int(Qt.UserRole) + 4
LIBRARY_ACTION_ROLE = int(Qt.UserRole) + 5

UI_INK = QColor("#26334a")
UI_MUTED = QColor("#718096")
UI_BORDER = QColor("#ddd4cc")
UI_SURFACE = QColor("#fffdf9")
UI_SURFACE_SOFT = QColor("#fff7f3")
UI_PRIMARY = QColor("#ff7f87")
UI_PRIMARY_SOFT = QColor("#ffe6e9")
UI_MINT = QColor("#57c7b8")
UI_MINT_SOFT = QColor("#dcf7f1")
UI_GOLD = QColor("#f3c969")


def draw_sticker_icon(painter, rect, icon_key, color=UI_INK, selected=False):
    """Draw the new soft-sticker icon family used by navigation and actions."""
    bounds = QRectF(rect).adjusted(3.0, 3.0, -3.0, -3.0)
    cx = bounds.center().x()
    cy = bounds.center().y()
    scale = min(bounds.width(), bounds.height()) / 34.0
    accent = QColor(color)
    if accent.alpha() == 0:
        accent = QColor(UI_INK)
    palette = {
        "coral": QColor("#ff9da4"),
        "mint": QColor("#7bd6c7"),
        "gold": QColor("#f6d37e"),
        "lavender": QColor("#c2b4eb"),
        "cream": QColor("#fff5dc"),
    }
    key_palette = {
        "pet": "coral", "tools": "mint", "events": "gold", "medals": "gold", "schedule": "mint", "settings": "coral",
        "search": "mint", "bell": "coral", "timer": "gold", "memo": "mint", "magic": "coral", "wallpaper": "mint",
        "refresh": "mint", "open": "coral", "folder": "gold", "folder-up": "gold", "file": "lavender", "app": "mint",
    }
    fill = palette[key_palette.get(icon_key, "lavender")]
    if selected:
        fill = QColor(UI_PRIMARY_SOFT)

    painter.save()
    painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
    painter.translate(cx, cy)
    painter.scale(scale, scale)
    painter.translate(-cx, -cy)
    painter.setPen(QPen(QColor("#ffffff"), 1.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(QBrush(fill))
    painter.drawRoundedRect(QRectF(cx - 15.5, cy - 15.5, 31, 31), 9, 9)
    painter.setPen(QPen(accent, 1.9, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)

    if icon_key == "pet":
        head = QPainterPath()
        head.moveTo(cx - 9.5, cy - 1.5)
        head.lineTo(cx - 8.2, cy - 10.0)
        head.lineTo(cx - 3.0, cy - 6.6)
        head.cubicTo(cx, cy - 8.2, cx + 3.0, cy - 8.2, cx + 6.0, cy - 6.6)
        head.lineTo(cx + 11.0, cy - 10.0)
        head.lineTo(cx + 10.0, cy + 0.0)
        head.cubicTo(cx + 10.0, cy + 8.0, cx + 4.5, cy + 11.0, cx, cy + 11.0)
        head.cubicTo(cx - 5.0, cy + 11.0, cx - 10.0, cy + 7.0, cx - 9.5, cy - 1.5)
        head.closeSubpath()
        painter.setBrush(QBrush(QColor("#fffaf2")))
        painter.drawPath(head)
        painter.setBrush(QBrush(accent))
        painter.drawEllipse(QPointF(cx - 3.8, cy - 0.8), 1.4, 1.4)
        painter.drawEllipse(QPointF(cx + 3.8, cy - 0.8), 1.4, 1.4)
        painter.setBrush(Qt.NoBrush)
        painter.drawArc(QRectF(cx - 2.5, cy + 1.5, 5, 4), 205 * 16, 130 * 16)
    elif icon_key == "tools":
        painter.setBrush(QBrush(QColor("#fffaf2")))
        painter.drawRoundedRect(QRectF(cx - 10, cy - 3, 20, 11), 3, 3)
        painter.drawArc(QRectF(cx - 5, cy - 10, 10, 11), 0, 180 * 16)
        painter.setBrush(QBrush(accent))
        painter.drawEllipse(QPointF(cx - 5.5, cy + 2.2), 1.8, 1.8)
        painter.drawEllipse(QPointF(cx, cy + 2.2), 1.8, 1.8)
        painter.drawEllipse(QPointF(cx + 5.5, cy + 2.2), 1.8, 1.8)
    elif icon_key == "events":
        star = QPainterPath()
        for i in range(8):
            angle = i * 45
            radius = 11 if i % 2 == 0 else 4.5
            point = QPointF(cx + radius * __import__("math").cos(__import__("math").radians(angle - 90)), cy + radius * __import__("math").sin(__import__("math").radians(angle - 90)))
            if i == 0: star.moveTo(point)
            else: star.lineTo(point)
        star.closeSubpath()
        painter.setBrush(QBrush(QColor("#fffaf2")))
        painter.drawPath(star)
        painter.setBrush(QBrush(accent))
        painter.drawEllipse(QPointF(cx + 10, cy - 8), 2.0, 2.0)
    elif icon_key == "medals":
        painter.setBrush(QBrush(QColor("#fffaf2")))
        painter.drawEllipse(QPointF(cx, cy - 3), 8.2, 8.2)
        painter.setBrush(QBrush(accent))
        painter.drawEllipse(QPointF(cx, cy - 3), 3.0, 3.0)
        painter.drawPolygon([QPointF(cx - 7, cy + 3), QPointF(cx - 4, cy + 13), QPointF(cx, cy + 8), QPointF(cx + 4, cy + 13), QPointF(cx + 7, cy + 3)])
    elif icon_key == "schedule":
        painter.setBrush(QBrush(QColor("#fffaf2")))
        painter.drawRoundedRect(QRectF(cx - 10.5, cy - 8.5, 21, 19), 4, 4)
        painter.drawLine(QPointF(cx - 10, cy - 3), QPointF(cx + 10, cy - 3))
        painter.drawLine(QPointF(cx - 5, cy - 12), QPointF(cx - 5, cy - 5))
        painter.drawLine(QPointF(cx + 5, cy - 12), QPointF(cx + 5, cy - 5))
        painter.setBrush(QBrush(accent))
        for x, y in ((cx - 5, cy + 2), (cx + 1, cy + 2), (cx + 6, cy + 2), (cx - 5, cy + 7), (cx + 1, cy + 7)):
            painter.drawEllipse(QPointF(x, y), 1.25, 1.25)
    elif icon_key == "settings":
        for y, knob in ((cy - 7, cx + 5), (cy, cx - 4), (cy + 7, cx + 3)):
            painter.drawLine(QPointF(cx - 10, y), QPointF(cx + 10, y))
            painter.setBrush(QBrush(QColor("#fffaf2")))
            painter.drawEllipse(QPointF(knob, y), 3.0, 3.0)
            painter.setBrush(Qt.NoBrush)
    elif icon_key in {"search", "open", "folder-up", "refresh"}:
        if icon_key == "search":
            painter.setBrush(QBrush(QColor("#fffaf2")))
            painter.drawEllipse(QPointF(cx - 2, cy - 2), 6.5, 6.5)
            painter.drawLine(QPointF(cx + 3, cy + 3), QPointF(cx + 9, cy + 9))
        elif icon_key == "refresh":
            painter.drawArc(QRectF(cx - 8, cy - 8, 16, 16), 35 * 16, 280 * 16)
            painter.drawLine(QPointF(cx + 7, cy - 8), QPointF(cx + 10, cy - 2))
            painter.drawLine(QPointF(cx + 10, cy - 2), QPointF(cx + 4, cy - 3))
        elif icon_key == "open":
            painter.setBrush(QBrush(QColor("#fffaf2")))
            painter.drawRoundedRect(QRectF(cx - 9, cy - 7, 18, 15), 3, 3)
            painter.drawLine(QPointF(cx - 1, cy + 3), QPointF(cx + 7, cy - 5))
            painter.drawLine(QPointF(cx + 3, cy - 5), QPointF(cx + 7, cy - 5))
            painter.drawLine(QPointF(cx + 7, cy - 5), QPointF(cx + 7, cy - 1))
        else:
            painter.setBrush(QBrush(QColor("#fffaf2")))
            painter.drawRoundedRect(QRectF(cx - 10, cy - 5, 20, 13), 3, 3)
            painter.drawLine(QPointF(cx - 7, cy - 8), QPointF(cx, cy - 8))
            painter.drawLine(QPointF(cx, cy - 8), QPointF(cx + 3, cy - 5))
            painter.drawLine(QPointF(cx + 3, cy + 3), QPointF(cx + 3, cy - 2))
            painter.drawLine(QPointF(cx + 3, cy - 2), QPointF(cx + 1, cy))
            painter.drawLine(QPointF(cx + 3, cy - 2), QPointF(cx + 5, cy))
    elif icon_key in {"bell", "timer", "memo", "magic", "wallpaper", "folder", "folder-up", "file", "app", "party", "offwork"}:
        if icon_key in {"party", "offwork"}:
            cone = QPainterPath()
            cone.moveTo(cx - 7, cy + 8)
            cone.lineTo(cx + 2, cy + 5)
            cone.lineTo(cx - 4, cy - 4)
            cone.closeSubpath()
            painter.setBrush(QBrush(QColor("#fffaf2")))
            painter.drawPath(cone)
            painter.setBrush(QBrush(accent))
            painter.drawEllipse(QPointF(cx + 4, cy - 4), 1.8, 1.8)
            painter.drawEllipse(QPointF(cx + 7, cy + 1), 1.5, 1.5)
            painter.drawEllipse(QPointF(cx - 1, cy - 8), 1.6, 1.6)
            painter.drawLine(QPointF(cx - 1, cy - 2), QPointF(cx + 6, cy - 6))
        elif icon_key == "bell":
            bell = QPainterPath(); bell.moveTo(cx - 8, cy + 5); bell.cubicTo(cx - 5, cy + 2, cx - 6, cy - 7, cx, cy - 9); bell.cubicTo(cx + 6, cy - 7, cx + 5, cy + 2, cx + 8, cy + 5); bell.closeSubpath()
            painter.setBrush(QBrush(QColor("#fffaf2"))); painter.drawPath(bell); painter.drawLine(QPointF(cx - 10, cy + 5), QPointF(cx + 10, cy + 5)); painter.drawEllipse(QPointF(cx, cy + 8), 1.7, 1.7)
        elif icon_key == "timer":
            painter.setBrush(QBrush(QColor("#fffaf2"))); painter.drawEllipse(QPointF(cx, cy + 1), 9, 9); painter.drawLine(QPointF(cx, cy + 1), QPointF(cx + 5, cy - 4)); painter.drawLine(QPointF(cx, cy - 9), QPointF(cx, cy - 12))
        elif icon_key == "memo":
            painter.setBrush(QBrush(QColor("#fffaf2"))); painter.drawRoundedRect(QRectF(cx - 8, cy - 10, 16, 20), 3, 3); painter.drawLine(QPointF(cx - 4, cy), QPointF(cx - 1, cy + 3)); painter.drawLine(QPointF(cx - 1, cy + 3), QPointF(cx + 5, cy - 4))
        elif icon_key == "magic":
            painter.drawLine(QPointF(cx - 8, cy + 8), QPointF(cx + 7, cy - 7)); painter.setBrush(QBrush(QColor("#fffaf2"))); painter.drawEllipse(QPointF(cx + 8, cy - 8), 4, 4); painter.drawEllipse(QPointF(cx + 8, cy - 8), 1, 1)
        elif icon_key == "wallpaper":
            painter.setBrush(QBrush(QColor("#fffaf2"))); painter.drawRoundedRect(QRectF(cx - 10, cy - 8, 20, 16), 3, 3); painter.drawEllipse(QPointF(cx + 5, cy - 3), 1.8, 1.8); painter.drawPolyline([QPointF(cx - 7, cy + 5), QPointF(cx - 1, cy), QPointF(cx + 3, cy + 4), QPointF(cx + 7, cy + 1)])
        elif icon_key in {"folder", "folder-up"}:
            painter.setBrush(QBrush(QColor("#fffaf2"))); painter.drawRoundedRect(QRectF(cx - 10, cy - 5, 20, 13), 3, 3); painter.drawLine(QPointF(cx - 7, cy - 8), QPointF(cx, cy - 8)); painter.drawLine(QPointF(cx, cy - 8), QPointF(cx + 3, cy - 5))
        else:
            painter.setBrush(QBrush(QColor("#fffaf2"))); painter.drawRoundedRect(QRectF(cx - 7, cy - 10, 14, 20), 3, 3); painter.drawLine(QPointF(cx - 4, cy - 3), QPointF(cx + 4, cy - 3)); painter.drawLine(QPointF(cx - 4, cy + 2), QPointF(cx + 4, cy + 2));
            if icon_key == "app":
                painter.setBrush(QBrush(accent));
                for x, y in ((cx - 3, cy + 6), (cx + 3, cy + 6)): painter.drawEllipse(QPointF(x, y), 1.2, 1.2)
    painter.restore()


def make_sticker_icon(icon_key, color=UI_INK, size=40):
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    draw_sticker_icon(painter, QRectF(1, 1, size - 2, size - 2), icon_key, color)
    painter.end()
    return QIcon(pixmap)


def make_action_icon(icon_key, color=UI_INK, size=28):
    """Create crisp, theme-owned sticker action icons instead of platform art."""
    return make_sticker_icon(icon_key, color, size)


def draw_rounded_cover_image(painter, rect, image_path, radius=16):
    pixmap = QPixmap(str(image_path))
    if pixmap.isNull():
        return False
    bounds = QRectF(rect)
    target_size = bounds.size().toSize()
    scaled = pixmap.scaled(target_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    target = QRectF(
        bounds.center().x() - scaled.width() / 2,
        bounds.center().y() - scaled.height() / 2,
        scaled.width(),
        scaled.height(),
    )
    clip = QPainterPath()
    clip.addRoundedRect(bounds, radius, radius)
    painter.save()
    painter.setClipPath(clip)
    painter.drawPixmap(target.toRect(), scaled)
    painter.restore()
    painter.setPen(QPen(QColor("#d6c8c3"), 1.2))
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(bounds, radius, radius)
    return True


def draw_lock_icon(painter, rect, color):
    bounds = QRectF(rect)
    side = min(bounds.width(), bounds.height()) * 0.62
    cx = bounds.center().x()
    body = QRectF(cx - side * 0.38, bounds.center().y() - side * 0.02, side * 0.76, side * 0.48)
    shackle_top = body.top() - side * 0.45
    shackle_bottom = body.top() + side * 0.08
    left = cx - side * 0.26
    right = cx + side * 0.26

    painter.save()
    painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
    pen = QPen(QColor(color), max(2.0, side * 0.07), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)

    shackle = QPainterPath()
    shackle.moveTo(left, body.top() + 2)
    shackle.lineTo(left, shackle_bottom)
    shackle.cubicTo(left, shackle_top, right, shackle_top, right, shackle_bottom)
    shackle.lineTo(right, body.top() + 2)
    painter.drawPath(shackle)

    body_color = QColor(color)
    body_color.setAlpha(132)
    painter.setBrush(QBrush(body_color))
    painter.drawRoundedRect(body, side * 0.1, side * 0.1)
    painter.setBrush(QBrush(QColor(color)))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(QRectF(cx - side * 0.045, body.center().y() - side * 0.04, side * 0.09, side * 0.09))
    painter.restore()


def draw_game_cloud(painter, center_x, center_y, scale=1.0, alpha=210):
    painter.save()
    outline = QColor("#5f4725")
    outline.setAlpha(min(255, alpha))
    fill = QColor("#fff7df")
    fill.setAlpha(min(255, alpha))
    shade = QColor("#e4ddc5")
    shade.setAlpha(min(230, alpha))

    painter.setPen(QPen(outline, max(2.0, 3.0 * scale), Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(QBrush(fill))
    painter.drawEllipse(QPointF(center_x - 22 * scale, center_y + 8 * scale), 22 * scale, 13 * scale)
    painter.drawEllipse(QPointF(center_x - 4 * scale, center_y - 4 * scale), 24 * scale, 20 * scale)
    painter.drawEllipse(QPointF(center_x + 20 * scale, center_y + 8 * scale), 25 * scale, 14 * scale)
    painter.drawEllipse(QPointF(center_x + 40 * scale, center_y + 13 * scale), 17 * scale, 10 * scale)

    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(fill))
    painter.drawEllipse(QPointF(center_x - 22 * scale, center_y + 8 * scale), 19 * scale, 10 * scale)
    painter.drawEllipse(QPointF(center_x - 4 * scale, center_y - 4 * scale), 21 * scale, 17 * scale)
    painter.drawEllipse(QPointF(center_x + 20 * scale, center_y + 8 * scale), 22 * scale, 11 * scale)
    painter.drawEllipse(QPointF(center_x + 40 * scale, center_y + 13 * scale), 14 * scale, 8 * scale)
    painter.setBrush(QBrush(shade))
    painter.drawEllipse(QPointF(center_x + 8 * scale, center_y + 15 * scale), 26 * scale, 5 * scale)
    painter.restore()


def draw_game_background(painter, rect, include_grass=True, muted=False):
    sky = QLinearGradient(rect.topLeft(), rect.bottomLeft())
    if muted:
        sky.setColorAt(0.0, QColor("#3e8796"))
        sky.setColorAt(1.0, QColor("#7bb8c5"))
    else:
        sky.setColorAt(0.0, QColor("#55c4e2"))
        sky.setColorAt(1.0, QColor("#93dceb"))
    painter.fillRect(rect, QBrush(sky))

    w = max(1.0, rect.width())
    h = max(1.0, rect.height())
    draw_game_cloud(painter, rect.left() + w * 0.18, rect.top() + h * 0.14, 0.75, 178)
    draw_game_cloud(painter, rect.left() + w * 0.56, rect.top() + h * 0.24, 0.62, 162)
    draw_game_cloud(painter, rect.left() + w * 0.80, rect.top() + h * 0.12, 0.50, 148)

    if not include_grass:
        return

    hill_top = rect.top() + h * 0.72
    grass = QPainterPath()
    grass.moveTo(rect.left(), hill_top)
    grass.cubicTo(rect.left() + w * 0.26, hill_top - h * 0.05, rect.left() + w * 0.63, hill_top - h * 0.03, rect.right(), hill_top - h * 0.06)
    grass.lineTo(rect.right(), rect.bottom())
    grass.lineTo(rect.left(), rect.bottom())
    grass.closeSubpath()

    grass_fill = QLinearGradient(QPointF(rect.left(), hill_top), rect.bottomLeft())
    grass_fill.setColorAt(0.0, QColor("#93d64c") if not muted else QColor("#5f9239"))
    grass_fill.setColorAt(1.0, QColor("#6cb22f") if not muted else QColor("#47742e"))
    painter.setPen(QPen(QColor("#4f7f28"), 2))
    painter.setBrush(QBrush(grass_fill))
    painter.drawPath(grass)


class RailNavButton(QPushButton):
    def __init__(self, icon_key, label, parent=None):
        super().__init__(parent)
        self.icon_key = icon_key
        self._icon_pixmap = QPixmap(str(resource_path(f"assets/UiAssets/nav-{icon_key}.png")))
        self._checked_icon_pixmap = QPixmap(str(resource_path(f"assets/UiAssets/nav-{icon_key}-selected.png")))
        self.setCheckable(True)
        self.setToolTip(label)
        self.setObjectName("RailNavButton")
        self.setFixedSize(50, 50)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)

    def set_nav_label(self, label):
        self.setToolTip(label)
        self.setAccessibleName(label)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)
        rect = QRectF(self.rect()).adjusted(2.0, 2.0, -2.0, -2.0)
        if self.isChecked():
            painter.setPen(QPen(QColor("#ffccd3"), 1.4))
            bg_grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
            bg_grad.setColorAt(0.0, QColor("#ffffff"))
            bg_grad.setColorAt(1.0, QColor("#fff0f3"))
            painter.setBrush(QBrush(bg_grad))
            painter.drawRoundedRect(rect, 16, 16)
            # Active indicator capsule on left
            indicator = QRectF(rect.left() + 2.5, rect.center().y() - 10, 3.5, 20)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor("#ff758c")))
            painter.drawRoundedRect(indicator, 1.75, 1.75)
        elif self.underMouse():
            painter.setPen(QPen(QColor("#dcebe6"), 1.2))
            painter.setBrush(QBrush(QColor("#f3faf8")))
            painter.drawRoundedRect(rect, 16, 16)
        else:
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.NoBrush)

        pixmap = self._checked_icon_pixmap if (self.isChecked() and not self._checked_icon_pixmap.isNull()) else self._icon_pixmap
        if not pixmap.isNull():
            icon_size = 36 if self.isChecked() else 32
            icon_rect = QRectF(
                rect.center().x() - icon_size / 2.0,
                rect.center().y() - icon_size / 2.0,
                icon_size,
                icon_size
            )
            painter.drawPixmap(icon_rect.toRect(), pixmap.scaled(int(icon_size), int(icon_size), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            self.draw_icon(painter, rect, UI_PRIMARY if self.isChecked() else UI_MUTED)

    def draw_icon(self, painter, rect, color):
        draw_sticker_icon(painter, rect, self.icon_key, color, self.isChecked())
        return

        # Legacy line-art fallback retained below for compatibility with old skins.
        cx = rect.center().x()
        cy = rect.center().y()
        scale = min(rect.width(), rect.height()) / 41.0

        painter.save()
        painter.translate(cx, cy)
        painter.scale(scale, scale)
        painter.translate(-cx, -cy)
        painter.setPen(QPen(color, 2.45, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)

        if self.icon_key == "pet":
            for x, y, rx, ry in (
                (cx - 9.2, cy - 7.5, 3.3, 4.6),
                (cx - 2.8, cy - 11.0, 3.0, 4.4),
                (cx + 3.6, cy - 11.0, 3.0, 4.4),
                (cx + 10.0, cy - 7.5, 3.3, 4.6),
            ):
                painter.drawEllipse(QPointF(x, y), rx, ry)
            pad = QPainterPath()
            pad.moveTo(cx - 8.4, cy + 7.2)
            pad.cubicTo(cx - 11.6, cy + 3.8, cx - 11.1, cy - 3.8, cx - 4.4, cy - 5.1)
            pad.cubicTo(cx - 1.5, cy - 5.8, cx + 1.7, cy - 5.8, cx + 4.6, cy - 5.1)
            pad.cubicTo(cx + 11.2, cy - 3.7, cx + 11.8, cy + 3.8, cx + 8.4, cy + 7.2)
            pad.cubicTo(cx + 5.4, cy + 10.3, cx - 5.4, cy + 10.3, cx - 8.4, cy + 7.2)
            painter.drawPath(pad)
            painter.restore()
            return

        if self.icon_key == "tools":
            tool = QPainterPath()
            tool.moveTo(cx - 7.0, cy + 8.5)
            tool.lineTo(cx + 1.2, cy + 0.3)
            tool.cubicTo(cx + 2.3, cy - 0.9, cx + 2.8, cy - 2.8, cx + 2.3, cy - 4.7)
            tool.cubicTo(cx + 1.5, cy - 7.8, cx + 2.6, cy - 11.3, cx + 5.4, cy - 13.0)
            tool.cubicTo(cx + 8.2, cy - 14.8, cx + 11.9, cy - 14.3, cx + 14.4, cy - 11.7)
            tool.lineTo(cx + 8.9, cy - 6.3)
            tool.cubicTo(cx + 7.6, cy - 5.0, cx + 7.7, cy - 2.7, cx + 9.0, cy - 1.3)
            tool.cubicTo(cx + 10.3, cy + 0.1, cx + 12.5, cy + 0.2, cx + 13.9, cy - 1.0)
            tool.lineTo(cx + 19.1, cy - 6.2)
            tool.cubicTo(cx + 21.4, cy - 3.3, cx + 21.3, cy + 0.9, cx + 18.8, cy + 3.4)
            tool.cubicTo(cx + 16.6, cy + 5.5, cx + 13.2, cy + 6.1, cx + 10.1, cy + 4.8)
            tool.cubicTo(cx + 8.3, cy + 4.1, cx + 6.5, cy + 4.4, cx + 5.2, cy + 5.6)
            tool.lineTo(cx - 3.0, cy + 13.8)
            tool.cubicTo(cx - 5.4, cy + 16.3, cx - 9.3, cy + 16.3, cx - 11.8, cy + 13.8)
            tool.cubicTo(cx - 14.3, cy + 11.3, cx - 14.3, cy + 7.4, cx - 11.8, cy + 4.9)
            tool.closeSubpath()
            painter.drawPath(tool)
            painter.restore()
            return

        if self.icon_key == "events":
            sparkle = QPainterPath()
            sparkle.moveTo(cx, cy - 13.0)
            sparkle.cubicTo(cx + 1.4, cy - 7.1, cx + 4.9, cy - 3.4, cx + 10.8, cy - 2.0)
            sparkle.cubicTo(cx + 4.9, cy - 0.6, cx + 1.4, cy + 3.1, cx, cy + 9.0)
            sparkle.cubicTo(cx - 1.4, cy + 3.1, cx - 4.9, cy - 0.6, cx - 10.8, cy - 2.0)
            sparkle.cubicTo(cx - 4.9, cy - 3.4, cx - 1.4, cy - 7.1, cx, cy - 13.0)
            painter.drawPath(sparkle)
            mini = QPainterPath()
            mini.moveTo(cx + 11.9, cy - 9.7)
            mini.cubicTo(cx + 12.6, cy - 7.2, cx + 14.0, cy - 5.8, cx + 16.5, cy - 5.1)
            mini.cubicTo(cx + 14.0, cy - 4.4, cx + 12.6, cy - 3.0, cx + 11.9, cy - 0.5)
            mini.cubicTo(cx + 11.2, cy - 3.0, cx + 9.8, cy - 4.4, cx + 7.3, cy - 5.1)
            mini.cubicTo(cx + 9.8, cy - 5.8, cx + 11.2, cy - 7.2, cx + 11.9, cy - 9.7)
            painter.drawPath(mini)
            painter.restore()
            return

        if self.icon_key == "medals":
            medal = QPainterPath()
            medal.addEllipse(QRectF(cx - 10.0, cy - 12.0, 20.0, 20.0))
            painter.drawPath(medal)
            painter.drawEllipse(QPointF(cx, cy - 2.0), 3.2, 3.2)
            painter.drawLine(QPointF(cx - 6.2, cy + 5.0), QPointF(cx - 8.7, cy + 13.0))
            painter.drawLine(QPointF(cx - 8.7, cy + 13.0), QPointF(cx - 1.8, cy + 9.4))
            painter.drawLine(QPointF(cx + 6.2, cy + 5.0), QPointF(cx + 8.7, cy + 13.0))
            painter.drawLine(QPointF(cx + 8.7, cy + 13.0), QPointF(cx + 1.8, cy + 9.4))
            painter.restore()
            return

        if self.icon_key == "schedule":
            box = QRectF(cx - 12.0, cy - 11.0, 24.0, 22.0)
            painter.drawRoundedRect(box, 6.5, 6.5)
            painter.drawLine(QPointF(cx - 12.0, cy - 4.2), QPointF(cx + 12.0, cy - 4.2))
            painter.drawLine(QPointF(cx - 6.6, cy - 15.0), QPointF(cx - 6.6, cy - 8.8))
            painter.drawLine(QPointF(cx + 6.6, cy - 15.0), QPointF(cx + 6.6, cy - 8.8))
            painter.setBrush(QBrush(color))
            for x in (cx - 6.2, cx, cx + 6.2):
                painter.drawEllipse(QPointF(x, cy + 2.6), 1.55, 1.55)
            for x in (cx - 6.2, cx, cx + 6.2):
                painter.drawEllipse(QPointF(x, cy + 7.8), 1.55, 1.55)
            painter.setBrush(Qt.NoBrush)
            painter.restore()
            return

        if self.icon_key == "settings":
            rows = (
                (cy - 8.4, cx - 4.8),
                (cy, cx + 6.8),
                (cy + 8.4, cx - 2.6),
            )
            for y, knob_x in rows:
                painter.drawLine(QPointF(cx - 13.8, y), QPointF(cx + 13.8, y))
                painter.setBrush(QBrush(QColor(248, 252, 255) if color != QColor("#ffffff") else color))
                painter.drawEllipse(QPointF(knob_x, y), 3.9, 3.9)
                painter.setBrush(Qt.NoBrush)
            painter.restore()
            return

        painter.restore()


class RailBrandMark(QWidget):
    _brand_pixmap = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("RailBrandMark")
        self.setToolTip("Window Pet")
        self.setFixedSize(46, 46)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)
        rect = QRectF(self.rect()).adjusted(2.5, 2.5, -2.5, -2.5)
        draw_sticker_icon(painter, rect, "pet", UI_PRIMARY, True)


class LoginPawButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = QPixmap(str(resource_path("assets/UiAssets/login-paw-cutout.png")))
        self._label = "登录"
        self.setObjectName("LoginPawButton")
        self.setFixedSize(70, 78)
        self.setCursor(Qt.PointingHandCursor)
        self.setFocusPolicy(Qt.NoFocus)

    def set_account_label(self, label):
        self._label = str(label or "登录")
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)
        rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        painter.setPen(QPen(QColor("#ffd5d9") if self.underMouse() else QColor("#e8ded7"), 1.3))
        painter.setBrush(QBrush(QColor("#fff4f6") if self.underMouse() else QColor("#ffffff")))
        painter.drawRoundedRect(rect, 18, 18)

        if not self._pixmap.isNull():
            paw_size = 44
            paw_rect = QRectF(rect.center().x() - paw_size / 2.0, rect.top() + 6, paw_size, paw_size)
            painter.drawPixmap(paw_rect.toRect(), self._pixmap.scaled(int(paw_size), int(paw_size), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            icon_rect = QRectF(rect.left() + 13, rect.top() + 7, 42, 42)
            draw_sticker_icon(painter, icon_rect, "pet", UI_PRIMARY, True)

        font = self.font()
        font.setFamily("Microsoft YaHei UI")
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(UI_INK)
        painter.drawText(QRectF(rect.left() + 4, rect.bottom() - 24, rect.width() - 8, 18).toRect(), Qt.AlignCenter, self._label)


class AccountDialog(QDialog):
    def __init__(self, account=None, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassDialog")
        PetCursorManager.apply_to_window(self)
        self.setWindowTitle("登录 / 注册 Window Pet")
        self.setMinimumSize(540, 520)
        account = account or {}
        self.original_identity = str(
            account.get("identity") or account.get("email") or account.get("phone") or ""
        ).strip()
        self.mode = "login" if self.original_identity else "register"
        self.cloud_account_data = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(0)

        surface = QFrame()
        surface.setObjectName("AccountDialogSurface")
        surface_layout = QVBoxLayout(surface)
        surface_layout.setContentsMargins(24, 22, 24, 22)
        surface_layout.setSpacing(16)
        layout.addWidget(surface)

        hero_row = QHBoxLayout()
        hero_row.setSpacing(16)
        hero_icon = QLabel()
        hero_icon.setObjectName("AccountHeroIcon")
        hero_icon.setFixedSize(76, 76)
        hero_pix = QPixmap(str(resource_path("assets/UiAssets/account-hero-welcome.png")))
        if not hero_pix.isNull():
            hero_icon.setPixmap(hero_pix.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        hero_icon.setAlignment(Qt.AlignCenter)
        hero_text = QVBoxLayout()
        hero_text.setContentsMargins(0, 0, 0, 0)
        hero_text.setSpacing(4)
        self.account_title = QLabel()
        self.account_title.setObjectName("AccountTitle")
        subtitle = QLabel("随时登录以同步您的云端角色、日程打卡与成就勋章。")
        subtitle.setObjectName("SubtleLabel")
        subtitle.setWordWrap(True)
        hero_text.addWidget(self.account_title)
        hero_text.addWidget(subtitle)
        hero_row.addWidget(hero_icon)
        hero_row.addLayout(hero_text, 1)
        surface_layout.addLayout(hero_row)

        self.mode_segment = SegmentedControl(
            [("login", "登录账号"), ("register", "注册新账号")],
            default_index=0 if self.mode == "login" else 1,
        )
        self.mode_segment.currentKeyChanged.connect(self.set_mode)
        surface_layout.addWidget(self.mode_segment)

        self.form_stack = QStackedWidget()
        self.form_stack.setObjectName("AccountFormStack")
        self.form_stack.addWidget(self.build_login_page())
        self.form_stack.addWidget(self.build_register_page(account))
        surface_layout.addWidget(self.form_stack)

        button_row = QHBoxLayout()
        button_row.setSpacing(12)
        button_row.addStretch(1)
        cancel_button = VibeButton("取消", variant="secondary")
        cancel_button.clicked.connect(self.reject)
        self.action_button = VibeButton("立即登录", variant="primary")
        self.action_button.clicked.connect(self.accept_login)
        button_row.addWidget(cancel_button)
        button_row.addWidget(self.action_button)
        surface_layout.addLayout(button_row)

        self.set_mode(self.mode)

    def build_login_page(self):
        page = QFrame()
        page.setObjectName("AccountFormPanel")
        form = QVBoxLayout(page)
        form.setContentsMargins(12, 12, 12, 12)
        form.setSpacing(12)

        form.addWidget(self.field_label("账号邮箱"))
        self.login_identity_input = VibeInput(
            "输入邮箱地址",
            icon_path=str(resource_path("assets/UiAssets/input-icon-mail.png")),
        )
        self.login_identity_input.setText(self.original_identity)
        form.addWidget(self.login_identity_input)

        form.addWidget(self.field_label("账号密码"))
        self.login_password_input = VibeInput(
            "输入账号密码",
            icon_path=str(resource_path("assets/UiAssets/input-icon-lock.png")),
            is_password=True,
        )
        self.login_password_input.returnPressed.connect(self.accept_login)
        form.addWidget(self.login_password_input)
        return page

    def build_register_page(self, account):
        page = QFrame()
        page.setObjectName("AccountFormPanel")
        form = QVBoxLayout(page)
        form.setContentsMargins(12, 12, 12, 12)
        form.setSpacing(10)

        form.addWidget(self.field_label("您的常用邮箱"))
        self.register_identity_input = VibeInput(
            "输入邮箱地址",
            icon_path=str(resource_path("assets/UiAssets/input-icon-mail.png")),
        )
        self.register_identity_input.setText(self.original_identity)
        form.addWidget(self.register_identity_input)

        form.addWidget(self.field_label("邮箱验证码"))
        code_row = QHBoxLayout()
        code_row.setSpacing(8)
        self.register_code_input = VibeInput(
            "输入邮件里的验证码",
            icon_path=str(resource_path("assets/UiAssets/input-icon-shield.png")),
        )
        self.register_code_button = VibeButton("获取验证码", variant="secondary")
        self.register_code_button.setFixedHeight(44)
        self.register_code_button.clicked.connect(self.request_register_code)
        code_row.addWidget(self.register_code_input, 1)
        code_row.addWidget(self.register_code_button)
        form.addLayout(code_row)

        form.addWidget(self.field_label("设置登录密码"))
        self.register_password_input = VibeInput(
            "密码至少 6 位",
            icon_path=str(resource_path("assets/UiAssets/input-icon-lock.png")),
            is_password=True,
        )
        form.addWidget(self.register_password_input)

        form.addWidget(self.field_label("再次确认密码"))
        self.register_confirm_input = VibeInput(
            "再输入一次密码",
            icon_path=str(resource_path("assets/UiAssets/input-icon-lock.png")),
            is_password=True,
        )
        self.register_confirm_input.returnPressed.connect(self.accept_login)
        form.addWidget(self.register_confirm_input)
        return page

    def field_label(self, text):
        label = QLabel(text)
        label.setObjectName("AccountFieldLabel")
        return label

    def set_mode(self, mode):
        self.mode = "login" if mode == "login" else "register"
        is_login = self.mode == "login"
        self.form_stack.setCurrentIndex(0 if is_login else 1)
        if hasattr(self, "mode_segment"):
            self.mode_segment.set_current_key(self.mode)
        self.account_title.setText("登录 Window Pet" if is_login else "注册 Window Pet")
        self.action_button.setText("立即登录" if is_login else "立即注册")

    def identity_input(self):
        return self.login_identity_input if self.mode == "login" else self.register_identity_input

    def password_input(self):
        return self.login_password_input if self.mode == "login" else self.register_password_input

    def normalized_identity(self):
        return self.identity_input().text().strip()

    def valid_identity(self, identity):
        name, _, domain = identity.partition("@")
        return bool(name and "." in domain and not domain.startswith(".") and not domain.endswith("."))

    def user_from_cloud_response(self, response, email, mode):
        response = response or {}
        user = response.get("user") if isinstance(response.get("user"), dict) else {}
        identity = str(user.get("email") or email).strip()
        name = str(user.get("name") or identity.split("@")[0]).strip()
        return {
            "identity": identity,
            "email": identity,
            "phone": "",
            "name": name,
            "provider": str(user.get("provider") or "email"),
            "auth_mode": mode,
            "token": response.get("token"),
            "user_id": user.get("id"),
            "user_number": user.get("userNumber") or user.get("user_number"),
            "invite_code": user.get("inviteCode") or user.get("invite_code"),
            "logged_in_at": datetime.now().isoformat(timespec="seconds"),
        }

    def run_cloud_action(self, title, callback):
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.action_button.setEnabled(False)
        if hasattr(self, "register_code_button"):
            self.register_code_button.setEnabled(False)
        try:
            return callback()
        except CloudApiError as exc:
            QMessageBox.warning(self, title, str(exc))
            return None
        finally:
            QApplication.restoreOverrideCursor()
            self.action_button.setEnabled(True)
            if hasattr(self, "register_code_button"):
                self.register_code_button.setEnabled(True)

    def request_register_code(self):
        identity = self.register_identity_input.text().strip()
        if not self.valid_identity(identity):
            QMessageBox.information(self, "验证码", "请先填写有效邮箱。")
            return
        result = self.run_cloud_action("验证码", lambda: send_register_code(identity))
        if result is not None:
            QMessageBox.information(self, "验证码", "验证码已发送，请去邮箱查看。")

    def accept_login(self):
        identity = self.normalized_identity()
        if not self.valid_identity(identity):
            QMessageBox.information(self, "账号", "请输入有效邮箱。")
            return
        password = self.password_input().text()
        if self.mode == "login" and len(password) < 4:
            QMessageBox.information(self, "登录", "密码至少 4 位。")
            return
        if self.mode == "register":
            if len(password) < 6:
                QMessageBox.information(self, "注册", "密码至少 6 位。")
                return
            if password != self.register_confirm_input.text():
                QMessageBox.information(self, "注册", "两次输入的密码不一致。")
                return
            email_code = self.register_code_input.text().strip()
            if not email_code:
                QMessageBox.information(self, "注册", "请填写邮箱验证码。")
                return
            result = self.run_cloud_action(
                "注册",
                lambda: cloud_register(identity, identity.split("@")[0], password, email_code),
            )
            if result is None:
                return
            self.cloud_account_data = self.user_from_cloud_response(result, identity, "register")
        else:
            result = self.run_cloud_action("登录", lambda: cloud_login(identity, password))
            if result is None:
                return
            self.cloud_account_data = self.user_from_cloud_response(result, identity, "login")
        self.accept()

    def account_data(self):
        if self.cloud_account_data:
            return self.cloud_account_data
        identity = self.normalized_identity()
        is_email = "@" in identity
        name = identity.split("@")[0] if identity else "Window Pet"
        return {
            "identity": identity,
            "email": identity if is_email else "",
            "phone": "" if is_email else identity,
            "name": name,
            "provider": "local",
            "auth_mode": self.mode,
            "local_account_id": f"local:{identity.lower()}",
            "logged_in_at": datetime.now().isoformat(timespec="seconds"),
        }


class DoubaoGuideDialog(QDialog):
    DOUBAO_URL = "https://www.doubao.com/chat/"

    def __init__(self, prompt, assets_root, on_installed, parent=None):
        super().__init__(parent)
        initial_prompt = str(prompt)
        initial_lines = initial_prompt.splitlines()
        if initial_lines and initial_lines[0].startswith("我创建这个角色是"):
            self.prompt_body = "\n".join(initial_lines[1:])
        else:
            self.prompt_body = initial_prompt
        self.prompt = ""
        self.current_mode = "auto"
        self.assets_root = Path(assets_root)
        self.on_installed = on_installed
        self.setObjectName("GlassDialog")
        self.setWindowTitle("豆包生成角色")
        self.setMinimumSize(720, 620)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(12)

        title = QLabel("豆包 AI 角色生成助手")
        title.setObjectName("SectionTitle")
        note = QLabel("支持「极简生图（一键出图）」与「本地全自动部署」两种方式。就算豆包无法直接跑代码，也能画图 100% 成功一键生成桌宠！")
        note.setObjectName("SubtleLabel")
        note.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(note)

        # 模式切换 segmented 按钮
        mode_frame = QFrame()
        mode_frame.setObjectName("AccountSegment")
        mode_layout = QHBoxLayout(mode_frame)
        mode_layout.setContentsMargins(4, 4, 4, 4)
        mode_layout.setSpacing(6)

        self.mode_auto_btn = QPushButton("💻 本地全自动模式 (办公任务 Turbo)")
        self.mode_auto_btn.setObjectName("AccountSegmentButton")
        self.mode_auto_btn.setCheckable(True)
        self.mode_auto_btn.setChecked(True)

        self.mode_simple_btn = QPushButton("🎨 极简生图模式 (手机/网页直接出图 · 推荐)")
        self.mode_simple_btn.setObjectName("AccountSegmentButton")
        self.mode_simple_btn.setCheckable(True)

        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.mode_auto_btn, 0)
        self.mode_group.addButton(self.mode_simple_btn, 1)
        self.mode_group.idClicked.connect(self._on_mode_switched)

        mode_layout.addWidget(self.mode_auto_btn)
        mode_layout.addWidget(self.mode_simple_btn)
        layout.addWidget(mode_frame)

        # 零门槛温馨提示卡片
        self.tips_card = QFrame()
        self.tips_card.setStyleSheet("""
            QFrame {
                background-color: rgba(226, 246, 255, 160);
                border: 1px solid rgba(29, 118, 216, 40);
                border-radius: 12px;
            }
        """)
        tips_layout = QVBoxLayout(self.tips_card)
        tips_layout.setContentsMargins(14, 10, 14, 10)
        tips_layout.setSpacing(4)
        tips_title = QLabel("💡 零门槛出图秘诀（小白推荐！即便豆包无法跑终端代码，也能 100% 成功）：")
        tips_title.setStyleSheet("font-weight: bold; color: #12315b; font-size: 13px;")
        tips_desc = QLabel(
            "1. 复制【极简生图提示词】发给豆包，豆包会为您画出高清 Q 版白底桌宠立绘；\n"
            "2. 手机或网页上右键保存生成的图片；\n"
            "3. 点击下方「🎨 打开九宫格动作工坊」，把图片直接拖进九宫格，一秒自动生成新桌宠！"
        )
        tips_desc.setWordWrap(True)
        tips_desc.setStyleSheet("color: #386381; font-size: 12px; line-height: 1.4;")
        tips_layout.addWidget(tips_title)
        tips_layout.addWidget(tips_desc)
        layout.addWidget(self.tips_card)

        self.doubao_mode_guide_label = QLabel()
        self.doubao_mode_guide_label.setObjectName("DoubaoModeGuide")
        self.doubao_mode_guide_label.setAlignment(Qt.AlignCenter)
        self.doubao_mode_guide_label.setToolTip(
            "在豆包输入框上方选择“办公任务 Turbo”和“本地电脑”"
        )
        guide_pixmap = QPixmap(
            str(resource_path("assets/UiAssets/doubao-local-computer-guide.png"))
        )
        self.doubao_mode_guide_label.setPixmap(
            guide_pixmap.scaled(
                640,
                120,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )
        layout.addWidget(self.doubao_mode_guide_label)

        description_label = QLabel("我想创建的角色")
        description_label.setObjectName("SearchMeta")
        self.character_description_input = QLineEdit()
        self.character_description_input.setPlaceholderText(
            "例如：一只戴红围巾、会弹吉他的白色小猫"
        )
        self.character_description_input.setClearButtonEnabled(True)
        layout.addWidget(description_label)
        layout.addWidget(self.character_description_input)

        self.package_label = QLabel("角色包最终地址")
        self.package_label.setObjectName("SearchMeta")
        self.package_path_label = QLabel(str(self.assets_root / "{角色英文名}Pet"))
        self.package_path_label.setObjectName("SettingsValue")
        self.package_path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.package_path_label.setWordWrap(True)
        layout.addWidget(self.package_label)
        layout.addWidget(self.package_path_label)

        self.prompt_view = QTextEdit()
        self.prompt_view.setObjectName("SettingsNotes")
        self.prompt_view.setReadOnly(True)
        layout.addWidget(self.prompt_view, 1)
        self.character_description_input.textChanged.connect(self.update_prompt)
        self.update_prompt()

        primary_row = QHBoxLayout()
        primary_row.setSpacing(10)
        self.copy_button = QPushButton("复制提示词")
        self.copy_button.setObjectName("ToolPrimaryButton")
        self.copy_button.clicked.connect(self.copy_prompt)

        self.open_button = QPushButton("复制并打开豆包")
        self.open_button.setObjectName("ToolPrimaryButton")
        self.open_button.clicked.connect(self.open_doubao)

        self.studio_button = QPushButton("🎨 打开九宫格动作工坊")
        self.studio_button.setObjectName("ToolPrimaryButton")
        self.studio_button.setToolTip("直接打开角色动作九宫格工坊，将豆包画好的图片拖入即可生成角色")
        self.studio_button.clicked.connect(self.open_action_studio)

        primary_row.addWidget(self.copy_button)
        primary_row.addWidget(self.open_button)
        primary_row.addWidget(self.studio_button)
        layout.addLayout(primary_row)

        footer = QHBoxLayout()
        refresh_button = QPushButton("生成完成，刷新角色库")
        refresh_button.clicked.connect(lambda: self.on_installed(None))
        close_button = QPushButton("关闭")
        close_button.clicked.connect(self.accept)
        footer.addWidget(refresh_button)
        footer.addStretch(1)
        footer.addWidget(close_button)
        layout.addLayout(footer)

    def _on_mode_switched(self, button_id):
        if button_id == 1:
            self.current_mode = "simple"
            self.doubao_mode_guide_label.setVisible(False)
            self.package_label.setVisible(False)
            self.package_path_label.setVisible(False)
            self.copy_button.setText("复制极简生图词")
        else:
            self.current_mode = "auto"
            self.doubao_mode_guide_label.setVisible(True)
            self.package_label.setVisible(True)
            self.package_path_label.setVisible(True)
            self.copy_button.setText("复制全自动提示词")
        self.update_prompt()

    def update_prompt(self, _text=None):
        description = self.character_description_input.text().strip().rstrip("。") or "XXX"
        first_line = f"我创建这个角色是{description}。"
        self.auto_prompt = (
            f"{first_line}\n{self.prompt_body}" if self.prompt_body else first_line
        )
        self.simple_prompt = build_doubao_image_prompt(description)
        if self.current_mode == "simple":
            self.prompt = self.simple_prompt
        else:
            self.prompt = self.auto_prompt
        self.prompt_view.setPlainText(self.prompt)

    def open_action_studio(self):
        parent = self.parent()
        if parent is not None and hasattr(parent, "open_character_action_studio"):
            parent.open_character_action_studio()
        else:
            from .character_action_studio import CharacterActionStudioDialog
            dialog = CharacterActionStudioDialog(parent=self)
            dialog.exec()

    def copy_prompt(self):
        QApplication.clipboard().setText(self.prompt)
        mode_name = "极简生图提示词" if self.current_mode == "simple" else "提示词"
        QMessageBox.information(self, "豆包生成", f"{mode_name}已复制。")

    def open_doubao(self):
        QApplication.clipboard().setText(self.prompt)
        if not QDesktopServices.openUrl(QUrl(self.DOUBAO_URL)):
            QMessageBox.warning(self, "豆包生成", "无法打开豆包网页，提示词已经复制，可手动粘贴。")

class RedeemCharacterDialog(QDialog):
    def __init__(self, token, assets_root, on_installed, parent=None):
        super().__init__(parent)
        self.token = str(token or "")
        self.assets_root = Path(assets_root)
        self.on_installed = on_installed
        self.setObjectName("GlassDialog")
        PetCursorManager.apply_to_window(self)
        self.setWindowTitle("兑换角色")
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        hero_row = QHBoxLayout()
        hero_row.setSpacing(16)
        hero_icon = QLabel()
        hero_icon.setFixedSize(76, 76)
        hero_pix = QPixmap(str(resource_path("assets/UiAssets/card-redeem-character.png")))
        if not hero_pix.isNull():
            hero_icon.setPixmap(hero_pix.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        hero_icon.setAlignment(Qt.AlignCenter)
        hero_row.addWidget(hero_icon)

        hero_text = QVBoxLayout()
        hero_text.setSpacing(4)
        title = QLabel("兑换云端专属角色")
        title.setObjectName("SectionTitle")
        note = QLabel("登录账号后，输入兑换码即可安全导入专属角色包，不会覆盖本地已有角色。")
        note.setObjectName("SubtleLabel")
        note.setWordWrap(True)
        hero_text.addWidget(title)
        hero_text.addWidget(note)
        hero_row.addLayout(hero_text, 1)
        layout.addLayout(hero_row)

        self.code_input = VibeInput(
            "输入角色兑换码，例如：WP-ABCD-1234",
            icon_path=str(resource_path("assets/UiAssets/card-redeem-character.png")),
        )
        self.code_input.returnPressed.connect(self.redeem)
        layout.addWidget(self.code_input)

        self.status_label = QLabel("角色兑换与下载服务由 WindowPet 云端官方提供。")
        self.status_label.setObjectName("SubtleLabel")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        buttons.setSpacing(12)
        cancel_button = VibeButton("取消", variant="secondary")
        cancel_button.clicked.connect(self.reject)
        self.redeem_button = VibeButton("立即兑换", variant="primary")
        self.redeem_button.clicked.connect(self.redeem)
        buttons.addWidget(cancel_button)
        buttons.addWidget(self.redeem_button)
        layout.addLayout(buttons)

    def redeem(self):
        code = re.sub(r"\s+", "", self.code_input.text().strip().upper())
        if not code:
            QMessageBox.information(self, "兑换角色", "请输入兑换码。")
            return
        if not re.fullmatch(r"[A-Z0-9-]{4,32}", code):
            QMessageBox.information(self, "兑换角色", "兑换码格式不正确。")
            return

        # 1. 检查是否为小鼻嘎展馆官方公开兑换码（支持免登录直接激活）
        public_map = {
            "WPX-2026-JIYI": ("JiyiPet", "吉伊"),
            "WPX-2026-DORA": ("NuonuoPet", "糯糯 Dora"),
            "WPX-2026-FOX": ("HuhuPet", "小狐狸"),
            "WPX-2026-XBA": ("XiaobaPet", "小八猫"),
            "WPX-2026-USAGI": ("UsagiPet", "乌萨奇兔兔"),
            "WPX-2026-XCHAI": ("XiaochaiPet", "小柴犬"),
            "WPX-2026-CAPY": ("LuluCapybaraPet", "卡皮巴拉 水豚"),
            "WPX-2026-BEAR": ("BearPet", "抱抱小熊"),
            "WPX-2026-BUBU": ("BubuPet", "布布鼠"),
            "WPX-2026-BUYA": ("BuyaPet", "不鸭"),
            "WPX-2026-WORK": ("SalaryCatPet", "打工猫"),
            "WPX-2026-KUN": ("KunLikePet", "小中分"),
            "WPX-2026-POPO": ("PopoPet", "啵啵 Popo"),
            "WPX-2026-LOGO": ("LogoGuineaPigPet", "豚鼠小鼻嘎"),
            "WPX-2026-MIAN": ("MianmianPet", "绵绵羊"),
            "WPX-2026-PANDA": ("PandaPet", "功夫大熊猫"),
            "WPX-2026-PENG": ("PenguinSisterPet", "企鹅妹妹"),
            "WPX-2026-KUMI": ("KumikoPet", "库库咔咔"),
            "WPX-2026-RED": ("Huhu2Pet", "赤狐烈焰"),
            "WPX-2026-TRACK": ("XiaobaTurnPet", "家宠·麦脆角 (摇头猫)"),
            "WPX-HOME-CAT": ("XiaobaTurnPet", "家宠·麦脆角 (摇头猫)"),
            "WPX-2026-NEZU": ("NezukoPet", "祢豆子"),
        }
        if code in public_map:
            folder, pet_name = public_map[code]
            target_path = Path(self.assets_root) / folder
            if not target_path.exists():
                cand = Path(__file__).resolve().parent.parent / "assets" / folder
                if cand.exists():
                    target_path = cand
            if target_path.exists():
                self.on_installed(target_path)
                QMessageBox.information(
                    self,
                    "兑换成功",
                    f"🎉 官方展馆公开兑换码验证成功！\n\n已为您成功解锁并激活小鼻嘎【{pet_name}】！",
                )
                self.accept()
                return

        if not self.token:
            QMessageBox.information(self, "兑换角色", "该兑换码需要联网核销，请先在控制台右上角登录账号。")
            return

        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.redeem_button.setEnabled(False)
        self.status_label.setText("正在验证兑换码并安全导入角色……")
        QApplication.processEvents()
        try:
            response = cloud_redeem_character(code, self.token)
            download = response.get("download") if isinstance(response, dict) else None
            if not isinstance(download, dict) or not download.get("url"):
                raise CharacterAcquisitionError("云端没有返回角色包，兑换尚未完成。")
            installed = download_and_install_character(download, self.assets_root)
            self.on_installed(installed)
        except (CloudApiError, CharacterAcquisitionError) as exc:
            self.status_label.setText(str(exc))
            QMessageBox.warning(self, "兑换角色", str(exc))
            return
        finally:
            QApplication.restoreOverrideCursor()
            self.redeem_button.setEnabled(True)

        QMessageBox.information(self, "兑换角色", f"兑换成功，角色已导入：\n{installed}")
        self.accept()


class UninstallDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassDialog")
        self.setWindowTitle("彻底删除 Window Pet")
        self.setMinimumWidth(520)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        hero_row = QHBoxLayout()
        hero_row.setSpacing(14)
        hero_icon = QLabel()
        hero_icon.setObjectName("AccountHeroIcon")
        hero_icon.setFixedSize(82, 82)
        jiyi_pixmap = QPixmap(str(resource_path("assets/JiyiPet/jiyi_01.png")))
        if not jiyi_pixmap.isNull():
            hero_icon.setPixmap(jiyi_pixmap.scaled(76, 76, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            hero_icon.setAlignment(Qt.AlignCenter)
        hero_text = QVBoxLayout()
        hero_text.setContentsMargins(0, 0, 0, 0)
        hero_text.setSpacing(6)
        title = QLabel("吉小伊想和主银好好告别")
        title.setObjectName("SectionTitle")
        message = QLabel(
            "非常感谢主银能给我一次陪伴的机会。现在的我还不够完善，但是我会努力变得越来越好。"
            "有一天再次和主银相见，请主银放心，我会带走我所有的东西，争取不给主银添麻烦，"
            "也非常希望主银给我一些建议。"
        )
        message.setObjectName("SubtleLabel")
        message.setWordWrap(True)
        hero_text.addWidget(title)
        hero_text.addWidget(message)
        hero_row.addWidget(hero_icon)
        hero_row.addLayout(hero_text, 1)
        layout.addLayout(hero_row)

        details = QLabel("确认后会退出程序，并删除当前 Window Pet 文件夹、本地配置、日志和快捷方式。")
        details.setObjectName("ActivityRuleText")
        details.setWordWrap(True)
        layout.addWidget(details)

        self.feedback_input = QTextEdit()
        self.feedback_input.setObjectName("SettingsNotes")
        self.feedback_input.setPlaceholderText("可以写一点建议给吉小伊：哪里不好用、希望下次变成什么样")
        self.feedback_input.setMinimumHeight(86)
        self.feedback_input.setMaximumHeight(126)
        layout.addWidget(self.feedback_input)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        cancel_button = QPushButton("取消卸载")
        cancel_button.clicked.connect(self.reject)
        uninstall_button = QPushButton("确认卸载")
        uninstall_button.setObjectName("DangerButton")
        uninstall_button.clicked.connect(self.accept)
        button_row.addWidget(cancel_button)
        button_row.addWidget(uninstall_button)
        layout.addLayout(button_row)

    def feedback_text(self):
        return self.feedback_input.toPlainText().strip()


class ToolChoiceButton(QPushButton):
    ICON_FILES = {
        "search": "assets/UiAssets/tool-search.png",
        "bell": "assets/UiAssets/tool-bell.png",
        "timer": "assets/UiAssets/tool-timer.png",
        "memo": "assets/UiAssets/tool-memo.png",
        "magic": "assets/UiAssets/tool-magic.png",
        "wallpaper": "assets/UiAssets/tool-wallpaper.png",
    }

    def __init__(self, icon_key, title, subtitle="", parent=None):
        super().__init__(parent)
        self.icon_key = icon_key
        self.title = title
        self.subtitle = subtitle
        self.setCheckable(True)
        self.setCursor(PetCursorManager.pointer_cursor())
        self.setFocusPolicy(Qt.NoFocus)
        self.setMinimumHeight(76)
        self.setObjectName("ToolChoiceButton")
        self.setToolTip(title)
        self.setIcon(self.load_icon(icon_key))
        self.setIconSize(QSize(42, 42))
        self.set_content(title, subtitle)

        self._hover_lift: float = 0.0
        self._lift_anim = QPropertyAnimation(self, b"hoverLift", self)
        self._lift_anim.setDuration(160)
        self._lift_anim.setEasingCurve(QEasingCurve.OutCubic)

    def get_hover_lift(self) -> float:
        return self._hover_lift

    def set_hover_lift(self, v: float):
        self._hover_lift = v
        self.update()

    hoverLift = Property(float, get_hover_lift, set_hover_lift)

    def enterEvent(self, event):
        self._lift_anim.stop()
        self._lift_anim.setStartValue(self._hover_lift)
        self._lift_anim.setEndValue(3.0)
        self._lift_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._lift_anim.stop()
        self._lift_anim.setStartValue(self._hover_lift)
        self._lift_anim.setEndValue(0.0)
        self._lift_anim.start()
        super().leaveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self._hover_lift > 0.01:
            painter.setRenderHints(QPainter.Antialiasing)
            s_rect = QRectF(self.rect()).adjusted(4, 5, -4, 2)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(255, 120, 140, int(30 * (self._hover_lift / 3.0))))
            painter.drawRoundedRect(s_rect, 20, 20)
            painter.translate(0, -self._hover_lift)
        super().paintEvent(event)

    def set_content(self, title, subtitle=""):
        self.title = str(title)
        self.subtitle = str(subtitle)
        self.setToolTip(self.title)
        self.setText(f"{self.title}\n{self.subtitle}" if self.subtitle else self.title)

    def load_icon(self, icon_key):
        file_rel = self.ICON_FILES.get(icon_key)
        if file_rel:
            p = resource_path(file_rel)
            if p.exists():
                return QIcon(str(p))
        return make_sticker_icon(icon_key, UI_INK, 48)

    def make_icon(self, icon_key, color):
        pixmap = QPixmap(40, 40)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        self.draw_icon(painter, QRectF(2, 2, 36, 36), color)
        painter.end()
        return QIcon(pixmap)

    def draw_icon(self, painter, rect, color):
        painter.save()
        painter.setPen(QPen(color, 2.6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(Qt.NoBrush)
        cx = rect.center().x()
        cy = rect.center().y()

        if self.icon_key == "search":
            page = QRectF(rect.left() + 4, rect.top() + 3, 21, 25)
            painter.drawRoundedRect(page, 4, 4)
            painter.drawLine(QPointF(page.right() - 5, page.top()), QPointF(page.right(), page.top() + 5))
            painter.drawEllipse(QPointF(cx + 5, cy + 5), 7, 7)
            painter.drawLine(QPointF(cx + 10, cy + 10), QPointF(rect.right() - 1, rect.bottom() - 1))
        elif self.icon_key == "bell":
            bell = QPainterPath()
            bell.moveTo(cx - 11, cy + 7)
            bell.cubicTo(cx - 6, cy + 4, cx - 8, cy - 1, cx - 7, cy - 7)
            bell.cubicTo(cx - 6, cy - 14, cx + 6, cy - 14, cx + 7, cy - 7)
            bell.cubicTo(cx + 8, cy - 1, cx + 6, cy + 4, cx + 11, cy + 7)
            bell.closeSubpath()
            painter.drawPath(bell)
            painter.drawArc(QRectF(cx - 4, cy + 5, 8, 9), 200 * 16, 140 * 16)
            painter.drawLine(QPointF(cx + 14, cy - 8), QPointF(cx + 17, cy - 3))
        elif self.icon_key == "timer":
            painter.drawEllipse(QPointF(cx, cy + 1), 13, 13)
            painter.drawRoundedRect(QRectF(cx - 5, cy - 18, 10, 5), 2, 2)
            painter.drawLine(QPointF(cx, cy + 1), QPointF(cx + 7, cy - 6))
            painter.drawLine(QPointF(cx + 9, cy - 12), QPointF(cx + 13, cy - 16))
            painter.drawArc(QRectF(cx - 9, cy - 8, 18, 18), 250 * 16, 70 * 16)
        elif self.icon_key == "memo":
            note = QRectF(cx - 13, cy - 14, 26, 28)
            painter.drawRoundedRect(note, 5, 5)
            painter.drawLine(QPointF(cx + 6, cy + 14), QPointF(cx + 13, cy + 7))
            painter.drawLine(QPointF(cx - 6, cy), QPointF(cx - 1, cy + 5))
            painter.drawLine(QPointF(cx - 1, cy + 5), QPointF(cx + 8, cy - 6))
        elif self.icon_key == "magic":
            painter.drawLine(QPointF(cx - 14, cy + 14), QPointF(cx + 9, cy - 9))
            star = QPainterPath()
            star.moveTo(cx + 11, cy - 17)
            star.lineTo(cx + 14, cy - 10)
            star.lineTo(cx + 21, cy - 8)
            star.lineTo(cx + 14, cy - 5)
            star.lineTo(cx + 12, cy + 2)
            star.lineTo(cx + 8, cy - 5)
            star.lineTo(cx + 1, cy - 7)
            star.lineTo(cx + 8, cy - 10)
            star.closeSubpath()
            painter.drawPath(star)
            feather = QPainterPath()
            feather.moveTo(cx + 6, cy + 12)
            feather.cubicTo(cx + 14, cy + 1, cx + 20, cy + 4, cx + 17, cy + 15)
            feather.cubicTo(cx + 13, cy + 18, cx + 9, cy + 18, cx + 6, cy + 12)
            painter.drawPath(feather)
            painter.drawLine(QPointF(cx + 7, cy + 15), QPointF(cx + 17, cy + 5))
        elif self.icon_key == "wallpaper":
            frame = QRectF(cx - 15, cy - 11, 30, 22)
            painter.drawRoundedRect(frame, 5, 5)
            painter.drawEllipse(QPointF(cx + 8, cy - 5), 2.5, 2.5)
            mountain = QPainterPath()
            mountain.moveTo(frame.left() + 3, frame.bottom() - 3)
            mountain.lineTo(cx - 5, cy + 1)
            mountain.lineTo(cx + 1, cy + 7)
            mountain.lineTo(cx + 7, cy + 1)
            mountain.lineTo(frame.right() - 3, frame.bottom() - 3)
            painter.drawPath(mountain)

        painter.restore()


class WallpaperSlotCard(QFrame):
    def __init__(self, slot, choose_callback, parent=None):
        super().__init__(parent)
        self.slot = dict(slot)
        self.choose_callback = choose_callback
        self.setObjectName("WallpaperSlotCard")
        self.setAcceptDrops(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(170)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.preview = QLabel()
        self.preview.setObjectName("WallpaperPreview")
        self.preview.setFixedHeight(96)
        self.preview.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.preview)

        self.title = QLabel()
        self.title.setObjectName("SearchMeta")
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title)

        self.hint = QLabel()
        self.hint.setObjectName("SubtleLabel")
        self.hint.setAlignment(Qt.AlignCenter)
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)

        self.refresh(slot)

    def refresh(self, slot):
        self.slot = dict(slot)
        path = Path(str(self.slot.get("path") or ""))
        self.title.setText(str(self.slot.get("label") or self.slot.get("time") or ""))
        self.hint.setText(path.name if path.name else "拖一张图片到这里")
        self.setToolTip(str(path))

        pixmap = QPixmap(str(path)) if path.exists() else QPixmap()
        if pixmap.isNull():
            placeholder = QPixmap(320, 180)
            placeholder.fill(QColor("#e0f2fe"))
            painter = QPainter(placeholder)
            painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
            painter.setPen(QPen(QColor("#1d4ed8"), 2))
            painter.drawRoundedRect(QRectF(8, 8, 304, 164), 18, 18)
            painter.setPen(QColor("#64748b"))
            painter.drawText(placeholder.rect(), Qt.AlignCenter, "拖入壁纸")
            painter.end()
            pixmap = placeholder
        self.preview.setPixmap(pixmap.scaled(180, 96, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation))

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.choose_callback(self.slot.get("id"))
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        menu = style_menu(QMenu(self))
        choose_action = QAction("更换图片", self)
        choose_action.triggered.connect(lambda: self.choose_callback(self.slot.get("id")))
        menu.addAction(choose_action)
        menu.exec(event.globalPos())

    def dragEnterEvent(self, event):
        if self.first_supported_file(event.mimeData()):
            event.acceptProposedAction()
            return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        path = self.first_supported_file(event.mimeData())
        if path:
            self.choose_callback(self.slot.get("id"), path)
            event.acceptProposedAction()
            return
        super().dropEvent(event)

    def first_supported_file(self, mime_data):
        if mime_data is None or not mime_data.hasUrls():
            return None
        for url in mime_data.urls():
            if not url.isLocalFile():
                continue
            path = Path(url.toLocalFile())
            if path.is_file() and path.suffix.lower() in SUPPORTED_WALLPAPER_EXTENSIONS:
                return path
        return None


class PetLibraryItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_list = parent
        self.hovered_row: int = -1
        self.hover_factor: float = 0.0
        self._target_factor: float = 0.0
        self.pressed_row: int = -1

        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(16)  # ~60fps
        self._anim_timer.timeout.connect(self._step_hover_anim)

        if self.parent_list is not None:
            self.parent_list.setMouseTracking(True)
            if hasattr(self.parent_list, "viewport") and self.parent_list.viewport():
                self.parent_list.viewport().setMouseTracking(True)
                self.parent_list.viewport().installEventFilter(self)
            self.parent_list.setCursor(PetCursorManager.pointer_cursor())

    def eventFilter(self, obj, event):
        try:
            if not self.parent_list:
                return super().eventFilter(obj, event)
            vp = self.parent_list.viewport() if hasattr(self.parent_list, "viewport") else None
            if obj != vp:
                return super().eventFilter(obj, event)

            t = event.type()
            if t == QEvent.MouseMove:
                pos = event.pos()
                idx = self.parent_list.indexAt(pos)
                row = idx.row() if idx.isValid() else -1
                if row != self.hovered_row:
                    self.hovered_row = row
                    self._target_factor = 1.0 if row >= 0 else 0.0
                    if not self._anim_timer.isActive():
                        self._anim_timer.start()
            elif t == QEvent.Leave:
                self.hovered_row = -1
                self._target_factor = 0.0
                if not self._anim_timer.isActive():
                    self._anim_timer.start()
            elif t == QEvent.MouseButtonPress:
                pos = event.pos()
                idx = self.parent_list.indexAt(pos)
                self.pressed_row = idx.row() if idx.isValid() else -1
                self.parent_list.viewport().update()
            elif t == QEvent.MouseButtonRelease:
                self.pressed_row = -1
                self.parent_list.viewport().update()
        except (RuntimeError, Exception):
            return False
        return super().eventFilter(obj, event)

    def _step_hover_anim(self):
        try:
            diff = self._target_factor - self.hover_factor
            if abs(diff) < 0.03:
                self.hover_factor = self._target_factor
                if self._target_factor == 0.0 and self.hovered_row < 0:
                    self._anim_timer.stop()
            else:
                self.hover_factor += diff * 0.35
            if self.parent_list and hasattr(self.parent_list, "viewport") and self.parent_list.viewport():
                self.parent_list.viewport().update()
        except (RuntimeError, Exception):
            if self._anim_timer.isActive():
                self._anim_timer.stop()

    def sizeHint(self, option, index):
        return QSize(100, 112)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)

        row = index.row()
        is_hovered = (row == self.hovered_row)
        is_pressed = (row == self.pressed_row)
        h = self.hover_factor if is_hovered else 0.0

        # Dynamic Lift & Press Sink
        raw_rect = QRectF(option.rect).adjusted(4, 4, -4, -4)
        dy = -5.0 * h
        if is_pressed:
            dy += 2.0
        rect = raw_rect.translated(0, dy)

        card_radius = 18
        card_path = QPainterPath()
        card_path.addRoundedRect(rect, card_radius, card_radius)
        locked = bool(index.data(LIBRARY_LOCKED_ROLE))
        library_action = str(index.data(LIBRARY_ACTION_ROLE) or "")
        selected = bool(option.state & QStyle.State_Selected)

        # 1. Soft Blooming Drop Shadow (underneath the lifted card)
        if h > 0.01:
            shadow_rect = rect.translated(0, 6.5).adjusted(-1, 0, 1, 4)
            if library_action == "redeem":
                bloom1 = QColor(245, 190, 80, int(35 * h))
                bloom2 = QColor(230, 160, 40, int(55 * h))
            else:
                bloom1 = QColor(255, 120, 140, int(32 * h))
                bloom2 = QColor(255, 90, 115, int(48 * h))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(bloom1))
            painter.drawRoundedRect(shadow_rect.adjusted(-2, 0, 2, 2), card_radius + 3, card_radius + 3)
            painter.setBrush(QBrush(bloom2))
            painter.drawRoundedRect(shadow_rect, card_radius, card_radius)

        # 2. Card Background Body
        if locked:
            painter.save()
            painter.setClipPath(card_path)
            locked_path = index.data(LIBRARY_LOCK_IMAGE_ROLE)
            locked_pixmap = QPixmap(str(locked_path)) if locked_path else QPixmap()
            if not locked_pixmap.isNull():
                painter.drawPixmap(
                    rect.toRect(),
                    locked_pixmap.scaled(rect.size().toSize(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation),
                )
            else:
                fill = QLinearGradient(rect.topLeft(), rect.bottomRight())
                fill.setColorAt(0.0, QColor("#eef1f5"))
                fill.setColorAt(0.55, QColor("#dfe5ec"))
                fill.setColorAt(1.0, QColor("#cdd6df"))
                painter.fillPath(card_path, QBrush(fill))
                painter.setPen(QPen(QColor(113, 128, 150, 60), 1))
                for offset in (25, 50, 75):
                    painter.drawLine(QPointF(rect.left() + offset, rect.top() + 8), QPointF(rect.left() + offset, rect.bottom() - 8))
            painter.restore()
            painter.setPen(QPen(QColor("#cbd5df"), 1.2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, card_radius, card_radius)
        elif library_action:
            fill = QLinearGradient(rect.topLeft(), rect.bottomRight())
            if library_action == "doubao":
                fill.setColorAt(0.0, QColor("#fff8e8"))
                fill.setColorAt(0.58, QColor("#fff0d2"))
                fill.setColorAt(1.0, QColor("#f5eaff"))
            else:
                fill.setColorAt(0.0, QColor("#fffdf7"))
                fill.setColorAt(0.58, QColor("#fff2c9"))
                fill.setColorAt(1.0, QColor("#e7f8f3"))
            painter.fillPath(card_path, QBrush(fill))
            border_base = QColor("#e4c97d") if library_action == "redeem" else QColor("#d7b7df")
            if h > 0.01:
                border_base = QColor("#f3b23e") if library_action == "redeem" else QColor("#e5a5f2")
            painter.setPen(QPen(border_base, 1.4 + 0.8 * h))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, card_radius, card_radius)
        else:
            fill = QLinearGradient(rect.topLeft(), rect.bottomRight())
            fill.setColorAt(0.0, QColor("#ffffff"))
            fill.setColorAt(0.62, QColor("#fffaf7"))
            fill.setColorAt(1.0, QColor("#f7fbfa"))
            painter.fillPath(card_path, QBrush(fill))
            border_base = UI_BORDER
            if h > 0.01:
                border_base = QColor("#ff8da1")
            painter.setPen(QPen(border_base, 1.2 + 0.8 * h))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, card_radius, card_radius)

        # 3. Selection or Hover Highlights
        if selected or h > 0.01:
            tint_alpha = 150 if selected else int(75 * h)
            fill = QColor(255, 230, 233, tint_alpha)
            pen_color = UI_PRIMARY if selected else QColor("#ff7a8a")
            painter.setPen(QPen(pen_color, 2.0 if selected else (1.3 + 0.7 * h)))
            painter.setBrush(QBrush(fill))
            painter.drawRoundedRect(rect, card_radius, card_radius)

        # 4. Icon with Micro-Zoom on Hover
        zoom = 1.0 + 0.06 * h
        icon_w = int(68 * zoom)
        icon_h = int(68 * zoom)
        icon_size = QSize(icon_w, icon_h)
        icon_rect = QRectF(
            rect.left() + (rect.width() - icon_w) / 2.0,
            rect.top() + 7.0 - (icon_h - 68) / 2.0,
            icon_w,
            icon_h,
        )

        if locked:
            draw_lock_icon(painter, icon_rect, QColor("#5f4725"))
        elif library_action:
            if library_action == "doubao":
                draw_rounded_cover_image(
                    painter,
                    icon_rect.adjusted(3, 3, -3, -3),
                    resource_path("assets/UiAssets/doubao-avatar.png"),
                    15,
                )
            elif library_action == "redeem":
                draw_rounded_cover_image(
                    painter,
                    icon_rect.adjusted(2, 2, -2, -2),
                    resource_path("assets/UiAssets/card-redeem-character.png"),
                    16,
                )
            else:
                draw_sticker_icon(
                    painter,
                    icon_rect.adjusted(8, 8, -8, -8),
                    "medals",
                    QColor("#9b7124"),
                    selected,
                )
        else:
            icon_data = index.data(Qt.DecorationRole)
            pixmap = QPixmap()
            if isinstance(icon_data, QIcon):
                pixmap = icon_data.pixmap(icon_size)
            elif isinstance(icon_data, QPixmap):
                pixmap = icon_data.scaled(icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            if not pixmap.isNull():
                target = pixmap.scaled(icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                target_rect = QRectF(
                    icon_rect.left() + (icon_rect.width() - target.width()) / 2.0,
                    icon_rect.top() + (icon_rect.height() - target.height()) / 2.0,
                    target.width(),
                    target.height(),
                )
                painter.drawPixmap(target_rect.toRect(), target)

        # 5. Name Badge Pill (Lifts dynamically with card)
        text = str(index.data(Qt.DisplayRole) or "").strip()
        if locked:
            text = "未解锁"
        if text:
            font = option.font
            font.setFamily("Microsoft YaHei UI")
            font.setBold(True)
            font.setPointSize(8)
            painter.setFont(font)
            metrics = painter.fontMetrics()
            text_width = max(36, int(rect.width()) - 16)
            label = metrics.elidedText(text, Qt.ElideRight, text_width)
            badge_height = 22
            badge_width = min(rect.width() - 8, max(50, metrics.horizontalAdvance(label) + 16))
            badge = QRectF(
                rect.left() + (rect.width() - badge_width) / 2.0,
                rect.bottom() - badge_height - 3.0,
                badge_width,
                badge_height,
            )

            badge_border = QColor("#ffc2c8") if not locked else QColor("#cbd5df")
            badge_bg = QColor("#fff0f2") if not locked else QColor("#eef1f5")
            if h > 0.01 and not locked:
                badge_border = QColor("#ff8da1")
                badge_bg = QColor("#ffe8ec")

            painter.setPen(QPen(badge_border, 1.1 + 0.4 * h))
            painter.setBrush(QBrush(badge_bg))
            painter.drawRoundedRect(badge, 13, 13)
            painter.setPen(UI_INK if not locked else UI_MUTED)
            painter.drawText(badge.toRect(), Qt.AlignCenter, label)

        painter.restore()


class ActivityPetGalleryItemDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        return QSize(88, 104)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)

        rect = QRectF(option.rect).adjusted(4, 4, -4, -4)
        selected = bool(option.state & QStyle.State_Selected)
        hovered = bool(option.state & QStyle.State_MouseOver)
        locked = bool(index.data(LIBRARY_LOCKED_ROLE))

        card_radius = 20
        card_path = QPainterPath()
        card_path.addRoundedRect(rect, card_radius, card_radius)
        fill = QLinearGradient(rect.topLeft(), rect.bottomRight())
        fill.setColorAt(0.0, QColor("#ffffff"))
        fill.setColorAt(0.58, QColor("#fff8f6"))
        fill.setColorAt(1.0, QColor("#f3fbf9"))
        painter.fillPath(card_path, QBrush(fill))
        if locked:
            painter.fillPath(card_path, QBrush(QColor(95, 71, 37, 42)))

        if selected:
            fill = QLinearGradient(rect.topLeft(), rect.bottomRight())
            fill.setColorAt(0.0, QColor("#ffffff"))
            fill.setColorAt(0.45, QColor("#fff2f4"))
            fill.setColorAt(1.0, QColor("#ffe2e7"))
            painter.fillPath(card_path, QBrush(fill))
            painter.setPen(QPen(QColor("#ff5c75"), 2.2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, card_radius, card_radius)
        elif hovered:
            painter.setPen(QPen(QColor("#ff9bb0"), 1.6))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, card_radius, card_radius)
        else:
            painter.setPen(QPen(QColor("#e8ded8"), 1.2))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(rect, card_radius, card_radius)

        path_data = index.data(Qt.UserRole)
        is_running = False
        if path_data:
            resolved_p = Path(path_data).resolve()
            is_running = any(Path(w.asset_path).resolve() == resolved_p for w in state.WINDOWS)
        if is_running:
            dot_rect = QRectF(rect.left() + 7, rect.top() + 7, 9, 9)
            painter.setPen(QPen(QColor("#ffffff"), 1.5))
            painter.setBrush(QBrush(QColor("#10b981")))
            painter.drawEllipse(dot_rect)

        icon_size = QSize(58, 58)
        icon_rect = QRectF(rect.left() + (rect.width() - icon_size.width()) / 2, rect.top() + 6, icon_size.width(), icon_size.height())
        icon_data = index.data(Qt.DecorationRole)
        pixmap = QPixmap()
        if isinstance(icon_data, QIcon):
            pixmap = icon_data.pixmap(icon_size)
        elif isinstance(icon_data, QPixmap):
            pixmap = icon_data.scaled(icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if not pixmap.isNull():
            target = pixmap.scaled(icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            target_rect = QRectF(
                icon_rect.left() + (icon_rect.width() - target.width()) / 2,
                icon_rect.top() + (icon_rect.height() - target.height()) / 2,
                target.width(),
                target.height(),
            )
            painter.drawPixmap(target_rect.toRect(), target)

        if locked:
            lock_rect = QRectF(rect.right() - 32, rect.top() + 8, 24, 24)
            badge_path = QPainterPath()
            badge_path.addRoundedRect(lock_rect, 14, 14)
            painter.fillPath(badge_path, QBrush(QColor("#e7ddc6")))
            painter.setPen(QPen(QColor("#5f4725"), 2))
            painter.drawRoundedRect(lock_rect, 12, 12)
            draw_lock_icon(painter, lock_rect.adjusted(4, 4, -4, -4), QColor("#5f4725"))

        text = str(index.data(Qt.DisplayRole) or "").strip()
        if text:
            font = option.font
            font.setFamily("Microsoft YaHei UI")
            font.setBold(True)
            font.setPointSize(8)
            painter.setFont(font)
            metrics = painter.fontMetrics()
            text_width = max(38, int(rect.width()) - 14)
            label = metrics.elidedText(text, Qt.ElideRight, text_width)
            badge_height = 21
            badge_width = min(rect.width() - 8, max(50, metrics.horizontalAdvance(label) + 14))
            badge = QRectF(
                rect.left() + (rect.width() - badge_width) / 2,
                rect.bottom() - badge_height - 3,
                badge_width,
                badge_height,
            )
            if selected:
                painter.setPen(QPen(QColor("#ff92a4"), 1.2))
                painter.setBrush(QBrush(QColor("#ffe8ec")))
                painter.drawRoundedRect(badge, 13, 13)
                painter.setPen(QColor("#d83852"))
            elif not locked:
                painter.setPen(QPen(QColor("#ffc2c8"), 1.1))
                painter.setBrush(QBrush(QColor("#fff0f2")))
                painter.drawRoundedRect(badge, 13, 13)
                painter.setPen(UI_INK)
            else:
                painter.setPen(QPen(QColor("#cbd5df"), 1.1))
                painter.setBrush(QBrush(QColor("#eef1f5")))
                painter.drawRoundedRect(badge, 13, 13)
                painter.setPen(UI_MUTED)
            painter.drawText(badge.toRect(), Qt.AlignCenter, label)

        painter.restore()


class GardenPreviewLabel(QLabel):
    _garden_pixmap = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pet_pixmap = QPixmap()
        self._locked_pixmap = QPixmap()
        self._locked_preview = False
        self._action_hint = ""
        self._action_title = ""
        self._action_description = ""

        # Dynamic Animation & Interaction State
        self._current_asset = None
        self._idle_frames = []
        self._idle_fps = 8
        self._active_frames = []
        self._active_fps = 8
        self._frame_index = 0
        self._is_action_active = False
        self._action_loop_count = 0
        self._max_action_loops = 1
        self._available_actions = []

        # Interactive click bounce / squish offset
        self._bounce_dy = 0.0
        self._bounce_timer = QTimer(self)
        self._bounce_timer.setInterval(16)
        self._bounce_timer.timeout.connect(self._step_bounce)

        # Main frame stepper timer
        self._frame_timer = QTimer(self)
        self._frame_timer.timeout.connect(self._advance_frame)

        # Spontaneous random action timer
        self._random_action_timer = QTimer(self)
        self._random_action_timer.setSingleShot(True)
        self._random_action_timer.timeout.connect(self._trigger_random_action)

        # GIF player support
        self._movie = None

        self.setCursor(PetCursorManager.pointer_cursor())

    @classmethod
    def garden_pixmap(cls):
        if cls._garden_pixmap is None:
            image_path = resource_path("assets/UiAssets/pet-garden-card-bg.png")
            cls._garden_pixmap = QPixmap(str(image_path)) if image_path.exists() else QPixmap()
        return cls._garden_pixmap

    def _stop_animation(self):
        if self._frame_timer.isActive():
            self._frame_timer.stop()
        if self._random_action_timer.isActive():
            self._random_action_timer.stop()
        if self._movie is not None:
            self._movie.stop()
            self._movie = None
        self._idle_frames = []
        self._active_frames = []
        self._frame_index = 0
        self._is_action_active = False

    def setPetPixmap(self, pixmap):
        self._stop_animation()
        self._pet_pixmap = pixmap if isinstance(pixmap, QPixmap) else QPixmap()
        self._locked_pixmap = QPixmap()
        self._locked_preview = False
        self._action_hint = ""
        self.update()

    def clearPetPixmap(self):
        self._stop_animation()
        self._pet_pixmap = QPixmap()
        self._locked_pixmap = QPixmap()
        self._locked_preview = False
        self._action_hint = ""
        self.update()

    def setLockedPixmap(self, pixmap):
        self._stop_animation()
        self._pet_pixmap = QPixmap()
        self._locked_pixmap = pixmap if isinstance(pixmap, QPixmap) else QPixmap()
        self._locked_preview = True
        self._action_hint = ""
        self.update()

    def setActionHint(self, action, title, description):
        self._stop_animation()
        self._pet_pixmap = QPixmap()
        self._locked_pixmap = QPixmap()
        self._locked_preview = False
        self._action_hint = str(action or "")
        self._action_title = str(title or "")
        self._action_description = str(description or "")
        self.update()

    def setPetAsset(self, asset):
        self._current_asset = asset
        self._stop_animation()
        self._locked_preview = False
        self._action_hint = ""

        if asset is None:
            self._pet_pixmap = QPixmap()
            self.update()
            return

        p = Path(asset.path)
        meta = asset.metadata or {}
        anims = meta.get("animations", {}) if isinstance(meta.get("animations"), dict) else {}

        self._idle_frames = []
        self._idle_fps = 8
        self._available_actions = []

        # 1. Spritesheet Pets (e.g. BearPet, BubuPet)
        if asset.type == AssetType.SPRITESHEET:
            frames, fps, _loop, _ = load_spritesheet_frames(p, meta, "idle")
            if frames:
                self._idle_frames = frames
                self._idle_fps = max(1, int(fps or 8))
            bad_keys = {"idle", "fall", "land", "drag", "failed", "whip-hit"}
            self._available_actions = [k for k in anims.keys() if k not in bad_keys]

        # 2. Frame Animation Pets (e.g. NuonuoPet, XiaobaPet, JiyiPet, PopoPet)
        elif asset.type == AssetType.FRAME_ANIMATION:
            idle_def = anims.get("idle", {}) if isinstance(anims, dict) else {}
            folder_name = idle_def.get("folder", ".") if isinstance(idle_def, dict) else "."
            folder = p if folder_name in {"", "."} else p / folder_name
            frame_paths = frame_paths_for_folder(folder)
            if not frame_paths:
                frame_paths = frame_paths_for_folder(p)
            if frame_paths:
                self._idle_frames = [QPixmap(str(fp)) for fp in frame_paths if not QPixmap(str(fp)).isNull()]
                self._idle_fps = int(idle_def.get("fps", meta.get("fps", 12))) if isinstance(idle_def, dict) else 12
            bad_keys = {"idle", "drag", "failed", "fall", "land", "whip-hit"}
            self._available_actions = [k for k in anims.keys() if k not in bad_keys]

        # 3. GIF Pets
        elif asset.type == AssetType.GIF or str(asset.path).lower().endswith(".gif"):
            self._movie = QMovie(str(asset.path))
            self._movie.frameChanged.connect(self._on_movie_frame)
            self._movie.start()
            self.update()
            return

        # 4. Fallback: single image or preview
        if not self._idle_frames:
            preview_path = asset.preview_path or asset.path
            pix = QPixmap(str(preview_path))
            if not pix.isNull():
                self._idle_frames = [pix]
                self._idle_fps = 1

        if self._idle_frames:
            self._active_frames = list(self._idle_frames)
            self._active_fps = self._idle_fps
            self._frame_index = 0
            self._pet_pixmap = self._active_frames[0]
            self._is_action_active = False

            interval = max(16, int(1000 / max(1, self._active_fps)))
            self._frame_timer.start(interval)

            if self._available_actions:
                self._schedule_next_random_action()
        else:
            self._pet_pixmap = QPixmap()

        self.update()

    def _on_movie_frame(self, _frame_number):
        if self._movie is not None:
            self._pet_pixmap = self._movie.currentPixmap()
            self.update()

    def _advance_frame(self):
        if not self._active_frames:
            return

        next_idx = self._frame_index + 1
        if next_idx >= len(self._active_frames):
            if self._is_action_active:
                self._action_loop_count += 1
                if self._action_loop_count >= self._max_action_loops:
                    self._return_to_idle()
                    return
            next_idx = 0

        self._frame_index = next_idx
        self._pet_pixmap = self._active_frames[self._frame_index]
        self.update()

    def _play_action(self, action_name: str, loops: int = 1):
        if not self._current_asset:
            return

        p = Path(self._current_asset.path)
        meta = self._current_asset.metadata or {}
        anims = meta.get("animations", {}) if isinstance(meta.get("animations"), dict) else {}

        frames = []
        fps = 8
        if self._current_asset.type == AssetType.SPRITESHEET:
            f, fps, _, _ = load_spritesheet_frames(p, meta, action_name)
            frames = f
        elif self._current_asset.type == AssetType.FRAME_ANIMATION:
            act_def = anims.get(action_name, {})
            folder_name = act_def.get("folder", ".") if isinstance(act_def, dict) else "."
            folder = p if folder_name in {"", "."} else p / folder_name
            paths = frame_paths_for_folder(folder)
            if paths:
                frames = [QPixmap(str(fp)) for fp in paths if not QPixmap(str(fp)).isNull()]
                fps = int(act_def.get("fps", meta.get("fps", 12))) if isinstance(act_def, dict) else 12

        if frames:
            self._active_frames = frames
            self._active_fps = fps or 8
            self._frame_index = 0
            self._is_action_active = True
            self._action_loop_count = 0
            self._max_action_loops = max(1, loops)
            self._pet_pixmap = frames[0]
            interval = max(16, int(1000 / max(1, self._active_fps)))
            self._frame_timer.setInterval(interval)
            self.update()

    def _return_to_idle(self):
        if not self._idle_frames:
            return
        self._active_frames = list(self._idle_frames)
        self._active_fps = self._idle_fps
        self._frame_index = 0
        self._is_action_active = False
        self._action_loop_count = 0
        self._pet_pixmap = self._active_frames[0]
        interval = max(16, int(1000 / max(1, self._active_fps)))
        self._frame_timer.setInterval(interval)
        self._schedule_next_random_action()
        self.update()

    def _schedule_next_random_action(self):
        if not self._available_actions:
            return
        interval_ms = random.randint(4500, 8500)
        self._random_action_timer.start(interval_ms)

    def _trigger_random_action(self):
        if not self._available_actions or self._is_action_active:
            self._schedule_next_random_action()
            return

        priority_keywords = [
            "waving", "jumping", "waiting", "hover", "reward", "review",
            "gesture-dance", "happy-dance", "sunny-guitar-bounce", "buddy-guitar-cheer",
            "concert-piano", "shy-paw-fidget", "shy-cheek-peek", "bashful-small-bow", "sleep"
        ]
        pool = [a for a in self._available_actions if any(kw in a for kw in priority_keywords)]
        if not pool:
            pool = self._available_actions

        action = random.choice(pool)
        self._play_action(action, loops=1 if len(self._active_frames) > 6 else 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self._locked_preview and not self._action_hint:
            self._bounce_dy = -14.0
            if not self._bounce_timer.isActive():
                self._bounce_timer.start()

            interactive_candidates = ["click", "hover", "waving", "jumping", "reward"]
            chosen = next((act for act in interactive_candidates if act in self._available_actions), None)
            if chosen:
                self._random_action_timer.stop()
                self._play_action(chosen, loops=1)
            self.update()
        super().mousePressEvent(event)

    def _step_bounce(self):
        self._bounce_dy *= 0.82
        if abs(self._bounce_dy) < 0.3:
            self._bounce_dy = 0.0
            self._bounce_timer.stop()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)
        rect = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        path = QPainterPath()
        preview_radius = 30
        path.addRoundedRect(rect, preview_radius, preview_radius)

        painter.save()
        painter.setClipPath(path)
        garden = self._locked_pixmap if self._locked_preview and not self._locked_pixmap.isNull() else self.garden_pixmap()
        if not garden.isNull():
            painter.drawPixmap(
                rect.toRect(),
                garden.scaled(rect.size().toSize(), Qt.IgnoreAspectRatio, Qt.SmoothTransformation),
            )
        elif self._locked_preview:
            draw_game_background(painter, rect, include_grass=True, muted=True)
        else:
            draw_game_background(painter, rect, include_grass=True)
        painter.restore()

        painter.setPen(QPen(QColor("#d8cec7"), 1.6))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(rect, preview_radius, preview_radius)

        if self._locked_preview:
            icon_rect = QRectF(rect.center().x() - 76, rect.center().y() - 96, 152, 152)
            draw_lock_icon(painter, icon_rect, QColor("#5f4725"))
            font = self.font()
            font.setFamily("Microsoft YaHei UI")
            font.setBold(True)
            font.setPointSize(16)
            painter.setFont(font)
            painter.setPen(QColor("#fff1cf"))
            note_rect = QRectF(rect.left() + 24, rect.bottom() - 92, rect.width() - 48, 48)
            painter.drawText(note_rect.toRect(), Qt.AlignCenter | Qt.TextWordWrap, "未解锁")
            return

        if self._action_hint:
            icon_rect = QRectF(rect.center().x() - 54, rect.top() + 58, 108, 108)
            if self._action_hint == "doubao":
                draw_rounded_cover_image(
                    painter,
                    icon_rect,
                    resource_path("assets/UiAssets/doubao-avatar.png"),
                    26,
                )
            else:
                draw_sticker_icon(
                    painter,
                    icon_rect,
                    "medals",
                    QColor("#9b7124"),
                    True,
                )
            copy_panel = QRectF(rect.left() + 24, rect.top() + 170, rect.width() - 48, 126)
            painter.setPen(QPen(QColor(221, 212, 204, 180), 1.2))
            painter.setBrush(QBrush(QColor(255, 253, 249, 224)))
            painter.drawRoundedRect(copy_panel, 22, 22)
            title_font = self.font()
            title_font.setFamily("Microsoft YaHei UI")
            title_font.setBold(True)
            title_font.setPointSize(16)
            painter.setFont(title_font)
            painter.setPen(UI_INK)
            painter.drawText(
                QRectF(rect.left() + 28, rect.top() + 184, rect.width() - 56, 34).toRect(),
                Qt.AlignCenter,
                self._action_title,
            )
            note_font = self.font()
            note_font.setFamily("Microsoft YaHei UI")
            note_font.setPointSize(10)
            painter.setFont(note_font)
            painter.setPen(UI_MUTED)
            painter.drawText(
                QRectF(rect.left() + 42, rect.top() + 226, rect.width() - 84, 58).toRect(),
                Qt.AlignHCenter | Qt.AlignTop | Qt.TextWordWrap,
                self._action_description,
            )
            return

        if self._pet_pixmap.isNull():
            return

        pet_max = QSize(max(100, int(rect.width() * 0.46)), max(100, int(rect.height() * 0.48)))
        pet = self._pet_pixmap.scaled(pet_max, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        pedestal_top_y = rect.top() + rect.height() * 0.655
        pet_x = rect.center().x() - pet.width() / 2
        pet_y = pedestal_top_y - pet.height() + 8 + self._bounce_dy

        shadow_scale = max(0.6, 1.0 + self._bounce_dy * 0.02)
        shadow = QRectF(
            rect.center().x() - pet.width() * 0.35 * shadow_scale,
            pedestal_top_y - 6,
            pet.width() * 0.70 * shadow_scale,
            14 * shadow_scale,
        )
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(36, 68, 56, 45)))
        painter.drawEllipse(shadow)
        painter.drawPixmap(QRectF(pet_x, pet_y, pet.width(), pet.height()).toRect(), pet)


class GoldenEggWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._egg_pixmap = QPixmap(str(resource_path("assets/UiAssets/blue-logo-egg.png")))
        self.setMinimumSize(150, 150)
        self.setMaximumSize(210, 200)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)

        bounds = QRectF(self.rect()).adjusted(18, 10, -18, -10)
        shadow = QRectF(bounds.left() + 34, bounds.bottom() - 24, bounds.width() - 68, 18)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(95, 71, 37, 48)))
        painter.drawEllipse(shadow)

        cx = bounds.center().x()
        top = bounds.top() + 8
        bottom = bounds.bottom() - 20
        egg = QPainterPath()
        egg.moveTo(cx, top)
        egg.cubicTo(bounds.left() + 20, top + 22, bounds.left() + 14, bottom - 54, bounds.left() + 42, bottom - 18)
        egg.cubicTo(bounds.left() + 66, bottom + 10, bounds.right() - 66, bottom + 10, bounds.right() - 42, bottom - 18)
        egg.cubicTo(bounds.right() - 14, bottom - 54, bounds.right() - 20, top + 22, cx, top)

        fill = QLinearGradient(bounds.topLeft(), bounds.bottomRight())
        fill.setColorAt(0.0, QColor("#fff3a6"))
        fill.setColorAt(0.48, QColor("#ffd34e"))
        fill.setColorAt(1.0, QColor("#d59a2e"))
        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(QColor("#5f4725"), 4))
        painter.drawPath(egg)

        glow = QPainterPath()
        glow.moveTo(cx - 42, top + 34)
        glow.cubicTo(cx - 68, top + 60, cx - 62, top + 116, cx - 32, top + 128)
        painter.setPen(QPen(QColor(255, 255, 255, 140), 10, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawPath(glow)

        crack_pen = QPen(QColor("#8a5b18"), 2.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(crack_pen)
        painter.drawLine(QPointF(cx - 18, bottom - 70), QPointF(cx - 4, bottom - 58))
        painter.drawLine(QPointF(cx - 4, bottom - 58), QPointF(cx - 15, bottom - 44))
        painter.drawLine(QPointF(cx + 20, top + 84), QPointF(cx + 36, top + 98))


class SoftCalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.setHorizontalHeaderFormat(QCalendarWidget.SingleLetterDayNames)
        self.setGridVisible(False)
        self.setNavigationBarVisible(False)
        self.setStyleSheet(
            """
            QCalendarWidget {
                background-color: transparent;
                border: 0;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: transparent;
            }
            QCalendarWidget QAbstractItemView {
                background-color: transparent;
                alternate-background-color: transparent;
                selection-background-color: transparent;
                selection-color: #1557b0;
                outline: 0;
                border: 0;
            }
            QCalendarWidget QToolButton {
                background: transparent;
                border: 0;
                color: #203247;
            }
            QCalendarWidget QSpinBox {
                background: transparent;
                border: 0;
            }
            """
        )

    def paintCell(self, painter, rect, date):
        painter.save()
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)
        weekday = date.dayOfWeek()
        selected = self.selectedDate() == date
        today = date == self.selectedDate()

        if selected:
            side = min(rect.width(), rect.height(), 44)
            selected_rect = QRectF(
                rect.center().x() - side / 2,
                rect.center().y() - side / 2,
                side,
                side,
            )
            painter.setPen(QPen(QColor(83, 146, 215, 42), 1))
            painter.setBrush(QBrush(QColor(42, 125, 224, 58)))
            painter.drawRoundedRect(selected_rect, side / 2, side / 2)

        if date.month() != self.monthShown():
            text_color = QColor(148, 163, 184)
        elif weekday >= 6:
            text_color = QColor(220, 38, 38)
        else:
            text_color = QColor(32, 50, 71)
        if selected:
            text_color = QColor(21, 87, 176)

        painter.setPen(text_color)
        painter.drawText(rect.adjusted(0, 0, 0, -2), Qt.AlignCenter, str(date.day()))
        painter.restore()


class SidebarPages:
    def __init__(self, nav_layout: QVBoxLayout, page_stack: QStackedWidget):
        self.nav_layout = nav_layout
        self.page_stack = page_stack
        self.currentChanged = page_stack.currentChanged
        self.buttons = []
        self._syncing = False
        self.page_stack.currentChanged.connect(self._on_stack_changed)

    def addTab(self, widget, label, icon_key=None):
        index = self.page_stack.addWidget(widget)
        button = RailNavButton(icon_key or "pet", label)
        button.clicked.connect(lambda _checked=False, page_index=index: self.setCurrentIndex(page_index))
        self.nav_layout.addWidget(button, 0, Qt.AlignHCenter)
        self.buttons.append(button)
        if self.page_stack.currentIndex() < 0 or len(self.buttons) == 1:
            self.setCurrentIndex(index)
        return index

    def setCurrentIndex(self, index):
        if index < 0 or index >= self.page_stack.count():
            return
        if self.page_stack.currentIndex() == index and self.button_checked_index() == index:
            return
        self._syncing = True
        try:
            self.page_stack.setCurrentIndex(index)
            self.sync_buttons(index)
        finally:
            self._syncing = False

    def currentIndex(self):
        return self.page_stack.currentIndex()

    def widget(self, index):
        return self.page_stack.widget(index)

    def count(self):
        return self.page_stack.count()

    def _on_stack_changed(self, index):
        if self._syncing or index < 0:
            return
        self._syncing = True
        try:
            self.sync_buttons(index)
        finally:
            self._syncing = False

    def button_checked_index(self):
        for index, button in enumerate(self.buttons):
            if button.isChecked():
                return index
        return -1

    def sync_buttons(self, active_index):
        for index, button in enumerate(self.buttons):
            button.setChecked(index == active_index)

    def setLabel(self, index, label):
        if 0 <= index < len(self.buttons):
            self.buttons[index].set_nav_label(label)

ASSET_TYPE_LABELS = {
    AssetType.GIF: "GIF 动画",
    AssetType.VIDEO: "视频（保留声音）",
    AssetType.STATIC_IMAGE: "静态图片",
    AssetType.FRAME_ANIMATION: "帧动画",
    AssetType.SPRITE_STRIP: "序列图",
    AssetType.SPRITESHEET: "精灵表",
    AssetType.COMPOSITE_UI: "组合界面/HUD",
    AssetType.UNKNOWN: "未知类型",
}


UI_TEXT = {
    "zh": {
        "nav_subtitle": "桌宠 / 工具 / 勋章 / 日程 / 设置",
        "header_subtitle": "桌宠、工具、勋章、日程和设置收成五个入口；角色兑换放进角色库卡片。",
        "language": "English",
        "current_version": "当前版本 v{version}",
        "manifest_configured": "更新清单：已配置",
        "manifest_unconfigured": "更新清单：未配置",
        "manifest_unchecked": "更新清单：未检查",
        "manifest_read": "更新清单：已读取",
        "check_updates": "检查更新",
        "open_site": "打开官网",
        "overview_tab": "桌宠",
        "pets_tab": "素材",
        "running_tab": "运行",
        "updates_tab": "设置",
        "search_tab": "工具",
        "medals_tab": "勋章",
        "schedule_tab": "日程",
        "debug_tab": "调试",
        "inspector_tab": "检查器",
        "overview_title": "桌宠",
        "overview_subtitle": "默认进入这里：桌面总控、当前主宠物、素材库和参数调节都在这一页。",
        "pet_library_group": "选择宠物",
        "pet_preview_group": "宠物展示",
        "pet_preview_empty_title": "暂未选中宠物",
        "pet_preview_empty_note": "在左侧选择一个宠物后，右侧会显示大预览和主要操作。",
        "pet_selected_pack": "素材包：{pack}",
        "pet_selected_path": "路径：{path}",
        "pet_preview_ready": "已就绪",
        "pet_preview_running": "已在桌面上",
        "pet_preview_idle": "尚未添加",
        "pet_open_config": "配置素材",
        "pet_import_hint": "导入或更换素材目录",
        "pet_desktop_group": "桌面状态",
        "pet_desktop_empty": "还没有正在运行的桌宠。右侧添加后，这里会显示当前桌面宠物列表。",
        "pet_current_running": "当前桌面",
        "pet_actions_group": "主要操作",
        "pet_preview_size": "预览",
        "pet_preview_type": "类型：{type}",
        "running_metric": "正在运行",
        "running_metric_note": "桌面上的宠物数量",
        "schedule_metric": "今日提醒",
        "schedule_metric_note": "备忘录和循环提醒",
        "asset_pack_metric": "素材包",
        "asset_pack_note": "assets 目录中的包",
        "behavior_pack_metric": "行为包",
        "behavior_pack_note": "behavior_packs",
        "client_version_metric": "客户端版本",
        "client_version_note": "自动更新本地版本",
        "update_manifest_metric": "更新清单",
        "manifest_address": "manifest 地址",
        "warnings_metric": "最近告警",
        "warnings_note": "warning / error",
        "quick_actions": "快捷操作",
        "show_all": "全部显示",
        "hide_all": "全部隐藏",
        "center_all": "全部居中",
        "disable_click": "取消点穿",
        "updates_title": "设置",
        "updates_subtitle": "按分类管理语言、开机启动、版本更新和反馈信息。",
        "settings_preferences": "偏好设置",
        "settings_language_label": "控制台语言",
        "settings_language_hint": "选择控制台显示语言。",
        "settings_system": "启动与显示",
        "settings_startup_hint": "开机后自动打开桌宠，不需要手动启动。",
        "settings_update_badge": "设置中心",
        "settings_uninstall_group": "彻底删除",
        "settings_uninstall_badge": "会删除本机文件",
        "settings_uninstall_title": "卸载 Window Pet",
        "settings_uninstall_hint": "不喜欢也没关系。确认后会退出程序，并删除当前安装文件夹、本地配置、日志和快捷方式。",
        "settings_uninstall_button": "彻底删除",
        "settings_uninstall_dev_warning": "源码运行模式下不会执行彻底删除，避免误删开发文件。请在打包后的正式软件里使用。",
        "settings_uninstall_failed": "卸载脚本启动失败，请手动删除当前文件夹：{path}",
        "feedback_title": "反馈",
        "feedback_hint": "写下你想反馈的问题或想法，我们后面接云服务器后会直接同步。",
        "feedback_placeholder": "例如：哪个小宠动作太多、哪里不好用、想要什么新功能",
        "feedback_submit": "提交反馈",
        "feedback_empty": "先写一点反馈内容。",
        "feedback_saved": "反馈已保存，谢谢。",
        "settings_release_notes": "最近更新",
        "settings_diagnostics_badge": "帮助与反馈",
        "update_config_group": "版本更新",
        "settings_version_hint": "当前安装的桌宠版本。",
        "settings_auto_update_title": "启动时自动检查",
        "settings_auto_update_hint": "打开软件几秒后静默检查一次；只有发现新版本才会提示你安装。",
        "settings_auto_update_check": "自动检查更新",
        "settings_update_check_title": "检查新版本",
        "settings_update_check_hint": "可以在软件内直接下载并安装新版本，不需要跳回官网手动下载。",
        "current_version_row": "当前版本",
        "site_url_row": "官网地址",
        "remote_version_row": "远程版本",
        "download_url_row": "下载地址",
        "status_row": "状态",
        "check_manifest": "检查更新",
        "install_updates": "软件内安装更新",
        "update_keep_data": "更新会保留登录信息、角色、反馈、设置和日志。",
        "copy_manifest": "复制 manifest",
        "copy_package": "复制下载地址",
        "search_title": "本地搜索",
        "search_subtitle": "查找电脑里的软件、文件和常用资料；也可以从这里启动桌宠小工具。",
        "search_placeholder": "输入软件名、文件名或关键词",
        "search_mode_apps": "软件",
        "search_mode_documents": "文件",
        "search_mode_all": "全部",
        "search_button": "搜索",
        "tool_group": "小功能",
        "tool_whip": "抽鞭子",
        "tools_file_search": "文件搜索",
        "tools_file_search_hint": "找软件、文件和资料",
        "tools_offwork_countdown": "下班倒计时",
        "tools_offwork_countdown_hint": "准点或倒计时欢庆跳舞",
        "tools_offwork_title": "下班狂喜倒计时 · 水豚嘟嘟音乐版",
        "tools_offwork_subtitle": "设置准点下班或时长倒计时。时间一到，默认以带音乐的水豚嘟嘟为主（或桌面上任意宠物）变大欢快起舞并伴有音乐，点击宠物即可缩回。右键任意桌宠也可随时触发！",
        "tools_offwork_start": "🚀 开启下班倒计时",
        "tools_offwork_stop": "⏹ 取消倒计时",
        "tools_offwork_test": "🎉 立即测试欢庆效果",
        "tools_offwork_mode_exact": "准点下班",
        "tools_offwork_mode_duration": "多久之后",
        "tools_offwork_exact_label": "设置下班时间",
        "tools_offwork_duration_label": "倒计时间隔",
        "tools_repeat_reminder": "提醒闹钟",
        "tools_repeat_reminder_hint": "循环提醒和到点提示",
        "tools_focus_timer": "专注计时",
        "tools_focus_timer_hint": "专注、休息、自定义",
        "tools_memo": "备忘便签",
        "tools_memo_hint": "写任务并显示在桌宠上",
        "tools_interaction": "互动道具",
        "tools_interaction_hint": "鞭子和奖励动作",
        "tools_wallpaper": "定时更换壁纸",
        "tools_wallpaper_hint": "6 点、12 点、18 点自动换壁纸",
        "tools_wallpaper_enable": "开启定时更换壁纸",
        "tools_wallpaper_title": "一天三次换上新背景",
        "tools_wallpaper_subtitle": "默认关闭。把喜欢的图片拖到卡片上，或者右键卡片更换图片。",
        "tools_wallpaper_drop_hint": "拖入图片，或右键更换",
        "tools_wallpaper_status_on": "已开启：到 06:00 / 12:00 / 18:00 会自动更换壁纸。",
        "tools_wallpaper_status_off": "默认关闭：开启后才会按时间更换壁纸。",
        "tools_wallpaper_choose": "更换壁纸图片",
        "tools_wallpaper_invalid": "请选择 png、jpg、jpeg、webp 或 bmp 图片。",
        "tools_target_pet": "作用到",
        "tools_no_pet": "请先启动一个桌宠",
        "tools_repeat_interval": "提醒间隔",
        "tools_repeat_start": "开启循环提醒",
        "tools_repeat_stop": "关闭提醒",
        "tools_repeat_status_on": "{pet}：每 {minutes} 分钟提醒一次",
        "tools_repeat_status_off": "{pet}：未开启循环提醒",
        "tools_timer_duration": "计时时长",
        "tools_timer_focus": "25 分钟专注",
        "tools_timer_break": "5 分钟休息",
        "tools_timer_start": "开始计时",
        "tools_timer_pause": "暂停计时",
        "tools_timer_resume": "开始 / 继续",
        "tools_timer_reset": "重置",
        "tools_timer_status": "{pet}：{state} · {time}",
        "tools_running": "运行中",
        "tools_paused": "未运行",
        "tools_memo_placeholder": "写下要让桌宠提醒你的事情",
        "tools_memo_save": "保存并显示",
        "tools_memo_show": "显示",
        "tools_memo_hide": "隐藏",
        "tools_memo_done": "标记完成",
        "tools_memo_clear": "清空",
        "tools_memo_status": "{pet}：备忘录{state}",
        "tools_visible": "已显示",
        "tools_hidden": "已隐藏",
        "tools_reward": "奖励动作",
        "tools_interaction_status": "{pet}：使用互动道具触发羽毛或鞭子动作",
        "tools_status_no_pet": "当前没有运行中的桌宠，请先在桌宠页添加一个。",
        "search_empty": "输入关键词后开始搜索。",
        "search_no_results": "没有找到匹配结果。可以换个关键词再试。",
        "search_status": "结果来源：{source}，共 {count} 项",
        "open_result": "打开",
        "open_parent": "定位",
        "library_title": "素材库",
        "library_subtitle": "选择素材包，把桌宠或图片动画添加到桌面。",
        "asset_pack_label": "素材包",
        "asset_root_label": "素材目录：{path}",
        "change_asset_root": "更换素材文件夹",
        "import_asset": "导入单个素材",
        "import_folder": "导入素材文件夹",
        "configure_asset": "配置素材",
        "add_to_desktop": "添加到桌面",
        "empty_library": "还没有素材。请导入素材，或把文件放进 assets 文件夹。",
        "active_title": "正在运行",
        "active_subtitle": "选择正在运行的桌宠，可以编辑、锁定或关闭。",
        "edit_selected": "编辑选中项",
        "close_selected": "关闭选中项",
        "lock_toggle": "锁定/解锁",
        "recovery_tools": "恢复工具",
        "center_all_full": "全部移到屏幕中央",
        "disable_click_full": "取消点击穿透",
        "unlock_all": "全部解锁",
        "clear_saved": "清空保存的桌宠",
        "startup": "开机自动启动",
        "pet_locked_title": "神秘角色",
        "pet_locked_note": "所有角色免费可用。",
        "pet_locked_message": "所有角色已经免费开放。",
        "reward_history": "记录",
        "reward_empty": "暂无记录。",
        "medals_title": "勋章墙",
        "medals_subtitle": "在自然使用中慢慢解锁；没有每日任务，也不会因为几天没打开而失去进度。",
        "medals_summary": "已发现 {unlocked} / {total} 枚",
        "medals_note": "勋章只用于收藏和装扮，不会锁住角色功能。",
        "medals_hide": "暂时隐藏",
        "medals_hidden_title": "勋章墙已暂时隐藏",
        "medals_hidden_note": "它不会打扰日常使用，想看时再回来就好。",
        "medals_restore": "重新显示",
        "schedule_title": "日程",
        "schedule_subtitle": "查看今天的备忘录、计时器和循环提醒。",
        "schedule_calendar": "小日历",
        "schedule_summary": "当前提醒",
        "schedule_running_badge": "{count} 个桌宠",
        "schedule_empty_badge": "未启动桌宠",
        "schedule_today_badge": "今天 {date}",
        "schedule_actions": "快捷操作",
        "schedule_open_calendar": "打开桌宠日历",
        "schedule_edit_memo": "编辑备忘录",
        "schedule_repeat": "设置循环提醒",
        "schedule_empty": "暂无正在运行的桌宠。启动桌宠后，这里会显示备忘录、计时器和循环提醒。",
        "debug_title": "帮助与反馈",
        "debug_subtitle": "遇到问题时，可以复制反馈信息发给我们排查。",
        "recent_warnings": "最近状态",
        "open_logs": "查看问题记录",
        "copy_diagnostics": "复制反馈信息",
        "refresh": "刷新",
        "editor_placeholder": "双击一个桌宠即可编辑",
        "selected_asset": "已选择素材",
        "scale_label": "大小：{value}%",
        "opacity_label": "透明度：{value}%",
        "speed_label": "速度：{value}%",
        "appearance": "外观调整",
        "always_on_top": "保持在最前面",
        "click_through": "点击穿透",
        "lock_position": "锁定位置",
        "reload_asset": "重新加载素材",
        "behavior": "行为",
        "spritesheet": "精灵表控制",
        "composite": "组合层数值",
        "animation": "动画",
        "type_prefix": "类型：{type}",
        "configured": "已配置",
        "not_configured": "未配置",
        "no_warnings": "暂无 warning/error",
        "active_instances": "当前桌面上的宠物实例",
        "not_checked": "未检查",
        "missing_version": "缺少 version",
        "missing_package": "缺少 package_url",
        "no_sha": "未提供 sha256",
        "manifest_loaded": "已读取 manifest",
        "no_release_notes": "manifest 中没有 release_notes。",
        "update_hint": "点击检查更新，确认是否有新版本。",
        "waiting_manifest": "还没有检查更新。",
        "reading_manifest": "正在检查更新...",
        "diagnostics_version": "版本：{version}",
        "diagnostics_config": "配置文件：{path}",
        "diagnostics_assets": "素材目录：{path}",
        "diagnostics_log": "日志文件：{path}",
        "diagnostics_count": "正在运行的桌宠数量：{count}",
        "diagnostics_empty": "本次运行还没有记录警告或错误。",
        "locked": "已锁定",
        "unlocked": "未锁定",
    },
    "en": {
        "nav_subtitle": "Pet / Tools / Medals / Schedule / Settings",
        "header_subtitle": "Pet, tools, medals, schedule, and settings are the five top-level entries; character redemption lives in the library card.",
        "language": "中文",
        "current_version": "Current v{version}",
        "manifest_configured": "Manifest: configured",
        "manifest_unconfigured": "Manifest: not configured",
        "manifest_unchecked": "Manifest: unchecked",
        "manifest_read": "Manifest: loaded",
        "check_updates": "Check Updates",
        "open_site": "Open Site",
        "overview_tab": "Pet",
        "pets_tab": "Assets",
        "running_tab": "Running",
        "updates_tab": "Settings",
        "search_tab": "Tools",
        "medals_tab": "Medals",
        "schedule_tab": "Schedule",
        "debug_tab": "Debug",
        "inspector_tab": "Inspector",
        "overview_title": "Pet",
        "overview_subtitle": "Default workspace for the desktop pet, active instances, assets, and tuning controls.",
        "pet_library_group": "Choose Pet",
        "pet_preview_group": "Pet Preview",
        "pet_preview_empty_title": "No pet selected",
        "pet_preview_empty_note": "Select a pet on the left to show a larger preview and the main actions here.",
        "pet_selected_pack": "Pack: {pack}",
        "pet_selected_path": "Path: {path}",
        "pet_preview_ready": "Ready",
        "pet_preview_running": "Already on desktop",
        "pet_preview_idle": "Not on desktop",
        "pet_open_config": "Configure Asset",
        "pet_import_hint": "Import or change asset folder",
        "pet_desktop_group": "Desktop Status",
        "pet_desktop_empty": "No running desktop pet yet. After you add one on the right, it will appear here.",
        "pet_current_running": "Current desktop pets",
        "pet_actions_group": "Main Actions",
        "pet_preview_size": "Preview",
        "pet_preview_type": "Type: {type}",
        "running_metric": "Running",
        "running_metric_note": "Pets on the desktop",
        "schedule_metric": "Reminders",
        "schedule_metric_note": "Memo and repeating reminders",
        "asset_pack_metric": "Asset Packs",
        "asset_pack_note": "Packages in assets",
        "behavior_pack_metric": "Behavior Packs",
        "behavior_pack_note": "behavior_packs",
        "client_version_metric": "Client Version",
        "client_version_note": "Local updater version",
        "update_manifest_metric": "Update Manifest",
        "manifest_address": "manifest URL",
        "warnings_metric": "Recent Warnings",
        "warnings_note": "warning / error",
        "quick_actions": "Quick Actions",
        "show_all": "Show All",
        "hide_all": "Hide All",
        "center_all": "Center All",
        "disable_click": "Disable Pass-through",
        "updates_title": "Settings",
        "updates_subtitle": "Manage language, startup, updates, and support in clear sections.",
        "settings_preferences": "Preferences",
        "settings_language_label": "Console Language",
        "settings_language_hint": "Chinese is the default. Switch to English when needed.",
        "settings_system": "Startup & Display",
        "settings_startup_hint": "Open the pet automatically after Windows starts.",
        "settings_update_badge": "Settings",
        "settings_uninstall_group": "Remove Completely",
        "settings_uninstall_badge": "Deletes local files",
        "settings_uninstall_title": "Uninstall Window Pet",
        "settings_uninstall_hint": "If it is not for you, that is okay. This exits the app and removes the current install folder, local config, logs, and shortcuts.",
        "settings_uninstall_button": "Remove Completely",
        "settings_uninstall_dev_warning": "Complete removal is disabled in source mode to avoid deleting development files. Use it from the packaged app.",
        "settings_uninstall_failed": "Unable to start uninstall script. Please remove this folder manually: {path}",
        "feedback_title": "Feedback",
        "feedback_hint": "Leave issues or ideas here. This can sync to the server later.",
        "feedback_placeholder": "Example: too many actions, awkward UI, or a feature idea",
        "feedback_submit": "Submit",
        "feedback_empty": "Write feedback first.",
        "feedback_saved": "Feedback saved.",
        "settings_release_notes": "Recent Updates",
        "settings_diagnostics_badge": "Support",
        "update_config_group": "App Updates",
        "settings_version_hint": "The desktop pet version currently installed.",
        "settings_auto_update_title": "Auto Check on Launch",
        "settings_auto_update_hint": "The app checks quietly a few seconds after launch and only prompts when a newer version exists.",
        "settings_auto_update_check": "Auto check updates",
        "settings_update_check_title": "Check for Updates",
        "settings_update_check_hint": "Download and install the new version inside the app instead of returning to the website.",
        "current_version_row": "Current Version",
        "site_url_row": "Site URL",
        "remote_version_row": "Remote Version",
        "download_url_row": "Download URL",
        "status_row": "Status",
        "check_manifest": "Check Updates",
        "install_updates": "Install in App",
        "update_keep_data": "Updates keep login, pets, feedback, settings, and logs.",
        "copy_manifest": "Copy Manifest",
        "copy_package": "Copy Download URL",
        "search_title": "Local Search",
        "search_subtitle": "Find apps, files, and working documents on this PC. Launch desktop-pet tools from the same page.",
        "search_placeholder": "Search apps, files, or keywords",
        "search_mode_apps": "Apps",
        "search_mode_documents": "Files",
        "search_mode_all": "All",
        "search_button": "Search",
        "tool_group": "Small Tools",
        "tool_whip": "Whip",
        "tools_file_search": "File Search",
        "tools_file_search_hint": "Find apps, files, and notes",
        "tools_offwork_countdown": "Off-Work Countdown",
        "tools_offwork_countdown_hint": "Clock-out dance celebration",
        "tools_offwork_title": "Off-Work Countdown · Dudu Music Capybara",
        "tools_offwork_subtitle": "Set clock-out time or countdown. By default Dudu the music Capybara (or any desktop pet) scales up to dance with music! Click to restore, or right-click any pet anytime.",
        "tools_offwork_start": "🚀 Start Countdown",
        "tools_offwork_stop": "⏹ Cancel",
        "tools_offwork_test": "🎉 Test Celebration",
        "tools_offwork_mode_exact": "Clock Out Time",
        "tools_offwork_mode_duration": "In Duration",
        "tools_offwork_exact_label": "Set Off-Work Time",
        "tools_offwork_duration_label": "Countdown Duration",
        "tools_repeat_reminder": "Reminder",
        "tools_repeat_reminder_hint": "Repeating alerts",
        "tools_focus_timer": "Focus Timer",
        "tools_focus_timer_hint": "Focus, break, custom",
        "tools_memo": "Memo",
        "tools_memo_hint": "Pin a task to the pet",
        "tools_interaction": "Interaction",
        "tools_interaction_hint": "Whip and reward actions",
        "tools_wallpaper": "Scheduled Wallpaper",
        "tools_wallpaper_hint": "Change at 06:00, 12:00, and 18:00",
        "tools_wallpaper_enable": "Enable scheduled wallpaper",
        "tools_wallpaper_title": "Three fresh backgrounds each day",
        "tools_wallpaper_subtitle": "Off by default. Drop an image onto a card or right-click a card to replace it.",
        "tools_wallpaper_drop_hint": "Drop an image or right-click",
        "tools_wallpaper_status_on": "Enabled: wallpaper changes at 06:00 / 12:00 / 18:00.",
        "tools_wallpaper_status_off": "Off by default. Enable it before the pet changes wallpaper.",
        "tools_wallpaper_choose": "Choose wallpaper image",
        "tools_wallpaper_invalid": "Choose a png, jpg, jpeg, webp, or bmp image.",
        "tools_target_pet": "Target",
        "tools_no_pet": "Start a pet first",
        "tools_repeat_interval": "Reminder interval",
        "tools_repeat_start": "Start Repeat",
        "tools_repeat_stop": "Stop Reminder",
        "tools_repeat_status_on": "{pet}: every {minutes} minutes",
        "tools_repeat_status_off": "{pet}: repeat reminder off",
        "tools_timer_duration": "Duration",
        "tools_timer_focus": "25 min Focus",
        "tools_timer_break": "5 min Break",
        "tools_timer_start": "Start Timer",
        "tools_timer_pause": "Pause Timer",
        "tools_timer_resume": "Start / Resume",
        "tools_timer_reset": "Reset",
        "tools_timer_status": "{pet}: {state} · {time}",
        "tools_running": "Running",
        "tools_paused": "Idle",
        "tools_memo_placeholder": "Write something for the pet to remind you about",
        "tools_memo_save": "Save and Show",
        "tools_memo_show": "Show",
        "tools_memo_hide": "Hide",
        "tools_memo_done": "Mark Done",
        "tools_memo_clear": "Clear",
        "tools_memo_status": "{pet}: memo {state}",
        "tools_visible": "visible",
        "tools_hidden": "hidden",
        "tools_reward": "Reward",
        "tools_interaction_status": "{pet}: use the interaction tools to trigger feather or whip actions",
        "tools_status_no_pet": "No running pet. Add one from the Pet page first.",
        "search_empty": "Enter a keyword to start searching.",
        "search_no_results": "No matching results. Try another keyword.",
        "search_status": "Source: {source}; {count} results",
        "open_result": "Open",
        "open_parent": "Show",
        "library_title": "Asset Library",
        "library_subtitle": "Choose an asset pack and add pets or image animations to the desktop.",
        "asset_pack_label": "Asset Pack",
        "asset_root_label": "Asset folder: {path}",
        "change_asset_root": "Change Asset Folder",
        "import_asset": "Import Asset",
        "import_folder": "Import Folder",
        "configure_asset": "Configure Asset",
        "add_to_desktop": "Add to Desktop",
        "empty_library": "No assets yet. Import an asset or place files in the assets folder.",
        "active_title": "Running Pets",
        "active_subtitle": "Select a running pet to edit, lock, or close it.",
        "edit_selected": "Edit Selected",
        "close_selected": "Close Selected",
        "lock_toggle": "Lock / Unlock",
        "recovery_tools": "Recovery Tools",
        "center_all_full": "Move All to Center",
        "disable_click_full": "Disable Click-through",
        "unlock_all": "Unlock All",
        "clear_saved": "Clear Saved Session",
        "startup": "Start with Windows",
        "pet_locked_title": "Mystery Pet",
        "pet_locked_note": "All pets are free.",
        "pet_locked_message": "All pets are free.",
        "reward_history": "History",
        "reward_empty": "No history yet.",
        "medals_title": "Medal Wall",
        "medals_subtitle": "Unlock medals naturally. There are no daily chores and no lost progress after a break.",
        "medals_summary": "{unlocked} / {total} discovered",
        "medals_note": "Medals are optional collectibles and never lock core pet features.",
        "medals_hide": "Hide for now",
        "medals_hidden_title": "Medal wall is hidden",
        "medals_hidden_note": "It will not interrupt daily use. Return whenever you want.",
        "medals_restore": "Show again",
        "schedule_title": "Schedule",
        "schedule_subtitle": "Review today's memo, timers, and repeating reminders.",
        "schedule_calendar": "Calendar",
        "schedule_summary": "Current Reminders",
        "schedule_running_badge": "{count} pets",
        "schedule_empty_badge": "No pet running",
        "schedule_today_badge": "Today {date}",
        "schedule_actions": "Quick Actions",
        "schedule_open_calendar": "Open Pet Calendar",
        "schedule_edit_memo": "Edit Memo",
        "schedule_repeat": "Repeat Reminder",
        "schedule_empty": "No running pet yet. Start a pet to show memo, timers, and repeating reminders here.",
        "debug_title": "Help & Support",
        "debug_subtitle": "If something feels wrong, copy support info and send it to us.",
        "recent_warnings": "Recent Status",
        "open_logs": "View Issue Log",
        "copy_diagnostics": "Copy Support Info",
        "refresh": "Refresh",
        "editor_placeholder": "Double-click a pet to edit it",
        "selected_asset": "Selected Asset",
        "scale_label": "Size: {value}%",
        "opacity_label": "Opacity: {value}%",
        "speed_label": "Speed: {value}%",
        "appearance": "Appearance",
        "always_on_top": "Always on Top",
        "click_through": "Click-through",
        "lock_position": "Lock Position",
        "reload_asset": "Reload Asset",
        "behavior": "Behavior",
        "spritesheet": "Spritesheet",
        "composite": "Composite Layers",
        "animation": "Animation",
        "type_prefix": "Type: {type}",
        "configured": "Configured",
        "not_configured": "Not configured",
        "no_warnings": "No warnings/errors",
        "active_instances": "Current desktop pet instances",
        "not_checked": "Not checked",
        "missing_version": "Missing version",
        "missing_package": "Missing package_url",
        "no_sha": "No sha256",
        "manifest_loaded": "Manifest loaded",
        "no_release_notes": "No release_notes in manifest.",
        "update_hint": "Check for a newer version when you need it.",
        "waiting_manifest": "No update check yet.",
        "reading_manifest": "Checking for updates...",
        "diagnostics_version": "Version: {version}",
        "diagnostics_config": "Config file: {path}",
        "diagnostics_assets": "Asset folder: {path}",
        "diagnostics_log": "Log file: {path}",
        "diagnostics_count": "Running pet count: {count}",
        "diagnostics_empty": "No warnings or errors recorded in this run.",
        "locked": "Locked",
        "unlocked": "Unlocked",
    },
}


class ControlPanel(QWidget):
    _window_bg_pixmap = None

    def __init__(self, app_icon=None):
        super().__init__()
        self.setObjectName("ControlPanelWindow")
        PetCursorManager.apply_to_window(self)
        self.setAttribute(Qt.WA_StyledBackground, False)
        self.setAutoFillBackground(False)
        self.language = "zh"
        self.selected_window = None
        self.loading_editor = False
        self.editor_tab = None
        self.editor_tab_index = -1
        self.tray_icon = None
        self.layer_value_sliders = {}
        self.update_manifest_data = None
        self.applying_language = False
        self.unlock_state = normalize_pet_unlocks(getattr(state, "PET_UNLOCKS", None))
        state.PET_UNLOCKS = self.unlock_state
        self.activity_egg_count = self.unlock_state["egg_chances"]
        self.activity_claimed_codes = set(self.unlock_state["claimed_invite_codes"])
        self.activity_rewards = list(self.unlock_state["history"])
        self.medal_store = getattr(state, "MEDAL_STORE", None) or MedalStore()
        state.MEDAL_STORE = self.medal_store

        self.setWindowTitle(f"{APP_DISPLAY_NAME} Cockpit")
        if app_icon is not None and not app_icon.isNull():
            self.setWindowIcon(app_icon)
        self.setMinimumSize(1120, 720)
        self.resize(1160, 740)
        screen = QApplication.primaryScreen()
        if screen is not None:
            geom = screen.availableGeometry()
            self.move(
                geom.left() + max(0, (geom.width() - 1160) // 2),
                geom.top() + max(0, (geom.height() - 740) // 2),
            )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)
        layout.addWidget(self.build_shell_header())

        body = QHBoxLayout()
        body.setSpacing(16)

        nav_panel = QFrame()
        nav_panel.setObjectName("ControlPanelNavPanel")
        nav_panel.setMinimumWidth(86)
        nav_panel.setMaximumWidth(92)
        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        nav_layout.addSpacing(4)

        nav_rail = QFrame()
        nav_rail.setObjectName("ControlPanelNavRail")
        rail_layout = QVBoxLayout(nav_rail)
        rail_layout.setContentsMargins(10, 14, 10, 14)
        rail_layout.setSpacing(12)

        self.nav_title = RailBrandMark()
        self.nav_title.hide()
        self.nav_subtitle = QLabel()
        self.nav_subtitle.setObjectName("SubtleLabel")
        self.nav_subtitle.hide()
        self.login_paw_button = LoginPawButton()
        self.login_paw_button.clicked.connect(self.open_account_dialog)
        nav_layout.addWidget(self.login_paw_button, 0, Qt.AlignHCenter)
        nav_layout.addSpacing(10)
        nav_layout.addWidget(nav_rail, 0, Qt.AlignHCenter)
        nav_layout.addStretch(1)

        self.page_stack = QStackedWidget()
        self.page_stack.setObjectName("ControlPanelStack")
        self.tabs = SidebarPages(rail_layout, self.page_stack)

        body.addWidget(nav_panel)
        body.addWidget(self.page_stack, 1)
        layout.addLayout(body, 1)

        self.build_overview_tab()
        self.build_search_tab()
        self.build_medals_tab()
        self.build_schedule_tab()
        self.build_updates_tab()
        self.tabs.currentChanged.connect(lambda index: self.refresh_diagnostics())
        self.apply_language()

        self.refresh_packs()
        self.refresh_active()
        self.refresh_diagnostics()
        self.refresh_overview()
        self.refresh_updates_page()
        self.refresh_account_status()
        self.load_editor(None)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform | QPainter.TextAntialiasing)
        rect = QRectF(self.rect())
        background = QLinearGradient(rect.topLeft(), rect.bottomRight())
        background.setColorAt(0.0, QColor("#fff7f2"))
        background.setColorAt(0.38, QColor("#f7f4ff"))
        background.setColorAt(0.72, QColor("#effaf7"))
        background.setColorAt(1.0, QColor("#e8f8f5"))
        painter.fillRect(rect, QBrush(background))

        painter.setPen(Qt.NoPen)
        for center, radius, color in (
            (QPointF(rect.width() * 0.20, rect.height() * 0.05), rect.width() * 0.20, QColor(255, 220, 225, 54)),
            (QPointF(rect.width() * 0.78, rect.height() * 0.16), rect.width() * 0.16, QColor(198, 235, 228, 62)),
            (QPointF(rect.width() * 0.64, rect.height() * 0.88), rect.width() * 0.24, QColor(218, 209, 248, 46)),
        ):
            painter.setBrush(QBrush(color))
            painter.drawEllipse(center, radius, radius)

        painter.setPen(QPen(QColor(255, 255, 255, 112), 1.2))
        wave = QPainterPath()
        wave.moveTo(rect.left() - 20, rect.height() * 0.74)
        wave.cubicTo(rect.width() * 0.22, rect.height() * 0.65, rect.width() * 0.38, rect.height() * 0.83, rect.width() * 0.58, rect.height() * 0.72)
        wave.cubicTo(rect.width() * 0.76, rect.height() * 0.62, rect.width() * 0.88, rect.height() * 0.78, rect.right() + 20, rect.height() * 0.68)
        painter.drawPath(wave)
        super().paintEvent(event)

    def tr(self, key, **kwargs):
        template = UI_TEXT.get(self.language, UI_TEXT["zh"]).get(key, UI_TEXT["zh"].get(key, key))
        return template.format(**kwargs) if kwargs else template

    def toggle_language(self):
        self.language = "en" if self.language == "zh" else "zh"
        self.apply_language()
        self.refresh_packs()
        self.refresh_active()
        self.refresh_diagnostics()

    def apply_language(self):
        if not hasattr(self, "nav_subtitle"):
            return
        if self.applying_language:
            return
        self.applying_language = True
        try:
            self.nav_subtitle.setText(self.tr("nav_subtitle"))
            self.set_tab_label(getattr(self, "overview_tab_index", -1), self.tr("overview_tab"))
            self.set_tab_label(getattr(self, "pets_tab_index", -1), self.tr("pets_tab"))
            self.set_tab_label(getattr(self, "running_tab_index", -1), self.tr("running_tab"))
            self.set_tab_label(getattr(self, "updates_tab_index", -1), self.tr("updates_tab"))
            self.set_tab_label(getattr(self, "search_tab_index", -1), self.tr("search_tab"))
            self.set_tab_label(getattr(self, "medals_tab_index", -1), self.tr("medals_tab"))
            self.set_tab_label(getattr(self, "schedule_tab_index", -1), self.tr("schedule_tab"))
            self.set_tab_label(getattr(self, "debug_tab_index", -1), self.tr("debug_tab"))
            self.set_tab_label(getattr(self, "editor_tab_index", -1), self.tr("inspector_tab"))

            for attr, key in (
                ("overview_title", "overview_title"),
                ("updates_title", "updates_title"),
                ("updates_subtitle", "updates_subtitle"),
                ("feedback_title_label", "feedback_title"),
                ("feedback_hint_label", "feedback_hint"),
                ("feedback_submit_button", "feedback_submit"),
                ("settings_preferences_label", "settings_preferences"),
                ("settings_language_label", "settings_language_label"),
                ("settings_language_hint", "settings_language_hint"),
                ("settings_system_label", "settings_system"),
                ("settings_uninstall_label", "settings_uninstall_group"),
                ("settings_uninstall_badge", "settings_uninstall_badge"),
                ("settings_uninstall_title", "settings_uninstall_title"),
                ("settings_uninstall_hint", "settings_uninstall_hint"),
                ("uninstall_button", "settings_uninstall_button"),
                ("settings_startup_title", "startup"),
                ("settings_startup_hint", "settings_startup_hint"),
                ("settings_update_badge", "settings_update_badge"),
                ("settings_release_notes_label", "settings_release_notes"),
                ("settings_diagnostics_badge", "settings_diagnostics_badge"),
                ("update_info_title", "update_config_group"),
                ("settings_version_title", "current_version_row"),
                ("settings_version_hint", "settings_version_hint"),
                ("settings_auto_update_title", "settings_auto_update_title"),
                ("settings_auto_update_hint", "settings_auto_update_hint"),
                ("auto_update_check", "settings_auto_update_check"),
                ("settings_update_check_title", "settings_update_check_title"),
                ("settings_update_check_hint", "settings_update_check_hint"),
                ("update_manifest_button", "check_manifest"),
                ("update_install_button", "install_updates"),
                ("update_site_button", "open_site"),
                ("update_keep_data_label", "update_keep_data"),
                ("update_copy_manifest_button", "copy_manifest"),
                ("update_copy_package_button", "copy_package"),
                ("search_title", "search_title"),
                ("search_subtitle", "search_subtitle"),
                ("search_button", "search_button"),
                ("tool_group", "tool_group"),
                ("tool_whip_button", "tool_whip"),
                ("medals_title_label", "medals_title"),
                ("medals_subtitle_label", "medals_subtitle"),
                ("medals_note_label", "medals_note"),
                ("medals_hide_button", "medals_hide"),
                ("medals_hidden_title_label", "medals_hidden_title"),
                ("medals_hidden_note_label", "medals_hidden_note"),
                ("medals_restore_button", "medals_restore"),
                ("schedule_title", "schedule_title"),
                ("schedule_subtitle", "schedule_subtitle"),
                ("schedule_calendar_label", "schedule_calendar"),
                ("schedule_summary_label", "schedule_summary"),
                ("schedule_actions_label", "schedule_actions"),
                ("schedule_open_calendar_button", "schedule_open_calendar"),
                ("schedule_edit_memo_button", "schedule_edit_memo"),
                ("schedule_repeat_button", "schedule_repeat"),
                ("active_hide_all_button", "hide_all"),
                ("active_show_all_button", "show_all"),
                ("recovery_group", "recovery_tools"),
                ("recovery_center_all_button", "center_all_full"),
                ("recovery_disable_click_button", "disable_click_full"),
                ("recovery_unlock_all_button", "unlock_all"),
                ("recovery_show_button", "show_all"),
                ("recovery_hide_button", "hide_all"),
                ("recovery_clear_button", "clear_saved"),
                ("startup_check", "startup"),
                ("diagnostics_title", "debug_title"),
                ("diagnostics_subtitle", "debug_subtitle"),
                ("diagnostics_warnings_label", "recent_warnings"),
                ("diagnostics_open_logs_button", "open_logs"),
                ("diagnostics_copy_button", "copy_diagnostics"),
                ("diagnostics_refresh_button", "refresh"),
                ("top_check", "always_on_top"),
                ("click_check", "click_through"),
                ("lock_check", "lock_position"),
                ("reload_button", "reload_asset"),
            ):
                widget = getattr(self, attr, None)
                if widget is not None:
                    self.set_widget_text(widget, self.tr(key))

            for label, key in getattr(self, "update_row_labels", []):
                label.setText(self.tr(key))
            if hasattr(self, "search_input"):
                self.search_input.setPlaceholderText(self.tr("search_placeholder"))
            if hasattr(self, "feedback_input"):
                self.feedback_input.setPlaceholderText(self.tr("feedback_placeholder"))
            if hasattr(self, "settings_language_button"):
                self.settings_language_button.setText(self.tr("language"))
            if hasattr(self, "search_mode_combo"):
                current_mode = self.search_mode_combo.currentData()
                self.search_mode_combo.blockSignals(True)
                self.search_mode_combo.clear()
                self.search_mode_combo.addItem(self.tr("search_mode_apps"), "apps")
                self.search_mode_combo.addItem(self.tr("search_mode_documents"), "documents")
                self.search_mode_combo.addItem(self.tr("search_mode_all"), "all")
                index = self.search_mode_combo.findData(current_mode)
                self.search_mode_combo.setCurrentIndex(index if index >= 0 else 0)
                self.search_mode_combo.blockSignals(False)
            if hasattr(self, "search_status_label") and not getattr(self, "search_results", []):
                self.search_status_label.setText(self.tr("search_empty"))
            if hasattr(self, "tool_memo_text"):
                self.tool_memo_text.setPlaceholderText(self.tr("tools_memo_placeholder"))
                self.refresh_tool_target_combos()
                self.update_tool_statuses()
            self.refresh_medals_page()
            self.refresh_schedule()
            self.update_metric_titles()
            self.refresh_overview_selection()
            self.refresh_account_status()
        finally:
            self.applying_language = False

    def set_tab_label(self, index, text):
        self.tabs.setLabel(index, text)

    def set_widget_text(self, widget, text):
        if hasattr(widget, "setText"):
            widget.setText(text)
        elif hasattr(widget, "setTitle"):
            widget.setTitle(text)

    def build_shell_header(self):
        header = QFrame()
        header.setObjectName("ControlPanelHeader")
        header.setFixedHeight(0)
        header.hide()
        return header

    def metric_card(self, title_key, value, note_key):
        card = QFrame()
        card.setObjectName("MetricCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        title_label = QLabel(self.tr(title_key))
        title_label.setObjectName("MetricTitle")
        value_label = QLabel(value)
        value_label.setObjectName("MetricValue")
        note_label = QLabel(self.tr(note_key))
        note_label.setObjectName("SubtleLabel")
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(note_label)
        return card, title_label, value_label, note_label

    def update_metric_titles(self):
        for title_label, title_key, note_label, note_key in getattr(self, "metric_labels", []):
            title_label.setText(self.tr(title_key))
            note_label.setText(self.tr(note_key))

    def build_overview_tab(self):
        tab = QWidget()
        page = QVBoxLayout(tab)
        page.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        page.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        self.overview_title = QLabel()
        self.overview_title.setObjectName("SectionTitle")
        self.overview_title.hide()
        layout.addWidget(self.overview_title)

        work_row = QHBoxLayout()
        work_row.setSpacing(18)

        library_panel = QWidget()
        library_panel.setMinimumWidth(444)
        library_panel.setMaximumWidth(456)
        library_layout = QVBoxLayout(library_panel)
        library_layout.setContentsMargins(0, 0, 0, 0)
        library_layout.setSpacing(10)
        library_group_layout = QVBoxLayout()
        library_group_layout.setContentsMargins(0, 0, 0, 0)
        library_group_layout.setSpacing(8)

        self.library_list = QListWidget()
        self.library_list.setObjectName("PetLibraryList")
        self.library_list.setViewMode(QListView.IconMode)
        self.library_list.setMovement(QListView.Static)
        self.library_list.setResizeMode(QListView.Adjust)
        self.library_list.setIconSize(QSize(76, 76))
        self.library_list.setGridSize(QSize(100, 112))
        self.library_list.setSpacing(4)
        self.library_list.setUniformItemSizes(True)
        self.library_list.setItemDelegate(PetLibraryItemDelegate(self.library_list))
        self.library_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.library_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.library_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.library_list.currentItemChanged.connect(self.on_library_selection_changed)
        self.library_list.itemClicked.connect(self.switch_library_asset_to_desktop)
        self.library_list.customContextMenuRequested.connect(self.open_library_menu)

        library_group_layout.addWidget(self.library_list, 1)
        library_layout.addLayout(library_group_layout, 1)

        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(True)
        detail_scroll.setFrameShape(QFrame.NoFrame)
        detail_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        detail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        detail_panel = QWidget()
        detail_scroll.setWidget(detail_panel)
        detail_layout = QVBoxLayout(detail_panel)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(10)
        detail_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        preview_group_layout = QVBoxLayout()
        preview_group_layout.setContentsMargins(0, 0, 0, 0)
        preview_group_layout.setSpacing(10)

        self.overview_preview_media = GardenPreviewLabel()
        self.overview_preview_media.setAlignment(Qt.AlignCenter)
        self.overview_preview_media.setMinimumWidth(360)
        self.overview_preview_media.setMinimumHeight(360)
        self.overview_preview_media.setMaximumWidth(430)
        self.overview_preview_media.setMaximumHeight(380)
        self.overview_preview_media.setObjectName("PetPreviewMedia")

        preview_group_layout.addWidget(self.overview_preview_media, 0, Qt.AlignHCenter | Qt.AlignTop)

        desktop_group_layout = QVBoxLayout()
        desktop_group_layout.setContentsMargins(0, 0, 0, 0)
        desktop_group_layout.setSpacing(10)
        self.active_list = QListWidget()
        self.active_list.setIconSize(QSize(48, 48))
        self.active_list.setSpacing(6)
        self.active_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.active_list.itemDoubleClicked.connect(lambda item: self.select_active())
        self.active_list.customContextMenuRequested.connect(self.open_active_menu)

        self.active_list.hide()
        desktop_group_layout.addWidget(self.active_list)

        self.scale_label = QLabel("大小：50%")
        self.scale_slider = VibeSlider(Qt.Horizontal, unit="%", color_variant="coral")
        self.scale_slider.setRange(25, 500)
        self.scale_slider.setTickInterval(25)
        self.scale_slider.valueChanged.connect(self.editor_scale_changed)

        self.opacity_label = QLabel("透明度：100%")
        self.opacity_slider = VibeSlider(Qt.Horizontal, unit="%", color_variant="mint")
        self.opacity_slider.setRange(50, 100)
        self.opacity_slider.setTickInterval(10)
        self.opacity_slider.valueChanged.connect(self.editor_opacity_changed)

        self.speed_label = QLabel("速度：100%")
        self.speed_slider = VibeSlider(Qt.Horizontal, unit="%", color_variant="coral")
        self.speed_slider.setRange(25, 200)
        self.speed_slider.setTickInterval(25)
        self.speed_slider.valueChanged.connect(self.editor_speed_changed)

        # Companion Quick Control Card
        self.pet_control_card = QFrame()
        self.pet_control_card.setObjectName("PetControlCard")
        self.pet_control_card.setAttribute(Qt.WA_StyledBackground, True)
        self.pet_control_card.setMinimumWidth(360)
        self.pet_control_card.setMaximumWidth(430)
        pet_ctrl_layout = QVBoxLayout(self.pet_control_card)
        pet_ctrl_layout.setContentsMargins(18, 14, 18, 14)
        pet_ctrl_layout.setSpacing(10)

        meta_row = QHBoxLayout()
        self.overview_pet_name_label = QLabel("桌面伙伴")
        self.overview_pet_name_label.setObjectName("SectionTitle")
        self.overview_pet_status_badge = QLabel("待命准备中")
        self.overview_pet_status_badge.setObjectName("StatusPill")
        meta_row.addWidget(self.overview_pet_name_label)
        meta_row.addStretch()
        meta_row.addWidget(self.overview_pet_status_badge)
        pet_ctrl_layout.addLayout(meta_row)

        pet_ctrl_layout.addWidget(self.slider_row(self.scale_label, self.scale_slider))

        opt_row = QHBoxLayout()
        self.top_check = QCheckBox("保持置顶")
        self.top_check.toggled.connect(self.editor_top_changed)
        self.click_check = QCheckBox("点击穿透")
        self.lock_check = QCheckBox("锁定位置")
        self.reload_button = QPushButton("重新加载")
        self.reload_button.clicked.connect(self.reload_selected_asset)

        self.action_studio_button = QPushButton("🎨 角色动作工坊")
        self.action_studio_button.setToolTip("设计该角色的动作触发、默认待机与右键备选动作")
        self.action_studio_button.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                border: 1px solid #fed7cc;
                border-radius: 8px;
                color: #ff526c;
                font-weight: bold;
                font-size: 11px;
                padding: 4px 10px;
            }
            QPushButton:hover {
                background: #ffeff0;
            }
        """)
        self.action_studio_button.clicked.connect(lambda: self.open_character_action_studio())

        opt_row.addWidget(self.top_check)
        opt_row.addStretch()
        opt_row.addWidget(self.action_studio_button)
        pet_ctrl_layout.addLayout(opt_row)

        self.spritesheet_layout = QVBoxLayout()
        self.composite_layout = QVBoxLayout()

        preview_group_layout.addWidget(self.pet_control_card, 0, Qt.AlignHCenter | Qt.AlignTop)

        detail_layout.addLayout(preview_group_layout, 1)
        detail_layout.addLayout(desktop_group_layout)

        work_row.addWidget(library_panel, 9)
        work_row.addWidget(detail_scroll, 11)
        layout.addLayout(work_row, 1)

        self.overview_tab_index = self.tabs.addTab(tab, self.tr("overview_tab"), "pet")

    def build_updates_tab(self):
        tab = QWidget()
        page = QVBoxLayout(tab)
        page.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        page.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(4)
        self.updates_title = QLabel()
        self.updates_title.setObjectName("SectionTitle")
        self.updates_subtitle = QLabel()
        self.updates_subtitle.setObjectName("SubtleLabel")
        self.updates_subtitle.setWordWrap(True)
        title_box.addWidget(self.updates_title)
        title_box.addWidget(self.updates_subtitle)
        self.settings_update_badge = QLabel()
        self.settings_update_badge.setObjectName("StatusPill")
        header_row.addLayout(title_box, 1)
        header_row.addWidget(self.settings_update_badge, 0, Qt.AlignTop)
        layout.addLayout(header_row)

        feedback_card = QFrame()
        feedback_card.setObjectName("SettingsCard")
        feedback_layout = QVBoxLayout(feedback_card)
        feedback_layout.setContentsMargins(22, 20, 22, 20)
        feedback_layout.setSpacing(12)
        self.feedback_title_label = QLabel()
        self.feedback_title_label.setObjectName("ActivityCardTitle")
        self.feedback_hint_label = QLabel()
        self.feedback_hint_label.setObjectName("SubtleLabel")
        self.feedback_hint_label.setWordWrap(True)
        self.feedback_input = QTextEdit()
        self.feedback_input.setObjectName("SettingsNotes")
        self.feedback_input.setMinimumHeight(86)
        self.feedback_input.setMaximumHeight(128)
        self.feedback_submit_button = QPushButton()
        self.feedback_submit_button.setObjectName("ToolPrimaryButton")
        self.feedback_submit_button.clicked.connect(self.submit_feedback)
        feedback_layout.addWidget(self.feedback_title_label)
        feedback_layout.addWidget(self.feedback_hint_label)
        feedback_layout.addWidget(self.feedback_input)
        feedback_layout.addWidget(self.feedback_submit_button, 0, Qt.AlignRight)
        layout.addWidget(feedback_card)

        preferences_card = QFrame()
        preferences_card.setObjectName("SettingsCard")
        preferences_layout = QVBoxLayout(preferences_card)
        preferences_layout.setContentsMargins(22, 20, 22, 20)
        preferences_layout.setSpacing(12)
        self.settings_preferences_label = QLabel()
        self.settings_preferences_label.setObjectName("ActivityCardTitle")
        preferences_layout.addWidget(self.settings_preferences_label)

        language_row = QFrame()
        language_row.setObjectName("SettingsInfoRow")
        language_layout = QHBoxLayout(language_row)
        language_layout.setContentsMargins(14, 12, 14, 12)
        language_layout.setSpacing(12)
        language_text = QVBoxLayout()
        language_text.setContentsMargins(0, 0, 0, 0)
        language_text.setSpacing(3)
        self.settings_language_label = QLabel()
        self.settings_language_label.setObjectName("SearchMeta")
        self.settings_language_hint = QLabel()
        self.settings_language_hint.setObjectName("SubtleLabel")
        self.settings_language_hint.setWordWrap(True)
        language_text.addWidget(self.settings_language_label)
        language_text.addWidget(self.settings_language_hint)
        self.settings_language_button = QPushButton()
        self.settings_language_button.clicked.connect(self.toggle_language)
        language_layout.addLayout(language_text, 1)
        language_layout.addWidget(self.settings_language_button)
        preferences_layout.addWidget(language_row)
        layout.addWidget(preferences_card)

        system_card = QFrame()
        system_card.setObjectName("SettingsCard")
        system_card_layout = QVBoxLayout(system_card)
        system_card_layout.setContentsMargins(22, 20, 22, 20)
        system_card_layout.setSpacing(12)
        self.settings_system_label = QLabel()
        self.settings_system_label.setObjectName("ActivityCardTitle")
        system_card_layout.addWidget(self.settings_system_label)
        system_row = QFrame()
        system_row.setObjectName("SettingsInfoRow")
        system_layout = QHBoxLayout(system_row)
        system_layout.setContentsMargins(14, 12, 14, 12)
        system_layout.setSpacing(12)
        startup_text = QVBoxLayout()
        startup_text.setContentsMargins(0, 0, 0, 0)
        startup_text.setSpacing(3)
        self.settings_startup_title = QLabel(self.tr("startup"))
        self.settings_startup_title.setObjectName("SearchMeta")
        self.settings_startup_hint = QLabel(self.tr("settings_startup_hint"))
        self.settings_startup_hint.setObjectName("SubtleLabel")
        self.settings_startup_hint.setWordWrap(True)
        startup_text.addWidget(self.settings_startup_title)
        startup_text.addWidget(self.settings_startup_hint)
        self.startup_check = QCheckBox("开机自动启动")
        self.startup_check.setEnabled(False)
        if hasattr(self.startup_check, "setVisible"):
            import sys

            self.startup_check.setVisible(sys.platform == "win32")
            if sys.platform == "win32":
                self.startup_check.setEnabled(True)
                self.startup_check.setChecked(startup_enabled())
                self.startup_check.toggled.connect(set_startup_enabled)
        system_layout.addLayout(startup_text, 1)
        system_layout.addWidget(self.startup_check)
        system_card_layout.addWidget(system_row)
        layout.addWidget(system_card)

        self.update_info_group = QFrame()
        self.update_info_group.setObjectName("SettingsCard")
        info_layout = QVBoxLayout(self.update_info_group)
        info_layout.setContentsMargins(22, 20, 22, 20)
        info_layout.setSpacing(12)
        update_header = QHBoxLayout()
        update_header.setSpacing(10)
        self.update_info_title = QLabel(self.tr("update_config_group"))
        self.update_info_title.setObjectName("ActivityCardTitle")
        self.update_status_label = QLabel()
        self.update_status_label.setObjectName("ActivityBadge")
        self.update_status_label.setWordWrap(True)
        update_header.addWidget(self.update_info_title)
        update_header.addStretch(1)
        update_header.addWidget(self.update_status_label)
        info_layout.addLayout(update_header)

        self.update_current_version_label = QLabel()
        self.update_site_url_label = QLabel()
        self.update_manifest_url_label = QLabel()
        self.update_remote_version_label = QLabel()
        self.update_package_url_label = QLabel()
        self.update_sha256_label = QLabel()
        for label in (
            self.update_current_version_label,
            self.update_site_url_label,
            self.update_manifest_url_label,
            self.update_remote_version_label,
            self.update_package_url_label,
            self.update_sha256_label,
        ):
            label.setObjectName("SettingsValue")
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            label.setWordWrap(True)

        self.update_row_labels = []
        version_row = QFrame()
        version_row.setObjectName("SettingsInfoRow")
        version_layout = QHBoxLayout(version_row)
        version_layout.setContentsMargins(14, 12, 14, 12)
        version_layout.setSpacing(12)
        version_text = QVBoxLayout()
        version_text.setContentsMargins(0, 0, 0, 0)
        version_text.setSpacing(3)
        self.settings_version_title = QLabel(self.tr("current_version_row"))
        self.settings_version_title.setObjectName("SearchMeta")
        self.settings_version_hint = QLabel(self.tr("settings_version_hint"))
        self.settings_version_hint.setObjectName("SubtleLabel")
        self.settings_version_hint.setWordWrap(True)
        version_text.addWidget(self.settings_version_title)
        version_text.addWidget(self.settings_version_hint)
        version_layout.addLayout(version_text, 1)
        version_layout.addWidget(self.update_current_version_label)
        info_layout.addWidget(version_row)

        auto_update_row = QFrame()
        auto_update_row.setObjectName("SettingsInfoRow")
        auto_update_layout = QHBoxLayout(auto_update_row)
        auto_update_layout.setContentsMargins(14, 12, 14, 12)
        auto_update_layout.setSpacing(12)
        auto_update_text = QVBoxLayout()
        auto_update_text.setContentsMargins(0, 0, 0, 0)
        auto_update_text.setSpacing(3)
        self.settings_auto_update_title = QLabel(self.tr("settings_auto_update_title"))
        self.settings_auto_update_title.setObjectName("SearchMeta")
        self.settings_auto_update_hint = QLabel(self.tr("settings_auto_update_hint"))
        self.settings_auto_update_hint.setObjectName("SubtleLabel")
        self.settings_auto_update_hint.setWordWrap(True)
        auto_update_text.addWidget(self.settings_auto_update_title)
        auto_update_text.addWidget(self.settings_auto_update_hint)
        self.auto_update_check = QCheckBox(self.tr("settings_auto_update_check"))
        self.auto_update_check.setChecked(auto_update_check_enabled())
        self.auto_update_check.toggled.connect(set_auto_update_check_enabled)
        auto_update_layout.addLayout(auto_update_text, 1)
        auto_update_layout.addWidget(self.auto_update_check)
        info_layout.addWidget(auto_update_row)

        update_row = QFrame()
        update_row.setObjectName("SettingsInfoRow")
        update_row_layout = QHBoxLayout(update_row)
        update_row_layout.setContentsMargins(14, 12, 14, 12)
        update_row_layout.setSpacing(12)
        update_text = QVBoxLayout()
        update_text.setContentsMargins(0, 0, 0, 0)
        update_text.setSpacing(3)
        self.settings_update_check_title = QLabel(self.tr("settings_update_check_title"))
        self.settings_update_check_title.setObjectName("SearchMeta")
        self.settings_update_check_hint = QLabel(self.tr("settings_update_check_hint"))
        self.settings_update_check_hint.setObjectName("SubtleLabel")
        self.settings_update_check_hint.setWordWrap(True)
        update_text.addWidget(self.settings_update_check_title)
        update_text.addWidget(self.settings_update_check_hint)
        self.update_manifest_button = QPushButton()
        self.update_manifest_button.setIcon(make_action_icon("refresh"))
        self.update_manifest_button.clicked.connect(self.refresh_update_manifest)
        self.update_install_button = QPushButton()
        self.update_install_button.setObjectName("ToolPrimaryButton")
        self.update_install_button.clicked.connect(lambda: check_for_updates(self))
        self.update_site_button = QPushButton()
        self.update_site_button.clicked.connect(lambda: open_official_site(self))
        self.update_copy_manifest_button = QPushButton()
        self.update_copy_manifest_button.clicked.connect(self.copy_manifest_url)
        self.update_copy_package_button = QPushButton()
        self.update_copy_package_button.clicked.connect(self.copy_package_url)

        update_row_layout.addLayout(update_text, 1)
        update_row_layout.addWidget(self.update_manifest_button)
        update_row_layout.addWidget(self.update_install_button)
        update_row_layout.addWidget(self.update_site_button)
        self.update_copy_manifest_button.hide()
        self.update_copy_package_button.hide()
        info_layout.addWidget(update_row)

        self.update_keep_data_label = QLabel(self.tr("update_keep_data"))
        self.update_keep_data_label.setObjectName("SubtleLabel")
        self.update_keep_data_label.setWordWrap(True)
        info_layout.addWidget(self.update_keep_data_label)

        self.settings_release_notes_label = QLabel()
        self.settings_release_notes_label.setObjectName("SearchMeta")
        self.update_notes = QTextEdit()
        self.update_notes.setObjectName("SettingsNotes")
        self.update_notes.setReadOnly(True)
        self.update_notes.setMinimumHeight(88)
        self.update_notes.setMaximumHeight(120)
        info_layout.addWidget(self.settings_release_notes_label)
        info_layout.addWidget(self.update_notes)
        layout.addWidget(self.update_info_group)

        diagnostics_panel = QFrame()
        diagnostics_panel.setObjectName("SettingsCard")
        diagnostics_layout = QVBoxLayout(diagnostics_panel)
        diagnostics_layout.setContentsMargins(22, 20, 22, 20)
        diagnostics_layout.setSpacing(12)
        diagnostics_header = QHBoxLayout()
        diagnostics_header.setSpacing(10)
        self.diagnostics_title = QLabel()
        self.diagnostics_title.setObjectName("ActivityCardTitle")
        self.settings_diagnostics_badge = QLabel()
        self.settings_diagnostics_badge.setObjectName("ActivityBadge")
        diagnostics_header.addWidget(self.diagnostics_title)
        diagnostics_header.addStretch(1)
        diagnostics_header.addWidget(self.settings_diagnostics_badge)
        self.diagnostics_subtitle = QLabel()
        self.diagnostics_subtitle.setObjectName("SubtleLabel")
        self.diagnostics_subtitle.setWordWrap(True)
        diagnostics_layout.addLayout(diagnostics_header)
        diagnostics_layout.addWidget(self.diagnostics_subtitle)

        support_row = QFrame()
        support_row.setObjectName("SettingsInfoRow")
        support_layout = QHBoxLayout(support_row)
        support_layout.setContentsMargins(14, 12, 14, 12)
        support_layout.setSpacing(12)
        support_text = QVBoxLayout()
        support_text.setContentsMargins(0, 0, 0, 0)
        support_text.setSpacing(3)
        self.diagnostics_warnings_label = QLabel()
        self.diagnostics_warnings_label.setObjectName("SearchMeta")
        self.settings_health_summary = QLabel()
        self.settings_health_summary.setObjectName("SubtleLabel")
        self.settings_health_summary.setWordWrap(True)
        support_text.addWidget(self.diagnostics_warnings_label)
        support_text.addWidget(self.settings_health_summary)
        self.diagnostics_open_logs_button = QPushButton()
        self.diagnostics_copy_button = QPushButton()
        self.diagnostics_refresh_button = QPushButton()
        self.diagnostics_refresh_button.setObjectName("ToolPrimaryButton")
        self.diagnostics_open_logs_button.clicked.connect(self.open_logs_folder)
        self.diagnostics_copy_button.clicked.connect(self.copy_diagnostics)
        self.diagnostics_refresh_button.clicked.connect(self.refresh_diagnostics)
        support_layout.addLayout(support_text, 1)
        support_layout.addWidget(self.diagnostics_copy_button)
        support_layout.addWidget(self.diagnostics_open_logs_button)
        support_layout.addWidget(self.diagnostics_refresh_button)
        diagnostics_layout.addWidget(support_row)

        self.diagnostics_version = QLabel()
        self.diagnostics_config_path = QLabel()
        self.diagnostics_asset_root = QLabel()
        self.diagnostics_log_path = QLabel()
        self.diagnostics_overlay_count = QLabel()
        for label in (
            self.diagnostics_version,
            self.diagnostics_config_path,
            self.diagnostics_asset_root,
            self.diagnostics_log_path,
            self.diagnostics_overlay_count,
        ):
            label.setObjectName("SettingsValue")
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            label.setWordWrap(True)
            label.hide()
        self.diagnostics_recent = QTextEdit()
        self.diagnostics_recent.setObjectName("SettingsNotes")
        self.diagnostics_recent.setReadOnly(True)
        self.diagnostics_recent.hide()
        layout.addWidget(diagnostics_panel)

        uninstall_card = QFrame()
        uninstall_card.setObjectName("SettingsCard")
        uninstall_layout = QVBoxLayout(uninstall_card)
        uninstall_layout.setContentsMargins(22, 20, 22, 20)
        uninstall_layout.setSpacing(12)
        uninstall_header = QHBoxLayout()
        uninstall_header.setSpacing(10)
        self.settings_uninstall_label = QLabel()
        self.settings_uninstall_label.setObjectName("ActivityCardTitle")
        self.settings_uninstall_badge = QLabel()
        self.settings_uninstall_badge.setObjectName("ActivityBadge")
        uninstall_header.addWidget(self.settings_uninstall_label)
        uninstall_header.addStretch(1)
        uninstall_header.addWidget(self.settings_uninstall_badge)
        uninstall_layout.addLayout(uninstall_header)

        uninstall_row = QFrame()
        uninstall_row.setObjectName("SettingsInfoRow")
        uninstall_row_layout = QHBoxLayout(uninstall_row)
        uninstall_row_layout.setContentsMargins(14, 12, 14, 12)
        uninstall_row_layout.setSpacing(12)
        uninstall_text = QVBoxLayout()
        uninstall_text.setContentsMargins(0, 0, 0, 0)
        uninstall_text.setSpacing(3)
        self.settings_uninstall_title = QLabel()
        self.settings_uninstall_title.setObjectName("SearchMeta")
        self.settings_uninstall_hint = QLabel()
        self.settings_uninstall_hint.setObjectName("SubtleLabel")
        self.settings_uninstall_hint.setWordWrap(True)
        uninstall_text.addWidget(self.settings_uninstall_title)
        uninstall_text.addWidget(self.settings_uninstall_hint)
        self.uninstall_button = QPushButton()
        self.uninstall_button.setObjectName("DangerButton")
        self.uninstall_button.clicked.connect(self.confirm_uninstall)
        uninstall_row_layout.addLayout(uninstall_text, 1)
        uninstall_row_layout.addWidget(self.uninstall_button)
        uninstall_layout.addWidget(uninstall_row)
        layout.addWidget(uninstall_card)
        layout.addStretch(1)

        self.updates_tab_index = self.tabs.addTab(tab, self.tr("updates_tab"), "settings")

    def build_search_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(18)

        self.tool_target_combos = []
        self.refreshing_tool_targets = False

        selector = QFrame()
        selector.setObjectName("ToolSelectorPanel")
        selector.setFixedWidth(272)
        selector_layout = QVBoxLayout(selector)
        selector_layout.setContentsMargins(0, 0, 0, 0)
        selector_layout.setSpacing(8)

        self.tools_stack = QStackedWidget()
        self.tools_stack.setObjectName("ToolsStack")
        self.tool_choice_buttons = []
        tool_pages = [
            ("search", "tools_file_search", "tools_file_search_hint", self.build_file_search_tool_page()),
            ("party", "tools_offwork_countdown", "tools_offwork_countdown_hint", self.build_offwork_countdown_tool_page()),
            ("bell", "tools_repeat_reminder", "tools_repeat_reminder_hint", self.build_reminder_tool_page()),
            ("timer", "tools_focus_timer", "tools_focus_timer_hint", self.build_timer_tool_page()),
            ("memo", "tools_memo", "tools_memo_hint", self.build_memo_tool_page()),
            ("magic", "tools_interaction", "tools_interaction_hint", self.build_interaction_tool_page()),
            ("wallpaper", "tools_wallpaper", "tools_wallpaper_hint", self.build_wallpaper_tool_page()),
        ]
        for index, (icon_key, title_key, hint_key, page) in enumerate(tool_pages):
            self.tools_stack.addWidget(page)
            button = ToolChoiceButton(icon_key, self.tr(title_key), self.tr(hint_key))
            button.clicked.connect(lambda _checked=False, page_index=index: self.set_tool_page(page_index))
            selector_layout.addWidget(button)
            self.tool_choice_buttons.append((button, title_key, hint_key))
        selector_layout.addStretch(1)

        layout.addWidget(selector)
        layout.addWidget(self.tools_stack, 1)

        self.search_results = []
        self.set_tool_page(0)
        self.refresh_tool_target_combos()
        self.set_search_results([], self.tr("search_empty"))
        self.search_tab_index = self.tabs.addTab(tab, self.tr("search_tab"), "tools")

    def build_file_search_tool_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr("search_placeholder"))
        self.search_input.returnPressed.connect(self.run_local_search)
        self.search_mode_combo = QComboBox()
        self.search_mode_combo.addItem(self.tr("search_mode_apps"), "apps")
        self.search_mode_combo.addItem(self.tr("search_mode_documents"), "documents")
        self.search_mode_combo.addItem(self.tr("search_mode_all"), "all")
        self.search_button = QPushButton()
        self.search_button.setObjectName("ToolPrimaryButton")
        self.search_button.setIcon(make_action_icon("search", QColor("#ffffff")))
        self.search_button.clicked.connect(self.run_local_search)
        self.search_status_label = QLabel(self.tr("search_empty"))
        self.search_status_label.setObjectName("SearchMeta")
        toolbar.addWidget(self.search_input, 1)
        toolbar.addWidget(self.search_mode_combo)
        toolbar.addWidget(self.search_button)
        layout.addLayout(toolbar)
        layout.addWidget(self.search_status_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        self.search_results_container = QWidget()
        self.search_results_layout = QVBoxLayout(self.search_results_container)
        self.search_results_layout.setContentsMargins(0, 0, 0, 0)
        self.search_results_layout.setSpacing(8)
        scroll.setWidget(self.search_results_container)
        layout.addWidget(scroll, 1)
        return page

    def build_offwork_countdown_tool_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # 1. Hero Promo Card for Off-work Countdown (Macaron Warm Sunshine Theme)
        hero_card = QFrame()
        hero_card.setObjectName("OffworkHeroCard")
        hero_card.setStyleSheet("""
            QFrame#OffworkHeroCard {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #fff8f0,
                    stop: 0.5 #ffeedd,
                    stop: 1 #ffe5d0
                );
                border: 1px solid #ffd4b8;
                border-radius: 14px;
            }
        """)
        hero_layout = QVBoxLayout(hero_card)
        hero_layout.setContentsMargins(16, 14, 16, 14)
        hero_layout.setSpacing(8)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        hero_title = QLabel("🎉 下班狂喜倒计时 · 水豚嘟嘟音乐版")
        h_font = QFont("Microsoft YaHei UI", 12)
        h_font.setBold(True)
        hero_title.setFont(h_font)
        hero_title.setStyleSheet("color: #8a3b14; background: transparent;")
        top_row.addWidget(hero_title)

        pet_badge = QLabel("默认水豚嘟嘟 · 支持桌面任意宠物")
        pet_badge.setStyleSheet("""
            color: #d34c1b;
            background: rgba(255, 255, 255, 0.7);
            border: 1px solid #ffbc94;
            border-radius: 6px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: bold;
        """)
        top_row.addWidget(pet_badge)
        top_row.addStretch(1)
        hero_layout.addLayout(top_row)

        hero_desc = QLabel(
            "设置准点下班或时长倒计时。时间一到，默认以带音乐的水豚嘟嘟为主（或桌面上任意宠物）变大欢快起舞并伴有音乐，头顶冒出【下班了~ 🥳🎉 打工人解放啦！】，点击宠物即可平滑缩回！右键桌面任意宠物也可随时触发。"
        )
        hero_desc.setStyleSheet("color: #965337; font-size: 11px; line-height: 1.4;")
        hero_desc.setWordWrap(True)
        hero_layout.addWidget(hero_desc)

        layout.addWidget(hero_card)

        # 2. Main Control Panel Surface
        panel = self.tool_panel()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 16, 18, 16)
        panel_layout.setSpacing(14)

        # Mode Segmented Control
        self.offwork_mode_segmented = SegmentedControl(
            items=[
                ("exact", "准点下班"),
                ("duration", "多久之后"),
            ],
            default_index=0,
            dark_mode=False,
        )
        self.offwork_mode_segmented.currentIndexChanged.connect(self._on_offwork_mode_changed)
        panel_layout.addWidget(self.offwork_mode_segmented)

        # Container for Mode Inputs (Stacked Widget)
        self.offwork_inputs_stack = QStackedWidget()

        # Page 0: Exact Time Mode
        exact_page = QWidget()
        exact_layout = QVBoxLayout(exact_page)
        exact_layout.setContentsMargins(0, 0, 0, 0)
        exact_layout.setSpacing(8)

        exact_card = QFrame()
        exact_card.setObjectName("ToolSettingRow")
        exact_card_layout = QVBoxLayout(exact_card)
        exact_card_layout.setContentsMargins(16, 14, 16, 14)
        exact_card_layout.setSpacing(10)

        exact_card_title = QLabel(self.tr("tools_offwork_exact_label"))
        exact_card_title.setObjectName("SearchMeta")
        exact_card_layout.addWidget(exact_card_title)

        exact_ctrl_row = QHBoxLayout()
        exact_ctrl_row.setSpacing(10)

        self.tool_offwork_time_edit = QTimeEdit()
        self.tool_offwork_time_edit.setDisplayFormat("HH:mm")
        self.tool_offwork_time_edit.setTime(QTime(18, 0))
        self.tool_offwork_time_edit.setStyleSheet("""
            QTimeEdit {
                background: #ffffff;
                border: 1.5px solid #d4dbe4;
                border-radius: 8px;
                padding: 4px 10px;
                font-size: 13px;
                font-weight: bold;
                color: #26334a;
                min-width: 90px;
            }
            QTimeEdit:focus {
                border-color: #ff7f87;
            }
        """)
        exact_ctrl_row.addWidget(self.tool_offwork_time_edit)

        # Quick preset buttons for exact time
        for preset_str, (h, m) in [("17:30", (17, 30)), ("18:00", (18, 0)), ("18:30", (18, 30)), ("19:00", (19, 0))]:
            btn = QPushButton(preset_str)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: #f4f6fa;
                    border: 1px solid #d8e0eb;
                    border-radius: 6px;
                    padding: 4px 10px;
                    font-size: 11px;
                    color: #4b5260;
                }
                QPushButton:hover {
                    background: #ffebed;
                    border-color: #ff7f87;
                    color: #d94154;
                }
            """)
            btn.clicked.connect(lambda _c=False, hour=h, minute=m: self.tool_offwork_time_edit.setTime(QTime(hour, minute)))
            exact_ctrl_row.addWidget(btn)

        exact_ctrl_row.addStretch(1)
        exact_card_layout.addLayout(exact_ctrl_row)
        exact_layout.addWidget(exact_card)
        self.offwork_inputs_stack.addWidget(exact_page)

        # Page 1: Duration Mode
        duration_page = QWidget()
        duration_layout = QVBoxLayout(duration_page)
        duration_layout.setContentsMargins(0, 0, 0, 0)
        duration_layout.setSpacing(8)

        self.tool_offwork_duration_picker = VibeTimePicker(default_minutes=60, presets=[15, 30, 45, 60, 90, 120])
        self.tool_offwork_duration_picker.setRange(1, 12 * 60)
        self.tool_offwork_duration_picker.setSingleStep(5)
        self.tool_offwork_duration_picker.setSuffix(" 分钟")
        self.tool_offwork_duration_picker.setValue(60)
        duration_layout.addWidget(self.tool_setting_card("tools_offwork_duration_label", self.tool_offwork_duration_picker))
        self.offwork_inputs_stack.addWidget(duration_page)

        panel_layout.addWidget(self.offwork_inputs_stack)

        # 3. Big Digital Countdown Display Card
        countdown_card = QFrame()
        countdown_card.setObjectName("OffworkDisplayCard")
        countdown_card.setStyleSheet("""
            QFrame#OffworkDisplayCard {
                background: #fdfbf7;
                border: 1.5px dashed #e4d8cb;
                border-radius: 12px;
                padding: 12px;
            }
        """)
        c_layout = QVBoxLayout(countdown_card)
        c_layout.setContentsMargins(14, 12, 14, 12)
        c_layout.setSpacing(6)

        c_top = QHBoxLayout()
        self.tool_offwork_badge = QLabel("○ 未开启倒计时")
        self.tool_offwork_badge.setStyleSheet("color: #8a94a6; font-size: 11px; font-weight: bold;")
        c_top.addWidget(self.tool_offwork_badge)
        c_top.addStretch(1)
        c_layout.addLayout(c_top)

        self.tool_offwork_clock_display = QLabel("--:--:--")
        clk_font = QFont("Consolas", 28)
        clk_font.setBold(True)
        self.tool_offwork_clock_display.setFont(clk_font)
        self.tool_offwork_clock_display.setAlignment(Qt.AlignCenter)
        self.tool_offwork_clock_display.setStyleSheet("color: #2b3345; letter-spacing: 2px;")
        c_layout.addWidget(self.tool_offwork_clock_display)

        self.tool_offwork_hint_display = QLabel("点击下方按钮开启倒计时，时间到达将触发水豚欢庆")
        self.tool_offwork_hint_display.setAlignment(Qt.AlignCenter)
        self.tool_offwork_hint_display.setStyleSheet("color: #9aa5b6; font-size: 11px;")
        c_layout.addWidget(self.tool_offwork_hint_display)

        panel_layout.addWidget(countdown_card)

        # 4. Action Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.tool_offwork_toggle_button = SpringPushButton(self.tr("tools_offwork_start"))
        self.tool_offwork_toggle_button.setObjectName("ToolPrimaryButton")
        self.tool_offwork_toggle_button.clicked.connect(self.toggle_offwork_countdown)

        self.tool_offwork_test_button = SpringPushButton(self.tr("tools_offwork_test"))
        self.tool_offwork_test_button.setCursor(Qt.PointingHandCursor)
        self.tool_offwork_test_button.setStyleSheet("""
            QPushButton {
                background: #fff0f5;
                border: 1px solid #ffccd5;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
                color: #c92a43;
            }
            QPushButton:hover {
                background: #ffe3eb;
                border-color: #ff99aa;
            }
        """)
        self.tool_offwork_test_button.clicked.connect(self.trigger_offwork_alarm)

        btn_row.addWidget(self.tool_offwork_toggle_button)
        btn_row.addWidget(self.tool_offwork_test_button)
        btn_row.addStretch(1)
        panel_layout.addLayout(btn_row)

        # 5. Power Management Card (Timed Sleep / Shutdown)
        power_card = QFrame()
        power_card.setObjectName("PowerScheduleCard")
        power_card.setStyleSheet("""
            QFrame#PowerScheduleCard {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
            }
        """)
        p_layout = QVBoxLayout(power_card)
        p_layout.setContentsMargins(14, 12, 14, 12)
        p_layout.setSpacing(8)

        p_title = QLabel("🌙 电脑定时休眠与自动关机 (电源计划)")
        p_title.setStyleSheet("font-weight: bold; color: #1e293b; font-size: 12px;")
        p_layout.addWidget(p_title)

        p_btns = QHBoxLayout()
        p_btns.setSpacing(8)

        btn_power_after = QPushButton("⏱️ 倒计时休眠/关机...")
        btn_power_after.setCursor(Qt.PointingHandCursor)
        btn_power_after.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                color: #334155;
            }
            QPushButton:hover {
                background: #f1f5f9;
                border-color: #94a3b8;
            }
        """)
        btn_power_after.clicked.connect(self.schedule_power_after_minutes_from_panel)

        btn_power_exact = QPushButton("⏰ 指定时刻休眠/关机...")
        btn_power_exact.setCursor(Qt.PointingHandCursor)
        btn_power_exact.setStyleSheet("""
            QPushButton {
                background: #ffffff;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                color: #334155;
            }
            QPushButton:hover {
                background: #f1f5f9;
                border-color: #94a3b8;
            }
        """)
        btn_power_exact.clicked.connect(self.schedule_power_at_time_from_panel)

        btn_power_cancel = QPushButton("❌ 取消电源计划")
        btn_power_cancel.setCursor(Qt.PointingHandCursor)
        btn_power_cancel.setStyleSheet("""
            QPushButton {
                background: #fff1f2;
                border: 1px solid #fecdd3;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 11px;
                color: #e11d48;
            }
            QPushButton:hover {
                background: #ffe4e6;
            }
        """)
        btn_power_cancel.clicked.connect(self.cancel_power_schedule_from_panel)

        p_btns.addWidget(btn_power_after)
        p_btns.addWidget(btn_power_exact)
        p_btns.addWidget(btn_power_cancel)
        p_btns.addStretch(1)
        p_layout.addLayout(p_btns)

        panel_layout.addWidget(power_card)

        panel_layout.addStretch(1)
        layout.addWidget(panel, 1)

        # Init offwork timer state
        self._offwork_timer = QTimer(self)
        self._offwork_timer.setInterval(1000)
        self._offwork_timer.timeout.connect(self._on_offwork_timer_tick)
        self._offwork_target_dt = None
        self._offwork_active = False

        return page

    def schedule_power_after_minutes_from_panel(self):
        if state.WINDOWS:
            state.WINDOWS[0].schedule_power_after_minutes()
        else:
            QMessageBox.information(self, "定时休眠与关机", "请先在主页桌面上开启桌宠，即可设置定时休眠/自动关机。")

    def schedule_power_at_time_from_panel(self):
        if state.WINDOWS:
            state.WINDOWS[0].schedule_power_at_time()
        else:
            QMessageBox.information(self, "定时休眠与关机", "请先在主页桌面上开启桌宠，即可设置定时休眠/自动关机。")

    def cancel_power_schedule_from_panel(self):
        if state.WINDOWS:
            state.WINDOWS[0].cancel_power_schedule()
            QMessageBox.information(self, "电源计划", "已取消定时休眠/关机计划。")
        else:
            QMessageBox.information(self, "电源计划", "当前没有生效中的电源计划。")

    def _on_offwork_mode_changed(self, index: int):
        if hasattr(self, "offwork_inputs_stack"):
            self.offwork_inputs_stack.setCurrentIndex(index)

    def toggle_offwork_countdown(self):
        if getattr(self, "_offwork_active", False):
            self.stop_offwork_countdown()
        else:
            self.start_offwork_countdown()

    def start_offwork_countdown(self):
        from datetime import timedelta
        now = datetime.now()
        mode_idx = self.offwork_mode_segmented.currentIndex() if hasattr(self, "offwork_mode_segmented") else 0

        if mode_idx == 0:
            t = self.tool_offwork_time_edit.time()
            target = now.replace(hour=t.hour(), minute=t.minute(), second=0, microsecond=0)
            if target <= now:
                target = target + timedelta(days=1)
        else:
            minutes = self.tool_offwork_duration_picker.value() if hasattr(self, "tool_offwork_duration_picker") else 60
            target = now + timedelta(minutes=minutes)

        self._offwork_target_dt = target
        self._offwork_active = True
        self._offwork_timer.start(1000)

        if hasattr(self, "tool_offwork_toggle_button"):
            self.tool_offwork_toggle_button.setText(self.tr("tools_offwork_stop"))
        if hasattr(self, "tool_offwork_badge"):
            self.tool_offwork_badge.setText("● 倒计时进行中")
            self.tool_offwork_badge.setStyleSheet("color: #27ae60; font-size: 11px; font-weight: bold;")
        if hasattr(self, "tool_offwork_hint_display"):
            self.tool_offwork_hint_display.setText(f"预定下班时刻：{target.strftime('%H:%M:%S')}（到点触发水豚狂喜跳舞）")

        self._on_offwork_timer_tick()

    def stop_offwork_countdown(self):
        self._offwork_active = False
        if hasattr(self, "_offwork_timer"):
            self._offwork_timer.stop()
        self._offwork_target_dt = None

        if hasattr(self, "tool_offwork_toggle_button"):
            self.tool_offwork_toggle_button.setText(self.tr("tools_offwork_start"))
        if hasattr(self, "tool_offwork_clock_display"):
            self.tool_offwork_clock_display.setText("--:--:--")
        if hasattr(self, "tool_offwork_badge"):
            self.tool_offwork_badge.setText("○ 未开启倒计时")
            self.tool_offwork_badge.setStyleSheet("color: #8a94a6; font-size: 11px; font-weight: bold;")
        if hasattr(self, "tool_offwork_hint_display"):
            self.tool_offwork_hint_display.setText("点击下方按钮开启倒计时，时间到达将触发水豚欢庆")

    def _on_offwork_timer_tick(self):
        if not getattr(self, "_offwork_active", False) or not getattr(self, "_offwork_target_dt", None):
            return
        now = datetime.now()
        diff = (self._offwork_target_dt - now).total_seconds()
        if diff <= 0:
            self.stop_offwork_countdown()
            if hasattr(self, "tool_offwork_clock_display"):
                self.tool_offwork_clock_display.setText("00:00:00")
            if hasattr(self, "tool_offwork_hint_display"):
                self.tool_offwork_hint_display.setText("🎉 下班时间到！水豚正在屏幕上狂喜跳舞！")
            self.trigger_offwork_alarm()
        else:
            hours = int(diff // 3600)
            mins = int((diff % 3600) // 60)
            secs = int(diff % 60)
            if hasattr(self, "tool_offwork_clock_display"):
                self.tool_offwork_clock_display.setText(f"{hours:02d}:{mins:02d}:{secs:02d}")

    def trigger_offwork_alarm(self):
        """下班欢庆到点触发：默认优先以带音乐的水豚“嘟嘟”为主；若桌面有其他宠物也完全兼容"""
        target = None
        # 1. 优先寻找桌面上的带音乐水豚嘟嘟
        for window in state.WINDOWS:
            asset_name = getattr(getattr(window, "asset", None), "name", "").lower()
            asset_path_str = str(getattr(window, "asset_path", "")).lower()
            if "嘟嘟" in asset_name or "dudu" in asset_path_str or "duducapybara" in asset_path_str:
                target = window
                break

        # 2. 其次寻找桌面上的其他水豚（如水豚噜噜）
        if target is None:
            for window in state.WINDOWS:
                asset_name = getattr(getattr(window, "asset", None), "name", "").lower()
                asset_path_str = str(getattr(window, "asset_path", "")).lower()
                if "capybara" in asset_name or "水豚" in asset_name or "lulucabybara" in asset_path_str:
                    target = window
                    break

        # 3. 如果桌面上已有正在运行的桌宠，也可以直接作为欢庆角色
        if target is None and state.WINDOWS:
            target = self.selected_window if self.selected_window in state.WINDOWS else state.WINDOWS[0]

        # 4. 如果桌面上当前没有运行任何桌宠，默认自动召唤带音乐的水豚“嘟嘟”
        if target is None:
            candidates = [
                Path(BASE_DIR) / "assets" / "DuduCapybaraPet",
                Path(BASE_DIR) / "assets" / "默认" / "DuduCapybaraPet",
                Path(BASE_DIR) / "assets" / "LuluCapybaraPet",
                Path(BASE_DIR) / "assets" / "默认" / "LuluCapybaraPet",
            ]
            if hasattr(self, "active_pack_dir"):
                candidates.append(Path(self.active_pack_dir()) / "DuduCapybaraPet")
                candidates.append(Path(self.active_pack_dir()) / "LuluCapybaraPet")

            for p in candidates:
                if p.is_dir():
                    target = add_window(str(p))
                    if target is not None:
                        self.refresh_active()
                        break

        if target is not None:
            if not target.isVisible():
                target.show()
            target.raise_()
            if hasattr(target, "trigger_offwork_celebration"):
                target.trigger_offwork_celebration(target_scale=150, duration_seconds=300)
            if hasattr(self, "tool_offwork_hint_display"):
                pet_name = getattr(getattr(target, "asset", None), "name", "桌宠")
                self.tool_offwork_hint_display.setText(f"🎉 {pet_name} 正在屏幕中央欢快起舞！点击它即可恢复原样。")
        else:
            QMessageBox.information(
                self,
                self.tr("tools_offwork_countdown"),
                "未找到可用桌宠，请先在【桌宠】页面启动一个宠物。",
            )

    def build_reminder_tool_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.add_tool_target_row(layout)

        panel = self.tool_panel()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(14)
        self.tool_repeat_minutes = VibeTimePicker(default_minutes=30, presets=[15, 30, 45, 60, 90, 120])
        self.tool_repeat_minutes.setRange(1, 24 * 60)
        self.tool_repeat_minutes.setSingleStep(5)
        self.tool_repeat_minutes.setSuffix(" 分钟")
        self.tool_repeat_minutes.setValue(30)
        self.tool_repeat_minutes.setKeyboardTracking(False)
        panel_layout.addWidget(self.tool_setting_card("tools_repeat_interval", self.tool_repeat_minutes))

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        self.tool_repeat_start_button = QPushButton()
        self.tool_repeat_start_button.setObjectName("ToolPrimaryButton")
        self.tool_repeat_start_button.clicked.connect(self.start_tool_repeat_reminder)
        self.tool_repeat_stop_button = QPushButton()
        self.tool_repeat_stop_button.clicked.connect(self.stop_tool_repeat_reminder)
        button_row.addWidget(self.tool_repeat_start_button)
        button_row.addWidget(self.tool_repeat_stop_button)
        button_row.addStretch(1)
        panel_layout.addLayout(button_row)

        self.tool_reminder_status = QLabel()
        self.tool_reminder_status.setObjectName("ToolStatusLabel")
        panel_layout.addWidget(self.tool_reminder_status)
        panel_layout.addStretch(1)
        layout.addWidget(panel, 1)
        return page

    def build_timer_tool_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.add_tool_target_row(layout)

        panel = self.tool_panel()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(14)
        self.tool_timer_minutes = VibeTimePicker(default_minutes=25, presets=[5, 15, 25, 45, 60])
        self.tool_timer_minutes.setRange(1, 24 * 60)
        self.tool_timer_minutes.setSingleStep(5)
        self.tool_timer_minutes.setSuffix(" 分钟")
        self.tool_timer_minutes.setValue(25)
        self.tool_timer_minutes.setKeyboardTracking(False)
        panel_layout.addWidget(self.tool_setting_card("tools_timer_duration", self.tool_timer_minutes))

        # VibeHub Segmented Control for Timer Mode
        self.tool_timer_segmented = SegmentedControl(
            items=[
                ("focus_25", "25m 专注"),
                ("break_5", "5m 休息"),
                ("custom", "自定义时长"),
            ],
            default_index=0,
            dark_mode=False,
        )
        self.tool_timer_segmented.currentIndexChanged.connect(self._on_timer_mode_changed)
        panel_layout.addWidget(self.tool_timer_segmented)

        # Vibe Modern Focus Clock Card
        self.tool_timer_clock_card = QFrame()
        self.tool_timer_clock_card.setObjectName("TimerClockCard")
        self.tool_timer_clock_card.setStyleSheet("""
            QFrame#TimerClockCard {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #fffdfa, stop: 1 #fff6f0);
                border: 1px solid #fed7cc;
                border-radius: 16px;
            }
        """)
        c_layout = QVBoxLayout(self.tool_timer_clock_card)
        c_layout.setContentsMargins(18, 14, 18, 14)
        c_layout.setSpacing(6)

        c_top = QHBoxLayout()
        c_title = QLabel("⏱️ 专注时钟 · Focus Clock")
        c_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #55443d; background: transparent;")
        c_top.addWidget(c_title)
        c_top.addStretch(1)

        self.tool_timer_badge = QLabel("准备就绪")
        self.tool_timer_badge.setStyleSheet("""
            background: #ffeff0;
            color: #ff526c;
            border: 1px solid #ffccd3;
            border-radius: 9px;
            padding: 2px 10px;
            font-size: 11px;
            font-weight: bold;
        """)
        c_top.addWidget(self.tool_timer_badge)
        c_layout.addLayout(c_top)

        self.tool_timer_clock_display = QLabel("25:00")
        clk_font = QFont("Consolas", 32, QFont.Bold)
        clk_font.setStyleHint(QFont.Monospace)
        self.tool_timer_clock_display.setFont(clk_font)
        self.tool_timer_clock_display.setAlignment(Qt.AlignCenter)
        self.tool_timer_clock_display.setStyleSheet("color: #2d2320; letter-spacing: 2px; padding: 2px 0;")
        c_layout.addWidget(self.tool_timer_clock_display)

        panel_layout.addWidget(self.tool_timer_clock_card)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self.tool_timer_custom_button = SpringPushButton()
        self.tool_timer_custom_button.setObjectName("ToolPrimaryButton")
        self.tool_timer_custom_button.clicked.connect(self._start_segmented_timer)
        self.tool_timer_focus_button = self.tool_timer_custom_button
        self.tool_timer_break_button = self.tool_timer_custom_button

        self.tool_timer_toggle_button = SpringPushButton()
        self.tool_timer_toggle_button.clicked.connect(self.toggle_tool_timer)
        self.tool_timer_reset_button = SpringPushButton()
        self.tool_timer_reset_button.clicked.connect(self.reset_tool_timer)
        action_row.addWidget(self.tool_timer_custom_button)
        action_row.addWidget(self.tool_timer_toggle_button)
        action_row.addWidget(self.tool_timer_reset_button)
        action_row.addStretch(1)
        panel_layout.addLayout(action_row)


        self.tool_timer_status = QLabel()
        self.tool_timer_status.setObjectName("ToolStatusLabel")
        panel_layout.addWidget(self.tool_timer_status)
        panel_layout.addStretch(1)
        layout.addWidget(panel, 1)
        return page

    def _on_timer_mode_changed(self, index: int):
        if index == 0:
            self.tool_timer_minutes.setValue(25)
        elif index == 1:
            self.tool_timer_minutes.setValue(5)

    def _start_segmented_timer(self):
        idx = self.tool_timer_segmented.currentIndex() if hasattr(self, "tool_timer_segmented") else 0
        if idx == 0:
            self.start_tool_timer(25, FOCUS_MODE_FOCUS)
        elif idx == 1:
            self.start_tool_timer(5, FOCUS_MODE_BREAK)
        else:
            self.start_tool_timer(self.tool_timer_minutes.value(), FOCUS_MODE_CUSTOM)

    def prompt_clear_tool_memo(self):
        pop = PopconfirmBubble(
            target_widget=self.tool_memo_clear_button,
            message="确定清空当前便签文本吗？",
            confirm_text="确定清空",
            cancel_text="取消",
            dark_mode=False,
            parent=self,
        )
        pop.confirmed.connect(self.clear_tool_memo)
        pop.show_above_target()
        self._memo_popconfirm = pop

    def build_memo_tool_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.add_tool_target_row(layout)

        # 1. NotchNotes Macaron Pastel Feature Card
        notchnotes_card = QFrame()
        notchnotes_card.setObjectName("NotchNotesPromoCard")
        notchnotes_card.setStyleSheet("""
            QFrame#NotchNotesPromoCard {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #fffdfa,
                    stop: 0.5 #fff7f2,
                    stop: 1 #fdf2e9
                );
                border: 1px solid #fed7cc;
                border-radius: 14px;
            }
        """)
        card_layout = QVBoxLayout(notchnotes_card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(10)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        card_title = QLabel("📝 NotchNotes 治愈便签")
        c_font = QFont("Microsoft YaHei UI", 11)
        c_font.setBold(True)
        card_title.setFont(c_font)
        card_title.setStyleSheet("color: #2d2320; background: transparent;")
        top_row.addWidget(card_title)

        author_badge = QLabel("灵感来自 oil-oil/NotchNotes")
        author_badge.setStyleSheet("""
            color: #ff526c;
            background: #ffeff0;
            border: 1px solid #ffccd3;
            border-radius: 6px;
            padding: 2px 8px;
            font-size: 10px;
            font-weight: bold;
        """)
        top_row.addWidget(author_badge)
        top_row.addStretch(1)

        self.notchnotes_open_btn = QPushButton("展开便签窗口 ✦")
        self.notchnotes_open_btn.setCursor(Qt.PointingHandCursor)
        self.notchnotes_open_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #ff8a9e, stop: 1 #ff526c);
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 6px 16px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #ff6b81, stop: 1 #e63950);
            }
        """)
        self.notchnotes_open_btn.clicked.connect(self.open_notchnotes_from_panel)
        top_row.addWidget(self.notchnotes_open_btn)
        card_layout.addLayout(top_row)

        desc_label = QLabel(
            "集成交互式 Todo 待办清单、Markdown 笔记灵感编辑、底部文件拖拽暂存架，并与桌宠头顶气泡与完成庆祝动作实时联动。"
        )
        desc_label.setStyleSheet("color: #7c6d66; font-size: 11px; line-height: 1.4;")
        desc_label.setWordWrap(True)
        card_layout.addWidget(desc_label)

        self.notchnotes_stats_label = QLabel()
        self.notchnotes_stats_label.setStyleSheet("color: #52c79b; font-size: 10px; font-weight: bold;")
        card_layout.addWidget(self.notchnotes_stats_label)

        layout.addWidget(notchnotes_card)


        # 2. Existing quick memo editor panel
        panel = self.tool_panel()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 16, 18, 16)
        panel_layout.setSpacing(12)

        panel_title = QLabel("简易便签文本快速同步")
        p_font = QFont("Microsoft YaHei UI", 10)
        p_font.setBold(True)
        panel_title.setFont(p_font)
        panel_title.setStyleSheet("color: #4b5260;")
        panel_layout.addWidget(panel_title)

        self.tool_memo_text = QTextEdit()
        self.tool_memo_text.setPlaceholderText(self.tr("tools_memo_placeholder"))
        self.tool_memo_text.setMinimumHeight(110)
        panel_layout.addWidget(self.tool_memo_text)

        button_row = QHBoxLayout()
        button_row.setSpacing(8)
        self.tool_memo_save_button = SpringPushButton()
        self.tool_memo_save_button.setObjectName("ToolPrimaryButton")
        self.tool_memo_save_button.clicked.connect(self.save_tool_memo)
        self.tool_memo_toggle_button = SpringPushButton()
        self.tool_memo_toggle_button.clicked.connect(self.toggle_tool_memo)
        self.tool_memo_done_button = SpringPushButton()
        self.tool_memo_done_button.clicked.connect(self.complete_tool_memo)
        self.tool_memo_clear_button = SpringPushButton()
        self.tool_memo_clear_button.clicked.connect(self.prompt_clear_tool_memo)
        button_row.addWidget(self.tool_memo_save_button)
        button_row.addWidget(self.tool_memo_toggle_button)
        button_row.addWidget(self.tool_memo_done_button)
        button_row.addWidget(self.tool_memo_clear_button)
        button_row.addStretch(1)
        panel_layout.addLayout(button_row)

        self.tool_memo_status = QLabel()
        self.tool_memo_status.setObjectName("ToolStatusLabel")
        panel_layout.addWidget(self.tool_memo_status)
        panel_layout.addStretch(1)
        layout.addWidget(panel, 1)
        return page

    def build_interaction_tool_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        self.add_tool_target_row(layout)

        panel = self.tool_panel()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(12)
        tool_row = QHBoxLayout()
        tool_row.setSpacing(8)
        self.tool_whip_button = QPushButton()
        self.tool_whip_button.clicked.connect(lambda: show_whip_tool(self))
        self.tool_reward_button = QPushButton()
        self.tool_reward_button.clicked.connect(self.play_tool_reward)
        tool_row.addWidget(self.tool_whip_button)
        tool_row.addWidget(self.tool_reward_button)
        tool_row.addStretch(1)
        panel_layout.addLayout(tool_row)

        self.tool_interaction_status = QLabel()
        self.tool_interaction_status.setObjectName("ToolStatusLabel")
        panel_layout.addWidget(self.tool_interaction_status)
        panel_layout.addStretch(1)
        layout.addWidget(panel, 1)
        return page

    def build_wallpaper_tool_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        panel = self.tool_panel()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(18, 18, 18, 18)
        panel_layout.setSpacing(14)

        header = QFrame()
        header.setObjectName("ToolSettingRow")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 12, 14, 12)
        header_layout.setSpacing(12)
        header_text = QVBoxLayout()
        header_text.setContentsMargins(0, 0, 0, 0)
        header_text.setSpacing(3)
        self.wallpaper_title_label = QLabel(self.tr("tools_wallpaper_title"))
        self.wallpaper_title_label.setObjectName("SearchMeta")
        self.wallpaper_subtitle_label = QLabel(self.tr("tools_wallpaper_subtitle"))
        self.wallpaper_subtitle_label.setObjectName("SubtleLabel")
        self.wallpaper_subtitle_label.setWordWrap(True)
        header_text.addWidget(self.wallpaper_title_label)
        header_text.addWidget(self.wallpaper_subtitle_label)
        self.wallpaper_enabled_check = QCheckBox(self.tr("tools_wallpaper_enable"))
        self.wallpaper_enabled_check.setChecked(bool(wallpaper_schedule_settings().get("enabled")))
        self.wallpaper_enabled_check.toggled.connect(self.toggle_wallpaper_schedule)
        header_layout.addLayout(header_text, 1)
        header_layout.addWidget(self.wallpaper_enabled_check)
        panel_layout.addWidget(header)

        self.wallpaper_slot_cards = {}
        slots_row = QHBoxLayout()
        slots_row.setSpacing(12)
        for slot in wallpaper_schedule_settings().get("slots", []):
            card = WallpaperSlotCard(slot, self.choose_wallpaper_slot_image, self)
            self.wallpaper_slot_cards[slot.get("id")] = card
            slots_row.addWidget(card, 1)
        panel_layout.addLayout(slots_row)

        self.wallpaper_status_label = QLabel()
        self.wallpaper_status_label.setObjectName("ToolStatusLabel")
        panel_layout.addWidget(self.wallpaper_status_label)
        panel_layout.addStretch(1)
        layout.addWidget(panel, 1)
        return page

    def tool_panel(self):
        frame = QFrame()
        frame.setObjectName("ToolSurfacePanel")
        frame.setFrameShape(QFrame.NoFrame)
        return frame

    def tool_setting_card(self, label_key, widget):
        card = QFrame()
        card.setObjectName("ToolSettingRow")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        label = QLabel(self.tr(label_key))
        label.setObjectName("SearchMeta")
        layout.addWidget(label)
        layout.addWidget(widget)
        return card

    def tool_setting_row(self, label_key, widget):
        row = QFrame()
        row.setObjectName("ToolSettingRow")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)
        label = QLabel(self.tr(label_key))
        label.setObjectName("SearchMeta")
        layout.addWidget(label, 1)
        layout.addWidget(widget)
        return row

    def add_tool_target_row(self, layout):
        row = QFrame()
        row.setObjectName("ToolTargetRow")
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(14, 10, 14, 10)
        row_layout.setSpacing(10)
        label = QLabel(self.tr("tools_target_pet"))
        label.setObjectName("SearchMeta")
        combo = QComboBox()
        combo.currentIndexChanged.connect(lambda _index, source=combo: self.tool_target_changed(source))
        row_layout.addWidget(label)
        row_layout.addWidget(combo, 1)
        layout.addWidget(row)
        self.tool_target_combos.append(combo)
        return combo

    def set_tool_page(self, index):
        if not hasattr(self, "tools_stack"):
            return
        self.tools_stack.setCurrentIndex(index)
        for button_index, (button, _title_key, _hint_key) in enumerate(getattr(self, "tool_choice_buttons", [])):
            button.setChecked(button_index == index)
        self.update_tool_statuses()

    def selected_tool_window(self):
        if self.selected_window in state.WINDOWS:
            return self.selected_window
        return state.WINDOWS[0] if state.WINDOWS else None

    def refresh_tool_target_combos(self):
        if not hasattr(self, "tool_target_combos"):
            return
        selected = self.selected_tool_window()
        self.refreshing_tool_targets = True
        try:
            for combo in self.tool_target_combos:
                current_id = id(selected) if selected is not None else combo.currentData()
                combo.clear()
                if not state.WINDOWS:
                    combo.addItem(self.tr("tools_no_pet"), None)
                    combo.setEnabled(False)
                    continue
                combo.setEnabled(True)
                for window in state.WINDOWS:
                    combo.addItem(getattr(window.asset, "name", "桌宠"), id(window))
                index = combo.findData(current_id)
                combo.setCurrentIndex(index if index >= 0 else 0)
        finally:
            self.refreshing_tool_targets = False
        self.update_tool_statuses()

    def tool_target_changed(self, source_combo):
        if getattr(self, "refreshing_tool_targets", False):
            return
        window_id = source_combo.currentData()
        window = next((item for item in state.WINDOWS if id(item) == window_id), None)
        if window is not None:
            self.selected_window = window
            for combo in getattr(self, "tool_target_combos", []):
                if combo is not source_combo:
                    combo.blockSignals(True)
                    index = combo.findData(window_id)
                    combo.setCurrentIndex(index if index >= 0 else 0)
                    combo.blockSignals(False)
        self.update_tool_statuses()

    def update_tool_statuses(self):
        window = self.selected_tool_window()
        if hasattr(self, "tool_repeat_start_button"):
            self.tool_repeat_start_button.setText(self.tr("tools_repeat_start"))
            self.tool_repeat_stop_button.setText(self.tr("tools_repeat_stop"))
            self.tool_timer_focus_button.setText(self.tr("tools_timer_focus"))
            self.tool_timer_break_button.setText(self.tr("tools_timer_break"))
            self.tool_timer_custom_button.setText(self.tr("tools_timer_start"))
            self.tool_timer_toggle_button.setText(self.tr("tools_timer_pause") if getattr(window, "timer_running", False) else self.tr("tools_timer_resume"))
            self.tool_timer_reset_button.setText(self.tr("tools_timer_reset"))
            self.tool_memo_save_button.setText(self.tr("tools_memo_save"))
            self.tool_memo_toggle_button.setText(self.tr("tools_memo_hide") if getattr(window, "memo_visible", False) else self.tr("tools_memo_show"))
            self.tool_memo_done_button.setText(self.tr("tools_memo_done"))
            self.tool_memo_clear_button.setText(self.tr("tools_memo_clear"))
            self.tool_whip_button.setText(self.tr("tool_whip"))
            self.tool_reward_button.setText(self.tr("tools_reward"))
        if hasattr(self, "wallpaper_enabled_check"):
            self.wallpaper_enabled_check.setText(self.tr("tools_wallpaper_enable"))
            self.wallpaper_title_label.setText(self.tr("tools_wallpaper_title"))
            self.wallpaper_subtitle_label.setText(self.tr("tools_wallpaper_subtitle"))
            self.refresh_wallpaper_tool()
        if hasattr(self, "tool_offwork_toggle_button"):
            if getattr(self, "_offwork_active", False):
                self.tool_offwork_toggle_button.setText(self.tr("tools_offwork_stop"))
            else:
                self.tool_offwork_toggle_button.setText(self.tr("tools_offwork_start"))
        if hasattr(self, "tool_offwork_test_button"):
            self.tool_offwork_test_button.setText(self.tr("tools_offwork_test"))

        for button, title_key, hint_key in getattr(self, "tool_choice_buttons", []):
            button.set_content(self.tr(title_key), self.tr(hint_key))

        if hasattr(self, "tool_memo_text") and window is not None and not self.tool_memo_text.hasFocus():
            self.tool_memo_text.setPlainText(getattr(window, "memo_text", ""))
        target_name = getattr(getattr(window, "asset", None), "name", self.tr("tools_no_pet")) if window is not None else self.tr("tools_no_pet")
        reminder = self.tr("tools_status_no_pet")
        timer = self.tr("tools_status_no_pet")
        memo = self.tr("tools_status_no_pet")
        interaction = self.tr("tools_status_no_pet")
        if window is not None:
            if getattr(window, "reminder_repeat_enabled", False):
                minutes = max(1, round(getattr(window, "reminder_interval_seconds", 60) / 60))
                reminder = self.tr("tools_repeat_status_on", pet=target_name, minutes=minutes)
                if hasattr(self, "tool_repeat_minutes"):
                    self.tool_repeat_minutes.setValue(minutes)
            else:
                reminder = self.tr("tools_repeat_status_off", pet=target_name)
            timer = self.tr(
                "tools_timer_status",
                pet=target_name,
                time=window.format_timer() if hasattr(window, "format_timer") else "--:--",
                state=self.tr("tools_running") if getattr(window, "timer_running", False) else self.tr("tools_paused"),
            )
            memo_state = self.tr("tools_visible") if getattr(window, "memo_visible", False) else self.tr("tools_hidden")
            memo = self.tr("tools_memo_status", pet=target_name, state=memo_state)
            interaction = self.tr("tools_interaction_status", pet=target_name)
        if hasattr(self, "tool_reminder_status"):
            self.tool_reminder_status.setText(reminder)
            self.tool_timer_status.setText(timer)
            self.tool_memo_status.setText(memo)
            self.tool_interaction_status.setText(interaction)
        if hasattr(self, "tool_timer_clock_display"):
            if window is not None and hasattr(window, "format_timer"):
                time_str = window.format_timer()
                self.tool_timer_clock_display.setText(time_str)
                is_running = getattr(window, "timer_running", False)
                mode = getattr(window, "focus_mode", "")
                if is_running:
                    if mode == "focus":
                        self.tool_timer_badge.setText("⏳ 正在专注")
                        self.tool_timer_badge.setStyleSheet("background: #ffeff0; color: #ff526c; border: 1px solid #ffccd3; border-radius: 9px; padding: 2px 10px; font-size: 11px; font-weight: bold;")
                    elif mode == "break":
                        self.tool_timer_badge.setText("☕ 正在休息")
                        self.tool_timer_badge.setStyleSheet("background: #f0fdf4; color: #16a34a; border: 1px solid #bbf7d0; border-radius: 9px; padding: 2px 10px; font-size: 11px; font-weight: bold;")
                    else:
                        self.tool_timer_badge.setText("⏱️ 计时运行中")
                        self.tool_timer_badge.setStyleSheet("background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; border-radius: 9px; padding: 2px 10px; font-size: 11px; font-weight: bold;")
                else:
                    self.tool_timer_badge.setText("⏸️ 已暂停")
                    self.tool_timer_badge.setStyleSheet("background: #fdf8f4; color: #7c6d66; border: 1px solid #ebdcd2; border-radius: 9px; padding: 2px 10px; font-size: 11px; font-weight: bold;")
            else:
                self.tool_timer_clock_display.setText("25:00")
                self.tool_timer_badge.setText("准备就绪")
                self.tool_timer_badge.setStyleSheet("background: #ffeff0; color: #ff526c; border: 1px solid #ffccd3; border-radius: 9px; padding: 2px 10px; font-size: 11px; font-weight: bold;")

        if hasattr(self, "notchnotes_stats_label"):
            try:
                from .notchnotes_store import NotchNotesStore
                store = NotchNotesStore.get_instance()
                done, total = store.get_todo_stats()
                files_cnt = len(store.file_shelf)
                top_task = store.get_top_pending_task()
                top_str = f" | 进行中: {top_task}" if top_task else ""
                self.notchnotes_stats_label.setText(
                    f"[待办进度] {done}/{total} 项完成 | [文件暂存架] {files_cnt} 个文件{top_str}"
                )
            except Exception:
                pass

    def refresh_wallpaper_tool(self):
        if not hasattr(self, "wallpaper_enabled_check"):
            return
        schedule = wallpaper_schedule_settings()
        self.wallpaper_enabled_check.blockSignals(True)
        self.wallpaper_enabled_check.setChecked(bool(schedule.get("enabled")))
        self.wallpaper_enabled_check.blockSignals(False)
        self.wallpaper_status_label.setText(
            self.tr("tools_wallpaper_status_on")
            if schedule.get("enabled")
            else self.tr("tools_wallpaper_status_off")
        )
        for slot in schedule.get("slots", []):
            card = self.wallpaper_slot_cards.get(slot.get("id"))
            if card is not None:
                card.refresh(slot)

    def toggle_wallpaper_schedule(self, enabled):
        set_wallpaper_schedule_enabled(enabled)
        self.refresh_wallpaper_tool()

    def choose_wallpaper_slot_image(self, slot_id, path=None):
        if path is None:
            path, _ = QFileDialog.getOpenFileName(
                self,
                self.tr("tools_wallpaper_choose"),
                str(Path.home()),
                "Images (*.png *.jpg *.jpeg *.webp *.bmp)",
            )
        if not path:
            return

        image_path = Path(path)
        if not image_path.is_file() or image_path.suffix.lower() not in SUPPORTED_WALLPAPER_EXTENSIONS:
            QMessageBox.information(self, self.tr("tools_wallpaper"), self.tr("tools_wallpaper_invalid"))
            return
        if set_wallpaper_slot_path(slot_id, image_path):
            self.refresh_wallpaper_tool()

    def require_tool_window(self):
        window = self.selected_tool_window()
        if window is None:
            QMessageBox.information(self, self.tr("search_tab"), self.tr("tools_status_no_pet"))
            return None
        self.selected_window = window
        return window

    def start_tool_repeat_reminder(self):
        window = self.require_tool_window()
        if window is None:
            return
        window.set_repeating_reminder(self.tool_repeat_minutes.value())
        self.update_tool_statuses()
        self.refresh_schedule()

    def stop_tool_repeat_reminder(self):
        window = self.require_tool_window()
        if window is None:
            return
        window.cancel_repeating_reminder()
        self.update_tool_statuses()
        self.refresh_schedule()

    def start_tool_timer(self, minutes, focus_mode):
        window = self.require_tool_window()
        if window is None:
            return
        window.start_preset_timer(int(minutes) * 60, focus_mode)
        self.update_tool_statuses()
        self.refresh_schedule()

    def toggle_tool_timer(self):
        window = self.require_tool_window()
        if window is None:
            return
        window.start_or_pause_timer()
        self.update_tool_statuses()
        self.refresh_schedule()

    def reset_tool_timer(self):
        window = self.require_tool_window()
        if window is None:
            return
        window.reset_timer()
        self.update_tool_statuses()
        self.refresh_schedule()

    def save_tool_memo(self):
        window = self.require_tool_window()
        if window is None:
            return
        window.memo_text = self.tool_memo_text.toPlainText().strip()[:220]
        window.memo_visible = bool(window.memo_text)
        if not window.memo_text:
            window.memo_checked = False
        window.apply_scale()
        window.update()
        save_config()
        self.update_tool_statuses()
        self.refresh_schedule()

    def toggle_tool_memo(self):
        window = self.require_tool_window()
        if window is None:
            return
        if not getattr(window, "memo_text", ""):
            self.save_tool_memo()
            return
        window.toggle_memo_visible()
        self.update_tool_statuses()
        self.refresh_schedule()

    def complete_tool_memo(self):
        window = self.require_tool_window()
        if window is None:
            return
        if self.tool_memo_text.toPlainText().strip() and not getattr(window, "memo_text", ""):
            self.save_tool_memo()
        window.complete_current_task()
        self.update_tool_statuses()
        self.refresh_schedule()

    def clear_tool_memo(self):
        window = self.require_tool_window()
        if window is None:
            return
        window.clear_memo()
        if hasattr(self, "tool_memo_text"):
            self.tool_memo_text.clear()
        self.update_tool_statuses()
        self.refresh_schedule()

    def open_notchnotes_from_panel(self):
        window = self.current_tool_target_window()
        if window is not None and hasattr(window, "toggle_notchnotes"):
            window.toggle_notchnotes()
        else:
            from .notchnotes_window import NotchNotesWindow
            from .notchnotes_store import NotchNotesStore
            if not hasattr(self, "_standalone_notchnotes") or self._standalone_notchnotes is None:
                self._standalone_notchnotes = NotchNotesWindow(store=NotchNotesStore.get_instance())
            self._standalone_notchnotes.show()
            self._standalone_notchnotes.raise_()
            self._standalone_notchnotes.activateWindow()

    def play_tool_reward(self):
        window = self.require_tool_window()
        if window is None:
            return
        window.trigger_reward("tool")
        self.update_tool_statuses()

    def build_medals_tab(self):
        tab = QWidget()
        page = QVBoxLayout(tab)
        page.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        page.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        header = QFrame()
        header.setObjectName("MedalHeaderCard")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(22, 18, 22, 18)
        header_layout.setSpacing(16)

        title_box = QVBoxLayout()
        title_box.setSpacing(5)
        self.medals_title_label = QLabel(self.tr("medals_title"))
        self.medals_title_label.setObjectName("MedalPageTitle")
        self.medals_subtitle_label = QLabel(self.tr("medals_subtitle"))
        self.medals_subtitle_label.setObjectName("MedalPageSubtitle")
        self.medals_subtitle_label.setWordWrap(True)
        title_box.addWidget(self.medals_title_label)
        title_box.addWidget(self.medals_subtitle_label)

        action_box = QVBoxLayout()
        action_box.setSpacing(8)
        self.medals_summary_label = QLabel()
        self.medals_summary_label.setObjectName("MedalSummary")
        self.medals_summary_label.setAlignment(Qt.AlignCenter)
        self.medals_hide_button = QPushButton(self.tr("medals_hide"))
        self.medals_hide_button.setObjectName("MedalSecondaryButton")
        self.medals_hide_button.clicked.connect(lambda: self.set_medals_hidden(True))
        action_box.addWidget(self.medals_summary_label)
        action_box.addWidget(self.medals_hide_button)

        header_layout.addLayout(title_box, 1)
        header_layout.addLayout(action_box)
        layout.addWidget(header)

        self.medals_note_label = QLabel(self.tr("medals_note"))
        self.medals_note_label.setObjectName("MedalNote")
        self.medals_note_label.setWordWrap(True)
        layout.addWidget(self.medals_note_label)

        self.medal_grid_widget = QWidget()
        self.medal_grid_widget.setObjectName("MedalGrid")
        medal_grid = QGridLayout(self.medal_grid_widget)
        medal_grid.setContentsMargins(0, 0, 0, 0)
        medal_grid.setHorizontalSpacing(12)
        medal_grid.setVerticalSpacing(12)
        self.medal_cards = []
        for index, _medal in enumerate(self.medal_store.snapshot(self.language)):
            card = QFrame()
            card.setObjectName("MedalCard")
            card.setMinimumHeight(108)
            card_layout = QHBoxLayout(card)
            card_layout.setContentsMargins(14, 12, 14, 12)
            card_layout.setSpacing(12)

            icon_label = QLabel()
            icon_label.setObjectName("MedalIcon")
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setFixedSize(46, 46)

            copy_box = QVBoxLayout()
            copy_box.setSpacing(3)
            title_label = QLabel()
            title_label.setObjectName("MedalCardTitle")
            detail_label = QLabel()
            detail_label.setObjectName("MedalCardDetail")
            detail_label.setWordWrap(True)
            status_label = QLabel()
            status_label.setObjectName("MedalStatus")
            copy_box.addWidget(title_label)
            copy_box.addWidget(detail_label, 1)
            copy_box.addWidget(status_label)

            card_layout.addWidget(icon_label, 0, Qt.AlignTop)
            card_layout.addLayout(copy_box, 1)
            medal_grid.addWidget(card, index // 3, index % 3)
            self.medal_cards.append(
                {
                    "card": card,
                    "icon": icon_label,
                    "title": title_label,
                    "detail": detail_label,
                    "status": status_label,
                }
            )
        layout.addWidget(self.medal_grid_widget)

        self.medals_hidden_card = QFrame()
        self.medals_hidden_card.setObjectName("MedalHiddenCard")
        hidden_layout = QVBoxLayout(self.medals_hidden_card)
        hidden_layout.setContentsMargins(28, 34, 28, 34)
        hidden_layout.setSpacing(10)
        self.medals_hidden_title_label = QLabel(self.tr("medals_hidden_title"))
        self.medals_hidden_title_label.setObjectName("MedalHiddenTitle")
        self.medals_hidden_title_label.setAlignment(Qt.AlignCenter)
        self.medals_hidden_note_label = QLabel(self.tr("medals_hidden_note"))
        self.medals_hidden_note_label.setObjectName("MedalHiddenNote")
        self.medals_hidden_note_label.setAlignment(Qt.AlignCenter)
        self.medals_hidden_note_label.setWordWrap(True)
        self.medals_restore_button = QPushButton(self.tr("medals_restore"))
        self.medals_restore_button.setObjectName("MedalSecondaryButton")
        self.medals_restore_button.clicked.connect(lambda: self.set_medals_hidden(False))
        hidden_layout.addWidget(self.medals_hidden_title_label)
        hidden_layout.addWidget(self.medals_hidden_note_label)
        hidden_layout.addWidget(self.medals_restore_button, 0, Qt.AlignHCenter)
        layout.addWidget(self.medals_hidden_card)
        layout.addStretch(1)

        self.medals_tab_index = self.tabs.addTab(tab, self.tr("medals_tab"), "medals")
        self.refresh_medals_page()

    def set_medals_hidden(self, hidden):
        self.medal_store.set_hidden(hidden)
        self.refresh_medals_page()

    def refresh_medals_page(self):
        if not hasattr(self, "medal_cards"):
            return
        snapshot = self.medal_store.snapshot(self.language)
        unlocked = sum(1 for medal in snapshot if medal["unlocked"])
        self.medals_summary_label.setText(
            self.tr("medals_summary", unlocked=unlocked, total=len(snapshot))
        )
        for widgets, medal in zip(self.medal_cards, snapshot):
            card = widgets["card"]
            card.setProperty("unlocked", medal["unlocked"])
            if medal["unlocked"]:
                gold_path = resource_path("assets/UiAssets/medal-trophy-gold.png")
                gold_pix = QPixmap(str(gold_path)) if gold_path.exists() else QPixmap()
                if not gold_pix.isNull():
                    widgets["icon"].setPixmap(gold_pix.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                else:
                    widgets["icon"].setText(medal["icon"])
            else:
                widgets["icon"].setText("🔒")
            widgets["title"].setText(medal["title"])
            widgets["detail"].setText(medal["detail"])
            widgets["status"].setText(medal["status"])
            card.style().unpolish(card)
            card.style().polish(card)

        hidden = self.medal_store.hidden
        self.medal_grid_widget.setVisible(not hidden)
        self.medals_note_label.setVisible(not hidden)
        self.medals_hide_button.setVisible(not hidden)
        self.medals_hidden_card.setVisible(hidden)

    def all_pet_assets(self):
        try:
            return assets_for_pack(state.ASSETS_DIR)
        except OSError as exc:
            log_warning("Unable to list pet assets: %s", exc)
            return []

    def sync_unlock_state(self):
        self.unlock_state = ensure_pet_unlock_state(self.all_pet_assets(), grant_login_pets=False)
        self.activity_egg_count = self.unlock_state["egg_chances"]
        self.activity_claimed_codes = set(self.unlock_state["claimed_invite_codes"])
        self.activity_rewards = list(self.unlock_state["history"])
        return self.unlock_state

    def grant_login_pets_if_needed(self):
        assets = self.all_pet_assets()
        self.unlock_state = ensure_pet_unlock_state(assets, grant_login_pets=True)
        state.PET_UNLOCKS = self.unlock_state
        self.save_unlock_state()
        return len(assets)

    def open_account_dialog(self):
        self.sync_unlock_state()
        dialog = AccountDialog(logged_in_account(self.unlock_state), self)
        if dialog.exec() != QDialog.Accepted:
            return False
        self.unlock_state["account"] = dialog.account_data()
        self.unlock_state["initialized"] = True
        state.PET_UNLOCKS = self.unlock_state
        self.grant_login_pets_if_needed()
        self.refresh_packs()
        self.refresh_active()
        self.refresh_account_status()

        if not state.WINDOWS:
            assets = self.all_pet_assets()
            unlocked = [asset for asset in assets if is_asset_unlocked(asset, assets)]
            if unlocked:
                window = add_window(unlocked[0].path)
                if window is not None:
                    self.select_window_silently(window)

        QMessageBox.information(self, "登录", "登录成功。所有角色已免费开放。")
        return True

    def on_character_installed(self, installed=None):
        self.refresh_packs()
        if installed is not None:
            self.select_imported_library_item(installed)

    def open_doubao_guide(self):
        guide_root = ensure_ai_authoring_guide(BASE_DIR)
        dialog = DoubaoGuideDialog(
            build_doubao_prompt(guide_root.parent, state.ASSETS_DIR),
            state.ASSETS_DIR,
            self.on_character_installed,
            self,
        )
        dialog.exec()

    def open_redeem_character(self):
        self.sync_unlock_state()
        account = logged_in_account(self.unlock_state)
        if not account:
            if not self.open_account_dialog():
                return
            account = logged_in_account(self.unlock_state)
        token = str((account or {}).get("token") or "").strip()
        if not token:
            QMessageBox.information(self, "兑换角色", "当前登录状态已失效，请重新登录后再兑换。")
            return
        dialog = RedeemCharacterDialog(
            token,
            state.ASSETS_DIR,
            self.on_character_installed,
            self,
        )
        dialog.exec()

    def refresh_account_status(self):
        if not hasattr(self, "login_paw_button"):
            return
        account = logged_in_account(self.unlock_state)
        if account:
            account_name = str(account.get("name") or account.get("email") or "账号").strip()
            self.login_paw_button.set_account_label("已登录")
            self.login_paw_button.setToolTip(f"{account_name} 已登录")
        else:
            self.login_paw_button.set_account_label("登录")
            self.login_paw_button.setToolTip("登录 / 注册")

    def save_unlock_state(self):
        assets = self.all_pet_assets()
        self.unlock_state["all_unlocked"] = True
        self.unlock_state["unlocked_asset_ids"] = [asset.id for asset in assets]
        self.unlock_state["egg_chances"] = 0
        self.activity_egg_count = 0
        self.unlock_state["claimed_invite_codes"] = sorted(self.activity_claimed_codes)
        self.unlock_state["history"] = list(self.activity_rewards[:12])
        state.PET_UNLOCKS = normalize_pet_unlocks(self.unlock_state)
        self.unlock_state = state.PET_UNLOCKS
        save_config()

    def unlocked_asset_ids(self):
        return set(self.unlock_state.get("unlocked_asset_ids") or [])

    def locked_assets(self):
        unlocked = self.unlocked_asset_ids()
        if self.unlock_state.get("all_unlocked"):
            return []
        return [asset for asset in self.all_pet_assets() if asset.id not in unlocked]

    def unlock_all_pets(self, reason=None):
        assets = self.all_pet_assets()
        self.unlock_state["all_unlocked"] = True
        self.unlock_state["unlocked_asset_ids"] = [asset.id for asset in assets]
        if reason:
            self.activity_rewards.insert(0, f"{datetime.now().strftime('%H:%M')}  {reason}")
            self.activity_rewards = self.activity_rewards[:12]
        self.save_unlock_state()
        self.refresh_library()

    def maybe_unlock_all_from_progress(self):
        return False

    def refresh_launch_mission_completion(self):
        self.unlock_state["mission_completed"] = True
        return True

    def unlock_random_pet_from_egg(self):
        self.unlock_all_pets()
        return None

    def add_activity_history(self, message):
        timestamp = datetime.now().strftime("%H:%M")
        self.activity_rewards.insert(0, f"{timestamp}  {message}")
        self.activity_rewards = self.activity_rewards[:12]
        self.save_unlock_state()

    def build_schedule_tab(self):
        tab = QWidget()
        page = QVBoxLayout(tab)
        page.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        page.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)
        title_box = QVBoxLayout()
        title_box.setContentsMargins(0, 0, 0, 0)
        title_box.setSpacing(4)
        self.schedule_title = QLabel()
        self.schedule_title.setObjectName("SectionTitle")
        self.schedule_subtitle = QLabel()
        self.schedule_subtitle.setObjectName("SubtleLabel")
        self.schedule_subtitle.setWordWrap(True)
        title_box.addWidget(self.schedule_title)
        title_box.addWidget(self.schedule_subtitle)
        self.schedule_today_badge = QLabel()
        self.schedule_today_badge.setObjectName("StatusPill")
        header_row.addLayout(title_box, 1)
        header_row.addWidget(self.schedule_today_badge, 0, Qt.AlignTop)
        layout.addLayout(header_row)

        row = QHBoxLayout()
        row.setSpacing(14)

        calendar_panel = QFrame()
        calendar_panel.setObjectName("ScheduleCalendarPanel")
        calendar_layout = QVBoxLayout(calendar_panel)
        calendar_layout.setContentsMargins(20, 20, 20, 20)
        calendar_layout.setSpacing(12)
        calendar_top = QHBoxLayout()
        calendar_top.setSpacing(10)
        self.schedule_calendar_label = QLabel()
        self.schedule_calendar_label.setObjectName("ActivityCardTitle")
        self.schedule_running_badge = QLabel()
        self.schedule_running_badge.setObjectName("ActivityBadge")
        calendar_top.addWidget(self.schedule_calendar_label)
        calendar_top.addStretch(1)
        calendar_top.addWidget(self.schedule_running_badge)
        self.schedule_calendar = SoftCalendarWidget()
        self.schedule_calendar.setGridVisible(False)
        self.schedule_calendar.setMinimumWidth(410)
        self.schedule_calendar.setMinimumHeight(380)
        calendar_layout.addLayout(calendar_top)
        calendar_layout.addWidget(self.schedule_calendar, 1)

        summary_panel = QFrame()
        summary_panel.setObjectName("SchedulePanel")
        summary_layout = QVBoxLayout(summary_panel)
        summary_layout.setContentsMargins(20, 20, 20, 20)
        summary_layout.setSpacing(12)
        summary_top = QHBoxLayout()
        summary_top.setSpacing(10)
        self.schedule_summary_label = QLabel()
        self.schedule_summary_label.setObjectName("ActivityCardTitle")
        self.schedule_actions_label = QLabel()
        self.schedule_actions_label.setObjectName("ActivityBadge")
        summary_top.addWidget(self.schedule_summary_label)
        summary_top.addStretch(1)
        summary_top.addWidget(self.schedule_actions_label)
        self.schedule_list = QListWidget()
        self.schedule_list.setObjectName("ScheduleReminderList")
        self.schedule_list.setSpacing(6)
        self.schedule_list.setWordWrap(True)
        self.schedule_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.schedule_open_calendar_button = QPushButton()
        self.schedule_edit_memo_button = QPushButton()
        self.schedule_repeat_button = QPushButton()
        self.schedule_open_calendar_button.setObjectName("ToolPrimaryButton")
        self.schedule_open_calendar_button.clicked.connect(self.open_selected_pet_calendar)
        self.schedule_edit_memo_button.clicked.connect(self.edit_selected_pet_memo)
        self.schedule_repeat_button.clicked.connect(self.configure_selected_pet_repeat)
        schedule_buttons = QHBoxLayout()
        schedule_buttons.setSpacing(8)
        schedule_buttons.addWidget(self.schedule_open_calendar_button)
        schedule_buttons.addWidget(self.schedule_edit_memo_button)
        schedule_buttons.addWidget(self.schedule_repeat_button)
        schedule_buttons.addStretch(1)
        summary_layout.addLayout(summary_top)
        summary_layout.addWidget(self.schedule_list, 1)
        summary_layout.addLayout(schedule_buttons)

        row.addWidget(calendar_panel, 9)
        row.addWidget(summary_panel, 11)
        layout.addLayout(row, 1)
        self.schedule_tab_index = self.tabs.addTab(tab, self.tr("schedule_tab"), "schedule")

    def panel(self):
        frame = QFrame()
        frame.setObjectName("Panel")
        frame.setFrameShape(QFrame.NoFrame)
        return frame

    def build_library_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        self.library_title = QLabel()
        self.library_title.setObjectName("SectionTitle")
        self.library_subtitle = QLabel()
        self.library_subtitle.setObjectName("SubtleLabel")
        title_box.addWidget(self.library_title)
        title_box.addWidget(self.library_subtitle)

        self.pack_combo = QComboBox()
        self.pack_combo.currentIndexChanged.connect(self.refresh_library)

        header.addLayout(title_box, 1)
        self.library_pack_label = QLabel()
        header.addWidget(self.library_pack_label)
        header.addWidget(self.pack_combo)

        root_row = QHBoxLayout()
        self.asset_root_label = QLabel()
        self.asset_root_label.setObjectName("SubtleLabel")
        self.library_change_root_button = QPushButton()
        self.library_change_root_button.clicked.connect(self.change_asset_root)
        root_row.addWidget(self.asset_root_label, 1)
        root_row.addWidget(self.library_change_root_button)

        self.library_list = QListWidget()
        self.library_list.setObjectName("PetLibraryList")
        self.library_list.setViewMode(QListView.IconMode)
        self.library_list.setMovement(QListView.Static)
        self.library_list.setResizeMode(QListView.Adjust)
        self.library_list.setIconSize(THUMBNAIL_SIZE)
        self.library_list.setGridSize(QSize(128, 132))
        self.library_list.setSpacing(8)
        self.library_list.setUniformItemSizes(True)
        self.library_list.setItemDelegate(PetLibraryItemDelegate(self.library_list))
        self.library_list.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.library_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.library_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.library_list.itemDoubleClicked.connect(lambda item: self.add_selected_library_asset())
        self.library_list.customContextMenuRequested.connect(self.open_library_menu)

        buttons = QHBoxLayout()
        self.library_import_button = QPushButton()
        self.library_import_folder_button = QPushButton()
        self.library_configure_button = QPushButton()
        self.library_add_button = QPushButton()
        self.library_import_button.clicked.connect(self.import_asset)
        self.library_import_folder_button.clicked.connect(self.import_folder)
        self.library_configure_button.clicked.connect(self.configure_selected_library_asset)
        self.library_add_button.clicked.connect(self.add_selected_library_asset)
        buttons.addWidget(self.library_import_button)
        buttons.addWidget(self.library_import_folder_button)
        buttons.addStretch()
        buttons.addWidget(self.library_configure_button)
        buttons.addWidget(self.library_add_button)

        layout.addLayout(header)
        layout.addLayout(root_row)
        layout.addWidget(self.library_list, 1)
        layout.addLayout(buttons)
        self.pets_tab_index = self.tabs.addTab(tab, self.tr("pets_tab"), "assets")

    def build_active_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.active_title = QLabel()
        self.active_title.setObjectName("SectionTitle")
        self.active_subtitle = QLabel()
        self.active_subtitle.setObjectName("SubtleLabel")

        self.active_list = QListWidget()
        self.active_list.setIconSize(QSize(56, 56))
        self.active_list.setSpacing(6)
        self.active_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.active_list.itemDoubleClicked.connect(lambda item: self.select_active())
        self.active_list.customContextMenuRequested.connect(self.open_active_menu)

        buttons = QHBoxLayout()
        self.active_select_button = QPushButton()
        self.active_configure_button = QPushButton()
        self.active_close_button = QPushButton()
        self.active_lock_button = QPushButton()
        self.active_hide_all_button = QPushButton()
        self.active_show_all_button = QPushButton()

        self.active_select_button.clicked.connect(self.select_active)
        self.active_configure_button.clicked.connect(self.configure_active_asset)
        self.active_close_button.clicked.connect(self.close_active)
        self.active_lock_button.clicked.connect(self.toggle_active_lock)
        self.active_hide_all_button.clicked.connect(self.hide_all_overlays)
        self.active_show_all_button.clicked.connect(self.show_all_overlays)

        buttons.addWidget(self.active_select_button)
        buttons.addWidget(self.active_configure_button)
        buttons.addWidget(self.active_lock_button)
        buttons.addWidget(self.active_close_button)
        buttons.addStretch()
        buttons.addWidget(self.active_hide_all_button)
        buttons.addWidget(self.active_show_all_button)

        self.recovery_group = QGroupBox()
        recovery_layout = QVBoxLayout(self.recovery_group)
        recovery_layout.setContentsMargins(14, 18, 14, 14)
        recovery_layout.setSpacing(8)

        recovery_row_one = QHBoxLayout()
        self.recovery_center_all_button = QPushButton()
        self.recovery_disable_click_button = QPushButton()
        self.recovery_unlock_all_button = QPushButton()
        self.recovery_center_all_button.clicked.connect(self.bring_all_overlays_to_center)
        self.recovery_disable_click_button.clicked.connect(self.disable_click_through_for_all)
        self.recovery_unlock_all_button.clicked.connect(self.unlock_all_overlays)
        recovery_row_one.addWidget(self.recovery_center_all_button)
        recovery_row_one.addWidget(self.recovery_disable_click_button)
        recovery_row_one.addWidget(self.recovery_unlock_all_button)

        recovery_row_two = QHBoxLayout()
        self.recovery_show_button = QPushButton()
        self.recovery_hide_button = QPushButton()
        self.recovery_clear_button = QPushButton()
        self.recovery_show_button.clicked.connect(self.show_all_overlays)
        self.recovery_hide_button.clicked.connect(self.hide_all_overlays)
        self.recovery_clear_button.clicked.connect(self.clear_saved_session)
        recovery_row_two.addWidget(self.recovery_show_button)
        recovery_row_two.addWidget(self.recovery_hide_button)
        recovery_row_two.addWidget(self.recovery_clear_button)

        recovery_layout.addLayout(recovery_row_one)
        recovery_layout.addLayout(recovery_row_two)

        self.startup_check = QCheckBox("开机自动启动")
        self.startup_check.setEnabled(False)
        if hasattr(self.startup_check, "setVisible"):
            import sys

            self.startup_check.setVisible(sys.platform == "win32")
            if sys.platform == "win32":
                self.startup_check.setEnabled(True)
                self.startup_check.setChecked(startup_enabled())
                self.startup_check.toggled.connect(set_startup_enabled)

        layout.addWidget(self.active_title)
        layout.addWidget(self.active_subtitle)
        layout.addWidget(self.active_list, 1)
        layout.addLayout(buttons)
        layout.addWidget(self.recovery_group)
        layout.addWidget(self.startup_check)
        self.running_tab_index = self.tabs.addTab(tab, self.tr("running_tab"), "running")

    def build_diagnostics_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.diagnostics_title = QLabel()
        self.diagnostics_title.setObjectName("SectionTitle")
        self.diagnostics_subtitle = QLabel()
        self.diagnostics_subtitle.setObjectName("SubtleLabel")

        info_panel = self.panel()
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(14, 14, 14, 14)
        info_layout.setSpacing(8)

        self.diagnostics_version = QLabel()
        self.diagnostics_config_path = QLabel()
        self.diagnostics_asset_root = QLabel()
        self.diagnostics_log_path = QLabel()
        self.diagnostics_overlay_count = QLabel()
        for label in (
            self.diagnostics_version,
            self.diagnostics_config_path,
            self.diagnostics_asset_root,
            self.diagnostics_log_path,
            self.diagnostics_overlay_count,
        ):
            label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            label.setWordWrap(True)
            label.hide()

        self.settings_health_summary = QLabel()
        self.settings_health_summary.setObjectName("SubtleLabel")
        self.settings_health_summary.setWordWrap(True)
        info_layout.addWidget(self.settings_health_summary)

        self.diagnostics_warnings_label = QLabel()
        self.diagnostics_warnings_label.setObjectName("SubtleLabel")
        self.diagnostics_recent = QTextEdit()
        self.diagnostics_recent.setReadOnly(True)
        self.diagnostics_recent.setMinimumHeight(160)
        self.diagnostics_recent.hide()

        buttons = QHBoxLayout()
        self.diagnostics_open_logs_button = QPushButton()
        self.diagnostics_copy_button = QPushButton()
        self.diagnostics_refresh_button = QPushButton()
        self.diagnostics_open_logs_button.clicked.connect(self.open_logs_folder)
        self.diagnostics_copy_button.clicked.connect(self.copy_diagnostics)
        self.diagnostics_refresh_button.clicked.connect(self.refresh_diagnostics)
        buttons.addWidget(self.diagnostics_open_logs_button)
        buttons.addWidget(self.diagnostics_copy_button)
        buttons.addStretch()
        buttons.addWidget(self.diagnostics_refresh_button)

        layout.addWidget(self.diagnostics_title)
        layout.addWidget(self.diagnostics_subtitle)
        layout.addWidget(info_panel)
        layout.addWidget(self.diagnostics_warnings_label)
        layout.addLayout(buttons)
        self.debug_tab_index = self.tabs.addTab(tab, self.tr("debug_tab"), "debug")

    def build_editor_tab(self):
        self.editor_tab = QWidget()
        layout = QVBoxLayout(self.editor_tab)
        layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        layout.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(14)

        self.editor_placeholder = QLabel("双击一个桌宠即可编辑")
        self.editor_placeholder.setObjectName("SubtleLabel")

        self.selected_group = QGroupBox("已选择素材")
        selected_layout = QVBoxLayout(self.selected_group)
        selected_layout.setContentsMargins(14, 18, 14, 14)
        selected_layout.setSpacing(6)
        self.editor_name = QLabel("双击一个桌宠即可编辑")
        self.editor_name.setObjectName("SubtleLabel")
        self.editor_type = QLabel("")
        self.editor_name.setObjectName("SubtleLabel")
        self.editor_type = QLabel("")
        self.editor_type.setObjectName("SubtleLabel")
        selected_layout.addWidget(self.editor_name)
        selected_layout.addWidget(self.editor_type)

        self.scale_label = QLabel("大小：50%")
        self.scale_slider = VibeSlider(Qt.Horizontal, unit="%", color_variant="coral")
        self.scale_slider.setRange(25, 500)
        self.scale_slider.setTickInterval(25)
        self.scale_slider.valueChanged.connect(self.editor_scale_changed)

        self.opacity_label = QLabel("透明度：100%")
        self.opacity_slider = VibeSlider(Qt.Horizontal, unit="%", color_variant="mint")
        self.opacity_slider.setRange(50, 100)
        self.opacity_slider.setTickInterval(10)
        self.opacity_slider.valueChanged.connect(self.editor_opacity_changed)

        self.speed_label = QLabel("速度：100%")
        self.speed_slider = VibeSlider(Qt.Horizontal, unit="%", color_variant="coral")
        self.speed_slider.setRange(25, 200)
        self.speed_slider.setTickInterval(25)
        self.speed_slider.valueChanged.connect(self.editor_speed_changed)

        self.transform_group = QGroupBox("外观调整")
        transform_layout = QVBoxLayout(self.transform_group)
        transform_layout.setContentsMargins(14, 18, 14, 14)
        transform_layout.setSpacing(12)
        transform_layout.addWidget(self.slider_row(self.scale_label, self.scale_slider))
        transform_layout.addWidget(self.slider_row(self.opacity_label, self.opacity_slider))
        self.speed_row = self.slider_row(self.speed_label, self.speed_slider)
        transform_layout.addWidget(self.speed_row)

        self.top_check = QCheckBox("保持在最前面")
        self.click_check = QCheckBox("点击穿透")
        self.lock_check = QCheckBox("锁定位置")
        self.top_check.toggled.connect(self.editor_top_changed)
        self.click_check.toggled.connect(self.editor_click_changed)
        self.lock_check.toggled.connect(self.editor_lock_changed)

        self.reload_button = QPushButton("重新加载素材")
        self.reload_button.clicked.connect(self.reload_selected_asset)

        self.behavior_group = QGroupBox("行为")
        behavior_layout = QVBoxLayout(self.behavior_group)
        behavior_layout.setContentsMargins(14, 18, 14, 14)
        behavior_layout.setSpacing(10)
        behavior_layout.addWidget(self.top_check)
        behavior_layout.addWidget(self.click_check)
        behavior_layout.addWidget(self.lock_check)
        behavior_layout.addWidget(self.reload_button)

        self.spritesheet_group = QGroupBox("精灵表控制")
        self.spritesheet_layout = QVBoxLayout(self.spritesheet_group)
        self.spritesheet_layout.setContentsMargins(14, 18, 14, 14)
        self.spritesheet_layout.setSpacing(10)

        self.composite_group = QGroupBox("组合层数值")
        self.composite_layout = QVBoxLayout(self.composite_group)
        self.composite_layout.setContentsMargins(14, 18, 14, 14)
        self.composite_layout.setSpacing(12)

        content_layout.addWidget(self.editor_placeholder)
        content_layout.addWidget(self.selected_group)
        content_layout.addWidget(self.transform_group)
        content_layout.addWidget(self.behavior_group)
        content_layout.addWidget(self.spritesheet_group)
        content_layout.addWidget(self.composite_group)
        content_layout.addStretch()
        self.editor_tab_index = self.tabs.addTab(self.editor_tab, self.tr("inspector_tab"), "editor")

    def slider_row(self, value_label, slider):
        row = QWidget()
        layout = QVBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        value_label.setMinimumWidth(120)
        layout.addWidget(value_label)
        layout.addWidget(slider)
        return row

    def on_library_selection_changed(self, current, previous):
        self.refresh_overview_selection()

    def selected_library_asset(self):
        path = self.library_path_from_current_item()
        if path is None:
            return None
        return detect_asset(path)

    def running_window_for_asset(self, asset):
        if asset is None:
            return None
        asset_path = Path(asset.path).resolve()
        return next((window for window in state.WINDOWS if Path(window.asset_path).resolve() == asset_path), None)

    def preview_pixmap_for_asset(self, asset):
        if asset is None:
            return QPixmap()

        preview_path = asset.preview_path or asset.path
        reader = QImageReader(str(preview_path))
        reader.setAutoTransform(True)
        image = reader.read()
        if not image.isNull():
            return QPixmap.fromImage(image)

        movie = QMovie(str(preview_path))
        movie.start()
        QApplication.processEvents()
        pixmap = movie.currentPixmap()
        movie.stop()
        return pixmap

    def toggle_summon_current_pet(self):
        asset = self.selected_library_asset()
        if asset is None:
            return
        running = self.running_window_for_asset(asset)
        if running is not None:
            running.show()
            running.raise_()
            running.activateWindow()
        else:
            self.add_selected_library_asset()
            self.refresh_overview_selection()

    def refresh_overview_selection(self):
        if not hasattr(self, "overview_preview_media"):
            return

        current_item = self.library_list.currentItem() if hasattr(self, "library_list") else None
        action = str(current_item.data(LIBRARY_ACTION_ROLE) or "") if current_item is not None else ""
        if action:
            if hasattr(self, "pet_control_card"):
                self.pet_control_card.hide()
            if action == "doubao":
                self.overview_preview_media.setActionHint(
                    "doubao",
                    "豆包生成",
                    "复制写好的提示词，让豆包直接把完整角色包生成到本软件角色库。",
                )
            else:
                self.overview_preview_media.setActionHint(
                    "redeem",
                    "兑换角色",
                    "登录后输入兑换码，校验云端角色包并安全导入角色库。",
                )
            return

        asset = self.selected_library_asset()
        if hasattr(self, "pet_control_card"):
            self.pet_control_card.show()
            if asset is not None:
                pet_name = getattr(asset, "title", None) or Path(asset.path).name.replace("Pet", "")
                self.overview_pet_name_label.setText(pet_name)
                running = self.running_window_for_asset(asset)
                if running is not None:
                    self.overview_pet_status_badge.setText("● 桌面运行中")
                    self.overview_pet_status_badge.setStyleSheet("color: #059669; background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 10px; padding: 2px 10px; font-weight: bold;")
                else:
                    self.overview_pet_status_badge.setText("○ 待命准备中")
                    self.overview_pet_status_badge.setStyleSheet("color: #64748b; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 10px; padding: 2px 10px;")

        if asset is None:
            self.overview_preview_media.setText("")
            self.overview_preview_media.clearPetPixmap()
            return

        if self.current_library_item_locked():
            locked_path = self.locked_card_image_path(asset)
            locked_pixmap = QPixmap(str(locked_path)) if locked_path.exists() else QPixmap()
            self.overview_preview_media.setLockedPixmap(locked_pixmap)
            self.overview_preview_media.setText("")
            if hasattr(self, "pet_control_card"):
                self.pet_control_card.hide()
            return

        self.overview_preview_media.setPetAsset(asset)
        self.overview_preview_media.setText("")

    def show_editor_tab(self):
        self.tabs.setCurrentIndex(getattr(self, "overview_tab_index", 0))

    def hide_editor_tab(self):
        self.tabs.setCurrentIndex(getattr(self, "overview_tab_index", 0))

    def refresh_overview(self):
        if not hasattr(self, "overview_title"):
            return

        self.refresh_overview_selection()

    def update_status_text(self, manifest_url=None):
        manifest_url = update_manifest_url() if manifest_url is None else manifest_url
        data = self.update_manifest_data or {}
        remote_version = str(data.get("version") or "").strip()
        if remote_version and is_newer_version(remote_version):
            return f"发现更新 v{remote_version} · 重启生效"
        if data:
            return self.tr("manifest_read")
        return self.tr("manifest_configured") if manifest_url else self.tr("manifest_unconfigured")

    def refresh_updates_page(self):
        if not hasattr(self, "update_current_version_label"):
            return

        manifest_url = update_manifest_url()
        site_url = official_site_url()
        self.update_current_version_label.setText(f"v{__version__}")
        self.update_site_url_label.setText(site_url or self.tr("not_configured"))
        self.update_manifest_url_label.setText(manifest_url or self.tr("not_configured"))

        data = self.update_manifest_data or {}
        if data:
            if hasattr(self, "auto_update_check"):
                self.auto_update_check.blockSignals(True)
                self.auto_update_check.setChecked(auto_update_check_enabled())
                self.auto_update_check.blockSignals(False)
            self.update_remote_version_label.setText(data.get("version") or self.tr("missing_version"))
            self.update_package_url_label.setText(data.get("package_url") or self.tr("missing_package"))
            self.update_sha256_label.setText(data.get("sha256") or self.tr("no_sha"))
            self.update_status_label.setText(data.get("status") or self.tr("manifest_loaded"))
            self.update_notes.setPlainText(data.get("release_notes") or self.tr("no_release_notes"))
            return

        self.update_remote_version_label.setText(self.tr("not_checked"))
        self.update_package_url_label.setText(self.tr("not_checked"))
        self.update_sha256_label.setText(self.tr("not_checked"))
        if hasattr(self, "auto_update_check"):
            self.auto_update_check.blockSignals(True)
            self.auto_update_check.setChecked(auto_update_check_enabled())
            self.auto_update_check.blockSignals(False)
        self.update_status_label.setText(self.tr("update_hint"))
        self.update_notes.setPlainText(self.tr("waiting_manifest"))

    def inspect_update_manifest(self):
        manifest_url = update_manifest_url()
        if not manifest_url:
            return {"status": "update_config.json 缺少 manifest_url"}

        try:
            manifest = fetch_json(manifest_url)
        except Exception as exc:
            log_warning("Unable to inspect update manifest: %s", exc)
            return {"status": f"读取 manifest 失败：{exc}", "manifest_url": manifest_url}

        if not isinstance(manifest, dict):
            return {"status": "manifest 格式错误：顶层必须是 JSON 对象", "manifest_url": manifest_url}

        remote_version = str(manifest.get("version") or "").strip()
        package_url = str(manifest.get("package_url") or "").strip()
        sha256 = str(manifest.get("sha256") or "").strip()
        release_notes = str(manifest.get("release_notes") or "").strip()
        missing = [name for name, value in (("version", remote_version), ("package_url", package_url)) if not value]
        if missing:
            status = "manifest 缺少：" + ", ".join(missing)
        elif is_newer_version(remote_version):
            status = f"发现新版本 v{remote_version}"
        else:
            status = f"当前版本 v{__version__} 已不低于远程版本 v{remote_version}"

        return {
            "status": status,
            "version": remote_version,
            "package_url": package_url,
            "sha256": sha256,
            "release_notes": release_notes,
            "manifest_url": manifest_url,
        }

    def refresh_update_manifest(self):
        self.update_status_label.setText(self.tr("reading_manifest"))
        QApplication.processEvents()
        self.update_manifest_data = self.inspect_update_manifest()
        self.refresh_updates_page()
        self.refresh_overview()

    def copy_manifest_url(self):
        manifest_url = update_manifest_url()
        if not manifest_url:
            QMessageBox.information(self, "更新中心", "还没有配置 manifest_url。")
            return
        QApplication.clipboard().setText(manifest_url)

    def copy_package_url(self):
        package_url = str((self.update_manifest_data or {}).get("package_url") or "").strip()
        if not package_url:
            QMessageBox.information(self, "更新中心", "请先点击“只检查清单”，读取下载地址。")
            return
        QApplication.clipboard().setText(package_url)

    def selected_schedule_window(self):
        if not hasattr(self, "schedule_list"):
            return None
        item = self.schedule_list.currentItem()
        if item is None:
            return state.WINDOWS[0] if state.WINDOWS else None
        window_id = item.data(Qt.UserRole)
        return next((window for window in state.WINDOWS if id(window) == window_id), None)

    def refresh_schedule(self):
        if not hasattr(self, "schedule_list"):
            return
        if hasattr(self, "schedule_today_badge"):
            self.schedule_today_badge.setText(self.tr("schedule_today_badge", date=datetime.now().strftime("%Y-%m-%d")))
        if hasattr(self, "schedule_running_badge"):
            if state.WINDOWS:
                self.schedule_running_badge.setText(self.tr("schedule_running_badge", count=len(state.WINDOWS)))
            else:
                self.schedule_running_badge.setText(self.tr("schedule_empty_badge"))
        selected_id = None
        current = self.schedule_list.currentItem()
        if current is not None:
            selected_id = current.data(Qt.UserRole)
        self.schedule_list.clear()
        if not state.WINDOWS:
            item = QListWidgetItem(self.tr("schedule_empty"))
            item.setFlags(Qt.NoItemFlags)
            self.schedule_list.addItem(item)
            return
        for window in state.WINDOWS:
            lines = window.calendar_summary_lines() if hasattr(window, "calendar_summary_lines") else []
            title = getattr(getattr(window, "asset", None), "name", "桌宠")
            text = f"{title}\n" + "\n".join(lines[:4])
            item = QListWidgetItem(text.strip())
            item.setData(Qt.UserRole, id(window))
            self.schedule_list.addItem(item)
            if id(window) == selected_id:
                self.schedule_list.setCurrentItem(item)
        if self.schedule_list.currentRow() < 0:
            self.schedule_list.setCurrentRow(0)

    def open_selected_pet_calendar(self):
        window = self.selected_schedule_window()
        if window is not None and hasattr(window, "show_calendar_dialog"):
            window.show_calendar_dialog()

    def edit_selected_pet_memo(self):
        window = self.selected_schedule_window()
        if window is not None and hasattr(window, "edit_memo"):
            window.edit_memo()
            self.refresh_active()
            self.refresh_schedule()

    def configure_selected_pet_repeat(self):
        window = self.selected_schedule_window()
        if window is not None and hasattr(window, "configure_repeating_reminder"):
            window.configure_repeating_reminder()
            self.refresh_active()
            self.refresh_schedule()
            self.refresh_active()

    def show_search_page(self, query=""):
        if hasattr(self, "search_tab_index"):
            self.tabs.setCurrentIndex(self.search_tab_index)
        self.show()
        self.raise_()
        self.activateWindow()
        if query and hasattr(self, "search_input"):
            self.search_input.setText(str(query))
            self.run_local_search()
        elif hasattr(self, "search_input"):
            self.search_input.setFocus()

    def run_local_search(self):
        query = self.search_input.text().strip()
        mode = self.search_mode_combo.currentData() or "apps"
        if not query:
            self.set_search_results([], self.tr("search_empty"))
            return
        self.search_status_label.setText("搜索中...")
        QApplication.processEvents()
        results, source = search_local(query, mode=mode, limit=80)
        status = self.tr("search_status", source=source, count=len(results)) if results else self.tr("search_no_results")
        self.set_search_results(results, status)

    def set_search_results(self, results, status):
        self.search_results = list(results or [])
        while self.search_results_layout.count():
            item = self.search_results_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.search_status_label.setText(status)
        if not self.search_results:
            empty_panel = QWidget()
            empty_layout = QVBoxLayout(empty_panel)
            empty_layout.setAlignment(Qt.AlignCenter)
            empty_layout.setContentsMargins(0, 30, 0, 30)
            empty_layout.setSpacing(14)

            mascot_path = resource_path("assets/UiAssets/ui-empty-mascot.png")
            if mascot_path.exists():
                mascot_label = QLabel()
                mascot_pix = QPixmap(str(mascot_path)).scaled(240, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                mascot_label.setPixmap(mascot_pix)
                mascot_label.setAlignment(Qt.AlignCenter)
                empty_layout.addWidget(mascot_label)

            empty = QLabel(status if status else "输入关键词即可检索应用或文件，或者选择左侧其他实用功能~")
            empty.setObjectName("SubtleLabel")
            empty.setAlignment(Qt.AlignCenter)
            empty.setWordWrap(True)
            empty_layout.addWidget(empty)
            self.search_results_layout.addWidget(empty_panel, 1)
            return

        for result in self.search_results:
            self.search_results_layout.addWidget(self.search_result_card(result))
        self.search_results_layout.addStretch()

    def search_result_card(self, result):
        card = QFrame()
        card.setObjectName("SearchResultCard")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        icon_label = QLabel()
        icon_label.setPixmap(make_action_icon(self.search_result_icon(result)).pixmap(28, 28))
        icon_label.setFixedWidth(34)

        text_box = QVBoxLayout()
        text_box.setSpacing(2)
        name_label = QLabel(result.name)
        name_label.setObjectName("SectionTitle")
        path_label = QLabel(result.path)
        path_label.setObjectName("SearchPath")
        path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        path_label.setWordWrap(True)
        meta_parts = [result.kind]
        size = format_size(result.size)
        modified = format_modified(result.modified)
        if size:
            meta_parts.append(size)
        if modified:
            meta_parts.append(modified)
        if result.source:
            meta_parts.append(result.source)
        meta_label = QLabel("  ·  ".join(meta_parts))
        meta_label.setObjectName("SearchMeta")
        text_box.addWidget(name_label)
        text_box.addWidget(path_label)
        text_box.addWidget(meta_label)

        open_button = QPushButton(self.tr("open_result"))
        open_button.setIcon(make_action_icon("open"))
        open_button.clicked.connect(lambda _checked=False, path=result.path: self.open_search_result(path))
        parent_button = QPushButton(self.tr("open_parent"))
        parent_button.setIcon(make_action_icon("folder-up"))
        parent_button.clicked.connect(lambda _checked=False, path=result.path: self.open_search_result_parent(path))

        layout.addWidget(icon_label)
        layout.addLayout(text_box, 1)
        layout.addWidget(open_button)
        layout.addWidget(parent_button)
        return card

    def search_result_icon(self, result):
        if result.kind == "folder":
            return "folder"
        suffix = Path(result.path).suffix.lower()
        if suffix in {".exe", ".lnk", ".appref-ms", ".bat", ".cmd", ".ps1"}:
            return "app"
        return "file"

    def open_search_result(self, path):
        if not open_path(path):
            QMessageBox.warning(self, "本地搜索", "无法打开这个结果。")

    def open_search_result_parent(self, path):
        if not open_parent(path):
            QMessageBox.warning(self, "本地搜索", "无法定位这个结果。")

    def active_pack_dir(self):
        if hasattr(self, "pack_combo"):
            return Path(self.pack_combo.currentData() or state.ASSETS_DIR)
        return state.ASSETS_DIR

    def refresh_packs(self):
        if not hasattr(self, "pack_combo"):
            self.refresh_library()
            self.refresh_overview()
            return

        current = self.pack_combo.currentData()
        self.pack_combo.blockSignals(True)
        self.pack_combo.clear()

        for name, path in asset_packs():
            self.pack_combo.addItem(name, str(path))

        if current:
            index = self.pack_combo.findData(current)
            if index >= 0:
                self.pack_combo.setCurrentIndex(index)

        self.pack_combo.blockSignals(False)
        self.refresh_library()
        self.refresh_overview()

    def change_asset_root(self):
        path = QFileDialog.getExistingDirectory(self, "更换素材文件夹", str(state.ASSETS_DIR))
        if not path:
            return

        state.ASSETS_DIR = Path(path).resolve()
        state.ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        save_config()
        self.refresh_packs()

    def refresh_library(self):
        if not hasattr(self, "library_list"):
            return

        self.sync_unlock_state()
        previous_path = None
        current_item = self.library_list.currentItem()
        if current_item is not None and current_item.data(Qt.UserRole):
            previous_path = Path(current_item.data(Qt.UserRole)).resolve()
        self.library_list.clear()
        assets = assets_for_pack(self.active_pack_dir())
        selected_item = None
        first_unlocked_item = None
        if not assets:
            item = QListWidgetItem(self.tr("empty_library"))
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(Qt.NoItemFlags)
            self.library_list.addItem(item)

        for asset in assets:
            package_code = str((asset.metadata or {}).get("package_code") or "").strip()
            item = QListWidgetItem(make_thumbnail(asset), asset.name)
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
            item.setData(Qt.UserRole, str(asset.path))
            item.setData(LIBRARY_ASSET_ID_ROLE, asset.id)
            item.setData(LIBRARY_PACKAGE_CODE_ROLE, package_code)
            locked = not is_asset_unlocked(asset, assets)
            item.setData(LIBRARY_LOCKED_ROLE, locked)
            if locked:
                item.setData(LIBRARY_LOCK_IMAGE_ROLE, str(self.locked_card_image_path(asset)))
                item.setToolTip(self.tr("pet_locked_note"))
            else:
                item.setToolTip(asset.name)
                if first_unlocked_item is None:
                    first_unlocked_item = item
            self.library_list.addItem(item)
            if previous_path is not None and Path(asset.path).resolve() == previous_path:
                selected_item = item

        for label, action, tooltip in (
            ("豆包生成", "doubao", "让豆包直接把完整角色包生成到本软件角色库"),
            ("兑换角色", "redeem", "登录账号后，用兑换码从云端安全导入角色"),
        ):
            item = QListWidgetItem(label)
            item.setTextAlignment(Qt.AlignHCenter | Qt.AlignBottom)
            item.setData(LIBRARY_ACTION_ROLE, action)
            item.setData(LIBRARY_LOCKED_ROLE, False)
            item.setToolTip(tooltip)
            self.library_list.addItem(item)

        if selected_item is not None:
            self.library_list.setCurrentItem(selected_item)
        elif first_unlocked_item is not None:
            self.library_list.setCurrentItem(first_unlocked_item)
        elif self.library_list.count():
            first_item = self.library_list.item(0)
            if first_item is not None and first_item.data(Qt.UserRole):
                self.library_list.setCurrentItem(first_item)
        self.refresh_overview_selection()

    def refresh_active(self):
        selected_id = id(self.selected_window) if self.selected_window in state.WINDOWS else None
        self.active_list.clear()

        for window in state.WINDOWS:
            state_text = self.tr("locked") if window.locked else self.tr("unlocked")
            item = QListWidgetItem(make_thumbnail(window.asset), f"{window.asset.name}  -  {state_text}")
            item.setData(Qt.UserRole, id(window))
            self.active_list.addItem(item)
            if id(window) == selected_id:
                self.active_list.setCurrentItem(item)

        if self.selected_window not in state.WINDOWS:
            self.selected_window = None
            self.load_editor(None)
            self.hide_editor_tab()
        self.refresh_diagnostics()
        self.refresh_schedule()
        self.refresh_tool_target_combos()
        self.refresh_overview_selection()

    def refresh_diagnostics(self):
        if not hasattr(self, "diagnostics_recent"):
            return

        overlay_count = len(state.WINDOWS)
        self.diagnostics_version.setText(self.tr("diagnostics_version", version=__version__))
        self.diagnostics_config_path.setText(self.tr("diagnostics_config", path=CONFIG_PATH))
        self.diagnostics_asset_root.setText(self.tr("diagnostics_assets", path=state.ASSETS_DIR))
        self.diagnostics_log_path.setText(self.tr("diagnostics_log", path=LOG_PATH))
        self.diagnostics_overlay_count.setText(self.tr("diagnostics_count", count=overlay_count))

        recent = recent_warnings_and_errors()
        if recent:
            lines = [f"{item['level']}: {item['message']}" for item in recent[-30:]]
            self.diagnostics_recent.setPlainText("\n".join(lines))
            if hasattr(self, "settings_health_summary"):
                self.settings_health_summary.setText(f"最近有 {len(recent[-30:])} 条记录；复制反馈信息后可以发给我们排查。")
        else:
            self.diagnostics_recent.setPlainText(self.tr("diagnostics_empty"))
            if hasattr(self, "settings_health_summary"):
                self.settings_health_summary.setText(f"运行正常，当前有 {overlay_count} 个桌宠在桌面上。")
        if not self.applying_language:
            self.refresh_overview()
            self.refresh_updates_page()

    def diagnostics_text(self):
        recent = recent_warnings_and_errors()
        warnings = "\n".join(f"- {item['level']}: {item['message']}" for item in recent[-30:])
        if not warnings:
            warnings = "- 本次运行暂无记录。"
        return "\n".join(
            [
                f"{APP_DISPLAY_NAME} 版本：{__version__}",
                f"官网地址：{official_site_url() or '未配置'}",
                f"正在运行的桌宠数量：{len(state.WINDOWS)}",
                "最近状态：",
                warnings,
            ]
        )

    def open_logs_folder(self):
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
            if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(LOG_DIR))):
                raise OSError(f"Could not open {LOG_DIR}")
        except Exception as exc:
            log_warning("Unable to open logs folder: %s", exc)
            QMessageBox.warning(self, self.tr("debug_title"), "无法打开问题记录。")

    def copy_diagnostics(self):
        QApplication.clipboard().setText(self.diagnostics_text())

    def submit_feedback(self):
        text = self.feedback_input.toPlainText().strip() if hasattr(self, "feedback_input") else ""
        if not text:
            QMessageBox.information(self, self.tr("feedback_title"), self.tr("feedback_empty"))
            return
        self.sync_unlock_state()
        account = logged_in_account(self.unlock_state)
        entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}  {account.get('email', 'local')}  {text}"
        feedback = [entry] + list(self.unlock_state.get("feedback") or [])
        self.unlock_state["feedback"] = feedback[:30]
        state.PET_UNLOCKS = self.unlock_state
        self.save_unlock_state()
        self.feedback_input.clear()
        QMessageBox.information(self, self.tr("feedback_title"), self.tr("feedback_saved"))

    def confirm_uninstall(self):
        if not can_self_uninstall():
            QMessageBox.information(self, self.tr("settings_uninstall_group"), self.tr("settings_uninstall_dev_warning"))
            return

        dialog = UninstallDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return

        # Future cloud feedback can be sent from dialog.feedback_text() before uninstall starts.
        if not start_self_uninstall():
            QMessageBox.warning(
                self,
                self.tr("settings_uninstall_group"),
                self.tr("settings_uninstall_failed", path=uninstall_target_dir()),
            )

    def window_from_current_item(self):
        item = self.active_list.currentItem()
        if item is None:
            return None
        window_id = item.data(Qt.UserRole)
        return next((window for window in state.WINDOWS if id(window) == window_id), None)

    def library_path_from_current_item(self):
        item = self.library_list.currentItem()
        if item is None or not item.data(Qt.UserRole):
            return None
        return Path(item.data(Qt.UserRole))

    def current_library_item_locked(self):
        item = self.library_list.currentItem() if hasattr(self, "library_list") else None
        return bool(item.data(LIBRARY_LOCKED_ROLE)) if item is not None else False

    def locked_card_image_path(self, asset):
        safe_id = "".join(ch if ch.isalnum() else "-" for ch in str(asset.id)).strip("-").lower()
        return resource_path(f"assets/UiAssets/locked-role-{safe_id}.png")

    def show_locked_pet_message(self):
        QMessageBox.information(self, self.tr("pet_locked_title"), self.tr("pet_locked_message"))

    def open_library_menu(self, pos):
        item = self.library_list.itemAt(pos)
        if item is None or not item.data(Qt.UserRole):
            return

        self.library_list.setCurrentItem(item)
        menu = style_menu(QMenu(self))

        add_action = QAction("添加到桌面", self)
        add_action.triggered.connect(self.add_selected_library_asset)
        add_action.setEnabled(not bool(item.data(LIBRARY_LOCKED_ROLE)))
        menu.addAction(add_action)

        studio_action = QAction("🎨 角色动作工坊 (设计动作)", self)
        studio_action.triggered.connect(lambda: self.open_character_action_studio())
        studio_action.setEnabled(not bool(item.data(LIBRARY_LOCKED_ROLE)))
        menu.addAction(studio_action)

        configure_action = QAction("配置素材", self)
        configure_action.triggered.connect(self.configure_selected_library_asset)
        menu.addAction(configure_action)

        style_menu(menu).exec(self.library_list.mapToGlobal(pos))

    def open_active_menu(self, pos):
        item = self.active_list.itemAt(pos)
        if item is None:
            return

        self.active_list.setCurrentItem(item)
        menu = style_menu(QMenu(self))

        edit_action = QAction("编辑", self)
        edit_action.triggered.connect(self.select_active)
        menu.addAction(edit_action)

        studio_action = QAction("🎨 角色动作工坊", self)
        studio_action.triggered.connect(self.open_active_character_action_studio)
        menu.addAction(studio_action)

        configure_action = QAction("配置素材信息", self)
        configure_action.triggered.connect(self.configure_active_asset)
        menu.addAction(configure_action)

        close_action = QAction("关闭素材", self)
        close_action.triggered.connect(self.close_active)
        menu.addAction(close_action)

        style_menu(menu).exec(self.active_list.mapToGlobal(pos))

    def open_character_action_studio(self, path=None):
        if path is None:
            path = self.library_path_from_current_item()
        if path is None:
            window = self.current_window()
            if window is not None and getattr(window, "asset", None):
                path = window.asset.path
        if path is None or not Path(path).is_dir():
            QMessageBox.information(self, "角色动作工坊", "请先在角色列表中选择一个角色。")
            return

        from .character_action_studio import CharacterActionStudioDialog
        dialog = CharacterActionStudioDialog(Path(path), parent=self)
        dialog.exec()
        self.refresh_packs()

    def open_active_character_action_studio(self):
        window = self.window_from_current_item()
        if window is not None and getattr(window, "asset", None):
            self.open_character_action_studio(window.asset.path)

    def import_asset(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "导入素材",
            str(BASE_DIR),
            "可视素材 (*.gif *.mp4 *.webm *.mov *.mkv *.avi *.m4v *.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if not path:
            return

        self.import_analyzed_path(Path(path))

    def import_folder(self):
        path = QFileDialog.getExistingDirectory(self, "导入素材文件夹", str(BASE_DIR))
        if not path:
            return
        self.import_analyzed_path(Path(path))

    def import_analyzed_path(self, path):
        analyzer = AssetAnalyzer()
        guesses = analyzer.analyze_path(path)
        if not guesses:
            log_warning("No supported asset type could be guessed for import path: %s", path)
            QMessageBox.warning(self, "导入素材", "这个路径无法识别为支持的素材类型。")
            return

        dialog = AssetSetupDialog(path, guesses, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return

        imported = self.create_import_from_setup(Path(path), dialog.metadata(), dialog.asset_name())
        if imported is None:
            log_warning("Selected asset could not be imported: %s", path)
            QMessageBox.warning(self, "导入素材", "选中的素材无法导入。")
            return

        self.refresh_packs()
        self.select_imported_library_item(imported)

    def create_import_from_setup(self, path: Path, metadata: dict, asset_name: str):
        asset_type = metadata.get("type")
        if path.is_file() and asset_type in {AssetType.GIF, AssetType.VIDEO, AssetType.STATIC_IMAGE}:
            return import_asset_to_assets(path, self.active_pack_dir())

        guess = AssetGuess(
            guessed_type=str(asset_type),
            confidence=1.0,
            reasons=["已在素材设置中确认。"],
            suggested_metadata=metadata,
        )
        return create_asset_folder_from_guess(path, self.active_pack_dir(), guess, asset_name)

    def select_imported_library_item(self, imported):
        imported = Path(imported).resolve()
        for index in range(self.library_list.count()):
            item = self.library_list.item(index)
            item_path = item.data(Qt.UserRole)
            if item_path and Path(item_path).resolve() == imported:
                self.library_list.setCurrentItem(item)
                break

    def configure_selected_library_asset(self):
        path = self.library_path_from_current_item()
        if path is None:
            return
        self.configure_asset_path(path)

    def configure_active_asset(self):
        window = self.window_from_current_item()
        if window is None:
            return
        self.configure_asset_path(window.asset.path)

    def configure_asset_path(self, path):
        path = Path(path).resolve()
        analyzer = AssetAnalyzer()
        guesses = analyzer.analyze_path(path)
        metadata = load_metadata(path) if path.is_dir() else {}
        asset = detect_asset(path)
        if asset is not None and not metadata:
            metadata = {"type": asset.type, "name": asset.name}

        if not guesses and asset is not None:
            guesses = [
                AssetGuess(
                    guessed_type=asset.type,
                    confidence=1.0,
                    reasons=["已有素材类型。"],
                    suggested_metadata=metadata,
                )
            ]

        dialog = AssetSetupDialog(path, guesses, existing_metadata=metadata, parent=self)
        if dialog.exec() != QDialog.Accepted:
            return

        new_metadata = dialog.metadata()
        saved_path = self.save_asset_metadata(path, new_metadata, dialog.asset_name())
        if saved_path is None:
            log_warning("Asset metadata could not be saved: %s", path)
            QMessageBox.warning(self, "配置素材", "这个素材信息无法保存。")
            return

        self.refresh_packs()
        self.select_imported_library_item(saved_path)
        self.offer_reload_running_overlays(saved_path)

    def save_asset_metadata(self, path: Path, metadata: dict, asset_name: str):
        asset_type = metadata.get("type")
        if path.is_dir():
            if asset_type in {AssetType.GIF, AssetType.VIDEO, AssetType.STATIC_IMAGE}:
                return path
            metadata_path = path / "asset.json"
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            asset = detect_asset(path)
            errors = validate_asset_metadata(asset) if asset is not None else ["无法读取已保存的素材信息。"]
            if errors:
                log_warning("Saved asset metadata has validation errors for %s: %s", path, "; ".join(errors))
                QMessageBox.warning(self, "配置素材", "\n".join(errors))
            return path

        if asset_type in {AssetType.GIF, AssetType.VIDEO, AssetType.STATIC_IMAGE}:
            return path

        guess = AssetGuess(
            guessed_type=str(asset_type),
            confidence=1.0,
            reasons=["由已有文件素材配置。"],
            suggested_metadata=metadata,
        )
        return create_asset_folder_from_guess(path, self.active_pack_dir(), guess, asset_name)

    def offer_reload_running_overlays(self, asset_path):
        asset_path = Path(asset_path).resolve()
        matching = [window for window in state.WINDOWS if Path(window.asset_path).resolve() == asset_path]
        if not matching:
            return

        result = QMessageBox.question(
            self,
            "重新加载素材",
            "是否重新加载正在运行的这个素材？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )
        if result != QMessageBox.Yes:
            return

        asset = detect_asset(asset_path)
        if asset is None:
            log_warning("Unable to reload asset definition: %s", asset_path)
            QMessageBox.warning(self, "重新加载素材", "无法重新加载这个素材定义。")
            return

        failed = []
        for window in matching:
            if not window.reload_asset_definition(asset):
                failed.append(window.asset.name)
        if failed:
            log_warning("Some overlays could not be reloaded for asset %s: %s", asset_path, ", ".join(failed))
            QMessageBox.warning(self, "重新加载素材", "部分桌宠无法重新加载，已保持原样。")
        self.refresh_active()
        if self.selected_window in state.WINDOWS:
            self.load_editor(self.selected_window)

    def add_selected_library_asset(self):
        item = self.library_list.currentItem()
        if item is not None and item.data(LIBRARY_LOCKED_ROLE):
            self.show_locked_pet_message()
            return
        if item is not None and item.data(Qt.UserRole):
            window = add_window(item.data(Qt.UserRole))
            if window is not None:
                self.select_window(window)

    def switch_library_asset_to_desktop(self, item=None):
        item = item or self.library_list.currentItem()
        if item is None:
            return
        action = str(item.data(LIBRARY_ACTION_ROLE) or "")
        if action == "doubao":
            self.open_doubao_guide()
            return
        if action == "redeem":
            self.open_redeem_character()
            return
        if not item.data(Qt.UserRole):
            return
        if item.data(LIBRARY_LOCKED_ROLE):
            self.library_list.setCurrentItem(item)
            self.show_locked_pet_message()
            return

        asset_path = item.data(Qt.UserRole)
        target = self.selected_window if self.selected_window in state.WINDOWS else (state.WINDOWS[0] if state.WINDOWS else None)
        if target is None:
            window = add_window(asset_path)
            if window is not None:
                self.select_window(window)
            return

        if target.switch_to_asset(asset_path):
            self.select_window(target)

    def hide_all_overlays(self):
        recovery.hide_all_overlays()
        self.refresh_active()

    def show_all_overlays(self):
        recovery.show_all_overlays()
        self.refresh_active()

    def bring_all_overlays_to_center(self):
        recovery.bring_all_overlays_to_center()
        self.refresh_active()

    def disable_click_through_for_all(self):
        recovery.disable_click_through_for_all()
        if self.selected_window in state.WINDOWS:
            self.load_editor(self.selected_window)
        self.refresh_active()

    def unlock_all_overlays(self):
        recovery.unlock_all_overlays()
        if self.selected_window in state.WINDOWS:
            self.load_editor(self.selected_window)
        self.refresh_active()

    def clear_saved_session(self):
        if not state.WINDOWS:
            save_config([])
            log_info("Recovery action: clear saved session requested with no active overlays")
            self.refresh_active()
            return

        result = QMessageBox.question(
            self,
            "清空保存的桌宠",
            "是否关闭所有正在运行的桌宠，并保存为空会话？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result != QMessageBox.Yes:
            return

        self.selected_window = None
        self.load_editor(None)
        self.hide_editor_tab()
        recovery.clear_saved_session()
        self.refresh_active()

    def select_window(self, window):
        if window not in state.WINDOWS:
            return

        self.selected_window = window
        self.load_editor(window)
        self.refresh_active()
        self.refresh_tool_target_combos()
        self.show_editor_tab()
        self.show()
        self.raise_()
        self.activateWindow()

    def select_window_silently(self, window):
        if window not in state.WINDOWS:
            return

        self.selected_window = window
        self.load_editor(window)
        self.refresh_active()
        self.refresh_tool_target_combos()

    def select_active(self):
        window = self.window_from_current_item()
        if window is not None:
            self.select_window(window)

    def close_active(self):
        window = self.window_from_current_item()
        if window is not None:
            if self.selected_window is window:
                self.selected_window = None
                self.load_editor(None)
                self.hide_editor_tab()
            window.close()

    def toggle_active_lock(self):
        window = self.window_from_current_item()
        if window is not None:
            window.toggle_lock()
            self.refresh_active()
            if self.selected_window is window:
                self.load_editor(window)

    def clear_overlay_selection(self):
        for window in state.WINDOWS:
            window.set_selected(False)

    def load_editor(self, window):
        self.loading_editor = True
        enabled = window is not None
        animated_types = {AssetType.GIF, AssetType.VIDEO, AssetType.FRAME_ANIMATION, AssetType.SPRITE_STRIP, AssetType.SPRITESHEET}

        self.clear_overlay_selection()
        if enabled:
            window.set_selected(True)

        self.scale_slider.setEnabled(enabled)
        self.opacity_slider.setEnabled(enabled)
        if hasattr(self, "speed_row"):
            self.speed_row.setVisible(enabled and window.asset_type in animated_types)
        if hasattr(self, "speed_slider"):
            self.speed_slider.setEnabled(enabled and window.asset_type in animated_types)
            self.speed_slider.setValue(window.speed if enabled else 100)
        self.top_check.setEnabled(enabled)
        self.click_check.setEnabled(enabled)
        self.lock_check.setEnabled(enabled)
        self.reload_button.setEnabled(enabled)

        self.scale_slider.setValue(window.scale if enabled else 50)
        self.opacity_slider.setValue(window.opacity if enabled else 100)
        self.top_check.setChecked(window.always_on_top if enabled else False)
        self.click_check.setChecked(window.click_through if enabled else False)
        self.lock_check.setChecked(window.locked if enabled else False)
        self.scale_label.setText(self.tr("scale_label", value=self.scale_slider.value()))
        self.opacity_label.setText(self.tr("opacity_label", value=self.opacity_slider.value()))
        if hasattr(self, "speed_label") and hasattr(self, "speed_slider"):
            self.speed_label.setText(self.tr("speed_label", value=self.speed_slider.value()))
        self.rebuild_runtime_editor(window if enabled else None)

        self.loading_editor = False

    def rebuild_runtime_editor(self, window):
        self.clear_layout(self.spritesheet_layout)
        self.clear_layout(self.composite_layout)
        self.layer_value_sliders = {}
        self.animation_combo = None

        if window is None:
            return

        if window.asset_type == AssetType.COMPOSITE_UI:
            values = window.clipped_layer_values()
            if not values:
                return
            for name, value in values.items():
                display_name = self.display_layer_name(name)
                label = QLabel(f"{display_name}: {round(value * 100)}%")
                slider = QSlider(Qt.Horizontal)
                slider.setRange(0, 100)
                slider.setValue(round(value * 100))
                slider.valueChanged.connect(
                    lambda slider_value, layer=name, layer_label=label, name_text=display_name: self.editor_layer_value_changed(
                        layer, slider_value, layer_label, name_text
                    )
                )
                self.layer_value_sliders[name] = slider
                self.composite_layout.addWidget(self.slider_row(label, slider))
            return

        if window.asset_type in {AssetType.FRAME_ANIMATION, AssetType.SPRITESHEET}:
            animations = window.available_animations()
            if not animations:
                return
            self.animation_combo = QComboBox()
            self.animation_combo.addItems(animations)
            if window.current_animation in animations:
                self.animation_combo.setCurrentText(window.current_animation)
            self.animation_combo.currentTextChanged.connect(self.editor_animation_changed)
            self.spritesheet_layout.addWidget(QLabel(self.tr("animation")))
            self.spritesheet_layout.addWidget(self.animation_combo)
            return

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def display_layer_name(self, name):
        return str(name).replace("_", " ").strip().title() or "图层"

    def editor_layer_value_changed(self, layer_name, slider_value, label, display_name):
        label.setText(f"{display_name}: {slider_value}%")
        if not self.loading_editor and self.selected_window in state.WINDOWS:
            try:
                self.selected_window.set_layer_value(layer_name, slider_value / 100)
            except Exception as exc:
                log_warning("Unable to update composite layer value %s: %s", layer_name, exc)

    def editor_animation_changed(self, animation_name):
        if not self.loading_editor and self.selected_window in state.WINDOWS:
            if not self.selected_window.set_animation(animation_name):
                log_warning("Unable to switch to animation: %s", animation_name)
                QMessageBox.warning(self, "动画", f"无法切换到动画：{animation_name}")

    def reload_selected_asset(self):
        if self.selected_window not in state.WINDOWS:
            return
        asset = detect_asset(self.selected_window.asset_path)
        if asset is None:
            log_warning("Unable to reload selected asset definition: %s", self.selected_window.asset_path)
            QMessageBox.warning(self, "重新加载素材", "无法重新加载这个素材定义。")
            return
        if not self.selected_window.reload_asset_definition(asset):
            log_warning("Reload failed for selected asset: %s", self.selected_window.asset_path)
            QMessageBox.warning(self, "重新加载素材", "重新加载失败，正在运行的桌宠已保持原样。")
            return
        self.load_editor(self.selected_window)
        self.refresh_active()

    def editor_scale_changed(self, value):
        self.scale_label.setText(self.tr("scale_label", value=value))
        if not self.loading_editor and self.selected_window in state.WINDOWS:
            self.selected_window.set_scale(value)

    def editor_opacity_changed(self, value):
        self.opacity_label.setText(self.tr("opacity_label", value=value))
        if not self.loading_editor and self.selected_window in state.WINDOWS:
            self.selected_window.set_opacity_percent(value)

    def editor_speed_changed(self, value):
        self.speed_label.setText(self.tr("speed_label", value=value))
        if not self.loading_editor and self.selected_window in state.WINDOWS:
            self.selected_window.set_speed(value)

    def editor_top_changed(self, checked):
        if not self.loading_editor and self.selected_window in state.WINDOWS:
            self.selected_window.always_on_top = checked
            self.selected_window.apply_window_flags()
            save_config()

    def editor_click_changed(self, checked):
        if not self.loading_editor and self.selected_window in state.WINDOWS:
            self.selected_window.click_through = checked
            self.selected_window.apply_click_through()
            save_config()

    def editor_lock_changed(self, checked):
        if not self.loading_editor and self.selected_window in state.WINDOWS:
            self.selected_window.locked = checked
            save_config()
            self.refresh_active()

    def closeEvent(self, event):
        self.clear_overlay_selection()
        if state.EXITING:
            super().closeEvent(event)
            return
        exit_app()
        event.accept()
