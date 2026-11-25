@echo off
title Genral Sync - Universal Sequence Clicker
cd /d "%~dp0"

echo ========================================================
echo   Launching Genral Sync...
echo ========================================================

python -c "import pyautogui, keyboard, pynput" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [Setup] Installing required packages ^(pyautogui, keyboard, pynput^)...
    python -m pip install pyautogui keyboard pynput
)

python app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Error] Could not start Genral Sync. Make sure Python is installed.
    pause
)
