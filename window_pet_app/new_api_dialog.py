from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QVBoxLayout

from .new_api import (
    NewApiClient,
    NewApiError,
    clear_token,
    load_credentials,
    normalize_base_url,
    save_credentials,
)
from .vibe_components import PetCursorManager, VibeButton


TEXT = {
    "zh": {
        "title": "AI 服务与额度",
        "subtitle": "New API 账户独立于 Window Pet 云端账号。注册、邮箱验证和充值在 New API 站点完成。",
        "site_label": "New API 站点地址",
        "site_placeholder": "https://api.example.com",
        "open_site": "打开注册 / 登录 / 充值站点",
        "token_label": "API 令牌",
        "token_placeholder": "粘贴站点生成的 sk- 令牌",
        "token_hint": "校验会访问 /v1/models。令牌仅在校验成功后保存，并使用当前 Windows 用户的 DPAPI 加密。",
        "verify": "校验并保存令牌",
        "clear": "删除本机令牌",
        "close": "关闭",
        "unconfigured": "尚未连接 New API。先填写站点地址，再打开站点注册、验证邮箱并生成令牌。",
        "saved": "已在本机加密保存令牌。点击“校验并保存令牌”可检查当前服务连接。",
        "verified": "令牌有效，可访问模型列表（{count} 个模型）。余额和充值请在 New API 站点查看。",
        "clear_confirm": "确定删除本机保存的 New API 令牌吗？",
        "cleared": "本机令牌已删除。",
        "open_failed": "无法打开 New API 站点，请检查地址。",
        "load_failed": "本机加密令牌无法读取，请重新验证并保存。",
        "clear_failed": "无法删除本机令牌。",
    },
    "en": {
        "title": "AI Service and Balance",
        "subtitle": "The New API account is separate from Window Pet cloud sync. Register, verify email, and recharge on the New API site.",
        "site_label": "New API site URL",
        "site_placeholder": "https://api.example.com",
        "open_site": "Open registration / login / recharge",
        "token_label": "API token",
        "token_placeholder": "Paste the sk- token created on the site",
        "token_hint": "Validation calls /v1/models. The token is saved only after validation and encrypted with the current Windows user's DPAPI.",
        "verify": "Verify and save token",
        "clear": "Delete local token",
        "close": "Close",
        "unconfigured": "New API is not connected. Enter the site URL, register, verify email, and create a token there.",
        "saved": "An encrypted token is saved locally. Verify it to check the current service connection.",
        "verified": "Token is valid; {count} models are available. Check balance and recharge on the New API site.",
        "clear_confirm": "Delete the New API token saved on this computer?",
        "cleared": "The local token was deleted.",
        "open_failed": "Unable to open the New API site. Check the URL.",
        "load_failed": "The encrypted local token could not be read. Verify and save it again.",
        "clear_failed": "Unable to delete the local token.",
    },
}


class NewApiDialog(QDialog):
    def __init__(self, language="zh", parent=None):
        super().__init__(parent)
        self.language = "en" if language == "en" else "zh"
        self.texts = TEXT[self.language]
        self.setObjectName("GlassDialog")
        PetCursorManager.apply_to_window(self)
        self.setWindowTitle(self.texts["title"])
        self.setMinimumWidth(620)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 22, 24, 22)
        root.setSpacing(14)

        surface = QFrame()
        surface.setObjectName("AccountDialogSurface")
        surface_layout = QVBoxLayout(surface)
        surface_layout.setContentsMargins(22, 20, 22, 20)
        surface_layout.setSpacing(12)
        root.addWidget(surface)

        title = QLabel(self.texts["title"])
        title.setObjectName("AccountTitle")
        subtitle = QLabel(self.texts["subtitle"])
        subtitle.setObjectName("SubtleLabel")
        subtitle.setWordWrap(True)
        surface_layout.addWidget(title)
        surface_layout.addWidget(subtitle)

        site_label = QLabel(self.texts["site_label"])
        site_label.setObjectName("AccountFieldLabel")
        self.site_input = QLineEdit()
        self.site_input.setObjectName("AccountInput")
        self.site_input.setPlaceholderText(self.texts["site_placeholder"])
        surface_layout.addWidget(site_label)
        surface_layout.addWidget(self.site_input)

        self.open_site_button = VibeButton(self.texts["open_site"], variant="secondary")
        self.open_site_button.clicked.connect(self.open_site)
        surface_layout.addWidget(self.open_site_button)

        token_label = QLabel(self.texts["token_label"])
        token_label.setObjectName("AccountFieldLabel")
        self.token_input = QLineEdit()
        self.token_input.setObjectName("AccountInput")
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setPlaceholderText(self.texts["token_placeholder"])
        self.token_hint = QLabel(self.texts["token_hint"])
        self.token_hint.setObjectName("SubtleLabel")
        self.token_hint.setWordWrap(True)
        surface_layout.addWidget(token_label)
        surface_layout.addWidget(self.token_input)
        surface_layout.addWidget(self.token_hint)

        self.status_label = QLabel()
        self.status_label.setObjectName("SubtleLabel")
        self.status_label.setWordWrap(True)
        surface_layout.addWidget(self.status_label)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.clear_button = VibeButton(self.texts["clear"], variant="secondary")
        self.clear_button.clicked.connect(self.remove_token)
        self.close_button = VibeButton(self.texts["close"], variant="secondary")
        self.close_button.clicked.connect(self.accept)
        self.verify_button = VibeButton(self.texts["verify"], variant="primary")
        self.verify_button.clicked.connect(self.verify_and_save)
        buttons.addWidget(self.clear_button)
        buttons.addWidget(self.close_button)
        buttons.addWidget(self.verify_button)
        surface_layout.addLayout(buttons)

        try:
            saved = load_credentials()
            self.site_input.setText(saved["base_url"])
            self.token_input.setText(saved["api_key"])
            self.status_label.setText(self.texts["saved"] if saved["api_key"] else self.texts["unconfigured"])
        except NewApiError:
            self.status_label.setText(self.texts["load_failed"])

    def open_site(self):
        try:
            base_url = normalize_base_url(self.site_input.text())
            save_credentials(base_url)
        except NewApiError as exc:
            QMessageBox.warning(self, self.texts["title"], str(exc))
            return

        if not QDesktopServices.openUrl(QUrl(base_url)):
            QMessageBox.warning(self, self.texts["title"], self.texts["open_failed"])

    def verify_and_save(self):
        try:
            base_url = normalize_base_url(self.site_input.text())
            result = NewApiClient(base_url).verify_token(self.token_input.text())
            save_credentials(base_url, self.token_input.text())
        except NewApiError as exc:
            self.status_label.setText(str(exc))
            return

        self.status_label.setText(self.texts["verified"].format(count=result["model_count"]))

    def remove_token(self):
        answer = QMessageBox.question(
            self,
            self.texts["title"],
            self.texts["clear_confirm"],
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if answer != QMessageBox.Yes:
            return
        try:
            clear_token()
            self.token_input.clear()
            self.status_label.setText(self.texts["cleared"])
        except NewApiError:
            self.status_label.setText(self.texts["clear_failed"])
