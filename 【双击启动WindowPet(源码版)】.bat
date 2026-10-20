@echo off
chcp 65001 >nul
title WindowPet 桌面伙伴 (源码调试版)
cd /d "%~dp0"

echo ========================================================
echo   WindowPet 桌面伙伴 - 正在以 Python 源码模式启动...
echo ========================================================
echo.

if exist "C:\Python313\pythonw.exe" (
    start "" "C:\Python313\pythonw.exe" main.py
    exit /b 0
)

if exist "C:\Python311\pythonw.exe" (
    start "" "C:\Python311\pythonw.exe" main.py
    exit /b 0
)

python main.py
if errorlevel 1 (
    echo.
    echo 启动异常，按任意键退出...
    pause >nul
)
