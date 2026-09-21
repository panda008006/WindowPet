from window_pet_app import overlay
from window_pet_app.focus import (
    FOCUS_MODE_BREAK,
    FOCUS_MODE_CUSTOM,
    FOCUS_MODE_FOCUS,
    normalize_focus_mode,
    timer_done_text,
    timer_prefix,
)
from window_pet_app.overlay import OverlayWindow


class FakeTimer:
    def __init__(self):
        self.stopped = False

    def stop(self):
        self.stopped = True


class FakeFocusWindow:
    def __init__(self):
        self.timer_running = True
        self.timer_done = False
        self.timer_seconds = 0
        self.focus_mode = FOCUS_MODE_FOCUS
        self.focus_sessions_completed = 0
        self.countdown_timer = FakeTimer()
        self.memo_text = "Finish draft"
        self.memo_visible = False
        self.memo_checked = False
        self.rewards = []
        self.messages = []
        self.updated = 0

    def trigger_reward(self, reason):
        self.rewards.append(reason)
        return ["fake:reward"]

    def complete_countdown(self):
        return OverlayWindow.complete_countdown(self)

    def show_focus_message(self, title, message):
        self.messages.append((title, message))

    def edit_memo(self):
        return

    def update(self):
        self.updated += 1


def test_focus_mode_labels_are_stable():
    assert normalize_focus_mode("focus") == FOCUS_MODE_FOCUS
    assert normalize_focus_mode("break") == FOCUS_MODE_BREAK
    assert normalize_focus_mode("bad-value") == FOCUS_MODE_CUSTOM
    assert timer_prefix(FOCUS_MODE_FOCUS) == "专注"
    assert timer_done_text(FOCUS_MODE_FOCUS, 2) == "专注完成 x2"


def test_focus_countdown_completion_only_counts_once(monkeypatch):
    saves = []
    monkeypatch.setattr(overlay, "save_config", lambda: saves.append(True))

    window = FakeFocusWindow()
    window.timer_seconds = 1

    OverlayWindow.tick_countdown(window)
    OverlayWindow.tick_countdown(window)

    assert window.timer_running is False
    assert window.timer_done is True
    assert window.countdown_timer.stopped is True
    assert window.focus_sessions_completed == 1
    assert window.rewards == ["timer"]
    assert len(window.messages) == 1
    assert len(saves) == 1


def test_complete_current_task_checks_memo_and_rewards(monkeypatch):
    saves = []
    monkeypatch.setattr(overlay, "save_config", lambda: saves.append(True))

    window = FakeFocusWindow()

    OverlayWindow.complete_current_task(window)

    assert window.memo_visible is True
    assert window.memo_checked is True
    assert window.timer_done is True
    assert window.rewards == ["task"]
    assert len(window.messages) == 1
    assert len(saves) == 1
