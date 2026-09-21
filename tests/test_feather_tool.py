import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication

from window_pet_app import state
from window_pet_app.feather_tool import FeatherOverlay


class FakePetWindow:
    def __init__(self, width=100, height=100):
        self.touches = 0
        self._width = width
        self._height = height

    def isVisible(self):
        return True

    def width(self):
        return self._width

    def height(self):
        return self._height

    def feather_touch_rect(self):
        return QRect(170, 135, 100, 100)

    def handle_feather_touch(self):
        self.touches += 1
        return True


def test_feather_detects_touch_while_left_button_is_held():
    app = QApplication.instance() or QApplication([])
    overlay = FeatherOverlay()
    overlay.setGeometry(0, 0, 800, 600)
    overlay.mouse_x = 180
    overlay.mouse_y = 230
    overlay.angle = -1.35
    overlay.left_held = True
    overlay.hold_started_at = time.monotonic() - 1.0

    pet = FakePetWindow()
    state.WINDOWS = [pet]
    try:
        assert overlay.detect_pet_touches(time.monotonic()) is True
        assert pet.touches == 1
    finally:
        state.WINDOWS = []
        overlay.close()
        app.processEvents()


def test_feather_render_area_stays_one_fifth_of_pet_area():
    app = QApplication.instance() or QApplication([])
    overlay = FeatherOverlay()
    pet = FakePetWindow(width=80, height=100)
    state.WINDOWS = [pet]
    try:
        size = overlay.feather_render_size()
        assert size.width() * size.height() <= pet.width() * pet.height() * 0.21
        assert size.width() > 0
        assert size.height() > 0
    finally:
        state.WINDOWS = []
        overlay.close()
        app.processEvents()
