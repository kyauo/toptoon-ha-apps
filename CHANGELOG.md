# Toptoon Attendance Bot v0.5.10

## v0.5.10
- Removed renderer JavaScript from login-state probing and attendance execution.
- Reads Toptoon cookies from persistent Chromium at browser/CDP level and performs the authoritative attendance POST with Python requests.
- Login preparation discovers the Facebook login target from Toptoon HTML and asks Chromium to navigate with CDP `Page.navigate`, avoiding `window.stop`, `execute_async_script`, and `current_url` renderer stalls.
- Direct HTTP operations use bounded connect/read timeouts, so a wedged Chromium renderer should no longer turn a login check into a 40–120 second wait.
- Synchronized visible package version strings to 0.5.10.

- Chromium now starts at `about:blank` instead of preloading Toptoon.
- Selenium uses `page_load_strategy=none` for non-blocking navigation.
- Login preparation caps renderer work and avoids repeated DOM/WebDriver round trips.
- Added foreground-renderer Chromium flags to reduce background throttling.
- Login preparation UI timeout reduced to 35 seconds so a stuck renderer fails fast.

# Changelog

## v0.5.10
- Removed blocking `driver.get()` from Facebook login preparation.
- Added bounded non-blocking Toptoon navigation.
- Added authoritative Toptoon AJAX authentication probe.
- Added a 45-second UI deadline for login preparation.
- Suppressed expected BrokenPipe/connection-reset tracebacks when Ingress disconnects first.
- Synchronized all visible version strings to 0.5.10.
