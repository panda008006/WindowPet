@echo off
chcp 65001 >nul
cd /d "%~dp0"
title WindowPet 调试终端

if exist "C:\Python313\python.exe" goto RUN_C313
if exist "dist\Window Pet.exe" goto RUN_DIST
goto RUN_PATH

:RUN_C313
echo [WindowPet] 正在使用 C:\Python313\python.exe 启动...
"C:\Python313\python.exe" main.py %*
goto FINISH

:RUN_DIST
echo [WindowPet] 正在启动 dist\Window Pet.exe...
cd /d "dist"
"Window Pet.exe" %*
goto FINISH

:RUN_PATH
echo [WindowPet] 正在使用系统 python 启动...
python main.py %*
goto FINISH

:FINISH
if errorlevel 1 (
    echo.
    echo [WindowPet] 程序退出，代码：%errorlevel%
    pause
)
