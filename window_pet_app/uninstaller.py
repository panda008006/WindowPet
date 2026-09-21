"""Self-uninstall support for packaged (PyInstaller) environments.

Dev warning: source-mode uninstall is disabled to avoid accidental data loss.
Only packaged builds trigger the real uninstaller.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def _is_packaged():
    """Return True when running inside a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def uninstall_target_dir():
    """Directory that the packaged uninstaller will remove."""
    if _is_packaged():
        return str(Path(sys.executable).parent)
    return str(Path(__file__).resolve().parent.parent)


def can_self_uninstall():
    """Return True if a self-uninstall is allowed in the current context.

    Dev runs return False (to protect the source tree).
    Packaged runs return True.
    """
    return _is_packaged()


def start_self_uninstall():
    """Launch the self-uninstall script and exit the app.

    Returns True if the uninstall script was written and launched.
    """
    if not _is_packaged():
        return False

    target_dir = uninstall_target_dir()

    # Write a temporary batch script that:
    # 1. Waits for the main process to exit
    # 2. Uses rmdir to remove the install directory
    # 3. Removes desktop shortcuts
    # 4. Self-destructs
    script_lines = [
        "@echo off",
        "chcp 65001 >nul",
        f'pushd "{tempfile.gettempdir()}"',
        "timeout /t 2 /nobreak >nul",
        # Remove the install directory
        f'if exist "{target_dir}" rmdir /s /q "{target_dir}" 2>nul',
        # Remove desktop shortcuts
        'if exist "%USERPROFILE%\\Desktop\\Window Pet.lnk" del /f /q "%USERPROFILE%\\Desktop\\Window Pet.lnk" 2>nul',
        'if exist "%USERPROFILE%\\Desktop\\小鼻嘎.lnk" del /f /q "%USERPROFILE%\\Desktop\\小鼻嘎.lnk" 2>nul',
        # Remove Start Menu entries
        'if exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Window Pet" rmdir /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Window Pet" 2>nul',
        'if exist "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\小鼻嘎" rmdir /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\小鼻嘎" 2>nul',
    ]
    script_content = "\r\n".join(script_lines)

    try:
        batch_path = os.path.join(tempfile.gettempdir(), "windowpet_uninstall.bat")
        with open(batch_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        subprocess.Popen(
            ["cmd", "/c", batch_path],
            shell=False,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0,
        )
        return True
    except Exception:
        return False
