@echo off
title BurlingtonEnglish Auto Clicker
cd /d "%~dp0"

echo ========================================================
echo   Launching BurlingtonEnglish Automation Tool...
echo ========================================================
echo.

python gui_controller.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Notice] GUI closed or failed, falling back to CLI mode...
    python auto_clicker.py
)

pause
