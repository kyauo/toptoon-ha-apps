# Toptoon Attendance Bot v0.5.13

## v0.5.13
- Open the Facebook login target through Chromium's debugging HTTP endpoint before falling back to CDP navigation, avoiding renderer wait during login preparation.
- Cap Selenium command waits so failed automatic Facebook submit returns in about 18 seconds instead of hanging for two minutes.
- When automatic submit times out, update status to `manual_needed` and direct the user to the login browser instead of leaving a generic request failure.
- Synchronized visible version strings to 0.5.13.

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
