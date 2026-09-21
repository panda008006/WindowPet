from pathlib import Path

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
        self.load_frames()
        self.update_interval()

    def load_frames(self):
        self.frames.clear()
        for path in self.frame_paths:
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self.frames.append(pixmap)

    def start(self):
        if not self.frames:
            return
        self.index = min(self.index, len(self.frames) - 1)
        self.pixmap_changed.emit(self.frames[self.index])
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
        if not self.frames:
            self.stop()
            return
        next_index = self.index + 1
        if next_index >= len(self.frames) and not self.loop:
            self.stop()
            self.finished.emit()
            return
        self.index = next_index % len(self.frames)
        self.pixmap_changed.emit(self.frames[self.index])
