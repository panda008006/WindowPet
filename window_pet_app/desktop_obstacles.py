import os
import sys
import time

from PySide6.QtCore import QRect


class DesktopObstacleProvider:
    def __init__(self, cache_seconds=0.5):
        self.cache_seconds = cache_seconds
        self.cached_at = 0.0
        self.cached_platforms = []

    def platforms(self):
        now = time.monotonic()
        if now - self.cached_at < self.cache_seconds:
            return list(self.cached_platforms)
        self.cached_platforms = detect_window_platforms()
        self.cached_at = now
        return list(self.cached_platforms)


def detect_window_platforms():
    if sys.platform != "win32":
        return []
    return _detect_windows()


def _detect_windows():
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    current_pid = os.getpid()
    platforms = []

    enum_proc_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd, _lparam):
        if not _is_candidate_window(user32, hwnd, current_pid):
            return True

        rect = _window_rect(hwnd)
        if rect is None:
            return True

        left, top, right, bottom = rect
        width = right - left
        height = bottom - top
        if width < 80 or height < 40:
            return True

        platforms.append(QRect(left, top, width, 10))
        return True

    user32.EnumWindows(enum_proc_type(callback), 0)
    return platforms


def _is_candidate_window(user32, hwnd, current_pid):
    import ctypes
    from ctypes import wintypes

    if not user32.IsWindowVisible(hwnd):
        return False
    if user32.IsIconic(hwnd):
        return False
    if _is_cloaked(hwnd):
        return False

    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if int(pid.value) == current_pid:
        return False

    if user32.GetWindow(hwnd, 4):  # GW_OWNER
        return False

    if _window_class_name(hwnd) in {
        "Progman",
        "WorkerW",
        "Shell_TrayWnd",
        "Shell_SecondaryTrayWnd",
    }:
        return False

    ex_style = user32.GetWindowLongW(hwnd, -20)  # GWL_EXSTYLE
    if ex_style & 0x00000080:  # WS_EX_TOOLWINDOW
        return False

    title_length = user32.GetWindowTextLengthW(hwnd)
    if title_length <= 0:
        return False

    return True


def _is_cloaked(hwnd):
    import ctypes
    from ctypes import wintypes

    cloaked = wintypes.DWORD()
    try:
        # DWMWA_CLOAKED marks windows that are technically visible but hidden by DWM.
        return ctypes.windll.dwmapi.DwmGetWindowAttribute(hwnd, 14, ctypes.byref(cloaked), ctypes.sizeof(cloaked)) == 0 and bool(cloaked.value)
    except Exception:
        return False


def _window_class_name(hwnd):
    import ctypes

    buffer = ctypes.create_unicode_buffer(256)
    if ctypes.windll.user32.GetClassNameW(hwnd, buffer, len(buffer)):
        return buffer.value
    return ""


def _window_rect(hwnd):
    import ctypes
    from ctypes import wintypes

    class Rect(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    rect = Rect()
    try:
        dwmapi = ctypes.windll.dwmapi
        # DWMWA_EXTENDED_FRAME_BOUNDS excludes much of the invisible resize border.
        if dwmapi.DwmGetWindowAttribute(hwnd, 9, ctypes.byref(rect), ctypes.sizeof(rect)) == 0:
            return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        pass

    if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return rect.left, rect.top, rect.right, rect.bottom
    return None
