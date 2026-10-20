@echo off
chcp 65001 >nul
title WindowPet 官网与小鼻嘎展馆本地预览
cd /d "%~dp0"

echo ========================================================
echo   WindowPet 官网与展馆 - 本地高速预览服务
echo ========================================================
echo.
echo 正在启动本地 Web 服务 (端口 4173)...
start /b "" node server-preview.js

timeout /t 1 /nobreak >nul
start http://127.0.0.1:4173

echo.
echo 官网已在默认浏览器中打开！
echo 本窗口保持开启以维持本地预览服务。
echo 如需关闭服务，可直接关闭此窗口。
echo.
pause
