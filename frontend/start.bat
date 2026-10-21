@echo off
title CongestAir - Research Dashboard
echo ========================================================
echo   CongestAir: Urban Traffic & Air Quality Intelligence
echo ========================================================
echo.

node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not found on your system!
    echo Please download and install Node.js from https://nodejs.org/
    echo Then double-click this file again.
    echo.
    pause
    exit /b 1
)

if not exist node_modules (
    echo [INFO] First-time setup: installing dependencies...
    call npm install
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
)

echo.
echo [INFO] Launching CongestAir Dashboard...
echo [INFO] Open your browser at: http://localhost:5173/
echo.
call npm run dev
pause
