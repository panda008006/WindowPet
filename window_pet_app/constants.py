import sys
from pathlib import Path

from PySide6.QtCore import QSize


def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        base_path = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base_path = Path(__file__).resolve().parent.parent

    return base_path / relative_path


BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_ASSETS_DIR = BASE_DIR / "assets"
BUNDLED_ASSETS_DIR = resource_path("assets")
CONFIG_PATH = BASE_DIR / "config.json"
LOG_DIR = BASE_DIR / "logs"
APP_DISPLAY_NAME = "Window Pet"
LOG_PATH = LOG_DIR / "window_pet.log"
DEFAULT_GIF = BASE_DIR / "overlay.gif"
ICON_PATH = resource_path("icon.ico")
THUMBNAIL_SIZE = QSize(96, 96)
UI_BUTTON_PRIMARY_URL = resource_path("assets/UiAssets/ui-button-primary.png").as_posix()
UI_BUTTON_SECONDARY_URL = resource_path("assets/UiAssets/ui-button-secondary.png").as_posix()


MENU_STYLE = """
QMenu {
    background-color: rgba(255, 255, 255, 246);
    color: #0f172a;
    border: 1px solid rgba(15, 23, 42, 28);
    border-radius: 16px;
    padding: 8px;
}
QMenu::item {
    padding: 8px 28px 8px 12px;
    border-radius: 12px;
}
QMenu::item:selected {
    background-color: rgba(29, 78, 216, 28);
    color: #1d4ed8;
}
QMenu::item:disabled {
    color: #94a3b8;
    background-color: transparent;
}
QMenu::separator {
    height: 1px;
    background: rgba(15, 23, 42, 20);
    margin: 7px 5px;
}
QMenu::indicator {
    width: 15px;
    height: 15px;
    border-radius: 5px;
    border: 1px solid rgba(15, 23, 42, 52);
    background-color: rgba(255, 255, 255, 226);
}
QMenu::indicator:checked {
    background-color: #1d4ed8;
    border-color: #1d4ed8;
}
"""


APP_STYLE = """
QWidget {
    background-color: #edf8ff;
    color: #0f172a;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}
QWidget#ControlPanelWindow, QDialog, QMessageBox {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 #f9fdff,
        stop: 0.28 #eef8ff,
        stop: 0.66 #e7fbff,
        stop: 1 #f6fbff
    );
}
QDialog#GlassDialog, QDialog#AssetSetupDialog {
    background-color: rgba(240, 249, 255, 232);
    border: 1px solid rgba(29, 78, 216, 34);
    border-radius: 30px;
}
QFrame#AccountDialogSurface {
    background-color: rgba(255, 255, 255, 214);
    border: 1px solid rgba(29, 78, 216, 24);
    border-radius: 30px;
}
QLabel#AccountHeroIcon {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 rgba(255, 255, 255, 232),
        stop: 1 rgba(219, 245, 255, 210)
    );
    border: 1px solid rgba(29, 118, 216, 30);
    border-radius: 30px;
}
QLabel#AccountTitle {
    color: #12315b;
    font-size: 18pt;
    font-weight: 800;
}
QFrame#AccountSegment {
    background-color: rgba(226, 246, 255, 128);
    border: 1px solid rgba(29, 118, 216, 20);
    border-radius: 22px;
}
QPushButton#AccountSegmentButton {
    min-height: 36px;
    border: 0;
    border-radius: 17px;
    padding: 0 18px;
    color: #386381;
    background-color: transparent;
    font-weight: 750;
}
QPushButton#AccountSegmentButton:checked {
    color: #ffffff;
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #1d4ed8, stop: 1 #0ea5a5);
}
QFrame#AccountFormPanel {
    background-color: rgba(255, 255, 255, 140);
    border: 1px solid rgba(29, 78, 216, 18);
    border-radius: 24px;
}
QLabel#AccountFieldLabel {
    color: #44627a;
    font-size: 9pt;
    font-weight: 750;
    padding-left: 4px;
}
QFrame#AccountRulePanel {
    background-color: rgba(226, 246, 255, 104);
    border: 1px solid rgba(29, 118, 216, 26);
    border-radius: 22px;
}
QLineEdit#AccountInput {
    min-height: 34px;
    border: 1px solid rgba(29, 78, 216, 22);
    border-radius: 18px;
    padding: 8px 14px;
    background-color: rgba(255, 255, 255, 232);
    selection-background-color: #93c5fd;
}
QLineEdit#AccountInput:focus {
    border-color: rgba(29, 78, 216, 118);
    background-color: #ffffff;
}
QPushButton#AccountSecondaryButton {
    min-height: 34px;
    padding: 0 18px;
    border: 1px solid rgba(29, 78, 216, 22);
    border-radius: 17px;
    color: #386381;
    background-color: rgba(255, 255, 255, 164);
    font-weight: 650;
}
QLabel {
    background-color: transparent;
}
QFrame#ControlPanelHeader, QFrame#ControlPanelNavPanel, QFrame#MetricCard {
    background-color: rgba(255, 255, 255, 172);
    border: 1px solid rgba(29, 78, 216, 28);
    border-radius: 24px;
}
QFrame#ControlPanelNavPanel {
    background-color: transparent;
    border: 0;
    border-radius: 0;
}
QFrame#ControlPanelNavRail {
    background-color: rgba(255, 255, 255, 164);
    border: 1px solid rgba(29, 78, 216, 30);
    border-radius: 34px;
}
QStackedWidget#ControlPanelStack {
    background-color: transparent;
    border: 0;
}
QPushButton#RailNavButton {
    background-color: transparent;
    border: 0;
    padding: 0;
}
QPushButton#LoginPawButton {
    background-color: transparent;
    border: 0;
    padding: 0;
}
QLabel#MetricTitle {
    color: #64748b;
    font-weight: 600;
}
QLabel#MetricValue {
    color: #1d4ed8;
    font-size: 22pt;
    font-weight: 700;
}
QGroupBox {
    background-color: rgba(255, 255, 255, 156);
    border: 1px solid rgba(29, 78, 216, 28);
    border-radius: 22px;
    margin-top: 13px;
    padding-top: 10px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    color: #0f172a;
    background-color: rgba(245, 251, 255, 210);
    border-radius: 10px;
}
QPushButton {
    background-color: rgba(255, 255, 255, 178);
    border: 1px solid rgba(29, 78, 216, 34);
    border-radius: 16px;
    padding: 8px 13px;
    color: #0f172a;
}
QPushButton:hover {
    background-color: rgba(255, 255, 255, 224);
    border-color: rgba(29, 78, 216, 92);
    color: #1d4ed8;
}
QPushButton:pressed {
    background-color: rgba(29, 78, 216, 24);
    border-color: #1d4ed8;
}
QPushButton:disabled {
    color: #94a3b8;
    background-color: rgba(241, 248, 255, 150);
    border-color: rgba(148, 163, 184, 70);
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
    background-color: rgba(255, 255, 255, 184);
    border: 1px solid rgba(29, 78, 216, 34);
    border-radius: 16px;
    padding: 7px 10px;
    color: #0f172a;
    selection-background-color: rgba(162, 209, 255, 210);
    selection-color: #0f3769;
    min-height: 19px;
}
QTextEdit, QPlainTextEdit {
    padding: 9px;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: rgba(29, 78, 216, 118);
    background-color: rgba(255, 255, 255, 232);
}
QTimeEdit {
    background-color: rgba(255, 255, 255, 184);
    border: 1px solid rgba(29, 78, 216, 34);
    border-radius: 16px;
    padding: 7px 10px;
    color: #0f172a;
    selection-background-color: rgba(162, 209, 255, 210);
    selection-color: #0f3769;
    min-height: 19px;
}
QTimeEdit:hover, QTimeEdit:focus {
    border-color: rgba(29, 78, 216, 118);
    background-color: rgba(255, 255, 255, 232);
}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    width: 18px;
    border: 0;
    background: transparent;
}
QTimeEdit::up-button, QTimeEdit::down-button {
    width: 18px;
    border: 0;
    background: transparent;
}
QListWidget {
    background-color: rgba(255, 255, 255, 144);
    border: 1px solid rgba(29, 78, 216, 28);
    border-radius: 22px;
    padding: 8px;
    outline: 0;
}
QListWidget::item {
    background-color: transparent;
    border-radius: 16px;
    padding: 8px;
    color: #0f172a;
}
QListWidget::item:selected {
    background-color: rgba(29, 78, 216, 36);
    color: #1d4ed8;
}
QListWidget::item:hover:!selected {
    background-color: rgba(255, 255, 255, 168);
}
QListWidget#PetLibraryList {
    background-color: transparent;
    border: 0;
    border-radius: 0;
    padding: 4px;
}
QListWidget#PetLibraryList::item {
    background-color: transparent;
    border-radius: 18px;
    padding: 6px;
}
QListWidget#PetLibraryList::item:selected {
    background-color: rgba(29, 78, 216, 26);
    color: #0f3769;
}
QListWidget#PetLibraryList::item:hover:!selected {
    background-color: rgba(255, 255, 255, 90);
}
QListWidget#PetLibraryList QScrollBar:vertical,
QListWidget#PetLibraryList QScrollBar:horizontal {
    background: transparent;
    width: 0;
    height: 0;
}
QComboBox {
    background-color: rgba(255, 255, 255, 184);
    border: 1px solid rgba(29, 78, 216, 34);
    border-radius: 16px;
    padding: 7px 30px 7px 10px;
    color: #0f172a;
    min-height: 19px;
}
QComboBox:hover, QComboBox:focus {
    border-color: rgba(29, 78, 216, 118);
    background-color: rgba(255, 255, 255, 232);
}
QComboBox::drop-down {
    border: 0;
    width: 28px;
}
QComboBox QAbstractItemView {
    background-color: rgba(255, 255, 255, 246);
    color: #0f172a;
    border: 1px solid rgba(29, 78, 216, 88);
    border-radius: 16px;
    selection-background-color: rgba(29, 78, 216, 36);
    selection-color: #1d4ed8;
    outline: 0;
}
QCalendarWidget {
    background-color: rgba(255, 255, 255, 150);
    border: 1px solid rgba(29, 78, 216, 30);
    border-radius: 22px;
    selection-background-color: #1d4ed8;
    selection-color: #ffffff;
}
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background-color: rgba(245, 251, 255, 176);
    border-top-left-radius: 22px;
    border-top-right-radius: 22px;
}
QCalendarWidget QToolButton {
    background-color: rgba(255, 255, 255, 164);
    border: 1px solid rgba(29, 78, 216, 28);
    border-radius: 14px;
    color: #0f172a;
    margin: 4px;
    padding: 5px 8px;
    font-weight: 600;
}
QCalendarWidget QToolButton:hover {
    background-color: rgba(255, 255, 255, 244);
    border-color: rgba(29, 78, 216, 88);
    color: #1d4ed8;
}
QCalendarWidget QMenu {
    background-color: rgba(255, 255, 255, 246);
    color: #0f172a;
    border: 1px solid rgba(15, 23, 42, 28);
    border-radius: 16px;
}
QCalendarWidget QSpinBox {
    background-color: rgba(255, 255, 255, 230);
    border: 1px solid rgba(15, 23, 42, 28);
    border-radius: 14px;
    padding: 5px 8px;
}
QCalendarWidget QAbstractItemView {
    background-color: #f6fbff;
    alternate-background-color: #eaf7ff;
    border: 0;
    border-bottom-left-radius: 22px;
    border-bottom-right-radius: 22px;
    color: #0f172a;
    selection-background-color: #1d4ed8;
    selection-color: #ffffff;
    outline: 0;
}
QCalendarWidget QAbstractItemView:enabled {
    background-color: #f6fbff;
    color: #0f172a;
    selection-background-color: #1d4ed8;
    selection-color: #ffffff;
}
QCalendarWidget QAbstractItemView:disabled {
    background-color: #f6fbff;
    color: #94a3b8;
}
QSlider::groove:horizontal {
    height: 8px;
    border-radius: 4px;
    background-color: rgba(148, 163, 184, 72);
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #1d4ed8, stop: 1 #0ea5a5);
    border-radius: 4px;
}
QSlider::handle:horizontal {
    background-color: #ffffff;
    border: 2px solid #1d4ed8;
    width: 19px;
    height: 19px;
    margin: -6px 0;
    border-radius: 10px;
}
QCheckBox {
    background-color: transparent;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 7px;
    border: 1px solid rgba(15, 23, 42, 48);
    background-color: rgba(255, 255, 255, 230);
}
QCheckBox::indicator:hover {
    border-color: #1d4ed8;
}
QCheckBox::indicator:checked {
    background-color: #1d4ed8;
    border-color: #1d4ed8;
}
QLabel#SectionTitle {
    color: #0f172a;
    font-size: 13pt;
    font-weight: 650;
}
QLabel#SubtleLabel {
    color: #64748b;
}
QLabel#StatusPill {
    background-color: rgba(255, 255, 255, 168);
    border: 1px solid rgba(29, 78, 216, 28);
    border-radius: 16px;
    padding: 7px 12px;
    color: #475569;
    font-weight: 600;
}
QLabel#UpdateStatus {
    background-color: rgba(255, 251, 235, 222);
    border: 1px solid rgba(245, 158, 11, 96);
    border-radius: 14px;
    padding: 7px 12px;
    color: #92400e;
    font-weight: 650;
}
QFrame#Panel {
    background-color: rgba(255, 255, 255, 132);
    border: 1px solid rgba(29, 78, 216, 24);
    border-radius: 22px;
}
QFrame#ToolSelectorPanel {
    background-color: transparent;
    border: 0;
}
QPushButton#ToolChoiceButton {
    background-color: rgba(255, 255, 255, 112);
    border: 1px solid rgba(29, 78, 216, 24);
    border-radius: 24px;
    padding: 10px 14px;
    color: #0f172a;
    font-weight: 650;
    text-align: left;
}
QPushButton#ToolChoiceButton:hover {
    background-color: rgba(255, 255, 255, 176);
    border-color: rgba(29, 78, 216, 66);
    color: #1d4ed8;
}
QPushButton#ToolChoiceButton:checked {
    background-color: rgba(255, 255, 255, 204);
    border-color: rgba(29, 78, 216, 104);
    color: #1d4ed8;
}
QStackedWidget#ToolsStack {
    background-color: transparent;
    border: 0;
}
QFrame#ToolSurfacePanel {
    background-color: transparent;
    border: 0;
    border-radius: 0;
}
QFrame#ToolTargetRow, QFrame#ToolSettingRow {
    background-color: rgba(255, 255, 255, 124);
    border: 1px solid rgba(29, 78, 216, 22);
    border-radius: 20px;
}
QFrame#WallpaperSlotCard {
    background-color: rgba(255, 255, 255, 150);
    border: 1px solid rgba(29, 78, 216, 34);
    border-radius: 22px;
}
QFrame#WallpaperSlotCard:hover {
    background-color: rgba(255, 255, 255, 206);
    border-color: rgba(29, 78, 216, 82);
}
QLabel#WallpaperPreview {
    background-color: rgba(224, 242, 254, 128);
    border: 1px solid rgba(29, 78, 216, 24);
    border-radius: 16px;
}
QPushButton#ToolPrimaryButton {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #1d4ed8, stop: 1 #0ea5a5);
    border-color: rgba(29, 78, 216, 100);
    border-radius: 16px;
    color: #ffffff;
    font-weight: 650;
}
QPushButton#ToolPrimaryButton:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #1e40af, stop: 1 #0f8f8f);
    border-color: rgba(29, 78, 216, 150);
    color: #ffffff;
}
QPushButton#DangerButton {
    background-color: rgba(255, 255, 255, 170);
    border: 1px solid rgba(220, 38, 38, 72);
    border-radius: 16px;
    color: #b91c1c;
    font-weight: 700;
}
QPushButton#DangerButton:hover {
    background-color: rgba(254, 226, 226, 210);
    border-color: rgba(220, 38, 38, 120);
    color: #991b1b;
}
QLabel#ToolStatusLabel {
    color: #0f766e;
    background-color: rgba(255, 255, 255, 124);
    border: 1px solid rgba(29, 78, 216, 22);
    border-radius: 18px;
    padding: 9px 12px;
    font-weight: 600;
}
QFrame#RedeemCard, QFrame#ActivityPanel {
    background-color: rgba(255, 255, 255, 124);
    border: 1px solid rgba(29, 78, 216, 24);
    border-radius: 26px;
}
QFrame#ScheduleCalendarPanel, QFrame#SchedulePanel {
    background-color: rgba(255, 255, 255, 124);
    border: 1px solid rgba(29, 78, 216, 24);
    border-radius: 26px;
}
QFrame#SettingsCard {
    background-color: rgba(255, 255, 255, 124);
    border: 1px solid rgba(29, 78, 216, 24);
    border-radius: 26px;
}
QFrame#SettingsInfoRow {
    background-color: rgba(255, 255, 255, 108);
    border: 1px solid rgba(29, 78, 216, 20);
    border-radius: 20px;
}
QFrame#RedeemCard {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 rgba(255, 255, 255, 190),
        stop: 0.42 rgba(226, 246, 255, 146),
        stop: 1 rgba(198, 241, 255, 128)
    );
    border: 1px solid rgba(29, 118, 216, 46);
}
QFrame#ScheduleCalendarPanel {
    background: qlineargradient(
        x1: 0, y1: 0, x2: 1, y2: 1,
        stop: 0 rgba(255, 255, 255, 164),
        stop: 0.5 rgba(232, 246, 255, 118),
        stop: 1 rgba(218, 249, 252, 112)
    );
}
QLabel#ActivityCardTitle, QLabel#RedeemCardTitle {
    color: #0f172a;
    font-size: 12pt;
    font-weight: 700;
}
QLabel#ActivityBadge {
    background-color: rgba(255, 255, 255, 156);
    border: 1px solid rgba(29, 78, 216, 28);
    border-radius: 16px;
    padding: 6px 11px;
    color: #1d4ed8;
    font-weight: 650;
}
QLabel#ActivityEggCount {
    color: #1d4ed8;
    font-size: 38pt;
    font-weight: 800;
}
QLabel#ActivityEggHint {
    color: #64748b;
    font-weight: 650;
}
QFrame#ActivityAccountPanel {
    background-color: rgba(255, 255, 255, 162);
    border: 1px solid rgba(29, 78, 216, 28);
    border-radius: 18px;
}
QLabel#ActivityAccountText {
    color: #315a7e;
    font-weight: 650;
}
QLabel#ActivityInviteCode {
    color: #0f3769;
    font-size: 12pt;
    font-weight: 800;
}
QLineEdit#RedeemCodeInput {
    background-color: rgba(255, 255, 255, 218);
    border: 1px solid rgba(29, 118, 216, 62);
    border-radius: 18px;
    padding: 9px 12px;
    color: #0f3769;
    font-weight: 650;
}
QLineEdit#RedeemCodeInput:focus,
QLineEdit#RedeemCodeInput:hover {
    border-color: rgba(29, 118, 216, 126);
    background-color: rgba(255, 255, 255, 240);
}
QFrame#ActivityRulePanel {
    background-color: rgba(255, 255, 255, 126);
    border: 1px solid rgba(29, 78, 216, 24);
    border-radius: 20px;
}
QLabel#ActivityRuleText {
    color: #315a7e;
    font-weight: 650;
}
QLabel#SettingsValue {
    color: #0f172a;
    font-weight: 600;
}
QTextEdit#SettingsNotes {
    background-color: rgba(255, 255, 255, 112);
    border: 1px solid rgba(29, 78, 216, 22);
    border-radius: 20px;
    padding: 10px;
}
QListWidget#ActivityPetGallery {
    background-color: rgba(255, 255, 255, 112);
    border: 1px solid rgba(29, 78, 216, 22);
    border-radius: 20px;
    padding: 8px;
}
QListWidget#ActivityPetGallery::item {
    background-color: transparent;
    border: none;
    margin: 2px;
}
QListWidget#ActivityPetGallery::item:selected {
    background-color: transparent;
}
QListWidget#ScheduleReminderList {
    background-color: rgba(255, 255, 255, 112);
    border: 1px solid rgba(29, 78, 216, 22);
    border-radius: 20px;
    padding: 8px;
}
QListWidget#ScheduleReminderList::item {
    background-color: rgba(255, 255, 255, 120);
    border: 1px solid rgba(29, 78, 216, 18);
    border-radius: 16px;
    padding: 10px 12px;
    margin: 3px 0;
}
QListWidget#ScheduleReminderList::item:selected {
    background-color: rgba(29, 78, 216, 32);
    color: #1d4ed8;
}
QFrame#SearchResultCard {
    background-color: rgba(255, 255, 255, 132);
    border: 1px solid rgba(29, 78, 216, 24);
    border-radius: 20px;
}
QFrame#SearchResultCard:hover {
    background-color: rgba(255, 255, 255, 188);
    border-color: rgba(29, 78, 216, 82);
}
QLabel#SearchPath {
    color: #64748b;
    font-size: 9pt;
}
QLabel#SearchMeta {
    color: #0f766e;
    font-size: 9pt;
    font-weight: 600;
}
QScrollArea {
    background-color: transparent;
    border: 0;
}
QScrollArea > QWidget > QWidget {
    background-color: transparent;
}
QScrollBar:vertical {
    background: transparent;
    width: 4px;
    margin: 0;
    border-radius: 2px;
}
QScrollBar::handle:vertical {
    background: rgba(100, 116, 139, 44);
    border-radius: 2px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: rgba(29, 78, 216, 92);
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 4px;
    margin: 0;
    border-radius: 2px;
}
QScrollBar::handle:horizontal {
    background: rgba(100, 116, 139, 44);
    border-radius: 2px;
    min-width: 24px;
}
QScrollBar::handle:horizontal:hover {
    background: rgba(29, 78, 216, 92);
}
QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
}
QToolTip {
    background-color: rgba(255, 255, 255, 246);
    color: #0f172a;
    border: 1px solid rgba(15, 23, 42, 28);
    border-radius: 12px;
    padding: 7px;
}
QSplitter::handle {
    background-color: rgba(148, 163, 184, 70);
}
"""

PET_GAME_MENU_STYLE = """
QMenu {
    background-color: #fff1cf;
    color: #5a4930;
    border: 3px solid #5f4725;
    border-radius: 18px;
    padding: 8px;
}
QMenu::item {
    padding: 8px 28px 8px 12px;
    border-radius: 12px;
}
QMenu::item:selected {
    background-color: #ffd34e;
    color: #4c351b;
}
QMenu::item:disabled {
    color: #a99c82;
    background-color: transparent;
}
QMenu::separator {
    height: 2px;
    background: rgba(95, 71, 37, 80);
    margin: 7px 5px;
}
QMenu::indicator {
    width: 15px;
    height: 15px;
    border-radius: 6px;
    border: 2px solid #6b4f2b;
    background-color: #fff7df;
}
QMenu::indicator:checked {
    background-color: #ffd34e;
    border-color: #5f4725;
}
"""


PET_GAME_STYLE = """
QWidget {
    background-color: transparent;
    color: #5a4930;
}
QWidget#ControlPanelWindow {
    background-color: #5bc7e5;
    color: #5a4930;
}
QDialog, QMessageBox {
    background-color: #fff1cf;
    color: #5a4930;
}
QDialog#GlassDialog, QDialog#AssetSetupDialog {
    background-color: #fff1cf;
    border: 4px solid #5f4725;
    border-radius: 34px;
}
QFrame#AccountDialogSurface {
    background-color: #fff7df;
    border: 4px solid #5f4725;
    border-radius: 32px;
}
QLabel#AccountHeroIcon {
    background-color: #ffe28a;
    border: 3px solid #5f4725;
    border-radius: 30px;
}
QLabel#AccountTitle {
    color: #4c351b;
    font-size: 18pt;
    font-weight: 800;
}
QFrame#AccountSegment {
    background-color: #efe2be;
    border: 3px solid #8a7753;
    border-radius: 24px;
}
QPushButton#AccountSegmentButton {
    min-height: 36px;
    border: 0;
    border-radius: 18px;
    padding: 0 18px;
    color: #6b5a3a;
    background-color: transparent;
    font-weight: 750;
}
QPushButton#AccountSegmentButton:checked {
    color: #4c351b;
    background-color: #ffd34e;
}
QFrame#AccountFormPanel, QFrame#AccountRulePanel {
    background-color: #fff7df;
    border: 3px solid #b9a777;
    border-radius: 24px;
}
QLabel#AccountFieldLabel {
    color: #6b5a3a;
    font-size: 9pt;
    font-weight: 750;
    padding-left: 4px;
}
QLineEdit#AccountInput, QLineEdit#RedeemCodeInput {
    min-height: 34px;
    border: 3px solid #b9a777;
    border-radius: 18px;
    padding: 8px 14px;
    background-color: #fffaf0;
    color: #4c351b;
    selection-background-color: #ffd34e;
    selection-color: #4c351b;
}
QLineEdit#AccountInput:focus, QLineEdit#RedeemCodeInput:focus,
QLineEdit#AccountInput:hover, QLineEdit#RedeemCodeInput:hover {
    border-color: #5f4725;
    background-color: #ffffff;
}
QPushButton#AccountSecondaryButton {
    min-height: 34px;
    padding: 0 18px;
    border: 3px solid #6a4a34;
    border-radius: 18px;
    color: #4c3425;
    background-color: #fff8e8;
    border-image: url("__UI_BUTTON_SECONDARY_URL__") 18 42 18 42 stretch stretch;
    font-weight: 700;
}
QPushButton#AccountSecondaryButton:hover {
    background-color: #ffe6ef;
    border-image: none;
    color: #4c3425;
}
QLabel {
    background-color: transparent;
}
QFrame#ControlPanelHeader, QFrame#MetricCard {
    background-color: rgba(255, 248, 232, 226);
    border: 3px solid #6a4a34;
    border-radius: 24px;
}
QFrame#ControlPanelNavPanel {
    background-color: transparent;
    border: 0;
    border-radius: 0;
}
QFrame#ControlPanelNavRail {
    background-color: rgba(255, 238, 246, 228);
    border: 4px solid #6a4a34;
    border-radius: 36px;
}
QStackedWidget#ControlPanelStack, QStackedWidget#ToolsStack {
    background-color: transparent;
    border: 0;
}
QPushButton#RailNavButton, QPushButton#LoginPawButton {
    background-color: transparent;
    border: 0;
    padding: 0;
}
QLabel#MetricTitle {
    color: #7b6a49;
    font-weight: 700;
}
QLabel#MetricValue {
    color: #4c351b;
    font-size: 22pt;
    font-weight: 800;
}
QGroupBox {
    background-color: #fff1cf;
    border: 3px solid #5f4725;
    border-radius: 24px;
    margin-top: 13px;
    padding-top: 10px;
    color: #4c351b;
    font-weight: 700;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    color: #4c351b;
    background-color: #fff7df;
    border-radius: 12px;
}
QPushButton {
    background-color: #fff8e8;
    border: 3px solid #6a4a34;
    border-image: url("__UI_BUTTON_SECONDARY_URL__") 18 42 18 42 stretch stretch;
    border-radius: 18px;
    padding: 8px 13px;
    color: #4c3425;
    font-weight: 700;
}
QPushButton:hover {
    background-color: #ffe6ef;
    border-image: none;
    border-color: #4c3425;
    color: #4c3425;
}
QPushButton:pressed {
    background-color: #ffd8e5;
    border-image: none;
    border-color: #4c3425;
}
QPushButton:disabled {
    color: #9d9279;
    background-color: #e7ddc6;
    border-image: none;
    border-color: #b9a777;
}
QPushButton#ToolPrimaryButton {
    background-color: #ffe993;
    border: 3px solid #6a4a34;
    border-image: url("__UI_BUTTON_PRIMARY_URL__") 18 52 18 52 stretch stretch;
    border-radius: 18px;
    color: #4c3425;
    font-weight: 800;
}
QPushButton#ToolPrimaryButton:hover {
    background-color: #ffd8e5;
    border-image: none;
    border-color: #4c3425;
    color: #4c3425;
}
QPushButton#DangerButton {
    background-color: #ffe3d5;
    border: 3px solid #8b3f2a;
    border-radius: 18px;
    color: #8b2f1a;
    font-weight: 800;
}
QPushButton#DangerButton:hover {
    background-color: #ffd1bc;
    border-color: #6f2b1b;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #fffaf0;
    border: 3px solid #b9a777;
    border-radius: 18px;
    padding: 7px 10px;
    color: #4c351b;
    selection-background-color: #ffd34e;
    selection-color: #4c351b;
    min-height: 19px;
}
QTextEdit, QPlainTextEdit {
    padding: 10px;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus,
QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover, QComboBox:hover {
    background-color: #ffffff;
    border-color: #5f4725;
}
QComboBox::drop-down {
    border: 0;
    width: 30px;
}
QComboBox QAbstractItemView {
    background-color: #fff1cf;
    color: #5a4930;
    border: 3px solid #5f4725;
    border-radius: 16px;
    selection-background-color: #ffd34e;
    selection-color: #4c351b;
}
QListWidget {
    background-color: #fff7df;
    border: 3px solid #b9a777;
    border-radius: 22px;
    color: #5a4930;
    padding: 8px;
}
QListWidget::item {
    border-radius: 16px;
    padding: 8px;
}
QListWidget::item:selected {
    background-color: #ffe28a;
    color: #4c351b;
}
QListWidget::item:hover:!selected {
    background-color: #fff1cf;
}
QListWidget#PetLibraryList, QListWidget#ActivityPetGallery, QListWidget#ScheduleReminderList {
    background-color: rgba(255, 247, 223, 230);
    border: 4px solid #5f4725;
    border-radius: 28px;
    padding: 10px;
}
QListWidget#PetLibraryList::item, QListWidget#ActivityPetGallery::item {
    background-color: transparent;
    border: none;
    margin: 2px;
}
QListWidget#PetLibraryList::item:selected, QListWidget#ActivityPetGallery::item:selected {
    background-color: transparent;
}
QListWidget#ScheduleReminderList::item {
    background-color: #fffaf0;
    border: 3px solid #b9a777;
    border-radius: 18px;
    padding: 10px 12px;
    margin: 3px 0;
}
QListWidget#ScheduleReminderList::item:selected {
    background-color: #ffe28a;
    color: #4c351b;
}
QCalendarWidget {
    background-color: #fff7df;
    border: 3px solid #5f4725;
    border-radius: 22px;
    color: #5a4930;
}
QCalendarWidget QWidget#qt_calendar_navigationbar {
    background-color: #fff1cf;
    border-radius: 18px;
}
QCalendarWidget QToolButton {
    background-color: #ffd34e;
    border: 2px solid #5f4725;
    border-radius: 15px;
    color: #4c351b;
    padding: 5px 9px;
    font-weight: 800;
}
QCalendarWidget QToolButton:hover {
    background-color: #ffe28a;
}
QCalendarWidget QMenu {
    background-color: #fff1cf;
    border: 3px solid #5f4725;
    border-radius: 16px;
}
QCalendarWidget QSpinBox {
    background-color: #fffaf0;
    border: 2px solid #b9a777;
    border-radius: 12px;
}
QCalendarWidget QAbstractItemView {
    background-color: #fffaf0;
    selection-background-color: #ffd34e;
    selection-color: #4c351b;
    border: 0;
}
QSlider::groove:horizontal {
    height: 12px;
    background-color: #d8c896;
    border: 2px solid #8a7753;
    border-radius: 7px;
}
QSlider::sub-page:horizontal {
    background-color: #ffd34e;
    border-radius: 7px;
}
QSlider::handle:horizontal {
    background-color: #fff1cf;
    border: 3px solid #5f4725;
    width: 22px;
    height: 22px;
    margin: -7px 0;
    border-radius: 12px;
}
QCheckBox {
    background-color: transparent;
    spacing: 8px;
    color: #5a4930;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 7px;
    border: 3px solid #6b4f2b;
    background-color: #fff7df;
}
QCheckBox::indicator:hover {
    background-color: #ffe28a;
}
QCheckBox::indicator:checked {
    background-color: #ffd34e;
    border-color: #5f4725;
}
QLabel#SectionTitle {
    color: #4c351b;
    font-size: 14pt;
    font-weight: 800;
}
QLabel#SubtleLabel {
    color: #7b6a49;
}
QLabel#StatusPill, QLabel#ActivityBadge, QLabel#UpdateStatus {
    background-color: #fff1cf;
    border: 3px solid #b9a777;
    border-radius: 18px;
    padding: 7px 12px;
    color: #5a4930;
    font-weight: 800;
}
QFrame#Panel, QFrame#SettingsCard, QFrame#RedeemCard, QFrame#ActivityPanel,
QFrame#ScheduleCalendarPanel, QFrame#SchedulePanel, QFrame#ActivityAccountPanel,
QFrame#ActivityRulePanel, QFrame#SettingsInfoRow, QFrame#ToolTargetRow,
QFrame#ToolSettingRow, QFrame#WallpaperSlotCard, QFrame#SearchResultCard,
QFrame#MedalHeaderCard, QFrame#MedalHiddenCard {
    background-color: rgba(255, 241, 207, 235);
    border: 4px solid #5f4725;
    border-radius: 28px;
}
QLabel#MedalPageTitle {
    color: #4c351b;
    font-size: 18pt;
    font-weight: 900;
}
QLabel#MedalPageSubtitle, QLabel#MedalHiddenNote {
    color: #6b5a3a;
    font-weight: 700;
}
QLabel#MedalSummary, QLabel#MedalNote {
    color: #4c351b;
    background-color: #fff1cf;
    border: 3px solid #b9a777;
    border-radius: 16px;
    padding: 7px 11px;
    font-weight: 800;
}
QFrame#MedalCard {
    background-color: rgba(239, 226, 190, 232);
    border: 3px solid #b9a777;
    border-radius: 22px;
}
QFrame#MedalCard[unlocked="true"] {
    background-color: #fff7df;
    border-color: #5f4725;
}
QLabel#MedalIcon {
    color: #7b6a49;
    background-color: #e7ddc6;
    border: 2px solid #b9a777;
    border-radius: 23px;
    font-size: 17pt;
    font-weight: 900;
}
QFrame#MedalCard[unlocked="true"] QLabel#MedalIcon {
    color: #4c351b;
    background-color: #ffd34e;
    border-color: #5f4725;
}
QLabel#MedalCardTitle, QLabel#MedalHiddenTitle {
    color: #4c351b;
    font-size: 11pt;
    font-weight: 900;
}
QLabel#MedalCardDetail {
    color: #7b6a49;
    font-size: 9pt;
    font-weight: 650;
}
QLabel#MedalStatus {
    color: #6b5a3a;
    font-size: 8pt;
    font-weight: 800;
}
QFrame#MedalCard[unlocked="true"] QLabel#MedalStatus {
    color: #1f7a43;
}
QPushButton#MedalSecondaryButton {
    min-height: 34px;
    padding: 0 16px;
    color: #5a4930;
    background-color: #fff7df;
    border: 3px solid #b9a777;
    border-radius: 17px;
    font-weight: 800;
}
QPushButton#MedalSecondaryButton:hover {
    color: #4c351b;
    background-color: #ffd34e;
    border-color: #5f4725;
}
QFrame#RedeemCard, QFrame#ScheduleCalendarPanel {
    background-color: rgba(255, 247, 223, 240);
}
QFrame#ToolSelectorPanel, QFrame#ToolSurfacePanel {
    background-color: transparent;
    border: 0;
    border-radius: 0;
}
QPushButton#ToolChoiceButton {
    background-color: #fff1cf;
    border: 3px solid #b9a777;
    border-radius: 24px;
    padding: 10px 14px;
    color: #5a4930;
    font-weight: 800;
    text-align: left;
}
QPushButton#ToolChoiceButton:hover, QPushButton#ToolChoiceButton:checked {
    background-color: #ffd34e;
    border-color: #5f4725;
    color: #4c351b;
}
QLabel#WallpaperPreview {
    background-color: #8adced;
    border: 3px solid #5f4725;
    border-radius: 18px;
}
QLabel#ToolStatusLabel {
    color: #4c351b;
    background-color: #fff1cf;
    border: 3px solid #b9a777;
    border-radius: 18px;
    padding: 9px 12px;
    font-weight: 800;
}
QLabel#ActivityCardTitle, QLabel#RedeemCardTitle {
    color: #4c351b;
    font-size: 12pt;
    font-weight: 800;
}
QLabel#ActivityEggCount {
    color: #4c351b;
    font-size: 38pt;
    font-weight: 900;
}
QLabel#ActivityEggHint, QLabel#ActivityAccountText, QLabel#ActivityRuleText,
QLabel#SettingsValue, QLabel#SearchPath, QLabel#SearchMeta {
    color: #6b5a3a;
    font-weight: 700;
}
QLabel#ActivityInviteCode {
    color: #4c351b;
    font-size: 12pt;
    font-weight: 900;
}
QTextEdit#SettingsNotes {
    background-color: #fffaf0;
    border: 3px solid #b9a777;
    border-radius: 20px;
    padding: 10px;
}
QScrollArea, QScrollArea > QWidget > QWidget {
    background-color: transparent;
    border: 0;
}
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #b9a777;
    border: 2px solid #6b4f2b;
    border-radius: 5px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover {
    background: #ffd34e;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
    margin: 0;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #b9a777;
    border: 2px solid #6b4f2b;
    border-radius: 5px;
    min-width: 28px;
}
QScrollBar::handle:horizontal:hover {
    background: #ffd34e;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QToolTip {
    background-color: #fff1cf;
    color: #5a4930;
    border: 3px solid #5f4725;
    border-radius: 14px;
    padding: 7px;
}
QSplitter::handle {
    background-color: #b9a777;
}
"""


PET_GAME_STYLE = (
    PET_GAME_STYLE
    .replace("__UI_BUTTON_PRIMARY_URL__", UI_BUTTON_PRIMARY_URL)
    .replace("__UI_BUTTON_SECONDARY_URL__", UI_BUTTON_SECONDARY_URL)
)

POLISHED_PET_STYLE = """
QWidget {
    color: #26334a;
    font-family: "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI", sans-serif;
}
QWidget#ControlPanelWindow {
    background-color: transparent;
}
QDialog, QMessageBox {
    background-color: #fffaf7;
    color: #26334a;
}
QDialog#GlassDialog, QDialog#AssetSetupDialog {
    background-color: #fffaf7;
    border: 1px solid #e3d9d2;
    border-radius: 26px;
}
QFrame#AccountDialogSurface {
    background-color: #fffdf9;
    border: 1px solid #e3d9d2;
    border-radius: 26px;
}
QLabel#AccountHeroIcon {
    background-color: #fff0f2;
    border: 1px solid #ffc7cd;
    border-radius: 28px;
}
QLabel#AccountTitle {
    color: #26334a;
    font-size: 18pt;
    font-weight: 800;
}
QFrame#AccountSegment {
    background-color: #f3f5f7;
    border: 1px solid #e0e6ea;
    border-radius: 20px;
}
QPushButton#AccountSegmentButton {
    border: 0;
    border-radius: 16px;
    color: #718096;
    background-color: transparent;
}
QPushButton#AccountSegmentButton:checked {
    color: #d94f61;
    background-color: #ffe6e9;
}
QFrame#AccountFormPanel, QFrame#AccountRulePanel {
    background-color: #ffffff;
    border: 1px solid #ebe3de;
    border-radius: 20px;
}
QLabel#AccountFieldLabel {
    color: #718096;
}
QFrame#ControlPanelHeader, QFrame#MetricCard {
    background-color: rgba(255, 253, 249, 236);
    border: 1px solid rgba(221, 212, 204, 210);
    border-radius: 22px;
}
QFrame#ControlPanelNavRail {
    background-color: rgba(255, 255, 255, 225);
    border: 1px solid rgba(220, 230, 226, 200);
    border-radius: 28px;
}
QFrame#ControlPanelNavPanel, QStackedWidget#ControlPanelStack, QStackedWidget#ToolsStack {
    background-color: transparent;
    border: 0;
}
QPushButton#RailNavButton, QPushButton#LoginPawButton {
    background-color: transparent;
    border: 0;
    padding: 0;
}
QGroupBox {
    background-color: rgba(255, 253, 249, 236);
    border: 1px solid #ddd4cc;
    border-radius: 20px;
    color: #26334a;
    font-weight: 700;
}
QGroupBox::title {
    color: #26334a;
    background-color: #fffdf9;
    border-radius: 9px;
}
QPushButton {
    background-color: #fffdf9;
    border: 1px solid #ddd4cc;
    border-image: none;
    border-radius: 15px;
    padding: 8px 14px;
    color: #344057;
    font-weight: 700;
}
QPushButton:hover {
    background-color: #fff0f2;
    border-color: #ffabb4;
    color: #c74759;
}
QPushButton:pressed {
    background-color: #ffe2e6;
    border-color: #ff7f87;
}
QPushButton:disabled {
    color: #a3adba;
    background-color: #f1f3f5;
    border-color: #e1e6ea;
}
QPushButton#ToolPrimaryButton {
    color: #ffffff;
    background-color: #ff7f87;
    border: 1px solid #f16f79;
    border-image: none;
    border-radius: 15px;
    font-weight: 800;
}
QPushButton#ToolPrimaryButton:hover {
    color: #ffffff;
    background-color: #f26f7a;
    border-color: #dc5e6b;
}
QPushButton#DangerButton {
    color: #b6404d;
    background-color: #fff1f2;
    border: 1px solid #ffc7cd;
    border-radius: 15px;
}
QPushButton#DangerButton:hover {
    background-color: #ffe2e6;
    border-color: #ff939e;
}
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox,
QLineEdit#AccountInput, QLineEdit#RedeemCodeInput {
    color: #26334a;
    background-color: #ffffff;
    border: 1px solid #ddd4cc;
    border-radius: 14px;
    padding: 8px 11px;
    selection-background-color: #ffd9de;
    selection-color: #26334a;
}
QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover, QSpinBox:hover,
QDoubleSpinBox:hover, QComboBox:hover, QLineEdit#AccountInput:hover,
QLineEdit#RedeemCodeInput:hover {
    background-color: #ffffff;
    border-color: #b9ccc7;
}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus,
QDoubleSpinBox:focus, QComboBox:focus, QLineEdit#AccountInput:focus,
QLineEdit#RedeemCodeInput:focus {
    background-color: #ffffff;
    border-color: #ff8f99;
}
QComboBox QAbstractItemView {
    color: #26334a;
    background-color: #fffdf9;
    border: 1px solid #ddd4cc;
    border-radius: 14px;
    selection-background-color: #ffe6e9;
    selection-color: #c74759;
}
QListWidget {
    color: #26334a;
    background-color: rgba(255, 253, 249, 232);
    border: 1px solid #ddd4cc;
    border-radius: 20px;
}
QListWidget::item:selected {
    background-color: #ffe6e9;
    color: #c74759;
    border: 1px solid rgba(199, 71, 89, 110);
    border-radius: 12px;
}
QListWidget::item:hover:!selected {
    background-color: #f0faf7;
}
QListWidget#PetLibraryList, QListWidget#ActivityPetGallery, QListWidget#ScheduleReminderList {
    background-color: rgba(255, 253, 249, 234);
    border: 1px solid #ddd4cc;
    border-radius: 24px;
    padding: 9px;
}
QListWidget#ScheduleReminderList::item {
    background-color: #ffffff;
    border: 1px solid #e5ddd7;
    border-radius: 15px;
    margin: 3px 0;
}
QSlider::groove:horizontal {
    height: 8px;
    background-color: #e6ebe9;
    border: 0;
    border-radius: 4px;
}
QSlider::sub-page:horizontal {
    background-color: #57c7b8;
    border-radius: 4px;
}
QSlider::handle:horizontal {
    background-color: #ffffff;
    border: 2px solid #57c7b8;
    width: 18px;
    height: 18px;
    margin: -5px 0;
    border-radius: 10px;
}
QCheckBox {
    color: #344057;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 6px;
    border: 1px solid #cfd8dc;
    background-color: #ffffff;
}
QCheckBox::indicator:hover {
    border-color: #57c7b8;
}
QCheckBox::indicator:checked {
    background-color: #57c7b8;
    border-color: #45b5a6;
}
QLabel#SectionTitle {
    color: #26334a;
    font-size: 15pt;
    font-weight: 800;
}
QLabel#SubtleLabel, QLabel#ActivityEggHint, QLabel#ActivityAccountText,
QLabel#ActivityRuleText, QLabel#SettingsValue, QLabel#SearchPath, QLabel#SearchMeta {
    color: #718096;
    font-weight: 600;
    font-size: 13px;
}
QLabel#StatusPill, QLabel#ActivityBadge, QLabel#UpdateStatus {
    color: #526176;
    background-color: #fffdf9;
    border: 1px solid #ddd4cc;
    border-radius: 15px;
    padding: 7px 12px;
}
QFrame#Panel, QFrame#SettingsCard, QFrame#RedeemCard, QFrame#ActivityPanel,
QFrame#ScheduleCalendarPanel, QFrame#SchedulePanel, QFrame#ActivityAccountPanel,
QFrame#ActivityRulePanel, QFrame#SettingsInfoRow, QFrame#ToolTargetRow,
QFrame#ToolSettingRow, QFrame#WallpaperSlotCard, QFrame#SearchResultCard,
QFrame#MedalHeaderCard, QFrame#MedalHiddenCard, QFrame#PetControlCard {
    background-color: rgba(255, 253, 249, 235);
    border: 1px solid #ddd4cc;
    border-radius: 22px;
}
QPushButton#ToolPrimaryButton {
    color: #ffffff;
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #ff6b81, stop: 1 #ff926b);
    border: none;
    border-radius: 18px;
    padding: 10px 20px;
    font-weight: 700;
    font-size: 11pt;
}
QPushButton#ToolPrimaryButton:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #ff526c, stop: 1 #ff8152);
}
QPushButton#ToolPrimaryButton:pressed {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0, stop: 0 #e63f59, stop: 1 #e66f40);
}
QFrame#SettingsInfoRow, QFrame#ToolTargetRow, QFrame#ToolSettingRow {
    background-color: rgba(255, 255, 255, 214);
    border-color: #ebe3de;
    border-radius: 17px;
}
QPushButton#ToolChoiceButton {
    color: #344057;
    background-color: rgba(255, 253, 249, 220);
    border: 1px solid #e2d8d1;
    border-radius: 20px;
    padding: 11px 15px;
    text-align: left;
}
QPushButton#ToolChoiceButton:hover {
    color: #337d73;
    background-color: #f0faf7;
    border-color: #addfd7;
}
QPushButton#ToolChoiceButton:checked {
    color: #c74759;
    background-color: #fff0f2;
    border-color: #ffb7bf;
}
QLabel#ToolStatusLabel {
    color: #337d73;
    background-color: #f0faf7;
    border: 1px solid #bde6df;
    border-radius: 15px;
}
QLabel#MedalPageTitle {
    color: #26334a;
    font-size: 18pt;
    font-weight: 900;
}
QLabel#MedalPageSubtitle, QLabel#MedalHiddenNote {
    color: #718096;
}
QLabel#MedalSummary, QLabel#MedalNote {
    color: #526176;
    background-color: #fffdf9;
    border: 1px solid #ddd4cc;
    border-radius: 14px;
}
QFrame#MedalCard {
    background-color: rgba(247, 246, 244, 230);
    border: 1px solid #e2ddd8;
    border-radius: 18px;
}
QFrame#MedalCard[unlocked="true"] {
    background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 1, stop: 0 #ffffff, stop: 1 #fff9ee);
    border: 1.5px solid #fed7aa;
}
QLabel#MedalIcon {
    color: #8994a5;
    background-color: #eef1f4;
    border: 1px solid #d8dfe5;
    border-radius: 22px;
}
QFrame#MedalCard[unlocked="true"] QLabel#MedalIcon {
    background-color: transparent;
    border: none;
}
QLabel#MedalCardTitle, QLabel#MedalHiddenTitle {
    color: #26334a;
}
QLabel#MedalCardDetail, QLabel#MedalStatus {
    color: #718096;
}
QFrame#MedalCard[unlocked="true"] QLabel#MedalStatus {
    color: #338b7f;
}
QPushButton#MedalSecondaryButton {
    color: #526176;
    background-color: #fffdf9;
    border: 1px solid #ddd4cc;
    border-radius: 15px;
}
QPushButton#MedalSecondaryButton:hover {
    color: #c74759;
    background-color: #fff0f2;
    border-color: #ffb7bf;
}
QTextEdit#SettingsNotes {
    background-color: #ffffff;
    border: 1px solid #ddd4cc;
    border-radius: 16px;
}
QScrollBar:vertical {
    background: transparent;
    width: 6px;
    margin: 0px;
}
QScrollBar:vertical:hover {
    width: 10px;
}
QScrollBar::handle:vertical {
    background: rgba(180, 195, 205, 0.45);
    border: 0;
    border-radius: 3px;
    min-height: 28px;
}
QScrollBar::handle:vertical:hover {
    background: #ff7a8a;
    border-radius: 5px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 6px;
    margin: 0px;
}
QScrollBar:horizontal:hover {
    height: 10px;
}
QScrollBar::handle:horizontal {
    background: rgba(180, 195, 205, 0.45);
    border: 0;
    border-radius: 3px;
    min-width: 28px;
}
QScrollBar::handle:horizontal:hover {
    background: #ff7a8a;
    border-radius: 5px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QToolTip {
    color: #26334a;
    background-color: #fffdf9;
    border: 1px solid #ddd4cc;
    border-radius: 10px;
    padding: 7px;
}
"""

POLISHED_MENU_STYLE = """
QMenu {
    color: #26334a;
    background-color: #fffdf9;
    border: 1px solid #ddd4cc;
    border-radius: 14px;
    padding: 7px;
}
QMenu::item {
    padding: 8px 28px 8px 12px;
    border-radius: 10px;
}
QMenu::item:selected {
    color: #c74759;
    background-color: #ffe6e9;
}
QMenu::separator {
    height: 1px;
    background: #ebe3de;
    margin: 6px 5px;
}
QMenu::indicator {
    width: 15px;
    height: 15px;
    border-radius: 5px;
    border: 1px solid #cfd8dc;
    background-color: #ffffff;
}
QMenu::indicator:checked {
    background-color: #57c7b8;
    border-color: #45b5a6;
}
"""

MENU_STYLE = MENU_STYLE + PET_GAME_MENU_STYLE + POLISHED_MENU_STYLE
APP_STYLE = APP_STYLE + PET_GAME_STYLE + POLISHED_PET_STYLE + MENU_STYLE
DARK_STYLE = APP_STYLE
