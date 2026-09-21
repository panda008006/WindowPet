from PySide6.QtCore import QPoint, QRect, QSize

from window_pet_app.overlay import EDGE_CRAWL_ANIMATIONS, OverlayWindow, _geometry_excluding_taskbars


class FakePixmap:
    def __init__(self, width=192, height=208):
        self._width = width
        self._height = height

    def isNull(self):
        return False

    def width(self):
        return self._width

    def height(self):
        return self._height


class FakeDockOverlay:
    base_visible_head_size = OverlayWindow.base_visible_head_size
    visible_edge_size = OverlayWindow.visible_edge_size
    docked_position = OverlayWindow.docked_position
    snap_position_if_near_edge = OverlayWindow.snap_position_if_near_edge
    edge_crawl_animation_name = OverlayWindow.edge_crawl_animation_name
    play_edge_crawl_animation = OverlayWindow.play_edge_crawl_animation

    def __init__(self, mode="none", content_rect=None):
        self.dock_mode = mode
        self.initializing_position = False
        self.current_frame_animation = "idle"
        self.current_pixmap = FakePixmap()
        self._content_rect = content_rect or QRect(0, 0, 192, 208)
        self._pos = QPoint(0, 0)
        self._size = QSize(192, 208)
        self.drag_released_at_top_edge = False
        self.played = []
        self.idle_variant_timer = type("Timer", (), {"stop": lambda _self: None})()
        self.asset_type = None
        self.character_id = ""

    def width(self):
        return self._size.width()

    def height(self):
        return self._size.height()

    def size(self):
        return self._size

    def pos(self):
        return self._pos

    def move(self, pos):
        self._pos = pos

    def current_content_rect(self):
        return self._content_rect

    def screen_geometry_for_window(self):
        return QRect(0, 0, 400, 300)

    def clamped_position(self, pos):
        return pos

    def play_frame_animation(self, name, *, loop=None, return_to_idle=True):
        self.played.append((name, loop, return_to_idle))
        self.current_frame_animation = name
        if name == "edge-crawl-right":
            self._content_rect = QRect(4, 43, 61, 122)
        elif name == "edge-crawl-bottom":
            self._content_rect = QRect(49, 4, 94, 92)
        return True

    def play_docked_idle_fallback(self):
        self.played.append(("idle", True, False))
        return True


def test_edge_crawl_animation_names_are_registered():
    assert {"edge-crawl-bottom", "edge-crawl-right"}.issubset(EDGE_CRAWL_ANIMATIONS)


def test_play_edge_crawl_repositions_after_switching_to_right_frame():
    window = FakeDockOverlay(mode="right", content_rect=QRect(0, 0, 192, 208))
    window.move(QPoint(208, 20))

    assert window.play_edge_crawl_animation() is True

    assert window.played == [("edge-crawl-right", False, False)]
    assert window.pos().x() == 335
    assert window.pos().x() + 192 - 1 > 400


def test_play_edge_crawl_repositions_after_switching_to_bottom_frame():
    window = FakeDockOverlay(mode="bottom", content_rect=QRect(0, 0, 192, 208))
    window.move(QPoint(20, 92))

    assert window.play_edge_crawl_animation() is True

    assert window.played == [("edge-crawl-bottom", False, False)]
    assert window.pos().y() == 204
    assert window.pos().y() + 208 - 1 > 300


def test_top_drop_threshold_does_not_trigger_far_from_top():
    window = FakeDockOverlay()
    snapped = window.snap_position_if_near_edge(QPoint(100, 30))

    assert window.dock_mode == "none"
    assert snapped == QPoint(100, 30)


def test_top_edge_release_is_not_special_cased():
    window = FakeDockOverlay()

    snapped = window.snap_position_if_near_edge(QPoint(40, 5))

    assert window.dock_mode == "none"
    assert window.drag_released_at_top_edge is False
    assert snapped == QPoint(40, 5)


def test_taskbar_geometry_trims_bottom_work_area():
    screen = QRect(0, 0, 1536, 960)
    available = QRect(0, 0, 1536, 960)
    taskbar = QRect(0, 920, 1536, 40)

    work_area = _geometry_excluding_taskbars(screen, available, [taskbar])

    assert work_area.bottom() == 919


def test_docked_frame_change_repositions_bottom_to_current_visible_size():
    window = FakeDockOverlay(mode="bottom", content_rect=QRect(49, 4, 94, 92))
    window.move(QPoint(20, 204))

    window._content_rect = QRect(43, 4, 106, 96)
    window.current_frame_animation = "edge-crawl-bottom"
    OverlayWindow.keep_docked_position_after_frame_change(window)

    assert window.pos().y() == 200
