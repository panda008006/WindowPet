# -*- mode: python ; coding: utf-8 -*-
"""WindowPet PyInstaller 打包配置（从 build/WindowPet/*.toc 还原）。

构建：
    pyinstaller WindowPet.spec --noconfirm

产物：
    dist/Window Pet.exe（onefile 单文件）
    dist/ 下同时复制外置资源：精简后的 assets、AI角色制作、AGENTS.md、
    CLAUDE.md、update_config.json、package_registry.json、medals.json。

    角色素材必须留在 exe 旁边。完整 assets 目录包含原始视频和抽帧缓存，
    直接放进 onefile 会把十几 GB 的素材压进 exe，导致构建和下载都不可用。
    构建时只把轻量 UI 素材放进 exe，外置目录保留透明帧缓存并排除原始视频。
"""
import shutil
from pathlib import Path

from PIL import Image

from PyInstaller.utils.win32.versioninfo import (
    FixedFileInfo,
    StringFileInfo,
    StringStruct,
    StringTable,
    VarFileInfo,
    VarStruct,
    VSVersionInfo,
)

ROOT = Path(SPECPATH)
# PyInstaller 执行 spec 时注入 DISTPATH（默认 dist/，可用 --distpath 覆盖），
# 外置资源与 exe 保持一致目录。
EXTERNAL_ROOT = Path(DISTPATH)
VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov", ".mkv", ".avi", ".m4v"}

# Keep the desktop download small and predictable.  The source tree still
# contains the other community roles for the website/import flow; only this
# allow-list is copied beside the desktop executable.
BUILTIN_PET_DIRS = (
    "ChubbyGoldenCatPet",
    "ClaudePet",
    "CodexPet",
    "DaDeepSeekPet",
    "DaFeiYuPet",
    "DoubaoAiPet",
    "DoubaoPet",
    "HuhuPet",
    "JiyiPet",
    "LeopardGeckoPet",
    "LiangShengPet",
    "LinChuXuePet",
    "MunchkinCatPet",
    "NuonuoPet",
    "PenguinSisterPet",
    "QianDuoDuoPet",
    "SugarGliderPet",
    "TeslaPet",
    "UsagiPet",
    "WestiePet",
    "XiaobaPet",
    "XiaobaTurnPet",
    "XiaoDeepSeekPet",
    "XiaoWangPet",
    "ZhuZhuXiaPet",
    "ZlmPet",
)
EXTERNAL_ASSET_DIRS = {"UiAssets", "ToolAssets", *BUILTIN_PET_DIRS}

# 打进 exe 的素材（运行时从 _MEIPASS 读取；外置副本仍由 collect_external_data 复制）
datas = [
    (str(ROOT / "icon.ico"), "."),
    (str(ROOT / "icon.png"), "."),
    (str(ROOT / "assets" / "UiAssets"), "assets/UiAssets"),
    (str(ROOT / "assets" / "ToolAssets"), "assets/ToolAssets"),
    (str(ROOT / "AI角色制作"), "AI角色制作"),
    (str(ROOT / "AGENTS.md"), "."),
    (str(ROOT / "CLAUDE.md"), "."),
    (str(ROOT / "update_config.json"), "."),
    (str(ROOT / "package_registry.json"), "."),
    (str(ROOT / "medals.json"), "."),
]

version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(2, 0, 0, 0),
        prodvers=(2, 0, 0, 0),
        mask=0x3F,
        flags=0x0,
        OS=0x40004,
        fileType=1,
        subtype=0x0,
        date=(0, 0),
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    "040904B0",
                    [
                        StringStruct("CompanyName", "Agent Panda"),
                        StringStruct("FileDescription", "Window Pet desktop companion"),
                        StringStruct("FileVersion", "2.0.0"),
                        StringStruct("InternalName", "Window Pet"),
                        StringStruct("OriginalFilename", "Window Pet.exe"),
                        StringStruct("ProductName", "Window Pet"),
                        StringStruct("ProductVersion", "2.0.0"),
                        StringStruct("LegalCopyright", "Copyright (c) 2026 Agent Panda"),
                    ],
                )
            ]
        ),
        VarFileInfo([VarStruct("Translation", [1033, 1200])]),
    ],
)

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets", "PySide6.QtMultimedia", "win32crypt"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Window Pet",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    icon=[str(ROOT / "icon.ico")],
    version=version_info,
)


def collect_external_data():
    """把角色素材与文档复制到 exe 旁边，保持发布版目录结构（可热改角色）。"""
    EXTERNAL_ROOT.mkdir(parents=True, exist_ok=True)
    copy2 = shutil.copy2
    copy2(ROOT / "update_config.json", EXTERNAL_ROOT / "update_config.json")
    for name in ("package_registry.json", "medals.json", "icon.ico", "icon.png"):
        source = ROOT / name
        if source.is_file():
            copy2(source, EXTERNAL_ROOT / name)
    if (EXTERNAL_ROOT / "角色").exists():
        shutil.rmtree(EXTERNAL_ROOT / "角色")
    if (EXTERNAL_ROOT / "AI角色制作").exists():
        shutil.rmtree(EXTERNAL_ROOT / "AI角色制作")
    if (ROOT / "AI角色制作").exists():
        shutil.copytree(
            ROOT / "AI角色制作",
            EXTERNAL_ROOT / "AI角色制作",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    for obsolete in ("【双击启动 Window Pet】.bat", "【双击启动 Window Pet】.lnk"):
        obs_file = EXTERNAL_ROOT / obsolete
        if obs_file.exists():
            obs_file.unlink()
    launcher_src = ROOT / "【双击启动 Window Pet】.exe"
    if launcher_src.exists():
        copy2(launcher_src, EXTERNAL_ROOT / "【双击启动 Window Pet】.exe")
    # 保留已有 assets 缓存，避免重复转换上万张 WebP 帧
    # if (EXTERNAL_ROOT / "assets").exists():
    #     shutil.rmtree(EXTERNAL_ROOT / "assets")

    source_assets = ROOT / "assets"
    target_assets = EXTERNAL_ROOT / "assets"
    target_assets.mkdir(parents=True, exist_ok=True)
    missing = [name for name in BUILTIN_PET_DIRS if not (source_assets / name).is_dir()]
    if missing:
        raise FileNotFoundError(
            "Required built-in role directories are missing: " + ", ".join(missing)
        )
    for source_path in source_assets.rglob("*"):
        relative = source_path.relative_to(source_assets)
        # Do not ship every source role.  Unlisted roles remain available in
        # the repository and website, and can be imported by users later.
        if not relative.parts or relative.parts[0] not in EXTERNAL_ASSET_DIRS:
            continue
        if "video_sources" in relative.parts or source_path.suffix.lower() in VIDEO_EXTENSIONS:
            continue
        target_path = target_assets / relative
        if source_path.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if not target_path.exists() or target_path.stat().st_size != source_path.stat().st_size:
            shutil.copy2(source_path, target_path)
    for name in ("AGENTS.md", "CLAUDE.md"):
        source = ROOT / name
        if source.is_file():
            copy2(source, EXTERNAL_ROOT / name)


# PyInstaller 执行本 spec 时：先铺好 exe 旁边的外置资源，exe 随后写入同一目录
collect_external_data()
