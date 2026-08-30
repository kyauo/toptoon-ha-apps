#!/usr/bin/with-contenv bashio
set -e
ts() { TZ="Asia/Seoul" date '+%Y-%m-%d %H:%M:%S KST'; }
echo "[$(ts)] [INFO] Starting Toptoon Attendance Bot..."
exec /opt/venv/bin/python3 -u /bot.py
