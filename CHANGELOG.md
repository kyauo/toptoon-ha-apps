# Changelog

## 0.5.1
- Reworked the VNC startup path for login renewal.
- Launches noVNC explicitly through `websockify` using the installed noVNC web assets.
- Verifies Chromium remote debugging (9222), x11vnc (5900), noVNC (6080), control UI (8098), and Ingress nginx (8099) before declaring startup ready.
- Emits actionable diagnostics from Xvfb, Chromium, x11vnc, noVNC/websockify, or nginx when a service fails.
- Keeps the persistent Chromium profile, existing attendance schedule/retries/notifications, and bundled red-circle white-KY `icon.png` / `logo.png`.

## 0.5.0
- Major authentication redesign: persistent Chromium profile replaces PHPSESSID/rm_session manual storage.
- Added Ingress control/status dashboard and VNC login-renewal browser.
- Attendance POST runs in the authenticated browser context.
- Retained 00:30 schedule, retries, 09:05 failure recheck/mobile alert, and 21:00 manual reminder.
- Added success mobile notification option.
- Added red-circle white-KY `icon.png` and `logo.png` to the app package.
- All app logs use KST timestamps.
