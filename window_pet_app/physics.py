from dataclasses import dataclass

from PySide6.QtCore import QPoint, QRect, QSize, QTimer

from .assets import save_config
from .desktop_obstacles import DesktopObstacleProvider


@dataclass
class PhysicsStepResult:
    position: QPoint
    velocity_y: float
    landed: bool = False
    bounced: bool = False
    settled: bool = False


@dataclass
class PhysicsBody:
    velocity_y: float = 0.0
    gravity: float = 1800.0
    bounce_factor: float = 0.32
    min_bounce_velocity: float = 700.0
    settle_velocity: float = 90.0

    def step(
        self,
        position: QPoint,
        size: QSize,
        bounds: QRect,
        elapsed_seconds: float,
        platforms=None,
    ) -> PhysicsStepResult:
        if elapsed_seconds <= 0 or not bounds.isValid():
            return PhysicsStepResult(position=position, velocity_y=self.velocity_y)

        next_velocity = self.velocity_y + self.gravity * elapsed_seconds
        next_y = position.y() + next_velocity * elapsed_seconds
        landing_y = self.landing_y(position, size, bounds, next_y, next_velocity, platforms or [])

        if next_y < landing_y:
            return PhysicsStepResult(
                position=QPoint(position.x(), round(next_y)),
                velocity_y=next_velocity,
            )

        if next_velocity >= self.min_bounce_velocity:
            return PhysicsStepResult(
                position=QPoint(position.x(), landing_y),
                velocity_y=-next_velocity * self.bounce_factor,
                landed=True,
                bounced=True,
            )

        return PhysicsStepResult(
            position=QPoint(position.x(), landing_y),
            velocity_y=0.0,
            landed=True,
            settled=abs(next_velocity) <= self.settle_velocity or next_velocity < self.min_bounce_velocity,
        )

    def landing_y(self, position, size, bounds, next_y, next_velocity, platforms):
        height = max(1, size.height())
        floor_y = bounds.bottom() - height + 1
        if next_velocity <= 0:
            return floor_y

        next_bottom = next_y + height - 1
        landing_lines = [bounds.bottom()]

        for platform in platforms:
            if not isinstance(platform, QRect) or not platform.isValid():
                continue
            if not platform.intersects(bounds):
                continue
            platform_top = platform.top()
            if position.y() <= platform_top <= next_bottom and self.horizontal_overlap(position, size, platform):
                landing_lines.append(platform_top)

        return min(landing_lines) - height + 1

    def horizontal_overlap(self, position, size, platform):
        left = position.x()
        right = position.x() + max(1, size.width()) - 1
        overlap = min(right, platform.right()) - max(left, platform.left()) + 1
        required = max(6, round(min(max(1, size.width()), max(1, platform.width())) * 0.15))
        return overlap >= required


class OverlayPhysics:
    def __init__(self, window, enabled=False):
        self.window = window
        self.enabled = bool(enabled)
        self.body = PhysicsBody()
        self.timer = QTimer(window)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.tick)
        self.last_tick = None
        self.airborne = False
        self.pending_landing_animation = False
        self.crawl_direction = 1
        self.current_crawl_animation = ""
        self.platform_provider = DesktopObstacleProvider()

    def set_enabled(self, enabled):
        self.enabled = bool(enabled)
        self.reset_motion()
        if self.enabled:
            self.start()
        else:
            self.stop()

    def start(self):
        if not self.enabled:
            return
        if not self.timer.isActive():
            self.last_tick = None
            self.timer.start()

    def stop(self):
        self.timer.stop()
        self.last_tick = None

    def reset_motion(self):
        self.body.velocity_y = 0.0
        self.airborne = False
        self.pending_landing_animation = False
        self.current_crawl_animation = ""

    def pause_for_drag(self):
        self.stop()
        self.reset_motion()

    def resume_after_drag(self, force_landing_animation=True):
        self.reset_motion()
        self.pending_landing_animation = bool(force_landing_animation)
        self.start()

    def start_temporary_fall(self, velocity_y=140.0):
        self.reset_motion()
        self.body.velocity_y = float(velocity_y)
        self.pending_landing_animation = True
        self.airborne = True
        self.start()

    def should_update(self):
        if not self.enabled:
            return False
        if self.window.is_dragging_asset:
            return False
        if self.window.screen_saver_active:
            return False
        return self.window.isVisible()

    def tick(self):
        if not self.should_update():
            return

        now = self.window.physics_time_seconds()
        if self.last_tick is None:
            self.last_tick = now
            return

        elapsed = min(0.08, max(0.0, now - self.last_tick))
        self.last_tick = now

        bounds = self.window.screen_geometry_for_window()
        if bounds is None:
            return

        if self.window.dock_mode != "none":
            self.body.velocity_y = 0.0
            self.airborne = False
            self.pending_landing_animation = False
            self.crawl_along_edge(bounds, elapsed)
            return

        platforms = self.platform_provider.platforms()
        result = self.body.step(self.window.pos(), self.window.size(), bounds, elapsed, platforms=platforms)
        self.body.velocity_y = result.velocity_y

        if result.position != self.window.pos():
            self.window.move(result.position)

        if not result.landed:
            self.start_fall_animation_if_needed()
            return

        if result.bounced:
            self.airborne = True
            return

        if result.settled:
            self.land()

    def start_fall_animation_if_needed(self):
        if self.airborne:
            return
        if self.body.velocity_y <= 80:
            return
        self.airborne = True
        # Physics can still move a pet, but fall/land are no longer automatic
        # action triggers. The role remains in its base idle state instead.
        if hasattr(self.window, "play_idle_animation"):
            self.window.play_idle_animation()

    def land(self):
        self.stop()
        should_play_landing = self.airborne or self.pending_landing_animation
        self.reset_motion()
        if getattr(self.window, "temporary_fall_enabled", False):
            self.window.temporary_fall_enabled = False
            if not getattr(self.window, "physics_enabled", False):
                self.set_enabled(False)
        if should_play_landing and hasattr(self.window, "play_idle_animation"):
            self.window.play_idle_animation()
        save_config()

    def crawl_along_edge(self, bounds, elapsed):
        if elapsed <= 0:
            return
        self.start_edge_crawl_animation_if_needed()
        pos = self.window.pos()
        mode = self.window.dock_mode

        if mode in {"bottom", "top"}:
            visible = self.window.visible_edge_size(mode)
            x = min(max(pos.x(), bounds.left()), max(bounds.left(), bounds.right() - self.window.width() + 1))
            y = bounds.bottom() - visible + 1 if mode == "bottom" else bounds.top() - self.window.height() + visible
            new_pos = QPoint(x, y)
        elif mode in {"left", "right"}:
            visible = self.window.visible_edge_size(mode)
            y = min(max(pos.y(), bounds.top()), max(bounds.top(), bounds.bottom() - self.window.height() + 1))
            x = bounds.left() - self.window.width() + visible if mode == "left" else bounds.right() - visible + 1
            new_pos = QPoint(x, y)
        else:
            return

        if new_pos != pos:
            self.window.move(new_pos)

    def start_edge_crawl_animation_if_needed(self):
        animation_name = ""
        if hasattr(self.window, "edge_crawl_animation_name"):
            animation_name = self.window.edge_crawl_animation_name()
        if not animation_name or animation_name == self.current_crawl_animation:
            return
        if self.window.play_frame_animation(animation_name, loop=False, return_to_idle=False):
            self.current_crawl_animation = animation_name
            return
        if hasattr(self.window, "play_docked_idle_fallback"):
            self.window.play_docked_idle_fallback()
            self.current_crawl_animation = "idle"

    def advance_axis(self, value, minimum, maximum, amount):
        if minimum >= maximum:
            return minimum, 1
        next_value = round(value + amount)
        direction = self.crawl_direction
        if next_value <= minimum:
            return minimum, 1
        if next_value >= maximum:
            return maximum, -1
        return next_value, direction
