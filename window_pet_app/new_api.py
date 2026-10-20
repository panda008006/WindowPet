"""New API token validation and per-user encrypted credential storage."""

import base64
import binascii
import ipaddress
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit


class NewApiError(Exception):
    pass


class _RejectRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, new_url):
        return None


def normalize_base_url(value):
    value = str(value or "").strip()
    try:
        parsed = urlsplit(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError as exc:
        raise NewApiError("New API 地址格式不正确。") from exc

    if parsed.scheme.lower() not in {"http", "https"} or not hostname:
        raise NewApiError("请输入完整的 New API 地址，例如 https://api.example.com。")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise NewApiError("New API 地址不能包含账号、密码、查询参数或片段。")

    if parsed.scheme.lower() == "http":
        try:
            is_loopback = ipaddress.ip_address(hostname).is_loopback
        except ValueError:
            is_loopback = hostname.lower() == "localhost"
        if not is_loopback:
            raise NewApiError("远程 New API 地址必须使用 HTTPS。")

    netloc = hostname
    if ":" in hostname and not hostname.startswith("["):
        netloc = f"[{hostname}]"
    if port is not None:
        netloc = f"{netloc}:{port}"
    return parsed._replace(scheme=parsed.scheme.lower(), netloc=netloc).geturl().rstrip("/")


class NewApiClient:
    def __init__(self, base_url):
        self.base_url = normalize_base_url(base_url)

    def verify_token(self, api_key, timeout=10):
        api_key = str(api_key or "").strip()
        if not api_key:
            raise NewApiError("请先输入 New API 令牌。")

        request = urllib.request.Request(
            f"{self.base_url}/v1/models",
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "WindowPet-NewAPI/1.0",
            },
        )
        try:
            opener = urllib.request.build_opener(_RejectRedirect())
            with opener.open(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                raise NewApiError("令牌无效或已停用，请在 New API 站点检查令牌。") from exc
            if exc.code == 429:
                raise NewApiError("New API 当前限流或额度不足，请到服务站点查看。") from exc
            raise NewApiError(f"New API 返回 HTTP {exc.code}，请稍后重试。") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise NewApiError("无法连接 New API，请检查地址和网络。") from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise NewApiError("New API 返回了无法识别的数据。") from exc

        models = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(models, list):
            raise NewApiError("New API 返回的数据格式不符合模型列表接口。")
        return {"valid": True, "model_count": len(models)}


def credentials_path():
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        root = Path(local_app_data)
    else:
        root = Path.home() / "AppData" / "Local"
    return root / "WindowPet" / "new_api_credentials.json"


def _read_store(path):
    path = Path(path or credentials_path())
    if not path.exists():
        return path, {"schema_version": 1, "base_url": ""}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise NewApiError("本机 New API 设置文件无法读取。") from exc
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise NewApiError("本机 New API 设置文件版本不受支持。")
    return path, value


def _write_store(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    try:
        temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _protect_token(token):
    if os.name != "nt":
        raise NewApiError("API 令牌加密保存需要在 Windows 上运行。")
    try:
        import win32crypt

        protected = win32crypt.CryptProtectData(
            token.encode("utf-8"), "WindowPet New API token", None, None, None, 0
        )
        return protected[-1] if isinstance(protected, tuple) else protected
    except Exception as exc:
        raise NewApiError("Windows 无法加密 API 令牌，请检查当前用户配置。") from exc


def _unprotect_token(encrypted):
    if os.name != "nt":
        raise NewApiError("API 令牌解密需要使用保存令牌的 Windows 用户。")
    try:
        import win32crypt

        unprotected = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)
        plaintext = unprotected[-1] if isinstance(unprotected, tuple) else unprotected
        return plaintext.decode("utf-8")
    except Exception as exc:
        raise NewApiError("本机 API 令牌无法解密，请重新验证并保存。") from exc


def load_credentials(path=None):
    path, value = _read_store(path)
    token_blob = str(value.get("token_dpapi") or "")
    token = ""
    if token_blob:
        try:
            encrypted = base64.b64decode(token_blob, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise NewApiError("本机 API 令牌数据损坏，请重新保存令牌。") from exc
        token = _unprotect_token(encrypted)
    return {"base_url": str(value.get("base_url") or ""), "api_key": token}


def save_credentials(base_url, api_key=None, path=None):
    base_url = normalize_base_url(base_url)
    path, value = _read_store(path)
    value["schema_version"] = 1
    value["base_url"] = base_url
    if api_key is not None:
        token = str(api_key or "").strip()
        if token:
            value["token_dpapi"] = base64.b64encode(_protect_token(token)).decode("ascii")
        else:
            value.pop("token_dpapi", None)
    _write_store(path, value)


def clear_token(path=None):
    path, value = _read_store(path)
    value.pop("token_dpapi", None)
    _write_store(path, value)
