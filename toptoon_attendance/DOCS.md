# Toptoon Attendance Bot

Toptoon attendance automation for Home Assistant using a persistent Chromium profile.

## Login
Open the App Web UI and use **로그인 브라우저 열기** only when Toptoon login has expired. The browser profile is stored under `/data/chromium-profile` and survives app restarts and updates.

## v0.5.2
The noVNC launch URL now uses a WebSocket path relative to `vnc.html` (`path=websockify`). This preserves the Home Assistant Ingress prefix automatically and avoids the duplicated `/vnc/vnc/websockify` route that caused “서버에 연결하지 못했습니다.” even while ports 5900/6080 were healthy.
