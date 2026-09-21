import pytest
from PySide6.QtCore import Qt, QPoint, QPointF
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication

from window_pet_app.vibe_components import VibeVerticalSizeControl
from window_pet_app.notchnotes_window import COLOR_BG_PAGE, COLOR_BG_CARD


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_vibe_vertical_size_control_range_and_steppers(qapp):
    changed_values = []
    ctrl = VibeVerticalSizeControl(current_scale=100, on_scale_changed=lambda v: changed_values.append(v))
    assert ctrl._scale == 100
    assert "100%" in ctrl.badge.text()

    # Step up (+10%)
    ctrl.adjust_scale(10)
    assert ctrl._scale == 110
    assert "110%" in ctrl.badge.text()
    assert changed_values[-1] == 110

    # Step down (-10%)
    ctrl.adjust_scale(-10)
    assert ctrl._scale == 100
    assert changed_values[-1] == 100

    # Boundary clamp: max 200
    ctrl.set_scale(250)
    assert ctrl._scale == 200

    # Boundary clamp: min 20
    ctrl.set_scale(10)
    assert ctrl._scale == 20

    # Reset
    ctrl.set_scale(100)
    assert ctrl._scale == 100


def test_vibe_vertical_size_control_wheel_event(qapp):
    ctrl = VibeVerticalSizeControl(current_scale=100)
    
    # Simulate wheel up (+5%)
    wheel_up = QWheelEvent(
        QPointF(50, 50),
        QPointF(50, 50),
        QPoint(0, 0),
        QPoint(0, 120),
        Qt.NoButton,
        Qt.NoModifier,
        Qt.ScrollUpdate,
        False,
    )
    ctrl.wheelEvent(wheel_up)
    assert ctrl._scale == 105

    # Simulate wheel down (-5%)
    wheel_down = QWheelEvent(
        QPointF(50, 50),
        QPointF(50, 50),
        QPoint(0, 0),
        QPoint(0, -120),
        Qt.NoButton,
        Qt.NoModifier,
        Qt.ScrollUpdate,
        False,
    )
    ctrl.wheelEvent(wheel_down)
    assert ctrl._scale == 100


def test_pastel_notchnotes_palette():
    # NotchNotes should have warm macaron pastel background, not dark obsidian
    assert COLOR_BG_PAGE.name().lower() in ("#fffdfa", "#ffffff", "#fdf7f2")
    assert COLOR_BG_CARD.name().lower() in ("#ffffff", "#fffdfa")
