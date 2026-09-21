"""Local file search powered by Everything HTTP or fallback filesystem scanning."""

import os
import subprocess
import sys
from collections import namedtuple
from datetime import datetime
from pathlib import Path

SearchResult = namedtuple(
    "SearchResult",
    ["path", "name", "size", "modified", "kind", "source"],
)


def _everything_exe_paths():
    """Return candidate Everything.exe paths."""
    candidates = [
        r"C:\Program Files\Everything\Everything.exe",
        r"C:\Program Files (x86)\Everything\Everything.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Everything\Everything.exe"),
        os.path.expandvars(r"%ProgramFiles%\Everything\Everything.exe"),
    ]
    for candidate in candidates:
        expanded = os.path.expandvars(candidate)
        if os.path.isfile(expanded):
            yield expanded


def _everything_http_base():
    """Try common Everything HTTP ports and return (base_url, True) or (None, False)."""
    import urllib.request
    import urllib.error

    for port in (8099, 8098, 8080):
        url = f"http://127.0.0.1:{port}"
        try:
            req = urllib.request.Request(url, method="HEAD")
            urllib.request.urlopen(req, timeout=0.5)
            return url
        except Exception:
            continue
    return None


def everything_available():
    """Return True if Everything HTTP is reachable."""
    return _everything_http_base() is not None


def _search_via_everything(query, mode, limit):
    import urllib.request
    import urllib.parse

    base = _everything_http_base()
    if not base:
        return [], None

    params = {"search": query, "count": str(limit), "json": "1", "path_column": "1", "size_column": "1", "date_modified_column": "1"}
    query_string = urllib.parse.urlencode(params)
    url = f"{base}/?{query_string}"

    try:
        import json
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
    except Exception:
        return [], None

    results = []
    items = data.get("results", [])
    for item in items:
        if not isinstance(item, dict):
            continue
        path = item.get("path", "")
        full_path = os.path.join(path, item.get("name", "")).replace("\\", "/")
        if not full_path or not os.path.exists(full_path):
            continue
        kind = "folder" if item.get("type") == 2 else _file_kind(full_path)
        if mode == "apps" and kind not in ("application", "shortcut"):
            continue
        if mode == "documents" and kind in ("application", "shortcut", "folder"):
            continue
        size = item.get("size", 0) or None
        modified_str = item.get("date_modified", "")
        modified = None
        if modified_str:
            try:
                modified = datetime.fromtimestamp(int(modified_str))
            except (ValueError, TypeError, OSError):
                pass
        results.append(SearchResult(
            path=full_path,
            name=item.get("name", os.path.basename(full_path)),
            size=size,
            modified=modified,
            kind=kind,
            source="Everything",
        ))
    return results, "Everything"


def _search_via_filesystem(query, mode, limit):
    """Fallback: walk common locations with simple name matching."""
    results = []
    lower_query = query.lower()
    search_roots = [
        os.path.expandvars(r"%USERPROFILE%\Desktop"),
        os.path.expandvars(r"%USERPROFILE%\Downloads"),
        os.path.expandvars(r"%USERPROFILE%\Documents"),
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs"),
    ]
    if mode == "apps":
        search_roots = [
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs"),
        ]

    count = 0
    for root in search_roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            if count >= limit:
                break
            # Search folders
            for name in dirnames:
                if lower_query in name.lower():
                    full_path = os.path.join(dirpath, name)
                    try:
                        st = os.stat(full_path)
                    except OSError:
                        continue
                    if mode == "apps":
                        continue  # skip folders in apps mode
                    results.append(SearchResult(
                        path=full_path,
                        name=name,
                        size=None,
                        modified=datetime.fromtimestamp(st.st_mtime),
                        kind="folder",
                        source="本地",
                    ))
                    count += 1
                    if count >= limit:
                        break
            # Search files
            for name in filenames:
                if lower_query in name.lower():
                    full_path = os.path.join(dirpath, name)
                    try:
                        st = os.stat(full_path)
                    except OSError:
                        continue
                    kind = _file_kind(full_path)
                    if mode == "apps" and kind not in ("application", "shortcut"):
                        continue
                    if mode == "documents" and kind in ("application", "shortcut"):
                        continue
                    results.append(SearchResult(
                        path=full_path,
                        name=name,
                        size=st.st_size,
                        modified=datetime.fromtimestamp(st.st_mtime),
                        kind=kind,
                        source="本地",
                    ))
                    count += 1
                    if count >= limit:
                        break
            dirnames.sort()

    return results, "本地"


def _file_kind(path):
    suffix = Path(path).suffix.lower()
    if suffix in {".exe", ".bat", ".cmd", ".ps1"}:
        return "application"
    if suffix in {".lnk", ".appref-ms"}:
        return "shortcut"
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg", ".ico"}:
        return "image"
    if suffix in {".mp3", ".wav", ".flac", ".aac", ".ogg"}:
        return "audio"
    if suffix in {".mp4", ".avi", ".mkv", ".mov", ".webm"}:
        return "video"
    if suffix in {".zip", ".rar", ".7z", ".tar", ".gz"}:
        return "archive"
    if suffix in {".pdf"}:
        return "document"
    if suffix in {".py", ".js", ".ts", ".html", ".css", ".json", ".xml", ".md", ".txt"}:
        return "code"
    if suffix in {".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}:
        return "office"
    return "file"


def search_local(query, mode="apps", limit=80):
    """Return (list_of_SearchResult, source_name)."""
    results, source = _search_via_everything(query, mode, limit)
    if results:
        return results[:limit], source

    results, source = _search_via_filesystem(query, mode, limit)
    return results[:limit], source


def open_everything_search(query):
    """Open Everything.exe with a search query. Return True on success."""
    for exe in _everything_exe_paths():
        try:
            subprocess.Popen([exe, "-search", query])
            return True
        except Exception:
            continue
    return False


def open_path(path):
    """Open a file or folder with the default application."""
    if not path or not os.path.exists(path):
        return False
    try:
        os.startfile(path)
        return True
    except Exception:
        return False


def open_parent(path):
    """Open the parent folder and select the file."""
    if not path or not os.path.exists(path):
        return False
    try:
        subprocess.Popen(["explorer", "/select,", os.path.abspath(path)])
        return True
    except Exception:
        return False


def format_size(size_bytes):
    """Format bytes into human-readable string."""
    if size_bytes is None:
        return ""
    try:
        size_bytes = int(size_bytes)
    except (TypeError, ValueError):
        return ""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    for unit in ("KB", "MB", "GB", "TB"):
        size_bytes /= 1024.0
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
    return f"{size_bytes:.1f} PB"


def format_modified(dt):
    """Format a datetime into a readable string."""
    if dt is None:
        return ""
    if not isinstance(dt, datetime):
        return str(dt)
    now = datetime.now()
    delta = now - dt
    if delta.days == 0:
        return f"今天 {dt.strftime('%H:%M')}"
    if delta.days == 1:
        return f"昨天 {dt.strftime('%H:%M')}"
    if delta.days < 7:
        return f"{delta.days}天前"
    if dt.year == now.year:
        return dt.strftime("%m-%d")
    return dt.strftime("%Y-%m-%d")
