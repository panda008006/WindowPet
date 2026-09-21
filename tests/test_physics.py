from PySide6.QtCore import QObject, QPoint, QRect, QSize

from window_pet_app.physics import OverlayPhysics, PhysicsBody


def test_physics_body_falls_until_screen_floor():
    body = PhysicsBody(gravity=1000, min_bounce_velocity=9999)

    result = body.step(
        position=QPoint(10, 10),
        size=QSize(20, 20),
        bounds=QRect(0, 0, 200, 200),
        elapsed_seconds=0.1,
    )

    assert result.position.y() > 10
    assert result.velocity_y > 0
    assert result.landed is False


def test_physics_body_settles_on_floor_when_velocity_is_low():
    body = PhysicsBody(velocity_y=80, gravity=1000, min_bounce_velocity=500)

    result = body.step(
        position=QPoint(10, 170),
        size=QSize(20, 20),
        bounds=QRect(0, 0, 200, 200),
        elapsed_seconds=0.1,
    )

    assert result.position == QPoint(10, 180)
    assert result.velocity_y == 0
    assert result.landed is True
    assert result.settled is True


def test_physics_body_bounces_on_hard_landing():
    body = PhysicsBody(velocity_y=900, gravity=1000, min_bounce_velocity=500, bounce_factor=0.5)

    result = body.step(
        position=QPoint(10, 170),
        size=QSize(20, 20),
        bounds=QRect(0, 0, 200, 200),
        elapsed_seconds=0.1,
    )

    assert result.position == QPoint(10, 180)
    assert result.velocity_y < 0
    assert result.landed is True
    assert result.bounced is True


def test_physics_body_lands_on_window_platform():
    body = PhysicsBody(velocity_y=200, gravity=1000, min_bounce_velocity=9999)

    result = body.step(
        position=QPoint(20, 50),
        size=QSize(30, 20),
        bounds=QRect(0, 0, 200, 200),
        elapsed_seconds=0.2,
        platforms=[QRect(0, 100, 120, 10)],
    )

    assert result.position == QPoint(20, 81)
    assert result.velocity_y == 0
    assert result.landed is True
    assert result.settled is True


def test_physics_body_ignores_platform_without_horizontal_overlap():
    body = PhysicsBody(velocity_y=200, gravity=1000, min_bounce_velocity=9999)

    result = body.step(
        position=QPoint(150, 50),
        size=QSize(30, 20),
        bounds=QRect(0, 0, 200, 200),
        elapsed_seconds=0.2,
        platforms=[QRect(0, 100, 80, 10)],
    )

    assert result.position.y() > 81
    assert result.landed is False


def test_physics_body_lands_when_released_partly_through_platform_top():
    body = PhysicsBody(velocity_y=0, gravity=1000, min_bounce_velocity=9999)

    result = body.step(
        position=QPoint(20, 90),
        size=QSize(30, 20),
        bounds=QRect(0, 0, 200, 200),
        elapsed_seconds=0.1,
        platforms=[QRect(0, 100, 120, 10)],
    )

    assert result.position == QPoint(20, 81)
    assert result.landed is True


class FakeDockWindow(QObject):
    def __init__(self):
        super().__init__()
        self._pos = QPoint(20, 0)
        self._size = QSize(192, 208)
        self.dock_mode = "bottom"
        self.played = []

    def pos(self):
        return self._pos

    def move(self, pos):
        self._pos = pos

    def width(self):
        return self._size.width()

    def height(self):
        return self._size.height()

    def visible_edge_size(self, mode):
        assert mode == "bottom"
        return 122

    def edge_crawl_animation_name(self):
        return "edge-crawl-bottom"

    def play_frame_animation(self, name, *, loop=None, return_to_idle=True):
        self.played.append((name, loop, return_to_idle))
        return False

    def play_docked_idle_fallback(self):
        self.played.append(("idle", True, False))
        return True


def test_docked_bottom_uses_alpha_aware_visible_edge_and_idle_fallback():
    window = FakeDockWindow()
    physics = OverlayPhysics(window, enabled=True)

    physics.crawl_along_edge(QRect(0, 0, 400, 300), 0.033)

    assert window.pos() == QPoint(20, 178)
    assert window.played == [
        ("edge-crawl-bottom", False, False),
        ("idle", True, False),
    ]
