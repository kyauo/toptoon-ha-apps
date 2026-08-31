# Changelog

## 0.5.3
- Optimized the interactive login browser for low-bandwidth Home Assistant Ingress/noVNC use.
- Reduced virtual display size from 1280x900x24 to 1024x720x16.
- Disabled Chromium window animations and smooth scrolling.
- Tuned x11vnc update behavior with `-noxdamage`, shorter wait/defer intervals.
- Requested lower noVNC visual quality and stronger compression for the login-only VNC session.
- Retains persistent Chromium profile, scheduler, retry logic, notifications, readiness diagnostics, and KY branding.
