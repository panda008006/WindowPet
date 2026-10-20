"""Small, local launch adapters for the AI tools supported by DaDeepSeekPet.

The adapters deliberately use the application's registered Windows URL scheme
when one exists.  They do not read credentials or automate another app's
private UI.  A tool can optionally notify WindowPet of a state change through
``windowpet://status?pet=dadeepseek&state=thinking``.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class ExternalIntegration:
    key: str
    label: str
    schemes: tuple[str, ...]
    fallback_url: str = ""
    executable_candidates: tuple[str, ...] = ()


INTEGRATIONS = (
    ExternalIntegration(
        "deepseek",
        "DeepSeek",
        ("deepseek",),
        "https://chat.deepseek.com/",
        (
            r"%LOCALAPPDATA%\Programs\DeepSeek Harness\DeepSeek Harness.exe",
            r"%LOCALAPPDATA%\Programs\DeepSeek\DeepSeek.exe",
        ),
    ),
    ExternalIntegration("codex", "Codex", ("codex",), "https://chatgpt.com/codex"),
    ExternalIntegration("workbuddy", "WorkBuddy", ("workbuddy",), "https://www.workbuddy.ai/"),
    # The product is commonly called Antigravity; accept the user's
    # "Antiquity" spelling as the stable WindowPet key and try both schemes.
    ExternalIntegration(
        "antiquity",
        "Antiquity / Antigravity",
        ("antiquity", "antigravity"),
        "https://antigravity.google/",
    ),
    ExternalIntegration("zcode", "Z Code", ("zcode",), "https://zcode.z.ai/"),
    ExternalIntegration("doubao", "豆包", ("doubao",), "https://www.doubao.com/chat/"),
)

_INTEGRATIONS_BY_KEY = {item.key: item for item in INTEGRATIONS}


def integrations():
    return INTEGRATIONS


def integration_for(key: str):
    normalized = str(key or "").strip().lower()
    aliases = {
        "antigravity": "antiquity",
        "antiquity": "antiquity",
        "豆包": "doubao",
    }
    return _INTEGRATIONS_BY_KEY.get(aliases.get(normalized, normalized))


def _protocol_command(scheme: str):
    if sys.platform != "win32":
        return ""
    try:
        import winreg

        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for path in (rf"Software\Classes\{scheme}\shell\open\command", rf"Software\WOW6432Node\Classes\{scheme}\shell\open\command"):
                try:
                    with winreg.OpenKey(root, path) as key:
                        value, _ = winreg.QueryValueEx(key, None)
                        return str(value or "")
                except OSError:
                    continue
    except OSError:
        pass
    return ""


def registered_scheme(schemes):
    for scheme in schemes:
        command = _protocol_command(scheme)
        if command:
            return scheme
    return ""


def _executable_from_command(command: str):
    match = re.match(r'^\s*"([^"]+)"', command)
    if match:
        return match.group(1)
    return command.strip().split(" ", 1)[0] if command.strip() else ""


def _candidate_executable(item: ExternalIntegration):
    for candidate in item.executable_candidates:
        path = os.path.expandvars(os.path.expanduser(candidate))
        if path and os.path.isfile(path):
            return path
    return ""


def launch_integration(key: str):
    """Launch one configured tool and return ``(ok, detail)``."""
    item = integration_for(key)
    if item is None:
        return False, "未找到这个接入项。"

    scheme = registered_scheme(item.schemes)
    if scheme:
        try:
            os.startfile(f"{scheme}://")
            return True, f"已打开 {item.label}"
        except OSError:
            command = _protocol_command(scheme)
            executable = _executable_from_command(command)
            if executable and os.path.exists(executable):
                try:
                    subprocess.Popen([executable], close_fds=True)
                    return True, f"已启动 {item.label}"
                except OSError:
                    pass

    executable = _candidate_executable(item)
    if executable:
        try:
            subprocess.Popen([executable], close_fds=True)
            return True, f"已启动 {item.label}"
        except OSError:
            pass

    if item.fallback_url:
        try:
            os.startfile(item.fallback_url)
            return True, f"已打开 {item.label}网页入口"
        except OSError:
            pass
    return False, f"未检测到 {item.label}，请先安装或注册它的 Windows 接入协议。"


def launch_all_integrations():
    """Open every supported AI tool and return per-tool results.

    This is intentionally a small orchestration helper: it only uses the
    registered Windows protocol (or the documented browser fallback) and
    never invokes a shell or reads credentials.  Keeping the loop here lets
    the desktop overlay and the control panel expose the same one-click
    behavior without maintaining two subtly different implementations.
    """
    return [
        (item, *launch_integration(item.key))
        for item in INTEGRATIONS
    ]


def integration_status_url(state: str, pet: str = "dadeepseek", provider: str = ""):
    state = str(state or "waiting").strip().lower()
    if state in {"done", "completed", "complete", "answered", "finished", "success"}:
        state = "result"
    if state not in {"thinking", "waiting", "result"}:
        state = "waiting"
    url = f"windowpet://status?pet={pet}&state={state}"
    provider_item = integration_for(provider)
    if provider_item is not None:
        url += f"&ai={provider_item.key}"
    return url
