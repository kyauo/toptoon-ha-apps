# Changelog

## 0.5.2
- Fixed the noVNC WebSocket path behind Home Assistant Ingress.
- Changed the login-browser link from `path=vnc/websockify` to `path=websockify`, allowing current noVNC to resolve the socket relative to `vnc.html` and preserve the dynamic Ingress prefix.
- Kept the 0.5.1 readiness checks for Chromium, x11vnc, noVNC/websockify, control UI, and nginx.
- Kept the persistent Chromium profile and KY icon/logo assets.

## 0.5.1
- Added service readiness diagnostics and explicit port checks.
- Added direct noVNC/websockify startup diagnostics.
