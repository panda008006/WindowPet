from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QFileDialog, QInputDialog, QLineEdit, QMessageBox, QMenu

from .constants import APP_STYLE, MENU_STYLE

_PATCHED_DIALOGS = False
_ORIGINALS = {}


def _remember(cls, name):
    key = (cls, name)
    if key not in _ORIGINALS:
        _ORIGINALS[key] = getattr(cls, name)
    return _ORIGINALS[key]


def style_menu(menu):
    if isinstance(menu, QMenu):
        menu.setStyleSheet(MENU_STYLE)
        for action in menu.actions():
            submenu = action.menu()
            if submenu is not None:
                style_menu(submenu)
    return menu


def style_message_box(box):
    if isinstance(box, QMessageBox):
        box.setOption(QMessageBox.Option.DontUseNativeDialog, True)
        box.setStyleSheet(APP_STYLE)
    return box


def style_file_dialog(dialog):
    if isinstance(dialog, QFileDialog):
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
        dialog.setStyleSheet(APP_STYLE)
    return dialog


def style_input_dialog(dialog):
    if isinstance(dialog, QInputDialog):
        dialog.setOption(QInputDialog.InputDialogOption.UsePlainTextEditForTextInput, False)
        dialog.setStyleSheet(APP_STYLE)
    return dialog


def enable_plain_text_input(dialog):
    if isinstance(dialog, QInputDialog):
        dialog.setOption(QInputDialog.InputDialogOption.UsePlainTextEditForTextInput, True)
        dialog.setStyleSheet(APP_STYLE)
    return dialog


def _show_message_box(icon, parent, title, text, buttons, default_button):
    box = style_message_box(QMessageBox(parent))
    box.setIcon(icon)
    box.setWindowTitle(str(title))
    box.setText(str(text))
    box.setTextFormat(Qt.TextFormat.PlainText)
    box.setStandardButtons(buttons)
    if default_button != QMessageBox.StandardButton.NoButton:
        box.setDefaultButton(default_button)
    return box.exec()


def _message_information(parent=None, title="", text="", buttons=QMessageBox.StandardButton.Ok, defaultButton=QMessageBox.StandardButton.NoButton):
    return _show_message_box(QMessageBox.Icon.Information, parent, title, text, buttons, defaultButton)


def _message_warning(parent=None, title="", text="", buttons=QMessageBox.StandardButton.Ok, defaultButton=QMessageBox.StandardButton.NoButton):
    return _show_message_box(QMessageBox.Icon.Warning, parent, title, text, buttons, defaultButton)


def _message_critical(parent=None, title="", text="", buttons=QMessageBox.StandardButton.Ok, defaultButton=QMessageBox.StandardButton.NoButton):
    return _show_message_box(QMessageBox.Icon.Critical, parent, title, text, buttons, defaultButton)


def _message_question(parent=None, title="", text="", buttons=QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, defaultButton=QMessageBox.StandardButton.NoButton):
    return _show_message_box(QMessageBox.Icon.Question, parent, title, text, buttons, defaultButton)


def _configure_file_dialog(dialog, options):
    style_file_dialog(dialog)
    if options is not None:
        dialog.setOptions(QFileDialog.Options(options))
    dialog.setOption(QFileDialog.Option.DontUseNativeDialog, True)
    return dialog


def _file_filters(dialog, file_filter, selected_filter):
    filters = [part.strip() for part in str(file_filter or "").split(";;") if part.strip()]
    if filters:
        if len(filters) == 1:
            dialog.setNameFilter(filters[0])
        else:
            dialog.setNameFilters(filters)
    if selected_filter:
        dialog.selectNameFilter(selected_filter)


def _get_open_file_name(parent=None, caption="", directory="", file_filter="", selected_filter="", options=QFileDialog.Options()):
    dialog = _configure_file_dialog(QFileDialog(parent, caption, directory), options)
    dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
    _file_filters(dialog, file_filter, selected_filter)
    if dialog.exec():
        files = dialog.selectedFiles()
        return (files[0] if files else "", dialog.selectedNameFilter())
    return "", dialog.selectedNameFilter()


def _get_open_file_names(parent=None, caption="", directory="", file_filter="", selected_filter="", options=QFileDialog.Options()):
    dialog = _configure_file_dialog(QFileDialog(parent, caption, directory), options)
    dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
    _file_filters(dialog, file_filter, selected_filter)
    if dialog.exec():
        return (dialog.selectedFiles(), dialog.selectedNameFilter())
    return ([], dialog.selectedNameFilter())


def _get_save_file_name(parent=None, caption="", directory="", file_filter="", selected_filter="", options=QFileDialog.Options()):
    dialog = _configure_file_dialog(QFileDialog(parent, caption, directory), options)
    dialog.setFileMode(QFileDialog.FileMode.AnyFile)
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
    _file_filters(dialog, file_filter, selected_filter)
    if dialog.exec():
        files = dialog.selectedFiles()
        return (files[0] if files else "", dialog.selectedNameFilter())
    return "", dialog.selectedNameFilter()


def _get_existing_directory(parent=None, caption="", directory="", options=QFileDialog.Option.ShowDirsOnly):
    dialog = _configure_file_dialog(QFileDialog(parent, caption, directory), options)
    dialog.setFileMode(QFileDialog.FileMode.Directory)
    dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
    if dialog.exec():
        files = dialog.selectedFiles()
        return files[0] if files else ""
    return ""


def _get_item(parent=None, title="", label="", items=None, current=0, editable=True, flags=Qt.WindowFlags(), inputMethodHints=Qt.InputMethodHints()):
    dialog = style_input_dialog(QInputDialog(parent))
    dialog.setWindowTitle(str(title))
    dialog.setLabelText(str(label))
    dialog.setComboBoxItems(list(items or []))
    dialog.setComboBoxEditable(bool(editable))
    if items:
        current = max(0, min(int(current), len(items) - 1))
        dialog.setTextValue(str(items[current]))
    if flags:
        dialog.setWindowFlags(dialog.windowFlags() | flags)
    if inputMethodHints:
        dialog.setInputMethodHints(inputMethodHints)
    if dialog.exec():
        return dialog.textValue(), True
    return "", False


def _get_int(parent=None, title="", label="", value=0, minValue=-2147483647, maxValue=2147483647, step=1, flags=Qt.WindowFlags(), inputMethodHints=Qt.InputMethodHints()):
    dialog = style_input_dialog(QInputDialog(parent))
    dialog.setWindowTitle(str(title))
    dialog.setLabelText(str(label))
    dialog.setInputMode(QInputDialog.InputMode.IntInput)
    dialog.setIntRange(int(minValue), int(maxValue))
    dialog.setIntStep(int(step))
    dialog.setIntValue(int(value))
    if flags:
        dialog.setWindowFlags(dialog.windowFlags() | flags)
    if inputMethodHints:
        dialog.setInputMethodHints(inputMethodHints)
    if dialog.exec():
        return int(dialog.intValue()), True
    return 0, False


def _get_text(parent=None, title="", label="", echo=QLineEdit.EchoMode.Normal, text="", flags=Qt.WindowFlags(), inputMethodHints=Qt.InputMethodHints()):
    dialog = style_input_dialog(QInputDialog(parent))
    dialog.setWindowTitle(str(title))
    dialog.setLabelText(str(label))
    dialog.setInputMode(QInputDialog.InputMode.TextInput)
    dialog.setTextEchoMode(echo)
    dialog.setTextValue(str(text))
    if flags:
        dialog.setWindowFlags(dialog.windowFlags() | flags)
    if inputMethodHints:
        dialog.setInputMethodHints(inputMethodHints)
    if dialog.exec():
        return dialog.textValue(), True
    return "", False


def _get_multi_line_text(parent=None, title="", label="", text="", flags=Qt.WindowFlags(), inputMethodHints=Qt.InputMethodHints()):
    dialog = enable_plain_text_input(QInputDialog(parent))
    dialog.setWindowTitle(str(title))
    dialog.setLabelText(str(label))
    dialog.setInputMode(QInputDialog.InputMode.TextInput)
    dialog.setTextValue(str(text))
    if flags:
        dialog.setWindowFlags(dialog.windowFlags() | flags)
    if inputMethodHints:
        dialog.setInputMethodHints(inputMethodHints)
    if dialog.exec():
        return dialog.textValue(), True
    return "", False


def install_dialog_patches():
    global _PATCHED_DIALOGS
    if _PATCHED_DIALOGS:
        return

    _remember(QMessageBox, "information")
    _remember(QMessageBox, "warning")
    _remember(QMessageBox, "critical")
    _remember(QMessageBox, "question")
    _remember(QFileDialog, "getOpenFileName")
    _remember(QFileDialog, "getOpenFileNames")
    _remember(QFileDialog, "getSaveFileName")
    _remember(QFileDialog, "getExistingDirectory")
    _remember(QInputDialog, "getItem")
    _remember(QInputDialog, "getInt")
    _remember(QInputDialog, "getText")
    _remember(QInputDialog, "getMultiLineText")

    QMessageBox.information = staticmethod(_message_information)
    QMessageBox.warning = staticmethod(_message_warning)
    QMessageBox.critical = staticmethod(_message_critical)
    QMessageBox.question = staticmethod(_message_question)

    QFileDialog.getOpenFileName = staticmethod(_get_open_file_name)
    QFileDialog.getOpenFileNames = staticmethod(_get_open_file_names)
    QFileDialog.getSaveFileName = staticmethod(_get_save_file_name)
    QFileDialog.getExistingDirectory = staticmethod(_get_existing_directory)

    QInputDialog.getItem = staticmethod(_get_item)
    QInputDialog.getInt = staticmethod(_get_int)
    QInputDialog.getText = staticmethod(_get_text)
    QInputDialog.getMultiLineText = staticmethod(_get_multi_line_text)

    _PATCHED_DIALOGS = True


def apply_non_native_dialogs():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)
    install_dialog_patches()


def apply_light_palette(app):
    if app is None:
        return

    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#edf7ff"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#203247"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#fbfdff"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#eaf4ff"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#fafdff"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor("#203247"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#203247"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#fafdff"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#203247"))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#cfe8ff"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#0f3769"))
    palette.setColor(QPalette.ColorRole.Link, QColor("#2a7de0"))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor("#7b8ba0"))
    app.setPalette(palette)
