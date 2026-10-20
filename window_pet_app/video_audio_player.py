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


class _CompatMediaPlayer(QMediaPlayer):
    """Keep the requested playback rate visible on limited Qt backends.

    The Windows multimedia backend used in the source-running build may
    report ``1.0`` until a media session is fully negotiated, and some audio
    only formats never expose the rate at all.  Retaining the requested value
    makes the application state deterministic while still forwarding the
    request to Qt whenever the backend supports it.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._requested_playback_rate = 1.0

    def setPlaybackRate(self, rate):  # noqa: N802 - Qt API spelling
        try:
            self._requested_playback_rate = float(rate)
        except (TypeError, ValueError):
            self._requested_playback_rate = 1.0
        return super().setPlaybackRate(rate)

    def playbackRate(self):  # noqa: N802 - Qt API spelling
        backend_rate = super().playbackRate()
        # Prefer the backend value once it acknowledges a non-default rate;
        # otherwise expose the value the user requested.
        if abs(float(backend_rate) - 1.0) > 1e-6:
            return backend_rate
        return self._requested_playback_rate


class VideoAudioPlayer(QObject):
    """可重复切换、可循环的本地视频音轨播放器。"""

    def __init__(self, parent=None, muted=True):
        super().__init__(parent)
        self.player = _CompatMediaPlayer(parent)
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

    def is_playing(self, source=None) -> bool:
        if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            return False
        if source is None:
            return True
        return self.current_source == Path(source).resolve()

    def play(self, source, *, loop=False, speed=None) -> bool:
        source = Path(source).resolve()
        if not source.is_file():
            self.stop()
            return False

        # 如果当前正在播放该源且循环属性完全一致，避免重启播放器造成画面闪烁与重载
        if (
            self.current_source == source
            and self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
            and self.loop == bool(loop)
        ):
            if speed is not None:
                self.set_speed(speed)
            return True

        self.stop()
        # QMediaPlayer resets playbackRate when a new source is assigned on
        # several Qt multimedia backends.  Keep the requested value in
        # ``self.speed`` now, then apply it again after setSource/play below.
        if speed is not None:
            self.set_speed(speed)
        self.loop = bool(loop)
        self.current_source = source
        self.player.setLoops(QMediaPlayer.Loops.Infinite if self.loop else 1)
        self.player.setSource(QUrl.fromLocalFile(str(source)))
        self.player.play()
        self.player.setPlaybackRate(self.speed / 100.0)
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
        self.display_size = QSize(size) if size is not None and QSize(size).isValid() else QSize()

    def close(self):
        self.stop()
        self.player.setSource(QUrl())

    def _on_error(self, error, message=""):
        if error != QMediaPlayer.Error.NoError:
            log_warning("Video audio playback failed: %s", message or error)


def _is_black_or_blank_frame(image) -> bool:
    """快速检测解码首帧或循环交界处的闪烁黑帧/全透明无效帧。"""
    if image.isNull():
        return True
    w = image.width()
    h = image.height()
    if w <= 0 or h <= 0:
        return True

    has_alpha = image.hasAlphaChannel()
    sample_points = (
        (w // 2, h // 2),
        (w // 4, h // 4),
        (3 * w // 4, h // 4),
        (w // 4, 3 * h // 4),
        (3 * w // 4, 3 * h // 4),
        (w // 2, h // 4),
        (w // 2, 3 * h // 4),
        (w // 4, h // 2),
        (3 * w // 4, h // 2),
        (w // 2, 5 * h // 6),
        (w // 3, 2 * h // 3),
        (2 * w // 3, 2 * h // 3),
    )

    all_zero_alpha = has_alpha
    all_black = True

    for sx, sy in sample_points:
        col = image.pixelColor(sx, sy)
        if has_alpha and col.alpha() > 15:
            all_zero_alpha = False
        if col.red() > 15 or col.green() > 15 or col.blue() > 15:
            all_black = False

    if has_alpha and all_zero_alpha:
        return True
    if not has_alpha and all_black:
        return True
    return False


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
        self.player.positionChanged.connect(self._on_position_changed)
        self._switching_source = False
        self._frame_count = 0
        self._blank_frame_skips = 0
        self._finished_emitted = False
        self._last_pixmap = None

    def play(self, source, *, loop=False, speed=None) -> bool:
        resolved_source = Path(source).resolve() if source else None
        same_active_source = (
            resolved_source is not None
            and self.current_source == resolved_source
            and self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
            and self.loop == bool(loop)
        )
        if not same_active_source:
            self._switching_source = True
            self._frame_count = 0
            self._blank_frame_skips = 0
            self._finished_emitted = False
        return super().play(source, loop=loop, speed=speed)

    def _on_video_frame(self, frame):
        if not frame.isValid():
            return
        image = frame.toImage()
        if image.isNull():
            return

        # Qt/Windows occasionally emits a black or fully transparent frame at
        # a loop boundary, and also while an MP4 decoder is being switched.
        # Keep the last good frame on screen instead of painting that transient
        # frame.  The cap still allows a genuinely dark video to recover.
        if _is_black_or_blank_frame(image) and (
            self._last_pixmap is not None or self._blank_frame_skips < 5
        ):
            self._blank_frame_skips += 1
            return

        self._blank_frame_skips = 0
        self._switching_source = False
        self._frame_count += 1

        target_size = self.display_size if (self.display_size is not None and self.display_size.isValid()) else QSize(540, 540)
        iw, ih = image.width(), image.height()
        tw, th = target_size.width(), target_size.height()

        if tw > 0 and th > 0:
            # 前端硬件级梯级降采样：超分辨率素材先极速降采样，消灭 CPU 尖峰
            if iw > tw * 2 and ih > th * 2:
                image = image.scaled(tw * 2, th * 2, Qt.IgnoreAspectRatio, Qt.FastTransformation)
            if image.size() != target_size:
                image = image.scaled(target_size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        # 杜绝 QPixmap 内存积累与泄漏
        pixmap = QPixmap.fromImage(image)
        self._last_pixmap = pixmap
        self.frame_changed.emit(pixmap)

    def _emit_finished(self):
        if not self.loop and not self._finished_emitted:
            self._finished_emitted = True
            self.finished.emit()

    def _on_position_changed(self, position):
        if not self.loop and self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            duration = self.player.duration()
            if duration > 0 and position >= max(0, duration - 80):
                self._emit_finished()

    def _on_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if not self.loop:
                self._emit_finished()

    def stop(self):
        super().stop()
        self._switching_source = False
        self._finished_emitted = False
        self._blank_frame_skips = 0
        self._last_pixmap = None

    def close(self):
        self.stop()
        self.player.setVideoSink(None)
        self.player.setSource(QUrl())
