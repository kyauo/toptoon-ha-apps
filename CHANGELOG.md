# Changelog

## v0.5.7
- Fixed false-positive login detection: ambiguous pages or stale cookies are no longer reported as definitely logged in.
- Attendance now reuses an already-open Toptoon document instead of reloading the attendance page every time.
- If Chromium is outside Toptoon, navigation is bounded to 18 seconds and continues only if Toptoon context is reached.
- Attendance AJAX now has a 12-second browser-side abort limit and logs timing separately.
- The Toptoon attendance AJAX result is authoritative for login state (`logged_in` / `login_required`).
- Control UI request timeout increased to 120 seconds and final backend result is shown before refresh.
- Failure results such as `login_required` persist immediately to `today_status`.
