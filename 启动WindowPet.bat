@echo off
chcp 65001 >nul
cd /d "%~dp0"
title WindowPet

if exist "C:\Python313\pythonw.exe" goto RUN_C313
if exist "dist\Window Pet.exe" goto RUN_DIST
goto RUN_PATH

:RUN_C313
start "" "C:\Python313\pythonw.exe" main.py %*
exit /b 0

:RUN_DIST
cd /d "dist"
start "" "Window Pet.exe" %*
exit /b 0

:RUN_PATH
start "" pythonw main.py %*
exit /b 0
