"""视频素材的音频播放层。

WindowPet 的角色画面继续由 PNG 帧绘制，原始视频只在这里提供声音。
这样不会把视频画面变成一个有黑底或无法透明的原生视频窗口。
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QSize, QUrl, Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimedia import QVideoSink

from .logging_utils import log_warning


class VideoAudioPlayer(QObject):
    """可重复切换、可循环的本地视频音轨播放器。"""

    def __init__(self, parent=None, muted=True):
        super().__init__(parent)
        self.player = QMediaPlayer(parent)
        self.audio_output = QAudioOutput(parent)
        self.muted = bool(muted)
        self.audio_output.setMuted(self.muted)
        self.audio_output.setVolume(0.0 if self.muted else 1.0)
        self.player.setAudioOutput(self.audio_output)
        self.player.errorOccurred.connect(self._on_error)
        self.current_source: Path | None = None
        self.loop = False
        self.speed = 100
        self.display_size = QSize()

    def set_muted(self, muted: bool):
        self.muted = bool(muted)
        self.audio_output.setMuted(self.muted)
        self.audio_output.setVolume(0.0 if self.muted else 1.0)

    def play(self, source, *, loop=False, speed=None) -> bool:
        source = Path(source).resolve()
        if not source.is_file():
            self.stop()
            return False

        self.stop()
        if speed is not None:
            self.set_speed(speed)
        self.loop = bool(loop)
        self.current_source = source
        self.player.setLoops(QMediaPlayer.Loops.Infinite if self.loop else 1)
        self.player.setSource(QUrl.fromLocalFile(str(source)))
        self.player.play()
        return True

    def stop(self):
        self.player.stop()
        self.current_source = None

    def set_speed(self, value):
        try:
            self.speed = max(1, int(value or 100))
        except (TypeError, ValueError):
            self.speed = 100
        self.player.setPlaybackRate(self.speed / 100.0)

    def set_display_size(self, size):
        self.display_size = QSize(size) if size is not None else QSize()

    def close(self):
        self.stop()
        self.player.setSource(QUrl())

    def _on_error(self, error, message=""):
        if error != QMediaPlayer.Error.NoError:
            log_warning("Video audio playback failed: %s", message or error)


class VideoMediaPlayer(VideoAudioPlayer):
    """同时提供视频帧和声音的独立视频素材播放器。"""

    frame_changed = Signal(QPixmap)
    finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_sink = QVideoSink(parent)
        self.video_sink.videoFrameChanged.connect(self._on_video_frame)
        self.player.setVideoSink(self.video_sink)
        self.player.mediaStatusChanged.connect(self._on_media_status)

    def _on_video_frame(self, frame):
        image = frame.toImage()
        if not image.isNull():
            if self.display_size.isValid() and image.size() != self.display_size:
                image = image.scaled(self.display_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            self.frame_changed.emit(QPixmap.fromImage(image))

    def _on_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.finished.emit()

    def close(self):
        self.stop()
        self.player.setVideoSink(None)
        self.player.setSource(QUrl())
