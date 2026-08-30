# Changelog

## 0.5.0
- Major authentication redesign: persistent Chromium profile replaces PHPSESSID/rm_session manual storage.
- Added Ingress control/status dashboard and VNC login-renewal browser.
- Attendance POST runs in the authenticated browser context.
- Retained 00:30 schedule, retries, 09:05 failure recheck/mobile alert, and 21:00 manual reminder.
- Added success mobile notification option.
- Added red-circle white-KY `icon.png` and `logo.png` to the app package.
- All app logs use KST timestamps.
