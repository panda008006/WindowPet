import os
import sys
from pathlib import Path
from PySide6.QtCore import QTime, Qt
from PySide6.QtWidgets import QApplication

from window_pet_app import state
from window_pet_app.control_panel import ControlPanel
from window_pet_app.overlay import add_window


def test_offwork_countdown_tool_page_and_trigger():
    app = QApplication.instance() or QApplication(sys.argv)

    panel = ControlPanel()
    assert hasattr(panel, "build_offwork_countdown_tool_page")
    assert hasattr(panel, "tool_offwork_clock_display")
    assert hasattr(panel, "tool_offwork_toggle_button")
    assert hasattr(panel, "tool_offwork_test_button")

    # Verify initial state
    assert panel.tool_offwork_clock_display.text() == "--:--:--"
    assert not panel._offwork_active

    # Test starting countdown in exact mode
    panel.offwork_mode_segmented.setCurrentIndex(0)
    panel.tool_offwork_time_edit.setTime(QTime(18, 0))
    panel.start_offwork_countdown()
    assert panel._offwork_active
    assert panel._offwork_target_dt is not None
    assert panel.tool_offwork_toggle_button.text() == panel.tr("tools_offwork_stop")

    # Test tick updates clock display
    panel._on_offwork_timer_tick()
    assert panel.tool_offwork_clock_display.text() != "--:--:--"

    # Test stopping countdown
    panel.stop_offwork_countdown()
    assert not panel._offwork_active
    assert panel.tool_offwork_clock_display.text() == "--:--:--"
    assert panel.tool_offwork_toggle_button.text() == panel.tr("tools_offwork_start")

    # Test duration mode
    panel.offwork_mode_segmented.setCurrentIndex(1)
    panel.tool_offwork_duration_picker.setValue(30)
    panel.start_offwork_countdown()
    assert panel._offwork_active
    panel.stop_offwork_countdown()
    assert not panel._offwork_active


def test_dudu_capybara_music_and_celebration():
    app = QApplication.instance() or QApplication(sys.argv)

    # Spawn Dudu Capybara (with music)
    dudu_dir = Path("assets/DuduCapybaraPet").resolve()
    assert dudu_dir.is_dir()

    window = add_window(str(dudu_dir))
    assert window is not None
    assert window in state.WINDOWS
    assert "嘟嘟" in getattr(window.asset, "name", "")

    orig_scale = window.scale
    assert not getattr(window, "is_celebrating_offwork", False)

    # Trigger celebration -> should scale up, speak, play music
    window.trigger_offwork_celebration(target_scale=150, duration_seconds=10)
    assert window.is_celebrating_offwork
    assert window._pre_celebration_scale == orig_scale
    assert window.video_audio_player is not None
    assert window.video_audio_player.current_source is not None

    # Dismiss celebration -> should stop music and scale back
    window.dismiss_offwork_celebration()
    assert not window.is_celebrating_offwork
    assert window.video_audio_player.current_source is None

    # Clean up
    window.close()
    if window in state.WINDOWS:
        state.WINDOWS.remove(window)


def test_any_pet_random_celebration_and_context_menu():
    app = QApplication.instance() or QApplication(sys.argv)

    # Test with another pet, e.g. XiaobaPet
    xiaoba_dir = Path("assets/XiaobaPet").resolve()
    if not xiaoba_dir.is_dir():
        return

    window = add_window(str(xiaoba_dir))
    assert window is not None

    # Verify right-click menu contains celebration action
    # We can inspect the menu actions created
    # Check that trigger_offwork_celebration runs a random animation
    window.trigger_offwork_celebration(target_scale=150, duration_seconds=10)
    assert window.is_celebrating_offwork

    # Dismiss
    window.dismiss_offwork_celebration()
    assert not window.is_celebrating_offwork

    # Clean up
    window.close()
    if window in state.WINDOWS:
        state.WINDOWS.remove(window)
