# Toptoon Attendance Bot v0.5.12

## v0.5.12
- Added a server-side duplicate-submit guard for quick Facebook login.
- Broadened the single CDP submit script to search visible login fields across accessible frames and submit the owning form when no button is found.
- Removed the legacy `rm_session` cookie shortcut from login probing; Toptoon auth is confirmed only by the direct attendance AJAX response.
- Synchronized visible version strings to 0.5.12.

## v0.5.11
- Facebook credential submission now uses one CDP `Runtime.evaluate` call instead of repeated Selenium element commands.
- The submit endpoint returns immediately after the click command is accepted.
- Toptoon authentication is verified in a background thread using the fast direct HTTP probe.
- Removed renderer-dependent post-submit polling that could hang for minutes.
- Synchronized visible version strings to 0.5.11.
