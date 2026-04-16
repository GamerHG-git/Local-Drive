#!/bin/bash

echo -e "\e[32m[1/3] Checking Dependencies...\e[0m"

# التحقق من بايثون
if ! command -v python3 &> /dev/null; then
    echo "[!] Python3 could not be found. Please install it."
    exit
fi

# تحميل المكتبات
if [ -f requirements.txt ]; then
    echo -e "\e[32m[2/3] Installing/Updating Python libraries...\e[0m"
    pip3 install -r requirements.txt --quiet
else
    echo "[!] requirements.txt not found."
fi

# التحقق من cloudflared
if ! command -v cloudflared &> /dev/null; then
    echo "[!] cloudflared not found. Please install it to use the tunnel."
fi

echo -e "\e[32m[3/3] Launching Local Drive...\e[0m"

# تشغيل السيرفر في الخلفية
python3 app.py &

# تشغيل النفق
echo -e "\e[34m[*] Starting Cloudflare Tunnel on Port 5000...\e[0m"
cloudflared tunnel --url http://localhost:5000