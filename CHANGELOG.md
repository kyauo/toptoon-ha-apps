# Toptoon Attendance Bot v0.5.20

## v0.5.20
- Changed the login status button to a fast saved-state check so it no longer attaches to slow Chromium/Selenium.
- Clarified in the UI that actual server authentication should be checked with the attendance test.
- Records `login_required` when Toptoon returns redirect HTML and the follow-up attendance probe still reports login required.
- Suppressed Selenium `set_timeout` deprecation noise while keeping short command timeouts.
- Synchronized visible version strings to 0.5.20.

## v0.5.19
- Added startup migration that removes stored legacy `phpsessid` and `rm_session` options from Supervisor's saved app configuration through the Supervisor options API.
- Kept the legacy keys in schema only, without default option values, so old saved configs validate during migration but new defaults no longer recreate them.
- Logs whether legacy option cleanup removed values, found nothing to remove, or could not reach the Supervisor API.
- Synchronized visible version strings to 0.5.19.

## v0.5.18
- Treat HTTP 200 `text/html` login responses as potentially successful and verify them with the direct attendance probe before failing.
- Share Chromium cookie persistence through one helper for JSON-success and HTML-success login flows.
- Return clearer messages when Toptoon returns an HTML response but the follow-up auth probe still reports login required.
- Synchronized visible version strings to 0.5.18.

## v0.5.17
- Added resilient login response parsing that can recover a JSON object embedded in an otherwise non-JSON Toptoon response.
- Logs the content type and a short sanitized response snippet when Toptoon returns HTTP 200 with a body that still cannot be parsed as JSON.
- Synchronized visible version strings to 0.5.17.

## v0.5.16
- Reintroduced legacy `phpsessid` and `rm_session` config keys as ignored compatibility options so Supervisor can validate old saved app options without warnings.
- The app still does not use cookie option values for login or authentication.
- Synchronized visible version strings to 0.5.16.

## v0.5.15
- Changed login preparation to return immediately without touching Chromium; Toptoon ID login no longer needs a browser page preparation step.
- Verifies successful ID/password login with a direct requests-session attendance probe before trying to persist cookies to Chromium.
- Keeps Chromium cookie persistence on a short timeout so a slow renderer cannot hide the direct login result.
- Synchronized visible version strings to 0.5.15.

## v0.5.14
- Replaced Facebook quick login with direct Toptoon ID/password login via `/login/login_proc`.
- Matches Toptoon's browser login POST shape, including `ci_token` from `ci_cookie`, auto-login, AJAX headers, and transient credentials.
- Persists successful login cookies into the persistent Chromium profile through CDP, then verifies authentication with the direct attendance AJAX probe.
- Keeps the login browser as the fallback for CAPTCHA, account challenge, or other manual confirmation.
- Synchronized visible version strings to 0.5.14.

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
