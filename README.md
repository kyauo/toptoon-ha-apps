# Toptoon Attendance Bot v0.5.7 bundle

This build focuses on the two problems observed in v0.5.6: false `already logged in` detection and an unnecessary full attendance-page reload before every attendance POST.

## Test after update
1. Update the `toptoon_attendance` folder and restart the App.
2. Do **not** open VNC first.
3. Press `지금 출석 테스트` once.
4. Check the UI result and log timing lines beginning with `Attendance:`.

If the existing Chromium document is already on `toptoon.com`, v0.5.7 should skip navigation completely and send the attendance AJAX request immediately. The AJAX response is treated as the authoritative login check.
