import math
import time

from PySide6.QtCore import QPoint, QPointF, QRect, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QWidget

from .constants import resource_path
from . import state


class FeatherOverlay(QWidget):
    FEATHER_ASSET_PATH = resource_path("assets/ToolAssets/feather_premium.png")
    PET_AREA_RATIO = 0.20
    FALLBACK_PET_AREA = 72.0 * 78.0
    HANDLE_X_RATIO = 0.035
    HANDLE_Y_RATIO = 0.975
    TIP_X_RATIO = 0.93
    TIP_Y_RATIO = 0.055
    LOCAL_HANDLE_X = 2.0
    LOCAL_HANDLE_Y = 22.0
    LOCAL_TIP_X = 20.24
    LOCAL_TIP_Y = 3.76
    LOCAL_LENGTH = math.hypot(LOCAL_TIP_X - LOCAL_HANDLE_X, LOCAL_TIP_Y - LOCAL_HANDLE_Y)
    LOCAL_ANGLE = math.atan2(LOCAL_TIP_Y - LOCAL_HANDLE_Y, LOCAL_TIP_X - LOCAL_HANDLE_X)
    SHAFT_COLOR = "#5aa9c7"
    FEATHER_FILL_COLOR = "#f8fdff"
    FEATHER_EDGE_COLOR = "#85d8f3"
    FEATHER_DETAIL_COLOR = "#42afd9"
    TOUCH_COOLDOWN_SECONDS = 0.8
    HOLD_TO_SWING_SECONDS = 0.16
    TOUCH_SAMPLE_STEP = 10.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.Tool
            | Qt.WindowStaysOnTopHint
            | Qt.NoDropShadowWindowHint
        )

        self.mouse_x = 0.0
        self.mouse_y = 0.0
        self.prev_mouse_x = 0.0
        self.prev_mouse_y = 0.0
        self.angle = -math.pi / 2.7
        self.swing_phase = 0.0
        self.left_held = False
        self.hold_started_at = 0.0
        self.touch_cooldowns = {}
        self.touch_flash_until = 0.0
        self.touch_flash_pos = None
        self.feather_pixmap = QPixmap(str(self.FEATHER_ASSET_PATH))

        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.step)

    def activate(self):
        self.setGeometry(self.virtual_desktop_geometry())
        cursor_pos = self.mapFromGlobal(self.cursor().pos())
        self.mouse_x = cursor_pos.x()
        self.mouse_y = cursor_pos.y()
        self.prev_mouse_x = self.mouse_x
        self.prev_mouse_y = self.mouse_y
        self.show()
        self.raise_()
        self.activateWindow()
        self.grabMouse(Qt.BlankCursor)
        self.grabKeyboard()
        self.setCursor(Qt.BlankCursor)
        self.timer.start()

    @staticmethod
    def virtual_desktop_geometry():
        app = QApplication.instance()
        screens = app.screens() if app is not None else []
        if not screens:
            return QRect(0, 0, 1280, 720)
        geometry = QRect(screens[0].geometry())
        for screen in screens[1:]:
            geometry = geometry.united(screen.geometry())
        return geometry

    @staticmethod
    def lerp(start, end, amount):
        return start + (end - start) * amount

    @staticmethod
    def wrap_pi(angle):
        while angle > math.pi:
            angle -= math.pi * 2.0
        while angle < -math.pi:
            angle += math.pi * 2.0
        return angle

    def step(self):
        now = time.monotonic()
        mvx = self.mouse_x - self.prev_mouse_x
        mvy = self.mouse_y - self.prev_mouse_y
        speed = math.hypot(mvx, mvy)
        if speed > 1.0:
            move_angle = math.atan2(mvy, mvx)
            target = move_angle - math.pi * 0.28
        else:
            target = -math.pi / 2.7

        delta = self.wrap_pi(target - self.angle)
        self.angle = self.wrap_pi(self.angle + delta * 0.14)

        if self.left_held:
            boost = min(0.2, speed / 180.0)
            self.swing_phase += 0.22 + boost
            if now - self.hold_started_at >= self.HOLD_TO_SWING_SECONDS:
                self.detect_pet_touches(now)
        else:
            self.swing_phase *= 0.88

        self.prev_mouse_x = self.mouse_x
        self.prev_mouse_y = self.mouse_y
        self.update()

    def draw_angle(self):
        swing = math.sin(self.swing_phase) * (0.42 if self.left_held else 0.08)
        return self.wrap_pi(self.angle + swing)

    def pet_reference_area(self):
        areas = []
        for window in list(state.WINDOWS):
            if window is self:
                continue
            try:
                if not window.isVisible():
                    continue
                width = max(1, int(window.width()))
                height = max(1, int(window.height()))
            except (RuntimeError, TypeError, AttributeError):
                continue
            areas.append(float(width * height))
        return min(areas) if areas else self.FALLBACK_PET_AREA

    def feather_source_size(self):
        if not self.feather_pixmap.isNull():
            return self.feather_pixmap.size()
        return QSize(64, 118)

    def feather_render_size(self):
        source_size = self.feather_source_size()
        source_area = max(1.0, float(source_size.width() * source_size.height()))
        target_area = max(1.0, self.pet_reference_area() * self.PET_AREA_RATIO)
        scale = math.sqrt(target_area / source_area)
        return QSize(
            max(1, round(source_size.width() * scale)),
            max(1, round(source_size.height() * scale)),
        )

    def feather_local_points(self):
        source_size = self.feather_source_size()
        return (
            QPointF(source_size.width() * self.HANDLE_X_RATIO, source_size.height() * self.HANDLE_Y_RATIO),
            QPointF(source_size.width() * self.TIP_X_RATIO, source_size.height() * self.TIP_Y_RATIO),
        )

    def feather_render_scale(self):
        source_size = self.feather_source_size()
        render_size = self.feather_render_size()
        return render_size.height() / max(1.0, float(source_size.height()))

    def feather_geometry(self):
        angle = self.draw_angle()
        dx = math.cos(angle)
        dy = math.sin(angle)
        nx = -dy
        ny = dx
        handle, tip_local = self.feather_local_points()
        scale = self.feather_render_scale()
        length = math.hypot(tip_local.x() - handle.x(), tip_local.y() - handle.y()) * scale
        base = QPointF(self.mouse_x, self.mouse_y)
        tip = QPointF(base.x() + dx * length, base.y() + dy * length)
        return base, tip, dx, dy, nx, ny

    def feather_sample_points(self):
        base, tip, dx, dy, nx, ny = self.feather_geometry()
        points = []
        length = math.hypot(tip.x() - base.x(), tip.y() - base.y())
        samples = max(1, math.ceil(length / self.TOUCH_SAMPLE_STEP))
        max_width = max(2.0, self.feather_render_size().width() * 0.35)
        for index in range(samples + 1):
            t = index / samples
            width = max_width * math.sin(math.pi * t) * (1.0 - 0.18 * t)
            center_x = self.lerp(base.x(), tip.x(), t)
            center_y = self.lerp(base.y(), tip.y(), t)
            points.append((center_x, center_y))
            points.append((center_x + nx * width * 0.8, center_y + ny * width * 0.8))
            points.append((center_x - nx * width * 0.8, center_y - ny * width * 0.8))
        return points

    def detect_pet_touches(self, now=None):
        now = time.monotonic() if now is None else now
        origin = self.geometry().topLeft()
        local_points = self.feather_sample_points()
        for window in list(state.WINDOWS):
            if not self.window_can_be_touched(window, now):
                continue
            rect = self.touch_rect_for_window(window)
            if rect is None:
                continue
            for local_x, local_y in local_points:
                global_point = QPoint(round(origin.x() + local_x), round(origin.y() + local_y))
                if rect.contains(global_point):
                    self.touch_cooldowns[id(window)] = now + self.TOUCH_COOLDOWN_SECONDS
                    self.touch_flash_until = now + 0.12
                    self.touch_flash_pos = (local_x, local_y)
                    if hasattr(window, "handle_feather_touch"):
                        window.handle_feather_touch()
                    return True
        return False

    def window_can_be_touched(self, window, now):
        if window is self:
            return False
        if now < self.touch_cooldowns.get(id(window), 0.0):
            return False
        try:
            return bool(window.isVisible())
        except RuntimeError:
            return False

    def touch_rect_for_window(self, window):
        if hasattr(window, "feather_touch_rect"):
            rect = window.feather_touch_rect()
        elif hasattr(window, "whip_hit_rect"):
            rect = window.whip_hit_rect()
        else:
            rect = QRect(window.x(), window.y(), window.width(), window.height())
        if not isinstance(rect, QRect) or not rect.isValid():
            return None
        return rect

    def mouseMoveEvent(self, event):
        pos = event.position()
        self.mouse_x = pos.x()
        self.mouse_y = pos.y()
        event.accept()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.left_held = True
            self.hold_started_at = time.monotonic()
            event.accept()
            return
        if event.button() == Qt.RightButton:
            self.close()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.left_held = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.close()
            event.accept()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 2))

        painter.save()
        if not self.feather_pixmap.isNull():
            handle, tip_local = self.feather_local_points()
            local_angle = math.atan2(tip_local.y() - handle.y(), tip_local.x() - handle.x())
            painter.translate(self.mouse_x, self.mouse_y)
            painter.rotate(math.degrees(self.draw_angle() - local_angle))
            scale = self.feather_render_scale()
            painter.scale(scale, scale)
            painter.translate(-handle.x(), -handle.y())
            painter.drawPixmap(0, 0, self.feather_pixmap)
        else:
            scale = 42.0 / self.LOCAL_LENGTH
            painter.translate(self.mouse_x, self.mouse_y)
            painter.rotate(math.degrees(self.draw_angle() - self.LOCAL_ANGLE))
            painter.scale(scale, scale)
            painter.translate(-self.LOCAL_HANDLE_X, -self.LOCAL_HANDLE_Y)
            self.draw_lucide_feather(painter)
        painter.restore()

        if self.touch_flash_pos and time.monotonic() < self.touch_flash_until:
            x, y = self.touch_flash_pos
            flash_pen = QPen(QColor("#ffffff"))
            flash_pen.setWidthF(2.0)
            painter.setPen(flash_pen)
            for angle in (0, math.pi * 0.65, math.pi * 1.3):
                painter.drawLine(
                    QPoint(round(x), round(y)),
                    QPoint(round(x + math.cos(angle) * 11.0), round(y + math.sin(angle) * 11.0)),
                )

    def lucide_body_path(self):
        path = QPainterPath()
        path.moveTo(12.67, 19.0)
        path.cubicTo(13.20, 19.0, 13.71, 18.79, 14.09, 18.41)
        path.lineTo(20.24, 12.24)
        path.cubicTo(22.58, 9.89, 22.58, 6.11, 20.24, 3.76)
        path.cubicTo(17.90, 1.42, 14.10, 1.42, 11.75, 3.76)
        path.lineTo(5.59, 9.91)
        path.cubicTo(5.21, 10.29, 5.00, 10.80, 5.00, 11.33)
        path.lineTo(5.00, 18.00)
        path.cubicTo(5.00, 18.55, 5.45, 19.00, 6.00, 19.00)
        path.closeSubpath()
        return path

    def draw_lucide_feather(self, painter):
        body_path = self.lucide_body_path()

        edge_pen = QPen(QColor(self.FEATHER_EDGE_COLOR))
        edge_pen.setWidthF(2.15)
        edge_pen.setCapStyle(Qt.RoundCap)
        edge_pen.setJoinStyle(Qt.RoundJoin)

        body_fill = QColor(self.FEATHER_FILL_COLOR)
        body_fill.setAlpha(225)
        painter.setBrush(body_fill)
        painter.setPen(edge_pen)
        painter.drawPath(body_path)

        detail_pen = QPen(QColor(self.FEATHER_DETAIL_COLOR))
        detail_pen.setWidthF(1.55)
        detail_pen.setCapStyle(Qt.RoundCap)
        detail_pen.setJoinStyle(Qt.RoundJoin)
        painter.setBrush(Qt.NoBrush)
        painter.setPen(detail_pen)
        painter.drawLine(QPointF(16.0, 8.0), QPointF(2.0, 22.0))
        painter.drawLine(QPointF(17.5, 15.0), QPointF(9.0, 15.0))

        shaft_pen = QPen(QColor(self.SHAFT_COLOR))
        shaft_pen.setWidthF(0.95)
        shaft_pen.setCapStyle(Qt.RoundCap)
        painter.setPen(shaft_pen)
        painter.drawLine(QPointF(13.0, 11.0), QPointF(7.5, 16.5))

    def closeEvent(self, event):
        self.timer.stop()
        try:
            self.releaseMouse()
        except RuntimeError:
            pass
        try:
            self.releaseKeyboard()
        except RuntimeError:
            pass
        global _ACTIVE_FEATHER_OVERLAY
        if _ACTIVE_FEATHER_OVERLAY is self:
            _ACTIVE_FEATHER_OVERLAY = None
        super().closeEvent(event)


_ACTIVE_FEATHER_OVERLAY = None


def show_feather_tool(parent=None):
    global _ACTIVE_FEATHER_OVERLAY
    if _ACTIVE_FEATHER_OVERLAY is not None:
        _ACTIVE_FEATHER_OVERLAY.close()
    overlay = FeatherOverlay(parent)
    _ACTIVE_FEATHER_OVERLAY = overlay
    overlay.activate()
    return overlay
