# Toptoon Attendance Bot v0.5.9

- Chromium now starts at `about:blank` instead of preloading Toptoon.
- Selenium uses `page_load_strategy=none` for non-blocking navigation.
- Login preparation caps renderer work and avoids repeated DOM/WebDriver round trips.
- Added foreground-renderer Chromium flags to reduce background throttling.
- Login preparation UI timeout reduced to 35 seconds so a stuck renderer fails fast.

# Changelog

## v0.5.9
- Removed blocking `driver.get()` from Facebook login preparation.
- Added bounded non-blocking Toptoon navigation.
- Added authoritative Toptoon AJAX authentication probe.
- Added a 45-second UI deadline for login preparation.
- Suppressed expected BrokenPipe/connection-reset tracebacks when Ingress disconnects first.
- Synchronized all visible version strings to 0.5.9.
