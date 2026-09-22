@echo off
chcp 65001 >nul
title WindowPet 官网与小鼻嘎展馆本地极速预览

echo ===================================================
echo   正在启动 WindowPet 本地服务并打开小鼻嘎展馆...
echo ===================================================
echo.

cd /d "%~dp0"
set "DIST_DIR=%~dp0website\dist"

if not exist "%DIST_DIR%" (
    echo [错误] 未找到编译产物目录: %DIST_DIR%
    pause
    exit /b
)

:: 检查 4173 端口是否已被占用
netstat -ano | findstr ":4173" >nul
if %errorlevel% equ 0 (
    echo [提示] 本地 4173 端口服务已在运行，直接唤醒浏览器...
) else (
    echo [正在启动本地 HTTP 静态服务器...]
    start "" /b python -m http.server 4173 --directory "%DIST_DIR%"
    timeout /t 1 /nobreak >nul
)

echo [正在打开浏览器...]
start "" "http://127.0.0.1:4173/#/gallery"

echo.
echo ===================================================
echo   展馆页面已在浏览器中打开！
echo   访问地址: http://127.0.0.1:4173/#/gallery
echo   若关闭此窗口，本地服务将随之停止。
echo ===================================================
echo.
pause
