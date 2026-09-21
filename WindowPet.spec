# -*- mode: python ; coding: utf-8 -*-
"""WindowPet PyInstaller 打包配置（从 build/WindowPet/*.toc 还原）。

构建：
    pyinstaller WindowPet.spec --noconfirm

产物：
    dist/Window Pet.exe（onefile 单文件）
    dist/ 下同时复制外置资源：assets、AI角色制作、AGENTS.md、CLAUDE.md、
    update_config.json —— 与线上发布版目录结构一致，用户可直接改 assets 换角色。
"""
import shutil
import sys
from pathlib import Path

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

# 打进 exe 的素材（运行时从 _MEIPASS 读取；外置副本仍由 collect_external_data 复制）
datas = [
    (str(ROOT / "assets" / "UiAssets"), "assets/UiAssets"),
    (str(ROOT / "assets" / "XiaobaPet"), "assets/XiaobaPet"),
    (str(ROOT / "assets" / "XiaochaiPet"), "assets/XiaochaiPet"),
    (str(ROOT / "AI角色制作"), "AI角色制作"),
    (str(ROOT / "AGENTS.md"), "."),
    (str(ROOT / "CLAUDE.md"), "."),
    (str(ROOT / "update_config.json"), "."),
]

version_info = VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1, 0, 32, 0),
        prodvers=(1, 0, 32, 0),
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
                        StringStruct("FileVersion", "1.0.32"),
                        StringStruct("InternalName", "Window Pet"),
                        StringStruct("OriginalFilename", "Window Pet.exe"),
                        StringStruct("ProductName", "Window Pet"),
                        StringStruct("ProductVersion", "1.0.32"),
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
    hiddenimports=["PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets", "PySide6.QtMultimedia"],
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
    copytree = shutil.copytree
    copy2(ROOT / "update_config.json", EXTERNAL_ROOT / "update_config.json")
    if (EXTERNAL_ROOT / "AI角色制作").exists():
        shutil.rmtree(EXTERNAL_ROOT / "AI角色制作")
    copytree(ROOT / "AI角色制作", EXTERNAL_ROOT / "AI角色制作")
    if (EXTERNAL_ROOT / "assets").exists():
        shutil.rmtree(EXTERNAL_ROOT / "assets")
    copytree(ROOT / "assets", EXTERNAL_ROOT / "assets")
    for name in ("AGENTS.md", "CLAUDE.md"):
        source = ROOT / name
        if source.is_file():
            copy2(source, EXTERNAL_ROOT / name)


# PyInstaller 执行本 spec 时：先铺好 exe 旁边的外置资源，exe 随后写入同一目录
collect_external_data()
