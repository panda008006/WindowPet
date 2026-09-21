import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QMessageBox

from .assets import save_config
from .constants import APP_DISPLAY_NAME, BASE_DIR
from .logging_utils import log_exception, log_info, log_warning
from .version import __version__


UPDATE_CONFIG_PATH = BASE_DIR / "update_config.json"
UPDATE_SCRIPT_NAME = "apply_window_pet_update.ps1"


def load_update_config():
    if not UPDATE_CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(UPDATE_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        log_warning("Unable to read update config: %s", exc)
        return {}
    return data if isinstance(data, dict) else {}


def update_manifest_url():
    value = str(load_update_config().get("manifest_url") or "").strip()
    return value


def official_site_url():
    value = str(load_update_config().get("official_site_url") or "").strip()
    return value


def open_official_site(parent=None):
    url = official_site_url()
    if not url:
        QMessageBox.information(
            parent,
            "软件更新",
            "还没有配置官网地址。请先在 update_config.json 里填写 official_site_url。",
        )
        return False
    if not QDesktopServices.openUrl(QUrl(url)):
        QMessageBox.warning(parent, "软件更新", "无法打开官网地址。")
        return False
    return True


def fetch_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": f"{APP_DISPLAY_NAME}/{__version__}"})
    with urllib.request.urlopen(request, timeout=20) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        if charset.lower().replace("_", "-") in {"utf-8", "utf8"}:
            charset = "utf-8-sig"
        return json.loads(response.read().decode(charset))


def version_parts(value):
    parts = []
    for piece in str(value).replace("-", ".").split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits or 0))
    return tuple(parts or [0])


def is_newer_version(remote, local=__version__):
    remote_parts = version_parts(remote)
    local_parts = version_parts(local)
    length = max(len(remote_parts), len(local_parts))
    return remote_parts + (0,) * (length - len(remote_parts)) > local_parts + (0,) * (length - len(local_parts))


def download_file(url, target_path):
    request = urllib.request.Request(url, headers={"User-Agent": f"{APP_DISPLAY_NAME}/{__version__}"})
    with urllib.request.urlopen(request, timeout=60) as response:
        with Path(target_path).open("wb") as output:
            shutil.copyfileobj(response, output)


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_package_hash(package_path, expected_sha256):
    expected = str(expected_sha256 or "").strip().lower()
    if not expected:
        return True
    return sha256_file(package_path).lower() == expected


def extracted_package_root(extract_dir):
    extract_dir = Path(extract_dir)
    if (extract_dir / "Window Pet.exe").exists():
        return extract_dir
    for child in extract_dir.iterdir():
        if child.is_dir() and (child / "Window Pet.exe").exists():
            return child
    return None


def powershell_literal(value):
    return str(value).replace("'", "''")


def write_update_script(source_root, target_root, exe_name):
    script_path = Path(tempfile.gettempdir()) / UPDATE_SCRIPT_NAME
    source = powershell_literal(Path(source_root))
    target = powershell_literal(Path(target_root))
    exe = powershell_literal(exe_name)
    process_id = int(os.getpid())
    script = f"""$ErrorActionPreference = 'Stop'
$source = '{source}'
$target = '{target}'
$exeName = '{exe}'
$pidToWait = {process_id}
$preserveNames = @('config.json', 'update_config.json', 'logs')
try {{
  Wait-Process -Id $pidToWait -Timeout 60 -ErrorAction SilentlyContinue
}} catch {{}}
Start-Sleep -Milliseconds 800
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$preserveRoot = Join-Path $env:TEMP ('WindowPet_preserve_' + $stamp)
New-Item -ItemType Directory -Path $preserveRoot -Force | Out-Null
foreach ($name in $preserveNames) {{
  $src = Join-Path $target $name
  if (Test-Path -LiteralPath $src) {{
    Copy-Item -LiteralPath $src -Destination (Join-Path $preserveRoot $name) -Recurse -Force
  }}
}}
Get-ChildItem -LiteralPath $target -Force | Where-Object {{
  $preserveNames -notcontains $_.Name -and $_.Name -notlike '.update_backup_*'
}} | ForEach-Object {{
  Remove-Item -LiteralPath $_.FullName -Recurse -Force
}}
Copy-Item -LiteralPath (Join-Path $source '*') -Destination $target -Recurse -Force
foreach ($name in $preserveNames) {{
  $src = Join-Path $preserveRoot $name
  if (Test-Path -LiteralPath $src) {{
    Copy-Item -LiteralPath $src -Destination (Join-Path $target $name) -Recurse -Force
  }}
}}
Start-Process -FilePath (Join-Path $target $exeName) -WorkingDirectory $target
"""
    script_path.write_text(script, encoding="utf-8")
    return script_path


def apply_update_after_exit(source_root):
    exe_name = Path(sys.executable).name if getattr(sys, "frozen", False) else "Window Pet.exe"
    script_path = write_update_script(source_root, BASE_DIR, exe_name)
    subprocess.Popen(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
        ],
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
    )
    log_info("Update script started: %s", script_path)
    QApplication.instance().quit()


def safe_extract_zip(package_path, extract_dir):
    extract_root = Path(extract_dir).resolve()
    with zipfile.ZipFile(package_path) as archive:
        for member in archive.infolist():
            target = (extract_root / member.filename).resolve()
            try:
                target.relative_to(extract_root)
            except ValueError:
                raise ValueError("更新包包含不安全路径。")
        archive.extractall(extract_root)


def check_for_updates(parent=None):
    manifest_url = update_manifest_url()
    if not manifest_url:
        result = QMessageBox.information(
            parent,
            "软件更新",
            "还没有配置更新清单地址。请先在 update_config.json 里填写 manifest_url。以后点更新时会从你的官网读取最新版本。",
            QMessageBox.Open | QMessageBox.Ok,
            QMessageBox.Ok,
        )
        if result == QMessageBox.Open:
            open_official_site(parent)
        return False

    try:
        manifest = fetch_json(manifest_url)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        log_warning("Update check failed: %s", exc)
        result = QMessageBox.warning(
            parent,
            "软件更新",
            "检查更新失败。可以先打开官网手动查看最新版本。",
            QMessageBox.Open | QMessageBox.Ok,
            QMessageBox.Ok,
        )
        if result == QMessageBox.Open:
            open_official_site(parent)
        return False

    if not isinstance(manifest, dict):
        QMessageBox.warning(parent, "软件更新", "官网更新清单格式不正确。")
        return False

    remote_version = str(manifest.get("version") or "").strip()
    package_url = str(manifest.get("package_url") or "").strip()
    if not remote_version or not package_url:
        QMessageBox.warning(parent, "软件更新", "官网更新清单缺少 version 或 package_url。")
        return False

    if not is_newer_version(remote_version):
        QMessageBox.information(parent, "软件更新", f"当前已经是最新版本：{__version__}")
        return False

    notes = str(manifest.get("release_notes") or "").strip()
    message = f"发现新版本：{remote_version}\n当前版本：{__version__}\n\n更新会保留 config.json、update_config.json 和 logs。"
    if notes:
        message += f"\n\n更新说明：\n{notes[:500]}"
    message += "\n\n是否现在下载并更新？"
    confirm = QMessageBox.question(parent, "软件更新", message, QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
    if confirm != QMessageBox.Yes:
        return False

    try:
        save_config()
        work_dir = Path(tempfile.mkdtemp(prefix="window_pet_update_"))
        package_path = work_dir / "window_pet_latest.zip"
        download_file(package_url, package_path)
        if not validate_package_hash(package_path, manifest.get("sha256")):
            QMessageBox.warning(parent, "软件更新", "下载包校验失败，已取消更新。")
            return False
        extract_dir = work_dir / "extracted"
        extract_dir.mkdir(parents=True, exist_ok=True)
        safe_extract_zip(package_path, extract_dir)
        source_root = extracted_package_root(extract_dir)
        if source_root is None:
            QMessageBox.warning(parent, "软件更新", "下载包里没有找到 Window Pet.exe，已取消更新。")
            return False
        QMessageBox.information(parent, "软件更新", "下载完成。程序会退出并自动替换文件，更新后会重新打开。")
        apply_update_after_exit(source_root)
        return True
    except Exception as exc:
        log_exception("Update install failed: %s", exc)
        QMessageBox.warning(parent, "软件更新", f"更新失败：{exc}")
        return False
