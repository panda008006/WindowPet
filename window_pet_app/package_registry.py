"""Stable four-digit package codes shared by desktop and delivery tooling."""

import json

from .constants import BASE_DIR


REGISTRY_PATH = BASE_DIR / "package_registry.json"


def _load_registry():
    try:
        payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"schema_version": 1, "code_width": 4, "packages": []}
    return payload if isinstance(payload, dict) else {"schema_version": 1, "code_width": 4, "packages": []}


def normalize_package_code(value):
    text = str(value or "").strip()
    if not text.isdigit():
        return ""
    return text.zfill(4)[-4:]


def package_records():
    records = _load_registry().get("packages", [])
    return [item for item in records if isinstance(item, dict) and normalize_package_code(item.get("code"))]


def package_code_for_folder(folder_name):
    folder = str(folder_name or "").strip().lower()
    for item in package_records():
        if str(item.get("folder_name") or "").strip().lower() == folder:
            return normalize_package_code(item.get("code"))
    return ""


def package_code_for_id(package_id):
    package_id = str(package_id or "").strip().lower()
    for item in package_records():
        if str(item.get("package_id") or "").strip().lower() == package_id:
            return normalize_package_code(item.get("code"))
    return ""


def package_for_code(code):
    normalized = normalize_package_code(code)
    return next((item for item in package_records() if normalize_package_code(item.get("code")) == normalized), None)
