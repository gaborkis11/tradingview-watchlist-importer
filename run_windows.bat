@echo off
title Trading Pairs Fetcher
cls
echo ======================================
echo    Trading Pairs Fetcher - Windows
echo ======================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [HIBA] Python nincs telepitve!
    pause
    exit /b 1
)

python multi_exchange_pairs.py
if %errorlevel% neq 0 (
    python3 multi_exchange_pairs.py
)

echo.
echo ======================================
pause
