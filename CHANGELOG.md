# Toptoon Attendance Bot v0.5.11

## v0.5.11
- Facebook credential submission now uses one CDP `Runtime.evaluate` call instead of repeated Selenium element commands.
- The submit endpoint returns immediately after the click command is accepted.
- Toptoon authentication is verified in a background thread using the fast direct HTTP probe.
- Removed renderer-dependent post-submit polling that could hang for minutes.
- Synchronized visible version strings to 0.5.11.
