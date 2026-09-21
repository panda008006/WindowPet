import os
import time

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRect
from PySide6.QtWidgets import QApplication

from window_pet_app import state
from window_pet_app.whip_tool import WhipOverlay, WhipPoint


class FakePetWindow:
    def __init__(self):
        self.hits = 0

    def isVisible(self):
        return True

    def whip_hit_rect(self):
        return QRect(250, 140, 80, 80)

    def handle_whip_hit(self):
        self.hits += 1
        return True


def test_whip_detects_pet_hit_from_fast_tip_segment():
    app = QApplication.instance() or QApplication([])
    overlay = WhipOverlay()
    overlay.setGeometry(0, 0, 800, 600)
    overlay.whip = []
    for index in range(WhipOverlay.SEGMENTS):
        x = 10 + index * 20
        y = 180
        overlay.whip.append(WhipPoint(x, y, x - 120, y))

    pet = FakePetWindow()
    state.WINDOWS = [pet]
    try:
        assert overlay.detect_pet_hits(time.monotonic()) is True
        assert pet.hits == 1
    finally:
        state.WINDOWS = []
        overlay.close()
        app.processEvents()
