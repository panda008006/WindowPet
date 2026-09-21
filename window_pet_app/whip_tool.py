import math
import random
import time
from dataclasses import dataclass

from PySide6.QtCore import QPoint, QRect, Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QApplication, QWidget

from . import state


@dataclass
class WhipPoint:
    x: float
    y: float
    px: float
    py: float


class WhipOverlay(QWidget):
    # Visual physics adapted from OpenWhip's MIT-licensed whip overlay:
    # https://github.com/GitFrog1111/OpenWhip
    SEGMENTS = 28
    SEGMENT_LENGTH = 25.0
    TAPER = 0.6

    GRAVITY = 1.2
    DROP_GRAVITY = 0.95
    DAMPING = 0.96
    CONSTRAINT_ITERS = 20
    MAX_STRETCH_RATIO = 1.2

    BASE_TARGET_ANGLE = -1.12
    HANDLE_AIM_BY_MOUSE_X = 0.4
    HANDLE_AIM_BY_MOUSE_Y = 0.2
    HANDLE_AIM_CLAMP = 2.0
    HANDLE_SPRING = 0.7
    HANDLE_ANGULAR_DAMPING = 0.078
    BASE_POSE_SEGMENTS = 2
    BASE_POSE_STIFF_START = 0.9
    BASE_POSE_STIFF_END = 0.8

    HANDLE_MAX_BEND_DEG = 16.0
    TIP_MAX_BEND_DEG = 130.0
    BEND_RIGIDITY_START = 0.8
    BEND_RIGIDITY_END = 0.12

    WALL_BOUNCE = 0.42
    WALL_FRICTION = 0.86

    CRACK_SPEED = 340.0
    CRACK_COOLDOWN_SECONDS = 0.2
    FIRST_CRACK_GRACE_SECONDS = 0.35

    LINE_WIDTH_HANDLE = 7.0
    LINE_WIDTH_TIP = 5.0
    OUTLINE_WIDTH = 3.0
    HANDLE_EXTRA_WIDTH = 5.0
    HANDLE_THICK_SEGMENTS = 2
    OUTLINE_COLOR = "#e6f8ff"
    CORE_COLOR = "#65ccff"
    CRACK_COLOR = "#c7f2ff"

    ARC_WIDTH = 260.0
    ARC_HEIGHT = 185.0
    HIT_START_SEGMENT = 14
    HIT_SPEED = 90.0
    HIT_SAMPLE_STEP = 8.0
    HIT_COOLDOWN_SECONDS = 0.9

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

        self.whip = []
        self.dropping = False
        self.mouse_x = 0.0
        self.mouse_y = 0.0
        self.prev_mouse_x = 0.0
        self.prev_mouse_y = 0.0
        self.whip_spawn_time = 0.0
        self.last_crack_time = 0.0
        self.handle_angle = self.BASE_TARGET_ANGLE
        self.handle_ang_vel = 0.0
        self.crack_flash_until = 0.0
        self.crack_flash_pos = None
        self.hit_cooldowns = {}

        self.timer = QTimer(self)
        self.timer.setInterval(16)
        self.timer.timeout.connect(self.step)

    def activate(self):
        self.setGeometry(self.virtual_desktop_geometry())
        cursor_pos = self.mapFromGlobal(self.cursor().pos())
        self.mouse_x = cursor_pos.x()
        self.mouse_y = cursor_pos.y()
        self.spawn_whip(self.mouse_x or self.width() / 2, self.mouse_y or self.height() / 2)
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

    def spawn_whip(self, mx, my):
        self.dropping = False
        self.last_crack_time = 0.0
        self.whip_spawn_time = time.monotonic()
        self.handle_angle = self.BASE_TARGET_ANGLE
        self.handle_ang_vel = 0.0
        self.whip = []
        for index in range(self.SEGMENTS):
            t = index / max(1, self.SEGMENTS - 1)
            x = mx + t * self.ARC_WIDTH
            y = my - math.sin(t * math.pi * 0.75) * self.ARC_HEIGHT
            self.whip.append(WhipPoint(x, y, x, y))
        self.prev_mouse_x = mx
        self.prev_mouse_y = my

    def segment_length(self, index):
        t = index / max(1, self.SEGMENTS - 1)
        return self.SEGMENT_LENGTH * (1.0 - t * (1.0 - self.TAPER))

    @staticmethod
    def clamp(value, low, high):
        return max(low, min(high, value))

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

    def catmull_point(self, index):
        points = self.whip
        count = len(points)
        if count == 0:
            return 0.0, 0.0
        if index < 0:
            if count >= 2:
                return 2 * points[0].x - points[1].x, 2 * points[0].y - points[1].y
            return points[0].x, points[0].y
        if index >= count:
            if count >= 2:
                a = points[count - 2]
                b = points[count - 1]
                return 2 * b.x - a.x, 2 * b.y - a.y
            return points[count - 1].x, points[count - 1].y
        return points[index].x, points[index].y

    def segment_bezier(self, index):
        p1 = self.whip[index]
        p2 = self.whip[index + 1]
        p0x, p0y = self.catmull_point(index - 1)
        p3x, p3y = self.catmull_point(index + 2)
        return (
            p1.x + (p2.x - p0x) / 6.0,
            p1.y + (p2.y - p0y) / 6.0,
            p2.x - (p3x - p1.x) / 6.0,
            p2.y - (p3y - p1.y) / 6.0,
            p2.x,
            p2.y,
        )

    def path_for_segments(self, start, stop):
        path = QPainterPath()
        if not self.whip or stop <= start:
            return path
        path.moveTo(self.whip[start].x, self.whip[start].y)
        for index in range(start, min(stop, len(self.whip) - 1)):
            cp1x, cp1y, cp2x, cp2y, x2, y2 = self.segment_bezier(index)
            path.cubicTo(cp1x, cp1y, cp2x, cp2y, x2, y2)
        return path

    def update_handle_aim(self):
        if self.dropping:
            return
        mvx = self.mouse_x - self.prev_mouse_x
        mvy = self.mouse_y - self.prev_mouse_y
        delta = self.clamp(
            mvx * self.HANDLE_AIM_BY_MOUSE_X + mvy * self.HANDLE_AIM_BY_MOUSE_Y,
            -self.HANDLE_AIM_CLAMP,
            self.HANDLE_AIM_CLAMP,
        )
        target = self.BASE_TARGET_ANGLE + delta
        error = self.wrap_pi(target - self.handle_angle)
        self.handle_ang_vel += error * self.HANDLE_SPRING
        self.handle_ang_vel *= self.HANDLE_ANGULAR_DAMPING
        self.handle_angle = self.wrap_pi(self.handle_angle + self.handle_ang_vel)

    def apply_base_pose(self):
        if not self.whip or self.dropping:
            return
        dx = math.cos(self.handle_angle)
        dy = math.sin(self.handle_angle)
        guided = min(self.BASE_POSE_SEGMENTS, len(self.whip) - 1)
        for index in range(1, guided + 1):
            t = (index - 1) / max(guided - 1, 1)
            stiff = self.lerp(self.BASE_POSE_STIFF_START, self.BASE_POSE_STIFF_END, t)
            prev = self.whip[index - 1]
            point = self.whip[index]
            target_len = self.segment_length(index - 1)
            tx = prev.x + dx * target_len
            ty = prev.y + dy * target_len
            point.x = self.lerp(point.x, tx, stiff)
            point.y = self.lerp(point.y, ty, stiff)

    def apply_bend_limits(self):
        if len(self.whip) < 3:
            return
        for index in range(1, len(self.whip) - 1):
            a = self.whip[index - 1]
            b = self.whip[index]
            c = self.whip[index + 1]
            v1x = a.x - b.x
            v1y = a.y - b.y
            v2x = c.x - b.x
            v2y = c.y - b.y
            l1 = math.hypot(v1x, v1y) or 0.0001
            l2 = math.hypot(v2x, v2y) or 0.0001
            n1x = v1x / l1
            n1y = v1y / l1
            n2x = v2x / l2
            n2y = v2y / l2
            dot = self.clamp(n1x * n2x + n1y * n2y, -1.0, 1.0)
            angle = math.acos(dot)
            t = index / max(1, len(self.whip) - 2)
            max_bend = math.radians(self.lerp(self.HANDLE_MAX_BEND_DEG, self.TIP_MAX_BEND_DEG, t))
            bend = math.pi - angle
            if bend <= max_bend:
                continue
            cross = n1x * n2y - n1y * n2x
            sign = 1.0 if cross >= 0 else -1.0
            target_angle = math.pi - max_bend
            target_a = math.atan2(n1y, n1x) + sign * target_angle
            tx = b.x + math.cos(target_a) * l2
            ty = b.y + math.sin(target_a) * l2
            rigidity = self.lerp(self.BEND_RIGIDITY_START, self.BEND_RIGIDITY_END, t)
            c.x = self.lerp(c.x, tx, rigidity)
            c.y = self.lerp(c.y, ty, rigidity)

    def cap_segment_stretch(self):
        if len(self.whip) < 2:
            return
        for index in range(len(self.whip) - 1):
            a = self.whip[index]
            b = self.whip[index + 1]
            dx = b.x - a.x
            dy = b.y - a.y
            distance = math.hypot(dx, dy) or 0.0001
            max_len = self.segment_length(index) * self.MAX_STRETCH_RATIO
            if distance <= max_len:
                continue
            factor = max_len / distance
            b.x = a.x + dx * factor
            b.y = a.y + dy * factor

    def apply_wall_collisions(self):
        if not self.whip or self.dropping:
            return
        width = max(1, self.width() - 1)
        height = max(1, self.height() - 1)
        for point in self.whip[1:]:
            vx = point.x - point.px
            vy = point.y - point.py
            hit = False
            if point.x < 0:
                point.x = 0
                if vx < 0:
                    vx = -vx * self.WALL_BOUNCE
                vy *= self.WALL_FRICTION
                hit = True
            elif point.x > width:
                point.x = width
                if vx > 0:
                    vx = -vx * self.WALL_BOUNCE
                vy *= self.WALL_FRICTION
                hit = True
            if point.y < 0:
                point.y = 0
                if vy < 0:
                    vy = -vy * self.WALL_BOUNCE
                vx *= self.WALL_FRICTION
                hit = True
            elif point.y > height:
                point.y = height
                if vy > 0:
                    vy = -vy * self.WALL_BOUNCE
                vx *= self.WALL_FRICTION
                hit = True
            if hit:
                point.px = point.x - vx
                point.py = point.y - vy

    def step(self):
        if not self.whip:
            return

        gravity = self.DROP_GRAVITY if self.dropping else self.GRAVITY
        self.update_handle_aim()
        start = 0 if self.dropping else 1
        for point in self.whip[start:]:
            vx = (point.x - point.px) * self.DAMPING
            vy = (point.y - point.py) * self.DAMPING
            point.px = point.x
            point.py = point.y
            point.x += vx
            point.y += vy + gravity

        if not self.dropping:
            handle = self.whip[0]
            handle.x = self.mouse_x
            handle.y = self.mouse_y
            handle.px = self.mouse_x
            handle.py = self.mouse_y

        self.cap_segment_stretch()
        self.apply_wall_collisions()
        self.apply_base_pose()

        for _ in range(self.CONSTRAINT_ITERS):
            for index in range(len(self.whip) - 1):
                a = self.whip[index]
                b = self.whip[index + 1]
                dx = b.x - a.x
                dy = b.y - a.y
                distance = math.hypot(dx, dy) or 0.0001
                target = self.segment_length(index)
                diff = (distance - target) / distance * 0.5
                ox = dx * diff
                oy = dy * diff
                if index == 0 and not self.dropping:
                    b.x -= ox * 2.0
                    b.y -= oy * 2.0
                else:
                    a.x += ox
                    a.y += oy
                    b.x -= ox
                    b.y -= oy
            self.apply_bend_limits()
            if not self.dropping:
                self.apply_base_pose()
            self.cap_segment_stretch()
            self.apply_wall_collisions()

        tip = self.whip[-1]
        tip_vel = math.hypot(tip.x - tip.px, tip.y - tip.py)
        now = time.monotonic()
        if (
            not self.dropping
            and tip_vel > self.CRACK_SPEED
            and now - self.whip_spawn_time >= self.FIRST_CRACK_GRACE_SECONDS
            and now - self.last_crack_time > self.CRACK_COOLDOWN_SECONDS
        ):
            self.last_crack_time = now
            self.crack_flash_until = now + 0.08
            self.crack_flash_pos = (tip.x, tip.y)

        if not self.dropping and now - self.whip_spawn_time >= self.FIRST_CRACK_GRACE_SECONDS:
            self.detect_pet_hits(now)

        if self.dropping and all(point.y > self.height() + 60 for point in self.whip):
            self.close()
            return

        self.prev_mouse_x = self.mouse_x
        self.prev_mouse_y = self.mouse_y
        self.update()

    def detect_pet_hits(self, now=None):
        if len(self.whip) < 2:
            return False
        now = time.monotonic() if now is None else now
        for window in list(state.WINDOWS):
            if not self.window_can_be_hit(window, now):
                continue
            hit_point = self.hit_point_for_window(window)
            if hit_point is None:
                continue
            self.hit_cooldowns[id(window)] = now + self.HIT_COOLDOWN_SECONDS
            self.crack_flash_until = now + 0.08
            self.crack_flash_pos = hit_point
            if hasattr(window, "handle_whip_hit"):
                window.handle_whip_hit()
            return True
        return False

    def window_can_be_hit(self, window, now):
        if window is self:
            return False
        if now < self.hit_cooldowns.get(id(window), 0.0):
            return False
        try:
            return bool(window.isVisible())
        except RuntimeError:
            return False

    def hit_rect_for_window(self, window):
        if hasattr(window, "whip_hit_rect"):
            rect = window.whip_hit_rect()
        else:
            rect = QRect(window.x(), window.y(), window.width(), window.height())
        if not isinstance(rect, QRect) or not rect.isValid():
            return None
        return rect

    def hit_point_for_window(self, window):
        rect = self.hit_rect_for_window(window)
        if rect is None:
            return None
        origin = self.geometry().topLeft()
        start = max(0, min(self.HIT_START_SEGMENT, len(self.whip) - 2))
        for index in range(start, len(self.whip) - 1):
            a = self.whip[index]
            b = self.whip[index + 1]
            speed = max(math.hypot(a.x - a.px, a.y - a.py), math.hypot(b.x - b.px, b.y - b.py))
            if speed < self.HIT_SPEED:
                continue
            distance = math.hypot(b.x - a.x, b.y - a.y)
            samples = max(1, math.ceil(distance / self.HIT_SAMPLE_STEP))
            for sample in range(samples + 1):
                t = sample / samples
                local_x = self.lerp(a.x, b.x, t)
                local_y = self.lerp(a.y, b.y, t)
                global_point = QPoint(round(origin.x() + local_x), round(origin.y() + local_y))
                if rect.contains(global_point):
                    return local_x, local_y
        return None

    def begin_drop(self):
        if self.whip and not self.dropping:
            self.dropping = True

    def mouseMoveEvent(self, event):
        pos = event.position()
        self.mouse_x = pos.x()
        self.mouse_y = pos.y()
        event.accept()

    def mousePressEvent(self, event):
        self.begin_drop()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self.close()
            event.accept()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 3))
        if not self.whip:
            return

        outline_pen = QPen(QColor(self.OUTLINE_COLOR))
        outline_pen.setCapStyle(Qt.RoundCap)
        outline_pen.setJoinStyle(Qt.RoundJoin)

        full_path = self.path_for_segments(0, len(self.whip) - 1)
        outline_pen.setWidthF(self.LINE_WIDTH_TIP + self.OUTLINE_WIDTH * 2.0)
        painter.setPen(outline_pen)
        painter.drawPath(full_path)

        thick_links = min(self.HANDLE_THICK_SEGMENTS, len(self.whip) - 1)
        if thick_links > 0 and self.HANDLE_EXTRA_WIDTH > 0:
            handle_path = self.path_for_segments(0, thick_links)
            outline_pen.setWidthF(
                self.LINE_WIDTH_HANDLE + self.HANDLE_EXTRA_WIDTH + self.OUTLINE_WIDTH * 2.0
            )
            painter.setPen(outline_pen)
            painter.drawPath(handle_path)

        core_pen = QPen(QColor(self.CORE_COLOR))
        core_pen.setCapStyle(Qt.RoundCap)
        core_pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(core_pen)
        for index in range(len(self.whip) - 1):
            t = index / max(1, len(self.whip) - 2)
            extra = self.HANDLE_EXTRA_WIDTH if index < self.HANDLE_THICK_SEGMENTS else 0.0
            core_pen.setWidthF(self.lerp(self.LINE_WIDTH_HANDLE, self.LINE_WIDTH_TIP, t) + extra)
            painter.setPen(core_pen)
            painter.drawPath(self.path_for_segments(index, index + 1))

        if self.crack_flash_pos and time.monotonic() < self.crack_flash_until:
            x, y = self.crack_flash_pos
            flash_pen = QPen(QColor(self.CRACK_COLOR))
            flash_pen.setWidthF(2.0)
            flash_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(flash_pen)
            for angle in (0, math.pi * 0.72, math.pi * 1.33):
                length = random.uniform(9.0, 16.0)
                painter.drawLine(
                    QPoint(round(x), round(y)),
                    QPoint(round(x + math.cos(angle) * length), round(y + math.sin(angle) * length)),
                )

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
        global _ACTIVE_WHIP_OVERLAY
        if _ACTIVE_WHIP_OVERLAY is self:
            _ACTIVE_WHIP_OVERLAY = None
        super().closeEvent(event)


_ACTIVE_WHIP_OVERLAY = None


def show_whip_tool(parent=None):
    global _ACTIVE_WHIP_OVERLAY
    if _ACTIVE_WHIP_OVERLAY is not None:
        _ACTIVE_WHIP_OVERLAY.close()
    overlay = WhipOverlay(parent)
    _ACTIVE_WHIP_OVERLAY = overlay
    overlay.activate()
    return overlay
