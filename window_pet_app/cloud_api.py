import json
import socket
import urllib.error
import urllib.request

from .constants import APP_DISPLAY_NAME
from .updater import load_update_config
from .version import __version__


class CloudApiError(Exception):
    pass


def api_base_url():
    value = str(load_update_config().get("api_base_url") or "").strip().rstrip("/")
    if not value:
        raise CloudApiError("还没有配置云端账号服务地址。")
    return value


def request_json(method, path, payload=None, token=None, timeout=20):
    url = f"{api_base_url()}{path}"
    headers = {
        "Accept": "application/json",
        "User-Agent": f"{APP_DISPLAY_NAME}/{__version__}",
    }
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, data=data, method=method.upper(), headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            raw = response.read().decode(charset)
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as exc:
        message = f"云端账号服务返回错误：{exc.code}"
        try:
            charset = exc.headers.get_content_charset() or "utf-8"
            body = json.loads(exc.read().decode(charset))
            message = str(body.get("error") or body.get("message") or message)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            pass
        raise CloudApiError(message) from exc
    except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
        raise CloudApiError("无法连接云端账号服务，请检查网络后再试。") from exc
    except json.JSONDecodeError as exc:
        raise CloudApiError("云端账号服务返回内容异常，请稍后再试。") from exc


def send_register_code(email):
    return request_json(
        "POST",
        "/api/auth/email-code",
        {"email": email, "purpose": "register"},
    )


def register(email, name, password, email_code):
    return request_json(
        "POST",
        "/api/auth/register",
        {
            "email": email,
            "name": name,
            "password": password,
            "emailCode": email_code,
        },
    )


def login(email, password):
    return request_json(
        "POST",
        "/api/auth/login",
        {"email": email, "password": password},
    )


def redeem_character(code, token, install_id=None):
    if not str(token or "").strip():
        raise CloudApiError("请先登录账号，再兑换角色。")
    payload = {"code": str(code or "").strip().upper()}
    if install_id:
        payload["installId"] = str(install_id)
    try:
        return request_json("POST", "/api/redeem", payload, token=token)
    except CloudApiError as exc:
        message = str(exc)
        if "404" in message or "not found" in message.lower():
            raise CloudApiError("角色兑换服务尚未开放，兑换码不会被消耗。") from exc
        raise
