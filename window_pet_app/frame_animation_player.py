from pathlib import Path
from collections import OrderedDict

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QPixmap


class FrameAnimationPlayer(QObject):
    pixmap_changed = Signal(QPixmap)
    finished = Signal()

    def __init__(self, frame_paths, fps=12, parent=None, loop=True):
        super().__init__(parent)
        self.frame_paths = [Path(path) for path in frame_paths]
        self.fps = max(1, int(fps or 12))
        self.loop = bool(loop)
        self.speed = 100
        self.index = 0
        self.frames = []
        # Large video animations used to decode every PNG into QPixmap at
        # once on the GUI thread.  That made the first click/drag after a
        # role switch pause for hundreds of milliseconds and consumed a large
        # amount of native image memory.  Keep a small rolling cache instead;
        # frames are decoded just before they are displayed.
        self._lazy = False
        self._frame_cache = OrderedDict()
        self._lazy_cache_limit = 16

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance)
        self.load_frames()
        self.update_interval()

    def set_frames(self, frame_paths, fps=None, loop=True):
        self.stop()
        self.frame_paths = [Path(path) for path in frame_paths]
        if fps is not None:
            self.fps = max(1, int(fps or 12))
        self.loop = bool(loop)
        self.index = 0
        self._frame_cache.clear()
        self.load_frames()
        self.update_interval()

    def load_frames(self):
        self.frames.clear()
        self._frame_cache.clear()
        self._lazy = len(self.frame_paths) > self._lazy_threshold()
        if self._lazy:
            # Keep positional placeholders so existing callers can still use
            # ``len(player.frames)`` and ``frames[0]``.
            self.frames = [QPixmap() for _ in self.frame_paths]
            self._load_frame(0)
            return
        for path in self.frame_paths:
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self.frames.append(pixmap)

    @staticmethod
    def _lazy_threshold():
        # Small hand-authored PNG animations benefit from eager loading; only
        # extracted video sequences need the rolling cache.
        return 24

    def _load_frame(self, index):
        if index < 0 or index >= len(self.frame_paths):
            return QPixmap()
        if not self._lazy:
            return self.frames[index] if index < len(self.frames) else QPixmap()
        cached = self._frame_cache.get(index)
        if cached is not None:
            self._frame_cache.move_to_end(index)
            return cached
        pixmap = QPixmap(str(self.frame_paths[index]))
        if pixmap.isNull():
            return pixmap
        self.frames[index] = pixmap
        self._frame_cache[index] = pixmap
        self._frame_cache.move_to_end(index)
        while len(self._frame_cache) > self._lazy_cache_limit:
            old_index, _old_pixmap = self._frame_cache.popitem(last=False)
            if old_index != index:
                self.frames[old_index] = QPixmap()
        return pixmap

    def start(self):
        if not self.frame_paths:
            return
        self.index = min(self.index, len(self.frame_paths) - 1)
        pixmap = self._load_frame(self.index)
        if pixmap.isNull():
            return
        self.pixmap_changed.emit(pixmap)
        self.timer.start()

    def stop(self):
        self.timer.stop()

    def set_speed(self, multiplier):
        self.speed = max(1, int(multiplier or 100))
        self.update_interval()

    def update_interval(self):
        interval = round(1000 / self.fps * 100 / max(1, self.speed))
        self.timer.setInterval(max(1, interval))

    def advance(self):
        if not self.frame_paths:
            self.stop()
            return
        next_index = self.index + 1
        if next_index >= len(self.frame_paths) and not self.loop:
            self.stop()
            self.finished.emit()
            return
        self.index = next_index % len(self.frame_paths)
        pixmap = self._load_frame(self.index)
        if not pixmap.isNull():
            self.pixmap_changed.emit(pixmap)
