#!/usr/bin/with-contenv bashio
set -euo pipefail

export DISPLAY=:99
PROFILE_DIR=/data/chromium-profile
mkdir -p "$PROFILE_DIR"

ts() { date '+%Y-%m-%d %H:%M:%S %Z'; }
log() { echo "[$(ts)] [$1] $2"; }

cleanup() {
  log INFO "Stopping Toptoon Attendance Bot services..."
  kill "${BOT_PID:-}" "${NGINX_PID:-}" "${NOVNC_PID:-}" "${VNC_PID:-}" "${CHROME_PID:-}" "${OPENBOX_PID:-}" "${XVFB_PID:-}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

port_ready() {
  python3 - "$1" <<'PYPORT'
import socket,sys
p=int(sys.argv[1])
s=socket.socket(); s.settimeout(0.5)
try:
    s.connect(('127.0.0.1',p)); ok=True
except Exception:
    ok=False
finally:
    s.close()
raise SystemExit(0 if ok else 1)
PYPORT
}

wait_port() {
  local port="$1" name="$2" tries="${3:-20}"
  local i
  for i in $(seq 1 "$tries"); do
    if port_ready "$port"; then
      log INFO "$name is ready on 127.0.0.1:$port."
      return 0
    fi
    sleep 0.5
  done
  log ERROR "$name did not open 127.0.0.1:$port."
  return 1
}

dump_log() {
  local label="$1" file="$2"
  if [ -s "$file" ]; then
    log ERROR "$label log follows:"
    tail -n 80 "$file" || true
  else
    log ERROR "$label produced no diagnostic output."
  fi
}

log INFO "Launching Xvfb display :99..."
Xvfb :99 -screen 0 1024x720x16 -ac +extension GLX +render -noreset >/tmp/xvfb.log 2>&1 &
XVFB_PID=$!
sleep 1
if ! kill -0 "$XVFB_PID" 2>/dev/null; then dump_log "Xvfb" /tmp/xvfb.log; exit 1; fi

openbox-session >/tmp/openbox.log 2>&1 &
OPENBOX_PID=$!

log INFO "Launching persistent Chromium profile..."
chromium-browser \
  --no-sandbox \
  --disable-dev-shm-usage \
  --disable-gpu \
  --disable-background-networking \
  --disable-component-update \
  --disable-features=Translate,OptimizationHints,SmoothScrolling \
  --wm-window-animations-disabled \
  --no-first-run \
  --no-default-browser-check \
  --user-data-dir="$PROFILE_DIR" \
  --remote-debugging-address=127.0.0.1 \
  --remote-debugging-port=9222 \
  --window-size=1024,720 \
  "https://toptoon.com/event/attendance" \
  >/tmp/chromium.log 2>&1 &
CHROME_PID=$!
if ! wait_port 9222 "Chromium remote debugging" 30; then dump_log "Chromium" /tmp/chromium.log; exit 1; fi

log INFO "Launching x11vnc..."
x11vnc -display :99 -forever -shared -nopw -localhost -rfbport 5900 -wait 20 -defer 20 -nap >/tmp/x11vnc.log 2>&1 &
VNC_PID=$!
if ! wait_port 5900 "x11vnc" 20; then dump_log "x11vnc" /tmp/x11vnc.log; exit 1; fi

NOVNC_WEB="$(dirname "$(find /usr/share -type f -name vnc.html 2>/dev/null | head -n 1)")"
if [ -z "$NOVNC_WEB" ] || [ "$NOVNC_WEB" = "." ]; then
  log ERROR "Could not locate noVNC web assets (vnc.html)."
  exit 1
fi
log INFO "Launching noVNC/websockify from $NOVNC_WEB..."
websockify --web="$NOVNC_WEB" 6080 localhost:5900 >/tmp/novnc.log 2>&1 &
NOVNC_PID=$!
if ! wait_port 6080 "noVNC/websockify" 20; then dump_log "noVNC/websockify" /tmp/novnc.log; exit 1; fi

python3 /bot.py &
BOT_PID=$!
if ! wait_port 8098 "Toptoon control UI" 20; then
  log ERROR "Toptoon control UI failed to start."
  kill "$BOT_PID" 2>/dev/null || true
  exit 1
fi

nginx -g 'daemon off;' >/tmp/nginx.log 2>&1 &
NGINX_PID=$!
if ! wait_port 8099 "Ingress nginx" 20; then dump_log "nginx" /tmp/nginx.log; exit 1; fi

log INFO "Toptoon browser, VNC, noVNC, control UI, and Ingress proxy are all ready."
wait "$BOT_PID"
