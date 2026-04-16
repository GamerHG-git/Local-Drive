@echo off
title Local Drive Starter - Windows
color 0A

echo [1/3] Checking Dependencies...
:: التحقق من وجود بايثون
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not installed. Please install it first.
    pause
    exit
)

:: تحميل المكتبات المطلوبة من ملف requirements.txt
if exist requirements.txt (
    echo [2/3] Installing/Updating Python libraries...
    pip install -r requirements.txt --quiet
) else (
    echo [!] requirements.txt not found. Skipping library install.
)

:: التحقق من وجود Cloudflared
cloudflared --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] cloudflared is not in PATH. Tunnel will not start.
    echo [!] Download it from: https://github.com/cloudflare/cloudflared/releases
)

echo [3/3] Launching Local Drive...
:: تشغيل تطبيق البايثون في نافذة منفصلة
start "Local Drive Server" cmd /k "py app.py"

:: تشغيل نفق كلاود فلير على بورت 5000
echo.
echo [*] Starting Cloudflare Tunnel on Port 5000...
cloudflared tunnel --url http://localhost:5000

pause